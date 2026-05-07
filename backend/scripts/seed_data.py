"""
Seed data initialization for LAOS system.
Creates initial departments, users, and system configuration.

Usage:
    python -m backend.scripts.seed_data
"""

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.db import SessionLocal, init_db
from app.models.domain.models import Department, User
from app.models.enums import UserRole

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def seed_departments(db: Session) -> list[Department]:
    """Create initial departments."""
    departments_data = [
        {"name": "Ministry of Law and Justice", "code": "LAW"},
        {"name": "Department of Revenue", "code": "REV"},
        {"name": "Ministry of Home Affairs", "code": "MHA"},
        {"name": "Ministry of Health and Family Welfare", "code": "HEALTH"},
        {"name": "Ministry of Education", "code": "EDU"},
        {"name": "Ministry of Environment, Forest and Climate Change", "code": "ENV"},
        {"name": "Ministry of Labour and Employment", "code": "LABOUR"},
        {"name": "Ministry of Finance", "code": "FIN"},
        {"name": "Ministry of Road Transport and Highways", "code": "ROAD"},
        {"name": "Ministry of Railways", "code": "RAIL"},
        {"name": "Ministry of External Affairs", "code": "MEA"},
        {"name": "Ministry of Commerce and Industry", "code": "COMM"},
        {"name": "Ministry of Information and Broadcasting", "code": "INFO"},
        {"name": "Ministry of Defence", "code": "DEF"},
        {"name": "Ministry of Agricultural and Farmers Welfare", "code": "AGR"},
    ]

    created_depts = []
    for dept_data in departments_data:
        existing = db.query(Department).filter(Department.code == dept_data["code"]).first()
        if not existing:
            dept = Department(
                name=dept_data["name"],
                code=dept_data["code"],
                is_active=True
            )
            db.add(dept)
            created_depts.append(dept)
            logger.info(f"✓ Created department: {dept_data['name']}")
        else:
            created_depts.append(existing)
            logger.info(f"  Department already exists: {dept_data['name']}")

    db.commit()
    return created_depts


def seed_users(db: Session, departments: list[Department]) -> list[User]:
    """Create initial users."""
    # Get Law and Justice department
    law_dept = next((d for d in departments if d.code == "LAW"), departments[0])

    users_data = [
        {
            "email": "admin@laos.gov.in",
            "full_name": "System Administrator",
            "password": "Admin@123456",
            "role": UserRole.SUPERADMIN,
            "department": law_dept
        },
        {
            "email": "reviewer@laos.gov.in",
            "full_name": "Legal Reviewer",
            "password": "Reviewer@123456",
            "role": UserRole.REVIEWER,
            "department": law_dept
        },
        {
            "email": "officer@laos.gov.in",
            "full_name": "Compliance Officer",
            "password": "Officer@123456",
            "role": UserRole.OFFICER,
            "department": law_dept
        },
        {
            "email": "viewer@laos.gov.in",
            "full_name": "System Viewer",
            "password": "Viewer@123456",
            "role": UserRole.VIEWER,
            "department": law_dept
        },
    ]

    created_users = []
    for user_data in users_data:
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if not existing:
            user = User(
                email=user_data["email"],
                full_name=user_data["full_name"],
                hashed_password=hash_password(user_data["password"]),
                department_id=user_data["department"].id,
                role=user_data["role"],
                is_active=True,
                password_changed_at=datetime.now(timezone.utc)
            )
            db.add(user)
            created_users.append(user)
            logger.info(f"✓ Created user: {user_data['email']} (password: {user_data['password']})")
        else:
            created_users.append(existing)
            logger.info(f"  User already exists: {user_data['email']}")

    db.commit()
    return created_users


def main():
    """Run all seed operations."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("  LAOS - Seed Data Initialization")
    logger.info("=" * 60)
    logger.info("")

    try:
        # Initialize database schema
        logger.info("[1/3] Initializing database schema...")
        init_db()
        logger.info("✓ Database schema initialized")
        logger.info("")

        # Get database session
        db = SessionLocal()

        try:
            # Seed departments
            logger.info("[2/3] Creating departments...")
            departments = seed_departments(db)
            logger.info(f"✓ {len(departments)} departments created/verified")
            logger.info("")

            # Seed users
            logger.info("[3/3] Creating users...")
            users = seed_users(db, departments)
            logger.info(f"✓ {len(users)} users created/verified")
            logger.info("")

            # Summary
            logger.info("=" * 60)
            logger.info("  SEED DATA COMPLETED SUCCESSFULLY")
            logger.info("=" * 60)
            logger.info("")
            logger.info("Test Accounts:")
            logger.info("-" * 60)
            logger.info("  Admin (SUPERADMIN):")
            logger.info("    Email: admin@laos.gov.in")
            logger.info("    Password: Admin@123456")
            logger.info("")
            logger.info("  Reviewer (REVIEWER):")
            logger.info("    Email: reviewer@laos.gov.in")
            logger.info("    Password: Reviewer@123456")
            logger.info("")
            logger.info("  Officer (OFFICER):")
            logger.info("    Email: officer@laos.gov.in")
            logger.info("    Password: Officer@123456")
            logger.info("")
            logger.info("  Viewer (VIEWER):")
            logger.info("    Email: viewer@laos.gov.in")
            logger.info("    Password: Viewer@123456")
            logger.info("-" * 60)
            logger.info("")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Seed data initialization failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
