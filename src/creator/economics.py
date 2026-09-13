"""Harness 9 Creator Economics & Cost/Revenue Ledger Engine (Milestone M5).

Tracks granular itemized resource consumption across all production stages:
1. LLM Inference (Prompt tokens, completion tokens, prompt cache hits across models)
2. Research APIs (Search queries across Tavily, Exa, Serper, Wikimedia)
3. TTS Audio Synthesis (Characters synthesized across ElevenLabs, OpenAI, local backends)
4. Video Rendering (Headless browser + FFmpeg GPU/CPU compute execution seconds)
5. Media Storage & Egress (Megabytes of frozen images, audio, comps, rendered MP4)

Calculates unit economics, cost-per-second, margin against CPM/RPM, and budget compliance.
"""

from datetime import datetime, timezone
from enum import Enum
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import Field, field_validator, model_validator

from src.models.contracts import H9BaseModel


# ===========================================================================
# 1. Enums and Rate Models
# ===========================================================================
class CostCategory(str, Enum):
    """5 itemized cost accounting categories."""
    LLM = "llm"
    RESEARCH = "research"
    TTS = "tts"
    RENDER = "render"
    STORAGE = "storage"


class UnitType(str, Enum):
    """Resource consumption measurement units."""
    TOKENS = "tokens"
    QUERIES = "queries"
    CHARACTERS = "characters"
    SECONDS = "seconds"
    MEGABYTES = "megabytes"
    GIGABYTES = "gigabytes"


class RateTable(H9BaseModel):
    """Default unit pricing rates in USD for all resources."""
    # LLM pricing per 1,000 tokens ($ / 1k tokens)
    llm_prompt_rate_per_1k: float = Field(default=0.0025, ge=0.0)      # $2.50 / 1M tokens
    llm_completion_rate_per_1k: float = Field(default=0.0100, ge=0.0)  # $10.00 / 1M tokens
    llm_cached_rate_per_1k: float = Field(default=0.0005, ge=0.0)      # $0.50 / 1M tokens

    # Research API query rates ($ / query)
    research_query_rate_usd: float = Field(default=0.0050, ge=0.0)     # $5.00 / 1k queries

    # TTS audio rates ($ / character)
    tts_char_rate_usd: float = Field(default=0.00003, ge=0.0)          # $30.00 / 1M chars (ElevenLabs tier)

    # Compute execution rates ($ / second)
    render_compute_rate_per_sec_usd: float = Field(default=0.0004, ge=0.0)  # ~$1.44 / GPU hr

    # Storage rates ($ / GB-month)
    storage_rate_per_gb_month_usd: float = Field(default=0.0200, ge=0.0)    # S3 standard tier

    # Per-model / per-provider overrides
    model_rates: Dict[str, Dict[str, float]] = Field(
        default_factory=lambda: {
            "gpt-4o": {"prompt": 0.0025, "completion": 0.0100, "cached": 0.00125},
            "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.00060, "cached": 0.000075},
            "claude-3-5-sonnet": {"prompt": 0.0030, "completion": 0.0150, "cached": 0.00030},
            "deepseek-v3": {"prompt": 0.00027, "completion": 0.00110, "cached": 0.00007},
            "elevenlabs": {"char": 0.00003},
            "openai-tts": {"char": 0.000015},
            "sapi": {"char": 0.0},
            "harmonic": {"char": 0.0},
        }
    )

    def get_llm_rate(self, model: str, token_type: str = "prompt") -> float:
        """Get per-token rate in USD."""
        model_clean = model.lower().strip()
        if model_clean in self.model_rates and token_type in self.model_rates[model_clean]:
            rate_per_1k = self.model_rates[model_clean][token_type]
        elif token_type == "completion":
            rate_per_1k = self.llm_completion_rate_per_1k
        elif token_type == "cached":
            rate_per_1k = self.llm_cached_rate_per_1k
        else:
            rate_per_1k = self.llm_prompt_rate_per_1k
        return rate_per_1k / 1000.0

    def get_tts_rate(self, provider: str) -> float:
        """Get per-character TTS rate in USD."""
        prov_clean = provider.lower().strip()
        if prov_clean in self.model_rates and "char" in self.model_rates[prov_clean]:
            return self.model_rates[prov_clean]["char"]
        if "eleven" in prov_clean:
            return 0.00003
        if "openai" in prov_clean:
            return 0.000015
        if "sapi" in prov_clean or "harmonic" in prov_clean or "local" in prov_clean:
            return 0.0
        return self.tts_char_rate_usd


