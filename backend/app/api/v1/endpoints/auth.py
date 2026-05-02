from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_current_user, require_department_access, require_role
from app.core.security import (
    AuthContext,
    blacklist_jti,
    change_password,
    create_access_token,
    decode_token,
    ensure_verified_document,
    get_current_user_from_payload,
    get_redis_client,
    hash_password,
    issue_token_pair,
    revoke_refresh_token,
    set_first_login_password_change,
    token_hash,
    validate_access_token,
    validate_password_strength,
    verify_token_payload,
)
from app.db.session import get_db
from app.models.domain.models import Department, RefreshToken, User
from app.models.enums import UserRole
from app.models.schemas.auth import (
    AuthTokenResponse,
    CurrentUserResponse,
    LogoutRequest,
    LogoutResponse,
    PasswordChangeRequest,
    PasswordChangeResponse,
    RefreshTokenRequest,
)
from app.models.schemas.base import normalize_optional_text

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthTokenResponse)
async def login(
    request: Request,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    from app.core.security import authenticate_user

    authenticated_user = authenticate_user(db, form_data.username, form_data.password)
    if authenticated_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")

    if authenticated_user.last_login is None and not authenticated_user.must_change_password:
        set_first_login_password_change(authenticated_user, db)
        db.refresh(authenticated_user)

    tokens = issue_token_pair(db, authenticated_user, request)
    authenticated_user.last_login = datetime.now(timezone.utc)
    db.add(authenticated_user)
    db.commit()
    db.refresh(authenticated_user)

    return AuthTokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type="bearer",
        expires_in_seconds=int((tokens["access_expires_at"] - datetime.now(timezone.utc)).total_seconds()),
        refresh_expires_in_seconds=int((tokens["refresh_expires_at"] - datetime.now(timezone.utc)).total_seconds()),
        requires_password_change=authenticated_user.must_change_password,
    )


@router.post("/refresh", response_model=AuthTokenResponse)
async def refresh_token(
    payload: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    token_payload = decode_token(payload.refresh_token)
    verify_token_payload(token_payload, expected_type="refresh")

    refresh_record = db.execute(
        select(RefreshToken).where(RefreshToken.jti == token_payload["jti"])
    ).scalar_one_or_none()
    if refresh_record is None or refresh_record.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh token is no longer valid")
    if refresh_record.token_hash != token_hash(payload.refresh_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh token mismatch")
    if refresh_record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh token expired")

    user = db.get(User, UUID(token_payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="inactive user")

    old_jti = token_payload["jti"]
    old_expires = datetime.fromtimestamp(token_payload["exp"], tz=timezone.utc)
    await blacklist_jti(old_jti, old_expires)
    refresh_record.revoked_at = datetime.now(timezone.utc)
    db.add(refresh_record)
    db.commit()

    tokens = issue_token_pair(db, user, request)
    refresh_record.replaced_by_jti = tokens["refresh_jti"]
    db.add(refresh_record)
    db.commit()

    return AuthTokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type="bearer",
        expires_in_seconds=int((tokens["access_expires_at"] - datetime.now(timezone.utc)).total_seconds()),
        refresh_expires_in_seconds=int((tokens["refresh_expires_at"] - datetime.now(timezone.utc)).total_seconds()),
        requires_password_change=user.must_change_password,
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    payload: LogoutRequest | None = Body(default=None),
):
    from app.core.security import oauth2_scheme

    access_token = await oauth2_scheme(request)
    token_payload = decode_token(access_token)
    verify_token_payload(token_payload, expected_type="access")
    await blacklist_jti(token_payload["jti"], datetime.fromtimestamp(token_payload["exp"], tz=timezone.utc))

    if payload and payload.refresh_token:
        refresh_payload = decode_token(payload.refresh_token)
        verify_token_payload(refresh_payload, expected_type="refresh")
        await blacklist_jti(refresh_payload["jti"], datetime.fromtimestamp(refresh_payload["exp"], tz=timezone.utc))
        revoke_refresh_token(db, payload.refresh_token)

    return LogoutResponse(message="Logged out successfully.")


@router.get("/me", response_model=CurrentUserResponse)
async def me(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    db.refresh(current_user, ["department"])
    return CurrentUserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        department_id=current_user.department_id,
        department_name=current_user.department.name,
        is_active=current_user.is_active,
        must_change_password=current_user.must_change_password,
    )


@router.post("/change-password", response_model=PasswordChangeResponse)
async def change_current_password(
    payload: PasswordChangeRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated_user = change_password(db, current_user, payload.current_password, payload.new_password)
    return PasswordChangeResponse(
        message="Password updated successfully.",
        password_changed_at=updated_user.password_changed_at.isoformat(),
    )
