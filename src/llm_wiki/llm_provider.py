"""
LLM Provider abstraction for multiple backends.
Supports: Ollama, WatsonX, OpenAI
"""

import os
from abc import ABC, abstractmethod
from typing import Any

import requests  # type: ignore
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
    """Ollama local LLM provider."""

    def __init__(self, config: dict[str, Any]):
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.model = config.get("model", "llama3.2")
        self.temperature = config.get("temperature", 0.7)

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate text using Ollama API."""
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": self.temperature},
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            raise RuntimeError(f"Ollama API error: {e}") from e


class WatsonXProvider(LLMProvider):
    """IBM WatsonX LLM provider."""

    def __init__(self, config: dict[str, Any]):
        self.url = config.get("url", "https://us-south.ml.cloud.ibm.com")
        self.project_id = os.getenv("WATSONX_PROJECT_ID")
        self.api_key = os.getenv("WATSONX_API_KEY")
        self.model = config.get("model", "meta-llama/llama-3-70b-instruct")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 4000)

        if not self.api_key:
            raise ValueError("WatsonX API key not found in .env file (WATSONX_API_KEY)")
        if not self.project_id:
            raise ValueError("WatsonX project ID not found in .env file (WATSONX_PROJECT_ID)")

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate text using WatsonX API."""
        # Combine system and user prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        url = f"{self.url}/ml/v1/text/generation?version=2023-05-29"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        payload = {
            "model_id": self.model,
            "input": full_prompt,
            "parameters": {
                "temperature": self.temperature,
                "max_new_tokens": self.max_tokens,
            },
            "project_id": self.project_id,
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=300)
            response.raise_for_status()
            return response.json()["results"][0]["generated_text"]
        except Exception as e:
            raise RuntimeError(f"WatsonX API error: {e}") from e


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""

    def __init__(self, config: dict[str, Any]):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = config.get("model", "gpt-4")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 4000)

        if not self.api_key:
            raise ValueError("OpenAI API key not found in .env file (OPENAI_API_KEY)")

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate text using OpenAI API."""
        url = "https://api.openai.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=300)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
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
