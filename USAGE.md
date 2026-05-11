# LLM Wiki - Usage Guide

Complete guide for using the LLM Wiki system with automatic agents.

## Setup

### 1. Install Dependencies

```bash
uv sync --dev
```

### 2. Configure LLM Provider

Configure the LLM Provider. Edit `config.yaml` to choose your LLM provider and edit `.env` to add your API keys.

#### Option A: Ollama (Local, Free)

**config.yaml:**
```yaml
llm:
  provider: ollama
  ollama:
    base_url: http://localhost:11434
    model: llama3.2
```

**No .env needed** - Ollama runs locally without API keys.

Make sure Ollama is running:
```bash
ollama serve
ollama pull llama3.2
```

#### Option B: WatsonX (IBM Cloud)

**config.yaml:**
```yaml
llm:
  provider: watsonx
  watsonx:
    url: https://us-south.ml.cloud.ibm.com
    model: meta-llama/llama-3-70b-instruct
```

**.env:**
```bash
WATSONX_API_KEY=your_api_key_here
WATSONX_PROJECT_ID=your_project_id_here
```

## Workflow

### 1. Download Articles

**Option A: Use download tool (for simple sites)**

```bash
uv run src/llm_wiki/download.py article https://example.com/article
```

**Option B: Use browser extension (for Medium, etc.)**

Use Obsidian Web Clipper or MarkDownload to save articles to `raw/articles/`

**Option C: Download images from existing markdown**

```bash
uv run src/llm_wiki/download_images.py raw/articles/article.md
```

### 2. Ingest Articles (Automatic)

Run the ingest agent to process an article:

```bash
uv run src/llm_wiki/agent_ingest.py raw/articles/your-article.md
```

**What happens:**
1. LLM reads the article
2. Extracts key concepts, entities, and metadata
3. Creates source summary in `wiki/sources/`
4. Creates concept pages in `wiki/concepts/`
5. Creates entity pages in `wiki/entities/`
6. Updates `wiki/index.md` and `wiki/log.md`

**Example output:**

```
============================================================
Ingesting: The Model Context Protocol (MCP)_ The Ultimate Guide.md
============================================================

Loading LLM provider...
✓ LLM provider loaded

Reading article...
✓ Article read (15234 characters)

Extracting metadata with LLM...
✓ Metadata extracted
  - Concepts: 5
  - Entities: 3
  - Tags: 4

Creating wiki pages...
  ✓ Created source summary: sources/the-model-context-protocol-mcp-the-ultimate-guide.md
  ✓ Created concept: Model Context Protocol
  ✓ Created concept: AI Integration
  ✓ Created entity: Anthropic
  ✓ Created entity: TONI RAMCHANDANI

Updating wiki metadata...
  ✓ Updated index
  ✓ Updated log

============================================================
✓ Ingest complete!
  Created/updated 7 pages
============================================================
```

### 3. Check Status

```bash
uv run src/llm_wiki/ingest.py status
```

Output:
```
=== LLM Wiki Status ===

Raw articles: 1
Processed sources: 1
Entity pages: 2
Concept pages: 5
Analysis pages: 0

All articles have been processed!
### 5. Clean the Wiki (Reset to Initial State)

If you want to start fresh and remove all generated content:

```bash
# Preview what will be deleted (recommended first)
uv run src/llm_wiki/clean_wiki.py --dry-run

# Actually clean the wiki
uv run src/llm_wiki/clean_wiki.py
```

**What happens:**
1. Shows all files that will be removed
2. Asks for confirmation
3. Removes all generated wiki pages (entities, concepts, sources, analyses)
4. Resets `wiki/index.md`, `wiki/log.md`, and `wiki/overview.md` to initial state
5. Preserves all raw sources in `raw/articles/` and `raw/assets/`

**Example output:**

```
🧹 LLM Wiki Cleanup Tool
==================================================
📊 Found 20 files to remove

