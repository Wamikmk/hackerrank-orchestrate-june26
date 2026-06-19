# PROGRESS.md — running log

> Update after each module finishes: flip status, add a 1–2 line retro, log any
> decision worth remembering. This is the file tired-hour-14-you re-reads.

## Module status

| # | Module | Status | Retro (1–2 lines) |
|---|--------|--------|-------------------|
| 0 | scaffold | DONE | Dir tree + stubs created via constrained CC prompt. `tree code/` matches plan. |
| 1 | io_utils | DONE | CSV read/write + image_path parsing done. 14-col output order round-trips; booleans lowercase, multi-values ;-joined no spaces. Acceptance output shown and verified. |
| 2 | history | DONE | user_history.csv lookup by user_id. history_flags split on ';' (NOT comma, report was wrong); only the two expected tokens present. Missing user returns safe empty default, no crash. Acceptance output verified. |
| 3 | requirements | DONE | Pure deterministic mapping (claim_object, num_images) -> all object-specific rules + generals. Accepted; then REVISED for option B: signature now (claim_object, num_images), returns ALL object-specific rules + generals; perception narrows the family. Per-object grouping confirmed 3/2/3. Unmapped object degrades to generals-only. Re-verified. |
| 4 | perception (VLM) | TODO | |
| 5 | policy | TODO | |
| 6 | main wiring | TODO | |
| 7 | evaluate | TODO | |

Milestones:
- [ ] Vertical slice: valid 14-col output.csv on sample with STUB perception
- [ ] Perception real (Sonnet) + 3-case spot check
- [ ] Policy passes all 5 invariant unit tests
- [ ] Full sample eval scored vs gold; mismatches triaged
- [ ] Two-config comparison (Sonnet vs Haiku) run + tabled
- [ ] FINAL run on real claims.csv (44 rows), output verified
- [ ] code.zip packaged, output.csv + transcript uploaded, submission confirmed

## Decisions log

- D1: Architecture = perception (VLM, observations only) + policy
  (deterministic, owns the verdict). Reason: n=20 too small to learn policy;
  keep it auditable + interview-defensible.
- D2: Primary model Sonnet 4.6, comparison Haiku 4.5. Reason: bounded visual
  task, Sonnet is the price/quality sweet spot; comparison is rubric-required.
- D3: One VLM call per ROW (all images batched in), not per image. Reason: cost
  + lets model compare images to pick supporting subset.
- D4: History never flips claim_status; only adds risk_flags + a justification
  clause. Reason: spec hierarchy, verified in sample.
- D5: Trust raw CSVs over DATASET_REPORT.md (report had a separator error).
- D8: image_ids are positional per row (img_1, img_2, ...), NOT globally
  unique across rows. An image_id is only meaningful within its own row.
  supporting_image_ids is therefore always a subset of that row's own ids.
  Do not build a global image index.
- D9: history.py is a dumb lookup, no scoring or verdict logic. Returns flags
  list + summary text only. 'none' is a sentinel meaning no flags, not a flag
  token. Parser returns [] for a none row, same as empty or missing user, so
  policy has one code path: non-empty list => append to risk_flags, empty =>
  nothing.
- D11: Option B chosen for issue-family selection. requirements.py returns
  ALL rules for the object (no family arg); perception picks the applicable
  one from claim text + images. Removes an extra extraction call and the
  requirements-before-perception ordering conflict. claimed_issue_family is
  now a recorded perception observation, not an input to requirements.
- D12: empty dataset/output.csv header inspected; matches the 14-column
  contract exactly, 4 inputs then 10 outputs. Header fields are quoted. Open:
  confirm grader CSV dialect (QUOTE_ALL vs MINIMAL) at final-run hygiene
  check; assume any-valid-CSV until confirmed.

## Open questions / risks to revisit

- Q: On `contradicted`, does supporting_image_ids list the image that SHOWS the
  contradiction, or `none`? Sample rows 4/7/18 listed the image (`img_1`), 19
  listed both. So: list the relevant image(s), NOT none. Confirmed — keep.
- Q: How does policy set severity on `supported`? From perception's
  visible-damage severity. Validate against sample once perception is real.
- R: 3-image test rows unverified until real run. Watch token cost there.
- R: prompt-injection images — confirm text_instruction_present fires on test.

## Deviations from playbook (track for v2)

- (none yet)
