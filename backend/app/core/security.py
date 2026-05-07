from __future__ import annotations

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache, wraps
from typing import Any, Callable

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.domain.models import Department, Document, RefreshToken, User
from app.models.enums import ProcessingStatus, UserRole


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.PASSWORD_HASH_ROUNDS,
)

ROLE_RANK = {
    UserRole.VIEWER: 0,
    UserRole.OFFICER: 1,
    UserRole.REVIEWER: 2,
    UserRole.ADMIN: 3,
    UserRole.SUPERADMIN: 4,
}

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
}


@dataclass(slots=True)
class AuthContext:
    user: User | None
    role: UserRole | None
    department_id: uuid.UUID | None
    request_id: str
    token_jti: str | None = None


def get_db_session() -> Session:
    return SessionLocal()


def validate_password_strength(password: str) -> None:
    if len(password) < 12:
        raise ValueError("password must be at least 12 characters long")
    checks = [
        any(char.islower() for char in password),
        any(char.isupper() for char in password),
        any(char.isdigit() for char in password),
        any(not char.isalnum() for char in password),
    ]
    if not all(checks):
        raise ValueError("password must include upper, lower, digit, and special characters")


def hash_password(password: str) -> str:
    validate_password_strength(password)
    try:
        import bcrypt
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
    except Exception:
        return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        # Fallback to passlib if bcrypt fails
        return pwd_context.verify(password, hashed_password)


def password_needs_upgrade(hashed_password: str) -> bool:
    return pwd_context.needs_update(hashed_password)


def upgrade_password_hash(password: str, hashed_password: str) -> str | None:
    if password_needs_upgrade(hashed_password):
        return hash_password(password)
    return None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _jti() -> str:
    return uuid.uuid4().hex


def _token_expiry(minutes: int | None = None, days: int | None = None) -> datetime:
    if minutes is not None:
        return _now() + timedelta(minutes=minutes)
    if days is not None:
        return _now() + timedelta(days=days)
    raise ValueError("either minutes or days must be supplied")


def _encode_token(user: User, token_type: str, expires_at: datetime) -> tuple[str, str]:
    jti = _jti()
    payload = {
        "sub": str(user.id),
        "role": user.role.value,
        "department_id": str(user.department_id),
        "token_type": token_type,
        "exp": expires_at,
        "iat": _now(),
        "jti": jti,
    }
    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )
    return token, jti


def create_access_token(user: User) -> tuple[str, str, datetime]:
    expires_at = _token_expiry(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token, jti = _encode_token(user, "access", expires_at)
    return token, jti, expires_at


def create_refresh_token(user: User) -> tuple[str, str, datetime]:
    expires_at = _token_expiry(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    token, jti = _encode_token(user, "refresh", expires_at)
    return token, jti, expires_at


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY.get_secret_value(),
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["sub", "role", "department_id", "exp", "iat", "jti"]},
    )


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@lru_cache(maxsize=1)
def get_redis_client() -> Redis:
    return Redis.from_url(str(settings.REDIS_URL), max_connections=settings.REDIS_MAX_CONNECTIONS, decode_responses=True)


async def blacklist_jti(jti: str, expires_at: datetime) -> None:
    ttl = max(int((expires_at - _now()).total_seconds()), 1)
    await get_redis_client().set(f"blacklist:jti:{jti}", "1", ex=ttl)


async def is_jti_blacklisted(jti: str) -> bool:
    return await get_redis_client().exists(f"blacklist:jti:{jti}") > 0


def _refresh_token_query(db: Session, jti: str | None = None, token: str | None = None) -> RefreshToken | None:
    query = select(RefreshToken)
    if jti is not None:
        query = query.where(RefreshToken.jti == jti)
    elif token is not None:
        query = query.where(RefreshToken.token_hash == token_hash(token))
    else:
        return None
    return db.execute(query).scalar_one_or_none()


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.execute(select(User).where(User.email == email.lower().strip())).scalar_one_or_none()
    if user is None or not verify_password(password, user.hashed_password):
        return None

    upgraded_hash = upgrade_password_hash(password, user.hashed_password)
    if upgraded_hash is not None:
        user.hashed_password = upgraded_hash
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def issue_token_pair(db: Session, user: User, request: Request | None = None) -> dict[str, Any]:
    access_token, access_jti, access_expires_at = create_access_token(user)
    refresh_token, refresh_jti, refresh_expires_at = create_refresh_token(user)

    refresh_record = RefreshToken(
        user_id=user.id,
        jti=refresh_jti,
        token_hash=token_hash(refresh_token),
        expires_at=refresh_expires_at,
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    db.add(refresh_record)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "access_jti": access_jti,
        "refresh_jti": refresh_jti,
        "access_expires_at": access_expires_at,
        "refresh_expires_at": refresh_expires_at,
    }


