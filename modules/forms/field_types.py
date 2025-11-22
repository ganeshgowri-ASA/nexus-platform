"""
Field Types Module

Defines 20+ field types for form building with comprehensive configuration options.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from datetime import datetime
import uuid


class FieldType(Enum):
    """Enumeration of all available field types"""
    # Text inputs
    SHORT_TEXT = "short_text"
    LONG_TEXT = "long_text"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    NUMBER = "number"

    # Selection inputs
    DROPDOWN = "dropdown"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    MULTI_SELECT = "multi_select"

    # Date & Time
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"

    # File & Media
    FILE_UPLOAD = "file_upload"
    IMAGE_UPLOAD = "image_upload"

    # Rating & Feedback
    RATING = "rating"
    SCALE = "scale"
    NPS = "nps"  # Net Promoter Score
    SLIDER = "slider"

    # Advanced
    MATRIX = "matrix"
    RANKING = "ranking"
    SIGNATURE = "signature"
    LOCATION = "location"

    # Special
    SECTION_BREAK = "section_break"
    PAGE_BREAK = "page_break"
    CALCULATED = "calculated"
    HIDDEN = "hidden"


@dataclass
class FieldConfig:
    """Configuration options for a field"""
    # Basic settings
    placeholder: Optional[str] = None
    default_value: Optional[Any] = None
    help_text: Optional[str] = None

    # Validation
    required: bool = False
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None

    # Options for selection fields
    options: Optional[List[str]] = None
    allow_other: bool = False
    randomize_options: bool = False

    # File upload settings
    max_file_size: int = 10  # MB
    allowed_file_types: Optional[List[str]] = None
    max_files: int = 1

    # Rating/Scale settings
    min_rating: int = 1
    max_rating: int = 5
    rating_icon: str = "star"  # star, heart, thumbs, number
    scale_labels: Optional[Dict[int, str]] = None

    # Matrix settings
    rows: Optional[List[str]] = None
    columns: Optional[List[str]] = None

    # Calculation settings
    calculation_formula: Optional[str] = None

    # Display settings
    width: str = "full"  # full, half, third, quarter
    show_character_count: bool = False

    # Advanced
    conditional_visibility: Optional[Dict[str, Any]] = None
    piping_source: Optional[str] = None  # Field ID to pipe from


@dataclass
class Field:
    """Represents a form field"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    field_type: FieldType = FieldType.SHORT_TEXT
    label: str = ""
    description: Optional[str] = None
    config: FieldConfig = field(default_factory=FieldConfig)
    position: int = 0
    page: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert field to dictionary"""
        return {
            "id": self.id,
            "field_type": self.field_type.value,
            "label": self.label,
            "description": self.description,
            "config": self._config_to_dict(),
            "position": self.position,
            "page": self.page,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def _config_to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        config_dict = {}
        for key, value in vars(self.config).items():
            if value is not None:
                if isinstance(value, list):
                    config_dict[key] = value
                elif isinstance(value, dict):
                    config_dict[key] = value
                else:
                    config_dict[key] = value
        return config_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Field":
        """Create field from dictionary"""
        config_data = data.get("config", {})
        config = FieldConfig(**config_data)

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            field_type=FieldType(data["field_type"]),
            label=data["label"],
            description=data.get("description"),
            config=config,
            position=data.get("position", 0),
            page=data.get("page", 0),
            created_at=datetime.fromisoformat(data["created_at"])
                if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"])
                if "updated_at" in data else datetime.now(),
        )

    def validate_value(self, value: Any) -> tuple[bool, Optional[str]]:
        """
        Validate a value against field configuration

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Required validation
        if self.config.required and (value is None or value == ""):
            return False, f"{self.label} is required"

        # Skip further validation if empty and not required
        if value is None or value == "":
            return True, None

        # Type-specific validation
        if self.field_type == FieldType.EMAIL:
            if not self._validate_email(value):
                return False, "Invalid email address"

        elif self.field_type == FieldType.URL:
            if not self._validate_url(value):
                return False, "Invalid URL"

        elif self.field_type == FieldType.NUMBER:
            try:
                num_value = float(value)
                if self.config.min_value and num_value < self.config.min_value:
                    return False, f"Value must be at least {self.config.min_value}"
                if self.config.max_value and num_value > self.config.max_value:
                    return False, f"Value must be at most {self.config.max_value}"
            except ValueError:
                return False, "Invalid number"

        # Length validation for text fields
        if self.field_type in [FieldType.SHORT_TEXT, FieldType.LONG_TEXT]:
            if self.config.min_length and len(str(value)) < self.config.min_length:
                return False, f"Minimum length is {self.config.min_length} characters"
            if self.config.max_length and len(str(value)) > self.config.max_length:
                return False, f"Maximum length is {self.config.max_length} characters"

        # Pattern validation
        if self.config.pattern:
            import re
            if not re.match(self.config.pattern, str(value)):
                return False, "Invalid format"

        return True, None

    @staticmethod
    def _validate_email(email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def _validate_url(url: str) -> bool:
        """Validate URL format"""
        import re
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, url))

    def clone(self) -> "Field":
        """Create a copy of this field with a new ID"""
        new_field = Field(
            field_type=self.field_type,
            label=f"{self.label} (Copy)",
            description=self.description,
            config=self.config,
            position=self.position,
            page=self.page,
        )
        return new_field


