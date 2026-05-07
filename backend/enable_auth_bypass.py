#!/usr/bin/env python3
"""
Enable Authentication Bypass Mode

This script enables AUTH_BYPASS mode for development/testing.
When enabled, all requests will bypass authentication and use a system user.

Usage:
    python enable_auth_bypass.py --enable    # Enable auth bypass
    python enable_auth_bypass.py --disable   # Disable auth bypass (normal mode)
    python enable_auth_bypass.py --status    # Check current status
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv, set_key

def get_env_file():
    """Get the .env file path."""
    env_file = Path(__file__).parent / ".env"
    return env_file

def enable_bypass():
    """Enable authentication bypass."""
    env_file = get_env_file()
    
    # Create .env if it doesn't exist
    if not env_file.exists():
        print(f"Creating .env file at {env_file}")
        # Copy from .env.example if it exists
        example_file = Path(__file__).parent / ".env.example"
        if example_file.exists():
            with open(example_file, 'r') as f:
                example_content = f.read()
            with open(env_file, 'w') as f:
                f.write(example_content)
        else:
            # Create minimal .env
            env_file.write_text("""
# Minimal configuration for AUTH_BYPASS demo
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key-minimum-32-characters-long!
JWT_SECRET_KEY=your-jwt-secret-key-minimum-32-characters-long!
DATABASE_URL=postgresql://user:password@localhost:5432/laos
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
AUTH_BYPASS=false
""")
    
    # Set AUTH_BYPASS to true
    set_key(str(env_file), "AUTH_BYPASS", "true")
    print("✅ Authentication bypass ENABLED")
    print(f"   Configuration file: {env_file}")
    print("\n📝 When AUTH_BYPASS is true:")
    print("   • All requests bypass token validation")
    print("   • A system user (00000000-0000-0000-0000-000000000001) handles all requests")
    print("   • User has SUPERADMIN role and full access")
    print("   • LLM features and document upload/processing work without auth tokens")

def disable_bypass():
    """Disable authentication bypass."""
    env_file = get_env_file()
    
    if env_file.exists():
        set_key(str(env_file), "AUTH_BYPASS", "false")
        print("✅ Authentication bypass DISABLED")
        print(f"   Configuration file: {env_file}")
        print("\n📝 Normal mode active:")
        print("   • JWT token validation is required")
        print("   • Users must provide valid authentication tokens")
    else:
        print("❌ .env file not found")

def check_status():
    """Check the current bypass status."""
    env_file = get_env_file()
    
    if not env_file.exists():
        print("❌ .env file not found")
        print(f"   Expected location: {env_file}")
        return
    
    load_dotenv(str(env_file))
    status = os.getenv("AUTH_BYPASS", "false").lower()
    
    if status == "true":
        print("✅ Authentication bypass is ENABLED")
        print("\n🚀 Backend API is running in bypass mode:")
        print("   • No authentication required for API requests")
        print("   • All features accessible without tokens")
        print("   • Perfect for development and testing LLM features")
    else:
        print("🔐 Authentication bypass is DISABLED")
        print("\n🔑 Normal authentication mode active:")
        print("   • JWT token validation required")
        print("   • Login required via /api/v1/auth/login")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        check_status()
        return
    
    command = sys.argv[1].lower()
    
    if command in ["--enable", "enable"]:
        enable_bypass()
    elif command in ["--disable", "disable"]:
        disable_bypass()
    elif command in ["--status", "status"]:
        check_status()
    else:
        print(f"❌ Unknown command: {command}")
        print(__doc__)

if __name__ == "__main__":
    main()
