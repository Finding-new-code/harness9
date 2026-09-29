import sys
import os
sys.path.insert(0, os.path.abspath("."))

from src.epistemic.script_verifier import ScriptVerifier
from src.epistemic.graph import EvidenceGraph
from src.models.contracts import ClaimRecord, ClaimType, ConsensusState, EpistemicStatus, SourceRecord, SourceTier

sample_source = SourceRecord(
    source_id="src_feynman_01",
    title="Plenty of Room at the Bottom",
    url="https://caltech.edu/feynman/room.html",
    tier=SourceTier.PRIMARY_SOURCE,
)
graph = EvidenceGraph(graph_id="g_test_script")
c5 = ClaimRecord(
    claim_id="claim_feynman_quote",
    claim_text="There is plenty of room at the bottom.",
    claim_type=ClaimType.DIRECT_QUOTE,
    epistemic_status=EpistemicStatus.VERIFIED,
    consensus_state=ConsensusState.STRONG_CONSENSUS,
    confidence_score=1.0,
    primary_source=sample_source,
)
graph.add_claim(
    claim_text=c5.claim_text,
    claim_id=c5.claim_id,
    epistemic_status=c5.epistemic_status.value,
    consensus_state=c5.consensus_state.value,
    confidence_score=c5.confidence_score,
    claim_record=c5,
)

v = ScriptVerifier()
q = chr(34)
script = f"Feynman said: {q}There is barely any room at the bottom.{q}"
report = v.verify_script(script, graph)
quote_drifts = [d for d in report.drifts if d.drift_type.value == "fabricated_quote"]
print("Number of fabricated quote drifts on grounded sentence:", len(quote_drifts))

# Also test compound growth duplication
c_fin = ClaimRecord(
    claim_id="claim_finance",
    claim_text="Revenue grew from 10 million to 30 million over five years.",
    confidence_score=0.9,
    primary_source=sample_source,
)
graph.add_claim(
    claim_text=c_fin.claim_text,
    claim_id=c_fin.claim_id,
    claim_record=c_fin,
)
script_math = "Revenue grew from 10 million to 30 million, a 300% increase."
report_math = v.verify_script(script_math, graph)
math_drifts = [d for d in report_math.drifts if "calculation error" in d.explanation.lower()]
print("Number of compound growth calculation error drifts:", len(math_drifts))
