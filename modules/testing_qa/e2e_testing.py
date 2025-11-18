"""
End-to-End Testing Module

Provides E2ETestRunner, SeleniumTester, and PlaywrightTester for browser automation.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import time

logger = logging.getLogger(__name__)


class SeleniumTester:
    """
    Selenium-based browser tester.

    Uses Selenium WebDriver for browser automation testing.
    """

    def __init__(self, browser: str = "chrome", headless: bool = True):
        """
        Initialize Selenium tester.

        Args:
            browser: Browser to use (chrome, firefox, edge)
            headless: Run in headless mode
        """
        self.browser = browser
        self.headless = headless
        self.driver = None
        self.logger = logging.getLogger(__name__)
        self.screenshots: List[str] = []

    def start_browser(self) -> bool:
        """
        Start browser session.

        Returns:
            True if successful
        """
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

            self.logger.info(f"Started {self.browser} browser")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start browser: {e}")
            return False

    def navigate_to(self, url: str) -> Dict[str, Any]:
        """
        Navigate to URL.

        Args:
            url: URL to navigate to

        Returns:
            Navigation result
        """
        try:
            start_time = time.time()
            self.driver.get(url)
            load_time = (time.time() - start_time) * 1000

            return {
                "success": True,
                "url": url,
                "load_time_ms": load_time,
                "title": self.driver.title,
            }

        except Exception as e:
            self.logger.error(f"Navigation failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def find_element(self, selector: str, by: str = "css") -> Dict[str, Any]:
        """
        Find element on page.

        Args:
            selector: Element selector
            by: Selector type (css, xpath, id, name)

        Returns:
            Element information
        """
        try:
            from selenium.webdriver.common.by import By

            by_mapping = {
                "css": By.CSS_SELECTOR,
                "xpath": By.XPATH,
                "id": By.ID,
                "name": By.NAME,
                "class": By.CLASS_NAME,
                "tag": By.TAG_NAME,
            }

            element = self.driver.find_element(by_mapping.get(by, By.CSS_SELECTOR), selector)

            return {
                "success": True,
                "found": True,
                "text": element.text,
                "tag_name": element.tag_name,
                "is_displayed": element.is_displayed(),
                "is_enabled": element.is_enabled(),
            }

        except Exception as e:
            return {
                "success": False,
                "found": False,
                "error": str(e),
            }

    def click_element(self, selector: str, by: str = "css") -> Dict[str, Any]:
        """Click element."""
        try:
            from selenium.webdriver.common.by import By

            by_mapping = {
                "css": By.CSS_SELECTOR,
                "xpath": By.XPATH,
                "id": By.ID,
            }

            element = self.driver.find_element(by_mapping.get(by, By.CSS_SELECTOR), selector)
            element.click()

            return {
                "success": True,
                "action": "click",
                "selector": selector,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def input_text(self, selector: str, text: str, by: str = "css") -> Dict[str, Any]:
        """Input text into element."""
        try:
            from selenium.webdriver.common.by import By

            by_mapping = {
                "css": By.CSS_SELECTOR,
                "xpath": By.XPATH,
                "id": By.ID,
            }

            element = self.driver.find_element(by_mapping.get(by, By.CSS_SELECTOR), selector)
            element.clear()
            element.send_keys(text)

            return {
                "success": True,
                "action": "input",
                "selector": selector,
                "text_length": len(text),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def take_screenshot(self, filename: str = None) -> str:
        """Take screenshot."""
        try:
            if not filename:
                filename = f"screenshot_{int(time.time())}.png"

            self.driver.save_screenshot(filename)
            self.screenshots.append(filename)
            self.logger.info(f"Screenshot saved: {filename}")

            return filename

        except Exception as e:
            self.logger.error(f"Screenshot failed: {e}")
            return None

    def stop_browser(self) -> None:
        """Stop browser session."""
        if self.driver:
            self.driver.quit()
            self.logger.info("Browser stopped")


class PlaywrightTester:
    """
    Playwright-based browser tester.

    Modern browser automation with Playwright.
    """

    def __init__(self, browser: str = "chromium", headless: bool = True):
        """
        Initialize Playwright tester.

        Args:
            browser: Browser type (chromium, firefox, webkit)
            headless: Run in headless mode
        """
        self.browser_type = browser
        self.headless = headless
        self.browser = None
        self.page = None
        self.logger = logging.getLogger(__name__)
        self.screenshots: List[str] = []

    async def start_browser(self) -> bool:
        """Start browser session."""
        try:
            from playwright.async_api import async_playwright

            self.playwright = await async_playwright().start()

            if self.browser_type == "chromium":
                self.browser = await self.playwright.chromium.launch(headless=self.headless)
            elif self.browser_type == "firefox":
                self.browser = await self.playwright.firefox.launch(headless=self.headless)
            elif self.browser_type == "webkit":
                self.browser = await self.playwright.webkit.launch(headless=self.headless)

            self.page = await self.browser.new_page()
            self.logger.info(f"Started {self.browser_type} browser")

            return True

        except Exception as e:
            self.logger.error(f"Failed to start browser: {e}")
            return False

    async def navigate_to(self, url: str) -> Dict[str, Any]:
        """Navigate to URL."""
        try:
            start_time = time.time()
            await self.page.goto(url)
            load_time = (time.time() - start_time) * 1000

            return {
                "success": True,
                "url": url,
                "load_time_ms": load_time,
                "title": await self.page.title(),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    async def click(self, selector: str) -> Dict[str, Any]:
        """Click element."""
        try:
            await self.page.click(selector)
            return {
                "success": True,
                "action": "click",
                "selector": selector,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    async def fill(self, selector: str, text: str) -> Dict[str, Any]:
        """Fill input field."""
        try:
            await self.page.fill(selector, text)
            return {
                "success": True,
                "action": "fill",
                "selector": selector,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    async def screenshot(self, filename: str = None) -> str:
        """Take screenshot."""
        try:
            if not filename:
                filename = f"screenshot_{int(time.time())}.png"

            await self.page.screenshot(path=filename)
            self.screenshots.append(filename)

            return filename

        except Exception as e:
            self.logger.error(f"Screenshot failed: {e}")
            return None

    async def stop_browser(self) -> None:
        """Stop browser."""
        if self.browser:
            await self.browser.close()
        if hasattr(self, "playwright"):
            await self.playwright.stop()


class E2ETestRunner:
    """
    End-to-end test runner.

    Orchestrates E2E tests using Selenium or Playwright.
    """

    def __init__(self, engine: str = "playwright", browser: str = "chromium"):
        """
        Initialize E2E test runner.

        Args:
            engine: Testing engine (selenium, playwright)
            browser: Browser to use
        """
        self.engine = engine
        self.browser = browser
        self.tester = None
        self.logger = logging.getLogger(__name__)

    async def setup(self) -> None:
        """Setup test environment."""
        if self.engine == "selenium":
            self.tester = SeleniumTester(browser=self.browser)
            self.tester.start_browser()
        elif self.engine == "playwright":
            self.tester = PlaywrightTester(browser=self.browser)
            await self.tester.start_browser()

        self.logger.info(f"E2E test environment ready ({self.engine})")

    async def teardown(self) -> None:
        """Teardown test environment."""
        if self.tester:
            if self.engine == "selenium":
                self.tester.stop_browser()
            elif self.engine == "playwright":
                await self.tester.stop_browser()

    async def run_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run E2E test scenario.

        Args:
            scenario: Test scenario configuration

        Returns:
            Scenario execution result
        """
        await self.setup()

        try:
            steps = scenario.get("steps", [])
            results = []

            for step in steps:
                action = step.get("action")
                result = await self._execute_step(action, step)
                results.append(result)

                if not result.get("success") and scenario.get("stop_on_failure", True):
                    break

            return {
                "success": all(r.get("success") for r in results),
                "scenario": scenario.get("name"),
                "steps_completed": len(results),
                "total_steps": len(steps),
                "results": results,
            }

        finally:
            await self.teardown()

    async def _execute_step(self, action: str, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute single test step."""
        if self.engine == "playwright":
            if action == "navigate":
                return await self.tester.navigate_to(step.get("url"))
            elif action == "click":
                return await self.tester.click(step.get("selector"))
            elif action == "fill":
                return await self.tester.fill(step.get("selector"), step.get("text"))
            elif action == "screenshot":
                filename = await self.tester.screenshot(step.get("filename"))
                return {"success": bool(filename), "filename": filename}

        return {"success": False, "error": f"Unknown action: {action}"}
