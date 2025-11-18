"""
NEXUS Dashboard Builder - Layouts Module
Flexible grid-based layout system with responsive design
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json


class LayoutType(Enum):
    """Layout types"""
    GRID = "grid"
    FIXED = "fixed"
    FLOW = "flow"
    CUSTOM = "custom"


class Breakpoint(Enum):
    """Responsive breakpoints"""
    XS = "xs"  # < 576px
    SM = "sm"  # >= 576px
    MD = "md"  # >= 768px
    LG = "lg"  # >= 992px
    XL = "xl"  # >= 1200px
    XXL = "xxl"  # >= 1600px


@dataclass
class GridConfig:
    """Grid configuration"""
    columns: int = 12
    row_height: int = 60
    max_rows: Optional[int] = None
    container_padding: Tuple[int, int] = (10, 10)
    widget_margin: Tuple[int, int] = (10, 10)
    is_resizable: bool = True
    is_draggable: bool = True
    prevent_collision: bool = True
    compact_type: str = "vertical"  # vertical, horizontal, none

    def to_dict(self) -> Dict[str, Any]:
        return {
            'columns': self.columns,
            'row_height': self.row_height,
            'max_rows': self.max_rows,
            'container_padding': list(self.container_padding),
            'widget_margin': list(self.widget_margin),
            'is_resizable': self.is_resizable,
            'is_draggable': self.is_draggable,
            'prevent_collision': self.prevent_collision,
            'compact_type': self.compact_type
        }


@dataclass
class ResponsiveLayout:
    """Responsive layout configuration for different breakpoints"""
    layouts: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)

    def set_layout(self, breakpoint: Breakpoint, layout: List[Dict[str, Any]]):
        """Set layout for a breakpoint"""
        self.layouts[breakpoint.value] = layout

    def get_layout(self, breakpoint: Breakpoint) -> List[Dict[str, Any]]:
        """Get layout for a breakpoint"""
        return self.layouts.get(breakpoint.value, [])

    def to_dict(self) -> Dict[str, Any]:
        return self.layouts


class LayoutManager:
    """Manages dashboard layouts"""

    def __init__(self):
        self.layout_type = LayoutType.GRID
        self.grid_config = GridConfig()
        self.responsive_layouts = ResponsiveLayout()
        self.current_breakpoint = Breakpoint.LG

    def set_grid_config(self, config: GridConfig):
        """Set grid configuration"""
        self.grid_config = config

    def optimize_layout(self, widgets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Optimize widget positions to minimize empty space"""
        if self.grid_config.compact_type == "vertical":
            return self._compact_vertical(widgets)
        elif self.grid_config.compact_type == "horizontal":
            return self._compact_horizontal(widgets)
        return widgets

    def _compact_vertical(self, widgets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Compact widgets vertically"""
        sorted_widgets = sorted(widgets, key=lambda w: (w['y'], w['x']))
        compacted = []

        for widget in sorted_widgets:
            # Find the highest available position
            min_y = 0
            for placed in compacted:
                if self._widgets_overlap_horizontally(widget, placed):
                    min_y = max(min_y, placed['y'] + placed['h'])

            widget['y'] = min_y
            compacted.append(widget)

        return compacted

    def _compact_horizontal(self, widgets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Compact widgets horizontally"""
        sorted_widgets = sorted(widgets, key=lambda w: (w['x'], w['y']))
        compacted = []

        for widget in sorted_widgets:
            min_x = 0
            for placed in compacted:
                if self._widgets_overlap_vertically(widget, placed):
                    min_x = max(min_x, placed['x'] + placed['w'])

            widget['x'] = min_x
            compacted.append(widget)

        return compacted

    def _widgets_overlap_horizontally(self, w1: Dict[str, Any], w2: Dict[str, Any]) -> bool:
        """Check if widgets overlap horizontally"""
        return not (w1['x'] + w1['w'] <= w2['x'] or w2['x'] + w2['w'] <= w1['x'])

    def _widgets_overlap_vertically(self, w1: Dict[str, Any], w2: Dict[str, Any]) -> bool:
        """Check if widgets overlap vertically"""
        return not (w1['y'] + w1['h'] <= w2['y'] or w2['y'] + w2['h'] <= w1['y'])

    def generate_responsive_layouts(self, base_layout: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Generate responsive layouts from base layout"""
        layouts = {}

        # Generate layouts for different breakpoints
        layouts[Breakpoint.XL.value] = base_layout
        layouts[Breakpoint.LG.value] = self._scale_layout(base_layout, 12)
        layouts[Breakpoint.MD.value] = self._scale_layout(base_layout, 10)
        layouts[Breakpoint.SM.value] = self._scale_layout(base_layout, 6)
        layouts[Breakpoint.XS.value] = self._stack_layout(base_layout)

        return layouts

    def _scale_layout(self, layout: List[Dict[str, Any]], columns: int) -> List[Dict[str, Any]]:
        """Scale layout to different column count"""
        scale_factor = columns / self.grid_config.columns

        scaled = []
        for widget in layout:
            scaled_widget = widget.copy()
            scaled_widget['x'] = int(widget['x'] * scale_factor)
            scaled_widget['w'] = max(1, int(widget['w'] * scale_factor))
            scaled.append(scaled_widget)

        return scaled

    def _stack_layout(self, layout: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Stack all widgets vertically for mobile"""
        stacked = []
        current_y = 0

        for widget in sorted(layout, key=lambda w: (w['y'], w['x'])):
            stacked_widget = widget.copy()
            stacked_widget['x'] = 0
            stacked_widget['y'] = current_y
            stacked_widget['w'] = self.grid_config.columns
            current_y += widget['h']
            stacked.append(stacked_widget)

        return stacked

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'layout_type': self.layout_type.value,
            'grid_config': self.grid_config.to_dict(),
            'responsive_layouts': self.responsive_layouts.to_dict(),
            'current_breakpoint': self.current_breakpoint.value
        }
