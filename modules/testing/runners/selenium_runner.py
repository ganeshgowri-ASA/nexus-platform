"""
Selenium runner for E2E tests
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.common.exceptions import TimeoutException, WebDriverException
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
import json


class SeleniumRunner:
    """Runner for executing Selenium E2E tests"""

    def __init__(
        self,
        browser: str = "chrome",
        headless: bool = True,
        implicit_wait: int = 10,
        page_load_timeout: int = 30
    ):
        self.browser = browser
        self.headless = headless
        self.implicit_wait = implicit_wait
        self.page_load_timeout = page_load_timeout
        self.driver = None
        self.screenshots_dir = "/tmp/nexus_screenshots"
        os.makedirs(self.screenshots_dir, exist_ok=True)

    def setup_driver(self):
        """Setup Selenium WebDriver"""
        if self.browser == "chrome":
            options = ChromeOptions()
            if self.headless:
                options.add_argument("--headless")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")

            self.driver = webdriver.Chrome(options=options)

        elif self.browser == "firefox":
            options = FirefoxOptions()
            if self.headless:
                options.add_argument("--headless")

            self.driver = webdriver.Firefox(options=options)

        else:
            raise ValueError(f"Unsupported browser: {self.browser}")

        self.driver.implicitly_wait(self.implicit_wait)
        self.driver.set_page_load_timeout(self.page_load_timeout)

    def teardown_driver(self):
        """Teardown Selenium WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def run_test_scenario(
        self,
        test_name: str,
        steps: List[Dict[str, Any]],
        base_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run a test scenario with multiple steps

        Args:
            test_name: Name of the test
            steps: List of test steps
            base_url: Base URL for the application

        Returns:
            Dict with test results

        Step format:
        {
            "action": "navigate|click|type|wait|assert_text|assert_element",
            "target": "element_selector or URL",
            "value": "optional value for type actions",
            "by": "id|xpath|css|name|class_name",
            "timeout": 10
        }
        """
        start_time = datetime.utcnow()
        results = {
            "test_name": test_name,
            "status": "passed",
            "steps": [],
            "screenshots": [],
            "error": None
        }

        try:
            self.setup_driver()

            for i, step in enumerate(steps, 1):
                step_result = self._execute_step(step, i, base_url)
                results["steps"].append(step_result)

                if not step_result["success"]:
                    results["status"] = "failed"
                    results["error"] = step_result.get("error")

                    # Take screenshot on failure
                    screenshot_path = self._take_screenshot(f"{test_name}_step_{i}_failed")
                    results["screenshots"].append(screenshot_path)
                    break

        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)

            # Take screenshot on error
            if self.driver:
                screenshot_path = self._take_screenshot(f"{test_name}_error")
                results["screenshots"].append(screenshot_path)

        finally:
            self.teardown_driver()

        end_time = datetime.utcnow()
        results["duration"] = (end_time - start_time).total_seconds()
        results["start_time"] = start_time.isoformat()
        results["end_time"] = end_time.isoformat()

        return results

    def _execute_step(
        self,
        step: Dict[str, Any],
        step_number: int,
        base_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a single test step"""
        action = step.get("action")
        target = step.get("target")
        value = step.get("value")
        by = step.get("by", "id")
        timeout = step.get("timeout", 10)

        step_result = {
            "step_number": step_number,
            "action": action,
            "target": target,
            "success": False,
            "error": None
        }

        try:
            if action == "navigate":
                url = target
                if base_url and not target.startswith("http"):
                    url = base_url + target
                self.driver.get(url)
                step_result["success"] = True

            elif action == "click":
                element = self._find_element(target, by, timeout)
                element.click()
                step_result["success"] = True

            elif action == "type":
                element = self._find_element(target, by, timeout)
                element.clear()
                element.send_keys(value)
                step_result["success"] = True

            elif action == "wait":
                import time
                time.sleep(int(value or 1))
                step_result["success"] = True

            elif action == "assert_text":
                element = self._find_element(target, by, timeout)
                actual_text = element.text
                if value and value not in actual_text:
                    raise AssertionError(f"Expected text '{value}' not found. Actual: '{actual_text}'")
                step_result["success"] = True

            elif action == "assert_element":
                self._find_element(target, by, timeout)
                step_result["success"] = True

            elif action == "screenshot":
                screenshot_path = self._take_screenshot(value or f"step_{step_number}")
                step_result["success"] = True
                step_result["screenshot"] = screenshot_path

            else:
                raise ValueError(f"Unknown action: {action}")

        except Exception as e:
            step_result["success"] = False
            step_result["error"] = str(e)

        return step_result

    def _find_element(self, selector: str, by: str = "id", timeout: int = 10):
        """Find element with explicit wait"""
        by_map = {
            "id": By.ID,
            "xpath": By.XPATH,
            "css": By.CSS_SELECTOR,
            "name": By.NAME,
            "class_name": By.CLASS_NAME,
            "tag_name": By.TAG_NAME,
            "link_text": By.LINK_TEXT,
            "partial_link_text": By.PARTIAL_LINK_TEXT
        }

        by_type = by_map.get(by, By.ID)

        wait = WebDriverWait(self.driver, timeout)
        element = wait.until(
            EC.presence_of_element_located((by_type, selector))
        )

        return element

    def _take_screenshot(self, name: str) -> str:
        """Take screenshot and return path"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = os.path.join(self.screenshots_dir, filename)

        if self.driver:
            self.driver.save_screenshot(filepath)

        return filepath

    def run_page_performance_test(self, url: str) -> Dict[str, Any]:
        """
        Run basic performance test for a page

        Args:
            url: URL to test

        Returns:
            Dict with performance metrics
        """
        try:
            self.setup_driver()

            # Navigate to page
            start_time = datetime.utcnow()
            self.driver.get(url)
            end_time = datetime.utcnow()

            # Calculate page load time
            page_load_time = (end_time - start_time).total_seconds()

            # Get performance timing data
            navigation_start = self.driver.execute_script("return window.performance.timing.navigationStart")
            response_start = self.driver.execute_script("return window.performance.timing.responseStart")
            dom_complete = self.driver.execute_script("return window.performance.timing.domComplete")

            return {
                "url": url,
                "page_load_time": page_load_time,
                "time_to_first_byte": (response_start - navigation_start) / 1000,
                "dom_load_time": (dom_complete - navigation_start) / 1000,
                "status": "completed"
            }

        except Exception as e:
            return {
                "url": url,
                "status": "failed",
                "error": str(e)
            }

        finally:
            self.teardown_driver()
