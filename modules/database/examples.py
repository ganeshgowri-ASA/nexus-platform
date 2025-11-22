"""
NEXUS Database Manager - Usage Examples

Complete examples demonstrating all features of the database manager.
"""

from typing import List, Dict, Any


def example_connection_management():
    """Example: Managing database connections"""
    from modules.database import DatabaseManager, ConnectionConfig, DatabaseType

    # Create database manager
    manager = DatabaseManager()

    # Add PostgreSQL connection
    postgres_config = ConnectionConfig(
        name="production_db",
        db_type=DatabaseType.POSTGRESQL,
        host="localhost",
        port=5432,
        database="myapp_production",
        username="admin",
        password="secure_password",
        ssl=True,
        pool_size=10
    )
    manager.add_connection(postgres_config)

    # Add MySQL connection
    mysql_config = ConnectionConfig(
        name="analytics_db",
        db_type=DatabaseType.MYSQL,
        host="analytics.example.com",
        port=3306,
        database="analytics",
        username="analyst",
        password="password123"
    )
    manager.add_connection(mysql_config)

    # Add SQLite connection
    sqlite_config = ConnectionConfig(
        name="local_cache",
        db_type=DatabaseType.SQLITE,
        database="./cache.db"
    )
    manager.add_connection(sqlite_config)

    # List all connections
    connections = manager.list_connections()
    print(f"Total connections: {len(connections)}")

    # Get connection info
    for conn_name in connections:
        info = manager.get_connection_info(conn_name)
        print(f"\n{conn_name}:")
        print(f"  Type: {info['config']['db_type']}")
        print(f"  Status: {'Connected' if info['status']['connected'] else 'Disconnected'}")

    # Test connection
    success, error = manager.test_connection(postgres_config)
    if success:
        print("\n✓ PostgreSQL connection successful!")
    else:
        print(f"\n✗ Connection failed: {error}")


def example_query_builder():
    """Example: Building queries visually"""
    from modules.database import QueryBuilder, Query, JoinType, OperatorType, SortOrder

    builder = QueryBuilder()

    # Example 1: Simple SELECT
    query1 = (Query()
        .select("id", "name", "email")
        .from_("users")
        .where("status", OperatorType.EQUALS, "active")
        .order("name", SortOrder.ASC)
        .limit_offset(limit=100)
    )

    sql1, params1 = query1.to_sql()
    print("Query 1 - Simple SELECT:")
    print(sql1)
    print(f"Parameters: {params1}\n")

    # Example 2: JOIN with aggregation
    query2 = (Query()
        .select("u.name", "COUNT(o.id) as order_count", "SUM(o.total) as total_spent")
        .from_("users", alias="u")
        .join("orders", "u.id", "o.user_id", JoinType.LEFT)
        .where("u.created_at", OperatorType.GREATER_THAN, "2024-01-01")
        .group("u.id", "u.name")
        .having("COUNT(o.id)", OperatorType.GREATER_THAN, 5)
        .order("total_spent", SortOrder.DESC)
    )

    sql2, params2 = query2.to_sql()
    print("Query 2 - JOIN with Aggregation:")
    print(sql2)
    print()

    # Save query as template
    builder.save_template(
        "user_orders_summary",
        query2,
        description="Summary of user orders with totals",
        tags=["reporting", "orders"]
    )

    # List templates
    templates = builder.list_templates(tag="reporting")
    print(f"Found {len(templates)} reporting templates")


