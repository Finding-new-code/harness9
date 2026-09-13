"""Harness 9 Security Capability Token Engine (Milestone M6).

Implements the principle-of-least-privilege capability token model with:
- Child permission calculus: P_child = P_parent ∩ P_role ∩ P_workflow
- HMAC-SHA256 cryptographic signing and tamper detection
- Deterministic token expiration and TTL enforcement
- Delegation depth limits and full lineage tracking
- Path confinement, tool whitelisting, and network egress boundaries
"""

from datetime import datetime, timezone
import hashlib
import hmac
import json
from pathlib import Path
import threading
import time
from typing import Any, Dict, List, Optional, Set, Union
import uuid

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


# ===========================================================================
# Security Exceptions
# ===========================================================================
class SecurityError(Exception):
    """Base exception for all security and capability token errors."""
    pass


class PermissionDeniedError(SecurityError):
    """Raised when an operation or tool execution is not authorized by the token."""
    pass


class TokenExpiredError(SecurityError):
    """Raised when an expired capability token is presented or delegated."""
    pass


class TokenTamperedError(SecurityError):
    """Raised when a token signature does not match or payload has been altered."""
    pass


class PathTraversalError(SecurityError, ValueError):
    """Raised when a filesystem path escapes allowed sandbox boundaries."""
    pass


class NetworkEgressError(SecurityError):
    """Raised when network egress to an unauthorized host is attempted."""
    pass


class DelegationLimitExceededError(SecurityError):
    """Raised when token delegation exceeds maximum allowed depth."""
    pass


class TokenValidationError(PermissionDeniedError):
    """Raised when capability token validation or authorization fails."""
    pass


# ===========================================================================
# Token Revocation Registry
# ===========================================================================
class TokenRevocationRegistry:
    """Thread-safe revocation registry tracking invalidated capability tokens."""

    def __init__(self) -> None:
        self._revoked_tokens: Dict[str, Dict[str, Any]] = {}
        self._parent_map: Dict[str, str] = {}
        self._children_map: Dict[str, Set[str]] = {}
        self._lock = threading.Lock()

    def register_token(
        self,
        token: Union["CapabilityToken", str],
        parent_token_id: Optional[str] = None,
    ) -> None:
        """Register a token and its parent to enable cascading lineage revocation."""
        with self._lock:
            if hasattr(token, "token_id"):
                t_id = token.token_id
                p_id = getattr(token, "parent_token_id", None)
            else:
                t_id = str(token)
                p_id = parent_token_id

            if p_id:
                self._parent_map[t_id] = p_id
                if p_id not in self._children_map:
                    self._children_map[p_id] = set()
                self._children_map[p_id].add(t_id)

    def revoke_token(
        self,
        token_id: str,
        reason: str = "manual_revocation",
        cascade: bool = True,
    ) -> None:
        """Revoke a token by its unique ID, optionally cascading to all descendants."""
        with self._lock:
            self._revoked_tokens[token_id] = {
                "revoked_at_utc": time.time(),
                "reason": reason,
            }
            if cascade:
                queue = list(self._children_map.get(token_id, set()))
                while queue:
                    child_id = queue.pop(0)
                    self._revoked_tokens[child_id] = {
                        "revoked_at_utc": time.time(),
                        "reason": f"cascaded_from_{token_id}",
                    }
                    queue.extend(self._children_map.get(child_id, set()))

    def revoke(
        self,
        token_id: str,
        reason: str = "manual_revocation",
        cascade: bool = True,
    ) -> None:
        """Alias for revoke_token."""
        self.revoke_token(token_id=token_id, reason=reason, cascade=cascade)

    def is_revoked(
        self,
        token: Union["CapabilityToken", str],
        lineage: Optional[List[str]] = None,
    ) -> bool:
        """Check if token itself OR any ancestor in its delegation lineage has been revoked."""
        with self._lock:
            if isinstance(token, str):
                token_id = token
                check_lineage = list(lineage or [])
            else:
                token_id = token.token_id
                check_lineage = list(getattr(token, "delegation_lineage", []) or [])

            if token_id in self._revoked_tokens:
                return True

            for ancestor_id in check_lineage:
                if ancestor_id in self._revoked_tokens:
                    return True

            # Walk parent map upwards
            curr = token_id
            while curr in self._parent_map:
                p = self._parent_map[curr]
                if p in self._revoked_tokens:
                    return True
                curr = p

            return False

    def get_revocation_info(self, token_id: str) -> Optional[Dict[str, Any]]:
        """Return metadata for a revoked token, or None if not revoked."""
        with self._lock:
            return self._revoked_tokens.get(token_id)

    def clear(self) -> None:
        """Clear all revocation records and lineage graphs."""
        with self._lock:
            self._revoked_tokens.clear()
            self._parent_map.clear()
            self._children_map.clear()


