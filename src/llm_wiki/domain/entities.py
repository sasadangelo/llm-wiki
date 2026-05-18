"""Domain entities - represent business objects."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Entity:
    """Entity domain model - represents people, organizations, tools."""

    name: str
    filename: str
    definition: str
    sources: list[str] = field(default_factory=list)
    created: datetime = field(default_factory=datetime.now)
    updated: datetime = field(default_factory=datetime.now)

    def add_source(self, source: str) -> None:
        """
        Add a source reference.

        Args:
            source: Source filename to add
        """
        if source not in self.sources:
            self.sources.append(source)
            self.updated = datetime.now()


@dataclass
class Concept:
    """Concept domain model - represents technical concepts and patterns."""

    name: str
    filename: str
    definition: str
    sources: list[str] = field(default_factory=list)
    related_concepts: list[str] = field(default_factory=list)
    created: datetime = field(default_factory=datetime.now)
    updated: datetime = field(default_factory=datetime.now)

    def add_source(self, source: str) -> None:
        """
        Add a source reference.

        Args:
            source: Source filename to add
        """
        if source not in self.sources:
            self.sources.append(source)
            self.updated = datetime.now()

    def add_related_concept(self, concept: str) -> None:
        """
        Add a related concept.

        Args:
            concept: Related concept name to add
        """
        if concept not in self.related_concepts:
            self.related_concepts.append(concept)
            self.updated = datetime.now()


@dataclass
class Source:
    """Source article domain model - represents processed articles."""

    title: str
    filename: str
    summary: str
    key_concepts: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    url: str = ""
    author: str = ""
    created: datetime = field(default_factory=datetime.now)


@dataclass
class Analysis:
    """Analysis domain model - represents query results saved as wiki pages."""

    question: str
    filename: str
    answer: str
    sources_consulted: list[str] = field(default_factory=list)
    created: datetime = field(default_factory=datetime.now)
