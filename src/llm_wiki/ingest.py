#!/usr/bin/env python3
"""
Simple helper script for ingesting sources into the LLM Wiki.
This is optional - you can also just tell your LLM agent to ingest files directly.
"""

import re
import sys
from pathlib import Path
from re import Match


def list_raw_articles():
    """List all articles in raw/articles/ that haven't been ingested yet."""
    raw_dir = Path("raw/articles")
    wiki_sources = Path("wiki/sources")

    if not raw_dir.exists():
        print("Error: raw/articles/ directory not found")
        return []

    # Get all markdown files in raw/articles
    raw_files: list[Path] = list(raw_dir.glob(pattern="*.md"))

    # Get all source summaries in wiki/sources
    processed = set()
    if wiki_sources.exists():
        for source_file in wiki_sources.glob("*.md"):
            # Read the file and extract source_file from YAML frontmatter
            content: str = source_file.read_text()

            # Look for source_file in YAML frontmatter
            match: Match[str] | None = re.search(r"^source_file:\s*(.+)$", content, re.MULTILINE)
            if match:
                source_path = match.group(1).strip()
                # Extract just the filename from the path
                filename: str = Path(source_path).name
                processed.add(filename)

    # Find unprocessed files
    unprocessed = []
    for raw_file in raw_files:
        if raw_file.name not in processed:
            unprocessed.append(raw_file)

    return unprocessed


def show_status() -> None:
    """Show the current status of the wiki."""
    print("=== LLM Wiki Status ===\n")

    # Count files in each directory
    raw_count: int = len(list(Path("raw/articles").glob("*.md"))) if Path("raw/articles").exists() else 0
    wiki_sources: int = len(list(Path("wiki/sources").glob("*.md"))) if Path("wiki/sources").exists() else 0
    wiki_entities: int = len(list(Path("wiki/entities").glob("*.md"))) if Path("wiki/entities").exists() else 0
    wiki_concepts: int = len(list(Path("wiki/concepts").glob("*.md"))) if Path("wiki/concepts").exists() else 0
    wiki_analyses: int = len(list(Path("wiki/analyses").glob("*.md"))) if Path("wiki/analyses").exists() else 0

    print(f"Raw articles: {raw_count}")
    print(f"Processed sources: {wiki_sources}")
    print(f"Entity pages: {wiki_entities}")
    print(f"Concept pages: {wiki_concepts}")
    print(f"Analysis pages: {wiki_analyses}")
    print()

    # Show unprocessed articles
    unprocessed = list_raw_articles()
    if unprocessed:
        print(f"Unprocessed articles ({len(unprocessed)}):")
        for article in unprocessed:
            print(f"  - {article.name}")
    else:
        print("All articles have been processed!")
    print()


def suggest_next() -> None:
    """Suggest the next article to ingest."""
    unprocessed = list_raw_articles()
    if not unprocessed:
        print("No unprocessed articles found.")
        print("\nAdd new articles to raw/articles/ to continue building your knowledge base.")
        return

    next_article = unprocessed[0]
    print(f"Next article to ingest: {next_article.name}")
    print("\nTell your LLM agent:")
    print(f'  "Please ingest the article at raw/articles/{next_article.name} following the SCHEMA.md workflow."')
    print()


def main() -> None:
    if len(sys.argv) > 1:
        command: str = sys.argv[1]
        if command == "status":
            show_status()
        elif command == "next":
            suggest_next()
        elif command == "list":
            unprocessed = list_raw_articles()
            if unprocessed:
                print("Unprocessed articles:")
                for article in unprocessed:
                    print(f"  {article.name}")
            else:
                print("No unprocessed articles.")
        else:
            print(f"Unknown command: {command}")
            print("Usage: .venv/bin/python src/llm_wiki/ingest.py [status|next|list]")
    else:
        show_status()


if __name__ == "__main__":
    main()
