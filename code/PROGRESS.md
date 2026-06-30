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
| 5 | policy | IN PROGRESS | Core built in slice: atomic INV1/2 gate, INV3 contradicted branch, INV4 independent valid_image, INV5 history passthrough. Supported path verified end-to-end. Contradicted / not_enough_information paths and the 5 invariant UNIT tests (incl. negatives + gold-row reproduction) still TODO in Module 5. |
| 6 | main wiring | IN PROGRESS | Wired all 6 stages on sample, writes valid 14-col output.csv, 20 rows, row order preserved. Real-claims final run still TODO. |
| 7 | evaluate | TODO | |

Milestones:
- [x] Vertical slice: valid 14-col output.csv on sample with STUB perception
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
- D13: vertical slice built with REAL policy core (not pass-through) fed by
  stub perception. Rationale: policy + invariants are the risky untested part;
  exercise them free before paying for VLM calls. Slice output is all-supported
  (stub limitation) and is NOT an accuracy result.
- D14 (behaviour b, adopted-and-fine): authenticity_flags (non_original_image,
  possible_manipulation) observed by perception are passed through into output
  risk_flags in addition to driving valid_image. This is a clean observation
  passthrough: the tokens are valid output risk_flags per CONTEXT.md and the
  data (sample row 7) confirms them present in gold risk_flags. No re-examination
  trigger needed; this is straightforward.
- D16 (claim_mismatch rule — PROVISIONAL, NOT SETTLED): policy appends
  claim_mismatch to risk_flags when claim_status=contradicted AND
  damage_not_visible is NOT in quality_flags. Rationale: claim_mismatch denotes
  a contradicted verdict where visible damage actively differs from what was
  claimed (a different part, different issue type, or severity mismatch), as
  distinct from the case where the claimed part is visible but damage is simply
  absent (damage_not_visible). This rule was reverse-engineered from 5 gold rows
  (4, 7, 13, 18, 19) and is consistent across them, but the n is small.
  RE-EXAMINE TRIGGER: after the real run on claims.csv, check whether
  claim_mismatch appears in proportion to the contradicted verdicts and in the
  right rows. If it fires systematically on rows where it should not, or misses
  rows where it should fire, revisit. This decision is NOT settled.
- D18 (INV1 enforced in policy as authoritative gate — severity coupled to verdict):
  Policy now owns severity atomically in the non-NEI branch. Rule: if observed_issue==none
  → severity=none; if observed_severity in {low,medium,high} → pass through; otherwise
  → floor to low (D19). severity=unknown is emitted ONLY on the not_enough_information
  path. The perception prompt nudge (observed_severity none vs unknown) is the first line
  of defense; policy is the guarantee. The prompt-only approach was insufficient: row 01
  (supported, scratch, observed_severity=unknown from an earlier perception run) would have
  emitted severity=unknown on a non-NEI row — a live INV1 violation. Gold-row severities
  are unaffected (none of the 7 gold rows had the violating profile).
- D19 (PROVISIONAL — non-NEI row with damage present but unrateable severity floors to low):
  When claimed_part_visible=True AND observed_issue != none AND observed_severity=unknown,
  policy sets severity=low. Rationale: "none" would falsely assert no damage; "unknown" is
  reserved for NEI and would violate INV1; "low" is the minimal-but-nonzero floor. This
  branch is logged at WARNING level. RE-EXAMINE TRIGGER: after the real run on claims.csv,
  check every row where the D19 floor fires. If low is systematically mis-calibrated (e.g.,
  what should be medium or high gets floored), revise the floor or adjust the perception
  prompt to produce a real severity estimate rather than unknown.
- D17 (history pass-through reaffirmed — cross-ref D9): manual_review_required
  is emitted in output risk_flags ONLY when it is present in the user's source
  history_flags (user_history.csv). It is never synthesised from user_history_risk
  or any other derived condition. The earlier session briefly added an auto-derive
  rule; that was cut because it violated D9 (history.py is a verbatim pass-through
  of the tokens as they appear). Effect: sample rows 4, 7, 18, 19 will show a
  risk_flags diff vs gold on manual_review_required. That diff is expected and
  correct; the gold may reflect a policy the grader applies separately.

## Open questions / risks to revisit

- Q: On `contradicted`, does supporting_image_ids list the image that SHOWS the
  contradiction, or `none`? Sample rows 4/7/18 listed the image (`img_1`), 19
  listed both. So: list the relevant image(s), NOT none. Confirmed — keep.
- Q: How does policy set severity on `supported`? From perception's
  visible-damage severity. Validate against sample once perception is real.
- R: 3-image test rows unverified until real run. Watch token cost there.
- R: prompt-injection images — confirm text_instruction_present fires on test.
- R: invariant_checker.py verified only on clean supported rows; NOT yet
  verified to CATCH a violation. Must feed it a deliberately broken row in
  Module 5 before relying on it.

## Deviations from playbook (track for v2)

- (none yet)
