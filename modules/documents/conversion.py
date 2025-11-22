"""
Document Conversion Module

Provides comprehensive document conversion capabilities including format conversion,
OCR processing, text extraction, and image processing.

Features:
- Multi-format conversion (PDF, DOCX, images, etc.)
- OCR processing with Tesseract
- Text extraction from various formats
- Image processing and optimization
- Support for LibreOffice and Pandoc conversions
"""

import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, BinaryIO
from enum import Enum
import io

logger = logging.getLogger(__name__)


class DocumentFormat(Enum):
    """Supported document formats."""
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    ODT = "odt"
    RTF = "rtf"
    TXT = "txt"
    HTML = "html"
    MARKDOWN = "md"
    PNG = "png"
    JPEG = "jpg"
    TIFF = "tiff"
    BMP = "bmp"
    GIF = "gif"
    XLSX = "xlsx"
    PPTX = "pptx"


class ConversionError(Exception):
    """Base exception for conversion errors."""
    pass


class OCRError(ConversionError):
    """Exception for OCR-related errors."""
    pass


class FormatNotSupportedError(ConversionError):
    """Exception for unsupported format errors."""
    pass


class DocumentConverter:
    """
    Main document conversion class handling various format conversions.

    Supports:
    - PDF conversions
    - Office document conversions
    - Image conversions
    - Text extraction
    """

    def __init__(
        self,
        tesseract_path: Optional[str] = None,
        libreoffice_path: Optional[str] = None,
        pandoc_path: Optional[str] = None,
        temp_dir: Optional[str] = None
    ):
        """
        Initialize the document converter.

        Args:
            tesseract_path: Path to Tesseract executable
            libreoffice_path: Path to LibreOffice executable
            pandoc_path: Path to Pandoc executable
            temp_dir: Temporary directory for conversion operations
        """
        self.tesseract_path = tesseract_path or "tesseract"
        self.libreoffice_path = libreoffice_path or "libreoffice"
        self.pandoc_path = pandoc_path or "pandoc"
        self.temp_dir = temp_dir or tempfile.gettempdir()

        logger.info("DocumentConverter initialized")
        self._verify_dependencies()

    def _verify_dependencies(self) -> None:
        """Verify that required external tools are available."""
        tools = {
            "tesseract": self.tesseract_path,
            "libreoffice": self.libreoffice_path,
            "pandoc": self.pandoc_path
        }

        for tool_name, tool_path in tools.items():
            try:
                subprocess.run(
                    [tool_path, "--version"],
                    capture_output=True,
                    check=True,
                    timeout=5
                )
                logger.debug(f"{tool_name} is available at {tool_path}")
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
                logger.warning(f"{tool_name} not available: {e}")

    def convert(
        self,
        input_path: Union[str, Path],
        output_format: DocumentFormat,
        output_path: Optional[Union[str, Path]] = None,
        **options
    ) -> Path:
        """
        Convert a document to the specified format.

        Args:
            input_path: Path to input document
            output_format: Target format
            output_path: Optional output path (generated if not provided)
            **options: Additional conversion options

        Returns:
            Path to converted document

        Raises:
            ConversionError: If conversion fails
            FileNotFoundError: If input file doesn't exist
        """
        input_path = Path(input_path)

        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        # Determine input format
        input_format = self._detect_format(input_path)
        logger.info(f"Converting {input_format.value} to {output_format.value}")

        # Generate output path if not provided
        if output_path is None:
            output_path = self._generate_output_path(input_path, output_format)
        else:
            output_path = Path(output_path)

        try:
            # Route to appropriate conversion method
            if input_format == output_format:
                logger.info("Input and output formats are the same, copying file")
                import shutil
                shutil.copy2(input_path, output_path)
                return output_path

            # Use appropriate converter
            if output_format == DocumentFormat.PDF:
                return self._convert_to_pdf(input_path, output_path, **options)
            elif input_format == DocumentFormat.PDF and output_format in [DocumentFormat.DOCX, DocumentFormat.ODT]:
                return self._convert_pdf_to_office(input_path, output_path, output_format, **options)
            elif input_format in [DocumentFormat.DOCX, DocumentFormat.DOC, DocumentFormat.ODT]:
                return self._convert_office_document(input_path, output_path, output_format, **options)
            elif self._is_image_format(input_format) and self._is_image_format(output_format):
                return self._convert_image(input_path, output_path, output_format, **options)
            else:
                return self._convert_with_pandoc(input_path, output_path, output_format, **options)

        except Exception as e:
            logger.error(f"Conversion failed: {e}", exc_info=True)
            raise ConversionError(f"Failed to convert document: {e}") from e

    def _detect_format(self, file_path: Path) -> DocumentFormat:
        """Detect document format from file extension."""
        extension = file_path.suffix.lower().lstrip('.')

        try:
            return DocumentFormat(extension)
        except ValueError:
            # Try common variations
            format_map = {
                'jpg': DocumentFormat.JPEG,
                'jpeg': DocumentFormat.JPEG,
                'tif': DocumentFormat.TIFF,
                'htm': DocumentFormat.HTML
            }

            if extension in format_map:
                return format_map[extension]

            raise FormatNotSupportedError(f"Unsupported format: {extension}")

    def _generate_output_path(self, input_path: Path, output_format: DocumentFormat) -> Path:
        """Generate output path based on input path and target format."""
        return input_path.parent / f"{input_path.stem}.{output_format.value}"

    def _is_image_format(self, format: DocumentFormat) -> bool:
        """Check if format is an image format."""
        image_formats = {
            DocumentFormat.PNG, DocumentFormat.JPEG, DocumentFormat.TIFF,
            DocumentFormat.BMP, DocumentFormat.GIF
        }
        return format in image_formats

    def _convert_to_pdf(
        self,
        input_path: Path,
        output_path: Path,
        **options
    ) -> Path:
        """Convert document to PDF using LibreOffice."""
        logger.info(f"Converting to PDF: {input_path}")

        try:
            # Use LibreOffice for office documents
            cmd = [
                self.libreoffice_path,
                "--headless",
                "--convert-to", "pdf",
                "--outdir", str(output_path.parent),
                str(input_path)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                check=True
            )

            logger.debug(f"LibreOffice output: {result.stdout}")

            # LibreOffice may generate with different name
            expected_output = output_path.parent / f"{input_path.stem}.pdf"
            if expected_output != output_path and expected_output.exists():
                expected_output.rename(output_path)

            return output_path

        except subprocess.CalledProcessError as e:
            logger.error(f"LibreOffice conversion failed: {e.stderr}")
            raise ConversionError(f"PDF conversion failed: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise ConversionError("PDF conversion timed out")

    def _convert_pdf_to_office(
        self,
        input_path: Path,
        output_path: Path,
        output_format: DocumentFormat,
        **options
    ) -> Path:
        """Convert PDF to office format (limited support)."""
        logger.warning("PDF to Office conversion has limited formatting support")

        # This is a simplified implementation - real production code would use
        # specialized libraries like pdf2docx or pdfminer
        raise ConversionError("PDF to Office conversion requires additional dependencies")

    def _convert_office_document(
        self,
        input_path: Path,
        output_path: Path,
        output_format: DocumentFormat,
        **options
    ) -> Path:
        """Convert between office document formats using LibreOffice."""
        logger.info(f"Converting office document to {output_format.value}")

        try:
            cmd = [
                self.libreoffice_path,
                "--headless",
                "--convert-to", output_format.value,
                "--outdir", str(output_path.parent),
                str(input_path)
            ]

            subprocess.run(cmd, capture_output=True, check=True, timeout=300)

            expected_output = output_path.parent / f"{input_path.stem}.{output_format.value}"
            if expected_output != output_path and expected_output.exists():
                expected_output.rename(output_path)

            return output_path

        except subprocess.CalledProcessError as e:
            raise ConversionError(f"Office conversion failed: {e}")

    def _convert_image(
        self,
        input_path: Path,
        output_path: Path,
        output_format: DocumentFormat,
        **options
    ) -> Path:
        """Convert between image formats using Pillow."""
        try:
            from PIL import Image

            logger.info(f"Converting image to {output_format.value}")

            with Image.open(input_path) as img:
                # Handle format-specific options
                save_kwargs = {}

                if output_format == DocumentFormat.JPEG:
                    # Convert RGBA to RGB for JPEG
                    if img.mode in ('RGBA', 'LA', 'P'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = background
                    save_kwargs['quality'] = options.get('quality', 95)
                    save_kwargs['optimize'] = options.get('optimize', True)

                elif output_format == DocumentFormat.PNG:
                    save_kwargs['optimize'] = options.get('optimize', True)

                # Apply image processing options
                if options.get('resize'):
                    img = img.resize(options['resize'], Image.Resampling.LANCZOS)

                img.save(output_path, format=output_format.value.upper(), **save_kwargs)

            return output_path

        except ImportError:
            raise ConversionError("Pillow library not available for image conversion")
        except Exception as e:
            raise ConversionError(f"Image conversion failed: {e}")

    def _convert_with_pandoc(
        self,
        input_path: Path,
        output_path: Path,
        output_format: DocumentFormat,
        **options
    ) -> Path:
        """Convert document using Pandoc."""
        logger.info(f"Converting with Pandoc to {output_format.value}")

        try:
            cmd = [
                self.pandoc_path,
                str(input_path),
                "-o", str(output_path)
            ]

            # Add Pandoc-specific options
            if options.get('standalone'):
                cmd.append('--standalone')

            subprocess.run(cmd, capture_output=True, check=True, timeout=120)

            return output_path

        except subprocess.CalledProcessError as e:
            raise ConversionError(f"Pandoc conversion failed: {e}")


class OCRProcessor:
    """
    OCR processing for extracting text from images and scanned documents.

    Uses Tesseract OCR engine for text recognition.
    """

    def __init__(
        self,
        tesseract_path: Optional[str] = None,
        default_language: str = "eng",
        temp_dir: Optional[str] = None
    ):
        """
        Initialize OCR processor.

        Args:
            tesseract_path: Path to Tesseract executable
            default_language: Default OCR language (e.g., 'eng', 'fra', 'deu')
            temp_dir: Temporary directory for processing
        """
        self.tesseract_path = tesseract_path or "tesseract"
        self.default_language = default_language
        self.temp_dir = temp_dir or tempfile.gettempdir()

        logger.info(f"OCRProcessor initialized with language: {default_language}")
        self._verify_tesseract()

    def _verify_tesseract(self) -> None:
        """Verify Tesseract is available."""
        try:
            result = subprocess.run(
                [self.tesseract_path, "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            logger.debug(f"Tesseract version: {result.stdout.split()[1]}")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(f"Tesseract not available: {e}")
            raise OCRError("Tesseract OCR not available")

    def extract_text(
        self,
        image_path: Union[str, Path],
        language: Optional[str] = None,
        config: Optional[str] = None
    ) -> str:
        """
        Extract text from an image using OCR.

        Args:
            image_path: Path to image file
            language: OCR language (uses default if not specified)
            config: Tesseract configuration string

        Returns:
            Extracted text

        Raises:
            OCRError: If OCR processing fails
        """
        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        language = language or self.default_language
        logger.info(f"Performing OCR on {image_path} with language {language}")

        try:
            # Preprocess image for better OCR results
            preprocessed_path = self._preprocess_image(image_path)

            cmd = [
                self.tesseract_path,
                str(preprocessed_path),
                "stdout",
                "-l", language
            ]

            if config:
                cmd.extend(["--psm", config])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=300
            )

            text = result.stdout.strip()
            logger.info(f"OCR extracted {len(text)} characters")

            # Clean up preprocessed image if it's different from original
            if preprocessed_path != image_path:
                preprocessed_path.unlink(missing_ok=True)

            return text

        except subprocess.CalledProcessError as e:
            logger.error(f"OCR failed: {e.stderr}")
            raise OCRError(f"OCR processing failed: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise OCRError("OCR processing timed out")

    def extract_text_with_confidence(
        self,
        image_path: Union[str, Path],
        language: Optional[str] = None
    ) -> Tuple[str, float]:
        """
        Extract text with confidence score.

        Args:
            image_path: Path to image file
            language: OCR language

        Returns:
            Tuple of (extracted text, average confidence score)
        """
        image_path = Path(image_path)
        language = language or self.default_language

        try:
            # Get TSV output with confidence scores
            cmd = [
                self.tesseract_path,
                str(image_path),
                "stdout",
                "-l", language,
                "tsv"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=300
            )

            # Parse TSV output
            lines = result.stdout.strip().split('\n')
            confidences = []
            text_parts = []

            for line in lines[1:]:  # Skip header
                parts = line.split('\t')
                if len(parts) >= 12:
                    conf = parts[10]
                    text = parts[11]

                    if conf != '-1' and text.strip():
                        confidences.append(float(conf))
                        text_parts.append(text)

            text = ' '.join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            logger.info(f"OCR confidence: {avg_confidence:.2f}%")

            return text, avg_confidence

        except Exception as e:
            logger.error(f"OCR with confidence failed: {e}")
            raise OCRError(f"OCR processing failed: {e}")

    def _preprocess_image(self, image_path: Path) -> Path:
        """
        Preprocess image for better OCR results.

        Args:
            image_path: Path to original image

        Returns:
            Path to preprocessed image
        """
        try:
            from PIL import Image, ImageEnhance, ImageFilter

            with Image.open(image_path) as img:
                # Convert to grayscale
                if img.mode != 'L':
                    img = img.convert('L')

                # Enhance contrast
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(2.0)

                # Apply slight sharpening
                img = img.filter(ImageFilter.SHARPEN)

                # Save preprocessed image
                output_path = Path(self.temp_dir) / f"ocr_prep_{image_path.name}"
                img.save(output_path)

                return output_path

        except ImportError:
            logger.warning("Pillow not available, skipping image preprocessing")
            return image_path
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}, using original")
            return image_path


class TextExtractor:
    """
    Extract text content from various document formats.
    """

    def __init__(self, ocr_processor: Optional[OCRProcessor] = None):
        """
        Initialize text extractor.

        Args:
            ocr_processor: Optional OCR processor for image-based documents
        """
        self.ocr_processor = ocr_processor
        logger.info("TextExtractor initialized")

    def extract(
        self,
        file_path: Union[str, Path],
        use_ocr: bool = False
    ) -> str:
        """
        Extract text from a document.

        Args:
            file_path: Path to document
            use_ocr: Whether to use OCR for image-based content

        Returns:
            Extracted text

        Raises:
            ConversionError: If extraction fails
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Extracting text from {file_path}")

        # Determine extraction method based on format
        extension = file_path.suffix.lower()

        try:
            if extension == '.txt':
                return self._extract_from_txt(file_path)
            elif extension == '.pdf':
                return self._extract_from_pdf(file_path, use_ocr)
            elif extension in ['.docx', '.doc']:
                return self._extract_from_word(file_path)
            elif extension in ['.odt']:
                return self._extract_from_odt(file_path)
            elif extension in ['.html', '.htm']:
                return self._extract_from_html(file_path)
            elif extension in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
                return self._extract_from_image(file_path)
            else:
                raise FormatNotSupportedError(f"Text extraction not supported for {extension}")

        except Exception as e:
            logger.error(f"Text extraction failed: {e}", exc_info=True)
            raise ConversionError(f"Failed to extract text: {e}") from e

    def _extract_from_txt(self, file_path: Path) -> str:
        """Extract text from plain text file."""
        return file_path.read_text(encoding='utf-8', errors='ignore')

    def _extract_from_pdf(self, file_path: Path, use_ocr: bool) -> str:
        """Extract text from PDF file."""
        try:
            import PyPDF2

            text_parts = []

            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)

                for page in pdf_reader.pages:
                    text = page.extract_text()
                    text_parts.append(text)

            extracted_text = '\n'.join(text_parts)

            # Use OCR if text is empty and OCR is enabled
            if not extracted_text.strip() and use_ocr and self.ocr_processor:
                logger.info("No text found in PDF, attempting OCR")
                # This would require converting PDF pages to images first
                # Simplified for this implementation

            return extracted_text

        except ImportError:
            logger.error("PyPDF2 not available")
            raise ConversionError("PyPDF2 library required for PDF text extraction")

    def _extract_from_word(self, file_path: Path) -> str:
        """Extract text from Word document."""
        try:
            import docx

            doc = docx.Document(file_path)
            text_parts = [paragraph.text for paragraph in doc.paragraphs]

            return '\n'.join(text_parts)

        except ImportError:
            logger.error("python-docx not available")
            raise ConversionError("python-docx library required for Word text extraction")

    def _extract_from_odt(self, file_path: Path) -> str:
        """Extract text from ODT document."""
        try:
            from odf import text, teletype
            from odf.opendocument import load

            doc = load(file_path)
            text_content = []

            for paragraph in doc.getElementsByType(text.P):
                text_content.append(teletype.extractText(paragraph))

            return '\n'.join(text_content)

        except ImportError:
            logger.error("odfpy not available")
            raise ConversionError("odfpy library required for ODT text extraction")

    def _extract_from_html(self, file_path: Path) -> str:
        """Extract text from HTML file."""
        try:
            from bs4 import BeautifulSoup

            html_content = file_path.read_text(encoding='utf-8', errors='ignore')
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            return soup.get_text(separator='\n', strip=True)

        except ImportError:
            logger.error("BeautifulSoup not available")
            raise ConversionError("BeautifulSoup library required for HTML text extraction")

    def _extract_from_image(self, file_path: Path) -> str:
        """Extract text from image using OCR."""
        if not self.ocr_processor:
            raise ConversionError("OCR processor required for image text extraction")

        return self.ocr_processor.extract_text(file_path)


# Convenience functions
def convert_document(
    input_path: Union[str, Path],
    output_format: str,
    output_path: Optional[Union[str, Path]] = None,
    **options
) -> Path:
    """
    Convenience function to convert a document.

    Args:
        input_path: Path to input document
        output_format: Target format (e.g., 'pdf', 'docx')
        output_path: Optional output path
        **options: Additional conversion options

    Returns:
        Path to converted document
    """
    converter = DocumentConverter()
    format_enum = DocumentFormat(output_format.lower())
    return converter.convert(input_path, format_enum, output_path, **options)


def extract_text(
    file_path: Union[str, Path],
    use_ocr: bool = False
) -> str:
    """
    Convenience function to extract text from a document.

    Args:
        file_path: Path to document
        use_ocr: Whether to use OCR for image-based content

    Returns:
        Extracted text
    """
    ocr_processor = OCRProcessor() if use_ocr else None
    extractor = TextExtractor(ocr_processor)
    return extractor.extract(file_path, use_ocr)


def perform_ocr(
    image_path: Union[str, Path],
    language: str = "eng"
) -> str:
    """
    Convenience function to perform OCR on an image.

    Args:
        image_path: Path to image file
        language: OCR language

    Returns:
        Extracted text
    """
    processor = OCRProcessor(default_language=language)
    return processor.extract_text(image_path)
