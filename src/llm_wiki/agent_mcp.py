#!/usr/bin/env python3
"""
LLM Wiki Autonomous Agent - MCP Server
An intelligent agent that can understand natural language requests and autonomously
decide which tools to use to accomplish tasks.
"""

import asyncio
import json
import re
from pathlib import Path
from typing import Any

from agent_ingest import ingest_article as do_ingest
from agent_query import query_wiki as do_query
from ingest import list_raw_articles
from llm_provider import get_llm_provider
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# Initialize MCP server
app = Server("llm-wiki-agent")

# Global LLM instance
llm = None


def get_llm():
    """Get or initialize LLM provider."""
    global llm
    if llm is None:
        llm = get_llm_provider("config.yaml")
    return llm


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools - only one: the agent itself."""
    return [
        Tool(
            name="agent",
            description=(
                "An intelligent agent that understands natural language requests about the wiki. "
                "You can ask it to ingest articles, query the wiki, check status, or perform any "
                "wiki-related task. The agent will autonomously decide which operations to perform. "
                "Examples: 'Ingest all unprocessed articles', 'What is MCP?', 'Show me the wiki status'"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "request": {
                        "type": "string",
                        "description": "Natural language request describing what you want to do with the wiki",
                    },
                },
                "required": ["request"],
            },
        ),
    ]


async def execute_ingest(article_path: str) -> str:
    """Execute article ingestion."""
    try:
        path = Path(article_path)
        if not path.is_absolute() and not str(path).startswith("raw/"):
            path = Path("raw/articles") / path

        if not path.exists():
            return f"❌ Error: Article not found at {path}"

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, do_ingest, path)

        return f"✅ Successfully ingested: {path.name}"
    except Exception as e:
        return f"❌ Error ingesting article: {str(e)}"


async def execute_query(question: str, save: bool = False) -> str:
    """Execute wiki query."""
    try:
        loop = asyncio.get_event_loop()
        answer = await loop.run_in_executor(None, do_query, question, save)
        return answer
    except Exception as e:
        return f"❌ Error querying wiki: {str(e)}"


async def execute_list_unprocessed() -> str:
    """List unprocessed articles."""
    try:
        unprocessed = list_raw_articles()
        if not unprocessed:
            return "✅ All articles have been processed!"

        result = f"📋 Found {len(unprocessed)} unprocessed article(s):\n\n"
        for article in unprocessed:
            result += f"  • {article.name}\n"
        return result
    except Exception as e:
        return f"❌ Error listing articles: {str(e)}"


async def execute_status() -> str:
    """Get wiki status."""
    try:
        raw_count = len(list(Path("raw/articles").glob("*.md"))) if Path("raw/articles").exists() else 0
        wiki_sources = len(list(Path("wiki/sources").glob("*.md"))) if Path("wiki/sources").exists() else 0
        wiki_entities = len(list(Path("wiki/entities").glob("*.md"))) if Path("wiki/entities").exists() else 0
        wiki_concepts = len(list(Path("wiki/concepts").glob("*.md"))) if Path("wiki/concepts").exists() else 0
        wiki_analyses = len(list(Path("wiki/analyses").glob("*.md"))) if Path("wiki/analyses").exists() else 0

        unprocessed = list_raw_articles()

        result = "📊 Wiki Status\n\n"
        result += f"📄 Raw articles: {raw_count}\n"
        result += f"✅ Processed sources: {wiki_sources}\n"
        result += f"🏷️  Entity pages: {wiki_entities}\n"
        result += f"💡 Concept pages: {wiki_concepts}\n"
        result += f"📈 Analysis pages: {wiki_analyses}\n"
        result += f"⏳ Unprocessed: {len(unprocessed)}\n"

        if unprocessed:
            result += f"\n📌 Next to process: {unprocessed[0].name}"

        return result
    except Exception as e:
        return f"❌ Error getting status: {str(e)}"


async def agent_think(request: str) -> str:
    """
    Agent reasoning: analyze the request and decide which actions to take.
    Returns a plan in JSON format.
    """
    llm_instance = get_llm()

    prompt = f"""You are an intelligent agent managing a personal wiki about AI Agents.
