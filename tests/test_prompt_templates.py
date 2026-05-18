"""
Test prompt template loading and formatting.
"""

import pytest

from llm_wiki.services.prompts import PromptLoader, format_prompt


def test_prompt_loader_initialization():
    """Test that PromptLoader initializes correctly."""
    loader = PromptLoader()
    assert loader.prompts_dir.exists()
    assert loader.prompts_dir.name == "prompts"


def test_load_extract_metadata_template():
    """Test loading the extract_metadata template."""
    loader = PromptLoader()
    template = loader.load("extract_metadata")
    assert template is not None

    # Test formatting
    formatted = template.format(title="Test Article", author="Test Author", content="Test content here...")
    assert "Test Article" in formatted
    assert "Test Author" in formatted
    assert "Test content here..." in formatted


def test_load_generate_answer_template():
    """Test loading the generate_answer template."""
    loader = PromptLoader()
    template = loader.load("generate_answer")
    assert template is not None

    # Test formatting
    formatted = template.format(question="What is MCP?", context="MCP is a protocol...")
    assert "What is MCP?" in formatted
    assert "MCP is a protocol..." in formatted


def test_load_concept_definition_template():
    """Test loading the generate_concept_definition template."""
    loader = PromptLoader()
    template = loader.load("generate_concept_definition")
    assert template is not None

    # Test formatting
    formatted = template.format(
        concept_name="ReAct Pattern", article_title="Test Article", article_content="Content about ReAct..."
    )
    assert "ReAct Pattern" in formatted
    assert "Test Article" in formatted


def test_load_entity_definition_template():
    """Test loading the generate_entity_definition template."""
    loader = PromptLoader()
    template = loader.load("generate_entity_definition")
    assert template is not None

    # Test formatting
    formatted = template.format(
        entity_name="Anthropic", article_title="Test Article", article_content="Content about Anthropic..."
    )
    assert "Anthropic" in formatted
    assert "Test Article" in formatted


def test_load_search_pages_template():
    """Test loading the search_relevant_pages template."""
    loader = PromptLoader()
    template = loader.load("search_relevant_pages")
    assert template is not None

    # Test formatting
    formatted = template.format(index_content="## Sources\n- article1.md\n- article2.md", question="What is MCP?")
    assert "What is MCP?" in formatted
    assert "article1.md" in formatted


def test_load_system_prompts():
    """Test loading system prompt templates."""
    loader = PromptLoader()

    # Test all system prompts
    system_prompts = [
        "extract_metadata_system",
        "generate_answer_system",
        "generate_concept_definition_system",
        "generate_entity_definition_system",
        "search_relevant_pages_system",
    ]

    for prompt_name in system_prompts:
        template = loader.load(prompt_name)
        assert template is not None
        formatted = template.format()
        assert len(formatted) > 0


def test_format_prompt_helper():
    """Test the format_prompt helper function."""
    formatted = format_prompt("extract_metadata", title="Test", author="Author", content="Content")
    assert "Test" in formatted
    assert "Author" in formatted
    assert "Content" in formatted


def test_template_caching():
    """Test that templates are cached after first load."""
    loader = PromptLoader()

    # Load template twice
    template1 = loader.load("extract_metadata")
    template2 = loader.load("extract_metadata")

    # Should be the same object (cached)
    assert template1 is template2


def test_missing_template_raises_error():
    """Test that loading a non-existent template raises FileNotFoundError."""
    loader = PromptLoader()

    with pytest.raises(FileNotFoundError):
        loader.load("non_existent_template")


def test_clear_cache():
    """Test clearing the template cache."""
    loader = PromptLoader()

    # Load a template
    loader.load("extract_metadata")
    assert len(loader._cache) > 0

    # Clear cache
    loader.clear_cache()
    assert len(loader._cache) == 0


# Made with Bob
