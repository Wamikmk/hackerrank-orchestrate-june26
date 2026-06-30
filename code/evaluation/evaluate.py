"""
evaluate.py — Score output.csv against gold (sample_claims.csv).
Produces per-field accuracy, claim_status headline, per-row diff,
invariant check, and clustered-vs-scattered triage.

Outputs: prints report to stdout AND saves to evaluation/evaluation_report.md
"""

from __future__ import annotations
import csv
import sys
import os
from collections import defaultdict
from pathlib import Path

# Resolve paths relative to repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
GOLD_CSV = REPO_ROOT / "dataset" / "sample_claims.csv"
PRED_CSV = REPO_ROOT / "output.csv"
REPORT_MD = Path(__file__).resolve().parent / "evaluation_report.md"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluation.invariant_checker import check_invariants

# ── column lists ────────────────────────────────────────────────────────────
STRUCTURED_FIELDS = [
    "evidence_standard_met",
    "risk_flags",
    "issue_type",
    "object_part",
    "claim_status",
    "supporting_image_ids",
    "valid_image",
    "severity",
]
FREETEXT_FIELDS = [
    "evidence_standard_met_reason",
    "claim_status_justification",
]
ALL_OUTPUT_FIELDS = STRUCTURED_FIELDS + FREETEXT_FIELDS


def load_csv(path: Path) -> dict[str, dict]:
    """Return {user_id: row_dict}."""
    with open(path, newline="", encoding="utf-8") as f:
        return {r["user_id"]: r for r in csv.DictReader(f)}


def exact_match(pred: str, gold: str) -> bool:
    return pred.strip() == gold.strip()


def build_report(lines: list[str]) -> str:
    return "\n".join(lines)


