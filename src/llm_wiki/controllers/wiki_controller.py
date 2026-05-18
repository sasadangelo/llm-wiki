# -----------------------------------------------------------------------------
# Copyright (c) 2025 Salvatore D'Angelo, Code4Projects
# Licensed under the MIT License. See LICENSE.md for details.
# -----------------------------------------------------------------------------
"""
WikiController - HTTP endpoint handler for FastAPI.
Converts between DTOs and domain objects, delegates to WikiService.
"""

import asyncio
import json
import logging
import uuid
from collections.abc import AsyncGenerator
from pathlib import Path

from llm_wiki.dtos import BulkIngestResponse, ChatRequest, ChatResponse, IngestResponse, QueryResponse, StatusResponse
from llm_wiki.services import WikiService
from llm_wiki.utils import extract_json_from_text

logger = logging.getLogger(name=__name__)


class WikiController:
    """Controller that converts between DTOs and domain objects."""

    def __init__(self, wiki_service: WikiService):
        """
        Initialize controller with wiki service.

        Args:
            wiki_service: WikiService instance
        """
        self.service = wiki_service
        self.conversations: dict[str, list[dict[str, str]]] = {}
        logger.info("WikiController initialized")

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """
        Handle chat request.

        Args:
            request: ChatRequest DTO from client

        Returns:
            ChatResponse DTO to client
        """
        conv_id = request.conversation_id or str(uuid.uuid4())

        if conv_id not in self.conversations:
            self.conversations[conv_id] = []

        # Add user message to history
        self.conversations[conv_id].append({"role": "user", "content": request.message})

        # Agent decides what to do
        decision = await self._agent_decide(request.message, self.conversations[conv_id])

        # Execute action based on decision
        final_response, actions_taken = await self._execute_action(decision, request.message)

        # Add assistant message to history
        self.conversations[conv_id].append({"role": "assistant", "content": final_response})

        return ChatResponse(response=final_response, conversation_id=conv_id, actions_taken=actions_taken)

    async def stream_chat(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """
        Handle streaming chat request.

        Args:
            request: ChatRequest DTO

        Yields:
            SSE events with chat progress
        """
        conv_id = request.conversation_id or str(uuid.uuid4())

        if conv_id not in self.conversations:
            self.conversations[conv_id] = []

        self.conversations[conv_id].append({"role": "user", "content": request.message})

        try:
            yield f"data: {json.dumps({'type': 'thinking', 'content': 'Analyzing...'})}\n\n"

            decision = await self._agent_decide(request.message, self.conversations[conv_id])

            yield f"data: {json.dumps({'type': 'decision', 'content': decision['response']})}\n\n"

            # Execute and stream results
            async for event in self._stream_action(decision, request.message):
                yield event

            self.conversations[conv_id].append({"role": "assistant", "content": decision["response"]})

            yield f"data: {json.dumps({'type': 'done', 'conversation_id': conv_id})}\n\n"

        except Exception as e:
            logger.error("Stream chat failed", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    async def get_status(self) -> StatusResponse:
        """
        Get wiki status.

        Returns:
            StatusResponse DTO
        """
        status_data = self.service.get_status()
        return StatusResponse(**status_data)

    async def ingest(self, article_path: str) -> IngestResponse:
        """
        Handle ingest request.

        Args:
            article_path: Path to article file

        Returns:
            IngestResponse DTO
        """
        path = Path(article_path)
        if not path.is_absolute() and not str(path).startswith("raw/"):
            path = Path("raw/articles") / path

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.service.ingest, path)

        return IngestResponse(
            success=result.success,
            article_name=result.article_name,
            pages_created=len(result.created_pages),
            error=result.error,
        )

    async def ingest_all(self) -> BulkIngestResponse:
        """
        Handle bulk ingest request.

        Returns:
            BulkIngestResponse DTO
        """
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.service.ingest_all)

        return BulkIngestResponse(
            success=result["success"],
            total_articles=result["total_articles"],
            successful=result["successful"],
            failed=result["failed"],
            details=result.get("details", []),
            error=result.get("error"),
        )

    async def query(self, question: str, save: bool = False) -> QueryResponse:
        """
        Handle query request.

        Args:
            question: Question to answer
            save: Whether to save answer as analysis

        Returns:
            QueryResponse DTO
        """
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.service.query, question, save)

        return QueryResponse(
            success=result.success,
            question=result.question,
            answer=result.answer,
            sources_used=result.sources_used,
            saved_path=str(result.saved_path) if result.saved_path else None,
            error=result.error,
        )

    async def _agent_decide(self, message: str, history: list) -> dict:
        """
        Agent decides what action to take.

        Args:
            message: User message
            history: Conversation history

        Returns:
            Decision dictionary with intent, action, params, response
        """
        logger.debug("Agent deciding", extra={"message": message[:100]})

        # Build context
        context = "\n".join(f"{msg['role']}: {msg['content']}" for msg in history[-5:])

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

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, self.service.llm.generate, prompt, system_prompt)

        # Parse JSON
        decision = extract_json_from_text(response)
        if decision:
            logger.debug(
                "Decision made",
                extra={"intent": decision.get("intent"), "action": decision.get("action")},
            )
            return decision

        # Fallback
        logger.warning("Could not parse decision, using fallback")
        return {
            "intent": "general",
            "action": "respond",
            "params": {},
            "response": response,
        }

    async def _execute_action(self, decision: dict, message: str) -> tuple[str, list]:
        """
        Execute the decided action.

        Args:
            decision: Decision dictionary
            message: Original user message

        Returns:
            Tuple of (final_response, actions_taken)
        """
        actions_taken = []
        final_response = decision["response"]

        intent = decision["intent"]

        if intent == "query":
            question = decision["params"].get("question", message)
            result = await self.query(question)
            if result.success:
                final_response = result.answer
                actions_taken.append({"action": "query", "params": {"question": question}})
            else:
                final_response = f"Error: {result.error}"

        elif intent == "ingest":
            article = decision["params"].get("article", "")
            result = await self.ingest(article)
            if result.success:
                final_response = f"Successfully ingested {article}"
                actions_taken.append({"action": "ingest", "params": {"article": article}})
            else:
                final_response = f"Error ingesting {article}: {result.error}"

        elif intent == "ingest_all":
            result = await self.ingest_all()
            if result.success:
                final_response = f"Processed {result.successful}/{result.total_articles} articles"
                if result.details:
                    final_response += "\n\nDetails:\n"
                    for detail in result.details:
                        status = "✓" if detail["success"] else "✗"
                        final_response += f"{status} {detail['article']}\n"
                actions_taken.append({"action": "ingest_all", "result": result.dict()})
            else:
                final_response = f"Error during bulk ingest: {result.error}"

        elif intent == "status":
            status = await self.get_status()
            final_response = f"Wiki Status: {status.model_dump_json()}"
            actions_taken.append({"action": "status", "params": {}})

        return final_response, actions_taken

    async def _stream_action(self, decision: dict, message: str) -> AsyncGenerator[str, None]:
        """
        Stream action execution.

        Args:
            decision: Decision dictionary
            message: Original user message

        Yields:
            SSE events
        """
        intent = decision["intent"]

        if intent == "query":
            question = decision["params"].get("question", message)
            result = await self.query(question)
            if result.success:
                yield f"data: {json.dumps({'type': 'result', 'content': result.answer})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'error', 'content': result.error})}\n\n"

        elif intent == "ingest":
            article = decision["params"].get("article", "")
            result = await self.ingest(article)
            if result.success:
                content = f"Successfully ingested {article}"
                yield f"data: {json.dumps({'type': 'result', 'content': content})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'error', 'content': result.error})}\n\n"

        elif intent == "ingest_all":
            yield f"data: {json.dumps({'type': 'progress', 'content': 'Starting bulk ingest...'})}\n\n"
            result = await self.ingest_all()
            if result.success:
                content = f"Processed {result.successful}/{result.total_articles} articles"
                yield f"data: {json.dumps({'type': 'result', 'content': content})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'error', 'content': result.error})}\n\n"

        elif intent == "status":
            status = await self.get_status()
            yield f"data: {json.dumps({'type': 'result', 'content': status.model_dump()})}\n\n"

        else:
            # General response
            yield f"data: {json.dumps({'type': 'result', 'content': decision['response']})}\n\n"
