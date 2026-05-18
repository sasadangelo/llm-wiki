"""Request DTOs for API communication."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Chat request from client."""

    message: str = Field(default=..., description="User message")
    conversation_id: str | None = Field(default=None, description="Optional conversation ID")
    stream: bool = Field(default=False, description="Whether to stream the response")


class IngestRequest(BaseModel):
    """Ingest article request."""

    article_path: str = Field(default=..., description="Path to article file")


class QueryRequest(BaseModel):
    """Query wiki request."""

    question: str = Field(default=..., description="Question to answer")
    save: bool = Field(default=False, description="Whether to save the answer as analysis")
