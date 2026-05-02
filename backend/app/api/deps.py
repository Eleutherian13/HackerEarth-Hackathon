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
from app.core.validators import InputValidator, ValidationError
from app.db.session import get_db
from app.models.domain.models import Document, ExtractedField, User
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


# Validation dependencies

def validate_document_exists(document_id: UUID, db: Session = Depends(get_db)) -> Document:
    """
    Dependency that validates document exists and is accessible.
    
    Args:
        document_id: UUID of document to validate
        db: Database session
        
    Returns:
        Document object if exists
        
    Raises:
        HTTPException 404: Document not found
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )
    return doc


def validate_field_exists(field_id: UUID, db: Session = Depends(get_db)) -> ExtractedField:
    """
    Dependency that validates extracted field exists.
    
    Args:
        field_id: UUID of field to validate
        db: Database session
        
    Returns:
        ExtractedField object if exists
        
    Raises:
        HTTPException 404: Field not found
    """
    field = db.query(ExtractedField).filter(ExtractedField.id == field_id).first()
    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Field {field_id} not found",
        )
    return field


def validate_reviewer_permission(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Dependency that ensures user has permission to review documents.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User object if has permission
        
    Raises:
        HTTPException 403: Insufficient permissions
    """
    allowed_roles = {UserRole.REVIEWER, UserRole.ADMIN, UserRole.SUPERADMIN}
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to review documents",
        )
    return current_user


def validate_pagination_params(
    page: int = 1,
    per_page: int = 20,
    max_per_page: int = 100,
) -> tuple[int, int]:
    """
    Dependency that validates pagination parameters.
    
    Args:
        page: Page number (1-indexed)
        per_page: Items per page
        max_per_page: Maximum items allowed per page
        
    Returns:
        Tuple of (page, per_page)
        
    Raises:
        HTTPException 422: Invalid pagination parameters
    """
    if not InputValidator.validate_pagination(page, per_page, max_per_page):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid pagination: page >= 1, 1 <= per_page <= {max_per_page}",
        )
    return page, per_page


def validate_sort_params(
    sort_by: str = "created_at",
    sort_order: str = "DESC",
    allowed_columns: list[str] = None,
) -> tuple[str, str]:
    """
    Dependency that validates sort parameters.
    
    Args:
        sort_by: Column to sort by
        sort_order: Sort order (ASC or DESC)
        allowed_columns: List of allowed column names
        
    Returns:
        Tuple of (sort_by, sort_order)
        
    Raises:
        HTTPException 422: Invalid sort parameters
    """
    if allowed_columns is None:
        allowed_columns = ["created_at", "updated_at", "processing_status", "original_filename"]
    
    if not InputValidator.validate_sort_column(sort_by, allowed_columns):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid sort column. Allowed: {', '.join(allowed_columns)}",
        )
    
    if not InputValidator.validate_sort_order(sort_order):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Sort order must be ASC or DESC",
        )
    
    return sort_by, sort_order

def get_request_context(request: Request) -> AuthContext:
    return request_context_from_request(request)
