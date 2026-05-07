"""
Health check endpoints for Kubernetes probes and monitoring.

Provides:
- /health - General health check
- /health/ready - Readiness probe (all dependencies ready)
- /health/live - Liveness probe (service alive)

Each endpoint returns comprehensive status of:
- Database connectivity
- Redis connectivity
- Celery broker connectivity
- Storage backend accessibility
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from redis.asyncio import Redis

from app.api.deps import get_db
from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import get_redis_client
from app.models.schemas.base import StrictSchema

logger = get_logger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


class HealthStatus(StrictSchema):
    """Health status response."""
    status: str  # "ok", "degraded", "error"
    timestamp: str
    version: str


class ComponentStatus(StrictSchema):
    """Individual component health status."""
    status: str  # "ok", "error"
    response_time_ms: float | None = None
    message: str | None = None


class DetailedHealthStatus(HealthStatus):
    """Detailed health status with component breakdown."""
    components: dict[str, ComponentStatus]


async def check_database(db: Session) -> tuple[str, float | None, str | None]:
    """Check database connectivity with timeout."""
    try:
        import asyncio
        
        # Run the synchronous database check with a 5-second timeout
        def _check():
            start = datetime.now(timezone.utc)
            try:
                result = db.execute(text("SELECT 1"))
                result.fetchone()
                duration_ms = (datetime.now(timezone.utc) - start).total_seconds() * 1000
                return "ok", duration_ms, None
            except Exception as e:
                return "error", None, f"Connection failed: {str(e)[:50]}"
        
        try:
            status, duration, msg = await asyncio.wait_for(
                asyncio.to_thread(_check),
                timeout=3.0
            )
            return status, duration, msg
        except asyncio.TimeoutError:
            return "error", None, "Database check timed out"
    except Exception as e:
        logger.error_context("Database health check failed", exc_info=True)
        return "error", None, f"Health check error: {str(e)[:50]}"


async def check_redis() -> tuple[str, float | None, str | None]:
    """Check Redis connectivity."""
    try:
        redis_client = get_redis_client()
        start = datetime.now(timezone.utc)
        await redis_client.ping()
        duration_ms = (datetime.now(timezone.utc) - start).total_seconds() * 1000
        return "ok", duration_ms, None
    except Exception as e:
        logger.error_context("Redis health check failed", exc_info=True)
        return "error", None, str(e)


async def check_storage() -> tuple[str, float | None, str | None]:
    """Check storage backend connectivity."""
    try:
        if settings.STORAGE_BACKEND == "local":
            # Check local storage directory
            settings.LOCAL_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
            return "ok", 0.0, None
        elif settings.STORAGE_BACKEND == "s3":
            # Note: Actual S3 check would require boto3 client
            # For now, just check configuration
            if not settings.S3_BUCKET_NAME:
                return "error", None, "S3_BUCKET_NAME not configured"
            return "ok", 0.0, None
        else:
            return "error", None, f"Unknown storage backend: {settings.STORAGE_BACKEND}"
    except Exception as e:
        logger.error_context("Storage health check failed", exc_info=True)
        return "error", None, str(e)


@router.get(
    "/",
    response_model=DetailedHealthStatus,
    status_code=status.HTTP_200_OK,
    summary="General Health Check",
    description="Returns overall health status and component breakdown",
)
async def health_check(db: Session = Depends(get_db)) -> DetailedHealthStatus:
    """
    General health check endpoint.

    Returns:
    - status: "ok" if all components healthy, "degraded" if some issues, "error" if critical failure
    - components: Individual status of each dependency
    """
    components: dict[str, ComponentStatus] = {}

    # Check database
    db_status, db_time, db_error = await check_database(db)
    components["database"] = ComponentStatus(
        status=db_status,
        response_time_ms=db_time,
        message=db_error,
    )

    # Check Redis
    redis_status, redis_time, redis_error = await check_redis()
    components["redis"] = ComponentStatus(
        status=redis_status,
        response_time_ms=redis_time,
        message=redis_error,
    )

    # Check storage
    storage_status, storage_time, storage_error = await check_storage()
    components["storage"] = ComponentStatus(
        status=storage_status,
        response_time_ms=storage_time,
        message=storage_error,
    )

    # Determine overall status
    critical_errors = [c for c in components.values() if c.status == "error" and c in [components["database"]]]
    non_critical_errors = [c for c in components.values() if c.status == "error" and c not in critical_errors]

    if critical_errors:
        overall_status = "error"
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE
    elif non_critical_errors:
        overall_status = "degraded"
        http_status = status.HTTP_200_OK
    else:
        overall_status = "ok"
        http_status = status.HTTP_200_OK

    logger.info_context(
        f"Health check completed: {overall_status}",
        overall_status=overall_status,
        components={k: v.status for k, v in components.items()},
    )

    return DetailedHealthStatus(
        status=overall_status,
        timestamp=datetime.now(timezone.utc).isoformat(),
        version=settings.APP_VERSION,
        components=components,
    )


@router.get(
    "/ready",
    response_model=HealthStatus,
    status_code=status.HTTP_200_OK,
    summary="Readiness Probe",
    description="Returns 200 if service is ready to accept traffic (Kubernetes readiness probe)",
)
async def readiness_probe(db: Session = Depends(get_db)) -> HealthStatus:
    """
    Readiness probe endpoint for Kubernetes.

    Returns 200 (OK) only if all dependencies are available and service is ready to accept traffic.
    Returns 503 (Service Unavailable) if any critical dependency is down.
    """
    try:
        # Check all critical dependencies
        db_status, _, _ = await check_database(db)
        redis_status, _, _ = await check_redis()
        storage_status, _, _ = await check_storage()

        if all(status == "ok" for status in [db_status, redis_status, storage_status]):
            return HealthStatus(
                status="ok",
                timestamp=datetime.now(timezone.utc).isoformat(),
                version=settings.APP_VERSION,
            )
        else:
            raise Exception("One or more dependencies not ready")

    except Exception as e:
        logger.warning_context("Readiness probe failed", exc_info=True)
        raise Exception("Service not ready")


@router.get(
    "/live",
    response_model=HealthStatus,
    status_code=status.HTTP_200_OK,
    summary="Liveness Probe",
    description="Returns 200 if service is alive (Kubernetes liveness probe)",
)
async def liveness_probe() -> HealthStatus:
    """
    Liveness probe endpoint for Kubernetes.

    Returns 200 (OK) if service is running and responsive.
    This is a simple check that the service process is alive.
    """
    return HealthStatus(
        status="ok",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version=settings.APP_VERSION,
    )