def main():
    lines: list[str] = []
    w = lines.append  # shorthand

    # ── Load data ────────────────────────────────────────────────────────────
    gold = load_csv(GOLD_CSV)
    pred = load_csv(PRED_CSV)

    gold_ids = set(gold.keys())
    pred_ids = set(pred.keys())
    assert gold_ids == pred_ids, (
        f"user_id mismatch:\n  gold-only: {gold_ids - pred_ids}\n"
        f"  pred-only: {pred_ids - gold_ids}"
    )
    user_ids = sorted(gold_ids)  # stable order

    w("# Evaluation Report — Module 7")
    w("")
    w(f"Gold: `{GOLD_CSV.relative_to(REPO_ROOT)}`  ")
    w(f"Predictions: `{PRED_CSV.relative_to(REPO_ROOT)}`  ")
    w(f"Rows: {len(user_ids)}")
    w("")

    # ── Invariant check ──────────────────────────────────────────────────────
    w("## Invariant Check (INV1 + INV4)")
    w("")
    inv_violations: list[str] = []
    for uid in user_ids:
        viols = check_invariants(pred[uid])
        for v in viols:
            inv_violations.append(f"  {uid}: {v}")
    if inv_violations:
        w(f"**VIOLATIONS ({len(inv_violations)}):**")
        for v in inv_violations:
            w(v)
    else:
        w("**0 violations** — all 20 output rows pass INV1 and INV4.")
    w("")

    # ── Per-field structured accuracy ────────────────────────────────────────
    # Track per-field matches
    field_correct: dict[str, int] = defaultdict(int)
    field_total: dict[str, int] = defaultdict(int)

    # Per-row mismatches for the diff section
    # mismatch_map[uid] = list of (field, pred_val, gold_val)
    mismatch_map: dict[str, list[tuple[str, str, str]]] = defaultdict(list)

    # Per-field mismatch rows (for clustering analysis)
    field_miss_rows: dict[str, list[str]] = defaultdict(list)

    for uid in user_ids:
        g = gold[uid]
        p = pred[uid]
        for field in STRUCTURED_FIELDS:
            gv = g.get(field, "")
            pv = p.get(field, "")
            field_total[field] += 1
            if exact_match(pv, gv):
                field_correct[field] += 1
            else:
                mismatch_map[uid].append((field, pv, gv))
                field_miss_rows[field].append(uid)

    # ── Headline: claim_status ───────────────────────────────────────────────
    cs_correct = field_correct["claim_status"]
    cs_total = field_total["claim_status"]
    cs_classes = ["supported", "contradicted", "not_enough_information"]
    # confusion: true_class -> {pred_class: count}
    confusion: dict[str, dict[str, int]] = {c: defaultdict(int) for c in cs_classes}
    for uid in user_ids:
        true_cls = gold[uid]["claim_status"]
        pred_cls = pred[uid]["claim_status"]
        if true_cls not in confusion:
            confusion[true_cls] = defaultdict(int)
        confusion[true_cls][pred_cls] += 1

    w("## Headline Metric: `claim_status` Accuracy")
    w("")
    w(f"**{cs_correct}/{cs_total} correct** ({cs_correct/cs_total*100:.1f}%)")
    w("")
    w("### Confusion Matrix (rows = gold, cols = predicted)")
    w("")
    all_pred_classes = sorted({pred[u]["claim_status"] for u in user_ids})
    header_cols = ["gold \\ predicted"] + all_pred_classes + ["total"]
    w("| " + " | ".join(header_cols) + " |")
    w("| " + " | ".join(["---"] * len(header_cols)) + " |")
    for true_cls in cs_classes:
        if true_cls not in confusion:
            continue
        row_counts = [confusion[true_cls].get(pc, 0) for pc in all_pred_classes]
        total = sum(row_counts)
        if total == 0:
            continue
        w("| " + " | ".join([true_cls] + [str(c) for c in row_counts] + [str(total)]) + " |")
    w("")

    # ── Per-field accuracy table ─────────────────────────────────────────────
    w("## Per-Field Accuracy (Structured Fields)")
    w("")
    w("| Field | Correct | Total | Accuracy |")
    w("| ----- | ------- | ----- | -------- |")
    for field in STRUCTURED_FIELDS:
        c = field_correct[field]
        t = field_total[field]
        pct = c / t * 100 if t else 0
        note = " **← headline**" if field == "claim_status" else ""
        w(f"| {field} | {c} | {t} | {pct:.1f}%{note} |")
    w("")

    # ── Free-text fields: presence + length ─────────────────────────────────
    w("## Free-Text Fields (Presence & Length)")
    w("")
    w("Exact-match excluded from headline. Reporting non-empty and character count.")
    w("")
    w("| user_id | field | pred_len | gold_len | pred_empty | gold_empty |")
    w("| ------- | ----- | -------- | -------- | ---------- | ---------- |")
    for uid in user_ids:
        for field in FREETEXT_FIELDS:
            gv = gold[uid].get(field, "")
            pv = pred[uid].get(field, "")
            w(f"| {uid} | {field} | {len(pv)} | {len(gv)} | "
              f"{'yes' if not pv else 'no'} | {'yes' if not gv else 'no'} |")
    w("")

    # ── Per-row diff ─────────────────────────────────────────────────────────
    w("## Per-Row Diff (Structured Field Mismatches)")
    w("")
    mismatch_row_count = sum(1 for mm in mismatch_map.values() if mm)
    w(f"{mismatch_row_count} rows have at least one structured-field mismatch.")
    w("")

    for uid in user_ids:
        mm = mismatch_map.get(uid, [])
        if not mm:
            continue
        w(f"### {uid}")
        w("")
        w("| Field | Predicted | Gold |")
        w("| ----- | --------- | ---- |")
        for field, pv, gv in mm:
            w(f"| {field} | `{pv}` | `{gv}` |")
        w("")

    # ── Clustered vs scattered triage ────────────────────────────────────────
    CLUSTER_THRESHOLD = 3
    w("## Triage: Clustered vs Scattered Mismatches")
    w("")
    w(f"Threshold: ≥{CLUSTER_THRESHOLD} misses on the same field = **clustered (investigate)**; "
      f"fewer = **scattered (noise)**.")
    w("")
    w("| Field | Miss Count | Verdict | Affected Rows |")
    w("| ----- | ---------- | ------- | ------------- |")
    for field in STRUCTURED_FIELDS:
        miss_rows = field_miss_rows.get(field, [])
        n = len(miss_rows)
        verdict = f"**clustered (investigate)**" if n >= CLUSTER_THRESHOLD else "scattered (noise)"
        affected = ";".join(miss_rows) if miss_rows else "—"
        w(f"| {field} | {n} | {verdict} | {affected} |")
    w("")

    # ── Summary ──────────────────────────────────────────────────────────────
    w("## Summary")
    w("")
    total_structured = sum(field_total[f] for f in STRUCTURED_FIELDS)
    total_correct_structured = sum(field_correct[f] for f in STRUCTURED_FIELDS)
    w(f"- **Overall structured accuracy**: {total_correct_structured}/{total_structured} "
      f"({total_correct_structured/total_structured*100:.1f}%)")
    w(f"- **claim_status (headline)**: {cs_correct}/{cs_total} "
      f"({cs_correct/cs_total*100:.1f}%)")
    w(f"- **Invariant violations**: {len(inv_violations)}")
    clustered_fields = [f for f in STRUCTURED_FIELDS
                        if len(field_miss_rows.get(f, [])) >= CLUSTER_THRESHOLD]
    if clustered_fields:
        w(f"- **Clustered fields needing investigation**: {', '.join(clustered_fields)}")
    else:
        w("- **Clustered fields**: none — all mismatches are scattered noise")
    w("")

    # ── Write and print ──────────────────────────────────────────────────────
    report = build_report(lines)
    REPORT_MD.write_text(report, encoding="utf-8")
    print(report)
    print(f"\n[Saved to {REPORT_MD}]")


if __name__ == "__main__":
    main()
