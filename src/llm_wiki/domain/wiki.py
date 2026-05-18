"""Wiki aggregate root - manages wiki structure."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Wiki:
    """Wiki aggregate root - represents the wiki directory structure."""

    root_path: Path

    @property
    def sources_dir(self) -> Path:
        """Get sources directory path."""
        return self.root_path / "sources"

    @property
    def entities_dir(self) -> Path:
        """Get entities directory path."""
        return self.root_path / "entities"

    @property
    def concepts_dir(self) -> Path:
        """Get concepts directory path."""
        return self.root_path / "concepts"

    @property
    def analyses_dir(self) -> Path:
        """Get analyses directory path."""
        return self.root_path / "analyses"

    @property
    def index_path(self) -> Path:
        """Get index file path."""
        return self.root_path / "index.md"

    @property
    def log_path(self) -> Path:
        """Get log file path."""
        return self.root_path / "log.md"

    @property
    def overview_path(self) -> Path:
        """Get overview file path."""
        return self.root_path / "overview.md"

    def ensure_directories(self) -> None:
        """Ensure all wiki directories exist."""
        for dir_path in [
            self.sources_dir,
            self.entities_dir,
            self.concepts_dir,
            self.analyses_dir,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)
