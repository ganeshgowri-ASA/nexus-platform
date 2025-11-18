# NEXUS Workflow Orchestration - Examples

This directory contains example workflows demonstrating various features of the NEXUS Workflow Orchestration module.

## Running Examples

1. **Start the services:**
   ```bash
   docker-compose up -d
   ```

2. **Run an example:**
   ```bash
   python examples/simple_workflow.py
   python examples/parallel_workflow.py
   python examples/http_workflow.py
   ```

## Examples

### 1. Simple Sequential Workflow (`simple_workflow.py`)
Demonstrates basic sequential task execution where each task depends on the previous one.

**Features:**
- Sequential task execution
- Task output passing
- Simple Python tasks

### 2. Parallel Processing Workflow (`parallel_workflow.py`)
Shows how multiple tasks can run in parallel and their results combined.

**Features:**
- Parallel task execution
- Multiple tasks depending on the same parent
- Result aggregation

### 3. HTTP API Workflow (`http_workflow.py`)
Demonstrates integration with external APIs using HTTP tasks.

**Features:**
- HTTP GET requests
- API response processing
- Error handling

## Creating Custom Workflows

You can create workflows programmatically or through the Streamlit UI:

### Programmatic Creation

```python
import asyncio
import httpx

async def create_workflow():
    workflow_data = {
        "name": "My Custom Workflow",
        "description": "Description here",
        "category": "Custom",
        "dag_definition": {
            "tasks": {
                "task1": {
                    "task_key": "task1",
                    "name": "My Task",
                    "task_type": "python",
                    "config": {"code": "output['result'] = 'Hello'"},
                    "depends_on": [],
                    "retry_config": {
                        "max_retries": 3,
                        "retry_delay": 60,
                        "timeout": 300
                    }
                }
            }
        },
        "tags": ["custom"],
        "is_scheduled": False
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/workflows/",
            json=workflow_data
        )
        return response.json()

asyncio.run(create_workflow())
```

### Using Streamlit UI

1. Open the UI: http://localhost:8501
2. Navigate to "Workflow Designer"
3. Add tasks using the visual interface
4. Configure dependencies
5. Click "Create Workflow"

## Task Types

### Python Tasks
Execute Python code:
```python
{
    "task_type": "python",
    "config": {
        "code": "output['result'] = input['data'] * 2"
    }
}
```

### HTTP Tasks
Make HTTP requests:
```python
{
    "task_type": "http",
    "config": {
        "method": "GET",
        "url": "https://api.example.com/data",
        "headers": {"Authorization": "Bearer token"}
    }
}
```

### Bash Tasks
Execute shell commands:
```python
{
    "task_type": "bash",
    "config": {
        "command": "echo 'Hello World'"
    }
}
```

### SQL Tasks
Run SQL queries:
```python
{
    "task_type": "sql",
    "config": {
        "query": "SELECT * FROM users LIMIT 10"
    }
}
```

## Best Practices

1. **Task Naming:** Use descriptive names for tasks
2. **Error Handling:** Configure appropriate retry policies
3. **Dependencies:** Keep DAGs simple and avoid deep nesting
4. **Testing:** Validate DAGs before deploying
5. **Monitoring:** Use the dashboard to track execution

## Troubleshooting

- **Connection refused:** Ensure services are running (`docker-compose ps`)
- **Task failures:** Check logs (`docker-compose logs celery_worker`)
- **DAG validation errors:** Use the `/dag/validate` endpoint

## Additional Resources

- API Documentation: http://localhost:8000/docs
- Streamlit UI: http://localhost:8501
- Flower (Celery): http://localhost:5555
- Temporal UI: http://localhost:8088
