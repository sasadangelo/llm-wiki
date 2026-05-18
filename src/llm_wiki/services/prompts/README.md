# Prompt Templates

This directory contains prompt templates for LLM Wiki services.

## Overview

All prompt templates are stored as `.txt` files and use LangChain's `PromptTemplate` for variable substitution. This approach:

- **Separates prompts from code**: Makes prompts easier to read, edit, and version control
- **Enables reusability**: Templates can be shared across services
- **Simplifies testing**: Prompts can be tested independently
- **Improves maintainability**: Changes to prompts don't require code changes

## Template Format

Templates use Python's string formatting with curly braces `{variable_name}` for variable substitution.

Example:
```
Based on the following article, provide a brief definition of "{entity_name}".

Article Title: {article_title}

Article Content:
{article_content}
```

## Available Templates

### Metadata Extraction
- **extract_metadata.txt**: Extracts structured metadata from articles
- **extract_metadata_system.txt**: System prompt for metadata extraction

Variables:
- `title`: Article title
- `author`: Article author
- `content`: Article content (truncated)

### Answer Generation
- **generate_answer.txt**: Generates answers to user questions
- **generate_answer_system.txt**: System prompt for answer generation

Variables:
- `question`: User's question
- `context`: Combined content from relevant wiki pages

### Concept Definitions
- **generate_concept_definition.txt**: Generates definitions for technical concepts
- **generate_concept_definition_system.txt**: System prompt for concept definitions

Variables:
- `concept_name`: Name of the concept
- `article_title`: Source article title
- `article_content`: Source article content (truncated)

### Entity Definitions
- **generate_entity_definition.txt**: Generates definitions for entities (people, organizations, tools)
- **generate_entity_definition_system.txt**: System prompt for entity definitions

Variables:
- `entity_name`: Name of the entity
- `article_title`: Source article title
- `article_content`: Source article content (truncated)

### Page Search
- **search_relevant_pages.txt**: Searches wiki index for relevant pages
- **search_relevant_pages_system.txt**: System prompt for page search

Variables:
- `index_content`: Wiki index content (truncated)
- `question`: User's question

## Usage

### In Service Code

```python
from llm_wiki.services.prompts import format_prompt

# Format a prompt with variables
prompt = format_prompt(
    "extract_metadata",
    title="Article Title",
    author="Author Name",
    content=article_content[:2000]
)

# Load system prompt
system_prompt = format_prompt("extract_metadata_system")

# Use with LLM
response = llm.generate(prompt, system_prompt)
```

### Adding New Templates

1. Create a new `.txt` file in this directory
2. Use `{variable_name}` for variables
3. Optionally create a corresponding `_system.txt` file for the system prompt
4. Import and use with `format_prompt()` in your service

Example:
```python
# In your service
from llm_wiki.services.prompts import format_prompt

prompt = format_prompt("my_new_template", var1="value1", var2="value2")
```

## Best Practices

1. **Keep prompts focused**: Each template should have a single, clear purpose
2. **Use descriptive names**: Template names should clearly indicate their purpose
3. **Document variables**: List all required variables in comments at the top of the template
4. **Test prompts**: Test templates with various inputs before deploying
5. **Version control**: Commit prompt changes with clear descriptions
6. **Separate system prompts**: Keep system prompts in separate `_system.txt` files

## Testing

To test a prompt template:

```python
from llm_wiki.services.prompts import PromptLoader

loader = PromptLoader()
template = loader.load("extract_metadata")
formatted = template.format(
    title="Test Title",
    author="Test Author",
    content="Test content..."
)
print(formatted)
```

## Notes

- Templates are cached after first load for performance
- Missing variables will raise a `KeyError`
- LangChain's `PromptTemplate` is used under the hood
- All templates use UTF-8 encoding