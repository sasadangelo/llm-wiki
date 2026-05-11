# LLM Wiki Schema - AI Agents Knowledge Base

This document defines the structure, conventions, and workflows for maintaining this wiki about AI Agents.

## Architecture

### 1. Raw Sources (`raw/`)
- `raw/articles/` - Web articles saved as markdown
- `raw/assets/` - Images and other assets downloaded locally
- Raw files are **immutable** - the LLM reads them but never modifies them

### 2. Wiki (`wiki/`)
Directory of markdown files generated and maintained by the LLM:
- `index.md` - Catalog of all pages with links and summaries
- `log.md` - Chronological log of all operations
- `overview.md` - General synthesis of the knowledge base
- `entities/` - Pages for people, organizations, specific tools
- `concepts/` - Pages for key concepts (e.g., "ReAct Pattern", "Tool Use")
- `sources/` - Summaries of processed raw documents
- `analyses/` - Analyses and comparisons generated from queries

### 3. Schema (this file)
Configuration that guides the LLM in maintaining the wiki.

## Conventions

### Naming
- Files: lowercase with hyphens (e.g., `multi-agent-systems.md`)
- Page titles: Title Case
- Internal links: relative to wiki root (e.g., `[Concept](concepts/react-pattern.md)`)

### YAML Frontmatter
Every wiki page must have:
```yaml
---
type: [entity|concept|source|analysis|overview]
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [tag1, tag2]
sources: [list of raw files that contributed]
---
```

### Cross-referencing
- Link freely between related pages
- When mentioning an entity or concept that has a page, link it
- Maintain a "Related" section at the end of each page

## Workflow: Ingest

When a new document is added to `raw/articles/`:

1. **Read**: Read the complete document
2. **Discuss**: Discuss with user the key points and what to emphasize
3. **Summary**: Create a page in `wiki/sources/` with:
   - Content summary
   - Key takeaways
   - Relevant quotes
   - Link to raw file
4. **Update entities**: Create or update pages in `wiki/entities/` for:
   - People mentioned
   - Organizations
   - Specific tools/frameworks
5. **Update concepts**: Create or update pages in `wiki/concepts/` for:
   - Patterns and techniques
   - Architectures
   - Methodologies
6. **Update overview**: Update `wiki/overview.md` if necessary
7. **Update index**: Add new pages to `wiki/index.md`
8. **Log**: Add entry to `wiki/log.md`:
   ```
   ## [YYYY-MM-DD HH:MM] ingest | Document Title
   - Created: [list of created pages]
   - Updated: [list of updated pages]
   - Key insights: [brief note]
   ```

## Workflow: Query

When the user asks a question:

1. **Search**: Consult `wiki/index.md` to find relevant pages
2. **Read**: Read the identified pages
3. **Synthesize**: Generate answer with citations
4. **Format**: Choose appropriate format:
   - Markdown page for in-depth analysis
   - Comparison table
   - Bullet list for brief answers
5. **File (optional)**: If the answer is substantial, save it in `wiki/analyses/`
6. **Log**: Record the query in `wiki/log.md`:
   ```
   ## [YYYY-MM-DD HH:MM] query | User's question
   - Pages consulted: [list]
   - Answer filed: [path if saved]
   ```

## Workflow: Lint

Periodically, check the wiki's health:

1. **Contradictions**: Look for conflicting claims between pages
2. **Stale content**: Identify information superseded by more recent sources
3. **Orphans**: Find pages with no incoming links
4. **Missing pages**: Concepts mentioned but without dedicated page
5. **Missing links**: Missing cross-references
6. **Gaps**: Suggest new sources to look for
7. **Log**: Record the lint pass and actions taken

## Domain: AI Agents

Specific focus of this wiki:

### Relevant Entities
- Researchers and thought leaders
- Organizations (OpenAI, Anthropic, etc.)
- Frameworks and tools (LangChain, AutoGPT, etc.)

### Key Concepts
- Agent architectures (ReAct, ReWOO, Reflexion, etc.)
- Tool use and function calling
- Planning and reasoning
- Multi-agent systems
- Memory systems
- Evaluation and benchmarking

### Source Types
- Research papers
- Technical blog posts
- Framework documentation
- Tutorials and guides
- Case studies

## Operational Notes

- **Language**: English for all wiki content
- **Style**: Technical but accessible, with examples when possible
- **Citations**: Always include references to sources
- **Images**: If present in raw, reference them with relative paths
- **Updates**: Prefer incremental updates to complete rewrites
- **Versioning**: The wiki is a git repo - meaningful commits after each ingest

## Schema Evolution

This schema will evolve over time. When we discover better patterns or new needs:
1. Discuss the changes
2. Update this file
3. Apply changes to existing wiki if necessary
4. Document the change in the log