<<<<<<< HEAD
# NEXUS Platform Database Layer

Comprehensive database layer for the NEXUS Platform using SQLAlchemy 2.0 with PostgreSQL.

## 📁 Structure

```
database/
├── __init__.py           # Package initialization, exports all models and utilities
├── connection.py         # Database connection, session management, and CRUD operations
├── models.py            # All 8 core SQLAlchemy models
├── init_db.py           # Database initialization and sample data utilities
├── alembic/             # Database migrations
│   ├── env.py           # Alembic environment configuration
│   ├── script.py.mako   # Migration template
│   ├── README.md        # Alembic usage documentation
│   └── versions/        # Migration scripts
│       └── 001_initial_schema.py
└── README.md            # This file
```

## 🗄️ Core Models

### 1. User Model
Authentication, authorization, and user management
- Role-based access control (admin, manager, user, guest)
- User preferences stored as JSONB
- Email verification and active status tracking

### 2. Document Model
Word, Excel, and PowerPoint document management
- Version control
- Collaborative sharing with permissions
- Soft delete support
- Content stored as JSONB

### 3. Email Model
Internal email system
- Full email addressing (to, cc, bcc)
- Thread support
- Status tracking (draft, sent, received)
- Attachments as JSONB

### 4. Chat Model
Real-time messaging
- Room/channel support
- Message threading (replies)
- Edit and delete tracking
- Attachments as JSONB

### 5. Project Model
Project management
- Status tracking (planning, active, completed)
- Priority levels (low, medium, high, critical)
- Timeline and completion tracking
- Team members and budget management

### 6. Task Model
Task management within projects
- Assignment to users
- Status and priority tracking
- Time tracking (estimated vs actual hours)
- Dependencies and tags
- Due date management

### 7. File Model
File storage and management
- File metadata and hash for deduplication
- Public/private access control
- Download tracking
- MIME type and size tracking

### 8. AI_Interaction Model
AI service usage tracking
- Track prompts and responses
- Model usage and token consumption
- Cost and performance metrics
- Module-specific tracking

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set database URL (optional, defaults to localhost)
export DATABASE_URL="postgresql://nexus_user:nexus_password@localhost:5432/nexus_db"
```

### Initialize Database

```bash
# Create all tables
python database/init_db.py create

# Or use Alembic migrations (recommended for production)
alembic upgrade head

# Create sample data for testing
python database/init_db.py sample

# Verify database setup
python database/init_db.py verify
```

### Basic Usage

```python
from database import get_db, crud, User, Project, Task

# Create a new user
with get_db() as db:
    user = crud.create(
        db,
        User,
        email="user@example.com",
        username="johndoe",
        password_hash="hashed_password",
        full_name="John Doe",
        role="user"
    )

# Get user by ID
with get_db() as db:
    user = crud.get_by_id(db, User, 1)
    print(f"Found user: {user.username}")

# Get multiple users with filters
with get_db() as db:
    active_users = crud.get_multi(
        db,
        User,
        filters={"is_active": True, "role": "admin"}
    )

# Update user
with get_db() as db:
    updated_user = crud.update(
        db,
        User,
        id=1,
        full_name="John Smith"
    )

# Soft delete (if model supports it)
with get_db() as db:
    crud.delete(db, Document, id=5, soft=True)

# Hard delete
with get_db() as db:
    crud.delete(db, File, id=10, soft=False)

# Check if record exists
with get_db() as db:
    exists = crud.exists(db, User, {"email": "user@example.com"})

# Count records
with get_db() as db:
    total_users = crud.count(db, User)
    active_users = crud.count(db, User, {"is_active": True})
```

### Working with Relationships

```python
from database import get_db, User, Project, Task

with get_db() as db:
    # Get user with all related projects
    user = db.query(User).filter(User.id == 1).first()
    for project in user.projects:
        print(f"Project: {project.name}")
        for task in project.tasks:
            print(f"  - Task: {task.title} ({task.status})")

    # Get project with tasks and assignees
    project = db.query(Project).filter(Project.id == 1).first()
    for task in project.tasks:
        assignee = task.assignee
        print(f"Task: {task.title} - Assigned to: {assignee.full_name if assignee else 'Unassigned'}")
```

## 🔄 Database Migrations

### Using Alembic

```bash
# Create a new migration after model changes
alembic revision --autogenerate -m "Add new field to User model"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# View current revision
alembic current
```

See `database/alembic/README.md` for detailed migration documentation.

## 🔧 Configuration

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
  - Default: `postgresql://nexus_user:nexus_password@localhost:5432/nexus_db`
  - Format: `postgresql://user:password@host:port/database`

- `SQL_ECHO`: Enable SQL query logging
  - Default: `false`
  - Set to `true` for debugging

### Database Connection Pooling

The connection pool is configured in `connection.py`:
- Pool size: 10 connections
- Max overflow: 20 connections
- Pre-ping: Enabled (verifies connections before use)

