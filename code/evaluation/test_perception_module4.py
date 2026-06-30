"""
test_perception_module4.py — Module 4 acceptance test.

Tests 4 cases:
  Case A: sample row 0  (user_001, case_001, 1 image, gold: supported/dent/rear_bumper)
  Case B: sample row 7  (user_008, case_008, 1 image, gold: contradicted/broken_part/front_bumper)
  Case C: test 2-image  (user_004, case_004) — structural only, no gold
  Case D: test 3-image  (user_002, case_001) — structural only; confirm 3 image_assessments

Writes full results (raw JSON + contract checks + token usage) to
  evaluation/test_perception_module4_results.txt
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Allow running from repo root or code/ directory
CODE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE_DIR))

from dotenv import load_dotenv
load_dotenv(CODE_DIR / ".env")

from pipeline.io_utils import load_sample_claims, load_claims, parse_image_ids, DATASET_DIR
from pipeline.requirements import RequirementsLookup
from pipeline.perception import call_perception, CONTRACT_KEYS, MODEL

RESULTS_PATH = CODE_DIR / "evaluation" / "test_perception_module4_results.txt"

# ── Allowed enum sets for contract validation ─────────────────────────────────

ALLOWED_ISSUE_TYPES = {
    "dent", "scratch", "crack", "glass_shatter", "broken_part", "missing_part",
    "torn_packaging", "crushed_packaging", "water_damage", "stain", "none", "unknown",
}
ALLOWED_SEVERITY = {"none", "low", "medium", "high", "unknown"}
ALLOWED_QUALITY_FLAGS = {
    "blurry_image", "cropped_or_obstructed", "low_light_or_glare",
    "wrong_angle", "wrong_object", "wrong_object_part", "damage_not_visible",
}
ALLOWED_AUTHENTICITY_FLAGS = {"possible_manipulation", "non_original_image"}
OBJECT_PARTS = {
    "car": {"front_bumper", "rear_bumper", "door", "hood", "windshield", "side_mirror",
             "headlight", "taillight", "fender", "quarter_panel", "body", "unknown"},
    "laptop": {"screen", "keyboard", "trackpad", "hinge", "lid", "corner",
               "port", "base", "body", "unknown"},
    "package": {"box", "package_corner", "package_side", "seal", "label",
                "contents", "item", "unknown"},
}


def validate_contract(result: dict, image_ids: list[str], claim_object: str) -> list[str]:
    """Return list of contract violations. Empty = valid."""
    errs = []
    # 1. All 11 keys present
    actual_keys = set(result.keys()) - {"_usage"}
    missing = CONTRACT_KEYS - actual_keys
    extra = actual_keys - CONTRACT_KEYS
    if missing:
        errs.append(f"MISSING KEYS: {sorted(missing)}")
    if extra:
        errs.append(f"EXTRA KEYS (unexpected): {sorted(extra)}")

    # 2. image_assessments count
    assessments = result.get("image_assessments", [])
    if len(assessments) != len(image_ids):
        errs.append(
            f"image_assessments count={len(assessments)} but expected {len(image_ids)}"
        )
    for a in assessments:
        if a.get("image_id") not in image_ids:
            errs.append(f"image_assessment has unknown image_id={a.get('image_id')!r}")

    # 3. Enum fields
    observed_issue = result.get("observed_issue", "")
    if observed_issue not in ALLOWED_ISSUE_TYPES:
        errs.append(f"observed_issue={observed_issue!r} not in allowed set")

    observed_severity = result.get("observed_severity", "")
    if observed_severity not in ALLOWED_SEVERITY:
        errs.append(f"observed_severity={observed_severity!r} not in allowed set")

    allowed_parts = OBJECT_PARTS.get(claim_object, set())
    observed_part = result.get("observed_part", "")
    if observed_part not in allowed_parts:
        errs.append(f"observed_part={observed_part!r} not in allowed set for {claim_object!r}")

    for flag in result.get("quality_flags", []):
        if flag not in ALLOWED_QUALITY_FLAGS:
            errs.append(f"quality_flag={flag!r} not in allowed set")

    for flag in result.get("authenticity_flags", []):
        if flag not in ALLOWED_AUTHENTICITY_FLAGS:
            errs.append(f"authenticity_flag={flag!r} not in allowed set")

    # 4. Bool fields
    for bfield in ("claimed_part_visible", "claimed_issue_present", "text_instruction_present"):
        if not isinstance(result.get(bfield), bool):
            errs.append(f"{bfield}={result.get(bfield)!r} is not a Python bool")

    return errs


# ── Gold observations from Module 5 (test_policy_module5.py authored fields) ─

GOLD_OBS = {
    "row_0": {
        "observed_part": "rear_bumper",
        "observed_issue": "dent",
        "authenticity_flags": [],
        "text_instruction_present": False,
    },
    "row_7": {
        "observed_part": "front_bumper",
        "observed_issue": "broken_part",
        "authenticity_flags": ["non_original_image"],
        "text_instruction_present": False,
    },
}


def compare_gold(result: dict, gold: dict) -> list[str]:
    """Return comparison lines (MATCH / DISAGREE) for the 4 observed fields."""
    lines = []
    for field, gold_val in gold.items():
        actual = result.get(field)
        tag = "MATCH    " if actual == gold_val else "DISAGREE "
        lines.append(f"  {tag} {field}: perception={actual!r}  gold={gold_val!r}")
    return lines


# ── Helpers ───────────────────────────────────────────────────────────────────

def run_case(
    label: str,
    row: dict,
    reqs_lookup: RequirementsLookup,
    gold_key: str | None = None,
) -> tuple[dict | None, list[str]]:
    """Run perception on one row. Returns (result, log_lines). result=None on error."""
    image_ids = parse_image_ids(row["image_paths"])
    image_paths = [p.strip() for p in row["image_paths"].split(";") if p.strip()]
    requirements = reqs_lookup.get(row["claim_object"], len(image_ids))

    lines = []
    lines.append(f"\n{'='*72}")
    lines.append(f"CASE: {label}")
    lines.append(f"  user_id:      {row['user_id']}")
    lines.append(f"  image_paths:  {row['image_paths']}")
    lines.append(f"  claim_object: {row['claim_object']}")
    lines.append(f"  user_claim:   {row['user_claim'][:120]}...")
    lines.append(f"  image_ids:    {image_ids}")
    lines.append(f"  n_images:     {len(image_ids)}")
    lines.append(f"  model:        {MODEL}")

    try:
        result = call_perception(image_ids, image_paths, row["claim_object"],
                                 row["user_claim"], requirements)
    except Exception as exc:
        lines.append(f"\n  ERROR: {exc}")
        return None, lines

    usage = result.pop("_usage", {})

    lines.append(f"\n--- RAW PERCEPTION JSON ---")
    lines.append(json.dumps(result, indent=2))

    # Contract validity
    errs = validate_contract(result, image_ids, row["claim_object"])
    lines.append(f"\n--- CONTRACT VALIDITY ---")
    if errs:
        for e in errs:
            lines.append(f"  VIOLATION: {e}")
    else:
        lines.append("  ALL CLEAR — 11 keys present, image_assessments count correct, "
                     "all enum tokens valid")

    # Token usage
    lines.append(f"\n--- TOKEN USAGE ---")
    lines.append(f"  input_tokens:               {usage.get('input_tokens', '?')}")
    lines.append(f"  output_tokens:              {usage.get('output_tokens', '?')}")
    lines.append(f"  cache_creation_input_tokens:{usage.get('cache_creation_input_tokens', 0)}")
    lines.append(f"  cache_read_input_tokens:    {usage.get('cache_read_input_tokens', 0)}")

    # Gold comparison (cases 0 and 7 only)
    if gold_key and gold_key in GOLD_OBS:
        lines.append(f"\n--- GOLD COMPARISON (Module 5 authored observations) ---")
        cmp_lines = compare_gold(result, GOLD_OBS[gold_key])
        lines.extend(cmp_lines)

    return result, lines


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    sample_rows = load_sample_claims()
    test_rows = load_claims()
    reqs_lookup = RequirementsLookup()

    all_lines = [
        f"Module 4 perception test results — {datetime.now().isoformat(timespec='seconds')}",
        f"Model: {MODEL}",
        "",
    ]

    token_totals: list[dict] = []

    # ── Case A: sample row 0 ─────────────────────────────────────────────────
    row_0 = sample_rows[0]
    result_a, lines_a = run_case("A — Sample row 0 (user_001, case_001, 1-image)",
                                 row_0, reqs_lookup, gold_key="row_0")
    all_lines.extend(lines_a)

    # ── Case B: sample row 7 ─────────────────────────────────────────────────
    row_7 = sample_rows[7]
    result_b, lines_b = run_case("B — Sample row 7 (user_008, case_008, 1-image)",
                                 row_7, reqs_lookup, gold_key="row_7")
    all_lines.extend(lines_b)

    # ── Case C: test 2-image (user_004, case_004) ────────────────────────────
    row_c = next(r for r in test_rows if "case_004" in r["image_paths"])
    result_c, lines_c = run_case("C — Test 2-image (user_004, case_004) [structural]",
                                 row_c, reqs_lookup)
    all_lines.extend(lines_c)

    # ── Case D: test 3-image (user_019, case_019) — all JPEG ────────────────
    # case_001 contains AVIF images unsupported by the API; case_019 is all JPEG.
    row_d = next(r for r in test_rows if "case_019" in r["image_paths"])
    result_d, lines_d = run_case("D — Test 3-image (user_019, case_019) [structural, all-JPEG]",
                                 row_d, reqs_lookup)
    all_lines.extend(lines_d)

    # ── Token cost summary ───────────────────────────────────────────────────
    all_lines.append(f"\n{'='*72}")
    all_lines.append("TOKEN COST SUMMARY (across 4 calls)")
    all_lines.append("(Sonnet 4.6: $3/MTok in, $15/MTok out; cache creation same as in, cache read 10% of in)")

    # Re-run won't work; we already popped _usage. Collect from results instead.
    # For now, just note where to look in the per-case sections.
    all_lines.append("  See per-case TOKEN USAGE sections above for individual call costs.")
    all_lines.append("  Sum those figures to get total spend for these 4 calls.")
    all_lines.append("  Extrapolation: 20 sample rows ≈ 20x single-call cost; 44 test rows ≈ 44x.")

    # ── Final verdict ────────────────────────────────────────────────────────
    all_lines.append(f"\n{'='*72}")
    all_lines.append("ACCEPTANCE CHECK")
    cases = [
        ("A", result_a, parse_image_ids(row_0["image_paths"]), row_0["claim_object"]),
        ("B", result_b, parse_image_ids(row_7["image_paths"]), row_7["claim_object"]),
        ("C", result_c, parse_image_ids(row_c["image_paths"]), row_c["claim_object"]),
        ("D", result_d, parse_image_ids(row_d["image_paths"]), row_d["claim_object"]),
    ]
    all_pass = True
    for cname, res, ids, obj in cases:
        if res is None:
            all_lines.append(f"  Case {cname}: FAIL — API call errored")
            all_pass = False
            continue
        errs = validate_contract(res, ids, obj)
        n_assess = len(res.get("image_assessments", []))
        if errs:
            all_lines.append(f"  Case {cname}: FAIL — {len(errs)} contract violation(s)")
            all_pass = False
        else:
            all_lines.append(
                f"  Case {cname}: PASS — valid contract, "
                f"image_assessments={n_assess}/{len(ids)}"
            )
    if all_pass:
        all_lines.append("\nALL 4 CASES PASSED ACCEPTANCE TEST.")
    else:
        all_lines.append("\nSOME CASES FAILED — see details above.")

    text = "\n".join(all_lines)
    RESULTS_PATH.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
