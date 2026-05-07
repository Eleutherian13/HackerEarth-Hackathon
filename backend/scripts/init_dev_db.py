#!/usr/bin/env python
"""Initialize development database with tables and seed data."""

import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, event
from sqlalchemy.pool import StaticPool
from app.models.domain.models import Base, User, Department
from app.models.enums import UserRole
from app.core.security import hash_password
from app.core.config import settings


def init_dev_database():
    """Initialize development database with PostgreSQL."""
    
    print("🔧 Initializing development database...")
    
    # Create engine
    engine = create_engine(
        str(settings.DATABASE_URL),
        echo=False,
        pool_pre_ping=True,
        future=True,
    )
    
    # Create all tables
    print("📋 Creating tables...")
    Base.metadata.create_all(engine)
    print("✅ Tables created successfully")
    
    # Add seed data
    from sqlalchemy.orm import Session
    
    with Session(engine) as session:
        # Check if data already exists
        existing_user = session.query(User).filter_by(email="admin@laos.gov.in").first()
        if existing_user:
            print("⏭️  Admin user already exists, skipping seed data")
            return
        
        print("🌱 Seeding database...")
        
        # Create default department
        dept = Department(
            id=uuid.uuid4(),
            name="Legal Affairs",
            code="LA",
            is_active=True,
        )
        session.add(dept)
        session.flush()
        
        # Create admin user
        admin = User(
            id=uuid.uuid4(),
            email="admin@laos.gov.in",
            full_name="Administrator",
            hashed_password=hash_password("Admin@123456"),
            department_id=dept.id,
            role=UserRole.ADMIN,
            is_active=True,
            last_login=None,
            must_change_password=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(admin)
        
        # Create test officer
        officer = User(
            id=uuid.uuid4(),
            email="officer@laos.gov.in",
            full_name="Test Officer",
            hashed_password=hash_password("Officer@123456"),
            department_id=dept.id,
            role=UserRole.OFFICER,
            is_active=True,
            last_login=None,
            must_change_password=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(officer)
        
        session.commit()
        print("✅ Seed data created successfully")
        print("\n📝 Test Credentials:")
        print("  Admin:  admin@laos.gov.in / Admin@123456")
        print("  Officer: officer@laos.gov.in / Officer@123456")


if __name__ == "__main__":
    try:
        init_dev_database()
        print("\n✨ Database initialization complete!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
