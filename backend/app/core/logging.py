"""
Structured logging configuration with JSON formatting, sensitive data redaction, and audit support.

Features:
- JSON structured logging with timestamp, level, logger, message, request_id, user_id, correlation_id
- Automatic redaction of sensitive fields (passwords, tokens, credit cards, PII)
- Flexible output: stdout (container-friendly) or file-based
- Correlation ID propagation across async tasks
- Request ID tracking throughout request lifecycle
- Error tracking with full tracebacks
"""

from __future__ import annotations

import json
import logging
import logging.config
import re
import sys
import traceback
from contextvars import ContextVar
from datetime import datetime, timezone
from logging import Formatter, LogRecord
from pathlib import Path
from typing import Any

from app.core.config import settings

# Context variables for tracking request and correlation IDs
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)
user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)


class SensitiveDataRedactor:
    """Redacts sensitive information from log messages and structured data."""

    # Patterns for sensitive data that should never appear in logs
    REDACTION_PATTERNS = {
        "password": re.compile(r'"password"\s*:\s*"[^"]*"', re.IGNORECASE),
        "secret": re.compile(r'"secret[^"]*"\s*:\s*"[^"]*"', re.IGNORECASE),
        "token": re.compile(r'"[^"]*token[^"]*"\s*:\s*"[^"]*"', re.IGNORECASE),
        "api_key": re.compile(r'"api[_-]?key"\s*:\s*"[^"]*"', re.IGNORECASE),
        "access_token": re.compile(r'"access[_-]?token"\s*:\s*"[^"]*"', re.IGNORECASE),
        "refresh_token": re.compile(r'"refresh[_-]?token"\s*:\s*"[^"]*"', re.IGNORECASE),
        "authorization": re.compile(r'"authorization"\s*:\s*"[^"]*"', re.IGNORECASE),
        "bearer": re.compile(r'Bearer\s+[^\s]+', re.IGNORECASE),
        "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
        "credit_card": re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'),
        "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        "phone": re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
    }

    REDACT_KEYS = {
        "password",
        "hashed_password",
        "secret",
        "token",
        "refresh_token",
        "access_token",
        "authorization",
        "api_key",
        "api_secret",
        "private_key",
        "auth_token",
        "bearer_token",
        "session_token",
        "jwt",
        "csrf_token",
        "x_api_key",
        "x_auth_token",
        "credentials",
    }

    @classmethod
    def redact_string(cls, value: str) -> str:
        """Redact sensitive patterns from string."""
        if not isinstance(value, str):
            return value

        for pattern in cls.REDACTION_PATTERNS.values():
            value = pattern.sub('***REDACTED***', value)
        return value

    @classmethod
    def redact_dict(cls, data: dict[str, Any], depth: int = 0, max_depth: int = 10) -> dict[str, Any]:
        """Recursively redact sensitive keys from dictionary."""
        if depth > max_depth:
            return data

        redacted = {}
        for key, value in data.items():
            if key.lower() in cls.REDACT_KEYS:
                redacted[key] = "***REDACTED***"
            elif isinstance(value, dict):
                redacted[key] = cls.redact_dict(value, depth + 1, max_depth)
            elif isinstance(value, list):
                redacted[key] = [cls.redact_dict(item, depth + 1, max_depth) if isinstance(item, dict) else item for item in value]
            elif isinstance(value, str):
                redacted[key] = cls.redact_string(value)
            else:
                redacted[key] = value
        return redacted

    @classmethod
    def redact(cls, data: Any) -> Any:
        """Redact sensitive data from string or dict."""
        if isinstance(data, str):
            return cls.redact_string(data)
        elif isinstance(data, dict):
            return cls.redact_dict(data)
        return data


