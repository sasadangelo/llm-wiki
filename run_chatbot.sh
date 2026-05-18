#!/bin/bash
# -----------------------------------------------------------------------------
# Copyright (c) 2025 Salvatore D'Angelo, Code4Projects
# Licensed under the MIT License. See LICENSE.md for details.
# -----------------------------------------------------------------------------
# Script to run the Gradio chatbot interface for LLM Wiki Agent
# -----------------------------------------------------------------------------

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🤖 LLM Wiki - Gradio Chatbot${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo -e "${YELLOW}Please run: uv sync${NC}"
    exit 1
fi

# Check if agent server is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Warning: Agent server not detected on port 8000${NC}"
    echo -e "${YELLOW}The chatbot requires the agent server to be running.${NC}"
    echo -e "${YELLOW}Start it in another terminal with: ./run_server.sh${NC}"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${GREEN}🚀 Starting Gradio chatbot...${NC}"
echo -e "${BLUE}📡 Interface will be available at: http://localhost:7860${NC}"
echo -e "${BLUE}Press Ctrl+C to stop${NC}"
echo ""

# Run chatbot using uv
uv run python src/chatbot/gradio_chat.py
