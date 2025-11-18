# 🎯 Nexus Platform

NEXUS: Unified AI-powered productivity platform with 24 integrated modules - Word, Excel, PPT, Projects, Email, Chat, Flowcharts, Analytics, Meetings & more. Built with Streamlit & Claude AI.

## ✨ Features

### 🚀 Background Task Processing
- **Celery + Redis** integration for async job processing
- **Multiple task queues** for different job types
- **Auto-retry logic** for failed tasks
- **Real-time monitoring** dashboard
- **Periodic tasks** with Celery Beat

### 📧 Email Tasks
- Send single or bulk emails
- Template-based notifications
- Scheduled email delivery
- Attachment support
- Auto-retry on failure

### 📁 File Processing Tasks
- **Word Documents**: Extract text, count stats, extract images
- **Excel Files**: Analyze sheets, convert to CSV, calculate totals
- **PowerPoint**: Extract text, analyze structure
- **PDFs**: Extract text, get metadata
- **Images**: Create thumbnails, resize, get info
- **Batch processing** support

### 🤖 AI Tasks
- **Claude AI** integration for advanced AI capabilities
- **OpenAI GPT** support
- Document analysis (summary, key points, sentiment)
- Content generation (emails, blogs, reports)
- Translation services
- Multi-turn chat completions
- Rate limiting and retry logic

### 📊 Report Generation
- Analytics reports (HTML, Excel, PDF, JSON)
- Summary reports with AI-powered executive summaries
- Data export (CSV, Excel, JSON, XML)
- Task performance reports
- Scheduled recurring reports

### 🔍 Task Monitoring Dashboard
- Real-time task status
- Queue length monitoring
- Worker information
- Active task tracking
- Task result inspection

## 🏗️ Architecture

```
nexus-platform/
├── app/
│   ├── tasks/
│   │   ├── email_tasks.py         # Email sending tasks
│   │   ├── file_tasks.py          # File processing tasks
│   │   ├── ai_tasks.py            # AI request tasks
│   │   ├── report_tasks.py        # Report generation tasks
│   │   └── maintenance_tasks.py   # System maintenance tasks
│   ├── utils/
│   │   └── task_stats.py          # Task statistics utilities
│   └── pages/
│       └── task_monitor.py        # Monitoring dashboard
├── config/
│   ├── settings.py                # Application settings
│   └── celery_config.py           # Celery configuration
├── uploads/                       # File uploads directory
├── temp/                          # Temporary files directory
├── logs/                          # Application logs
├── app.py                         # Main Streamlit app
├── requirements.txt               # Python dependencies
├── docker-compose.yml             # Docker orchestration
├── Dockerfile                     # Container definition
└── celery_worker.sh              # Worker startup script
```

## 🚀 Quick Start

### Option 1: Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd nexus-platform
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Access the applications**
   - **Streamlit App**: http://localhost:8501
   - **Flower Dashboard**: http://localhost:5555

### Option 2: Local Development

1. **Install Redis**
   ```bash
   # macOS
   brew install redis
   brew services start redis

   # Ubuntu/Debian
   sudo apt-get install redis-server
   sudo systemctl start redis
   ```

2. **Install Python dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start Celery workers**
   ```bash
   ./celery_worker.sh
   ```

5. **Start Streamlit app** (in a new terminal)
   ```bash
   streamlit run app.py
   ```

6. **Start Flower monitoring** (optional, in a new terminal)
   ```bash
   celery -A config.celery_config flower
   ```

## 🔧 Configuration

### Environment Variables

Edit `.env` file with your configuration:

```env
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# AI Configuration
ANTHROPIC_API_KEY=your-anthropic-api-key
OPENAI_API_KEY=your-openai-api-key
```

### Task Queues

The platform uses separate queues for different task types:

- **default_queue**: General purpose tasks
- **email_queue**: Email sending tasks
- **file_processing_queue**: File processing tasks
- **ai_queue**: AI request tasks (rate-limited)
- **reports_queue**: Report generation tasks

## 📚 Usage Examples

### Email Tasks

