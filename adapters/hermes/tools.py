"""Hermes Model Toolset & Schema Definitions for Harness 9.

Implements service-gated tool definitions conforming to the Hermes Footprint Ladder
and OpenAI function calling standard. Preserves prompt caching by ensuring schemas
are static, deterministic, and free of runtime mutations.
"""

from typing import Any, Callable, Dict, List, Optional
from adapters.hermes.bridge import HermesBridge
from src.utils.ffmpeg import is_ffmpeg_available


def check_harness9_available() -> bool:
    """Service gate check function answering whether Harness 9 is usable on this machine."""
    # Harness 9 supports both system FFmpeg and pure Python procedural/WAV synthesis
    return True


# ===========================================================================
# Tool Schemas (OpenAI / Hermes Standard)
# ===========================================================================
TOOL_GENERATE_VIDEO = {
    "type": "function",
    "function": {
        "name": "generate_video_from_brief",
        "description": "Generate a broadcast-ready rendered MP4 video from a topic brief using the Harness 9 production operating system.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The topic, technology, or narrative subject of the video.",
                },
                "format": {
                    "type": "string",
                    "enum": ["16:9", "9:16"],
                    "default": "16:9",
                    "description": "Target video aspect ratio (16:9 for YouTube/Desktop, 9:16 for Shorts/Reels/TikTok).",
                },
                "duration": {
                    "type": "integer",
                    "default": 30,
                    "description": "Target duration in seconds (between 5 and 300).",
                },
                "offline": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to run in 100% deterministic offline mode using curated benchmarks and procedural generation.",
                },
                "custom_instructions": {
                    "type": "string",
                    "description": "Optional custom creator instructions, specific angles, or narrative constraints.",
                },
            },
            "required": ["topic"],
        },
    },
}

TOOL_INSPECT_STATE = {
    "type": "function",
    "function": {
        "name": "inspect_production_state",
        "description": "Inspect the 17-state lifecycle progress, transition audit logs, and generated artifacts for a video production session.",
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "The session ID of the production run to inspect.",
                },
            },
            "required": ["session_id"],
        },
    },
}

TOOL_EVALUATE_QUALITY = {
    "type": "function",
    "function": {
        "name": "evaluate_content_quality",
        "description": "Run the 4-layer quality evaluation (ContentBench) on the research, script, video, and acoustic integrity of a production session.",
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "The session ID of the production run to evaluate.",
                },
            },
            "required": ["session_id"],
        },
    },
}


def get_tool_schemas() -> List[Dict[str, Any]]:
    """Return static list of all tool schemas provided by the Harness 9 adapter."""
    return [
        TOOL_GENERATE_VIDEO,
        TOOL_INSPECT_STATE,
        TOOL_EVALUATE_QUALITY,
    ]


def get_harness9_toolsets() -> Dict[str, Any]:
    """Return toolset mapping for Hermes toolset configuration."""
    return {
        "name": "harness9_video",
        "description": "Autonomous video production OS toolset",
        "check_fn": check_harness9_available,
        "tools": [
            "generate_video_from_brief",
            "inspect_production_state",
            "evaluate_content_quality",
        ],
        "schemas": get_tool_schemas(),
    }


# ===========================================================================
# Tool Execution Dispatcher
# ===========================================================================
def handle_tool_call(
    tool_name: str,
    arguments: Dict[str, Any],
    session_id: str,
    bridge: Optional[HermesBridge] = None,
) -> Dict[str, Any]:
    """Dispatch and execute a tool call requested by a Hermes agent."""
    if not check_harness9_available():
        return {
            "success": False,
            "error": "Harness 9 service is currently unavailable.",
        }

    b = bridge or HermesBridge()

    if tool_name == "generate_video_from_brief":
        topic = arguments.get("topic", "")
        fmt = arguments.get("format", "16:9")
        duration = int(arguments.get("duration", 30))
        offline = bool(arguments.get("offline", True))
        custom_instructions = arguments.get("custom_instructions")
        
        return b.run_production(
            session_id=session_id,
            topic=topic,
            format=fmt,
            duration=duration,
            offline=offline,
            custom_instructions=custom_instructions,
        )

    elif tool_name == "inspect_production_state":
        target_session = arguments.get("session_id", session_id)
        return b.inspect_session(session_id=target_session)

    elif tool_name == "evaluate_content_quality":
        target_session = arguments.get("session_id", session_id)
        return b.evaluate_session(session_id=target_session)

    else:
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}",
        }
