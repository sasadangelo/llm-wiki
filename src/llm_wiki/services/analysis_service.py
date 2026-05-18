# -----------------------------------------------------------------------------
# Copyright (c) 2026 Salvatore D'Angelo, Code4Projects
# Licensed under the MIT License. See LICENSE.md for details.
# -----------------------------------------------------------------------------
"""
AnalysisService - Manages Analysis domain objects.

Handles creation of analysis pages from query results.
"""

import logging
import re
from datetime import datetime
from pathlib import Path

from llm_wiki.domain.entities import Analysis
from llm_wiki.models import AnalysisRepository

logger = logging.getLogger(name=__name__)


class AnalysisService:
    """Service for managing Analysis domain objects."""

    def __init__(self, analysis_repo: AnalysisRepository) -> None:
        """
        Initialize analysis service.

        Args:
            analysis_repo: Repository for analysis persistence
        """
        self.analysis_repo = analysis_repo

    def create(self, question: str, answer: str, sources_consulted: list[str]) -> Path:
        """
        Create an analysis page from a query result.

        Args:
            question: The question that was asked
            answer: The generated answer
            sources_consulted: List of source page paths that were consulted

        Returns:
            Path to the created analysis file
        """
        # Create filename from question
        safe_name: str = re.sub(r'[<>:"/\\|?*]', "", question)
        safe_name = re.sub(r"\s+", "-", safe_name).strip("-")[:80]
        filename = safe_name

        # Create Analysis entity
        analysis: Analysis = Analysis(
            question=question,
            filename=filename,
            answer=answer,
            sources_consulted=sources_consulted,
            created=datetime.now(),
        )

        # Save using repository
        output_path: Path = self.analysis_repo.save(analysis)
        logger.debug(msg="Created analysis", extra={"question": question[:50]})

        return output_path
