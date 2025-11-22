"""
Language Module

Language detection, multilingual OCR, and script detection.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import re

logger = logging.getLogger(__name__)


class LanguageDetection:
    """Detect language from text"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.LanguageDetection")
        self._detector = None
        self._initialize()

    def _initialize(self):
        """Initialize language detector"""
        try:
            from langdetect import detect, detect_langs
            self._detector = detect
            self._detect_langs = detect_langs
            self.logger.info("Language detector initialized")
        except ImportError:
            self.logger.warning("langdetect not installed")

    def detect(self, text: str) -> str:
        """
        Detect language from text

        Args:
            text: Input text

        Returns:
            Language code (e.g., 'en', 'fr', 'de')
        """
        try:
            if self._detector and len(text.strip()) > 20:
                return self._detector(text)
            return "en"  # Default
        except Exception as e:
            self.logger.error(f"Error detecting language: {e}")
            return "en"

    def detect_with_confidence(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect language with confidence scores

        Args:
            text: Input text

        Returns:
            List of language detections with probabilities
        """
        try:
            if self._detect_langs and len(text.strip()) > 20:
                langs = self._detect_langs(text)
                return [
                    {'lang': lang.lang, 'prob': lang.prob}
                    for lang in langs
                ]
            return [{'lang': 'en', 'prob': 1.0}]
        except Exception as e:
            self.logger.error(f"Error detecting languages: {e}")
            return [{'lang': 'en', 'prob': 1.0}]

    def is_multilingual(self, text: str, threshold: float = 0.3) -> bool:
        """
        Check if text contains multiple languages

        Args:
            text: Input text
            threshold: Minimum probability for secondary language

        Returns:
            Whether text is multilingual
        """
        try:
            langs = self.detect_with_confidence(text)
            return len(langs) > 1 and langs[1]['prob'] > threshold
        except:
            return False


class ScriptDetection:
    """Detect writing script (Latin, Arabic, Chinese, etc.)"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ScriptDetection")

    def detect_script(self, text: str) -> str:
        """
        Detect writing script

        Args:
            text: Input text

        Returns:
            Script name
        """
        try:
            # Count characters by script
            latin = len(re.findall(r'[a-zA-Z]', text))
            arabic = len(re.findall(r'[\u0600-\u06FF]', text))
            chinese = len(re.findall(r'[\u4E00-\u9FFF]', text))
            japanese = len(re.findall(r'[\u3040-\u30FF]', text))
            korean = len(re.findall(r'[\uAC00-\uD7AF]', text))
            cyrillic = len(re.findall(r'[\u0400-\u04FF]', text))

            # Determine dominant script
            scripts = {
                'latin': latin,
                'arabic': arabic,
                'chinese': chinese,
                'japanese': japanese,
                'korean': korean,
                'cyrillic': cyrillic,
            }

            dominant = max(scripts, key=scripts.get)
            return dominant if scripts[dominant] > 0 else 'latin'

        except Exception as e:
            self.logger.error(f"Error detecting script: {e}")
            return 'latin'

    def get_script_info(self, text: str) -> Dict[str, Any]:
        """
        Get detailed script information

        Args:
            text: Input text

        Returns:
            Script information dictionary
        """
        try:
            total_chars = len([c for c in text if not c.isspace()])
            if total_chars == 0:
                return {'dominant': 'unknown', 'scripts': {}}

            latin = len(re.findall(r'[a-zA-Z]', text))
            arabic = len(re.findall(r'[\u0600-\u06FF]', text))
            chinese = len(re.findall(r'[\u4E00-\u9FFF]', text))
            japanese = len(re.findall(r'[\u3040-\u30FF]', text))
            korean = len(re.findall(r'[\uAC00-\uD7AF]', text))
            cyrillic = len(re.findall(r'[\u0400-\u04FF]', text))

            scripts = {
                'latin': latin / total_chars,
                'arabic': arabic / total_chars,
                'chinese': chinese / total_chars,
                'japanese': japanese / total_chars,
                'korean': korean / total_chars,
                'cyrillic': cyrillic / total_chars,
            }

            dominant = max(scripts, key=scripts.get)

            return {
                'dominant': dominant,
                'scripts': scripts,
                'is_mixed': sum(1 for v in scripts.values() if v > 0.1) > 1
            }

        except Exception as e:
            self.logger.error(f"Error getting script info: {e}")
            return {'dominant': 'unknown', 'scripts': {}}


