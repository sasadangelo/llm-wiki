#!/bin/bash
# Helper script to run HTTP agent server with correct PYTHONPATH

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export PYTHONPATH="${SCRIPT_DIR}/src:${PYTHONPATH}"

uv run python src/llm_wiki/http_agent_server.py "$@"

# Made with Bob
