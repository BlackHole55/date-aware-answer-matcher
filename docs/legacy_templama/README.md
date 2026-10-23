# Outdated vs. Irrelevant: TempLAMA study

This project tests whether a simple date-aware answer matcher can distinguish a benchmark-correct answer, an earlier answer, and any other answer. The pilot has 20 TempLAMA facts; the prepared full-study sample has 200. Both use **2020 as the reference year**. They do not represent facts verified as current in 2026.

For the complete sequence from fact audit through Part 7 and the held-out full-study evaluation, follow [docs/full_pipeline_plan.md](docs/full_pipeline_plan.md).

## Data source and scope

The source is the official [TempLAMA test split](https://storage.googleapis.com/gresearch/templama/test.json) from [Dhingra et al. (2022)](https://doi.org/10.1162/tacl_a_00459), documented by [Google Research](https://github.com/google-research/language/tree/master/language/templama). Its records are yearly Wikidata-derived cloze statements from 2010–2020. The exact downloaded file and SHA-256 are recorded in [data/raw_benchmark/README.md](data/raw_benchmark/README.md).

The sampler keeps records with exactly one 2020 answer and a distinct earlier answer, then balances five change-sensitive relations: political party (P102), owner (P127), head coach (P286), chairperson (P488), and head of government (P6). Education is excluded because a school attended in the past does not become false. Even included relations can have overlapping or erroneous entries. **A human must check each selected fact before treating the labels as research evidence.**

## Quick start

Python 3.10+ is sufficient for all scripts. Install Jupyter Notebook (`python -m pip install notebook`) only if you want to open the notebook. Run commands from this folder.

```powershell
python src/select_sample.py --size 20 --output data/sample_questions.csv
python src/select_sample.py --size 200 --output data/full_questions.csv
python src/select_verification.py
python src/make_templates.py --questions data/sample_questions.csv --prefix pilot
```

The selected CSVs are already included. The pilot is the first 20 rows of the same seeded, balanced selection used for the 200-row study. The 50-row verification subset is drawn from the remaining 180 full-study items before any responses are collected.

### 1. Collect model answers

Use one fixed model. **Recommended free option:** Groq's `openai/gpt-oss-120b`. Its [free-plan limits](https://console.groq.com/docs/rate-limits) currently list 30 requests/minute and 1,000 requests/day for this model, enough for the 20-question pilot and 200-question study under the published limits. Groq's [OpenAI-compatible endpoint](https://console.groq.com/docs/openai) works with the collector. Create a Groq API key, paste it after `LLM_API_KEY=` in the project-root `.env`, then run:

```powershell
python -m pip install -r requirements.txt
python src/generate_responses.py
```

The included `.env.example` shows the same settings without a key. The collector reads `.env` automatically; environment variables and command-line settings take precedence. Groq requests use its official Python client; other OpenAI-compatible chat APIs, including local Ollama at `http://localhost:11434/v1`, use the standard-library HTTP path. For the 200-item run, add `--questions data/full_questions.csv --output data/full_model_responses.csv --delay 2.1` to stay below the published requests-per-minute limit. Exact limits may differ by account; check the provider's limits page. The script saves one answer at a time and resumes completed rows. It writes `data/model_responses.csv` and a metadata JSON file. If answers have already been collected, use the template in `data/templates/` and save a CSV with columns `id,model_answer` instead. Do not put an API key in a CSV or in Git.

The fixed prompt is `Answer the following question with a short factual answer only:\n{question}` and temperature is zero. Each question explicitly names 2020. API providers may interpret zero temperature differently; record the exact model version and provider in the metadata.

If Groq returns `HTTP 403: error code: 1010`, [Cloudflare identifies 1010 as a client-signature block](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1010/). Install `requirements.txt` and rerun so the collector uses Groq's official client. If the official client is also blocked, contact Groq support with the Cloudflare Ray ID from the response; changing the API key alone does not address that block.

### 2. Annotate independently

Follow [docs/annotation_protocol.md](docs/annotation_protocol.md). Fill `data/human_labels.csv` with columns `id,human_label`, using exactly `Correct`, `Outdated`, or `Irrelevant`. Use the template generated under `data/templates/`. Annotators should not see `auto_label` while labeling. The scripts reject missing rows or labels rather than silently scoring an incomplete study.

### 3. Classify and evaluate

```powershell
python src/date_compare.py
python src/evaluate.py
jupyter notebook notebooks/pilot_run.ipynb
```

The evaluator writes `data/analysis_table.csv`, `results/metrics.json`, and `results/confusion_matrix.csv`. It reports agreement, Cohen's kappa, and per-class precision, recall, and F1. The notebook shows all 20 rows, metrics, the confusion matrix, and one automatically assigned example of each class. It also explains which input is missing when results are not ready.

For the full 200-row study, pass `--questions data/full_questions.csv --output data/full_model_responses.csv` to the response collector. The prepared `data/verification_questions.csv` contains 50 items balanced across the five relations and excludes the pilot. Annotate those 50 in `data/verification_human_labels.csv`. Filter the full response file to those IDs, then evaluate:

```powershell
python src/filter_to_questions.py --questions data/verification_questions.csv --input data/full_model_responses.csv --output data/verification_model_responses.csv
python src/evaluate.py --questions data/verification_questions.csv --responses data/verification_model_responses.csv --human-labels data/verification_human_labels.csv --analysis data/verification_analysis.csv --results results/verification
```

Do not change the verification subset after seeing model answers or labels. When presenting results, state that the metrics estimate performance on the annotated 50, not on all 200.

## Files

- `data/sample_questions.csv`: 20 selected benchmark items.
- `data/full_questions.csv`: 200 selected items for the later study.
- `data/verification_questions.csv`: 50 preselected full-study items, disjoint from the pilot.
- `data/raw_benchmark/templama_test.jsonl`: unmodified official test split.
- `src/select_sample.py`: deterministic relation-balanced selection.
- `src/generate_responses.py`: response collection.
- `src/date_compare.py`: automatic three-class labeling.
- `src/evaluate.py`: paired evaluation and exports.
- `notebooks/pilot_run.ipynb`: one-run evidence view once response and human-label CSVs exist.
- `docs/matching_rules.md`: matching behavior and limitations.

## Interpretation limits

`Correct` means a match to the benchmark's 2020 answer, not independently established historical truth. `Outdated` means a match to one of its earlier answers. `Irrelevant` includes other wrong answers, ambiguous answers, refusals, and answers missed by exact matching. A model may produce an alias or longer phrase that the matcher calls `Irrelevant`; the human label and disagreement analysis should identify these cases. No model responses, human labels, or measured results are invented in this repository.
