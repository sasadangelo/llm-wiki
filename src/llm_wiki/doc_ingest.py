#!/usr/bin/env python3
"""
Automatic ingest agent for LLM Wiki.
Now uses WikiService for all operations.
"""

import sys
from pathlib import Path

from llm_wiki.core import init_config
from llm_wiki.services import IngestResult, WikiService


def ingest_article(article_path: Path) -> None:
    """
    Main ingest function using WikiService.

    Args:
        article_path: Path to article file
    """
    print(f"\n{'=' * 60}")
    print(f"Ingesting: {article_path.name}")
    print(f"{'=' * 60}\n")

    # Initialize service (automatically loads config and creates LLM client)
    print("Initializing wiki service...")
    service: WikiService = WikiService()
    print("✓ Wiki service initialized\n")

    # Ingest article
    print("Processing article...")
    result: IngestResult = service.ingest(article_path)

    if result.success:
        print(f"\n{'=' * 60}")
        print("✓ Ingest complete!")
        print(f"  Created/updated {len(result.created_pages)} pages")
        print(f"{'=' * 60}\n")
    else:
        print(f"\n{'=' * 60}")
        print("✗ Ingest failed!")
        print(f"  Error: {result.error}")
        print(f"{'=' * 60}\n")
        sys.exit(1)


def main() -> None:
    # Initialize configuration at startup
    init_config()

    if len(sys.argv) < 2:
        print("Usage: .venv/bin/python src/llm_wiki/doc_ingest.py <article_path>")
        print("\nExample:")
        print("  .venv/bin/python src/llm_wiki/doc_ingest.py raw/articles/article.md")
        sys.exit(1)

    article_path: Path = Path(sys.argv[1])

    if not article_path.exists():
        print(f"Error: File not found: {article_path}")
        sys.exit(1)

    ingest_article(article_path)


if __name__ == "__main__":
    main()
