"""Custom exceptions for wiki operations."""

from .wiki_exceptions import IngestError, LLMError, QueryError, WikiError

__all__ = ["WikiError", "IngestError", "QueryError", "LLMError"]
