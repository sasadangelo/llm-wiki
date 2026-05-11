#!/usr/bin/env python3
"""
LLM Wiki HTTP Agent Server
Exposes the wiki agent via HTTP/REST API with streaming support.
Compatible with A2A (Agent-to-Agent) communication.
"""

import asyncio
import json
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from pathlib import Path

from agent_ingest import ingest_article as do_ingest
from agent_query import query_wiki as do_query
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from ingest import list_raw_articles
from llm_provider import get_llm_provider
from pydantic import BaseModel

# Initialize FastAPI app
app = FastAPI(
    title="LLM Wiki Agent",
    description="Autonomous agent for managing a personal wiki via HTTP API",
    version="1.0.0",
)

# Global LLM instance
llm = None

# Conversation memory (simple in-memory store)
conversations: dict[str, list[dict[str, str]]] = {}


def get_llm():
    """Get or initialize LLM provider."""
    global llm
    if llm is None:
        llm = get_llm_provider("config.yaml")
    return llm


# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    stream: bool = False


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    actions_taken: list[dict]
    timestamp: str


class StatusResponse(BaseModel):
    raw_articles: int
    processed_sources: int
    entities: int
    concepts: int
    analyses: int
    unprocessed: int


# Helper functions
async def execute_ingest(article_path: str) -> dict:
    """Execute article ingestion."""
    try:
        print(f"[INGEST] Starting ingestion of: {article_path}")
        path = Path(article_path)
        if not path.is_absolute() and not str(path).startswith("raw/"):
            path = Path("raw/articles") / path

        if not path.exists():
            print(f"[INGEST] Error: Article not found: {path}")
            return {"success": False, "error": f"Article not found: {path}"}

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, do_ingest, path)

        print(f"[INGEST] Successfully ingested: {path.name}")
        return {"success": True, "article": path.name}
    except Exception as e:
        print(f"[INGEST] Error: {str(e)}")
        return {"success": False, "error": str(e)}


async def execute_ingest_all() -> dict:
    """Execute ingestion of all unprocessed articles."""
    try:
        print("[INGEST_ALL] Starting bulk ingestion...")
        unprocessed = list_raw_articles()
        print(f"[INGEST_ALL] Found {len(unprocessed)} unprocessed articles")

        if not unprocessed:
            print("[INGEST_ALL] No unprocessed articles found")
            return {"success": True, "message": "No unprocessed articles found", "count": 0}

        results = []
        for i, article in enumerate(unprocessed, 1):
            print(f"[INGEST_ALL] Processing {i}/{len(unprocessed)}: {article.name}")
            result = await execute_ingest(str(article))
            results.append({"article": article.name, "success": result["success"]})

        successful = sum(1 for r in results if r["success"])
        print(f"[INGEST_ALL] Completed: {successful}/{len(results)} successful")
        return {
            "success": True,
            "message": f"Processed {successful}/{len(results)} articles",
            "count": successful,
            "details": results,
        }
    except Exception as e:
        print(f"[INGEST_ALL] Error: {str(e)}")
        return {"success": False, "error": str(e)}


async def execute_query(question: str, save: bool = False) -> dict:
    """Execute wiki query."""
    try:
        loop = asyncio.get_event_loop()
        answer = await loop.run_in_executor(None, do_query, question, save)
        return {"success": True, "answer": answer}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_wiki_status() -> StatusResponse:
    """Get current wiki status."""
    raw_count = len(list(Path("raw/articles").glob("*.md"))) if Path("raw/articles").exists() else 0
    sources = len(list(Path("wiki/sources").glob("*.md"))) if Path("wiki/sources").exists() else 0
    entities = len(list(Path("wiki/entities").glob("*.md"))) if Path("wiki/entities").exists() else 0
    concepts = len(list(Path("wiki/concepts").glob("*.md"))) if Path("wiki/concepts").exists() else 0
    analyses = len(list(Path("wiki/analyses").glob("*.md"))) if Path("wiki/analyses").exists() else 0
    unprocessed = list_raw_articles()

    return StatusResponse(
        raw_articles=raw_count,
        processed_sources=sources,
        entities=entities,
        concepts=concepts,
        analyses=analyses,
        unprocessed=len(unprocessed),
    )


