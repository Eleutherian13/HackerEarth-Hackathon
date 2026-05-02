#!/usr/bin/env python
"""
Bootstrap script to create the first superadmin user if none exists.

This script:
1. Checks if a superadmin user already exists
2. If not, prompts for superadmin credentials
3. Creates the superadmin in the default department
4. Sets up first login password change requirement
5. Outputs credentials and next steps

Usage:
    python scripts/create_superadmin.py
"""

from __future__ import annotations

import sys
from getpass import getpass
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.core.config import get_settings
from app.core.security import hash_password, validate_password_strength
from app.db.session import SessionLocal, engine
from app.models.domain.models import Department, User
from app.models.enums import UserRole


def check_superadmin_exists(db) -> bool:
    """Check if any superadmin user exists."""
    superadmin = db.execute(
        select(User).where(User.role == UserRole.SUPERADMIN)
    ).scalar_one_or_none()
    return superadmin is not None


def get_or_create_default_department(db) -> Department:
    """Get or create the default department."""
    default_dept = db.execute(
        select(Department).where(Department.code == "DEFAULT")
    ).scalar_one_or_none()
    
    if default_dept is None:
        print("Creating default department...")
        default_dept = Department(
            name="Government of India",
            code="DEFAULT",
            is_active=True,
        )
        db.add(default_dept)
        db.commit()
        db.refresh(default_dept)
    
    return default_dept


def prompt_for_credentials() -> tuple[str, str, str]:
    """Prompt user for superadmin credentials."""
    print("\n" + "=" * 60)
    print("Create Superadmin User".center(60))
    print("=" * 60)
    
    while True:
        email = input("\nEnter superadmin email: ").strip().lower()
        if "@" not in email or len(email) < 5:
            print("Invalid email format. Please try again.")
            continue
        break
    
    while True:
        full_name = input("Enter superadmin full name: ").strip()
        if len(full_name) < 2:
            print("Full name must be at least 2 characters. Please try again.")
            continue
        break
    
    while True:
        password = getpass("Enter superadmin password: ")
        if len(password) == 0:
            print("Password cannot be empty.")
            continue
        
        try:
            validate_password_strength(password)
        except ValueError as e:
            print(f"Password validation failed: {e}")
            continue
        
        password_confirm = getpass("Confirm password: ")
        if password != password_confirm:
            print("Passwords do not match. Please try again.")
            continue
        
        break
    
    return email, full_name, password


def create_superadmin() -> None:
    """Main function to create superadmin."""
    settings = get_settings()
    db = SessionLocal()
    
    try:
        # Check if superadmin already exists
        if check_superadmin_exists(db):
            print("\n✓ Superadmin user already exists. Exiting.")
            return
        
        print("\nNo superadmin found. Creating one now...")
        
        # Get or create default department
        default_dept = get_or_create_default_department(db)
        
        # Prompt for credentials
        email, full_name, password = prompt_for_credentials()
        
        # Create superadmin user
        hashed_password = hash_password(password)
        superadmin = User(
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            department_id=default_dept.id,
            role=UserRole.SUPERADMIN,
            is_active=True,
            must_change_password=True,  # Force password change on first login
        )
        
        db.add(superadmin)
        db.commit()
        db.refresh(superadmin)
        
        # Display confirmation
        print("\n" + "=" * 60)
        print("✓ Superadmin created successfully!".center(60))
        print("=" * 60)
        print(f"\nSuperadmin Details:")
        print(f"  Email: {superadmin.email}")
        print(f"  Full Name: {superadmin.full_name}")
        print(f"  Role: SUPERADMIN")
        print(f"  Department: {default_dept.name}")
        print(f"\nFirst Login Instructions:")
        print(f"  1. Log in with: {superadmin.email}")
        print(f"  2. First login will require immediate password change")
        print(f"  3. After password change, full access enabled")
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error creating superadmin: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    create_superadmin()
