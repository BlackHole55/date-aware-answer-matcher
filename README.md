# Date Aware Answer Matcher on SituatedQA

Evaluates a deterministic matcher for answers to time-anchored questions. Model responses are labeled **Correct**, **Outdated**, or **Irrelevant**, then compared with blind human judgments.

The current primary study is **full-200**: 200 mixed-source questions (122 SituatedQA + 78 U.S. House) with 200 blind human labels. See [docs/protocol_amendment_full_200_labels.md](docs/protocol_amendment_full_200_labels.md).

## Layout

| Path | Role |
|------|------|
| `src/` | Matchers and pipeline scripts |
| `data/` | Frozen CSVs / JSON (see [data/README.md](data/README.md)) |
| `docs/` | Protocol, plans, evaluation notes (see [docs/README.md](docs/README.md)) |
| `results/` | Named primary and exploratory runs |
| `tests/` | Unit tests |
| `snapshots/` | Hash-named freezes of label/response files |
| `notebooks/` | Exploratory notebooks |

## Experiment timeline

1. **Pilot** — 20 questions (`data/sample_questions.csv`, `results/`, `results/v2/`)
2. **Prior primary** — amended 122 SituatedQA questions, 50 held-out labels (`*_amended*`, `results/verification_primary_120f5f83/`, `verification_exact/`, `verification_v2/`)
3. **full-200 (current)** — 200 mixed-source questions, 200 blind labels (`full_*_200_new*`, `results/verification_200_new_*`, `annotator_agreement_50/`)
4. **Exploratory / legacy** — `*_refs_exploratory*`, `results/refs/`, `data/legacy_templama/`, `docs/legacy_templama/`, `snapshots/assignment4_pre_run_2026-10-31/`

## Setup

From this directory in PowerShell:

```powershell
if (-not (Test-Path .venv\Scripts\python.exe)) { py -3.11 -m venv .venv }
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

For new model calls, copy `.env.example` to a private `.env`. Never commit the API key.

## Reproduce without an API key

Pilot matchers:

```powershell
.\.venv\Scripts\python.exe src/evaluate.py --matcher exact
.\.venv\Scripts\python.exe src/evaluate.py --matcher year-token --analysis data/analysis_table_v2.csv --results results/v2
```

full-200 primary comparison (uses frozen responses and human labels):

```powershell
.\.venv\Scripts\python.exe src/compare_methods.py `
  --questions data/full_questions_200_new.csv `
  --responses data/full_200_new_model_responses.csv `
  --human-labels data/full_200_new_protocol_labels.csv `
  --audit data/full_fact_audit_200_new.csv `
  --output-dir results/verification_200_new_full
```

## Key docs

- [Annotation protocol](docs/annotation_protocol.md)
- [Matching rules v2](docs/matching_rules_v2.md)
- [full-200 amendment](docs/protocol_amendment_full_200_labels.md)
- [New 200 question set](docs/new_200_question_set.md)
- [Repo cleanup plan](docs/repo_cleanup_plan.md)
