# -----------------------------------------------------------------------------
# Copyright (c) 2026 Salvatore D'Angelo, Code4Projects
# Licensed under the MIT License. See LICENSE.md for details.
# -----------------------------------------------------------------------------
"""
WatsonX LLM Client implementation.

This module provides a client for communicating with IBM WatsonX AI services.
"""

import os

from dotenv import load_dotenv
from langchain_core.messages.ai import AIMessage

from llm_wiki.clients.base import LLMClient
from llm_wiki.core.config import WatsonXConfig

# Load environment variables
load_dotenv()


class WatsonXClient(LLMClient):
    """IBM WatsonX LLM client using langchain-ibm."""

    def __init__(self, config: WatsonXConfig) -> None:
        """
        Initialize WatsonX client.

        Args:
            config: WatsonX configuration

        Raises:
            ImportError: If langchain-ibm or ibm-watsonx-ai is not installed
            ValueError: If API key or project ID is missing
        """
        try:
            from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
            from langchain_ibm import ChatWatsonx
        except ImportError as e:
            raise ImportError(
                "langchain-ibm and ibm-watsonx-ai are required for WatsonX client. "
                "Install with: uv add langchain-ibm ibm-watsonx-ai"
            ) from e

        self.url = config.url
        self.project_id = os.getenv("WATSONX_PROJECT_ID")
        self.api_key = os.getenv("WATSONX_API_KEY")
        self.model = config.model
        self.temperature = config.temperature or 0.7

        if not self.api_key:
            raise ValueError("WatsonX API key not found in .env file (WATSONX_API_KEY)")
        if not self.project_id:
            raise ValueError("WatsonX project ID not found in .env file (WATSONX_PROJECT_ID)")

        # Initialize ChatWatsonx
        parameters = {
            GenParams.DECODING_METHOD: "sample",
            GenParams.MIN_NEW_TOKENS: 1,
            GenParams.TEMPERATURE: self.temperature,
        }

        self.chat = ChatWatsonx(
            model_id=self.model,
            url=self.url,  # type: ignore[arg-type]
            project_id=self.project_id,
            params=parameters,
        )

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """
        Generate text using WatsonX via langchain-ibm.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for context

        Returns:
            Generated text response

        Raises:
            RuntimeError: If the WatsonX API call fails
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
            raise RuntimeError(f"WatsonX API error: {e}") from e
