"""
NEXUS Dashboard Builder - Main Builder Module
Enterprise-grade dashboard builder with drag-drop interface and real-time updates
Rivals: Grafana, Metabase, Tableau
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid


class DashboardTheme(Enum):
    """Dashboard themes"""
    LIGHT = "light"
    DARK = "dark"
    BLUE = "blue"
    CUSTOM = "custom"


class RefreshInterval(Enum):
    """Auto-refresh intervals"""
    NONE = 0
    FIVE_SECONDS = 5
    TEN_SECONDS = 10
    THIRTY_SECONDS = 30
    ONE_MINUTE = 60
    FIVE_MINUTES = 300
    TEN_MINUTES = 600
    THIRTY_MINUTES = 1800
    ONE_HOUR = 3600


@dataclass
class GridPosition:
    """Position and size in grid system"""
    x: int
    y: int
    width: int
    height: int
    min_width: int = 1
    min_height: int = 1
    max_width: Optional[int] = None
    max_height: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DashboardWidget:
    """Represents a widget on the dashboard"""
    widget_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    widget_type: str = "chart"
    title: str = ""
    position: GridPosition = field(default_factory=lambda: GridPosition(0, 0, 4, 4))
    config: Dict[str, Any] = field(default_factory=dict)
    data_source: str = ""
    query: str = ""
    refresh_enabled: bool = False
    refresh_interval: int = 60
    filters: List[str] = field(default_factory=list)
    drill_down_enabled: bool = False
    drill_down_target: Optional[str] = None
    visible: bool = True
    locked: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'widget_id': self.widget_id,
            'widget_type': self.widget_type,
            'title': self.title,
            'position': self.position.to_dict(),
            'config': self.config,
            'data_source': self.data_source,
            'query': self.query,
            'refresh_enabled': self.refresh_enabled,
            'refresh_interval': self.refresh_interval,
            'filters': self.filters,
            'drill_down_enabled': self.drill_down_enabled,
            'drill_down_target': self.drill_down_target,
            'visible': self.visible,
            'locked': self.locked
        }


@dataclass
class DashboardFilter:
    """Global dashboard filter"""
    filter_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    filter_type: str = "dropdown"  # dropdown, multiselect, date_range, text
    options: List[Any] = field(default_factory=list)
    default_value: Any = None
    current_value: Any = None
    applies_to: List[str] = field(default_factory=list)  # Widget IDs
    visible: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DashboardAlert:
    """Dashboard alert configuration"""
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    widget_id: str = ""
    condition: str = ""  # e.g., "value > 100"
    threshold: float = 0.0
    comparison: str = "greater_than"  # greater_than, less_than, equals, etc.
    notification_channel: str = "email"
    recipients: List[str] = field(default_factory=list)
    enabled: bool = True
    last_triggered: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.last_triggered:
            data['last_triggered'] = self.last_triggered.isoformat()
        return data


class DashboardBuilder:
    """
    Main dashboard builder class with full functionality
    Features:
    - Drag-drop interface support
    - Real-time data updates
    - Custom layouts
    - KPIs, charts, tables
    - Filters and drill-down
    - Themes and responsive design
    - Sharing and embeds
    - Alerts
    """

    def __init__(self, dashboard_id: Optional[str] = None):
        self.dashboard_id = dashboard_id or str(uuid.uuid4())
        self.name = "New Dashboard"
        self.description = ""
        self.theme = DashboardTheme.LIGHT
        self.widgets: List[DashboardWidget] = []
        self.filters: List[DashboardFilter] = []
        self.alerts: List[DashboardAlert] = []
        self.layout_config: Dict[str, Any] = {
            "columns": 12,
            "row_height": 60,
            "container_padding": [10, 10],
            "widget_margin": [10, 10],
            "responsive": True
        }
        self.refresh_interval = RefreshInterval.NONE
        self.auto_refresh_enabled = False
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.created_by = "admin"
        self.tags: List[str] = []
        self.is_public = False
        self.is_published = False
        self.permissions: Dict[str, List[str]] = {
            "view": ["*"],
            "edit": ["admin"],
            "delete": ["admin"]
        }

        # Version control
        self.version = 1
        self.versions: List[Dict[str, Any]] = []

        # Sharing settings
        self.share_token: Optional[str] = None
        self.embed_enabled = False
        self.embed_code: Optional[str] = None

    def add_widget(self, widget: DashboardWidget) -> str:
        """Add a widget to the dashboard"""
        # Check for position conflicts
        if not self._check_position_available(widget.position):
            # Find next available position
            widget.position = self._find_next_available_position(
                widget.position.width,
                widget.position.height
            )

        self.widgets.append(widget)
        self.updated_at = datetime.now()
        return widget.widget_id

    def remove_widget(self, widget_id: str) -> bool:
        """Remove a widget from the dashboard"""
        for i, widget in enumerate(self.widgets):
            if widget.widget_id == widget_id:
                self.widgets.pop(i)
                self.updated_at = datetime.now()
                return True
        return False

    def update_widget(self, widget_id: str, updates: Dict[str, Any]) -> bool:
        """Update a widget's properties"""
        for widget in self.widgets:
            if widget.widget_id == widget_id:
                for key, value in updates.items():
                    if hasattr(widget, key):
                        setattr(widget, key, value)
                self.updated_at = datetime.now()
                return True
        return False

    def move_widget(self, widget_id: str, new_position: GridPosition) -> bool:
        """Move a widget to a new position"""
        for widget in self.widgets:
            if widget.widget_id == widget_id:
                if widget.locked:
                    return False

                if self._check_position_available(new_position, exclude_widget_id=widget_id):
                    widget.position = new_position
                    self.updated_at = datetime.now()
                    return True
        return False

    def resize_widget(self, widget_id: str, width: int, height: int) -> bool:
        """Resize a widget"""
        for widget in self.widgets:
            if widget.widget_id == widget_id:
                if widget.locked:
                    return False

                # Check constraints
                if width < widget.position.min_width or height < widget.position.min_height:
                    return False

                if widget.position.max_width and width > widget.position.max_width:
                    return False

                if widget.position.max_height and height > widget.position.max_height:
                    return False

                new_position = GridPosition(
                    x=widget.position.x,
                    y=widget.position.y,
                    width=width,
                    height=height,
                    min_width=widget.position.min_width,
                    min_height=widget.position.min_height,
                    max_width=widget.position.max_width,
                    max_height=widget.position.max_height
                )

                if self._check_position_available(new_position, exclude_widget_id=widget_id):
                    widget.position = new_position
                    self.updated_at = datetime.now()
                    return True
        return False

    def duplicate_widget(self, widget_id: str) -> Optional[str]:
        """Duplicate a widget"""
        for widget in self.widgets:
            if widget.widget_id == widget_id:
                new_widget = DashboardWidget(
                    widget_type=widget.widget_type,
                    title=f"{widget.title} (Copy)",
                    position=GridPosition(
                        x=widget.position.x + 1,
                        y=widget.position.y + 1,
                        width=widget.position.width,
                        height=widget.position.height
                    ),
                    config=widget.config.copy(),
                    data_source=widget.data_source,
                    query=widget.query,
                    refresh_enabled=widget.refresh_enabled,
                    refresh_interval=widget.refresh_interval
                )
                return self.add_widget(new_widget)
        return None

    def lock_widget(self, widget_id: str) -> bool:
        """Lock a widget to prevent modifications"""
        return self.update_widget(widget_id, {'locked': True})

    def unlock_widget(self, widget_id: str) -> bool:
        """Unlock a widget"""
        return self.update_widget(widget_id, {'locked': False})

    def add_filter(self, filter: DashboardFilter) -> str:
        """Add a global filter"""
        self.filters.append(filter)
        self.updated_at = datetime.now()
        return filter.filter_id

    def remove_filter(self, filter_id: str) -> bool:
        """Remove a filter"""
        for i, filter in enumerate(self.filters):
            if filter.filter_id == filter_id:
                self.filters.pop(i)
                self.updated_at = datetime.now()
                return True
        return False

    def apply_filter(self, filter_id: str, value: Any) -> bool:
        """Apply a filter value"""
        for filter in self.filters:
            if filter.filter_id == filter_id:
                filter.current_value = value
                self.updated_at = datetime.now()
                return True
        return False

    def add_alert(self, alert: DashboardAlert) -> str:
        """Add an alert"""
        self.alerts.append(alert)
        self.updated_at = datetime.now()
        return alert.alert_id

    def remove_alert(self, alert_id: str) -> bool:
        """Remove an alert"""
        for i, alert in enumerate(self.alerts):
            if alert.alert_id == alert_id:
                self.alerts.pop(i)
                self.updated_at = datetime.now()
                return True
        return False

    def set_theme(self, theme: DashboardTheme):
        """Set dashboard theme"""
        self.theme = theme
        self.updated_at = datetime.now()

    def set_refresh_interval(self, interval: RefreshInterval):
        """Set auto-refresh interval"""
        self.refresh_interval = interval
        self.auto_refresh_enabled = interval != RefreshInterval.NONE
        self.updated_at = datetime.now()

    def enable_sharing(self) -> str:
        """Enable dashboard sharing and generate share token"""
        if not self.share_token:
            self.share_token = str(uuid.uuid4())
        return self.share_token

    def disable_sharing(self):
        """Disable dashboard sharing"""
        self.share_token = None

    def enable_embed(self) -> str:
        """Enable embedding and generate embed code"""
        if not self.share_token:
            self.enable_sharing()

        self.embed_enabled = True
        self.embed_code = f'''<iframe
            src="https://nexus.example.com/embed/dashboard/{self.dashboard_id}?token={self.share_token}"
            width="100%"
            height="800"
            frameborder="0"
        ></iframe>'''

        return self.embed_code

    def disable_embed(self):
        """Disable embedding"""
        self.embed_enabled = False
        self.embed_code = None

    def publish(self):
        """Publish the dashboard"""
        self.is_published = True
        self.updated_at = datetime.now()

    def unpublish(self):
        """Unpublish the dashboard"""
        self.is_published = False
        self.updated_at = datetime.now()

    def create_version(self, comment: str = "") -> int:
        """Create a new version snapshot"""
        version_data = {
            'version': self.version,
            'created_at': datetime.now().isoformat(),
            'comment': comment,
            'dashboard_state': self.to_dict()
        }

        self.versions.append(version_data)
        self.version += 1
        return self.version - 1

    def restore_version(self, version: int) -> bool:
        """Restore a previous version"""
        for version_data in self.versions:
            if version_data['version'] == version:
                self._load_from_dict(version_data['dashboard_state'])
                return True
        return False

    def auto_layout(self):
        """Automatically arrange widgets in optimal layout"""
        # Simple auto-layout: arrange widgets in grid from top-left
        current_x = 0
        current_y = 0
        max_columns = self.layout_config['columns']

        for widget in self.widgets:
            if widget.locked:
                continue

            # Move to next row if widget doesn't fit
            if current_x + widget.position.width > max_columns:
                current_x = 0
                current_y += 4  # Default row height

            widget.position.x = current_x
            widget.position.y = current_y

            current_x += widget.position.width

        self.updated_at = datetime.now()

    def _check_position_available(self, position: GridPosition, exclude_widget_id: Optional[str] = None) -> bool:
        """Check if a position is available (no overlaps)"""
        for widget in self.widgets:
            if exclude_widget_id and widget.widget_id == exclude_widget_id:
                continue

            # Check for overlap
            if not (position.x + position.width <= widget.position.x or
                   widget.position.x + widget.position.width <= position.x or
                   position.y + position.height <= widget.position.y or
                   widget.position.y + widget.position.height <= position.y):
                return False

        return True

    def _find_next_available_position(self, width: int, height: int) -> GridPosition:
        """Find next available position for a widget"""
        max_columns = self.layout_config['columns']

        # Try to find an empty spot
        for y in range(0, 100, height):  # Arbitrary max of 100 rows
            for x in range(0, max_columns - width + 1):
                pos = GridPosition(x, y, width, height)
                if self._check_position_available(pos):
                    return pos

        # If no spot found, place at end
        max_y = max([w.position.y + w.position.height for w in self.widgets], default=0)
        return GridPosition(0, max_y, width, height)

    def get_widget_data(self, widget_id: str) -> Optional[Dict[str, Any]]:
        """Get data for a specific widget"""
        # Placeholder - would fetch from data source
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert dashboard to dictionary"""
        return {
            'dashboard_id': self.dashboard_id,
            'name': self.name,
            'description': self.description,
            'theme': self.theme.value,
            'widgets': [w.to_dict() for w in self.widgets],
            'filters': [f.to_dict() for f in self.filters],
            'alerts': [a.to_dict() for a in self.alerts],
            'layout_config': self.layout_config,
            'refresh_interval': self.refresh_interval.value,
            'auto_refresh_enabled': self.auto_refresh_enabled,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'created_by': self.created_by,
            'tags': self.tags,
            'is_public': self.is_public,
            'is_published': self.is_published,
            'permissions': self.permissions,
            'version': self.version,
            'share_token': self.share_token,
            'embed_enabled': self.embed_enabled,
            'embed_code': self.embed_code
        }

    def to_json(self) -> str:
        """Convert dashboard to JSON"""
        return json.dumps(self.to_dict(), indent=2)

    def _load_from_dict(self, data: Dict[str, Any]):
        """Load dashboard from dictionary"""
        self.dashboard_id = data['dashboard_id']
        self.name = data['name']
        self.description = data.get('description', '')
        self.theme = DashboardTheme(data.get('theme', 'light'))

        # Load widgets
        self.widgets = [
            DashboardWidget(
                widget_id=w['widget_id'],
                widget_type=w['widget_type'],
                title=w['title'],
                position=GridPosition(**w['position']),
                config=w['config'],
                data_source=w.get('data_source', ''),
                query=w.get('query', ''),
                refresh_enabled=w.get('refresh_enabled', False),
                refresh_interval=w.get('refresh_interval', 60)
            )
            for w in data.get('widgets', [])
        ]

        self.layout_config = data.get('layout_config', {})
        self.created_at = datetime.fromisoformat(data['created_at'])
        self.updated_at = datetime.fromisoformat(data['updated_at'])

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DashboardBuilder':
        """Create dashboard from dictionary"""
        dashboard = cls(dashboard_id=data['dashboard_id'])
        dashboard._load_from_dict(data)
        return dashboard

    @classmethod
    def from_json(cls, json_str: str) -> 'DashboardBuilder':
        """Create dashboard from JSON"""
        data = json.loads(json_str)
        return cls.from_dict(data)
