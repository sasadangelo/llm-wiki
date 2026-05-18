"""
WikiService - Facade for wiki operations.
Delegates to specialized services for ingest, query, and wiki management.
"""

import logging
from pathlib import Path

from llm_wiki.clients import LLMClient, LLMClientFactory
from llm_wiki.core import get_config
from llm_wiki.core.config import AppConfig
from llm_wiki.domain import Frontmatter, Metadata, Wiki
from llm_wiki.exceptions import IngestError
from llm_wiki.ingest import list_raw_articles
from llm_wiki.models import AnalysisRepository, ConceptRepository, EntityRepository, SourceRepository, WikiRepository
from llm_wiki.services.analysis_service import AnalysisService
from llm_wiki.services.concept_service import ConceptService
from llm_wiki.services.entity_service import EntityService
from llm_wiki.services.index_service import IndexService
from llm_wiki.services.log_service import LogService
from llm_wiki.services.prompts import format_prompt
from llm_wiki.services.source_service import SourceService
from llm_wiki.utils import extract_json_from_text, read_article

logger = logging.getLogger(name=__name__)


class IngestResult:
    """Result of ingest operation (domain object, not DTO)."""

    def __init__(
        self,
        success: bool,
        article_name: str,
        created_pages: list[Path] | None = None,
        error: str | None = None,
    ) -> None:
        self.success = success
        self.article_name = article_name
        self.created_pages = created_pages or []
        self.error = error


class QueryResult:
    """Result of query operation (domain object, not DTO)."""

    def __init__(
        self,
        success: bool,
        question: str,
        answer: str,
        sources_used: list[str] | None = None,
        saved_path: Path | None = None,
        error: str | None = None,
    ) -> None:
        self.success = success
        self.question = question
        self.answer = answer
        self.sources_used = sources_used or []
        self.saved_path = saved_path
        self.error = error