def revoke_refresh_token(db: Session, refresh_token: str, replacement_jti: str | None = None) -> None:
    record = _refresh_token_query(db, token=refresh_token)
    if record is None:
        return
    record.revoked_at = _now()
    record.replaced_by_jti = replacement_jti
    db.add(record)
    db.commit()


def change_password(db: Session, user: User, current_password: str, new_password: str) -> User:
    if not verify_password(current_password, user.hashed_password):
        raise ValueError("current password is invalid")
    validate_password_strength(new_password)
    user.hashed_password = hash_password(new_password)
    user.must_change_password = False
    user.password_changed_at = _now()
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def set_first_login_password_change(user: User, db: Session) -> None:
    user.must_change_password = True
    db.add(user)
    db.commit()


def verify_token_payload(payload: dict[str, Any], expected_type: str = "access") -> dict[str, Any]:
    if payload.get("token_type") != expected_type:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token type")
    return payload


async def validate_access_token(token: str) -> dict[str, Any]:
    payload = decode_token(token)
    verify_token_payload(payload, "access")
    if await is_jti_blacklisted(payload["jti"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token has been revoked")
    return payload


def get_current_user_from_payload(db: Session, payload: dict[str, Any]) -> User:
    user = db.get(User, uuid.UUID(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="inactive or missing user")
    return user


def _department_is_ancestor(db: Session, ancestor_id: uuid.UUID, descendant_id: uuid.UUID) -> bool:
    current_id: uuid.UUID | None = descendant_id
    visited: set[uuid.UUID] = set()
    while current_id is not None and current_id not in visited:
        if current_id == ancestor_id:
            return True
        visited.add(current_id)
        current_id = db.execute(
            select(Department.parent_department_id).where(Department.id == current_id)
        ).scalar_one_or_none()
    return False


def user_has_department_access(db: Session, user: User, target_department_id: uuid.UUID | None) -> bool:
    if target_department_id is None or user.role == UserRole.SUPERADMIN:
        return True
    if user.department_id == target_department_id:
        return True
    return _department_is_ancestor(db, user.department_id, target_department_id)


def ensure_verified_document(db: Session, document_id: uuid.UUID) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="document not found")
    if document.processing_status != ProcessingStatus.VERIFIED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="document must be verified first")
    return document


def role_guard(*roles: UserRole):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.__required_roles__ = roles  # type: ignore[attr-defined]
        return wrapper

    return decorator


def request_context_from_request(request: Request) -> AuthContext:
    context = getattr(request.state, "context", None)
    if isinstance(context, AuthContext):
        return context
    return AuthContext(
        user=None,
        role=None,
        department_id=None,
        request_id=getattr(request.state, "request_id", secrets.token_hex(16)),
    )


def build_security_headers() -> dict[str, str]:
    return dict(SECURITY_HEADERS)


def get_cors_allowed_origins() -> list[str]:
    return list(settings.CORS_ALLOWED_ORIGINS)


def get_or_create_bypass_user(db: Session) -> User:
    """Get or create a bypass user for when AUTH_BYPASS is enabled."""
    from uuid import UUID
    
    bypass_user_id = UUID(settings.AUTH_BYPASS_USER_ID)
    user = db.get(User, bypass_user_id)
    
    if user is None:
        # Get or create the default department
        default_dept = db.query(Department).filter(
            Department.code == "DEFAULT"
        ).first()
        
        if default_dept is None:
            # Create default department if it doesn't exist
            default_dept = Department(
                id=UUID("00000000-0000-0000-0000-000000000000"),
                name="System Department",
                code="DEFAULT",
                is_active=True,
            )
            db.add(default_dept)
            db.flush()
        
        user = User(
            id=bypass_user_id,
            email=settings.AUTH_BYPASS_USER_EMAIL,
            full_name="System Bypass User",
            hashed_password="!",  # No password
            is_active=True,
            role=UserRole.SUPERADMIN,
            department_id=default_dept.id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user

