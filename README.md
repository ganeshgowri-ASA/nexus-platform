# NEXUS Platform

Unified AI-powered productivity platform with integrated modules for enterprise task automation and management.

## 🎯 Current Modules

### ⏰ Scheduler Module

Advanced task scheduling system with comprehensive job management and monitoring.

**Features:**
- ✅ Cron scheduling with visual builder
- ✅ Interval and date-based scheduling
- ✅ Calendar-based scheduling
- ✅ Timezone support and conversion
- ✅ Job execution history and retry logic
- ✅ Multi-channel notifications (Email, Telegram, Webhook)
- ✅ Real-time dashboard and monitoring
- ✅ Task queue visualization
- ✅ Production-ready with Docker

**Tech Stack:**
- FastAPI for REST API
- PostgreSQL for data persistence
- Redis for caching and task queue
- Celery Beat for distributed task scheduling
- APScheduler for advanced scheduling
- Streamlit for web UI

**Quick Start:**
```bash
# Start the scheduler module
cd nexus-platform
./scripts/start.sh

# Access the application
# API: http://localhost:8000
# UI:  http://localhost:8501
```

**Documentation:**
- [Scheduler README](modules/scheduler/README.md)
- [API Documentation](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd nexus-platform

# Copy environment configuration
cp .env.example .env

# Start services
make up

# Or use the start script
./scripts/start.sh
```

## 📖 Module Documentation

- **Scheduler Module**: [modules/scheduler/README.md](modules/scheduler/README.md)

## 🛠️ Development

```bash
# Install dependencies
make install

# Run tests
make test

# Format code
make format

# View logs
make logs
```

## 📊 Architecture

```
NEXUS Platform
├── modules/
│   └── scheduler/          # Task scheduling module
│       ├── api/           # FastAPI endpoints
│       ├── models/        # Database models
│       ├── services/      # Business logic
│       ├── tasks/         # Celery tasks
│       ├── ui/            # Streamlit interface
│       └── utils/         # Utilities
├── docs/                  # Documentation
├── scripts/               # Deployment scripts
└── docker-compose.yml     # Service orchestration
```

## 🔧 Configuration

See `.env.example` for all available configuration options.

## 🧪 Testing

```bash
# Run all tests
make test

# Run specific module tests
pytest modules/scheduler/tests/ -v
```

## 📝 License

[Your License Here]

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines first.

## 📞 Support

For issues and questions, please open a GitHub issue.
