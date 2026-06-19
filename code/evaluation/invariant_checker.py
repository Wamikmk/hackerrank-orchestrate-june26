"""
invariant_checker.py — Reusable checker for all 5 output invariants.

Given an output row dict (14 columns) plus optional perception + history,
returns a list of violation strings. Empty list = all invariants satisfied.

Used by:
  - main.py vertical-slice acceptance test
  - Module 7 evaluation harness
"""

from __future__ import annotations

_VALID_BOOL = {"true", "false"}


def check_invariants(
    row: dict,
    perception: dict | None = None,
    history=None,  # HistoryRecord | None — kept untyped to avoid import cycle
) -> list[str]:
    """
    Check all 5 invariants for a single output row.

    row       : dict keyed by the 14 output column names
    perception: optional perception dict — enables INV2 and INV3 checks
    history   : optional HistoryRecord — enables INV5 history-flag check

    Returns list of violation strings; empty list = clean.
    """
    violations: list[str] = []

    # ── Invariant 1: ATOMIC four-field consistency ───────────────────────────
    # not_enough_information ⟺ evidence_standard_met=false
    #                        ⟺ supporting_image_ids=none
    #                        ⟺ severity=unknown
    is_nei = row.get("claim_status") == "not_enough_information"
    is_esm_false = row.get("evidence_standard_met") == "false"
    is_sid_none = row.get("supporting_image_ids") == "none"
    is_sev_unknown = row.get("severity") == "unknown"
    four = [is_nei, is_esm_false, is_sid_none, is_sev_unknown]
    if not (all(four) or not any(four)):
        violations.append(
            "INV1: four-field atomicity broken — "
            f"claim_status={row.get('claim_status')!r}  "
            f"evidence_standard_met={row.get('evidence_standard_met')!r}  "
            f"supporting_image_ids={row.get('supporting_image_ids')!r}  "
            f"severity={row.get('severity')!r}"
        )

    # ── Invariant 2: claimed part NOT visible -> not_enough_information ──────
    if perception is not None:
        if (
            not perception.get("claimed_part_visible")
            and row.get("claim_status") != "not_enough_information"
        ):
            violations.append(
                f"INV2: claimed_part_visible=False but "
                f"claim_status={row.get('claim_status')!r} "
                f"(expected not_enough_information)"
            )

    # ── Invariant 3: part visible + issue absent -> contradicted ─────────────
    if perception is not None:
        part_vis = perception.get("claimed_part_visible", True)
        issue_pres = perception.get("claimed_issue_present", True)
        if part_vis and not issue_pres and row.get("claim_status") != "contradicted":
            violations.append(
                f"INV3: claimed_part_visible=True + claimed_issue_present=False "
                f"but claim_status={row.get('claim_status')!r} (expected contradicted)"
            )

    # ── Invariant 4: valid_image must be a valid boolean string ──────────────
    # Also confirms it is NOT derived from claim_status (value check only here;
    # coupling check is a policy unit test).
    if row.get("valid_image") not in _VALID_BOOL:
        violations.append(
            f"INV4: valid_image must be 'true' or 'false', "
            f"got {row.get('valid_image')!r}"
        )

    # ── Invariant 5: history flags must appear in risk_flags ─────────────────
    if history is not None and history.flags:
        rf = row.get("risk_flags", "none")
        risk_tokens = set(rf.split(";")) if rf and rf != "none" else set()
        for flag in history.flags:
            if flag not in risk_tokens:
                violations.append(
                    f"INV5: history flag {flag!r} missing from "
                    f"risk_flags={rf!r}"
                )

    return violations
