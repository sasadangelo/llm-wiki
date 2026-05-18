"""
Entity Repository - handles persistence of Entity domain objects.
"""

from pathlib import Path

from llm_wiki.domain.entities import Entity
from llm_wiki.utils import sanitize_filename


class EntityRepository:
    """Repository for Entity domain objects (people, organizations, tools)."""

    def __init__(self, entities_dir: Path):
        """
        Initialize entity repository.

        Args:
            entities_dir: Directory where entity markdown files are stored
        """
        self.entities_dir = entities_dir
        self.entities_dir.mkdir(parents=True, exist_ok=True)

    def save(self, entity: Entity) -> Path:
        """
        Save an entity to markdown file.

        Args:
            entity: Entity to save

        Returns:
            Path to the saved file
        """
        file_path = self.entities_dir / f"{entity.filename}.md"

        # Build markdown content
        content = f"""---
type: entity
created: {entity.created.strftime("%Y-%m-%d")}
updated: {entity.updated.strftime("%Y-%m-%d")}
tags: [entity]
---

# {entity.name}

## Overview

{entity.definition}

## Mentioned In

{chr(10).join(f"- [{source}](../sources/{source}.md)" for source in entity.sources)}

## Related

- [Index](../index.md)
"""

        file_path.write_text(content, encoding="utf-8")
        return file_path

    def find_by_name(self, name: str) -> Entity | None:
        """
        Find an entity by name.

        Args:
            name: Entity name

        Returns:
            Entity if found, None otherwise
        """
        filename = sanitize_filename(name)
        file_path = self.entities_dir / f"{filename}.md"

        if not file_path.exists():
            return None

        # Parse the markdown file to reconstruct the Entity
        content = file_path.read_text(encoding="utf-8")

        # Extract definition (text between ## Overview and ## Mentioned In)
        import re

        definition_match = re.search(r"## Overview\n\n(.*?)\n\n## Mentioned In", content, re.DOTALL)
        definition = definition_match.group(1).strip() if definition_match else ""

        # Extract sources
        sources_match = re.findall(r"- \[(.*?)\]\(../sources/(.*?)\.md\)", content)
        sources = [source[1] for source in sources_match]

        # Extract dates from frontmatter
        created_match = re.search(r"created: (\d{4}-\d{2}-\d{2})", content)
        updated_match = re.search(r"updated: (\d{4}-\d{2}-\d{2})", content)

        from datetime import datetime

        created = datetime.strptime(created_match.group(1), "%Y-%m-%d") if created_match else datetime.now()
        updated = datetime.strptime(updated_match.group(1), "%Y-%m-%d") if updated_match else datetime.now()

        return Entity(
            name=name, filename=filename, definition=definition, sources=sources, created=created, updated=updated
        )

    def exists(self, name: str) -> bool:
        """
        Check if an entity exists.

        Args:
            name: Entity name

        Returns:
            True if entity exists, False otherwise
        """
        filename = sanitize_filename(name)
        file_path = self.entities_dir / f"{filename}.md"
        return file_path.exists()

    def list_all(self) -> list[str]:
        """
        List all entity filenames.

        Returns:
            List of entity filenames (without .md extension)
        """
        return [f.stem for f in self.entities_dir.glob("*.md")]


# Made with Bob