_global_revocation_registry = TokenRevocationRegistry()


def get_token_revocation_registry() -> TokenRevocationRegistry:
    """Get the process-wide active token revocation registry."""
    return _global_revocation_registry


def reset_token_revocation_registry() -> None:
    """Reset the process-wide token revocation registry."""
    _global_revocation_registry.clear()


# ===========================================================================
# Standard Role & Workflow Stage Permission Sets
# ===========================================================================
ALL_PERMISSIONS: Set[str] = {
    "read_file",
    "write_file",
    "web_search",
    "web_extract",
    "h9.research",
    "h9_research",
    "h9.discover_assets",
    "h9_discover_assets",
    "h9.generate_script",
    "h9_generate_script",
    "h9.render",
    "h9_render",
    "h9.publish",
    "h9_publish",
}

ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    "orchestrator": {"*", *ALL_PERMISSIONS},
    "researcher": {"web_search", "web_extract", "read_file", "h9.research", "h9_research"},
    "scriptwriter": {"read_file", "write_file", "h9.generate_script", "h9_generate_script"},
    "writer": {"read_file", "write_file", "h9.generate_script", "h9_generate_script"},
    "asset_specialist": {"read_file", "write_file", "h9.discover_assets", "h9_discover_assets"},
    "video_editor": {"read_file", "write_file", "h9.render", "h9_render"},
    "editor": {"read_file", "write_file", "h9.render", "h9_render"},
    "publisher": {"read_file", "h9.publish", "h9_publish"},
    "reviewer": {"read_file"},
}

STAGE_PERMISSIONS: Dict[str, Set[str]] = {
    "ROOT": {"*", *ALL_PERMISSIONS},
    "RESEARCH_IN_PROGRESS": {"web_search", "web_extract", "read_file", "h9.research", "h9_research"},
    "research": {"web_search", "web_extract", "read_file", "h9.research", "h9_research"},
    "SCRIPTING_IN_PROGRESS": {"read_file", "write_file", "h9.generate_script", "h9_generate_script"},
    "scripting": {"read_file", "write_file", "h9.generate_script", "h9_generate_script"},
    "ASSET_DISCOVERY_IN_PROGRESS": {"read_file", "write_file", "h9.discover_assets", "h9_discover_assets"},
    "assets": {"read_file", "write_file", "h9.discover_assets", "h9_discover_assets"},
    "RENDERING_IN_PROGRESS": {"read_file", "write_file", "h9.render", "h9_render"},
    "rendering": {"read_file", "write_file", "h9.render", "h9_render"},
    "assembly": {"read_file", "write_file", "h9.render", "h9_render"},
    "PUBLISHING_IN_PROGRESS": {"read_file", "h9.publish", "h9_publish"},
    "publishing": {"read_file", "h9.publish", "h9_publish"},
    "distribution": {"read_file", "h9.publish", "h9_publish"},
}



