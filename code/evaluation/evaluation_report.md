# Evaluation Report — Module 7

Gold: `dataset/sample_claims.csv`  
Predictions: `output.csv`  
Rows: 20

## Invariant Check (INV1 + INV4)

**0 violations** — all 20 output rows pass INV1 and INV4.

## Headline Metric: `claim_status` Accuracy

**15/20 correct** (75.0%)

### Confusion Matrix (rows = gold, cols = predicted)

| gold \ predicted | contradicted | not_enough_information | supported | total |
| --- | --- | --- | --- | --- |
| supported | 1 | 0 | 12 | 13 |
| contradicted | 2 | 1 | 2 | 5 |
| not_enough_information | 0 | 1 | 1 | 2 |

## Per-Field Accuracy (Structured Fields)

| Field | Correct | Total | Accuracy |
| ----- | ------- | ----- | -------- |
| evidence_standard_met | 18 | 20 | 90.0% |
| risk_flags | 8 | 20 | 40.0% |
| issue_type | 8 | 20 | 40.0% |
| object_part | 16 | 20 | 80.0% |
| claim_status | 15 | 20 | 75.0% **← headline** |
| supporting_image_ids | 15 | 20 | 75.0% |
| valid_image | 14 | 20 | 70.0% |
| severity | 5 | 20 | 25.0% |

## Free-Text Fields (Presence & Length)

Exact-match excluded from headline. Reporting non-empty and character count.

| user_id | field | pred_len | gold_len | pred_empty | gold_empty |
| ------- | ----- | -------- | -------- | ---------- | ---------- |
| user_001 | evidence_standard_met_reason | 266 | 81 | no | no |
| user_001 | claim_status_justification | 266 | 89 | no | no |
| user_002 | evidence_standard_met_reason | 318 | 98 | no | no |
| user_002 | claim_status_justification | 318 | 71 | no | no |
| user_003 | evidence_standard_met_reason | 287 | 70 | no | no |
| user_003 | claim_status_justification | 287 | 74 | no | no |
| user_004 | evidence_standard_met_reason | 280 | 73 | no | no |
| user_004 | claim_status_justification | 280 | 89 | no | no |
| user_005 | evidence_standard_met_reason | 317 | 97 | no | no |
| user_005 | claim_status_justification | 377 | 143 | no | no |
| user_006 | evidence_standard_met_reason | 59 | 79 | no | no |
| user_006 | claim_status_justification | 110 | 104 | no | no |
| user_007 | evidence_standard_met_reason | 243 | 57 | no | no |
| user_007 | claim_status_justification | 243 | 69 | no | no |
| user_008 | evidence_standard_met_reason | 391 | 105 | no | no |
| user_008 | claim_status_justification | 442 | 128 | no | no |
| user_009 | evidence_standard_met_reason | 219 | 67 | no | no |
| user_009 | claim_status_justification | 219 | 54 | no | no |
| user_010 | evidence_standard_met_reason | 309 | 76 | no | no |
| user_010 | claim_status_justification | 309 | 71 | no | no |
| user_011 | evidence_standard_met_reason | 309 | 77 | no | no |
| user_011 | claim_status_justification | 309 | 64 | no | no |
| user_012 | evidence_standard_met_reason | 282 | 63 | no | no |
| user_012 | claim_status_justification | 282 | 84 | no | no |
| user_015 | evidence_standard_met_reason | 296 | 50 | no | no |
| user_015 | claim_status_justification | 296 | 64 | no | no |
| user_018 | evidence_standard_met_reason | 324 | 92 | no | no |
| user_018 | claim_status_justification | 324 | 124 | no | no |
| user_020 | evidence_standard_met_reason | 304 | 113 | no | no |
| user_020 | claim_status_justification | 357 | 179 | no | no |
| user_030 | evidence_standard_met_reason | 359 | 101 | no | no |
| user_030 | claim_status_justification | 359 | 66 | no | no |
| user_031 | evidence_standard_met_reason | 367 | 79 | no | no |
| user_031 | claim_status_justification | 417 | 116 | no | no |
| user_032 | evidence_standard_met_reason | 286 | 123 | no | no |
| user_032 | claim_status_justification | 334 | 108 | no | no |
| user_033 | evidence_standard_met_reason | 63 | 124 | no | no |
| user_033 | claim_status_justification | 159 | 216 | no | no |
| user_034 | evidence_standard_met_reason | 394 | 119 | no | no |
| user_034 | claim_status_justification | 434 | 155 | no | no |

## Per-Row Diff (Structured Field Mismatches)

18 rows have at least one structured-field mismatch.

### user_001

| Field | Predicted | Gold |
| ----- | --------- | ---- |
| issue_type | `missing_part` | `dent` |
| severity | `high` | `medium` |

### user_002

| Field | Predicted | Gold |
| ----- | --------- | ---- |
| risk_flags | `claim_mismatch;non_original_image;possible_manipulation` | `none` |
| issue_type | `none` | `scratch` |
| claim_status | `contradicted` | `supported` |
| supporting_image_ids | `img_1;img_2` | `img_1` |
| valid_image | `false` | `true` |
| severity | `none` | `low` |

### user_004

| Field | Predicted | Gold |
| ----- | --------- | ---- |
| issue_type | `glass_shatter` | `crack` |
| severity | `high` | `medium` |

### user_005

| Field | Predicted | Gold |
| ----- | --------- | ---- |
| risk_flags | `wrong_object_part;claim_mismatch;user_history_risk` | `claim_mismatch;user_history_risk;manual_review_required` |
| issue_type | `none` | `scratch` |
| supporting_image_ids | `img_2` | `img_1` |
| severity | `none` | `low` |

