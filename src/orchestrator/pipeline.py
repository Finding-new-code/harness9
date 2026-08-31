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
from src.hyperframes.renderer import HyperFramesRenderer
from src.models.dossier import ResearchDossier
from src.models.ledger import AssetProvenanceLedger
from src.models.summary import PipelineSummary, StageResult
from src.research.engine import ResearchEngine
from src.scriptwriting.pipeline import ScriptwritingPipeline
from src.utils.filesystem import atomic_write, ensure_dir

logger = logging.getLogger("harness9.orchestrator.pipeline")


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
        **kwargs: Any,
    ):
        self.topic = topic.strip() if topic else "Technology Overview"
        self.output_dir = Path(output_dir).resolve()
        self.offline = bool(offline)
        self.format = format if format in ["16:9", "9:16"] else "16:9"
        self.duration = max(1, int(duration))
        self.voice = voice or "default"
        self.quality = quality or "standard"
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
                metrics={"claims_count": len(dossier.claims), "talking_points_count": len(dossier.talking_points)},
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
                offline=self.offline,
                format_aspect=self.format,
            )
            t_dur = time.time() - t0
            asset_files = [a.local_path for a in ledger.assets if a.local_path]
            stage_results.append(StageResult(
                stage_name="assets",
                success=True,
                execution_time_seconds=t_dur,
                artifacts=["asset_ledger.json", "asset_ledger.yaml"] + asset_files,
                metrics={"total_assets": ledger.total_assets, "licenses": ledger.license_summary},
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
                },
            ))
            logger.info(f"Stage 3 (Script & Audio) completed in {t_dur:.2f}s with {len(script_res.storyboard)} scenes.")
        except Exception as e:
            t_dur = time.time() - t0
            logger.error(f"Stage 3 (Script & Audio) failed: {e}")
            stage_results.append(StageResult(
                stage_name="script_voiceover",
                success=False,
                execution_time_seconds=t_dur,
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

            hf_renderer = HyperFramesRenderer(fps=30, quality=self.quality)
            render_res = hf_renderer.render(
                project_dir=self.output_dir,
                output_mp4=self.output_dir / "renders" / "final.mp4",
                duration=float(self.duration),
            )
            t_dur = time.time() - t0
            stage_results.append(StageResult(
                stage_name="hyperframes_render",
                success=True,
                execution_time_seconds=t_dur,
                artifacts=[
                    "index.html",
                    "styles.css",
                    "main.js",
                    "renders/final.mp4",
                ],
                metrics={
                    "video_duration": render_res.duration_seconds,
                    "video_size_bytes": render_res.file_size_bytes,
                    "width": render_res.width,
                    "height": render_res.height,
                    "fps": render_res.fps,
                },
            ))
            logger.info(f"Stage 4 (HyperFrames Render) completed in {t_dur:.2f}s: {render_res.output_path}")
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
            status="SUCCESS",
            stage_results=stage_results,
            final_video_path="renders/final.mp4",
        )
        logger.info(f"Harness 9 Pipeline Run [{run_id}] completed successfully!")
        return True

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
                "voice": self.voice,
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
