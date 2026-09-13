"""Harness 9 Security Package (Milestone M6).

Exports:
- CapabilityToken: Principle-of-least-privilege token model
- SecurityGuard: Sandboxing and permission enforcement guard
- Security Exceptions: PermissionDeniedError, TokenExpiredError, TokenTamperedError,
  PathTraversalError, NetworkEgressError, DelegationLimitExceededError
- Helper & Calculus Functions: calculate_capability_token, sign_capability_token,
  verify_capability_token, create_root_token, derive_child_token
"""

from src.security.tokens import (
    CapabilityToken,
    DelegationLimitExceededError,
    NetworkEgressError,
    PathTraversalError,
    PermissionDeniedError,
    ROLE_PERMISSIONS,
    STAGE_PERMISSIONS,
    SecurityError,
    TokenExpiredError,
    TokenRevocationRegistry,
    TokenTamperedError,
    TokenValidationError,
    calculate_capability_token,
    create_root_token,
    derive_child_token,
    get_token_revocation_registry,
    reset_token_revocation_registry,
    sign_capability_token,
    verify_capability_token,
)
from src.security.guard import (
    SecurityGuard,
    TokenGuard,
    current_capability_token,
    get_security_guard,
    reset_security_guard,
)

__all__ = [
    "CapabilityToken",
    "SecurityGuard",
    "TokenGuard",
    "TokenRevocationRegistry",
    "SecurityError",
    "PermissionDeniedError",
    "TokenExpiredError",
    "TokenTamperedError",
    "TokenValidationError",
    "PathTraversalError",
    "NetworkEgressError",
    "DelegationLimitExceededError",
    "ROLE_PERMISSIONS",
    "STAGE_PERMISSIONS",
    "calculate_capability_token",
    "sign_capability_token",
    "verify_capability_token",
    "create_root_token",
    "derive_child_token",
    "get_token_revocation_registry",
    "reset_token_revocation_registry",
    "get_security_guard",
    "reset_security_guard",
    "current_capability_token",
]

