"""
src.orchestrator.pipeline — End-to-End Orchestrator Pipeline for Harness 9 (Milestone 5 - F11).

Orchestrates all 5 stages from a topic brief to a rendered broadcast MP4 video:
- Stage 1: Research & Fact Synthesis (ResearchEngine -> research_dossier.json/.yaml)
- Stage 2: Asset Discovery & Rights Ledger (AssetPipeline -> asset_ledger.json/.yaml + assets/images/*)
- Stage 3: Script, Storyboard & TTS Voiceover (ScriptwritingPipeline -> BRIEF.md, DESIGN.md, SCRIPT.md, STORYBOARD.md, assets/audio/narration.wav, assets/transcript.json)
- Stage 4: HyperFrames Composition & Video Rendering (HyperFramesGenerator + HyperFramesRenderer -> index.html, styles.css, main.js, renders/final.mp4)
- Stage 5: Summary Reporting (PipelineSummary -> pipeline_summary.json/.yaml)
"""

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from src.assets.pipeline import AssetPipeline
from src.hyperframes.generator import HyperFramesGenerator
from src.evaluation.media_gate import MediaGateError
from src.hyperframes.browser_capture import BrowserCaptureError, RenderUnavailableError
from src.hyperframes.renderer import HyperFramesRenderer
from src.utils.ffmpeg import FFmpegError
from src.models.dossier import ResearchDossier
from src.models.ledger import AssetProvenanceLedger
from src.models.summary import PipelineSummary, StageResult
from src.research.engine import ResearchEngine
from src.scriptwriting.pipeline import ScriptwritingPipeline
from src.utils.filesystem import atomic_write, ensure_dir

logger = logging.getLogger("harness9.orchestrator.pipeline")


def _audio_duration_tolerance(target_duration: float) -> float:
    """Allow small TTS timing variance without accepting materially clipped audio."""
    return max(1.0, float(target_duration) * 0.10)


