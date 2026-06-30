# HackerRank Orchestrate — Multi-Modal Evidence Review

Damage-claim verification system using a VLM perception layer + deterministic policy layer.

## Architecture

```
claims.csv  ──►  perception.py  ──►  policy.py  ──►  output.csv
                 (Claude VLM)        (deterministic)
```

- **perception.py** — one Anthropic API call per claim row; batches all images; returns a locked 11-key JSON observation (no verdict, no decision).
- **policy.py** — deterministic mapping from perception JSON + user history → 10 output fields; zero model calls; enforces all 5 output invariants.
- **pipeline/requirements.py** — looks up minimum image evidence requirements per object type and image count.
- **pipeline/history.py** — looks up user risk history from `user_history.csv`.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # add your ANTHROPIC_API_KEY
```

## Run on full dataset

```bash
python main.py                        # defaults to dataset/sample_claims.csv
python main.py dataset/claims.csv     # full test set → output.csv
```

Output is written to `output.csv` at the repo root (14 columns, invariant-checked).

## Evaluate on sample

```bash
python evaluation/main.py             # runs pipeline on sample_claims.csv + scores vs gold
python evaluation/evaluate.py         # score an existing output.csv vs sample gold
```

## Model

`claude-sonnet-4-6` via the Anthropic API. Rate limited to ~4.6 RPM (13 s sleep between rows).

## Environment variables

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Required. Anthropic API key. |
