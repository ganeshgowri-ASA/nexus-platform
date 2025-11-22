"""
Database initialization script for NEXUS Platform.

This module provides utilities for initializing the database,
creating sample data, and managing database lifecycle.
"""

import sys
from typing import Optional
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from database.connection import engine, get_db, init_database, drop_database, get_table_names, Base
from database.models import (
    User,
    Document,
    Email,
    Chat,
    Project,
    Task,
    File,
    AIInteraction,
)


def create_tables():
    """
    Create all database tables.

    This function creates all tables defined in the models.
    For production, use Alembic migrations instead.
    """
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ All tables created successfully")

    # List created tables
    tables = get_table_names()
    print(f"\nCreated tables ({len(tables)}):")
    for table in sorted(tables):
        print(f"  - {table}")


def drop_tables():
    """
    Drop all database tables.

    WARNING: This will delete all data!
    """
    print("WARNING: This will delete all data!")
    response = input("Are you sure you want to drop all tables? (yes/no): ")

    if response.lower() == "yes":
        print("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        print("✓ All tables dropped successfully")
    else:
        print("Operation cancelled")


def create_sample_data():
    """
    Create sample data for testing and development.

    This function populates the database with sample users, documents,
    emails, chats, projects, tasks, files, and AI interactions.
    """
    print("Creating sample data...")

    with get_db() as db:
        try:
            # Create sample users
            print("  Creating users...")
            admin_user = User(
                email="admin@nexus.com",
                username="admin",
                password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lW6P5W1J3XYa",  # "password123"
                full_name="Admin User",
                role="admin",
                is_active=True,
                is_verified=True,
                preferences={"theme": "dark", "notifications": True},
                last_login=datetime.utcnow(),
            )
            db.add(admin_user)

            manager_user = User(
                email="manager@nexus.com",
                username="manager",
                password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lW6P5W1J3XYa",
                full_name="Manager User",
                role="manager",
                is_active=True,
                is_verified=True,
                preferences={"theme": "light", "notifications": True},
            )
            db.add(manager_user)

            regular_user = User(
                email="user@nexus.com",
                username="user",
                password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lW6P5W1J3XYa",
                full_name="Regular User",
                role="user",
                is_active=True,
                is_verified=True,
                preferences={"theme": "dark", "notifications": False},
            )
            db.add(regular_user)

            db.flush()  # Get user IDs

            # Create sample documents
            print("  Creating documents...")
            doc1 = Document(
                user_id=admin_user.id,
                title="NEXUS Platform Requirements",
                type="word",
                content={"text": "This document outlines the requirements for NEXUS Platform..."},
                version=1,
                shared_with={"users": [manager_user.id], "permissions": ["read", "comment"]},
            )
            db.add(doc1)

            doc2 = Document(
                user_id=manager_user.id,
                title="Q4 Budget Planning",
                type="excel",
                content={"sheets": [{"name": "Budget", "data": []}]},
                version=2,
            )
            db.add(doc2)

            # Create sample emails
            print("  Creating emails...")
            email1 = Email(
                user_id=admin_user.id,
                from_addr="admin@nexus.com",
                to_addr="manager@nexus.com",
                subject="Welcome to NEXUS Platform",
                body="Welcome to the NEXUS Platform! This is your admin notification...",
                status="sent",
                sent_at=datetime.utcnow(),
                is_read=False,
            )
            db.add(email1)

            email2 = Email(
                user_id=regular_user.id,
                from_addr="user@nexus.com",
                to_addr="admin@nexus.com",
                cc="manager@nexus.com",
                subject="Question about project timeline",
                body="I have a question about the project timeline...",
                status="sent",
                sent_at=datetime.utcnow(),
                thread_id="thread-001",
            )
            db.add(email2)

            # Create sample chats
            print("  Creating chats...")
            chat1 = Chat(
                user_id=admin_user.id,
                room_id="general",
                message="Welcome everyone to the NEXUS Platform!",
            )
            db.add(chat1)

            chat2 = Chat(
                user_id=manager_user.id,
                room_id="general",
                message="Thanks! Excited to get started.",
                replied_to_id=None,  # Will be set after chat1 is flushed
            )
            db.add(chat2)

            db.flush()  # Get chat IDs
            chat2.replied_to_id = chat1.id

            # Create sample projects
            print("  Creating projects...")
            project1 = Project(
                user_id=admin_user.id,
                name="NEXUS Platform Development",
                description="Main project for developing the NEXUS Platform",
                status="active",
                priority="critical",
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=180),
                completion_percentage=35,
                team_members=[
                    {"user_id": admin_user.id, "role": "lead"},
                    {"user_id": manager_user.id, "role": "developer"},
                    {"user_id": regular_user.id, "role": "tester"},
                ],
                budget=250000.00,
            )
            db.add(project1)

            project2 = Project(
                user_id=manager_user.id,
                name="Marketing Campaign Q4",
                description="Q4 marketing campaign planning and execution",
                status="planning",
                priority="high",
                start_date=datetime.utcnow() + timedelta(days=30),
                end_date=datetime.utcnow() + timedelta(days=120),
                completion_percentage=0,
                team_members=[{"user_id": manager_user.id, "role": "lead"}],
                budget=50000.00,
            )
            db.add(project2)

            db.flush()  # Get project IDs

            # Create sample tasks
            print("  Creating tasks...")
            task1 = Task(
                project_id=project1.id,
                assignee_id=manager_user.id,
                title="Implement database models",
                description="Create SQLAlchemy models for all core entities",
                status="completed",
                priority="high",
                start_date=datetime.utcnow() - timedelta(days=5),
                due_date=datetime.utcnow() - timedelta(days=1),
                completed_at=datetime.utcnow() - timedelta(days=1),
                estimated_hours=16,
                actual_hours=14,
                tags=["backend", "database", "sqlalchemy"],
            )
            db.add(task1)

            task2 = Task(
                project_id=project1.id,
                assignee_id=regular_user.id,
                title="Write API documentation",
                description="Document all REST API endpoints",
                status="in_progress",
                priority="medium",
                start_date=datetime.utcnow(),
                due_date=datetime.utcnow() + timedelta(days=7),
                estimated_hours=20,
                actual_hours=8,
                dependencies=[task1.id],
                tags=["documentation", "api"],
            )
            db.add(task2)

            task3 = Task(
                project_id=project1.id,
                assignee_id=admin_user.id,
                title="Set up CI/CD pipeline",
                description="Configure GitHub Actions for automated testing and deployment",
                status="pending",
                priority="critical",
                due_date=datetime.utcnow() + timedelta(days=3),
                estimated_hours=12,
                tags=["devops", "ci/cd"],
            )
            db.add(task3)

            # Create sample files
            print("  Creating files...")
            file1 = File(
                user_id=admin_user.id,
                filename="nexus-logo.png",
                file_path="/uploads/images/nexus-logo.png",
                file_type="image",
                file_size=245678,
                mime_type="image/png",
                hash="a3b5c7d9e1f2a3b5c7d9e1f2",
                is_public=True,
                download_count=42,
                metadata={"width": 512, "height": 512, "dpi": 72},
            )
            db.add(file1)

            file2 = File(
                user_id=manager_user.id,
                filename="requirements.pdf",
                file_path="/uploads/documents/requirements.pdf",
                file_type="document",
                file_size=1024567,
                mime_type="application/pdf",
                hash="b4c6d8e0f2a4b6c8d0e2f4a6",
                is_public=False,
                download_count=15,
                metadata={"pages": 24, "author": "Manager User"},
            )
            db.add(file2)

            # Create sample AI interactions
            print("  Creating AI interactions...")
            ai1 = AIInteraction(
                user_id=admin_user.id,
                module="document",
                prompt="Summarize this document about NEXUS Platform requirements",
                response="The NEXUS Platform is a comprehensive 24-module integrated system...",
                model_used="gpt-4",
                tokens_used=1250,
                cost=0.0375,
                duration_ms=2340,
            )
            db.add(ai1)

            ai2 = AIInteraction(
                user_id=regular_user.id,
                module="email",
                prompt="Generate a professional email about project status",
                response="Subject: Project Status Update\n\nDear Team,\n\nI hope this email finds you well...",
                model_used="gpt-3.5-turbo",
                tokens_used=450,
                cost=0.0009,
                duration_ms=890,
            )
            db.add(ai2)

            # Commit all changes
            db.commit()
            print("✓ Sample data created successfully")

        except IntegrityError as e:
            db.rollback()
            print(f"✗ Error creating sample data: {e}")
            print("  Sample data may already exist. Run reset_database() to start fresh.")
        except Exception as e:
            db.rollback()
            print(f"✗ Unexpected error: {e}")
            raise


