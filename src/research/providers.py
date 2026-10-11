"""Live web search adapters and multi-provider dispatch for R1."""

import json
import logging
import re
import urllib.error
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from src.config import (
    DEFAULT_MAX_SEARCH_RESULTS,
    DEFAULT_SEARCH_TIMEOUT_SEC,
    get_env_var,
)

logger = logging.getLogger(__name__)

_QUERY_DIRECTIVE_WORDS = {
    "a", "an", "and", "application", "applications", "architecture", "background",
    "components", "diagrams", "facts", "for", "from", "global", "history", "how",
    "impact", "key", "mechanism", "mechanisms", "milestones", "modern", "numbers",
    "of", "on", "origin", "origins", "photographs", "principles", "quantitative",
    "schematics", "significance", "specification", "specifications", "statistics",
    "technical", "the", "to", "work", "works", "future", "historical",
}


def _relevance_terms(text: str) -> List[str]:
    """Return topic terms, omitting intent words added by research query expansion."""
    terms = []
    for token in re.findall(r"[a-z0-9]+", text.lower()):
        if token in _QUERY_DIRECTIVE_WORDS:
            continue
        if token.endswith("ing") and len(token) > 5:
            token = token[:-3]
        elif token.endswith("er") and len(token) > 5:
            token = token[:-2]
        elif token.endswith("s") and len(token) > 4:
            token = token[:-1]
        if token and token not in terms:
            terms.append(token)
    return terms


def _title_relevance(query: str, title: str) -> int:
    """Count topic terms in a title using simple singular/gerund normalization."""
    query_terms = _relevance_terms(query)
    title_terms = _relevance_terms(title)
    return sum(
        1 for term in query_terms
        if any(term == title_term or term.startswith(title_term) or title_term.startswith(term) for title_term in title_terms)
    )


@dataclass
class SearchResult:
    """Standardized search snippet result across providers."""
    title: str
    url: str
    snippet: str
    source_domain: str
    authority_score: float = 0.50
    published_date: Optional[str] = None
    raw_content: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source_domain": self.source_domain,
            "authority_score": self.authority_score,
            "published_date": self.published_date,
        }


def extract_domain(url: str) -> str:
    """Extract clean domain name from URL."""
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        if ":" in netloc:
            netloc = netloc.split(":")[0]
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc or "unknown"
    except Exception:
        return "unknown"


def clean_snippet(text: str) -> str:
    """Clean HTML tags, multiple spaces, and control characters from text snippet."""
    if not text:
        return ""
    # Strip HTML tags
    cleaned = re.sub(r"<[^>]+>", "", text)
    # Unescape common entities
    cleaned = (
        cleaned.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
        .replace("&nbsp;", " ")
    )
    # Remove space before punctuation and collapse whitespace
    cleaned = re.sub(r"\s+([,.:;!?])", r"\1", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


class BaseSearchProvider(ABC):
    """Abstract search provider interface."""

    def __init__(self, name: str, timeout: int = DEFAULT_SEARCH_TIMEOUT_SEC):
        self.name = name
        self.timeout = timeout

    @abstractmethod
    def search(self, query: str, max_results: int = DEFAULT_MAX_SEARCH_RESULTS) -> List[SearchResult]:
        """Execute search query and return standardized results."""
        pass


class WikipediaProvider(BaseSearchProvider):
    """Live search adapter querying the MediaWiki Action API with page extracts."""

    USER_AGENT = "Harness9/0.2 (https://github.com/nousresearch/hermes-agent)"

    def __init__(self, timeout: int = DEFAULT_SEARCH_TIMEOUT_SEC):
        super().__init__(name="wikipedia", timeout=timeout)
        self.opensearch_url = "https://en.wikipedia.org/w/api.php"

    def search(self, query: str, max_results: int = DEFAULT_MAX_SEARCH_RESULTS) -> List[SearchResult]:
        results: List[SearchResult] = []
        try:
            # Fetch result titles and introductory extracts in a single request.
            # The previous OpenSearch-plus-summary loop could make dozens of
            # requests per topic and used a placeholder contact address in its
            # User-Agent, making throttling more likely.
            params = {
                "action": "query",
                "generator": "search",
                "gsrsearch": query,
                "gsrnamespace": "0",
                "gsrlimit": str(min(max(1, max_results), 5)),
                "prop": "extracts|info",
                "exintro": "1",
                "explaintext": "1",
                "inprop": "url",
                "format": "json",
                "formatversion": "2",
            }
            req_url = f"{self.opensearch_url}?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(
                req_url,
                headers={"User-Agent": self.USER_AGENT, "Accept": "application/json"},
            )

            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            pages = (data.get("query") or {}).get("pages", []) if isinstance(data, dict) else []
            if not isinstance(pages, list):
                return results

            ranked_pages = []
            core_terms = _relevance_terms(query)
            minimum_overlap = min(3, len(core_terms)) if core_terms else 1
            for page in pages:
                if not isinstance(page, dict):
                    continue
                title = str(page.get("title") or "").strip()
                relevance = _title_relevance(query, title)
                if not title or relevance < minimum_overlap:
                    continue
                ranked_pages.append((relevance, page))

            ranked_pages.sort(key=lambda item: item[0], reverse=True)
            for _, page in ranked_pages[:max_results]:
                title = str(page.get("title") or "").strip()
                snippet = clean_snippet(str(page.get("extract") or ""))
                url = str(page.get("fullurl") or "").strip()
                if title and url:
                    results.append(
                        SearchResult(
                            title=f"{title} - Wikipedia",
                            url=url,
                            snippet=snippet,
                            source_domain="wikipedia.org",
                            authority_score=0.75,
                        )
                    )
        except Exception as e:
            logger.warning(f"WikipediaProvider search failed for query '{query}': {e}")

        return results


