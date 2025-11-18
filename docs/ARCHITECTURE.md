# NEXUS DMS Architecture Overview

Comprehensive architecture documentation for the NEXUS Document Management System.

## Table of Contents

- [System Overview](#system-overview)
- [Architecture Patterns](#architecture-patterns)
- [Component Architecture](#component-architecture)
- [Data Models](#data-models)
- [Storage Architecture](#storage-architecture)
- [Security Architecture](#security-architecture)
- [Scalability](#scalability)
- [Technology Stack](#technology-stack)

## System Overview

NEXUS DMS is a modern, enterprise-grade document management system built with a microservices-oriented architecture. The system is designed to be scalable, secure, and extensible.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Load Balancer                         │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼────────┐       ┌───────▼────────┐
│   Web Client   │       │   Mobile App   │
│   (Streamlit)  │       │    (Future)    │
└───────┬────────┘       └───────┬────────┘
        │                        │
        └────────────┬───────────┘
                     │
        ┌────────────▼────────────┐
        │    API Gateway (Nginx)   │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │   FastAPI Backend API    │
        │   (Python 3.11+)         │
        └──┬──────┬──────┬──────┬─┘
           │      │      │      │
    ┌──────▼──┐ ┌▼─────▼┐ ┌───▼────┐ ┌────▼─────┐
    │Document │ │Search │ │Workflow│ │Permission│
    │Service  │ │Service│ │Engine  │ │Service   │
    └─────┬───┘ └───┬───┘ └───┬────┘ └────┬─────┘
          │         │         │            │
    ┌─────▼─────────▼─────────▼────────────▼─────┐
    │           PostgreSQL Database               │
    └─────────────────┬───────────────────────────┘
                      │
    ┌─────────────────▼───────────────────────────┐
    │              Storage Layer                   │
    │  (Local / S3 / Azure Blob / Google Cloud)   │
    └─────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────┐
    │           Background Services                │
    │                                              │
    │  ┌──────────┐  ┌───────────┐  ┌──────────┐ │
    │  │  Celery  │  │  Redis    │  │  Email   │ │
    │  │  Workers │  │  Cache    │  │  Queue   │ │
    │  └──────────┘  └───────────┘  └──────────┘ │
    └─────────────────────────────────────────────┘
```

### Key Components

1. **Frontend Layer**: Streamlit-based web interface
2. **API Layer**: FastAPI REST API with OpenAPI documentation
3. **Service Layer**: Business logic and domain services
4. **Data Layer**: PostgreSQL with SQLAlchemy ORM
5. **Storage Layer**: Multi-backend file storage
6. **Cache Layer**: Redis for caching and session management
7. **Task Queue**: Celery for asynchronous processing

## Architecture Patterns

### 1. Layered Architecture

The application follows a clean layered architecture:

```
┌─────────────────────────────────────┐
│       Presentation Layer            │
│   (API Endpoints, Frontend)         │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│        Service Layer                │
│   (Business Logic, Services)        │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│       Repository Layer              │
│   (Data Access, ORM)                │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│        Data Layer                   │
│   (Database, Storage)               │
└─────────────────────────────────────┘
```

### 2. Service-Oriented Architecture

Core services are organized around business capabilities:

- **Document Service**: Document CRUD operations
- **Storage Service**: File storage and retrieval
- **Permission Service**: Access control management
- **Version Control Service**: Document versioning
- **Search Service**: Full-text and faceted search
- **Workflow Service**: Document workflows and approvals
- **Audit Service**: Activity logging and compliance
- **AI Service**: Document analysis and classification

### 3. Domain-Driven Design

The codebase is organized by domain concepts:

```
backend/
├── models/          # Domain models (entities)
├── services/        # Domain services
├── repositories/    # Data access repositories
├── schemas/         # API schemas (DTOs)
└── api/            # API endpoints
```

## Component Architecture

### Backend API (FastAPI)

```
backend/
├── main.py                    # Application entry point
├── core/
│   ├── config.py             # Configuration management
│   ├── security.py           # Authentication & authorization
│   ├── logging.py            # Logging configuration
│   ├── exceptions.py         # Custom exceptions
│   └── dependencies.py       # Dependency injection
├── api/
│   └── v1/
│       ├── documents.py      # Document endpoints
│       ├── folders.py        # Folder endpoints
│       ├── search.py         # Search endpoints
│       ├── permissions.py    # Permission endpoints
│       └── router.py         # Route aggregation
├── models/
│   ├── base.py              # Base model
│   ├── user.py              # User models
│   └── document.py          # Document models
├── services/
│   ├── document.py          # Document service
│   ├── storage.py           # Storage service
│   └── permission.py        # Permission service
├── schemas/
│   ├── document.py          # Document schemas
│   └── user.py              # User schemas
└── database.py              # Database configuration
```

### Document Module

```
modules/documents/
├── __init__.py
├── storage.py               # Storage backends
├── permissions.py           # Permission system
├── versioning.py            # Version control
├── search.py                # Search functionality
├── workflow.py              # Workflow engine
├── classification.py        # AI classification
├── metadata.py              # Metadata extraction
├── preview.py               # Document preview
├── conversion.py            # Format conversion
└── audit.py                 # Audit logging
```

## Data Models

### Core Entities

#### Document

```python
Document
├── id: int (PK)
├── title: str
├── description: str
├── file_name: str
├── file_path: str
├── file_size: int
├── mime_type: str
├── file_hash: str
├── status: DocumentStatus
├── owner_id: int (FK -> User)
├── folder_id: int (FK -> Folder)
├── current_version: int
├── is_locked: bool
├── is_public: bool
├── created_at: datetime
└── updated_at: datetime

Relationships:
├── owner: User
├── folder: Folder
├── versions: List[DocumentVersion]
├── permissions: List[DocumentPermission]
├── tags: List[DocumentTag]
├── metadata: List[DocumentMetadata]
└── audit_logs: List[DocumentAuditLog]
```

#### Folder

```python
Folder
├── id: int (PK)
├── name: str
├── description: str
├── path: str
├── parent_id: int (FK -> Folder)
├── owner_id: int (FK -> User)
├── is_public: bool
└── created_at: datetime

Relationships:
├── parent: Folder
├── subfolders: List[Folder]
├── documents: List[Document]
└── permissions: List[FolderPermission]
```

#### DocumentVersion

```python
DocumentVersion
├── id: int (PK)
├── document_id: int (FK -> Document)
├── version_number: int
├── file_path: str
├── file_size: int
├── file_hash: str
├── change_summary: str
├── created_by_id: int (FK -> User)
└── created_at: datetime
```

### Entity Relationships

```
User ──┬──< owns >──── Document
       │
       ├──< owns >──── Folder
       │
       ├──< has permission >──── DocumentPermission
       │
       └──< created >──── DocumentVersion

Document ──┬──< contains >──── DocumentVersion
           │
           ├──< has >──── DocumentMetadata
           │
           ├──< tagged with >──── DocumentTag
           │
           ├──< has >──── DocumentPermission
           │
           └──< logged in >──── DocumentAuditLog

Folder ──┬──< contains >──── Document
         │
         └──< contains >──── Folder (subfolder)
```

## Storage Architecture

### Multi-Backend Storage

The system supports multiple storage backends:

```
┌─────────────────────────────────────────────┐
│         Storage Manager                      │
│  (Unified Interface)                        │
└──────────────┬──────────────────────────────┘
               │
     ┌─────────┴─────────┐
     │                   │
┌────▼─────┐      ┌─────▼──────┐
│  Local   │      │   Cloud    │
│ Storage  │      │  Storage   │
└────┬─────┘      └─────┬──────┘
     │                  │
     │           ┌──────┴──────┬──────────┐
     │           │             │          │
 ┌───▼────┐  ┌──▼──┐     ┌────▼───┐  ┌──▼───┐
 │  Disk  │  │ S3  │     │ Azure  │  │ GCS  │
 └────────┘  └─────┘     │  Blob  │  └──────┘
                         └────────┘
```

### Storage Features

1. **Deduplication**: Content-based deduplication using SHA-256 hashing
2. **Compression**: Automatic compression for text documents
3. **Chunking**: Large file upload with resumable chunks
4. **Encryption**: At-rest and in-transit encryption
5. **CDN Integration**: Content delivery network support
6. **Backup**: Automated backup to secondary storage

### File Organization

```
storage/
├── documents/
│   ├── 2025/
│   │   ├── 01/
│   │   │   ├── doc_abc123.pdf
│   │   │   └── doc_def456.docx
│   │   └── 02/
│   └── 2024/
├── versions/
│   ├── doc_1/
│   │   ├── v1
│   │   ├── v2
│   │   └── v3
│   └── doc_2/
├── thumbnails/
│   ├── small/
│   └── large/
└── temp/
    └── uploads/
```

## Security Architecture

### Authentication & Authorization

```
┌──────────────────────────────────────────┐
│            User Request                   │
└──────────────┬───────────────────────────┘
               │
┌──────────────▼───────────────────────────┐
│      Authentication Middleware            │
│  (JWT Token Validation)                  │
└──────────────┬───────────────────────────┘
               │
┌──────────────▼───────────────────────────┐
│      Authorization Layer                  │
│  (Permission Checking)                   │
└──────────────┬───────────────────────────┘
               │
┌──────────────▼───────────────────────────┐
│         Resource Access                   │
└──────────────────────────────────────────┘
```

### Security Layers

1. **Network Security**:
   - HTTPS/TLS encryption
   - API rate limiting
   - DDoS protection
   - Firewall rules

2. **Application Security**:
   - JWT-based authentication
   - Role-based access control (RBAC)
   - Granular permissions
   - Session management
   - CSRF protection
   - XSS prevention
   - SQL injection prevention

3. **Data Security**:
   - Encryption at rest
   - Encryption in transit
   - Secure password hashing (bcrypt)
   - Data anonymization
   - Audit logging

4. **Compliance**:
   - GDPR compliance
   - SOC 2 compliance
   - Document retention policies
   - Legal hold support

### Permission Model

```
Access Levels (Hierarchical):
├── NONE: No access
├── VIEW: Read-only access
├── COMMENT: View + commenting
├── EDIT: View + comment + modify
└── ADMIN: Full control

Permission Sources:
├── Ownership: Document owner has ADMIN
├── Direct Permission: Explicitly granted
├── Folder Permission: Inherited from folder
└── Public Access: VIEW for public documents
```

## Scalability

### Horizontal Scaling

```
┌───────────────────────────────────────────────┐
│           Load Balancer (HAProxy)              │
└─────┬──────────┬──────────┬──────────┬────────┘
      │          │          │          │
┌─────▼────┐ ┌──▼─────┐ ┌──▼─────┐ ┌──▼─────┐
│  API     │ │  API   │ │  API   │ │  API   │
│  Node 1  │ │ Node 2 │ │ Node 3 │ │ Node N │
└─────┬────┘ └────┬───┘ └────┬───┘ └────┬───┘
      │           │           │           │
      └───────────┴───────────┴───────────┘
                  │
    ┌─────────────▼─────────────┐
    │   PostgreSQL (Primary)     │
    │   + Read Replicas         │
    └───────────────────────────┘
```

### Caching Strategy

```
Request Flow:
1. Check Redis cache
2. If hit: Return cached data
3. If miss:
   a. Query database
   b. Store in cache
   c. Return data

Cache Layers:
├── L1: In-memory (application)
├── L2: Redis (distributed)
└── L3: CDN (static assets)
```

### Asynchronous Processing

```
┌─────────────────────────────────────┐
│      Celery Task Queue              │
└──────┬──────────────────────────────┘
       │
  ┌────┴────┬─────────┬──────────┐
  │         │         │          │
┌─▼──┐  ┌──▼─┐  ┌────▼──┐  ┌───▼───┐
│OCR │  │PDF │  │Email │  │Backup │
│Task│  │Gen │  │Task  │  │Task   │
└────┘  └────┘  └──────┘  └───────┘
```

Background tasks:
- Document indexing
- OCR processing
- Thumbnail generation
- Email notifications
- Scheduled backups
- Report generation

## Technology Stack

### Backend

- **Framework**: FastAPI 0.109+
- **Language**: Python 3.11+
- **ORM**: SQLAlchemy 2.0+
- **Database**: PostgreSQL 16+
- **Cache**: Redis 7+
- **Task Queue**: Celery 5+
- **Search**: PostgreSQL FTS / Elasticsearch 8+
- **AI**: Anthropic Claude API

### Frontend

- **Framework**: Streamlit 1.30+
- **Language**: Python 3.11+
- **Styling**: Custom CSS

### Infrastructure

- **Web Server**: Nginx
- **ASGI Server**: Uvicorn / Gunicorn
- **Process Manager**: Supervisor
- **Container**: Docker
- **Orchestration**: Docker Compose / Kubernetes
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)

### Cloud Services

- **Storage**: AWS S3 / Azure Blob / Google Cloud Storage
- **CDN**: CloudFront / Azure CDN
- **Email**: SendGrid / AWS SES
- **Monitoring**: DataDog / New Relic

## Performance Considerations

### Database Optimization

1. **Indexing**:
   - Composite indexes on frequently queried columns
   - Full-text search indexes
   - Foreign key indexes

2. **Query Optimization**:
   - Eager loading with `selectinload()`
   - Query result caching
   - Connection pooling

3. **Partitioning**:
   - Table partitioning by date
   - Archival of old data

### API Performance

1. **Response Optimization**:
   - Response compression (gzip)
   - Pagination for list endpoints
   - Partial responses (field filtering)

2. **Caching**:
   - HTTP caching headers
   - Redis caching
   - CDN caching

3. **Rate Limiting**:
   - Per-user rate limits
   - Per-endpoint rate limits
   - Burst allowance

## Monitoring and Observability

### Metrics

- Request rate and latency
- Error rates
- Database query performance
- Storage usage
- Queue length
- Worker status

### Logging

- Structured JSON logging
- Centralized log aggregation
- Log levels (DEBUG, INFO, WARNING, ERROR)
- Request/response logging
- Audit trail logging

### Alerting

- Error rate thresholds
- Performance degradation
- System resource usage
- Failed background jobs
- Security events

## Disaster Recovery

### Backup Strategy

1. **Database**: Daily full backup + hourly incremental
2. **Files**: Continuous replication to backup storage
3. **Configuration**: Version controlled in Git
4. **Retention**: 30 days online, 1 year archive

### Recovery Procedures

1. **Database Restore**: Point-in-time recovery
2. **File Restore**: Object versioning / snapshots
3. **Application Deploy**: Automated deployment from CI/CD
4. **Testing**: Regular DR drills

## Future Enhancements

- Microservices architecture migration
- Real-time collaboration features
- Advanced AI capabilities
- Mobile applications
- Blockchain integration for audit trail
- GraphQL API
- Kubernetes deployment
- Multi-tenant support

## Contributing

For architecture discussions and proposals:

- Email: architecture@nexus-platform.com
- GitHub: https://github.com/your-org/nexus-platform
- Wiki: https://wiki.nexus-platform.com
