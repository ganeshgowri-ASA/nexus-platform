#!/usr/bin/env python3
"""
Database initialization script for NEXUS Platform.
Run this script to create database tables and initialize default data.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from modules.database.connection import init_db


def main():
    """Main initialization function."""
    print("=" * 60)
    print("NEXUS Platform - Database Initialization")
    print("=" * 60)
    print()

    try:
        print("🚀 Starting database initialization...")
        print()

        # Initialize database
        init_db()

        print()
        print("=" * 60)
        print("✅ Database initialization completed successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Run: streamlit run app.py")
        print("2. Navigate to the Register page to create your first account")
        print("3. Assign admin role to your account if needed")
        print()

    except Exception as e:
        print()
        print("=" * 60)
        print("❌ Database initialization failed!")
        print("=" * 60)
        print(f"Error: {str(e)}")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
