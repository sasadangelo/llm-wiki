# -----------------------------------------------------------------------------
# Copyright (c) 2026 Salvatore D'Angelo, Code4Projects
# Licensed under the MIT License. See LICENSE.md for details.
# -----------------------------------------------------------------------------
"""
LLM Client Factory.

This module provides a factory for creating LLM client instances based on configuration.
Uses the Factory Method pattern to instantiate the appropriate client.
"""

from llm_wiki.clients.base import LLMClient
from llm_wiki.clients.ollama_client import OllamaClient
from llm_wiki.clients.openai_client import OpenAIClient
from llm_wiki.clients.watsonx_client import WatsonXClient
from llm_wiki.core import get_config
from llm_wiki.core.config import AppConfig


class LLMClientFactory:
    """
    Factory class for creating LLM clients.

    This class uses the Factory Method pattern to create the appropriate
    LLM client based on the application configuration.
    """

    @staticmethod
    def create_client() -> LLMClient:
        """
        Factory method to create an LLM client based on global configuration.

        The configuration must be initialized before calling this method
        (via init_config() in agent startup).

        Returns:
            LLMClient: Configured LLM client instance

        Raises:
            RuntimeError: If configuration not initialized
            ValueError: If provider configuration is missing or invalid

        Example:
            >>> from llm_wiki.core import init_config
            >>> from llm_wiki.clients import LLMClientFactory
            >>> init_config()
            >>> client = LLMClientFactory.create_client()
            >>> response = client.generate("Hello, world!")
        """
        cfg: AppConfig = get_config()
        provider_name = cfg.llm.provider

        if provider_name == "ollama":
            return OllamaClient(config=cfg.llm.ollama)
        elif provider_name == "watsonx":
            if cfg.llm.watsonx is None:
                raise ValueError("WatsonX configuration is missing in config.yaml")
            return WatsonXClient(config=cfg.llm.watsonx)
        elif provider_name == "openai":
            if cfg.llm.openai is None:
                raise ValueError("OpenAI configuration is missing in config.yaml")
            return OpenAIClient(config=cfg.llm.openai)
        else:
            raise ValueError(f"Unknown LLM provider: {provider_name}. Supported providers: ollama, watsonx, openai")


def get_llm_client() -> LLMClient:
    """
    Convenience function to get an LLM client using the factory.

    This is a shorthand for LLMClientFactory.create_client().

    Returns:
        LLMClient: Configured LLM client instance

    Raises:
        RuntimeError: If configuration not initialized
        ValueError: If provider configuration is missing or invalid

    Example:
        >>> from llm_wiki.core import init_config
        >>> from llm_wiki.clients import get_llm_client
        >>> init_config()
        >>> client = get_llm_client()
        >>> response = client.generate("Hello, world!")
    """
    return LLMClientFactory.create_client()
