"""
Source Repository - handles persistence of Source domain objects.
"""

from pathlib import Path

from llm_wiki.domain.entities import Source
from llm_wiki.utils import sanitize_filename


class SourceRepository:
    """Repository for Source domain objects (processed articles)."""

    def __init__(self, sources_dir: Path):
        """
        Initialize source repository.

        Args:
            sources_dir: Directory where source markdown files are stored
        """
        self.sources_dir = sources_dir
        self.sources_dir.mkdir(parents=True, exist_ok=True)

    def save(self, source: Source, raw_file_path: Path) -> Path:
        """
        Save a source to markdown file.

        Args:
            source: Source to save
            raw_file_path: Path to the original raw article file

        Returns:
            Path to the saved file
        """
        file_path = self.sources_dir / f"{source.filename}.md"

        # Convert to relative path
        abs_path = raw_file_path.resolve()
        try:
            rel_path = abs_path.relative_to(Path.cwd())
        except ValueError:
            rel_path = raw_file_path

        # Build markdown content
        content = f"""---
type: source
created: {source.created.strftime("%Y-%m-%d")}
updated: {source.created.strftime("%Y-%m-%d")}
source_file: {rel_path}
url: {source.url}
author: {source.author}
tags: {list(source.tags)}
---

# {source.title}

## Summary

{source.summary}

## Key Concepts

{chr(10).join(f"- [{concept}](../concepts/{sanitize_filename(concept)}.md)" for concept in source.key_concepts)}

## Entities Mentioned

{chr(10).join(f"- [{entity}](../entities/{sanitize_filename(entity)}.md)" for entity in source.entities)}

## Source Information

- **Author**: {source.author}
- **URL**: {source.url}
- **Raw File**: [{raw_file_path.name}](../../{rel_path})

## Related

- [Index](../index.md)
"""

        file_path.write_text(content, encoding="utf-8")
        return file_path

    def find_by_filename(self, filename: str) -> Source | None:
        """
        Find a source by filename.

        Args:
            filename: Source filename (without .md extension)

        Returns:
            Source if found, None otherwise
        """
        file_path = self.sources_dir / f"{filename}.md"

        if not file_path.exists():
            return None

        # Parse the markdown file to reconstruct the Source
        content = file_path.read_text(encoding="utf-8")

        import re

        # Extract title
        title_match = re.search(r"^# (.+)$", content, re.MULTILINE)
        title = title_match.group(1) if title_match else "Unknown"

        # Extract summary
        summary_match = re.search(r"## Summary\n\n(.*?)\n\n## Key Concepts", content, re.DOTALL)
        summary = summary_match.group(1).strip() if summary_match else ""

        # Extract key concepts
        concepts_match = re.findall(r"- \[(.*?)\]\(../concepts/.*?\.md\)", content)
        key_concepts = concepts_match if concepts_match else []

        # Extract entities
        entities_match = re.findall(r"- \[(.*?)\]\(../entities/.*?\.md\)", content)
        entities = entities_match if entities_match else []

        # Extract metadata from frontmatter
        url_match = re.search(r"url: (.+)", content)
        url = url_match.group(1).strip() if url_match else ""

        author_match = re.search(r"author: (.+)", content)
        author = author_match.group(1).strip() if author_match else ""

        tags_match = re.search(r"tags: \[(.*?)\]", content)
        tags = []
        if tags_match:
            tags_str = tags_match.group(1)
            tags = [t.strip().strip("'\"") for t in tags_str.split(",") if t.strip()]

        # Extract date
        created_match = re.search(r"created: (\d{4}-\d{2}-\d{2})", content)
        from datetime import datetime

        created = datetime.strptime(created_match.group(1), "%Y-%m-%d") if created_match else datetime.now()

        return Source(
            title=title,
            filename=filename,
            summary=summary,
            key_concepts=key_concepts,
            entities=entities,
            tags=tags,
            url=url,
            author=author,
            created=created,
        )

    def exists(self, filename: str) -> bool:
        """
        Check if a source exists.

        Args:
            filename: Source filename (without .md extension)

        Returns:
            True if source exists, False otherwise
        """
        file_path = self.sources_dir / f"{filename}.md"
        return file_path.exists()

    def list_all(self) -> list[str]:
        """
        List all source filenames.

        Returns:
            List of source filenames (without .md extension)
        """
        return [f.stem for f in self.sources_dir.glob("*.md")]


# Made with Bob
