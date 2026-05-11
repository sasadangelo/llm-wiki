#!/usr/bin/env python3
"""
LLM Wiki MCP Server
Provides agent tools for ingesting articles and querying the wiki via MCP protocol.
"""

import asyncio
from pathlib import Path
from typing import Any

from agent_ingest import ingest_article as do_ingest
from agent_query import query_wiki as do_query
from ingest import list_raw_articles
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# Initialize MCP server
app = Server("llm-wiki-agent")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="ingest_article",
            description=(
                "Ingest a raw article into the wiki. Reads the article, extracts metadata using LLM, "
                "creates wiki pages for sources, concepts, and entities, and updates the index."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "article_path": {
                        "type": "string",
                        "description": "Path to the article file relative to raw/articles/ (e.g., 'article-name.md')",
                    },
                },
                "required": ["article_path"],
            },
        ),
        Tool(
            name="query_wiki",
            description=(
                "Query the wiki with a question. Searches relevant pages, generates an answer using LLM, "
                "and optionally saves the analysis."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question to ask about the wiki content",
                    },
                    "save_analysis": {
                        "type": "boolean",
                        "description": "Whether to save the Q&A as an analysis page (default: false)",
                        "default": False,
                    },
                },
                "required": ["question"],
            },
        ),
        Tool(
            name="list_unprocessed",
            description=(
                "List all articles in raw/articles/ that haven't been ingested yet. "
                "Useful for finding what to process next."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_wiki_status",
            description=(
                "Get current status of the wiki including counts of raw articles, "
                "processed sources, entities, concepts, and analyses."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "ingest_article":
            return await handle_ingest(arguments)
        elif name == "query_wiki":
            return await handle_query(arguments)
        elif name == "list_unprocessed":
            return await handle_list_unprocessed(arguments)
        elif name == "get_wiki_status":
            return await handle_status(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def handle_ingest(arguments: dict) -> list[TextContent]:
    """Handle ingest_article tool call."""
    article_path_str = arguments.get("article_path", "")

    # Resolve path - if it's just a filename, assume it's in raw/articles/
    article_path = Path(article_path_str)
    if not article_path.is_absolute() and not str(article_path).startswith("raw/"):
        article_path = Path("raw/articles") / article_path

    if not article_path.exists():
        return [TextContent(type="text", text=f"Error: Article not found at {article_path}")]

    # Run ingest in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, do_ingest, article_path)

    return [
        TextContent(
            type="text",
            text=f"✓ Successfully ingested article: {article_path.name}\n\n"
            f"Created/updated wiki pages for sources, concepts, and entities.\n"
            f"Check wiki/log.md for details.",
        )
    ]


async def handle_query(arguments: dict) -> list[TextContent]:
    """Handle query_wiki tool call."""
    question = arguments.get("question", "")
    save_analysis = arguments.get("save_analysis", False)

    if not question:
        return [TextContent(type="text", text="Error: Question is required")]

    # Run query in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    answer = await loop.run_in_executor(None, do_query, question, save_analysis)

    return [TextContent(type="text", text=answer)]


async def handle_list_unprocessed(arguments: dict) -> list[TextContent]:
    """Handle list_unprocessed tool call."""
    unprocessed = list_raw_articles()

    if not unprocessed:
        return [
            TextContent(
                type="text", text="No unprocessed articles found.\n\nAll articles in raw/articles/ have been ingested."
            )
        ]

    result = f"Found {len(unprocessed)} unprocessed article(s):\n\n"
    for article in unprocessed:
        result += f"- {article.name}\n"

    result += "\nTo ingest the next article, use:\n"
    result += f'  ingest_article(article_path="{unprocessed[0].name}")'

    return [TextContent(type="text", text=result)]


async def handle_status(arguments: dict) -> list[TextContent]:
    """Handle get_wiki_status tool call."""
    # Count files in each directory
    raw_count = len(list(Path("raw/articles").glob("*.md"))) if Path("raw/articles").exists() else 0
    wiki_sources = len(list(Path("wiki/sources").glob("*.md"))) if Path("wiki/sources").exists() else 0
    wiki_entities = len(list(Path("wiki/entities").glob("*.md"))) if Path("wiki/entities").exists() else 0
    wiki_concepts = len(list(Path("wiki/concepts").glob("*.md"))) if Path("wiki/concepts").exists() else 0
    wiki_analyses = len(list(Path("wiki/analyses").glob("*.md"))) if Path("wiki/analyses").exists() else 0

    unprocessed = list_raw_articles()

    result = "=== LLM Wiki Status ===\n\n"
    result += f"📄 Raw articles: {raw_count}\n"
    result += f"✓ Processed sources: {wiki_sources}\n"
    result += f"🏷️  Entity pages: {wiki_entities}\n"
    result += f"💡 Concept pages: {wiki_concepts}\n"
    result += f"📊 Analysis pages: {wiki_analyses}\n"
    result += f"⏳ Unprocessed: {len(unprocessed)}\n\n"

    if unprocessed:
        result += f"Next to process: {unprocessed[0].name}"
    else:
        result += "All articles processed! ✨"

    return [TextContent(type="text", text=result)]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())

# Made with Bob
