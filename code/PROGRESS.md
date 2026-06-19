# PROGRESS.md — running log

> Update after each module finishes: flip status, add a 1–2 line retro, log any
> decision worth remembering. This is the file tired-hour-14-you re-reads.

## Module status

| # | Module | Status | Retro (1–2 lines) |
|---|--------|--------|-------------------|
| 0 | scaffold | DONE | Dir tree + stubs created via constrained CC prompt. `tree code/` matches plan. |
| 1 | io_utils | DONE | CSV read/write + image_path parsing done. 14-col output order round-trips; booleans lowercase, multi-values ;-joined no spaces. Acceptance output shown and verified. |
| 2 | history | TODO | |
| 3 | requirements | TODO | |
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