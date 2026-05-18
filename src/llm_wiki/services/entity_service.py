# -----------------------------------------------------------------------------
# Copyright (c) 2026 Salvatore D'Angelo, Code4Projects
# Licensed under the MIT License. See LICENSE.md for details.
# -----------------------------------------------------------------------------
"""
EntityService - Manages Entity domain objects.

Handles creation and updates of entities (people, organizations, tools).
"""

import logging
import re
from datetime import datetime
from pathlib import Path

from llm_wiki.clients import get_llm_client
from llm_wiki.domain.entities import Entity
from llm_wiki.models import EntityRepository
from llm_wiki.services.prompts import format_prompt
from llm_wiki.utils import sanitize_filename

logger = logging.getLogger(name=__name__)


class EntityService:
    """Service for managing Entity domain objects."""

    def __init__(self, entity_repo: EntityRepository) -> None:
        """
        Initialize entity service.

        Args:
            entity_repo: Repository for entity persistence
        """
        self.entity_repo = entity_repo
        self.llm = get_llm_client()

    def create_or_update(
        self, entity_name: str, article_title: str, source_file: str, article_content: str = ""
    ) -> Path:
        """
        Create a new entity or update an existing one.

        Args:
            entity_name: Name of the entity
            article_title: Title of the source article
            source_file: Filename of the source (without .md)
            article_content: Content of the article for definition generation

        Returns:
            Path to the created/updated entity file
        """
        filename: str = sanitize_filename(text=entity_name)

        # Try to find existing entity
        existing_entity: Entity | None = self.entity_repo.find_by_name(name=entity_name)

        if existing_entity:
            # Update existing entity
            self._update_entity_metadata(entity=existing_entity, source_file=source_file)
            output_path = self.entity_repo.save(entity=existing_entity)
            logger.debug("Updated entity", extra={"entity": entity_name})
        else:
            # Create new entity
            definition: str = self._generate_definition(entity_name, article_content, article_title)

            entity: Entity = Entity(
                name=entity_name,
                filename=filename,
                definition=definition,
                sources=[source_file],
                created=datetime.now(),
                updated=datetime.now(),
            )

            output_path = self.entity_repo.save(entity)
            logger.debug(msg="Created entity", extra={"entity": entity_name})

        return output_path

    def _update_entity_metadata(self, entity: Entity, source_file: str) -> None:
        """
        Update entity with new source.

        Args:
            entity: Entity to update
            source_file: Source file to add
        """
        if source_file not in entity.sources:
            entity.add_source(source=source_file)

    def _generate_definition(self, entity_name: str, article_content: str, article_title: str) -> str:
        """
        Use LLM to generate a brief definition of an entity.

        Args:
            entity_name: Name of the entity
            article_content: Content of the article
            article_title: Title of the article

        Returns:
            Generated definition text
        """
        prompt: str = format_prompt(
            template_name="generate_entity_definition",
            entity_name=entity_name,
            article_title=article_title,
            article_content=article_content[:3000],
        )

        system_prompt: str = format_prompt(template_name="generate_entity_definition_system")

        try:
            definition: str = self.llm.generate(prompt, system_prompt).strip()
            # Remove any markdown formatting or labels
            definition = re.sub(r"^(Definition:|Overview:)\s*", "", definition, flags=re.IGNORECASE)
            return definition
        except Exception as e:
            logger.warning(msg="Could not generate definition", extra={"entity": entity_name, "error": str(e)})
            return "*This entity page will be expanded as more sources are added.*"
