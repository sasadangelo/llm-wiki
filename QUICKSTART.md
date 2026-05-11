# Quick Start Guide

Get your LLM Wiki up and running in 5 minutes.

## Step 1: Add Your First Source

Save a web article about AI Agents as markdown in `raw/articles/`.

**Easy way**: Use [MarkDownload](https://github.com/deathau/markdownload) browser extension
1. Install the extension for Chrome/Firefox
2. Navigate to an article about AI Agents
3. Click the extension icon
4. Save the markdown file to `raw/articles/`

**Manual way**: Copy/paste article content into a new `.md` file in `raw/articles/`

## Step 2: Ingest the Source

Tell your LLM agent (Claude, ChatGPT, etc.):

```
Please ingest the article at raw/articles/[your-filename].md
following the SCHEMA.md workflow.
```

The LLM will:
- Read the article
- Discuss key points with you
- Create pages in the wiki
- Update the index and log

## Step 3: Explore the Wiki

Open these files to see what was created:
- `wiki/index.md` - See all pages
- `wiki/sources/` - Read the summary
- `wiki/entities/` - See extracted entities
- `wiki/concepts/` - See key concepts
- `wiki/log.md` - See what happened

**Tip**: Use VS Code's markdown preview (Cmd/Ctrl+Shift+V) to view pages with clickable links!

## Step 4: Ask Questions

Now query your knowledge base:

```
What are the main concepts from the article I just ingested?
```

```
How does [concept X] relate to [concept Y]?
```

The LLM will search the wiki and synthesize an answer.

## Step 5: Add More Sources

Repeat steps 1-2 with more articles. Watch your knowledge base grow!

Each new source:
- Adds to existing pages
- Creates new pages
- Updates cross-references
- Flags contradictions

## Optional: Use Helper Tools

Check wiki status:
```bash
.venv/bin/python src/llm_wiki/ingest.py status
```

See next article to process:
```bash
.venv/bin/python src/llm_wiki/ingest.py next
```

## Tips for Success

1. **Start small**: Ingest 1-2 articles first to understand the workflow
2. **Stay involved**: Review what the LLM creates and guide it
3. **Ask questions**: Query the wiki frequently to discover connections
4. **Maintain regularly**: Run lint checks every 10-20 sources
5. **Use git**: Commit after each ingest to track evolution

## Example Session

```
You: Please ingest raw/articles/react-pattern.md following SCHEMA.md

LLM: [Reads article, discusses key points]
     Created wiki/sources/react-pattern.md
     Created wiki/concepts/react-pattern.md
     Updated wiki/entities/yao-shunyu.md
     Updated wiki/index.md
     Updated wiki/log.md

You: What is the ReAct pattern?

LLM: [Searches wiki, reads relevant pages, synthesizes answer]

You: How does ReAct compare to chain-of-thought prompting?

LLM: [Creates comparison, files it in wiki/analyses/]
```

## Next Steps

- Read [README.md](README.md) for full documentation
- Check [SCHEMA.md](SCHEMA.md) to understand the structure
- Browse [wiki/index.md](wiki/index.md) to see your knowledge base
- Add more sources and watch it grow!

## Need Help?

The LLM is your guide. Just ask:
- "How should I structure this source?"
- "What pages should I create for this concept?"
- "Can you suggest related sources to add?"

The wiki evolves with you. Start simple, learn as you go.