class FieldFactory:
    """Factory for creating pre-configured field instances"""

    @staticmethod
    def create_short_text(label: str, required: bool = False,
                         placeholder: str = "") -> Field:
        """Create a short text field"""
        return Field(
            field_type=FieldType.SHORT_TEXT,
            label=label,
            config=FieldConfig(
                required=required,
                placeholder=placeholder,
                max_length=255
            )
        )

    @staticmethod
    def create_long_text(label: str, required: bool = False,
                        placeholder: str = "") -> Field:
        """Create a long text field"""
        return Field(
            field_type=FieldType.LONG_TEXT,
            label=label,
            config=FieldConfig(
                required=required,
                placeholder=placeholder,
                max_length=5000
            )
        )

    @staticmethod
    def create_email(label: str = "Email", required: bool = True) -> Field:
        """Create an email field"""
        return Field(
            field_type=FieldType.EMAIL,
            label=label,
            config=FieldConfig(
                required=required,
                placeholder="you@example.com"
            )
        )

    @staticmethod
    def create_phone(label: str = "Phone Number",
                    required: bool = False) -> Field:
        """Create a phone field"""
        return Field(
            field_type=FieldType.PHONE,
            label=label,
            config=FieldConfig(
                required=required,
                placeholder="+1 (555) 000-0000",
                pattern=r'^\+?1?\d{9,15}$'
            )
        )

    @staticmethod
    def create_dropdown(label: str, options: List[str],
                       required: bool = False) -> Field:
        """Create a dropdown field"""
        return Field(
            field_type=FieldType.DROPDOWN,
            label=label,
            config=FieldConfig(
                required=required,
                options=options,
                allow_other=False
            )
        )

    @staticmethod
    def create_radio(label: str, options: List[str],
                    required: bool = False) -> Field:
        """Create a radio button field"""
        return Field(
            field_type=FieldType.RADIO,
            label=label,
            config=FieldConfig(
                required=required,
                options=options,
                allow_other=False
            )
        )

    @staticmethod
    def create_checkbox(label: str, options: List[str],
                       required: bool = False) -> Field:
        """Create a checkbox field"""
        return Field(
            field_type=FieldType.CHECKBOX,
            label=label,
            config=FieldConfig(
                required=required,
                options=options,
                allow_other=False
            )
        )

    @staticmethod
    def create_rating(label: str, max_rating: int = 5,
                     required: bool = False) -> Field:
        """Create a rating field"""
        return Field(
            field_type=FieldType.RATING,
            label=label,
            config=FieldConfig(
                required=required,
                min_rating=1,
                max_rating=max_rating,
                rating_icon="star"
            )
        )

    @staticmethod
    def create_nps(label: str = "How likely are you to recommend us?") -> Field:
        """Create an NPS (Net Promoter Score) field"""
        return Field(
            field_type=FieldType.NPS,
            label=label,
            config=FieldConfig(
                required=True,
                min_rating=0,
                max_rating=10,
                scale_labels={
                    0: "Not at all likely",
                    10: "Extremely likely"
                }
            )
        )

    @staticmethod
    def create_file_upload(label: str, max_files: int = 1,
                          allowed_types: Optional[List[str]] = None) -> Field:
        """Create a file upload field"""
        return Field(
            field_type=FieldType.FILE_UPLOAD,
            label=label,
            config=FieldConfig(
                max_files=max_files,
                max_file_size=10,
                allowed_file_types=allowed_types or ["pdf", "doc", "docx", "txt"]
            )
        )

    @staticmethod
    def create_matrix(label: str, rows: List[str],
                     columns: List[str]) -> Field:
        """Create a matrix field"""
        return Field(
            field_type=FieldType.MATRIX,
            label=label,
            config=FieldConfig(
                rows=rows,
                columns=columns
            )
        )

    @staticmethod
    def create_date(label: str, required: bool = False) -> Field:
        """Create a date field"""
        return Field(
            field_type=FieldType.DATE,
            label=label,
            config=FieldConfig(required=required)
        )

    @staticmethod
    def create_hidden(field_id: str, value: Any) -> Field:
        """Create a hidden field"""
        return Field(
            id=field_id,
            field_type=FieldType.HIDDEN,
            label="",
            config=FieldConfig(default_value=value)
        )
