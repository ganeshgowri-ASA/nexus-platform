# NEXUS Database Manager & Query Builder

A comprehensive, professional-grade database management tool built for the NEXUS platform. Rivals phpMyAdmin, DBeaver, and TablePlus with a modern, AI-powered interface.

## 🌟 Features

### 1. Multi-Database Support
- **PostgreSQL** - Full support with connection pooling
- **MySQL/MariaDB** - Complete compatibility
- **MongoDB** - NoSQL database support
- **SQLite** - Embedded database support
- **SQL Server** - Enterprise database support

### 2. Visual Query Builder
- **Drag & Drop Interface** - Build queries visually without writing SQL
- **JOIN Support** - Inner, Left, Right, Full Outer, Cross joins
- **Filters & Conditions** - Complex WHERE clauses with AND/OR logic
- **Aggregations** - COUNT, SUM, AVG, MIN, MAX, GROUP BY
- **Subqueries** - Nested query support
- **Query Templates** - Save and reuse common queries
- **Query History** - Track all executed queries with performance metrics

### 3. Schema Designer
- **Visual ER Diagrams** - Interactive entity-relationship diagrams
- **Table Designer** - Create and modify tables visually
- **Relationships** - Define foreign keys and relationships
- **Indexes** - Create and manage indexes for optimization
- **Constraints** - Primary keys, unique, check, not null
- **Schema Versioning** - Track schema changes over time

### 4. Data Explorer
- **Browse Tables** - View and navigate table data with pagination
- **Filter & Sort** - Advanced filtering and sorting capabilities
- **CRUD Operations** - Create, Read, Update, Delete records
- **Bulk Operations** - Insert, update, delete multiple records
- **Search** - Full-text search across tables
- **Export Data** - CSV, JSON, Excel, SQL, XML formats

### 5. Migration System
- **Version Control** - Track database schema versions
- **Up/Down Migrations** - Apply and rollback changes
- **Migration History** - Complete audit trail
- **Auto-generation** - Generate migrations from schema differences
- **Checksum Verification** - Ensure migration integrity
- **Schema Snapshots** - Save point-in-time schema states

### 6. Backup & Restore
- **Automated Backups** - Schedule regular backups
- **Full Backups** - Complete database dumps
- **Incremental Backups** - Only changed data
- **Schema-Only Backups** - Structure without data
- **Point-in-Time Recovery** - Restore to specific timestamp
- **Compression** - GZIP, BZIP2 support
- **Backup Verification** - Automatic integrity checks

### 7. Performance Monitoring
- **Query Analysis** - Identify slow queries and bottlenecks
- **Execution Plans** - EXPLAIN query plans
- **Index Recommendations** - AI-powered index suggestions
- **Slow Query Log** - Track queries above threshold
- **Performance Metrics** - Response times, throughput, etc.
- **Connection Pool Stats** - Monitor active connections
- **Query Profiling** - Detailed performance analysis

### 8. User Administration
- **User Management** - Create, update, delete users
- **Role-Based Access** - Define custom roles
- **Permissions** - Granular permission control
- **Access Reports** - Audit who has access to what
- **Password Management** - Secure password hashing
- **Session Tracking** - Monitor user activity

### 9. Streamlit UI
- **Modern Interface** - Clean, intuitive design
- **Responsive Layout** - Works on all screen sizes
- **Dark/Light Mode** - Theme customization
- **Real-time Updates** - Live data refresh
- **Export/Download** - Download results and reports
- **Interactive Charts** - Visualize data and metrics

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/your-org/nexus-platform.git
cd nexus-platform

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run modules/database/streamlit_ui.py
```

## 📖 Quick Start

### 1. Create a Database Connection

```python
from modules.database import DatabaseManager, ConnectionConfig, DatabaseType

# Create database manager
manager = DatabaseManager()

# Add PostgreSQL connection
config = ConnectionConfig(
    name="my_postgres",
    db_type=DatabaseType.POSTGRESQL,
    host="localhost",
    port=5432,
    database="mydb",
    username="user",
    password="password"
)

manager.add_connection(config)
```

### 2. Build a Query

```python
from modules.database import QueryBuilder, Query

# Create query builder
builder = QueryBuilder()

# Build query
query = (Query()
    .select("users.name", "orders.total")
    .from_("users")
    .join("orders", "users.id", "orders.user_id")
    .where("orders.total", ">", 100)
    .order("orders.total", "DESC")
    .limit(10)
)

# Generate SQL
sql, params = query.to_sql()
print(sql)
```

### 3. Explore Data

```python
from modules.database import DataExplorer

# Get connection
conn = manager.get_connection("my_postgres")

# Create explorer
explorer = DataExplorer(conn)

# Browse table
results = explorer.browse_table("users", page=1, page_size=50)

