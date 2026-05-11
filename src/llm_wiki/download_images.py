#!/usr/bin/env python3
"""
Download images from a markdown file and update references.
Useful when you've saved an article with a browser extension.
"""

import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests  # type: ignore


def download_image(img_url: str, base_url: str, assets_dir: Path) -> str | None:
    """Download an image and return the local path."""
    try:
        # Skip if already local
        if img_url.startswith("../assets/"):
            return img_url

        # Skip data URLs
        if img_url.startswith("data:"):
            return None

        # Make absolute URL
        if not img_url.startswith("http"):
            img_url = urljoin(base_url, img_url)

        # Get filename from URL
        parsed = urlparse(img_url)
        filename = Path(parsed.path).name

        # If no filename, generate one
        if not filename or "." not in filename:
            ext = ".jpg"  # default
            filename = f"image_{abs(hash(img_url))}{ext}"

        # Download image with headers
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        }
        response = requests.get(img_url, headers=headers, timeout=10)
        response.raise_for_status()

        # Save to assets
        assets_dir.mkdir(parents=True, exist_ok=True)
        img_path = assets_dir / filename

        with open(img_path, "wb") as f:
            f.write(response.content)

        print(f"  ✓ Downloaded: {filename}")
        return f"../assets/images/{filename}"

    except Exception as e:
        print(f"  ✗ Failed: {img_url} - {e}")
        return None


def process_markdown_file(file_path: Path) -> None:
    """Process a markdown file and download all images."""
    print(f"Processing: {file_path}")

    # Read the file
    content = file_path.read_text(encoding="utf-8")

    # Extract base URL from frontmatter if present
    base_url = ""
    url_match = re.search(r"^url:\s*(.+)$", content, re.MULTILINE)
    if url_match:
        base_url = url_match.group(1).strip()
    else:
        print("Warning: No URL found in frontmatter, using relative paths")

    # Find all images
    img_pattern = r"!\[([^\]]*)\]\(([^)]+)\)"
    images = re.findall(img_pattern, content)

    if not images:
        print("No images found in the file")
        return

    print(f"Found {len(images)} images")

    # Download images
    assets_dir = Path("raw/assets/images")
    downloaded = 0

    def replace_image(match):
        nonlocal downloaded
        alt_text = match.group(1)
        img_url = match.group(2)

        # Skip if already local
        if img_url.startswith("../assets/"):
            return match.group(0)

        # Download image
        local_path = download_image(img_url, base_url, assets_dir)
        if local_path:
            downloaded += 1
            return f"![{alt_text}]({local_path})"
        else:
            # Keep original if download failed
            return match.group(0)

    # Replace image URLs
    new_content = re.sub(img_pattern, replace_image, content)

    # Save updated file
    file_path.write_text(new_content, encoding="utf-8")

    print(f"\n✓ Downloaded {downloaded}/{len(images)} images")
    print(f"✓ Updated: {file_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: .venv/bin/python src/llm_wiki/download_images.py <markdown_file>")
        print("\nExample:")
        print("  .venv/bin/python src/llm_wiki/download_images.py raw/articles/article.md")
        sys.exit(1)

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    if file_path.suffix != ".md":
        print(f"Error: Not a markdown file: {file_path}")
        sys.exit(1)

    process_markdown_file(file_path)


if __name__ == "__main__":
    main()

# Made with Bob
