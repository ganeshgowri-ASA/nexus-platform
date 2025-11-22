# NEXUS Contracts Management Module

## Overview

The Contracts Management Module is a comprehensive, production-ready system for managing the complete contract lifecycle within the NEXUS platform. It provides end-to-end functionality from contract creation through execution, tracking, and compliance.

## Features

### 1. Contract Lifecycle Management
- **Draft Creation**: Create contracts from templates or from scratch
- **Negotiation**: Version tracking, redlines, comments, and collaborative editing
- **Approval Workflows**: Multi-level approval chains with conditional routing
- **Execution**: E-signature integration (DocuSign, Adobe Sign, HelloSign)
- **Tracking**: Real-time status tracking and monitoring
- **Renewal**: Automatic renewal reminders and processing
- **Termination**: Structured termination with reason tracking
- **Archival**: Complete archive with audit trail

### 2. Template Library
Pre-built templates for common contract types:
- **NDA**: Non-Disclosure Agreement
- **MSA**: Master Service Agreement
- **SOW**: Statement of Work
- **Employment**: Employment contracts
- **Vendor**: Vendor agreements
- **Sales**: Sales contracts
- **Purchase**: Purchase orders
- **Lease**: Lease agreements
- **Service**: Service agreements

### 3. Clause Management
- **Standard Clause Library**: Pre-approved clauses by category
- **Custom Clause Builder**: Create and manage custom clauses
- **Clause Recommendations**: AI-powered clause suggestions
- **Risk Assessment**: Automatic risk level identification for clauses

### 4. Negotiation & Collaboration
- **Version Control**: Complete version history with visual diff
- **Redlining**: Track all changes with accept/reject workflow
- **Comments**: Threaded comments on contracts and clauses
- **Stakeholder Collaboration**: Multi-party collaboration support

### 5. Approval Workflows
- **Multi-Level Approval**: Configurable approval chains
- **Conditional Routing**: Route based on value, type, risk level
- **Escalation**: Automatic escalation on timeout
- **Notifications**: Email/SMS notifications to approvers

### 6. E-Signature Integration
- **DocuSign**: Full DocuSign integration
- **Adobe Sign**: Adobe Sign support
- **HelloSign**: HelloSign integration
- **Witness Management**: Witness signatures
- **Notarization**: Notarization support
- **Audit Trail**: Complete signature audit log

### 7. Obligation Management
- **Auto-Extraction**: AI-powered obligation extraction from contracts
- **Deadline Tracking**: Track all contractual deadlines
- **Responsibility Assignment**: Assign obligations to parties
- **Alerts**: Configurable alerts for upcoming/overdue obligations
- **Dependencies**: Track obligation dependencies

### 8. Milestone Tracking
- **Milestone Definition**: Define project milestones
- **Progress Tracking**: Track milestone completion
- **Payment Triggers**: Link milestones to payments
- **Deliverable Verification**: Verify deliverable completion

### 9. Compliance & Risk
- **Regulatory Compliance**: GDPR, CCPA, and other regulations
- **Legal Requirement Validation**: Ensure all requirements met
- **Risk Assessment**: AI-powered contract risk scoring
- **Risk Identification**: Identify high-risk clauses
- **Compliance Reporting**: Generate compliance reports

### 10. AI Assistant
- **Contract Summarization**: Generate executive summaries
- **Risk Identification**: Identify potential risks
- **Clause Recommendation**: Suggest appropriate clauses
- **Anomaly Detection**: Detect unusual or problematic terms
- **Key Term Extraction**: Extract important contract terms

### 11. Search & Analytics
- **Full-Text Search**: Search across all contracts and clauses
- **Semantic Search**: AI-powered semantic search
- **Metadata Filters**: Filter by type, status, party, etc.
- **Cycle Time Analytics**: Track contract processing time
- **Bottleneck Detection**: Identify workflow bottlenecks
- **Value Analysis**: Analyze contract value distribution
- **Risk Metrics**: Risk distribution and trends

### 12. Integration Hub
- **CRM Sync**: Salesforce, HubSpot, etc.
- **Accounting**: QuickBooks, Xero, etc.
- **Project Management**: Jira, Asana, etc.
- **Document Management**: SharePoint, Google Drive, etc.

### 13. Audit Trail
- **Complete Audit Log**: Tamper-proof audit trail
- **Change History**: Track all modifications
- **Access Logs**: Log all access events
- **Compliance Reporting**: Generate audit reports

### 14. Alerts & Notifications
- **Expiration Alerts**: Contract expiration warnings
- **Renewal Reminders**: Automatic renewal notifications
- **Obligation Due Dates**: Deadline reminders
- **Milestone Notifications**: Milestone completion alerts

### 15. Reporting
- **Contract Register**: Complete contract inventory
- **Obligation Reports**: Track all obligations
- **Value Reports**: Contract value analysis
- **Risk Reports**: Risk assessment summaries
- **Compliance Reports**: Compliance status

### 16. Export/Import
- **PDF Export**: High-quality PDF generation
- **Word Export**: Editable Word documents
- **HTML Export**: Formatted HTML output
- **Bulk Export**: Export multiple contracts
- **Template Export**: Export templates

