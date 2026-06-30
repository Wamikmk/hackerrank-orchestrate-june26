# Dataset Report — HackerRank Orchestrate (June 2026)

## Overview

The dataset supports a multi-modal damage claim verification task. Each claim
consists of a support conversation transcript, one or more photos of the
alleged damage, and a claim object type (`car`, `laptop`, or `package`). The
system must produce structured predictions for 44 unlabeled test claims.

---

## Files

| File | Rows | Columns | Purpose |
|---|---|---|---|
| `sample_claims.csv` | 20 | 14 | Labeled development set |
| `claims.csv` | 44 | 4 | Unlabeled test set (predict these) |
| `user_history.csv` | 47 | 8 | Per-user risk history (join on `user_id`) |
| `evidence_requirements.csv` | 11 | 4 | Minimum image evidence rules per object/damage type |
| `output.csv` | 0 | — | Empty — populated by the system at inference time |

**Images:** 116 files total across `images/sample/` (20 case folders) and
`images/test/` (44 case folders).

---

## 1. `sample_claims.csv` — Labeled Training Data

### Schema

| Column | Type | Description |
|---|---|---|
| `user_id` | string | Claimant identifier |
| `image_paths` | string | Semicolon-separated relative paths to submitted images |
| `user_claim` | string | Full claim conversation (Customer ↔ Support) |
| `claim_object` | string | Object being claimed: `car`, `laptop`, `package` |
| `evidence_standard_met` | bool | Whether submitted images meet the minimum evidence bar |
| `evidence_standard_met_reason` | string | Free-text justification for evidence verdict |
| `risk_flags` | string | Semicolon-separated flag codes, or `none` |
| `issue_type` | string | Damage category: `dent`, `scratch`, `crack`, `broken_part`, etc. |
| `object_part` | string | Specific part damaged: `rear_bumper`, `windshield`, `screen`, etc. |
| `claim_status` | string | **Primary prediction target**: `supported` / `contradicted` / `not_enough_information` |
| `claim_status_justification` | string | Free-text explanation of the status decision |
| `supporting_image_ids` | string | Image IDs that support the verdict |
| `valid_image` | bool | Whether the submitted image(s) are usable |
| `severity` | string | `low` / `medium` / `high` / `unknown` / `none` |

### Label Distributions

**`claim_status` (primary target)**

| Value | Count | Share |
|---|---|---|
| `supported` | 13 | 65% |
| `contradicted` | 5 | 25% |
| `not_enough_information` | 2 | 10% |

**`claim_object`**

| Value | Count |
|---|---|
| `car` | 8 |
| `laptop` | 6 |
| `package` | 6 |

**`issue_type`**

| Value | Count |
|---|---|
| `dent` | 3 |
| `crack` | 3 |
| `broken_part` | 3 |
| `unknown` | 3 |
| `scratch` | 2 |
| `stain` / `water_damage` / `crushed_packaging` / `torn_packaging` | 1 each |

**`severity`**

| Value | Count |
|---|---|
| `medium` | 11 |
| `low` | 4 |
| `unknown` | 2 |
| `none` | 2 |
| `high` | 1 |

**Images per claim**

| Count | Rows |
|---|---|
| 1 image | 11 |
| 2 images | 9 |

### Risk Flags

9 of 20 claims carry at least one risk flag. Observed flag codes:

- `claim_mismatch` — described damage doesn't match visible damage
- `user_history_risk` — claimant has a risky prior claim history
- `manual_review_required` — case escalated for human review
- `wrong_angle` — image taken from an unhelpful angle
- `damage_not_visible` — damage cannot be confirmed from the image
- `blurry_image` — image quality too low
- `non_original_image` — image may not be an original photo
- `cropped_or_obstructed` — relevant area cut off or blocked
- `wrong_object` — image shows a different object than claimed
- `text_instruction_present` — image contains overlaid text or instructions

### Language Notes

Claim conversations are multilingual. Hindi-English code-switching appears in
several rows, e.g.:
- *"Parking lot mein meri car ko scrape lag gaya."*
- *"Package receive hua toh opened jaisa lag raha tha."*

The system must handle both languages without special pre-processing.

---

## 2. `claims.csv` — Unlabeled Test Data

Input-only file. Contains the same four input columns as `sample_claims.csv`
but no output labels.

| Column | Description |
|---|---|
| `user_id` | Claimant identifier |
| `image_paths` | Semicolon-separated paths under `images/test/` |
| `user_claim` | Claim conversation text |
| `claim_object` | `car` (18), `laptop` (13), `package` (13) |

