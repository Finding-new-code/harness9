"""Global configuration, paths, and environment settings for Harness 9."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Standard Directory Paths
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output"
DEFAULT_ASSETS_DIR = PROJECT_ROOT / "assets"
DEFAULT_RENDERS_DIR = PROJECT_ROOT / "renders"
RESEARCH_PRESETS_DIR = PROJECT_ROOT / "src" / "research" / "presets"

# Pipeline Defaults
DEFAULT_VIDEO_WIDTH = 1920
DEFAULT_VIDEO_HEIGHT = 1080
DEFAULT_VIDEO_FPS = 30
DEFAULT_TARGET_DURATION_SEC = 30
DEFAULT_AUDIO_SAMPLE_RATE = 44100
DEFAULT_WORDS_PER_SECOND = 2.5

# Search & Research Defaults
DEFAULT_SEARCH_TIMEOUT_SEC = 10
DEFAULT_MAX_SEARCH_RESULTS = 5
DEFAULT_MIN_CLAIMS = 3

# Confidence Scoring Weights
CONFIDENCE_WEIGHT_AUTHORITY = 0.40
CONFIDENCE_WEIGHT_CORROBORATION = 0.35
CONFIDENCE_WEIGHT_CLARITY = 0.25

# API Keys & Secrets (read from environment variables)
def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """Retrieve environment variable value with fallback."""
    return os.environ.get(key, default)


@dataclass
class AppConfig:
    """Centralized runtime application configuration."""
    project_root: Path = PROJECT_ROOT
    output_dir: Path = DEFAULT_OUTPUT_DIR
    presets_dir: Path = RESEARCH_PRESETS_DIR
    offline_mode: bool = False
    target_duration: int = DEFAULT_TARGET_DURATION_SEC
    video_width: int = DEFAULT_VIDEO_WIDTH
    video_height: int = DEFAULT_VIDEO_HEIGHT
    video_fps: int = DEFAULT_VIDEO_FPS
    audio_sample_rate: int = DEFAULT_AUDIO_SAMPLE_RATE
    search_timeout_sec: int = DEFAULT_SEARCH_TIMEOUT_SEC
    max_search_results: int = DEFAULT_MAX_SEARCH_RESULTS
    
    # API credentials
    tavily_api_key: Optional[str] = field(default_factory=lambda: get_env_var("TAVILY_API_KEY"))
    exa_api_key: Optional[str] = field(default_factory=lambda: get_env_var("EXA_API_KEY"))
    pexels_api_key: Optional[str] = field(default_factory=lambda: get_env_var("PEXELS_API_KEY"))
    elevenlabs_api_key: Optional[str] = field(default_factory=lambda: get_env_var("ELEVENLABS_API_KEY"))

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary representation (masking sensitive keys)."""
        return {
            "project_root": str(self.project_root),
            "output_dir": str(self.output_dir),
            "presets_dir": str(self.presets_dir),
            "offline_mode": self.offline_mode,
            "target_duration": self.target_duration,
            "video_width": self.video_width,
            "video_height": self.video_height,
            "video_fps": self.video_fps,
            "audio_sample_rate": self.audio_sample_rate,
            "has_tavily_key": bool(self.tavily_api_key),
            "has_exa_key": bool(self.exa_api_key),
            "has_pexels_key": bool(self.pexels_api_key),
            "has_elevenlabs_key": bool(self.elevenlabs_api_key),
        }


def get_default_config() -> AppConfig:
    """Factory helper to obtain standard default config instance."""
    return AppConfig()
