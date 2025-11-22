"""
Performance Monitor

Query optimization, explain plans, index recommendations,
slow query logging, and performance metrics.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import time
import statistics
import logging
from collections import defaultdict, deque


class QueryType(Enum):
    """Query types"""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    OTHER = "OTHER"


@dataclass
class QueryMetrics:
    """Query execution metrics"""
    query: str
    query_type: QueryType
    execution_time_ms: float
    rows_affected: int
    timestamp: datetime
    explain_plan: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "query": self.query,
            "query_type": self.query_type.value,
            "execution_time_ms": self.execution_time_ms,
            "rows_affected": self.rows_affected,
            "timestamp": self.timestamp.isoformat(),
            "explain_plan": self.explain_plan,
            "parameters": self.parameters
        }


@dataclass
class IndexRecommendation:
    """Index recommendation"""
    table: str
    columns: List[str]
    reason: str
    impact: str  # LOW, MEDIUM, HIGH
    create_sql: str
    estimated_improvement: Optional[float] = None


@dataclass
class PerformanceStats:
    """Performance statistics"""
    total_queries: int = 0
    total_execution_time_ms: float = 0
    avg_execution_time_ms: float = 0
    min_execution_time_ms: float = 0
    max_execution_time_ms: float = 0
    slow_query_count: int = 0
    queries_per_second: float = 0
    by_query_type: Dict[str, int] = field(default_factory=dict)


class PerformanceMonitor:
    """
    Performance Monitor

    Monitor query performance, analyze slow queries, recommend indexes,
    and provide optimization suggestions.
    """

    def __init__(self, connection, slow_query_threshold_ms: float = 1000):
        """
        Initialize performance monitor

        Args:
            connection: DatabaseConnection instance
            slow_query_threshold_ms: Threshold for slow queries (ms)
        """
        self.connection = connection
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self.logger = logging.getLogger("database.performance")

        # Query history
        self.query_history: deque = deque(maxlen=1000)
        self.slow_queries: List[QueryMetrics] = []

        # Performance metrics
        self.metrics_by_table: Dict[str, List[QueryMetrics]] = defaultdict(list)
        self.metrics_by_type: Dict[QueryType, List[QueryMetrics]] = defaultdict(list)

        # Monitoring start time
        self.monitoring_started = datetime.now()

    def execute_with_monitoring(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        explain: bool = False
    ) -> Tuple[List[Dict[str, Any]], QueryMetrics]:
        """
        Execute query with performance monitoring

        Args:
            query: SQL query
            params: Query parameters
            explain: Generate explain plan

        Returns:
            Tuple of (results, metrics)
        """
        # Detect query type
        query_type = self._detect_query_type(query)

        # Get explain plan if requested
        explain_plan = None
        if explain and query_type == QueryType.SELECT:
            explain_plan = self.get_explain_plan(query, params)

        # Execute query and measure time
        start_time = time.time()

        if query_type == QueryType.SELECT:
            results = self.connection.execute_query(query, params)
            rows_affected = len(results)
        else:
            rows_affected = self.connection.execute_command(query, params)
            results = []

        execution_time_ms = (time.time() - start_time) * 1000

        # Create metrics
        metrics = QueryMetrics(
            query=query,
            query_type=query_type,
            execution_time_ms=execution_time_ms,
            rows_affected=rows_affected,
            timestamp=datetime.now(),
            explain_plan=explain_plan,
            parameters=params
        )

        # Store metrics
        self._record_metrics(metrics)

        return results, metrics

    def get_explain_plan(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get query execution plan

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Explain plan data
        """
        try:
            # PostgreSQL/MySQL style EXPLAIN
            explain_query = f"EXPLAIN {query}"
            results = self.connection.execute_query(explain_query, params)

            return {
                "plan": results,
                "formatted": self._format_explain_plan(results)
            }
        except Exception as e:
            self.logger.error(f"Failed to get explain plan: {e}")
            return {"error": str(e)}

    def _format_explain_plan(self, plan: List[Dict[str, Any]]) -> str:
        """Format explain plan for display"""
        lines = []
        for row in plan:
            for key, value in row.items():
                lines.append(f"{key}: {value}")
        return "\n".join(lines)

    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze query for optimization opportunities

        Args:
            query: SQL query

        Returns:
            Analysis results
        """
        analysis = {
            "query": query,
            "issues": [],
            "recommendations": [],
            "index_suggestions": []
        }

        query_lower = query.lower()

        # Check for SELECT *
        if "select *" in query_lower:
            analysis["issues"].append({
                "severity": "MEDIUM",
                "issue": "Using SELECT * instead of specific columns",
                "recommendation": "Specify only needed columns to reduce data transfer"
            })

        # Check for missing WHERE clause
        if "select" in query_lower and "where" not in query_lower and "join" not in query_lower:
            analysis["issues"].append({
                "severity": "HIGH",
                "issue": "SELECT without WHERE clause - full table scan",
                "recommendation": "Add WHERE clause to filter results"
            })

        # Check for LIKE with leading wildcard
        if "like" in query_lower and "'%" in query_lower:
            analysis["issues"].append({
                "severity": "MEDIUM",
                "issue": "LIKE with leading wildcard prevents index usage",
                "recommendation": "Avoid leading wildcards in LIKE patterns"
            })

        # Check for OR conditions
        if " or " in query_lower:
            analysis["issues"].append({
                "severity": "LOW",
                "issue": "OR conditions may prevent index usage",
                "recommendation": "Consider using UNION or IN clause instead"
            })

        # Check for subqueries in SELECT
        if "select" in query_lower.count("select") > 1:
            if query_lower.index("select") < query_lower.index("from"):
                analysis["issues"].append({
                    "severity": "MEDIUM",
                    "issue": "Subquery in SELECT clause",
                    "recommendation": "Consider using JOIN instead"
                })

        return analysis

    def get_slow_queries(
        self,
        threshold_ms: Optional[float] = None,
        limit: int = 50
    ) -> List[QueryMetrics]:
        """
        Get slow queries

        Args:
            threshold_ms: Threshold in milliseconds (uses default if None)
            limit: Maximum queries to return

        Returns:
            List of slow query metrics
        """
        threshold = threshold_ms or self.slow_query_threshold_ms

        slow = [
            m for m in self.query_history
            if m.execution_time_ms >= threshold
        ]

        # Sort by execution time (slowest first)
        slow.sort(key=lambda m: m.execution_time_ms, reverse=True)

        return slow[:limit]

    def get_performance_stats(self) -> PerformanceStats:
        """
        Get overall performance statistics

        Returns:
            PerformanceStats object
        """
        if not self.query_history:
            return PerformanceStats()

        execution_times = [m.execution_time_ms for m in self.query_history]

        # Calculate statistics
        total_queries = len(self.query_history)
        total_time = sum(execution_times)
        avg_time = statistics.mean(execution_times)
        min_time = min(execution_times)
        max_time = max(execution_times)

        # Count slow queries
        slow_count = sum(
            1 for m in self.query_history
            if m.execution_time_ms >= self.slow_query_threshold_ms
        )

        # Calculate queries per second
        duration = (datetime.now() - self.monitoring_started).total_seconds()
        qps = total_queries / duration if duration > 0 else 0

        # Count by query type
        by_type = defaultdict(int)
        for metrics in self.query_history:
            by_type[metrics.query_type.value] += 1

        return PerformanceStats(
            total_queries=total_queries,
            total_execution_time_ms=total_time,
            avg_execution_time_ms=avg_time,
            min_execution_time_ms=min_time,
            max_execution_time_ms=max_time,
            slow_query_count=slow_count,
            queries_per_second=qps,
            by_query_type=dict(by_type)
        )

    def recommend_indexes(
        self,
        table_name: Optional[str] = None
    ) -> List[IndexRecommendation]:
        """
        Recommend indexes based on query patterns

        Args:
            table_name: Specific table (None = all tables)

        Returns:
            List of index recommendations
        """
        recommendations = []

        # Analyze slow queries for index opportunities
        slow_queries = self.get_slow_queries()

        # Track frequently queried columns
        column_usage = defaultdict(int)
        where_columns = defaultdict(list)

        for metrics in slow_queries:
            # Parse query to find WHERE columns
            # This is simplified - real implementation would use SQL parser
            query_lower = metrics.query.lower()

            if "where" in query_lower:
                # Extract table and columns from WHERE clause
                # Simplified extraction
                parts = query_lower.split("where")[1].split()
                for i, part in enumerate(parts):
                    if i < len(parts) - 1 and parts[i + 1] in ['=', '>', '<', '>=', '<=', 'in', 'like']:
                        # This looks like a column in WHERE clause
                        column_usage[part] += 1
                        where_columns[part].append(metrics.query)

        # Generate recommendations for frequently used columns
        for column, count in column_usage.items():
            if count >= 3:  # Column used in 3+ slow queries
                # Try to determine table name
                # This is simplified
                table = table_name or "table_name"

                recommendation = IndexRecommendation(
                    table=table,
                    columns=[column],
                    reason=f"Column used in {count} slow queries",
                    impact="HIGH" if count >= 10 else "MEDIUM",
                    create_sql=f"CREATE INDEX idx_{table}_{column} ON {table}({column});"
                )
                recommendations.append(recommendation)

        return recommendations

    def get_table_statistics(self, table_name: str) -> Dict[str, Any]:
        """
        Get table performance statistics

        Args:
            table_name: Table name

        Returns:
            Statistics dictionary
        """
        metrics = self.metrics_by_table.get(table_name, [])

        if not metrics:
            return {
                "table": table_name,
                "query_count": 0
            }

        execution_times = [m.execution_time_ms for m in metrics]

        return {
            "table": table_name,
            "query_count": len(metrics),
            "total_time_ms": sum(execution_times),
            "avg_time_ms": statistics.mean(execution_times),
            "min_time_ms": min(execution_times),
            "max_time_ms": max(execution_times),
            "slow_query_count": sum(
                1 for m in metrics
                if m.execution_time_ms >= self.slow_query_threshold_ms
            )
        }

    def get_connection_pool_stats(self) -> Dict[str, Any]:
        """
        Get connection pool statistics

        Returns:
            Pool statistics
        """
        status = self.connection.check_health()

        return {
            "active_connections": status.active_connections,
            "pool_size": status.pool_size,
            "utilization_percent": (
                (status.active_connections / status.pool_size * 100)
                if status.pool_size > 0 else 0
            ),
            "response_time_ms": status.response_time
        }

    def optimize_table(self, table_name: str) -> Dict[str, Any]:
        """
        Optimize table (VACUUM, ANALYZE, etc.)

        Args:
            table_name: Table name

        Returns:
            Optimization results
        """
        results = {
            "table": table_name,
            "operations": []
        }

        try:
            # PostgreSQL: VACUUM ANALYZE
            self.connection.execute_command(f"VACUUM ANALYZE {table_name}")
            results["operations"].append("VACUUM ANALYZE")
            self.logger.info(f"Optimized table: {table_name}")

        except Exception as e:
            # MySQL: OPTIMIZE TABLE
            try:
                self.connection.execute_command(f"OPTIMIZE TABLE {table_name}")
                results["operations"].append("OPTIMIZE TABLE")
                self.logger.info(f"Optimized table: {table_name}")
            except Exception as e2:
                results["error"] = str(e2)
                self.logger.error(f"Failed to optimize table {table_name}: {e2}")

        return results

    def get_query_profile(self, query: str, iterations: int = 10) -> Dict[str, Any]:
        """
        Profile a query by running it multiple times

        Args:
            query: SQL query
            iterations: Number of iterations

        Returns:
            Profiling results
        """
        execution_times = []

        for i in range(iterations):
            start = time.time()
            self.connection.execute_query(query)
            execution_times.append((time.time() - start) * 1000)

        return {
            "query": query,
            "iterations": iterations,
            "avg_time_ms": statistics.mean(execution_times),
            "min_time_ms": min(execution_times),
            "max_time_ms": max(execution_times),
            "median_time_ms": statistics.median(execution_times),
            "stdev_ms": statistics.stdev(execution_times) if len(execution_times) > 1 else 0,
            "all_times_ms": execution_times
        }

    def detect_missing_indexes(self, table_name: str) -> List[str]:
        """
        Detect missing indexes on foreign keys

        Args:
            table_name: Table name

        Returns:
            List of columns missing indexes
        """
        # Get table schema
        schema = self.connection.get_table_schema(table_name)

        # This is simplified - real implementation would:
        # 1. Identify foreign key columns
        # 2. Check existing indexes
        # 3. Find FK columns without indexes

        missing = []
        # Placeholder implementation
        self.logger.info(f"Checking missing indexes for {table_name}")

        return missing

    def clear_metrics(self) -> None:
        """Clear all performance metrics"""
        self.query_history.clear()
        self.slow_queries.clear()
        self.metrics_by_table.clear()
        self.metrics_by_type.clear()
        self.monitoring_started = datetime.now()
        self.logger.info("Cleared performance metrics")

    def export_metrics(self, filepath: str) -> None:
        """Export metrics to JSON file"""
        import json

        data = {
            "monitoring_period": {
                "started": self.monitoring_started.isoformat(),
                "ended": datetime.now().isoformat()
            },
            "stats": self.get_performance_stats().__dict__,
            "slow_queries": [m.to_dict() for m in self.get_slow_queries()],
            "query_history": [m.to_dict() for m in list(self.query_history)]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        self.logger.info(f"Exported metrics to {filepath}")

    def _detect_query_type(self, query: str) -> QueryType:
        """Detect query type from SQL"""
        query_lower = query.strip().lower()

        if query_lower.startswith("select"):
            return QueryType.SELECT
        elif query_lower.startswith("insert"):
            return QueryType.INSERT
        elif query_lower.startswith("update"):
            return QueryType.UPDATE
        elif query_lower.startswith("delete"):
            return QueryType.DELETE
        else:
            return QueryType.OTHER

    def _record_metrics(self, metrics: QueryMetrics) -> None:
        """Record query metrics"""
        # Add to history
        self.query_history.append(metrics)

        # Track by type
        self.metrics_by_type[metrics.query_type].append(metrics)

        # Extract table name and track by table
        # Simplified - real implementation would parse SQL
        table_name = self._extract_table_name(metrics.query)
        if table_name:
            self.metrics_by_table[table_name].append(metrics)

        # Track slow queries
        if metrics.execution_time_ms >= self.slow_query_threshold_ms:
            self.slow_queries.append(metrics)
            self.logger.warning(
                f"Slow query detected ({metrics.execution_time_ms:.2f}ms): "
                f"{metrics.query[:100]}"
            )

    def _extract_table_name(self, query: str) -> Optional[str]:
        """Extract table name from query (simplified)"""
        query_lower = query.lower()

        # Try to find FROM clause
        if " from " in query_lower:
            parts = query_lower.split(" from ")[1].split()
            if parts:
                return parts[0].strip()

        # Try to find INTO clause (for INSERT)
        if " into " in query_lower:
            parts = query_lower.split(" into ")[1].split()
            if parts:
                return parts[0].strip()

        # Try to find UPDATE clause
        if "update " in query_lower:
            parts = query_lower.split("update ")[1].split()
            if parts:
                return parts[0].strip()

        return None
