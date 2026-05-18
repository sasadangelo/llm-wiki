# -----------------------------------------------------------------------------
# Copyright (c) 2026 Salvatore D'Angelo, Code4Projects
# Licensed under the MIT License. See LICENSE.md for details.
# -----------------------------------------------------------------------------
"""
LogService - Manages wiki log entries.

Handles adding entries to the wiki log for operations like ingest and query.
"""

import logging
from pathlib import Path

from llm_wiki.models import WikiRepository

logger = logging.getLogger(name=__name__)


class LogService:
    """Service for managing wiki log."""

    def __init__(self, wiki_repo: WikiRepository, wiki_root: Path) -> None:
        """
        Initialize log service.

        Args:
            wiki_repo: Repository for wiki-level operations
            wiki_root: Root path of the wiki
        """
        self.wiki_repo = wiki_repo
        self.wiki_root = wiki_root

    def add_ingest_entry(self, article_title: str, created_pages: list[Path]) -> None:
        """
        Add an ingest operation entry to the log.

        Args:
            article_title: Title of the ingested article
            created_pages: List of paths to created/updated pages
        """
        # Build details list
        details: list[str] = ["Created/Updated:"]
        for page in created_pages:
            rel_path: Path = page.relative_to(self.wiki_root)
            details.append(f"- `{rel_path}`")

        # Add log entry using repository
        self.wiki_repo.add_log_entry(operation="ingest", title=article_title, details=details)
        logger.debug(msg="Added ingest log entry", extra={"article": article_title})

    def add_query_entry(self, question: str, pages_used: list[str], saved_path: Path | None = None) -> None:
        """
        Add a query operation entry to the log.

        Args:
            question: The question that was asked
            pages_used: List of page paths that were consulted
            saved_path: Optional path where the answer was saved
        """
        # Build details list
        details: list[str] = [f"Pages consulted: {len(pages_used)}"]
        if saved_path:
            rel_path: Path = saved_path.relative_to(self.wiki_root)
            details.append(f"Answer filed: `{rel_path}`")

        # Add log entry using repository
        # Truncate question if too long
        title: str = question[:60] + "..." if len(question) > 60 else question
        self.wiki_repo.add_log_entry(operation="query", title=title, details=details)
        logger.debug(msg="Added query log entry")
