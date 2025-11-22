"""Base browser automation service interface"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from pathlib import Path


class BrowserAutomationService(ABC):
    """Abstract base class for browser automation services"""

    def __init__(
        self,
        headless: bool = True,
        timeout: int = 30000,
        browser_type: str = "chromium"
    ):
        self.headless = headless
        self.timeout = timeout
        self.browser_type = browser_type
        self.browser = None
        self.context = None
        self.page = None

    @abstractmethod
    async def start(self) -> None:
        """Initialize and start the browser"""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop and cleanup the browser"""
        pass

    @abstractmethod
    async def navigate(self, url: str) -> None:
        """Navigate to URL"""
        pass

    @abstractmethod
    async def click(self, selector: str, selector_type: str = "css") -> None:
        """Click an element"""
        pass

    @abstractmethod
    async def type_text(
        self,
        selector: str,
        text: str,
        selector_type: str = "css",
        clear_first: bool = True
    ) -> None:
        """Type text into an element"""
        pass

    @abstractmethod
    async def extract_text(
        self,
        selector: str,
        selector_type: str = "css"
    ) -> Optional[str]:
        """Extract text from an element"""
        pass

    @abstractmethod
    async def extract_attribute(
        self,
        selector: str,
        attribute: str,
        selector_type: str = "css"
    ) -> Optional[str]:
        """Extract attribute from an element"""
        pass

    @abstractmethod
    async def extract_multiple(
        self,
        selector: str,
        selector_type: str = "css"
    ) -> List[str]:
        """Extract text from multiple elements"""
        pass

    @abstractmethod
    async def screenshot(
        self,
        path: str,
        full_page: bool = True
    ) -> str:
        """Take screenshot"""
        pass

    @abstractmethod
    async def generate_pdf(
        self,
        path: str,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate PDF"""
        pass

    @abstractmethod
    async def wait(self, milliseconds: int) -> None:
        """Wait for specified milliseconds"""
        pass

    @abstractmethod
    async def wait_for_selector(
        self,
        selector: str,
        selector_type: str = "css",
        timeout: Optional[int] = None
    ) -> bool:
        """Wait for selector to appear"""
        pass

    @abstractmethod
    async def scroll(
        self,
        direction: str = "down",
        amount: Optional[int] = None
    ) -> None:
        """Scroll the page"""
        pass

    @abstractmethod
    async def select_option(
        self,
        selector: str,
        value: str,
        selector_type: str = "css"
    ) -> None:
        """Select option from dropdown"""
        pass

    @abstractmethod
    async def execute_script(self, script: str) -> Any:
        """Execute custom JavaScript"""
        pass

    @abstractmethod
    async def get_current_url(self) -> str:
        """Get current URL"""
        pass

    @abstractmethod
    async def get_page_title(self) -> str:
        """Get page title"""
        pass