Analyze this user request and create an execution plan.

User Request: {request}

Available Operations:
1. INGEST - Ingest an article from raw/articles/ into the wiki
2. QUERY - Answer a question using the wiki content
3. LIST_UNPROCESSED - List articles not yet ingested
4. STATUS - Show wiki statistics
5. MULTIPLE - Execute multiple operations in sequence

Respond with a JSON plan in this format:
{{
  "reasoning": "Brief explanation of what you understood and plan to do",
  "actions": [
    {{"operation": "STATUS"}},
    {{"operation": "INGEST", "article": "filename.md"}},
    {{"operation": "QUERY", "question": "What is...?", "save": false}}
  ]
}}

Examples:
- "Show me the status" -> {{"reasoning": "User wants wiki statistics",
  "actions": [{{"operation": "STATUS"}}]}}
- "Ingest article.md" -> {{"reasoning": "User wants to ingest a specific article",
  "actions": [{{"operation": "INGEST", "article": "article.md"}}]}}
- "What is MCP?" -> {{"reasoning": "User has a question",
  "actions": [{{"operation": "QUERY", "question": "What is MCP?", "save": false}}]}}
- "Process all articles" -> {{"reasoning": "User wants to ingest all unprocessed",
  "actions": [{{"operation": "LIST_UNPROCESSED"}}, {{"operation": "INGEST", "article": "ALL"}}]}}

Return ONLY the JSON, no other text."""

    system_prompt = "You are a planning agent. Analyze requests and create execution plans in JSON format."

    response = llm_instance.generate(prompt, system_prompt)

    # Extract JSON from response
    json_match = re.search(r"\{.*\}", response, re.DOTALL)
    if json_match:
        return json_match.group()
    return response


async def agent_execute(plan_json: str) -> str:
    """Execute the agent's plan."""
    try:
        plan = json.loads(plan_json)
        reasoning = plan.get("reasoning", "")
        actions = plan.get("actions", [])

        result = f"🤔 Agent Reasoning: {reasoning}\n\n"
        result += f"📋 Executing {len(actions)} action(s)...\n\n"

        for i, action in enumerate(actions, 1):
            operation = action.get("operation", "").upper()
            result += f"[{i}/{len(actions)}] {operation}...\n"

            if operation == "STATUS":
                output = await execute_status()
                result += f"{output}\n\n"

            elif operation == "LIST_UNPROCESSED":
                output = await execute_list_unprocessed()
                result += f"{output}\n\n"

            elif operation == "INGEST":
                article = action.get("article", "")
                if article == "ALL":
                    # Ingest all unprocessed
                    unprocessed = list_raw_articles()
                    for art in unprocessed:
                        output = await execute_ingest(art.name)
                        result += f"  {output}\n"
                    result += "\n"
                else:
                    output = await execute_ingest(article)
                    result += f"{output}\n\n"

            elif operation == "QUERY":
                question = action.get("question", "")
                save = action.get("save", False)
                output = await execute_query(question, save)
                result += f"{output}\n\n"

            else:
                result += f"⚠️  Unknown operation: {operation}\n\n"

        result += "✅ Agent execution complete!"
        return result

    except json.JSONDecodeError as e:
        return f"❌ Error parsing plan: {str(e)}\n\nPlan was:\n{plan_json}"
    except Exception as e:
        return f"❌ Error executing plan: {str(e)}"


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls - the agent tool."""
    if name != "agent":
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    request = arguments.get("request", "")
    if not request:
        return [TextContent(type="text", text="Error: No request provided")]

    try:
        # Step 1: Agent thinks and creates a plan
        plan = await agent_think(request)

        # Step 2: Agent executes the plan
        result = await agent_execute(plan)

        return [TextContent(type="text", text=result)]

    except Exception as e:
        return [TextContent(type="text", text=f"Agent error: {str(e)}")]


async def main():
    """Run the MCP agent server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())

# Made with Bob
