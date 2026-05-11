"""
LLM Provider abstraction for multiple backends.
Supports: Ollama, WatsonX, OpenAI
"""

import os
from abc import ABC, abstractmethod
from typing import Any

import yaml  # type: ignore
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate text from prompt."""
        pass


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider using langchain-ollama."""

    def __init__(self, config: dict[str, Any]):
        try:
            from langchain_ollama import ChatOllama
        except ImportError as e:
            raise ImportError(
                "langchain-ollama is required for Ollama provider. Install with: uv add langchain-ollama"
            ) from e

        self.base_url = config.get("base_url", "http://localhost:11434")
        self.model = config.get("model", "llama3.2")
        self.temperature = config.get("temperature", 0.7)

        # Initialize ChatOllama
        self.chat = ChatOllama(
            model=self.model,
            base_url=self.base_url,
            temperature=self.temperature,
        )

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate text using Ollama via langchain-ollama."""
        try:
            # Combine system and user prompt if provided
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            # Use invoke for synchronous response
            response = self.chat.invoke(full_prompt)
            return str(response.content)
        except Exception as e:
            raise RuntimeError(f"Ollama API error: {e}") from e


class WatsonXProvider(LLMProvider):
    """IBM WatsonX LLM provider using langchain-ibm."""

    def __init__(self, config: dict[str, Any]):
        try:
            from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
            from langchain_ibm import ChatWatsonx
        except ImportError as e:
            raise ImportError(
                "langchain-ibm and ibm-watsonx-ai are required for WatsonX provider. "
                "Install with: uv add langchain-ibm ibm-watsonx-ai"
            ) from e

        self.url = config.get("url", "https://us-south.ml.cloud.ibm.com")
        self.project_id = os.getenv("WATSONX_PROJECT_ID")
        self.api_key = os.getenv("WATSONX_API_KEY")
        self.model = config.get("model", "ibm/granite-4-h-small")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 4000)

        if not self.api_key:
            raise ValueError("WatsonX API key not found in .env file (WATSONX_API_KEY)")
        if not self.project_id:
            raise ValueError("WatsonX project ID not found in .env file (WATSONX_PROJECT_ID)")

        # Initialize ChatWatsonx
        parameters = {
            GenParams.DECODING_METHOD: "sample",
            GenParams.MIN_NEW_TOKENS: 1,
            GenParams.MAX_NEW_TOKENS: self.max_tokens,
            GenParams.TEMPERATURE: self.temperature,
        }

        self.chat = ChatWatsonx(
            model_id=self.model,
            url=self.url,  # type: ignore[arg-type]
            project_id=self.project_id,
            params=parameters,
        )

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate text using WatsonX via langchain-ibm."""
        try:
            # Combine system and user prompt if provided
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            # Use invoke instead of stream for simpler synchronous response
            response = self.chat.invoke(full_prompt)
            return str(response.content)
        except Exception as e:
            raise RuntimeError(f"WatsonX API error: {e}") from e


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider using langchain-openai."""

    def __init__(self, config: dict[str, Any]):
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as e:
            raise ImportError(
                "langchain-openai is required for OpenAI provider. Install with: uv add langchain-openai"
            ) from e

        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = config.get("model", "gpt-4")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 4000)

        if not self.api_key:
            raise ValueError("OpenAI API key not found in .env file (OPENAI_API_KEY)")

        # Initialize ChatOpenAI (api_key read from OPENAI_API_KEY env var automatically)
        self.chat = ChatOpenAI(
            model=self.model,
            temperature=self.temperature,
            max_completion_tokens=self.max_tokens,
        )

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate text using OpenAI via langchain-openai."""
        try:
            # Combine system and user prompt if provided
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            # Use invoke for synchronous response
            response = self.chat.invoke(full_prompt)
            return str(response.content)
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}") from e


def load_config(config_path: str = "config.yaml") -> dict[str, Any]:
    """Load configuration from YAML file."""
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_llm_provider(config_path: str = "config.yaml") -> LLMProvider:
    """Get LLM provider based on configuration."""
    config = load_config(config_path)
    provider_name = config["llm"]["provider"]

    providers = {
        "ollama": OllamaProvider,
        "watsonx": WatsonXProvider,
        "openai": OpenAIProvider,
    }

    if provider_name not in providers:
        raise ValueError(f"Unknown provider: {provider_name}")

    provider_class = providers[provider_name]
    provider_config = config["llm"][provider_name]

    return provider_class(provider_config)


# Made with Bob
