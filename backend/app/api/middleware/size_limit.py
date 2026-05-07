"""
Request size limiting middleware for FastAPI.

Enforces maximum request body size limits per endpoint to prevent
memory exhaustion and denial-of-service attacks.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces request size limits.
    
    Configuration:
    - DEFAULT_MAX_SIZE: 10MB (10 * 1024 * 1024)
    - UPLOAD_MAX_SIZE: 55MB (for file uploads)
    """
    
    # Size limits in bytes
    DEFAULT_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    UPLOAD_MAX_SIZE = 55 * 1024 * 1024   # 55MB
    
    # Paths with custom size limits
    CUSTOM_LIMITS = {
        "/api/v1/documents/upload": UPLOAD_MAX_SIZE,
    }
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request and check size limits.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            Response or 413 if size limit exceeded
        """
        # Get content length header
        content_length = request.headers.get("content-length")
        
        if content_length:
            try:
                size = int(content_length)
                max_size = self._get_max_size_for_path(request.url.path)
                
                if size > max_size:
                    logger.warning_context(
                        "Request size limit exceeded",
                        path=request.url.path,
                        content_length=size,
                        max_size=max_size,
                        method=request.method,
                    )
                    
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={
                            "error": "REQUEST_TOO_LARGE",
                            "message": f"Request size {size} bytes exceeds limit of {max_size} bytes",
                            "max_size": max_size,
                        },
                    )
            
            except (ValueError, TypeError):
                logger.warning_context(
                    "Invalid content-length header",
                    content_length=content_length,
                )
        
        # Check for streaming requests that might be large
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error_context(
                "Error processing request",
                error=str(e),
                path=request.url.path,
                exc_info=True,
            )
            raise
    
    @staticmethod
    def _get_max_size_for_path(path: str) -> int:
        """
        Get maximum size limit for a specific path.
        
        Args:
            path: Request path
            
        Returns:
            Maximum size in bytes
        """
        for route, limit in RequestSizeLimitMiddleware.CUSTOM_LIMITS.items():
            if path.startswith(route):
                return limit
        
        return RequestSizeLimitMiddleware.DEFAULT_MAX_SIZE


class ContentTypeValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware that validates Content-Type headers.

    Ensures requests use appropriate content types for their endpoints:
    - POST/PUT with body: must be application/json
    - File uploads: must be multipart/form-data
    - Login/Auth endpoints: accept form-data
    """

    # Paths that require specific content types
    REQUIRED_JSON_PATHS = {
        "/api/v1/",  # Most API endpoints
    }

    # Paths that require multipart/form-data
    MULTIPART_PATHS = {
        "/api/v1/documents/upload",
    }

    # POST endpoints that intentionally do not send a body
    NO_BODY_PATHS = {
        "/api/v1/review/documents/",
    }

    # Paths that accept form data (form-urlencoded or multipart)
    FORM_DATA_PATHS = {
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
    }

    # Methods that require content-type validation
    METHODS_REQUIRING_CONTENT = {"POST", "PUT", "PATCH"}

    async def dispatch(self, request: Request, call_next):
        """
        Process the request and validate Content-Type.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            Response or 415 if content-type invalid
        """
        # Skip GET, DELETE, HEAD, OPTIONS
        if request.method not in self.METHODS_REQUIRING_CONTENT:
            response = await call_next(request)
            return response

        # Check if path has content-type requirement
        path = request.url.path
        content_type = request.headers.get("content-type", "").lower()

        # Check for form-data paths (login, auth endpoints)
        for form_path in self.FORM_DATA_PATHS:
            if path.startswith(form_path):
                # Accept both form-urlencoded and multipart
                if not (content_type.startswith("application/x-www-form-urlencoded") or 
                        content_type.startswith("multipart/form-data")):
                    logger.warning_context(
                        "Invalid content-type for auth endpoint",
                        path=path,
                        expected="application/x-www-form-urlencoded or multipart/form-data",
                        received=content_type,
                    )

                    return JSONResponse(
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        content={
                            "error": "UNSUPPORTED_MEDIA_TYPE",
                            "message": "Auth endpoint requires application/x-www-form-urlencoded or multipart/form-data content-type",
                            "required_content_type": "application/x-www-form-urlencoded or multipart/form-data",
                        },
                    )
                
                # Auth endpoints are valid, proceed
                response = await call_next(request)
                return response
        
        # Check for multipart paths
        for multipart_path in self.MULTIPART_PATHS:
            if path.startswith(multipart_path):
                if not content_type.startswith("multipart/form-data"):
                    logger.warning_context(
                        "Invalid content-type for upload",
                        path=path,
                        expected="multipart/form-data",
                        received=content_type,
                    )

                    return JSONResponse(
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        content={
                            "error": "UNSUPPORTED_MEDIA_TYPE",
                            "message": "Upload endpoint requires multipart/form-data content-type",
                            "required_content_type": "multipart/form-data",
                        },
                    )

        # Check for JSON paths
        for json_path in self.REQUIRED_JSON_PATHS:
            if path.startswith(json_path):
                # Exception for upload endpoint (handled above)
                if any(path.startswith(mp) for mp in self.MULTIPART_PATHS):
                    continue

                # Exception for body-less action endpoints
                if any(path.startswith(no_body_path) for no_body_path in self.NO_BODY_PATHS):
                    continue
                
                # Exception for form-data endpoints (handled above)
                if any(path.startswith(fp) for fp in self.FORM_DATA_PATHS):
                    continue

                # Require JSON content-type for API endpoints with body
                if not content_type.startswith("application/json"):
                    logger.warning_context(
                        "Invalid content-type for API endpoint",
                        path=path,
                        expected="application/json",
                        received=content_type,
                    )

                    return JSONResponse(
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        content={
                            "error": "UNSUPPORTED_MEDIA_TYPE",
                            "message": "API endpoint requires application/json content-type",
                            "required_content_type": "application/json",
                        },
                    )

        response = await call_next(request)
        return response
        # Check for multipart paths
        for multipart_path in self.MULTIPART_PATHS:
            if path.startswith(multipart_path):
                if not content_type.startswith("multipart/form-data"):
                    logger.warning_context(
                        "Invalid content-type for upload",
                        path=path,
                        expected="multipart/form-data",
                        received=content_type,
                    )
                    
                    return JSONResponse(
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        content={
                            "error": "UNSUPPORTED_MEDIA_TYPE",
                            "message": "Upload endpoint requires multipart/form-data content-type",
                            "required_content_type": "multipart/form-data",
                        },
                    )
        
        # Check for JSON paths
        for json_path in self.REQUIRED_JSON_PATHS:
            if path.startswith(json_path):
                # Exception for upload endpoint (handled above)
                if any(path.startswith(mp) for mp in self.MULTIPART_PATHS):
                    continue
                
                # Require JSON content-type for API endpoints with body
                if not content_type.startswith("application/json"):
                    logger.warning_context(
                        "Invalid content-type for API endpoint",
                        path=path,
                        expected="application/json",
                        received=content_type,
                    )
                    
                    return JSONResponse(
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        content={
                            "error": "UNSUPPORTED_MEDIA_TYPE",
                            "message": "API endpoint requires application/json content-type",
                            "required_content_type": "application/json",
                        },
                    )
        
        response = await call_next(request)
        return response
