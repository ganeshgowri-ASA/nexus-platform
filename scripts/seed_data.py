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

    finally:
        db.close()


if __name__ == "__main__":
    main()
