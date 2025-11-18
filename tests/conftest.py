"""
Pytest configuration and fixtures
"""
import pytest
import os
from pathlib import Path

# Set test environment
os.environ["ENV"] = "test"
os.environ["ANTHROPIC_API_KEY"] = "test-api-key"


@pytest.fixture
def mock_claude_client():
    """Mock Claude client for testing"""
    from src.nexus.core.claude_client import ClaudeClient

    class MockClaudeClient(ClaudeClient):
        def __init__(self):
            self.api_key = "test-key"
            self.model = "test-model"

        def generate(self, prompt, **kwargs):
            return "Mock response"

        async def agenerate(self, prompt, **kwargs):
            return "Mock async response"

    return MockClaudeClient()


@pytest.fixture
def cache_manager():
    """Cache manager fixture"""
    from src.nexus.core.cache import CacheManager
    return CacheManager(default_ttl=60)


@pytest.fixture
def test_data_dir():
    """Test data directory"""
    return Path(__file__).parent / "data"
