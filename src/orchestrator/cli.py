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
        help="Force offline mode using curated presets, procedural SVGs, and deterministic TTS",
    )

    parser.add_argument(
        "--online",
        dest="offline",
        action="store_false",
        help="Enable live web research and online asset discovery",
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

    topic = parsed_args.topic.strip()
    if not topic:
        print("Error: --topic must not be empty.", file=sys.stderr)
        return 1

    if parsed_args.duration <= 0:
        print("Error: --duration must be greater than 0.", file=sys.stderr)
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
        )
        success = pipeline.run()

        if parsed_args.json:
            summary_file = out_dir / "pipeline_summary.json"
            if summary_file.exists():
                print(summary_file.read_text(encoding="utf-8"))
            else:
                print(json.dumps({"success": success, "output_directory": str(out_dir)}))

        if success:
            print(f"\n[SUCCESS] Video generation pipeline completed successfully!")
            print(f"Artifacts and summary written to: {out_dir}")
            print(f"Rendered video: {out_dir / 'renders' / 'final.mp4'}")
            return 0
        else:
            print(f"\n[FAILED] Pipeline execution failed. See logs for details.", file=sys.stderr)
            return 1
    except Exception as e:
        logger.exception(f"Unhandled pipeline exception: {e}")
        if parsed_args.json:
            print(json.dumps({"success": False, "error": str(e)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
