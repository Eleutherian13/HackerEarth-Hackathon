from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response

from app.core.config import settings
from app.core.security import (
    AuthContext,
    SECURITY_HEADERS,
    build_security_headers,
    decode_token,
    get_current_user_from_payload,
    get_db_session,
    get_redis_client,
    is_jti_blacklisted,
    request_context_from_request,
    validate_access_token,
)
from app.models.enums import UserRole

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.state.request_id = request_id
        request.state.context = AuthContext(user=None, role=None, department_id=None, request_id=request_id)

        token = self._extract_bearer_token(request)
        if token is not None:
            try:
                payload = await validate_access_token(token)
                db = get_db_session()
                try:
                    user = get_current_user_from_payload(db, payload)
                    request.state.context = AuthContext(
                        user=user,
                        role=user.role,
                        department_id=user.department_id,
                        request_id=request_id,
                        token_jti=payload["jti"],
                    )
                finally:
                    db.close()
            except HTTPException:
                raise
            except Exception as exc:  # pragma: no cover - defensive path
                logger.exception("Failed to validate bearer token: %s", exc)
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid authentication token")

        await self._apply_rate_limit(request)
        response = await call_next(request)
        self._apply_security_headers(response, request_id)
        return response

    @staticmethod
    def _extract_bearer_token(request: Request) -> str | None:
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.lower().startswith("bearer "):
            return None
        token = authorization.split(" ", 1)[1].strip()
        return token or None

    async def _apply_rate_limit(self, request: Request) -> None:
        if settings.TESTING:
            return

        try:
            redis_client = get_redis_client()
        except Exception:
            logger.warning("Redis unavailable, skipping rate limiting", exc_info=settings.DEBUG)
            return

        context = getattr(request.state, "context", None)
        user_id = getattr(getattr(context, "user", None), "id", None)
        ip_address = request.client.host if request.client else "unknown"

        current_minute = int(datetime.now(timezone.utc).timestamp() // 60)
        current_second = int(datetime.now(timezone.utc).timestamp())

        identifiers = [f"ip:{ip_address}"]
        if user_id is not None:
            identifiers.append(f"user:{user_id}")

        try:
            for identifier in identifiers:
                minute_key = f"ratelimit:{identifier}:{current_minute}"
                burst_key = f"ratelimit:burst:{identifier}:{current_second}"
                minute_count = await redis_client.incr(minute_key)
                if minute_count == 1:
                    await redis_client.expire(minute_key, 120)
                burst_count = await redis_client.incr(burst_key)
                if burst_count == 1:
                    await redis_client.expire(burst_key, 2)

                if minute_count > settings.RATE_LIMIT_PER_MINUTE or burst_count > settings.RATE_LIMIT_BURST:
                    raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="rate limit exceeded")
        except HTTPException:
            raise
        except Exception:
            logger.warning("Rate limit check failed, allowing request", exc_info=settings.DEBUG)

    @staticmethod
    def _apply_security_headers(response: Response, request_id: str) -> None:
        for header_name, header_value in SECURITY_HEADERS.items():
            response.headers[header_name] = header_value
        response.headers["X-Request-ID"] = request_id


def configure_security(app) -> None:
    app.add_middleware(AuthMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )
