"""
Unit Testing Module

Provides UnitTestGenerator, MockGenerator, and AssertionBuilder for unit testing.
"""

import ast
import inspect
import logging
from typing import List, Dict, Any, Optional, Callable, Type
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import pytest

logger = logging.getLogger(__name__)


class AssertionBuilder:
    """
    Builder for creating custom assertions in unit tests.

    Provides fluent API for building complex assertions.
    """

    def __init__(self):
        """Initialize assertion builder."""
        self.assertions: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)

    def assert_equals(self, actual: Any, expected: Any, message: str = None) -> "AssertionBuilder":
        """
        Assert equality.

        Args:
            actual: Actual value
            expected: Expected value
            message: Optional assertion message

        Returns:
            Self for chaining
        """
        self.assertions.append({
            "type": "equals",
            "actual": actual,
            "expected": expected,
            "message": message or f"Expected {expected}, got {actual}",
        })
        assert actual == expected, message or f"Expected {expected}, got {actual}"
        return self

    def assert_not_equals(self, actual: Any, expected: Any, message: str = None) -> "AssertionBuilder":
        """Assert inequality."""
        self.assertions.append({
            "type": "not_equals",
            "actual": actual,
            "expected": expected,
            "message": message,
        })
        assert actual != expected, message or f"Expected not {expected}, got {actual}"
        return self

    def assert_true(self, condition: bool, message: str = None) -> "AssertionBuilder":
        """Assert true."""
        self.assertions.append({
            "type": "true",
            "condition": condition,
            "message": message,
        })
        assert condition is True, message or f"Expected True, got {condition}"
        return self

    def assert_false(self, condition: bool, message: str = None) -> "AssertionBuilder":
        """Assert false."""
        self.assertions.append({
            "type": "false",
            "condition": condition,
            "message": message,
        })
        assert condition is False, message or f"Expected False, got {condition}"
        return self

    def assert_none(self, value: Any, message: str = None) -> "AssertionBuilder":
        """Assert None."""
        self.assertions.append({"type": "none", "value": value, "message": message})
        assert value is None, message or f"Expected None, got {value}"
        return self

    def assert_not_none(self, value: Any, message: str = None) -> "AssertionBuilder":
        """Assert not None."""
        self.assertions.append({"type": "not_none", "value": value, "message": message})
        assert value is not None, message or "Expected not None"
        return self

    def assert_in(self, item: Any, container: Any, message: str = None) -> "AssertionBuilder":
        """Assert item in container."""
        self.assertions.append({
            "type": "in",
            "item": item,
            "container": container,
            "message": message,
        })
        assert item in container, message or f"Expected {item} in {container}"
        return self

    def assert_not_in(self, item: Any, container: Any, message: str = None) -> "AssertionBuilder":
        """Assert item not in container."""
        self.assertions.append({
            "type": "not_in",
            "item": item,
            "container": container,
            "message": message,
        })
        assert item not in container, message or f"Expected {item} not in {container}"
        return self

    def assert_isinstance(self, obj: Any, cls: Type, message: str = None) -> "AssertionBuilder":
        """Assert isinstance."""
        self.assertions.append({
            "type": "isinstance",
            "obj": obj,
            "class": cls,
            "message": message,
        })
        assert isinstance(obj, cls), message or f"Expected instance of {cls}, got {type(obj)}"
        return self

    def assert_raises(self, exception: Type[Exception], callable_obj: Callable, *args, **kwargs) -> "AssertionBuilder":
        """Assert raises exception."""
        self.assertions.append({
            "type": "raises",
            "exception": exception,
            "callable": callable_obj,
        })
        with pytest.raises(exception):
            callable_obj(*args, **kwargs)
        return self

    def assert_greater(self, a: Any, b: Any, message: str = None) -> "AssertionBuilder":
        """Assert greater than."""
        self.assertions.append({"type": "greater", "a": a, "b": b, "message": message})
        assert a > b, message or f"Expected {a} > {b}"
        return self

    def assert_less(self, a: Any, b: Any, message: str = None) -> "AssertionBuilder":
        """Assert less than."""
        self.assertions.append({"type": "less", "a": a, "b": b, "message": message})
        assert a < b, message or f"Expected {a} < {b}"
        return self

    def assert_contains(self, text: str, substring: str, message: str = None) -> "AssertionBuilder":
        """Assert string contains substring."""
        self.assertions.append({
            "type": "contains",
            "text": text,
            "substring": substring,
            "message": message,
        })
        assert substring in text, message or f"Expected '{substring}' in '{text}'"
        return self

    def get_assertions(self) -> List[Dict[str, Any]]:
        """Get all assertions."""
        return self.assertions

    def reset(self) -> None:
        """Reset assertions."""
        self.assertions = []