# Export data
csv_data = explorer.export_data("users", ExportFormat.CSV)
```

### 4. Design Schema

```python
from modules.database import SchemaDesigner, TableBuilder, DataType

# Create schema designer
designer = SchemaDesigner()

# Create schema
schema = designer.create_schema("my_app", "Application database")

# Build table
table = (TableBuilder("users")
    .add_column("id", DataType.INTEGER, auto_increment=True)
    .add_column("email", DataType.VARCHAR, length=255, nullable=False)
    .add_column("created_at", DataType.TIMESTAMP)
    .primary_key("id")
    .add_unique("email")
    .add_index(["email"], unique=True)
    .build()
)

# Add to schema
schema.add_table(table)

# Generate DDL
ddl = schema.generate_ddl()
print(ddl)
```

### 5. Create Migrations

```python
from modules.database import MigrationManager

# Create migration manager
migration_mgr = MigrationManager(conn)

# Add migration
migration = migration_mgr.add_migration(
    version="001",
    name="create_users_table",
    up_sql="""
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """,
    down_sql="DROP TABLE users;"
)

# Apply migration
migration_mgr.apply_migration("001")

# Check status
status = migration_mgr.get_migration_status()
```

### 6. Backup Database

```python
from modules.database import BackupManager, BackupConfig, BackupType

# Create backup manager
backup_config = BackupConfig(backup_dir="./backups")
backup_mgr = BackupManager(conn, backup_config)

# Create backup
backup = backup_mgr.create_backup(
    name="daily_backup",
    backup_type=BackupType.FULL
)

# List backups
backups = backup_mgr.list_backups()

# Restore backup
backup_mgr.restore_backup(backup.id)
```

### 7. Monitor Performance

```python
from modules.database import PerformanceMonitor

# Create performance monitor
perf_monitor = PerformanceMonitor(conn, slow_query_threshold_ms=1000)

# Execute with monitoring
results, metrics = perf_monitor.execute_with_monitoring(
    "SELECT * FROM large_table WHERE status = 'active'",
    explain=True
)

# Get slow queries
slow_queries = perf_monitor.get_slow_queries()

# Get recommendations
recommendations = perf_monitor.recommend_indexes()

# Get stats
stats = perf_monitor.get_performance_stats()
```

### 8. Manage Users

```python
from modules.database import AdminManager

# Create admin manager
admin = AdminManager(conn)

# Create user
user = admin.create_user(
    username="john_doe",
    password="secure_password",
    email="john@example.com",
    roles=["developer"]
)

# Assign role
admin.assign_role("john_doe", "admin")

# Check permission
has_access = admin.check_permission("john_doe", "SELECT", "users")

# Get access report
report = admin.get_access_report()
```

## 🏗️ Architecture

```
modules/database/
├── __init__.py           # Package initialization
├── manager.py            # Database connection manager
├── query_builder.py      # Visual query builder
├── schema_designer.py    # Schema design & ER diagrams
├── data_explorer.py      # Data browsing & CRUD
├── migration.py          # Migration system
├── backup.py             # Backup & restore
├── performance.py        # Performance monitoring
├── admin.py              # User administration
├── streamlit_ui.py       # Streamlit interface
├── tests/                # Test suite
│   ├── test_manager.py
│   ├── test_query_builder.py
│   └── ...
└── README.md             # Documentation
```

## 🔒 Security

- **Password Hashing** - PBKDF2-HMAC-SHA256 with salt
- **SQL Injection Protection** - Parameterized queries
- **Connection Encryption** - SSL/TLS support
- **Role-Based Access** - Granular permissions
- **Audit Logging** - Track all operations
- **Secure Backups** - Encrypted backup support

## 📊 Performance

- **Connection Pooling** - Reuse database connections
- **Query Optimization** - Automatic index recommendations
- **Lazy Loading** - Pagination for large datasets
- **Caching** - Query result caching
- **Batch Operations** - Bulk inserts/updates

## 🧪 Testing

```bash
# Run all tests
pytest modules/database/tests/

# Run with coverage
pytest --cov=modules/database modules/database/tests/

# Run specific test
pytest modules/database/tests/test_manager.py::TestDatabaseManager::test_init
```

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please read CONTRIBUTING.md for guidelines.

## 📧 Support

For issues and questions:
- GitHub Issues: https://github.com/your-org/nexus-platform/issues
- Documentation: https://docs.nexus-platform.com
- Email: support@nexus-platform.com

## 🎯 Roadmap

- [ ] Real-time collaboration
- [ ] AI-powered query optimization
- [ ] Visual data modeling
- [ ] Advanced analytics
- [ ] Cloud database support (AWS RDS, Azure SQL, etc.)
- [ ] Data lineage tracking
- [ ] Automated testing suite
- [ ] API endpoint generation

---

**Built with ❤️ for the NEXUS Platform**
