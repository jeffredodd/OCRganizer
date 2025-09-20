"""Pytest configuration and shared fixtures."""

import os
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest


# Test environment detection
def is_ci_environment():
    """Check if we're running in CI environment."""
    return os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true"


def has_real_api_keys():
    """Check if real API keys are available for integration testing."""
    return (
        os.getenv("OPENAI_API_KEY")
        and os.getenv("OPENAI_API_KEY") != "test-key"
        and len(os.getenv("OPENAI_API_KEY", "")) > 10
    )


@pytest.fixture(autouse=True)
def setup_tinyllama_environment():
    """Setup environment for TinyLlama testing."""

    # Set default environment variables for TinyLlama
    default_env = {
        "OPENAI_BASE_URL": os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "ollama"),
        "OPENAI_MODEL": os.getenv("OPENAI_MODEL", "tinyllama"),
        "LOCAL_MODEL_NAME": os.getenv("LOCAL_MODEL_NAME", "tinyllama"),
    }

    with patch.dict(os.environ, default_env, clear=False):
        yield default_env


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    env_vars = {
        "OPENAI_API_KEY": "test-openai-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "OPENAI_BASE_URL": "http://localhost:1234/v1",
        "LOCAL_MODEL_NAME": "test-model",
    }

    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def sample_pdf_document():
    """Create a sample PDF document for testing."""
    from src.pdf_processor import PDFDocument

    return PDFDocument(
        file_path=Path("test_document.pdf"),
        text_content="Sample PDF content for testing",
        metadata={"title": "Test Document", "author": "Test Author"},
        page_count=1,
        extraction_method="pypdf",
    )


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file for testing."""
    config_content = """
organization:
  structure_pattern: "{company}/{year}/{month}"
  filename_pattern: "{date}_{company}_{type}"
  confidence_threshold: 0.7

ai:
  preferred_provider: "openai"
  openai:
    model: "gpt-3.5-turbo"
    max_tokens: 800
    temperature: 0.1

processing:
  batch_size: 10
  retry_attempts: 3
  timeout_seconds: 30
"""

    config_file = tmp_path / "config.yaml"
    config_file.write_text(config_content)
    return config_file


@pytest.fixture
def mock_file_operations():
    """Mock file system operations for testing."""
    with patch("pathlib.Path.exists") as mock_exists, patch(
        "pathlib.Path.mkdir"
    ) as mock_mkdir, patch("shutil.move") as mock_move, patch(
        "shutil.copy2"
    ) as mock_copy:
        mock_exists.return_value = True
        yield {
            "exists": mock_exists,
            "mkdir": mock_mkdir,
            "move": mock_move,
            "copy": mock_copy,
        }


# Pytest markers for different test types
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests (mocked)")
    config.addinivalue_line("markers", "integration: Integration tests (real APIs)")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid or "e2e" in item.nodeid:
            item.add_marker(pytest.mark.integration)

        # Mark slow tests
        if "batch" in item.nodeid or "large" in item.nodeid:
            item.add_marker(pytest.mark.slow)

        # Default to unit tests
        if not any(
            marker.name in ["integration", "e2e"] for marker in item.iter_markers()
        ):
            item.add_marker(pytest.mark.unit)
