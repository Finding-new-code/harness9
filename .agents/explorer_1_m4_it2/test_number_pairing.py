import re
import math
from typing import List, Tuple, Optional

# Let's test the number pairing algorithm

def audit_numbers(
    s_numbers: List[Tuple[float, str, bool]],  # (val, tok, is_approx)
    e_numbers: List[Tuple[float, str, bool]],  # (val, tok, is_approx)
    sentence_text: str,
    tolerance_exact: float = 0.001,
    tolerance_approx: float = 0.05,
):
    drifts = []
    if not s_numbers or not e_numbers:
        return drifts

    matched_s_indices = set()
    matched_e_indices = set()

    # Pass 1: Match numbers that are identical or within tolerance
    for s_idx, (s_val, s_tok, is_approx) in enumerate(s_numbers):
        tol = tolerance_approx if is_approx else tolerance_exact
        best_e_idx = None
        best_err = float("inf")
        for e_idx, (e_val, e_tok, _) in enumerate(e_numbers):
            if e_idx in matched_e_indices:
                continue
            err = abs(s_val - e_val) / abs(e_val) if e_val != 0 else abs(s_val)
            if err <= tol and err < best_err:
                best_err = err
                best_e_idx = e_idx
        if best_e_idx is not None:
            matched_s_indices.add(s_idx)
            matched_e_indices.add(best_e_idx)

    # Pass 2: For remaining unmatched script numbers, pair with unmatched evidence numbers
    # only if they appear to be corresponding quantities (e.g. within 10x - 100x order of magnitude)
    unmatched_s = [i for i in range(len(s_numbers)) if i not in matched_s_indices]
    unmatched_e = [j for j in range(len(e_numbers)) if j not in matched_e_indices]

    for s_idx in unmatched_s:
        s_val, s_tok, is_approx = s_numbers[s_idx]
        if not unmatched_e:
            break

        # Find best unmatched evidence number by logarithmic distance
        best_e_idx = None
        best_log_diff = float("inf")
        for e_idx in unmatched_e:
            e_val, e_tok, _ = e_numbers[e_idx]
            if s_val > 0 and e_val > 0:
                ld = abs(math.log10(s_val) - math.log10(e_val))
            else:
                ld = abs(s_val - e_val)
            if ld < best_log_diff:
                best_log_diff = ld
                best_e_idx = e_idx

        # If log distance is too large (e.g., > 1.5, meaning > 30x difference) and there is a huge magnitude gap,
        # auxiliary counts like "3 engineers" vs "1948" (log diff 2.8) or "3" vs "50,000" (log diff 4.2)
        # should NOT be paired if best_log_diff >= 1.5 unless it's an intentional order of magnitude check
        # Specifically, order of magnitude 10x trap is between ~0.95 and ~1.2 (10x is log10(10)=1.0, 100x is 2.0).
        # But auxiliary counts (3 vs 1948) have log diff 2.81, or (3 vs 50000) 4.22!
        if best_e_idx is not None and best_log_diff < 1.5:
            e_val, e_tok, _ = e_numbers[best_e_idx]
            matched_e_indices.add(best_e_idx)
            matched_s_indices.add(s_idx)
            unmatched_e.remove(best_e_idx)

            err = abs(s_val - e_val) / abs(e_val) if e_val != 0 else abs(s_val)

            # Order of magnitude check: 10x trap (log diff in [0.99, 1.49])
            if s_val > 0 and e_val > 0 and 0.99 <= best_log_diff:
                rec_edit = re.sub(rf'\b{re.escape(s_tok)}\b', e_tok, sentence_text)
                drifts.append({
                    "drift_type": "altered_number",
                    "severity": "critical",
                    "explanation": f"Order-of-magnitude 10x trap: {s_tok} ({s_val}) vs {e_tok} ({e_val})",
                    "recommended_edit": rec_edit,
                })
                continue

            tol = tolerance_approx if is_approx else tolerance_exact
            if err > tol:
                severity = "high" if err > 0.10 else "medium"
                rec_edit = re.sub(rf'\b{re.escape(s_tok)}\b', e_tok, sentence_text)
                drifts.append({
                    "drift_type": "altered_number",
                    "severity": severity,
                    "explanation": f"Tolerance exceeded: {s_tok} ({s_val}) vs {e_tok} ({e_val}), err={err:.2%}",
                    "recommended_edit": rec_edit,
                })

    return drifts

# Case 1: Auxiliary count "3 engineers" with years and counts
s_nums = [(1948.0, "1948", False), (3.0, "3", False), (4980.0, "4,980", False)]
e_nums = [(4980.0, "4,980", False), (1948.0, "1948", False)]
text = "In 1948, 3 engineers at Bell Labs produced 4,980 prototype units."
drifts1 = audit_numbers(s_nums, e_nums, text)
print("Case 1 (3 engineers): drifts =", drifts1)
assert len(drifts1) == 0

# Case 2: 10x trap (500,000 vs 50,000)
s_nums2 = [(500000.0, "500,000", False)]
e_nums2 = [(50000.0, "50,000", False)]
text2 = "During the siege, over 500,000 soldiers perished in the battle."
drifts2 = audit_numbers(s_nums2, e_nums2, text2)
print("Case 2 (10x trap): drifts =", drifts2)
assert len(drifts2) == 1
assert drifts2[0]["severity"] == "critical"
assert "50,000" in drifts2[0]["recommended_edit"]

# Case 3: Approximate qualifier within tolerance
s_nums3 = [(5000.0, "5,000", True), (1948.0, "1948", False)]
e_nums3 = [(4980.0, "4,980", False), (1948.0, "1948", False)]
text3 = "Bell Labs produced approximately 5,000 units in 1948."
drifts3 = audit_numbers(s_nums3, e_nums3, text3)
print("Case 3 (approx within tol): drifts =", drifts3)
assert len(drifts3) == 0

# Case 4: Exact qualifier exceeding tolerance
s_nums4 = [(5000.0, "5,000", False), (1948.0, "1948", False)]
e_nums4 = [(4980.0, "4,980", False), (1948.0, "1948", False)]
text4 = "Bell Labs produced exactly 5,000 units in 1948."
drifts4 = audit_numbers(s_nums4, e_nums4, text4)
print("Case 4 (exact exceeding tol): drifts =", drifts4)
assert len(drifts4) == 1
assert drifts4[0]["severity"] == "medium"

print("ALL NUMBER AUDIT CASES PASSED!")
