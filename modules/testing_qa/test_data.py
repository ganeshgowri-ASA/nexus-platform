"""
Test Data Generation Module

Provides TestDataGenerator, FixtureManager, and MockDataBuilder for test data.
"""

import logging
import random
import string
from typing import Dict, Any, List, Optional, Type
from datetime import datetime, timedelta
from faker import Faker
import json

logger = logging.getLogger(__name__)


class MockDataBuilder:
    """
    Mock data builder for generating realistic test data.

    Uses Faker library for realistic data generation.
    """

    def __init__(self, locale: str = "en_US", seed: int = None):
        """
        Initialize mock data builder.

        Args:
            locale: Locale for data generation
            seed: Random seed for reproducibility
        """
        self.fake = Faker(locale)
        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)
        self.logger = logging.getLogger(__name__)

    def person(self) -> Dict[str, Any]:
        """Generate mock person data."""
        return {
            "id": self.fake.uuid4(),
            "first_name": self.fake.first_name(),
            "last_name": self.fake.last_name(),
            "email": self.fake.email(),
            "phone": self.fake.phone_number(),
            "date_of_birth": self.fake.date_of_birth().isoformat(),
            "address": {
                "street": self.fake.street_address(),
                "city": self.fake.city(),
                "state": self.fake.state(),
                "zip_code": self.fake.zipcode(),
                "country": self.fake.country(),
            },
        }

    def company(self) -> Dict[str, Any]:
        """Generate mock company data."""
        return {
            "id": self.fake.uuid4(),
            "name": self.fake.company(),
            "email": self.fake.company_email(),
            "phone": self.fake.phone_number(),
            "website": self.fake.url(),
            "industry": self.fake.bs(),
            "employees": random.randint(10, 10000),
        }

    def product(self) -> Dict[str, Any]:
        """Generate mock product data."""
        return {
            "id": self.fake.uuid4(),
            "name": self.fake.catch_phrase(),
            "description": self.fake.text(max_nb_chars=200),
            "price": round(random.uniform(10, 1000), 2),
            "category": random.choice(["Electronics", "Clothing", "Food", "Books", "Toys"]),
            "in_stock": random.choice([True, False]),
            "quantity": random.randint(0, 100),
            "sku": self.fake.ean13(),
        }

    def transaction(self) -> Dict[str, Any]:
        """Generate mock transaction data."""
        return {
            "id": self.fake.uuid4(),
            "amount": round(random.uniform(1, 10000), 2),
            "currency": random.choice(["USD", "EUR", "GBP", "JPY"]),
            "status": random.choice(["pending", "completed", "failed", "cancelled"]),
            "created_at": self.fake.date_time_this_year().isoformat(),
            "payment_method": random.choice(["credit_card", "debit_card", "paypal", "bank_transfer"]),
        }

    def user_credentials(self) -> Dict[str, str]:
        """Generate mock user credentials."""
        username = self.fake.user_name()
        return {
            "username": username,
            "email": f"{username}@{self.fake.domain_name()}",
            "password": self.fake.password(length=12, special_chars=True, digits=True, upper_case=True),
        }

    def api_response(self, success: bool = True) -> Dict[str, Any]:
        """Generate mock API response."""
        if success:
            return {
                "status": "success",
                "code": 200,
                "data": {
                    "id": self.fake.uuid4(),
                    "message": "Operation successful",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }
        else:
            return {
                "status": "error",
                "code": random.choice([400, 401, 403, 404, 500]),
                "error": {
                    "message": self.fake.sentence(),
                    "details": self.fake.text(max_nb_chars=100),
                },
                "timestamp": datetime.utcnow().isoformat(),
            }


class FixtureManager:
    """
    Test fixture manager for pytest.

    Manages test fixtures and test data lifecycle.
    """

    def __init__(self):
        """Initialize fixture manager."""
        self.fixtures: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)

    def register_fixture(self, name: str, data: Any) -> None:
        """
        Register a test fixture.

        Args:
            name: Fixture name
            data: Fixture data
        """
        self.fixtures[name] = data
        self.logger.debug(f"Registered fixture: {name}")

    def get_fixture(self, name: str) -> Any:
        """
        Get a test fixture.

        Args:
            name: Fixture name

        Returns:
            Fixture data
        """
        return self.fixtures.get(name)

    def load_from_json(self, filepath: str) -> None:
        """
        Load fixtures from JSON file.

        Args:
            filepath: Path to JSON file
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                for name, fixture_data in data.items():
                    self.register_fixture(name, fixture_data)
            self.logger.info(f"Loaded fixtures from {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to load fixtures: {e}")

    def save_to_json(self, filepath: str) -> None:
        """
        Save fixtures to JSON file.

        Args:
            filepath: Path to JSON file
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(self.fixtures, f, indent=2, default=str)
            self.logger.info(f"Saved fixtures to {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to save fixtures: {e}")

    def clear_fixtures(self) -> None:
        """Clear all fixtures."""
        self.fixtures = {}
        self.logger.debug("Cleared all fixtures")


