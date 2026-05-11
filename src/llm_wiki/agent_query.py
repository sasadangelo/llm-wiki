#!/usr/bin/env python3
"""
Query agent for LLM Wiki.
Searches the wiki and answers questions using LLM.
"""

import sys
from datetime import datetime
from pathlib import Path

from llm_provider import get_llm_provider


def read_index(wiki_dir: Path) -> str:
    """Read the wiki index."""
    index_path = wiki_dir / "index.md"
    if not index_path.exists():
        return ""
    return index_path.read_text(encoding="utf-8")


def search_relevant_pages(llm, index_content: str, question: str) -> list[str]:
    """Use LLM to identify relevant pages for the question."""
    prompt = f"""Given this wiki index and a user question, identify the most relevant page paths to answer the question.

Wiki Index:
{index_content[:3000]}

User Question: {question}

Return ONLY a JSON array of relevant page paths (relative to wiki/), like:
["sources/article-name.md", "concepts/concept-name.md"]

Return maximum 5 most relevant pages. If no relevant pages, return empty array []."""

    system_prompt = "You are a search assistant. Return only valid JSON arrays of file paths."

    response = llm.generate(prompt, system_prompt)

    # Try to parse JSON array
    import json
    import re

    try:
        # Find JSON array in response
        json_match = re.search(r"\[.*?\]", response, re.DOTALL)
        if json_match:
            paths = json.loads(json_match.group())
            return [p for p in paths if isinstance(p, str)]
        else:
            return []
    except json.JSONDecodeError:
        print(f"Warning: Could not parse LLM response as JSON: {response[:200]}")
        return []


def read_pages(wiki_dir: Path, page_paths: list[str]) -> dict[str, str]:
    """Read content from wiki pages."""
    pages = {}
    for path in page_paths:
        full_path = wiki_dir / path
        if full_path.exists():
            pages[path] = full_path.read_text(encoding="utf-8")
        else:
            print(f"Warning: Page not found: {path}")
    return pages


def generate_answer(llm, question: str, pages: dict[str, str]) -> str:
    """Generate answer using LLM based on wiki pages."""
    # Combine page contents
    context = ""
    for path, content in pages.items():
        context += f"\n\n## From: {path}\n\n{content[:2000]}\n"

    prompt = f"""Answer the following question based on the wiki pages provided.

Question: {question}

Wiki Pages:
{context}

Provide a clear, concise answer with citations to the source pages.
Format citations as [page-name](path/to/page.md)."""

    system_prompt = """You are a knowledgeable assistant answering questions based on a personal wiki.
Always cite your sources. Be accurate and concise."""

    return llm.generate(prompt, system_prompt)


def save_analysis(wiki_dir: Path, question: str, answer: str, pages_used: list[str]) -> Path | None:
    """Optionally save the Q&A as an analysis page."""
    analyses_dir = wiki_dir / "analyses"
    analyses_dir.mkdir(exist_ok=True)

    # Create filename from question
    import re

    safe_name = re.sub(r'[<>:"/\\|?*]', "", question)
    safe_name = re.sub(r"\s+", "-", safe_name).strip("-")[:80]
    filename = f"{safe_name}.md"

    output_path = analyses_dir / filename

    content = f"""---
type: analysis
created: {datetime.now().strftime("%Y-%m-%d")}
question: {question}
sources: {pages_used}
---

# Query: {question}

## Answer

{answer}

## Sources Consulted

{chr(10).join(f"- [{p}](../{p})" for p in pages_used)}

## Related

- [Index](../index.md)
"""

    output_path.write_text(content, encoding="utf-8")
    return output_path


def update_log(wiki_dir: Path, question: str, pages_used: list[str], saved_path: Path | None) -> None:
    """Update wiki log with query operation."""
    log_path = wiki_dir / "log.md"
    content = log_path.read_text(encoding="utf-8")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n## [{timestamp}] query | {question[:60]}...\n\n"
    entry += f"Pages consulted: {len(pages_used)}\n"
    if saved_path:
        entry += f"Answer filed: `{saved_path.relative_to(wiki_dir)}`\n"
    entry += "\n"

    content += entry
    log_path.write_text(content, encoding="utf-8")


def query_wiki(question: str, save: bool = False, config_path: str = "config.yaml") -> str:
    """Main query function."""
    print(f"\n{'=' * 60}")
    print(f"Query: {question}")
    print(f"{'=' * 60}\n")

    # Load LLM provider
    print("Loading LLM provider...")
    llm = get_llm_provider(config_path)
    print("✓ LLM provider loaded\n")

    # Read index
    wiki_dir = Path("wiki")
    print("Reading wiki index...")
    index_content = read_index(wiki_dir)
    if not index_content:
        print("Error: Wiki index not found. Have you ingested any articles?")
        return ""
    print("✓ Index loaded\n")

    # Search for relevant pages
    print("Searching for relevant pages...")
    page_paths = search_relevant_pages(llm, index_content, question)
    print(f"✓ Found {len(page_paths)} relevant pages")
    for path in page_paths:
        print(f"  - {path}")
    print()

    if not page_paths:
        answer = "I couldn't find any relevant pages in the wiki to answer this question."
        print(answer)
        return answer

    # Read pages
    print("Reading wiki pages...")
    pages = read_pages(wiki_dir, page_paths)
    print(f"✓ Read {len(pages)} pages\n")

    # Generate answer
    print("Generating answer with LLM...")
    answer = generate_answer(llm, question, pages)
    print("✓ Answer generated\n")

    # Display answer
    print(f"{'=' * 60}")
    print("ANSWER:")
    print(f"{'=' * 60}\n")
    print(answer)
    print(f"\n{'=' * 60}\n")

    # Save if requested
    saved_path = None
    if save:
        print("Saving analysis...")
        saved_path = save_analysis(wiki_dir, question, answer, page_paths)
        if saved_path:
            print(f"✓ Saved to: {saved_path.relative_to(wiki_dir)}\n")

    # Update log
    print("Updating log...")
    update_log(wiki_dir, question, page_paths, saved_path)
    print("✓ Log updated\n")

    return answer


def main():
    if len(sys.argv) < 2:
        print("Usage: .venv/bin/python src/llm_wiki/agent_query.py <question> [--save]")
        print("\nExamples:")
        print('  .venv/bin/python src/llm_wiki/agent_query.py "What is MCP?"')
        print('  .venv/bin/python src/llm_wiki/agent_query.py "How does MCP work?" --save')
        sys.exit(1)

    question = sys.argv[1]
    save = "--save" in sys.argv

    query_wiki(question, save)


if __name__ == "__main__":
    main()
