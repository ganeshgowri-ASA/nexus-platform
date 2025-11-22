<<<<<<< HEAD
#!/usr/bin/env python
"""
Sample data seeding script for NEXUS Platform.

This script populates the database with sample data for development and testing:
- Users (admin, regular users)
- Folders
- Documents
- Tags
- Permissions
- Comments

Usage:
    python scripts/seed_data.py [OPTIONS]

Options:
    --clear         Clear existing data before seeding
    --users N       Number of users to create (default: 10)
    --documents N   Number of documents to create (default: 50)
    --help          Show this help message
"""

import argparse
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from faker import Faker

from backend.core.logging import get_logger
from backend.core.security import get_password_hash
from backend.database import get_db_session
from backend.models.document import (
    AccessLevel,
    Document,
    DocumentComment,
    DocumentMetadata,
    DocumentPermission,
    DocumentStatus,
    DocumentTag,
    Folder,
    Tag,
)
from backend.models.user import User

logger = get_logger(__name__)
fake = Faker()

# Sample data constants
SAMPLE_TAGS = [
    ("Important", "#FF5733"),
    ("Urgent", "#E74C3C"),
    ("Draft", "#95A5A6"),
    ("Approved", "#27AE60"),
    ("Review", "#F39C12"),
    ("Marketing", "#3498DB"),
    ("Finance", "#9B59B6"),
    ("HR", "#1ABC9C"),
    ("Legal", "#34495E"),
    ("Technical", "#16A085"),
]

SAMPLE_FOLDER_NAMES = [
    "Projects",
    "Marketing Materials",
    "Financial Reports",
    "HR Documents",
    "Legal Contracts",
    "Technical Documentation",
    "Meeting Notes",
    "Proposals",
    "Invoices",
    "Presentations",
]

MIME_TYPES = [
    ("application/pdf", ".pdf"),
    ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", ".docx"),
    ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", ".xlsx"),
    ("application/vnd.openxmlformats-officedocument.presentationml.presentation", ".pptx"),
    ("text/plain", ".txt"),
    ("image/png", ".png"),
    ("image/jpeg", ".jpg"),
]


def clear_data(db) -> None:
    """Clear all existing data from database."""
    logger.info("Clearing existing data...")

    # Delete in reverse order of foreign key dependencies
    db.query(DocumentComment).delete()
    db.query(DocumentPermission).delete()
    db.query(DocumentTag).delete()
    db.query(DocumentMetadata).delete()
    db.query(Document).delete()
    db.query(Folder).delete()
    db.query(Tag).delete()
    # Don't delete users - keep any existing admin users
    db.query(User).filter(User.is_admin == False).delete()

    db.commit()
    logger.info("Existing data cleared")


def create_users(db, count: int) -> list[User]:
    """Create sample users."""
    logger.info(f"Creating {count} users...")

    users = []

    # Ensure admin user exists
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            email="admin@nexus.local",
            username="admin",
            hashed_password=get_password_hash("Admin@123"),
            full_name="System Administrator",
            is_active=True,
            is_admin=True,
            is_superuser=True,
            is_verified=True,
            password_changed_at=datetime.utcnow(),
            storage_quota=107374182400,  # 100GB
            storage_used=0,
        )
        db.add(admin)
        users.append(admin)

    # Create regular users
    for i in range(count):
        first_name = fake.first_name()
        last_name = fake.last_name()
        username = f"{first_name.lower()}.{last_name.lower()}{i}"

        user = User(
            email=fake.email(),
            username=username,
            hashed_password=get_password_hash("Password@123"),
            full_name=f"{first_name} {last_name}",
            bio=fake.text(max_nb_chars=200),
            phone=fake.phone_number()[:20],
            is_active=True,
            is_admin=random.choice([True, False]) if i % 5 == 0 else False,
            is_superuser=False,
            is_verified=random.choice([True, True, True, False]),  # 75% verified
            last_login=fake.date_time_between(start_date="-30d", end_date="now"),
            password_changed_at=fake.date_time_between(start_date="-90d", end_date="now"),
            storage_quota=10737418240,  # 10GB
            storage_used=random.randint(0, 5368709120),  # 0-5GB used
        )
        db.add(user)
        users.append(user)

    db.commit()
    logger.info(f"Created {len(users)} users")
    return users


