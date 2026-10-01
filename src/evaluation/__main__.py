"""`python -m src.evaluation <video.mp4> [--duration S] [--size WxH] [--fps N] [--json]` runs the media gate."""

from src.evaluation.media_gate import main

raise SystemExit(main())
