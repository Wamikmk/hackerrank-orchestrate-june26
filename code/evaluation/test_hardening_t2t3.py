"""
Hardening tests 2 and 3 — no real API calls.

Test 2: JSON retry + fallback via mock injection.
Test 3: INV1 gate on severity edge, both directions (hand-built dicts).
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import MagicMock, patch
import json

from pipeline.perception import call_perception, _FALLBACK_PERCEPTION, CONTRACT_KEYS
from pipeline.policy import run_policy
from pipeline.history import HistoryRecord


# ─────────────────────────────────────────────────────────────────────────────
# TEST 2 — JSON retry + fallback
# ─────────────────────────────────────────────────────────────────────────────

def test2_json_retry_and_fallback():
    print("\n" + "="*70)
    print("TEST 2 — JSON retry + fallback")
    print("="*70)

    malformed = '{"claimed_part_visible": true, "authenticity_flags": [non_original_image]}'
    print(f"\nInjected malformed JSON (unquoted array element):\n  {malformed}\n")

    attempt_log = []

    def fake_response():
        r = MagicMock()
        r.content = [MagicMock(text=malformed)]
        r.usage = MagicMock(
            input_tokens=100, output_tokens=10,
            cache_creation_input_tokens=0, cache_read_input_tokens=0
        )
        return r

    fake_client = MagicMock()
    fake_client.messages.create.side_effect = lambda **kw: (
        attempt_log.append(len(attempt_log) + 1) or fake_response()
    )

    # Also patch image loading so mock doesn't need real image bytes
    fake_b64 = ("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
                "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")
    with patch("pipeline.perception.anthropic.Anthropic", return_value=fake_client), \
         patch("pipeline.perception._load_image_b64", return_value=(fake_b64, "image/png")):
        result = call_perception(
            image_ids=["img_1"],
            image_paths=["images/test/case_005/img_1.jpg"],
            claim_object="car",
            user_claim="test claim",
            requirements=[],
        )

    print(f"(a) Retry attempts fired: {len(attempt_log)} (expected 3) — {'PASS' if len(attempt_log) == 3 else 'FAIL'}")
    print(f"    Attempt log: {attempt_log}")

    is_fallback = result.get("_fallback") is True
    print(f"\n(b) Fallback returned: {is_fallback} (expected True) — {'PASS' if is_fallback else 'FAIL'}")
    print(f"    _retries in result: {result.get('_retries')}")

    missing = CONTRACT_KEYS - set(result.keys())
    extra_keys = {"_fallback", "_retries"}
    has_all = len(missing) == 0
    print(f"\n(c) Fallback dict has ALL 11 contract keys: {has_all} — {'PASS' if has_all else 'FAIL'}")
    if missing:
        print(f"    MISSING keys: {missing}")
    print(f"\nFallback dict (excluding meta-keys):")
    for k, v in result.items():
        if k not in extra_keys:
            print(f"  {k}: {v!r}")

    # Pass fallback to policy — confirm no crash and INV1 holds
    dummy_row = {"claim_object": "car"}
    empty_history = HistoryRecord(flags=[], summary="")
    try:
        policy_out = run_policy(result, empty_history, dummy_row)
    except Exception as e:
        print(f"\n(c) CRITICAL: policy crashed on fallback dict: {e}")
        return

    claim_status = policy_out["claim_status"]
    severity = policy_out["severity"]
    evidence_std = policy_out["evidence_standard_met"]
    supporting = policy_out["supporting_image_ids"]

    # INV1: not_enough_information ⟺ evidence_standard_met=false ⟺ supporting_image_ids=none ⟺ severity=unknown
    inv1_holds = (
        claim_status == "not_enough_information"
        and evidence_std == "false"
        and supporting == "none"
        and severity == "unknown"
    )
    print(f"\n(c) Policy output from fallback:")
    print(f"  claim_status: {claim_status!r}")
    print(f"  evidence_standard_met: {evidence_std!r}")
    print(f"  supporting_image_ids: {supporting!r}")
    print(f"  severity: {severity!r}")
    print(f"  risk_flags: {policy_out['risk_flags']!r}")
    print(f"\n  INV1 holds (NEI ⟺ esm=false ⟺ supp=none ⟺ sev=unknown): {inv1_holds} — {'PASS' if inv1_holds else 'FAIL'}")

    return inv1_holds and is_fallback and has_all and len(attempt_log) == 3


# ─────────────────────────────────────────────────────────────────────────────
# TEST 3 — INV1 gate on severity edge, both directions
# ─────────────────────────────────────────────────────────────────────────────

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


def test3_inv1_gate():
    print("\n" + "="*70)
    print("TEST 3 — INV1 gate, both directions")
    print("="*70)

    empty_history = HistoryRecord(flags=[], summary="")
    dummy_row = {"claim_object": "car"}

    # ── 3(a): old bad perception output scenario ──────────────────────────────
    # claimed_part_visible=true, claimed_issue_present=false, observed_issue=none, observed_severity=unknown
    print("\n3(a): Part visible, issue absent, severity=unknown (old bad perception scenario)")
    p_a = _make_perception(
        claimed_part_visible=True,
        claimed_issue_present=False,
        observed_issue="none",
        observed_severity="unknown",  # policy should handle this gracefully
        image_assessments=[{"image_id": "img_1", "relevant": True, "note": "test"}],
    )
    out_a = run_policy(p_a, empty_history, dummy_row)

    cs_a = out_a["claim_status"]
    sev_a = out_a["severity"]
    esm_a = out_a["evidence_standard_met"]
    supp_a = out_a["supporting_image_ids"]

    # claim_status must be "contradicted" (part visible, issue absent)
    # INV1: NEI ⟺ esm=false. Since part IS visible, esm=true, cs != NEI.
    # INV1 just needs: if cs==NEI then esm=false,supp=none,sev=unknown. Here cs!=NEI.
    # The row must be internally consistent (no cross-invariant clash).
    inv1_a = not (cs_a == "not_enough_information" and (esm_a != "false" or supp_a != "none" or sev_a != "unknown"))

    print(f"  claim_status: {cs_a!r}  (expected 'contradicted')")
    print(f"  severity: {sev_a!r}     (policy passes through perception severity=unknown)")
    print(f"  evidence_standard_met: {esm_a!r}")
    print(f"  supporting_image_ids: {supp_a!r}")
    print(f"  INV1 consistent (no contradictory NEI state): {inv1_a} — {'PASS' if inv1_a else 'FAIL'}")
    print(f"  claim_status==contradicted: {cs_a == 'contradicted'} — {'PASS' if cs_a == 'contradicted' else 'FAIL'}")
    # Note: severity=unknown here because policy just echoes observed_severity from perception.
    # This is expected — policy doesn't override severity when part IS visible.

    # ── 3(b): genuine NEI (claimed_part_visible=false) ───────────────────────
    print("\n3(b): Part not visible — genuine not_enough_information")
    p_b = _make_perception(
        claimed_part_visible=False,
        claimed_issue_present=False,
        observed_issue="unknown",
        observed_severity="unknown",
    )
    out_b = run_policy(p_b, empty_history, dummy_row)

    cs_b = out_b["claim_status"]
    sev_b = out_b["severity"]
    esm_b = out_b["evidence_standard_met"]
    supp_b = out_b["supporting_image_ids"]

    inv1_b = (
        cs_b == "not_enough_information"
        and esm_b == "false"
        and supp_b == "none"
        and sev_b == "unknown"
    )

    print(f"  claim_status: {cs_b!r}  (expected 'not_enough_information')")
    print(f"  severity: {sev_b!r}     (expected 'unknown', NOT 'none')")
    print(f"  evidence_standard_met: {esm_b!r}  (expected 'false')")
    print(f"  supporting_image_ids: {supp_b!r}  (expected 'none')")
    print(f"  INV1 holds (all four fields consistent): {inv1_b} — {'PASS' if inv1_b else 'FAIL'}")

    return inv1_a and (cs_a == "contradicted") and inv1_b


if __name__ == "__main__":
    t2 = test2_json_retry_and_fallback()
    t3 = test3_inv1_gate()
    print("\n" + "="*70)
    print(f"SUMMARY: Test2={'PASS' if t2 else 'FAIL'}  Test3={'PASS' if t3 else 'FAIL'}")
    print("="*70)
