# Celery Background Tasks Setup Guide

This guide provides detailed information about the Celery task queue implementation in Nexus Platform.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Task Types](#task-types)
4. [Configuration](#configuration)
5. [Queue Management](#queue-management)
6. [Monitoring](#monitoring)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## Overview

Nexus Platform uses Celery with Redis for asynchronous task processing. This allows:

- **Non-blocking operations**: Users don't wait for long-running tasks
- **Scalability**: Process multiple tasks concurrently
- **Reliability**: Auto-retry failed tasks
- **Monitoring**: Real-time task tracking and monitoring

## Architecture

### Components

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Streamlit  │─────▶│    Redis    │◀─────│   Celery    │
│     App     │      │   Broker    │      │   Workers   │
└─────────────┘      └─────────────┘      └─────────────┘
       │                    │                     │
       │                    │                     │
       ▼                    ▼                     ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│    Queue    │      │   Result    │      │    Task     │
│    Tasks    │      │   Backend   │      │  Execution  │
└─────────────┘      └─────────────┘      └─────────────┘
```

### Task Flow

1. **User Action**: User triggers an action in Streamlit
2. **Task Queue**: Task is queued in Redis
3. **Worker Pickup**: Available worker picks up task
4. **Execution**: Worker executes task
5. **Result Storage**: Result stored in Redis
6. **User Notification**: User can check result

## Task Types

### 1. Email Tasks (`app/tasks/email_tasks.py`)

**Queue**: `email_queue`

**Tasks**:
- `send_email`: Send individual emails with attachments
- `send_bulk_emails`: Send multiple emails in batch
- `send_notification`: Send templated notifications
- `send_scheduled_email`: Schedule emails for future delivery

**Example**:
```python
from app.tasks.email_tasks import send_email

task = send_email.delay(
    to_email="user@example.com",
    subject="Welcome to Nexus",
    body="Thank you for joining!",
    html_body="<h1>Welcome!</h1>"
)
```

**Retry Policy**:
- Max retries: 3
- Countdown: 60 seconds
- Backoff: True

### 2. File Processing Tasks (`app/tasks/file_tasks.py`)

**Queue**: `file_processing_queue`

**Tasks**:
- `process_word_document`: Extract text, stats, images from DOCX
- `process_excel_file`: Analyze, convert, calculate Excel files
- `process_powerpoint`: Extract text and analyze PPT structure
- `process_pdf`: Extract text and metadata from PDFs
- `process_image`: Resize, thumbnail, get image info
- `batch_process_files`: Process multiple files in parallel
- `cleanup_temp_files`: Clean up temporary files (periodic)

**Example**:
```python
from app.tasks.file_tasks import process_word_document

task = process_word_document.delay(
    file_path="/uploads/document.docx",
    operations=["extract_text", "count_stats", "extract_images"]
)

result = task.get()
print(f"Text file: {result['outputs']['text_file']}")
print(f"Stats: {result['outputs']['stats']}")
```

**Retry Policy**:
- Max retries: 2
- Countdown: 30 seconds

### 3. AI Tasks (`app/tasks/ai_tasks.py`)

**Queue**: `ai_queue`

**Tasks**:
- `claude_completion`: Generate text using Claude AI
- `openai_completion`: Generate text using GPT
- `analyze_document`: AI-powered document analysis
- `generate_content`: Generate various content types
- `translate_text`: Translate text between languages
- `chat_completion`: Multi-turn chat conversations
- `batch_ai_requests`: Process multiple AI requests

**Example**:
```python
from app.tasks.ai_tasks import analyze_document

task = analyze_document.delay(
    document_text="Your long document here...",
    analysis_type="summary"
)

result = task.get()
print(f"Summary: {result['content']}")
```

**Retry Policy**:
- Max retries: 3
- Countdown: 10 seconds
- Rate limit: 10/minute
- Time limit: 10 minutes

### 4. Report Tasks (`app/tasks/report_tasks.py`)

**Queue**: `reports_queue`

**Tasks**:
- `generate_analytics_report`: Create analytics reports
- `generate_summary_report`: Create summary reports with AI
- `export_data`: Export data to various formats
- `generate_task_performance_report`: Report on task metrics
- `schedule_recurring_report`: Schedule periodic reports

**Example**:
```python
from app.tasks.report_tasks import generate_analytics_report

task = generate_analytics_report.delay(
    data={'records': [...]},
    report_type='summary',
    format='html'
)

result = task.get()
print(f"Report saved to: {result['outputs']['html_file']}")
```

**Retry Policy**:
- Max retries: 2
- Countdown: 30 seconds

### 5. Maintenance Tasks (`app/tasks/maintenance_tasks.py`)

**Queue**: `default_queue`

**Tasks**:
- `cleanup_old_results`: Clean old task results from Redis
- `health_check`: System health check
- `monitor_queue_sizes`: Monitor queue lengths
- `cleanup_failed_tasks`: Clean up failed task data
- `archive_old_files`: Archive old uploaded files

**Periodic Schedule**:
- `cleanup_temp_files`: Every hour
- `cleanup_old_results`: Every day

## Configuration

### Celery Settings (`config/celery_config.py`)

```python
celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    task_track_started=True,
    task_time_limit=1800,  # 30 minutes
    task_soft_time_limit=1500,  # 25 minutes
    task_acks_late=True,
    worker_prefetch_multiplier=4,
    result_expires=3600,  # 1 hour
)
```

### Task Routing

```python
task_routes={
    'app.tasks.email_tasks.*': {'queue': 'email_queue'},
    'app.tasks.file_tasks.*': {'queue': 'file_processing_queue'},
    'app.tasks.ai_tasks.*': {'queue': 'ai_queue'},
    'app.tasks.report_tasks.*': {'queue': 'reports_queue'},
}
```

## Queue Management

### Starting Workers

**Single Worker**:
```bash
celery -A config.celery_config worker -Q email_queue --loglevel=info
```

**Multiple Workers**:
```bash
# Use the provided script
./celery_worker.sh
```

**Docker**:
```bash
docker-compose up -d
```

### Queue Priority

Tasks can be prioritized within queues:

```python
task.apply_async(priority=0)  # Highest priority
task.apply_async(priority=5)  # Default
task.apply_async(priority=9)  # Lowest priority
```

### Worker Concurrency

Configure worker concurrency:

```bash
# 4 concurrent tasks
celery -A config.celery_config worker --concurrency=4

# AI queue with limited concurrency
celery -A config.celery_config worker -Q ai_queue --concurrency=2
```

## Monitoring

### 1. Streamlit Dashboard

Navigate to **Task Monitor** page in the app:

- View active tasks
- Check queue lengths
- Monitor worker status
- Execute test tasks
- Check task results

### 2. Flower Dashboard

Access at http://localhost:5555:

```bash
celery -A config.celery_config flower
```

Features:
- Task history
- Worker statistics
- Task timelines
- Rate limiting info

### 3. Command Line

```bash
# Check active workers
celery -A config.celery_config inspect active

# Check scheduled tasks
celery -A config.celery_config inspect scheduled

# Check registered tasks
celery -A config.celery_config inspect registered

# Get statistics
celery -A config.celery_config inspect stats
```

## Best Practices

### 1. Task Design

✅ **DO**:
- Keep tasks focused and single-purpose
- Make tasks idempotent (safe to retry)
- Use appropriate timeouts
- Return structured results
- Log important events

❌ **DON'T**:
- Create tasks that are too granular
- Store large data in task arguments
- Use tasks for real-time operations
- Ignore error handling

### 2. Error Handling

```python
@celery_app.task(bind=True, autoretry_for=(Exception,),
                 retry_kwargs={'max_retries': 3})
def my_task(self, arg):
    try:
        # Task logic
        return result
    except Exception as e:
        logger.error(f"Task failed: {e}")
        raise self.retry(exc=e)
```

### 3. Task Chaining

```python
from celery import chain

# Sequential execution
workflow = chain(
    task1.s(arg1),
    task2.s(),
    task3.s()
)
workflow.apply_async()
```

### 4. Task Grouping

```python
from celery import group

# Parallel execution
job = group([
    task1.s(1),
    task2.s(2),
    task3.s(3)
])
result = job.apply_async()
```

### 5. Performance

- **Use connection pooling**: Redis connections are pooled
- **Set result expiry**: Old results are cleaned up
- **Monitor queue sizes**: Prevent queue buildup
- **Scale workers**: Add workers for high load
- **Use compression**: For large task payloads

## Troubleshooting

### Workers Not Picking Up Tasks

**Check**:
1. Are workers running?
   ```bash
   celery -A config.celery_config inspect active
   ```

2. Is Redis running?
   ```bash
   redis-cli ping
   ```

3. Are queues correct?
   ```bash
   celery -A config.celery_config inspect active_queues
   ```

### Tasks Failing

**Debug**:
1. Check worker logs
2. Verify task arguments
3. Test task function directly
4. Check error messages in Flower

### High Memory Usage

**Solutions**:
1. Reduce worker concurrency
2. Set `worker_max_tasks_per_child`
3. Clean up temp files regularly
4. Monitor with Flower

### Slow Task Processing

**Optimize**:
1. Add more workers
2. Increase concurrency
3. Optimize task code
4. Use task priorities

### Redis Connection Issues

**Fix**:
1. Check Redis service status
2. Verify connection settings
3. Check network connectivity
4. Review Redis logs

## Advanced Topics

### Custom Task Classes

```python
class CustomTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        # Custom failure handling
        send_alert(f"Task {task_id} failed: {exc}")

@celery_app.task(base=CustomTask)
def my_task():
    pass
```

### Task Rate Limiting

```python
@celery_app.task(rate_limit='10/m')  # 10 tasks per minute
def rate_limited_task():
    pass
```

### Task ETA and Countdown

```python
# Execute after 1 hour
task.apply_async(countdown=3600)

# Execute at specific time
from datetime import datetime, timedelta
eta = datetime.now() + timedelta(hours=1)
task.apply_async(eta=eta)
```

### Canvas Workflows

```python
from celery import chain, group, chord

# Complex workflow
workflow = chain(
    task1.s(),
    group([task2.s(), task3.s()]),
    task4.s()
)
```

## Resources

- [Celery Documentation](https://docs.celeryq.dev/)
- [Redis Documentation](https://redis.io/docs/)
- [Flower Documentation](https://flower.readthedocs.io/)
- [Best Practices Guide](https://docs.celeryq.dev/en/stable/userguide/tasks.html#best-practices)
