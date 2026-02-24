"""SI3DC — Role-Based Access Control (RBAC).

Defines access levels and role-based permission checks.
"""

from __future__ import annotations

from enum import Enum
from functools import wraps
from typing import Callable

from fastapi import Depends, HTTPException, status

from backend.domain.models.professional import HealthProfessionalORM
from backend.infrastructure.auth.oauth2 import get_current_user


class AccessLevel(str, Enum):
    BASIC = "BASIC"       # Can view patient summaries
    MEDIUM = "MEDIUM"     # Can view/write clinical data
    ADMIN = "ADMIN"       # Full access, system configuration


# Role hierarchy: ADMIN > MEDIUM > BASIC
ROLE_HIERARCHY = {
    AccessLevel.BASIC: 1,
    AccessLevel.MEDIUM: 2,
    AccessLevel.ADMIN: 3,
}

# Permission map: resource -> minimum access level
PERMISSIONS = {
    "patient:read": AccessLevel.BASIC,
    "patient:write": AccessLevel.MEDIUM,
    "patient:delete": AccessLevel.ADMIN,
    "clinical:read": AccessLevel.BASIC,
    "clinical:write": AccessLevel.MEDIUM,
    "clinical:delete": AccessLevel.ADMIN,
    "prescription:read": AccessLevel.BASIC,
    "prescription:write": AccessLevel.MEDIUM,
    "exam:read": AccessLevel.BASIC,
    "exam:write": AccessLevel.MEDIUM,
    "allergy:read": AccessLevel.BASIC,
    "allergy:write": AccessLevel.MEDIUM,
    "ai:summary": AccessLevel.BASIC,
    "ai:governance": AccessLevel.MEDIUM,
    "emergency:read": AccessLevel.BASIC,
    "admin:users": AccessLevel.ADMIN,
    "admin:system": AccessLevel.ADMIN,
    "audit:read": AccessLevel.ADMIN,
}


def has_permission(user_role: str, required_permission: str) -> bool:
    """Check if the user's role meets the required permission level."""
    try:
        user_level = ROLE_HIERARCHY.get(AccessLevel(user_role), 0)
    except ValueError:
        return False

    required_level_enum = PERMISSIONS.get(required_permission)
    if required_level_enum is None:
        return False

    required_level = ROLE_HIERARCHY.get(required_level_enum, 999)
    return user_level >= required_level


def require_permission(permission: str) -> Callable:
    """FastAPI dependency that enforces a specific permission."""

    async def _check(
        current_user: HealthProfessionalORM = Depends(get_current_user),
    ) -> HealthProfessionalORM:
        if not has_permission(current_user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Permissão necessária: {permission}",
            )
        return current_user

    return _check


def require_role(minimum_role: AccessLevel) -> Callable:
    """FastAPI dependency that enforces a minimum role level."""

    async def _check(
        current_user: HealthProfessionalORM = Depends(get_current_user),
    ) -> HealthProfessionalORM:
        try:
            user_level = ROLE_HIERARCHY.get(AccessLevel(current_user.role), 0)
        except ValueError:
            user_level = 0

        if user_level < ROLE_HIERARCHY[minimum_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Nível de acesso insuficiente. Mínimo: {minimum_role.value}",
            )
        return current_user

    return _check
