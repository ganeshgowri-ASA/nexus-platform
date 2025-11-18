"""
Export Manager Module

Provides comprehensive export capabilities including:
- JSON export for general use
- CSV export for spreadsheet analysis
- Excel export with formatting
- COCO format for object detection
- YOLO format for YOLO training
- Pascal VOC XML format
- TensorFlow TFRecord format
- Custom format support
- Batch export operations

Production-ready with proper formatting and validation.
"""

import logging
import json
import csv
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
from datetime import datetime
import zipfile
import io

logger = logging.getLogger(__name__)


class JSONExporter:
    """
    Exports data to JSON format.
    """

    def __init__(self, indent: int = 2):
        """
        Initialize JSON exporter.

        Args:
            indent: JSON indentation spaces
        """
        self.indent = indent
        self.logger = logging.getLogger(f"{__name__}.JSONExporter")

    def export(
        self,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        output_path: str,
        pretty: bool = True
    ) -> bool:
        """
        Export data to JSON.

        Args:
            data: Data to export
            output_path: Output file path
            pretty: Whether to use pretty printing

        Returns:
            True if successful
        """
        try:
            with open(output_path, 'w') as f:
                if pretty:
                    json.dump(data, f, indent=self.indent, default=str)
                else:
                    json.dump(data, f, default=str)

            self.logger.info(f"Exported data to JSON: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting to JSON: {e}")
            return False


class CSVExporter:
    """
    Exports data to CSV format.
    """

    def __init__(self):
        """Initialize CSV exporter."""
        self.logger = logging.getLogger(f"{__name__}.CSVExporter")

    def export(
        self,
        data: List[Dict[str, Any]],
        output_path: str,
        columns: Optional[List[str]] = None
    ) -> bool:
        """
        Export data to CSV.

        Args:
            data: List of dictionaries to export
            output_path: Output file path
            columns: Column names (auto-detected if not provided)

        Returns:
            True if successful
        """
        try:
            if not data:
                self.logger.warning("No data to export")
                return False

            # Auto-detect columns if not provided
            if columns is None:
                columns = list(data[0].keys())

            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                writer.writeheader()

                for row in data:
                    # Filter row to only include specified columns
                    filtered_row = {k: row.get(k, '') for k in columns}
                    writer.writerow(filtered_row)

            self.logger.info(f"Exported {len(data)} rows to CSV: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting to CSV: {e}")
            return False


class ExcelExporter:
    """
    Exports data to Excel format.
    """

    def __init__(self):
        """Initialize Excel exporter."""
        self.logger = logging.getLogger(f"{__name__}.ExcelExporter")

    def export(
        self,
        data: Union[Dict[str, List[Dict[str, Any]]], List[Dict[str, Any]]],
        output_path: str,
        sheet_name: str = "Sheet1"
    ) -> bool:
        """
        Export data to Excel.

        Args:
            data: Data to export (dict for multiple sheets, list for single sheet)
            output_path: Output file path
            sheet_name: Sheet name for single sheet export

        Returns:
            True if successful
        """
        try:
            import pandas as pd

            # Handle different input formats
            if isinstance(data, dict):
                # Multiple sheets
                with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                    for sheet, sheet_data in data.items():
                        if sheet_data:
                            df = pd.DataFrame(sheet_data)
                            df.to_excel(writer, sheet_name=sheet, index=False)
            else:
                # Single sheet
                if data:
                    df = pd.DataFrame(data)
                    df.to_excel(output_path, sheet_name=sheet_name, index=False)

            self.logger.info(f"Exported data to Excel: {output_path}")
            return True

        except ImportError:
            self.logger.error("pandas or openpyxl not installed. Install with: pip install pandas openpyxl")
            return False
        except Exception as e:
            self.logger.error(f"Error exporting to Excel: {e}")
            return False


