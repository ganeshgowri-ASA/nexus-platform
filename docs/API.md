# NEXUS Scheduler API Documentation

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Currently, the API does not require authentication. This should be added in production.

## Endpoints

### Jobs

#### Create Job

Create a new scheduled job.

**Endpoint:** `POST /jobs/`

**Request Body:**
```json
{
  "name": "Daily Report",
  "description": "Generate daily analytics report",
  "job_type": "cron",
  "cron_expression": "0 9 * * 1-5",
  "interval_seconds": null,
  "scheduled_time": null,
  "calendar_rule": null,
  "task_name": "tasks.generate_report",
  "task_args": [],
  "task_kwargs": {"format": "pdf"},
  "timezone": "US/Eastern",
  "is_active": true,
  "max_retries": 3,
  "retry_delay": 60,
  "retry_backoff": true,
  "priority": 5,
  "tags": ["report", "analytics"],
  "metadata": {},
  "created_by": "admin"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "name": "Daily Report",
  "job_type": "cron",
  "status": "pending",
  "is_active": true,
  "next_run_at": "2025-01-20T14:00:00Z",
  ...
}
```

#### List Jobs

Get all scheduled jobs with optional filtering.

**Endpoint:** `GET /jobs/`

**Query Parameters:**
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Maximum records to return (default: 100, max: 1000)
- `is_active` (bool): Filter by active status
- `job_type` (string): Filter by job type (cron, interval, date, calendar)
- `tags` (string): Comma-separated tags

**Example:**
```
GET /jobs/?is_active=true&job_type=cron&limit=50
```

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "name": "Daily Report",
    ...
  }
]
```

#### Get Job

Get a specific job by ID.

**Endpoint:** `GET /jobs/{job_id}`

**Response:** `200 OK`
```json
{
  "id": 1,
  "name": "Daily Report",
  ...
}
```

#### Update Job

Update an existing job.

**Endpoint:** `PUT /jobs/{job_id}`

**Request Body:**
```json
{
  "name": "Updated Job Name",
  "is_active": false,
  "priority": 7
}
```

**Response:** `200 OK`

#### Delete Job

Delete a job.

**Endpoint:** `DELETE /jobs/{job_id}`

**Response:** `204 No Content`

#### Execute Job

Manually execute a job immediately.

**Endpoint:** `POST /jobs/{job_id}/execute`

**Request Body (Optional):**
```json
{
  "task_args": [1, 2],
  "task_kwargs": {"override": true}
}
```

**Response:** `200 OK`
```json
{
  "message": "Job execution started",
  "task_id": "abc123-def456-ghi789"
}
```

#### Pause Job

Pause a job.

**Endpoint:** `POST /jobs/{job_id}/pause`

**Response:** `200 OK`
```json
{
  "message": "Job paused"
}
```

#### Resume Job

Resume a paused job.

**Endpoint:** `POST /jobs/{job_id}/resume`

**Response:** `200 OK`
```json
{
  "message": "Job resumed"
}
```

#### Get Job Executions

Get execution history for a specific job.

**Endpoint:** `GET /jobs/{job_id}/executions`

**Query Parameters:**
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Maximum records to return (default: 50, max: 500)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "job_id": 1,
    "status": "completed",
    "started_at": "2025-01-20T14:00:00Z",
    "completed_at": "2025-01-20T14:05:30Z",
    "duration_seconds": 330,
    ...
  }
]
```

### Statistics

#### Get Overview Stats

Get overall scheduler statistics.

**Endpoint:** `GET /jobs/stats/overview`

**Response:** `200 OK`
```json
{
  "total_jobs": 15,
  "active_jobs": 12,
  "paused_jobs": 3,
  "total_executions": 1543,
  "successful_executions": 1489,
  "failed_executions": 54,
  "running_executions": 2,
  "average_duration": 125.5,
  "last_24h_executions": 287
}
```

### Cron

#### Validate Cron Expression

Validate a cron expression and get next run times.

**Endpoint:** `POST /cron/validate`

**Request Body:**
```json
{
  "expression": "*/5 * * * *",
  "timezone": "UTC"
}
```

**Response:** `200 OK`
```json
{
  "is_valid": true,
  "description": "Every 5 minutes",
  "next_runs": [
    "2025-01-20T14:05:00Z",
    "2025-01-20T14:10:00Z",
    "2025-01-20T14:15:00Z",
    "2025-01-20T14:20:00Z",
    "2025-01-20T14:25:00Z"
  ],
  "error": null
}
```

#### Get Cron Presets

Get common cron expression presets.

**Endpoint:** `GET /cron/presets`

**Response:** `200 OK`
```json
{
  "every_minute": {
    "expression": "* * * * *",
    "description": "Every minute"
  },
  "hourly": {
    "expression": "0 * * * *",
    "description": "Every hour"
  },
  "daily_midnight": {
    "expression": "0 0 * * *",
    "description": "Daily at midnight"
  },
  ...
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request data"
}
```

### 404 Not Found
```json
{
  "detail": "Job not found"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "cron_expression"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limiting

Currently, there are no rate limits. This should be implemented in production.

## Pagination

List endpoints support pagination via `skip` and `limit` query parameters.

**Example:**
```
GET /jobs/?skip=20&limit=10
```

## Filtering

Jobs can be filtered by:
- `is_active`: Boolean
- `job_type`: String (cron, interval, date, calendar)
- `tags`: Comma-separated string

**Example:**
```
GET /jobs/?is_active=true&job_type=cron&tags=report,analytics
```

## Sorting

Jobs are sorted by `created_at` in descending order (newest first).

## WebSocket Support

WebSocket support for real-time updates is planned for future releases.
