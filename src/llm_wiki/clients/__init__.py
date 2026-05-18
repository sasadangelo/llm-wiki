# -----------------------------------------------------------------------------
# Copyright (c) 2026 Salvatore D'Angelo, Code4Projects
# Licensed under the MIT License. See LICENSE.md for details.
# -----------------------------------------------------------------------------
"""
LLM client implementations for different providers.

This package contains client classes that handle network communication
with various LLM providers (Ollama, WatsonX, OpenAI).

The package follows a clean architecture with:
- base.py: Abstract base class defining the client interface
- ollama_client.py: Ollama implementation
- watsonx_client.py: WatsonX implementation
- openai_client.py: OpenAI implementation
- factory.py: Factory class with factory method pattern
"""

from llm_wiki.clients.base import LLMClient
from llm_wiki.clients.factory import LLMClientFactory, get_llm_client
from llm_wiki.clients.ollama_client import OllamaClient
from llm_wiki.clients.openai_client import OpenAIClient
from llm_wiki.clients.watsonx_client import WatsonXClient

__all__ = [
    # Base class
    "LLMClient",
    # Implementations
    "OllamaClient",
    "WatsonXClient",
    "OpenAIClient",
    # Factory
    "LLMClientFactory",
    "get_llm_client",
]
