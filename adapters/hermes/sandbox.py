"""Hermes Session Sandbox Manager.

Provides session-scoped directory isolation, workspace management, path traversal guards,
and scratch space cleanup for upstream Hermes Agent hosts.
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
from typing import Any, Dict, List, Optional, Union


class HermesSessionSandbox:
    """Manages an isolated directory environment for a specific Hermes conversation session."""

    def __init__(
        self,
        session_id: str,
        base_dir: Optional[Union[str, Path]] = None,
    ):
        if not session_id or not str(session_id).strip():
            session_id = "default_session"
        
        # Sanitize session_id for filesystem safety (disallow .. and path separators)
        clean_id = re.sub(r"[^a-zA-Z0-9_-]", "_", str(session_id).strip())
        if not clean_id or not clean_id.strip("_"):
            clean_id = "default_session"
        self.session_id = clean_id
        
        if base_dir is not None:
            self.base_dir = Path(base_dir).resolve() / self.session_id
        else:
            # Check HERMES_HOME env var or default to output/hermes_sessions
            hermes_home = os.environ.get("HERMES_HOME")
            if hermes_home:
                self.base_dir = Path(hermes_home).resolve() / "sessions" / self.session_id / "harness9"
            else:
                self.base_dir = Path("output/hermes_sessions").resolve() / self.session_id

        self.session_root = self.base_dir
        self.workspace_dir = self.session_root / "workspace"
        self.renders_dir = self.session_root / "renders"
        self.audit_dir = self.session_root / "audit"

        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create all required session subdirectories."""
        self.session_root.mkdir(parents=True, exist_ok=True)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.renders_dir.mkdir(parents=True, exist_ok=True)
        self.audit_dir.mkdir(parents=True, exist_ok=True)

    def get_session_root(self) -> Path:
        """Return the absolute path to the session root directory."""
        return self.session_root

    def get_workspace_dir(self) -> Path:
        """Return the workspace directory for intermediate files."""
        return self.workspace_dir

    def get_renders_dir(self) -> Path:
        """Return the renders directory for final video artifacts."""
        return self.renders_dir

    def get_audit_dir(self) -> Path:
        """Return the audit directory for state machine and summary logs."""
        return self.audit_dir

    def validate_path(self, target_path: Union[str, Path]) -> Path:
        """Validate that a target path is contained within the session root (path traversal guard).
        
        Raises ValueError if the path escapes the session sandbox.
        """
        resolved = Path(target_path).resolve()
        try:
            resolved.relative_to(self.session_root.resolve())
        except ValueError as exc:
            raise ValueError(
                f"Path traversal detected: {resolved} is outside session sandbox {self.session_root}"
            ) from exc
        return resolved

    def save_audit_record(self, record_name: str, data: Dict[str, Any]) -> Path:
        """Save a JSON audit record into the session audit directory."""
        if not record_name or not str(record_name).strip():
            raise ValueError("record_name cannot be empty")
        target = (self.audit_dir / f"{record_name}.json").resolve()
        try:
            target.relative_to(self.audit_dir.resolve())
        except ValueError as exc:
            raise ValueError(
                f"Path traversal detected: {record_name} escapes audit directory {self.audit_dir}"
            ) from exc
        self.validate_path(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        return target

    def get_audit_records(self) -> List[Dict[str, Any]]:
        """Retrieve all audit records stored for this session."""
        records = []
        if self.audit_dir.exists():
            for f in sorted(self.audit_dir.glob("*.json")):
                try:
                    records.append(json.loads(f.read_text(encoding="utf-8")))
                except Exception:
                    continue
        return records

    def list_render_artifacts(self) -> List[Path]:
        """List all rendered media files in the renders directory."""
        if not self.renders_dir.exists():
            return []
        return sorted(list(self.renders_dir.glob("*.mp4")) + list(self.renders_dir.glob("*.webm")))

    def cleanup_scratch(self) -> None:
        """Remove intermediate scratch files in workspace while preserving renders and audit logs."""
        if self.workspace_dir.exists():
            for item in self.workspace_dir.iterdir():
                try:
                    if item.is_file() or item.is_symlink():
                        item.unlink(missing_ok=True)
                    elif item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                except Exception:
                    pass
            self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def purge(self) -> None:
        """Purge the entire session sandbox directory."""
        if self.session_root.exists():
            shutil.rmtree(self.session_root, ignore_errors=True)
