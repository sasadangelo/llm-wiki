#!/usr/bin/env python3
"""
Download web articles and convert them to markdown for the LLM Wiki.
Downloads images locally and updates references in the markdown.
"""

from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests  # type: ignore
from bs4 import BeautifulSoup, Tag
from markdownify import markdownify as md  # type: ignore


def sanitize_filename(title: str) -> str:
    """Convert title to safe filename."""
    # Remove or replace unsafe characters
    safe = re.sub(r'[<>:"/\\|?*]', "", title)
    safe = re.sub(r"\s+", " ", safe).strip()
    # Limit length
    if len(safe) > 100:
        safe = safe[:100]
    return safe + ".md"


def download_image(img_url: str, base_url: str, assets_dir: Path) -> str | None:
    """Download an image and return the local path."""
    try:
        # Make absolute URL
        absolute_url = urljoin(base_url, img_url)

        # Get filename from URL
        parsed = urlparse(absolute_url)
        filename = Path(parsed.path).name

        # If no filename, generate one
        if not filename or "." not in filename:
            ext = ".jpg"  # default
            filename = f"image_{hash(absolute_url)}{ext}"

        # Download image
        response = requests.get(absolute_url, timeout=10)
        response.raise_for_status()

        # Save to assets
        assets_dir.mkdir(parents=True, exist_ok=True)
        img_path = assets_dir / filename

        with open(img_path, "wb") as f:
            f.write(response.content)

        # Return relative path from raw/articles/
        return f"../assets/images/{filename}"

    except Exception as e:
        print(f"Warning: Failed to download image {img_url}: {e}")
        return None


def extract_metadata(soup: BeautifulSoup, url: str) -> dict[str, Any]:
    """Extract metadata from HTML."""
    metadata = {
        "url": url,
        "type": "article",
        "downloaded": datetime.now().strftime("%Y-%m-%d"),
        "title": "",
        "author": "",
        "published": "",
        "tags": [],
    }

    # Extract title
    title_tag = soup.find("title")
    if title_tag:
        metadata["title"] = title_tag.get_text().strip()

    # Try to find h1 if title is empty
    if not metadata["title"]:
        h1 = soup.find("h1")
        if h1:
            metadata["title"] = h1.get_text().strip()

    # Extract author - try common meta tags
    author_selectors = [
        ('meta[name="author"]', "content"),
        ('meta[property="article:author"]', "content"),
        ('meta[name="twitter:creator"]', "content"),
        (".author", "text"),
        (".byline", "text"),
    ]

    for selector, attr in author_selectors:
        elem = soup.select_one(selector)
        if elem:
            if attr == "content":
                content = elem.get("content", "")
                if isinstance(content, str):
                    metadata["author"] = content.strip()
            else:
                metadata["author"] = elem.get_text().strip()
            if metadata["author"]:
                break

    # Extract published date
    date_selectors = [
        ('meta[property="article:published_time"]', "content"),
        ('meta[name="publication_date"]', "content"),
        ("time[datetime]", "datetime"),
        (".published", "text"),
        (".date", "text"),
    ]

    for selector, attr in date_selectors:
        elem = soup.select_one(selector)
        if elem:
            if attr == "content":
                content = elem.get("content", "")
                date_str = content.strip() if isinstance(content, str) else ""
            elif attr == "datetime":
                datetime_val = elem.get("datetime", "")
                date_str = datetime_val.strip() if isinstance(datetime_val, str) else ""
            else:
                date_str = elem.get_text().strip()

            if date_str:
                # Try to parse and format date
                try:
                    # Handle ISO format
                    if "T" in date_str:
                        date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        metadata["published"] = date_obj.strftime("%Y-%m-%d")
                    else:
                        metadata["published"] = date_str
                    break
                except Exception:
                    metadata["published"] = date_str
                    break

    # Extract keywords/tags
    keywords_tag = soup.find("meta", attrs={"name": "keywords"})
    if isinstance(keywords_tag, Tag):
        keywords = keywords_tag.get("content", "")
        if isinstance(keywords, str):
            metadata["tags"] = [k.strip() for k in keywords.split(",") if k.strip()]

    # Try article:tag meta tags
    if not metadata["tags"]:
        tag_metas = soup.find_all("meta", property="article:tag")
        metadata["tags"] = [
            content.strip()
            for tag in tag_metas
            if isinstance(tag, Tag) and (content := tag.get("content")) and isinstance(content, str)
        ]

    return metadata


def download_article(url: str, content_type: str = "article") -> None:
    """Download article from URL and save as markdown."""
    print(f"Downloading: {url}")

    try:
        # Create session with browser-like headers
        session = requests.Session()
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": ("text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"),
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0",
        }

        # For Medium, try to get the page with additional headers
        if "medium.com" in url:
            headers["Referer"] = "https://www.google.com/"
            headers["sec-ch-ua"] = '"Not_A Brand";v="8", "Chromium";v="120"'
            headers["sec-ch-ua-mobile"] = "?0"
            headers["sec-ch-ua-platform"] = '"macOS"'

        response = session.get(url, headers=headers, timeout=30, allow_redirects=True)
        response.raise_for_status()

        # Parse HTML
        html_content = response.text
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract metadata
        metadata = extract_metadata(soup, url)

        # Convert to markdown
        markdown_content = md(html_content, heading_style="ATX")

        # Use metadata title or fallback
        title = metadata["title"] or "article"

        # Create filename
        filename = sanitize_filename(title)
        # Map type to directory (article -> articles)
        dir_name = f"{content_type}s" if not content_type.endswith("s") else content_type
        output_dir = Path(f"raw/{dir_name}")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / filename

        # Download images and update references
        assets_dir = Path("raw/assets/images")
        img_pattern = r"!\[([^\]]*)\]\(([^)]+)\)"

        def replace_image(match):
            alt_text = match.group(1)
            img_url = match.group(2)

            # Skip data URLs
            if img_url.startswith("data:"):
                return match.group(0)

            # Download image
            local_path = download_image(img_url, url, assets_dir)
            if local_path:
                return f"![{alt_text}]({local_path})"
            else:
                # Keep original if download failed
                return match.group(0)

        markdown_content = re.sub(img_pattern, replace_image, markdown_content)

        # Add metadata header with all extracted info
        tags_str = ", ".join(metadata["tags"]) if metadata["tags"] else ""
        header = f"""---
url: {metadata["url"]}
type: {metadata["type"]}
title: {metadata["title"]}
author: {metadata["author"]}
published: {metadata["published"]}
downloaded: {metadata["downloaded"]}
tags: [{tags_str}]
---

"""
        final_content = header + markdown_content

        # Save markdown
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_content)

        print(f"✓ Saved to: {output_path}")
        print(f"✓ Title: {title}")

        # Count downloaded images
        img_count = len(list(assets_dir.glob("*"))) if assets_dir.exists() else 0
        print(f"✓ Images downloaded: {img_count}")

    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) < 3:
        print("Usage: .venv/bin/python src/llm_wiki/download.py <type> <url>")
        print("\nExamples:")
        print("  .venv/bin/python src/llm_wiki/download.py article https://example.com/article")
        print("\nTypes: article")
        sys.exit(1)

    content_type = sys.argv[1]
    url = sys.argv[2]

    download_article(url, content_type)


if __name__ == "__main__":
    main()
