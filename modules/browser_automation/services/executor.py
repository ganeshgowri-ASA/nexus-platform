"""Workflow execution service"""
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from modules.browser_automation.models.workflow import Workflow, WorkflowStep, WorkflowExecution, WorkflowStatus, StepType
from modules.browser_automation.services.playwright_service import PlaywrightService
from modules.browser_automation.services.selenium_service import SeleniumService
from modules.browser_automation.services.automation import BrowserAutomationService
from modules.browser_automation.config import settings


class WorkflowExecutor:
    """Executes browser automation workflows"""

    def __init__(
        self,
        workflow: Workflow,
        use_playwright: bool = True,
        execution: Optional[WorkflowExecution] = None
    ):
        self.workflow = workflow
        self.execution = execution
        self.use_playwright = use_playwright

        # Initialize browser service
        if use_playwright:
            self.service: BrowserAutomationService = PlaywrightService(
                headless=workflow.headless,
                timeout=workflow.timeout,
                browser_type=workflow.browser_type
            )
        else:
            self.service = SeleniumService(
                headless=workflow.headless,
                timeout=workflow.timeout,
                browser_type=workflow.browser_type
            )

        self.extracted_data: Dict[str, Any] = {}
        self.screenshots: List[str] = []
        self.pdfs: List[str] = []
        self.current_step: Optional[int] = None

    async def execute(self) -> Dict[str, Any]:
        """Execute the complete workflow"""
        start_time = time.time()

        try:
            # Start browser
            await self.service.start()

            # Update execution status
            if self.execution:
                self.execution.status = WorkflowStatus.RUNNING
                self.execution.started_at = datetime.utcnow()

            # Execute each step in order
            sorted_steps = sorted(self.workflow.steps, key=lambda s: s.step_order)

            for step in sorted_steps:
                self.current_step = step.step_order

                # Wait before step if configured
                if step.wait_before > 0:
                    await self.service.wait(step.wait_before)

                # Execute step with retries
                success = await self._execute_step_with_retry(step)

                if not success and step.error_handling == "stop":
                    raise Exception(f"Step {step.step_order} failed: {step.name}")

                # Wait after step if configured
                if step.wait_after > 0:
                    await self.service.wait(step.wait_after)

            # Calculate execution time
            duration = int(time.time() - start_time)

            # Update execution status
            if self.execution:
                self.execution.status = WorkflowStatus.COMPLETED
                self.execution.completed_at = datetime.utcnow()
                self.execution.duration_seconds = duration
                self.execution.result_data = self.extracted_data
                self.execution.screenshots = self.screenshots
                self.execution.pdfs = self.pdfs

            return {
                "status": "success",
                "duration": duration,
                "extracted_data": self.extracted_data,
                "screenshots": self.screenshots,
                "pdfs": self.pdfs,
            }

        except Exception as e:
            # Update execution status on error
            if self.execution:
                self.execution.status = WorkflowStatus.FAILED
                self.execution.error_message = str(e)
                self.execution.error_step = self.current_step
                self.execution.completed_at = datetime.utcnow()
                self.execution.duration_seconds = int(time.time() - start_time)

            return {
                "status": "failed",
                "error": str(e),
                "error_step": self.current_step,
                "extracted_data": self.extracted_data,
            }

        finally:
            # Always stop browser
            await self.service.stop()

    async def _execute_step_with_retry(self, step: WorkflowStep) -> bool:
        """Execute a single step with retry logic"""
        max_attempts = step.max_retries + 1 if step.error_handling == "retry" else 1

        for attempt in range(max_attempts):
            try:
                await self._execute_step(step)
                return True
            except Exception as e:
                if attempt < max_attempts - 1:
                    await self.service.wait(1000)  # Wait 1 second before retry
                    continue
                else:
                    if step.error_handling == "continue":
                        return False
                    raise e

        return False

    async def _execute_step(self, step: WorkflowStep) -> None:
        """Execute a single workflow step"""
        step_type = step.step_type

        if step_type == StepType.NAVIGATE:
            await self._execute_navigate(step)
        elif step_type == StepType.CLICK:
            await self._execute_click(step)
        elif step_type == StepType.TYPE:
            await self._execute_type(step)
        elif step_type == StepType.EXTRACT:
            await self._execute_extract(step)
        elif step_type == StepType.SCREENSHOT:
            await self._execute_screenshot(step)
        elif step_type == StepType.PDF:
            await self._execute_pdf(step)
        elif step_type == StepType.WAIT:
            await self._execute_wait(step)
        elif step_type == StepType.SCROLL:
            await self._execute_scroll(step)
        elif step_type == StepType.SELECT:
            await self._execute_select(step)
        elif step_type == StepType.SUBMIT:
            await self._execute_submit(step)
        elif step_type == StepType.CUSTOM_JS:
            await self._execute_custom_js(step)

    async def _execute_navigate(self, step: WorkflowStep) -> None:
        """Execute navigation step"""
        if not step.value:
            raise ValueError("Navigate step requires a URL in value field")
        await self.service.navigate(step.value)

    async def _execute_click(self, step: WorkflowStep) -> None:
        """Execute click step"""
        if not step.selector:
            raise ValueError("Click step requires a selector")
        await self.service.click(step.selector, step.selector_type)

    async def _execute_type(self, step: WorkflowStep) -> None:
        """Execute type step"""
        if not step.selector or not step.value:
            raise ValueError("Type step requires selector and value")

        clear_first = step.options.get("clear_first", True) if step.options else True
        await self.service.type_text(
            step.selector,
            step.value,
            step.selector_type,
            clear_first
        )

    async def _execute_extract(self, step: WorkflowStep) -> None:
        """Execute data extraction step"""
        if not step.selector:
            raise ValueError("Extract step requires a selector")

        options = step.options or {}
        extract_type = options.get("type", "text")  # text, attribute, multiple

        if extract_type == "attribute":
            attribute = options.get("attribute", "value")
            data = await self.service.extract_attribute(
                step.selector,
                attribute,
                step.selector_type
            )
        elif extract_type == "multiple":
            data = await self.service.extract_multiple(
                step.selector,
                step.selector_type
            )
        else:
            data = await self.service.extract_text(
                step.selector,
                step.selector_type
            )

        # Store extracted data
        storage_key = options.get("storage_key", f"step_{step.step_order}")
        self.extracted_data[storage_key] = data

    async def _execute_screenshot(self, step: WorkflowStep) -> None:
        """Execute screenshot step"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"workflow_{self.workflow.id}_{timestamp}_{step.step_order}.png"
        path = Path(settings.SCREENSHOT_PATH) / filename

        options = step.options or {}
        full_page = options.get("full_page", True)

        screenshot_path = await self.service.screenshot(str(path), full_page)
        self.screenshots.append(screenshot_path)

    async def _execute_pdf(self, step: WorkflowStep) -> None:
        """Execute PDF generation step"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"workflow_{self.workflow.id}_{timestamp}_{step.step_order}.pdf"
        path = Path(settings.PDF_PATH) / filename

        options = step.options or {}
        pdf_path = await self.service.generate_pdf(str(path), options)
        self.pdfs.append(pdf_path)

    async def _execute_wait(self, step: WorkflowStep) -> None:
        """Execute wait step"""
        if step.value:
            wait_ms = int(step.value)
        else:
            wait_ms = step.options.get("duration", 1000) if step.options else 1000

        await self.service.wait(wait_ms)

    async def _execute_scroll(self, step: WorkflowStep) -> None:
        """Execute scroll step"""
        options = step.options or {}
        direction = options.get("direction", "down")
        amount = options.get("amount")

        await self.service.scroll(direction, amount)

    async def _execute_select(self, step: WorkflowStep) -> None:
        """Execute select option step"""
        if not step.selector or not step.value:
            raise ValueError("Select step requires selector and value")

        await self.service.select_option(
            step.selector,
            step.value,
            step.selector_type
        )

    async def _execute_submit(self, step: WorkflowStep) -> None:
        """Execute form submit step"""
        if step.selector:
            # Click submit button
            await self.service.click(step.selector, step.selector_type)
        else:
            # Submit via JavaScript
            await self.service.execute_script(
                "document.querySelector('form').submit()"
            )

    async def _execute_custom_js(self, step: WorkflowStep) -> None:
        """Execute custom JavaScript step"""
        if not step.value:
            raise ValueError("Custom JS step requires JavaScript code in value field")

        result = await self.service.execute_script(step.value)

        # Store result if storage key provided
        if step.options and "storage_key" in step.options:
            self.extracted_data[step.options["storage_key"]] = result
