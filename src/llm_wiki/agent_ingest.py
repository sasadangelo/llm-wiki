#!/usr/bin/env python3
"""
Automatic ingest agent for LLM Wiki.
Reads articles, extracts entities and concepts using LLM, creates wiki pages.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

from llm_provider import get_llm_provider


def read_article(file_path: Path) -> tuple[dict, str]:
    """Read article and extract frontmatter and content."""
    content = file_path.read_text(encoding="utf-8")

    # Extract frontmatter
    frontmatter = {}
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1].strip()
            for line in fm_text.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    frontmatter[key.strip()] = value.strip()
            content = parts[2].strip()

    return frontmatter, content


def sanitize_filename(text: str) -> str:
    """Convert text to safe filename."""
    safe = re.sub(r'[<>:"/\\|?*]', "", text)
    safe = re.sub(r"\s+", "-", safe).strip("-")
    return safe.lower()[:100]


def extract_metadata(llm, article_content: str, frontmatter: dict) -> dict:
    """Use LLM to extract metadata from article."""
    prompt = f"""Analyze this article and extract key metadata in JSON format.

Article Title: {frontmatter.get("title", "Unknown")}
Author: {frontmatter.get("author", "Unknown")}

Article Content (first 2000 chars):
{article_content[:2000]}

Extract and return ONLY a JSON object with:
- summary: A 2-3 sentence summary of the article
- key_concepts: List of 3-5 main technical concepts discussed
- entities: List of people, organizations, or tools mentioned
- tags: List of 3-5 relevant tags

Return ONLY the JSON, no other text."""

    system_prompt = "You are a technical analyst extracting structured information from articles."

    response = llm.generate(prompt, system_prompt)

    # Try to parse JSON from response
    try:
        # Find JSON in response
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            # Fallback
            return {
                "summary": "Article summary not available",
                "key_concepts": [],
                "entities": [],
                "tags": [],
            }
    except json.JSONDecodeError:
        print(f"Warning: Could not parse LLM response as JSON: {response[:200]}")
        return {
            "summary": "Article summary not available",
            "key_concepts": [],
            "entities": [],
            "tags": [],
        }


def create_source_summary(wiki_dir: Path, article_path: Path, frontmatter: dict, metadata: dict) -> Path:
    """Create source summary page in wiki/sources/."""
    sources_dir = wiki_dir / "sources"
    sources_dir.mkdir(exist_ok=True)

    filename = sanitize_filename(frontmatter.get("title", article_path.stem))
    output_path = sources_dir / f"{filename}.md"

    # Convert to absolute path first, then make relative to cwd
    abs_path = article_path.resolve()
    try:
        rel_path = abs_path.relative_to(Path.cwd())
    except ValueError:
        # If path is not relative to cwd, just use the path as-is
        rel_path = article_path

    content = f"""---
type: source
created: {datetime.now().strftime("%Y-%m-%d")}
updated: {datetime.now().strftime("%Y-%m-%d")}
source_file: {rel_path}
url: {frontmatter.get("url", "")}
author: {frontmatter.get("author", "")}
tags: {metadata.get("tags", [])}
---

# {frontmatter.get("title", "Unknown Title")}

## Summary

{metadata.get("summary", "No summary available")}

## Key Concepts

{
        chr(10).join(
            f"- [{concept}](../concepts/{sanitize_filename(concept)}.md)"
            for concept in metadata.get("key_concepts", [])
        )
    }

## Entities Mentioned

{chr(10).join(f"- [{entity}](../entities/{sanitize_filename(entity)}.md)" for entity in metadata.get("entities", []))}

## Source Information

- **Author**: {frontmatter.get("author", "Unknown")}
- **Published**: {frontmatter.get("published", "Unknown")}
- **Downloaded**: {frontmatter.get("downloaded", "Unknown")}
- **URL**: {frontmatter.get("url", "N/A")}
- **Raw File**: [{article_path.name}](../../{rel_path})

## Related

- [Index](../index.md)
"""

    output_path.write_text(content, encoding="utf-8")
    print(f"  ✓ Created source summary: {output_path.relative_to(wiki_dir)}")
    return output_path


def generate_concept_definition(llm, concept: str, article_content: str, article_title: str) -> str:
    """Use LLM to generate a brief definition of a concept based on article context."""
    prompt = f"""Based on the following article, provide a brief 2-3 sentence explanation of the concept "{concept}".