def create_tags(db) -> list[Tag]:
    """Create sample tags."""
    logger.info("Creating tags...")

    tags = []
    admin = db.query(User).filter(User.is_admin == True).first()

    for name, color in SAMPLE_TAGS:
        tag = Tag(name=name, color=color, created_by_id=admin.id)
        db.add(tag)
        tags.append(tag)

    db.commit()
    logger.info(f"Created {len(tags)} tags")
    return tags


def create_folders(db, users: list[User]) -> list[Folder]:
    """Create sample folders."""
    logger.info("Creating folders...")

    folders = []

    for user in users[:5]:  # Create folders for first 5 users
        # Create root folders
        for folder_name in random.sample(SAMPLE_FOLDER_NAMES, k=random.randint(2, 4)):
            folder = Folder(
                name=folder_name,
                description=fake.text(max_nb_chars=200),
                path=f"/{folder_name}",
                owner_id=user.id,
                is_public=random.choice([True, False]),
                color=random.choice(["#3498DB", "#E74C3C", "#27AE60", "#F39C12", "#9B59B6"]),
                icon=random.choice(["folder", "folder-open", "archive", "briefcase"]),
            )
            db.add(folder)
            folders.append(folder)

    db.commit()

    # Create subfolders
    subfolders = []
    for folder in random.sample(folders, k=min(10, len(folders))):
        for i in range(random.randint(1, 3)):
            subfolder = Folder(
                name=fake.word().title(),
                description=fake.text(max_nb_chars=100),
                path=f"{folder.path}/{fake.word()}",
                parent_id=folder.id,
                owner_id=folder.owner_id,
                is_public=folder.is_public,
                color=folder.color,
            )
            db.add(subfolder)
            subfolders.append(subfolder)

    db.commit()
    folders.extend(subfolders)

    logger.info(f"Created {len(folders)} folders")
    return folders


def create_documents(db, users: list[User], folders: list[Folder], tags: list[Tag], count: int) -> list[Document]:
    """Create sample documents."""
    logger.info(f"Creating {count} documents...")

    documents = []

    for i in range(count):
        owner = random.choice(users)
        folder = random.choice(folders) if folders and random.random() > 0.3 else None
        mime_type, ext = random.choice(MIME_TYPES)

        # Generate file info
        file_name = f"{fake.word()}_{i}{ext}"
        file_size = random.randint(1024, 10485760)  # 1KB - 10MB
        file_hash = fake.sha256()

        document = Document(
            title=fake.catch_phrase(),
            description=fake.text(max_nb_chars=500),
            file_name=file_name,
            file_path=f"/storage/{owner.id}/{file_hash}{ext}",
            file_size=file_size,
            mime_type=mime_type,
            file_hash=file_hash,
            status=random.choice(list(DocumentStatus)),
            owner_id=owner.id,
            folder_id=folder.id if folder else None,
            is_public=random.choice([True, False]),
            view_count=random.randint(0, 1000),
            download_count=random.randint(0, 500),
            current_version=random.randint(1, 5),
            is_locked=random.choice([True, False]) if random.random() > 0.9 else False,
            locked_by_id=owner.id if random.random() > 0.9 else None,
            locked_at=datetime.utcnow() if random.random() > 0.9 else None,
            retention_date=fake.date_time_between(start_date="+1y", end_date="+7y")
            if random.random() > 0.7
            else None,
            is_on_legal_hold=random.choice([True, False]) if random.random() > 0.95 else False,
        )
        db.add(document)
        documents.append(document)

        # Update owner's storage
        owner.storage_used += file_size

    db.commit()

    # Add tags to documents
    for document in documents:
        num_tags = random.randint(0, 3)
        for tag in random.sample(tags, k=num_tags):
            doc_tag = DocumentTag(
                document_id=document.id,
                tag_id=tag.id,
                added_by_id=document.owner_id,
            )
            db.add(doc_tag)

    # Add metadata
    for document in random.sample(documents, k=int(count * 0.6)):
        for _ in range(random.randint(1, 4)):
            metadata = DocumentMetadata(
                document_id=document.id,
                key=random.choice(["author", "department", "project", "category", "client"]),
                value=fake.word(),
                value_type="string",
                is_system=False,
            )
            db.add(metadata)

    # Add permissions
    for document in random.sample(documents, k=int(count * 0.4)):
        for user in random.sample(users, k=random.randint(1, 3)):
            if user.id != document.owner_id:
                permission = DocumentPermission(
                    document_id=document.id,
                    user_id=user.id,
                    access_level=random.choice([AccessLevel.VIEW, AccessLevel.COMMENT, AccessLevel.EDIT]),
                    granted_by_id=document.owner_id,
                    expires_at=fake.date_time_between(start_date="+30d", end_date="+365d")
                    if random.random() > 0.7
                    else None,
                )
                db.add(permission)

    # Add comments
    for document in random.sample(documents, k=int(count * 0.3)):
        for _ in range(random.randint(1, 5)):
            comment = DocumentComment(
                document_id=document.id,
                user_id=random.choice(users).id,
                content=fake.text(max_nb_chars=300),
                is_resolved=random.choice([True, False]),
            )
            db.add(comment)

    db.commit()
    logger.info(f"Created {len(documents)} documents with metadata, permissions, and comments")
    return documents