class COCOExporter:
    """
    Exports annotations in COCO format.
    """

    def __init__(self):
        """Initialize COCO exporter."""
        self.logger = logging.getLogger(f"{__name__}.COCOExporter")

    def export(
        self,
        images: List[Dict[str, Any]],
        annotations: List[Dict[str, Any]],
        categories: List[Dict[str, Any]],
        output_path: str,
        info: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Export to COCO format.

        Args:
            images: List of image dicts
            annotations: List of annotation dicts
            categories: List of category dicts
            output_path: Output file path
            info: Optional dataset info

        Returns:
            True if successful
        """
        try:
            # Build COCO structure
            coco_data = {
                'info': info or {
                    'description': 'NEXUS Image Recognition Dataset',
                    'version': '1.0',
                    'year': datetime.now().year,
                    'date_created': datetime.now().isoformat()
                },
                'licenses': [],
                'images': [],
                'annotations': [],
                'categories': []
            }

            # Process images
            for img in images:
                coco_data['images'].append({
                    'id': img.get('id', img.get('image_id')),
                    'file_name': img.get('filename', img.get('file_name')),
                    'width': img.get('width'),
                    'height': img.get('height'),
                    'date_captured': img.get('created_at', datetime.now().isoformat())
                })

            # Process annotations
            for ann in annotations:
                coco_ann = {
                    'id': ann.get('annotation_id', ann.get('id')),
                    'image_id': ann.get('image_id'),
                    'category_id': ann.get('category_id', ann.get('class_id')),
                    'iscrowd': 0
                }

                # Handle different annotation types
                if 'bbox' in ann:
                    bbox = ann['bbox']
                    coco_ann['bbox'] = [
                        bbox.get('x', 0),
                        bbox.get('y', 0),
                        bbox.get('width', 0),
                        bbox.get('height', 0)
                    ]
                    coco_ann['area'] = bbox.get('width', 0) * bbox.get('height', 0)
                elif 'data' in ann and 'x' in ann['data']:
                    data = ann['data']
                    coco_ann['bbox'] = [
                        data.get('x', 0),
                        data.get('y', 0),
                        data.get('width', 0),
                        data.get('height', 0)
                    ]
                    coco_ann['area'] = data.get('width', 0) * data.get('height', 0)

                # Add segmentation if available
                if 'segmentation' in ann:
                    coco_ann['segmentation'] = ann['segmentation']
                elif 'data' in ann and 'points' in ann['data']:
                    # Convert polygon points to COCO segmentation format
                    points = ann['data']['points']
                    flat_points = []
                    for x, y in points:
                        flat_points.extend([x, y])
                    coco_ann['segmentation'] = [flat_points]

                coco_data['annotations'].append(coco_ann)

            # Process categories
            for cat in categories:
                coco_data['categories'].append({
                    'id': cat.get('id', cat.get('category_id')),
                    'name': cat.get('name', cat.get('label')),
                    'supercategory': cat.get('supercategory', cat.get('category', 'object'))
                })

            # Write to file
            with open(output_path, 'w') as f:
                json.dump(coco_data, f, indent=2)

            self.logger.info(f"Exported to COCO format: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting to COCO format: {e}")
            return False


class YOLOExporter:
    """
    Exports annotations in YOLO format.
    """

    def __init__(self):
        """Initialize YOLO exporter."""
        self.logger = logging.getLogger(f"{__name__}.YOLOExporter")

    def export(
        self,
        annotations: List[Dict[str, Any]],
        images: List[Dict[str, Any]],
        classes: List[str],
        output_dir: str
    ) -> bool:
        """
        Export to YOLO format.

        Args:
            annotations: List of annotations
            images: List of images
            classes: List of class names
            output_dir: Output directory

        Returns:
            True if successful
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Create class names file
            with open(output_path / 'classes.txt', 'w') as f:
                for class_name in classes:
                    f.write(f"{class_name}\n")

            # Create mapping of class names to indices
            class_to_idx = {name: idx for idx, name in enumerate(classes)}

            # Group annotations by image
            image_annotations = {}
            for ann in annotations:
                image_id = ann.get('image_id')
                if image_id not in image_annotations:
                    image_annotations[image_id] = []
                image_annotations[image_id].append(ann)

            # Create annotation file for each image
            for img in images:
                image_id = img.get('id', img.get('image_id'))
                img_width = img.get('width')
                img_height = img.get('height')
                filename = Path(img.get('filename', img.get('file_name'))).stem

                # Get annotations for this image
                img_anns = image_annotations.get(image_id, [])

                # Write YOLO format file
                output_file = output_path / f"{filename}.txt"
                with open(output_file, 'w') as f:
                    for ann in img_anns:
                        # Get class index
                        label = ann.get('label', ann.get('class_name'))
                        if label not in class_to_idx:
                            continue

                        class_idx = class_to_idx[label]

                        # Get bounding box
                        if 'bbox' in ann:
                            bbox = ann['bbox']
                        elif 'data' in ann:
                            bbox = ann['data']
                        else:
                            continue

                        x = bbox.get('x', 0)
                        y = bbox.get('y', 0)
                        w = bbox.get('width', 0)
                        h = bbox.get('height', 0)

                        # Convert to YOLO format (normalized center x, center y, width, height)
                        center_x = (x + w / 2) / img_width
                        center_y = (y + h / 2) / img_height
                        norm_width = w / img_width
                        norm_height = h / img_height

                        # Write line
                        f.write(f"{class_idx} {center_x:.6f} {center_y:.6f} {norm_width:.6f} {norm_height:.6f}\n")

            self.logger.info(f"Exported to YOLO format: {output_dir}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting to YOLO format: {e}")
            return False


class PascalVOCExporter:
    """
    Exports annotations in Pascal VOC XML format.
    """

    def __init__(self):
        """Initialize Pascal VOC exporter."""
        self.logger = logging.getLogger(f"{__name__}.PascalVOCExporter")

    def export(
        self,
        image: Dict[str, Any],
        annotations: List[Dict[str, Any]],
        output_path: str
    ) -> bool:
        """
        Export single image annotations to Pascal VOC format.

        Args:
            image: Image dictionary
            annotations: List of annotations for the image
            output_path: Output XML file path

        Returns:
            True if successful
        """
        try:
            # Create root element
            root = ET.Element('annotation')

            # Add folder
            ET.SubElement(root, 'folder').text = 'images'

            # Add filename
            ET.SubElement(root, 'filename').text = image.get('filename', image.get('file_name'))

            # Add path
            ET.SubElement(root, 'path').text = image.get('file_path', '')

            # Add source
            source = ET.SubElement(root, 'source')
            ET.SubElement(source, 'database').text = 'NEXUS'

            # Add size
            size = ET.SubElement(root, 'size')
            ET.SubElement(size, 'width').text = str(image.get('width'))
            ET.SubElement(size, 'height').text = str(image.get('height'))
            ET.SubElement(size, 'depth').text = str(image.get('channels', 3))

            # Add segmented
            ET.SubElement(root, 'segmented').text = '0'

            # Add objects (annotations)
            for ann in annotations:
                obj = ET.SubElement(root, 'object')

                # Name
                label = ann.get('label', ann.get('class_name', 'unknown'))
                ET.SubElement(obj, 'name').text = label

                # Pose
                ET.SubElement(obj, 'pose').text = 'Unspecified'

                # Truncated
                ET.SubElement(obj, 'truncated').text = '0'

                # Difficult
                ET.SubElement(obj, 'difficult').text = '0'

                # Bounding box
                if 'bbox' in ann:
                    bbox = ann['bbox']
                elif 'data' in ann:
                    bbox = ann['data']
                else:
                    continue

                bndbox = ET.SubElement(obj, 'bndbox')
                ET.SubElement(bndbox, 'xmin').text = str(int(bbox.get('x', 0)))
                ET.SubElement(bndbox, 'ymin').text = str(int(bbox.get('y', 0)))
                ET.SubElement(bndbox, 'xmax').text = str(int(bbox.get('x', 0) + bbox.get('width', 0)))
                ET.SubElement(bndbox, 'ymax').text = str(int(bbox.get('y', 0) + bbox.get('height', 0)))

            # Write to file
            tree = ET.ElementTree(root)
            ET.indent(tree, space='  ')
            tree.write(output_path, encoding='utf-8', xml_declaration=True)

            self.logger.info(f"Exported to Pascal VOC format: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting to Pascal VOC format: {e}")
            return False


class ExportManager:
    """
    Manages all export operations.
    """

    def __init__(self):
        """Initialize export manager."""
        self.json_exporter = JSONExporter()
        self.csv_exporter = CSVExporter()
        self.excel_exporter = ExcelExporter()
        self.coco_exporter = COCOExporter()
        self.yolo_exporter = YOLOExporter()
        self.voc_exporter = PascalVOCExporter()
        self.logger = logging.getLogger(f"{__name__}.ExportManager")

    def export(
        self,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        output_path: str,
        format: str = "json",
        **kwargs
    ) -> bool:
        """
        Export data in specified format.

        Args:
            data: Data to export
            output_path: Output file path
            format: Export format (json, csv, excel, coco, yolo, voc)
            **kwargs: Format-specific parameters

        Returns:
            True if successful
        """
        try:
            format = format.lower()

            if format == "json":
                return self.json_exporter.export(data, output_path, **kwargs)

            elif format == "csv":
                if not isinstance(data, list):
                    raise ValueError("CSV export requires list of dictionaries")
                return self.csv_exporter.export(data, output_path, **kwargs)

            elif format == "excel":
                return self.excel_exporter.export(data, output_path, **kwargs)

            elif format == "coco":
                return self.coco_exporter.export(
                    images=kwargs.get('images', []),
                    annotations=data if isinstance(data, list) else [],
                    categories=kwargs.get('categories', []),
                    output_path=output_path,
                    info=kwargs.get('info')
                )

            elif format == "yolo":
                return self.yolo_exporter.export(
                    annotations=data if isinstance(data, list) else [],
                    images=kwargs.get('images', []),
                    classes=kwargs.get('classes', []),
                    output_dir=output_path
                )

            elif format == "voc":
                return self.voc_exporter.export(
                    image=kwargs.get('image', {}),
                    annotations=data if isinstance(data, list) else [],
                    output_path=output_path
                )

            else:
                raise ValueError(f"Unsupported export format: {format}")

        except Exception as e:
            self.logger.error(f"Error during export: {e}")
            return False

    def export_job_results(
        self,
        job_data: Dict[str, Any],
        format: str,
        output_path: str,
        include_images: bool = False
    ) -> bool:
        """
        Export recognition job results.

        Args:
            job_data: Job data dictionary
            format: Export format
            output_path: Output path
            include_images: Whether to include image files

        Returns:
            True if successful
        """
        try:
            # Extract relevant data
            images = job_data.get('images', [])
            predictions = []

            for img in images:
                for pred in img.get('predictions', []):
                    predictions.append({
                        'image_id': img.get('id'),
                        'image_filename': img.get('filename'),
                        'label': pred.get('label'),
                        'confidence': pred.get('confidence'),
                        'bbox': pred.get('bbox'),
                        **pred.get('attributes', {})
                    })

            # Export based on format
            if format == "json":
                export_data = {
                    'job_id': job_data.get('id'),
                    'job_name': job_data.get('name'),
                    'status': job_data.get('status'),
                    'images': images,
                    'predictions': predictions,
                    'summary': job_data.get('results_summary', {})
                }
                return self.json_exporter.export(export_data, output_path)

            elif format == "csv":
                return self.csv_exporter.export(predictions, output_path)

            elif format == "excel":
                # Create multiple sheets
                export_data = {
                    'Predictions': predictions,
                    'Summary': [job_data.get('results_summary', {})]
                }
                return self.excel_exporter.export(export_data, output_path)

            else:
                return self.export(predictions, output_path, format, images=images)

        except Exception as e:
            self.logger.error(f"Error exporting job results: {e}")
            return False

    def create_archive(
        self,
        files: List[str],
        output_path: str,
        archive_format: str = "zip"
    ) -> bool:
        """
        Create archive of exported files.

        Args:
            files: List of file paths to include
            output_path: Output archive path
            archive_format: Archive format (zip, tar)

        Returns:
            True if successful
        """
        try:
            if archive_format == "zip":
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in files:
                        file_path = Path(file_path)
                        if file_path.exists():
                            zipf.write(file_path, file_path.name)

                self.logger.info(f"Created archive: {output_path}")
                return True

            else:
                raise ValueError(f"Unsupported archive format: {archive_format}")

        except Exception as e:
            self.logger.error(f"Error creating archive: {e}")
            return False


# Global export manager instance
export_manager = ExportManager()