📁 Files to be removed:
  - wiki/concepts/...
  - wiki/entities/...
  - wiki/sources/...

⚠️  Are you sure you want to delete these files? (yes/no): yes

🗑️  Removing files...
  ✓ Removed wiki/concepts/...

📝 Resetting wiki to initial state...
  ✓ Reset wiki/index.md
  ✓ Reset wiki/log.md
  ✓ Reset wiki/overview.md

✅ Wiki cleaned successfully!

📚 Raw sources preserved:
  - raw/articles/ (source documents)
  - raw/assets/ (images and media)

🚀 Next steps:
  1. Run ingest to process existing sources
  2. Or add new sources to raw/articles/
```

**When to use:**
- Starting fresh with a clean wiki
- After experimenting with ingestion
- When you want to rebuild the knowledge base from scratch
- Before major restructuring

```

### 4. Browse the Wiki

Open `wiki/index.md` to see all pages, or browse directly:

- `wiki/sources/` - Article summaries
- `wiki/concepts/` - Technical concepts
- `wiki/entities/` - People, organizations, tools
- `wiki/log.md` - Operation history

**Tip**: Use VS Code's markdown preview (Cmd/Ctrl+Shift+V) to view pages with clickable links!

## Query the Wiki

Ask questions to your knowledge base:

```bash
# Basic query
PYTHONPATH=src/llm_wiki uv run src/llm_wiki/agent_query.py "What is MCP?"

# Save the answer as an analysis page
PYTHONPATH=src/llm_wiki uv run src/llm_wiki/agent_query.py "How does MCP work?" --save
```

**What happens:**
1. LLM searches the wiki index for relevant pages
2. Reads the identified pages
3. Generates an answer with citations
4. Optionally saves the Q&A in `wiki/analyses/`
5. Updates `wiki/log.md`

**Example output:**

```
============================================================
Query: What is MCP?
============================================================

Loading LLM provider...
✓ LLM provider loaded

Reading wiki index...
✓ Index loaded

Searching for relevant pages...
✓ Found 3 relevant pages
  - sources/the-model-context-protocol-mcp-the-ultimate-guide.md
  - concepts/model-context-protocol.md
  - entities/anthropic.md

Reading wiki pages...
✓ Read 3 pages

Generating answer with LLM...
✓ Answer generated

============================================================
ANSWER:
============================================================

The Model Context Protocol (MCP) is an open standard developed by
Anthropic that streamlines the integration of AI assistants with
external data sources, tools, and systems...

[Full answer with citations]

============================================================
```

## Advanced Usage

### Batch Ingest Multiple Articles

```bash
for file in raw/articles/*.md; do
  uv run src/llm_wiki/agent_ingest.py "$file"
done
```

### Custom Configuration

Edit `config.yaml` to adjust:
- LLM temperature (creativity vs. consistency)
- Max tokens (response length)
- Model selection

### Troubleshooting

**Problem**: `ModuleNotFoundError: No module named 'llm_provider'`

**Solution**: Run from project root:
```bash
cd /path/to/llm-wiki
PYTHONPATH=src/llm_wiki uv run src/llm_wiki/agent_ingest.py raw/articles/article.md
```

**Problem**: Ollama connection error

**Solution**: Make sure Ollama is running:
```bash
ollama serve
```

**Problem**: LLM returns invalid JSON

**Solution**: The agent has fallback handling, but you can:
- Try a different model
- Adjust temperature in config.yaml
- Check the article isn't too long

## Tips

1. **Start with Ollama** - It's free and runs locally
2. **Process one article at a time** - Review the results
3. **Check the log** - See what was created: `wiki/log.md`
4. **Use git** - Commit after each ingest to track changes
5. **Iterate** - The wiki improves as you add more sources

## Next Steps

1. Ingest your first article
2. Browse the generated wiki pages
3. Add more articles to build the knowledge base
4. Use the query agent (when available) to ask questions

Happy wiki building! 🚀