class WikiService:
    """
    Facade for wiki operations.

    Delegates operations to specialized services:
    - SourceService: Creates source summaries
    - EntityService: Manages entities (people, organizations, tools)
    - ConceptService: Manages concepts (patterns, techniques)
    - AnalysisService: Creates analysis pages from query results
    - QueryService: Handles wiki search and answer generation
    - IndexService: Updates wiki index
    - LogService: Manages operation logs
    """

    def __init__(self) -> None:
        """
        Initialize wiki service facade.

        Automatically loads configuration and creates LLM client using factory.
        Initializes all repositories and specialized services.

        Raises:
            RuntimeError: If configuration not initialized
        """
        # Get wiki root from configuration
        config: AppConfig = get_config()
        wiki_root: Path = Path(config.wiki.wiki_dir)

        # Create LLM client using factory
        self.llm: LLMClient = LLMClientFactory.create_client()

        # Initialize wiki
        self.wiki = Wiki(root_path=wiki_root)
        self.wiki.ensure_directories()

        # Initialize repositories
        self.entity_repo = EntityRepository(entities_dir=self.wiki.entities_dir)
        self.concept_repo = ConceptRepository(concepts_dir=self.wiki.concepts_dir)
        self.source_repo = SourceRepository(sources_dir=self.wiki.sources_dir)
        self.analysis_repo = AnalysisRepository(analyses_dir=self.wiki.analyses_dir)
        self.wiki_repo = WikiRepository(wiki_root=self.wiki.root_path)

        # Initialize specialized services
        self.source_service = SourceService(source_repo=self.source_repo)
        self.entity_service = EntityService(entity_repo=self.entity_repo)
        self.concept_service = ConceptService(concept_repo=self.concept_repo)
        self.analysis_service = AnalysisService(analysis_repo=self.analysis_repo)
        self.index_service = IndexService(
            wiki_repo=self.wiki_repo,
            source_repo=self.source_repo,
            entity_repo=self.entity_repo,
            concept_repo=self.concept_repo,
            analyses_dir=self.wiki.analyses_dir,
            index_path=self.wiki.index_path,
        )
        self.log_service = LogService(wiki_repo=self.wiki_repo, wiki_root=self.wiki.root_path)

        logger.info(
            msg="WikiService initialized", extra={"wiki_root": str(wiki_root), "llm_provider": config.llm.provider}
        )

    def ingest(self, article_path: Path) -> IngestResult:
        """
        Ingest an article into the wiki.

        Delegates to specialized services:
        - Reads article and extracts metadata
        - Creates source summary via SourceService
        - Creates/updates concepts via ConceptService
        - Creates/updates entities via EntityService
        - Updates index via IndexService
        - Logs operation via LogService

        Args:
            article_path: Path to the article file

        Returns:
            IngestResult with created pages and metadata

        Raises:
            IngestError: If article processing fails
        """
        logger.info(msg="Starting ingest", extra={"article": article_path.name})

        try:
            # Read article
            frontmatter_dict, content = read_article(file_path=article_path)
            frontmatter: Frontmatter = Frontmatter.from_dict(data=frontmatter_dict)
            logger.debug(msg="Article read", extra={"chars": len(content)})

            # Extract metadata using LLM
            metadata: Metadata = self._extract_metadata(article_content=content, frontmatter=frontmatter)
            logger.debug(
                msg="Metadata extracted",
                extra={
                    "concepts": len(metadata.key_concepts),
                    "entities": len(metadata.entities),
                },
            )

            # Create source summary
            source_page: Path = self.source_service.create(
                article_path=article_path, frontmatter=frontmatter, metadata=metadata
            )

            # Create all wiki pages
            created_pages = [source_page]
            created_pages.extend(
                self._create_concept_pages(
                    concepts=list(metadata.key_concepts),
                    article_title=frontmatter.title,
                    source_file=source_page.stem,
                    article_content=content,
                )
            )
            created_pages.extend(
                self._create_entity_pages(
                    entities=metadata.entities,
                    article_title=frontmatter.title,
                    source_file=source_page.stem,
                    article_content=content,
                )
            )

            # Update index and log
            self.index_service.update()
            self.log_service.add_ingest_entry(article_title=frontmatter.title, created_pages=created_pages)

            logger.info(msg="Ingest complete", extra={"pages_created": len(created_pages)})

            return IngestResult(success=True, article_name=article_path.name, created_pages=created_pages)

        except (FileNotFoundError, ValueError, IngestError) as e:
            logger.error(msg="Ingest failed", extra={"error": str(e)}, exc_info=True)
            return IngestResult(success=False, article_name=article_path.name, error=str(e))
        except Exception as e:
            logger.critical(msg="Unexpected ingest error", extra={"error": str(e)}, exc_info=True)
            return IngestResult(success=False, article_name=article_path.name, error=f"Unexpected error: {str(e)}")

    def query(self, question: str, save: bool = False) -> QueryResult:
        """
        Query the wiki and return an answer.

        Delegates to QueryService for search and answer generation:
        - Reads wiki index
        - Uses LLM to find relevant pages
        - Reads page contents
        - Generates answer using LLM
        - Optionally saves as analysis via AnalysisService
        - Logs operation via LogService

        Args:
            question: The question to answer
            save: Whether to save the answer as an analysis

        Returns:
            QueryResult with answer and sources used
        """
        logger.info(msg="Starting query", extra={"question": question[:100]})

        try:
            # Read index via IndexService
            index_content: str = self.index_service.read_index()

            # Search for relevant pages using IndexService
            page_paths: list[str] = self.index_service.search_relevant_pages(index_content, question)
            logger.debug(msg="Pages found", extra={"count": len(page_paths)})

            if not page_paths:
                return QueryResult(
                    success=True,
                    question=question,
                    answer="No relevant pages found in the wiki.",
                    sources_used=[],
                )

            # Read pages
            pages: dict[str, str] = self._read_pages(page_paths)

            # Generate answer using LLM
            answer: str = self._generate_answer(question, pages)

            # Save if requested via AnalysisService
            saved_path: Path | None = (
                self.analysis_service.create(question=question, answer=answer, sources_consulted=page_paths)
                if save
                else None
            )

            # Update log via LogService
            self.log_service.add_query_entry(question=question, pages_used=page_paths, saved_path=saved_path)

            logger.info(msg="Query complete", extra={"sources_used": len(page_paths)})

            return QueryResult(
                success=True,
                question=question,
                answer=answer,
                sources_used=page_paths,
                saved_path=saved_path,
            )

        except (FileNotFoundError, ValueError) as e:
            logger.exception(msg="Query failed due to file or value error")
            return QueryResult(
                success=False,
                question=question,
                answer="",
                sources_used=[],
                saved_path=None,
                error=str(e),
            )
        except Exception as e:
            logger.exception(msg="Unexpected query error")
            return QueryResult(
                success=False,
                question=question,
                answer="",
                sources_used=[],
                saved_path=None,
                error=f"Unexpected error: {str(e)}",
            )

    def get_status(self) -> dict:
        """
        Get current wiki statistics.

        Returns:
            Dictionary with wiki statistics
        """
        raw_count: int = len(list(Path("raw/articles").glob(pattern="*.md"))) if Path("raw/articles").exists() else 0
        sources: int = len(list(self.wiki.sources_dir.glob(pattern="*.md")))
        entities: int = len(list(self.wiki.entities_dir.glob(pattern="*.md")))
        concepts: int = len(list(self.wiki.concepts_dir.glob(pattern="*.md")))
        analyses: int = len(list(self.wiki.analyses_dir.glob(pattern="*.md")))

        # Calculate unprocessed
        try:
            from llm_wiki.ingest import list_raw_articles

            unprocessed = len(list_raw_articles())
        except Exception:
            unprocessed = 0

        return {
            "raw_articles": raw_count,
            "processed_sources": sources,
            "entities": entities,
            "concepts": concepts,
            "analyses": analyses,
            "unprocessed": unprocessed,
        }

    def ingest_all(self) -> dict:
        """
        Ingest all unprocessed articles.

        Returns:
            Dictionary with bulk ingest results
        """
        logger.info(msg="Starting bulk ingest")

        try:
            unprocessed = list_raw_articles()

            if not unprocessed:
                return {
                    "success": True,
                    "total_articles": 0,
                    "successful": 0,
                    "failed": 0,
                    "details": [],
                }

            results = []
            successful = 0
            failed = 0

            for article in unprocessed:
                result: IngestResult = self.ingest(article_path=article)
                results.append({"article": article.name, "success": result.success})
                if result.success:
                    successful += 1
                else:
                    failed += 1

            logger.info(msg="Bulk ingest complete", extra={"successful": successful, "failed": failed})

            return {
                "success": True,
                "total_articles": len(unprocessed),
                "successful": successful,
                "failed": failed,
                "details": results,
            }

        except Exception as e:
            logger.error(msg="Bulk ingest failed", extra={"error": str(e)}, exc_info=True)
            return {
                "success": False,
                "total_articles": 0,
                "successful": 0,
                "failed": 0,
                "error": str(e),
            }

    # Private helper methods for ingest operations
    def _create_concept_pages(
        self, concepts: list[str] | tuple[str, ...], article_title: str, source_file: str, article_content: str
    ) -> list[Path]:
        """Create or update concept pages from metadata."""
        return [
            self.concept_service.create_or_update(
                concept_name=concept,
                article_title=article_title,
                source_file=source_file,
                related_concepts=list(concepts),
                article_content=article_content,
            )
            for concept in concepts
            if concept.strip()
        ]

    def _create_entity_pages(
        self, entities: list[str] | tuple[str, ...], article_title: str, source_file: str, article_content: str
    ) -> list[Path]:
        """Create or update entity pages from metadata."""
        return [
            self.entity_service.create_or_update(
                entity_name=entity,
                article_title=article_title,
                source_file=source_file,
                article_content=article_content,
            )
            for entity in entities
            if entity.strip()
        ]

    # Private helper methods for metadata extraction and query operations
    def _extract_metadata(self, article_content: str, frontmatter: Frontmatter) -> Metadata:
        """Extract metadata from article using LLM."""
        prompt = format_prompt(
            template_name="extract_metadata",
            title=frontmatter.title,
            author=frontmatter.author,
            content=article_content[:2000],
        )

        system_prompt: str = format_prompt(template_name="extract_metadata_system")

        response: str = self.llm.generate(prompt, system_prompt)

        # Try to parse JSON from response
        metadata_dict = extract_json_from_text(text=response)
        if metadata_dict:
            return Metadata.from_dict(data=metadata_dict)
        else:
            logger.warning(msg="Could not parse LLM response", extra={"response": response[:200]})
            return Metadata.from_dict(
                data={"summary": "Article summary not available", "key_concepts": [], "entities": [], "tags": []}
            )

    def _read_pages(self, page_paths: list[str]) -> dict[str, str]:
        """Read content from wiki pages."""
        pages = {}
        for path in page_paths:
            full_path: Path = self.wiki.root_path / path
            if full_path.exists():
                pages[path] = full_path.read_text(encoding="utf-8")
            else:
                logger.warning(msg="Page not found", extra={"path": path})
        return pages

    def _generate_answer(self, question: str, pages: dict[str, str]) -> str:
        """Generate answer using LLM based on wiki pages."""
        # Combine page contents
        context = ""
        for path, content in pages.items():
            context += f"\n\n## From: {path}\n\n{content[:2000]}\n"

        prompt: str = format_prompt(template_name="generate_answer", question=question, context=context)

        system_prompt: str = format_prompt(template_name="generate_answer_system")

        return self.llm.generate(prompt, system_prompt)
