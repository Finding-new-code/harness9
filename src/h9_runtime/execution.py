"""src/h9_runtime/execution.py

ExecutionRuntime protocol and DefaultExecutionRuntime implementation.
Governs sandboxed subprocess execution (FFmpeg, Playwright, shell),
bounded output capture, path confinement validation, and safe atomic file I/O.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
import subprocess
import tempfile
import time
from typing import Any, Dict, List, Optional, Protocol, Union, runtime_checkable

from src.h9_runtime.types import ExecutionResult
from src.security.tokens import PathTraversalError

logger = logging.getLogger(__name__)

MAX_CAPTURE_BYTES = 1024 * 1024  # 1MB output cap for stdout/stderr


@runtime_checkable
class ExecutionRuntime(Protocol):
    """Runtime interface for sandbox-isolated shell and filesystem operations."""

    def execute_command(
        self,
        command: Union[str, List[str]],
        cwd: Optional[Path] = None,
        timeout_seconds: float = 300.0,
        env_vars: Optional[Dict[str, str]] = None,
        session_id: Optional[str] = None,
    ) -> ExecutionResult:
        """Execute a shell command within the configured sandbox environment."""
        ...

    def validate_path(self, target_path: Union[str, Path], session_id: str) -> Path:
        """Validate and resolve a path against session sandbox confinement boundaries."""
        ...

    def read_file(self, path: Union[str, Path], session_id: Optional[str] = None) -> str:
        """Read text content from a confined file."""
        ...

    def write_file(
        self,
        path: Union[str, Path],
        content: Union[str, bytes],
        session_id: Optional[str] = None,
        atomic: bool = True,
    ) -> Path:
        """Write content to a confined file atomically."""
        ...


class DefaultExecutionRuntime:
    """Concrete implementation of ExecutionRuntime with path confinement and bounded capture."""

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        self.base_dir = (base_dir or Path("output/sessions")).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_session_root(self, session_id: str) -> Path:
        """Get or create the root directory for a session."""
        root = (self.base_dir / session_id).resolve()
        root.mkdir(parents=True, exist_ok=True)
        return root

    def validate_path(self, target_path: Union[str, Path], session_id: str) -> Path:
        """Validate that a target path is strictly confined within the session root."""
        path_str = str(target_path)
        if "\0" in path_str:
            raise PathTraversalError("Null byte injection detected in filesystem path")

        session_root = self.get_session_root(session_id)
        candidate = Path(target_path)
        if not candidate.is_absolute():
            resolved = (session_root / candidate).resolve()
        else:
            resolved = candidate.resolve()

        try:
            resolved.relative_to(session_root)
        except ValueError:
            raise PathTraversalError(
                f"Path traversal violation: '{target_path}' escapes session root '{session_root}'"
            )

        return resolved

    def execute_command(
        self,
        command: Union[str, List[str]],
        cwd: Optional[Path] = None,
        timeout_seconds: float = 300.0,
        env_vars: Optional[Dict[str, str]] = None,
        session_id: Optional[str] = None,
    ) -> ExecutionResult:
        """Execute a command with timeout enforcement and bounded output capture."""
        start_time = time.time()
        effective_cwd = cwd
        if session_id and effective_cwd is None:
            effective_cwd = self.get_session_root(session_id)

        effective_env = os.environ.copy()
        if env_vars:
            effective_env.update(env_vars)

        is_shell = isinstance(command, str)

        try:
            process = subprocess.Popen(
                command,
                cwd=str(effective_cwd) if effective_cwd else None,
                env=effective_env,
                shell=is_shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            try:
                raw_out, raw_err = process.communicate(timeout=timeout_seconds)
                timed_out = False
            except subprocess.TimeoutExpired:
                process.kill()
                raw_out, raw_err = process.communicate()
                timed_out = True

            elapsed = time.time() - start_time

            # Bounded output decoding
            def _decode_bounded(b: Optional[bytes]) -> str:
                if not b:
                    return ""
                if len(b) > MAX_CAPTURE_BYTES:
                    head = b[: MAX_CAPTURE_BYTES // 2]
                    tail = b[-MAX_CAPTURE_BYTES // 2 :]
                    return (
                        head.decode("utf-8", errors="replace")
                        + "\n... [OUTPUT TRUNCATED] ...\n"
                        + tail.decode("utf-8", errors="replace")
                    )
                return b.decode("utf-8", errors="replace")

            return ExecutionResult(
                exit_code=process.returncode if not timed_out else -1,
                stdout=_decode_bounded(raw_out),
                stderr=_decode_bounded(raw_err),
                duration_seconds=round(elapsed, 3),
                timed_out=timed_out,
            )

        except Exception as exc:
            elapsed = time.time() - start_time
            logger.exception(f"Subprocess execution error: {exc}")
            return ExecutionResult(
                exit_code=1,
                stdout="",
                stderr=str(exc),
                duration_seconds=round(elapsed, 3),
                timed_out=False,
            )

    def read_file(self, path: Union[str, Path], session_id: Optional[str] = None) -> str:
        """Read text content from a confined file."""
        target = self.validate_path(path, session_id) if session_id else Path(path).resolve()
        if not target.exists():
            raise FileNotFoundError(f"File not found: {target}")
        return target.read_text(encoding="utf-8")

    def write_file(
        self,
        path: Union[str, Path],
        content: Union[str, bytes],
        session_id: Optional[str] = None,
        atomic: bool = True,
    ) -> Path:
        """Write content to a file atomically within confinement boundaries."""
        target = self.validate_path(path, session_id) if session_id else Path(path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)

        if atomic:
            # Write to temporary file in same directory then rename
            with tempfile.NamedTemporaryFile(
                dir=str(target.parent),
                delete=False,
                mode="wb" if isinstance(content, bytes) else "w",
                encoding=None if isinstance(content, bytes) else "utf-8",
            ) as tf:
                tf.write(content)
                temp_name = tf.name
            os.replace(temp_name, str(target))
        else:
            if isinstance(content, bytes):
                target.write_bytes(content)
            else:
                target.write_text(content, encoding="utf-8")

        return target


class HermesExecutionRuntime:
    """ExecutionRuntime implementation backed by Hermes BaseEnvironment sandboxing."""

    def __init__(
        self,
        session_id: str = "default_session",
        base_dir: Optional[Path] = None,
        environment: Optional[Any] = None,
        env_type: str = "auto",  # auto, local, docker, modal
        docker_shm_size: str = "1g",
    ) -> None:
        self.session_id = session_id
        self.base_dir = (base_dir or Path("output/sessions")).resolve()
        self.session_root = (self.base_dir / session_id).resolve()
        self.session_root.mkdir(parents=True, exist_ok=True)
        self.environment = environment
        self.env_type = env_type
        self.docker_shm_size = docker_shm_size

    @property
    def env(self) -> Any:
        """Active BaseEnvironment instance."""
        return self.resolve_environment()

    def get_session_root(self, session_id: Optional[str] = None) -> Path:
        """Get or create the root directory for a session."""
        sid = session_id or self.session_id
        root = (self.base_dir / sid).resolve()
        root.mkdir(parents=True, exist_ok=True)
        return root

    def validate_path(
        self, target_path: Union[str, Path], session_id: Optional[str] = None
    ) -> Path:
        """Enforce strict path confinement inside session root, rejecting traversal escapes."""
        sid = session_id or self.session_id
        root = self.get_session_root(sid)
        path_str = str(target_path)
        if "\0" in path_str:
            raise PathTraversalError("Null byte injection detected in filesystem path")

        candidate = Path(target_path)
        if not candidate.is_absolute():
            resolved = (root / candidate).resolve()
        else:
            resolved = candidate.resolve()

        try:
            resolved.relative_to(root)
        except ValueError:
            raise PathTraversalError(
                f"Path traversal violation: '{target_path}' escapes session root '{root}'"
            )

        return resolved

    def resolve_environment(self) -> Any:
        """Resolve active BaseEnvironment from terminal registry or instantiate configured mode."""
        if self.environment is not None:
            return self.environment

        from tools.terminal_tool import get_active_env, ensure_task_env

        env = get_active_env(self.session_id)
        if env is None and self.env_type not in ("local",):
            env = ensure_task_env(self.session_id)

        if env is None:
            if self.env_type == "docker":
                from tools.environments.docker import DockerEnvironment

                env = DockerEnvironment(
                    cwd=str(self.session_root),
                    timeout=300,
                    task_id=self.session_id,
                    shm_size=self.docker_shm_size,
                )
            elif self.env_type == "modal":
                from tools.environments.modal import ModalEnvironment

                env = ModalEnvironment(
                    cwd=str(self.session_root),
                    timeout=300,
                    task_id=self.session_id,
                )
            else:
                from tools.environments.local import LocalEnvironment

                env = LocalEnvironment(
                    cwd=str(self.session_root),
                    timeout=300,
                )

        return env

    def execute_command(
        self,
        command: Union[str, List[str]],
        cwd: Optional[Path] = None,
        timeout_seconds: float = 300.0,
        env_vars: Optional[Dict[str, str]] = None,
        session_id: Optional[str] = None,
    ) -> ExecutionResult:
        """Execute command within active BaseEnvironment (Docker, Modal, Local)."""
        import shlex

        sid = session_id or self.session_id
        root = self.get_session_root(sid)

        effective_cwd = self.validate_path(cwd, sid) if cwd else root

        # Translate list command to shell string
        if isinstance(command, list):
            cmd_str = " ".join(shlex.quote(str(arg)) for arg in command)
        else:
            cmd_str = str(command)

        # Inject env vars prefix if specified
        if env_vars:
            prefix_parts = [f"{k}={shlex.quote(str(v))}" for k, v in env_vars.items()]
            cmd_str = f"export {' '.join(prefix_parts)} && {cmd_str}"

        env = self.resolve_environment()

        # Handle container path translation if non-local
        is_local = getattr(env, "is_local", False)
        container_cwd = str(effective_cwd) if is_local else "/workspace"

        start_time = time.time()
        try:
            raw_res = env.execute(
                cmd_str,
                cwd=container_cwd,
                timeout=max(1, int(timeout_seconds)),
                bounded_capture=False,
            )
            elapsed = time.time() - start_time
            retcode = int(
                raw_res.get("returncode")
                if raw_res.get("returncode") is not None
                else 0
            )
            output = raw_res.get("output", "")
            timed_out = retcode == 124 or "[Command timed out" in output

            # Bounded output formatting
            def _decode_bounded_str(s: str) -> str:
                if len(s) > MAX_CAPTURE_BYTES:
                    head = s[: MAX_CAPTURE_BYTES // 2]
                    tail = s[-MAX_CAPTURE_BYTES // 2 :]
                    return head + "\n... [OUTPUT TRUNCATED] ...\n" + tail
                return s

            stderr_out = _decode_bounded_str(raw_res.get("stderr", ""))
            if timed_out:
                timeout_msg = f"Command timed out after {timeout_seconds}s"
                if not stderr_out or "timed out" not in stderr_out.lower():
                    stderr_out = f"{timeout_msg}\n{stderr_out}".strip() if stderr_out else timeout_msg

            return ExecutionResult(
                exit_code=retcode,
                stdout=_decode_bounded_str(output),
                stderr=stderr_out,
                duration_seconds=round(elapsed, 3),
                timed_out=timed_out,
            )

        except Exception as exc:
            elapsed = time.time() - start_time
            logger.exception(f"HermesExecutionRuntime subprocess execution error: {exc}")
            return ExecutionResult(
                exit_code=1,
                stdout="",
                stderr=str(exc),
                duration_seconds=round(elapsed, 3),
                timed_out=False,
            )

    def read_file(self, path: Union[str, Path], session_id: Optional[str] = None) -> str:
        """Read text content from a confined file."""
        target = self.validate_path(path, session_id)
        if not target.exists():
            raise FileNotFoundError(f"File not found in sandbox: {target}")
        return target.read_text(encoding="utf-8")

    def write_file(
        self,
        path: Union[str, Path],
        content: Union[str, bytes],
        session_id: Optional[str] = None,
        atomic: bool = True,
    ) -> Path:
        """Write content to a confined file atomically."""
        target = self.validate_path(path, session_id)
        target.parent.mkdir(parents=True, exist_ok=True)

        if atomic:
            with tempfile.NamedTemporaryFile(
                dir=str(target.parent),
                delete=False,
                mode="wb" if isinstance(content, bytes) else "w",
                encoding=None if isinstance(content, bytes) else "utf-8",
            ) as tf:
                tf.write(content)
                temp_name = tf.name
            os.replace(temp_name, str(target))
        else:
            if isinstance(content, bytes):
                target.write_bytes(content)
            else:
                target.write_text(content, encoding="utf-8")

        return target


def resolve_environment(
    env_type: str = "local",
    cwd: Optional[Union[str, Path]] = None,
    timeout: int = 300,
    session_id: Optional[str] = None,
    **kwargs: Any,
) -> Any:
    """Resolve or instantiate a Hermes BaseEnvironment by type (local, docker, modal)."""
    work_dir = str(cwd) if cwd else os.getcwd()
    if env_type == "docker":
        try:
            from tools.environments.docker import DockerEnvironment

            shm_size = kwargs.pop("shm_size", "1g")
            image = kwargs.pop("image", "ubuntu:latest")
            return DockerEnvironment(
                image=image,
                cwd=work_dir,
                timeout=timeout,
                task_id=session_id or "default",
                shm_size=shm_size,
                **kwargs,
            )
        except Exception as e:
            logger.warning(
                "Failed to initialize DockerEnvironment (%s); falling back to LocalEnvironment",
                e,
            )
    elif env_type == "modal":
        try:
            from tools.environments.modal import ModalEnvironment

            return ModalEnvironment(
                cwd=work_dir,
                timeout=timeout,
                task_id=session_id or "default",
                **kwargs,
            )
        except Exception as e:
            logger.warning(
                "Failed to initialize ModalEnvironment (%s); falling back to LocalEnvironment",
                e,
            )

    from tools.environments.local import LocalEnvironment

    return LocalEnvironment(cwd=work_dir, timeout=timeout)