Article Title: {article_title}

Article Content (first 3000 chars):
{article_content[:3000]}

Write a concise, informative explanation that describes what {concept} is and why it's important in the \
context of AI agents and LLMs. Return ONLY the explanation text, no additional formatting or labels."""

    system_prompt = "You are a technical writer creating concise explanations for a knowledge base about AI agents."

    try:
        definition = llm.generate(prompt, system_prompt).strip()
        # Remove any markdown formatting or labels that might have been added
        definition = re.sub(r"^(Definition:|Overview:|Explanation:)\s*", "", definition, flags=re.IGNORECASE)
        return definition
    except Exception as e:
        print(f"  Warning: Could not generate definition for {concept}: {e}")
        return "*This concept page will be expanded as more sources are added.*"


def build_related_concepts_section(current_concept: str, all_concepts: list[str]) -> str:
    """Build markdown list of related concepts for a concept page."""
    related_links = []
    current_filename = sanitize_filename(current_concept)

    for concept in all_concepts:
        if concept and sanitize_filename(concept) != current_filename:
            related_links.append(f"- [{concept}]({sanitize_filename(concept)}.md)")

    if not related_links:
        return "*To be added*"

    return "\n".join(sorted(set(related_links)))


def create_concept_page(
    wiki_dir: Path,
    concept: str,
    article_title: str,
    source_file: str,
    related_concepts: list[str] | None = None,
    llm=None,
    article_content: str = "",
) -> Path:
    """Create or update concept page."""
    concepts_dir = wiki_dir / "concepts"
    concepts_dir.mkdir(exist_ok=True)

    filename = sanitize_filename(concept)
    output_path = concepts_dir / f"{filename}.md"
    related_concepts_section = build_related_concepts_section(concept, related_concepts or [])

    if output_path.exists():
        # Update existing page
        content = output_path.read_text(encoding="utf-8")
        updated = False

        if source_file not in content:
            sources_match = re.search(
                r"(## Sources\n\n(?:- .+\n)+)",
                content,
                re.MULTILINE,
            )
            if sources_match:
                replacement = sources_match.group(1) + f"- [{article_title}](../sources/{source_file})\n"
                content = content.replace(sources_match.group(1), replacement, 1)
            else:
                content += f"\n- [{article_title}](../sources/{source_file})\n"
            updated = True

        content, related_count = re.subn(
            r"## Related Concepts\n\n(?:\*To be added\*|(?:- .+\n)+)",
            f"## Related Concepts\n\n{related_concepts_section}",
            content,
            count=1,
        )
        if related_count:
            updated = True

        if updated:
            output_path.write_text(content, encoding="utf-8")
            print(f"  ✓ Updated concept: {concept}")
    else:
        # Generate definition using LLM if available
        if llm and article_content:
            definition = generate_concept_definition(llm, concept, article_content, article_title)
        else:
            definition = "*This concept page will be expanded as more sources are added.*"

        # Create new page
        content = f"""---
type: concept
created: {datetime.now().strftime("%Y-%m-%d")}
updated: {datetime.now().strftime("%Y-%m-%d")}
tags: [concept]
---

# {concept}

## Overview

{definition}

## Sources

- [{article_title}](../sources/{source_file})

## Related Concepts

{related_concepts_section}

## Related

- [Index](../index.md)
"""
        output_path.write_text(content, encoding="utf-8")
        print(f"  ✓ Created concept: {concept}")

    return output_path


def generate_entity_definition(llm, entity: str, article_content: str, article_title: str) -> str:
    """Use LLM to generate a brief definition of an entity based on article context."""
    prompt = f"""Based on the following article, provide a brief 2-3 sentence definition of "{entity}".

Article Title: {article_title}

Article Content (first 3000 chars):
{article_content[:3000]}

Write a concise, informative definition that explains what {entity} is and its relevance in the context \
of AI agents and LLMs. Return ONLY the definition text, no additional formatting or labels."""

    system_prompt = "You are a technical writer creating concise definitions for a knowledge base about AI agents."

    try:
        definition = llm.generate(prompt, system_prompt).strip()
        # Remove any markdown formatting or labels that might have been added
        definition = re.sub(r"^(Definition:|Overview:)\s*", "", definition, flags=re.IGNORECASE)
        return definition
    except Exception as e:
        print(f"  Warning: Could not generate definition for {entity}: {e}")
        return "*This entity page will be expanded as more sources are added.*"


