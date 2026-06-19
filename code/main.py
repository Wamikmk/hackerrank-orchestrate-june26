"""
main.py — Module 6: Full pipeline wire-up.

Usage:
  python main.py [csv_path]

  csv_path defaults to dataset/sample_claims.csv.
  Output is always written to output.csv at the repo root.

After writing output.csv, runs the invariant checker over all rows and prints
a per-row violation summary.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE_DIR))

from pipeline.history import HistoryLookup
from pipeline.io_utils import OUTPUT_COLUMNS, parse_image_ids, write_output
from pipeline.perception import call_perception
from pipeline.policy import run_policy
from pipeline.requirements import RequirementsLookup
from evaluation.invariant_checker import check_invariants

OUTPUT_PATH = REPO_ROOT / "output.csv"


def _load_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def process_csv(csv_path: Path) -> list[dict]:
    """Run full pipeline over csv_path; return output rows (also written to OUTPUT_PATH)."""
    rows = _load_csv(csv_path)
    history_lookup = HistoryLookup()
    requirements_lookup = RequirementsLookup()

    perceptions: list[dict] = []
    histories = []
    output_rows: list[dict] = []

    for row in rows:
        image_ids = parse_image_ids(row["image_paths"])
        requirements = requirements_lookup.get(row["claim_object"], len(image_ids))
        history = history_lookup.get(row["user_id"])
        perception = call_perception(
            image_ids, row["claim_object"], row["user_claim"], requirements
        )
        policy_out = run_policy(perception, history, row)

        output_rows.append(
            {
                "user_id": row["user_id"],
                "image_paths": row["image_paths"],
                "user_claim": row["user_claim"],
                "claim_object": row["claim_object"],
                **policy_out,
            }
        )
        perceptions.append(perception)
        histories.append(history)

    write_output(output_rows, OUTPUT_PATH)
    print(f"Wrote {len(output_rows)} rows to {OUTPUT_PATH}")

    # ── Acceptance check ─────────────────────────────────────────────────────
    # Verify column order matches CONTEXT.md spec.
    with open(OUTPUT_PATH, encoding="utf-8", newline="") as f:
        actual_cols = next(csv.reader(f))
    if actual_cols != OUTPUT_COLUMNS:
        print(f"COLUMN MISMATCH:\n  expected: {OUTPUT_COLUMNS}\n  got:      {actual_cols}")
    else:
        print(f"Columns: {len(actual_cols)} in correct order ✓")

    # ── Invariant check ──────────────────────────────────────────────────────
    total_violations = 0
    for i, (out_row, perc, hist) in enumerate(zip(output_rows, perceptions, histories)):
        viols = check_invariants(out_row, perception=perc, history=hist)
        if viols:
            total_violations += len(viols)
            print(f"  row {i:02d} ({out_row['user_id']}): {len(viols)} violation(s)")
            for v in viols:
                print(f"    {v}")
        else:
            print(f"  row {i:02d} ({out_row['user_id']}): 0 violations")

    print(f"Total invariant violations: {total_violations}")

    # ── Sample rows ──────────────────────────────────────────────────────────
    # Pick row 0 (car, 1 image), row 1 (car, 2 images), row 8 (laptop), row 14 (package)
    sample_indices = [0, 1, 8, 14]
    print("\n── Sample output rows (all 14 fields) ──")
    for i in sample_indices:
        if i < len(output_rows):
            r = output_rows[i]
            print(f"\n[row {i}]")
            for col in OUTPUT_COLUMNS:
                print(f"  {col}: {r.get(col, '')!r}")

    return output_rows


if __name__ == "__main__":
    csv_path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else REPO_ROOT / "dataset" / "sample_claims.csv"
    )
    process_csv(csv_path)
