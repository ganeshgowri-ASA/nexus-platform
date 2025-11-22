"""
Session 56: AI Browser Automation Module
Features: Web scraping, form filling, vision-based detection
"""
import asyncio
import base64
from typing import Any, Dict, List, Optional
from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup
import json
from loguru import logger

from ..base_module import BaseModule, ModuleConfig
from ...core.claude_client import ClaudeClient


class BrowserAutomationModule(BaseModule):
    """AI-powered browser automation with vision capabilities"""

    def __init__(self, claude_client: ClaudeClient, **kwargs):
        config = ModuleConfig(
            session=56,
            name="AI Browser Automation",
            icon="🌐",
            description="Web scraping, form filling, vision-based detection",
            version="1.0.0",
            features=["web_scraping", "form_filling", "vision_detection", "smart_navigation"]
        )
        super().__init__(config, claude_client, **kwargs)
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data"""
        required_fields = ["action"]
        return all(field in input_data for field in required_fields)

    async def initialize_browser(self, headless: bool = True) -> Browser:
        """Initialize Playwright browser"""
        if not self.browser:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=headless)
            logger.info("Browser initialized")
        return self.browser

    async def close_browser(self):
        """Close browser instance"""
        if self.browser:
            await self.browser.close()
            self.browser = None
            logger.info("Browser closed")

    async def scrape_website(
        self,
        url: str,
        selectors: Optional[Dict[str, str]] = None,
        wait_for: Optional[str] = None,
        extract_schema: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Scrape website content with AI assistance

        Args:
            url: Target URL
            selectors: CSS selectors for specific elements
            wait_for: Selector to wait for before scraping
            extract_schema: Schema for structured extraction

        Returns:
            Scraped data
        """
        try:
            await self.initialize_browser()
            page = await self.browser.new_page()

            # Navigate to URL
            await page.goto(url, wait_until="networkidle")
            logger.info(f"Navigated to: {url}")

            # Wait for specific element if specified
            if wait_for:
                await page.wait_for_selector(wait_for, timeout=30000)

            # Get page content
            html_content = await page.content()
            soup = BeautifulSoup(html_content, 'html.parser')

            # Extract using selectors if provided
            if selectors:
                data = {}
                for key, selector in selectors.items():
                    elements = soup.select(selector)
                    data[key] = [elem.get_text(strip=True) for elem in elements]
            else:
                # Use AI to extract structured data
                text_content = soup.get_text(separator='\n', strip=True)

                prompt = f"""Extract structured information from this web page content:

{text_content[:5000]}

{"Extract according to this schema: " + json.dumps(extract_schema) if extract_schema else "Extract all relevant information including headings, links, text, and metadata."}

Return as JSON."""

                ai_response = await self.claude.agenerate(
                    prompt,
                    system_prompt=self.get_system_prompt()
                )

                try:
                    data = json.loads(ai_response)
                except json.JSONDecodeError:
                    data = {"raw_text": text_content, "ai_analysis": ai_response}

            await page.close()

            return {
                "success": True,
                "url": url,
                "data": data,
                "timestamp": page.url
            }

        except Exception as e:
            logger.error(f"Scraping error: {e}")
            return self.handle_error(e, "scrape_website")

    async def fill_form(
        self,
        url: str,
        form_data: Dict[str, Any],
        submit: bool = True,
        vision_assist: bool = False
    ) -> Dict[str, Any]:
        """
        Fill web form with AI assistance

        Args:
            url: Form URL
            form_data: Data to fill {field_label_or_name: value}
            submit: Whether to submit the form
            vision_assist: Use vision to identify form fields

        Returns:
            Form filling result
        """
        try:
            await self.initialize_browser()
            page = await self.browser.new_page()
            await page.goto(url, wait_until="networkidle")

            if vision_assist:
                # Take screenshot for vision analysis
                screenshot = await page.screenshot()
                screenshot_b64 = base64.b64encode(screenshot).decode()

                # Use Claude vision to identify form fields
                vision_prompt = f"""Analyze this web form screenshot and identify:
1. All input fields (labels, placeholders, types)
2. The CSS selectors or identifiers for each field
3. The submit button location

Form data to fill: {json.dumps(form_data)}

Return a mapping of form_data keys to CSS selectors in JSON format."""

                field_mapping_str = self.claude.analyze_image(
                    screenshot_b64,
                    vision_prompt,
                    media_type="image/png"
                )

                try:
                    field_mapping = json.loads(field_mapping_str)
                except json.JSONDecodeError:
                    # Fallback to name-based matching
                    field_mapping = {k: f'[name="{k}"]' for k in form_data.keys()}
            else:
                # Try common patterns for field identification
                field_mapping = {}
                for field_name in form_data.keys():
                    # Try multiple selector strategies
                    field_mapping[field_name] = (
                        f'[name="{field_name}"], '
                        f'[id="{field_name}"], '
                        f'[placeholder*="{field_name}" i], '
                        f'label:has-text("{field_name}") + input'
                    )

            # Fill form fields
            filled_fields = []
            for field_name, value in form_data.items():
                selector = field_mapping.get(field_name)
                if selector:
                    try:
                        await page.fill(selector, str(value))
                        filled_fields.append(field_name)
                        logger.info(f"Filled field: {field_name}")
                    except Exception as e:
                        logger.warning(f"Could not fill field {field_name}: {e}")

            # Submit form if requested
            if submit:
                # Try to find and click submit button
                submit_selectors = [
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button:has-text("Submit")',
                    'button:has-text("Send")',
                    'button:has-text("Continue")'
                ]

                for selector in submit_selectors:
                    try:
                        await page.click(selector)
                        await page.wait_for_load_state("networkidle")
                        logger.info("Form submitted")
                        break
                    except Exception:
                        continue

            await page.close()

            return {
                "success": True,
                "url": url,
                "filled_fields": filled_fields,
                "submitted": submit
            }

        except Exception as e:
            logger.error(f"Form filling error: {e}")
            return self.handle_error(e, "fill_form")

    async def vision_detect(
        self,
        url: str,
        detection_query: str,
        click_element: bool = False
    ) -> Dict[str, Any]:
        """
        Use vision AI to detect elements on page

        Args:
            url: Target URL
            detection_query: What to detect (e.g., "find the login button")
            click_element: Whether to click the detected element

        Returns:
            Detection result
        """
        try:
            await self.initialize_browser()
            page = await self.browser.new_page()
            await page.goto(url, wait_until="networkidle")

            # Take screenshot
            screenshot = await page.screenshot()
            screenshot_b64 = base64.b64encode(screenshot).decode()

            # Use Claude vision for detection
            vision_prompt = f"""{detection_query}

Analyze this screenshot and:
1. Identify if the element exists
2. Describe its location (approximate coordinates or position)
3. Provide a CSS selector or description to locate it
4. Provide any relevant text or attributes

Return as JSON with fields: found, description, selector, location"""

            detection_result_str = self.claude.analyze_image(
                screenshot_b64,
                vision_prompt,
                media_type="image/png"
            )

            try:
                detection_result = json.loads(detection_result_str)
            except json.JSONDecodeError:
                detection_result = {
                    "found": "unknown",
                    "description": detection_result_str
                }

            # Click element if requested and found
            clicked = False
            if click_element and detection_result.get("found") and detection_result.get("selector"):
                try:
                    await page.click(detection_result["selector"])
                    await page.wait_for_load_state("networkidle")
                    clicked = True
                    logger.info(f"Clicked element: {detection_result['selector']}")
                except Exception as e:
                    logger.warning(f"Could not click element: {e}")

            await page.close()

            return {
                "success": True,
                "url": url,
                "query": detection_query,
                "detection": detection_result,
                "clicked": clicked
            }

        except Exception as e:
            logger.error(f"Vision detection error: {e}")
            return self.handle_error(e, "vision_detect")

    async def smart_navigation(
        self,
        start_url: str,
        goal: str,
        max_steps: int = 10
    ) -> Dict[str, Any]:
        """
        AI-guided navigation to accomplish a goal

        Args:
            start_url: Starting URL
            goal: Navigation goal (e.g., "find pricing page")
            max_steps: Maximum navigation steps

        Returns:
            Navigation result
        """
        try:
            await self.initialize_browser()
            page = await self.browser.new_page()
            await page.goto(start_url, wait_until="networkidle")

            navigation_history = [start_url]
            step = 0

            while step < max_steps:
                # Get current page state
                html_content = await page.content()
                soup = BeautifulSoup(html_content, 'html.parser')
                links = [
                    {"text": a.get_text(strip=True), "href": a.get('href')}
                    for a in soup.find_all('a', href=True)
                ][:20]  # Limit to first 20 links

                # Take screenshot
                screenshot = await page.screenshot()
                screenshot_b64 = base64.b64encode(screenshot).decode()

                # Ask Claude for next action
                navigation_prompt = f"""Current URL: {page.url}
Goal: {goal}
Navigation history: {navigation_history}

Available links: {json.dumps(links, indent=2)}

Analyze the screenshot and decide:
1. Have we reached the goal? (yes/no)
2. If not, which link should we click next?
3. Provide the href of the link to navigate to

Return as JSON: {{"goal_reached": bool, "next_action": "click_link_href or "goal_reached"", "reasoning": "..."}}"""

                decision_str = self.claude.analyze_image(
                    screenshot_b64,
                    navigation_prompt,
                    media_type="image/png"
                )

                try:
                    decision = json.loads(decision_str)
                except json.JSONDecodeError:
                    decision = {"goal_reached": False, "reasoning": decision_str}

                if decision.get("goal_reached"):
                    await page.close()
                    return {
                        "success": True,
                        "goal": goal,
                        "reached": True,
                        "final_url": page.url,
                        "steps": step + 1,
                        "history": navigation_history
                    }

                # Navigate to next page
                next_link = decision.get("next_action")
                if next_link and next_link != "goal_reached":
                    try:
                        await page.goto(next_link, wait_until="networkidle")
                        navigation_history.append(next_link)
                        logger.info(f"Navigated to: {next_link}")
                    except Exception as e:
                        logger.warning(f"Navigation error: {e}")
                        break

                step += 1

            await page.close()

            return {
                "success": False,
                "goal": goal,
                "reached": False,
                "final_url": page.url,
                "steps": step,
                "history": navigation_history,
                "reason": "Max steps reached"
            }

        except Exception as e:
            logger.error(f"Smart navigation error: {e}")
            return self.handle_error(e, "smart_navigation")

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process browser automation request (sync wrapper)"""
        return asyncio.run(self.aprocess(input_data))

    async def aprocess(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process browser automation request"""
        if not self.validate_input(input_data):
            return {
                "success": False,
                "error": "Invalid input: 'action' field required"
            }

        action = input_data["action"]
        self.log_operation(action, input_data)

        try:
            if action == "scrape":
                return await self.scrape_website(
                    url=input_data["url"],
                    selectors=input_data.get("selectors"),
                    wait_for=input_data.get("wait_for"),
                    extract_schema=input_data.get("extract_schema")
                )
            elif action == "fill_form":
                return await self.fill_form(
                    url=input_data["url"],
                    form_data=input_data["form_data"],
                    submit=input_data.get("submit", True),
                    vision_assist=input_data.get("vision_assist", False)
                )
            elif action == "vision_detect":
                return await self.vision_detect(
                    url=input_data["url"],
                    detection_query=input_data["query"],
                    click_element=input_data.get("click", False)
                )
            elif action == "smart_navigation":
                return await self.smart_navigation(
                    start_url=input_data["url"],
                    goal=input_data["goal"],
                    max_steps=input_data.get("max_steps", 10)
                )
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }

        finally:
            await self.close_browser()
