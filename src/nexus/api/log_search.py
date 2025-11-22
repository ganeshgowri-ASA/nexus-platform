"""Log search and query API endpoints."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from nexus.models.log_models import (
    LogEntry,
    LogLevelEnum,
    LogSearchQuery,
    LogSearchResponse,
    LogStats,
)


class LogSearchService:
    """Service for searching and aggregating logs."""

    def __init__(self, log_dir: Path = Path("logs")):
        """Initialize log search service.

        Args:
            log_dir: Directory containing log files
        """
        self.log_dir = log_dir

    def _read_json_logs(
        self, log_file: Path, max_lines: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Read logs from JSON log file.

        Args:
            log_file: Path to log file
            max_lines: Maximum number of lines to read

        Returns:
            List of log entries as dictionaries
        """
        logs = []

        if not log_file.exists():
            return logs

        try:
            with open(log_file, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if max_lines and i >= max_lines:
                        break

                    line = line.strip()
                    if not line:
                        continue

                    try:
                        log_entry = json.loads(line)
                        logs.append(log_entry)
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            print(f"Error reading log file {log_file}: {e}")

        return logs

    def _filter_logs(
        self, logs: List[Dict[str, Any]], query: LogSearchQuery
    ) -> List[Dict[str, Any]]:
        """Filter logs based on query parameters.

        Args:
            logs: List of log entries
            query: Search query parameters

        Returns:
            Filtered list of log entries
        """
        filtered = logs

        # Filter by time range
        if query.start_time:
            filtered = [
                log
                for log in filtered
                if datetime.fromisoformat(log.get("timestamp", ""))
                >= query.start_time
            ]

        if query.end_time:
            filtered = [
                log
                for log in filtered
                if datetime.fromisoformat(log.get("timestamp", ""))
                <= query.end_time
            ]

        # Filter by level
        if query.level:
            filtered = [
                log for log in filtered if log.get("level") == query.level.value
            ]

        # Filter by logger name
        if query.logger_name:
            filtered = [
                log
                for log in filtered
                if query.logger_name in log.get("logger_name", "")
            ]

        # Filter by request ID
        if query.request_id:
            filtered = [
                log
                for log in filtered
                if log.get("request_id") == query.request_id
            ]

        # Filter by user ID
        if query.user_id:
            filtered = [
                log for log in filtered if log.get("user_id") == query.user_id
            ]

        # Filter by error type
        if query.error_type:
            filtered = [
                log
                for log in filtered
                if log.get("error_type") == query.error_type
            ]

        # Search in message
        if query.search_text:
            search_lower = query.search_text.lower()
            filtered = [
                log
                for log in filtered
                if search_lower in log.get("event", "").lower()
                or search_lower in str(log.get("error_message", "")).lower()
            ]

        return filtered

    def search_logs(self, query: LogSearchQuery) -> LogSearchResponse:
        """Search logs based on query parameters.

        Args:
            query: Search query parameters

        Returns:
            Search results with pagination
        """
        # Read logs from JSON log file
        log_file = self.log_dir / "nexus.json.log"
        all_logs = self._read_json_logs(log_file, max_lines=10000)

        # Filter logs
        filtered_logs = self._filter_logs(all_logs, query)

        # Sort logs
        filtered_logs.sort(
            key=lambda x: x.get("timestamp", ""),
            reverse=(query.sort_order == "desc"),
        )

        # Apply pagination
        total_count = len(filtered_logs)
        start = query.offset
        end = query.offset + query.limit
        paginated_logs = filtered_logs[start:end]

        # Convert to LogEntry models
        log_entries = []
        for log in paginated_logs:
            try:
                log_entry = LogEntry(
                    timestamp=datetime.fromisoformat(log.get("timestamp", "")),
                    level=LogLevelEnum(log.get("level", "INFO")),
                    logger_name=log.get("logger_name", "unknown"),
                    message=log.get("event", ""),
                    app=log.get("app", "nexus"),
                    request_id=log.get("request_id"),
                    user_id=log.get("user_id"),
                    error_type=log.get("error_type"),
                    error_message=log.get("error_message"),
                    traceback=log.get("traceback"),
                    context=log.get("context"),
                    extra={
                        k: v
                        for k, v in log.items()
                        if k
                        not in [
                            "timestamp",
                            "level",
                            "logger_name",
                            "event",
                            "app",
                            "request_id",
                            "user_id",
                            "error_type",
                            "error_message",
                            "traceback",
                            "context",
                        ]
                    },
                )
                log_entries.append(log_entry)
            except Exception:
                continue

        return LogSearchResponse(
            logs=log_entries,
            total_count=total_count,
            offset=query.offset,
            limit=query.limit,
            has_more=(query.offset + query.limit) < total_count,
        )

    def get_log_stats(
        self, hours: int = 24
    ) -> LogStats:
        """Get log statistics.

        Args:
            hours: Number of hours to analyze

        Returns:
            Log statistics
        """
        # Read logs
        log_file = self.log_dir / "nexus.json.log"
        all_logs = self._read_json_logs(log_file, max_lines=10000)

        # Filter by time range
        start_time = datetime.utcnow() - timedelta(hours=hours)
        filtered_logs = [
            log
            for log in all_logs
            if datetime.fromisoformat(log.get("timestamp", "")) >= start_time
        ]

        # Count by level
        level_counts = {
            "DEBUG": 0,
            "INFO": 0,
            "WARNING": 0,
            "ERROR": 0,
            "CRITICAL": 0,
        }

        for log in filtered_logs:
            level = log.get("level", "INFO")
            if level in level_counts:
                level_counts[level] += 1

        # Get top errors
        error_types: Dict[str, int] = {}
        for log in filtered_logs:
            if log.get("error_type"):
                error_type = log["error_type"]
                error_types[error_type] = error_types.get(error_type, 0) + 1

        top_errors = [
            {"error_type": error_type, "count": count}
            for error_type, count in sorted(
                error_types.items(), key=lambda x: x[1], reverse=True
            )[:10]
        ]

        # Calculate logs per hour
        logs_per_hour_dict: Dict[str, int] = {}
        for log in filtered_logs:
            timestamp = datetime.fromisoformat(log.get("timestamp", ""))
            hour_key = timestamp.strftime("%Y-%m-%d %H:00")
            logs_per_hour_dict[hour_key] = logs_per_hour_dict.get(hour_key, 0) + 1

        logs_per_hour = [
            {"hour": hour, "count": count}
            for hour, count in sorted(logs_per_hour_dict.items())
        ]

        # Get time range
        if filtered_logs:
            timestamps = [
                datetime.fromisoformat(log.get("timestamp", ""))
                for log in filtered_logs
            ]
            time_range = {
                "start": min(timestamps),
                "end": max(timestamps),
            }
        else:
            time_range = {
                "start": start_time,
                "end": datetime.utcnow(),
            }

        return LogStats(
            total_logs=len(filtered_logs),
            error_count=level_counts["ERROR"],
            warning_count=level_counts["WARNING"],
            info_count=level_counts["INFO"],
            debug_count=level_counts["DEBUG"],
            critical_count=level_counts["CRITICAL"],
            time_range=time_range,
            top_errors=top_errors,
            logs_per_hour=logs_per_hour,
        )


def create_log_search_api(log_dir: Path = Path("logs")) -> FastAPI:
    """Create FastAPI application for log search.

    Args:
        log_dir: Directory containing log files

    Returns:
        FastAPI application
    """
    app = FastAPI(
        title="NEXUS Log Search API",
        description="API for searching and analyzing NEXUS platform logs",
        version="1.0.0",
    )

    log_service = LogSearchService(log_dir=log_dir)

    @app.get("/")
    async def root() -> Dict[str, str]:
        """Root endpoint."""
        return {
            "service": "NEXUS Log Search API",
            "version": "1.0.0",
            "status": "running",
        }

    @app.get("/health")
    async def health() -> Dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy"}

    @app.post("/search", response_model=LogSearchResponse)
    async def search_logs(query: LogSearchQuery) -> LogSearchResponse:
        """Search logs based on query parameters.

        Args:
            query: Search query parameters

        Returns:
            Search results
        """
        try:
            return log_service.search_logs(query)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/search", response_model=LogSearchResponse)
    async def search_logs_get(
        start_time: Optional[datetime] = Query(None),
        end_time: Optional[datetime] = Query(None),
        level: Optional[LogLevelEnum] = Query(None),
        logger_name: Optional[str] = Query(None),
        request_id: Optional[str] = Query(None),
        user_id: Optional[str] = Query(None),
        search_text: Optional[str] = Query(None),
        error_type: Optional[str] = Query(None),
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
        sort_order: str = Query("desc"),
    ) -> LogSearchResponse:
        """Search logs using GET method.

        Args:
            start_time: Start of time range
            end_time: End of time range
            level: Filter by log level
            logger_name: Filter by logger name
            request_id: Filter by request ID
            user_id: Filter by user ID
            search_text: Search in messages
            error_type: Filter by error type
            limit: Maximum results
            offset: Offset for pagination
            sort_order: Sort order (asc/desc)

        Returns:
            Search results
        """
        query = LogSearchQuery(
            start_time=start_time,
            end_time=end_time,
            level=level,
            logger_name=logger_name,
            request_id=request_id,
            user_id=user_id,
            search_text=search_text,
            error_type=error_type,
            limit=limit,
            offset=offset,
            sort_order=sort_order,
        )

        try:
            return log_service.search_logs(query)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/stats", response_model=LogStats)
    async def get_stats(hours: int = Query(24, ge=1, le=168)) -> LogStats:
        """Get log statistics.

        Args:
            hours: Number of hours to analyze (default: 24, max: 168)

        Returns:
            Log statistics
        """
        try:
            return log_service.get_log_stats(hours=hours)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return app
