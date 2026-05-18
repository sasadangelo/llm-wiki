# -----------------------------------------------------------------------------
# Copyright (c) 2026 Salvatore D'Angelo, Code4Projects
# Licensed under the MIT License. See LICENSE.md for details.
# -----------------------------------------------------------------------------
"""
IndexService - Manages wiki index operations.

Handles updating the wiki index, reading it, and searching for relevant pages.
"""

import logging
from pathlib import Path

from llm_wiki.clients import LLMClientFactory
from llm_wiki.models import ConceptRepository, EntityRepository, SourceRepository, WikiRepository
from llm_wiki.services.prompts import format_prompt
from llm_wiki.utils import extract_json_array_from_text

logger = logging.getLogger(name=__name__)


class IndexService:
    """Service for managing wiki index operations."""

    def __init__(
        self,
        wiki_repo: WikiRepository,
        source_repo: SourceRepository,
        entity_repo: EntityRepository,
        concept_repo: ConceptRepository,
        analyses_dir: Path,
        index_path: Path,
    ) -> None:
        """
        Initialize index service.

        Args:
            wiki_repo: Repository for wiki-level operations
            source_repo: Repository for sources
            entity_repo: Repository for entities
            concept_repo: Repository for concepts
            analyses_dir: Directory containing analysis files
            index_path: Path to the wiki index file
        """
        self.wiki_repo = wiki_repo
        self.source_repo = source_repo
        self.entity_repo = entity_repo
        self.concept_repo = concept_repo
        self.analyses_dir = analyses_dir
        self.index_path = index_path
        self.llm = LLMClientFactory.create_client()

    def update(self) -> None:
        """
        Update the wiki index with current page listings.

        Collects all filenames from repositories and updates the index.
        """
        # Get all filenames from repositories
        sources: list[str] = self.source_repo.list_all()
        entities: list[str] = self.entity_repo.list_all()
        concepts: list[str] = self.concept_repo.list_all()
        analyses: list[str] = [f.stem for f in self.analyses_dir.glob(pattern="*.md")]

        # Update index using repository
        self.wiki_repo.update_index(sources, entities, concepts, analyses)
        logger.debug(msg="Updated wiki index")

    def read_index(self) -> str:
        """
        Read the wiki index content.

        Returns:
            Index content as string, empty if index doesn't exist
        """
        if not self.index_path.exists():
            return ""
        return self.index_path.read_text(encoding="utf-8")

    def search_relevant_pages(self, index_content: str, question: str) -> list[str]:
        """
        Use LLM to identify relevant pages for answering the question.

        Args:
            index_content: Content of the wiki index
            question: User's question

        Returns:
            List of relevant page paths (relative to wiki/)
        """
        prompt: str = format_prompt(
            template_name="search_relevant_pages", index_content=index_content[:3000], question=question
        )

        system_prompt = format_prompt(template_name="search_relevant_pages_system")

        response: str = self.llm.generate(prompt, system_prompt)

        # Try to parse JSON array
        paths = extract_json_array_from_text(text=response)
        if paths:
            return [p for p in paths if isinstance(p, str)]
        else:
            logger.warning(msg="Could not parse LLM response", extra={"response": response[:200]})
            return []
