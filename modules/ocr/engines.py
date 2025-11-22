"""
OCR Engines Module

Provides multiple OCR engine implementations with unified interface.
Supports Tesseract, Google Vision, Azure, AWS Textract, OpenAI GPT-4 Vision, and Anthropic Claude.
"""

import io
import base64
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)


class OCRResult:
    """Unified OCR result structure"""

    def __init__(
        self,
        text: str,
        confidence: float,
        words: Optional[List[Dict[str, Any]]] = None,
        lines: Optional[List[Dict[str, Any]]] = None,
        blocks: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.text = text
        self.confidence = confidence
        self.words = words or []
        self.lines = lines or []
        self.blocks = blocks or []
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "text": self.text,
            "confidence": self.confidence,
            "words": self.words,
            "lines": self.lines,
            "blocks": self.blocks,
            "metadata": self.metadata,
        }


class OCREngine(ABC):
    """Abstract base class for OCR engines"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def process_image(
        self,
        image: np.ndarray,
        language: str = "eng",
        **kwargs
    ) -> OCRResult:
        """Process image and extract text"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if engine is available and configured"""
        pass

    def process_file(
        self,
        file_path: Path,
        language: str = "eng",
        **kwargs
    ) -> OCRResult:
        """Process image file"""
        try:
            image = Image.open(file_path)
            image_array = np.array(image)
            return self.process_image(image_array, language, **kwargs)
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}")
            raise


