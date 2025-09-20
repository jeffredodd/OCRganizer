"""Tests for the configuration management system."""

import os
import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
import yaml

from src.config import (
    AIConfig,
    AppConfig,
    FileConfig,
    OrganizationConfig,
    ProcessingConfig,
    WebConfig,
    get_config,
    reload_config,
)


class TestAIConfig:
    """Test AI configuration."""

    def test_default_values(self):
        """Test default AI configuration values."""
        config = AIConfig()
        assert config.preferred_provider == "openai"
        assert config.openai_model == "gpt-3.5-turbo"
        assert config.openai_temperature == 0.3
        assert config.openai_max_tokens == 800


class TestOrganizationConfig:
    """Test organization configuration."""

    def test_default_values(self):
        """Test default organization configuration values."""
        config = OrganizationConfig()
        assert config.structure_pattern == "{company}/{year}/{month}"
        assert config.filename_pattern == "{company}_{type}_{date}"
        assert config.date_format == "%Y-%m-%d"


class TestProcessingConfig:
    """Test processing configuration."""

    def test_default_values(self):
        """Test default processing configuration values."""
        config = ProcessingConfig()
        assert config.enable_ocr is True
        assert config.min_text_length == 100
        assert config.max_text_for_ai == 4000
        assert config.confidence_threshold == 0.7


class TestFileConfig:
    """Test file configuration."""

    def test_default_values(self):
        """Test default file configuration values."""
        config = FileConfig()
        assert config.max_file_size_mb == 50
        assert config.allowed_extensions == [".pdf"]
        assert config.input_dir == "input_pdfs"
        assert config.output_dir == "output"
        assert config.copy_mode is False


class TestWebConfig:
    """Test web configuration."""

    def test_default_values(self):
        """Test default web configuration values."""
        config = WebConfig()
        assert config.port == 5000
        assert config.debug is False
        assert config.host == "0.0.0.0"


class TestAppConfig:
    """Test main application configuration."""

    def test_default_initialization(self):
        """Test default app config initialization."""
        config = AppConfig()
        assert isinstance(config.ai, AIConfig)
        assert isinstance(config.organization, OrganizationConfig)
        assert isinstance(config.processing, ProcessingConfig)
        assert isinstance(config.files, FileConfig)
        assert isinstance(config.web, WebConfig)

    def test_load_from_nonexistent_file(self):
        """Test loading config when no file exists."""
        with patch("src.config.Path.exists", return_value=False):
            config = AppConfig.load_from_file()
            assert isinstance(config, AppConfig)
            # Should have default values
            assert config.ai.preferred_provider == "openai"

    def test_load_from_yaml_file(self):
        """Test loading config from YAML file."""
        yaml_content = """
ai:
  preferred_provider: "anthropic"
  openai:
    model: "gpt-4"
organization:
  structure_pattern: "{company}/{year}"
processing:
  confidence_threshold: 0.8
files:
  max_file_size_mb: 100
web:
  port: 8080
"""
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            with patch("src.config.Path.exists", return_value=True):
                config = AppConfig.load_from_file("test_config.yaml")

                assert config.ai.preferred_provider == "anthropic"
                assert config.ai.openai_model == "gpt-4"
                assert config.organization.structure_pattern == "{company}/{year}"
                assert config.processing.confidence_threshold == 0.8
                assert config.files.max_file_size_mb == 100
                assert config.web.port == 8080

    @patch.dict(
        os.environ,
        {
            "AI_PROVIDER": "anthropic",
            "INPUT_DIR": "/custom/input",
            "OUTPUT_DIR": "/custom/output",
            "PORT": "3000",
            "CONFIDENCE_THRESHOLD": "0.9",
        },
    )
    def test_environment_variable_overrides(self):
        """Test that environment variables override config values."""
        with patch("src.config.Path.exists", return_value=False):
            config = AppConfig.load_from_file()

            assert config.ai.preferred_provider == "anthropic"
            assert config.files.input_dir == "/custom/input"
            assert config.files.output_dir == "/custom/output"
            assert config.web.port == 3000
            assert config.processing.confidence_threshold == 0.9

    def test_validation_success(self):
        """Test successful configuration validation."""
        config = AppConfig()
        assert config.validate() is True

    def test_validation_invalid_provider(self):
        """Test validation with invalid AI provider."""
        config = AppConfig()
        config.ai.preferred_provider = "invalid_provider"
        assert config.validate() is False

    def test_validation_invalid_confidence_threshold(self):
        """Test validation with invalid confidence threshold."""
        config = AppConfig()
        config.processing.confidence_threshold = 1.5  # Invalid, should be 0-1
        assert config.validate() is False

    def test_validation_invalid_port(self):
        """Test validation with invalid port."""
        config = AppConfig()
        config.web.port = 0  # Invalid port
        assert config.validate() is False

    def test_get_ai_credentials(self):
        """Test getting AI credentials from environment."""
        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test_openai_key",
                "ANTHROPIC_API_KEY": "test_anthropic_key",
                "OPENAI_BASE_URL": "http://localhost:1234/v1",
            },
        ):
            config = AppConfig()
            credentials = config.get_ai_credentials()

            assert credentials["openai_api_key"] == "test_openai_key"
            assert credentials["anthropic_api_key"] == "test_anthropic_key"
            assert credentials["openai_base_url"] == "http://localhost:1234/v1"

    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = AppConfig()
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert "ai" in config_dict
        assert "organization" in config_dict
        assert "processing" in config_dict
        assert "files" in config_dict
        assert "web" in config_dict

        # Check nested structure
        assert "preferred_provider" in config_dict["ai"]
        assert "structure_pattern" in config_dict["organization"]