class Pipeline:
    """Master Pipeline Orchestrator executing Stages 1 through 5."""

    def __init__(
        self,
        topic: str,
        output_dir: Union[str, Path],
        offline: bool = True,
        format: str = "16:9",
        duration: int = 30,
        voice: str = "default",
        quality: str = "standard",
        model_assisted_scripts: bool = False,
        online_assets: bool = False,
        **kwargs: Any,
    ):
        self.topic = topic.strip() if topic else "Technology Overview"
        self.output_dir = Path(output_dir).resolve()
        self.offline = bool(offline)
        self.format = format if format in ["16:9", "9:16"] else "16:9"
        self.duration = max(1, int(duration))
        self.voice = voice or "default"
        self.quality = quality or "standard"
        self.model_assisted_scripts = bool(model_assisted_scripts)
        self.online_assets = bool(online_assets)
        self.render_backend: Optional[str] = kwargs.get("render_backend")
        self.extra_kwargs = kwargs

    def run(self) -> bool:
        """
        Execute the end-to-end pipeline and generate all artifacts and summary reports.
        Returns True on success, False on unrecoverable failure.
        """
        run_id = f"run_{int(time.time())}_{self.topic[:16].replace(' ', '_').lower()}"
        start_ts = datetime.now(timezone.utc).isoformat()
        start_time = time.time()
        stage_results: List[StageResult] = []

        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        images_dir = self.output_dir / "assets" / "images"
        audio_dir = self.output_dir / "assets" / "audio"
        renders_dir = self.output_dir / "renders"
        images_dir.mkdir(parents=True, exist_ok=True)
        audio_dir.mkdir(parents=True, exist_ok=True)
        renders_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Starting Harness 9 Pipeline Run [{run_id}] for topic: '{self.topic}'")

        # --------------------------------------------------------------------
        # Stage 1: Research & Fact Synthesis
        # --------------------------------------------------------------------
        t0 = time.time()
        try:
            research_engine = ResearchEngine()
            dossier = research_engine.synthesize_research(
                topic=self.topic,
                offline=self.offline,
                target_duration=self.duration,
            )
            # Save research dossier
            dossier.save(self.output_dir, base_name="research_dossier")
            t_dur = time.time() - t0
            stage_results.append(StageResult(
                stage_name="research",
                success=True,
                execution_time_seconds=t_dur,
                artifacts=["research_dossier.json", "research_dossier.yaml"],
                metrics={
                    "claims_count": len(dossier.claims),
                    "unverified_claims": sum(1 for claim in dossier.claims if claim.verification_status != "VERIFIED"),
                    "talking_points_count": len(dossier.talking_points),
                },
            ))
            logger.info(f"Stage 1 (Research) completed in {t_dur:.2f}s with {len(dossier.claims)} claims.")
        except Exception as e:
            t_dur = time.time() - t0
            logger.error(f"Stage 1 (Research) failed: {e}")
            stage_results.append(StageResult(
                stage_name="research",
                success=False,
                execution_time_seconds=t_dur,
                error=str(e),
            ))
            self._write_summary(run_id, start_ts, start_time, "FAILED", stage_results)
            return False

        # --------------------------------------------------------------------
        # Stage 2: Asset Discovery, Rights Ledger & Local Freezing
        # --------------------------------------------------------------------
        t0 = time.time()
        try:
            asset_pipeline = AssetPipeline()
            ledger = asset_pipeline.discover_and_freeze_assets(
                dossier=dossier,
                output_dir=self.output_dir,
                offline=self.offline and not self.online_assets,
                format_aspect=self.format,
            )
            t_dur = time.time() - t0
            asset_files = [a.local_path for a in ledger.assets if a.local_path]
            stage_results.append(StageResult(
                stage_name="assets",
                success=True,
                execution_time_seconds=t_dur,
                artifacts=["asset_ledger.json", "asset_ledger.yaml"] + asset_files,
                metrics={
                    "total_assets": ledger.total_assets,
                    "fallback_generated_assets": sum(1 for asset in ledger.assets if asset.verification_status == "FALLBACK_GENERATED"),
                    "frozen_source_assets": sum(1 for asset in ledger.assets if asset.verification_status == "FROZEN_LOCAL"),
                    "licenses": ledger.license_summary,
                },
            ))
            logger.info(f"Stage 2 (Assets) completed in {t_dur:.2f}s with {ledger.total_assets} frozen assets.")
        except Exception as e:
            t_dur = time.time() - t0
            logger.error(f"Stage 2 (Assets) failed: {e}")
            stage_results.append(StageResult(
                stage_name="assets",
                success=False,
                execution_time_seconds=t_dur,
                error=str(e),
            ))
            self._write_summary(run_id, start_ts, start_time, "FAILED", stage_results)
            return False

        # --------------------------------------------------------------------
        # Stage 3: Script, Storyboard & TTS Voiceover
        # --------------------------------------------------------------------
        t0 = time.time()
        try:
            script_pipeline = ScriptwritingPipeline()
            script_res = script_pipeline.run(
                dossier=dossier,
                ledger=ledger,
                output_dir=self.output_dir,
                target_duration=float(self.duration),
                voice=self.voice,
                format_aspect=self.format,
                model_assisted=self.model_assisted_scripts,
            )
            audio_duration = float(script_res.audio.duration_seconds)
            if script_res.audio.provider_used == "harmonic_synthesizer":
                raise ValueError(
                    "TTS produced a synthetic tone track, not intelligible speech. "
                    "Configure Windows SAPI or ElevenLabs before rendering a beta video."
                )
            audio_tolerance = _audio_duration_tolerance(float(self.duration))
            if audio_duration > float(self.duration) + 0.01:
                raise ValueError(
                    f"Narration audio is {audio_duration:.1f}s for a {self.duration:.1f}s target. "
                    "Refusing to render because the video would truncate the narration."
                )
            if float(self.duration) - audio_duration > audio_tolerance:
                raise ValueError(
                    f"Narration audio is {audio_duration:.1f}s for a {self.duration:.1f}s target "
                    f"(allowed early ending {audio_tolerance:.1f}s). Refusing to render a video "
                    "with a materially silent tail."
                )
            t_dur = time.time() - t0
            stage_results.append(StageResult(
                stage_name="script_voiceover",
                success=True,
                execution_time_seconds=t_dur,
                artifacts=[
                    "BRIEF.md",
                    "DESIGN.md",
                    "SCRIPT.md",
                    "STORYBOARD.md",
                    "assets/audio/narration.wav",
                    "assets/transcript.json",
                ],
                metrics={
                    "scenes_count": len(script_res.storyboard),
                    "audio_duration": script_res.audio.duration_seconds,
                    "audio_provider": script_res.audio.provider_used,
                    "narration_provider": script_res.narration_provider,
                },
            ))
            logger.info(f"Stage 3 (Script & Audio) completed in {t_dur:.2f}s with {len(script_res.storyboard)} scenes.")
        except Exception as e:
            t_dur = time.time() - t0
            logger.error(f"Stage 3 (Script & Audio) failed: {e}")
            expected_artifacts = [
                "BRIEF.md",
                "DESIGN.md",
                "SCRIPT.md",
                "STORYBOARD.md",
                "script.json",
                "script.yaml",
                "assets/audio/narration.wav",
                "assets/transcript.json",
                "transcript.json",
            ]
            existing_artifacts = [
                artifact
                for artifact in expected_artifacts
                if (self.output_dir / artifact).is_file()
            ]
            stage_results.append(StageResult(
                stage_name="script_voiceover",
                success=False,
                execution_time_seconds=t_dur,
                artifacts=existing_artifacts,
                error=str(e),
            ))
            self._write_summary(run_id, start_ts, start_time, "FAILED", stage_results)
            return False

        # --------------------------------------------------------------------
        # Stage 4: HyperFrames Composition & Video Rendering
        # --------------------------------------------------------------------
        t0 = time.time()
        try:
            hf_generator = HyperFramesGenerator(format_aspect=self.format, fps=30)
            hf_generator.generate_composition(
                topic=self.topic,
                storyboard=script_res.storyboard,
                output_dir=self.output_dir,
                duration=float(self.duration),
                audio_rel_path="assets/audio/narration.wav",
                transcript=script_res.transcript,
                brand=script_res.brand,
            )

            hf_renderer = HyperFramesRenderer(fps=30, quality=self.quality, backend=self.render_backend)
            render_res = hf_renderer.render(
                project_dir=self.output_dir,
                output_mp4=self.output_dir / "renders" / "final.mp4",
                duration=float(self.duration),
            )
            t_dur = time.time() - t0
            gate = (render_res.gate or {}).get("metrics", {})
            rel_video = Path(render_res.output_path).resolve().relative_to(self.output_dir).as_posix()
            artifacts = ["index.html", "styles.css", "main.js", rel_video]
            if render_res.gate is not None:
                artifacts.append("renders/final.gate.json")
            stage_results.append(StageResult(
                stage_name="hyperframes_render",
                success=True,
                execution_time_seconds=t_dur,
                artifacts=artifacts,
                metrics={
                    "video_duration": render_res.duration_seconds,
                    "video_size_bytes": render_res.file_size_bytes,
                    "width": render_res.width,
                    "height": render_res.height,
                    "fps": render_res.fps,
                    "backend": render_res.backend,
                    "validation_status": render_res.validation_status,
                    "frames_captured": render_res.frames_captured,
                    "gate_passed": None if render_res.gate is None else bool(render_res.gate.get("passed")),
                    "measured": {k: gate[k] for k in (
                        "flat_frame_ratio", "edge_density", "motion_ratio", "frozen_ratio", "black_ratio",
                        "mean_volume_db", "integrated_lufs", "silence_ratio",
                    ) if k in gate},
                    "warnings": list(render_res.warnings),
                },
            ))
            logger.info(f"Stage 4 (HyperFrames Render) completed in {t_dur:.2f}s [{render_res.backend}/"
                        f"{render_res.validation_status}]: {render_res.output_path}")
            for warning in render_res.warnings:
                logger.warning(f"Stage 4 warning: {warning}")
            final_rel_video = rel_video
            narration_truncated = script_res.audio.duration_seconds > render_res.duration_seconds + 0.01
            if narration_truncated:
                run_status = "FAILED"
            else:
                has_generated_assets = any(
                    asset.verification_status == "FALLBACK_GENERATED"
                    for asset in ledger.assets
                )
                has_unverified_claims = any(
                    claim.verification_status != "VERIFIED"
                    for claim in dossier.claims
                )
                run_status = (
                    "SUCCESS"
                    if render_res.validation_status == "VERIFIED"
                    and not has_generated_assets
                    and not has_unverified_claims
                    else "PARTIAL"
                )
        except (RenderUnavailableError, BrowserCaptureError, FFmpegError, MediaGateError) as e:
            # Expected, actionable failures: report them as they are. No placeholder video is produced.
            t_dur = time.time() - t0
            logger.error(f"Stage 4 (HyperFrames Render) failed: {e}")
            failed_artifacts: List[str] = []
            if isinstance(e, MediaGateError):
                failed_artifacts = ["renders/final.rejected.mp4", "renders/final.gate.json"]
            stage_results.append(StageResult(
                stage_name="hyperframes_render",
                success=False,
                execution_time_seconds=t_dur,
                artifacts=failed_artifacts,
                error=f"{type(e).__name__}: {e}",
                metrics={"failure_kind": type(e).__name__},
            ))
            self._write_summary(run_id, start_ts, start_time, "FAILED", stage_results)
            return False
        except Exception as e:
            t_dur = time.time() - t0
            logger.error(f"Stage 4 (HyperFrames Render) failed: {e}")
            stage_results.append(StageResult(
                stage_name="hyperframes_render",
                success=False,
                execution_time_seconds=t_dur,
                error=str(e),
            ))
            self._write_summary(run_id, start_ts, start_time, "FAILED", stage_results)
            return False

        # --------------------------------------------------------------------
        # Stage 5: Summary Report & Finalization
        # --------------------------------------------------------------------
        self._write_summary(
            run_id=run_id,
            start_ts=start_ts,
            start_time=start_time,
            status=run_status,
            stage_results=stage_results,
            final_video_path=final_rel_video,
        )
        if run_status == "SUCCESS":
            logger.info(f"Harness 9 Pipeline Run [{run_id}] completed successfully!")
        elif run_status == "FAILED":
            logger.error(f"Harness 9 Pipeline Run [{run_id}] failed: narration did not fit the rendered video.")
        else:
            logger.warning(
                f"Harness 9 Pipeline Run [{run_id}] finished as {run_status}: "
                "review the stage metrics for unverified claims or generated fallback visuals."
            )
        return run_status == "SUCCESS"

    def _write_summary(
        self,
        run_id: str,
        start_ts: str,
        start_time: float,
        status: str,
        stage_results: List[StageResult],
        final_video_path: Optional[str] = None,
    ) -> PipelineSummary:
        """Collate and write dual pipeline_summary.json and .yaml."""
        end_ts = datetime.now(timezone.utc).isoformat()
        total_dur = time.time() - start_time

        summary = PipelineSummary(
            schema_version="1.0.0",
            run_id=run_id,
            topic=self.topic,
            start_time=start_ts,
            end_time=end_ts,
            total_duration_seconds=round(total_dur, 3),
            status=status,
            stages=stage_results,
            output_directory=str(self.output_dir),
            final_video_path=final_video_path,
            metrics={
                "format": self.format,
                "target_duration_seconds": self.duration,
                "offline_mode": self.offline,
                "research_mode": "curated" if self.offline else "online",
                "asset_mode": "online" if (not self.offline or self.online_assets) else "offline",
                "online_assets": not self.offline or self.online_assets,
                "model_assisted_scripts": self.model_assisted_scripts,
                "voice": self.voice,
                "render_backend": self.render_backend or "default",
            },
        )
        summary.save(self.output_dir, base_name="pipeline_summary")
        return summary


def run_pipeline(
    topic: str,
    output_dir: Union[str, Path],
    offline: bool = True,
    format: str = "16:9",
    duration: int = 30,
    voice: str = "default",
    **kwargs: Any,
) -> bool:
    """Convenience functional wrapper to execute Pipeline."""
    p = Pipeline(
        topic=topic,
        output_dir=output_dir,
        offline=offline,
        format=format,
        duration=duration,
        voice=voice,
        **kwargs,
    )
    return p.run()
