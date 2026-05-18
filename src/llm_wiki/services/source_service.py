# -----------------------------------------------------------------------------
# Copyright (c) 2026 Salvatore D'Angelo, Code4Projects
# Licensed under the MIT License. See LICENSE.md for details.
# -----------------------------------------------------------------------------
"""
SourceService - Manages Source domain objects.

Handles creation of source summaries from articles.
"""

import logging
from datetime import datetime
from pathlib import Path

from llm_wiki.domain.entities import Source
from llm_wiki.domain.value_objects import Frontmatter, Metadata
from llm_wiki.models import SourceRepository
from llm_wiki.utils import sanitize_filename

logger = logging.getLogger(name=__name__)


class SourceService:
    """Service for managing Source domain objects."""

    def __init__(self, source_repo: SourceRepository) -> None:
        """
        Initialize source service.

        Args:
            source_repo: Repository for source persistence
        """
        self.source_repo = source_repo

    def create(self, article_path: Path, frontmatter: Frontmatter, metadata: Metadata) -> Path:
        """
        Create a source summary from an article.

        Args:
            article_path: Path to the original article file
            frontmatter: Article frontmatter metadata
            metadata: Extracted metadata from the article

        Returns:
            Path to the created source file
        """
        filename: str = sanitize_filename(text=frontmatter.title)

        # Create Source entity
        source: Source = Source(
            title=frontmatter.title,
            filename=filename,
            summary=metadata.summary,
            key_concepts=list(metadata.key_concepts),
            entities=list(metadata.entities),
            tags=list(metadata.tags),
            url=frontmatter.url,
            author=frontmatter.author,
            created=datetime.now(),
        )

        # Save using repository
        output_path: Path = self.source_repo.save(source=source, raw_file_path=article_path)
        logger.debug(msg="Created source summary", extra={"title": frontmatter.title})

        return output_path
