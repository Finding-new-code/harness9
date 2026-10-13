"""src/h9_runtime/content.py

ContentRuntime protocol and DefaultContentRuntime implementation.
Governs high-level multimedia content production, 17-state lifecycle execution,
Production IR compilation, and broadcast MP4 rendering.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import shutil
import time
from typing import Any, Dict, List, Optional, Protocol, Tuple, Union, runtime_checkable

from src.evaluation.media_gate import ExpectedMedia, MediaGate
from src.evaluation.render_evaluation import evaluate_render
from src.h9_runtime.types import (
    ExecutionResult,
    ProductionIR,
    ProductionResult,
)
if False:  # TYPE_CHECKING guard
    from src.models.ir import ProductionIRDocument
from src.models.contracts import (
    ContentBrief,
    ContentOutline,
    EditorialAngle,
    EvaluationLayer,
    EvaluationReport,
    PublishPackage,
    RenderArtifact,
    ResearchDossier,
    Script,
    ScriptScene,
    ScriptBeat,
)
logger = logging.getLogger(__name__)


def _render_stage_metrics(workspace: Path) -> Dict[str, Any]:
    """Metrics of the pipeline's render stage (backend, validation_status, gate result), or {}."""
    summary_file = Path(workspace) / "pipeline_summary.json"
    try:
        data = json.loads(summary_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    for stage in data.get("stages", []):
        if stage.get("stage_name") == "hyperframes_render":
            return dict(stage.get("metrics", {}))
    return {}


def _canonical_state_history(state_machine: Any) -> List[Dict[str, Any]]:
    """Return lifecycle history with an explicit state field on every record."""
    audit_log = state_machine.get_audit_log()
    first_timestamp = (
        state_machine.history[0].timestamp
        if state_machine.history
        else datetime.now(timezone.utc).isoformat()
    )
    history = [{
        "state": "CREATED",
        "from_state": None,
        "to_state": "CREATED",
        "timestamp": first_timestamp,
    }]
    for record in audit_log:
        entry = dict(record)
        entry.setdefault("state", entry.get("to_state", entry.get("from_state")))
        history.append(entry)
    return history


@runtime_checkable
class ContentRuntime(Protocol):
    """High-level content production interface connecting H9 domain logic with Hermes."""

    def plan_research(
        self,
        topic: str,
        session_id: str,
        offline: bool = True,
        duration: int = 30,
    ) -> ResearchDossier:
        """Execute multi-source research synthesis returning a validated dossier."""
        ...

    def evaluate_angles(
        self,
        dossier: ResearchDossier,
        creator_id: Optional[str] = None,
    ) -> Tuple[List[EditorialAngle], EditorialAngle]:
        """Generate candidate angles and select winning angle via 9-dimension evaluation."""
        ...

    def generate_script(
        self,
        angle: EditorialAngle,
        dossier: ResearchDossier,
        creator_id: Optional[str] = None,
        format_aspect: str = "16:9",
        duration: float = 30.0,
    ) -> Script:
        """Generate structured script, voiceover beats, and narration."""
        ...

    def compile_production_ir(
        self,
        script: Script,
        workspace_dir: Path,
    ) -> ProductionIRDocument:
        """Compile script and discovered assets into typed Production IR AST."""
        ...

    def render_video(
        self,
        ir: Union[ProductionIRDocument, ProductionIR, Dict[str, Any]],
        output_dir: Path,
        session_id: str,
    ) -> RenderArtifact:
        """Render broadcast MP4 from Production IR using sandboxed execution."""
        ...

    def run_full_production(
        self,
        brief: ContentBrief,
        session_id: str,
    ) -> ProductionResult:
        """Execute full 17-state autonomous production pipeline."""
        ...


class DefaultContentRuntime:
    """Concrete implementation of ContentRuntime connecting H9 domain modules."""

    def __init__(self, base_workspace_dir: Optional[Path] = None) -> None:
        self.base_workspace_dir = (base_workspace_dir or Path("output/sessions")).resolve()
        self.base_workspace_dir.mkdir(parents=True, exist_ok=True)

    def _get_session_workspace(self, session_id: str) -> Path:
        ws = (self.base_workspace_dir / session_id / "workspace").resolve()
        ws.mkdir(parents=True, exist_ok=True)
        return ws

    def _get_session_renders(self, session_id: str) -> Path:
        renders = (self.base_workspace_dir / session_id / "renders").resolve()
        renders.mkdir(parents=True, exist_ok=True)
        return renders

    def plan_research(
        self,
        topic: str,
        session_id: str,
        offline: bool = True,
        duration: int = 30,
    ) -> ResearchDossier:
        """Execute research synthesis returning a validated ResearchDossier."""
        from src.research.engine import ResearchEngine

        engine = ResearchEngine()
        ws = self._get_session_workspace(session_id)
        dossier_obj = engine.synthesize_research(
            topic=topic,
            offline=offline,
            target_duration=duration,
        )

        if isinstance(dossier_obj, ResearchDossier):
            return dossier_obj

        dossier_dict = dossier_obj.to_dict() if hasattr(dossier_obj, "to_dict") else dict(dossier_obj)
        claims = dossier_dict.get("claims", [])
        if not claims:
            from src.research.engine import ResearchUnavailableError

            raise ResearchUnavailableError(f"Research for {topic!r} returned no source-backed claims.")
        summary = dossier_dict.get("summary") or {}
        for c in claims:
            if "claim_id" not in c and "id" in c:
                c["claim_id"] = c["id"]
            if "confidence_score" not in c and "confidence" in c:
                c["confidence_score"] = c["confidence"]
            if "epistemic_status" not in c:
                verification_status = str(c.get("verification_status") or "").upper()
                c["epistemic_status"] = (
                    "verified" if verification_status == "VERIFIED" else "unverifiable"
                )

        measured_scores = [float(c["confidence_score"]) for c in claims if c.get("confidence_score") is not None]
        if len(measured_scores) != len(claims):
            raise ValueError("Research claims must carry measured confidence scores.")

        key_takeaways = (
            dossier_dict.get("key_takeaways")
            or summary.get("key_takeaways")
            or [str(claim.get("claim_text") or "").strip() for claim in claims]
        )
        key_takeaways = [takeaway for takeaway in key_takeaways if takeaway]
        if not key_takeaways:
            raise ValueError("Research dossier contains no usable claim text for script generation.")

        return ResearchDossier(
            dossier_id=dossier_dict.get("run_id", f"dossier_{session_id}"),
            topic=topic,
            headline=str(summary.get("headline") or ""),
            executive_summary=str(summary.get("executive_summary") or ""),
            key_takeaways=key_takeaways,
            claims=claims,
            search_queries=dossier_dict.get("suggested_visual_queries", []),
            confidence_score=sum(measured_scores) / len(measured_scores),
        )

    def evaluate_angles(
        self,
        dossier: ResearchDossier,
        creator_id: Optional[str] = None,
    ) -> Tuple[List[EditorialAngle], EditorialAngle]:
        """Generate candidate angles and select winning angle."""
        from src.editorial import EditorialEngine

        editorial = EditorialEngine()
        candidates, winner, _, _ = editorial.process_editorial(dossier=dossier)
        return candidates, winner

    def generate_script(
        self,
        angle: EditorialAngle,
        dossier: ResearchDossier,
        creator_id: Optional[str] = None,
        format_aspect: str = "16:9",
        duration: float = 30.0,
    ) -> Script:
        """Generate structured script with timestamped scenes and beats."""
        if not dossier.claims:
            raise ValueError("Script generation requires at least one source-backed claim.")
        total_duration = max(5.0, float(duration))
        scene_count = 4
        scene_duration = total_duration / scene_count

        scenes: List[ScriptScene] = []
        full_text_parts = []

        components = [
            "reference_collage_hook",
            "split_screen_intro",
            "timeline_reveal",
            "creator_bottom_collage",
        ]

        style_name = getattr(angle, "narrative_style", getattr(angle, "title", "Editorial Perspective"))

        takeaways = dossier.key_takeaways or [claim.claim_text for claim in dossier.claims]
        for i, comp in enumerate(components):
            start = i * scene_duration
            end = (i + 1) * scene_duration
            takeaway = (
                takeaways[i % len(takeaways)]
            )
            narration = (
                f"Scene {i+1}: Investigating {dossier.topic} through {style_name}. "
                f"Key discovery: {takeaway}"
            )
            full_text_parts.append(narration)

            beat = ScriptBeat(
                beat_id=f"beat_{i+1:02d}",
                start_time=start,
                end_time=end,
                duration=scene_duration,
                text=narration,
                visual_cue=f"Animate {comp}",
            )

            scene = ScriptScene(
                scene_id=f"scene_{i+1:02d}",
                title=f"Part {i+1}: {dossier.topic}",
                start_time=start,
                duration=scene_duration,
                narration_text=narration,
                component_type=comp,
                beats=[beat],
            )
            scenes.append(scene)

        full_script = " ".join(full_text_parts)
        words = len(full_script.split())

        return Script(
            topic=dossier.topic,
            title=getattr(angle, "title", f"The Story of {dossier.topic}"),
            angle_id=getattr(angle, "angle_id", None),
            total_duration=total_duration,
            full_transcript=full_script,
            word_count=words,
            scenes=scenes,
        )

    def compile_production_ir(
        self,
        script: Script,
        workspace_dir: Path,
    ) -> ProductionIRDocument:
        """Compile script and discovered assets into typed Production IR AST."""
        # Discover any assets staged in workspace directory
        assets: List[Dict[str, Any]] = []
        images_dir = workspace_dir / "assets" / "images"
        if images_dir.exists():
            for p in images_dir.glob("*.*"):
                if p.is_file():
                    assets.append({
                        "asset_id": p.stem,
                        "file_path": str(p.relative_to(workspace_dir).as_posix()),
                        "media_type": "image/svg+xml" if p.suffix.lower() == ".svg" else "image/png",
                    })

        total_dur = float(
            script.total_duration
            if getattr(script, "total_duration", 0.0) > 0
            else sum(float(s.duration) for s in script.scenes)
        )
        if total_dur <= 0:
            total_dur = 30.0

        audio_narration = {
            "audio_rel_path": "assets/audio/narration.wav",
            "total_duration_sec": total_dur,
            "sample_rate": 44100,
            "channels": 2,
        }

        from src.models.ir import compile_script_to_ir

        doc = compile_script_to_ir(
            script=script,
            assets=assets,
            audio_narration=audio_narration,
        )
        if hasattr(script, "project_id") and script.project_id:
            doc.metadata.project_id = script.project_id
        return doc

    def render_video(
        self,
        ir: Union[ProductionIRDocument, ProductionIR, Dict[str, Any]],
        output_dir: Path,
        session_id: str,
    ) -> RenderArtifact:
        """Copy and re-verify the completed render associated with this session.

        Production IR alone does not contain the synthesized narration media needed
        to render a video. Never fabricate a media container when the production
        pipeline has not produced a real video.
        """
        ws = self._get_session_workspace(session_id)
        candidate = ws / "renders" / "final.mp4"
        summary_path = ws / "pipeline_summary.json"
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise RuntimeError(
                "No completed Harness 9 production summary exists for this session. "
                "Production IR does not include narration audio; run the full production pipeline first."
            ) from exc
        if summary.get("status") != "SUCCESS":
            raise RuntimeError(
                f"Session production status is {summary.get('status', 'UNKNOWN')}; only SUCCESS runs can be exported."
            )

        metadata = getattr(ir, "metadata", {})
        expected_topic = getattr(metadata, "topic", None) if not isinstance(metadata, dict) else metadata.get("topic")
        metrics = summary.get("metrics") or {}
        render_stages = [
            stage for stage in summary.get("stages", [])
            if stage.get("stage_name") == "hyperframes_render"
        ]
        render_metrics = render_stages[-1].get("metrics", {}) if render_stages else {}
        if not expected_topic or str(summary.get("topic", "")).casefold() != str(expected_topic).casefold():
            raise RuntimeError("The completed render does not match the topic in the supplied Production IR.")
        if summary.get("final_video_path") != "renders/final.mp4":
            raise RuntimeError("The production summary does not identify its canonical final video.")
        if metrics.get("format") != ir.aspect_ratio:
            raise RuntimeError("The completed render aspect ratio does not match the supplied Production IR.")
        if abs(float(metrics.get("target_duration_seconds", 0.0)) - float(ir.duration_seconds)) > 0.01:
            raise RuntimeError("The completed render duration does not match the supplied Production IR.")
        if render_metrics.get("validation_status") != "VERIFIED" or render_metrics.get("gate_passed") is not True:
            raise RuntimeError("The production summary does not contain a passing measured render gate.")
        if not candidate.is_file() or candidate.stat().st_size == 0:
            raise FileNotFoundError(
                "The successful production summary points to a missing or empty final video."
            )

        if ir.aspect_ratio not in {"16:9", "9:16"}:
            raise ValueError(f"Unsupported render aspect ratio: {ir.aspect_ratio!r}")
        if ir.duration_seconds <= 0 or ir.fps <= 0:
            raise ValueError("Production IR must specify a positive duration and frame rate.")

        width, height = (1920, 1080) if ir.aspect_ratio == "16:9" else (1080, 1920)
        expected = ExpectedMedia(
            duration=float(ir.duration_seconds),
            width=width,
            height=height,
            fps=float(ir.fps),
            require_audio=True,
        )
        gate = MediaGate()
        report = gate.enforce(candidate, expected=expected)

        output_dir.mkdir(parents=True, exist_ok=True)
        video_target = output_dir / "final.mp4"
        if candidate.resolve() != video_target.resolve():
            shutil.copy2(candidate, video_target)
            report = gate.enforce(video_target, expected=expected)

        measured = gate.probe_summary(video_target)
        if not measured.get("has_video") or not measured.get("has_audio"):
            raise RuntimeError("The delivered render is missing a measured video or audio stream.")
        container = report.metrics.get("container", {})
        video_stream = container.get("video") or {}
        audio_stream = container.get("audio") or {}

        return RenderArtifact(
            video_path=str(video_target.resolve()),
            duration_seconds=float(measured.get("duration") or 0.0),
            file_size_bytes=video_target.stat().st_size,
            width=int(measured.get("width") or 0),
            height=int(measured.get("height") or 0),
            fps=int(round(measured.get("fps") or 0)),
            video_codec=str(video_stream.get("codec_name") or "unknown"),
            audio_codec=str(audio_stream.get("codec_name") or "unknown"),
            validation_status="VERIFIED",
        )

    def run_full_production(
        self,
        brief: ContentBrief,
        session_id: str,
    ) -> ProductionResult:
        """Execute full 17-state autonomous production pipeline."""
        start_time = time.time()
        ws = self._get_session_workspace(session_id)
        renders_dir = self._get_session_renders(session_id)

        from src.orchestrator.state_machine import (
            ProductionState,
            ProductionStateMachine,
        )
        from src.orchestrator.pipeline import Pipeline

        sm = ProductionStateMachine(run_id=brief.project_id)

        try:
            # 1. State: CREATED -> RESEARCH_PLANNED
            sm.transition_to(
                ProductionState.RESEARCH_PLANNED,
                payload={"topic": brief.topic, "brief": brief.to_dict()},
            )

            # 2. State: RESEARCH_PLANNED -> RESEARCH_IN_PROGRESS
            sm.transition_to(
                ProductionState.RESEARCH_IN_PROGRESS,
                payload={"search_mode": "offline" if brief.offline_mode else "online"},
            )

            # Execute pipeline
            pipeline = Pipeline(
                topic=brief.topic,
                output_dir=ws,
                offline=brief.offline_mode,
                format=brief.aspect_ratio,
                duration=brief.target_duration_seconds,
            )

            success = pipeline.run()

            if not success:
                sm.transition_to(
                    ProductionState.FAILED,
                    payload={"error": "Pipeline execution failed"},
                )
                return ProductionResult(
                    success=False,
                    project_id=brief.project_id,
                    session_id=session_id,
                    error_message="Pipeline execution returned failure status",
                    state_history=_canonical_state_history(sm),
                    elapsed_seconds=round(time.time() - start_time, 2),
                )

            # A pipeline that claims success but left no video at the canonical path has failed.
            source_video = ws / "renders" / "final.mp4"
            if not source_video.exists():
                sm.transition_to(
                    ProductionState.FAILED,
                    payload={"error": "Pipeline reported success but renders/final.mp4 does not exist"},
                )
                return ProductionResult(
                    success=False,
                    project_id=brief.project_id,
                    session_id=session_id,
                    error_message="Pipeline reported success but produced no video (renders/final.mp4 is missing)",
                    state_history=_canonical_state_history(sm),
                    elapsed_seconds=round(time.time() - start_time, 2),
                )
            render_stage = _render_stage_metrics(ws)

            # Advance state machine through canonical lifecycle milestones
            sm.transition_to(ProductionState.RESEARCH_COMPLETED)
            sm.transition_to(ProductionState.EDITORIAL_ANALYSIS)
            sm.transition_to(ProductionState.ANGLE_SELECTED)
            sm.transition_to(ProductionState.OUTLINE_APPROVED)
            sm.transition_to(ProductionState.SCRIPTING_IN_PROGRESS)
            sm.transition_to(ProductionState.SCRIPT_COMPLETED)
            sm.transition_to(ProductionState.VOICE_GENERATED)
            sm.transition_to(ProductionState.VOICE_QA_PASSED)
            sm.transition_to(ProductionState.ASSETS_DISCOVERED)
            sm.transition_to(ProductionState.ASSETS_FROZEN)
            sm.transition_to(ProductionState.COMPOSITION_GENERATED)
            sm.transition_to(ProductionState.RENDER_IN_PROGRESS)
            sm.transition_to(ProductionState.RENDER_COMPLETED)
            sm.transition_to(ProductionState.COMPLETED)

            # Copy rendered MP4 to session renders directory
            target_video = renders_dir / "final.mp4"
            shutil.copy2(source_video, target_video)

            # Measure the delivered file; nothing below is assumed from the brief.
            width = 1920 if brief.aspect_ratio == "16:9" else 1080
            height = 1080 if brief.aspect_ratio == "16:9" else 1920
            evaluation_report = evaluate_render(
                target_video,
                run_id=f"eval_{session_id}_{int(time.time())}",
                expected=ExpectedMedia(
                    duration=float(brief.target_duration_seconds), width=width, height=height, fps=30,
                    require_audio=True,
                ),
                notes=(
                    ["Render backend was 'stub': placeholder frames, NOT a real video."]
                    if render_stage.get("validation_status") == "STUB" else None
                ),
            )
            measured = MediaGate().probe_summary(target_video)

            render_artifact = RenderArtifact(
                video_path=str(target_video.resolve()),
                duration_seconds=float(measured.get("duration") or 0.0),
                file_size_bytes=target_video.stat().st_size,
                width=int(measured.get("width") or width),
                height=int(measured.get("height") or height),
                fps=int(round(measured.get("fps") or 30)),
                validation_status=str(render_stage.get("validation_status") or "UNVERIFIED"),
            )

            # Build PublishPackage
            publish_package = PublishPackage(
                project_id=brief.project_id,
                title=f"Video: {brief.topic}",
                description=f"Generated video on {brief.topic} for session {session_id}",
                tags=[brief.topic, "Harness9", "HermesAgent"],
                video_path=render_artifact.video_path,
                total_cost_usd=0.0,
            )

            elapsed = round(time.time() - start_time, 2)

            canonical_history = _canonical_state_history(sm)

            return ProductionResult(
                success=True,
                project_id=brief.project_id,
                session_id=session_id,
                video_path=render_artifact.video_path,
                render_artifact=render_artifact,
                publish_package=publish_package,
                evaluation_report=evaluation_report,
                state_history=canonical_history,
                elapsed_seconds=elapsed,
            )

        except Exception as exc:
            logger.exception(f"run_full_production failed: {exc}")
            if sm.current_state != ProductionState.FAILED and sm.can_transition(ProductionState.FAILED):
                sm.transition_to(
                    ProductionState.FAILED,
                    payload={"exception": str(exc)},
                )
            canonical_history = _canonical_state_history(sm)
            return ProductionResult(
                success=False,
                project_id=brief.project_id,
                session_id=session_id,
                error_message=str(exc),
                state_history=canonical_history,
                elapsed_seconds=round(time.time() - start_time, 2),
            )
