"""Example: Workflow with HTTP API calls."""

import asyncio
import httpx


async def create_http_workflow():
    """Create a workflow that makes HTTP API calls."""

    workflow_data = {
        "name": "HTTP API Workflow",
        "description": "Demonstrates HTTP task execution and API integration",
        "category": "API Integration",
        "dag_definition": {
            "tasks": {
                "fetch_users": {
                    "task_key": "fetch_users",
                    "name": "Fetch Users from API",
                    "task_type": "http",
                    "config": {
                        "method": "GET",
                        "url": "https://jsonplaceholder.typicode.com/users",
                        "timeout": 30,
                    },
                    "depends_on": [],
                    "retry_config": {"max_retries": 3, "retry_delay": 30, "timeout": 60},
                },
                "process_users": {
                    "task_key": "process_users",
                    "name": "Process User Data",
                    "task_type": "python",
                    "config": {
                        "code": """
import json

# Get users from previous task
users_response = input.get('fetch_users', {}).get('body', [])

# Process users
if isinstance(users_response, str):
    users = json.loads(users_response)
else:
    users = users_response

# Extract names and emails
output['user_count'] = len(users)
output['user_emails'] = [user.get('email') for user in users[:5]]
output['summary'] = f"Processed {len(users)} users"

print(f"User count: {output['user_count']}")
print(f"Sample emails: {output['user_emails']}")
"""
                    },
                    "depends_on": ["fetch_users"],
                    "retry_config": {"max_retries": 3, "retry_delay": 60, "timeout": 300},
                },
                "send_notification": {
                    "task_key": "send_notification",
                    "name": "Send Summary",
                    "task_type": "python",
                    "config": {
                        "code": """
summary = input.get('process_users', {}).get('summary', 'No summary')
output['notification_sent'] = True
output['message'] = f"Workflow completed: {summary}"
print(output['message'])
"""
                    },
                    "depends_on": ["process_users"],
                    "retry_config": {"max_retries": 3, "retry_delay": 60, "timeout": 300},
                },
            }
        },
        "tags": ["example", "http", "api"],
        "is_scheduled": False,
    }

    # Create and trigger workflow
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
        )
        trigger_response.raise_for_status()
        execution = trigger_response.json()

        print(f"✅ Triggered execution: {execution['run_id']}")

        return workflow, execution


if __name__ == "__main__":
    asyncio.run(create_http_workflow())