# ===========================================================================
# 2. Usage Events & Cost Items
# ===========================================================================
class UsageEvent(H9BaseModel):
    """Raw usage telemetry recorded during a stage execution."""
    event_id: str = Field(..., min_length=1)
    category: str = Field(..., description="CostCategory value")
    item_name: str = Field(..., min_length=1)
    units_consumed: float = Field(..., ge=0.0)
    unit_type: str = Field(default="tokens")
    model_or_provider: Optional[str] = None
    stage: Optional[str] = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CostItem(H9BaseModel):
    """Granular itemized cost line entry."""
    category: str = Field(..., description="CostCategory value")
    item_name: str = Field(..., min_length=1)
    units_consumed: float = Field(..., ge=0.0)
    unit_type: str = Field(..., min_length=1)
    unit_rate_usd: float = Field(..., ge=0.0)
    total_cost_usd: float = Field(..., ge=0.0)
    stage: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ===========================================================================
# 3. Production Cost Ledger
# ===========================================================================
class ProductionCostLedger(H9BaseModel):
    """Itemized cost and margin ledger for a video production run."""
    run_id: str = Field(..., min_length=1)
    project_id: str = Field(default="project_default")
    items: List[CostItem] = Field(default_factory=list)
    total_cost_usd: float = Field(default=0.0, ge=0.0)
    cost_per_video_second: float = Field(default=0.0, ge=0.0)
    video_duration_seconds: float = Field(default=30.0, ge=0.0)
    estimated_revenue_usd: float = Field(default=0.0, ge=0.0)
    estimated_margin_percent: float = Field(default=0.0)
    target_cpm_usd: float = Field(default=5.0, ge=0.0)
    projected_views: int = Field(default=1000, ge=0)
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def calculate_totals(self) -> "ProductionCostLedger":
        """Compute aggregate totals, cost-per-second, and margin."""
        if self.items:
            total = sum(item.total_cost_usd for item in self.items)
            object.__setattr__(self, "total_cost_usd", round(total, 6))

        # Zero-duration safe calculation
        if self.video_duration_seconds > 0.0:
            cps = self.total_cost_usd / self.video_duration_seconds
            object.__setattr__(self, "cost_per_video_second", round(cps, 6))
        else:
            object.__setattr__(self, "cost_per_video_second", 0.0)

        # Revenue and margin calculation
        if self.projected_views > 0 and self.target_cpm_usd > 0:
            revenue = (self.projected_views / 1000.0) * self.target_cpm_usd
            object.__setattr__(self, "estimated_revenue_usd", round(revenue, 4))
            if revenue > 0:
                margin = ((revenue - self.total_cost_usd) / revenue) * 100.0
                object.__setattr__(self, "estimated_margin_percent", round(margin, 2))
        return self

    def add_item(self, item: CostItem) -> None:
        """Add cost item and update ledger summary."""
        self.items.append(item)
        self.recalculate()

    def recalculate(
        self,
        video_duration_seconds: Optional[float] = None,
        target_cpm_usd: Optional[float] = None,
        projected_views: Optional[int] = None,
    ) -> None:
        """Recalculate ledger totals."""
        if video_duration_seconds is not None:
            self.video_duration_seconds = max(0.0, float(video_duration_seconds))
        if target_cpm_usd is not None:
            self.target_cpm_usd = max(0.0, float(target_cpm_usd))
        if projected_views is not None:
            self.projected_views = max(0, int(projected_views))

        self.total_cost_usd = round(sum(i.total_cost_usd for i in self.items), 6)

        if self.video_duration_seconds > 0:
            self.cost_per_video_second = round(self.total_cost_usd / self.video_duration_seconds, 6)
        else:
            self.cost_per_video_second = 0.0

        revenue = (self.projected_views / 1000.0) * self.target_cpm_usd
        self.estimated_revenue_usd = round(revenue, 4)
        if revenue > 0:
            self.estimated_margin_percent = round(((revenue - self.total_cost_usd) / revenue) * 100.0, 2)
        else:
            self.estimated_margin_percent = 0.0

    def summary_by_category(self) -> Dict[str, float]:
        """Aggregate total expenses by category."""
        summary: Dict[str, float] = {
            CostCategory.LLM.value: 0.0,
            CostCategory.RESEARCH.value: 0.0,
            CostCategory.TTS.value: 0.0,
            CostCategory.RENDER.value: 0.0,
            CostCategory.STORAGE.value: 0.0,
        }
        for item in self.items:
            cat = item.category.lower()
            summary[cat] = round(summary.get(cat, 0.0) + item.total_cost_usd, 6)
        return summary

    def summary_by_unit_type(self) -> Dict[str, float]:
        """Aggregate units consumed by unit type."""
        summary: Dict[str, float] = {}
        for item in self.items:
            ut = item.unit_type.lower()
            summary[ut] = round(summary.get(ut, 0.0) + item.units_consumed, 2)
        return summary

    def to_markdown_table(self) -> str:
        """Format ledger as a clean markdown table."""
        lines = [
            "### Production Cost Ledger",
            f"**Run ID**: `{self.run_id}` | **Project ID**: `{self.project_id}`",
            f"**Duration**: {self.video_duration_seconds:.1f}s | **Total Cost**: ${self.total_cost_usd:.4f} | **Cost/Sec**: ${self.cost_per_video_second:.5f}/s",
            f"**Estimated Margin**: {self.estimated_margin_percent:.1f}% (at ${self.target_cpm_usd:.2f} CPM)",
            "",
            "| Category | Resource Item | Units Consumed | Unit Rate ($) | Total Cost ($) |",
            "|---|---|---|---|---|",
        ]
        for item in self.items:
            lines.append(
                f"| `{item.category}` | {item.item_name} | {item.units_consumed:,.1f} {item.unit_type} | ${item.unit_rate_usd:.6f} | ${item.total_cost_usd:.4f} |"
            )
        lines.append(
            f"| **TOTAL** | **All Categories** | - | - | **${self.total_cost_usd:.4f}** |"
        )
        return "\n".join(lines)