class MockGenerator:
    """
    Generator for creating mocks and test doubles.

    Supports Mock, MagicMock, AsyncMock, and patching.
    """

    def __init__(self):
        """Initialize mock generator."""
        self.mocks: Dict[str, Any] = {}
        self.patches: List[Any] = []
        self.logger = logging.getLogger(__name__)

    def create_mock(self, name: str, spec: Type = None, **kwargs) -> Mock:
        """
        Create a Mock object.

        Args:
            name: Mock name
            spec: Class/object to mock
            **kwargs: Additional Mock arguments

        Returns:
            Mock instance
        """
        mock = Mock(spec=spec, **kwargs)
        self.mocks[name] = mock
        self.logger.debug(f"Created mock: {name}")
        return mock

    def create_magic_mock(self, name: str, spec: Type = None, **kwargs) -> MagicMock:
        """
        Create a MagicMock object.

        Args:
            name: Mock name
            spec: Class/object to mock
            **kwargs: Additional MagicMock arguments

        Returns:
            MagicMock instance
        """
        mock = MagicMock(spec=spec, **kwargs)
        self.mocks[name] = mock
        self.logger.debug(f"Created magic mock: {name}")
        return mock

    def create_async_mock(self, name: str, spec: Type = None, **kwargs) -> AsyncMock:
        """
        Create an AsyncMock object for async functions.

        Args:
            name: Mock name
            spec: Class/object to mock
            **kwargs: Additional AsyncMock arguments

        Returns:
            AsyncMock instance
        """
        mock = AsyncMock(spec=spec, **kwargs)
        self.mocks[name] = mock
        self.logger.debug(f"Created async mock: {name}")
        return mock

    def patch_object(self, target: str, attribute: str, new: Any = None) -> Any:
        """
        Patch an object attribute.

        Args:
            target: Target module/class path
            attribute: Attribute to patch
            new: New value/mock

        Returns:
            Patch context manager
        """
        patcher = patch.object(target, attribute, new=new)
        self.patches.append(patcher)
        return patcher

    def patch_function(self, target: str, new: Any = None) -> Any:
        """
        Patch a function.

        Args:
            target: Full path to function
            new: New function/mock

        Returns:
            Patch context manager
        """
        patcher = patch(target, new=new)
        self.patches.append(patcher)
        return patcher

    def start_patches(self) -> None:
        """Start all patches."""
        for patcher in self.patches:
            patcher.start()
        self.logger.debug(f"Started {len(self.patches)} patches")

    def stop_patches(self) -> None:
        """Stop all patches."""
        for patcher in self.patches:
            patcher.stop()
        self.patches = []
        self.logger.debug("Stopped all patches")

    def get_mock(self, name: str) -> Optional[Any]:
        """Get a mock by name."""
        return self.mocks.get(name)

    def reset_mocks(self) -> None:
        """Reset all mocks."""
        for mock in self.mocks.values():
            if hasattr(mock, "reset_mock"):
                mock.reset_mock()
        self.logger.debug("Reset all mocks")