class MultilingualOCR:
    """Handle multilingual OCR"""

    # Language code mappings
    LANGUAGE_CODES = {
        'en': 'eng', 'english': 'eng',
        'fr': 'fra', 'french': 'fra',
        'de': 'deu', 'german': 'deu',
        'es': 'spa', 'spanish': 'spa',
        'it': 'ita', 'italian': 'ita',
        'pt': 'por', 'portuguese': 'por',
        'ru': 'rus', 'russian': 'rus',
        'zh': 'chi_sim', 'chinese': 'chi_sim',
        'ja': 'jpn', 'japanese': 'jpn',
        'ko': 'kor', 'korean': 'kor',
        'ar': 'ara', 'arabic': 'ara',
    }

    def __init__(self, ocr_engine=None):
        self.ocr_engine = ocr_engine
        self.lang_detector = LanguageDetection()
        self.script_detector = ScriptDetection()
        self.logger = logging.getLogger(f"{__name__}.MultilingualOCR")

    def process_multilingual(
        self,
        image,
        languages: Optional[List[str]] = None,
        auto_detect: bool = True
    ) -> Dict[str, Any]:
        """
        Process image with multilingual OCR

        Args:
            image: Input image
            languages: List of language codes
            auto_detect: Auto-detect language

        Returns:
            OCR result with language info
        """
        try:
            results = []

            # If languages not specified and auto-detect enabled
            if not languages and auto_detect:
                # Try with default language first
                if self.ocr_engine:
                    initial_result = self.ocr_engine.process_image(image, "eng")
                    detected_lang = self.lang_detector.detect(initial_result.text)
                    languages = [detected_lang]
                else:
                    languages = ['eng']

            # Process with each language
            if languages:
                for lang in languages:
                    tesseract_lang = self.get_tesseract_language(lang)
                    if self.ocr_engine:
                        result = self.ocr_engine.process_image(image, tesseract_lang)
                        results.append({
                            'language': lang,
                            'text': result.text,
                            'confidence': result.confidence,
                        })

            # Select best result
            if results:
                best_result = max(results, key=lambda r: r['confidence'])
                return best_result
            else:
                return {'language': 'eng', 'text': '', 'confidence': 0.0}

        except Exception as e:
            self.logger.error(f"Error in multilingual OCR: {e}")
            return {'language': 'eng', 'text': '', 'confidence': 0.0}

    def get_tesseract_language(self, lang_code: str) -> str:
        """
        Convert language code to Tesseract format

        Args:
            lang_code: Language code (e.g., 'en', 'fr')

        Returns:
            Tesseract language code
        """
        return self.LANGUAGE_CODES.get(lang_code.lower(), 'eng')

    def detect_and_process(self, image, **kwargs) -> Dict[str, Any]:
        """
        Auto-detect language and process

        Args:
            image: Input image
            **kwargs: Additional options

        Returns:
            OCR result with detected language
        """
        try:
            # First pass with English
            if self.ocr_engine:
                initial_result = self.ocr_engine.process_image(image, "eng")

                # Detect language
                detected_lang = self.lang_detector.detect(initial_result.text)

                # If not English, reprocess with detected language
                if detected_lang != 'en':
                    tesseract_lang = self.get_tesseract_language(detected_lang)
                    final_result = self.ocr_engine.process_image(image, tesseract_lang)
                    return {
                        'language': detected_lang,
                        'text': final_result.text,
                        'confidence': final_result.confidence,
                        'auto_detected': True,
                    }
                else:
                    return {
                        'language': 'en',
                        'text': initial_result.text,
                        'confidence': initial_result.confidence,
                        'auto_detected': True,
                    }
            else:
                return {'language': 'en', 'text': '', 'confidence': 0.0}

        except Exception as e:
            self.logger.error(f"Error in detect and process: {e}")
            return {'language': 'en', 'text': '', 'confidence': 0.0}

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return list(set(self.LANGUAGE_CODES.values()))