class DuckDuckGoProvider(BaseSearchProvider):
    """Live search adapter querying DuckDuckGo Instant Answer API."""

    def __init__(self, timeout: int = DEFAULT_SEARCH_TIMEOUT_SEC):
        super().__init__(name="duckduckgo", timeout=timeout)
        self.api_url = "https://api.duckduckgo.com/"

    def search(self, query: str, max_results: int = DEFAULT_MAX_SEARCH_RESULTS) -> List[SearchResult]:
        results: List[SearchResult] = []
        try:
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1",
            }
            req_url = f"{self.api_url}?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(
                req_url,
                headers={"User-Agent": "Harness9VideoPipeline/1.0 (Research)"},
            )

            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            abstract = clean_snippet(data.get("AbstractText", ""))
            abstract_url = data.get("AbstractURL", "")
            heading = data.get("Heading", query)
            source_name = data.get("AbstractSource", "DuckDuckGo")

            if abstract and abstract_url:
                domain = extract_domain(abstract_url)
                results.append(
                    SearchResult(
                        title=f"{heading} ({source_name})",
                        url=abstract_url,
                        snippet=abstract,
                        source_domain=domain,
                        authority_score=0.82 if "wikipedia" in domain else 0.70,
                    )
                )

            # Check RelatedTopics
            related = data.get("RelatedTopics", [])
            for item in related:
                if len(results) >= max_results:
                    break
                if isinstance(item, dict) and "Text" in item and "FirstURL" in item:
                    item_text = clean_snippet(item.get("Text", ""))
                    item_url = item.get("FirstURL", "")
                    if item_text and item_url:
                        domain = extract_domain(item_url)
                        results.append(
                            SearchResult(
                                title=item_text.split(" - ")[0] if " - " in item_text else heading,
                                url=item_url,
                                snippet=item_text,
                                source_domain=domain,
                                authority_score=0.75 if "wikipedia" in domain else 0.65,
                            )
                        )
        except Exception as e:
            logger.warning(f"DuckDuckGoProvider search failed for query '{query}': {e}")

        return results


class TavilyProvider(BaseSearchProvider):
    """Tavily Search API provider (used if TAVILY_API_KEY is configured)."""

    def __init__(self, api_key: Optional[str] = None, timeout: int = DEFAULT_SEARCH_TIMEOUT_SEC):
        super().__init__(name="tavily", timeout=timeout)
        self.api_key = api_key or get_env_var("TAVILY_API_KEY")
        self.endpoint = "https://api.tavily.com/search"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def search(self, query: str, max_results: int = DEFAULT_MAX_SEARCH_RESULTS) -> List[SearchResult]:
        if not self.is_available():
            return []
        results: List[SearchResult] = []
        try:
            payload = json.dumps({
                "api_key": self.api_key,
                "query": query,
                "search_depth": "advanced",
                "max_results": max_results,
                "include_raw_content": False,
            }).encode("utf-8")

            req = urllib.request.Request(
                self.endpoint,
                data=payload,
                headers={"Content-Type": "application/json", "User-Agent": "Harness9VideoPipeline/1.0"},
            )

            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            for item in data.get("results", []):
                title = clean_snippet(item.get("title", ""))
                url = item.get("url", "")
                snippet = clean_snippet(item.get("content", ""))
                domain = extract_domain(url)
                if title and url:
                    results.append(
                        SearchResult(
                            title=title,
                            url=url,
                            snippet=snippet,
                            source_domain=domain,
                            authority_score=0.85,
                        )
                    )
        except Exception as e:
            logger.warning(f"TavilyProvider search failed: {e}")

        return results


