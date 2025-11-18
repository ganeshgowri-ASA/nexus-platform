"""Seed sample data for NEXUS Platform."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import SessionLocal
from database.models.batch_job import BatchJob, BatchTask, JobStatus, TaskStatus
from modules.batch_processing.service import BatchJobService, BatchTaskService
from modules.batch_processing.schemas import BatchJobCreate, BatchTaskCreate
from loguru import logger


def seed_batch_jobs():
    """Seed sample batch jobs."""
    db = SessionLocal()

    try:
        logger.info("Seeding sample batch jobs...")

        # Sample job 1: CSV Import
        job1 = BatchJobService.create_job(
            db,
            BatchJobCreate(
                name="Sample CSV Import Job",
                description="Import customer data from CSV file",
                job_type="csv_import",
                config={
                    "delimiter": ",",
                    "has_header": True,
                    "chunk_size": 100
                },
                created_by="admin",
                metadata={"source": "sample_data.csv"}
            )
        )
        job1.total_items = 1000
        db.commit()

        # Create sample tasks for job 1
        for i in range(10):
            BatchTaskService.create_task(
                db,
                BatchTaskCreate(
                    batch_job_id=job1.id,
                    task_number=i + 1,
                    task_name=f"Process chunk {i + 1}",
                    input_data={"chunk_start": i * 100, "chunk_end": (i + 1) * 100},
                    max_retries=3
                )
            )

        logger.info(f"✅ Created job: {job1.name} (ID: {job1.id})")

        # Sample job 2: Data Transformation
        job2 = BatchJobService.create_job(
            db,
            BatchJobCreate(
                name="Data Transformation Job",
                description="Transform customer data with multiple operations",
                job_type="data_transformation",
                config={
                    "transformations": [
                        {"source_column": "name", "target_column": "name_upper", "transformation_type": "uppercase"},
                        {"source_column": "email", "target_column": "email_lower", "transformation_type": "lowercase"}
                    ]
                },
                created_by="admin"
            )
        )
        job2.total_items = 500
        db.commit()

        # Create sample tasks for job 2
        for i in range(5):
            BatchTaskService.create_task(
                db,
                BatchTaskCreate(
                    batch_job_id=job2.id,
                    task_number=i + 1,
                    task_name=f"Transform batch {i + 1}",
                    input_data={"batch_number": i + 1},
                    max_retries=3
                )
            )

        logger.info(f"✅ Created job: {job2.name} (ID: {job2.id})")

        # Sample job 3: Completed Job
        job3 = BatchJobService.create_job(
            db,
            BatchJobCreate(
                name="Completed Export Job",
                description="This job has already been completed",
                job_type="data_export",
                config={"format": "excel"},
                created_by="admin"
            )
        )
        job3.total_items = 100
        job3.processed_items = 100
        job3.successful_items = 95
        job3.failed_items = 5
        job3.progress_percentage = 100.0
        job3.status = JobStatus.COMPLETED
        db.commit()

        logger.info(f"✅ Created job: {job3.name} (ID: {job3.id})")

        logger.info(f"🎉 Successfully seeded {3} sample batch jobs!")

    except Exception as e:
        logger.error(f"❌ Error seeding data: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_batch_jobs()
