# Outdated vs. Irrelevant: SituatedQA study

This project tests whether a deterministic answer matcher can distinguish an answer valid **as of 2020**, an answer valid earlier, and other responses. It now uses the temporal question-answer data from [SituatedQA](https://github.com/mikejqzhang/SituatedQA). The 20-item pilot is part of the 200-item full candidate sample; a preselected 50-item subset outside the pilot is reserved for verification.

**The selected rows are candidates, not verified facts.** Some released SituatedQA questions have ambiguous wording or questionable dated answers. The sampler removes several obvious cases, and the collector and evaluator require a completed fact audit for every selected item. See [the pipeline plan](docs/full_pipeline_plan.md) and [the annotation protocol](docs/annotation_protocol.md).

## Source and selection

The raw official `temp.train.jsonl` and `temp.dev.jsonl` files, URLs, hashes, and retrieval date are recorded in [data/raw_benchmark/SITUATEDQA.md](data/raw_benchmark/SITUATEDQA.md). The selector groups rows by source question, requires one 2020 answer and a distinct earlier single answer, rejects conflicting same-year answers and several ambiguous phrasings, then samples with seed 7. It creates 224 structurally eligible candidates from the downloaded files; [the permanent exclusion log](data/situatedqa_exclusions.csv) now removes 19 rows found wrong or unsuitable during inspection, leaving 205 candidates. The selection is deterministic; the 20 pilot IDs are the first 20 of the 200-item sample. The 50 verification IDs are sampled from the remaining 180 with seed 19. These filters reduce obvious problems but do not establish factual correctness.

`current_answer` means **the dataset answer for 2020**, not an answer verified as current in 2026. The human audit must confirm the 2020 and earlier answers against dated evidence. The official dataset's human validation is useful but does not replace this check for our three-class task. Our 50-item verification subset is held out from the pilot and rule tuning; it is **not** the official SituatedQA test split.

The current 20-row pilot audit has 20 verified questions with evidence URLs. Earlier excluded questions and the original selections are retained in `data/audit_archive/2026-10-22-pre-replacement/`; the permanent exclusion log explains each decision. The 200-row full-study audit currently has only those 20 pilot questions verified, so full-study collection remains gated pending the other 180 fact checks.

## Set up

Run from the project root in PowerShell:

```powershell
if (-not (Test-Path .venv\Scripts\python.exe)) { py -3.11 -m venv .venv }
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The project-root `.env` contains the provider configuration and must stay private. `.env.example` shows the expected fields. The collector reads `.env` automatically. Check your provider's current limits before a large run.

## Pilot: 20 items

1. Open `data/fact_audit.csv`. For each candidate, verify the 2020 answer and that every listed historical answer had ceased to hold by 2020. Put a source URL in `evidence_url` and a decision in `status`: `verified` or `excluded`. Keep reasons in `notes`. A question is not usable merely because it appears in SituatedQA.
2. Replace excluded candidates before collection. Add each excluded ID and reason to `data/situatedqa_exclusions.csv`. The selector reads this permanent log automatically; it also accepts `--exclude-audit data/fact_audit.csv` for provisional exclusions. Generate new question CSVs with the **same seed**, then use `make_audit_sheet.py --previous` to carry forward matching verified rows. See the [pipeline plan](docs/full_pipeline_plan.md) for the exact revision procedure.
3. When all 20 selected facts are verified, collect model answers. The fixed prompt is `Answer the following question with a short factual answer only:\n{question}` and temperature is zero.

```powershell
.\.venv\Scripts\python.exe src/generate_responses.py
```

The collector writes `data/model_responses.csv` and `data/model_responses.metadata.json`, saves each answer as it arrives, and resumes a matching run. It refuses to use SituatedQA rows whose audit status is not `verified`.

4. Copy `data/templates/pilot_human_labels.csv` to `data/human_labels.csv` **once** and fill every `human_label` using `Correct`, `Outdated`, or `Irrelevant`. Annotate without seeing the automatic labels. Follow [docs/annotation_protocol.md](docs/annotation_protocol.md).
5. After annotation, run:

```powershell
.\.venv\Scripts\python.exe src/date_compare.py
.\.venv\Scripts\python.exe src/evaluate.py
```

The evaluator writes `data/analysis_table.csv`, `results/metrics.json`, and `results/confusion_matrix.csv`. It reports agreement, Cohen's kappa, and per-class precision, recall, F1, and support. Open `notebooks/pilot_run.ipynb` for the Part 7 evidence view. Jupyter is optional; install it with `python -m pip install notebook` if needed.

## Full study: 200 candidates and 50 verification items

Audit all 200 candidates in `data/full_fact_audit.csv` before collection, including the 50 verification rows. Exclude or replace any invalid fact before freezing the sample. Then:

```powershell
.\.venv\Scripts\python.exe src/generate_responses.py --questions data/full_questions.csv --output data/full_model_responses.csv --audit data/full_fact_audit.csv --delay 2.1
.\.venv\Scripts\python.exe src/date_compare.py --questions data/full_questions.csv --responses data/full_model_responses.csv --output data/full_auto_labels.csv
```

Annotate the held-out 50 without viewing automatic labels, using a copy of `data/templates/verification_human_labels.csv` saved as `data/verification_human_labels.csv`. Then:

```powershell
.\.venv\Scripts\python.exe src/filter_to_questions.py --questions data/verification_questions.csv --input data/full_model_responses.csv --output data/verification_model_responses.csv
.\.venv\Scripts\python.exe src/evaluate.py --questions data/verification_questions.csv --responses data/verification_model_responses.csv --human-labels data/verification_human_labels.csv --audit data/full_fact_audit.csv --analysis data/verification_analysis.csv --results results/verification
```

Only the 50 human-annotated items support verification metrics. Counts from all 200 automatic labels describe the selected sample; they are not accuracy estimates.

## Previous TempLAMA run

The original TempLAMA questions, 20 collected responses, metadata, and blank templates are preserved in `data/legacy_templama/`. The former project documents are in `docs/legacy_templama/`; the original TempLAMA source file remains in `data/raw_benchmark/`. No earlier response was assigned to a new SituatedQA question.
