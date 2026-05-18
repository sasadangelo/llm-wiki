# -----------------------------------------------------------------------------
# Copyright (c) 2026 Salvatore D'Angelo, Code4Projects
# Licensed under the MIT License. See LICENSE.md for details.
# -----------------------------------------------------------------------------
"""
OpenAI LLM Client implementation.

This module provides a client for communicating with OpenAI's API services.
"""

import os

from dotenv import load_dotenv
from langchain_core.messages.ai import AIMessage

from llm_wiki.clients.base import LLMClient
from llm_wiki.core.config import OpenAIConfig

# Load environment variables
load_dotenv()


class OpenAIClient(LLMClient):
    """OpenAI LLM client using langchain-openai."""

    def __init__(self, config: OpenAIConfig) -> None:
        """
        Initialize OpenAI client.

        Args:
            config: OpenAI configuration

        Raises:
            ImportError: If langchain-openai is not installed
            ValueError: If API key is missing
        """
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as e:
            raise ImportError(
                "langchain-openai is required for OpenAI client. Install with: uv add langchain-openai"
            ) from e

        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = config.model
        self.temperature = config.temperature or 0.7
        self.max_tokens = config.max_tokens or 4000

        if not self.api_key:
            raise ValueError("OpenAI API key not found in .env file (OPENAI_API_KEY)")

        # Initialize ChatOpenAI (api_key read from OPENAI_API_KEY env var automatically)
        self.chat = ChatOpenAI(
            model=self.model,
            temperature=self.temperature,
            max_completion_tokens=self.max_tokens,
        )

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """
        Generate text using OpenAI via langchain-openai.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for context

        Returns:
            Generated text response

        Raises:
            RuntimeError: If the OpenAI API call fails
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
            raise RuntimeError(f"OpenAI API error: {e}") from e
