from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from playwright.sync_api import Page

@dataclass
class RuleMetadata:
    """Metadata for a WCAG rule."""
    id: str
    description: str
    wcag_criterion: str
    level: str  # A, AA, AAA
    impact: str  # minor, moderate, serious, critical
    applicability: str  # e.g. "image", "form", "page"

class AbstractRule(ABC):
    """Base interface for all WCAG evaluation rules."""

    @property
    @abstractmethod
    def metadata(self) -> RuleMetadata:
        """Return the metadata for the rule."""
        pass

    @abstractmethod
    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        """
        Evaluate the page and return a list of violations.
        Each violation should be a dictionary with keys like:
        - 'element': Snippet of the failing element or summary
        - 'message': Why it failed
        - 'suggestion': How to fix it
        """
        pass
