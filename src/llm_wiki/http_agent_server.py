#!/usr/bin/env python3
"""
LLM Wiki HTTP Agent Server
Exposes the wiki agent via HTTP/REST API with streaming support.
Compatible with A2A (Agent-to-Agent) communication.
Now uses WikiController for all operations.
"""

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

from llm_wiki.controllers.wiki_controller import WikiController
from llm_wiki.core import init_config
from llm_wiki.dtos.requests import ChatRequest
from llm_wiki.services.wiki_service import WikiService

# Initialize configuration at startup
init_config()

# Initialize FastAPI app
app = FastAPI(
    title="LLM Wiki Agent",
    description="Autonomous agent for managing a personal wiki via HTTP API",
    version="2.0.0",
)

# Global instances
wiki_service = None
controller = None


def get_controller() -> WikiController:
    """Get or initialize controller."""
    global wiki_service, controller
    if controller is None:
        wiki_service = WikiService()
        controller = WikiController(wiki_service)
    return controller


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "LLM Wiki Agent",
        "version": "2.0.0",
        "endpoints": {
            "chat": "POST /chat",
            "status": "GET /status",
            "health": "GET /health",
        },
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    from datetime import datetime

    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/status")
async def status():
    """Get wiki status."""
    ctrl = get_controller()
    return await ctrl.get_status()


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Main chat endpoint. Accepts messages and returns agent responses.
    Supports streaming via SSE if stream=true.
    """
    ctrl = get_controller()

    if request.stream:
        # Streaming response
        return StreamingResponse(ctrl.stream_chat(request), media_type="text/event-stream")
    else:
        # Non-streaming response
        return await ctrl.chat(request)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)  # nosec B104

# Made with Bob
