"""Research Engine Package for Milestone 1."""

from src.research.engine import ResearchEngine
from src.research.providers import (
    BaseSearchProvider,
    DuckDuckGoProvider,
    ExaProvider,
    MultiProviderDispatcher,
    SearchResult,
    TavilyProvider,
    WikipediaProvider,
)
from src.research.scoring import (
    calculate_clarity_score,
    calculate_conflict_penalty,
    calculate_corroboration_score,
    get_domain_authority,
    score_claim,
)

__all__ = [
    "ResearchEngine",
    "BaseSearchProvider",
    "WikipediaProvider",
    "DuckDuckGoProvider",
    "TavilyProvider",
    "ExaProvider",
    "MultiProviderDispatcher",
    "SearchResult",
    "get_domain_authority",
    "calculate_corroboration_score",
    "calculate_clarity_score",
    "calculate_conflict_penalty",
    "score_claim",
]
