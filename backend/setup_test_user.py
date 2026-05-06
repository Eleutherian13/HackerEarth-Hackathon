#!/usr/bin/env python
"""Setup test user and database schema"""

import sys
from datetime import datetime
from app.db.session import SessionLocal, engine
from app.models.domain.models import Base, Department, User
from app.models.enums import UserRole
from app.core.security import hash_password

# Create all tables
print("Creating database schema...")
Base.metadata.create_all(bind=engine)
print("✓ Schema created")

# Create session
db = SessionLocal()

try:
    # Check if default department exists
    default_dept = db.query(Department).filter(Department.code == "DEFAULT").first()
    
    if not default_dept:
        print("Creating default department...")
        default_dept = Department(name="Government of India", code="DEFAULT")
        db.add(default_dept)
        db.commit()
        print("✓ Department created")
    
    # Create test user
    print("Creating test superadmin user...")
    user = User(
        email="admin@example.com",
        full_name="Admin User",
        hashed_password=hash_password("Admin@12345"),
        department_id=default_dept.id,
        role=UserRole.SUPERADMIN,
        is_active=True,
        must_change_password=False
    )
    db.add(user)
    db.commit()
    
    print("\n✓ Superadmin user created successfully!")
    print(f"\nLogin credentials:")
    print(f"  Email: admin@example.com")
    print(f"  Password: Admin@12345")
    print(f"\nYou can now login at: http://localhost:8081/login")

except Exception as e:
    print(f"✗ Error: {e}")
    db.rollback()
finally:
    db.close()
