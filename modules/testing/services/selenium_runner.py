"""
Selenium test runner for E2E testing
"""
import logging
import time
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SeleniumRunner:
    """Selenium-based E2E test runner"""

    def __init__(self, browser: str = "chrome", headless: bool = True):
        self.browser = browser
        self.headless = headless
        self.driver = None

    def _init_driver(self):
        """Initialize Selenium WebDriver"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options as ChromeOptions
            from selenium.webdriver.firefox.options import Options as FirefoxOptions

            if self.browser == "chrome":
                options = ChromeOptions()
                if self.headless:
                    options.add_argument("--headless")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                self.driver = webdriver.Chrome(options=options)

            elif self.browser == "firefox":
                options = FirefoxOptions()
                if self.headless:
                    options.add_argument("--headless")
                self.driver = webdriver.Firefox(options=options)

            else:
                raise ValueError(f"Unsupported browser: {self.browser}")

            self.driver.implicitly_wait(10)

        except Exception as e:
            logger.error(f"WebDriver initialization error: {e}")
            raise

    def run_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Run E2E test"""
        screenshots = []

        try:
            self._init_driver()

            start_time = time.time()

            # Execute test steps
            test_data = test_case.get("test_data", {})
            url = test_data.get("url")

            if not url:
                return {
                    "status": "error",
                    "error_message": "No URL provided for E2E test"
                }

            # Navigate to URL
            self.driver.get(url)

            # Execute test actions
            actions = test_data.get("actions", [])
            for action in actions:
                self._execute_action(action)

            # Take screenshot
            screenshot_path = self._take_screenshot(test_case["id"])
            if screenshot_path:
                screenshots.append(screenshot_path)

            duration = time.time() - start_time

            return {
                "status": "passed",
                "duration_seconds": duration,
                "output": "E2E test passed successfully",
                "screenshots": screenshots
            }

        except Exception as e:
            logger.error(f"E2E test execution error: {e}")

            # Take error screenshot
            try:
                screenshot_path = self._take_screenshot(test_case["id"], suffix="_error")
                if screenshot_path:
                    screenshots.append(screenshot_path)
            except:
                pass

            return {
                "status": "failed",
                "error_message": str(e),
                "screenshots": screenshots
            }

        finally:
            if self.driver:
                self.driver.quit()

    def _execute_action(self, action: Dict[str, Any]):
        """Execute a single test action"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        action_type = action.get("type")
        selector = action.get("selector")
        value = action.get("value")

        # Map selector type
        by_type = {
            "id": By.ID,
            "name": By.NAME,
            "xpath": By.XPATH,
            "css": By.CSS_SELECTOR,
            "class": By.CLASS_NAME
        }.get(action.get("selector_type", "css"), By.CSS_SELECTOR)

        if action_type == "click":
            element = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((by_type, selector))
            )
            element.click()

        elif action_type == "input":
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((by_type, selector))
            )
            element.clear()
            element.send_keys(value)

        elif action_type == "wait":
            time.sleep(value or 1)

        elif action_type == "assert_text":
            element = self.driver.find_element(by_type, selector)
            assert value in element.text, f"Expected text '{value}' not found"

        elif action_type == "assert_visible":
            element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((by_type, selector))
            )

    def _take_screenshot(self, test_id: int, suffix: str = "") -> Optional[str]:
        """Take screenshot"""
        try:
            screenshots_dir = Path("./screenshots")
            screenshots_dir.mkdir(parents=True, exist_ok=True)

            filename = f"test_{test_id}{suffix}_{int(time.time())}.png"
            filepath = screenshots_dir / filename

            self.driver.save_screenshot(str(filepath))

            return str(filepath)

        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return None
