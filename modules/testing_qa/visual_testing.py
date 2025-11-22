"""
Visual Testing Module

Provides ScreenshotComparison, VisualRegression, and PixelDiff for visual testing.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from PIL import Image, ImageChops, ImageStat
import numpy as np

logger = logging.getLogger(__name__)


class PixelDiff:
    """
    Pixel-level image difference calculator.

    Compares images at pixel level and calculates differences.
    """

    def __init__(self):
        """Initialize pixel diff calculator."""
        self.logger = logging.getLogger(__name__)

    def compare_images(
        self,
        image1_path: str,
        image2_path: str,
        threshold: float = 0.1,
    ) -> Dict[str, Any]:
        """
        Compare two images pixel by pixel.

        Args:
            image1_path: Path to first image
            image2_path: Path to second image
            threshold: Difference threshold (0-1)

        Returns:
            Comparison result
        """
        try:
            img1 = Image.open(image1_path)
            img2 = Image.open(image2_path)

            # Resize if dimensions don't match
            if img1.size != img2.size:
                img2 = img2.resize(img1.size)

            # Calculate difference
            diff = ImageChops.difference(img1, img2)

            # Calculate statistics
            stat = ImageStat.Stat(diff)
            mean_diff = sum(stat.mean) / len(stat.mean) / 255.0

            is_identical = mean_diff < threshold

            return {
                "identical": is_identical,
                "difference_percentage": mean_diff * 100,
                "threshold_percentage": threshold * 100,
                "image1_size": img1.size,
                "image2_size": img2.size,
            }

        except Exception as e:
            self.logger.error(f"Image comparison failed: {e}")
            return {
                "identical": False,
                "error": str(e),
            }

    def generate_diff_image(
        self,
        image1_path: str,
        image2_path: str,
        output_path: str,
    ) -> str:
        """
        Generate visual diff image.

        Args:
            image1_path: Path to first image
            image2_path: Path to second image
            output_path: Output path for diff image

        Returns:
            Output path
        """
        try:
            img1 = Image.open(image1_path)
            img2 = Image.open(image2_path)

            if img1.size != img2.size:
                img2 = img2.resize(img1.size)

            diff = ImageChops.difference(img1, img2)

            # Enhance differences
            diff = diff.convert("RGB")
            enhancer = ImageEnhance.Contrast(diff)
            diff = enhancer.enhance(10.0)

            diff.save(output_path)
            self.logger.info(f"Diff image saved: {output_path}")

            return output_path

        except Exception as e:
            self.logger.error(f"Failed to generate diff image: {e}")
            return None


class ScreenshotComparison:
    """
    Screenshot comparison for visual regression testing.

    Compares screenshots and detects visual changes.
    """

    def __init__(self, baseline_dir: str = "baselines", threshold: float = 0.1):
        """
        Initialize screenshot comparison.

        Args:
            baseline_dir: Directory for baseline screenshots
            threshold: Difference threshold
        """
        self.baseline_dir = Path(baseline_dir)
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        self.threshold = threshold
        self.pixel_diff = PixelDiff()
        self.logger = logging.getLogger(__name__)

    def save_baseline(
        self,
        screenshot_path: str,
        name: str,
    ) -> str:
        """
        Save screenshot as baseline.

        Args:
            screenshot_path: Path to screenshot
            name: Baseline name

        Returns:
            Baseline path
        """
        baseline_path = self.baseline_dir / f"{name}.png"

        img = Image.open(screenshot_path)
        img.save(baseline_path)

        self.logger.info(f"Baseline saved: {baseline_path}")
        return str(baseline_path)

    def compare_with_baseline(
        self,
        screenshot_path: str,
        baseline_name: str,
    ) -> Dict[str, Any]:
        """
        Compare screenshot with baseline.

        Args:
            screenshot_path: Path to screenshot
            baseline_name: Baseline name

        Returns:
            Comparison result
        """
        baseline_path = self.baseline_dir / f"{baseline_name}.png"

        if not baseline_path.exists():
            return {
                "passed": False,
                "error": f"Baseline not found: {baseline_name}",
            }

        result = self.pixel_diff.compare_images(
            str(baseline_path),
            screenshot_path,
            self.threshold,
        )

        result["passed"] = result.get("identical", False)
        result["baseline_name"] = baseline_name

        return result


class VisualRegression:
    """
    Visual regression testing framework.

    Orchestrates visual regression tests across multiple pages/components.
    """

    def __init__(self, baseline_dir: str = "visual-baselines"):
        """
        Initialize visual regression tester.

        Args:
            baseline_dir: Directory for baselines
        """
        self.screenshot_comparison = ScreenshotComparison(baseline_dir)
        self.logger = logging.getLogger(__name__)
        self.test_results: List[Dict[str, Any]] = []

    def test_screenshot(
        self,
        screenshot_path: str,
        test_name: str,
        update_baseline: bool = False,
    ) -> Dict[str, Any]:
        """
        Test a screenshot against baseline.

        Args:
            screenshot_path: Path to screenshot
            test_name: Test name
            update_baseline: Whether to update baseline

        Returns:
            Test result
        """
        if update_baseline:
            self.screenshot_comparison.save_baseline(screenshot_path, test_name)
            result = {
                "test_name": test_name,
                "passed": True,
                "message": "Baseline updated",
            }
        else:
            result = self.screenshot_comparison.compare_with_baseline(
                screenshot_path,
                test_name,
            )
            result["test_name"] = test_name

        self.test_results.append(result)
        return result

    def test_multiple_screenshots(
        self,
        screenshots: List[Tuple[str, str]],
        update_baselines: bool = False,
    ) -> Dict[str, Any]:
        """
        Test multiple screenshots.

        Args:
            screenshots: List of (path, name) tuples
            update_baselines: Whether to update baselines

        Returns:
            Aggregated results
        """
        results = []

        for screenshot_path, name in screenshots:
            result = self.test_screenshot(
                screenshot_path,
                name,
                update_baselines,
            )
            results.append(result)

        passed = sum(1 for r in results if r.get("passed"))
        failed = len(results) - passed

        return {
            "total_tests": len(results),
            "passed": passed,
            "failed": failed,
            "pass_rate": (passed / len(results) * 100) if results else 0,
            "results": results,
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get test summary."""
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r.get("passed"))

        return {
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": (passed / total * 100) if total > 0 else 0,
        }


# Import for enhancement (optional)
try:
    from PIL import ImageEnhance
except ImportError:
    ImageEnhance = None
