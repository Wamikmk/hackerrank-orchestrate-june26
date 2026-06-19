"""
policy.py — Module 5: Deterministic policy layer.

Maps perception JSON + history record -> the 10 output fields.
Zero model calls. Enforces all 5 invariants from PLAN.md / CONTEXT.md.

Decision hierarchy:
  1. Images are truth (perception drives everything).
  2. Claim text defines WHAT to check.
  3. History adds risk context only — never flips claim_status.
"""

from __future__ import annotations

from pipeline.history import HistoryRecord


def run_policy(perception: dict, history: HistoryRecord, row: dict) -> dict:
    """
    Map perception + history -> the 10 output-only fields.

    perception : dict matching the LOCKED contract in CONTEXT.md
    history    : HistoryRecord from HistoryLookup.get()
    row        : raw CSV row dict (claim_object used in justification text)
    Returns dict with exactly the 10 output columns.
    """
    claimed_part_visible: bool = bool(perception["claimed_part_visible"])
    claimed_issue_present: bool = bool(perception["claimed_issue_present"])
    observed_part: str = perception["observed_part"]
    observed_issue: str = perception["observed_issue"]
    observed_severity: str = perception["observed_severity"]
    image_assessments: list[dict] = perception["image_assessments"]
    quality_flags: list[str] = list(perception["quality_flags"])
    authenticity_flags: list[str] = list(perception["authenticity_flags"])
    text_instruction_present: bool = bool(perception["text_instruction_present"])
    observation_note: str = perception["observation_note"]
    claim_object: str = row.get("claim_object", "object")

    # ── Invariant 4: valid_image is INDEPENDENT of verdict ──────────────────
    # Driven only by authenticity_flags. Never coupled to claim_status.
    valid_image: str = "false" if authenticity_flags else "true"

    # ── risk_flags: quality + text_instruction + history (Invariant 5) ──────
    raw_risk: list[str] = list(quality_flags)
    if text_instruction_present:
        raw_risk.append("text_instruction_present")
    raw_risk.extend(history.flags)  # INV5: history flags pass through
    risk_flags: str = ";".join(raw_risk) if raw_risk else "none"

    # ── ATOMIC gate (Invariants 1 + 2) ──────────────────────────────────────
    # If claimed part not visible: set ALL FOUR fields as one coupled decision.
    # No other code path may set any of these four in isolation.
    if not claimed_part_visible:
        evidence_standard_met = "false"
        supporting_image_ids = "none"
        severity = "unknown"
        claim_status = "not_enough_information"
        evidence_standard_met_reason = (
            f"The claimed {claim_object} part is not visible in any submitted image."
        )
        base_just = (
            f"The submitted images do not show the claimed {claim_object} part, "
            f"so there is insufficient evidence to assess the damage."
        )
        claim_status_justification = _with_history(base_just, history)

    else:
        # Part IS visible — evidence standard met.
        evidence_standard_met = "true"
        relevant_ids = [a["image_id"] for a in image_assessments if a.get("relevant")]
        supporting_image_ids = ";".join(relevant_ids) if relevant_ids else "none"
        severity = observed_severity
        evidence_standard_met_reason = observation_note  # VLM's visual description

        # ── Invariant 3: part visible + issue absent -> contradicted ─────────
        if not claimed_issue_present:
            claim_status = "contradicted"
        else:
            claim_status = "supported"

        claim_status_justification = _with_history(observation_note, history)

    return {
        "evidence_standard_met": evidence_standard_met,
        "evidence_standard_met_reason": evidence_standard_met_reason,
        "risk_flags": risk_flags,
        "issue_type": observed_issue,
        "object_part": observed_part,
        "claim_status": claim_status,
        "claim_status_justification": claim_status_justification,
        "supporting_image_ids": supporting_image_ids,
        "valid_image": valid_image,
        "severity": severity,
    }


def _with_history(base: str, history: HistoryRecord) -> str:
    """Append history summary as a secondary clause when flags are present (INV5)."""
    if not history.flags:
        return base
    clause = history.summary if history.summary else "User history also adds a risk signal."
    return base.rstrip(".") + ". " + clause
