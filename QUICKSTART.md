# Quick Start Guide - Nexus Platform

Get started with Nexus Platform in 5 minutes!

## Prerequisites

- Docker and Docker Compose installed
- OR Python 3.11+ and Redis installed locally

## Quick Start with Docker (Recommended)

### 1. Setup

```bash
# Clone the repository
git clone <repository-url>
cd nexus-platform

# Copy environment file
cp .env.example .env
```

### 2. Configure (Optional)

Edit `.env` file if you want to add:
- Email settings (SMTP)
- AI API keys (Anthropic, OpenAI)

```bash
nano .env  # or use your preferred editor
```

### 3. Start Everything

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

### 4. Access Applications

- **Streamlit App**: http://localhost:8501
- **Flower Dashboard**: http://localhost:5555

### 5. Test It Out

1. Open http://localhost:8501
2. Go to **Task Monitor** page
3. Click **Test Health Check** button
4. See the task appear in the queue!

## Quick Start - Local Development

### 1. Install Redis

**macOS**:
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis
```

### 2. Setup Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure

```bash
# Copy environment file
cp .env.example .env

# Edit if needed
nano .env
```

### 4. Start Services

**Terminal 1 - Celery Workers**:
```bash
./celery_worker.sh
```

**Terminal 2 - Streamlit App**:
```bash
streamlit run app.py
```

**Terminal 3 - Flower (Optional)**:
```bash
celery -A config.celery_config flower
```

### 5. Access

- **Streamlit**: http://localhost:8501
- **Flower**: http://localhost:5555

## Testing the System

### Test Email Task

```python
from app.tasks.email_tasks import send_notification

task = send_notification.delay(
    user_email="test@example.com",
    notification_type="task_complete",
    context={'task_name': 'Test', 'details': 'Success'}
)

print(f"Task ID: {task.id}")
```

### Test File Processing

```python
from app.tasks.file_tasks import process_word_document

task = process_word_document.delay(
    file_path="/path/to/document.docx",
    operations=["extract_text", "count_stats"]
)

result = task.get()  # Wait for result
print(result)
```

### Test AI Task

```python
from app.tasks.ai_tasks import claude_completion

task = claude_completion.delay(
    prompt="Write a haiku about programming",
    max_tokens=100
)

result = task.get()
print(result['content'])
```

## Common Commands

### Docker

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop everything
docker-compose down

# Rebuild after code changes
docker-compose build
docker-compose up -d
```

### Celery

```bash
# Check active workers
celery -A config.celery_config inspect active

# Check registered tasks
celery -A config.celery_config inspect registered

# Purge all tasks
celery -A config.celery_config purge
```

### Monitoring

```bash
# Redis CLI
redis-cli

# Check queue lengths
redis-cli LLEN email_queue
redis-cli LLEN ai_queue
```

## Troubleshooting

### Workers not starting?

```bash
# Check Redis
redis-cli ping  # Should return PONG

# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Check logs
docker-compose logs celery_worker
```

### Tasks not processing?

1. Check workers are running
2. Verify queue names match
3. Check Redis connection
4. Look at Flower dashboard

### Port already in use?

Change ports in `docker-compose.yml`:
```yaml
ports:
  - "8502:8501"  # Use 8502 instead of 8501
```

## Next Steps

1. **Configure AI**: Add your Anthropic/OpenAI API keys to `.env`
2. **Setup Email**: Configure SMTP settings for email tasks
3. **Explore Tasks**: Check out the different task types in `app/tasks/`
4. **Read Docs**: See `README.md` and `CELERY_SETUP.md` for details
5. **Customize**: Add your own tasks and workflows

## Support

- **Documentation**: See `README.md`
- **Celery Guide**: See `CELERY_SETUP.md`
- **Issues**: Open an issue on GitHub

Happy coding! 🚀
