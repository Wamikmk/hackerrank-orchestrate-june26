"""
requirements.py — Module 3: Evidence requirement lookup.

Pure deterministic mapping. Takes (claim_object, claimed_issue_family,
num_images); returns relevant Requirement records with verbatim CSV text.
Zero model calls, zero claim-text parsing.
"""

from dataclasses import dataclass

from pipeline.io_utils import load_evidence_requirements

# (claim_object, issue_family_token) -> requirement_id
# Tokens per CONTEXT.md evidence_requirements mapping section.
# Short forms (dent, broken) AND canonical issue_type enum values included
# so that whatever clean token perception produces, a lookup hits.
_FAMILY_MAP: dict[str, dict[str, str]] = {
    "car": {
        "dent":          "REQ_CAR_BODY_PANEL",
        "scratch":       "REQ_CAR_BODY_PANEL",
        "crack":         "REQ_CAR_GLASS_LIGHT_MIRROR",
        "glass_shatter": "REQ_CAR_GLASS_LIGHT_MIRROR",
        "broken_part":   "REQ_CAR_GLASS_LIGHT_MIRROR",
        "missing_part":  "REQ_CAR_GLASS_LIGHT_MIRROR",
        "broken":        "REQ_CAR_GLASS_LIGHT_MIRROR",
        "missing":       "REQ_CAR_GLASS_LIGHT_MIRROR",
        "identity":      "REQ_CAR_IDENTITY_OR_SIDE",
        "side":          "REQ_CAR_IDENTITY_OR_SIDE",
    },
    "laptop": {
        "screen":   "REQ_LAPTOP_SCREEN_KEYBOARD_TRACKPAD",
        "keyboard": "REQ_LAPTOP_SCREEN_KEYBOARD_TRACKPAD",
        "trackpad": "REQ_LAPTOP_SCREEN_KEYBOARD_TRACKPAD",
        "hinge":    "REQ_LAPTOP_BODY_HINGE_PORT",
        "lid":      "REQ_LAPTOP_BODY_HINGE_PORT",
        "corner":   "REQ_LAPTOP_BODY_HINGE_PORT",
        "body":     "REQ_LAPTOP_BODY_HINGE_PORT",
        "base":     "REQ_LAPTOP_BODY_HINGE_PORT",
        "port":     "REQ_LAPTOP_BODY_HINGE_PORT",
    },
    "package": {
        "crushed":           "REQ_PACKAGE_EXTERIOR",
        "crushed_packaging": "REQ_PACKAGE_EXTERIOR",
        "torn":              "REQ_PACKAGE_EXTERIOR",
        "torn_packaging":    "REQ_PACKAGE_EXTERIOR",
        "seal":              "REQ_PACKAGE_EXTERIOR",
        "water":             "REQ_PACKAGE_LABEL_OR_STAIN",
        "water_damage":      "REQ_PACKAGE_LABEL_OR_STAIN",
        "stain":             "REQ_PACKAGE_LABEL_OR_STAIN",
        "label":             "REQ_PACKAGE_LABEL_OR_STAIN",
        "contents":          "REQ_PACKAGE_CONTENTS",
        "inner":             "REQ_PACKAGE_CONTENTS",
        "item":              "REQ_PACKAGE_CONTENTS",
    },
}

_MULTI_IMAGE_ID = "REQ_GENERAL_MULTI_IMAGE"


@dataclass
class Requirement:
    requirement_id: str
    minimum_image_evidence: str


class RequirementsLookup:
    """Loads evidence_requirements.csv once; get() never raises."""

    def __init__(self) -> None:
        rows = load_evidence_requirements()
        self._by_id: dict[str, str] = {
            r["requirement_id"]: r["minimum_image_evidence"] for r in rows
        }
        # All 'all'-scoped rules except the conditional multi-image one
        self._always_general: list[str] = [
            r["requirement_id"]
            for r in rows
            if r["claim_object"] == "all" and r["requirement_id"] != _MULTI_IMAGE_ID
        ]

    def _req(self, req_id: str) -> Requirement:
        return Requirement(req_id, self._by_id[req_id])

    def get(
        self,
        claim_object: str,
        claimed_issue_family: str,
        num_images: int,
    ) -> list[Requirement]:
        results = [self._req(rid) for rid in self._always_general]
        if num_images > 1:
            results.append(self._req(_MULTI_IMAGE_ID))
        specific_id = _FAMILY_MAP.get(claim_object, {}).get(claimed_issue_family)
        if specific_id:
            results.append(self._req(specific_id))
        return results