def main() -> int:
    """Main function to seed database."""
    parser = argparse.ArgumentParser(
        description="Seed NEXUS Platform database with sample data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing data before seeding",
    )
    parser.add_argument(
        "--users",
        type=int,
        default=10,
        help="Number of users to create (default: 10)",
    )
    parser.add_argument(
        "--documents",
        type=int,
        default=50,
        help="Number of documents to create (default: 50)",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("NEXUS Platform - Data Seeding")
    print("=" * 70)
    print()

    db = get_db_session()

    try:
        if args.clear:
            print("Clearing existing data...")
            clear_data(db)
            print("✓ Data cleared")
            print()

        # Create data
        users = create_users(db, args.users)
        print(f"✓ Created {len(users)} users")

        tags = create_tags(db)
        print(f"✓ Created {len(tags)} tags")

        folders = create_folders(db, users)
        print(f"✓ Created {len(folders)} folders")

        documents = create_documents(db, users, folders, tags, args.documents)
        print(f"✓ Created {len(documents)} documents")

        print()
        print("=" * 70)
        print("Sample data seeded successfully!")
        print("=" * 70)
        print()
        print("Sample credentials:")
        print("  Admin: admin@nexus.local / Admin@123")
        print("  Users: <username> / Password@123")
        print()

        return 0

    except Exception as e:
        logger.exception("Data seeding failed")
        print(f"\nERROR: {e}")
        print("\nData seeding failed!")
        return 1
=======
"""
Seed database with sample data
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config.database import SessionLocal
from src.database.models import (
    Bot,
    Automation,
    AutomationStatus,
    TriggerType,
)
from src.utils.helpers import generate_id
from src.utils.logger import get_logger

logger = get_logger(__name__)


def seed_bots(db):
    """Seed sample bots"""
    logger.info("Seeding bots...")

    bots = [
        {
            "id": generate_id(),
            "name": "Web Automation Bot",
            "description": "Bot for web scraping and browser automation",
            "bot_type": "ui_automation",
            "capabilities": ["web_scraping", "browser_automation", "form_filling"],
            "configuration": {"browser": "chromium", "headless": True},
            "status": AutomationStatus.ACTIVE,
            "created_by": "admin",
        },
        {
            "id": generate_id(),
            "name": "Data Processing Bot",
            "description": "Bot for data processing and transformation",
            "bot_type": "data_processing",
            "capabilities": ["data_transformation", "csv_processing", "excel_automation"],
            "configuration": {},
            "status": AutomationStatus.ACTIVE,
            "created_by": "admin",
        },
        {
            "id": generate_id(),
            "name": "API Integration Bot",
            "description": "Bot for API calls and integration tasks",
            "bot_type": "api",
            "capabilities": ["rest_api", "webhook", "data_sync"],
            "configuration": {},
            "status": AutomationStatus.ACTIVE,
            "created_by": "admin",
        },
    ]

    created_bots = []
    for bot_data in bots:
        bot = Bot(**bot_data)
        db.add(bot)
        created_bots.append(bot)

    db.commit()
    logger.info(f"✅ Created {len(bots)} sample bots")

    return created_bots


def seed_automations(db, bots):
    """Seed sample automations"""
    logger.info("Seeding automations...")

    automations = [
        {
            "id": generate_id(),
            "name": "Daily Report Generator",
            "description": "Automatically generates daily reports from database",
            "bot_id": bots[1].id if len(bots) > 1 else None,
            "trigger_type": TriggerType.SCHEDULED,
            "workflow": {
                "nodes": [
                    {
                        "id": "node_1",
                        "type": "http_request",
                        "name": "Fetch Data",
                        "config": {
                            "url": "https://api.example.com/data",
                            "method": "GET",
                            "store_as": "api_data",
                        },
                        "position": {"x": 100, "y": 0},
                    },
                    {
                        "id": "node_2",
                        "type": "data_manipulation",
                        "name": "Process Data",
                        "config": {
                            "operation": "parse_json",
                            "data": "{{api_data}}",
                            "store_as": "processed_data",
                        },
                        "position": {"x": 100, "y": 100},
                    },
                    {
                        "id": "node_3",
                        "type": "log",
                        "name": "Log Result",
                        "config": {"message": "Report generated successfully", "level": "INFO"},
                        "position": {"x": 100, "y": 200},
                    },
                ],
                "edges": [
                    {"id": "edge_1", "source": "node_1", "target": "node_2"},
                    {"id": "edge_2", "source": "node_2", "target": "node_3"},
                ],
                "variables": {},
            },
            "inputs": {},
            "outputs": {},
            "variables": {"report_name": "daily_report"},
            "timeout": 1800,
            "status": AutomationStatus.ACTIVE,
            "tags": ["reporting", "daily", "automated"],
            "created_by": "admin",
        },
        {
            "id": generate_id(),
            "name": "Web Scraping Task",
            "description": "Scrapes data from websites periodically",
            "bot_id": bots[0].id if len(bots) > 0 else None,
            "trigger_type": TriggerType.MANUAL,
            "workflow": {
                "nodes": [
                    {
                        "id": "node_1",
                        "type": "http_request",
                        "name": "Fetch Webpage",
                        "config": {
                            "url": "https://example.com",
                            "method": "GET",
                            "store_as": "webpage",
                        },
                        "position": {"x": 100, "y": 0},
                    },
                    {
                        "id": "node_2",
                        "type": "log",
                        "name": "Log Success",
                        "config": {"message": "Webpage fetched", "level": "INFO"},
                        "position": {"x": 100, "y": 100},
                    },
                ],
                "edges": [
                    {"id": "edge_1", "source": "node_1", "target": "node_2"},
                ],
                "variables": {},
            },
            "inputs": {},
            "outputs": {},
            "variables": {},
            "timeout": 3600,
            "status": AutomationStatus.DRAFT,
            "tags": ["scraping", "web"],
            "created_by": "admin",
        },
    ]

    for automation_data in automations:
        automation = Automation(**automation_data)
        db.add(automation)

    db.commit()
    logger.info(f"✅ Created {len(automations)} sample automations")


def main():
    """Main seeding function"""
    logger.info("Starting database seeding...")

    db = SessionLocal()

    try:
        # Seed data
        bots = seed_bots(db)
        seed_automations(db, bots)

        logger.info("✅ Database seeded successfully!")

    except Exception as e:
        logger.error(f"❌ Failed to seed database: {str(e)}")
        db.rollback()
        raise

>>>>>>> origin/claude/build-rpa-module-011gc98wDCMg5EmJGgT8DFqE
    finally:
        db.close()


if __name__ == "__main__":
<<<<<<< HEAD
    sys.exit(main())
=======
    main()
>>>>>>> origin/claude/build-rpa-module-011gc98wDCMg5EmJGgT8DFqE
