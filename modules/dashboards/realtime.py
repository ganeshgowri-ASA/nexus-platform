"""
NEXUS Dashboard Builder - Real-time Updates Module
WebSocket-based real-time dashboard updates with automatic refresh
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import uuid


class UpdateType(Enum):
    """Types of real-time updates"""
    WIDGET_DATA = "widget_data"
    WIDGET_CONFIG = "widget_config"
    DASHBOARD_CONFIG = "dashboard_config"
    FILTER_CHANGE = "filter_change"
    ALERT = "alert"
    CONNECTION_STATUS = "connection_status"


@dataclass
class Update:
    """Represents a real-time update"""
    update_id: str
    update_type: UpdateType
    dashboard_id: str
    widget_id: Optional[str]
    data: Any
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            'update_id': self.update_id,
            'update_type': self.update_type.value,
            'dashboard_id': self.dashboard_id,
            'widget_id': self.widget_id,
            'data': self.data,
            'timestamp': self.timestamp.isoformat()
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class RealtimeConnection:
    """Manages a single real-time connection"""

    def __init__(self, connection_id: str, dashboard_id: str):
        self.connection_id = connection_id
        self.dashboard_id = dashboard_id
        self.connected_at = datetime.now()
        self.last_activity = datetime.now()
        self.subscribed_widgets: Set[str] = set()
        self.is_active = True

    def subscribe_widget(self, widget_id: str):
        """Subscribe to widget updates"""
        self.subscribed_widgets.add(widget_id)

    def unsubscribe_widget(self, widget_id: str):
        """Unsubscribe from widget updates"""
        if widget_id in self.subscribed_widgets:
            self.subscribed_widgets.remove(widget_id)

    def is_subscribed(self, widget_id: str) -> bool:
        """Check if subscribed to widget"""
        return widget_id in self.subscribed_widgets

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()


class RealtimeManager:
    """Manages real-time connections and updates"""

    def __init__(self):
        self.connections: Dict[str, RealtimeConnection] = {}
        self.update_queue: asyncio.Queue = asyncio.Queue()
        self.update_handlers: Dict[UpdateType, List[Callable]] = {}
        self.is_running = False

    def create_connection(self, dashboard_id: str) -> str:
        """Create a new real-time connection"""
        connection_id = str(uuid.uuid4())
        connection = RealtimeConnection(connection_id, dashboard_id)
        self.connections[connection_id] = connection
        return connection_id

    def close_connection(self, connection_id: str):
        """Close a connection"""
        if connection_id in self.connections:
            self.connections[connection_id].is_active = False
            del self.connections[connection_id]

    def get_connection(self, connection_id: str) -> Optional[RealtimeConnection]:
        """Get a connection"""
        return self.connections.get(connection_id)

    def subscribe(self, connection_id: str, widget_id: str):
        """Subscribe connection to widget updates"""
        connection = self.get_connection(connection_id)
        if connection:
            connection.subscribe_widget(widget_id)

    def unsubscribe(self, connection_id: str, widget_id: str):
        """Unsubscribe connection from widget updates"""
        connection = self.get_connection(connection_id)
        if connection:
            connection.unsubscribe_widget(widget_id)

    async def push_update(self, update: Update):
        """Push an update to the queue"""
        await self.update_queue.put(update)

    async def broadcast_update(self, update: Update):
        """Broadcast update to all relevant connections"""
        for connection in self.connections.values():
            if not connection.is_active:
                continue

            # Check if connection should receive this update
            if connection.dashboard_id != update.dashboard_id:
                continue

            if update.widget_id and not connection.is_subscribed(update.widget_id):
                continue

            # Send update to connection
            await self._send_update(connection, update)

    async def _send_update(self, connection: RealtimeConnection, update: Update):
        """Send update to a connection"""
        # Placeholder - would send via WebSocket
        connection.update_activity()

    def register_handler(self, update_type: UpdateType, handler: Callable):
        """Register update handler"""
        if update_type not in self.update_handlers:
            self.update_handlers[update_type] = []
        self.update_handlers[update_type].append(handler)

    async def process_updates(self):
        """Process updates from queue"""
        while self.is_running:
            try:
                update = await asyncio.wait_for(self.update_queue.get(), timeout=1.0)

                # Call handlers
                if update.update_type in self.update_handlers:
                    for handler in self.update_handlers[update.update_type]:
                        try:
                            await handler(update)
                        except Exception as e:
                            print(f"Handler failed: {e}")

                # Broadcast to connections
                await self.broadcast_update(update)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error processing update: {e}")

    async def start(self):
        """Start the real-time manager"""
        self.is_running = True
        await self.process_updates()

    def stop(self):
        """Stop the real-time manager"""
        self.is_running = False

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics"""
        active_connections = sum(1 for c in self.connections.values() if c.is_active)

        return {
            'total_connections': len(self.connections),
            'active_connections': active_connections,
            'queue_size': self.update_queue.qsize()
        }


class RefreshScheduler:
    """Schedules automatic widget refreshes"""

    def __init__(self):
        self.schedules: Dict[str, Dict[str, Any]] = {}
        self.is_running = False

    def schedule_refresh(self, widget_id: str, interval: int, callback: Callable):
        """Schedule widget refresh"""
        self.schedules[widget_id] = {
            'interval': interval,
            'callback': callback,
            'last_refresh': datetime.now()
        }

    def unschedule_refresh(self, widget_id: str):
        """Unschedule widget refresh"""
        if widget_id in self.schedules:
            del self.schedules[widget_id]

    async def run(self):
        """Run the refresh scheduler"""
        self.is_running = True

        while self.is_running:
            now = datetime.now()

            for widget_id, schedule in list(self.schedules.items()):
                last_refresh = schedule['last_refresh']
                interval = schedule['interval']

                if (now - last_refresh).total_seconds() >= interval:
                    # Trigger refresh
                    try:
                        callback = schedule['callback']
                        if asyncio.iscoroutinefunction(callback):
                            await callback(widget_id)
                        else:
                            callback(widget_id)

                        schedule['last_refresh'] = now
                    except Exception as e:
                        print(f"Refresh callback failed for {widget_id}: {e}")

            await asyncio.sleep(1)

    def stop(self):
        """Stop the scheduler"""
        self.is_running = False