class TestDataGenerator:
    """
    Comprehensive test data generator.

    Generates various types of test data for different testing scenarios.
    """

    def __init__(self, seed: int = None):
        """
        Initialize test data generator.

        Args:
            seed: Random seed for reproducibility
        """
        self.mock_builder = MockDataBuilder(seed=seed)
        self.fixture_manager = FixtureManager()
        self.logger = logging.getLogger(__name__)

        if seed is not None:
            random.seed(seed)

    def generate_batch(
        self,
        data_type: str,
        count: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Generate batch of test data.

        Args:
            data_type: Type of data (person, company, product, transaction)
            count: Number of items to generate

        Returns:
            List of generated data items
        """
        generator_map = {
            "person": self.mock_builder.person,
            "company": self.mock_builder.company,
            "product": self.mock_builder.product,
            "transaction": self.mock_builder.transaction,
            "user": self.mock_builder.user_credentials,
        }

        generator = generator_map.get(data_type)
        if not generator:
            raise ValueError(f"Unknown data type: {data_type}")

        return [generator() for _ in range(count)]

    def generate_edge_cases(self, data_type: str) -> List[Dict[str, Any]]:
        """
        Generate edge case test data.

        Args:
            data_type: Type of data

        Returns:
            List of edge cases
        """
        edge_cases = []

        if data_type == "string":
            edge_cases = [
                {"value": "", "description": "empty string"},
                {"value": " ", "description": "single space"},
                {"value": "a" * 1000, "description": "very long string"},
                {"value": "special!@#$%^&*()", "description": "special characters"},
                {"value": "unicode: 你好世界", "description": "unicode characters"},
                {"value": None, "description": "null value"},
            ]

        elif data_type == "number":
            edge_cases = [
                {"value": 0, "description": "zero"},
                {"value": -1, "description": "negative"},
                {"value": float('inf'), "description": "infinity"},
                {"value": float('-inf'), "description": "negative infinity"},
                {"value": 2**31 - 1, "description": "max 32-bit int"},
                {"value": -2**31, "description": "min 32-bit int"},
            ]

        elif data_type == "array":
            edge_cases = [
                {"value": [], "description": "empty array"},
                {"value": [None], "description": "array with null"},
                {"value": list(range(1000)), "description": "large array"},
            ]

        elif data_type == "object":
            edge_cases = [
                {"value": {}, "description": "empty object"},
                {"value": None, "description": "null object"},
                {"value": {"nested": {"very": {"deep": "value"}}}, "description": "deeply nested"},
            ]

        return edge_cases

    def generate_sql_injection_payloads(self) -> List[str]:
        """Generate SQL injection test payloads."""
        return [
            "' OR '1'='1",
            "' OR '1'='1' --",
            "' OR '1'='1' /*",
            "admin' --",
            "admin' #",
            "' UNION SELECT NULL--",
            "1' AND '1' = '1",
            "1' DROP TABLE users--",
        ]

    def generate_xss_payloads(self) -> List[str]:
        """Generate XSS test payloads."""
        return [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(1)'>",
            "<body onload=alert('XSS')>",
        ]

    def generate_boundary_values(
        self,
        min_val: int,
        max_val: int,
    ) -> List[int]:
        """
        Generate boundary value test cases.

        Args:
            min_val: Minimum value
            max_val: Maximum value

        Returns:
            List of boundary values
        """
        return [
            min_val - 1,  # Just below minimum
            min_val,      # Minimum
            min_val + 1,  # Just above minimum
            (min_val + max_val) // 2,  # Middle value
            max_val - 1,  # Just below maximum
            max_val,      # Maximum
            max_val + 1,  # Just above maximum
        ]

    def generate_random_string(
        self,
        length: int = 10,
        include_special: bool = False,
    ) -> str:
        """
        Generate random string.

        Args:
            length: String length
            include_special: Include special characters

        Returns:
            Random string
        """
        chars = string.ascii_letters + string.digits

        if include_special:
            chars += string.punctuation

        return ''.join(random.choice(chars) for _ in range(length))

    def generate_time_series_data(
        self,
        start_date: datetime,
        end_date: datetime,
        interval_minutes: int = 60,
    ) -> List[Dict[str, Any]]:
        """
        Generate time series test data.

        Args:
            start_date: Start date
            end_date: End date
            interval_minutes: Interval in minutes

        Returns:
            List of time series data points
        """
        data = []
        current_date = start_date

        while current_date <= end_date:
            data.append({
                "timestamp": current_date.isoformat(),
                "value": random.uniform(0, 100),
                "status": random.choice(["normal", "warning", "critical"]),
            })
            current_date += timedelta(minutes=interval_minutes)

        return data

    def save_test_data(
        self,
        filename: str,
        data: List[Dict[str, Any]],
    ) -> None:
        """
        Save test data to file.

        Args:
            filename: Output filename
            data: Test data to save
        """
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            self.logger.info(f"Saved test data to {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save test data: {e}")
