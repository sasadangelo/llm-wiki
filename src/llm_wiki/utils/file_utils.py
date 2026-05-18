"""File operation utilities."""

import re
from pathlib import Path


def sanitize_filename(text: str) -> str:
    """
    Convert text to safe filename.

    Args:
        text: Text to sanitize

    Returns:
        Safe filename string
    """
    safe = re.sub(r'[<>:"/\\|?*]', "", text)
    safe = re.sub(r"\s+", "-", safe).strip("-")
    return safe.lower()[:100]


def read_article(file_path: Path) -> tuple[dict, str]:
    """
    Read article and extract frontmatter and content.

    Args:
        file_path: Path to the article file

    Returns:
        Tuple of (frontmatter dict, content string)
    """
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


# Made with Bob
