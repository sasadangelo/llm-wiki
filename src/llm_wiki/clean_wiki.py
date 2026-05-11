#!/usr/bin/env python3
"""
Clean Wiki Tool - Reset the wiki to initial state

This script removes all generated wiki content while preserving:
- Raw sources in raw/articles/
- Raw assets in raw/assets/
- The wiki directory structure
- Configuration files (AGENTS.md, config.yaml, etc.)

Usage:
    uv run src/llm_wiki/clean_wiki.py [--dry-run]
    # or
    python src/llm_wiki/clean_wiki.py [--dry-run]

Options:
    --dry-run    Show what would be deleted without actually deleting
"""

import argparse
from datetime import datetime
from pathlib import Path


def get_wiki_root() -> Path:
    """Get the root directory of the wiki project."""
    # From src/llm_wiki/clean_wiki.py, go up to project root
    return Path(__file__).parent.parent.parent


def create_initial_index(wiki_dir: Path) -> None:
    """Create a fresh index.md file."""
    content = (
        """---
type: index
created: {date}
updated: {date}
---

# Wiki Index - AI Agents Knowledge Base

This is the master catalog of all pages in this wiki. The LLM updates
this file after every ingest operation.

## Overview
- [Overview](overview.md) - General synthesis of the knowledge base

## Entities

### People
*No entries yet*

### Organizations
*No entries yet*

### Tools & Frameworks
*No entries yet*

## Concepts

### Agent Architectures
*No entries yet*

### Core Capabilities
*No entries yet*

## Sources

### Research Papers
*No entries yet*

### Articles & Blog Posts
*No entries yet*

### Documentation
*No entries yet*

## Analyses

### Comparisons
*No entries yet*

### Deep Dives
*No entries yet*

---

**Total Pages**: 3 (index, log, overview)
**Last Updated**: {date}
**Sources Processed**: 0
"""
    ).format(date=datetime.now().strftime("%Y-%m-%d"))

    (wiki_dir / "index.md").write_text(content)


def create_initial_log(wiki_dir: Path) -> None:
    """Create a fresh log.md file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    date = datetime.now().strftime("%Y-%m-%d")
    content = f"""---
type: log
created: {date}
---

# Wiki Operations Log

This is a chronological record of all operations performed on this wiki.
Each entry is prefixed with `## [YYYY-MM-DD HH:MM]` for easy parsing.

---

## [{timestamp}] init | Wiki Reset

- Wiki cleaned and reset to initial state
- All generated content removed
- Ready for fresh ingest operations

**Next steps**:
1. Add source documents to `raw/articles/`
2. Run ingest operation
3. Build knowledge base about AI Agents
"""

    (wiki_dir / "log.md").write_text(content)


def create_initial_overview(wiki_dir: Path) -> None:
    """Create a fresh overview.md file."""
    content = (
        """---
type: overview
created: {date}
updated: {date}
tags: [meta, overview]
sources: []
---

# AI Agents Knowledge Base - Overview

## Purpose

This wiki is a living knowledge base about AI Agents, built using the
LLM Wiki pattern. It accumulates and synthesizes knowledge from various
sources over time, maintaining a structured, interlinked collection of
insights about agent architectures, patterns, tools, and best practices.

## Current State

**Status**: Initialized
**Sources Processed**: 0
**Total Pages**: 3 (index, log, overview)
**Last Updated**: {date}

## Scope

This knowledge base focuses on:

- **Agent Architectures**: Different patterns and approaches to building
  AI agents (ReAct, ReWOO, Reflexion, etc.)
- **Core Capabilities**: Tool use, function calling, planning, reasoning,
  memory systems
- **Multi-Agent Systems**: Coordination, communication, and collaboration
  between agents
- **Frameworks & Tools**: LangChain, AutoGPT, and other agent development
  frameworks
- **Evaluation**: Benchmarks, metrics, and best practices for assessing
  agent performance
- **Research & Practice**: Both academic research and practical implementations

## Key Themes

*This section will be populated as sources are ingested and patterns emerge*

## Evolution

This wiki grows through:
1. **Ingest**: Processing new articles, papers, and documentation
2. **Query**: Answering questions and filing substantial analyses
3. **Lint**: Periodic health checks and maintenance

Each operation is logged in [log.md](log.md), and all pages are
cataloged in [index.md](index.md).

## How to Use

