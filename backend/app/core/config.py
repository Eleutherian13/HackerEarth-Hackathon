from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	model_config = SettingsConfigDict(
		env_file=".env",
		env_file_encoding="utf-8",
		case_sensitive=False,
		arbitrary_types_allowed=True,
		extra="ignore",
	)

	APP_NAME: str = "Court Judgment Action System"
	APP_VERSION: str = "1.0.0"
	ENVIRONMENT: Literal["development", "staging", "production"] = "development"
	DEBUG: bool = False
	SECRET_KEY: SecretStr = Field(min_length=32)

	DATABASE_URL: PostgresDsn
	DATABASE_MAX_CONNECTIONS: int = 20
	DATABASE_POOL_SIZE: int = 5
	DATABASE_POOL_OVERFLOW: int = 10

	REDIS_URL: RedisDsn
	REDIS_MAX_CONNECTIONS: int = 10

	CELERY_BROKER_URL: str
	CELERY_RESULT_BACKEND: str

	DEFAULT_PAGE_SIZE: int = 25

	JWT_SECRET_KEY: SecretStr = Field(min_length=32)
	JWT_ALGORITHM: str = "HS256"
	ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
	REFRESH_TOKEN_EXPIRE_DAYS: int = 7
	PASSWORD_HASH_ROUNDS: int = 12

	STORAGE_BACKEND: Literal["local", "s3"] = "local"
	LOCAL_STORAGE_PATH: Path = Path("./storage")
	S3_BUCKET_NAME: str | None = None
	S3_ENDPOINT_URL: str | None = None
	MAX_UPLOAD_SIZE_MB: int = 50

	OCR_LANGUAGE: str = "eng+hin"
	OCR_ENGINE: Literal["tesseract", "paddleocr"] = "paddleocr"
	EXTRACTION_MODEL: str = "gpt-4o-mini"
	EXTRACTION_TEMPERATURE: float = 0.0
	EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
	MIN_CONFIDENCE_THRESHOLD: float = 0.60
	HIGH_CONFIDENCE_THRESHOLD: float = 0.85

	RATE_LIMIT_PER_MINUTE: int = 60
	RATE_LIMIT_BURST: int = 100
	CORS_ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"]

	LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
	LOG_FORMAT: Literal["json", "text"] = "json"
	LOG_FILE_PATH: Path | None = None
	SENTRY_DSN: str | None = None
	TESTING: bool = False

	# Email Configuration
	ADMIN_EMAIL: str = "admin@example.com"
	FRONTEND_URL: str = "http://localhost:5173"
	SMTP_ENABLED: bool = False
	SMTP_HOST: str = "smtp.gmail.com"
	SMTP_PORT: int = 587
	SMTP_USER: str = ""
	SMTP_PASSWORD: str = ""
	SMTP_FROM_EMAIL: str = ""
	SMTP_FROM_NAME: str = "LAOS Admin"

	@field_validator(
		"SECRET_KEY",
		"JWT_SECRET_KEY",
		mode="after",
	)
	@classmethod
	def validate_secret_length(cls, value: SecretStr) -> SecretStr:
		if len(value.get_secret_value()) < 32:
			raise ValueError("secret values must be at least 32 characters long")
		return value

	@field_validator(
		"DATABASE_MAX_CONNECTIONS",
		"DATABASE_POOL_SIZE",
		"DATABASE_POOL_OVERFLOW",
		"REDIS_MAX_CONNECTIONS",
		"ACCESS_TOKEN_EXPIRE_MINUTES",
		"REFRESH_TOKEN_EXPIRE_DAYS",
		"PASSWORD_HASH_ROUNDS",
		"MAX_UPLOAD_SIZE_MB",
		"RATE_LIMIT_PER_MINUTE",
		"RATE_LIMIT_BURST",
		"DEFAULT_PAGE_SIZE",
		mode="after",
	)
	@classmethod
	def validate_positive_ints(cls, value: int) -> int:
		if value <= 0:
			raise ValueError("value must be greater than 0")
		return value

	@field_validator("EXTRACTION_TEMPERATURE", mode="after")
	@classmethod
	def validate_temperature(cls, value: float) -> float:
		if not 0.0 <= value <= 1.0:
			raise ValueError("EXTRACTION_TEMPERATURE must be between 0.0 and 1.0")
		return value

	@field_validator("MIN_CONFIDENCE_THRESHOLD", "HIGH_CONFIDENCE_THRESHOLD", mode="after")
	@classmethod
	def validate_confidence_threshold(cls, value: float) -> float:
		if not 0.0 <= value <= 1.0:
			raise ValueError("confidence thresholds must be between 0.0 and 1.0")
		return value

	@field_validator("HIGH_CONFIDENCE_THRESHOLD", mode="after")
	@classmethod
	def validate_threshold_order(cls, value: float, info) -> float:
		min_threshold = info.data.get("MIN_CONFIDENCE_THRESHOLD")
		if min_threshold is not None and value <= min_threshold:
			raise ValueError("HIGH_CONFIDENCE_THRESHOLD must be greater than MIN_CONFIDENCE_THRESHOLD")
		return value

	@field_validator("LOCAL_STORAGE_PATH", mode="after")
	@classmethod
	def normalize_storage_path(cls, value: Path) -> Path:
		return value.expanduser().resolve()

	@field_validator("S3_BUCKET_NAME", "S3_ENDPOINT_URL", "SENTRY_DSN", mode="before")
	@classmethod
	def normalize_optional_strings(cls, value):
		if value is None:
			return None
		if isinstance(value, str):
			cleaned = value.strip()
			return cleaned or None
		return value

	@field_validator("CORS_ALLOWED_ORIGINS", mode="before")
	@classmethod
	def normalize_cors_origins(cls, value):
		if value is None:
			return ["http://localhost:3000", "http://127.0.0.1:3000"]
		if isinstance(value, str):
			cleaned = [item.strip() for item in value.split(",") if item.strip()]
			return cleaned
		if isinstance(value, list):
			return [item.strip() for item in value if isinstance(item, str) and item.strip()]
		raise TypeError("CORS_ALLOWED_ORIGINS must be a list or comma-separated string")


class DevelopmentSettings(Settings):
	DEBUG: bool = True
	LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "DEBUG"
	LOG_FORMAT: Literal["json", "text"] = "text"
	STORAGE_BACKEND: Literal["local", "s3"] = "local"


class StagingSettings(Settings):
	DEBUG: bool = False
	LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
	LOG_FORMAT: Literal["json", "text"] = "json"


class ProductionSettings(Settings):
	DEBUG: bool = False
	LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
	LOG_FORMAT: Literal["json", "text"] = "json"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
	environment = Settings().ENVIRONMENT
	if environment == "development":
		return DevelopmentSettings()
	if environment == "staging":
		return StagingSettings()
	return ProductionSettings()


settings = get_settings()

# Secret rotation strategy:
# - rotate SECRET_KEY and JWT_SECRET_KEY independently through environment updates
# - keep old JWT signing keys available only long enough to validate active refresh sessions
# - force refresh-token reissue after rotation and revoke compromised keys immediately
# - never store secrets in code or image layers; load them from environment or secret managers
