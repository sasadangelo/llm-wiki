"""
Services layer - Business logic and orchestration.

This package contains service classes that implement business logic:
- WikiService: Facade that coordinates all other services (public API)
- EntityService: Manages Entity domain objects
- ConceptService: Manages Concept domain objects
- SourceService: Manages Source domain objects
- IndexService: Manages wiki index updates
- LogService: Manages wiki log entries

Only WikiService is exposed publicly. Other services are internal.
"""

from llm_wiki.services.wiki_service import IngestResult, QueryResult, WikiService

__all__ = [
    "WikiService",
    "IngestResult",
    "QueryResult",
]

# Made with Bob