class ExaProvider(BaseSearchProvider):
    """Exa Neural Search API provider (used if EXA_API_KEY is configured)."""

    def __init__(self, api_key: Optional[str] = None, timeout: int = DEFAULT_SEARCH_TIMEOUT_SEC):
        super().__init__(name="exa", timeout=timeout)
        self.api_key = api_key or get_env_var("EXA_API_KEY")
        self.endpoint = "https://api.exa.ai/search"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def search(self, query: str, max_results: int = DEFAULT_MAX_SEARCH_RESULTS) -> List[SearchResult]:
        if not self.is_available():
            return []
        results: List[SearchResult] = []
        try:
            payload = json.dumps({
                "query": query,
                "num_results": max_results,
                "use_autoprompt": True,
            }).encode("utf-8")

            req = urllib.request.Request(
                self.endpoint,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self.api_key,  # type: ignore
                    "User-Agent": "Harness9VideoPipeline/1.0",
                },
            )

            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            for item in data.get("results", []):
                title = clean_snippet(item.get("title", ""))
                url = item.get("url", "")
                snippet = clean_snippet(item.get("text", "") or item.get("snippet", ""))
                domain = extract_domain(url)
                if title and url:
                    results.append(
                        SearchResult(
                            title=title,
                            url=url,
                            snippet=snippet,
                            source_domain=domain,
                            authority_score=0.85,
                        )
                    )
        except Exception as e:
            logger.warning(f"ExaProvider search failed: {e}")

        return results


class MultiProviderDispatcher:
    """Orchestrates search queries across active and fallback providers."""

    def __init__(
        self,
        tavily_key: Optional[str] = None,
        exa_key: Optional[str] = None,
        timeout: int = DEFAULT_SEARCH_TIMEOUT_SEC,
    ):
        self.providers: List[BaseSearchProvider] = []

        # High-priority commercial APIs if keys available
        tavily = TavilyProvider(api_key=tavily_key, timeout=timeout)
        if tavily.is_available():
            self.providers.append(tavily)

        exa = ExaProvider(api_key=exa_key, timeout=timeout)
        if exa.is_available():
            self.providers.append(exa)

        # Standard open providers (zero API key required)
        self.providers.append(WikipediaProvider(timeout=timeout))
        self.providers.append(DuckDuckGoProvider(timeout=timeout))

    def search(self, query: str, max_results: int = DEFAULT_MAX_SEARCH_RESULTS) -> List[SearchResult]:
        """Dispatch query to providers in priority order, merging and deduplicating results."""
        all_results: List[SearchResult] = []
        seen_urls = set()
        query_terms = _relevance_terms(query)
        minimum_overlap = min(3, len(query_terms)) if query_terms else 1

        for provider in self.providers:
            try:
                res = provider.search(query, max_results=max_results)
                for item in res:
                    normalized_url = item.url.lower().rstrip("/")
                    if (
                        normalized_url not in seen_urls
                        and _title_relevance(query, item.title) >= minimum_overlap
                    ):
                        seen_urls.add(normalized_url)
                        all_results.append(item)
                if len(all_results) >= max_results:
                    break
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed during multi-search: {e}")

        # Return top results up to max_results
        return all_results[:max_results]


def expand_topic_queries(topic: str) -> List[str]:
    """Generate multi-intent query strings for a given topic."""
    return [
        f"{topic} invention origins history background",
        f"How {topic} works architecture mechanisms technical principles",
        f"{topic} key statistics quantitative facts numbers milestones",
        f"{topic} global impact modern applications future significance",
        f"{topic} diagrams photographs historical schematics components",
    ]


class MockSearchProvider(BaseSearchProvider):
    """Mock search provider for testing error simulation and hermetic fallback."""

    def __init__(self, simulate_error: bool = False, timeout: int = DEFAULT_SEARCH_TIMEOUT_SEC):
        super().__init__(name="mock", timeout=timeout)
        self.simulate_error = simulate_error

    def search(self, query: str, max_results: int = DEFAULT_MAX_SEARCH_RESULTS) -> List[SearchResult]:
        if self.simulate_error:
            raise RuntimeError(f"Simulated network search error for query '{query}'")
        return [
            SearchResult(
                title=f"Mock result for {query}",
                url=f"https://example.org/mock/{urllib.parse.quote(query)}",
                snippet=f"Mock factual extract regarding {query}.",
                source_domain="example.org",
                authority_score=0.80,
            )
        ]

