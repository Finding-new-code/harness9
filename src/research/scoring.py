"""Claim confidence scoring heuristics and domain authority rating for R1."""

import re
from typing import List, Optional, Tuple
from urllib.parse import urlparse

from src.config import (
    CONFIDENCE_WEIGHT_AUTHORITY,
    CONFIDENCE_WEIGHT_CORROBORATION,
    CONFIDENCE_WEIGHT_CLARITY,
)
from src.models.dossier import Claim, Source

# High authority domain registries
TIER_1_DOMAINS = {
    "nobelprize.org": 1.0,
    "bell-labs.com": 1.0,
    "nasa.gov": 1.0,
    "ieee.org": 0.98,
    "computerhistory.org": 0.98,
    "aps.org": 0.98,
    "acm.org": 0.98,
    "nist.gov": 0.98,
    "cern.ch": 0.98,
    "mit.edu": 0.98,
    "stanford.edu": 0.98,
    "nature.com": 0.96,
    "science.org": 0.96,
}

TIER_2_DOMAINS = {
    "wikipedia.org": 0.88,
    "britannica.com": 0.90,
    "semiconductors.org": 0.88,
    "spectrum.ieee.org": 0.90,
    "si.edu": 0.92,
    "loc.gov": 0.92,
}

TIER_3_DOMAINS = {
    "arstechnica.com": 0.80,
    "anandtech.com": 0.80,
    "tomshardware.com": 0.75,
    "theverge.com": 0.72,
    "wired.com": 0.75,
    "bbc.com": 0.80,
    "reuters.com": 0.82,
    "nytimes.com": 0.80,
}

DISPUTED_TERMS = [
    "disputed",
    "alleged",
    "unverified",
    "controversial",
    "claimed without evidence",
    "debated",
    "rumored",
    "myth",
    "apocryphal",
    "unconfirmed",
]


def extract_root_domain(url: str) -> str:
    """Extract root domain and TLD from URL."""
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


def get_domain_authority(url: str) -> float:
    """Compute domain authority score A in [0.0, 1.0]."""
    domain = extract_root_domain(url)
    if not domain or domain == "unknown":
        return 0.40

    # Exact or suffix domain match
    for d, score in TIER_1_DOMAINS.items():
        if domain == d or domain.endswith("." + d):
            return score

    # General .gov / .edu top-level domains
    if domain.endswith(".gov") or domain.endswith(".mil"):
        return 0.98
    if domain.endswith(".edu"):
        return 0.95

    for d, score in TIER_2_DOMAINS.items():
        if domain == d or domain.endswith("." + d):
            return score

    for d, score in TIER_3_DOMAINS.items():
        if domain == d or domain.endswith("." + d):
            return score

    if domain.endswith(".org"):
        return 0.70

    return 0.55


def calculate_corroboration_score(primary: Source, corroborating: List[Source]) -> float:
    """Compute corroboration score C in [0.0, 1.0] based on distinct sources and domains."""
    all_urls = [primary.url] + [s.url for s in corroborating if s.url]
    domains = {extract_root_domain(u) for u in all_urls if u}
    domains.discard("unknown")
    num_domains = len(domains)

    if num_domains >= 3:
        return 1.0
    elif num_domains == 2:
        return 0.75
    elif len(corroborating) >= 1:
        return 0.60
    return 0.40


def calculate_clarity_score(claim_text: str) -> float:
    """Compute specificity/clarity score Q in [0.0, 1.0] based on dates, metrics, and entities."""
    if not claim_text:
        return 0.20

    score = 0.20  # Base score

    # Check for precise 4-digit years or dates (e.g. 1947, 2026, December 23)
    if re.search(r"\b(18|19|20)\d{2}\b", claim_text) or re.search(r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\b", claim_text, re.IGNORECASE):
        score += 0.30

    # Check for numerical metrics, percentages, transistor counts, speeds
    if re.search(r"\b\d+(\.\d+)?\s*(%|percent|billion|million|trillion|nm|nanometer|GHz|MHz|kHz|transistor|watts?|volts?|kg|bytes?|MB|GB|TB)\b", claim_text, re.IGNORECASE) or re.search(r"\b\d{1,3}(,\d{3})+\b", claim_text):
        score += 0.30

    # Check for proper capitalized names and entities (at least 2 capitalized terms)
    capitalized_words = re.findall(r"\b[A-Z][a-z]{2,}\b", claim_text)
    if len(capitalized_words) >= 2:
        score += 0.20

    return min(1.0, score)


def calculate_conflict_penalty(claim_text: str) -> float:
    """Compute conflict penalty P_conflict in [0.0, 0.5]."""
    if not claim_text:
        return 0.0

    lower = claim_text.lower()
    for term in DISPUTED_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", lower):
            return 0.25
    return 0.0


def score_claim(
    claim_text: str,
    primary_source: Source,
    corroborating_sources: Optional[List[Source]] = None,
    w_auth: float = CONFIDENCE_WEIGHT_AUTHORITY,
    w_corrob: float = CONFIDENCE_WEIGHT_CORROBORATION,
    w_clarity: float = CONFIDENCE_WEIGHT_CLARITY,
) -> float:
    """
    Calculate confidence score using the formula:
    Confidence = w_auth * A + w_corrob * C + w_clarity * Q - P_conflict
    """
    corroborating = corroborating_sources or []

    # 1. Authority A
    auth_primary = get_domain_authority(primary_source.url)
    auth_corrob = [get_domain_authority(s.url) for s in corroborating]
    # Authority is weighted average of primary (60%) and best corroborating (40%)
    if auth_corrob:
        authority_score = 0.60 * auth_primary + 0.40 * max(auth_corrob)
    else:
        authority_score = auth_primary

    # 2. Corroboration C
    corroboration_score = calculate_corroboration_score(primary_source, corroborating)

    # 3. Clarity Q
    clarity_score = calculate_clarity_score(claim_text)

    # 4. Conflict penalty
    conflict_penalty = calculate_conflict_penalty(claim_text)

    # Final weighted score
    raw_score = (
        w_auth * authority_score
        + w_corrob * corroboration_score
        + w_clarity * clarity_score
        - conflict_penalty
    )

    clamped_score = max(0.0, min(1.0, raw_score))
    return round(clamped_score, 2)


class ScoringWeights:
    """Weight configuration for confidence scoring formula."""

    def __init__(
        self,
        weight_authority: float = CONFIDENCE_WEIGHT_AUTHORITY,
        weight_corroboration: float = CONFIDENCE_WEIGHT_CORROBORATION,
        weight_clarity: float = CONFIDENCE_WEIGHT_CLARITY,
    ):
        self.weight_authority = weight_authority
        self.weight_corroboration = weight_corroboration
        self.weight_clarity = weight_clarity


def calculate_confidence_score(
    domain_auth: float = 0.5,
    corroboration: float = 0.5,
    clarity: float = 0.5,
    conflict_penalty: float = 0.0,
    weights: Optional[ScoringWeights] = None,
) -> float:
    """
    Direct formula calculator: w_auth * domain_auth + w_corrob * corroboration + w_clarity * clarity - conflict_penalty
    """
    w = weights or ScoringWeights()
    raw = (
        w.weight_authority * domain_auth
        + w.weight_corroboration * corroboration
        + w.weight_clarity * clarity
        - conflict_penalty
    )
    return round(max(0.0, min(1.0, raw)), 2)

