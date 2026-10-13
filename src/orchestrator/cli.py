"""
src.orchestrator.cli — Command-Line Interface for Harness 9 Unified Pipeline (Milestone 5 - F11).

Usage:
    python -m src.orchestrator.cli --topic "The History of the Transistor" --duration 30 --format 16:9
    python run_harness9.py --topic "How GPUs Work" --output-dir output/gpu_run --offline
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import List, Optional

from src.orchestrator.pipeline import Pipeline, run_pipeline

logger = logging.getLogger("harness9.cli")


def build_parser() -> argparse.ArgumentParser:
    """Construct command-line argument parser for Harness 9."""
    parser = argparse.ArgumentParser(
        prog="hermes-video-generator",
        description="Harness 9: Autonomous End-to-End AI Video Generation Pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--topic", "-t",
        type=str,
        default="The History of the Transistor",
        help="Creator topic brief or subject matter for the video",
    )

    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default=None,
        help="Target output directory for all generated artifacts and renders",
    )

    parser.add_argument(
        "--offline",
        action="store_true",
        default=True,
        help="Use curated research presets, procedural offline visuals, and local text-to-speech",
    )

    parser.add_argument(
        "--online",
        dest="offline",
        action="store_false",
        help="Enable live web research and online asset discovery",
    )

    parser.add_argument(
        "--online-assets",
        action="store_true",
        default=False,
        help="Keep curated offline research but discover and freeze real images online",
    )

    parser.add_argument(
        "--model-script",
        action="store_true",
        default=False,
        help="Use the model selected in Hermes config.yaml to write source-grounded, duration-bounded narration (requires --online or --online-assets)",
    )

    parser.add_argument(
        "--format", "-f",
        choices=["16:9", "9:16"],
        default="16:9",
        help="Target aspect ratio (16:9 landscape or 9:16 vertical short-form)",
    )

    parser.add_argument(
        "--duration", "-d",
        type=int,
        default=30,
        help="Target duration of the video in seconds",
    )

    parser.add_argument(
        "--voice", "-v",
        type=str,
        default="default",
        help="TTS voice model or preset name",
    )

    parser.add_argument(
        "--quality",
        choices=["draft", "standard", "high"],
        default="standard",
        help="Video rendering quality profile",
    )

    parser.add_argument(
        "--render-backend",
        choices=["chrome", "stub"],
        default=None,
        help="chrome = real headless-Chromium render + measured media gate (default, or $HARNESS9_RENDER_BACKEND); "
             "stub = labelled dry run with placeholder frames (never marked VERIFIED)",
    )

    parser.add_argument(
        "--check-render",
        action="store_true",
        default=False,
        help="Report whether the real renderer can run on this machine (Node, Chrome, FFmpeg, toolchain) and exit",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output structured JSON summary to stdout on completion",
    )

    parser.add_argument(
        "--test-mode",
        action="store_true",
        default=False,
        help="Run fast verification pass with minimal duration",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="Harness 9 Video Engine v1.0.0 (HyperFrames)",
    )

    return parser


def main(args: Optional[List[str]] = None) -> int:
    """CLI execution entrypoint."""
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    parser = build_parser()
    parsed_args = parser.parse_args(args)

    if parsed_args.check_render:
        from src.hyperframes.browser_capture import availability

        report = availability()
        print(json.dumps(report, indent=2))
        return 0 if not report["problems"] else 1

    topic = parsed_args.topic.strip()
    if not topic:
        print("Error: --topic must not be empty.", file=sys.stderr)
        return 1

    if parsed_args.duration <= 0:
        print("Error: --duration must be greater than 0.", file=sys.stderr)
        return 1

    if parsed_args.model_script and parsed_args.offline and not parsed_args.online_assets:
        print(
            "Error: --model-script requires --online or --online-assets; offline-only runs make no model calls.",
            file=sys.stderr,
        )
        return 1

    if parsed_args.test_mode:
        duration = min(parsed_args.duration, 5)
    else:
        duration = parsed_args.duration

    if parsed_args.output_dir:
        out_dir = Path(parsed_args.output_dir)
    else:
        timestamp_str = time.strftime("%Y%m%d_%H%M%S")
        slug = "".join(c if c.isalnum() else "_" for c in topic.lower())[:24].strip("_")
        out_dir = Path(f"output/{slug}_{timestamp_str}")

    try:
        pipeline = Pipeline(
            topic=topic,
            output_dir=out_dir,
            offline=parsed_args.offline,
            format=parsed_args.format,
            duration=duration,
            voice=parsed_args.voice,
            quality=parsed_args.quality,
            model_assisted_scripts=parsed_args.model_script,
            online_assets=parsed_args.online_assets,
            render_backend=parsed_args.render_backend,
        )
        success = pipeline.run()

        if parsed_args.json:
            summary_file = out_dir / "pipeline_summary.json"
            if summary_file.exists():
                print(summary_file.read_text(encoding="utf-8"))
            else:
                print(json.dumps({"success": success, "output_directory": str(out_dir)}))

        summary_file = out_dir / "pipeline_summary.json"
        status = "FAILED"
        video = out_dir / "renders" / "final.mp4"
        if summary_file.exists():
            try:
                data = json.loads(summary_file.read_text(encoding="utf-8"))
                status = data.get("status", status)
                video = out_dir / (data.get("final_video_path") or "renders/final.mp4")
            except (OSError, ValueError):
                pass
        if status == "SUCCESS":
            print("\n[SUCCESS] Video generated and verified by the media gate.")
            print(f"Artifacts and summary written to: {out_dir}")
            print(f"Rendered video: {video}")
            return 0
        if status == "PARTIAL":
            print("\n[PARTIAL] Real video rendered and measured; review unverified claims or fallback visuals in the summary.", file=sys.stderr)
            print(f"Artifacts and summary written to: {out_dir}")
            print(f"Rendered video: {video}")
            return 2

        print("\n[FAILED] Pipeline execution failed. See logs for details.", file=sys.stderr)
        if summary_file.exists():
            try:
                data = json.loads(summary_file.read_text(encoding="utf-8"))
                for stage in data.get("stages", []):
                    if not stage.get("success") and stage.get("error"):
                        print(f"  {stage['stage_name']}: {stage['error']}", file=sys.stderr)
            except (OSError, ValueError):
                pass
        return 1
    except Exception as e:
        logger.exception(f"Unhandled pipeline exception: {e}")
        if parsed_args.json:
            print(json.dumps({"success": False, "error": str(e)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
