#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Create test user directly"""

from app.db.session import SessionLocal
from app.models.domain.models import Department, User
from app.models.enums import UserRole
from app.core.security import hash_password

db = SessionLocal()

try:
    # Get or create default department
    default_dept = db.query(Department).filter(Department.code == "DEFAULT").first()
    if not default_dept:
        default_dept = Department(name="Government of India", code="DEFAULT")
        db.add(default_dept)
        db.commit()
    
    # Create test user
    existing_user = db.query(User).filter(User.email == "admin@example.com").first()
    if not existing_user:
        user = User(
            email="admin@example.com",
            full_name="Admin User",
            hashed_password=hash_password("Test@Pass123"),
            department_id=default_dept.id,
            role=UserRole.SUPERADMIN,
            is_active=True,
            must_change_password=False
        )
        db.add(user)
        db.commit()
        print("DONE - Superadmin created!")
        print("\nLogin Credentials:")
        print("  Email: admin@example.com")
        print("  Password: Test@Pass123")
        print("\nOpen: http://localhost:8081/login")
    else:
        print("DONE - User already exists: admin@example.com")
        
except Exception as e:
    print(f"ERROR: {str(e)}")
    db.rollback()
finally:
    db.close()
