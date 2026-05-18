#!/usr/bin/env python3
"""
Query agent for LLM Wiki.
Now uses WikiService for all operations.
"""

import sys

from llm_wiki.core import init_config
from llm_wiki.services import QueryResult, WikiService


def query_wiki(question: str, save: bool = False) -> str:
    """
    Main query function using WikiService.

    Args:
        question: Question to answer
        save: Whether to save answer as analysis

    Returns:
        Answer string
    """
    print(f"\n{'=' * 60}")
    print(f"Query: {question}")
    print(f"{'=' * 60}\n")

    # Initialize service (automatically loads config and creates LLM client)
    print("Initializing wiki service...")
    service: WikiService = WikiService()
    print("✓ Wiki service initialized\n")

    # Query wiki
    print("Searching wiki...")
    result: QueryResult = service.query(question, save)

    if result.success:
        print(f"✓ Found {len(result.sources_used)} relevant pages\n")
        print(f"{'=' * 60}")
        print("ANSWER:")
        print(f"{'=' * 60}\n")
        print(result.answer)
        print(f"\n{'=' * 60}\n")

        if result.saved_path:
            print(f"✓ Answer saved to: {result.saved_path}\n")

        return result.answer
    else:
        print(f"\n✗ Query failed: {result.error}\n")
        return ""


def main() -> None:
    # Initialize configuration at startup
    init_config()

    if len(sys.argv) < 2:
        print("Usage: .venv/bin/python src/llm_wiki/doc_query.py <question> [--save]")
        print("\nExamples:")
        print('  .venv/bin/python src/llm_wiki/doc_query.py "What is MCP?"')
        print('  .venv/bin/python src/llm_wiki/doc_query.py "How does MCP work?" --save')
        sys.exit(1)

    question = sys.argv[1]
    save = "--save" in sys.argv

    query_wiki(question, save)


if __name__ == "__main__":
    main()
