"""
UI Element Detector - Detects and identifies UI elements for automation
"""
from typing import List, Dict, Any, Optional, Tuple
import time

try:
    import pyautogui
    import cv2
    import numpy as np
    from PIL import Image
    import pytesseract
    UI_DETECTION_AVAILABLE = True
except ImportError:
    UI_DETECTION_AVAILABLE = False

from src.utils.logger import get_logger
from src.config.settings import settings

logger = get_logger(__name__)


class UIElementDetector:
    """Detects and identifies UI elements on screen"""

    def __init__(self):
        self.screenshot_dir = settings.RPA_SCREENSHOT_DIR

    def capture_screen(
        self, region: Optional[Tuple[int, int, int, int]] = None
    ) -> Optional[np.ndarray]:
        """
        Capture screen or region

        Args:
            region: (x, y, width, height) tuple for region capture

        Returns:
            numpy array of the captured image
        """
        if not UI_DETECTION_AVAILABLE:
            logger.error("UI detection libraries not available")
            return None

        try:
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()

            # Convert to numpy array
            return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        except Exception as e:
            logger.error(f"Failed to capture screen: {str(e)}")
            return None

    def find_element_by_image(
        self,
        template_path: str,
        confidence: float = 0.8,
        grayscale: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Find UI element by template matching

        Args:
            template_path: Path to template image
            confidence: Matching confidence threshold (0-1)
            grayscale: Whether to use grayscale matching

        Returns:
            Dictionary with element location and confidence
        """
        if not UI_DETECTION_AVAILABLE:
            logger.error("UI detection libraries not available")
            return None

        try:
            location = pyautogui.locateOnScreen(
                template_path, confidence=confidence, grayscale=grayscale
            )

            if location:
                center = pyautogui.center(location)
                return {
                    "found": True,
                    "x": center.x,
                    "y": center.y,
                    "left": location.left,
                    "top": location.top,
                    "width": location.width,
                    "height": location.height,
                }
            else:
                return {"found": False}
        except Exception as e:
            logger.error(f"Failed to find element: {str(e)}")
            return {"found": False, "error": str(e)}

    def find_all_elements_by_image(
        self,
        template_path: str,
        confidence: float = 0.8,
        grayscale: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Find all occurrences of UI element by template matching

        Args:
            template_path: Path to template image
            confidence: Matching confidence threshold (0-1)
            grayscale: Whether to use grayscale matching

        Returns:
            List of dictionaries with element locations
        """
        if not UI_DETECTION_AVAILABLE:
            logger.error("UI detection libraries not available")
            return []

        try:
            locations = list(
                pyautogui.locateAllOnScreen(
                    template_path, confidence=confidence, grayscale=grayscale
                )
            )

            elements = []
            for location in locations:
                center = pyautogui.center(location)
                elements.append(
                    {
                        "x": center.x,
                        "y": center.y,
                        "left": location.left,
                        "top": location.top,
                        "width": location.width,
                        "height": location.height,
                    }
                )

            return elements
        except Exception as e:
            logger.error(f"Failed to find elements: {str(e)}")
            return []

    def detect_text_on_screen(
        self, region: Optional[Tuple[int, int, int, int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect text on screen using OCR

        Args:
            region: (x, y, width, height) tuple for region

        Returns:
            List of detected text elements with locations
        """
        if not UI_DETECTION_AVAILABLE:
            logger.error("UI detection libraries not available")
            return []

        try:
            # Capture screen
            screen = self.capture_screen(region)
            if screen is None:
                return []

            # Perform OCR
            data = pytesseract.image_to_data(
                screen, output_type=pytesseract.Output.DICT
            )

            text_elements = []
            n_boxes = len(data["text"])

            for i in range(n_boxes):
                text = data["text"][i].strip()
                if text:
                    confidence = int(data["conf"][i])
                    if confidence > 0:
                        text_elements.append(
                            {
                                "text": text,
                                "confidence": confidence,
                                "x": data["left"][i],
                                "y": data["top"][i],
                                "width": data["width"][i],
                                "height": data["height"][i],
                            }
                        )

            return text_elements
        except Exception as e:
            logger.error(f"Failed to detect text: {str(e)}")
            return []

    def find_text_location(
        self, text: str, region: Optional[Tuple[int, int, int, int]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find location of specific text on screen

        Args:
            text: Text to search for
            region: (x, y, width, height) tuple for region

        Returns:
            Dictionary with text location or None
        """
        text_elements = self.detect_text_on_screen(region)

        for element in text_elements:
            if text.lower() in element["text"].lower():
                return element

        return None

    def detect_color_at_position(
        self, x: int, y: int
    ) -> Optional[Tuple[int, int, int]]:
        """
        Detect color at specific position

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            (R, G, B) color tuple
        """
        if not UI_DETECTION_AVAILABLE:
            logger.error("UI detection libraries not available")
            return None

        try:
            screen = self.capture_screen()
            if screen is None:
                return None

            # OpenCV uses BGR, convert to RGB
            color = screen[y, x]
            return (int(color[2]), int(color[1]), int(color[0]))
        except Exception as e:
            logger.error(f"Failed to detect color: {str(e)}")
            return None

    def wait_for_element(
        self,
        template_path: str,
        timeout: int = 10,
        confidence: float = 0.8,
        check_interval: float = 0.5,
    ) -> Optional[Dict[str, Any]]:
        """
        Wait for element to appear on screen

        Args:
            template_path: Path to template image
            timeout: Maximum time to wait in seconds
            confidence: Matching confidence threshold
            check_interval: Time between checks in seconds

        Returns:
            Element location if found, None otherwise
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            element = self.find_element_by_image(template_path, confidence)

            if element and element.get("found"):
                return element

            time.sleep(check_interval)

        logger.warning(
            f"Element not found after {timeout} seconds: {template_path}"
        )
        return None

    def save_element_screenshot(
        self, x: int, y: int, width: int, height: int, filename: str
    ) -> bool:
        """
        Save screenshot of specific element

        Args:
            x, y: Top-left coordinates
            width, height: Element dimensions
            filename: Output filename

        Returns:
            True if successful
        """
        if not UI_DETECTION_AVAILABLE:
            logger.error("UI detection libraries not available")
            return False

        try:
            region = (x, y, width, height)
            screenshot = pyautogui.screenshot(region=region)
            screenshot.save(filename)
            logger.info(f"Saved element screenshot to {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to save screenshot: {str(e)}")
            return False

    def compare_images(
        self, image1_path: str, image2_path: str
    ) -> Dict[str, Any]:
        """
        Compare two images and return similarity score

        Args:
            image1_path: Path to first image
            image2_path: Path to second image

        Returns:
            Dictionary with similarity metrics
        """
        if not UI_DETECTION_AVAILABLE:
            logger.error("UI detection libraries not available")
            return {"error": "Libraries not available"}

        try:
            img1 = cv2.imread(image1_path, cv2.IMREAD_GRAYSCALE)
            img2 = cv2.imread(image2_path, cv2.IMREAD_GRAYSCALE)

            # Resize images to same size
            height = min(img1.shape[0], img2.shape[0])
            width = min(img1.shape[1], img2.shape[1])

            img1 = cv2.resize(img1, (width, height))
            img2 = cv2.resize(img2, (width, height))

            # Calculate difference
            difference = cv2.absdiff(img1, img2)
            similarity = 100 - (np.sum(difference) / (height * width * 255) * 100)

            return {
                "similarity": round(similarity, 2),
                "different_pixels": int(np.sum(difference > 0)),
                "total_pixels": height * width,
            }
        except Exception as e:
            logger.error(f"Failed to compare images: {str(e)}")
            return {"error": str(e)}