## Architecture

### Technology Stack
- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Caching**: Redis
- **Background Tasks**: Celery
- **AI/LLM**: Anthropic Claude, OpenAI GPT-4
- **Frontend**: Streamlit interactive UI
- **Testing**: pytest with 80%+ coverage
- **Documentation**: OpenAPI/Swagger

### Module Structure
```
modules/contracts/
├── __init__.py                 # Module initialization
├── contract_types.py           # Core data types and models
├── models.py                   # Database models (SQLAlchemy)
├── lifecycle.py                # Contract lifecycle management
├── templates.py                # Template library and management
├── clauses.py                  # Clause library and builder
├── negotiation.py              # Version tracking and collaboration
├── approval.py                 # Approval workflow engine
├── execution.py                # E-signature integration
├── obligations.py              # Obligation tracking
├── milestones.py               # Milestone management
├── compliance.py               # Compliance and risk engine
├── metadata.py                 # Metadata and categorization
├── search.py                   # Search functionality
├── analytics.py                # Analytics engine
├── ai_assistant.py             # AI-powered features
├── integration.py              # External integrations
├── audit.py                    # Audit trail
├── alerts.py                   # Alert and notification system
├── reports.py                  # Report generation
├── export.py                   # Export functionality
├── api.py                      # FastAPI endpoints
└── streamlit_ui.py             # Streamlit UI
```

## Installation

### Prerequisites
- Python 3.11 or higher
- PostgreSQL 14+
- Redis 6+

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/your-org/nexus-platform.git
cd nexus-platform
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Initialize database**
```bash
python -c "from shared.database import init_db; init_db()"
```

6. **Run migrations** (if using Alembic)
```bash
alembic upgrade head
```

## Usage

### Running the API Server

```bash
# Development
uvicorn main:app --reload

# Production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

API will be available at: http://localhost:8000
API Documentation: http://localhost:8000/api/docs

### Running the Streamlit UI

```bash
streamlit run modules/contracts/streamlit_ui.py
```

UI will be available at: http://localhost:8501

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=modules --cov-report=html

# Run specific test file
pytest tests/contracts/test_contract_types.py

# Run with markers
pytest -m unit
pytest -m integration
```

## API Examples

### Create a Contract

```python
import requests

response = requests.post(
    "http://localhost:8000/api/contracts/",
    params={"user_id": "user-uuid"},
    json={
        "title": "Software Development Agreement",
        "contract_type": "service",
        "parties": [
            {
                "name": "Acme Corp",
                "role": "client",
                "email": "contact@acme.com"
            },
            {
                "name": "DevShop Inc",
                "role": "vendor",
                "email": "hello@devshop.com"
            }
        ],
        "description": "Development of mobile application"
    }
)

contract = response.json()
print(f"Created contract: {contract['id']}")
```

### Start Negotiation

```python
response = requests.post(
    f"http://localhost:8000/api/contracts/{contract_id}/negotiate",
    params={"user_id": "user-uuid"}
)
```

### Submit for Approval

```python
response = requests.post(
    f"http://localhost:8000/api/contracts/{contract_id}/submit-approval",
    params={"user_id": "user-uuid"}
)
```

## Configuration

See `.env.example` for all configuration options. Key settings:

- **Database**: Configure PostgreSQL connection
- **Redis**: Set Redis URL for caching
- **AI Keys**: Add Anthropic/OpenAI API keys
- **E-Signature**: Configure DocuSign/Adobe Sign credentials
- **Email**: Set SMTP settings for notifications

## Security

- **Authentication**: JWT-based authentication
- **Authorization**: Role-based access control (RBAC)
- **Encryption**: AES-256 encryption for sensitive data
- **Audit Trail**: Complete tamper-proof audit log
- **Data Privacy**: GDPR and CCPA compliant

## Performance

- **Caching**: Redis caching for frequently accessed data
- **Pagination**: All list endpoints support pagination
- **Async Operations**: Background tasks via Celery
- **Database Indexing**: Optimized database indexes
- **Connection Pooling**: Database connection pooling

## Monitoring

- **Health Checks**: `/health` endpoint
- **Metrics**: Prometheus metrics (optional)
- **Logging**: Structured JSON logging
- **Error Tracking**: Sentry integration (optional)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests (maintain 80%+ coverage)
5. Submit a pull request

## License

Copyright (c) 2024 NEXUS Platform. All rights reserved.

## Support

For issues and questions:
- GitHub Issues: https://github.com/your-org/nexus-platform/issues
- Email: support@nexus.com
- Documentation: https://docs.nexus.com

## Roadmap

### Upcoming Features
- [ ] Blockchain integration for immutable contract records
- [ ] Mobile app for contract approval
- [ ] Advanced OCR for contract digitization
- [ ] Multi-language support (10+ languages)
- [ ] Contract analytics dashboard enhancements
- [ ] Integration with more e-signature providers
- [ ] Advanced AI features (contract drafting, negotiation assistance)
- [ ] Contract comparison and analysis tools