# ===========================================================================
# 4. Creator Economics Engine
# ===========================================================================
class CreatorEconomicsEngine:
    """Engine for recording usage events, compiling ledgers, and evaluating margins."""

    def __init__(self, rate_table: Optional[RateTable] = None):
        self.rates = rate_table or RateTable()
        self._events: List[UsageEvent] = []

    def record_event(self, event: UsageEvent) -> None:
        """Log a generic usage event."""
        self._events.append(event)

    def record_llm_usage(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        cached_tokens: int = 0,
        model: str = "gpt-4o",
        stage: str = "editorial",
    ) -> List[UsageEvent]:
        """Record prompt, completion, and cached token consumption."""
        ts = datetime.now(timezone.utc).isoformat()
        events = []
        if prompt_tokens > 0:
            events.append(
                UsageEvent(
                    event_id=f"llm_p_{int(datetime.now().timestamp()*1000)}",
                    category=CostCategory.LLM.value,
                    item_name=f"LLM Prompt Tokens ({model})",
                    units_consumed=float(prompt_tokens),
                    unit_type=UnitType.TOKENS.value,
                    model_or_provider=model,
                    stage=stage,
                    timestamp=ts,
                )
            )
        if completion_tokens > 0:
            events.append(
                UsageEvent(
                    event_id=f"llm_c_{int(datetime.now().timestamp()*1000)+1}",
                    category=CostCategory.LLM.value,
                    item_name=f"LLM Completion Tokens ({model})",
                    units_consumed=float(completion_tokens),
                    unit_type=UnitType.TOKENS.value,
                    model_or_provider=model,
                    stage=stage,
                    timestamp=ts,
                )
            )
        if cached_tokens > 0:
            events.append(
                UsageEvent(
                    event_id=f"llm_cache_{int(datetime.now().timestamp()*1000)+2}",
                    category=CostCategory.LLM.value,
                    item_name=f"LLM Cached Tokens ({model})",
                    units_consumed=float(cached_tokens),
                    unit_type=UnitType.TOKENS.value,
                    model_or_provider=model,
                    stage=stage,
                    timestamp=ts,
                )
            )
        self._events.extend(events)
        return events

    def record_research_usage(
        self,
        queries_count: int,
        provider: str = "tavily",
        stage: str = "research",
    ) -> UsageEvent:
        """Record research API query calls."""
        event = UsageEvent(
            event_id=f"res_{int(datetime.now().timestamp()*1000)}",
            category=CostCategory.RESEARCH.value,
            item_name=f"Research Queries ({provider})",
            units_consumed=float(queries_count),
            unit_type=UnitType.QUERIES.value,
            model_or_provider=provider,
            stage=stage,
        )
        self._events.append(event)
        return event

    def record_tts_usage(
        self,
        character_count: int,
        provider: str = "elevenlabs",
        stage: str = "scriptwriting",
    ) -> UsageEvent:
        """Record TTS character synthesis."""
        event = UsageEvent(
            event_id=f"tts_{int(datetime.now().timestamp()*1000)}",
            category=CostCategory.TTS.value,
            item_name=f"TTS Characters ({provider})",
            units_consumed=float(character_count),
            unit_type=UnitType.CHARACTERS.value,
            model_or_provider=provider,
            stage=stage,
        )
        self._events.append(event)
        return event

    def record_render_usage(
        self,
        render_duration_sec: float,
        gpu_accelerated: bool = True,
        stage: str = "render",
    ) -> UsageEvent:
        """Record video rendering compute seconds."""
        event = UsageEvent(
            event_id=f"rnd_{int(datetime.now().timestamp()*1000)}",
            category=CostCategory.RENDER.value,
            item_name=f"Render Compute ({'GPU' if gpu_accelerated else 'CPU'})",
            units_consumed=float(render_duration_sec),
            unit_type=UnitType.SECONDS.value,
            model_or_provider="ffmpeg_chromium",
            stage=stage,
        )
        self._events.append(event)
        return event

    def record_storage_usage(
        self,
        storage_mb: float,
        stage: str = "assets",
    ) -> UsageEvent:
        """Record asset and media storage footprint."""
        event = UsageEvent(
            event_id=f"sto_{int(datetime.now().timestamp()*1000)}",
            category=CostCategory.STORAGE.value,
            item_name="Media Storage Footprint",
            units_consumed=float(storage_mb),
            unit_type=UnitType.MEGABYTES.value,
            model_or_provider="local_s3",
            stage=stage,
        )
        self._events.append(event)
        return event

    def calculate_production_cost(
        self,
        session_id: str,
        events: Optional[List[UsageEvent]] = None,
        video_duration_seconds: float = 30.0,
        target_cpm: float = 5.0,
        projected_views: int = 1000,
        project_id: str = "default_project",
    ) -> ProductionCostLedger:
        """Convert recorded usage events into an itemized production cost ledger."""
        all_events = events if events is not None else self._events
        items: List[CostItem] = []

        for ev in all_events:
            category = ev.category.lower()
            model_prov = ev.model_or_provider or "default"

            # Determine unit rate
            if category == CostCategory.LLM.value:
                if "completion" in ev.item_name.lower():
                    rate = self.rates.get_llm_rate(model_prov, "completion")
                elif "cached" in ev.item_name.lower():
                    rate = self.rates.get_llm_rate(model_prov, "cached")
                else:
                    rate = self.rates.get_llm_rate(model_prov, "prompt")
            elif category == CostCategory.RESEARCH.value:
                rate = self.rates.research_query_rate_usd
            elif category == CostCategory.TTS.value:
                rate = self.rates.get_tts_rate(model_prov)
            elif category == CostCategory.RENDER.value:
                rate = self.rates.render_compute_rate_per_sec_usd
            elif category == CostCategory.STORAGE.value:
                # Convert storage per GB-month to MB-month
                rate = (self.rates.storage_rate_per_gb_month_usd / 1024.0)
            else:
                rate = 0.0

            total_cost = round(ev.units_consumed * rate, 6)

            items.append(
                CostItem(
                    category=ev.category,
                    item_name=ev.item_name,
                    units_consumed=ev.units_consumed,
                    unit_type=ev.unit_type,
                    unit_rate_usd=rate,
                    total_cost_usd=total_cost,
                    stage=ev.stage,
                    metadata=ev.metadata,
                )
            )

        ledger = ProductionCostLedger(
            run_id=session_id,
            project_id=project_id,
            items=items,
            video_duration_seconds=max(0.0, float(video_duration_seconds)),
            target_cpm_usd=max(0.0, float(target_cpm)),
            projected_views=max(0, int(projected_views)),
        )
        return ledger

    def estimate_budget_compliance(
        self,
        ledger: ProductionCostLedger,
        max_budget_usd: float = 0.50,
    ) -> Dict[str, Any]:
        """Check whether production ledger conforms to budget constraints."""
        total = ledger.total_cost_usd
        compliant = total <= max_budget_usd
        headroom = round(max_budget_usd - total, 4)
        pct_used = round((total / max_budget_usd) * 100.0, 2) if max_budget_usd > 0 else 100.0

        return {
            "compliant": compliant,
            "max_budget_usd": max_budget_usd,
            "actual_cost_usd": total,
            "headroom_usd": headroom,
            "percent_budget_used": pct_used,
            "cost_per_second": ledger.cost_per_video_second,
            "recommendation": "Optimal cost profile" if compliant else "Optimize LLM prompt size or switch to cheaper TTS tier",
        }
