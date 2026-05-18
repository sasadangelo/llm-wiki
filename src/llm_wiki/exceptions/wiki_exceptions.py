"""Custom exceptions for wiki operations."""


class WikiError(Exception):
    """Base exception for wiki operations."""

    pass


class IngestError(WikiError):
    """Error during article ingestion."""

    pass


class QueryError(WikiError):
    """Error during wiki query."""

    pass


class LLMError(WikiError):
    """Error from LLM provider."""

    pass
