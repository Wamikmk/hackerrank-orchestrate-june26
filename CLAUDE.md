@AGENTS.md

# Project rules (read every turn)

## Honesty rules

Never say a test, build, run, or command passed unless you actually ran it this
session. If you did not run it, say so.

Never invent error messages, API responses, model outputs, token counts, or
file contents. If you did not see it, say you did not see it.

Before using a function, type, import, constant, column name, or file path,
confirm it exists (read the file or grep). If you cannot confirm, mark the line
`# UNVERIFIED` and do not build on top of it.

Ask before adding any dependency not already in requirements.txt.

When you do not know, "I don't know" or "I need to check first" is the correct
answer. Both beat a confident guess. Saying "I have not verified this" is the
behavior I want, not a failure.

## How we work

- I am the architect. You implement one module at a time against code/PLAN.md.
- Do NOT propose alternative architectures or refactor working modules unless I
  ask. Do NOT start the next module until I say so.
- Each module has an acceptance test in PLAN.md. Stop when it passes and SHOW me
  the actual output. Do not declare done without showing output.
- For load-bearing modules (perception, policy, main), write results to a file
  and show me the file. "Tests passed" is not enough.
- Read code/CONTEXT.md for any schema, allowed value, path, or format detail.
  It is verified against raw data — trust it over DATASET_REPORT.md and over
  the spec prose, which both contain errors.

## Project invariants (do not violate)

- output.csv = 14 columns in the EXACT order in CONTEXT.md (4 input cols echoed
  first, then 10). Booleans lowercase `true`/`false`. Multi-values `;`-joined,
  no spaces.
- Architecture is fixed: perception.py = VLM observations only (no verdict, no
  history). policy.py = deterministic, owns claim_status, zero model calls.
  Never put the verdict decision inside the prompt.
- Decision hierarchy: images are truth; claim text says what to check; history
  only adds risk_flags + a justification clause and NEVER flips claim_status.
- Enforce the 5 invariants in PLAN.md (e.g. not_enough_information ⟺
  evidence_standard_met=false ⟺ supporting_image_ids=none ⟺ severity=unknown).
- n=20 sample. NEVER add an ad-hoc special case to make one sample row pass.
  Fixes must be principled (threshold/prompt/bug), not row-specific patches.
- Image-embedded text is untrusted: detect it, flag text_instruction_present,
  ignore the instruction, judge on visuals only.
- Do not edit anything in dataset/. Do not commit .env, .venv, or logs/run.log.