## 📊 Features

### ✅ SQLAlchemy 2.0 Syntax
- Modern type hints with `Mapped[]` annotations
- Declarative base with `DeclarativeBase`
- Improved relationship definitions

### ✅ Production-Ready
- Connection pooling
- Foreign key constraints with proper cascades
- Comprehensive indexes for query optimization
- Soft delete support where appropriate
- Timestamps (created_at, updated_at)

### ✅ PostgreSQL Optimized
- JSONB columns for flexible data storage
- Proper timezone handling (DateTime with timezone=True)
- Efficient indexing strategies

### ✅ Base CRUD Operations
- Generic CRUD class for all models
- Automatic timestamp management
- Soft delete support
- Filtering and pagination

### ✅ Type Safety
- Full type hints throughout
- Type checking compatible
- IDE autocomplete support

## 🧪 Testing

```python
# Example test setup
import pytest
from database import get_db, User, crud

def test_create_user():
    with get_db() as db:
        user = crud.create(
            db,
            User,
            email="test@example.com",
            username="testuser",
            password_hash="hash",
            role="user"
        )
        assert user.id is not None
        assert user.email == "test@example.com"

def test_get_user():
    with get_db() as db:
        user = crud.get_by_id(db, User, 1)
        assert user is not None
```

## 📝 Model Relationships

```
User (1) ─────< (Many) Documents
User (1) ─────< (Many) Emails
User (1) ─────< (Many) Chats
User (1) ─────< (Many) Projects ─────< (Many) Tasks
User (1) ─────< (Many) Files
User (1) ─────< (Many) AI_Interactions
User (1) ─────< (Many) Tasks (as assignee)

Chat (1) ─────< (Many) Chats (replies)
```

## 🔒 Security Considerations

1. **Password Hashing**: Always hash passwords before storing
   ```python
   import bcrypt
   password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
   ```

2. **SQL Injection**: Use SQLAlchemy's parameter binding (done automatically)

3. **Soft Deletes**: Documents support soft delete to prevent accidental data loss

4. **Access Control**: Use role-based permissions from User model

## 📚 Additional Resources

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## 🛠️ Maintenance

### Reset Database (Development Only)

```bash
# WARNING: This deletes all data!
python database/init_db.py reset
```

### Backup Database

```bash
# Using pg_dump
pg_dump -U nexus_user nexus_db > backup.sql

# Restore
psql -U nexus_user nexus_db < backup.sql
```

## 🤝 Contributing

When adding new models or modifying existing ones:

1. Update `models.py` with your changes
2. Create a new migration: `alembic revision --autogenerate -m "Description"`
3. Review the generated migration in `database/alembic/versions/`
4. Test the migration: `alembic upgrade head`
5. Update this README if adding new models
6. Add sample data to `init_db.py` if appropriate

## 📄 License

Part of the NEXUS Platform project.
=======
# NEXUS Platform Database

This directory contains all database-related code for the NEXUS platform.

## Structure

```
database/
├── __init__.py         # Database initialization and session management
├── models/             # SQLAlchemy models (to be created)
├── migrations/         # Alembic migrations (to be created)
└── README.md          # This file
```

## Database Configuration

Database settings are managed through the `app/config.py` file using Pydantic settings.

### Default Configuration

- **Engine**: SQLite (development)
- **URL**: `sqlite:///nexus.db`
- **Pool Size**: 5
- **Max Overflow**: 10

### Production Configuration

For production, update the `.env` file:

```env
DATABASE__URL=postgresql://user:password@localhost:5432/nexus
DATABASE__POOL_SIZE=20
DATABASE__MAX_OVERFLOW=40
```

## Usage

### Initialize Database

```python
from database import init_db

# Create all tables
init_db()
```

### Get Database Session

```python
from database import get_db

# Using context manager
with next(get_db()) as db:
    # Perform database operations
    pass

# Or in FastAPI/Streamlit
db = next(get_db())
try:
    # Perform operations
    pass
finally:
    db.close()
```

## Future Enhancements

- [ ] Add SQLAlchemy models for all modules
- [ ] Implement Alembic for database migrations
- [ ] Add database backup utilities
- [ ] Implement connection pooling optimization
- [ ] Add database health checks
- [ ] Create database seeding scripts

## Models to be Created

1. **Users** - User authentication and profiles
2. **Documents** - Word processor documents
3. **Spreadsheets** - Excel sheets
4. **Presentations** - PowerPoint files
5. **Projects** - Project management data
6. **Tasks** - Task tracking
7. **Messages** - Chat messages
8. **Emails** - Email storage
9. **Files** - File metadata
10. **Analytics** - Analytics data

## Security

- All passwords are hashed using bcrypt
- Database credentials stored in environment variables
- SQL injection prevention through parameterized queries
- Connection encryption in production
>>>>>>> origin/claude/nexus-platform-setup-01GgK8vgMUpRwMXvUmBp8eNW
