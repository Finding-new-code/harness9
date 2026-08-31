"""Research dossier schema and data models for R1."""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import yaml

from src.utils.filesystem import atomic_write, ensure_dir


@dataclass
class Source:
    """Source citation metadata."""
    title: str
    url: str
    publisher: Optional[str] = None

    def __str__(self) -> str:
        return self.url

    def startswith(self, prefix: str) -> bool:
        """Allow string-like startswith inspection on URL."""
        return self.url.startswith(prefix)

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {"title": self.title, "url": self.url}
        if self.publisher is not None:
            data["publisher"] = self.publisher
        return data

    @classmethod
    def from_dict(cls, data: Union[str, Dict[str, Any]]) -> "Source":
        if isinstance(data, str):
            return cls(title=data, url=data)
        return cls(
            title=str(data.get("title", "")),
            url=str(data.get("url", "")),
            publisher=data.get("publisher"),
        )


@dataclass
class Claim:
    """Factual claim with citation, category, and confidence score."""
    claim_id: str
    claim_text: str
    category: str
    confidence_score: float
    primary_source: Source
    corroborating_sources: List[Source] = field(default_factory=list)
    visual_cue_suggestion: str = ""
    verification_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "claim_id": self.claim_id,
            "claim_text": self.claim_text,
            "category": self.category,
            "confidence_score": float(self.confidence_score),
            "primary_source": self.primary_source.to_dict(),
            "visual_cue_suggestion": self.visual_cue_suggestion,
        }
        if self.corroborating_sources:
            data["corroborating_sources"] = [s.to_dict() for s in self.corroborating_sources]
        if self.verification_notes:
            data["verification_notes"] = self.verification_notes
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Claim":
        primary = data.get("primary_source") or {}
        primary_source = Source.from_dict(primary) if isinstance(primary, dict) else Source(title="Unknown", url="https://example.com")
        corrob_raw = data.get("corroborating_sources") or []
        corroborating = [Source.from_dict(s) for s in corrob_raw if isinstance(s, dict)]

        return cls(
            claim_id=str(data.get("claim_id", "")),
            claim_text=str(data.get("claim_text", "")),
            category=str(data.get("category", "origin_history")),
            confidence_score=float(data.get("confidence_score", 0.0)),
            primary_source=primary_source,
            corroborating_sources=corroborating,
            visual_cue_suggestion=str(data.get("visual_cue_suggestion", "")),
            verification_notes=str(data.get("verification_notes", "")),
        )


@dataclass
class TalkingPoint:
    """Script beat talking point blueprint."""
    beat_index: int
    title: str
    narrative_hook: str
    supported_claim_ids: List[str] = field(default_factory=list)
    estimated_duration_sec: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "beat_index": int(self.beat_index),
            "title": self.title,
            "narrative_hook": self.narrative_hook,
            "supported_claim_ids": list(self.supported_claim_ids),
            "estimated_duration_sec": float(self.estimated_duration_sec),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TalkingPoint":
        return cls(
            beat_index=int(data.get("beat_index", 1)),
            title=str(data.get("title", "")),
            narrative_hook=str(data.get("narrative_hook", "")),
            supported_claim_ids=[str(cid) for cid in data.get("supported_claim_ids", [])],
            estimated_duration_sec=float(data.get("estimated_duration_sec", 0.0)),
        )


@dataclass
class Statistic:
    """Key metric or numerical statistic."""
    metric: str
    value: str
    context: str
    source_claim_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric": self.metric,
            "value": str(self.value),
            "context": self.context,
            "source_claim_id": self.source_claim_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Statistic":
        return cls(
            metric=str(data.get("metric", "")),
            value=str(data.get("value", "")),
            context=str(data.get("context", "")),
            source_claim_id=str(data.get("source_claim_id", "")),
        )


@dataclass
class Summary:
    """Executive summary and high-level takeaways."""
    headline: str
    executive_summary: str
    key_takeaways: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "headline": self.headline,
            "executive_summary": self.executive_summary,
            "key_takeaways": list(self.key_takeaways),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Summary":
        return cls(
            headline=str(data.get("headline", "")),
            executive_summary=str(data.get("executive_summary", "")),
            key_takeaways=[str(t) for t in data.get("key_takeaways", [])],
        )


