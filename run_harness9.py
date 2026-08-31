#!/usr/bin/env python3
"""
run_harness9.py — Root Entrypoint for Harness 9 Video Generation Engine.

Usage:
    python run_harness9.py --topic "The History of the Transistor" --format 16:9 --duration 30
    python run_harness9.py --topic "How GPUs Work" --format 9:16 --output-dir output/gpu_video
"""

import sys
from src.orchestrator.cli import main

if __name__ == "__main__":
    sys.exit(main())
