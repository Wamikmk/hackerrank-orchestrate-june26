"""
test_inv1_gate.py — Verify the INV1 atomic severity gate in policy.py (D18/D19).

Three unit tests:
  1. Original bug: contradicted + severity=unknown → now severity=none, INV1 clean
  2. Low-floor branch: supported + real damage + severity=unknown → severity=low
  3. NEI unchanged: part not visible → severity=unknown survives, INV1 clean
"""
from __future__ import annotations

import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE_DIR))

from pipeline.policy import run_policy
from pipeline.history import HistoryRecord
from evaluation.invariant_checker import check_invariants

_NO_HISTORY = HistoryRecord(flags=[], summary="")
_ROW = {"claim_object": "car"}

PASS_COUNT = 0
FAIL_COUNT = 0


def check(label: str, cond: bool, detail: str = ""):
    global PASS_COUNT, FAIL_COUNT
    status = "PASS" if cond else "FAIL"
    if cond:
        PASS_COUNT += 1
    else:
        FAIL_COUNT += 1
    print(f"  {status}  {label}")
    if detail:
        print(f"        {detail}")
    if not cond:
        print(f"  ^^^ ASSERTION FAILED ^^^")


def _make_perception(
    claimed_part_visible: bool,
    claimed_issue_present: bool,
    observed_issue: str,
    observed_severity: str,
    image_assessments=None,
) -> dict:
    return {
        "claimed_part_visible": claimed_part_visible,
        "observed_part": "door" if claimed_part_visible else "unknown",
        "claimed_issue_present": claimed_issue_present,
        "observed_issue": observed_issue,
        "observed_severity": observed_severity,
        "claimed_issue_family": "dent",
        "image_assessments": image_assessments or [],
        "quality_flags": [],
        "authenticity_flags": [],
        "text_instruction_present": False,
        "observation_note": "Test observation.",
    }


print("=" * 70)
print("TEST 1 — Original bug: contradicted + severity=unknown from perception")
print("  Input: claimed_part_visible=true, claimed_issue_present=false,")
print("         observed_issue=none, observed_severity=unknown")
print("  Expected: claim_status=contradicted, severity=none (NOT unknown), INV1 clean")
print("=" * 70)

p1 = _make_perception(
    claimed_part_visible=True,
    claimed_issue_present=False,
    observed_issue="none",
    observed_severity="unknown",
    image_assessments=[{"image_id": "img_1", "relevant": True, "note": "Part visible, no damage"}],
)
out1 = run_policy(p1, _NO_HISTORY, _ROW)
viols1 = check_invariants(out1, perception=p1)

print(f"\n  policy output:")
print(f"    claim_status:         {out1['claim_status']!r}")
print(f"    severity:             {out1['severity']!r}")
print(f"    evidence_standard_met:{out1['evidence_standard_met']!r}")
print(f"    supporting_image_ids: {out1['supporting_image_ids']!r}")
print(f"  invariant violations:   {viols1}")
print()

check("claim_status == 'contradicted'", out1["claim_status"] == "contradicted",
      f"got {out1['claim_status']!r}")
check("severity == 'none' (NOT 'unknown')", out1["severity"] == "none",
      f"got {out1['severity']!r}")
check("evidence_standard_met == 'true'", out1["evidence_standard_met"] == "true")
check("INV1 clean (checker returns 0 violations)", len(viols1) == 0,
      f"violations: {viols1}")


print()
print("=" * 70)
print("TEST 2 — Low-floor branch: supported + real damage issue + severity=unknown")
print("  Input: claimed_part_visible=true, claimed_issue_present=true,")
print("         observed_issue=dent, observed_severity=unknown")
print("  Expected: claim_status=supported, severity=low (D19 floor), INV1 clean")
print("=" * 70)

p2 = _make_perception(
    claimed_part_visible=True,
    claimed_issue_present=True,
    observed_issue="dent",
    observed_severity="unknown",
    image_assessments=[{"image_id": "img_1", "relevant": True, "note": "Dent visible but unrateable"}],
)
out2 = run_policy(p2, _NO_HISTORY, _ROW)
viols2 = check_invariants(out2, perception=p2)

print(f"\n  policy output:")
print(f"    claim_status:         {out2['claim_status']!r}")
print(f"    severity:             {out2['severity']!r}")
print(f"    evidence_standard_met:{out2['evidence_standard_met']!r}")
print(f"    supporting_image_ids: {out2['supporting_image_ids']!r}")
print(f"  invariant violations:   {viols2}")
print()

check("claim_status == 'supported'", out2["claim_status"] == "supported",
      f"got {out2['claim_status']!r}")
check("severity == 'low' (D19 floor, not unknown)", out2["severity"] == "low",
      f"got {out2['severity']!r}")
check("INV1 clean", len(viols2) == 0, f"violations: {viols2}")


print()
print("=" * 70)
print("TEST 3 — NEI unchanged: part not visible → severity=unknown survives")
print("  Input: claimed_part_visible=false")
print("  Expected: claim_status=not_enough_information, severity=unknown (NOT none), INV1 clean")
print("=" * 70)

p3 = _make_perception(
    claimed_part_visible=False,
    claimed_issue_present=False,
    observed_issue="unknown",
    observed_severity="unknown",
    image_assessments=[{"image_id": "img_1", "relevant": False, "note": "Part not visible"}],
)
out3 = run_policy(p3, _NO_HISTORY, _ROW)
viols3 = check_invariants(out3, perception=p3)

print(f"\n  policy output:")
print(f"    claim_status:         {out3['claim_status']!r}")
print(f"    severity:             {out3['severity']!r}")
print(f"    evidence_standard_met:{out3['evidence_standard_met']!r}")
print(f"    supporting_image_ids: {out3['supporting_image_ids']!r}")
print(f"  invariant violations:   {viols3}")
print()

check("claim_status == 'not_enough_information'",
      out3["claim_status"] == "not_enough_information",
      f"got {out3['claim_status']!r}")
check("severity == 'unknown' (NOT forced to 'none' — NEI path untouched)",
      out3["severity"] == "unknown",
      f"got {out3['severity']!r}")
check("evidence_standard_met == 'false'", out3["evidence_standard_met"] == "false")
check("supporting_image_ids == 'none'", out3["supporting_image_ids"] == "none")
check("INV1 clean (all four fields consistent)", len(viols3) == 0,
      f"violations: {viols3}")


print()
print("=" * 70)
print(f"TOTAL: {PASS_COUNT + FAIL_COUNT} checks | {PASS_COUNT} passed | {FAIL_COUNT} failed")
print("=" * 70)

if FAIL_COUNT > 0:
    sys.exit(1)
