"""
Table Extraction Module

Detect and extract tables to structured data and Excel format.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import cv2
import pandas as pd

logger = logging.getLogger(__name__)


class TableDetector:
    """Detect tables in documents"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.TableDetector")

    def detect_tables(
        self,
        image: np.ndarray,
        min_rows: int = 2,
        min_cols: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Detect tables in image

        Args:
            image: Input image
            min_rows: Minimum number of rows
            min_cols: Minimum number of columns

        Returns:
            List of detected tables with structure info
        """
        try:
            tables = []

            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # Threshold
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            # Detect horizontal and vertical lines
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))

            horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
            vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel, iterations=2)

            # Combine lines to create table mask
            table_mask = cv2.add(horizontal_lines, vertical_lines)

            # Find contours of tables
            contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)

                # Filter by size
                if w < 100 or h < 100:
                    continue

                # Extract table region
                table_roi = binary[y:y+h, x:x+w]

                # Detect rows and columns
                rows = self._detect_lines(table_roi, horizontal_kernel)
                cols = self._detect_lines(table_roi, vertical_kernel)

                if len(rows) >= min_rows and len(cols) >= min_cols:
                    tables.append({
                        'bbox': (x, y, w, h),
                        'rows': rows,
                        'cols': cols,
                        'num_rows': len(rows) - 1,
                        'num_cols': len(cols) - 1,
                    })

            self.logger.info(f"Detected {len(tables)} tables")
            return tables

        except Exception as e:
            self.logger.error(f"Error detecting tables: {e}")
            return []

    def _detect_lines(
        self,
        image: np.ndarray,
        kernel: np.ndarray
    ) -> List[int]:
        """Detect line positions in image"""
        try:
            lines_img = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)

            # Project along perpendicular axis
            if kernel.shape[0] > kernel.shape[1]:  # Vertical kernel
                projection = np.sum(lines_img, axis=0)
            else:  # Horizontal kernel
                projection = np.sum(lines_img, axis=1)

            # Find peaks
            threshold = np.max(projection) * 0.3
            line_positions = []

            for i, val in enumerate(projection):
                if val > threshold:
                    line_positions.append(i)

            # Group nearby positions
            if not line_positions:
                return []

            grouped = [line_positions[0]]
            for pos in line_positions[1:]:
                if pos - grouped[-1] > 10:
                    grouped.append(pos)

            return grouped

        except Exception as e:
            self.logger.error(f"Error detecting lines: {e}")
            return []


class CellExtractor:
    """Extract cell content from tables"""

    def __init__(self, ocr_engine=None):
        self.ocr_engine = ocr_engine
        self.logger = logging.getLogger(f"{__name__}.CellExtractor")

    def extract_cells(
        self,
        image: np.ndarray,
        table_info: Dict[str, Any],
        ocr_engine=None
    ) -> List[List[str]]:
        """
        Extract content from table cells

        Args:
            image: Input image
            table_info: Table structure information
            ocr_engine: OCR engine to use

        Returns:
            2D list of cell contents
        """
        try:
            x, y, w, h = table_info['bbox']
            rows = table_info['rows']
            cols = table_info['cols']

            # Extract table region
            table_img = image[y:y+h, x:x+w]

            # Initialize cell matrix
            cell_matrix = []

            # Extract each cell
            for i in range(len(rows) - 1):
                row_cells = []
                y1, y2 = rows[i], rows[i + 1]

                for j in range(len(cols) - 1):
                    x1, x2 = cols[j], cols[j + 1]

                    # Extract cell image
                    cell_img = table_img[y1:y2, x1:x2]

                    # Perform OCR on cell
                    if ocr_engine:
                        try:
                            result = ocr_engine.process_image(cell_img)
                            cell_text = result.text.strip()
                        except:
                            cell_text = ""
                    else:
                        cell_text = ""

                    row_cells.append(cell_text)

                cell_matrix.append(row_cells)

            self.logger.info(f"Extracted {len(cell_matrix)} rows from table")
            return cell_matrix

        except Exception as e:
            self.logger.error(f"Error extracting cells: {e}")
            return []


class TableToExcel:
    """Convert extracted tables to Excel format"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.TableToExcel")

    def convert_to_excel(
        self,
        tables: List[List[List[str]]],
        output_path: str,
        sheet_names: Optional[List[str]] = None
    ) -> bool:
        """
        Convert tables to Excel file

        Args:
            tables: List of tables (each table is 2D list)
            output_path: Path to save Excel file
            sheet_names: Optional sheet names for each table

        Returns:
            Success status
        """
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                for i, table in enumerate(tables):
                    if not table:
                        continue

                    # Convert to DataFrame
                    df = pd.DataFrame(table)

                    # Use first row as header if it looks like headers
                    if self._is_header_row(table[0]):
                        df.columns = table[0]
                        df = df[1:]

                    # Determine sheet name
                    if sheet_names and i < len(sheet_names):
                        sheet_name = sheet_names[i]
                    else:
                        sheet_name = f'Table_{i + 1}'

                    # Write to Excel
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

            self.logger.info(f"Saved {len(tables)} tables to {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error converting to Excel: {e}")
            return False

    def convert_to_dataframe(
        self,
        table: List[List[str]],
        has_header: bool = True
    ) -> pd.DataFrame:
        """
        Convert table to pandas DataFrame

        Args:
            table: 2D list representing table
            has_header: Whether first row is header

        Returns:
            pandas DataFrame
        """
        try:
            if not table:
                return pd.DataFrame()

            df = pd.DataFrame(table)

            if has_header and len(table) > 1:
                df.columns = table[0]
                df = df[1:]
                df = df.reset_index(drop=True)

            return df

        except Exception as e:
            self.logger.error(f"Error converting to DataFrame: {e}")
            return pd.DataFrame()

    def _is_header_row(self, row: List[str]) -> bool:
        """Check if row looks like a header row"""
        try:
            # Heuristics: headers usually don't contain numbers,
            # and are shorter than data rows
            numeric_count = sum(1 for cell in row if cell.replace('.', '').replace(',', '').isdigit())
            return numeric_count < len(row) * 0.5

        except:
            return True

    def convert_to_csv(
        self,
        table: List[List[str]],
        output_path: str
    ) -> bool:
        """
        Convert table to CSV file

        Args:
            table: 2D list representing table
            output_path: Path to save CSV file

        Returns:
            Success status
        """
        try:
            df = self.convert_to_dataframe(table)
            df.to_csv(output_path, index=False)
            self.logger.info(f"Saved table to {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error converting to CSV: {e}")
            return False

    def convert_to_json(
        self,
        table: List[List[str]],
        output_path: str
    ) -> bool:
        """
        Convert table to JSON file

        Args:
            table: 2D list representing table
            output_path: Path to save JSON file

        Returns:
            Success status
        """
        try:
            df = self.convert_to_dataframe(table)
            df.to_json(output_path, orient='records', indent=2)
            self.logger.info(f"Saved table to {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error converting to JSON: {e}")
            return False