def reset_database():
    """
    Reset the database by dropping and recreating all tables.

    WARNING: This will delete all data!
    """
    print("WARNING: This will delete all data!")
    response = input("Are you sure you want to reset the database? (yes/no): ")

    if response.lower() == "yes":
        print("\nResetting database...")
        drop_database()
        create_tables()
        print("\n✓ Database reset complete")
    else:
        print("Operation cancelled")


def verify_database():
    """
    Verify database connection and table structure.
    """
    print("Verifying database connection...")

    try:
        with engine.connect() as conn:
            # Test connection
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
            print("✓ Database connection successful")

            # Check tables
            tables = get_table_names()
            expected_tables = {
                "users",
                "documents",
                "emails",
                "chats",
                "projects",
                "tasks",
                "files",
                "ai_interactions",
            }

            existing = set(tables)
            missing = expected_tables - existing
            extra = existing - expected_tables

            if not missing and not extra:
                print(f"✓ All {len(expected_tables)} tables present")
            else:
                if missing:
                    print(f"✗ Missing tables: {missing}")
                if extra:
                    print(f"  Extra tables: {extra}")

    except Exception as e:
        print(f"✗ Database verification failed: {e}")
        raise


def main():
    """
    Main function for database initialization CLI.
    """
    import argparse

    parser = argparse.ArgumentParser(description="NEXUS Platform Database Initialization")
    parser.add_argument(
        "command",
        choices=["create", "drop", "reset", "sample", "verify"],
        help="Command to execute"
    )

    args = parser.parse_args()

    if args.command == "create":
        create_tables()
    elif args.command == "drop":
        drop_tables()
    elif args.command == "reset":
        reset_database()
    elif args.command == "sample":
        create_sample_data()
    elif args.command == "verify":
        verify_database()


if __name__ == "__main__":
    main()
