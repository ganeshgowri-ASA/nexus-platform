"""Example: Simple workflow with sequential tasks."""

import asyncio
import httpx


async def create_simple_workflow():
    """Create a simple workflow with 3 sequential tasks."""

    # Define workflow
    workflow_data = {
        "name": "Simple Sequential Workflow",
        "description": "A simple workflow demonstrating sequential task execution",
        "category": "Example",
        "dag_definition": {
            "tasks": {
                "task1": {
                    "task_key": "task1",
                    "name": "Print Hello",
                    "task_type": "python",
                    "config": {
                        "code": """
output['message'] = 'Hello from Task 1!'
print(output['message'])
"""
                    },
                    "depends_on": [],
                    "retry_config": {
                        "max_retries": 3,
                        "retry_delay": 60,
                        "timeout": 300,
                    },
                },
                "task2": {
                    "task_key": "task2",
                    "name": "Process Data",
                    "task_type": "python",
                    "config": {
                        "code": """
# Access output from task1
previous_message = input.get('task1', {}).get('message', 'No message')
output['processed'] = f"Processed: {previous_message}"
print(output['processed'])
"""
                    },
                    "depends_on": ["task1"],
                    "retry_config": {
                        "max_retries": 3,
                        "retry_delay": 60,
                        "timeout": 300,
                    },
                },
                "task3": {
                    "task_key": "task3",
                    "name": "Print Summary",
                    "task_type": "python",
                    "config": {
                        "code": """
processed = input.get('task2', {}).get('processed', 'No data')
output['summary'] = f"Summary: {processed}"
print(output['summary'])
"""
                    },
                    "depends_on": ["task2"],
                    "retry_config": {
                        "max_retries": 3,
                        "retry_delay": 60,
                        "timeout": 300,
                    },
                },
            }
        },
        "tags": ["example", "simple"],
        "is_scheduled": False,
    }

    # Create workflow
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/workflows/",
            json=workflow_data,
        )
        response.raise_for_status()
        workflow = response.json()

        print(f"✅ Created workflow: {workflow['name']} (ID: {workflow['id']})")

        # Trigger workflow
        trigger_response = await client.post(
            f"http://localhost:8000/api/v1/workflows/{workflow['id']}/trigger",
            json={"input_data": {"user": "example"}},
        )
        trigger_response.raise_for_status()
        execution = trigger_response.json()

        print(f"✅ Triggered execution: {execution['run_id']}")

        return workflow, execution


if __name__ == "__main__":
    asyncio.run(create_simple_workflow())
