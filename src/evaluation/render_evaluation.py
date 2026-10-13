"""
src.evaluation.render_evaluation — build an EvaluationReport from *measurements only*.

This replaces the previous evaluators that returned hardcoded numbers
(``audio_speech_alignment=0.95``, ``scene_pacing=0.92``, ``factual_grounding=0.96`` …) and passed
whenever an MP4 file existed. Here:

  * every score is a ratio measured by decoding the video (src.evaluation.media_gate);
  * ``passed`` is the media gate's verdict, nothing else;
  * dimensions that are NOT measured are listed explicitly in the feedback instead of being invented.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Union

from src.evaluation.media_gate import ExpectedMedia, MediaGate, MediaGateReport, MediaGateUnavailable
from src.models.contracts import EvaluationLayer, EvaluationReport

__all__ = ["NOT_MEASURED", "evaluate_render", "pick_video_to_evaluate", "report_from_gate"]

# Quality dimensions Harness 9 cannot measure yet. They are reported as such, never scored.
NOT_MEASURED: Sequence[str] = (
    "factual grounding of the narration (needs claim-to-source verification)",
    "speech/caption alignment (needs forced alignment of the audio)",
    "editorial pacing and storytelling quality",
)


def pick_video_to_evaluate(videos: Iterable[Union[str, Path]]) -> Optional[Path]:
    """Prefer final.mp4, then any non-rejected video, then a rejected one (so the report can say why)."""
    paths = [Path(v) for v in videos]
    existing = [p for p in paths if p.exists()]
    if not existing:
        return None
    for p in existing:
        if p.name == "final.mp4":
            return p
    clean = [p for p in existing if ".rejected" not in p.name]
    return (clean or existing)[0]


def _ratio(report: MediaGateReport, key: str, invert: bool = False) -> Optional[float]:
    value = report.metrics.get(key)
    if not isinstance(value, (int, float)):
        return None
    value = min(1.0, max(0.0, float(value)))
    return round(1.0 - value if invert else value, 4)


def report_from_gate(
    gate_report: MediaGateReport,
    run_id: str,
    notes: Optional[List[str]] = None,
) -> EvaluationReport:
    """Translate a MediaGateReport into the EvaluationReport contract without inventing anything."""
    fail_checks = [c for c in gate_report.checks if c.severity == "fail"]
    passed_checks = [c for c in fail_checks if c.passed]
    media_checks_passed = round(len(passed_checks) / len(fail_checks), 4) if fail_checks else 0.0

    scores = {"media_checks_passed": media_checks_passed}
    for name, key, invert in (
        ("picture_not_flat", "flat_frame_ratio", True),
        ("picture_not_black", "black_ratio", True),
        ("picture_not_frozen", "frozen_ratio", True),
        ("picture_motion", "motion_ratio", False),
        ("audio_not_silent", "silence_ratio", True),
    ):
        value = _ratio(gate_report, key, invert)
        if value is not None:
            scores[name] = value

    feedback: List[str] = list(notes or [])
    feedback += [f"FAIL {c.name}: {c.message}" for c in gate_report.failed_checks()]
    feedback += [f"WARN {c.name}: {c.message}" for c in gate_report.warnings()]
    m = gate_report.metrics
    measured = []
    if "edge_density" in m:
        measured.append(f"edge density {m['edge_density']}")
    if "median_luma_range" in m:
        measured.append(f"median luma range {m['median_luma_range']:.0f}")
    if m.get("integrated_lufs") is not None:
        measured.append(f"loudness {m['integrated_lufs']} LUFS")
    if measured:
        feedback.append("Measured: " + ", ".join(measured) + ".")
    feedback.append("NOT MEASURED (not part of this score): " + "; ".join(NOT_MEASURED) + ".")

    return EvaluationReport(
        run_id=run_id,
        layer=EvaluationLayer.VIDEO,
        scores=scores,
        composite_score=media_checks_passed,
        passed=gate_report.passed,
        feedback=feedback,
    )


def evaluate_render(
    video_path: Optional[Union[str, Path]],
    run_id: Optional[str] = None,
    expected: Optional[ExpectedMedia] = None,
    gate: Optional[MediaGate] = None,
    notes: Optional[List[str]] = None,
) -> EvaluationReport:
    """Measure ``video_path`` and report. A missing video is a failed evaluation, never a pass."""
    rid = run_id or f"eval_{int(time.time())}"
    if video_path is None or not Path(video_path).exists():
        return EvaluationReport(
            run_id=rid,
            layer=EvaluationLayer.VIDEO,
            scores={},
            composite_score=0.0,
            passed=False,
            feedback=list(notes or []) + ["FAIL no rendered video was found, so nothing could be measured."],
        )
    exp = expected or ExpectedMedia(require_audio=True)
    try:
        gate_report = (gate or MediaGate()).evaluate(video_path, exp)
    except MediaGateUnavailable as exc:
        # Cannot measure => cannot pass. Report it instead of crashing the caller.
        return EvaluationReport(
            run_id=rid,
            layer=EvaluationLayer.VIDEO,
            scores={},
            composite_score=0.0,
            passed=False,
            feedback=list(notes or []) + [f"FAIL the video could not be measured: {exc}"],
        )
    return report_from_gate(gate_report, rid, notes=notes)
