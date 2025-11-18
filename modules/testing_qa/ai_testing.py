"""
AI-Powered Testing Module

Provides AITestGenerator, IntelligentTestCreation, and BugPrediction using LLMs.
"""

import logging
import json
from typing import Dict, Any, List, Optional
import anthropic
import os

logger = logging.getLogger(__name__)


class IntelligentTestCreation:
    """
    Intelligent test creation using AI.

    Analyzes code and creates comprehensive test cases.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize intelligent test creation.

        Args:
            api_key: Anthropic API key
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=self.api_key) if self.api_key else None
        self.logger = logging.getLogger(__name__)

    async def analyze_code(
        self,
        code: str,
        language: str = "python",
    ) -> Dict[str, Any]:
        """
        Analyze code using AI.

        Args:
            code: Source code to analyze
            language: Programming language

        Returns:
            Analysis result
        """
        if not self.client:
            return {
                "error": "Anthropic API key not configured",
            }

        prompt = f"""Analyze this {language} code and provide:
1. Functions/methods to test
2. Edge cases to consider
3. Potential bugs or issues
4. Recommended test coverage

Code:
```{language}
{code}
```

Provide response in JSON format."""

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            analysis = message.content[0].text

            return {
                "success": True,
                "analysis": analysis,
            }

        except Exception as e:
            self.logger.error(f"Code analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def create_test_cases(
        self,
        code: str,
        test_type: str = "unit",
        language: str = "python",
    ) -> Dict[str, Any]:
        """
        Create test cases using AI.

        Args:
            code: Source code to test
            test_type: Type of tests (unit, integration, e2e)
            language: Programming language

        Returns:
            Generated test cases
        """
        if not self.client:
            return {
                "error": "Anthropic API key not configured",
            }

        prompt = f"""Generate comprehensive {test_type} tests for this {language} code.

Include:
1. Happy path tests
2. Edge cases
3. Error handling tests
4. Boundary conditions
5. Mock/stub setup where needed

Use pytest framework with proper assertions.

Code to test:
```{language}
{code}
```

Generate complete, runnable test code."""

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            test_code = message.content[0].text

            return {
                "success": True,
                "test_code": test_code,
                "test_type": test_type,
            }

        except Exception as e:
            self.logger.error(f"Test generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }


class BugPrediction:
    """
    Bug prediction using AI.

    Predicts potential bugs in code using machine learning.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize bug prediction.

        Args:
            api_key: Anthropic API key
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=self.api_key) if self.api_key else None
        self.logger = logging.getLogger(__name__)

    async def predict_bugs(
        self,
        code: str,
        language: str = "python",
    ) -> Dict[str, Any]:
        """
        Predict potential bugs in code.

        Args:
            code: Source code
            language: Programming language

        Returns:
            Bug predictions
        """
        if not self.client:
            return {
                "error": "Anthropic API key not configured",
            }

        prompt = f"""Analyze this {language} code for potential bugs and issues.

Identify:
1. Logic errors
2. Edge cases not handled
3. Potential runtime errors
4. Security vulnerabilities
5. Performance issues
6. Code smells

Provide specific line numbers and severity levels (critical, high, medium, low).

Code:
```{language}
{code}
```

Response format:
{{
  "bugs": [
    {{
      "line": <line_number>,
      "severity": "<severity>",
      "type": "<bug_type>",
      "description": "<description>",
      "suggestion": "<fix_suggestion>"
    }}
  ]
}}"""

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_text = message.content[0].text

            # Try to extract JSON
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)

            if json_match:
                bugs_data = json.loads(json_match.group())
                return {
                    "success": True,
                    "bugs": bugs_data.get("bugs", []),
                }
            else:
                return {
                    "success": True,
                    "raw_analysis": response_text,
                }

        except Exception as e:
            self.logger.error(f"Bug prediction failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }


class AITestGenerator:
    """
    Comprehensive AI test generator.

    Orchestrates AI-powered test generation and bug prediction.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize AI test generator.

        Args:
            api_key: Anthropic API key
        """
        self.test_creator = IntelligentTestCreation(api_key)
        self.bug_predictor = BugPrediction(api_key)
        self.logger = logging.getLogger(__name__)

    async def generate_comprehensive_tests(
        self,
        source_file: str,
        output_file: str = None,
        test_types: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive tests for source file.

        Args:
            source_file: Source file path
            output_file: Output test file path
            test_types: Types of tests to generate

        Returns:
            Generation result
        """
        test_types = test_types or ["unit", "integration"]

        # Read source code
        try:
            with open(source_file, 'r') as f:
                source_code = f.read()
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to read source file: {e}",
            }

        # Analyze code
        analysis = await self.test_creator.analyze_code(source_code)

        if not analysis.get("success"):
            return analysis

        # Generate tests for each type
        all_tests = []

        for test_type in test_types:
            test_result = await self.test_creator.create_test_cases(
                source_code,
                test_type=test_type,
            )

            if test_result.get("success"):
                all_tests.append({
                    "type": test_type,
                    "code": test_result["test_code"],
                })

        # Predict bugs
        bug_predictions = await self.bug_predictor.predict_bugs(source_code)

        # Save tests if output file specified
        if output_file and all_tests:
            try:
                with open(output_file, 'w') as f:
                    f.write("# Auto-generated tests by AI Test Generator\n\n")

                    for test in all_tests:
                        f.write(f"# {test['type'].upper()} TESTS\n")
                        f.write(test['code'])
                        f.write("\n\n")

                self.logger.info(f"Tests saved to {output_file}")

            except Exception as e:
                self.logger.error(f"Failed to save tests: {e}")

        return {
            "success": True,
            "source_file": source_file,
            "output_file": output_file,
            "analysis": analysis.get("analysis"),
            "tests_generated": len(all_tests),
            "test_types": [t["type"] for t in all_tests],
            "bug_predictions": bug_predictions.get("bugs", []),
        }

    async def improve_test_coverage(
        self,
        source_file: str,
        existing_test_file: str,
        coverage_report: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Improve test coverage using AI.

        Args:
            source_file: Source file path
            existing_test_file: Existing test file
            coverage_report: Coverage report data

        Returns:
            Improvement suggestions
        """
        # Read files
        try:
            with open(source_file, 'r') as f:
                source_code = f.read()

            with open(existing_test_file, 'r') as f:
                test_code = f.read()

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to read files: {e}",
            }

        # Get uncovered lines
        uncovered_lines = coverage_report.get("uncovered_lines", [])

        if not uncovered_lines:
            return {
                "success": True,
                "message": "Full coverage achieved!",
            }

        prompt = f"""The following code has incomplete test coverage.

Uncovered lines: {uncovered_lines}

Source code:
```python
{source_code}
```

Existing tests:
```python
{test_code}
```

Generate additional test cases to cover the uncovered lines.
Focus on testing the specific functionality in those lines."""

        if not self.test_creator.client:
            return {
                "error": "Anthropic API key not configured",
            }

        try:
            message = self.test_creator.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            additional_tests = message.content[0].text

            return {
                "success": True,
                "uncovered_lines": uncovered_lines,
                "additional_tests": additional_tests,
            }

        except Exception as e:
            self.logger.error(f"Coverage improvement failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }
