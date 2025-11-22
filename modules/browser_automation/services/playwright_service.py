"""Playwright browser automation service"""
import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeoutError
from .automation import BrowserAutomationService


class PlaywrightService(BrowserAutomationService):
    """Playwright implementation of browser automation"""

    def __init__(
        self,
        headless: bool = True,
        timeout: int = 30000,
        browser_type: str = "chromium"
    ):
        super().__init__(headless, timeout, browser_type)
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def start(self) -> None:
        """Initialize and start Playwright browser"""
        self.playwright = await async_playwright().start()

        # Select browser type
        if self.browser_type == "firefox":
            browser_launcher = self.playwright.firefox
        elif self.browser_type == "webkit":
            browser_launcher = self.playwright.webkit
        else:
            browser_launcher = self.playwright.chromium

        # Launch browser
        self.browser = await browser_launcher.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled'
            ]
        )

        # Create context with realistic viewport
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

        # Create page
        self.page = await self.context.new_page()
        self.page.set_default_timeout(self.timeout)

    async def stop(self) -> None:
        """Stop and cleanup Playwright browser"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def navigate(self, url: str) -> None:
        """Navigate to URL"""
        if not self.page:
            raise RuntimeError("Browser not started")
        await self.page.goto(url, wait_until="domcontentloaded")

    def _convert_selector(self, selector: str, selector_type: str) -> str:
        """Convert selector to Playwright format"""
        if selector_type == "xpath":
            return f"xpath={selector}"
        elif selector_type == "id":
            return f"#{selector}"
        elif selector_type == "name":
            return f"[name='{selector}']"
        return selector  # CSS by default

    async def click(self, selector: str, selector_type: str = "css") -> None:
        """Click an element"""
        if not self.page:
            raise RuntimeError("Browser not started")
        pw_selector = self._convert_selector(selector, selector_type)
        await self.page.click(pw_selector)

    async def type_text(
        self,
        selector: str,
        text: str,
        selector_type: str = "css",
        clear_first: bool = True
    ) -> None:
        """Type text into an element"""
        if not self.page:
            raise RuntimeError("Browser not started")
        pw_selector = self._convert_selector(selector, selector_type)

        if clear_first:
            await self.page.fill(pw_selector, "")

        await self.page.type(pw_selector, text, delay=50)

    async def extract_text(
        self,
        selector: str,
        selector_type: str = "css"
    ) -> Optional[str]:
        """Extract text from an element"""
        if not self.page:
            raise RuntimeError("Browser not started")
        pw_selector = self._convert_selector(selector, selector_type)

        try:
            element = await self.page.wait_for_selector(pw_selector, timeout=5000)
            if element:
                return await element.inner_text()
        except PlaywrightTimeoutError:
            return None
        return None

    async def extract_attribute(
        self,
        selector: str,
        attribute: str,
        selector_type: str = "css"
    ) -> Optional[str]:
        """Extract attribute from an element"""
        if not self.page:
            raise RuntimeError("Browser not started")
        pw_selector = self._convert_selector(selector, selector_type)

        try:
            return await self.page.get_attribute(pw_selector, attribute, timeout=5000)
        except PlaywrightTimeoutError:
            return None

    async def extract_multiple(
        self,
        selector: str,
        selector_type: str = "css"
    ) -> List[str]:
        """Extract text from multiple elements"""
        if not self.page:
            raise RuntimeError("Browser not started")
        pw_selector = self._convert_selector(selector, selector_type)

        elements = await self.page.query_selector_all(pw_selector)
        texts = []
        for element in elements:
            text = await element.inner_text()
            texts.append(text)
        return texts

    async def screenshot(
        self,
        path: str,
        full_page: bool = True
    ) -> str:
        """Take screenshot"""
        if not self.page:
            raise RuntimeError("Browser not started")

        # Ensure directory exists
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        await self.page.screenshot(path=path, full_page=full_page)
        return path

    async def generate_pdf(
        self,
        path: str,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate PDF"""
        if not self.page:
            raise RuntimeError("Browser not started")

        # Ensure directory exists
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        pdf_options = {
            'path': path,
            'format': 'A4',
            'print_background': True,
        }

        if options:
            pdf_options.update(options)

        await self.page.pdf(**pdf_options)
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
        if not self.page:
            raise RuntimeError("Browser not started")
        pw_selector = self._convert_selector(selector, selector_type)

        try:
            await self.page.wait_for_selector(
                pw_selector,
                timeout=timeout or self.timeout
            )
            return True
        except PlaywrightTimeoutError:
            return False

    async def scroll(
        self,
        direction: str = "down",
        amount: Optional[int] = None
    ) -> None:
        """Scroll the page"""
        if not self.page:
            raise RuntimeError("Browser not started")

        if direction == "down":
            await self.page.evaluate(f"window.scrollBy(0, {amount or 500})")
        elif direction == "up":
            await self.page.evaluate(f"window.scrollBy(0, -{amount or 500})")
        elif direction == "top":
            await self.page.evaluate("window.scrollTo(0, 0)")
        elif direction == "bottom":
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

    async def select_option(
        self,
        selector: str,
        value: str,
        selector_type: str = "css"
    ) -> None:
        """Select option from dropdown"""
        if not self.page:
            raise RuntimeError("Browser not started")
        pw_selector = self._convert_selector(selector, selector_type)
        await self.page.select_option(pw_selector, value)

    async def execute_script(self, script: str) -> Any:
        """Execute custom JavaScript"""
        if not self.page:
            raise RuntimeError("Browser not started")
        return await self.page.evaluate(script)

    async def get_current_url(self) -> str:
        """Get current URL"""
        if not self.page:
            raise RuntimeError("Browser not started")
        return self.page.url

    async def get_page_title(self) -> str:
        """Get page title"""
        if not self.page:
            raise RuntimeError("Browser not started")
        return await self.page.title()