def create_entity_page(
    wiki_dir: Path, entity: str, article_title: str, source_file: str, llm=None, article_content: str = ""
) -> Path:
    """Create or update entity page."""
    entities_dir = wiki_dir / "entities"
    entities_dir.mkdir(exist_ok=True)

    filename = sanitize_filename(entity)
    output_path = entities_dir / f"{filename}.md"

    if output_path.exists():
        # Update existing page
        content = output_path.read_text(encoding="utf-8")
        if source_file not in content:
            content += f"\n- [{article_title}](../sources/{source_file})\n"
            output_path.write_text(content, encoding="utf-8")
            print(f"  ✓ Updated entity: {entity}")
    else:
        # Generate definition using LLM if available
        if llm and article_content:
            definition = generate_entity_definition(llm, entity, article_content, article_title)
        else:
            definition = "*This entity page will be expanded as more sources are added.*"

        # Create new page
        content = f"""---
type: entity
created: {datetime.now().strftime("%Y-%m-%d")}
updated: {datetime.now().strftime("%Y-%m-%d")}
tags: [entity]
---

# {entity}

## Overview

{definition}

## Mentioned In

- [{article_title}](../sources/{source_file})

## Related

- [Index](../index.md)
"""
        output_path.write_text(content, encoding="utf-8")
        print(f"  ✓ Created entity: {entity}")

    return output_path


def update_index(wiki_dir: Path, created_pages: list[Path]) -> None:
    """Update wiki index with new pages."""
    index_path = wiki_dir / "index.md"
    content = index_path.read_text(encoding="utf-8")

    # Collect all pages by type
    source_files = sorted((wiki_dir / "sources").glob("*.md"))
    entity_files = sorted((wiki_dir / "entities").glob("*.md"))
    concept_files = sorted((wiki_dir / "concepts").glob("*.md"))
    analysis_files = sorted((wiki_dir / "analyses").glob("*.md"))

    # Build sources section
    sources_section = "### Articles & Blog Posts\n"
    if source_files:
        for f in source_files:
            title = f.stem.replace("-", " ").title()
            sources_section += f"- [{title}](sources/{f.name})\n"
    else:
        sources_section += "*No entries yet*\n"

    # Build entities section
    entities_section = "### Tools & Frameworks\n"
    if entity_files:
        for f in entity_files:
            title = f.stem.replace("-", " ").title()
            entities_section += f"- [{title}](entities/{f.name})\n"
    else:
        entities_section += "*No entries yet*\n"

    # Build concepts section
    concepts_section = "### Core Capabilities\n"
    if concept_files:
        for f in concept_files:
            title = f.stem.replace("-", " ").replace("‑", " ").title()
            concepts_section += f"- [{title}](concepts/{f.name})\n"
    else:
        concepts_section += "*No entries yet*\n"

    # Build analyses section
    analyses_section = "### Deep Dives\n"
    if analysis_files:
        for f in analysis_files:
            title = f.stem.replace("-", " ").title()
            analyses_section += f"- [{title}](analyses/{f.name})\n"
    else:
        analyses_section += "*No entries yet*\n"

    # Replace sections in content
    content = re.sub(
        r"### Articles & Blog Posts\n(?:.*?\n)*?(?=###|\n## |---)",
        sources_section + "\n",
        content,
        flags=re.DOTALL,
    )
    content = re.sub(
        r"### Tools & Frameworks\n(?:.*?\n)*?(?=## Concepts)",
        entities_section + "\n",
        content,
        flags=re.DOTALL,
    )
    content = re.sub(
        r"### Core Capabilities\n(?:.*?\n)*?(?=## Sources)",
        concepts_section + "\n",
        content,
        flags=re.DOTALL,
    )
    content = re.sub(
        r"### Deep Dives\n(?:.*?\n)*?(?=---)",
        analyses_section + "\n",
        content,
        flags=re.DOTALL,
    )

    # Update counts in frontmatter
    content = re.sub(
        r"(updated: )\d{4}-\d{2}-\d{2}",
        f"updated: {datetime.now().strftime('%Y-%m-%d')}",
        content,
    )

    # Update footer stats
    total = 1 + len(source_files) + len(entity_files) + len(concept_files) + len(analysis_files)
    content = re.sub(
        r"\*\*Total Pages\*\*: \d+",
        f"**Total Pages**: {total}",
        content,
    )
    content = re.sub(
        r"\*\*Last Updated\*\*: \d{4}-\d{2}-\d{2}",
        f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d')}",
        content,
    )
    content = re.sub(
        r"\*\*Sources Processed\*\*: \d+",
        f"**Sources Processed**: {len(source_files)}",
        content,
    )

    index_path.write_text(content, encoding="utf-8")
    print("  ✓ Updated index")


