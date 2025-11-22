"""
Layout Analysis Module

Detects document layout including columns, tables, images, headers, and footers.
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import cv2
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Region:
    """Represents a document region"""
    type: str  # 'text', 'image', 'table', 'header', 'footer'
    bbox: Tuple[int, int, int, int]  # (x, y, width, height)
    confidence: float
    content: Any = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class LayoutDetector:
    """Detect document layout and structure"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.LayoutDetector")

    def detect_layout(self, image: np.ndarray) -> List[Region]:
        """
        Detect document layout regions

        Args:
            image: Input image

        Returns:
            List of detected regions
        """
        try:
            regions = []

            # Detect text regions
            text_regions = self._detect_text_regions(image)
            regions.extend(text_regions)

            # Detect image regions
            image_regions = self._detect_image_regions(image)
            regions.extend(image_regions)

            # Detect table regions
            table_regions = self._detect_table_regions(image)
            regions.extend(table_regions)

            # Sort regions by position (top to bottom, left to right)
            regions.sort(key=lambda r: (r.bbox[1], r.bbox[0]))

            self.logger.info(f"Detected {len(regions)} layout regions")
            return regions

        except Exception as e:
            self.logger.error(f"Error detecting layout: {e}")
            return []

    def _detect_text_regions(self, image: np.ndarray) -> List[Region]:
        """Detect text regions using MSER or contours"""
        try:
            regions = []

            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # Apply binary threshold
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Filter and create regions
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)

                # Filter by size
                if w > 20 and h > 10:
                    regions.append(Region(
                        type='text',
                        bbox=(x, y, w, h),
                        confidence=0.8
                    ))

            return regions

        except Exception as e:
            self.logger.error(f"Error detecting text regions: {e}")
            return []

    def _detect_image_regions(self, image: np.ndarray) -> List[Region]:
        """Detect image/photo regions"""
        try:
            regions = []

            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # Detect edges
            edges = cv2.Canny(gray, 50, 150)

            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Filter for large rectangular regions (likely images)
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)

                # Check if it's large and rectangular
                aspect_ratio = float(w) / h if h > 0 else 0
                area = w * h

                if area > 10000 and 0.5 < aspect_ratio < 2.0:
                    regions.append(Region(
                        type='image',
                        bbox=(x, y, w, h),
                        confidence=0.7
                    ))

            return regions

        except Exception as e:
            self.logger.error(f"Error detecting image regions: {e}")
            return []

    def _detect_table_regions(self, image: np.ndarray) -> List[Region]:
        """Detect table regions"""
        try:
            regions = []

            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # Detect horizontal and vertical lines
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))

            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
            vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)

            # Combine lines
            table_mask = cv2.add(horizontal_lines, vertical_lines)

            # Find table contours
            contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)

                # Filter by size
                if w > 100 and h > 100:
                    regions.append(Region(
                        type='table',
                        bbox=(x, y, w, h),
                        confidence=0.75
                    ))

            return regions

        except Exception as e:
            self.logger.error(f"Error detecting table regions: {e}")
            return []


