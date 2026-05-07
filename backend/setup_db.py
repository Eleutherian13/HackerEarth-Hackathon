"""
Database setup script: Creates all tables and seeds initial data.
Run from backend directory: python setup_db.py
"""
import uuid
from datetime import datetime, timezone

from app.core.config import settings
from app.db.session import engine, SessionLocal
from app.models.domain.base import Base
from app.models.domain.models import (
    Department, User, Document, DocumentPage,
    ExtractedField, ActionPlanItem, ReviewSession,
    AuditLog, ProcessingJob, RefreshToken, AccessRequest,
)
from app.models.enums import UserRole
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_tables():
    """Create all database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created successfully")


def seed_data():
    """Seed initial departments and users."""
    db = SessionLocal()
    try:
        # Check if data already exists
        existing_dept = db.query(Department).first()
        if existing_dept:
            print("✓ Data already seeded, skipping")
            return

        print("Seeding initial data...")

        # Create departments
        default_dept = Department(
            id=uuid.uuid4(),
            name="Default Department",
            code="DEFAULT",
            is_active=True,
        )
        legal_dept = Department(
            id=uuid.uuid4(),
            name="Legal Department",
            code="LEGAL",
            is_active=True,
        )
        compliance_dept = Department(
            id=uuid.uuid4(),
            name="Compliance Department",
            code="COMPLIANCE",
            is_active=True,
        )
        db.add_all([default_dept, legal_dept, compliance_dept])
        db.flush()

        # Create users
        users = [
            User(
                id=uuid.uuid4(),
                email="admin@laos.gov.in",
                full_name="Admin User",
                hashed_password=pwd_context.hash("Admin@123456"),
                department_id=default_dept.id,
                role=UserRole.ADMIN,
                is_active=True,
            ),
            User(
                id=uuid.uuid4(),
                email="reviewer@laos.gov.in",
                full_name="Reviewer User",
                hashed_password=pwd_context.hash("Reviewer@123456"),
                department_id=legal_dept.id,
                role=UserRole.REVIEWER,
                is_active=True,
            ),
            User(
                id=uuid.uuid4(),
                email="officer@laos.gov.in",
                full_name="Officer User",
                hashed_password=pwd_context.hash("Officer@123456"),
                department_id=compliance_dept.id,
                role=UserRole.OFFICER,
                is_active=True,
            ),
            User(
                id=uuid.uuid4(),
                email="viewer@laos.gov.in",
                full_name="Viewer User",
                hashed_password=pwd_context.hash("Viewer@123456"),
                department_id=default_dept.id,
                role=UserRole.VIEWER,
                is_active=True,
            ),
        ]
        db.add_all(users)
        db.commit()

        print("✓ Seeded 3 departments and 4 users")
        print("\n  Test Accounts:")
        print("    Admin:    admin@laos.gov.in / Admin@123456")
        print("    Reviewer: reviewer@laos.gov.in / Reviewer@123456")
        print("    Officer:  officer@laos.gov.in / Officer@123456")
        print("    Viewer:   viewer@laos.gov.in / Viewer@123456")

    except Exception as e:
        db.rollback()
        print(f"✗ Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_tables()
    seed_data()
    print("\n✓ Database setup complete!")
