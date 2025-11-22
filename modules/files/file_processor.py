"""File processing module for NEXUS Platform.

This module handles text extraction, thumbnail generation, and format conversion.
"""
import os
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from io import BytesIO
from PIL import Image
import pandas as pd


class FileProcessor:
    """Handles file processing operations like text extraction and thumbnail generation."""

    def __init__(self):
        """Initialize the file processor."""
        self.thumbnail_size = (200, 200)
        self.preview_size = (800, 600)

    def extract_text(self, file_path: str, mime_type: str) -> Optional[str]:
        """Extract text from various file formats.

        Args:
            file_path: Path to the file
            mime_type: MIME type of the file

        Returns:
            Extracted text or None if extraction failed
        """
        try:
            if mime_type == 'application/pdf':
                return self._extract_text_from_pdf(file_path)
            elif mime_type in ['application/msword',
                              'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                return self._extract_text_from_word(file_path)
            elif mime_type in ['application/vnd.ms-excel',
                              'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
                return self._extract_text_from_excel(file_path)
            elif mime_type in ['text/plain', 'text/markdown', 'text/csv']:
                return self._extract_text_from_text_file(file_path)
            elif mime_type.startswith('image/'):
                return self._extract_text_from_image(file_path)
            else:
                return None
        except Exception as e:
            print(f"Error extracting text from {file_path}: {e}")
            return None

    def _extract_text_from_pdf(self, file_path: str) -> Optional[str]:
        """Extract text from PDF file.

        Args:
            file_path: Path to PDF file

        Returns:
            Extracted text or None
        """
        try:
            import PyPDF2
            text = []
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    text.append(page.extract_text())
            return '\n'.join(text)
        except ImportError:
            # Fallback to pdfplumber if PyPDF2 not available
            try:
                import pdfplumber
                text = []
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text.append(page_text)
                return '\n'.join(text)
            except ImportError:
                print("PDF text extraction requires PyPDF2 or pdfplumber")
                return None
        except Exception as e:
            print(f"Error extracting PDF text: {e}")
            return None

    def _extract_text_from_word(self, file_path: str) -> Optional[str]:
        """Extract text from Word document.

        Args:
            file_path: Path to Word file

        Returns:
            Extracted text or None
        """
        try:
            from docx import Document
            doc = Document(file_path)
            text = []
            for paragraph in doc.paragraphs:
                text.append(paragraph.text)
            return '\n'.join(text)
        except ImportError:
            print("Word text extraction requires python-docx")
            return None
        except Exception as e:
            print(f"Error extracting Word text: {e}")
            return None

    def _extract_text_from_excel(self, file_path: str) -> Optional[str]:
        """Extract text from Excel file.

        Args:
            file_path: Path to Excel file

        Returns:
            Extracted text or None
        """
        try:
            # Read all sheets and convert to text
            excel_file = pd.ExcelFile(file_path)
            text = []
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                text.append(f"Sheet: {sheet_name}")
                text.append(df.to_string())
            return '\n'.join(text)
        except Exception as e:
            print(f"Error extracting Excel text: {e}")
            return None

    def _extract_text_from_text_file(self, file_path: str) -> Optional[str]:
        """Extract text from plain text file.

        Args:
            file_path: Path to text file

        Returns:
            File contents or None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading text file: {e}")
                return None
        except Exception as e:
            print(f"Error extracting text: {e}")
            return None

    def _extract_text_from_image(self, file_path: str) -> Optional[str]:
        """Extract text from image using OCR.

        Args:
            file_path: Path to image file

        Returns:
            Extracted text or None
        """
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img)
            return text
        except ImportError:
            print("OCR requires pytesseract and tesseract-ocr installation")
            return None
        except Exception as e:
            print(f"Error extracting text from image: {e}")
            return None

    def generate_thumbnail(self,
                          file_path: str,
                          mime_type: str,
                          output_path: Optional[str] = None) -> Optional[str]:
        """Generate thumbnail for a file.

        Args:
            file_path: Path to the file
            mime_type: MIME type of the file
            output_path: Optional output path for thumbnail

        Returns:
            Path to generated thumbnail or None
        """
        try:
            if not output_path:
                output_path = self._get_thumbnail_path(file_path)

            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            if mime_type.startswith('image/'):
                return self._generate_image_thumbnail(file_path, output_path)
            elif mime_type == 'application/pdf':
                return self._generate_pdf_thumbnail(file_path, output_path)
            elif mime_type.startswith('video/'):
                return self._generate_video_thumbnail(file_path, output_path)
            else:
                # Return None for other file types
                # Could generate generic icons based on file type
                return None
        except Exception as e:
            print(f"Error generating thumbnail: {e}")
            return None

    def _generate_image_thumbnail(self, file_path: str, output_path: str) -> str:
        """Generate thumbnail for image file.

        Args:
            file_path: Path to image file
            output_path: Output path for thumbnail

        Returns:
            Path to generated thumbnail
        """
        img = Image.open(file_path)

        # Convert RGBA to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background

        # Generate thumbnail
        img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
        img.save(output_path, 'JPEG', quality=85)
        return output_path

    def _generate_pdf_thumbnail(self, file_path: str, output_path: str) -> Optional[str]:
        """Generate thumbnail from first page of PDF.

        Args:
            file_path: Path to PDF file
            output_path: Output path for thumbnail

        Returns:
            Path to generated thumbnail or None
        """
        try:
            # Try using pdf2image
            from pdf2image import convert_from_path

            images = convert_from_path(file_path, first_page=1, last_page=1, dpi=72)
            if images:
                img = images[0]
                img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
                img.save(output_path, 'JPEG', quality=85)
                return output_path
        except ImportError:
            print("PDF thumbnail generation requires pdf2image and poppler")
        except Exception as e:
            print(f"Error generating PDF thumbnail: {e}")

        return None

    def _generate_video_thumbnail(self, file_path: str, output_path: str) -> Optional[str]:
        """Generate thumbnail from video at 5 seconds.

        Args:
            file_path: Path to video file
            output_path: Output path for thumbnail

        Returns:
            Path to generated thumbnail or None
        """
        try:
            import cv2

            cap = cv2.VideoCapture(file_path)
            # Seek to 5 seconds or middle of video
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            seek_frame = min(int(fps * 5), frame_count // 2)

            cap.set(cv2.CAP_PROP_POS_FRAMES, seek_frame)
            ret, frame = cap.read()
            cap.release()

            if ret:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
                img.save(output_path, 'JPEG', quality=85)
                return output_path
        except ImportError:
            print("Video thumbnail generation requires opencv-python")
        except Exception as e:
            print(f"Error generating video thumbnail: {e}")

        return None

    def convert_format(self,
                      file_path: str,
                      source_format: str,
                      target_format: str,
                      output_path: Optional[str] = None) -> Optional[str]:
        """Convert file from one format to another.

        Args:
            file_path: Path to source file
            source_format: Source format extension (e.g., '.pdf')
            target_format: Target format extension (e.g., '.docx')
            output_path: Optional output path

        Returns:
            Path to converted file or None
        """
        if not output_path:
            output_path = file_path.replace(source_format, target_format)

        try:
            # PDF conversions
            if source_format == '.pdf' and target_format in ['.docx', '.doc']:
                return self._convert_pdf_to_word(file_path, output_path)

            # Excel/CSV conversions
            elif source_format == '.csv' and target_format in ['.xlsx', '.xls']:
                return self._convert_csv_to_excel(file_path, output_path)
            elif source_format in ['.xlsx', '.xls'] and target_format == '.csv':
                return self._convert_excel_to_csv(file_path, output_path)

            # Image conversions
            elif source_format in ['.jpg', '.jpeg', '.png', '.gif', '.bmp'] and \
                 target_format in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                return self._convert_image_format(file_path, output_path, target_format)

            else:
                print(f"Conversion from {source_format} to {target_format} not supported")
                return None
        except Exception as e:
            print(f"Error converting file: {e}")
            return None

    def _convert_pdf_to_word(self, pdf_path: str, output_path: str) -> Optional[str]:
        """Convert PDF to Word document.

        Args:
            pdf_path: Path to PDF file
            output_path: Output path for Word document

        Returns:
            Path to converted file or None
        """
        try:
            # This is a placeholder - requires pypandoc or pdf2docx
            # from pdf2docx import Converter
            # cv = Converter(pdf_path)
            # cv.convert(output_path)
            # cv.close()
            print("PDF to Word conversion requires pdf2docx library")
            return None
        except Exception as e:
            print(f"Error converting PDF to Word: {e}")
            return None

    def _convert_csv_to_excel(self, csv_path: str, output_path: str) -> str:
        """Convert CSV to Excel.

        Args:
            csv_path: Path to CSV file
            output_path: Output path for Excel file

        Returns:
            Path to converted file
        """
        df = pd.read_csv(csv_path)
        df.to_excel(output_path, index=False)
        return output_path

    def _convert_excel_to_csv(self, excel_path: str, output_path: str) -> str:
        """Convert Excel to CSV.

        Args:
            excel_path: Path to Excel file
            output_path: Output path for CSV file

        Returns:
            Path to converted file
        """
        df = pd.read_excel(excel_path)
        df.to_csv(output_path, index=False)
        return output_path

    def _convert_image_format(self,
                             input_path: str,
                             output_path: str,
                             target_format: str) -> str:
        """Convert image from one format to another.

        Args:
            input_path: Path to source image
            output_path: Output path
            target_format: Target format extension

        Returns:
            Path to converted file
        """
        img = Image.open(input_path)

        # Convert RGBA to RGB for JPEG
        if target_format.lower() in ['.jpg', '.jpeg'] and img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background

        # Save in new format
        save_format = target_format.lstrip('.').upper()
        if save_format == 'JPG':
            save_format = 'JPEG'

        img.save(output_path, save_format)
        return output_path

    @staticmethod
    def _get_thumbnail_path(file_path: str) -> str:
        """Generate thumbnail path from file path.

        Args:
            file_path: Original file path

        Returns:
            Path for thumbnail
        """
        path = Path(file_path)
        thumb_dir = path.parent / 'thumbnails'
        thumb_dir.mkdir(exist_ok=True)
        return str(thumb_dir / f"{path.stem}_thumb.jpg")

    def create_preview(self,
                      file_path: str,
                      mime_type: str,
                      output_path: Optional[str] = None) -> Optional[str]:
        """Create a preview image for a file.

        Args:
            file_path: Path to the file
            mime_type: MIME type of the file
            output_path: Optional output path

        Returns:
            Path to preview image or None
        """
        if not output_path:
            path = Path(file_path)
            preview_dir = path.parent / 'previews'
            preview_dir.mkdir(exist_ok=True)
            output_path = str(preview_dir / f"{path.stem}_preview.jpg")

        try:
            if mime_type.startswith('image/'):
                img = Image.open(file_path)
                # Keep aspect ratio
                img.thumbnail(self.preview_size, Image.Resampling.LANCZOS)
                img.save(output_path, 'JPEG', quality=90)
                return output_path
            elif mime_type == 'application/pdf':
                return self._generate_pdf_thumbnail(file_path, output_path)
            else:
                return None
        except Exception as e:
            print(f"Error creating preview: {e}")
            return None

    def get_image_dimensions(self, file_path: str) -> Optional[Tuple[int, int]]:
        """Get dimensions of an image file.

        Args:
            file_path: Path to image file

        Returns:
            Tuple of (width, height) or None
        """
        try:
            img = Image.open(file_path)
            return img.size
        except Exception as e:
            print(f"Error getting image dimensions: {e}")
            return None

    def compress_image(self,
                      file_path: str,
                      output_path: Optional[str] = None,
                      quality: int = 85,
                      max_size: Optional[Tuple[int, int]] = None) -> Optional[str]:
        """Compress an image file.

        Args:
            file_path: Path to image file
            output_path: Output path for compressed image
            quality: JPEG quality (1-100)
            max_size: Optional maximum dimensions (width, height)

        Returns:
            Path to compressed image or None
        """
        try:
            if not output_path:
                output_path = file_path

            img = Image.open(file_path)

            # Resize if max_size specified
            if max_size:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Convert RGBA to RGB for JPEG
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background

            # Save with compression
            img.save(output_path, 'JPEG', quality=quality, optimize=True)
            return output_path
        except Exception as e:
            print(f"Error compressing image: {e}")
            return None