class TestGlobalConfig:
    """Test global configuration functions."""

    def test_get_config_singleton(self):
        """Test that get_config returns the same instance."""
        with patch("src.config._config", None):  # Reset global config
            config1 = get_config()
            config2 = get_config()
            assert config1 is config2

    def test_reload_config(self):
        """Test reloading configuration."""
        with patch("src.config._config", None):
            original_config = get_config()
            reloaded_config = reload_config()

            # Should be a new instance
            assert reloaded_config is not original_config
            assert isinstance(reloaded_config, AppConfig)


class TestConfigFileDiscovery:
    """Test configuration file discovery."""

    def test_find_config_file_current_directory(self):
        """Test finding config file in current directory."""
        with patch("src.config.Path.exists") as mock_exists:
            # Mock that config.yaml exists in current directory
            def exists_side_effect():
                # This will be called on each Path object
                return True  # Just return True for the first path (config.yaml)

            mock_exists.side_effect = [
                True,
                False,
                False,
                False,
            ]  # Only first path exists

            found_path = AppConfig._find_config_file()
            assert found_path == Path("config.yaml")

    def test_find_config_file_not_found(self):
        """Test when no config file is found."""
        with patch("src.config.Path.exists", return_value=False):
            found_path = AppConfig._find_config_file()
            assert found_path is None


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    config_content = {
        "ai": {"preferred_provider": "openai", "openai": {"model": "gpt-3.5-turbo"}},
        "files": {"input_dir": "test_input", "output_dir": "test_output"},
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_content, f)
        temp_path = f.name

    yield temp_path

    # Cleanup
    os.unlink(temp_path)


def test_load_from_real_file(temp_config_file):
    """Test loading configuration from a real temporary file."""
    # Clear environment variables that might override config and disable dotenv
    with patch.dict("os.environ", {}, clear=True), patch("src.config.load_dotenv"):
        config = AppConfig.load_from_file(temp_config_file)

        assert config.ai.preferred_provider == "openai"
        assert config.ai.openai_model == "gpt-3.5-turbo"
        assert config.files.input_dir == "test_input"
        assert config.files.output_dir == "test_output"