class UnitTestGenerator:
    """
    Generator for creating unit tests automatically.

    Analyzes code and generates pytest unit tests with mocks and assertions.
    """

    def __init__(self, target_coverage: float = 80.0):
        """
        Initialize unit test generator.

        Args:
            target_coverage: Target code coverage percentage
        """
        self.target_coverage = target_coverage
        self.logger = logging.getLogger(__name__)
        self.mock_generator = MockGenerator()
        self.assertion_builder = AssertionBuilder()

    def analyze_function(self, func: Callable) -> Dict[str, Any]:
        """
        Analyze a function to extract metadata.

        Args:
            func: Function to analyze

        Returns:
            Function metadata
        """
        try:
            signature = inspect.signature(func)
            source = inspect.getsource(func)
            doc = inspect.getdoc(func)

            metadata = {
                "name": func.__name__,
                "signature": str(signature),
                "parameters": [
                    {
                        "name": name,
                        "annotation": str(param.annotation) if param.annotation != inspect.Parameter.empty else None,
                        "default": str(param.default) if param.default != inspect.Parameter.empty else None,
                    }
                    for name, param in signature.parameters.items()
                ],
                "return_annotation": str(signature.return_annotation) if signature.return_annotation != inspect.Signature.empty else None,
                "docstring": doc,
                "source_lines": len(source.split("\n")),
                "is_async": inspect.iscoroutinefunction(func),
            }

            self.logger.debug(f"Analyzed function: {func.__name__}")
            return metadata

        except Exception as e:
            self.logger.error(f"Error analyzing function {func.__name__}: {e}")
            return {}

    def analyze_class(self, cls: Type) -> Dict[str, Any]:
        """
        Analyze a class to extract metadata.

        Args:
            cls: Class to analyze

        Returns:
            Class metadata
        """
        try:
            methods = [
                method for method in dir(cls)
                if callable(getattr(cls, method)) and not method.startswith("_")
            ]

            metadata = {
                "name": cls.__name__,
                "module": cls.__module__,
                "methods": methods,
                "docstring": inspect.getdoc(cls),
                "bases": [base.__name__ for base in cls.__bases__],
            }

            self.logger.debug(f"Analyzed class: {cls.__name__}")
            return metadata

        except Exception as e:
            self.logger.error(f"Error analyzing class {cls.__name__}: {e}")
            return {}

    def generate_test_for_function(
        self,
        func: Callable,
        test_name: str = None,
        use_mocks: bool = True,
    ) -> str:
        """
        Generate unit test code for a function.

        Args:
            func: Function to test
            test_name: Optional test name
            use_mocks: Whether to generate mocks

        Returns:
            Generated test code
        """
        metadata = self.analyze_function(func)
        test_name = test_name or f"test_{func.__name__}"

        # Generate test code
        test_code = f'''
def {test_name}():
    """Test {func.__name__} function."""
    # Arrange
'''

        # Add mock setup if needed
        if use_mocks and metadata.get("parameters"):
            test_code += "    # Setup mocks\n"
            for param in metadata["parameters"]:
                if param["name"] != "self":
                    test_code += f'    mock_{param["name"]} = Mock()\n'

        # Add function call
        test_code += "\n    # Act\n"
        params = ", ".join([
            f'mock_{p["name"]}'
            for p in metadata.get("parameters", [])
            if p["name"] != "self"
        ])

        if metadata.get("is_async"):
            test_code += f"    result = await {func.__name__}({params})\n"
        else:
            test_code += f"    result = {func.__name__}({params})\n"

        # Add assertions
        test_code += "\n    # Assert\n"
        test_code += "    assert result is not None\n"

        if metadata.get("return_annotation") and metadata["return_annotation"] != "None":
            test_code += f"    # TODO: Add specific assertions for {metadata['return_annotation']}\n"

        self.logger.info(f"Generated test for function: {func.__name__}")
        return test_code

    def generate_test_for_class(
        self,
        cls: Type,
        methods_to_test: List[str] = None,
    ) -> str:
        """
        Generate unit tests for a class.

        Args:
            cls: Class to test
            methods_to_test: Specific methods to test (None = all)

        Returns:
            Generated test code
        """
        metadata = self.analyze_class(cls)
        methods = methods_to_test or metadata.get("methods", [])

        test_code = f'''
import pytest
from unittest.mock import Mock, MagicMock


class Test{cls.__name__}:
    """Tests for {cls.__name__} class."""

    @pytest.fixture
    def instance(self):
        """Create instance for testing."""
        return {cls.__name__}()
'''

        # Generate tests for each method
        for method_name in methods:
            test_code += f'''
    def test_{method_name}(self, instance):
        """Test {method_name} method."""
        # Arrange
        # TODO: Setup test data

        # Act
        result = instance.{method_name}()

        # Assert
        assert result is not None
        # TODO: Add specific assertions
'''

        self.logger.info(f"Generated tests for class: {cls.__name__}")
        return test_code

    def generate_test_file(
        self,
        module_path: str,
        output_path: str = None,
    ) -> str:
        """
        Generate test file for a module.

        Args:
            module_path: Path to module to test
            output_path: Output path for test file

        Returns:
            Generated test file path
        """
        module_name = Path(module_path).stem
        output_path = output_path or f"test_{module_name}.py"

        # Generate test header
        test_content = f'''
"""
Unit tests for {module_name} module.

Auto-generated by UnitTestGenerator.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock


# TODO: Import classes and functions to test
# from {module_name} import YourClass, your_function


# Add your test cases here
'''

        # Write test file
        with open(output_path, "w") as f:
            f.write(test_content)

        self.logger.info(f"Generated test file: {output_path}")
        return output_path

    def generate_parametrized_test(
        self,
        func: Callable,
        test_cases: List[Dict[str, Any]],
    ) -> str:
        """
        Generate parametrized test.

        Args:
            func: Function to test
            test_cases: List of test case dictionaries with 'input' and 'expected'

        Returns:
            Generated parametrized test code
        """
        params = ", ".join([f"test_case_{i}" for i in range(len(test_cases))])

        test_code = f'''
@pytest.mark.parametrize("inputs,expected", [
'''

        for i, case in enumerate(test_cases):
            test_code += f"    ({case['input']}, {case['expected']}),\n"

        test_code += f'''
])
def test_{func.__name__}_parametrized(inputs, expected):
    """Parametrized test for {func.__name__}."""
    result = {func.__name__}(**inputs)
    assert result == expected
'''

        return test_code
