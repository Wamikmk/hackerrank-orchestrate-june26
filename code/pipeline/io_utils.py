"""
io_utils.py — Module 1: CSV I/O and image path parsing.

Reads the four dataset CSVs, parses image_paths into image_ids,
and writes the 14-column output.csv in the exact order from CONTEXT.md.
"""

import csv
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_DIR = REPO_ROOT / "dataset"

OUTPUT_COLUMNS = [
    "user_id",
    "image_paths",
    "user_claim",
    "claim_object",
    "evidence_standard_met",
    "evidence_standard_met_reason",
    "risk_flags",
    "issue_type",
    "object_part",
    "claim_status",
    "claim_status_justification",
    "supporting_image_ids",
    "valid_image",
    "severity",
]


def _read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def parse_image_ids(image_paths_str: str) -> list[str]:
    """Split ';'-joined path string -> list of image_ids (filename no ext)."""
    paths = image_paths_str.strip().split(";")
    ids = []
    for p in paths:
        p = p.strip()
        if p:
            ids.append(Path(p).stem)
    return ids


def load_sample_claims() -> list[dict]:
    return _read_csv(DATASET_DIR / "sample_claims.csv")


def load_claims() -> list[dict]:
    return _read_csv(DATASET_DIR / "claims.csv")


def load_user_history() -> list[dict]:
    return _read_csv(DATASET_DIR / "user_history.csv")


def load_evidence_requirements() -> list[dict]:
    return _read_csv(DATASET_DIR / "evidence_requirements.csv")


def write_output(rows: list[dict], output_path: Path) -> None:
    """Write rows to output_path with the 14 required columns in exact order."""
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=OUTPUT_COLUMNS,
            extrasaction="ignore",
            quoting=csv.QUOTE_ALL,
        )
        writer.writeheader()
        writer.writerows(rows)


def read_output(output_path: Path) -> list[dict]:
    return _read_csv(output_path)