```python
from app.tasks.email_tasks import send_email

# Send a simple email
task = send_email.delay(
    to_email="recipient@example.com",
    subject="Hello from Nexus",
    body="This is a test email",
    html_body="<h1>This is a test email</h1>"
)

# Check task status
print(f"Task ID: {task.id}")
print(f"Task Status: {task.status}")
```

### File Processing Tasks

```python
from app.tasks.file_tasks import process_word_document

# Process a Word document
task = process_word_document.delay(
    file_path="/path/to/document.docx",
    operations=["extract_text", "count_stats"]
)

# Get results
result = task.get()
print(result)
```

### AI Tasks

```python
from app.tasks.ai_tasks import claude_completion, analyze_document

# Generate AI completion
task = claude_completion.delay(
    prompt="Explain quantum computing in simple terms",
    max_tokens=500
)

# Analyze a document
task = analyze_document.delay(
    document_text="Your document text here...",
    analysis_type="summary"
)
```

### Report Generation

```python
from app.tasks.report_tasks import generate_analytics_report

# Generate analytics report
task = generate_analytics_report.delay(
    data={
        'records': [
            {'date': '2024-01-01', 'value': 100},
            {'date': '2024-01-02', 'value': 150}
        ]
    },
    report_type='summary',
    format='html'
)
```

## 📊 Monitoring

### Streamlit Dashboard
Access the built-in monitoring dashboard at: http://localhost:8501
- Navigate to "Task Monitor" page
- View real-time task status
- Check queue lengths
- Monitor worker health

### Flower Dashboard
Access Flower at: http://localhost:5555
- View task history
- Monitor worker status
- See task statistics
- Inspect task results

## 🔍 Task Management

### Checking Task Status

```python
from celery.result import AsyncResult
from config.celery_config import celery_app

task_id = "your-task-id"
result = AsyncResult(task_id, app=celery_app)

print(f"Status: {result.status}")
print(f"Ready: {result.ready()}")

if result.ready():
    print(f"Result: {result.result}")
```

### Periodic Tasks

Periodic tasks are configured in `config/celery_config.py`:

- **cleanup-temp-files**: Runs every hour
- **cleanup-old-results**: Runs daily

## 🛠️ Development

### Adding New Tasks

1. Create a new task in the appropriate file (e.g., `app/tasks/custom_tasks.py`)
2. Register the task in `config/celery_config.py`
3. Add the task to the appropriate queue

Example:

```python
from celery import Task
from config.celery_config import celery_app

@celery_app.task(name='app.tasks.custom_tasks.my_task')
def my_task(param1, param2):
    # Your task logic here
    return {'status': 'success'}
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_tasks.py

# Run with coverage
pytest --cov=app tests/
```

## 🐳 Docker Services

The `docker-compose.yml` includes:

- **redis**: Message broker and result backend
- **celery_worker**: Default queue worker
- **celery_worker_email**: Email queue worker
- **celery_worker_files**: File processing worker
- **celery_worker_ai**: AI tasks worker (2 concurrent tasks)
- **celery_worker_reports**: Reports worker
- **celery_beat**: Periodic task scheduler
- **flower**: Monitoring dashboard
- **streamlit**: Web application

### Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild containers
docker-compose build

# Scale workers
docker-compose up -d --scale celery_worker=3
```

## 📈 Performance Tips

1. **Queue Separation**: Use dedicated queues for different task types
2. **Worker Scaling**: Scale workers based on queue load
3. **Rate Limiting**: Configure rate limits for API-heavy tasks
4. **Task Timeouts**: Set appropriate timeouts for long-running tasks
5. **Result Expiry**: Clean up old results regularly

## 🔒 Security

- Store API keys in `.env` file (never commit to git)
- Use environment variables for sensitive configuration
- Implement task authentication for production
- Enable Redis authentication in production
- Use HTTPS for Streamlit in production

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review Celery and Streamlit docs

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Background tasks powered by [Celery](https://docs.celeryq.dev/)
- AI integration with [Anthropic Claude](https://www.anthropic.com/)
- Task monitoring with [Flower](https://flower.readthedocs.io/)

---

**Version**: 1.0.0
**Last Updated**: 2024