class TableExtractor:
    """Main table extraction coordinator"""

    def __init__(self, ocr_engine=None):
        self.detector = TableDetector()
        self.cell_extractor = CellExtractor(ocr_engine)
        self.exporter = TableToExcel()
        self.ocr_engine = ocr_engine
        self.logger = logging.getLogger(f"{__name__}.TableExtractor")

    def extract_tables(
        self,
        image: np.ndarray,
        extract_cells: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Complete table extraction pipeline

        Args:
            image: Input image
            extract_cells: Whether to extract cell content

        Returns:
            List of extracted tables with data
        """
        try:
            # Detect tables
            tables = self.detector.detect_tables(image)

            # Extract cell content if requested
            if extract_cells and self.ocr_engine:
                for table in tables:
                    cells = self.cell_extractor.extract_cells(
                        image,
                        table,
                        self.ocr_engine
                    )
                    table['data'] = cells

            self.logger.info(f"Extracted {len(tables)} tables")
            return tables

        except Exception as e:
            self.logger.error(f"Error in table extraction pipeline: {e}")
            return []

    def extract_and_save(
        self,
        image: np.ndarray,
        output_path: str,
        format: str = "excel"
    ) -> bool:
        """
        Extract tables and save to file

        Args:
            image: Input image
            output_path: Path to save output
            format: Output format ('excel', 'csv', 'json')

        Returns:
            Success status
        """
        try:
            # Extract tables
            tables = self.extract_tables(image, extract_cells=True)

            if not tables:
                self.logger.warning("No tables found")
                return False

            # Extract table data
            table_data = [table.get('data', []) for table in tables if 'data' in table]

            # Save based on format
            if format.lower() == "excel":
                return self.exporter.convert_to_excel(table_data, output_path)
            elif format.lower() == "csv":
                # Save first table to CSV
                if table_data:
                    return self.exporter.convert_to_csv(table_data[0], output_path)
            elif format.lower() == "json":
                # Save first table to JSON
                if table_data:
                    return self.exporter.convert_to_json(table_data[0], output_path)
            else:
                self.logger.error(f"Unknown format: {format}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error extracting and saving tables: {e}")
            return False
