"""
Hardening test 1 — AVIF integration via real API call.

Runs call_perception on case_005 (all-AVIF row from claims.csv).
Verifies:
  - AVIF images transcode in-memory (no on-disk modification)
  - API call succeeds
  - Valid 11-key contract JSON returned
  - image_assessments count matches image count (2)
  - On-disk file bytes are unchanged (not modified to JPEG)
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

import hashlib
import json

from pipeline.perception import call_perception, CONTRACT_KEYS
from pipeline.requirements import RequirementsLookup
from pipeline.io_utils import DATASET_DIR


def sha256_file(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def main():
    print("="*70)
    print("TEST 1 — AVIF integration (real API call, case_005, all-AVIF)")
    print("="*70)

    # Row data for case_005 (row index 3 in claims.csv, 0-indexed)
    image_paths = [
        "images/test/case_005/img_1.jpg",
        "images/test/case_005/img_2.jpg",
    ]
    image_ids = ["img_1", "img_2"]
    claim_object = "car"
    user_claim = (
        "Customer: Hi, I am not sure which photo is clearest, but my side mirror is the issue. "
        "| Support: What happened to it? | Customer: It seems missing or broken after the car "
        "was parked outside. | Support: Should we ignore unrelated car photos if any? "
        "| Customer: Please focus on the side mirror claim."
    )

    # Snapshot on-disk file hashes BEFORE the call
    full_paths = [str(DATASET_DIR / p) for p in image_paths]
    hashes_before = {p: sha256_file(p) for p in full_paths}

    print(f"\nImages: {image_ids}")
    print(f"Paths:  {image_paths}")
    print(f"\nOn-disk SHA256 BEFORE call:")
    for p, h in hashes_before.items():
        print(f"  {os.path.basename(p)}: {h}")

    # Confirm they are AVIF before the call
    for p in full_paths:
        with open(p, "rb") as f:
            magic = f.read(12)
        is_avif = len(magic) >= 12 and magic[4:8] == b"ftyp" and magic[8:12] in (b"avif", b"avis", b"heic", b"heix", b"mif1")
        print(f"  {os.path.basename(p)} is AVIF: {is_avif}")

    req_lookup = RequirementsLookup()
    reqs = req_lookup.get(claim_object, len(image_ids))
    print(f"\nRequirements for '{claim_object}': {len(reqs)} rules")

    print("\nCalling call_perception (real API)…")
    result = call_perception(
        image_ids=image_ids,
        image_paths=image_paths,
        claim_object=claim_object,
        user_claim=user_claim,
        requirements=reqs,
    )
    print("API call returned.\n")

    # Check on-disk hashes AFTER — must be unchanged
    hashes_after = {p: sha256_file(p) for p in full_paths}
    files_unchanged = all(hashes_before[p] == hashes_after[p] for p in full_paths)
    print(f"On-disk files unchanged (no in-place modification): {files_unchanged} — {'PASS' if files_unchanged else 'FAIL'}")
    if not files_unchanged:
        for p in full_paths:
            if hashes_before[p] != hashes_after[p]:
                print(f"  CHANGED: {p}")

    # Check 11-key contract
    result_keys = set(result.keys()) - {"_usage", "_retries", "_fallback"}
    missing = CONTRACT_KEYS - result_keys
    has_all_keys = len(missing) == 0
    print(f"\n11-key contract satisfied: {has_all_keys} — {'PASS' if has_all_keys else 'FAIL'}")
    if missing:
        print(f"  MISSING: {missing}")

    # Check image_assessments count
    ia = result.get("image_assessments", [])
    count_ok = len(ia) == len(image_ids)
    print(f"image_assessments count={len(ia)} matches image count={len(image_ids)}: {count_ok} — {'PASS' if count_ok else 'FAIL'}")

    # Print full returned JSON (excluding _usage bulk)
    usage = result.pop("_usage", None)
    retries = result.get("_retries", 0)
    print(f"\nReturned perception JSON (_retries={retries}):")
    printable = {k: v for k, v in result.items() if not k.startswith("_")}
    print(json.dumps(printable, indent=2))

    if usage:
        print(f"\nToken usage: input={usage['input_tokens']}, output={usage['output_tokens']}, "
              f"cache_creation={usage['cache_creation_input_tokens']}, cache_read={usage['cache_read_input_tokens']}")

    overall = files_unchanged and has_all_keys and count_ok and not result.get("_fallback")
    print(f"\nTEST 1 OVERALL: {'PASS' if overall else 'FAIL'}")
    return overall


if __name__ == "__main__":
    main()
