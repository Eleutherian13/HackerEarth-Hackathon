"""Pytest configuration and test fixtures."""

import os
import pytest
from pathlib import Path

# Ensure required application settings are available during test collection.
os.environ.setdefault("SECRET_KEY", "x" * 32)
os.environ.setdefault("JWT_SECRET_KEY", "y" * 32)
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/testdb")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/1")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
os.environ["ENVIRONMENT"] = "development"
os.environ["DEBUG"] = "false"
os.environ["TESTING"] = "true"

from tests.factories import make_department, make_user
from app.models.enums import UserRole

# Get fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_text_pdf_bytes():
    """Load sample text-based PDF for testing."""
    pdf_path = FIXTURES_DIR / "sample_text.pdf"

    if not pdf_path.exists():
        pytest.skip(f"Test fixture not found: {pdf_path}")

    return pdf_path.read_bytes()


@pytest.fixture
def sample_scanned_pdf_bytes():
    """Load sample scanned PDF for testing."""
    pdf_path = FIXTURES_DIR / "sample_scanned.pdf"

    if not pdf_path.exists():
        pytest.skip(f"Test fixture not found: {pdf_path}")

    return pdf_path.read_bytes()


@pytest.fixture
def sample_hybrid_pdf_bytes():
    """Load sample hybrid PDF for testing."""
    pdf_path = FIXTURES_DIR / "sample_hybrid.pdf"

    if not pdf_path.exists():
        pytest.skip(f"Test fixture not found: {pdf_path}")

    return pdf_path.read_bytes()


@pytest.fixture
def invalid_pdf_bytes():
    """Create invalid PDF bytes for error testing."""
    return b"Not a PDF file at all"


@pytest.fixture
def corrupted_pdf_bytes():
    """Create corrupted PDF bytes (valid header but invalid structure)."""
    return b"%PDF-1.4\ngarbage data that makes invalid PDF"


@pytest.fixture
def admin_user():
    """Create an admin user model for endpoint tests."""
    department = make_department(name="Admin Department", code="ADM")
    return make_user(email="admin@example.com", role=UserRole.ADMIN, department_id=department.id)
