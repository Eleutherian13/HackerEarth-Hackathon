"""Mock authentication service for development/testing without PostgreSQL."""

from datetime import datetime, timezone
from typing import Optional
import uuid
from app.models.enums import UserRole


class MockUser:
    """Mock user object that matches the real User model interface."""
    
    def __init__(self, email: str, full_name: str, role: UserRole = UserRole.OFFICER):
        self.id = uuid.uuid4()
        self.email = email
        self.full_name = full_name
        self.role = role
        self.is_active = True
        self.department_id = uuid.uuid4()
        self.last_login = None
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)


# Mock user database for testing
MOCK_USERS = {
    "admin@laos.gov.in": {
        "user": MockUser("admin@laos.gov.in", "Administrator", UserRole.ADMIN),
        "password_hash": "$2b$12$R9h7cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jKMUe",  # Admin@123456
    },
    "officer@laos.gov.in": {
        "user": MockUser("officer@laos.gov.in", "Test Officer", UserRole.OFFICER),
        "password_hash": "$2b$12$R9h7cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jKMUe",  # Officer@123456
    },
}


def get_mock_user(email: str) -> Optional[MockUser]:
    """Get a mock user by email."""
    user_data = MOCK_USERS.get(email.lower())
    if user_data:
        return user_data["user"]
    return None


def verify_mock_password(email: str, password: str) -> bool:
    """Verify password for mock user."""
    user_data = MOCK_USERS.get(email.lower())
    if not user_data:
        return False
    
    # For testing, accept both the actual password and the hash-like string
    # In production, this would use bcrypt.checkpw()
    expected_password = "Admin@123456" if "admin" in email else "Officer@123456"
    return password == expected_password
