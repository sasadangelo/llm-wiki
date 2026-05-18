"""
Concept Repository - handles persistence of Concept domain objects.
"""

from pathlib import Path

from llm_wiki.domain.entities import Concept
from llm_wiki.utils import sanitize_filename


class ConceptRepository:
    """Repository for Concept domain objects (technical concepts, patterns)."""

    def __init__(self, concepts_dir: Path):
        """
        Initialize concept repository.

        Args:
            concepts_dir: Directory where concept markdown files are stored
        """
        self.concepts_dir = concepts_dir
        self.concepts_dir.mkdir(parents=True, exist_ok=True)

    def save(self, concept: Concept) -> Path:
        """
        Save a concept to markdown file.

        Args:
            concept: Concept to save

        Returns:
            Path to the saved file
        """
        file_path = self.concepts_dir / f"{concept.filename}.md"

        # Build related concepts section
        related_section = "*To be added*"
        if concept.related_concepts:
            related_links = [f"- [{name}]({sanitize_filename(name)}.md)" for name in concept.related_concepts]
            related_section = "\n".join(sorted(set(related_links)))

        # Build markdown content
        content = f"""---
type: concept
created: {concept.created.strftime("%Y-%m-%d")}
updated: {concept.updated.strftime("%Y-%m-%d")}
tags: [concept]
---

# {concept.name}

## Overview

{concept.definition}

## Sources

{chr(10).join(f"- [{source}](../sources/{source}.md)" for source in concept.sources)}

## Related Concepts

{related_section}

## Related

- [Index](../index.md)
"""

        file_path.write_text(content, encoding="utf-8")
        return file_path

    def find_by_name(self, name: str) -> Concept | None:
        """
        Find a concept by name.

        Args:
            name: Concept name

        Returns:
            Concept if found, None otherwise
        """
        filename = sanitize_filename(name)
        file_path = self.concepts_dir / f"{filename}.md"

        if not file_path.exists():
            return None

        # Parse the markdown file to reconstruct the Concept
        content = file_path.read_text(encoding="utf-8")

        # Extract definition
        import re

        definition_match = re.search(r"## Overview\n\n(.*?)\n\n## Sources", content, re.DOTALL)
        definition = definition_match.group(1).strip() if definition_match else ""

        # Extract sources
        sources_match = re.findall(r"## Sources\n\n(.*?)\n\n## Related Concepts", content, re.DOTALL)
        sources = []
        if sources_match:
            source_links = re.findall(r"- \[(.*?)\]\(../sources/(.*?)\.md\)", sources_match[0])
            sources = [source[1] for source in source_links]

        # Extract related concepts
        related_match = re.findall(r"## Related Concepts\n\n(.*?)\n\n## Related", content, re.DOTALL)
        related_concepts = []
        if related_match and "*To be added*" not in related_match[0]:
            concept_links = re.findall(r"- \[(.*?)\]\((.*?)\.md\)", related_match[0])
            related_concepts = [concept[0] for concept in concept_links]

        # Extract dates
        created_match = re.search(r"created: (\d{4}-\d{2}-\d{2})", content)
        updated_match = re.search(r"updated: (\d{4}-\d{2}-\d{2})", content)

        from datetime import datetime

        created = datetime.strptime(created_match.group(1), "%Y-%m-%d") if created_match else datetime.now()
        updated = datetime.strptime(updated_match.group(1), "%Y-%m-%d") if updated_match else datetime.now()

        return Concept(
            name=name,
            filename=filename,
            definition=definition,
            sources=sources,
            related_concepts=related_concepts,
            created=created,
            updated=updated,
        )

    def exists(self, name: str) -> bool:
        """
        Check if a concept exists.

        Args:
            name: Concept name

        Returns:
            True if concept exists, False otherwise
        """
        filename = sanitize_filename(name)
        file_path = self.concepts_dir / f"{filename}.md"
        return file_path.exists()

    def list_all(self) -> list[str]:
        """
        List all concept filenames.

        Returns:
            List of concept filenames (without .md extension)
        """
        return [f.stem for f in self.concepts_dir.glob("*.md")]


# Made with Bob
