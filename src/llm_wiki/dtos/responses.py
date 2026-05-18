"""Response DTOs for API communication."""

from datetime import datetime

from pydantic import BaseModel, Field


class ChatResponse(BaseModel):
    """Chat response to client."""

    response: str = Field(default=..., description="Agent response")
    conversation_id: str = Field(default=..., description="Conversation ID")
    actions_taken: list[dict] = Field(default_factory=list, description="Actions performed")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Response timestamp")


class IngestResponse(BaseModel):
    """Ingest operation response."""

    success: bool = Field(default=..., description="Whether ingest succeeded")
    article_name: str = Field(default=..., description="Name of ingested article")
    pages_created: int = Field(default=..., description="Number of pages created/updated")
    error: str | None = Field(default=None, description="Error message if failed")


class QueryResponse(BaseModel):
    """Query operation response."""

    success: bool = Field(default=..., description="Whether query succeeded")
    question: str = Field(default=..., description="Original question")
    answer: str = Field(default=..., description="Generated answer")
    sources_used: list[str] = Field(default_factory=list, description="Sources consulted")
    saved_path: str | None = Field(default=None, description="Path where answer was saved")
    error: str | None = Field(default=None, description="Error message if failed")


class StatusResponse(BaseModel):
    """Wiki status response."""

    raw_articles: int = Field(default=..., description="Number of raw articles")
    processed_sources: int = Field(default=..., description="Number of processed sources")
    entities: int = Field(default=..., description="Number of entities")
    concepts: int = Field(default=..., description="Number of concepts")
    analyses: int = Field(default=..., description="Number of analyses")
    unprocessed: int = Field(default=..., description="Number of unprocessed articles")


class BulkIngestResponse(BaseModel):
    """Bulk ingest response."""

    success: bool = Field(default=..., description="Whether bulk ingest succeeded")
    total_articles: int = Field(default=..., description="Total articles processed")
    successful: int = Field(default=..., description="Number of successful ingests")
    failed: int = Field(default=..., description="Number of failed ingests")
    details: list[dict] = Field(default_factory=list, description="Details per article")
    error: str | None = Field(default=None, description="Error message if failed")
