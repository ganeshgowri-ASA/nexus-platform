"""Tests for browser automation services"""
import pytest
from modules.browser_automation.services.playwright_service import PlaywrightService
from modules.browser_automation.utils.selector_helper import SelectorHelper


@pytest.mark.asyncio
async def test_playwright_service_initialization():
    """Test Playwright service initialization"""
    service = PlaywrightService(headless=True, timeout=30000, browser_type="chromium")

    assert service.headless is True
    assert service.timeout == 30000
    assert service.browser_type == "chromium"


@pytest.mark.asyncio
async def test_playwright_selector_conversion():
    """Test selector type conversion"""
    service = PlaywrightService()

    # CSS selector
    assert service._convert_selector("div.class", "css") == "div.class"

    # XPath selector
    assert service._convert_selector("//div[@id='test']", "xpath") == "xpath=//div[@id='test']"

    # ID selector
    assert service._convert_selector("test-id", "id") == "#test-id"

    # Name selector
    assert service._convert_selector("test-name", "name") == "[name='test-name']"


def test_selector_helper_css_generation():
    """Test CSS selector generation"""
    element_info = {
        "id": "test-id",
        "tag": "div",
        "classes": ["class1", "class2"]
    }

    selector = SelectorHelper.generate_css_selector(element_info)
    assert selector == "#test-id"

    # Without ID
    element_info_no_id = {
        "tag": "div",
        "classes": ["class1", "class2"]
    }

    selector = SelectorHelper.generate_css_selector(element_info_no_id)
    assert "class1" in selector


def test_selector_helper_xpath_generation():
    """Test XPath selector generation"""
    element_info = {
        "id": "test-id",
        "tag": "div"
    }

    selector = SelectorHelper.generate_xpath_selector(element_info)
    assert selector == "//*[@id='test-id']"


def test_selector_validation():
    """Test selector validation"""
    # Valid CSS
    assert SelectorHelper.validate_selector("div.class", "css") is True
    assert SelectorHelper.validate_selector("#id", "css") is True

    # Invalid CSS
    assert SelectorHelper.validate_selector("div{}", "css") is False
    assert SelectorHelper.validate_selector("", "css") is False

    # Valid XPath
    assert SelectorHelper.validate_selector("//div[@id='test']", "xpath") is True

    # Invalid XPath
    assert SelectorHelper.validate_selector("div", "xpath") is False
