#!/usr/bin/env python3
"""
Simple helper script for ingesting sources into the LLM Wiki.
This is optional - you can also just tell your LLM agent to ingest files directly.
"""

import sys
from pathlib import Path


def list_raw_articles():
    """List all articles in raw/articles/ that haven't been ingested yet."""
    raw_dir = Path("raw/articles")
    wiki_sources = Path("wiki/sources")

    if not raw_dir.exists():
        print("Error: raw/articles/ directory not found")
        return []

    # Get all markdown files in raw/articles
    raw_files = list(raw_dir.glob("*.md"))

    # Get all source summaries in wiki/sources
    processed = set()
    if wiki_sources.exists():
        for source_file in wiki_sources.glob("*.md"):
            # Read the file to find the raw source reference
            content = source_file.read_text()
            # Simple heuristic: look for raw/articles/ references
            for line in content.split("\n"):
                if "raw/articles/" in line:
                    # Extract filename
                    parts = line.split("raw/articles/")
                    if len(parts) > 1:
                        filename = parts[1].split(")")[0].split("]")[0].strip()
                        processed.add(filename)

    # Find unprocessed files
    unprocessed = []
    for raw_file in raw_files:
        if raw_file.name not in processed:
            unprocessed.append(raw_file)

    return unprocessed


def show_status():
    """Show the current status of the wiki."""
    print("=== LLM Wiki Status ===\n")

    # Count files in each directory
    raw_count = len(list(Path("raw/articles").glob("*.md"))) if Path("raw/articles").exists() else 0
    wiki_sources = len(list(Path("wiki/sources").glob("*.md"))) if Path("wiki/sources").exists() else 0
    wiki_entities = len(list(Path("wiki/entities").glob("*.md"))) if Path("wiki/entities").exists() else 0
    wiki_concepts = len(list(Path("wiki/concepts").glob("*.md"))) if Path("wiki/concepts").exists() else 0
    wiki_analyses = len(list(Path("wiki/analyses").glob("*.md"))) if Path("wiki/analyses").exists() else 0

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


def suggest_next():
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


def main():
    if len(sys.argv) > 1:
        command = sys.argv[1]
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

# Made with Bob
