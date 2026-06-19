"""
requirements.py — Module 3: Evidence requirement lookup.

Pure deterministic mapping. Takes (claim_object, num_images); returns ALL
requirement rules for that object plus the applicable general rules. Verbatim
text from CSV. Zero model calls, zero claim-text parsing.
"""

from dataclasses import dataclass

from pipeline.io_utils import load_evidence_requirements

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
        # Object-specific rules grouped by claim_object
        self._by_object: dict[str, list[str]] = {}
        for r in rows:
            obj = r["claim_object"]
            if obj != "all":
                self._by_object.setdefault(obj, []).append(r["requirement_id"])

    def _req(self, req_id: str) -> Requirement:
        return Requirement(req_id, self._by_id[req_id])

    def get(self, claim_object: str, num_images: int) -> list[Requirement]:
        results = [self._req(rid) for rid in self._always_general]
        if num_images > 1:
            results.append(self._req(_MULTI_IMAGE_ID))
        for rid in self._by_object.get(claim_object, []):
            results.append(self._req(rid))
        return results
