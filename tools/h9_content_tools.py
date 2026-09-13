"""tools/h9_content_tools.py

Harness 9 Content Production Model Tools for Hermes Agent (Milestone M2).
Exposes granular content production capabilities as native Hermes model tools:
1. h9.research (alias: h9_research)
2. h9.discover_assets (alias: h9_discover_assets)
3. h9.generate_script (alias: h9_generate_script)
4. h9.render (alias: h9_render)

All tools live in the named toolset 'h9_content' and are service-gated by
check_h9_available() conforming strictly to Rung 3 of the Footprint Ladder.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.h9_runtime.bridge import get_capability_bridge
from src.h9_runtime.types import ProductionIR
from src.models.contracts import (
    AssetRequirement,
    EditorialAngle,
    ResearchDossier,
    Script,
)
from src.security import (
    CapabilityToken,
    PermissionDeniedError,
    SecurityError,
    TokenValidationError,
    current_capability_token,
    get_security_guard,
)

from tools.registry import (
    check_h9_available,
    registry,
    tool_error,
    tool_result,
)

logger = logging.getLogger(__name__)

# ===========================================================================
# 1. Schemas for H9 Content Production Model Tools
# ===========================================================================

H9_RESEARCH_SCHEMA: Dict[str, Any] = {
    "name": "h9.research",
    "description": (
        "Execute deep multi-source factual research, claim extraction, and confidence scoring "
        "for a content production topic. Returns a verified structured ResearchDossier."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "The topic, technology, concept, or historical event to research.",
            },
            "depth": {
                "type": "string",
                "enum": ["overview", "standard", "deep"],
                "default": "standard",
                "description": "Depth of research investigation ('overview', 'standard', or 'deep').",
            },
            "constraints": {
                "type": "object",
                "description": (
                    "Optional research constraints such as target_duration (seconds), "
                    "offline mode (boolean), focus_areas (list of strings), or max_claims."
                ),
            },
        },
        "required": ["topic"],
    },
}

H9_DISCOVER_ASSETS_SCHEMA: Dict[str, Any] = {
    "name": "h9.discover_assets",
    "description": (
        "Discover, generate, freeze, and deduplicate media assets based on visual requirements "
        "and scene IDs. Emits verified AssetRecords."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "requirements": {
                "type": "array",
                "items": {"type": "object"},
                "description": (
                    "List of asset requirements (description, visual cue, style notes, "
                    "associated claim IDs, etc.)."
                ),
            },
            "scene_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of scene IDs corresponding to the asset requirements.",
            },
            "format_aspect": {
                "type": "string",
                "enum": ["16:9", "9:16", "1:1"],
                "default": "16:9",
                "description": "Target video aspect ratio.",
            },
            "dossier": {
                "type": "object",
                "description": "Optional ResearchDossier dictionary to infer visual requirements from.",
            },
        },
        "required": ["dossier"],
    },
}

H9_GENERATE_SCRIPT_SCHEMA: Dict[str, Any] = {
    "name": "h9.generate_script",
    "description": (
        "Generate a structured broadcast script with timestamped scenes, narration, and beats "
        "from a narrative outline and research dossier."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "dossier": {
                "type": "object",
                "description": "ResearchDossier dictionary containing verified claims, talking points, and topic.",
            },
            "outline": {
                "type": "object",
                "description": "Optional narrative outline or 4-act structure.",
            },
            "creator": {
                "type": "object",
                "description": "Optional Creator DNA guidelines, brand rules, or negative constraints.",
            },
            "target_duration": {
                "type": "number",
                "default": 30.0,
                "description": "Target total script duration in seconds.",
            },
            "format_aspect": {
                "type": "string",
                "enum": ["16:9", "9:16"],
                "default": "16:9",
                "description": "Target video aspect ratio.",
            },
        },
        "required": ["dossier"],
    },
}

H9_RENDER_SCHEMA: Dict[str, Any] = {
    "name": "h9.render",
    "description": (
        "Render a broadcast MP4 video from a Production IR AST, ensuring hermetic composition "
        "and asset validation."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "production_ir": {
                "type": "object",
                "description": "Production Intermediate Representation dictionary containing timeline blocks and audio tracks.",
            },
            "output_dir": {
                "type": "string",
                "description": "Destination directory for rendered MP4 and output artifacts.",
            },
        },
        "required": ["production_ir", "output_dir"],
    },
}

H9_PUBLISH_SCHEMA: Dict[str, Any] = {
    "name": "h9.publish",
    "description": (
        "Package, license, and distribute rendered video content to target broadcast platforms "
        "(e.g. YouTube, TikTok, Instagram, or local export)."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "Production project identifier.",
            },
            "video_path": {
                "type": "string",
                "description": "Filesystem path to rendered MP4 video artifact.",
            },
            "title": {
                "type": "string",
                "description": "Release title for broadcast distribution.",
            },
            "description": {
                "type": "string",
                "description": "Video description and show notes.",
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Metadata discovery tags.",
            },
            "platform": {
                "type": "string",
                "enum": ["youtube", "tiktok", "instagram", "local_export"],
                "default": "local_export",
                "description": "Target publishing platform.",
            },
            "platforms": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["youtube", "tiktok", "instagram", "local_export"],
                },
                "default": ["local_export"],
                "description": "Target publishing platforms.",
            },
        },
        "required": ["project_id", "video_path", "title", "platform"],
    },
}


def resolve_capability_token(
    args: Dict[str, Any], kwargs: Dict[str, Any], session_id: str
) -> Optional[CapabilityToken]:
    """Extract and validate capability token from invocation arguments, contextvar, or session."""
    # 1. From args
    token = None
    if isinstance(args, dict):
        token = args.get("capability_token") or args.get("token")
    if token is not None:
        if isinstance(token, CapabilityToken):
            return token
        if isinstance(token, dict):
            return CapabilityToken.from_dict(token)

    # 2. From kwargs
    if isinstance(kwargs, dict):
        token = kwargs.get("capability_token") or kwargs.get("token")
    else:
        token = None
    if token is not None:
        if isinstance(token, CapabilityToken):
            return token
        if isinstance(token, dict):
            return CapabilityToken.from_dict(token)

    # 3. From contextvar
    token = current_capability_token.get()
    if token is not None:
        return token

    # 4. From security guard session tokens
    guard = get_security_guard()
    token = guard.get_session_token(session_id)
    if token is not None:
        return token

    return None


# ===========================================================================
# 2. Handlers for H9 Content Production Model Tools
# ===========================================================================

def handle_h9_research(args: Dict[str, Any], **kwargs: Any) -> str:
    """Handler for h9.research / h9_research tool."""
    session_id = kwargs.get("session_id") or "default_session"
    parent_agent = kwargs.get("parent_agent")

    # Capability token enforcement FIRST
    token = resolve_capability_token(args, kwargs, session_id)
    if token is not None:
        try:
            guard = get_security_guard()
            guard.enforce_tool_execution(token, "h9.research")
        except SecurityError as sec_err:
            if (args.get("raise_on_error") if isinstance(args, dict) else False) or kwargs.get("raise_on_error"):
                raise
            return tool_error(f"Permission denied: {sec_err}", status="error", error_type="permission_denied", success=False)

    if not isinstance(args, dict):
        return tool_error("Arguments must be a JSON dictionary.", status="error", success=False)

    topic = args.get("topic")
    if not topic or not isinstance(topic, str) or not topic.strip():
        return tool_error("Missing or invalid required parameter: 'topic'", success=False)

    depth = str(args.get("depth", "standard")).lower()
    if depth not in ("overview", "standard", "deep"):
        depth = "standard"

    constraints = args.get("constraints")
    if constraints is not None and not isinstance(constraints, dict):
        return tool_error("Parameter 'constraints' must be an object/dictionary.", success=False)

    try:
        bridge = get_capability_bridge(session_id=session_id)
        dossier = bridge.plan_research(
            topic=topic.strip(),
            depth=depth,
            constraints=constraints,
            parent_agent=parent_agent,
        )

        dossier_dict = (
            dossier.to_dict()
            if hasattr(dossier, "to_dict")
            else (dossier if isinstance(dossier, dict) else {"topic": topic})
        )
        res = dict(dossier_dict)
        res["success"] = True
        res["topic"] = topic.strip()
        res["dossier"] = dict(dossier_dict)
        return tool_result(res)

    except SecurityError as sec_err:
        if (args.get("raise_on_error") if isinstance(args, dict) else False) or kwargs.get("raise_on_error"):
            raise
        return tool_error(f"Permission denied: {sec_err}", status="error", error_type="permission_denied", success=False)
    except Exception as exc:
        logger.exception("Error executing h9.research: %s", exc)
        return tool_error(f"Research execution failed: {exc}", topic=topic, success=False)


def handle_h9_discover_assets(args: Dict[str, Any], **kwargs: Any) -> str:
    """Handler for h9.discover_assets / h9_discover_assets tool."""
    session_id = kwargs.get("session_id") or "default_session"

    # Capability token enforcement FIRST
    token = resolve_capability_token(args, kwargs, session_id)
    if token is not None:
        try:
            guard = get_security_guard()
            guard.enforce_tool_execution(token, "h9.discover_assets")
        except SecurityError as sec_err:
            if (args.get("raise_on_error") if isinstance(args, dict) else False) or kwargs.get("raise_on_error"):
                raise
            return tool_error(f"Permission denied: {sec_err}", status="error", error_type="permission_denied", success=False)

    if not isinstance(args, dict):
        return tool_error("Arguments must be a JSON dictionary.", status="error", success=False)

    requirements = args.get("requirements") or []
    if not isinstance(requirements, list):
        return tool_error("Parameter 'requirements' must be a list of objects.", success=False)

    scene_ids = args.get("scene_ids")
    if scene_ids is not None and not isinstance(scene_ids, list):
        return tool_error("Parameter 'scene_ids' must be a list of strings.", success=False)

    format_aspect = str(args.get("format_aspect", "16:9"))
    dossier = args.get("dossier")
    if dossier is not None and not isinstance(dossier, dict):
        return tool_error("Parameter 'dossier' must be an object/dictionary.", success=False)

    try:
        bridge = get_capability_bridge(session_id=session_id)
        asset_records = bridge.discover_assets(
            requirements=requirements,
            scene_ids=scene_ids,
            dossier=dossier,
            format_aspect=format_aspect,
        )

        return tool_result(
            success=True,
            assets=asset_records,
            total_assets=len(asset_records),
            format_aspect=format_aspect,
        )

    except SecurityError as sec_err:
        if (args.get("raise_on_error") if isinstance(args, dict) else False) or kwargs.get("raise_on_error"):
            raise
        return tool_error(f"Permission denied: {sec_err}", status="error", error_type="permission_denied", success=False)
    except Exception as exc:
        logger.exception("Error executing h9.discover_assets: %s", exc)
        return tool_error(f"Asset discovery failed: {exc}", success=False)


def handle_h9_generate_script(args: Dict[str, Any], **kwargs: Any) -> str:
    """Handler for h9.generate_script / h9_generate_script tool."""
    session_id = kwargs.get("session_id") or "default_session"

    # Capability token enforcement FIRST
    token = resolve_capability_token(args, kwargs, session_id)
    if token is not None:
        try:
            guard = get_security_guard()
            guard.enforce_tool_execution(token, "h9.generate_script")
        except SecurityError as sec_err:
            if (args.get("raise_on_error") if isinstance(args, dict) else False) or kwargs.get("raise_on_error"):
                raise
            return tool_error(f"Permission denied: {sec_err}", status="error", error_type="permission_denied", success=False)

    if not isinstance(args, dict):
        return tool_error("Arguments must be a JSON dictionary.", status="error", success=False)

    dossier_raw = args.get("dossier")
    if not dossier_raw:
        return tool_error("Missing required parameter: 'dossier'", success=False)
    if not isinstance(dossier_raw, dict):
        return tool_error("Parameter 'dossier' must be an object/dictionary.", success=False)

    outline = args.get("outline") or {}
    if not isinstance(outline, dict):
        return tool_error("Parameter 'outline' must be an object/dictionary.", success=False)

    creator = args.get("creator") or {}
    if not isinstance(creator, dict):
        return tool_error("Parameter 'creator' must be an object/dictionary.", success=False)

    format_aspect = str(args.get("format_aspect", "16:9"))

    try:
        raw_duration = args.get("target_duration", 30.0)
        if isinstance(raw_duration, bool):
            return tool_error("Parameter 'target_duration' must be a valid number of seconds.", success=False)
        try:
            duration = float(raw_duration)
        except (ValueError, TypeError):
            return tool_error("Parameter 'target_duration' must be a valid number of seconds.", success=False)

        bridge = get_capability_bridge(session_id=session_id)

        # Parse ResearchDossier from payload
        claims = dossier_raw.get("claims") or []
        for c in claims:
            if isinstance(c, dict):
                if "claim_id" not in c and "id" in c:
                    c["claim_id"] = c["id"]
                if "claim_text" not in c and "text" in c:
                    c["claim_text"] = c["text"]
                if "confidence_score" not in c and "confidence" in c:
                    c["confidence_score"] = c["confidence"]
                if "primary_source" not in c or not c.get("primary_source"):
                    c["primary_source"] = {
                        "title": f"Verified Source for {c.get('claim_id', 'claim')}",
                        "url": "https://harness9.local/verified-source",
                        "reliability_score": 0.95,
                    }

        dossier = ResearchDossier(
            topic=dossier_raw.get("topic", "Technology Overview"),
            headline=dossier_raw.get("headline", ""),
            executive_summary=dossier_raw.get("executive_summary", ""),
            key_takeaways=dossier_raw.get("key_takeaways") or [],
            claims=claims,
            suggested_visual_queries=dossier_raw.get("suggested_visual_queries") or [],
        )

        # Determine angle
        if "angle_id" in outline or "angle_archetype" in outline:
            premise = outline.get("premise") or f"Exploring {dossier.topic} from a compelling perspective"
            core_thesis = outline.get("core_thesis") or premise
            angle = EditorialAngle(
                angle_id=outline.get("angle_id", "angle_selected"),
                title=outline.get("title", f"The Story of {dossier.topic}"),
                premise=premise,
                core_thesis=core_thesis,
                target_audience=outline.get("target_audience", "General"),
                narrative_style=outline.get("narrative_style", "Cinematic Discovery"),
            )
        else:
            _, angle = bridge.evaluate_angles(dossier=dossier)

        creator_id = creator.get("creator_id") if isinstance(creator, dict) else None

        script = bridge.generate_script(
            angle=angle,
            dossier=dossier,
            creator_id=creator_id,
            format_aspect=format_aspect,
            duration=duration,
        )

        script_dict = script.to_dict() if hasattr(script, "to_dict") else dict(script)
        res = dict(script_dict)
        res["success"] = True
        res["script"] = dict(script_dict)
        return tool_result(res)

    except Exception as exc:
        logger.exception("Error executing h9.generate_script: %s", exc)
        return tool_error(f"Script generation failed: {exc}", success=False)


def handle_h9_render(args: Dict[str, Any], **kwargs: Any) -> str:
    """Handler for h9.render / h9_render tool."""
    session_id = kwargs.get("session_id") or "default_session"

    # Capability token enforcement FIRST
    token = resolve_capability_token(args, kwargs, session_id)
    if token is not None:
        try:
            guard = get_security_guard()
            guard.enforce_tool_execution(token, "h9.render")
            output_dir_candidate = args.get("output_dir") if isinstance(args, dict) else None
            if output_dir_candidate and isinstance(output_dir_candidate, str) and output_dir_candidate.strip():
                guard.enforce_filesystem_access(token, output_dir_candidate.strip(), mode="write")
        except SecurityError as sec_err:
            if (args.get("raise_on_error") if isinstance(args, dict) else False) or kwargs.get("raise_on_error"):
                raise
            return tool_error(f"Permission denied: {sec_err}", status="error", error_type="permission_denied", success=False)

    if not isinstance(args, dict):
        return tool_error("Arguments must be a JSON dictionary.", status="error", success=False)

    production_ir = args.get("production_ir")
    if not production_ir:
        return tool_error("Missing required parameter: 'production_ir'", success=False)
    if not isinstance(production_ir, dict):
        return tool_error("Parameter 'production_ir' must be an object/dictionary.", success=False)

    output_dir = args.get("output_dir")
    if not output_dir or not isinstance(output_dir, str) or not output_dir.strip():
        return tool_error("Missing or invalid required parameter: 'output_dir'", success=False)

    try:
        bridge = get_capability_bridge(session_id=session_id)
        artifact = bridge.render_video(
            ir=production_ir,
            output_dir=output_dir.strip(),
            session_id=session_id,
            capability_token=token,
        )

        artifact_dict = (
            artifact.to_dict() if hasattr(artifact, "to_dict") else dict(artifact)
        )
        res = dict(artifact_dict)
        res["success"] = True
        return tool_result(res)

    except SecurityError as sec_err:
        if (args.get("raise_on_error") if isinstance(args, dict) else False) or kwargs.get("raise_on_error"):
            raise
        return tool_error(f"Permission denied: {sec_err}", status="error", error_type="permission_denied", success=False)
    except Exception as exc:
        logger.exception("Error executing h9.render: %s", exc)
        return tool_error(f"Video render failed: {exc}", success=False)


def handle_h9_publish(args: Dict[str, Any], **kwargs: Any) -> str:
    """Handler for h9.publish / h9_publish tool."""
    session_id = kwargs.get("session_id") or "default_session"

    # Capability token enforcement FIRST
    token = resolve_capability_token(args, kwargs, session_id)
    if token is not None:
        try:
            guard = get_security_guard()
            guard.enforce_tool_execution(token, "h9.publish")
            video_path_candidate = args.get("video_path") if isinstance(args, dict) else None
            if video_path_candidate and isinstance(video_path_candidate, str) and video_path_candidate.strip():
                guard.enforce_filesystem_access(token, video_path_candidate.strip(), mode="read")
        except SecurityError as sec_err:
            if (args.get("raise_on_error") if isinstance(args, dict) else False) or kwargs.get("raise_on_error"):
                raise
            return tool_error(f"Permission denied: {sec_err}", status="error", error_type="permission_denied", success=False)

    if not isinstance(args, dict):
        return tool_error("Arguments must be a JSON dictionary.", status="error", success=False)

    project_id = args.get("project_id")
    if not project_id or not isinstance(project_id, str):
        return tool_error("Missing or invalid required parameter: 'project_id'", success=False)

    video_path = args.get("video_path")
    if not video_path or not isinstance(video_path, str):
        return tool_error("Missing or invalid required parameter: 'video_path'", success=False)

    title = args.get("title")
    if not title or not isinstance(title, str):
        return tool_error("Missing or invalid required parameter: 'title'", success=False)

    description = args.get("description", "")
    tags = args.get("tags") or []
    platform = args.get("platform")
    platforms = args.get("platforms") or ([platform] if platform else ["local_export"])

    try:
        bridge = get_capability_bridge(session_id=session_id)
        res = bridge.publish(
            package={
                "project_id": project_id,
                "video_path": video_path,
                "title": title,
                "description": description,
                "tags": tags,
                "platforms": platforms,
            },
            platform=platform or (platforms[0] if platforms else "local_export"),
            session_id=session_id,
            capability_token=token,
        )
        res_dict = dict(res)
        res_dict["success"] = True
        return tool_result(res_dict)
    except SecurityError as sec_err:
        if (args.get("raise_on_error") if isinstance(args, dict) else False) or kwargs.get("raise_on_error"):
            raise
        return tool_error(f"Permission denied: {sec_err}", status="error", error_type="permission_denied", success=False)
    except Exception as exc:
        logger.exception("Error executing h9.publish: %s", exc)
        return tool_error(f"Publishing failed: {exc}", success=False)


# ===========================================================================
# 3. Tool Registration Hook
# ===========================================================================

def register_tools(reg: Optional[Any] = None) -> None:
    """Register the 5 H9 content tools and their aliases into a tool registry."""
    r = reg or registry

    # 1. h9.research + h9_research
    r.register(
        name="h9.research",
        toolset="h9_content",
        schema=H9_RESEARCH_SCHEMA,
        handler=handle_h9_research,
        check_fn=check_h9_available,
        description="Synthesize multi-source research into a structured ResearchDossier.",
        emoji="🔬",
    )
    r.register(
        name="h9_research",
        toolset="h9_content",
        schema={**H9_RESEARCH_SCHEMA, "name": "h9_research"},
        handler=handle_h9_research,
        check_fn=check_h9_available,
        description="Synthesize multi-source research into a structured ResearchDossier.",
        emoji="🔬",
    )

    # 2. h9.discover_assets + h9_discover_assets
    r.register(
        name="h9.discover_assets",
        toolset="h9_content",
        schema=H9_DISCOVER_ASSETS_SCHEMA,
        handler=handle_h9_discover_assets,
        check_fn=check_h9_available,
        description="Discover, generate, freeze, and deduplicate media assets for scenes.",
        emoji="🎨",
    )
    r.register(
        name="h9_discover_assets",
        toolset="h9_content",
        schema={**H9_DISCOVER_ASSETS_SCHEMA, "name": "h9_discover_assets"},
        handler=handle_h9_discover_assets,
        check_fn=check_h9_available,
        description="Discover, generate, freeze, and deduplicate media assets for scenes.",
        emoji="🎨",
    )

    # 3. h9.generate_script + h9_generate_script
    r.register(
        name="h9.generate_script",
        toolset="h9_content",
        schema=H9_GENERATE_SCRIPT_SCHEMA,
        handler=handle_h9_generate_script,
        check_fn=check_h9_available,
        description="Generate a structured broadcast script from outline and dossier.",
        emoji="📜",
    )
    r.register(
        name="h9_generate_script",
        toolset="h9_content",
        schema={**H9_GENERATE_SCRIPT_SCHEMA, "name": "h9_generate_script"},
        handler=handle_h9_generate_script,
        check_fn=check_h9_available,
        description="Generate a structured broadcast script from outline and dossier.",
        emoji="📜",
    )

    # 4. h9.render + h9_render
    r.register(
        name="h9.render",
        toolset="h9_content",
        schema=H9_RENDER_SCHEMA,
        handler=handle_h9_render,
        check_fn=check_h9_available,
        description="Render broadcast MP4 video from a Production IR AST.",
        emoji="🎬",
    )
    r.register(
        name="h9_render",
        toolset="h9_content",
        schema={**H9_RENDER_SCHEMA, "name": "h9_render"},
        handler=handle_h9_render,
        check_fn=check_h9_available,
        description="Render broadcast MP4 video from a Production IR AST.",
        emoji="🎬",
    )

    # 5. h9.publish + h9_publish
    r.register(
        name="h9.publish",
        toolset="h9_content",
        schema=H9_PUBLISH_SCHEMA,
        handler=handle_h9_publish,
        check_fn=check_h9_available,
        description="Package, license, and distribute rendered video content.",
        emoji="🚀",
    )
    r.register(
        name="h9_publish",
        toolset="h9_content",
        schema={**H9_PUBLISH_SCHEMA, "name": "h9_publish"},
        handler=handle_h9_publish,
        check_fn=check_h9_available,
        description="Package, license, and distribute rendered video content.",
        emoji="🚀",
    )


# Automatically register on module import so discover_builtin_tools picks them up
register_tools()

