#!/bin/bash
# Helper script to run clean_wiki with correct PYTHONPATH

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export PYTHONPATH="${SCRIPT_DIR}/src:${PYTHONPATH}"

uv run python src/llm_wiki/clean_wiki.py "$@"
