"""Configuration management for OCRganizer."""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


@dataclass
class AIConfig:
    """AI provider configuration."""

    preferred_provider: str = "openai"
    openai_model: str = "gpt-3.5-turbo"
    openai_temperature: float = 0.3
    openai_max_tokens: int = 800
    anthropic_model: str = "claude-3-haiku-20240307"
    anthropic_temperature: float = 0.3
    anthropic_max_tokens: int = 800


@dataclass
class OrganizationConfig:
    """File organization configuration."""

    structure_pattern: str = "{company}/{year}/{month}"
    filename_pattern: str = "{company}_{type}_{date}"
    date_format: str = "%Y-%m-%d"
    enable_company_normalization: bool = True
    company_similarity_threshold: float = 0.75


@dataclass
class ProcessingConfig:
    """Document processing configuration."""

    enable_ocr: bool = True
    min_text_length: int = 100
    max_text_for_ai: int = 4000
    confidence_threshold: float = 0.7


@dataclass
class FileConfig:
    """File handling configuration."""

    max_file_size_mb: int = 50
    allowed_extensions: list = field(default_factory=lambda: [".pdf"])
    input_dir: str = "input_pdfs"
    output_dir: str = "output"
    copy_mode: bool = False


@dataclass
class WebConfig:
    """Web interface configuration."""

    port: int = 5000
    debug: bool = False
    host: str = "0.0.0.0"