async def agent_decide(message: str, conversation_history: list) -> dict:
    """Agent decides what to do based on the message."""
    print(f"[AGENT] Deciding action for message: {message}")
    llm_instance = get_llm()

    # Build context
    context = "\n".join(f"{msg['role']}: {msg['content']}" for msg in conversation_history[-5:])

    prompt = f"""You are an intelligent agent managing a personal wiki about AI Agents.

Conversation history:
{context}

User: {message}

Analyze the user's message and decide what to do. Respond with JSON:
{{
  "intent": "query|ingest|ingest_all|status|list|general",
  "action": "specific action to take",
  "params": {{"key": "value"}},
  "response": "natural language response to user"
}}

Examples:
- "What is MCP?" -> {{"intent": "query", "action": "query_wiki",
  "params": {{"question": "What is MCP?"}},
  "response": "Let me search the wiki for information about MCP..."}}
- "Ingest article.md" -> {{"intent": "ingest", "action": "ingest_article",
  "params": {{"article": "article.md"}},
  "response": "I'll ingest article.md into the wiki..."}}
- "Ingest all articles" -> {{"intent": "ingest_all", "action": "ingest_all_articles",
  "params": {{}},
  "response": "I'll ingest all unprocessed articles into the wiki..."}}
- "Show status" -> {{"intent": "status", "action": "get_status",
  "params": {{}}, "response": "Here's the current wiki status..."}}

Return ONLY valid JSON."""

    system_prompt = "You are a helpful wiki agent. Analyze requests and decide actions."

    response = llm_instance.generate(prompt, system_prompt)
    print(f"[AGENT] LLM response: {response[:200]}...")

    # Parse JSON
    import re

    json_match = re.search(r"\{.*\}", response, re.DOTALL)
    if json_match:
        decision = json.loads(json_match.group())
        print(f"[AGENT] Decision: intent={decision.get('intent')}, action={decision.get('action')}")
        return decision

    # Fallback
    print("[AGENT] Warning: Could not parse JSON, using fallback")
    return {
        "intent": "general",
        "action": "respond",
        "params": {},
        "response": response,
    }


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "LLM Wiki Agent",
        "version": "1.0.0",
        "endpoints": {
            "chat": "POST /chat",
            "status": "GET /status",
            "health": "GET /health",
        },
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/status")
async def status():
    """Get wiki status."""
    return get_wiki_status()


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Main chat endpoint. Accepts messages and returns agent responses.
    Supports streaming via SSE if stream=true.
    """
    # Get or create conversation
    conv_id = request.conversation_id or str(uuid.uuid4())

    if conv_id not in conversations:
        conversations[conv_id] = []

    # Add user message to history
    conversations[conv_id].append({"role": "user", "content": request.message})

    if request.stream:
        # Streaming response
        return StreamingResponse(
            stream_agent_response(request.message, conv_id),
            media_type="text/event-stream",
        )
    else:
        # Non-streaming response
        result = await process_message(request.message, conv_id)
        return result


async def stream_agent_response(message: str, conv_id: str) -> AsyncGenerator[str, None]:
    """Stream agent response as SSE events."""
    try:
        # Yield thinking event
        yield f"data: {json.dumps({'type': 'thinking', 'content': 'Analyzing your request...'})}\n\n"

        # Agent decides
        decision = await agent_decide(message, conversations[conv_id])

        # Yield decision event
        yield f"data: {json.dumps({'type': 'decision', 'content': decision['response']})}\n\n"

        actions_taken = []

        # Execute action
        if decision["intent"] == "query":
            question = decision["params"].get("question", message)
            result = await execute_query(question)
            if result["success"]:
                yield f"data: {json.dumps({'type': 'result', 'content': result['answer']})}\n\n"
                actions_taken.append({"action": "query", "params": {"question": question}})
            else:
                yield f"data: {json.dumps({'type': 'error', 'content': result['error']})}\n\n"

        elif decision["intent"] == "ingest":
            article = decision["params"].get("article", "")
            result = await execute_ingest(article)
            if result["success"]:
                yield f"data: {json.dumps({'type': 'result', 'content': f'Successfully ingested {article}'})}\n\n"
                actions_taken.append({"action": "ingest", "params": {"article": article}})
            else:
                yield f"data: {json.dumps({'type': 'error', 'content': result['error']})}\n\n"

        elif decision["intent"] == "ingest_all":
            yield f"data: {json.dumps({'type': 'progress', 'content': 'Starting to ingest all articles...'})}\n\n"
            result = await execute_ingest_all()
            if result["success"]:
                yield f"data: {json.dumps({'type': 'result', 'content': result['message']})}\n\n"
                actions_taken.append({"action": "ingest_all", "params": {}, "result": result})
            else:
                yield f"data: {json.dumps({'type': 'error', 'content': result['error']})}\n\n"

        elif decision["intent"] == "status":
            status_data = get_wiki_status()
            yield f"data: {json.dumps({'type': 'result', 'content': status_data.model_dump()})}\n\n"
            actions_taken.append({"action": "status", "params": {}})

        else:
            # General response
            yield f"data: {json.dumps({'type': 'result', 'content': decision['response']})}\n\n"

        # Add assistant message to history
        conversations[conv_id].append({"role": "assistant", "content": decision["response"]})

        # Yield done event
        yield f"data: {json.dumps({'type': 'done', 'conversation_id': conv_id, 'actions': actions_taken})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"


async def process_message(message: str, conv_id: str) -> ChatResponse:
    """Process message and return complete response."""
    # Agent decides
    decision = await agent_decide(message, conversations[conv_id])

    actions_taken = []
    final_response = decision["response"]

    # Execute action
    if decision["intent"] == "query":
        question = decision["params"].get("question", message)
        result = await execute_query(question)
        if result["success"]:
            final_response = result["answer"]
            actions_taken.append({"action": "query", "params": {"question": question}})

    elif decision["intent"] == "ingest":
        article = decision["params"].get("article", "")
        result = await execute_ingest(article)
        if result["success"]:
            final_response = f"Successfully ingested {article}"
            actions_taken.append({"action": "ingest", "params": {"article": article}})
        else:
            final_response = f"Error ingesting {article}: {result.get('error', 'Unknown error')}"

    elif decision["intent"] == "ingest_all":
        result = await execute_ingest_all()
        if result["success"]:
            final_response = result["message"]
            if result.get("details"):
                final_response += "\n\nDetails:\n"
                for detail in result["details"]:
                    status = "✓" if detail["success"] else "✗"
                    final_response += f"{status} {detail['article']}\n"
            actions_taken.append({"action": "ingest_all", "params": {}, "result": result})
        else:
            final_response = f"Error during bulk ingest: {result.get('error', 'Unknown error')}"

    elif decision["intent"] == "status":
        status_data = get_wiki_status()
        final_response = f"Wiki Status: {status_data.model_dump_json()}"
        actions_taken.append({"action": "status", "params": {}})

    # Add assistant message to history
    conversations[conv_id].append({"role": "assistant", "content": final_response})

    return ChatResponse(
        response=final_response,
        conversation_id=conv_id,
        actions_taken=actions_taken,
        timestamp=datetime.now().isoformat(),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)  # nosec B104

# Made with Bob
