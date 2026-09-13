"""Adversarial and Forensic Stress Testing for Milestone M1."""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import unittest
import tempfile

from src.orchestrator.state_machine import (
    ProductionState,
    ProductionStateMachine,
    StateTransitionError,
    TransitionRecord,
)
from src.models.contracts import (
    CreatorProfile,
    ContentBrief,
    ResearchPlan,
    SourceRecord,
    ClaimRecord,
    EditorialScorecard,
    EditorialAngle,
    AnalyticsSnapshot,
    Script,
    RenderArtifact,
    PublishPackage,
)
from adapters.hermes.sandbox import HermesSessionSandbox
from adapters.hermes.tools import handle_tool_call
from pydantic import ValidationError

def run_stress_tests():
    print("=== ADVERSARIAL STRESS TESTING (AUDITOR M1) ===")

    # 1. State machine jump rejection
    sm = ProductionStateMachine(run_id="adv_01")
    for bad_state in [ProductionState.COMPLETED, ProductionState.RENDER_COMPLETED, ProductionState.VOICE_GENERATED]:
        assert not sm.can_transition(bad_state), f"Should not transition to {bad_state}"
        try:
            sm.transition_to(bad_state)
            assert False, f"Failed to block transition to {bad_state}"
        except StateTransitionError:
            pass
    print("[PASS] State machine jump rejections confirmed")

    # 2. State machine gibberish state
    try:
        sm.transition_to("UNKNOWN_GIBBERISH_STATE")
        assert False, "Failed to block unknown state string"
    except StateTransitionError:
        pass
    print("[PASS] Unknown state rejection confirmed")

    # 3. State machine serialization roundtrip
    sm.transition_to(ProductionState.RESEARCH_PLANNED, payload={"data": "test"})
    sm_json = sm.to_json()
    sm_restored = ProductionStateMachine.from_json(sm_json)
    assert sm_restored.current_state == ProductionState.RESEARCH_PLANNED
    assert len(sm_restored.history) == 1
    assert sm_restored.history[0].payload_summary == {"data": "test"}
    print("[PASS] State machine JSON roundtrip verified")

    # 4. Contracts validation constraints
    try:
        CreatorProfile(creator_id="c1", display_name="C1", default_format="4:3")
        assert False, "Failed to reject invalid aspect ratio"
    except ValidationError:
        pass

    try:
        ContentBrief(project_id="p1", topic="T", target_duration_seconds=1)
        assert False, "Failed to reject duration < 5"
    except ValidationError:
        pass

    try:
        ContentBrief(project_id="p1", topic="T", target_duration_seconds=1000)
        assert False, "Failed to reject duration > 600"
    except ValidationError:
        pass

    try:
        SourceRecord(title="S", url="http://x.com", reliability_score=1.5)
        assert False, "Failed to reject reliability > 1.0"
    except ValidationError:
        pass

    try:
        AnalyticsSnapshot(project_id="p1", average_watch_percentage=150.0)
        assert False, "Failed to reject watch pct > 100"
    except ValidationError:
        pass
    print("[PASS] Schema boundary and regex constraints verified")

    # 5. Scorecard auto-computation
    sc = EditorialScorecard(
        audience_relevance=1.0,
        novelty=1.0,
        hook_potential=1.0,
        narrative_potential=1.0,
        creator_fit=1.0,
        evidence_availability=1.0,
        visual_potential=1.0,
        platform_fit=1.0,
        saturation_risk=0.0,
    )
    assert sc.composite_score == 1.0, f"Expected 1.0, got {sc.composite_score}"
    print("[PASS] EditorialScorecard composite score auto-calculation verified")

    # 6. Hermes sandbox path traversal security
    with tempfile.TemporaryDirectory() as td:
        sandbox = HermesSessionSandbox(session_id="sec_test", base_dir=td)
        try:
            sandbox.validate_path(Path(td) / ".." / "escape.txt")
            assert False, "Failed to block path traversal"
        except ValueError:
            pass
        
        # Valid inside
        in_path = sandbox.get_workspace_dir() / "valid.txt"
        assert sandbox.validate_path(in_path) == in_path.resolve()
    print("[PASS] HermesSessionSandbox path traversal guards verified")

    # 7. Tool dispatcher unknown tool handling
    res = handle_tool_call(tool_name="malicious_tool", arguments={}, session_id="s1")
    assert not res["success"]
    assert "Unknown tool" in res["error"]
    print("[PASS] Hermes tool dispatcher unknown tool rejection verified")

    print("\n>>> ALL ADVERSARIAL STRESS CHECKS EMPIRICALLY CONFIRMED AND PASSED! <<<")

if __name__ == "__main__":
    run_stress_tests()
