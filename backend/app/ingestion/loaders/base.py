"""Base abstractions for document loaders."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class RawDocumentPage:
    """Represents raw extracted text from a specific document page or section."""
    page_number: int
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseDocumentLoader(ABC):
    """Abstract base class for format-specific document loaders."""

    @abstractmethod
    def load(self, file_path: Path) -> List[RawDocumentPage]:
        """Load and extract pages with text and metadata from the given file."""
        pass
