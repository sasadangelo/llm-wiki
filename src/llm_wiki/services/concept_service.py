# -----------------------------------------------------------------------------
# Copyright (c) 2026 Salvatore D'Angelo, Code4Projects
# Licensed under the MIT License. See LICENSE.md for details.
# -----------------------------------------------------------------------------
"""
ConceptService - Manages Concept domain objects.

Handles creation and updates of concepts (technical concepts, patterns).
"""

import logging
import re
from datetime import datetime
from pathlib import Path

from llm_wiki.clients import get_llm_client
from llm_wiki.domain.entities import Concept
from llm_wiki.models import ConceptRepository
from llm_wiki.services.prompts import format_prompt
from llm_wiki.utils import sanitize_filename

logger = logging.getLogger(name=__name__)


class ConceptService:
    """Service for managing Concept domain objects."""

    def __init__(self, concept_repo: ConceptRepository) -> None:
        """
        Initialize concept service.

        Args:
            concept_repo: Repository for concept persistence
        """
        self.concept_repo = concept_repo
        self.llm = get_llm_client()

    def create_or_update(
        self,
        concept_name: str,
        article_title: str,
        source_file: str,
        related_concepts: list[str],
        article_content: str = "",
    ) -> Path:
        """
        Create a new concept or update an existing one.

        Args:
            concept_name: Name of the concept
            article_title: Title of the source article
            source_file: Filename of the source (without .md)
            related_concepts: List of related concept names
            article_content: Content of the article for definition generation

        Returns:
            Path to the created/updated concept file
        """
        filename: str = sanitize_filename(text=concept_name)

        # Filter out the current concept from related concepts
        related_list: list[str] = [c for c in related_concepts if c and sanitize_filename(text=c) != filename]

        # Try to find existing concept
        existing_concept: Concept | None = self.concept_repo.find_by_name(name=concept_name)

        if existing_concept:
            # Update existing concept
            self._update_concept_metadata(
                concept=existing_concept, source_file=source_file, related_concepts=related_list
            )
            output_path = self.concept_repo.save(concept=existing_concept)
            logger.debug(msg="Updated concept", extra={"concept": concept_name})
        else:
            # Create new concept
            definition: str = self._generate_definition(concept_name, article_content, article_title)

            concept: Concept = Concept(
                name=concept_name,
                filename=filename,
                definition=definition,
                sources=[source_file],
                related_concepts=related_list,
                created=datetime.now(),
                updated=datetime.now(),
            )

            output_path = self.concept_repo.save(concept)
            logger.debug(msg="Created concept", extra={"concept": concept_name})

        return output_path

    def _update_concept_metadata(
        self,
        concept: Concept,
        source_file: str,
        related_concepts: list[str],
    ) -> None:
        """
        Update concept with new source and related concepts.

        Args:
            concept: Concept to update
            source_file: Source file to add
            related_concepts: Related concepts to add
        """
        if source_file not in concept.sources:
            concept.add_source(source=source_file)

        for related in related_concepts:
            if related not in concept.related_concepts:
                concept.add_related_concept(concept=related)

    def _generate_definition(self, concept_name: str, article_content: str, article_title: str) -> str:
        """
        Use LLM to generate a brief definition of a concept.

        Args:
            concept_name: Name of the concept
            article_content: Content of the article
            article_title: Title of the article

        Returns:
            Generated definition text
        """
        prompt: str = format_prompt(
            template_name="generate_concept_definition",
            concept_name=concept_name,
            article_title=article_title,
            article_content=article_content[:3000],
        )

        system_prompt: str = format_prompt(template_name="generate_concept_definition_system")

        try:
            definition: str = self.llm.generate(prompt, system_prompt).strip()
            # Remove any markdown formatting or labels
            definition = re.sub(r"^(Definition:|Overview:|Explanation:)\s*", "", definition, flags=re.IGNORECASE)
            return definition
        except Exception as e:
            logger.warning(msg="Could not generate definition", extra={"concept": concept_name, "error": str(e)})
            return "*This concept page will be expanded as more sources are added.*"
