"""
Pytest configuration and fixtures for the test suite.
"""

import os
from pathlib import Path
from unittest.mock import Mock

import pytest

# Load environment variables from backend/.env file
from dotenv import load_dotenv

# Find the backend directory (one level up from tests directory)
backend_dir = Path(__file__).parent.parent
env_path = backend_dir / ".env"

if env_path.exists():
    load_dotenv(env_path)

# Set test environment variables only if not already set
if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "test-key-for-testing"

os.environ["LOG_LEVEL"] = "ERROR"  # Reduce logging noise during tests


# ── LLM mock ----------------------------------------------------------
class FakeResponse:
    def __init__(self, content="LLM OK"):
        self.content = content


@pytest.fixture(autouse=True)
def mock_llm(monkeypatch):
    """Mock LLM calls to avoid token consumption."""
    fake = Mock()
    fake.invoke.return_value = FakeResponse("Mocked summary")
    monkeypatch.setattr("app.llm_config.get_llm_model", lambda *a, **kw: fake)
    return fake


# ── Dataset repository -------------------------------------------------
@pytest.fixture(scope="session")
def repo():
    """Get dataset repository instance."""
    from app.infrastructure.security_data_repository import get_dataset_repository

    return get_dataset_repository()


# ── FastAPI test client -----------------------------------------------
@pytest.fixture(scope="session")
def client():
    """Create FastAPI test client."""
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)


@pytest.fixture
def sample_host_data():
    """Sample host data for testing."""
    return {
        "ip": "192.168.1.100",
        "domain": "example.com",
        "os": "ubuntu-20.04",
        "ports": [22, 80, 443],
        "services": ["ssh", "http", "https"],
    }


@pytest.fixture
def sample_thread_id():
    """Sample thread ID for testing."""
    return "test-thread-12345"


@pytest.fixture
def sample_user_message():
    """Sample user message for testing."""
    return "Please analyze this host for security vulnerabilities and provide recommendations."