**Images per claim:** 1 image: 13 rows · 2 images: 24 rows · 3 images: 7 rows.
**Unique users:** 36.

---

## 3. `user_history.csv` — Per-User Risk Context

Join this table on `user_id` to enrich each claim with historical risk signals.

| Column | Description |
|---|---|
| `past_claim_count` | Total historical claims (range 0–14, avg 4.0) |
| `accept_claim` | Number of claims accepted |
| `manual_review_claim` | Number sent to manual review |
| `rejected_claim` | Number rejected (23 of 47 users have ≥ 1 rejection) |
| `last_90_days_claim_count` | Recent activity window |
| `history_flags` | Comma-separated risk flags for the user overall |
| `history_summary` | Free-text narrative of the user's risk profile |

**`history_flags` distribution**

| Value | Users |
|---|---|
| `none` | 22 |
| `user_history_risk` | 14 |
| `user_history_risk;manual_review_required` | 8 |
| `manual_review_required` | 3 |

Notable high-risk users:

| User | Rejections | Notes |
|---|---|---|
| `user_016` | 7 | Frequent rejected car scratch claims |
| `user_037` | 6 | Unusually frequent package damage claims |
| `user_047` | 3 | Repeated side-specific car claims with mismatches |
| `user_005` | 3 | Exaggerated vehicle damage claims |
| `user_040` | 3 | Prior open-box image pattern matches current evidence |

---

## 4. `evidence_requirements.csv` — Minimum Image Evidence Rules

11 named requirements that define what a valid image must show per object and
damage type. These can be applied programmatically as a checklist before
issuing a verdict.

| Requirement ID | Applies to | Scope |
|---|---|---|
| `REQ_GENERAL_OBJECT_PART` | All objects | Claimed object and part must be clearly visible |
| `REQ_GENERAL_MULTI_IMAGE` | All multi-image rows | At least one image must show the claimed object/part |
| `REQ_REVIEW_TRUST` | All objects | Image must be reviewable and trustworthy |
| `REQ_CAR_BODY_PANEL` | Car — dent or scratch | Panel/bumper visible from angle showing surface marks |
| `REQ_CAR_GLASS_LIGHT_MIRROR` | Car — crack, broken, missing | Glass/light/mirror visible with damage clearly shown |
| `REQ_CAR_IDENTITY_OR_SIDE` | Car — identity/orientation | Vehicle identity or which side is affected must be discernible |
| `REQ_LAPTOP_SCREEN_KEYBOARD_TRACKPAD` | Laptop — screen/keyboard/trackpad | Specific component visible with alleged condition |
| `REQ_LAPTOP_BODY_HINGE_PORT` | Laptop — hinge/lid/corner/body/port | Component visible at angle where deformation can be assessed |
| `REQ_PACKAGE_EXTERIOR` | Package — crushed/torn/seal | Exterior damage visible from angle showing condition |
| `REQ_PACKAGE_LABEL_OR_STAIN` | Package — water/stain/label | Label or stained area must be legible or visible |
| `REQ_PACKAGE_CONTENTS` | Package — contents/inner item | Contents or inner item visible if contents are being claimed |

---

## 5. `output.csv` — Prediction Target

Currently empty. The system populates this file with one row per claim in
`claims.csv`. Based on `sample_claims.csv`, expected output columns are:

`evidence_standard_met`, `evidence_standard_met_reason`, `risk_flags`,
`issue_type`, `object_part`, `claim_status`, `claim_status_justification`,
`supporting_image_ids`, `valid_image`, `severity`

---

## Key Design Observations

1. **3-way classification** — `claim_status` is `supported` / `contradicted` /
   `not_enough_information`. Do not collapse to binary.

2. **Multi-modal input required** — Every claim combines images with text. A
   vision-language model (VLM) is necessary; text-only models will miss
   critical visual evidence signals.

3. **Risk layering** — `user_history.csv` flags should influence `risk_flags`
   in the output and can push borderline verdicts toward
   `manual_review_required`.

4. **Evidence rules are explicit** — The 11 requirements in
   `evidence_requirements.csv` are checkable per (object, issue_type) pair and
   should drive `evidence_standard_met` and `evidence_standard_met_reason`.

5. **Multilingual claims** — Hindi-English code-switching requires the LLM to
   handle both languages natively.

6. **Class imbalance** — ~65% of sample labels are `supported`. Avoid a model
   that defaults to this majority class for every case.

7. **Variable image count** — Claims have 1–3 images. The system must evaluate
   all images per claim and identify which ones are supporting evidence.
