"""
NEXUS Dashboard Builder - Data Sources Module
Real-time data sources with caching and streaming support
"""

import pandas as pd
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import threading
import time


class CacheStrategy(Enum):
    """Cache strategies"""
    NONE = "none"
    MEMORY = "memory"
    DISK = "disk"
    DISTRIBUTED = "distributed"


@dataclass
class DataSourceConfig:
    """Data source configuration"""
    name: str
    connection_string: str
    query: str = ""
    refresh_interval: int = 60  # seconds
    cache_enabled: bool = True
    cache_ttl: int = 300  # seconds
    cache_strategy: CacheStrategy = CacheStrategy.MEMORY
    max_rows: Optional[int] = None
    streaming_enabled: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'connection_string': self.connection_string,
            'query': self.query,
            'refresh_interval': self.refresh_interval,
            'cache_enabled': self.cache_enabled,
            'cache_ttl': self.cache_ttl,
            'cache_strategy': self.cache_strategy.value,
            'max_rows': self.max_rows,
            'streaming_enabled': self.streaming_enabled
        }


class DataCache:
    """In-memory data cache"""

    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()

    def get(self, key: str) -> Optional[pd.DataFrame]:
        """Get cached data"""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                if datetime.now() < entry['expires_at']:
                    return entry['data']
                else:
                    del self.cache[key]
        return None

    def set(self, key: str, data: pd.DataFrame, ttl: int):
        """Set cached data"""
        with self.lock:
            self.cache[key] = {
                'data': data,
                'cached_at': datetime.now(),
                'expires_at': datetime.now() + timedelta(seconds=ttl)
            }

    def invalidate(self, key: str):
        """Invalidate cache entry"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]

    def clear(self):
        """Clear all cache"""
        with self.lock:
            self.cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            return {
                'entries': len(self.cache),
                'total_size': sum(entry['data'].memory_usage(deep=True).sum() for entry in self.cache.values())
            }


class RealtimeDataSource:
    """Real-time data source with auto-refresh"""

    def __init__(self, config: DataSourceConfig):
        self.config = config
        self.cache = DataCache()
        self.data: Optional[pd.DataFrame] = None
        self.last_update: Optional[datetime] = None
        self.is_running = False
        self.update_thread: Optional[threading.Thread] = None
        self.callbacks: List[Callable] = []

    def start(self):
        """Start auto-refresh"""
        if not self.is_running:
            self.is_running = True
            self.update_thread = threading.Thread(target=self._auto_refresh_loop, daemon=True)
            self.update_thread.start()

    def stop(self):
        """Stop auto-refresh"""
        self.is_running = False
        if self.update_thread:
            self.update_thread.join(timeout=5)

    def _auto_refresh_loop(self):
        """Auto-refresh loop"""
        while self.is_running:
            try:
                self.refresh()
                time.sleep(self.config.refresh_interval)
            except Exception as e:
                print(f"Auto-refresh failed: {e}")
                time.sleep(5)

    def refresh(self) -> pd.DataFrame:
        """Refresh data"""
        # Check cache first
        if self.config.cache_enabled:
            cached_data = self.cache.get(self.config.name)
            if cached_data is not None:
                return cached_data

        # Fetch fresh data
        data = self._fetch_data()

        # Cache data
        if self.config.cache_enabled:
            self.cache.set(self.config.name, data, self.config.cache_ttl)

        # Update internal state
        self.data = data
        self.last_update = datetime.now()

        # Notify callbacks
        for callback in self.callbacks:
            try:
                callback(data)
            except Exception as e:
                print(f"Callback failed: {e}")

        return data

    def _fetch_data(self) -> pd.DataFrame:
        """Fetch data from source (to be overridden)"""
        # Placeholder implementation
        return pd.DataFrame()

    def get_data(self) -> Optional[pd.DataFrame]:
        """Get current data"""
        if self.data is None:
            return self.refresh()
        return self.data

    def register_callback(self, callback: Callable):
        """Register callback for data updates"""
        self.callbacks.append(callback)

    def unregister_callback(self, callback: Callable):
        """Unregister callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def invalidate_cache(self):
        """Invalidate cached data"""
        self.cache.invalidate(self.config.name)


class StreamingDataSource(RealtimeDataSource):
    """Streaming data source"""

    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self.buffer: List[Dict[str, Any]] = []
        self.buffer_size = 1000
        self.streaming = False

    def start_streaming(self):
        """Start streaming data"""
        self.streaming = True
        self.start()

    def stop_streaming(self):
        """Stop streaming data"""
        self.streaming = False
        self.stop()

    def push_data(self, record: Dict[str, Any]):
        """Push new data to stream"""
        self.buffer.append(record)

        if len(self.buffer) >= self.buffer_size:
            self.buffer.pop(0)

        # Convert buffer to DataFrame
        self.data = pd.DataFrame(self.buffer)
        self.last_update = datetime.now()

        # Notify callbacks
        for callback in self.callbacks:
            try:
                callback(self.data)
            except Exception as e:
                print(f"Streaming callback failed: {e}")


class DataSourceManager:
    """Manages multiple data sources"""

    def __init__(self):
        self.sources: Dict[str, RealtimeDataSource] = {}

    def add_source(self, source: RealtimeDataSource) -> str:
        """Add a data source"""
        self.sources[source.config.name] = source
        return source.config.name

    def remove_source(self, name: str) -> bool:
        """Remove a data source"""
        if name in self.sources:
            source = self.sources[name]
            source.stop()
            del self.sources[name]
            return True
        return False

    def get_source(self, name: str) -> Optional[RealtimeDataSource]:
        """Get a data source"""
        return self.sources.get(name)

    def start_all(self):
        """Start all data sources"""
        for source in self.sources.values():
            source.start()

    def stop_all(self):
        """Stop all data sources"""
        for source in self.sources.values():
            source.stop()

    def refresh_all(self):
        """Refresh all data sources"""
        for source in self.sources.values():
            source.refresh()

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for all sources"""
        return {
            'total_sources': len(self.sources),
            'active_sources': sum(1 for s in self.sources.values() if s.is_running),
            'sources': {
                name: {
                    'last_update': source.last_update.isoformat() if source.last_update else None,
                    'is_running': source.is_running,
                    'rows': len(source.data) if source.data is not None else 0
                }
                for name, source in self.sources.items()
            }
        }
