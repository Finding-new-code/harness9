import sys
import os
sys.path.insert(0, os.path.abspath("."))

from src.epistemic.script_verifier import ScriptVerifier
from src.epistemic.graph import EvidenceGraph
from src.models.contracts import ClaimRecord, SourceRecord, SourceTier

v = ScriptVerifier()
g = EvidenceGraph(graph_id='g')
src = SourceRecord(source_id='s1', title='t', url='u', tier=SourceTier.PRIMARY_SOURCE)
c = ClaimRecord(claim_id='c1', claim_text='Silicon transistors typically exhibit higher thermal stability.', confidence_score=0.85, primary_source=src)
g.add_claim(claim_text=c.claim_text, claim_id=c.claim_id, confidence_score=c.confidence_score, claim_record=c)

# Test 1: Contraction false-positive quote block
r1 = v.verify_script("It's clear that the company's product was innovative.", g)
print('Test 1 (Contractions):', r1.gate_recommendation, [d.drift_type for d in r1.drifts])

# Test 2: Level 2 -> Level 3 missed escalation
r2 = v.verify_script('Silicon transistors undeniably prove higher thermal stability.', g)
print('Test 2 (Modal Escalation):', r2.gate_recommendation, [d.drift_type for d in r2.drifts])

# Test 3: Substring 'factory' -> 'fact' false Level 3
exts = v.extract_sentences('The factory opened in June.')
print('Test 3 (Modal Level of factory):', exts[0].modal_level)

# Test 4: Duplicate drifts on fabricated quote
q = chr(34)
script4 = f"Feynman famously proclaimed: {q}We can easily shrink machines to the atomic scale!{q}"
r4 = v.verify_script(script4, g)
print('Test 4 (Drifts on fabricated quote):', [d.drift_type for d in r4.drifts])

# Test 5: 3 engineers vs 1948
c_bell = ClaimRecord(claim_id='c_bell', claim_text='Bell Labs produced 4,980 prototype units in 1948.', confidence_score=0.85, primary_source=src)
g.add_claim(claim_text=c_bell.claim_text, claim_id=c_bell.claim_id, confidence_score=c_bell.confidence_score, claim_record=c_bell)
r5 = v.verify_script("In 1948, 3 engineers at Bell Labs produced 4,980 prototype units.", g)
print('Test 5 (3 engineers):', r5.gate_recommendation, [(d.drift_type, d.explanation, d.recommended_edit) for d in r5.drifts])
