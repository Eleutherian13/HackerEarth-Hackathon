"""
Request and response logging middleware for FastAPI.

Logs HTTP requests and responses with:
- Method, path, status code, duration
- Request/correlation ID tracking
- Automatic timing measurements
- Response body truncation for large payloads
- Health check endpoint filtering
"""

from __future__ import annotations

import secrets
import time
import uuid
from typing import Awaitable, Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

from app.core.logging import get_logger, set_request_context, clear_request_context

logger = get_logger(__name__)

# Endpoints that should not be logged (health checks, etc.)
SKIP_LOGGING_PATHS = {
    "/health",
    "/health/ready",
    "/health/live",
    "/metrics",
    "/.well-known",
}


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log HTTP requests and responses with timing."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Log request and response."""
        # Skip logging for health checks and metrics
        if self._should_skip_logging(request.url.path):
            return await call_next(request)

        # Generate or get request ID
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        correlation_id = request.headers.get("x-correlation-id", request_id)

        # Set request context for logging
        set_request_context(request_id=request_id, correlation_id=correlation_id)

        # Store request ID in request state for later access
        request.state.request_id = request_id
        request.state.correlation_id = correlation_id

        # Capture request start time
        start_time = time.perf_counter()

        # Extract basic request info
        method = request.method
        path = request.url.path
        query_string = request.url.query

        # Log request
        logger.info_context(
            f"{method} {path}",
            method=method,
            path=path,
            query=query_string,
            request_id=request_id,
            correlation_id=correlation_id,
        )

        try:
            # Call the next middleware/handler
            response = await call_next(request)
        except Exception as e:
            # Log exception
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error_context(
                f"{method} {path} raised exception",
                method=method,
                path=path,
                duration_ms=duration_ms,
                request_id=request_id,
                correlation_id=correlation_id,
                exc_info=True,
            )
            raise
        finally:
            # Clear request context
            clear_request_context()

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Correlation-ID"] = correlation_id

        # Log response
        status_code = response.status_code
        logger.info_context(
            f"{method} {path} {status_code}",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=round(duration_ms, 2),
            request_id=request_id,
            correlation_id=correlation_id,
        )

        return response

    @staticmethod
    def _should_skip_logging(path: str) -> bool:
        """Check if path should skip logging."""
        return any(path.startswith(skip_path) for skip_path in SKIP_LOGGING_PATHS)


def configure_request_logging(app) -> None:
    """Configure request logging middleware on FastAPI app."""
    app.add_middleware(RequestLoggingMiddleware)
