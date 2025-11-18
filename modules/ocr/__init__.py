"""
NEXUS OCR Module - Production-Ready Optical Character Recognition

This module provides comprehensive OCR capabilities for the NEXUS platform,
including multi-engine support, preprocessing, layout analysis, and export.

Author: NEXUS Platform Team
Version: 1.0.0
"""

from typing import Dict, Any
import logging

__version__ = "1.0.0"
__author__ = "NEXUS Platform Team"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Module exports
__all__ = [
    "engines",
    "processor",
    "preprocessor",
    "layout_analysis",
    "text_extraction",
    "post_processing",
    "table_extraction",
    "handwriting",
    "quality",
    "formats",
    "language",
    "export",
    "api",
    "models",
    "schemas",
    "tasks",
    "ui",
]

logger.info(f"NEXUS OCR Module v{__version__} initialized")
