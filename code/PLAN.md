# PLAN.md — Multi-Modal Evidence Review

> Update rule: change this file only on a real plan change (scope cut, module
> split, strategy switch). Not a daily log — that is PROGRESS.md.

## Goal

For each of the 44 rows in `dataset/claims.csv`, emit one row in `output.csv`
with all 14 columns in the exact required order, deciding whether the submitted
images `supported` / `contradicted` / `not_enough_information` the claim.

## Core architecture: perception vs policy (the whole strategy)

Two layers, deliberately separated so policy is testable and defensible:

- **Perception (1 VLM call/row)** — looks at all images for the row + the
  extracted claim + the relevant evidence requirement. Returns a JSON object of
  pure observations: which part is visible, what issue is visible, is the
  CLAIMED part shown, embedded-text present?, looks non-original/manipulated?,
  per-image relevance, visible-damage severity. NO verdict, NO history.
- **Policy (deterministic Python, 0 model calls)** — maps perception + history
  lookup -> the 10 output fields, enforcing the decision hierarchy and the
  cross-field invariants. This is where `claim_status` is decided.

Why: only 20 labeled rows, 2 of them `not_enough_information`. Cannot learn
policy from data. But policy is rule-shaped and consistent in the sample, so we
encode it as auditable code, not hope the model infers it.

## Decision hierarchy (from the spec, verified in sample)

1. Images are the source of truth.
2. The claim text defines WHAT to check (claimed part + claimed issue).
3. History adds risk context ONLY. It may add `risk_flags` and a secondary
   justification clause. It may NEVER flip `claim_status` on its own.

## Verified invariants (policy enforces; eval harness checks every row)

- `not_enough_information`  ⟺  `evidence_standard_met=false`  ⟺
  `supporting_image_ids=none`  ⟺  `severity=unknown`
- claimed part NOT visible  →  evidence not met  →  `not_enough_information`
- claimed part visible but issue absent/different  →  `contradicted`;
  `issue_type` = what is ACTUALLY visible (`none` if part fine)
- `valid_image` is INDEPENDENT of the verdict. It marks authenticity/usability
  (non-original, manipulated, severe quality). A `valid_image=false` row can
  still be `contradicted` with evidence met (sample row 7).
- booleans are lowercase strings `true`/`false`; multi-values joined by `;`
  with no spaces; status token is exactly `not_enough_information`.

## Modules (target 8, each with an acceptance test)

| # | Module | One-line | Acceptance test | Est | x1.5 |
|---|--------|----------|-----------------|-----|------|
| 0 | scaffold | dirs + stubs + .gitignore | `tree code/` matches; `python main.py` runs | done | — |
| 1 | io_utils | read CSVs, parse image_paths, write 14-col output | prints 20 sample rows parsed; image_id extraction `img_1` correct; writes a dummy 14-col csv that re-reads identically | 45m | 70m |
| 2 | history | load user_history, lookup by user_id | returns flags+summary for user_005; missing user -> safe default (no flags) | 30m | 45m |
| 3 | requirements | pick rule(s) for (object, claimed issue family) | car+dent -> REQ_CAR_BODY_PANEL text; package+contents -> REQ_PACKAGE_CONTENTS; always returns 3 `all` rules (OBJECT_PART + REVIEW_TRUST unconditional; MULTI_IMAGE only when num_images > 1) | 30m | 45m |
| 4 | perception | VLM call: images+claim+req -> perception JSON | on 3 hand-picked sample cases, returns valid JSON with all keys; correctly flags embedded text on case_020 | 2h | 3h |
| 5 | policy | perception+history -> 10 fields | unit tests for all 5 invariants pass incl. negative cases; reproduces gold verdict on rows 0,4,5,7,17,18,19 | 2h | 3h |
| 6 | main | wire end-to-end over a CSV arg | runs full sample, writes valid 14-col output.csv, row count = input | 45m | 70m |
| 7 | evaluate | score vs gold + invariant validator + per-row diff | prints per-field accuracy, lists every mismatch + every invariant violation, writes evaluation_report stub | 1.5h | 2.25h |

Sum x1.5 ≈ 15.5h of build. Leaves buffer in 24h incl. sleep + freeze. OK.

## Vertical slice (reach FIRST, obsess over)

Stub perception to return a fixed JSON, wire io->requirements->history->
(stub perception)->policy->write. Get a valid 14-col `output.csv` on the sample
end-to-end BEFORE making perception real. Target: hour ~4.

## Two-strategy comparison (rubric REQUIRES ≥2 configs)

Primary: **Sonnet 4.6** perception. Comparison: **Haiku 4.5** perception, same
prompt. Score both on sample, report accuracy vs cost. Mention Opus 4.8 as
tested-not-worth-it unless a class is weak. This one experiment satisfies the
strategy-comparison AND feeds the operational analysis.

## Explicitly NOT building

- No translation pre-step (VLM handles Hindi-English natively).
- No fine-tuning, no embeddings/retrieval (44 rows, pointless).
- No web UI, no CLI flag soup, no config system.
- No per-image separate VLM calls (batch all row images into one call — cost).
- No ad-hoc patches to make a single sample row pass (overfit on n=20).

## Freeze rule

Last 15% of time = ship only. Final run on REAL `claims.csv` (not sample),
verify 44 rows + 14 cols, package code.zip (exclude .venv/.env/logs/run.log),
upload, confirm, upload transcript (`~/hackerrank_orchestrate/log.txt`).