def example_schema_designer():
    """Example: Designing database schema"""
    from modules.database import (
        SchemaDesigner, TableBuilder, DataType,
        IndexType, OnAction
    )

    designer = SchemaDesigner()

    # Create schema
    schema = designer.create_schema(
        "ecommerce",
        "E-commerce application database"
    )

    # Design users table
    users_table = (TableBuilder("users")
        .add_column("id", DataType.INTEGER, auto_increment=True)
        .add_column("email", DataType.VARCHAR, length=255, nullable=False)
        .add_column("username", DataType.VARCHAR, length=50, nullable=False)
        .add_column("password_hash", DataType.VARCHAR, length=255, nullable=False)
        .add_column("created_at", DataType.TIMESTAMP, default="CURRENT_TIMESTAMP")
        .add_column("updated_at", DataType.TIMESTAMP, default="CURRENT_TIMESTAMP")
        .primary_key("id")
        .add_unique("email")
        .add_unique("username")
        .add_index(["email"], name="idx_users_email")
        .add_index(["created_at"], name="idx_users_created")
        .set_comment("Application users")
        .build()
    )

    schema.add_table(users_table)

    # Design products table
    products_table = (TableBuilder("products")
        .add_column("id", DataType.INTEGER, auto_increment=True)
        .add_column("name", DataType.VARCHAR, length=255, nullable=False)
        .add_column("description", DataType.TEXT)
        .add_column("price", DataType.DECIMAL, precision=10, scale=2, nullable=False)
        .add_column("stock", DataType.INTEGER, default="0")
        .add_column("category_id", DataType.INTEGER)
        .add_column("created_at", DataType.TIMESTAMP, default="CURRENT_TIMESTAMP")
        .primary_key("id")
        .add_index(["category_id"], name="idx_products_category")
        .add_index(["price"], name="idx_products_price")
        .add_check("chk_positive_price", "price > 0")
        .add_check("chk_positive_stock", "stock >= 0")
        .build()
    )

    schema.add_table(products_table)

    # Design orders table
    orders_table = (TableBuilder("orders")
        .add_column("id", DataType.INTEGER, auto_increment=True)
        .add_column("user_id", DataType.INTEGER, nullable=False)
        .add_column("total", DataType.DECIMAL, precision=10, scale=2, nullable=False)
        .add_column("status", DataType.VARCHAR, length=20, default="'pending'")
        .add_column("created_at", DataType.TIMESTAMP, default="CURRENT_TIMESTAMP")
        .primary_key("id")
        .add_foreign_key(
            columns=["user_id"],
            ref_table="users",
            ref_columns=["id"],
            on_delete=OnAction.CASCADE
        )
        .add_index(["user_id"], name="idx_orders_user")
        .add_index(["status"], name="idx_orders_status")
        .add_index(["created_at"], name="idx_orders_created")
        .build()
    )

    schema.add_table(orders_table)

    # Generate DDL
    ddl = schema.generate_ddl("postgresql")
    print("Generated DDL:")
    print(ddl)

    # Export schema
    designer.export_schema("ecommerce", "schema.json", format="json")
    designer.export_schema("ecommerce", "schema.sql", format="sql")
    print("\n✓ Schema exported successfully!")


def example_data_explorer():
    """Example: Exploring and manipulating data"""
    from modules.database import DatabaseManager, DataExplorer, ExportFormat

    # Get connection (assuming already created)
    manager = DatabaseManager()
    # conn = manager.get_connection("production_db")

    # Example with mock connection
    print("Data Explorer Examples:")

    # Browse table with pagination
    print("\n1. Browse table:")
    print("   results = explorer.browse_table('users', page=1, page_size=50)")

    # Search data
    print("\n2. Search across table:")
    print("   results = explorer.search_table('users', 'john', columns=['name', 'email'])")

    # Insert data
    print("\n3. Insert record:")
    print("   new_user = {'name': 'John Doe', 'email': 'john@example.com'}")
    print("   rows = explorer.insert_row('users', new_user)")

    # Update data
    print("\n4. Update record:")
    print("   explorer.update_row('users',")
    print("       data={'status': 'active'},")
    print("       where={'id': 123})")

    # Bulk insert
    print("\n5. Bulk insert:")
    print("   users = [")
    print("       {'name': 'Alice', 'email': 'alice@example.com'},")
    print("       {'name': 'Bob', 'email': 'bob@example.com'}")
    print("   ]")
    print("   explorer.bulk_insert('users', users)")

    # Export data
    print("\n6. Export to CSV:")
    print("   csv_data = explorer.export_data('users', ExportFormat.CSV)")

    # Get statistics
    print("\n7. Get column statistics:")
    print("   stats = explorer.get_column_statistics('orders', 'total')")
    print("   # Returns: count, min, max, distinct_count, null_count")


def example_migrations():
    """Example: Database migrations"""
    from modules.database import MigrationManager, DatabaseManager

    # Get connection
    manager = DatabaseManager()
    # conn = manager.get_connection("production_db")

    # Example migration workflow
    print("Migration Examples:")

    print("\n1. Create migration:")
    print("""
    migration_mgr = MigrationManager(conn)

    migration = migration_mgr.add_migration(
        version="001",
        name="create_users_table",
        up_sql=\"\"\"
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        \"\"\",
        down_sql="DROP TABLE users;"
    )
    """)

    print("\n2. Apply migration:")
    print("   migration_mgr.apply_migration('001')")

    print("\n3. Check status:")
    print("   status = migration_mgr.get_migration_status()")
    print("   current = migration_mgr.get_current_version()")

    print("\n4. Rollback migration:")
    print("   migration_mgr.rollback_migration('001')")

    print("\n5. Apply all pending:")
    print("   applied = migration_mgr.apply_all_pending()")

    print("\n6. Verify integrity:")
    print("   verification = migration_mgr.verify_migrations()")