1. **Browse**: Start with [index.md](index.md) to see all available pages
2. **Search**: Look for specific topics in the index categories
3. **Follow Links**: Pages are heavily cross-referenced - follow connections
4. **Check Log**: See [log.md](log.md) for recent additions and updates

## Related

- [Index](index.md) - Full catalog of pages
- [Log](log.md) - Chronological history
- [AGENTS.md](../AGENTS.md) - Wiki structure and conventions
"""
    ).format(date=datetime.now().strftime("%Y-%m-%d"))

    (wiki_dir / "overview.md").write_text(content)


def clean_wiki(dry_run: bool = False) -> None:
    """
    Clean the wiki by removing all generated content.

    Args:
        dry_run: If True, only show what would be deleted
                 without actually deleting
    """
    root = get_wiki_root()
    wiki_dir = root / "wiki"

    if not wiki_dir.exists():
        print("❌ Wiki directory not found!")
        return

    print("🧹 LLM Wiki Cleanup Tool")
    print("=" * 50)

    if dry_run:
        print("🔍 DRY RUN MODE - No files will be deleted")
        print()

    # Directories to clean (remove all content)
    dirs_to_clean = [
        wiki_dir / "entities",
        wiki_dir / "concepts",
        wiki_dir / "sources",
        wiki_dir / "analyses",
    ]

    # Files to remove
    files_to_remove = []

    # Count items
    total_files = 0

    for dir_path in dirs_to_clean:
        if dir_path.exists():
            for item in dir_path.rglob("*"):
                if item.is_file():
                    total_files += 1
                    files_to_remove.append(item)

    print(f"📊 Found {total_files} files to remove")
    print()

    if total_files == 0:
        print("✨ Wiki is already clean!")
        return

    # Show what will be deleted
    print("📁 Files to be removed:")
    for file_path in sorted(files_to_remove):
        rel_path = file_path.relative_to(root)
        print(f"  - {rel_path}")

    print()

    if dry_run:
        print("🔍 DRY RUN - No changes made")
        print()
        print("To actually clean the wiki, run:")
        print("  uv run src/llm_wiki/clean_wiki.py")
        return

    # Ask for confirmation
    prompt = "⚠️  Are you sure you want to delete these files? (yes/no): "
    response = input(prompt)
    if response.lower() not in ["yes", "y"]:
        print("❌ Cleanup cancelled")
        return

    print()
    print("🗑️  Removing files...")

    # Remove all files
    for file_path in files_to_remove:
        try:
            file_path.unlink()
            rel = file_path.relative_to(root)
            print(f"  ✓ Removed {rel}")
        except Exception as e:
            rel = file_path.relative_to(root)
            print(f"  ✗ Error removing {rel}: {e}")

    # Remove empty directories
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            try:
                # Remove directory if empty
                if not any(dir_path.iterdir()):
                    dir_path.rmdir()
                    rel = dir_path.relative_to(root)
                    print(f"  ✓ Removed empty directory {rel}")
            except Exception as e:
                rel = dir_path.relative_to(root)
                print(f"  ✗ Error removing directory {rel}: {e}")

    print()
    print("📝 Resetting wiki to initial state...")

    # Recreate the subdirectories
    for dir_path in dirs_to_clean:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created {dir_path.relative_to(root)}")

    # Reset core wiki files (even if they exist)
    create_initial_index(wiki_dir)
    print("  ✓ Reset wiki/index.md")

    create_initial_log(wiki_dir)
    print("  ✓ Reset wiki/log.md")

    create_initial_overview(wiki_dir)
    print("  ✓ Reset wiki/overview.md")

    print()
    print("✅ Wiki cleaned successfully!")
    print()
    print("📚 Raw sources preserved:")
    print("  - raw/articles/ (source documents)")
    print("  - raw/assets/ (images and media)")
    print()
    print("🚀 Next steps:")
    print("  1. Run ingest to process existing sources")
    print("  2. Or add new sources to raw/articles/")


def main():
    parser = argparse.ArgumentParser(
        description="Clean the LLM Wiki and reset to initial state",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview what would be deleted
  uv run src/llm_wiki/clean_wiki.py --dry-run

  # Actually clean the wiki
  uv run src/llm_wiki/clean_wiki.py
        """,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )

    args = parser.parse_args()

    try:
        clean_wiki(dry_run=args.dry_run)
    except KeyboardInterrupt:
        print("\n\n❌ Cleanup cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
