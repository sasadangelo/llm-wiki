"""Value objects - immutable data structures."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Frontmatter:
    """Article frontmatter - immutable metadata from article header."""

    title: str
    author: str = ""
    url: str = ""
    published: str = ""
    downloaded: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Frontmatter":
        """
        Create Frontmatter from dictionary.

        Args:
            data: Dictionary with frontmatter data

        Returns:
            Frontmatter instance
        """
        return cls(
            title=data.get("title", "Unknown"),
            author=data.get("author", ""),
            url=data.get("url", ""),
            published=data.get("published", ""),
            downloaded=data.get("downloaded", ""),
        )


@dataclass(frozen=True)
class Metadata:
    """Extracted article metadata - immutable analysis results."""

    summary: str
    key_concepts: tuple[str, ...]
    entities: tuple[str, ...]
    tags: tuple[str, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Metadata":
        """
        Create Metadata from dictionary.

        Args:
            data: Dictionary with metadata

        Returns:
            Metadata instance
        """
        return cls(
            summary=data.get("summary", ""),
            key_concepts=tuple(data.get("key_concepts", [])),
            entities=tuple(data.get("entities", [])),
            tags=tuple(data.get("tags", [])),
        )
