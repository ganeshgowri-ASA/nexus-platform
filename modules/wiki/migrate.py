"""
Wiki Database Migration Script

Simple migration script to create and manage wiki database tables.
For production, consider using Alembic for more advanced migrations.

Author: NEXUS Platform Team
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import inspect
from app.utils import get_logger
from database import engine, Base
from modules.wiki.models import (
    WikiTag, WikiCategory, WikiPage, WikiSection, WikiLink,
    WikiAttachment, WikiComment, WikiHistory, WikiPermission,
    WikiTemplate, WikiAnalytics, WikiMacro
)

logger = get_logger(__name__)


def check_table_exists(table_name: str) -> bool:
    """
    Check if a table exists in the database.

    Args:
        table_name: Name of the table to check

    Returns:
        True if table exists, False otherwise
    """
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def create_wiki_tables():
    """
    Create all wiki tables in the database.

    This will create all tables defined in the wiki models if they don't exist.
    Existing tables will not be modified.
    """
    logger.info("Starting wiki database migration...")

    # List of all wiki tables
    wiki_tables = [
        WikiTag.__table__,
        WikiCategory.__table__,
        WikiPage.__table__,
        WikiSection.__table__,
        WikiLink.__table__,
        WikiAttachment.__table__,
        WikiComment.__table__,
        WikiHistory.__table__,
        WikiPermission.__table__,
        WikiTemplate.__table__,
        WikiAnalytics.__table__,
        WikiMacro.__table__,
    ]

    # Check existing tables
    existing_tables = []
    new_tables = []

    for table in wiki_tables:
        if check_table_exists(table.name):
            existing_tables.append(table.name)
        else:
            new_tables.append(table.name)

    logger.info(f"Existing tables: {len(existing_tables)}")
    logger.info(f"New tables to create: {len(new_tables)}")

    if new_tables:
        logger.info(f"Creating tables: {', '.join(new_tables)}")
        try:
            # Create only the wiki tables
            Base.metadata.create_all(bind=engine, tables=wiki_tables)
            logger.info("✅ Wiki tables created successfully!")
        except Exception as e:
            logger.error(f"❌ Error creating tables: {str(e)}")
            raise
    else:
        logger.info("✅ All wiki tables already exist. No migration needed.")

    # Display table summary
    logger.info("\n" + "="*60)
    logger.info("Wiki Database Schema:")
    logger.info("="*60)

    for table in wiki_tables:
        status = "✓" if table.name in existing_tables else "+"
        logger.info(f"  {status} {table.name}")

    logger.info("="*60)


def drop_wiki_tables():
    """
    Drop all wiki tables from the database.

    WARNING: This will delete all wiki data! Use with caution.
    """
    logger.warning("⚠️  WARNING: This will delete all wiki data!")
    confirmation = input("Type 'DELETE' to confirm: ")

    if confirmation != "DELETE":
        logger.info("Migration cancelled.")
        return

    logger.info("Dropping wiki tables...")

    wiki_tables = [
        WikiTag.__table__,
        WikiCategory.__table__,
        WikiPage.__table__,
        WikiSection.__table__,
        WikiLink.__table__,
        WikiAttachment.__table__,
        WikiComment.__table__,
        WikiHistory.__table__,
        WikiPermission.__table__,
        WikiTemplate.__table__,
        WikiAnalytics.__table__,
        WikiMacro.__table__,
    ]

    try:
        Base.metadata.drop_all(bind=engine, tables=wiki_tables)
        logger.info("✅ Wiki tables dropped successfully!")
    except Exception as e:
        logger.error(f"❌ Error dropping tables: {str(e)}")
        raise


def seed_default_data():
    """
    Seed the database with default wiki data (categories, templates, etc.).
    """
    from database import SessionLocal
    from modules.wiki.wiki_types import TemplateCategory

    logger.info("Seeding default wiki data...")
    db = SessionLocal()

    try:
        # Create default categories
        default_categories = [
            {"name": "Documentation", "slug": "documentation", "icon": "📚", "color": "#3498db"},
            {"name": "Tutorials", "slug": "tutorials", "icon": "🎓", "color": "#2ecc71"},
            {"name": "API Reference", "slug": "api-reference", "icon": "⚙️", "color": "#e74c3c"},
            {"name": "Meeting Notes", "slug": "meeting-notes", "icon": "📝", "color": "#f39c12"},
            {"name": "Projects", "slug": "projects", "icon": "🚀", "color": "#9b59b6"},
        ]

        for cat_data in default_categories:
            existing = db.query(WikiCategory).filter(
                WikiCategory.slug == cat_data["slug"]
            ).first()

            if not existing:
                category = WikiCategory(**cat_data)
                db.add(category)
                logger.info(f"  + Created category: {cat_data['name']}")

        # Create default tags
        default_tags = [
            {"name": "tutorial", "color": "#3498db"},
            {"name": "beginner", "color": "#2ecc71"},
            {"name": "advanced", "color": "#e74c3c"},
            {"name": "api", "color": "#f39c12"},
            {"name": "reference", "color": "#9b59b6"},
        ]

        for tag_data in default_tags:
            existing = db.query(WikiTag).filter(
                WikiTag.name == tag_data["name"]
            ).first()

            if not existing:
                tag = WikiTag(**tag_data)
                db.add(tag)
                logger.info(f"  + Created tag: {tag_data['name']}")

        # Create default templates
        meeting_template = WikiTemplate(
            name="Meeting Notes",
            description="Standard template for meeting notes",
            category=TemplateCategory.MEETING_NOTES,
            content="""# {{meeting_title}}

**Date:** {{date}}
**Attendees:** {{attendees}}
**Facilitator:** {{facilitator}}

## Agenda
1. Item 1
2. Item 2
3. Item 3

## Discussion

### Topic 1
[Notes]

### Topic 2
[Notes]

## Action Items
- [ ] Action 1 - @person
- [ ] Action 2 - @person

## Next Meeting
**Date:** {{next_meeting_date}}
**Topics:**
""",
            variables=["meeting_title", "date", "attendees", "facilitator", "next_meeting_date"],
            is_public=True,
            created_by=1
        )

        existing_template = db.query(WikiTemplate).filter(
            WikiTemplate.name == "Meeting Notes"
        ).first()

        if not existing_template:
            db.add(meeting_template)
            logger.info("  + Created template: Meeting Notes")

        db.commit()
        logger.info("✅ Default data seeded successfully!")

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error seeding data: {str(e)}")
        raise
    finally:
        db.close()


def main():
    """Main migration entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="NEXUS Wiki Database Migration")
    parser.add_argument(
        "command",
        choices=["create", "drop", "seed", "reset"],
        help="Migration command to execute"
    )

    args = parser.parse_args()

    if args.command == "create":
        create_wiki_tables()
    elif args.command == "drop":
        drop_wiki_tables()
    elif args.command == "seed":
        create_wiki_tables()
        seed_default_data()
    elif args.command == "reset":
        drop_wiki_tables()
        create_wiki_tables()
        seed_default_data()


if __name__ == "__main__":
    main()
