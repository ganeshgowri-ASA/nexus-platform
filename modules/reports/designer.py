"""
NEXUS Reports Builder - Report Designer Module
Enterprise-grade report designer with drag-drop interface, custom layouts, and versioning
Rivals: Crystal Reports, Power BI, Tableau
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid


class ReportElementType(Enum):
    """Types of elements that can be added to a report"""
    TEXT = "text"
    IMAGE = "image"
    CHART = "chart"
    TABLE = "table"
    FILTER = "filter"
    PARAMETER = "parameter"
    SUBREPORT = "subreport"
    CALCULATED_FIELD = "calculated_field"
    HEADER = "header"
    FOOTER = "footer"
    PAGE_NUMBER = "page_number"
    DATE_TIME = "date_time"


class PageOrientation(Enum):
    """Page orientation options"""
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


class PageSize(Enum):
    """Standard page sizes"""
    A4 = "A4"
    LETTER = "Letter"
    LEGAL = "Legal"
    TABLOID = "Tabloid"
    A3 = "A3"
    CUSTOM = "Custom"


@dataclass
class ReportElement:
    """Represents a single element in the report"""
    id: str
    type: ReportElementType
    x: float
    y: float
    width: float
    height: float
    properties: Dict[str, Any]
    z_index: int = 0

    def to_dict(self):
        data = asdict(self)
        data['type'] = self.type.value
        return data


@dataclass
class PageSettings:
    """Page layout settings"""
    size: PageSize = PageSize.A4
    orientation: PageOrientation = PageOrientation.PORTRAIT
    margin_top: float = 1.0
    margin_bottom: float = 1.0
    margin_left: float = 1.0
    margin_right: float = 1.0
    custom_width: Optional[float] = None
    custom_height: Optional[float] = None

    def to_dict(self):
        data = asdict(self)
        data['size'] = self.size.value
        data['orientation'] = self.orientation.value
        return data


@dataclass
class ReportVersion:
    """Tracks report versions for version control"""
    version: int
    created_by: str
    created_at: datetime
    changes: str
    report_definition: Dict[str, Any]

    def to_dict(self):
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data


class ReportDesigner:
    """
    Main report designer class with full visual editing capabilities
    Features:
    - Drag-drop interface support
    - Element positioning and sizing
    - Layering (z-index)
    - Version control
    - Undo/redo support
    - Template support
    """

    def __init__(self, report_id: Optional[str] = None):
        self.report_id = report_id or str(uuid.uuid4())
        self.name = "Untitled Report"
        self.description = ""
        self.elements: List[ReportElement] = []
        self.page_settings = PageSettings()
        self.versions: List[ReportVersion] = []
        self.current_version = 0
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.created_by = "admin"
        self.tags: List[str] = []
        self.permissions: Dict[str, List[str]] = {
            "view": ["*"],
            "edit": ["admin"],
            "delete": ["admin"]
        }

        # Undo/redo stack
        self._undo_stack: List[Dict[str, Any]] = []
        self._redo_stack: List[Dict[str, Any]] = []
        self._max_undo = 50

    def add_element(self, element: ReportElement) -> str:
        """Add an element to the report"""
        self._save_state_for_undo()
        self.elements.append(element)
        self.updated_at = datetime.now()
        return element.id

    def remove_element(self, element_id: str) -> bool:
        """Remove an element from the report"""
        self._save_state_for_undo()
        for i, elem in enumerate(self.elements):
            if elem.id == element_id:
                self.elements.pop(i)
                self.updated_at = datetime.now()
                return True
        return False

    def update_element(self, element_id: str, properties: Dict[str, Any]) -> bool:
        """Update an element's properties"""
        self._save_state_for_undo()
        for elem in self.elements:
            if elem.id == element_id:
                elem.properties.update(properties)
                self.updated_at = datetime.now()
                return True
        return False

    def move_element(self, element_id: str, x: float, y: float) -> bool:
        """Move an element to a new position"""
        self._save_state_for_undo()
        for elem in self.elements:
            if elem.id == element_id:
                elem.x = x
                elem.y = y
                self.updated_at = datetime.now()
                return True
        return False

    def resize_element(self, element_id: str, width: float, height: float) -> bool:
        """Resize an element"""
        self._save_state_for_undo()
        for elem in self.elements:
            if elem.id == element_id:
                elem.width = width
                elem.height = height
                self.updated_at = datetime.now()
                return True
        return False

    def change_z_index(self, element_id: str, z_index: int) -> bool:
        """Change the z-index (layer order) of an element"""
        self._save_state_for_undo()
        for elem in self.elements:
            if elem.id == element_id:
                elem.z_index = z_index
                self.updated_at = datetime.now()
                return True
        return False

    def bring_to_front(self, element_id: str) -> bool:
        """Bring an element to the front"""
        max_z = max([e.z_index for e in self.elements], default=0)
        return self.change_z_index(element_id, max_z + 1)

    def send_to_back(self, element_id: str) -> bool:
        """Send an element to the back"""
        min_z = min([e.z_index for e in self.elements], default=0)
        return self.change_z_index(element_id, min_z - 1)

    def duplicate_element(self, element_id: str) -> Optional[str]:
        """Duplicate an existing element"""
        for elem in self.elements:
            if elem.id == element_id:
                new_elem = ReportElement(
                    id=str(uuid.uuid4()),
                    type=elem.type,
                    x=elem.x + 10,
                    y=elem.y + 10,
                    width=elem.width,
                    height=elem.height,
                    properties=elem.properties.copy(),
                    z_index=elem.z_index + 1
                )
                return self.add_element(new_elem)
        return None

    def align_elements(self, element_ids: List[str], alignment: str) -> bool:
        """Align multiple elements (left, right, top, bottom, center)"""
        if not element_ids:
            return False

        self._save_state_for_undo()
        elements = [e for e in self.elements if e.id in element_ids]

        if alignment == "left":
            min_x = min(e.x for e in elements)
            for elem in elements:
                elem.x = min_x
        elif alignment == "right":
            max_x = max(e.x + e.width for e in elements)
            for elem in elements:
                elem.x = max_x - elem.width
        elif alignment == "top":
            min_y = min(e.y for e in elements)
            for elem in elements:
                elem.y = min_y
        elif alignment == "bottom":
            max_y = max(e.y + e.height for e in elements)
            for elem in elements:
                elem.y = max_y - elem.height
        elif alignment == "center_horizontal":
            center_x = sum(e.x + e.width / 2 for e in elements) / len(elements)
            for elem in elements:
                elem.x = center_x - elem.width / 2
        elif alignment == "center_vertical":
            center_y = sum(e.y + e.height / 2 for e in elements) / len(elements)
            for elem in elements:
                elem.y = center_y - elem.height / 2

        self.updated_at = datetime.now()
        return True

    def distribute_elements(self, element_ids: List[str], axis: str) -> bool:
        """Distribute elements evenly along an axis"""
        if len(element_ids) < 3:
            return False

        self._save_state_for_undo()
        elements = sorted(
            [e for e in self.elements if e.id in element_ids],
            key=lambda e: e.x if axis == "horizontal" else e.y
        )

        if axis == "horizontal":
            start = elements[0].x
            end = elements[-1].x + elements[-1].width
            total_width = sum(e.width for e in elements)
            gap = (end - start - total_width) / (len(elements) - 1)

            current_x = start
            for elem in elements:
                elem.x = current_x
                current_x += elem.width + gap
        else:  # vertical
            start = elements[0].y
            end = elements[-1].y + elements[-1].height
            total_height = sum(e.height for e in elements)
            gap = (end - start - total_height) / (len(elements) - 1)

            current_y = start
            for elem in elements:
                elem.y = current_y
                current_y += elem.height + gap

        self.updated_at = datetime.now()
        return True

    def update_page_settings(self, settings: Dict[str, Any]) -> bool:
        """Update page layout settings"""
        self._save_state_for_undo()
        if 'size' in settings:
            self.page_settings.size = PageSize(settings['size'])
        if 'orientation' in settings:
            self.page_settings.orientation = PageOrientation(settings['orientation'])
        if 'margin_top' in settings:
            self.page_settings.margin_top = settings['margin_top']
        if 'margin_bottom' in settings:
            self.page_settings.margin_bottom = settings['margin_bottom']
        if 'margin_left' in settings:
            self.page_settings.margin_left = settings['margin_left']
        if 'margin_right' in settings:
            self.page_settings.margin_right = settings['margin_right']

        self.updated_at = datetime.now()
        return True

    def create_version(self, created_by: str, changes: str) -> int:
        """Create a new version of the report"""
        version = ReportVersion(
            version=self.current_version + 1,
            created_by=created_by,
            created_at=datetime.now(),
            changes=changes,
            report_definition=self.to_dict()
        )
        self.versions.append(version)
        self.current_version = version.version
        return version.version

    def restore_version(self, version: int) -> bool:
        """Restore a specific version of the report"""
        for v in self.versions:
            if v.version == version:
                self._load_from_dict(v.report_definition)
                return True
        return False

    def get_version_history(self) -> List[Dict[str, Any]]:
        """Get the version history"""
        return [v.to_dict() for v in self.versions]

    def undo(self) -> bool:
        """Undo the last change"""
        if not self._undo_stack:
            return False

        current_state = self._get_state()
        self._redo_stack.append(current_state)

        previous_state = self._undo_stack.pop()
        self._load_state(previous_state)
        return True

    def redo(self) -> bool:
        """Redo the last undone change"""
        if not self._redo_stack:
            return False

        current_state = self._get_state()
        self._undo_stack.append(current_state)

        next_state = self._redo_stack.pop()
        self._load_state(next_state)
        return True

    def _save_state_for_undo(self):
        """Save current state for undo"""
        state = self._get_state()
        self._undo_stack.append(state)
        if len(self._undo_stack) > self._max_undo:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def _get_state(self) -> Dict[str, Any]:
        """Get current state"""
        return {
            'elements': [e.to_dict() for e in self.elements],
            'page_settings': self.page_settings.to_dict()
        }

    def _load_state(self, state: Dict[str, Any]):
        """Load state"""
        self.elements = [
            ReportElement(
                id=e['id'],
                type=ReportElementType(e['type']),
                x=e['x'],
                y=e['y'],
                width=e['width'],
                height=e['height'],
                properties=e['properties'],
                z_index=e.get('z_index', 0)
            )
            for e in state['elements']
        ]
        ps = state['page_settings']
        self.page_settings = PageSettings(
            size=PageSize(ps['size']),
            orientation=PageOrientation(ps['orientation']),
            margin_top=ps['margin_top'],
            margin_bottom=ps['margin_bottom'],
            margin_left=ps['margin_left'],
            margin_right=ps['margin_right']
        )

    def set_permissions(self, role: str, users: List[str]):
        """Set permissions for a role"""
        self.permissions[role] = users

    def check_permission(self, user: str, action: str) -> bool:
        """Check if a user has permission for an action"""
        if action not in self.permissions:
            return False
        users = self.permissions[action]
        return "*" in users or user in users

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary"""
        return {
            'report_id': self.report_id,
            'name': self.name,
            'description': self.description,
            'elements': [e.to_dict() for e in self.elements],
            'page_settings': self.page_settings.to_dict(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'created_by': self.created_by,
            'current_version': self.current_version,
            'tags': self.tags,
            'permissions': self.permissions
        }

    def to_json(self) -> str:
        """Convert report to JSON"""
        return json.dumps(self.to_dict(), indent=2)

    def _load_from_dict(self, data: Dict[str, Any]):
        """Load report from dictionary"""
        self.report_id = data['report_id']
        self.name = data['name']
        self.description = data.get('description', '')

        self.elements = [
            ReportElement(
                id=e['id'],
                type=ReportElementType(e['type']),
                x=e['x'],
                y=e['y'],
                width=e['width'],
                height=e['height'],
                properties=e['properties'],
                z_index=e.get('z_index', 0)
            )
            for e in data['elements']
        ]

        ps = data['page_settings']
        self.page_settings = PageSettings(
            size=PageSize(ps['size']),
            orientation=PageOrientation(ps['orientation']),
            margin_top=ps['margin_top'],
            margin_bottom=ps['margin_bottom'],
            margin_left=ps['margin_left'],
            margin_right=ps['margin_right']
        )

        self.created_at = datetime.fromisoformat(data['created_at'])
        self.updated_at = datetime.fromisoformat(data['updated_at'])
        self.created_by = data.get('created_by', 'admin')
        self.current_version = data.get('current_version', 0)
        self.tags = data.get('tags', [])
        self.permissions = data.get('permissions', {
            "view": ["*"],
            "edit": ["admin"],
            "delete": ["admin"]
        })

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReportDesigner':
        """Create report from dictionary"""
        report = cls(report_id=data['report_id'])
        report._load_from_dict(data)
        return report

    @classmethod
    def from_json(cls, json_str: str) -> 'ReportDesigner':
        """Create report from JSON"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def validate(self) -> List[str]:
        """Validate report and return list of errors"""
        errors = []

        if not self.name:
            errors.append("Report name is required")

        if not self.elements:
            errors.append("Report must contain at least one element")

        # Check for overlapping elements
        for i, elem1 in enumerate(self.elements):
            for elem2 in self.elements[i+1:]:
                if self._elements_overlap(elem1, elem2):
                    errors.append(f"Elements {elem1.id} and {elem2.id} overlap")

        return errors

    def _elements_overlap(self, elem1: ReportElement, elem2: ReportElement) -> bool:
        """Check if two elements overlap"""
        return not (elem1.x + elem1.width < elem2.x or
                   elem2.x + elem2.width < elem1.x or
                   elem1.y + elem1.height < elem2.y or
                   elem2.y + elem2.height < elem1.y)
