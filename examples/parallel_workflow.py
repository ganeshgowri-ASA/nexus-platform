"""Example: Workflow with parallel task execution."""

import asyncio
import httpx


async def create_parallel_workflow():
    """Create a workflow with parallel task execution."""

    # Define workflow with parallel tasks
    workflow_data = {
        "name": "Parallel Processing Workflow",
        "description": "Demonstrates parallel task execution with a join task",
        "category": "Example",
        "dag_definition": {
            "tasks": {
                "start": {
                    "task_key": "start",
                    "name": "Initialize Data",
                    "task_type": "python",
                    "config": {
                        "code": """
output['data'] = [1, 2, 3, 4, 5]
print(f"Initialized data: {output['data']}")
"""
                    },
                    "depends_on": [],
                    "retry_config": {"max_retries": 3, "retry_delay": 60, "timeout": 300},
                },
                "process_a": {
                    "task_key": "process_a",
                    "name": "Process A (Square)",
                    "task_type": "python",
                    "config": {
                        "code": """
data = input.get('start', {}).get('data', [])
output['result'] = [x ** 2 for x in data]
print(f"Process A result: {output['result']}")
"""
                    },
                    "depends_on": ["start"],
                    "retry_config": {"max_retries": 3, "retry_delay": 60, "timeout": 300},
                },
                "process_b": {
                    "task_key": "process_b",
                    "name": "Process B (Double)",
                    "task_type": "python",
                    "config": {
                        "code": """
data = input.get('start', {}).get('data', [])
output['result'] = [x * 2 for x in data]
print(f"Process B result: {output['result']}")
"""
                    },
                    "depends_on": ["start"],
                    "retry_config": {"max_retries": 3, "retry_delay": 60, "timeout": 300},
                },
                "process_c": {
                    "task_key": "process_c",
                    "name": "Process C (Add 10)",
                    "task_type": "python",
                    "config": {
                        "code": """
data = input.get('start', {}).get('data', [])
output['result'] = [x + 10 for x in data]
print(f"Process C result: {output['result']}")
"""
                    },
                    "depends_on": ["start"],
                    "retry_config": {"max_retries": 3, "retry_delay": 60, "timeout": 300},
                },
                "combine": {
                    "task_key": "combine",
                    "name": "Combine Results",
                    "task_type": "python",
                    "config": {
                        "code": """
result_a = input.get('process_a', {}).get('result', [])
result_b = input.get('process_b', {}).get('result', [])
result_c = input.get('process_c', {}).get('result', [])

output['combined'] = {
    'squared': result_a,
    'doubled': result_b,
    'added': result_c,
    'sum': sum(result_a) + sum(result_b) + sum(result_c)
}
print(f"Combined results: {output['combined']}")
"""
                    },
                    "depends_on": ["process_a", "process_b", "process_c"],
                    "retry_config": {"max_retries": 3, "retry_delay": 60, "timeout": 300},
                },
            }
        },
        "tags": ["example", "parallel"],
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
        print(
            f"   This workflow has 3 tasks (process_a, process_b, process_c) that run in parallel!"
        )

        # Trigger workflow
        trigger_response = await client.post(
            f"http://localhost:8000/api/v1/workflows/{workflow['id']}/trigger",
        )
        trigger_response.raise_for_status()
        execution = trigger_response.json()

        print(f"✅ Triggered execution: {execution['run_id']}")

        return workflow, execution


if __name__ == "__main__":
    asyncio.run(create_parallel_workflow())