@dataclass
class AppConfig:
    """Main application configuration."""

    ai: AIConfig = field(default_factory=AIConfig)
    organization: OrganizationConfig = field(default_factory=OrganizationConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    files: FileConfig = field(default_factory=FileConfig)
    web: WebConfig = field(default_factory=WebConfig)

    @classmethod
    def load_from_file(
        cls, config_path: Optional[Union[str, Path]] = None
    ) -> "AppConfig":
        """
        Load configuration from YAML file with environment variable overrides.

        Args:
            config_path: Path to configuration file. If None, uses default locations.

        Returns:
            AppConfig instance with loaded configuration
        """
        # Load environment variables first
        load_dotenv()

        # Find config file
        if config_path is None:
            config_path = cls._find_config_file()

        config_data = {}
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, "r") as f:
                    config_data = yaml.safe_load(f) or {}
                logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
        else:
            logger.info(
                "No config file found, using defaults with environment overrides"
            )

        # Apply environment variable overrides
        config_data = cls._apply_env_overrides(config_data)

        # Create configuration objects
        return cls(
            ai=cls._create_ai_config(config_data.get("ai", {})),
            organization=OrganizationConfig(**config_data.get("organization", {})),
            processing=ProcessingConfig(**config_data.get("processing", {})),
            files=FileConfig(**config_data.get("files", {})),
            web=WebConfig(**config_data.get("web", {})),
        )

    @staticmethod
    def _create_ai_config(ai_data: Dict[str, Any]) -> AIConfig:
        """Create AIConfig from nested YAML structure."""
        # Extract flat fields from nested structure
        config_dict = {
            "preferred_provider": ai_data.get("preferred_provider", "openai"),
            "openai_model": ai_data.get("openai", {}).get("model", "gpt-3.5-turbo"),
            "openai_temperature": ai_data.get("openai", {}).get("temperature", 0.3),
            "openai_max_tokens": ai_data.get("openai", {}).get("max_tokens", 800),
            "anthropic_model": ai_data.get("anthropic", {}).get(
                "model", "claude-3-haiku-20240307"
            ),
            "anthropic_temperature": ai_data.get("anthropic", {}).get(
                "temperature", 0.3
            ),
            "anthropic_max_tokens": ai_data.get("anthropic", {}).get("max_tokens", 800),
        }
        return AIConfig(**config_dict)

    @staticmethod
    def _find_config_file() -> Optional[Path]:
        """Find configuration file in standard locations."""
        possible_paths = [
            Path("config.yaml"),
            Path("config.yml"),
            Path("src/config.yaml"),
            Path("src/config.yml"),
            Path.home() / ".pdf-categorizer" / "config.yaml",
            Path("/etc/pdf-categorizer/config.yaml"),
        ]

        for path in possible_paths:
            if path.exists():
                return path

        return None

    @staticmethod
    def _apply_env_overrides(config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration."""
        # Initialize nested dictionaries if they don't exist
        for section in ["ai", "organization", "processing", "files", "web"]:
            if section not in config_data:
                config_data[section] = {}

        # AI configuration overrides
        env_mappings = {
            # AI settings
            "OPENAI_MODEL": ("ai", "openai_model"),
            "ANTHROPIC_MODEL": ("ai", "anthropic_model"),
            "AI_PROVIDER": ("ai", "preferred_provider"),
            "AI_TEMPERATURE": ("ai", "openai_temperature"),
            "AI_MAX_TOKENS": ("ai", "openai_max_tokens"),
            # File settings
            "INPUT_DIR": ("files", "input_dir"),
            "OUTPUT_DIR": ("files", "output_dir"),
            "MAX_FILE_SIZE_MB": ("files", "max_file_size_mb"),
            "COPY_MODE": ("files", "copy_mode"),
            # Processing settings
            "ENABLE_OCR": ("processing", "enable_ocr"),
            "CONFIDENCE_THRESHOLD": ("processing", "confidence_threshold"),
            "MIN_TEXT_LENGTH": ("processing", "min_text_length"),
            "MAX_TEXT_FOR_AI": ("processing", "max_text_for_ai"),
            # Web settings
            "PORT": ("web", "port"),
            "DEBUG": ("web", "debug"),
            "HOST": ("web", "host"),
            # Organization settings
            "STRUCTURE_PATTERN": ("organization", "structure_pattern"),
            "FILENAME_PATTERN": ("organization", "filename_pattern"),
            "DATE_FORMAT": ("organization", "date_format"),
        }

        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Type conversion based on the key
                if key in [
                    "port",
                    "max_file_size_mb",
                    "min_text_length",
                    "max_text_for_ai",
                    "openai_max_tokens",
                    "anthropic_max_tokens",
                ]:
                    try:
                        value = int(value)
                    except ValueError:
                        logger.warning(f"Invalid integer value for {env_var}: {value}")
                        continue
                elif key in [
                    "openai_temperature",
                    "anthropic_temperature",
                    "confidence_threshold",
                ]:
                    try:
                        value = float(value)
                    except ValueError:
                        logger.warning(f"Invalid float value for {env_var}: {value}")
                        continue
                elif key in ["debug", "enable_ocr", "copy_mode"]:
                    value = value.lower() in ("true", "1", "yes", "on")

                config_data[section][key] = value
                logger.debug(
                    f"Applied environment override: {env_var} -> {section}.{key} = {value}"
                )

        return config_data

    def get_ai_credentials(self) -> Dict[str, Optional[str]]:
        """Get AI provider credentials from environment variables."""
        return {
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "openai_base_url": os.getenv("OPENAI_BASE_URL"),
            "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
            "local_model_name": os.getenv("LOCAL_MODEL_NAME"),
        }

    def validate(self) -> bool:
        """
        Validate configuration settings.

        Returns:
            True if configuration is valid, False otherwise
        """
        errors = []

        # Validate AI settings
        if self.ai.preferred_provider not in ["openai", "anthropic"]:
            errors.append(f"Invalid AI provider: {self.ai.preferred_provider}")

        if not (0.0 <= self.ai.openai_temperature <= 2.0):
            errors.append(f"Invalid OpenAI temperature: {self.ai.openai_temperature}")

        if not (0.0 <= self.ai.anthropic_temperature <= 1.0):
            errors.append(
                f"Invalid Anthropic temperature: {self.ai.anthropic_temperature}"
            )

        # Validate processing settings
        if not (0.0 <= self.processing.confidence_threshold <= 1.0):
            errors.append(
                f"Invalid confidence threshold: {self.processing.confidence_threshold}"
            )

        if self.processing.min_text_length < 0:
            errors.append(f"Invalid min_text_length: {self.processing.min_text_length}")

        if self.processing.max_text_for_ai < 100:
            errors.append(f"Invalid max_text_for_ai: {self.processing.max_text_for_ai}")

        # Validate file settings
        if self.files.max_file_size_mb <= 0:
            errors.append(f"Invalid max_file_size_mb: {self.files.max_file_size_mb}")

        # Validate web settings
        if not (1 <= self.web.port <= 65535):
            errors.append(f"Invalid port: {self.web.port}")

        # Check for required placeholders in patterns
        required_org_placeholders = ["{company}"]
        if not any(
            ph in self.organization.structure_pattern
            for ph in required_org_placeholders
        ):
            errors.append("Organization structure pattern must contain {company}")

        if errors:
            for error in errors:
                logger.error(f"Configuration validation error: {error}")
            return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "ai": {
                "preferred_provider": self.ai.preferred_provider,
                "openai_model": self.ai.openai_model,
                "openai_temperature": self.ai.openai_temperature,
                "openai_max_tokens": self.ai.openai_max_tokens,
                "anthropic_model": self.ai.anthropic_model,
                "anthropic_temperature": self.ai.anthropic_temperature,
                "anthropic_max_tokens": self.ai.anthropic_max_tokens,
            },
            "organization": {
                "structure_pattern": self.organization.structure_pattern,
                "filename_pattern": self.organization.filename_pattern,
                "date_format": self.organization.date_format,
            },
            "processing": {
                "enable_ocr": self.processing.enable_ocr,
                "min_text_length": self.processing.min_text_length,
                "max_text_for_ai": self.processing.max_text_for_ai,
                "confidence_threshold": self.processing.confidence_threshold,
            },
            "files": {
                "max_file_size_mb": self.files.max_file_size_mb,
                "allowed_extensions": self.files.allowed_extensions,
                "input_dir": self.files.input_dir,
                "output_dir": self.files.output_dir,
                "copy_mode": self.files.copy_mode,
            },
            "web": {
                "port": self.web.port,
                "debug": self.web.debug,
                "host": self.web.host,
            },
        }


# Global configuration instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = AppConfig.load_from_file()
        if not _config.validate():
            logger.warning(
                "Configuration validation failed, using defaults where possible"
            )
    return _config


def reload_config(config_path: Optional[Union[str, Path]] = None) -> AppConfig:
    """Reload configuration from file."""
    global _config
    _config = AppConfig.load_from_file(config_path)
    if not _config.validate():
        logger.warning("Configuration validation failed, using defaults where possible")
    return _config