# ===========================================================================
# Capability Token Model
# ===========================================================================
class CapabilityToken(BaseModel):
    """Principle-of-least-privilege capability token for agents and pipeline workers."""
    model_config = ConfigDict(
        extra="allow",
        validate_assignment=True,
        populate_by_name=True,
    )

    token_id: str = Field(
        default_factory=lambda: f"cap_{uuid.uuid4().hex[:16]}",
        description="Unique identifier for this capability token",
    )
    parent_token_id: Optional[str] = Field(
        default=None,
        description="Token ID of the parent delegator, or None for root tokens",
    )
    subject_id: str = Field(
        ...,
        description="Identifier of the principal/agent holding this token",
    )
    role: str = Field(
        default="worker",
        description="Functional role (e.g. orchestrator, researcher, scriptwriter)",
    )
    workflow_id: str = Field(
        default="workflow_root",
        description="Production workflow / project execution ID",
    )
    workflow_stage: Optional[str] = Field(
        default=None,
        description="Optional active lifecycle stage (e.g. RESEARCH_IN_PROGRESS)",
    )
    allowed_tools: Set[str] = Field(
        default_factory=set,
        description="Set of permitted tool names (or '*' for unrestricted)",
    )
    allowed_write_paths: Set[str] = Field(
        default_factory=set,
        description="Set of normalized directory path prefixes allowed for write",
    )
    allowed_read_paths: Set[str] = Field(
        default_factory=set,
        description="Set of normalized directory path prefixes allowed for read",
    )
    allowed_network_hosts: Set[str] = Field(
        default_factory=set,
        description="Set of allowed egress hostnames/domains (or '*' for full access)",
    )
    created_at_utc: float = Field(
        default_factory=lambda: time.time(),
        description="Token creation epoch timestamp",
    )

    @property
    def subject(self) -> str:
        """Alias for subject_id."""
        if hasattr(self, "__pydantic_extra__") and self.__pydantic_extra__ and "subject" in self.__pydantic_extra__:
            return self.__pydantic_extra__["subject"]
        return self.subject_id

    @subject.setter
    def subject(self, value: str) -> None:
        object.__setattr__(self, "subject_id", value)
        if hasattr(self, "__pydantic_extra__") and self.__pydantic_extra__ is not None:
            self.__pydantic_extra__["subject"] = value

    @property
    def issued_at_utc(self) -> float:
        """Alias for created_at_utc."""
        return self.created_at_utc

    @issued_at_utc.setter
    def issued_at_utc(self, value: float) -> None:
        object.__setattr__(self, "created_at_utc", value)

    @model_validator(mode="before")
    @classmethod
    def _handle_issued_at_utc(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "issued_at_utc" in data and "created_at_utc" not in data:
                data["created_at_utc"] = data["issued_at_utc"]
            if "subject" in data and "subject_id" not in data:
                data["subject_id"] = data["subject"]
        return data
    expires_at_utc: float = Field(
        default_factory=lambda: time.time() + 3600.0,
        description="Token expiration epoch timestamp",
    )
    delegation_depth: int = Field(
        default=0,
        ge=0,
        description="Current delegation hierarchy depth (0 = root)",
    )
    max_delegation_depth: int = Field(
        default=3,
        ge=0,
        description="Maximum permitted delegation depth",
    )
    delegation_lineage: List[str] = Field(
        default_factory=list,
        description="Ordered list of ancestor token IDs from root down to parent",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary audit or workflow metadata",
    )
    signature: Optional[str] = Field(
        default=None,
        description="HMAC-SHA256 signature validating token integrity",
    )

    @field_validator("allowed_write_paths", "allowed_read_paths", mode="before")
    @classmethod
    def _normalize_paths(cls, v: Any) -> Set[str]:
        if isinstance(v, (list, tuple, set)):
            normalized = set()
            for p in v:
                if p:
                    # Normalize separators and strip redundant slashes
                    norm = str(p).replace("\\", "/").rstrip("/")
                    normalized.add(norm)
            return normalized
        return set()

    @field_validator("allowed_tools", "allowed_network_hosts", mode="before")
    @classmethod
    def _normalize_sets(cls, v: Any) -> Set[str]:
        if isinstance(v, (list, tuple, set)):
            return {str(item).strip() for item in v if item}
        return set()

    def is_expired(self, current_time: Optional[float] = None) -> bool:
        """Check if the capability token has expired."""
        now = current_time if current_time is not None else time.time()
        return now > self.expires_at_utc

    def to_canonical_payload(self) -> Dict[str, Any]:
        """Produce a deterministic dictionary representation for cryptographic signing."""
        subj = (
            self.__pydantic_extra__.get("subject")
            if hasattr(self, "__pydantic_extra__") and self.__pydantic_extra__
            else None
        ) or self.subject_id
        return {
            "token_id": self.token_id,
            "parent_token_id": self.parent_token_id,
            "subject_id": subj,
            "role": self.role,
            "workflow_id": self.workflow_id,
            "workflow_stage": self.workflow_stage,
            "allowed_tools": sorted(list(self.allowed_tools)),
            "allowed_write_paths": sorted(list(self.allowed_write_paths)),
            "allowed_read_paths": sorted(list(self.allowed_read_paths)),
            "allowed_network_hosts": sorted(list(self.allowed_network_hosts)),
            "created_at_utc": round(self.created_at_utc, 4),
            "expires_at_utc": round(self.expires_at_utc, 4),
            "delegation_depth": self.delegation_depth,
            "max_delegation_depth": self.max_delegation_depth,
            "delegation_lineage": self.delegation_lineage,
            "metadata": self.metadata,
        }

    def sign(self, secret_key: Union[str, bytes]) -> str:
        """Sign the token payload using HMAC-SHA256 and store the signature."""
        sig = sign_capability_token(self.to_canonical_payload(), secret_key)
        self.signature = sig
        return sig

    def verify_signature(self, secret_key: Union[str, bytes]) -> bool:
        """Verify the cryptographic signature of this token."""
        if not self.signature:
            return False
        return verify_capability_token(
            self.to_canonical_payload(),
            self.signature,
            secret_key,
        )

    def has_tool_permission(self, tool_name: str) -> bool:
        """Check whether the token permits execution of a specific tool."""
        if "*" in self.allowed_tools:
            return True
        return tool_name in self.allowed_tools

    def has_write_permission(self, target_path: Union[str, Path]) -> bool:
        """Check whether writing to the target path is allowed under path confinement."""
        if not self.allowed_write_paths:
            return False
        
        target_str = str(Path(target_path).resolve()).replace("\\", "/").rstrip("/")
        for allowed in self.allowed_write_paths:
            if allowed == "*":
                return True
            allowed_str = str(Path(allowed).resolve()).replace("\\", "/").rstrip("/")
            if target_str == allowed_str or target_str.startswith(allowed_str + "/"):
                return True
        return False

    def has_read_permission(self, target_path: Union[str, Path]) -> bool:
        """Check whether reading the target path is allowed under path confinement."""
        if not self.allowed_read_paths:
            return False
        
        target_str = str(Path(target_path).resolve()).replace("\\", "/").rstrip("/")
        for allowed in self.allowed_read_paths:
            if allowed == "*":
                return True
            allowed_str = str(Path(allowed).resolve()).replace("\\", "/").rstrip("/")
            if target_str == allowed_str or target_str.startswith(allowed_str + "/"):
                return True
        return False

    def has_network_permission(self, host: str) -> bool:
        """Check whether network egress to a specific hostname/domain is allowed."""
        if "*" in self.allowed_network_hosts:
            return True
        host_clean = host.strip().lower()
        for allowed in self.allowed_network_hosts:
            allowed_clean = allowed.strip().lower()
            if allowed_clean == host_clean:
                return True
            # Wildcard domain suffix matching (e.g. *.wikimedia.org)
            if allowed_clean.startswith("*.") and host_clean.endswith(allowed_clean[1:]):
                return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize token to dictionary."""
        data = self.model_dump()
        data["allowed_tools"] = list(self.allowed_tools)
        data["allowed_write_paths"] = list(self.allowed_write_paths)
        data["allowed_read_paths"] = list(self.allowed_read_paths)
        data["allowed_network_hosts"] = list(self.allowed_network_hosts)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CapabilityToken":
        """Deserialize token from dictionary."""
        return cls.model_validate(data)

    @classmethod
    def create(
        cls,
        subject_id: str = "orchestrator_root",
        role: str = "orchestrator",
        workflow_id: str = "workflow_root",
        workflow_stage: str = "ROOT",
        allowed_tools: Optional[Set[str]] = None,
        allowed_write_paths: Optional[Set[str]] = None,
        allowed_read_paths: Optional[Set[str]] = None,
        allowed_network_hosts: Optional[Set[str]] = None,
        lifetime_seconds: Optional[float] = None,
        ttl_seconds: float = 3600.0,
        max_delegation_depth: int = 3,
        secret_key: Optional[Union[str, bytes]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> "CapabilityToken":
        """Factory method to instantiate a new capability token with optional signature."""
        effective_ttl = lifetime_seconds if lifetime_seconds is not None else ttl_seconds
        token = create_root_token(
            subject_id=subject_id,
            role=role,
            workflow_id=workflow_id,
            allowed_tools=allowed_tools,
            allowed_write_paths=allowed_write_paths,
            allowed_read_paths=allowed_read_paths,
            allowed_network_hosts=allowed_network_hosts,
            ttl_seconds=effective_ttl,
            max_delegation_depth=max_delegation_depth,
            secret_key=secret_key,
            metadata=metadata,
        )
        if workflow_stage and workflow_stage != "ROOT":
            token.workflow_stage = workflow_stage
            if secret_key:
                token.sign(secret_key)
        return token


# ===========================================================================
# Cryptographic & Calculus Helper Functions
# ===========================================================================
def calculate_capability_token(
    parent_perms: Set[str],
    role_perms: Set[str],
    workflow_perms: Set[str],
) -> Set[str]:
    """Calculate child permission set via set intersection:
    P_child = P_parent ∩ P_role ∩ P_workflow
    """
    # Handle wildcard permissions if present in parent
    effective_parent = parent_perms
    if "*" in parent_perms:
        return role_perms.intersection(workflow_perms)
    return effective_parent.intersection(role_perms).intersection(workflow_perms)


def sign_capability_token(
    token_data: Dict[str, Any],
    secret_key: Union[str, bytes],
) -> str:
    """Generate HMAC-SHA256 hex digest signature for canonical token payload."""
    key_bytes = secret_key.encode("utf-8") if isinstance(secret_key, str) else secret_key
    payload_str = json.dumps(token_data, sort_keys=True, separators=(",", ":"))
    return hmac.new(key_bytes, payload_str.encode("utf-8"), hashlib.sha256).hexdigest()


DEFAULT_SECRET_KEY: str = "h9_capability_secret_key_default"


def verify_capability_token(
    token_or_data: Union[CapabilityToken, Dict[str, Any]],
    signature: Optional[str] = None,
    secret_key: Optional[Union[str, bytes]] = None,
) -> bool:
    """Verify HMAC-SHA256 signature and validity of a token or payload dictionary.

    Supports:
    1. Single-arg mode: verify_capability_token(token)
       Enforces revocation, expiration, and cryptographic HMAC signature.
       Raises TokenExpiredError on expired tokens.
       Raises PermissionDeniedError on revoked tokens.
       Raises TokenTamperedError on signature failure or tampered payload.
       Returns True on success.
    2. Three-arg mode: verify_capability_token(token_data, signature, secret_key)
       Performs timing-attack resistant HMAC comparison.
       Returns True if valid, False otherwise.
    """
    if isinstance(token_or_data, CapabilityToken):
        token = token_or_data

        # 1. Check expiration
        now = time.time()
        if token.is_expired(now):
            raise TokenExpiredError(
                f"Capability token {token.token_id} expired at {token.expires_at_utc} (current: {now})"
            )

        # 2. Check revocation
        if get_token_revocation_registry().is_revoked(token):
            raise PermissionDeniedError(
                f"Capability token {token.token_id} has been revoked."
            )

        # 3. Check cryptographic signature
        if not token.signature:
            raise TokenTamperedError(
                f"Capability token {token.token_id} is missing required cryptographic signature"
            )

        key = secret_key or getattr(token, "_secret_key", None) or DEFAULT_SECRET_KEY
        expected_signature = sign_capability_token(token.to_canonical_payload(), key)
        if not hmac.compare_digest(expected_signature, token.signature):
            raise TokenTamperedError(
                f"Capability token {token.token_id} signature verification failed. Possible payload tampering."
            )
        return True

    # 3-arg dictionary mode
    if not signature or not secret_key:
        return False
    expected_signature = sign_capability_token(token_or_data, secret_key)
    return hmac.compare_digest(expected_signature, signature)


# ===========================================================================
# Factory & Delegation Engine
# ===========================================================================
def create_root_token(
    subject_id: Optional[str] = None,
    role: str = "orchestrator",
    workflow_id: str = "workflow_root",
    allowed_tools: Optional[Set[str]] = None,
    allowed_write_paths: Optional[Set[str]] = None,
    allowed_read_paths: Optional[Set[str]] = None,
    allowed_network_hosts: Optional[Set[str]] = None,
    ttl_seconds: float = 3600.0,
    max_delegation_depth: int = 3,
    secret_key: Optional[Union[str, bytes]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    subject: Optional[str] = None,
    **kwargs: Any,
) -> CapabilityToken:
    """Create a root capability token with initial full/configured authorities."""
    now = time.time()
    effective_subject = subject or subject_id or "orchestrator_root"
    effective_key = secret_key or DEFAULT_SECRET_KEY

    token = CapabilityToken(
        token_id=f"root_{uuid.uuid4().hex[:16]}",
        parent_token_id=None,
        subject_id=effective_subject,
        role=role,
        workflow_id=workflow_id,
        workflow_stage="ROOT",
        allowed_tools=allowed_tools if allowed_tools is not None else {"*"},
        allowed_write_paths=allowed_write_paths if allowed_write_paths is not None else {"*"},
        allowed_read_paths=allowed_read_paths if allowed_read_paths is not None else {"*"},
        allowed_network_hosts=allowed_network_hosts if allowed_network_hosts is not None else {"*"},
        created_at_utc=now,
        expires_at_utc=now + ttl_seconds,
        delegation_depth=0,
        max_delegation_depth=max_delegation_depth,
        delegation_lineage=[],
        metadata=metadata or {},
    )
    object.__setattr__(token, "_secret_key", effective_key)
    token.sign(effective_key)
    get_token_revocation_registry().register_token(token)
    return token


def derive_child_token(
    parent_token: CapabilityToken,
    child_subject_id: Optional[str] = None,
    role_allowed_tools: Optional[Set[str]] = None,
    workflow_allowed_tools: Optional[Set[str]] = None,
    role_allowed_write_paths: Optional[Set[str]] = None,
    workflow_allowed_write_paths: Optional[Set[str]] = None,
    role_allowed_read_paths: Optional[Set[str]] = None,
    workflow_allowed_read_paths: Optional[Set[str]] = None,
    role_allowed_network_hosts: Optional[Set[str]] = None,
    workflow_allowed_network_hosts: Optional[Set[str]] = None,
    child_role: Optional[str] = None,
    workflow_stage: Optional[str] = None,
    child_workflow_stage: Optional[str] = None,
    ttl_seconds: Optional[float] = None,
    lifetime_seconds: Optional[float] = None,
    secret_key: Optional[Union[str, bytes]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    child_subject: Optional[str] = None,
    role: Optional[str] = None,
    workflow: Optional[str] = None,
    **kwargs: Any,
) -> CapabilityToken:
    """Derive a restricted child capability token adhering strictly to least privilege:
    
    1. Validates parent expiration and signature
    2. Enforces delegation depth constraints
    3. Calculates tool intersection: P_tools = P_parent ∩ P_role ∩ P_workflow
    4. Confinement: Child paths and egress hosts cannot exceed parent authority
    5. Enforces expiration <= parent expiration
    6. Appends parent ID to delegation lineage
    """
    now = time.time()
    
    # 1. Check parent expiration
    if parent_token.is_expired(now):
        raise TokenExpiredError(
            f"Cannot derive child token: Parent token {parent_token.token_id} expired at {parent_token.expires_at_utc} (current: {now})"
        )

    # 1b. Check parent revocation
    if get_token_revocation_registry().is_revoked(parent_token):
        raise TokenValidationError(
            f"Cannot derive child token: Parent token {parent_token.token_id} (or its ancestor) has been revoked."
        )

    effective_key = secret_key or getattr(parent_token, "_secret_key", None) or DEFAULT_SECRET_KEY

    # 2. Check parent signature if effective_key provided
    if parent_token.signature:
        if not parent_token.verify_signature(effective_key):
            raise TokenTamperedError(
                f"Parent token {parent_token.token_id} signature verification failed. Possible payload tampering."
            )

    # 3. Check delegation depth
    if parent_token.delegation_depth >= parent_token.max_delegation_depth:
        raise DelegationLimitExceededError(
            f"Delegation depth limit reached ({parent_token.delegation_depth}/{parent_token.max_delegation_depth})"
        )

    effective_subject = child_subject or child_subject_id or "child_worker"
    effective_child_role = role or child_role or parent_token.role
    effective_stage = workflow or child_workflow_stage or workflow_stage or parent_token.workflow_stage
    effective_ttl = lifetime_seconds if lifetime_seconds is not None else ttl_seconds

    if role_allowed_tools is None:
        role_allowed_tools = ROLE_PERMISSIONS.get(effective_child_role, parent_token.allowed_tools) if effective_child_role else parent_token.allowed_tools
    if workflow_allowed_tools is None:
        workflow_allowed_tools = STAGE_PERMISSIONS.get(effective_stage, {"*"}) if effective_stage else {"*"}

    # 4. Tool intersection calculus
    child_tools = calculate_capability_token(
        parent_token.allowed_tools,
        role_allowed_tools,
        workflow_allowed_tools,
    )

    # 5. Path confinement calculus
    def _intersect_paths(
        parent_paths: Set[str],
        role_paths: Optional[Set[str]],
        wf_paths: Optional[Set[str]],
    ) -> Set[str]:
        if "*" in parent_paths:
            base = role_paths if role_paths is not None else {"*"}
            if wf_paths is not None:
                base = base.intersection(wf_paths) if "*" not in base else wf_paths
            return base
        
        # Filter role & workflow paths to only those permitted by parent
        candidates = set(parent_paths)
        if role_paths is not None and "*" not in role_paths:
            candidates = candidates.intersection(role_paths)
        if wf_paths is not None and "*" not in wf_paths:
            candidates = candidates.intersection(wf_paths)
        return candidates

    child_write_paths = _intersect_paths(
        parent_token.allowed_write_paths,
        role_allowed_write_paths,
        workflow_allowed_write_paths,
    )
    
    child_read_paths = _intersect_paths(
        parent_token.allowed_read_paths,
        role_allowed_read_paths,
        workflow_allowed_read_paths,
    )

    # 6. Network host intersection
    def _intersect_hosts(
        parent_hosts: Set[str],
        role_hosts: Optional[Set[str]],
        wf_hosts: Optional[Set[str]],
    ) -> Set[str]:
        if "*" in parent_hosts:
            base = role_hosts if role_hosts is not None else {"*"}
            if wf_hosts is not None:
                base = base.intersection(wf_hosts) if "*" not in base else wf_hosts
            return base
        
        candidates = set(parent_hosts)
        if role_hosts is not None and "*" not in role_hosts:
            candidates = candidates.intersection(role_hosts)
        if wf_hosts is not None and "*" not in wf_hosts:
            candidates = candidates.intersection(wf_hosts)
        return candidates

    child_hosts = _intersect_hosts(
        parent_token.allowed_network_hosts,
        role_allowed_network_hosts,
        workflow_allowed_network_hosts,
    )

    # 7. Expiry calculation: child cannot outlive parent
    requested_expiry = (now + effective_ttl) if effective_ttl is not None else parent_token.expires_at_utc
    child_expires_at = min(requested_expiry, parent_token.expires_at_utc)

    # 8. Build child token with lineage
    lineage = list(parent_token.delegation_lineage) + [parent_token.token_id]
    
    child_token = CapabilityToken(
        token_id=f"child_{uuid.uuid4().hex[:16]}",
        parent_token_id=parent_token.token_id,
        subject_id=effective_subject,
        role=effective_child_role,
        workflow_id=parent_token.workflow_id,
        workflow_stage=effective_stage,
        allowed_tools=child_tools,
        allowed_write_paths=child_write_paths,
        allowed_read_paths=child_read_paths,
        allowed_network_hosts=child_hosts,
        created_at_utc=now,
        expires_at_utc=child_expires_at,
        delegation_depth=parent_token.delegation_depth + 1,
        max_delegation_depth=parent_token.max_delegation_depth,
        delegation_lineage=lineage,
        metadata=metadata or {},
    )

    object.__setattr__(child_token, "_secret_key", effective_key)
    child_token.sign(effective_key)
    get_token_revocation_registry().register_token(child_token, parent_token_id=parent_token.token_id)
    return child_token
