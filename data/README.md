# Data layout

Files are grouped by experiment stage. Prefer the **full-200** set for new work. Policy detail: [docs/repo_cleanup_plan.md](../docs/repo_cleanup_plan.md).

## full-200 (current primary)

| File | Role |
|------|------|
| `full_questions_200_new.csv` | 200 questions (122 SituatedQA + 78 House) |
| `full_fact_audit_200_new.csv` | Matching verified audits |
| `house_roster_78_verified.csv` | House source rows with PDF locators |
| `full_200_new_model_responses.csv` (+ `.metadata.json`) | Fresh 200 model answers |
| `full_200_new_protocol_labels.csv` | Blind human labels (primary) |
| `full_200_new_annotator_b_50.csv` | Second-annotator subset |
| `full_200_new_auto_labels_exact.csv` | Exact matcher labels |
| `full_200_new_auto_labels_v2.csv` | Year-token matcher labels |
| `templates/full_200_new_*` | Annotation / response templates |

## Prior primary (122 / 50)

Amended SituatedQA-only run with a 50-label held-out set. Keep as archive; do not overwrite.

- Questions: `full_questions_amended.csv`, `verification_questions_amended.csv`
- Responses: `full_model_responses.csv`, `verification_model_responses.csv`
- Labels / analysis: `verification_amended_human_labels.csv`, `verification_analysis_*.csv`, `verification_error_analysis_2026-11-01.csv`
- Auto labels: `full_auto_labels_exact.csv`, `full_auto_labels_v2.csv`

## Pilot (20)

- `sample_questions.csv`, `model_responses.csv`, `human_labels.csv`
- `fact_audit.csv`, `analysis_table.csv`, `analysis_table_v2.csv`, `auto_labels*.csv`
- `pilot_reference_supplement.csv`

## Exploratory (not primary)

Post hoc reference expansion and related outputs. Cite separately from primary results.

- `*_refs_exploratory*`
- `full_reference_supplement_exploratory.json`
- `verification_reference_supplement_exploratory.json`
- `verification_ai_assisted_draft.json`

## Other folders

| Path | Role |
|------|------|
| `raw_benchmark/` | SituatedQA / TemQa source dumps |
| `legacy_templama/` | Pre-SituatedQA TemQa pilot artifacts |
| `audit_archive/` | Pre-replacement audit snapshots |
| `templates/` | Blank sheets for annotation / collection |
