"""
Analysis Repository - handles persistence of Analysis domain objects.
"""

from pathlib import Path

from llm_wiki.domain.entities import Analysis


class AnalysisRepository:
    """Repository for Analysis domain objects (saved query results)."""

    def __init__(self, analyses_dir: Path):
        """
        Initialize analysis repository.

        Args:
            analyses_dir: Directory where analysis markdown files are stored
        """
        self.analyses_dir = analyses_dir
        self.analyses_dir.mkdir(parents=True, exist_ok=True)

    def save(self, analysis: Analysis) -> Path:
        """
        Save an analysis to markdown file.

        Args:
            analysis: Analysis to save

        Returns:
            Path to the saved file
        """
        file_path = self.analyses_dir / f"{analysis.filename}.md"

        # Build markdown content
        content = f"""---
type: analysis
created: {analysis.created.strftime("%Y-%m-%d")}
question: {analysis.question}
sources: {analysis.sources_consulted}
---

# Query: {analysis.question}

## Answer

{analysis.answer}

## Sources Consulted

{chr(10).join(f"- [{p}](../{p})" for p in analysis.sources_consulted)}

## Related

- [Index](../index.md)
"""

        file_path.write_text(content, encoding="utf-8")
        return file_path

    def find_by_filename(self, filename: str) -> Analysis | None:
        """
        Find an analysis by filename.

        Args:
            filename: Analysis filename (without .md extension)

        Returns:
            Analysis if found, None otherwise
        """
        file_path = self.analyses_dir / f"{filename}.md"

        if not file_path.exists():
            return None

        # Parse the markdown file to reconstruct the Analysis
        content = file_path.read_text(encoding="utf-8")

        import re
        from datetime import datetime

        # Extract question from frontmatter
        question_match = re.search(r"question: (.+)", content)
        question = question_match.group(1).strip() if question_match else "Unknown"

        # Extract answer
        answer_match = re.search(r"## Answer\n\n(.*?)\n\n## Sources Consulted", content, re.DOTALL)
        answer = answer_match.group(1).strip() if answer_match else ""

        # Extract sources from frontmatter
        sources_match = re.search(r"sources: \[(.*?)\]", content, re.DOTALL)
        sources_consulted = []
        if sources_match:
            sources_str = sources_match.group(1)
            sources_consulted = [s.strip().strip("'\"") for s in sources_str.split(",") if s.strip()]

        # Extract date
        created_match = re.search(r"created: (\d{4}-\d{2}-\d{2})", content)
        created = datetime.strptime(created_match.group(1), "%Y-%m-%d") if created_match else datetime.now()

        return Analysis(
            question=question,
            filename=filename,
            answer=answer,
            sources_consulted=sources_consulted,
            created=created,
        )

    def exists(self, filename: str) -> bool:
        """
        Check if an analysis exists.

        Args:
            filename: Analysis filename (without .md extension)

        Returns:
            True if analysis exists, False otherwise
        """
        file_path = self.analyses_dir / f"{filename}.md"
        return file_path.exists()

    def list_all(self) -> list[str]:
        """
        List all analysis filenames.

        Returns:
            List of analysis filenames (without .md extension)
        """
        return [f.stem for f in self.analyses_dir.glob("*.md")]


# Made with Bob
