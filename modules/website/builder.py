"""
Website Builder - Core drag-drop builder logic and visual editor
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Literal
from enum import Enum
from datetime import datetime
import json
import uuid


class DeviceType(Enum):
    """Device types for responsive preview"""
    DESKTOP = "desktop"
    TABLET = "tablet"
    MOBILE = "mobile"


class BuilderMode(Enum):
    """Builder editing modes"""
    DESIGN = "design"
    PREVIEW = "preview"
    CODE = "code"


@dataclass
class BuilderConfig:
    """Configuration for website builder"""
    project_id: str
    project_name: str
    auto_save: bool = True
    auto_save_interval: int = 30  # seconds
    enable_responsive: bool = True
    enable_animations: bool = True
    enable_custom_css: bool = True
    enable_custom_js: bool = False
    max_pages: int = 100
    max_components_per_page: int = 500
    default_theme: str = "modern"

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "auto_save": self.auto_save,
            "auto_save_interval": self.auto_save_interval,
            "enable_responsive": self.enable_responsive,
            "enable_animations": self.enable_animations,
            "enable_custom_css": self.enable_custom_css,
            "enable_custom_js": self.enable_custom_js,
            "max_pages": self.max_pages,
            "max_components_per_page": self.max_components_per_page,
            "default_theme": self.default_theme,
        }


@dataclass
class ComponentState:
    """State of a component in the builder"""
    component_id: str
    component_type: str
    position: Dict[str, int]  # x, y, width, height
    properties: Dict[str, Any]
    styles: Dict[str, str]
    children: List['ComponentState'] = field(default_factory=list)
    parent_id: Optional[str] = None
    locked: bool = False
    hidden: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "component_id": self.component_id,
            "component_type": self.component_type,
            "position": self.position,
            "properties": self.properties,
            "styles": self.styles,
            "children": [child.to_dict() for child in self.children],
            "parent_id": self.parent_id,
            "locked": self.locked,
            "hidden": self.hidden,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ComponentState':
        """Create from dictionary"""
        children_data = data.get("children", [])
        children = [cls.from_dict(child) for child in children_data]

        return cls(
            component_id=data["component_id"],
            component_type=data["component_type"],
            position=data["position"],
            properties=data["properties"],
            styles=data["styles"],
            children=children,
            parent_id=data.get("parent_id"),
            locked=data.get("locked", False),
            hidden=data.get("hidden", False),
        )


@dataclass
class BuilderState:
    """Current state of the builder"""
    page_id: str
    components: List[ComponentState] = field(default_factory=list)
    selected_component_id: Optional[str] = None
    device_type: DeviceType = DeviceType.DESKTOP
    mode: BuilderMode = BuilderMode.DESIGN
    zoom_level: float = 1.0
    grid_enabled: bool = True
    snap_to_grid: bool = True
    history: List[Dict[str, Any]] = field(default_factory=list)
    history_index: int = -1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "page_id": self.page_id,
            "components": [c.to_dict() for c in self.components],
            "selected_component_id": self.selected_component_id,
            "device_type": self.device_type.value,
            "mode": self.mode.value,
            "zoom_level": self.zoom_level,
            "grid_enabled": self.grid_enabled,
            "snap_to_grid": self.snap_to_grid,
            "history_index": self.history_index,
        }


class WebsiteBuilder:
    """Main website builder class with drag-drop functionality"""

    def __init__(self, config: BuilderConfig):
        self.config = config
        self.state: Optional[BuilderState] = None
        self.last_save: Optional[datetime] = None
        self._clipboard: Optional[ComponentState] = None

    def create_project(self) -> Dict[str, Any]:
        """Create a new website project"""
        return {
            "project_id": self.config.project_id,
            "project_name": self.config.project_name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "config": self.config.to_dict(),
            "pages": [],
            "assets": [],
            "theme": self.config.default_theme,
        }

    def initialize_builder(self, page_id: str) -> BuilderState:
        """Initialize builder for a specific page"""
        self.state = BuilderState(page_id=page_id)
        return self.state

    def add_component(
        self,
        component_type: str,
        position: Dict[str, int],
        properties: Optional[Dict[str, Any]] = None,
        styles: Optional[Dict[str, str]] = None,
        parent_id: Optional[str] = None,
    ) -> ComponentState:
        """Add a component to the canvas"""
        if not self.state:
            raise ValueError("Builder not initialized")

        component = ComponentState(
            component_id=str(uuid.uuid4()),
            component_type=component_type,
            position=position,
            properties=properties or {},
            styles=styles or {},
            parent_id=parent_id,
        )

        if parent_id:
            parent = self._find_component(parent_id)
            if parent:
                parent.children.append(component)
        else:
            self.state.components.append(component)

        self._save_to_history("add_component", component.to_dict())
        return component

    def remove_component(self, component_id: str) -> bool:
        """Remove a component from the canvas"""
        if not self.state:
            return False

        component = self._find_component(component_id)
        if not component:
            return False

        if component.locked:
            return False

        self._save_to_history("remove_component", component.to_dict())

        if component.parent_id:
            parent = self._find_component(component.parent_id)
            if parent:
                parent.children = [c for c in parent.children if c.component_id != component_id]
        else:
            self.state.components = [c for c in self.state.components if c.component_id != component_id]

        return True

    def update_component(
        self,
        component_id: str,
        position: Optional[Dict[str, int]] = None,
        properties: Optional[Dict[str, Any]] = None,
        styles: Optional[Dict[str, str]] = None,
    ) -> Optional[ComponentState]:
        """Update component properties"""
        component = self._find_component(component_id)
        if not component or component.locked:
            return None

        old_state = component.to_dict()

        if position:
            component.position = position
        if properties:
            component.properties.update(properties)
        if styles:
            component.styles.update(styles)

        self._save_to_history("update_component", {
            "old": old_state,
            "new": component.to_dict(),
        })

        return component

    def move_component(self, component_id: str, x: int, y: int) -> Optional[ComponentState]:
        """Move a component to a new position"""
        component = self._find_component(component_id)
        if not component or component.locked:
            return None

        if self.state and self.state.snap_to_grid:
            x = (x // 10) * 10
            y = (y // 10) * 10

        component.position["x"] = x
        component.position["y"] = y

        return component

    def resize_component(
        self,
        component_id: str,
        width: int,
        height: int
    ) -> Optional[ComponentState]:
        """Resize a component"""
        component = self._find_component(component_id)
        if not component or component.locked:
            return None

        if self.state and self.state.snap_to_grid:
            width = (width // 10) * 10
            height = (height // 10) * 10

        component.position["width"] = max(width, 50)  # Minimum width
        component.position["height"] = max(height, 30)  # Minimum height

        return component

    def duplicate_component(self, component_id: str) -> Optional[ComponentState]:
        """Duplicate a component"""
        component = self._find_component(component_id)
        if not component:
            return None

        new_component = ComponentState(
            component_id=str(uuid.uuid4()),
            component_type=component.component_type,
            position={
                "x": component.position["x"] + 20,
                "y": component.position["y"] + 20,
                "width": component.position["width"],
                "height": component.position["height"],
            },
            properties=component.properties.copy(),
            styles=component.styles.copy(),
            parent_id=component.parent_id,
        )

        if component.parent_id:
            parent = self._find_component(component.parent_id)
            if parent:
                parent.children.append(new_component)
        else:
            if self.state:
                self.state.components.append(new_component)

        self._save_to_history("duplicate_component", new_component.to_dict())
        return new_component

    def copy_component(self, component_id: str) -> bool:
        """Copy component to clipboard"""
        component = self._find_component(component_id)
        if not component:
            return False

        self._clipboard = component
        return True

    def paste_component(self) -> Optional[ComponentState]:
        """Paste component from clipboard"""
        if not self._clipboard or not self.state:
            return None

        return self.duplicate_component(self._clipboard.component_id)

    def select_component(self, component_id: str) -> bool:
        """Select a component"""
        if not self.state:
            return False

        component = self._find_component(component_id)
        if not component:
            return False

        self.state.selected_component_id = component_id
        return True

    def deselect_component(self) -> None:
        """Deselect current component"""
        if self.state:
            self.state.selected_component_id = None

    def lock_component(self, component_id: str) -> bool:
        """Lock a component to prevent editing"""
        component = self._find_component(component_id)
        if not component:
            return False

        component.locked = True
        return True

    def unlock_component(self, component_id: str) -> bool:
        """Unlock a component"""
        component = self._find_component(component_id)
        if not component:
            return False

        component.locked = False
        return True

    def toggle_component_visibility(self, component_id: str) -> bool:
        """Toggle component visibility"""
        component = self._find_component(component_id)
        if not component:
            return False

        component.hidden = not component.hidden
        return True

    def set_device_type(self, device_type: DeviceType) -> None:
        """Set preview device type"""
        if self.state:
            self.state.device_type = device_type

    def set_builder_mode(self, mode: BuilderMode) -> None:
        """Set builder mode"""
        if self.state:
            self.state.mode = mode

    def set_zoom_level(self, zoom: float) -> None:
        """Set canvas zoom level"""
        if self.state:
            self.state.zoom_level = max(0.25, min(zoom, 4.0))

    def toggle_grid(self) -> None:
        """Toggle grid visibility"""
        if self.state:
            self.state.grid_enabled = not self.state.grid_enabled

    def toggle_snap_to_grid(self) -> None:
        """Toggle snap to grid"""
        if self.state:
            self.state.snap_to_grid = not self.state.snap_to_grid

    def undo(self) -> bool:
        """Undo last action"""
        if not self.state or self.state.history_index < 0:
            return False

        self.state.history_index -= 1
        self._restore_from_history()
        return True

    def redo(self) -> bool:
        """Redo last undone action"""
        if not self.state or self.state.history_index >= len(self.state.history) - 1:
            return False

        self.state.history_index += 1
        self._restore_from_history()
        return True

    def get_html_output(self) -> str:
        """Generate HTML output for the current page"""
        if not self.state:
            return ""

        html_parts = ['<!DOCTYPE html>\n<html lang="en">\n<head>\n']
        html_parts.append('    <meta charset="UTF-8">\n')
        html_parts.append('    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n')
        html_parts.append('    <title>NEXUS Website</title>\n')
        html_parts.append('</head>\n<body>\n')

        for component in self.state.components:
            html_parts.append(self._component_to_html(component))

        html_parts.append('</body>\n</html>')
        return ''.join(html_parts)

    def get_css_output(self) -> str:
        """Generate CSS output for the current page"""
        if not self.state:
            return ""

        css_parts = []
        for component in self.state.components:
            css_parts.append(self._component_to_css(component))

        return '\n'.join(css_parts)

    def save_state(self) -> Dict[str, Any]:
        """Save current builder state"""
        if not self.state:
            return {}

        self.last_save = datetime.now()
        return {
            "state": self.state.to_dict(),
            "saved_at": self.last_save.isoformat(),
        }

    def load_state(self, saved_data: Dict[str, Any]) -> bool:
        """Load builder state from saved data"""
        try:
            state_data = saved_data["state"]
            self.state = BuilderState(
                page_id=state_data["page_id"],
                components=[ComponentState.from_dict(c) for c in state_data["components"]],
                selected_component_id=state_data.get("selected_component_id"),
                device_type=DeviceType(state_data.get("device_type", "desktop")),
                mode=BuilderMode(state_data.get("mode", "design")),
                zoom_level=state_data.get("zoom_level", 1.0),
                grid_enabled=state_data.get("grid_enabled", True),
                snap_to_grid=state_data.get("snap_to_grid", True),
            )
            return True
        except Exception:
            return False

    def _find_component(self, component_id: str) -> Optional[ComponentState]:
        """Find a component by ID"""
        if not self.state:
            return None

        def search(components: List[ComponentState]) -> Optional[ComponentState]:
            for component in components:
                if component.component_id == component_id:
                    return component
                if component.children:
                    result = search(component.children)
                    if result:
                        return result
            return None

        return search(self.state.components)

    def _save_to_history(self, action: str, data: Dict[str, Any]) -> None:
        """Save action to history for undo/redo"""
        if not self.state:
            return

        # Remove any history after current index
        if self.state.history_index < len(self.state.history) - 1:
            self.state.history = self.state.history[:self.state.history_index + 1]

        # Add new history entry
        self.state.history.append({
            "action": action,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        })

        self.state.history_index = len(self.state.history) - 1

        # Limit history size
        if len(self.state.history) > 100:
            self.state.history = self.state.history[-100:]
            self.state.history_index = 99

    def _restore_from_history(self) -> None:
        """Restore state from history"""
        # Implementation depends on the specific action type
        pass

    def _component_to_html(self, component: ComponentState, indent: int = 1) -> str:
        """Convert component to HTML"""
        indent_str = "    " * indent
        html = f'{indent_str}<div id="{component.component_id}" class="{component.component_type}">\n'

        # Add content based on component type
        if "content" in component.properties:
            html += f'{indent_str}    {component.properties["content"]}\n'

        # Add children
        for child in component.children:
            html += self._component_to_html(child, indent + 1)

        html += f'{indent_str}</div>\n'
        return html

    def _component_to_css(self, component: ComponentState) -> str:
        """Convert component styles to CSS"""
        if not component.styles:
            return ""

        css = f'#{component.component_id} {{\n'
        for prop, value in component.styles.items():
            css += f'    {prop}: {value};\n'
        css += '}\n'

        # Add children CSS
        for child in component.children:
            css += self._component_to_css(child)

        return css
