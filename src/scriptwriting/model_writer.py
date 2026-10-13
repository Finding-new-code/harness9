"""Provider-neutral source-grounded script narration and validation."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Protocol, Tuple

from src.models.dossier import ResearchDossier
from src.models.script import Scene


class NarrationModel(Protocol):
    """Provider-neutral interface for source-grounded narration generation."""

    @property
    def label(self) -> str: ...

    def complete(self, prompt: str) -> str: ...


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def generate_narration(
    *,
    dossier: ResearchDossier,
    scenes: List[Scene],
    target_duration: float,
    model_client: NarrationModel,
) -> Tuple[str, Dict[str, Dict[str, Any]]]:
    """Generate and validate a target-length narration tied to scene claim IDs."""
    if not scenes:
        raise ValueError("Cannot write narration for an empty storyboard.")

    claim_map = {claim.claim_id: claim for claim in dossier.claims}
    scene_claims: Dict[str, List[str]] = {}
    for index, scene in enumerate(scenes):
        point = dossier.talking_points[index] if index < len(dossier.talking_points) else None
        allowed_ids = [
            claim_id for claim_id in (point.supported_claim_ids if point else [])
            if claim_id in claim_map
        ]
        if not allowed_ids:
            raise ValueError(f"Scene {scene.scene_id} has no source-backed claim to narrate.")
        scene_claims[scene.scene_id] = allowed_ids

    # Windows SAPI on the beta machine measured about 98 words/minute. Target
    # slightly below that rate and do not permit extra words above the target:
    # number/acronym expansion and utterance rounding can push measured WAVs
    # over the video boundary. Pipeline's stage-3 gate remains authoritative.
    target_words = max(1, round(float(target_duration) * 95.0 / 60.0))
    low_words = max(1, round(target_words * 0.94))
    high_words = target_words
    scene_count = len(scenes)
    per_scene_min = max(1, low_words // scene_count)
    per_scene_max = max(per_scene_min, (high_words + scene_count - 1) // scene_count)
    base_scene_words, scene_word_remainder = divmod(target_words, scene_count)
    scene_word_targets = [
        base_scene_words + (1 if index < scene_word_remainder else 0)
        for index in range(scene_count)
    ]

    source_claims = []
    for claim in dossier.claims:
        source_claims.append({
            "claim_id": claim.claim_id,
            "claim_text": claim.claim_text,
            "source_title": claim.primary_source.title,
            "source_url": claim.primary_source.url,
            "verification_status": claim.verification_status,
        })

    prompt_obj = {
        "task": "Write one concise narration passage for each scene.",
        "topic": dossier.topic,
        "target_duration_seconds": float(target_duration),
        "target_total_words": target_words,
        "allowed_total_word_range": [low_words, high_words],
        "scenes": [
            {
                "scene_id": scene.scene_id,
                "visual_title": scene.title,
                "allowed_claim_ids": scene_claims[scene.scene_id],
                "claims": [claim for claim in source_claims if claim["claim_id"] in scene_claims[scene.scene_id]],
                "target_narration_words": scene_word_targets[index],
                "allowed_narration_word_range": [per_scene_min, per_scene_max],
            }
            for index, scene in enumerate(scenes)
        ],
        "required_output": {
            "scenes": [
                {"scene_id": "scene_1", "claim_ids": ["claim_01"], "narration_text": "spoken words"}
            ]
        },
        "rules": [
            "Return exactly one scene entry per requested scene, in the same order.",
            "Use only claim IDs allowed for that scene and include at least one.",
            f"Write {per_scene_min}-{per_scene_max} narration words for every scene; aim for each scene's target word count.",
            "Keep both each scene and the total narration within their allowed word ranges.",
            "Use one short spoken sentence per scene when possible.",
            "Do not speak scene headings, citations, or verification labels.",
            "A source URL is provenance, not permission to add facts absent from claim_text.",
        ],
    }
    prompt = json.dumps(prompt_obj, ensure_ascii=False)
    raw_output = model_client.complete(prompt).strip()
    if not raw_output:
        raise RuntimeError("Configured Hermes model returned an empty narration response.")

    # Some compatible Responses endpoints wrap JSON in a Markdown fence despite
    # the instruction. Remove only that wrapper; do not recover partial text.
    raw_output = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_output, flags=re.IGNORECASE)
    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        raise ValueError("Configured Hermes model returned invalid JSON for narration.") from exc

    entries = parsed.get("scenes") if isinstance(parsed, dict) else None
    if not isinstance(entries, list) or len(entries) != len(scenes):
        raise ValueError("Model narration must contain exactly one entry for every storyboard scene.")

    def length_counts(candidate_entries: List[Any]) -> List[int]:
        counts: List[int] = []
        for scene, entry in zip(scenes, candidate_entries):
            if not isinstance(entry, dict) or entry.get("scene_id") != scene.scene_id:
                raise ValueError(f"Model narration scene order/ID mismatch at {scene.scene_id}.")
            counts.append(_word_count(str(entry.get("narration_text") or "")))
        return counts

    # Models often satisfy the total word limit while concentrating too many
    # words in one scene. Give the model explicit per-scene budgets, then retry
    # the complete object twice before failing closed.
    for revision_number in range(2):
        counts = length_counts(entries)
        total_words = sum(counts)
        scene_lengths_valid = all(per_scene_min <= count <= per_scene_max for count in counts)
        total_length_valid = low_words <= total_words <= high_words
        if scene_lengths_valid and total_length_valid:
            break
        if revision_number == 1:
            break

        revision_prompt = (
            f"{prompt}\n\nYour previous draft has {total_words} narration words total and "
            f"these per-scene counts: {counts}. Rewrite the entire JSON object. Each scene must "
            f"contain {per_scene_min}-{per_scene_max} words, aiming for {scene_word_targets} words "
            f"in order; the total must contain {low_words}-{high_words} words. Keep each sentence "
            "short, preserve the scene IDs, and use only each scene's allowed claim IDs. "
            f"Previous draft: {json.dumps(parsed, ensure_ascii=False)}"
        )
        raw_output = model_client.complete(revision_prompt).strip()
        raw_output = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_output, flags=re.IGNORECASE)
        try:
            parsed = json.loads(raw_output)
        except json.JSONDecodeError as exc:
            raise ValueError("Configured Hermes model returned invalid JSON while revising narration length.") from exc
        entries = parsed.get("scenes") if isinstance(parsed, dict) else None
        if not isinstance(entries, list) or len(entries) != len(scenes):
            raise ValueError("Revised model narration must contain exactly one entry for every storyboard scene.")

    counts = length_counts(entries)
    actual_words = sum(counts)
    if not all(per_scene_min <= count <= per_scene_max for count in counts):
        raise ValueError(
            f"Model narration scene word counts {counts}; expected {per_scene_min}-{per_scene_max} words per scene."
        )
    if actual_words < low_words or actual_words > high_words:
        raise ValueError(
            f"Model narration has {actual_words} words; expected {low_words}-{high_words} "
            f"for a {target_duration:.1f}s Windows SAPI target."
        )

    validated: Dict[str, Dict[str, Any]] = {}
    all_text: List[str] = []
    for scene, entry in zip(scenes, entries):
        if not isinstance(entry, dict) or entry.get("scene_id") != scene.scene_id:
            raise ValueError(f"Model narration scene order/ID mismatch at {scene.scene_id}.")
        text = str(entry.get("narration_text") or "").strip()
        claim_ids = entry.get("claim_ids")
        if not text or not isinstance(claim_ids, list) or not claim_ids:
            raise ValueError(f"Model narration for {scene.scene_id} is missing text or claim IDs.")
        if any(claim_id not in scene_claims[scene.scene_id] for claim_id in claim_ids):
            raise ValueError(f"Model narration for {scene.scene_id} cites a claim not assigned to it.")
        validated[scene.scene_id] = {"narration_text": text, "claim_ids": claim_ids}
        all_text.append(text)

    return model_client.label, validated