def update_log(wiki_dir: Path, article_title: str, created_pages: list[Path]) -> None:
    """Update wiki log with ingest operation."""
    log_path = wiki_dir / "log.md"
    content = log_path.read_text(encoding="utf-8")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n## [{timestamp}] ingest | {article_title}\n\n"
    entry += "Created/Updated:\n"
    for page in created_pages:
        rel_path = page.relative_to(wiki_dir)
        entry += f"- `{rel_path}`\n"
    entry += "\n"

    content += entry
    log_path.write_text(content, encoding="utf-8")
    print("  ✓ Updated log")


def ingest_article(article_path: Path, config_path: str = "config.yaml") -> None:
    """Main ingest function."""
    print(f"\n{'=' * 60}")
    print(f"Ingesting: {article_path.name}")
    print(f"{'=' * 60}\n")

    # Load LLM provider
    print("Loading LLM provider...")
    llm = get_llm_provider(config_path)
    print("✓ LLM provider loaded\n")

    # Read article
    print("Reading article...")
    frontmatter, content = read_article(article_path)
    print(f"✓ Article read ({len(content)} characters)\n")

    # Extract metadata using LLM
    print("Extracting metadata with LLM...")
    metadata = extract_metadata(llm, content, frontmatter)
    print("✓ Metadata extracted")
    print(f"  - Concepts: {len(metadata.get('key_concepts', []))}")
    print(f"  - Entities: {len(metadata.get('entities', []))}")
    print(f"  - Tags: {len(metadata.get('tags', []))}\n")

    # Create wiki pages
    wiki_dir = Path("wiki")
    created_pages = []

    print("Creating wiki pages...")

    # Create source summary
    source_page = create_source_summary(wiki_dir, article_path, frontmatter, metadata)
    created_pages.append(source_page)

    # Create concept pages
    all_concepts = [concept for concept in metadata.get("key_concepts", []) if concept]
    for concept in all_concepts:
        page = create_concept_page(
            wiki_dir,
            concept,
            frontmatter.get("title", "Unknown"),
            source_page.stem,
            related_concepts=all_concepts,
            llm=llm,
            article_content=content,
        )
        created_pages.append(page)

    # Create entity pages
    for entity in metadata.get("entities", []):
        if entity:
            page = create_entity_page(
                wiki_dir,
                entity,
                frontmatter.get("title", "Unknown"),
                source_page.stem,
                llm=llm,
                article_content=content,
            )
            created_pages.append(page)

    print()

    # Update index and log
    print("Updating wiki metadata...")
    update_index(wiki_dir, created_pages)
    update_log(wiki_dir, frontmatter.get("title", article_path.stem), created_pages)

    print(f"\n{'=' * 60}")
    print("✓ Ingest complete!")
    print(f"  Created/updated {len(created_pages)} pages")
    print(f"{'=' * 60}\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: .venv/bin/python src/llm_wiki/agent_ingest.py <article_path>")
        print("\nExample:")
        print("  .venv/bin/python src/llm_wiki/agent_ingest.py raw/articles/article.md")
        sys.exit(1)

    article_path = Path(sys.argv[1])

    if not article_path.exists():
        print(f"Error: File not found: {article_path}")
        sys.exit(1)

    ingest_article(article_path)


if __name__ == "__main__":
    main()
