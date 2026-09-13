"""Harness 9 Security Sandboxing & Guard (Milestone M6).

Enforces:
- Model tool execution whitelisting
- Strict filesystem path confinement (path traversal and directory escape rejection)
- Network egress filtering (offline isolation, host whitelisting)
- Capability token validity and signature integrity checking
"""

from contextlib import contextmanager
import contextvars
import functools
import os
from pathlib import Path
import re
import time
from typing import Any, Callable, Dict, List, Optional, Set, Union

from src.security.tokens import (
    CapabilityToken,
    SecurityError,
    PermissionDeniedError,
    TokenExpiredError,
    TokenTamperedError,
    TokenValidationError,
    PathTraversalError,
    NetworkEgressError,
    DelegationLimitExceededError,
    TokenRevocationRegistry,
    get_token_revocation_registry,
)

# Active capability token in current thread/async context
current_capability_token: contextvars.ContextVar[Optional[CapabilityToken]] = (
    contextvars.ContextVar("current_capability_token", default=None)
)


class SecurityGuard:
    """Runtime enforcement guard applying capability token policies to pipeline operations."""

    def __init__(
        self,
        secret_key: Optional[Union[str, bytes]] = None,
        enforce_expiry: bool = True,
        enforce_signatures: bool = True,
        strict_path_confinement: bool = True,
        revocation_registry: Optional[TokenRevocationRegistry] = None,
    ):
        self.secret_key = secret_key
        self.enforce_expiry = enforce_expiry
        self.enforce_signatures = enforce_signatures
        self.strict_path_confinement = strict_path_confinement
        self.revocation_registry = (
            revocation_registry
            if revocation_registry is not None
            else get_token_revocation_registry()
        )
        self._session_tokens: Dict[str, CapabilityToken] = {}

    def bind_session_token(self, session_id: str, token: CapabilityToken) -> None:
        """Bind a capability token to a specific runtime session."""
        self.verify_token(token)
        self._session_tokens[session_id] = token

    def register_session_token(self, session_id: str, token: CapabilityToken) -> None:
        """Alias for bind_session_token."""
        self.bind_session_token(session_id, token)

    def get_session_token(self, session_id: str) -> Optional[CapabilityToken]:
        """Retrieve the capability token bound to a session."""
        return self._session_tokens.get(session_id)

    def revoke_session_token(self, session_id: str, reason: str = "session_closed") -> None:
        """Revoke and unbind the token associated with a session."""
        token = self._session_tokens.pop(session_id, None)
        if token and self.revocation_registry:
            self.revocation_registry.revoke(token.token_id, reason=reason)

    def revoke_token(self, token_id: str, reason: str = "manual_revocation") -> None:
        """Revoke a token by ID across the revocation registry."""
        if self.revocation_registry:
            self.revocation_registry.revoke(token_id, reason=reason)

    @contextmanager
    def use_token(self, token: CapabilityToken):
        """Context manager setting the active capability token in current execution context."""
        self.verify_token(token)
        t_token = current_capability_token.set(token)
        try:
            yield token
        finally:
            current_capability_token.reset(t_token)

    def get_current_token(self) -> Optional[CapabilityToken]:
        """Retrieve the active capability token from ContextVar."""
        return current_capability_token.get()

    def verify_token(self, token: CapabilityToken) -> bool:
        """Verify token validity, expiration, revocation status, and signature."""
        if not isinstance(token, CapabilityToken):
            raise PermissionDeniedError(f"Invalid token type provided: {type(token)}")

        # Check active revocation registry
        if self.revocation_registry and self.revocation_registry.is_revoked(token):
            raise TokenValidationError(
                f"Token {token.token_id} (or an ancestor in its lineage) has been revoked."
            )

        now = time.time()
        if self.enforce_expiry and token.is_expired(now):
            raise TokenExpiredError(
                f"Token {token.token_id} for subject '{token.subject_id}' expired at {token.expires_at_utc} (current: {now})"
            )

        if self.enforce_signatures and self.secret_key:
            if not token.signature:
                raise TokenTamperedError(
                    f"Token {token.token_id} is missing required cryptographic signature"
                )
            if not token.verify_signature(self.secret_key):
                raise TokenTamperedError(
                    f"Token {token.token_id} signature validation failed. Payload integrity compromised."
                )

        return True

    # -----------------------------------------------------------------------
    # Tool Execution Enforcement
    # -----------------------------------------------------------------------
    def check_tool_execution(self, token: CapabilityToken, tool_name: str) -> bool:
        """Check whether tool execution is authorized by the token."""
        try:
            self.verify_token(token)
            return token.has_tool_permission(tool_name)
        except SecurityError:
            return False

    def enforce_tool_execution(self, token: CapabilityToken, tool_name: str) -> bool:
        """Enforce tool authorization, raising PermissionDeniedError on unauthorized calls."""
        self.verify_token(token)
        if not token.has_tool_permission(tool_name):
            raise PermissionDeniedError(
                f"Unauthorized tool execution: Tool '{tool_name}' is not in permitted tool set "
                f"for subject '{token.subject_id}' (role: '{token.role}', stage: '{token.workflow_stage}'). "
                f"Allowed tools: {sorted(list(token.allowed_tools))}"
            )
        return True

    # -----------------------------------------------------------------------
    # Filesystem Path Confinement
    # -----------------------------------------------------------------------
    def _sanitize_and_resolve_path(self, target_path: Union[str, Path]) -> str:
        """Sanitize and resolve path, checking for null bytes or illegal traversal patterns."""
        path_str = str(target_path)
        if "\0" in path_str:
            raise PathTraversalError("Null byte injection detected in filesystem path")
        
        try:
            resolved = Path(path_str).resolve()
            return str(resolved).replace("\\", "/").rstrip("/")
        except Exception as e:
            raise PathTraversalError(f"Invalid filesystem path: {target_path} ({e})")

    def check_filesystem_access(
        self,
        token: CapabilityToken,
        target_path: Union[str, Path],
        mode: str = "write",
    ) -> bool:
        """Check if filesystem path access (read or write) is within allowed sandbox jails."""
        try:
            self.verify_token(token)
            resolved_target = self._sanitize_and_resolve_path(target_path)
            
            allowed_paths = (
                token.allowed_write_paths if mode == "write" else token.allowed_read_paths
            )
            
            if "*" in allowed_paths:
                return True
            
            for allowed in allowed_paths:
                if allowed == "*":
                    return True
                resolved_allowed = self._sanitize_and_resolve_path(allowed)
                # Exact match or subpath match
                if resolved_target == resolved_allowed or resolved_target.startswith(resolved_allowed + "/"):
                    return True
            return False
        except SecurityError:
            return False

    def enforce_filesystem_access(
        self,
        token: CapabilityToken,
        target_path: Union[str, Path],
        mode: str = "write",
    ) -> str:
        """Enforce path confinement, raising PathTraversalError or PermissionDeniedError if outside jail."""
        self.verify_token(token)
        resolved_target = self._sanitize_and_resolve_path(target_path)
        
        if not self.check_filesystem_access(token, target_path, mode=mode):
            allowed_paths = (
                token.allowed_write_paths if mode == "write" else token.allowed_read_paths
            )
            raise PathTraversalError(
                f"Path confinement violation ({mode}): Target path '{resolved_target}' escapes "
                f"authorized sandbox directories for subject '{token.subject_id}'. "
                f"Allowed {mode} paths: {sorted(list(allowed_paths))}"
            )
        return resolved_target

    # -----------------------------------------------------------------------
    # Network Egress Enforcement
    # -----------------------------------------------------------------------
    def check_network_egress(
        self,
        token: CapabilityToken,
        host: str,
        port: Optional[int] = None,
    ) -> bool:
        """Check whether network egress to target host is permitted."""
        try:
            self.verify_token(token)
            return token.has_network_permission(host)
        except SecurityError:
            return False

    def enforce_network_egress(
        self,
        token: CapabilityToken,
        host: str,
        port: Optional[int] = None,
    ) -> None:
        """Enforce network egress whitelist, raising NetworkEgressError if blocked."""
        self.verify_token(token)
        if not token.has_network_permission(host):
            raise NetworkEgressError(
                f"Network egress blocked: Host '{host}' is not in permitted egress whitelist "
                f"for subject '{token.subject_id}' (role: '{token.role}'). "
                f"Allowed hosts: {sorted(list(token.allowed_network_hosts))}"
            )

    # -----------------------------------------------------------------------
    # Context Guard & Decorators
    # -----------------------------------------------------------------------
    @contextmanager
    def guard_context(
        self,
        token: CapabilityToken,
        tool_name: Optional[str] = None,
        write_paths: Optional[List[Union[str, Path]]] = None,
        read_paths: Optional[List[Union[str, Path]]] = None,
        network_hosts: Optional[List[str]] = None,
    ):
        """Context manager validating all operation permissions upon entry."""
        self.verify_token(token)
        
        if tool_name is not None:
            self.enforce_tool_execution(token, tool_name)
            
        if write_paths:
            for wp in write_paths:
                self.enforce_filesystem_access(token, wp, mode="write")
                
        if read_paths:
            for rp in read_paths:
                self.enforce_filesystem_access(token, rp, mode="read")
                
        if network_hosts:
            for nh in network_hosts:
                self.enforce_network_egress(token, nh)
                
        yield token

    def guarded_tool(
        self,
        required_tool_name: Optional[str] = None,
        write_path_arg: Optional[str] = None,
        read_path_arg: Optional[str] = None,
        network_host_arg: Optional[str] = None,
    ):
        """Decorator guarding tool execution functions against capability token policies."""
        def decorator(fn: Callable) -> Callable:
            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                # Look for token in positional arguments or kwargs
                token = kwargs.get("token") or kwargs.get("capability_token")
                if token is None:
                    for arg in args:
                        if isinstance(arg, CapabilityToken):
                            token = arg
                            break
                            
                if token is None:
                    raise PermissionDeniedError(
                        f"Guarded function '{fn.__name__}' called without a valid CapabilityToken"
                    )

                tool_name = required_tool_name or fn.__name__
                self.enforce_tool_execution(token, tool_name)

                if write_path_arg and write_path_arg in kwargs:
                    self.enforce_filesystem_access(token, kwargs[write_path_arg], mode="write")

                if read_path_arg and read_path_arg in kwargs:
                    self.enforce_filesystem_access(token, kwargs[read_path_arg], mode="read")

                if network_host_arg and network_host_arg in kwargs:
                    self.enforce_network_egress(token, kwargs[network_host_arg])

                return fn(*args, **kwargs)
            return wrapper
        return decorator


# Class alias for TokenGuard
TokenGuard = SecurityGuard

_global_security_guard: Optional[SecurityGuard] = None


def get_security_guard(secret_key: Optional[Union[str, bytes]] = None) -> SecurityGuard:
    """Retrieve or create the process-wide active SecurityGuard / TokenGuard."""
    global _global_security_guard
    if _global_security_guard is None:
        _global_security_guard = SecurityGuard(secret_key=secret_key)
    elif secret_key and not _global_security_guard.secret_key:
        _global_security_guard.secret_key = secret_key
    return _global_security_guard


def reset_security_guard() -> None:
    """Reset the global SecurityGuard instance."""
    global _global_security_guard
    _global_security_guard = None

