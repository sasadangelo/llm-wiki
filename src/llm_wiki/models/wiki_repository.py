"""
Wiki Repository - handles persistence of wiki-level files (index, log, overview).
"""

import re
from datetime import datetime
from pathlib import Path


class WikiRepository:
    """Repository for wiki-level files (index, log, overview)."""

    def __init__(self, wiki_root: Path):
        """
        Initialize wiki repository.

        Args:
            wiki_root: Root directory of the wiki
        """
        self.wiki_root = wiki_root
        self.index_path = wiki_root / "index.md"
        self.log_path = wiki_root / "log.md"
        self.overview_path = wiki_root / "overview.md"

    def update_index(self, sources: list[str], entities: list[str], concepts: list[str], analyses: list[str]) -> None:
        """
        Update the wiki index with current pages.

        Args:
            sources: List of source filenames
            entities: List of entity filenames
            concepts: List of concept filenames
            analyses: List of analysis filenames
        """
        if not self.index_path.exists():
            return

        content = self.index_path.read_text(encoding="utf-8")

        # Build sections
        sources_section = "### Articles & Blog Posts\n"
        if sources:
            for filename in sorted(sources):
                title = filename.replace("-", " ").title()
                sources_section += f"- [{title}](sources/{filename}.md)\n"
        else:
            sources_section += "*No entries yet*\n"

        entities_section = "### Tools & Frameworks\n"
        if entities:
            for filename in sorted(entities):
                title = filename.replace("-", " ").title()
                entities_section += f"- [{title}](entities/{filename}.md)\n"
        else:
            entities_section += "*No entries yet*\n"

        concepts_section = "### Core Capabilities\n"
        if concepts:
            for filename in sorted(concepts):
                title = filename.replace("-", " ").replace("‑", " ").title()
                concepts_section += f"- [{title}](concepts/{filename}.md)\n"
        else:
            concepts_section += "*No entries yet*\n"

        analyses_section = "### Deep Dives\n"
        if analyses:
            for filename in sorted(analyses):
                title = filename.replace("-", " ").title()
                analyses_section += f"- [{title}](analyses/{filename}.md)\n"
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

        # Update metadata
        content = re.sub(
            r"(updated: )\d{4}-\d{2}-\d{2}",
            f"updated: {datetime.now().strftime('%Y-%m-%d')}",
            content,
        )

        # Update footer stats
        total = 1 + len(sources) + len(entities) + len(concepts) + len(analyses)
        content = re.sub(r"\*\*Total Pages\*\*: \d+", f"**Total Pages**: {total}", content)
        content = re.sub(
            r"\*\*Last Updated\*\*: \d{4}-\d{2}-\d{2}",
            f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d')}",
            content,
        )
        content = re.sub(
            r"\*\*Sources Processed\*\*: \d+",
            f"**Sources Processed**: {len(sources)}",
            content,
        )

        self.index_path.write_text(content, encoding="utf-8")

    def add_log_entry(self, operation: str, title: str, details: list[str]) -> None:
        """
        Add an entry to the wiki log.

        Args:
            operation: Operation type (e.g., "ingest", "query")
            title: Entry title
            details: List of detail lines
        """
        if not self.log_path.exists():
            return

        content = self.log_path.read_text(encoding="utf-8")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"\n## [{timestamp}] {operation} | {title}\n\n"
        for detail in details:
            entry += f"{detail}\n"
        entry += "\n"

        content += entry
        self.log_path.write_text(content, encoding="utf-8")

    def read_index(self) -> str:
        """
        Read the wiki index content.

        Returns:
            Index content as string
        """
        if not self.index_path.exists():
            return ""
        return self.index_path.read_text(encoding="utf-8")


# Made with Bob