class JSONFormatter(Formatter):
    """JSON formatter for structured logging output."""

    def format(self, record: LogRecord) -> str:
        """Format log record as JSON."""
        log_obj = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add context variables if available
        request_id = request_id_var.get()
        if request_id:
            log_obj["request_id"] = request_id

        correlation_id = correlation_id_var.get()
        if correlation_id:
            log_obj["correlation_id"] = correlation_id

        user_id = user_id_var.get()
        if user_id:
            log_obj["user_id"] = user_id

        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        # Add extra fields with redaction
        extra_fields = {k: v for k, v in record.__dict__.items() if not k.startswith("_") and k not in {
            "name",
            "msg",
            "args",
            "created",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "message",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "thread",
            "threadName",
            "exc_info",
            "exc_text",
            "stack_info",
            "taskName",
        }}

        if extra_fields:
            log_obj["extra"] = SensitiveDataRedactor.redact(extra_fields)

        return json.dumps(log_obj, default=str, ensure_ascii=False)


class StructuredLogger(logging.Logger):
    """Extended logger with structured logging methods."""

    def log_context(self, level: int, msg: str, **kwargs) -> None:
        """Log with additional context fields."""
        extra = kwargs.pop("extra", {})
        extra.update(kwargs)
        self.log(level, msg, extra=extra)

    def debug_context(self, msg: str, **kwargs) -> None:
        """Debug with context."""
        self.log_context(logging.DEBUG, msg, **kwargs)

    def info_context(self, msg: str, **kwargs) -> None:
        """Info with context."""
        self.log_context(logging.INFO, msg, **kwargs)

    def warning_context(self, msg: str, **kwargs) -> None:
        """Warning with context."""
        self.log_context(logging.WARNING, msg, **kwargs)

    def error_context(self, msg: str, **kwargs) -> None:
        """Error with context."""
        self.log_context(logging.ERROR, msg, **kwargs)

    def critical_context(self, msg: str, **kwargs) -> None:
        """Critical with context."""
        self.log_context(logging.CRITICAL, msg, **kwargs)


def configure_logging() -> None:
    """Configure structured logging based on settings."""
    # Determine log level
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Create handlers
    handlers = {}

    # Stdout handler (always present for container environments)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(log_level)

    if settings.LOG_FORMAT == "json":
        stdout_handler.setFormatter(JSONFormatter())
    else:
        # Text format with timestamps
        text_format = "%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s"
        formatter = logging.Formatter(text_format, datefmt="%Y-%m-%d %H:%M:%S")
        stdout_handler.setFormatter(formatter)

    handlers["stdout"] = stdout_handler

    # File handler (if configured)
    if settings.LOG_FILE_PATH:
        log_file = Path(settings.LOG_FILE_PATH)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)

        if settings.LOG_FORMAT == "json":
            file_handler.setFormatter(JSONFormatter())
        else:
            file_handler.setFormatter(logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            ))

        handlers["file"] = file_handler

    # Configure root logger
    logging.setLoggerClass(StructuredLogger)
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add new handlers
    for handler in handlers.values():
        root_logger.addHandler(handler)

    # Configure app loggers
    for logger_name in [
        "app",
        "app.api",
        "app.core",
        "app.db",
        "app.models",
        "sqlalchemy.engine",
        "celery",
    ]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)

    # Set SQLAlchemy echo if debug mode
    if settings.DEBUG:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    else:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # Suppress noisy loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("redis").setLevel(logging.WARNING)


def set_request_context(request_id: str | None = None, correlation_id: str | None = None, user_id: str | None = None) -> None:
    """Set request context for logging."""
    if request_id:
        request_id_var.set(request_id)
    if correlation_id:
        correlation_id_var.set(correlation_id)
    if user_id:
        user_id_var.set(user_id)


def clear_request_context() -> None:
    """Clear request context."""
    request_id_var.set(None)
    correlation_id_var.set(None)
    user_id_var.set(None)


def get_logger(name: str) -> StructuredLogger:
    """Get or create a structured logger."""
    return logging.getLogger(name)


# Initialize logging on module load
configure_logging()
