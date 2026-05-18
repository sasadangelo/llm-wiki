# -----------------------------------------------------------------------------
# Copyright (c) 2026 Salvatore D'Angelo, Code4Projects
# Licensed under the MIT License. See LICENSE.md for details.
# -----------------------------------------------------------------------------
"""
Ollama LLM Client implementation.

This module provides a client for communicating with local Ollama instances.
"""

from langchain_core.messages.ai import AIMessage

from llm_wiki.clients.base import LLMClient
from llm_wiki.core.config import OllamaConfig


class OllamaClient(LLMClient):
    """Ollama local LLM client using langchain-ollama."""

    def __init__(self, config: OllamaConfig) -> None:
        """
        Initialize Ollama client.

        Args:
            config: Ollama configuration

        Raises:
            ImportError: If langchain-ollama is not installed
        """
        try:
            from langchain_ollama import ChatOllama
        except ImportError as e:
            raise ImportError(
                "langchain-ollama is required for Ollama client. Install with: uv add langchain-ollama"
            ) from e

        self.base_url = config.base_url
        self.model = config.model
        self.temperature = config.temperature or 0.7

        # Initialize ChatOllama
        self.chat = ChatOllama(
            model=self.model,
            base_url=self.base_url,
            temperature=self.temperature,
        )

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """
        Generate text using Ollama via langchain-ollama.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for context

        Returns:
            Generated text response

        Raises:
            RuntimeError: If the Ollama API call fails
        """
        try:
            # Combine system and user prompt if provided
            full_prompt: str = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            # Use invoke for synchronous response
            response: AIMessage = self.chat.invoke(input=full_prompt)
            return str(response.content)
        except Exception as e:
            raise RuntimeError(f"Ollama API error: {e}") from e