class TesseractOCR(OCREngine):
    """Tesseract OCR Engine"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._pytesseract = None
        self._initialize()

    def _initialize(self):
        """Initialize Tesseract"""
        try:
            import pytesseract
            self._pytesseract = pytesseract

            # Set Tesseract path if provided
            if "path" in self.config and self.config["path"]:
                pytesseract.pytesseract.tesseract_cmd = self.config["path"]

            # Set TESSDATA_PREFIX if provided
            if "data_path" in self.config and self.config["data_path"]:
                import os
                os.environ["TESSDATA_PREFIX"] = self.config["data_path"]

            self.logger.info("Tesseract OCR initialized successfully")
        except ImportError:
            self.logger.warning("pytesseract not installed")
        except Exception as e:
            self.logger.error(f"Error initializing Tesseract: {e}")

    def is_available(self) -> bool:
        """Check if Tesseract is available"""
        return self._pytesseract is not None

    def process_image(
        self,
        image: np.ndarray,
        language: str = "eng",
        **kwargs
    ) -> OCRResult:
        """Process image with Tesseract"""
        if not self.is_available():
            raise RuntimeError("Tesseract OCR is not available")

        try:
            # Convert numpy array to PIL Image
            if isinstance(image, np.ndarray):
                image_pil = Image.fromarray(image)
            else:
                image_pil = image

            # Extract text
            text = self._pytesseract.image_to_string(
                image_pil,
                lang=language,
                config=kwargs.get("config", "")
            )

            # Get detailed data
            data = self._pytesseract.image_to_data(
                image_pil,
                lang=language,
                output_type=self._pytesseract.Output.DICT
            )

            # Calculate average confidence
            confidences = [
                float(conf) for conf in data["conf"]
                if conf != -1
            ]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            avg_confidence = avg_confidence / 100.0  # Normalize to 0-1

            # Extract words with positions and confidence
            words = []
            for i in range(len(data["text"])):
                if data["text"][i].strip():
                    words.append({
                        "text": data["text"][i],
                        "confidence": float(data["conf"][i]) / 100.0 if data["conf"][i] != -1 else 0.0,
                        "bbox": {
                            "x": data["left"][i],
                            "y": data["top"][i],
                            "width": data["width"][i],
                            "height": data["height"][i],
                        },
                        "block_num": data["block_num"][i],
                        "par_num": data["par_num"][i],
                        "line_num": data["line_num"][i],
                        "word_num": data["word_num"][i],
                    })

            # Group into lines
            lines = self._group_into_lines(words)

            # Group into blocks
            blocks = self._group_into_blocks(words)

            return OCRResult(
                text=text,
                confidence=avg_confidence,
                words=words,
                lines=lines,
                blocks=blocks,
                metadata={"engine": "tesseract", "language": language}
            )

        except Exception as e:
            self.logger.error(f"Tesseract OCR error: {e}")
            raise

    def _group_into_lines(self, words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group words into lines"""
        lines_dict = {}
        for word in words:
            line_key = (word["block_num"], word["par_num"], word["line_num"])
            if line_key not in lines_dict:
                lines_dict[line_key] = []
            lines_dict[line_key].append(word)

        lines = []
        for line_words in lines_dict.values():
            if line_words:
                text = " ".join(w["text"] for w in line_words)
                avg_conf = sum(w["confidence"] for w in line_words) / len(line_words)
                lines.append({
                    "text": text,
                    "confidence": avg_conf,
                    "words": line_words,
                })
        return lines

    def _group_into_blocks(self, words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group words into blocks"""
        blocks_dict = {}
        for word in words:
            block_key = word["block_num"]
            if block_key not in blocks_dict:
                blocks_dict[block_key] = []
            blocks_dict[block_key].append(word)

        blocks = []
        for block_words in blocks_dict.values():
            if block_words:
                text = " ".join(w["text"] for w in block_words)
                avg_conf = sum(w["confidence"] for w in block_words) / len(block_words)
                blocks.append({
                    "text": text,
                    "confidence": avg_conf,
                    "words": block_words,
                })
        return blocks


class GoogleVisionOCR(OCREngine):
    """Google Cloud Vision OCR Engine"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._client = None
        self._initialize()

    def _initialize(self):
        """Initialize Google Vision client"""
        try:
            from google.cloud import vision
            import os

            # Set credentials if provided
            if "credentials" in self.config and self.config["credentials"]:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.config["credentials"]

            self._client = vision.ImageAnnotatorClient()
            self.logger.info("Google Vision OCR initialized successfully")
        except ImportError:
            self.logger.warning("google-cloud-vision not installed")
        except Exception as e:
            self.logger.error(f"Error initializing Google Vision: {e}")

    def is_available(self) -> bool:
        """Check if Google Vision is available"""
        return self._client is not None

    def process_image(
        self,
        image: np.ndarray,
        language: str = "eng",
        **kwargs
    ) -> OCRResult:
        """Process image with Google Vision"""
        if not self.is_available():
            raise RuntimeError("Google Vision OCR is not available")

        try:
            from google.cloud import vision

            # Convert numpy array to bytes
            if isinstance(image, np.ndarray):
                image_pil = Image.fromarray(image)
                img_byte_arr = io.BytesIO()
                image_pil.save(img_byte_arr, format='PNG')
                content = img_byte_arr.getvalue()
            else:
                content = image

            # Create vision image
            vision_image = vision.Image(content=content)

            # Perform OCR
            response = self._client.document_text_detection(
                image=vision_image,
                image_context={"language_hints": [language]}
            )

            if response.error.message:
                raise Exception(response.error.message)

            # Extract full text
            text = response.full_text_annotation.text if response.full_text_annotation else ""

            # Extract detailed information
            words = []
            lines = []
            blocks = []

            if response.full_text_annotation:
                for page in response.full_text_annotation.pages:
                    for block in page.blocks:
                        block_words = []
                        block_text = ""

                        for paragraph in block.paragraphs:
                            for word in paragraph.words:
                                word_text = "".join([symbol.text for symbol in word.symbols])
                                word_confidence = word.confidence

                                # Get bounding box
                                vertices = word.bounding_box.vertices
                                bbox = {
                                    "x": vertices[0].x,
                                    "y": vertices[0].y,
                                    "width": vertices[1].x - vertices[0].x,
                                    "height": vertices[2].y - vertices[0].y,
                                }

                                word_dict = {
                                    "text": word_text,
                                    "confidence": word_confidence,
                                    "bbox": bbox,
                                }
                                words.append(word_dict)
                                block_words.append(word_dict)
                                block_text += word_text + " "

                        if block_words:
                            avg_conf = sum(w["confidence"] for w in block_words) / len(block_words)
                            blocks.append({
                                "text": block_text.strip(),
                                "confidence": avg_conf,
                                "words": block_words,
                            })

            # Calculate overall confidence
            overall_confidence = (
                sum(w["confidence"] for w in words) / len(words)
                if words else 0.0
            )

            return OCRResult(
                text=text,
                confidence=overall_confidence,
                words=words,
                lines=lines,
                blocks=blocks,
                metadata={"engine": "google_vision", "language": language}
            )

        except Exception as e:
            self.logger.error(f"Google Vision OCR error: {e}")
            raise


class AzureOCR(OCREngine):
    """Azure Computer Vision OCR Engine"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._client = None
        self._initialize()

    def _initialize(self):
        """Initialize Azure Computer Vision client"""
        try:
            from azure.cognitiveservices.vision.computervision import ComputerVisionClient
            from msrest.authentication import CognitiveServicesCredentials

            endpoint = self.config.get("endpoint")
            key = self.config.get("key")

            if endpoint and key:
                self._client = ComputerVisionClient(
                    endpoint,
                    CognitiveServicesCredentials(key)
                )
                self.logger.info("Azure OCR initialized successfully")
            else:
                self.logger.warning("Azure credentials not provided")

        except ImportError:
            self.logger.warning("azure-cognitiveservices-vision-computervision not installed")
        except Exception as e:
            self.logger.error(f"Error initializing Azure OCR: {e}")

    def is_available(self) -> bool:
        """Check if Azure OCR is available"""
        return self._client is not None

    def process_image(
        self,
        image: np.ndarray,
        language: str = "eng",
        **kwargs
    ) -> OCRResult:
        """Process image with Azure OCR"""
        if not self.is_available():
            raise RuntimeError("Azure OCR is not available")

        try:
            import time

            # Convert numpy array to bytes
            if isinstance(image, np.ndarray):
                image_pil = Image.fromarray(image)
                img_byte_arr = io.BytesIO()
                image_pil.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                image_data = img_byte_arr
            else:
                image_data = image

            # Start OCR operation
            read_operation = self._client.read_in_stream(image_data, raw=True)
            operation_location = read_operation.headers["Operation-Location"]
            operation_id = operation_location.split("/")[-1]

            # Wait for completion
            while True:
                result = self._client.get_read_result(operation_id)
                if result.status.lower() not in ['notstarted', 'running']:
                    break
                time.sleep(1)

            # Extract text
            text = ""
            words = []
            lines = []

            if result.status.lower() == 'succeeded':
                for page in result.analyze_result.read_results:
                    for line in page.lines:
                        text += line.text + "\n"
                        line_words = []

                        for word in line.words:
                            bbox = word.bounding_box
                            word_dict = {
                                "text": word.text,
                                "confidence": word.confidence,
                                "bbox": {
                                    "x": bbox[0],
                                    "y": bbox[1],
                                    "width": bbox[2] - bbox[0],
                                    "height": bbox[5] - bbox[1],
                                },
                            }
                            words.append(word_dict)
                            line_words.append(word_dict)

                        lines.append({
                            "text": line.text,
                            "confidence": sum(w["confidence"] for w in line_words) / len(line_words) if line_words else 0.0,
                            "words": line_words,
                        })

            # Calculate overall confidence
            overall_confidence = (
                sum(w["confidence"] for w in words) / len(words)
                if words else 0.0
            )

            return OCRResult(
                text=text.strip(),
                confidence=overall_confidence,
                words=words,
                lines=lines,
                blocks=[],
                metadata={"engine": "azure", "language": language}
            )

        except Exception as e:
            self.logger.error(f"Azure OCR error: {e}")
            raise


class AWSOCR(OCREngine):
    """AWS Textract OCR Engine"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._client = None
        self._initialize()

    def _initialize(self):
        """Initialize AWS Textract client"""
        try:
            import boto3

            aws_access_key_id = self.config.get("access_key_id")
            aws_secret_access_key = self.config.get("secret_access_key")
            region = self.config.get("region", "us-east-1")

            if aws_access_key_id and aws_secret_access_key:
                self._client = boto3.client(
                    'textract',
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    region_name=region
                )
                self.logger.info("AWS Textract initialized successfully")
            else:
                # Try default credentials
                try:
                    self._client = boto3.client('textract', region_name=region)
                    self.logger.info("AWS Textract initialized with default credentials")
                except:
                    self.logger.warning("AWS credentials not provided")

        except ImportError:
            self.logger.warning("boto3 not installed")
        except Exception as e:
            self.logger.error(f"Error initializing AWS Textract: {e}")

    def is_available(self) -> bool:
        """Check if AWS Textract is available"""
        return self._client is not None

    def process_image(
        self,
        image: np.ndarray,
        language: str = "eng",
        **kwargs
    ) -> OCRResult:
        """Process image with AWS Textract"""
        if not self.is_available():
            raise RuntimeError("AWS Textract is not available")

        try:
            # Convert numpy array to bytes
            if isinstance(image, np.ndarray):
                image_pil = Image.fromarray(image)
                img_byte_arr = io.BytesIO()
                image_pil.save(img_byte_arr, format='PNG')
                image_bytes = img_byte_arr.getvalue()
            else:
                image_bytes = image

            # Call Textract
            response = self._client.detect_document_text(
                Document={'Bytes': image_bytes}
            )

            # Extract text and details
            text = ""
            words = []
            lines = []

            for block in response['Blocks']:
                if block['BlockType'] == 'LINE':
                    text += block['Text'] + "\n"
                    line_words = []

                    # Get word-level details
                    for relationship in block.get('Relationships', []):
                        if relationship['Type'] == 'CHILD':
                            for word_id in relationship['Ids']:
                                # Find word block
                                word_block = next(
                                    (b for b in response['Blocks'] if b['Id'] == word_id),
                                    None
                                )
                                if word_block and word_block['BlockType'] == 'WORD':
                                    bbox = word_block['Geometry']['BoundingBox']
                                    word_dict = {
                                        "text": word_block['Text'],
                                        "confidence": word_block['Confidence'] / 100.0,
                                        "bbox": {
                                            "x": bbox['Left'],
                                            "y": bbox['Top'],
                                            "width": bbox['Width'],
                                            "height": bbox['Height'],
                                        },
                                    }
                                    words.append(word_dict)
                                    line_words.append(word_dict)

                    lines.append({
                        "text": block['Text'],
                        "confidence": block['Confidence'] / 100.0,
                        "words": line_words,
                    })

            # Calculate overall confidence
            overall_confidence = (
                sum(w["confidence"] for w in words) / len(words)
                if words else 0.0
            )

            return OCRResult(
                text=text.strip(),
                confidence=overall_confidence,
                words=words,
                lines=lines,
                blocks=[],
                metadata={"engine": "aws_textract", "language": language}
            )

        except Exception as e:
            self.logger.error(f"AWS Textract error: {e}")
            raise


class OpenAIGPT4VisionOCR(OCREngine):
    """OpenAI GPT-4 Vision OCR Engine"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._client = None
        self._initialize()

    def _initialize(self):
        """Initialize OpenAI client"""
        try:
            from openai import OpenAI

            api_key = self.config.get("api_key")
            if api_key:
                self._client = OpenAI(api_key=api_key)
                self.logger.info("OpenAI GPT-4 Vision initialized successfully")
            else:
                self.logger.warning("OpenAI API key not provided")

        except ImportError:
            self.logger.warning("openai package not installed")
        except Exception as e:
            self.logger.error(f"Error initializing OpenAI: {e}")

    def is_available(self) -> bool:
        """Check if OpenAI is available"""
        return self._client is not None

    def process_image(
        self,
        image: np.ndarray,
        language: str = "eng",
        **kwargs
    ) -> OCRResult:
        """Process image with GPT-4 Vision"""
        if not self.is_available():
            raise RuntimeError("OpenAI GPT-4 Vision is not available")

        try:
            # Convert numpy array to base64
            if isinstance(image, np.ndarray):
                image_pil = Image.fromarray(image)
                img_byte_arr = io.BytesIO()
                image_pil.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                image_base64 = base64.b64encode(img_byte_arr.read()).decode('utf-8')
            else:
                image_base64 = base64.b64encode(image).decode('utf-8')

            # Create prompt
            prompt = kwargs.get(
                "prompt",
                "Extract all text from this image. Preserve the layout and formatting as much as possible."
            )

            # Call GPT-4 Vision
            response = self._client.chat.completions.create(
                model=self.config.get("model", "gpt-4-vision-preview"),
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4096,
            )

            text = response.choices[0].message.content

            # GPT-4 Vision doesn't provide word-level details
            return OCRResult(
                text=text,
                confidence=0.95,  # Assumed high confidence
                words=[],
                lines=[],
                blocks=[],
                metadata={
                    "engine": "openai_gpt4_vision",
                    "model": self.config.get("model"),
                    "language": language
                }
            )

        except Exception as e:
            self.logger.error(f"OpenAI GPT-4 Vision error: {e}")
            raise


class OCREngineFactory:
    """Factory for creating OCR engines"""

    @staticmethod
    def create_engine(
        engine_type: str,
        config: Optional[Dict[str, Any]] = None
    ) -> OCREngine:
        """Create OCR engine by type"""
        engines = {
            "tesseract": TesseractOCR,
            "google_vision": GoogleVisionOCR,
            "azure": AzureOCR,
            "aws": AWSOCR,
            "aws_textract": AWSOCR,
            "openai": OpenAIGPT4VisionOCR,
            "gpt4_vision": OpenAIGPT4VisionOCR,
        }

        engine_class = engines.get(engine_type.lower())
        if not engine_class:
            raise ValueError(f"Unknown engine type: {engine_type}")

        return engine_class(config)

    @staticmethod
    def get_available_engines(config_dict: Dict[str, Dict[str, Any]]) -> List[str]:
        """Get list of available engines"""
        available = []
        for engine_type in ["tesseract", "google_vision", "azure", "aws", "openai"]:
            try:
                engine = OCREngineFactory.create_engine(
                    engine_type,
                    config_dict.get(engine_type)
                )
                if engine.is_available():
                    available.append(engine_type)
            except:
                pass
        return available
