"""
Format Processors Module

Handle PDF, images, and multi-page document processing.
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import numpy as np
from PIL import Image
import io

logger = logging.getLogger(__name__)


class PDFOCRProcessor:
    """Process PDF documents with OCR"""

    def __init__(self, ocr_engine=None):
        self.ocr_engine = ocr_engine
        self.logger = logging.getLogger(f"{__name__}.PDFOCRProcessor")

    def process_pdf(
        self,
        pdf_path: Path,
        dpi: int = 300,
        language: str = "eng"
    ) -> List[Dict[str, Any]]:
        """
        Process PDF with OCR

        Args:
            pdf_path: Path to PDF file
            dpi: Resolution for rendering
            language: OCR language

        Returns:
            List of page results
        """
        try:
            import pdf2image

            # Convert PDF to images
            images = pdf2image.convert_from_path(
                str(pdf_path),
                dpi=dpi
            )

            results = []
            for page_num, image in enumerate(images, 1):
                self.logger.info(f"Processing page {page_num}/{len(images)}")

                # Convert PIL to numpy
                image_np = np.array(image)

                # OCR
                if self.ocr_engine:
                    ocr_result = self.ocr_engine.process_image(image_np, language)
                    results.append({
                        'page_number': page_num,
                        'text': ocr_result.text,
                        'confidence': ocr_result.confidence,
                        'words': ocr_result.words,
                        'lines': ocr_result.lines,
                    })
                else:
                    results.append({
                        'page_number': page_num,
                        'text': '',
                        'confidence': 0.0,
                    })

            self.logger.info(f"Processed {len(results)} pages")
            return results

        except ImportError:
            self.logger.error("pdf2image not installed")
            return []
        except Exception as e:
            self.logger.error(f"Error processing PDF: {e}")
            return []

    def extract_text_from_pdf(
        self,
        pdf_path: Path,
        try_native_first: bool = True
    ) -> str:
        """
        Extract text from PDF (native or OCR)

        Args:
            pdf_path: Path to PDF
            try_native_first: Try native extraction first

        Returns:
            Extracted text
        """
        try:
            # Try native text extraction first
            if try_native_first:
                try:
                    import PyPDF2

                    with open(pdf_path, 'rb') as file:
                        reader = PyPDF2.PdfReader(file)
                        text = ""
                        for page in reader.pages:
                            text += page.extract_text() + "\n"

                        # If we got substantial text, return it
                        if len(text.strip()) > 100:
                            self.logger.info("Extracted text natively from PDF")
                            return text
                except ImportError:
                    pass

            # Fall back to OCR
            self.logger.info("Falling back to OCR for PDF")
            results = self.process_pdf(pdf_path)
            text = "\n\n".join(r['text'] for r in results)
            return text

        except Exception as e:
            self.logger.error(f"Error extracting text from PDF: {e}")
            return ""


class ImageOCRProcessor:
    """Process image files with OCR"""

    def __init__(self, ocr_engine=None):
        self.ocr_engine = ocr_engine
        self.logger = logging.getLogger(f"{__name__}.ImageOCRProcessor")

    def process_image_file(
        self,
        image_path: Path,
        language: str = "eng"
    ) -> Dict[str, Any]:
        """
        Process image file with OCR

        Args:
            image_path: Path to image file
            language: OCR language

        Returns:
            OCR result dictionary
        """
        try:
            # Load image
            image = Image.open(image_path)
            image_np = np.array(image)

            # Process with OCR
            if self.ocr_engine:
                result = self.ocr_engine.process_image(image_np, language)
                return {
                    'text': result.text,
                    'confidence': result.confidence,
                    'words': result.words,
                    'lines': result.lines,
                    'blocks': result.blocks,
                }
            else:
                return {
                    'text': '',
                    'confidence': 0.0,
                }

        except Exception as e:
            self.logger.error(f"Error processing image: {e}")
            return {'text': '', 'confidence': 0.0}

    def process_image_bytes(
        self,
        image_bytes: bytes,
        language: str = "eng"
    ) -> Dict[str, Any]:
        """
        Process image from bytes

        Args:
            image_bytes: Image data as bytes
            language: OCR language

        Returns:
            OCR result dictionary
        """
        try:
            # Load image from bytes
            image = Image.open(io.BytesIO(image_bytes))
            image_np = np.array(image)

            # Process with OCR
            if self.ocr_engine:
                result = self.ocr_engine.process_image(image_np, language)
                return {
                    'text': result.text,
                    'confidence': result.confidence,
                    'words': result.words,
                    'lines': result.lines,
                }
            else:
                return {'text': '', 'confidence': 0.0}

        except Exception as e:
            self.logger.error(f"Error processing image bytes: {e}")
            return {'text': '', 'confidence': 0.0}


class MultiPageProcessor:
    """Process multi-page documents"""

    def __init__(self, ocr_engine=None):
        self.ocr_engine = ocr_engine
        self.pdf_processor = PDFOCRProcessor(ocr_engine)
        self.image_processor = ImageOCRProcessor(ocr_engine)
        self.logger = logging.getLogger(f"{__name__}.MultiPageProcessor")

    def process_document(
        self,
        file_path: Path,
        language: str = "eng",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process document (any format)

        Args:
            file_path: Path to document
            language: OCR language
            **kwargs: Additional options

        Returns:
            Processing result
        """
        try:
            suffix = file_path.suffix.lower()

            if suffix == '.pdf':
                pages = self.pdf_processor.process_pdf(file_path, language=language)
                return {
                    'type': 'pdf',
                    'pages': pages,
                    'page_count': len(pages),
                    'text': '\n\n'.join(p['text'] for p in pages),
                }

            elif suffix in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif']:
                result = self.image_processor.process_image_file(file_path, language)
                return {
                    'type': 'image',
                    'pages': [result],
                    'page_count': 1,
                    'text': result['text'],
                }

            elif suffix in ['.tif', '.tiff']:
                # Multi-page TIFF
                pages = self._process_multipage_tiff(file_path, language)
                return {
                    'type': 'tiff',
                    'pages': pages,
                    'page_count': len(pages),
                    'text': '\n\n'.join(p['text'] for p in pages),
                }

            else:
                raise ValueError(f"Unsupported file format: {suffix}")

        except Exception as e:
            self.logger.error(f"Error processing document: {e}")
            return {
                'type': 'unknown',
                'pages': [],
                'page_count': 0,
                'text': '',
                'error': str(e)
            }

    def _process_multipage_tiff(
        self,
        tiff_path: Path,
        language: str = "eng"
    ) -> List[Dict[str, Any]]:
        """Process multi-page TIFF"""
        try:
            from PIL import Image

            results = []
            with Image.open(tiff_path) as img:
                page_count = getattr(img, 'n_frames', 1)

                for page_num in range(page_count):
                    img.seek(page_num)
                    image_np = np.array(img)

                    if self.ocr_engine:
                        result = self.ocr_engine.process_image(image_np, language)
                        results.append({
                            'page_number': page_num + 1,
                            'text': result.text,
                            'confidence': result.confidence,
                        })

            return results

        except Exception as e:
            self.logger.error(f"Error processing TIFF: {e}")
            return []

    def batch_process(
        self,
        file_paths: List[Path],
        language: str = "eng",
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Batch process multiple documents

        Args:
            file_paths: List of file paths
            language: OCR language
            **kwargs: Additional options

        Returns:
            List of processing results
        """
        results = []

        for file_path in file_paths:
            self.logger.info(f"Processing {file_path}")
            result = self.process_document(file_path, language, **kwargs)
            result['file_path'] = str(file_path)
            results.append(result)

        self.logger.info(f"Batch processed {len(results)} documents")
        return results


class DocumentProcessor:
    """Main document processor combining all format processors"""

    def __init__(self, ocr_engine=None):
        self.multi_page_processor = MultiPageProcessor(ocr_engine)
        self.pdf_processor = PDFOCRProcessor(ocr_engine)
        self.image_processor = ImageOCRProcessor(ocr_engine)
        self.logger = logging.getLogger(f"{__name__}.DocumentProcessor")

    def process(
        self,
        file_path: Path,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process any document format

        Args:
            file_path: Path to document
            **kwargs: Processing options

        Returns:
            Processing result
        """
        return self.multi_page_processor.process_document(file_path, **kwargs)

    def batch_process(
        self,
        file_paths: List[Path],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Batch process documents

        Args:
            file_paths: List of document paths
            **kwargs: Processing options

        Returns:
            List of results
        """
        return self.multi_page_processor.batch_process(file_paths, **kwargs)


class BatchProcessor:
    """Process multiple documents in batch"""

    def __init__(self, ocr_engine=None, max_workers: int = 4):
        self.ocr_engine = ocr_engine
        self.max_workers = max_workers
        self.document_processor = DocumentProcessor(ocr_engine)
        self.logger = logging.getLogger(f"{__name__}.BatchProcessor")

    def process_batch(
        self,
        file_paths: List[Path],
        parallel: bool = True,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Process batch of documents

        Args:
            file_paths: List of file paths
            parallel: Use parallel processing
            **kwargs: Processing options

        Returns:
            List of results
        """
        try:
            if parallel:
                return self._process_parallel(file_paths, **kwargs)
            else:
                return self._process_sequential(file_paths, **kwargs)

        except Exception as e:
            self.logger.error(f"Error in batch processing: {e}")
            return []

    def _process_sequential(
        self,
        file_paths: List[Path],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Process documents sequentially"""
        results = []
        for i, file_path in enumerate(file_paths, 1):
            self.logger.info(f"Processing {i}/{len(file_paths)}: {file_path}")
            result = self.document_processor.process(file_path, **kwargs)
            result['file_path'] = str(file_path)
            results.append(result)
        return results

    def _process_parallel(
        self,
        file_paths: List[Path],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Process documents in parallel"""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_path = {
                executor.submit(self.document_processor.process, path, **kwargs): path
                for path in file_paths
            }

            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    result = future.result()
                    result['file_path'] = str(path)
                    results.append(result)
                    self.logger.info(f"Completed: {path}")
                except Exception as e:
                    self.logger.error(f"Error processing {path}: {e}")
                    results.append({
                        'file_path': str(path),
                        'error': str(e)
                    })

        return results
