#!/usr/bin/env python3
"""
Simple Gradio chat interface for LLM Wiki Agent.
"""

import gradio as gr
import requests  # type: ignore[import-untyped]


def chat(message, history):
    """Send message to agent and get response."""
    try:
        # Show initial thinking message
        yield "🤔 Thinking..."

        response = requests.post(
            "http://localhost:8000/chat",
            json={"message": message, "stream": False},
            timeout=120,  # Increased timeout for complex queries
        )
        response.raise_for_status()
        data = response.json()

        # Show the actual response
        yield data["response"]

    except requests.exceptions.ConnectionError:
        yield "❌ Error: Agent server not running. Start it with: .venv/bin/python src/llm_wiki/http_agent_server.py"
    except requests.exceptions.Timeout:
        yield "⏱️ Request timed out. The agent might be processing a complex query. Check the server logs."
    except Exception as e:
        yield f"❌ Error: {str(e)}"


# Create Gradio interface
demo = gr.ChatInterface(
    chat,
    title="🤖 LLM Wiki Assistant",
    description="Ask me anything about the wiki! I can ingest articles, answer questions, and show status.",
    examples=[
        "What is MCP?",
        "Show me the wiki status",
        "List unprocessed articles",
        "Ingest all articles",
    ],
)

if __name__ == "__main__":
    print("🚀 Starting Gradio Chat Interface...")
    print("📡 Make sure the agent server is running:")
    print("   .venv/bin/python src/llm_wiki/http_agent_server.py")
    print()
    demo.launch(server_name="0.0.0.0", server_port=7860)  # nosec B104

# Made with Bob
