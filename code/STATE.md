# STATE.md — live policy decisions

> This file tracks decisions that are actively unsettled or have a
> re-examination trigger. See PROGRESS.md decisions log for the full archive.
> Update this file when a decision is settled or a trigger fires.

---

## D18 — INV1 severity gate (SETTLED)

**Rule as implemented (policy.py, non-NEI branch):**
```
if observed_issue == "none":
    severity = "none"
elif observed_severity in ("low", "medium", "high"):
    severity = observed_severity
else:
    severity = "low"  # D19 floor — see below
```
`severity="unknown"` is emitted ONLY from the NEI branch (`claimed_part_visible=False`).

**Why:** Perception's prompt nudge (none vs unknown) is first-line defense; policy is the
hard guarantee. Without this gate, a `contradicted` or `supported` row with
`observed_severity=unknown` from perception would emit `severity=unknown`, violating INV1
(which requires `severity=unknown ⟺ claim_status=not_enough_information`). The original
row 01 bug was this exact profile — the fix is now the policy gate, not the prompt alone.

**Status: SETTLED**

---

## D19 — severity low-floor (PROVISIONAL, NOT SETTLED)

**Rule as implemented (policy.py):**
Non-NEI row with `observed_issue != "none"` and `observed_severity == "unknown"` floors to
`severity = "low"`. Logged at WARNING level with `D19:` prefix.

**Reasoning:** "none" would falsely assert no damage; "unknown" is reserved for NEI and
would violate INV1; "low" is the minimal-but-nonzero floor consistent with "damage exists
but cannot be rated from image quality."

**RE-EXAMINE TRIGGER:** After the real run on `claims.csv`, check every row where the D19
WARNING fires. If "low" is systematically wrong (should have been medium/high), improve the
perception prompt to avoid returning `observed_severity=unknown` when damage IS present.
If "low" appears to be fair (minor damage that's hard to rate) then no change is needed.

**Status: NOT SETTLED — re-examine after real claims.csv run**

---

## D16 — claim_mismatch rule (PROVISIONAL, NOT SETTLED)

**Rule as implemented (policy.py):**
Append `claim_mismatch` to `risk_flags` when:
- `claim_status == "contradicted"`, AND
- `"damage_not_visible"` is NOT in `quality_flags`

**Reasoning:**
`claim_mismatch` signals a contradicted verdict where visible damage actively
differs from the claim — a different part shown, a different issue type, or
severity that does not match. This is distinct from the case where the claimed
part is visible but damage is simply absent (`damage_not_visible` in
quality_flags), which is a softer contradiction with no visible evidence to
compare against.

**Provenance:** Reverse-engineered from 5 gold sample rows (4, 7, 13, 18, 19).
Consistent across all five but n is small. No explicit rule exists in
CONTEXT.md, PLAN.md, or the spec prose.

**RE-EXAMINE TRIGGER:** After the real run on `claims.csv` (44 rows), review
every row where `claim_mismatch` fires and every contradicted row where it
does not. If it over-fires (fires on rows where only `damage_not_visible`
should apply) or under-fires (misses rows with active type/severity mismatch),
revise the condition. Check especially whether `wrong_object_part` in
quality_flags should suppress or force it, analogously to `wrong_object` (row 18).

**Status: NOT SETTLED**

---

## D17 — history pass-through verbatim (cross-ref D9)

**Rule as implemented (policy.py):**
`history.flags` tokens are copied verbatim into `risk_flags`. No token is
synthesised from another token. In particular, `manual_review_required` appears
in output `risk_flags` if and only if it appears in the user's source
`history_flags` column in `user_history.csv`.

**Reasoning:**
D9 established that `history.py` is a dumb pass-through with no verdict logic.
The corollary is that `policy.py` must not derive new tokens from the tokens it
receives. `user_history_risk` is not a predicate that implies `manual_review_required`;
they are independent flags that happen to co-occur in some users' history records.

**Effect on sample gold rows:** rows 4, 7, 18, 19 show a `risk_flags` diff
(gold contains `manual_review_required`, policy output does not, because those
users' `history_flags` is `user_history_risk` only). This diff is expected and
correct under D17. The gold may reflect a grader-side derived rule; if so, that
is a grader concern, not a policy concern.

**Behaviour (b) note — authenticity_flags passthrough (adopted-and-fine):**
`authenticity_flags` (possible_manipulation, non_original_image) observed by
perception are passed through into output `risk_flags` as well as driving
`valid_image`. Both are valid `risk_flags` tokens per CONTEXT.md. Sample row 7
confirms `non_original_image` in gold `risk_flags`. No re-examination trigger.

**Status: SETTLED**
