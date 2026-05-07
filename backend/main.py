"""
FastAPI application factory and configuration.

Initializes the FastAPI app with:
- Middleware (CORS, logging, auth, rate limiting, security headers)
- Exception handlers
- Dependency injection
- API routes
- Logging configuration
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError, StarletteHTTPException
from fastapi.responses import JSONResponse

from app.api.middleware.auth import configure_security
from app.api.middleware.audit_middleware import configure_audit_middleware
from app.api.middleware.logging import configure_request_logging
from app.api.middleware.size_limit import RequestSizeLimitMiddleware, ContentTypeValidationMiddleware
from app.api.v1.endpoints import auth, health
from app.api.v1.endpoints.action_plan import router as action_plan_router
from app.api.v1.endpoints.cases import router as cases_router
from app.api.v1.endpoints.dashboard import router as dashboard_router
from app.api.v1.endpoints.documents import router as documents_router
from app.api.v1.endpoints.documents_extraction import router as extraction_router
from app.api.v1.endpoints.review_api import router as review_router
from app.api.v1.endpoints.admin import router as admin_router
from app.core.config import settings
from app.core.logging import get_logger, configure_logging

logger = get_logger(__name__)


# Lifespan context manager for startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting up LAOS server...")
    logger.info_context(
        f"Environment: {settings.ENVIRONMENT}",
        environment=settings.ENVIRONMENT,
        debug=settings.DEBUG,
        log_level=settings.LOG_LEVEL,
        log_format=settings.LOG_FORMAT,
    )
    yield
    # Shutdown
    logger.info("Shutting down LAOS server...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    # Configure logging first
    configure_logging()

    # Create FastAPI app
    app = FastAPI(
        title=settings.APP_NAME,
        description="Court Judgment Action System - Compliance Decision Support",
        version=settings.APP_VERSION,
        lifespan=lifespan,
        debug=settings.DEBUG,
    )

    # Configure middleware
    configure_request_logging(app)
    configure_security(app)
    configure_audit_middleware(app)
    
    # Add input validation middleware
    app.add_middleware(ContentTypeValidationMiddleware)
    app.add_middleware(RequestSizeLimitMiddleware)

    # Exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        """Handle validation errors with structured response."""
        logger.warning_context(
            "Validation error",
            path=request.url.path,
            errors=exc.errors(),
        )
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Validation error",
                "errors": exc.errors(),
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request, exc):
        """Handle HTTP exceptions with structured response."""
        logger.info_context(
            f"HTTP {exc.status_code}",
            path=request.url.path,
            status_code=exc.status_code,
            detail=exc.detail,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        """Handle unexpected exceptions with structured response."""
        logger.error_context(
            "Unhandled exception",
            path=request.url.path,
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    # Include routers
    app.include_router(health.router)
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(documents_router, prefix="/api/v1")
    app.include_router(extraction_router, prefix="/api/v1")
    app.include_router(review_router, prefix="/api/v1")
    app.include_router(action_plan_router, prefix="/api/v1")
    app.include_router(cases_router, prefix="/api/v1")
    app.include_router(dashboard_router, prefix="/api/v1")
    app.include_router(admin_router, prefix="/api/v1")

    # Root endpoint
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint."""
        return {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "docs": "/docs",
            "openapi": "/openapi.json",
        }

    logger.info("FastAPI application initialized successfully")
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_config=None,  # Use our custom logging configuration
    )
