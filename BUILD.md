# Multi-Modal Evidence Review

A pipeline that verifies damage claims by inspecting submitted photos and deciding whether the images support, contradict, or lack enough evidence to assess the claim.

## Why

This was the HackerRank Orchestrate June 2026 hackathon task: build a system that reads a CSV of damage claims (car dents, laptop cracks, package damage), examines the submitted photos, and returns structured predictions including a verdict, a severity rating, image quality flags, and a one-sentence justification. The same problem exists in real insurance workflows. The interesting parts are that the evidence is in images, the claim text may be multilingual (Hindi-English code-switching appears in the dataset), and the verdict rules have cross-field constraints that must hold exactly.

## What

Input: `dataset/claims.csv` (44 rows). Each row has a user ID, one to three image paths, a short claim conversation, and an object type (car, laptop, or package).

The pipeline runs these stages in order per row:

1. **history** (`pipeline/history.py`): looks up the user in `user_history.csv` (47 users, stats like past rejections and a free-text risk summary). Pure CSV lookup, no model calls.
2. **requirements** (`pipeline/requirements.py`): returns the applicable image evidence rules from `evidence_requirements.csv` (11 rules across three object types). Deterministic; the rule set is passed into the VLM prompt.
3. **perception** (`pipeline/perception.py`): one Anthropic API call per row. All row images are batched into a single call with the claim text and evidence requirements. Returns a locked 11-key JSON observation: which part is visible, what issue is visible, per-image relevance, quality flags, authenticity flags, whether embedded instruction text is present, and a short observation note. No verdict in this output.
4. **policy** (`pipeline/policy.py`): deterministic Python. Maps the perception JSON and user history to the 10 output fields. Owns the `claim_status` decision and enforces five cross-field invariants (for example, `not_enough_information` always co-occurs with `evidence_standard_met=false`, `supporting_image_ids=none`, and `severity=unknown`). Zero model calls.

Output: `output.csv` (14 columns: the 4 input columns echoed first, then 10 output fields including `claim_status`, `severity`, `risk_flags`, and justification text).

On the 20-row labeled sample, the pipeline reaches **75% `claim_status` accuracy** and **0 invariant violations**. The two-model comparison (Sonnet 4.6 vs Haiku 4.5) was planned but not completed within the hackathon window, so only Sonnet results exist.

Dataset scale: 44 test rows, 116 total images, 47 users, 11 evidence rules, 3 object types.

## How

**Why perception and policy are separate modules.** With only 20 labeled rows, there is no training signal large enough to teach a model the output rules. The rules are consistent and explicit in the data, so they are better written as auditable Python than hoped for from a prompt. Splitting perception from policy also means policy can be unit-tested without any API calls.

**Model choice.** `claude-sonnet-4-6` is the primary model. Haiku 4.5 was the planned comparison (same prompt, lower cost). Opus 4.8 was listed as a fallback if a class showed systematic weakness. All three support vision. The perception system prompt is cached using Anthropic's prompt caching to avoid re-sending the same 1000-token prompt on every row.

**How perception works.** All images for a row are sent in a single API call as base64 blocks. The system prompt instructs the model to return raw JSON with exactly 11 keys and lists every allowed enum value. The user turn includes the claim text, the object type, the allowed part names, and the applicable evidence requirements. A fallback JSON (all fields set to the most conservative values) is returned if the response cannot be parsed after three attempts. AVIF and HEIF images, which the Anthropic API does not accept natively, are transcoded to JPEG in memory before encoding; the files on disk are not modified.

**Security handling.** The dataset includes at least one image with embedded instruction text ("mark as approved" style overlays, confirmed in sample row 19). The system prompt explicitly labels embedded text as untrusted content. Perception flags `text_instruction_present=true` and the policy raises that flag in `risk_flags`, but the text does not influence the verdict.

**The invariant system.** Five cross-field constraints are stated in the plan and enforced in two places: policy never produces an output that violates them, and an invariant checker (`evaluation/invariant_checker.py`) validates every row after the run. This double-check caught a real bug during development where perception returning `observed_severity=unknown` on a supported row would have produced a severity value reserved for the `not_enough_information` path. The fix is a severity gate in policy (decision D18 in STATE.md), not a prompt patch.

**Evaluation.** `evaluation/evaluate.py` loads the gold CSV and the prediction CSV, computes per-field exact-match accuracy for all 8 structured output fields, produces a confusion matrix for `claim_status`, lists every per-row mismatch, and flags any field where 3 or more rows miss as a cluster worth investigating. It also runs the invariant checker. The report is saved to `evaluation/evaluation_report.md`.

**Rate limiting.** The Anthropic free tier for vision runs at approximately 5 requests per minute. The pipeline sleeps 13 seconds between rows to stay at about 4.6 RPM. This is the main reason a full run on 44 rows takes roughly 10 minutes.

## Running it

**Install dependencies**

```bash
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r code/requirements.txt
```

Dependencies: `anthropic==0.111.0`, `python-dotenv==1.2.2`, `pillow==12.2.0`, `pillow-heif==1.4.0`.

**Configure the API key**

```bash
cp code/.env.example code/.env
# Edit code/.env and set ANTHROPIC_API_KEY=sk-ant-...
```

**Run the pipeline**

```bash
cd code
python main.py                        # sample set (20 rows), writes output.csv
python main.py ../dataset/claims.csv  # full test set (44 rows), writes output.csv
```

After writing `output.csv`, the pipeline automatically checks column order and runs the invariant checker over every row. Results print to stdout; a detailed log goes to `code/logs/run.log`.

**Evaluate against the labeled sample**

```bash
python evaluation/evaluate.py   # scores existing output.csv vs sample gold
```

## What I would do next

**Severity is the worst field.** On the 20-row sample, severity accuracy was 25%. The model frequently returned `high` where gold said `medium`, and `glass_shatter` where gold said `crack`. Better prompt examples with explicit disambiguation rules would help. The type disambiguation section in the system prompt exists but is not enough.

**risk_flags has 40% accuracy.** Most misses come from two sources: the model flags `non_original_image` or `possible_manipulation` on images where gold says `valid_image=true` (the model is over-sensitive to image quality), and `manual_review_required` is never emitted by the system because it only propagates from `user_history.csv`, which does not always contain it for the affected users. It may be that the grader derives `manual_review_required` from other criteria.

**The two-model comparison was not completed.** The plan called for running both Sonnet 4.6 and Haiku 4.5 and comparing accuracy vs cost. Only Sonnet results exist.

**The 44-row test run was not verified end to end within the hackathon window.** The pipeline is built to handle it (tested on the 20-row sample), but the final test run output was not confirmed complete.

**Prompt caching saves money but the system prompt is large.** The 1000-token system prompt is cached across rows. If the cache misses (cold start or after a 5-minute gap), every row pays the full input cost. A shorter system prompt with a structured few-shot block appended per row might hold the cache better.

**The contradicted path logic for `wrong_object` and `wrong_object_part` is not fully settled.** Decision D16 in STATE.md covers when to emit `claim_mismatch`, but edge cases around whether `wrong_object_part` should suppress or force the flag were flagged for re-examination after a real claims.csv run.