### user_006

| Field | Predicted | Gold |
| ----- | --------- | ---- |
| risk_flags | `wrong_angle;damage_not_visible;cropped_or_obstructed` | `wrong_angle;damage_not_visible` |
| object_part | `body` | `headlight` |

### user_007

| Field | Predicted | Gold |
| ----- | --------- | ---- |
| issue_type | `glass_shatter` | `broken_part` |
| severity | `high` | `medium` |

### user_008

| Field | Predicted | Gold |
| ----- | --------- | ---- |
| risk_flags | `claim_mismatch;non_original_image;user_history_risk` | `claim_mismatch;non_original_image;user_history_risk;manual_review_required` |
| object_part | `hood` | `front_bumper` |

### user_009

| Field | Predicted | Gold |
| ----- | --------- | ---- |
| issue_type | `glass_shatter` | `crack` |
| severity | `high` | `medium` |

### user_010

| Field | Predicted | Gold |
| ----- | --------- | ---- |
| risk_flags | `non_original_image` | `none` |
| valid_image | `false` | `true` |
| severity | `high` | `medium` |

### user_011

| Field | Predicted | Gold |
| ----- | --------- | ---- |
| issue_type | `water_damage` | `stain` |
| severity | `high` | `medium` |

### user_012

| Field | Predicted | Gold |
| ----- | --------- | ---- |
| risk_flags | `low_light_or_glare;non_original_image` | `none` |
| valid_image | `false` | `true` |

### user_018

| Field | Predicted | Gold |
| ----- | --------- | ---- |
| issue_type | `glass_shatter` | `crack` |
| severity | `high` | `medium` |

### user_020

| Field | Predicted | Gold |
| ----- | --------- | ---- |
| risk_flags | `user_history_risk` | `damage_not_visible;user_history_risk;manual_review_required` |
| issue_type | `dent` | `none` |
| claim_status | `supported` | `contradicted` |
| severity | `medium` | `none` |

### user_030

| Field | Predicted | Gold |
| ----- | --------- | ---- |
| risk_flags | `non_original_image` | `none` |
| object_part | `box` | `seal` |
| valid_image | `false` | `true` |
| severity | `high` | `medium` |

### user_031

| Field | Predicted | Gold |
| ----- | --------- | ---- |
| risk_flags | `low_light_or_glare;user_history_risk` | `user_history_risk;manual_review_required` |
| object_part | `package_corner` | `package_side` |
| severity | `high` | `medium` |

### user_032

| Field | Predicted | Gold |
| ----- | --------- | ---- |
| evidence_standard_met | `true` | `false` |
| risk_flags | `manual_review_required` | `cropped_or_obstructed;damage_not_visible;manual_review_required` |
| issue_type | `missing_part` | `unknown` |
| claim_status | `supported` | `not_enough_information` |
| supporting_image_ids | `img_1` | `none` |
| valid_image | `true` | `false` |
| severity | `high` | `unknown` |

### user_033

| Field | Predicted | Gold |
| ----- | --------- | ---- |
| evidence_standard_met | `false` | `true` |
| risk_flags | `wrong_object;user_history_risk` | `wrong_object;claim_mismatch;user_history_risk;manual_review_required` |
| issue_type | `none` | `unknown` |
| claim_status | `not_enough_information` | `contradicted` |
| supporting_image_ids | `none` | `img_1` |
| severity | `unknown` | `low` |

### user_034

| Field | Predicted | Gold |
| ----- | --------- | ---- |
| risk_flags | `text_instruction_present;possible_manipulation;user_history_risk` | `damage_not_visible;text_instruction_present;user_history_risk;manual_review_required` |
| issue_type | `torn_packaging` | `none` |
| claim_status | `supported` | `contradicted` |
| supporting_image_ids | `img_1` | `img_1;img_2` |
| valid_image | `false` | `true` |
| severity | `high` | `none` |

## Triage: Clustered vs Scattered Mismatches

Threshold: ≥3 misses on the same field = **clustered (investigate)**; fewer = **scattered (noise)**.

| Field | Miss Count | Verdict | Affected Rows |
| ----- | ---------- | ------- | ------------- |
| evidence_standard_met | 2 | scattered (noise) | user_032;user_033 |
| risk_flags | 12 | **clustered (investigate)** | user_002;user_005;user_006;user_008;user_010;user_012;user_020;user_030;user_031;user_032;user_033;user_034 |
| issue_type | 12 | **clustered (investigate)** | user_001;user_002;user_004;user_005;user_007;user_009;user_011;user_018;user_020;user_032;user_033;user_034 |
| object_part | 4 | **clustered (investigate)** | user_006;user_008;user_030;user_031 |
| claim_status | 5 | **clustered (investigate)** | user_002;user_020;user_032;user_033;user_034 |
| supporting_image_ids | 5 | **clustered (investigate)** | user_002;user_005;user_032;user_033;user_034 |
| valid_image | 6 | **clustered (investigate)** | user_002;user_010;user_012;user_030;user_032;user_034 |
| severity | 15 | **clustered (investigate)** | user_001;user_002;user_004;user_005;user_007;user_009;user_010;user_011;user_018;user_020;user_030;user_031;user_032;user_033;user_034 |

## Summary

- **Overall structured accuracy**: 99/160 (61.9%)
- **claim_status (headline)**: 15/20 (75.0%)
- **Invariant violations**: 0
- **Clustered fields needing investigation**: risk_flags, issue_type, object_part, claim_status, supporting_image_ids, valid_image, severity
