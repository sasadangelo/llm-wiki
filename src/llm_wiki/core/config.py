"""
Configuration management using Pydantic Settings.

This module handles loading and validating the config.yaml file.
It's the lowest-level component and doesn't depend on logging to avoid circular dependencies.
If configuration loading fails, it logs to console and exits the application.
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator


class OllamaConfig(BaseModel):
    """Ollama LLM provider configuration."""

    base_url: str = Field(default="http://localhost:11434")
    model: str = Field(default="llama3.2")
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)


class WatsonXConfig(BaseModel):
    """WatsonX LLM provider configuration."""

    url: str
    model: str
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, gt=0)


class OpenAIConfig(BaseModel):
    """OpenAI LLM provider configuration."""

    model: str
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, gt=0)


class LLMConfig(BaseModel):
    """LLM configuration with provider selection."""

    provider: Literal["ollama", "watsonx", "openai"] = Field(default="ollama")
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    watsonx: WatsonXConfig | None = None
    openai: OpenAIConfig | None = None

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate that provider is one of the supported values."""
        if v not in ["ollama", "watsonx", "openai"]:
            raise ValueError(f"Invalid provider: {v}. Must be one of: ollama, watsonx, openai")
        return v


class WikiConfig(BaseModel):
    """Wiki directory and processing configuration."""

    raw_dir: str = Field(default="raw")
    wiki_dir: str = Field(default="wiki")
    max_chunk_size: int = Field(default=8000, gt=0)


class LogConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO")
    console: bool = Field(default=False)
    file: str = Field(default="logs/llm-wiki.log")
    rotation: str = Field(default="10 MB")
    retention: str = Field(default="7 days")
    compression: str = Field(default="zip")

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of: {', '.join(valid_levels)}")
        return v_upper


class AppConfig(BaseModel):
    """Main application configuration."""

    llm: LLMConfig
    wiki: WikiConfig
    log: LogConfig


# Global configuration variable
_config: AppConfig | None = None


def get_config() -> AppConfig:
    """
    Get the global configuration.

    Raises:
        RuntimeError: If configuration not initialized

    Returns:
        AppConfig: The application configuration
    """
    if _config is None:
        raise RuntimeError("Configuration not initialized. Call init_config() at application startup.")
    return _config


def _load_config() -> AppConfig:
    """
    Load and validate configuration from config.yaml.

    Exits the application if configuration is invalid.

    Returns:
        AppConfig: Validated configuration
    """
    try:
        # Find config.yaml in the package directory
        config_path = Path(__file__).parent.parent / "config.yaml"

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        # Load YAML
        with open(config_path, encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        # Validate with Pydantic
        app_config = AppConfig(**config_data)

        # Console log success (can't use logging module yet)
        print(f"✓ Configuration loaded successfully from {config_path}")
        print(f"  - LLM Provider: {app_config.llm.provider}")
        print(f"  - Wiki Directory: {app_config.wiki.wiki_dir}")
        print(f"  - Log Level: {app_config.log.level}")

        return app_config

    except FileNotFoundError as e:
        print(f"✗ Configuration Error: {e}", file=sys.stderr)
        print("\nStack trace:", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)

    except yaml.YAMLError as e:
        print(f"✗ YAML Parsing Error in config.yaml: {e}", file=sys.stderr)
        print("\nStack trace:", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)

    except Exception as e:
        print(f"✗ Configuration Validation Error: {e}", file=sys.stderr)
        print("\nStack trace:", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)


def init_config() -> AppConfig:
    """
    Initialize the global application configuration.

    This should be called at application startup (e.g., in doc_ingest.py, doc_query.py).

    Returns:
        AppConfig: The application configuration

    Example:
        >>> from llm_wiki.core import init_config, get_config
        >>> init_config()  # Call once at startup
        >>> config = get_config()
        >>> print(config.llm.provider)
        ollama
    """
    global _config
    if _config is None:
        _config = _load_config()
    return _config
