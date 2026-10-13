"""Main Research & Fact Synthesis Engine (Requirement R1)."""

import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from src.config import (
    AppConfig,
    DEFAULT_TARGET_DURATION_SEC,
    RESEARCH_PRESETS_DIR,
    get_default_config,
)
from src.models.dossier import (
    Claim,
    DossierMetadata,
    ResearchDossier,
    Source,
    Statistic,
    Summary,
    TalkingPoint,
)
from src.research.providers import MultiProviderDispatcher, SearchResult
from src.research.scoring import score_claim
from src.utils.filesystem import ensure_dir

logger = logging.getLogger(__name__)
MAX_TOPIC_LENGTH = 240


class ResearchUnavailableError(RuntimeError):
    """Raised when the engine cannot produce source-backed research."""


class InsufficientEvidenceError(ResearchUnavailableError):
    """Raised when live search does not produce enough distinct claims."""


class ResearchEngine:
    """Orchestrates web research and the bundled research presets."""

    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or get_default_config()
        self.presets_dir = Path(self.config.presets_dir)
        self.dispatcher = MultiProviderDispatcher(
            tavily_key=self.config.tavily_api_key,
            exa_key=self.config.exa_api_key,
            timeout=self.config.search_timeout_sec,
        )

        # Keyword mapping for curated benchmark presets
        self.preset_keywords: Dict[str, str] = {
            "the history of the transistor": "transistor_history.yaml",
            "history of the transistor": "transistor_history.yaml",
            "transistor": "transistor_history.yaml",
            "the invention of the transistor": "transistor_history.yaml",
            "transistor invention": "transistor_history.yaml",
            "how gpus work": "how_gpus_work.yaml",
            "how gpus work: parallel computing": "how_gpus_work.yaml",
            "how gpu works": "how_gpus_work.yaml",
            "gpu parallel computing": "how_gpus_work.yaml",
            "the apollo guidance computer": "apollo_computer.yaml",
            "the apollo 11 guidance computer": "apollo_computer.yaml",
            "apollo guidance computer": "apollo_computer.yaml",
            "how quantum computers work": "quantum_computing.yaml",
            "quantum computing": "quantum_computing.yaml",
        }

    def _match_preset(self, topic: str, target_duration: int) -> Optional[ResearchDossier]:
        """Check if topic matches a curated preset dossier and adapt metadata."""
        if not self.presets_dir.exists():
            return None

        # Curated dossiers are whole-topic matches. Substring and prefix
        # matching lets unrelated or adversarial briefs inherit trusted claims.
        topic_clean = re.sub(r"\s+", " ", topic.casefold()).strip()
        matched_filename = self.preset_keywords.get(topic_clean)

        if matched_filename:
            preset_path = self.presets_dir / matched_filename
            if preset_path.exists():
                try:
                    dossier = ResearchDossier.load(preset_path)
                    # Update metadata with fresh run id, generated timestamp and target duration
                    dossier.topic = topic.strip()
                    dossier.metadata.run_id = f"run_{uuid.uuid4().hex[:8]}_{preset_path.stem}"
                    dossier.metadata.generated_at = datetime.now(timezone.utc).isoformat()
                    dossier.metadata.target_duration_seconds = target_duration
                    dossier.metadata.mode = "curated_preset"
                    dossier.metadata.search_backend = "curated_preset"

                    # Presets carry source metadata, not fixed confidence values.
                    for claim in dossier.claims:
                        claim.confidence_score = score_claim(
                            claim.claim_text,
                            claim.primary_source,
                            claim.corroborating_sources,
                        )

                    # Scale talking point durations to match target_duration
                    total_preset_duration = sum(tp.estimated_duration_sec for tp in dossier.talking_points)
                    if total_preset_duration > 0 and len(dossier.talking_points) > 0:
                        scale = target_duration / total_preset_duration
                        for tp in dossier.talking_points:
                            tp.estimated_duration_sec = round(tp.estimated_duration_sec * scale, 1)

                    return dossier
                except Exception as e:
                    logger.warning(f"Failed to load preset '{matched_filename}': {e}")

        return None

    def _generate_queries(self, topic: str) -> List[Tuple[str, str]]:
        """Generate focused factual queries without a redundant image-search query."""
        return [
            ("origin_history", f"{topic} history"),
            ("technical_mechanism", f"{topic} technology"),
            ("quantitative_metric", f"{topic} specifications"),
            ("modern_impact", f"{topic} impact"),
        ]

    @staticmethod
    def _claim_matches_topic(claim_text: str, topic: str) -> bool:
        """Reject snippets that mention a related entity but do not discuss the requested subject."""
        stop_words = {
            "a", "an", "and", "history", "how", "of", "the", "work", "works",
        }

        def terms(text: str) -> set[str]:
            normalized = set()
            for token in re.findall(r"[a-z0-9]+", text.lower()):
                if token in stop_words:
                    continue
                if token.endswith("s") and len(token) > 4:
                    token = token[:-1]
                if token.endswith("ing") and len(token) > 5:
                    token = token[:-3]
                elif token.endswith("er") and len(token) > 5:
                    token = token[:-2]
                normalized.add(token)
            return normalized

        topic_terms = terms(topic)
        claim_terms = terms(claim_text)
        if not topic_terms:
            return False

        # Acronyms commonly used in source text for bundled, named topics.
        aliases = {
            "apollo guidance computer": {"agc"},
            "graphics processing unit": {"gpu"},
            "quantum computing": {"qubit"},
        }
        alias_terms = aliases.get(topic.lower().strip(), set())
        if claim_terms & alias_terms:
            return True

        # Multiword named technologies need the complete name in the sentence;
        # a generic word such as "computer" is not enough to make a claim relevant.
        if len(topic_terms) >= 3:
            return topic_terms.issubset(claim_terms)
        return bool(topic_terms & claim_terms)

    def _synthesize_live(self, topic: str, target_duration: int) -> ResearchDossier:
        """Execute live multi-intent query expansion and claim synthesis."""
        intent_queries = self._generate_queries(topic)
        all_results: Dict[str, List[SearchResult]] = {}
        all_snippets: List[SearchResult] = []

        # First fetch primary topic search for broad factual ground truth
        primary_results = self.dispatcher.search(topic, max_results=5)
        all_snippets.extend(primary_results)

        for category, query in intent_queries:
            results = self.dispatcher.search(query, max_results=3)
            # Combine category results with primary results
            combined = results + [r for r in primary_results if r not in results]
            all_results[category] = combined
            all_snippets.extend(results)

        if not all_snippets:
            raise InsufficientEvidenceError(
                f"Live research for '{topic}' returned no source results. "
                "Check the search provider configuration and try again."
            )

        # Extract sentences from snippets
        extracted_claims: List[Claim] = []
        seen_texts = set()

        categories = ["origin_history", "technical_mechanism", "quantitative_metric", "modern_impact"]
        claim_counter = 1

        for cat in categories:
            results = all_results.get(cat, [])
            if not results:
                continue

            for res in results:
                sentences = re.split(r"(?<=[.!?])\s+", res.snippet)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if len(sentence) < 40 or len(sentence) > 280:
                        continue
                    if not self._claim_matches_topic(sentence, topic):
                        continue
                    if sentence in seen_texts:
                        continue

                    seen_texts.add(sentence)
                    primary_source = Source(
                        title=res.title,
                        url=res.url,
                        publisher=res.source_domain,
                    )
                    # A different search result is not automatically evidence for
                    # this sentence. Until a source is matched claim-by-claim,
                    # do not describe it as corroboration.
                    corrob: List[Source] = []
                    conf_score = score_claim(sentence, primary_source, corrob)

                    extracted_claims.append(
                        Claim(
                            claim_id=f"claim_{claim_counter:02d}",
                            claim_text=sentence,
                            category=cat,
                            confidence_score=conf_score,
                            primary_source=primary_source,
                            corroborating_sources=corrob,
                            visual_cue_suggestion=f"Visual representation of {topic} highlighting {cat.replace('_', ' ')}",
                            verification_notes=(
                                f"Extracted from {res.source_domain}; source and claim require human review."
                            ),
                        )
                    )
                    claim_counter += 1
                    break  # Take one strong claim per category

        if len(extracted_claims) < 3:
            raise InsufficientEvidenceError(
                f"Live research for '{topic}' found only {len(extracted_claims)} usable claims; "
                "at least 3 are required. No claims were added to fill the gap."
            )

        # Sort claims by confidence score descending and select top 4-5
        extracted_claims.sort(key=lambda c: c.confidence_score, reverse=True)
        extracted_claims = extracted_claims[:5]
        # Re-index claim_ids cleanly
        for idx, clm in enumerate(extracted_claims, start=1):
            clm.claim_id = f"claim_{idx:02d}"

        # Build talking points
        dur1 = round(target_duration * 0.25, 1)
        dur2 = round(target_duration * 0.45, 1)
        dur3 = round(target_duration - (dur1 + dur2), 1)

        talking_points = [
            TalkingPoint(
                beat_index=1,
                title="Key source claim",
                narrative_hook=extracted_claims[0].claim_text,
                supported_claim_ids=[extracted_claims[0].claim_id],
                estimated_duration_sec=dur1,
            ),
            TalkingPoint(
                beat_index=2,
                title="Mechanism and evidence",
                narrative_hook=extracted_claims[1].claim_text,
                supported_claim_ids=[c.claim_id for c in extracted_claims[1:3]],
                estimated_duration_sec=dur2,
            ),
            TalkingPoint(
                beat_index=3,
                title="Additional source claim",
                narrative_hook=extracted_claims[-1].claim_text,
                supported_claim_ids=[extracted_claims[-1].claim_id],
                estimated_duration_sec=dur3,
            ),
        ]

        # Build statistics
        statistics: List[Statistic] = []
        for c in extracted_claims:
            stat_match = re.search(r"(\d+(\.\d+)?\s*(%|percent|billion|million|trillion|nm|GHz|MHz|KB|MB|GB|TB))", c.claim_text, re.IGNORECASE)
            if stat_match:
                statistics.append(
                    Statistic(
                        metric="Key Milestone Metric",
                        value=stat_match.group(0),
                        context=c.claim_text[:100],
                        source_claim_id=c.claim_id,
                    )
                )
        # Image search needs short subject terms, not whole factual sentences.
        # Use three queries to align one visual with each generated scene.
        if "apollo" in topic.lower() and ("guidance computer" in topic.lower() or "agc" in topic.lower()):
            visual_terms = ("hardware", "block diagram", "DSKY")
        else:
            visual_terms = ("hardware", "system diagram", "interface")
        suggested_visual_queries = [f"{topic} {term}" for term in visual_terms]

        # Executive summary
        summary = Summary(
            headline=f"{topic}: Source review required",
            executive_summary="Retrieved statements remain unverified and require review against their linked sources. "
            + " ".join(c.claim_text for c in extracted_claims[:3]),
            key_takeaways=[c.claim_text for c in extracted_claims[:3]],
        )

        metadata = DossierMetadata(
            run_id=f"run_live_{uuid.uuid4().hex[:8]}",
            generated_at=datetime.now(timezone.utc).isoformat(),
            mode="online",
            target_duration_seconds=target_duration,
            search_backend="multi_provider_web",
        )

        return ResearchDossier(
            topic=topic,
            metadata=metadata,
            summary=summary,
            claims=extracted_claims,
            talking_points=talking_points,
            statistics=statistics,
            suggested_visual_queries=suggested_visual_queries,
        )

    def synthesize_research(
        self,
        topic: str,
        offline: bool = False,
        target_duration: int = DEFAULT_TARGET_DURATION_SEC,
        output_dir: Optional[Union[str, Path]] = None,
    ) -> ResearchDossier:
        """
        Synthesize a dossier from a bundled preset or live search.

        Offline mode is limited to the curated presets. Online mode fails closed
        when providers are unavailable or return fewer than three usable claims;
        it never pads the dossier with generated claims or citations.
        """
        if not topic or not topic.strip():
            raise ValueError("Topic string cannot be empty")

        clean_topic = topic.strip()
        if len(clean_topic) > MAX_TOPIC_LENGTH:
            raise ResearchUnavailableError(
                f"Topic exceeds the {MAX_TOPIC_LENGTH}-character limit. "
                "Shorten the brief and try again."
            )
        effective_offline = offline or self.config.offline_mode

        dossier: Optional[ResearchDossier] = None

        if effective_offline:
            dossier = self._match_preset(clean_topic, target_duration)
            if not dossier:
                available = (
                    "The History of the Transistor",
                    "How GPUs Work",
                    "The Apollo Guidance Computer",
                    "How Quantum Computers Work",
                )
                raise ResearchUnavailableError(
                    f"No offline research preset matches {clean_topic[:80]!r}. "
                    f"Available curated topics: {', '.join(available)}. "
                    "Use online research for other topics."
                )
        else:
            try:
                dossier = self._synthesize_live(clean_topic, target_duration)
            except InsufficientEvidenceError:
                raise
            except Exception as e:
                logger.warning(f"Live research failed for '{clean_topic}': {e}")
                raise ResearchUnavailableError(
                    f"Live research is unavailable for '{clean_topic}': {e}. "
                    "Check the configured search providers and try again."
                ) from e

        # Ensure schema version and target duration are set
        dossier.schema_version = "1.0.0"
        dossier.metadata.target_duration_seconds = target_duration

        # Save to output_dir if requested
        if output_dir:
            out_path = ensure_dir(output_dir)
            dossier.save(out_path, base_name="research_dossier")

        return dossier