@dataclass
class DossierMetadata:
    """Generation metadata for the research dossier."""
    run_id: str
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    mode: str = "online"  # "online" or "offline_fallback"
    target_duration_seconds: int = 30
    search_backend: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "run_id": self.run_id,
            "generated_at": self.generated_at,
            "mode": self.mode,
            "target_duration_seconds": int(self.target_duration_seconds),
        }
        if self.search_backend is not None:
            data["search_backend"] = self.search_backend
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DossierMetadata":
        return cls(
            run_id=str(data.get("run_id", "")),
            generated_at=str(data.get("generated_at", datetime.now(timezone.utc).isoformat())),
            mode=str(data.get("mode", "online")),
            target_duration_seconds=int(data.get("target_duration_seconds", 30)),
            search_backend=data.get("search_backend"),
        )


@dataclass
class ResearchDossier:
    """Complete structured research dossier (Requirement R1)."""
    topic: str
    metadata: DossierMetadata
    summary: Summary
    claims: List[Claim] = field(default_factory=list)
    talking_points: List[TalkingPoint] = field(default_factory=list)
    statistics: List[Statistic] = field(default_factory=list)
    suggested_visual_queries: List[str] = field(default_factory=list)
    schema_version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert full dossier to JSON/YAML serializable dictionary."""
        return {
            "schema_version": self.schema_version,
            "topic": self.topic,
            "metadata": self.metadata.to_dict(),
            "summary": self.summary.to_dict(),
            "claims": [c.to_dict() for c in self.claims],
            "talking_points": [tp.to_dict() for tp in self.talking_points],
            "statistics": [st.to_dict() for st in self.statistics],
            "suggested_visual_queries": list(self.suggested_visual_queries),
        }

    def model_dump(self) -> Dict[str, Any]:
        """Pydantic-compatible model dump."""
        return self.to_dict()

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self.to_dict().get(key, default)

    def __contains__(self, key: str) -> bool:
        return key in self.to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearchDossier":
        """Reconstruct ResearchDossier from parsed dictionary."""
        meta_dict = data.get("metadata") or {}
        metadata = DossierMetadata.from_dict(meta_dict)

        sum_dict = data.get("summary") or {}
        summary = Summary.from_dict(sum_dict)

        claims_raw = data.get("claims") or []
        claims = [Claim.from_dict(c) for c in claims_raw if isinstance(c, dict)]

        tp_raw = data.get("talking_points") or []
        talking_points = [TalkingPoint.from_dict(tp) for tp in tp_raw if isinstance(tp, dict)]

        stat_raw = data.get("statistics") or []
        statistics = [Statistic.from_dict(st) for st in stat_raw if isinstance(st, dict)]

        vis_raw = data.get("suggested_visual_queries") or []
        suggested_visual_queries = [str(q) for q in vis_raw]

        return cls(
            schema_version=str(data.get("schema_version", "1.0.0")),
            topic=str(data.get("topic", "")),
            metadata=metadata,
            summary=summary,
            claims=claims,
            talking_points=talking_points,
            statistics=statistics,
            suggested_visual_queries=suggested_visual_queries,
        )

    def to_json(self, indent: int = 2) -> str:
        """Serialize dossier to JSON formatted string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "ResearchDossier":
        """Deserialize dossier from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def to_yaml(self) -> str:
        """Serialize dossier to YAML formatted string."""
        return yaml.safe_dump(self.to_dict(), sort_keys=False, allow_unicode=True, default_flow_style=False)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "ResearchDossier":
        """Deserialize dossier from YAML string."""
        data = yaml.safe_load(yaml_str)
        if not isinstance(data, dict):
            raise ValueError("YAML root must be a dictionary object")
        return cls.from_dict(data)

    def save(
        self,
        output_dir: Union[str, Path],
        base_name: str = "research_dossier",
    ) -> Tuple[Path, Path]:
        """Save dossier to both JSON and YAML atomically."""
        out_dir = ensure_dir(output_dir)
        json_path = out_dir / f"{base_name}.json"
        yaml_path = out_dir / f"{base_name}.yaml"

        atomic_write(json_path, self.to_json(indent=2), mode="w")
        atomic_write(yaml_path, self.to_yaml(), mode="w")

        return json_path, yaml_path

    @classmethod
    def load(cls, file_path: Union[str, Path]) -> "ResearchDossier":
        """Load dossier from either a JSON or YAML file."""
        p = Path(file_path).resolve()
        if not p.exists():
            raise FileNotFoundError(f"Dossier file not found: {p}")
        text = p.read_text(encoding="utf-8")
        if p.suffix.lower() in [".yaml", ".yml"]:
            return cls.from_yaml(text)
        return cls.from_json(text)
