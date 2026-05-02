from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.logging import set_request_context
from app.core.security import (
    AuthContext,
    decode_token,
    ensure_verified_document,
    get_current_user_from_payload,
    oauth2_scheme,
    request_context_from_request,
    user_has_department_access,
    validate_access_token,
)
from app.db.session import get_db
from app.models.domain.models import Document, User
from app.models.enums import UserRole


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    context = getattr(request.state, "context", None)
    if isinstance(context, AuthContext) and context.user is not None:
        return context.user

    payload = await validate_access_token(token)
    user = get_current_user_from_payload(db, payload)
    request.state.context = AuthContext(
        user=user,
        role=user.role,
        department_id=user.department_id,
        request_id=getattr(request.state, "request_id", payload["jti"]),
        token_jti=payload["jti"],
    )
    set_request_context(
        request_id=getattr(request.state, "request_id", payload["jti"]),
        user_id=str(user.id),
    )
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="inactive user")
    return current_user


def require_role(*roles: UserRole):
    async def dependency(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in roles and current_user.role != UserRole.SUPERADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="insufficient role")
        return current_user

    return dependency


def require_any_role(roles: Iterable[UserRole]):
    return require_role(*tuple(roles))


def require_department_access(path_param_name: str = "department_id"):
    async def dependency(
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        raw_department_id = request.path_params.get(path_param_name) or request.query_params.get(path_param_name)
        if raw_department_id is None:
            return current_user
        target_department_id = UUID(str(raw_department_id))
        if not user_has_department_access(db, current_user, target_department_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="department access denied")
        return current_user

    return dependency


def require_verified_document(path_param_name: str = "document_id"):
    async def dependency(
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
    ) -> Document:
        raw_document_id = request.path_params.get(path_param_name) or request.query_params.get(path_param_name)
        if raw_document_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="document_id is required")
        document = ensure_verified_document(db, UUID(str(raw_document_id)))
        return document

    return dependency


def get_request_context(request: Request) -> AuthContext:
    return request_context_from_request(request)