def example_backup_restore():
    """Example: Backup and restore operations"""
    from modules.database import BackupManager, BackupConfig, BackupType

    print("Backup & Restore Examples:")

    print("\n1. Create backup manager:")
    print("""
    backup_config = BackupConfig(
        backup_dir="./backups",
        max_backups=10,
        compression=CompressionType.GZIP
    )
    backup_mgr = BackupManager(conn, backup_config)
    """)

    print("\n2. Create full backup:")
    print("""
    backup = backup_mgr.create_backup(
        name="daily_backup",
        backup_type=BackupType.FULL
    )
    print(f"Backup created: {backup.filepath}")
    print(f"Size: {backup.size_bytes / (1024*1024):.2f} MB")
    """)

    print("\n3. Create schema-only backup:")
    print("""
    schema_backup = backup_mgr.create_backup(
        name="schema_snapshot",
        backup_type=BackupType.SCHEMA_ONLY
    )
    """)

    print("\n4. List backups:")
    print("""
    backups = backup_mgr.list_backups(limit=10)
    for backup in backups:
        print(f"{backup.name}: {backup.size_bytes} bytes")
    """)

    print("\n5. Restore backup:")
    print("""
    backup_mgr.restore_backup(backup.id)
    """)

    print("\n6. Schedule automatic backups:")
    print("""
    schedule_id = backup_mgr.schedule_backup(
        name="nightly",
        interval_hours=24,
        backup_type=BackupType.FULL
    )
    """)


def example_performance_monitoring():
    """Example: Performance monitoring and optimization"""
    from modules.database import PerformanceMonitor

    print("Performance Monitoring Examples:")

    print("\n1. Create monitor:")
    print("""
    perf_monitor = PerformanceMonitor(
        conn,
        slow_query_threshold_ms=1000
    )
    """)

    print("\n2. Execute with monitoring:")
    print("""
    results, metrics = perf_monitor.execute_with_monitoring(
        "SELECT * FROM large_table WHERE status = 'active'",
        explain=True
    )

    print(f"Execution time: {metrics.execution_time_ms}ms")
    print(f"Rows affected: {metrics.rows_affected}")
    """)

    print("\n3. Analyze query:")
    print("""
    analysis = perf_monitor.analyze_query(
        "SELECT * FROM users WHERE name LIKE '%john%'"
    )

    for issue in analysis['issues']:
        print(f"{issue['severity']}: {issue['issue']}")
        print(f"  → {issue['recommendation']}")
    """)

    print("\n4. Get slow queries:")
    print("""
    slow_queries = perf_monitor.get_slow_queries(threshold_ms=500, limit=10)

    for query_metrics in slow_queries:
        print(f"{query_metrics.execution_time_ms}ms: {query_metrics.query}")
    """)

    print("\n5. Get performance statistics:")
    print("""
    stats = perf_monitor.get_performance_stats()

    print(f"Total queries: {stats.total_queries}")
    print(f"Average time: {stats.avg_execution_time_ms}ms")
    print(f"Slow queries: {stats.slow_query_count}")
    print(f"Queries/sec: {stats.queries_per_second}")
    """)

    print("\n6. Index recommendations:")
    print("""
    recommendations = perf_monitor.recommend_indexes()

    for rec in recommendations:
        print(f"Table: {rec.table}")
        print(f"Columns: {', '.join(rec.columns)}")
        print(f"Impact: {rec.impact}")
        print(f"SQL: {rec.create_sql}")
    """)


def example_user_administration():
    """Example: User and role management"""
    from modules.database import AdminManager, PermissionType, ResourceType

    print("User Administration Examples:")

    print("\n1. Create admin manager:")
    print("   admin = AdminManager(conn)")

    print("\n2. Create user:")
    print("""
    user = admin.create_user(
        username="john_doe",
        password="secure_password_123",
        email="john@example.com",
        roles=["developer"]
    )
    """)

    print("\n3. Create custom role:")
    print("""
    role = admin.create_role(
        name="data_analyst",
        description="Read-only access to analytics"
    )

    admin.grant_permission(
        role_name="data_analyst",
        permission_type=PermissionType.SELECT,
        resource_type=ResourceType.TABLE,
        resource_name="analytics.*"
    )
    """)

    print("\n4. Assign role to user:")
    print("   admin.assign_role('john_doe', 'data_analyst')")

    print("\n5. Check permissions:")
    print("""
    has_access = admin.check_permission(
        username="john_doe",
        permission_type=PermissionType.SELECT,
        resource_name="analytics.sales"
    )
    """)

    print("\n6. Get access report:")
    print("""
    report = admin.get_access_report()

    print(f"Total users: {report['total_users']}")
    print(f"Active users: {report['active_users']}")
    print(f"Total roles: {report['total_roles']}")
    """)


def main():
    """Run all examples"""
    print("=" * 70)
    print("NEXUS Database Manager - Complete Examples")
    print("=" * 70)

    examples = [
        ("Connection Management", example_connection_management),
        ("Query Builder", example_query_builder),
        ("Schema Designer", example_schema_designer),
        ("Data Explorer", example_data_explorer),
        ("Migrations", example_migrations),
        ("Backup & Restore", example_backup_restore),
        ("Performance Monitoring", example_performance_monitoring),
        ("User Administration", example_user_administration),
    ]

    for title, example_func in examples:
        print(f"\n{'=' * 70}")
        print(f"Example: {title}")
        print('=' * 70)
        try:
            example_func()
        except Exception as e:
            print(f"Error running example: {e}")

    print(f"\n{'=' * 70}")
    print("Examples completed!")
    print('=' * 70)


if __name__ == "__main__":
    main()
