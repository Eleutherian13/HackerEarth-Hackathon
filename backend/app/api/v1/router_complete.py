"""
Complete API v1 router - connects all endpoints
"""

from fastapi import APIRouter
from app.api.v1.endpoints import health
from app.api.v1.endpoints.auth_complete import router as auth_router
from app.api.v1.endpoints.documents_fixed import router as documents_router

api_router = APIRouter(prefix="/api/v1")

# Include all endpoint routers
api_router.include_router(auth_router, tags=["Authentication"])
api_router.include_router(documents_router, tags=["Documents"])

# Health check is at root
# api_router.include_router(health.router, tags=["Health"])
