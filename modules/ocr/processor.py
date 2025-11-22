"""
Main OCR Processor Module

Coordinates all OCR components: engines, preprocessing, extraction, post-processing, export.
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import numpy as np
from PIL import Image

from .engines import OCREngineFactory, OCREngine
from .preprocessor import ImageProcessor
from .layout_analysis import LayoutDetector, ColumnDetector, RegionClassifier
from .text_extraction import TextExtractor, StructuredExtractor
from .post_processing import TextPostProcessor
from .table_extraction import TableExtractor
from .handwriting import HandwritingRecognizer
from .quality import QualityAssessment, ConfidenceScoring
from .formats import DocumentProcessor as FormatProcessor
from .language import MultilingualOCR, LanguageDetection
from .export import ExportManager
from .config import config

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Process single images with OCR"""

    def __init__(
        self,
        engine_type: str = "tesseract",
        engine_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize image processor

        Args:
            engine_type: OCR engine to use
            engine_config: Engine configuration
        """
        self.logger = logging.getLogger(f"{__name__}.ImageProcessor")

        # Initialize OCR engine
        engine_config = engine_config or config.get_engine_config(engine_type)
        self.ocr_engine = OCREngineFactory.create_engine(engine_type, engine_config)

        # Initialize components
        from .preprocessor import ImageProcessor as PreprocessorClass
        self.preprocessor = PreprocessorClass()
        self.layout_detector = LayoutDetector()
        self.text_extractor = TextExtractor()
        self.post_processor = TextPostProcessor()
        self.quality_assessor = QualityAssessment()
        self.multilingual_ocr = MultilingualOCR(self.ocr_engine)

    def process(
        self,
        image: np.ndarray,
        language: str = "eng",
        preprocess: bool = True,
        detect_layout: bool = False,
        post_process: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process image with OCR

        Args:
            image: Input image (numpy array)
            language: OCR language
            preprocess: Apply preprocessing
            detect_layout: Detect document layout
            post_process: Apply post-processing
            **kwargs: Additional options

        Returns:
            Processing result dictionary
        """
        try:
            # 1. Assess input image quality
            quality_metrics = self.quality_assessor.assess_image_quality(image)

            # 2. Preprocess image
            if preprocess:
                processed_image = self.preprocessor.preprocess_for_ocr(image)
            else:
                processed_image = image

            # 3. Detect layout (optional)
            layout_regions = None
            if detect_layout:
                layout_regions = self.layout_detector.detect_layout(processed_image)

            # 4. Perform OCR
            ocr_result = self.ocr_engine.process_image(processed_image, language)

            # 5. Extract text blocks
            text_blocks = self.text_extractor.extract(ocr_result)

            # 6. Post-process text
            if post_process:
                processed_text = self.post_processor.process(ocr_result.text)
            else:
                processed_text = ocr_result.text

            # 7. Assess OCR quality
            result_quality = self.quality_assessor.assess_ocr_result(ocr_result, image)

            # 8. Build result
            result = {
                'text': processed_text,
                'raw_text': ocr_result.text,
                'confidence': ocr_result.confidence,
                'words': ocr_result.words,
                'lines': ocr_result.lines,
                'blocks': ocr_result.blocks,
                'text_blocks': [tb.to_dict() for tb in text_blocks],
                'layout_regions': [vars(r) for r in layout_regions] if layout_regions else [],
                'image_quality': quality_metrics,
                'result_quality': vars(result_quality),
                'language': language,
                'metadata': ocr_result.metadata,
            }

            self.logger.info(f"Image processing complete. Confidence: {ocr_result.confidence:.2f}")
            return result

        except Exception as e:
            self.logger.error(f"Error processing image: {e}")
            return {
                'text': '',
                'confidence': 0.0,
                'error': str(e)
            }


class DocumentProcessor:
    """Process complete documents (PDF, images, multi-page)"""

    def __init__(
        self,
        engine_type: str = "tesseract",
        engine_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize document processor

        Args:
            engine_type: OCR engine to use
            engine_config: Engine configuration
        """
        self.logger = logging.getLogger(f"{__name__}.DocumentProcessor")

        # Initialize OCR engine
        engine_config = engine_config or config.get_engine_config(engine_type)
        self.ocr_engine = OCREngineFactory.create_engine(engine_type, engine_config)

        # Initialize processors
        self.image_processor = ImageProcessor(engine_type, engine_config)
        self.format_processor = FormatProcessor(self.ocr_engine)
        self.table_extractor = TableExtractor(self.ocr_engine)
        self.handwriting_recognizer = HandwritingRecognizer(self.ocr_engine)
        self.export_manager = ExportManager()

    def process_file(
        self,
        file_path: Path,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process document file

        Args:
            file_path: Path to document
            **kwargs: Processing options

        Returns:
            Processing result
        """
        try:
            result = self.format_processor.process(file_path, **kwargs)
            self.logger.info(f"Processed document: {file_path}")
            return result

        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}")
            return {
                'error': str(e),
                'file_path': str(file_path)
            }

    def process_with_tables(
        self,
        file_path: Path,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process document and extract tables

        Args:
            file_path: Path to document
            **kwargs: Processing options

        Returns:
            Result with extracted tables
        """
        try:
            # Process document
            result = self.process_file(file_path, **kwargs)

            # Extract tables from each page
            if result.get('type') == 'pdf':
                pages = result.get('pages', [])
                for page in pages:
                    # Load page image and extract tables
                    # (Would need page image here)
                    pass

            return result

        except Exception as e:
            self.logger.error(f"Error processing with tables: {e}")
            return {'error': str(e)}

    def export_result(
        self,
        result: Dict[str, Any],
        output_path: Path,
        format: str = "pdf",
        **kwargs
    ) -> bool:
        """
        Export processing result

        Args:
            result: Processing result
            output_path: Output path
            format: Export format
            **kwargs: Format options

        Returns:
            Success status
        """
        try:
            return self.export_manager.export(result, output_path, format, **kwargs)
        except Exception as e:
            self.logger.error(f"Error exporting result: {e}")
            return False


class BatchProcessor:
    """Process multiple documents in batch"""

    def __init__(
        self,
        engine_type: str = "tesseract",
        engine_config: Optional[Dict[str, Any]] = None,
        max_workers: int = 4
    ):
        """
        Initialize batch processor

        Args:
            engine_type: OCR engine to use
            engine_config: Engine configuration
            max_workers: Maximum parallel workers
        """
        self.logger = logging.getLogger(f"{__name__}.BatchProcessor")
        self.max_workers = max_workers

        # Initialize document processor
        self.document_processor = DocumentProcessor(engine_type, engine_config)

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
            result = self.document_processor.process_file(file_path, **kwargs)
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
                executor.submit(
                    self.document_processor.process_file,
                    path,
                    **kwargs
                ): path
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


class OCRPipeline:
    """Complete OCR processing pipeline"""

    def __init__(
        self,
        engine_type: str = "tesseract",
        engine_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize OCR pipeline

        Args:
            engine_type: OCR engine to use
            engine_config: Engine configuration
        """
        self.logger = logging.getLogger(f"{__name__}.OCRPipeline")

        # Initialize processors
        self.image_processor = ImageProcessor(engine_type, engine_config)
        self.document_processor = DocumentProcessor(engine_type, engine_config)
        self.batch_processor = BatchProcessor(engine_type, engine_config)

    def process_image(
        self,
        image: np.ndarray,
        **kwargs
    ) -> Dict[str, Any]:
        """Process single image"""
        return self.image_processor.process(image, **kwargs)

    def process_file(
        self,
        file_path: Path,
        **kwargs
    ) -> Dict[str, Any]:
        """Process document file"""
        return self.document_processor.process_file(file_path, **kwargs)

    def process_batch(
        self,
        file_paths: List[Path],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Process batch of files"""
        return self.batch_processor.process_batch(file_paths, **kwargs)

    def process_and_export(
        self,
        input_path: Path,
        output_path: Path,
        export_format: str = "pdf",
        **kwargs
    ) -> bool:
        """
        Process file and export result

        Args:
            input_path: Input file path
            output_path: Output file path
            export_format: Export format
            **kwargs: Processing options

        Returns:
            Success status
        """
        try:
            # Process
            result = self.process_file(input_path, **kwargs)

            # Export
            return self.document_processor.export_result(
                result,
                output_path,
                export_format,
                **kwargs
            )

        except Exception as e:
            self.logger.error(f"Error in process and export: {e}")
            return False


# Convenience function for quick OCR
def ocr(
    input_path: Path,
    engine: str = "tesseract",
    language: str = "eng",
    **kwargs
) -> Dict[str, Any]:
    """
    Quick OCR function

    Args:
        input_path: Path to image or document
        engine: OCR engine to use
        language: Language code
        **kwargs: Additional options

    Returns:
        OCR result
    """
    pipeline = OCRPipeline(engine_type=engine)
    return pipeline.process_file(input_path, language=language, **kwargs)
