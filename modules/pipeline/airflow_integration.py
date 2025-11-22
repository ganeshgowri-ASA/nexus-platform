"""Airflow integration for Pipeline module."""

import os
from typing import Dict, Any, Optional
from datetime import datetime
import json

from config.settings import settings
from core.utils import get_logger

logger = get_logger(__name__)


class AirflowService:
    """Service for Airflow integration."""

    def __init__(self):
        """Initialize Airflow service."""
        self.airflow_home = settings.AIRFLOW_HOME
        self.dags_folder = os.path.join(self.airflow_home, "dags")
        self.enabled = settings.AIRFLOW_ENABLED

        # Create dags folder if it doesn't exist
        os.makedirs(self.dags_folder, exist_ok=True)

    def sync_pipeline_to_dag(self, pipeline, schedule=None) -> Dict[str, Any]:
        """
        Sync pipeline to Airflow DAG.

        Args:
            pipeline: Pipeline model
            schedule: Schedule model (optional)

        Returns:
            Sync results
        """
        if not self.enabled:
            logger.warning("Airflow integration is disabled")
            return {"success": False, "message": "Airflow integration disabled"}

        try:
            dag_id = f"nexus_pipeline_{pipeline.id}"
            dag_file_path = os.path.join(self.dags_folder, f"{dag_id}.py")

            # Generate DAG Python code
            dag_code = self._generate_dag_code(pipeline, schedule, dag_id)

            # Write DAG file
            with open(dag_file_path, 'w') as f:
                f.write(dag_code)

            logger.info(f"Synced pipeline {pipeline.id} to Airflow DAG: {dag_id}")

            return {
                "success": True,
                "dag_id": dag_id,
                "dag_file": dag_file_path
            }

        except Exception as e:
            logger.error(f"Failed to sync pipeline to Airflow: {e}")
            return {
                "success": False,
                "message": str(e)
            }

    def _generate_dag_code(self, pipeline, schedule, dag_id: str) -> str:
        """
        Generate Airflow DAG Python code.

        Args:
            pipeline: Pipeline model
            schedule: Schedule model
            dag_id: DAG ID

        Returns:
            DAG Python code
        """
        # Get schedule configuration
        if schedule:
            schedule_interval = schedule.cron_expression
            start_date = schedule.start_date or datetime(2024, 1, 1)
        else:
            schedule_interval = None
            start_date = datetime(2024, 1, 1)

        # Generate code
        code = f'''"""
Auto-generated Airflow DAG for NEXUS Pipeline: {pipeline.name}
Generated at: {datetime.utcnow().isoformat()}
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import requests
import os

# DAG default arguments
default_args = {{
    'owner': 'nexus',
    'depends_on_past': False,
    'start_date': datetime({start_date.year}, {start_date.month}, {start_date.day}),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}}

# Create DAG
dag = DAG(
    '{dag_id}',
    default_args=default_args,
    description='{pipeline.description or pipeline.name}',
    schedule_interval={'None' if schedule_interval is None else f"'{schedule_interval}'"},
    catchup=False,
    tags=['nexus', 'pipeline'],
)


def execute_pipeline(**context):
    """Execute NEXUS pipeline via API."""
    import os
    import requests

    api_url = os.getenv('NEXUS_API_URL', 'http://localhost:8000')

    response = requests.post(
        f'{{api_url}}/api/v1/pipelines/{pipeline.id}/execute',
        json={{
            'trigger_type': 'schedule',
            'execution_date': context['execution_date'].isoformat()
        }}
    )

    if response.status_code != 200:
        raise Exception(f'Pipeline execution failed: {{response.text}}')

    return response.json()


# Create task
execute_task = PythonOperator(
    task_id='execute_pipeline',
    python_callable=execute_pipeline,
    provide_context=True,
    dag=dag,
)
'''

        return code

    def delete_dag(self, dag_id: str) -> bool:
        """
        Delete Airflow DAG.

        Args:
            dag_id: DAG ID

        Returns:
            True if deleted
        """
        if not self.enabled:
            return False

        try:
            dag_file_path = os.path.join(self.dags_folder, f"{dag_id}.py")

            if os.path.exists(dag_file_path):
                os.remove(dag_file_path)
                logger.info(f"Deleted Airflow DAG: {dag_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to delete DAG: {e}")
            return False

    def trigger_dag_run(self, dag_id: str, conf: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Trigger a DAG run via Airflow API.

        Args:
            dag_id: DAG ID
            conf: DAG run configuration

        Returns:
            DAG run info
        """
        if not self.enabled:
            return {"success": False, "message": "Airflow integration disabled"}

        try:
            import requests
            from requests.auth import HTTPBasicAuth

            url = f"{settings.AIRFLOW_API_URL}/dags/{dag_id}/dagRuns"

            auth = HTTPBasicAuth(settings.AIRFLOW_USERNAME, settings.AIRFLOW_PASSWORD)

            payload = {
                "conf": conf or {},
                "dag_run_id": f"manual_{datetime.utcnow().isoformat()}"
            }

            response = requests.post(url, json=payload, auth=auth)
            response.raise_for_status()

            logger.info(f"Triggered DAG run: {dag_id}")

            return {
                "success": True,
                "dag_run": response.json()
            }

        except Exception as e:
            logger.error(f"Failed to trigger DAG run: {e}")
            return {
                "success": False,
                "message": str(e)
            }

    def get_dag_runs(self, dag_id: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get DAG runs via Airflow API.

        Args:
            dag_id: DAG ID
            limit: Number of runs to fetch

        Returns:
            DAG runs
        """
        if not self.enabled:
            return {"success": False, "message": "Airflow integration disabled"}

        try:
            import requests
            from requests.auth import HTTPBasicAuth

            url = f"{settings.AIRFLOW_API_URL}/dags/{dag_id}/dagRuns"

            auth = HTTPBasicAuth(settings.AIRFLOW_USERNAME, settings.AIRFLOW_PASSWORD)

            params = {"limit": limit}

            response = requests.get(url, params=params, auth=auth)
            response.raise_for_status()

            return {
                "success": True,
                "dag_runs": response.json().get("dag_runs", [])
            }

        except Exception as e:
            logger.error(f"Failed to get DAG runs: {e}")
            return {
                "success": False,
                "message": str(e)
            }
