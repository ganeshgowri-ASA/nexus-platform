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