class ColumnDetector:
    """Detect column layout in documents"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ColumnDetector")

    def detect_columns(self, image: np.ndarray) -> List[Tuple[int, int]]:
        """
        Detect column boundaries in document

        Args:
            image: Input image

        Returns:
            List of (x_start, x_end) tuples for each column
        """
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # Calculate vertical projection profile
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            vertical_projection = np.sum(binary, axis=0)

            # Find valleys (gaps between columns)
            threshold = np.mean(vertical_projection) * 0.1
            gaps = vertical_projection < threshold

            # Find continuous gaps
            columns = []
            in_gap = False
            gap_start = 0

            for i, is_gap in enumerate(gaps):
                if is_gap and not in_gap:
                    gap_start = i
                    in_gap = True
                elif not is_gap and in_gap:
                    # Found column boundary
                    if i - gap_start > 20:  # Minimum gap width
                        columns.append((gap_start, i))
                    in_gap = False

            # Convert gaps to column boundaries
            if len(columns) == 0:
                return [(0, image.shape[1])]

            column_bounds = []
            prev_end = 0
            for gap_start, gap_end in columns:
                if gap_start - prev_end > 50:  # Minimum column width
                    column_bounds.append((prev_end, gap_start))
                prev_end = gap_end

            # Add last column
            if image.shape[1] - prev_end > 50:
                column_bounds.append((prev_end, image.shape[1]))

            self.logger.info(f"Detected {len(column_bounds)} columns")
            return column_bounds

        except Exception as e:
            self.logger.error(f"Error detecting columns: {e}")
            return [(0, image.shape[1])]


class TableDetector:
    """Detect tables in documents"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.TableDetector")

    def detect_tables(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect tables and their structure

        Args:
            image: Input image

        Returns:
            List of table dictionaries with structure info
        """
        try:
            tables = []

            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # Detect lines
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            # Horizontal and vertical kernels
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))

            horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
            vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)

            # Find line positions
            h_lines = self._detect_line_positions(horizontal_lines, axis=0)
            v_lines = self._detect_line_positions(vertical_lines, axis=1)

            # Create table structure
            if len(h_lines) >= 2 and len(v_lines) >= 2:
                table = {
                    'bbox': (
                        min(v_lines), min(h_lines),
                        max(v_lines) - min(v_lines), max(h_lines) - min(h_lines)
                    ),
                    'rows': len(h_lines) - 1,
                    'cols': len(v_lines) - 1,
                    'horizontal_lines': h_lines,
                    'vertical_lines': v_lines,
                }
                tables.append(table)

            self.logger.info(f"Detected {len(tables)} tables")
            return tables

        except Exception as e:
            self.logger.error(f"Error detecting tables: {e}")
            return []

    def _detect_line_positions(self, line_image: np.ndarray, axis: int) -> List[int]:
        """Detect positions of lines along an axis"""
        try:
            projection = np.sum(line_image, axis=axis)
            threshold = np.max(projection) * 0.5
            lines = np.where(projection > threshold)[0]

            # Group nearby lines
            if len(lines) == 0:
                return []

            grouped = []
            current_group = [lines[0]]

            for line in lines[1:]:
                if line - current_group[-1] <= 5:
                    current_group.append(line)
                else:
                    grouped.append(int(np.mean(current_group)))
                    current_group = [line]

            grouped.append(int(np.mean(current_group)))
            return grouped

        except Exception as e:
            self.logger.error(f"Error detecting line positions: {e}")
            return []


class RegionClassifier:
    """Classify document regions (header, footer, body, etc.)"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.RegionClassifier")

    def classify_regions(
        self,
        regions: List[Region],
        image_height: int
    ) -> List[Region]:
        """
        Classify regions based on position and characteristics

        Args:
            regions: List of detected regions
            image_height: Height of the document image

        Returns:
            Classified regions
        """
        try:
            header_threshold = image_height * 0.15
            footer_threshold = image_height * 0.85

            for region in regions:
                y_pos = region.bbox[1]

                # Classify based on vertical position
                if y_pos < header_threshold:
                    region.type = 'header'
                elif y_pos > footer_threshold:
                    region.type = 'footer'
                else:
                    # Keep existing classification for body regions
                    pass

            return regions

        except Exception as e:
            self.logger.error(f"Error classifying regions: {e}")
            return regions

    def detect_reading_order(self, regions: List[Region]) -> List[Region]:
        """
        Determine reading order of regions

        Args:
            regions: List of regions

        Returns:
            Regions sorted in reading order
        """
        try:
            # Sort by vertical position, then horizontal
            sorted_regions = sorted(
                regions,
                key=lambda r: (r.bbox[1] // 50, r.bbox[0])  # Group by row, then column
            )

            # Add reading order metadata
            for i, region in enumerate(sorted_regions):
                region.metadata['reading_order'] = i

            self.logger.info(f"Determined reading order for {len(sorted_regions)} regions")
            return sorted_regions

        except Exception as e:
            self.logger.error(f"Error detecting reading order: {e}")
            return regions
