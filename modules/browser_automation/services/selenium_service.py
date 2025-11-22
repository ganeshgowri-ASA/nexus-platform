"""Selenium browser automation service"""
import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from .automation import BrowserAutomationService


class SeleniumService(BrowserAutomationService):
    """Selenium implementation of browser automation"""

    def __init__(
        self,
        headless: bool = True,
        timeout: int = 30000,
        browser_type: str = "chromium"
    ):
        super().__init__(headless, timeout, browser_type)
        self.driver = None
        self.wait = None

    async def start(self) -> None:
        """Initialize and start Selenium browser"""
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._start_sync)

    def _start_sync(self) -> None:
        """Synchronous browser start"""
        if self.browser_type == "firefox":
            options = FirefoxOptions()
            if self.headless:
                options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            service = FirefoxService(GeckoDriverManager().install())
            self.driver = webdriver.Firefox(service=service, options=options)
        else:
            # Chrome/Chromium
            options = ChromeOptions()
            if self.headless:
                options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)

        self.driver.set_window_size(1920, 1080)
        self.driver.implicitly_wait(self.timeout / 1000)
        self.wait = WebDriverWait(self.driver, self.timeout / 1000)

    async def stop(self) -> None:
        """Stop and cleanup Selenium browser"""
        if self.driver:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.driver.quit)

    async def navigate(self, url: str) -> None:
        """Navigate to URL"""
        if not self.driver:
            raise RuntimeError("Browser not started")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.driver.get, url)

    def _get_by_type(self, selector_type: str) -> By:
        """Convert selector type to Selenium By"""
        mapping = {
            "css": By.CSS_SELECTOR,
            "xpath": By.XPATH,
            "id": By.ID,
            "name": By.NAME,
            "class": By.CLASS_NAME,
            "tag": By.TAG_NAME,
        }
        return mapping.get(selector_type, By.CSS_SELECTOR)

    async def click(self, selector: str, selector_type: str = "css") -> None:
        """Click an element"""
        if not self.driver:
            raise RuntimeError("Browser not started")

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._click_sync,
            selector,
            selector_type
        )

    def _click_sync(self, selector: str, selector_type: str) -> None:
        """Synchronous click"""
        by = self._get_by_type(selector_type)
        element = self.wait.until(EC.element_to_be_clickable((by, selector)))
        element.click()

    async def type_text(
        self,
        selector: str,
        text: str,
        selector_type: str = "css",
        clear_first: bool = True
    ) -> None:
        """Type text into an element"""
        if not self.driver:
            raise RuntimeError("Browser not started")

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._type_text_sync,
            selector,
            text,
            selector_type,
            clear_first
        )

    def _type_text_sync(
        self,
        selector: str,
        text: str,
        selector_type: str,
        clear_first: bool
    ) -> None:
        """Synchronous type text"""
        by = self._get_by_type(selector_type)
        element = self.wait.until(EC.presence_of_element_located((by, selector)))

        if clear_first:
            element.clear()

        element.send_keys(text)

    async def extract_text(
        self,
        selector: str,
        selector_type: str = "css"
    ) -> Optional[str]:
        """Extract text from an element"""
        if not self.driver:
            raise RuntimeError("Browser not started")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._extract_text_sync,
            selector,
            selector_type
        )

    def _extract_text_sync(self, selector: str, selector_type: str) -> Optional[str]:
        """Synchronous extract text"""
        try:
            by = self._get_by_type(selector_type)
            element = self.wait.until(EC.presence_of_element_located((by, selector)))
            return element.text
        except (TimeoutException, NoSuchElementException):
            return None

    async def extract_attribute(
        self,
        selector: str,
        attribute: str,
        selector_type: str = "css"
    ) -> Optional[str]:
        """Extract attribute from an element"""
        if not self.driver:
            raise RuntimeError("Browser not started")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._extract_attribute_sync,
            selector,
            attribute,
            selector_type
        )

    def _extract_attribute_sync(
        self,
        selector: str,
        attribute: str,
        selector_type: str
    ) -> Optional[str]:
        """Synchronous extract attribute"""
        try:
            by = self._get_by_type(selector_type)
            element = self.wait.until(EC.presence_of_element_located((by, selector)))
            return element.get_attribute(attribute)
        except (TimeoutException, NoSuchElementException):
            return None

    async def extract_multiple(
        self,
        selector: str,
        selector_type: str = "css"
    ) -> List[str]:
        """Extract text from multiple elements"""
        if not self.driver:
            raise RuntimeError("Browser not started")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._extract_multiple_sync,
            selector,
            selector_type
        )

    def _extract_multiple_sync(self, selector: str, selector_type: str) -> List[str]:
        """Synchronous extract multiple"""
        by = self._get_by_type(selector_type)
        elements = self.driver.find_elements(by, selector)
        return [element.text for element in elements]

    async def screenshot(
        self,
        path: str,
        full_page: bool = True
    ) -> str:
        """Take screenshot"""
        if not self.driver:
            raise RuntimeError("Browser not started")

        # Ensure directory exists
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self.driver.save_screenshot,
            path
        )
        return path

    async def generate_pdf(
        self,
        path: str,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate PDF (Chrome only)"""
        if not self.driver:
            raise RuntimeError("Browser not started")

        # Ensure directory exists
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self._generate_pdf_sync,
            path,
            options
        )
        return result

    def _generate_pdf_sync(self, path: str, options: Optional[Dict[str, Any]]) -> str:
        """Synchronous PDF generation"""
        # Use Chrome DevTools Protocol for PDF generation
        pdf_data = self.driver.execute_cdp_cmd("Page.printToPDF", options or {})

        import base64
        with open(path, 'wb') as f:
            f.write(base64.b64decode(pdf_data['data']))

        return path

    async def wait(self, milliseconds: int) -> None:
        """Wait for specified milliseconds"""
        await asyncio.sleep(milliseconds / 1000)

    async def wait_for_selector(
        self,
        selector: str,
        selector_type: str = "css",
        timeout: Optional[int] = None
    ) -> bool:
        """Wait for selector to appear"""
        if not self.driver:
            raise RuntimeError("Browser not started")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._wait_for_selector_sync,
            selector,
            selector_type,
            timeout
        )

    def _wait_for_selector_sync(
        self,
        selector: str,
        selector_type: str,
        timeout: Optional[int]
    ) -> bool:
        """Synchronous wait for selector"""
        try:
            by = self._get_by_type(selector_type)
            wait = WebDriverWait(self.driver, (timeout or self.timeout) / 1000)
            wait.until(EC.presence_of_element_located((by, selector)))
            return True
        except TimeoutException:
            return False

    async def scroll(
        self,
        direction: str = "down",
        amount: Optional[int] = None
    ) -> None:
        """Scroll the page"""
        if not self.driver:
            raise RuntimeError("Browser not started")

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._scroll_sync,
            direction,
            amount
        )

    def _scroll_sync(self, direction: str, amount: Optional[int]) -> None:
        """Synchronous scroll"""
        if direction == "down":
            self.driver.execute_script(f"window.scrollBy(0, {amount or 500})")
        elif direction == "up":
            self.driver.execute_script(f"window.scrollBy(0, -{amount or 500})")
        elif direction == "top":
            self.driver.execute_script("window.scrollTo(0, 0)")
        elif direction == "bottom":
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")

    async def select_option(
        self,
        selector: str,
        value: str,
        selector_type: str = "css"
    ) -> None:
        """Select option from dropdown"""
        if not self.driver:
            raise RuntimeError("Browser not started")

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._select_option_sync,
            selector,
            value,
            selector_type
        )

    def _select_option_sync(self, selector: str, value: str, selector_type: str) -> None:
        """Synchronous select option"""
        by = self._get_by_type(selector_type)
        element = self.wait.until(EC.presence_of_element_located((by, selector)))
        select = Select(element)
        select.select_by_value(value)

    async def execute_script(self, script: str) -> Any:
        """Execute custom JavaScript"""
        if not self.driver:
            raise RuntimeError("Browser not started")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.driver.execute_script,
            script
        )

    async def get_current_url(self) -> str:
        """Get current URL"""
        if not self.driver:
            raise RuntimeError("Browser not started")
        return self.driver.current_url

    async def get_page_title(self) -> str:
        """Get page title"""
        if not self.driver:
            raise RuntimeError("Browser not started")
        return self.driver.title
