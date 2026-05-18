"""
Prompt templates for LLM Wiki services.

Uses LangChain's PromptTemplate for loading and rendering prompts from files.
"""

from pathlib import Path

from langchain_core.prompts import PromptTemplate


class PromptLoader:
    """
    Loads and manages prompt templates from files.

    Uses LangChain's PromptTemplate for variable substitution.
    """

    def __init__(self, prompts_dir: Path | None = None):
        """
        Initialize prompt loader.

        Args:
            prompts_dir: Directory containing prompt template files.
                        Defaults to the directory containing this file.
        """
        if prompts_dir is None:
            prompts_dir = Path(__file__).parent
        self.prompts_dir = Path(prompts_dir)
        self._cache: dict[str, PromptTemplate] = {}

    def load(self, template_name: str) -> PromptTemplate:
        """
        Load a prompt template from file.

        Args:
            template_name: Name of the template file (without .txt extension)

        Returns:
            LangChain PromptTemplate object

        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        if template_name in self._cache:
            return self._cache[template_name]

        template_path = self.prompts_dir / f"{template_name}.txt"

        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        template_content = template_path.read_text(encoding="utf-8")

        # Create LangChain PromptTemplate
        prompt_template = PromptTemplate.from_template(template_content)
        self._cache[template_name] = prompt_template

        return prompt_template

    def format(self, template_name: str, **variables) -> str:
        """
        Load and format a prompt template with variables.

        Args:
            template_name: Name of the template file (without .txt extension)
            **variables: Variables to substitute in the template

        Returns:
            Formatted prompt string

        Raises:
            FileNotFoundError: If template file doesn't exist
            KeyError: If required template variable is missing
        """
        template = self.load(template_name)
        return template.format(**variables)

    def clear_cache(self) -> None:
        """Clear the template cache."""
        self._cache.clear()


# Global prompt loader instance
_prompt_loader = PromptLoader()


def load_prompt(template_name: str) -> PromptTemplate:
    """
    Load a prompt template using the global loader.

    Args:
        template_name: Name of the template file (without .txt extension)

    Returns:
        LangChain PromptTemplate object
    """
    return _prompt_loader.load(template_name)


def format_prompt(template_name: str, **variables) -> str:
    """
    Format a prompt template with variables using the global loader.

    Args:
        template_name: Name of the template file (without .txt extension)
        **variables: Variables to substitute in the template

    Returns:
        Formatted prompt string
    """
    return _prompt_loader.format(template_name, **variables)


# Made with Bob
