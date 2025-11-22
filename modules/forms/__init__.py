"""
NEXUS Forms & Surveys Module

A comprehensive form builder and survey platform that rivals Google Forms and Typeform.
Includes drag-drop builder, 20+ field types, conditional logic, analytics, and more.
"""

from .form_builder import FormBuilder, Form
from .field_types import FieldType, Field
from .logic import ConditionalLogic, LogicRule
from .validation import ValidationRule, Validator
from .responses import ResponseManager, FormResponse
from .analytics import FormAnalytics
from .export import DataExporter
from .templates import FormTemplate, TemplateLibrary

__version__ = "1.0.0"
__all__ = [
    "FormBuilder",
    "Form",
    "FieldType",
    "Field",
    "ConditionalLogic",
    "LogicRule",
    "ValidationRule",
    "Validator",
    "ResponseManager",
    "FormResponse",
    "FormAnalytics",
    "DataExporter",
    "FormTemplate",
    "TemplateLibrary",
]
