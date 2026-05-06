from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator

from app.models.enums import UserRole

from .base import StrictSchema, normalize_optional_text, normalize_required_text


class PasswordChangeRequest(StrictSchema):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=False,
        json_schema_extra={
            "examples": [
                {
                    "current_password": "OldPassw0rd!",
                    "new_password": "N3wStr0ngPass!",
                }
            ]
        },
    )

    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=12)

    @field_validator("current_password", "new_password", mode="before")
    @classmethod
    def normalize_passwords(cls, value: Any, info):
        return normalize_required_text(value, info.field_name)

    @field_validator("new_password")
    @classmethod
    def validate_new_password_complexity(cls, value: str) -> str:
        if len(value) < 12:
            raise ValueError("new_password must be at least 12 characters long")
        checks = [any(char.islower() for char in value), any(char.isupper() for char in value), any(char.isdigit() for char in value), any(not char.isalnum() for char in value)]
        if not all(checks):
            raise ValueError("new_password must contain upper, lower, digit, and special characters")
        return value


class RefreshTokenRequest(StrictSchema):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=False,
        json_schema_extra={
            "examples": [
                {
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                }
            ]
        },
    )

    refresh_token: str

    @field_validator("refresh_token", mode="before")
    @classmethod
    def normalize_refresh_token(cls, value: Any) -> str:
        return normalize_required_text(value, "refresh_token")


class LogoutRequest(StrictSchema):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=False,
        json_schema_extra={
            "examples": [
                {
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                }
            ]
        },
    )

    refresh_token: str | None = None

    @field_validator("refresh_token", mode="before")
    @classmethod
    def normalize_refresh_token(cls, value: Any) -> str | None:
        return normalize_optional_text(value)


class AuthTokenResponse(StrictSchema):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=False,
        json_schema_extra={
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in_seconds": 1800,
                    "refresh_expires_in_seconds": 604800,
                    "requires_password_change": False,
                }
            ]
        },
    )

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_seconds: int = Field(gt=0)
    refresh_expires_in_seconds: int = Field(gt=0)
    requires_password_change: bool = False

    @field_validator("access_token", "refresh_token", "token_type", mode="before")
    @classmethod
    def normalize_required_text(cls, value: Any, info):
        return normalize_required_text(value, info.field_name)


class CurrentUserResponse(StrictSchema):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=False,
        json_schema_extra={
            "examples": [
                {
                    "id": "9c5f4d76-7d29-4b9d-8d7a-0f47b2a8d8ca",
                    "email": "reviewer@example.gov",
                    "full_name": "Asha Rao",
                    "role": "REVIEWER",
                    "department_id": "3a1d640c-b50a-4fd0-bcbb-ec16f2ac0f47",
                    "department_name": "Legal Department",
                    "is_active": True,
                    "must_change_password": False,
                }
            ]
        },
    )

    id: UUID
    email: str
    full_name: str
    role: UserRole
    department_id: UUID
    department_name: str
    is_active: bool
    must_change_password: bool

    @field_validator("email", "full_name", "department_name", mode="before")
    @classmethod
    def normalize_required_text(cls, value: Any, info):
        return normalize_required_text(value, info.field_name)


class LogoutResponse(StrictSchema):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=False,
        json_schema_extra={
            "examples": [
                {
                    "message": "Logged out successfully.",
                }
            ]
        },
    )

    message: str

    @field_validator("message", mode="before")
    @classmethod
    def normalize_message(cls, value: Any) -> str:
        return normalize_required_text(value, "message")


class PasswordChangeResponse(StrictSchema):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=False,
        json_schema_extra={
            "examples": [
                {
                    "message": "Password updated successfully.",
                    "password_changed_at": "2026-01-12T10:10:00Z",
                }
            ]
        },
    )

    message: str
    password_changed_at: str

    @field_validator("message", "password_changed_at", mode="before")
    @classmethod
    def normalize_text(cls, value: Any, info):
        return normalize_required_text(value, info.field_name)


class AccessRequestRequest(StrictSchema):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=False,
        json_schema_extra={
            "examples": [
                {
                    "email": "officer@example.gov",
                    "full_name": "Officer Name",
                }
            ]
        },
    )

    email: str = Field(min_length=5)
    full_name: str = Field(min_length=2)

    @field_validator("email", "full_name", mode="before")
    @classmethod
    def normalize_text(cls, value: Any, info):
        return normalize_required_text(value, info.field_name)


class AccessRequestResponse(StrictSchema):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=False,
        json_schema_extra={
            "examples": [
                {
                    "message": "Access request submitted successfully. An administrator will review and create your account.",
                }
            ]
        },
    )

    message: str

    @field_validator("message", mode="before")
    @classmethod
    def normalize_message(cls, value: Any) -> str:
        return normalize_required_text(value, "message")
