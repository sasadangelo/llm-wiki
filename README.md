# LLM Wiki - AI Agents Knowledge Base

A living, evolving knowledge base about AI Agents, built using the [LLM Wiki pattern](https://karpathy.ai/llmwiki) by Andrej Karpathy.

## What is this?

This is not a traditional RAG system. Instead of retrieving from raw documents on every query, an LLM incrementally builds and maintains a **persistent wiki** - a structured, interlinked collection of markdown files that synthesizes knowledge from multiple sources over time.

The key difference: **the wiki is a compounding artifact**. Cross-references are already there. Contradictions have been flagged. The synthesis reflects everything you've read. The wiki gets richer with every source you add and every question you ask.

## Structure

```
llm-wiki/
├── raw/                    # Source documents (immutable)
│   ├── articles/          # Web articles in markdown
│   └── assets/            # Images and media files
├── wiki/                   # LLM-maintained knowledge base
│   ├── index.md           # Master catalog of all pages
│   ├── log.md             # Chronological operation log
│   ├── overview.md        # General synthesis
│   ├── entities/          # People, orgs, tools
│   ├── concepts/          # Key concepts and patterns
│   ├── sources/           # Summaries of raw documents
│   └── analyses/          # Generated analyses
├── src/llm_wiki/          # Helper tools
│   └── ingest.py          # Status checker
├── SCHEMA.md              # Wiki structure and workflows
└── README.md              # This file
```

## Quick Start

### 1. Add Your First Source

Save a web article about AI Agents as markdown in `raw/articles/`.

**Easy way**: Use [Obsidian Web Clipper](https://obsidian.md/clipper)

### 2. Ingest the Source

Tell your LLM agent (Claude, ChatGPT, etc.):

```
Please ingest the article at raw/articles/[your-filename].md
following the SCHEMA.md workflow.
```

The LLM will read, discuss, create wiki pages, and update the index.

### 3. Explore the Wiki

- `wiki/index.md` - See all pages
- `wiki/sources/` - Read summaries
- `wiki/entities/` - See extracted entities
- `wiki/concepts/` - See key concepts
- `wiki/log.md` - See what happened

**Pro tip**: Open this folder in [Obsidian](https://obsidian.md) to browse with graph view!

### 4. Ask Questions

Query your knowledge base:

```
What are the main concepts from the article I just ingested?
```

The LLM will search the wiki and synthesize an answer.

### 5. Add More Sources

Repeat steps 1-2. Watch your knowledge base grow!

## Helper Tools

Check wiki status:
```bash
.venv/bin/python src/llm_wiki/ingest.py status
```

See next article to process:
```bash
.venv/bin/python src/llm_wiki/ingest.py next
```

List unprocessed articles:
```bash
.venv/bin/python src/llm_wiki/ingest.py list
```

## Workflows

### Ingest Workflow
1. Add source to `raw/articles/`
2. LLM reads and discusses with you
3. LLM creates summary in `wiki/sources/`
4. LLM updates/creates entity and concept pages
5. LLM updates index and logs the operation

### Query Workflow
1. You ask a question
2. LLM searches index for relevant pages
3. LLM reads pages and synthesizes answer
4. Substantial answers get filed in `wiki/analyses/`
5. Query is logged

### Lint Workflow
1. LLM checks for contradictions
2. Identifies stale content
3. Finds orphaned pages
4. Suggests missing links
5. Recommends new sources to explore

## Domain Focus

This wiki focuses on **AI Agents**:
- Agent architectures (ReAct, ReWOO, Reflexion, etc.)
- Tool use and function calling
- Planning and reasoning
- Multi-agent systems
- Memory systems
- Evaluation and benchmarking

## Key Features

- **Persistent Knowledge**: Information is compiled once and kept current
- **Cross-Referenced**: Pages link to related concepts and entities
- **Evolving**: The wiki improves with every source and query
- **Transparent**: All operations logged in `wiki/log.md`
- **Structured**: Clear organization in `wiki/index.md`
- **Maintainable**: LLM does all the bookkeeping

## Setup

### Install Dependencies

```bash
uv sync --group dev
```

### Initialize Git (if not already done)

```bash
git init
git add -A
git commit -m "Initial LLM Wiki setup"
```

## Tips

1. **Use Obsidian**: Open this folder in Obsidian to browse with graph view
2. **One source at a time**: Ingest sources individually for better control
3. **Stay involved**: Review summaries and guide what to emphasize
4. **File good answers**: Save substantial query responses as wiki pages
5. **Regular linting**: Keep the wiki healthy as it grows
6. **Version control**: Commit after significant changes

## Philosophy

> "The tedious part of maintaining a knowledge base is not the reading or the thinking — it's the bookkeeping. LLMs don't get bored, don't forget to update a cross-reference, and can touch 15 files in one pass. The wiki stays maintained because the cost of maintenance is near zero."
>
> — Andrej Karpathy

The human's job: curate sources, direct analysis, ask good questions, think about meaning.
The LLM's job: everything else.

## Resources

- [Original LLM Wiki concept](https://karpathy.ai/llmwiki) by Andrej Karpathy
- [Obsidian](https://obsidian.md) - Recommended wiki browser
- [Obsidian Web Clipper](https://obsidian.md/clipper) - Save web articles as markdown
- [QUICKSTART.md](QUICKSTART.md) - Get started in 5 minutes

## License

MIT License © 2025 Salvatore D'Angelo
