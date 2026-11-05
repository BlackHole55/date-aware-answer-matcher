# Assignment 4 — approved amendment Option B (label all 200)

**Status:** Instructor-approved (per student report).  
**Change:** Replace the primary 50-label held-out analysis with **blind human labels on all 200** questions in `data/full_questions_200_new.csv` (122 SituatedQA + 78 U.S. House).  
**Relation to prior work:** The original Moodle Part 1–2 freeze (30 October 2026, 11:37 AM), the 122/50 SituatedQA amendment (1 November 2026), and that run’s 50-label primary results remain archived. This mixed-source **200-label** study is the new approved primary evaluation under this amendment.

See also: [new question set](new_200_question_set.md), [prior 122/50 amendment record](protocol_amendment_record.md). The earlier draft plan that kept a 50-item primary subset ([new_200_experiment_plan.md](new_200_experiment_plan.md)) is superseded for primary analysis by this Option B record.

---

## Deviations from the Frozen Protocol

After the protocol freeze and the later approved reduction to 122 SituatedQA questions with a 50-item verification subset, the study is amended as follows.

**Approved sample.** Use the mixed-source corpus `data/full_questions_200_new.csv`: the 122 verified SituatedQA questions from `data/full_questions_amended.csv` (original order), plus 78 source-backed U.S. House district questions from `data/house_roster_78_verified.csv`. Matching audit: `data/full_fact_audit_200_new.csv` (all 200 `status=verified`).

**Approved evaluation change.** The primary outcome is no longer three-class macro-F1 on 50 held-out labels. It is three-class macro-F1 on **200 blind human labels**, one per question in that corpus. There is no separate primary verification subsample for this amendment. Full-corpus automatic label counts remain descriptive and are not accuracy estimates by themselves.

**Unchanged.** Model (`openai/gpt-oss-120b` via Groq), short-answer prompt, temperature 0, tool choice `none`, four classification conditions (Always Correct; exact; SQuAD-style token overlap; proposed exact-plus-year-token), blind annotation protocol, secondary metrics, 10,000 class-stratified bootstrap intervals with seed `20261028`, paired McNemar tests with Holm correction across three baseline comparisons, year-token ablation, no tuning against evaluation labels, and separate reporting of any post hoc reference expansion.

**Disclosure required.**

1. Topic mix is 122 SituatedQA + 78 House (House-heavy relative to SituatedQA-only).
2. The 122 SituatedQA IDs include the prior pilot and prior verification IDs; those items are not independent of earlier project stages—report that as a limitation.
3. Collect **all 200 responses in one fresh run**; do not splice the old 122 responses into a file presented as one new run unless separately documented and approved.
4. Preserve the prior 50-label SituatedQA result as a separate archive; do not overwrite its snapshot.

---

## Frozen file identity (record before collection)

Re-run assembly and confirm these hashes (from `docs/new_200_question_set.md`):

| File | Role | SHA-256 |
|------|------|---------|
| `data/full_questions_200_new.csv` | 200 questions | `3a50905fdbe919a5b61e2291248c654437464ae6e2c0fe8a40af47cf1993e67d` |
| `data/full_fact_audit_200_new.csv` | 200 verified audits | `ff05019314b5b14c042e1e7a610228e6876761d84fa959179a42d9bb6f373cdc` |
| `data/house_roster_78_verified.csv` | House source rows | `a262e442b1808896908cf51b9300e01c4c013b75cebb7a36a7b93e4c3b75b3e9` |

Also record after each later step: response CSV + `.metadata.json` hashes, human-label CSV hash, `compare_methods.py` hash, and results directory name.

**House fact rule (unchanged):** questions ask who represented a numbered U.S. House district on **15 December 2020**; historical answer is the distinct name on **4 January 2011** Clerk roster. Numbered seat ≠ fixed geography.

---

## What this amendment changes vs the draft new-200 plan

| Item | Draft plan (`new_200_experiment_plan.md`) | This approved Option B |
|------|-------------------------------------------|------------------------|
| Primary N | 50 stratified subset | **200 (all questions)** |
| Subset sampling (`Random(20261103)`, 31/19) | Required | **Not used for primary** |
| `filter_to_questions` for verification | Yes | **Skip** |
| Human labels file | `verification_200_new_human_labels.csv` (50) | `full_200_new_human_labels.csv` (200) |
| `compare_methods.py` | Requires exactly 50 | **Must accept 200** |
| Source breakdown | Optional descriptive | **Report SituatedQA vs House metrics as secondary descriptive splits** |

---

## Execution checklist

Do in order. Freeze files and analysis code before inspecting evaluation labels for tuning.

### Gate A — Facts and templates

```powershell
.\.venv\Scripts\python.exe src/assemble_new_200_questions.py
.\.venv\Scripts\python.exe src/make_templates.py --questions data/full_questions_200_new.csv --prefix full_200_new
```

Confirm 200 unique IDs, 200 verified audit rows, and hashes matching the table above. Spot-check House roster locators; log any correction and regenerate if a row changes.

### Gate B — Collect 200 fresh responses

```powershell
.\.venv\Scripts\python.exe src/generate_responses.py `
  --questions data/full_questions_200_new.csv `
  --audit data/full_fact_audit_200_new.csv `
  --output data/full_200_new_model_responses.csv `
  --base-url https://api.groq.com/openai/v1 `
  --model openai/gpt-oss-120b `
  --delay 2.1
```

Keep `data/full_200_new_model_responses.metadata.json`. Check that 200 IDs match the question file exactly and every `model_answer` is nonblank. Record start/end UTC, delay used, model string, and code version.

### Gate C — Frozen automatic methods

```powershell
.\.venv\Scripts\python.exe src/date_compare.py `
  --questions data/full_questions_200_new.csv `
  --responses data/full_200_new_model_responses.csv `
  --output data/full_200_new_auto_labels_exact.csv

.\.venv\Scripts\python.exe src/date_compare_v2.py `
  --questions data/full_questions_200_new.csv `
  --responses data/full_200_new_model_responses.csv `
  --output data/full_200_new_auto_labels_v2.csv
```

Always Correct and token-overlap remain inside `src/compare_methods.py`. Do not add aliases or references from these responses before the primary run.

### Gate D — Blind human labels on all 200

Prepare an annotation sheet from the template with id, question, model answer, 2020 answer, historical answer(s), and evidence — **no automatic predictions**. Annotators use `docs/annotation_protocol.md`.

Save `data/full_200_new_human_labels.csv` with `id,human_label` (plus notes and evidence as required).

**House Outdated rule:** an earlier name counts as Outdated only if the response clearly names that person for the numbered district and they were not the 15 December 2020 representative. Clear name variants are acceptable for human labels; the automatic exact matcher remains exact.

Prefer a second annotator on a subset; store initial and reconciled labels separately. Copy finalized labels to a SHA-256 snapshot before analysis, for example `snapshots/full_200_new_human_labels_<date>_<hash8>.csv`. Keep any AI provisional review closed until labels are final, or disclose exposure.

### Gate E — Primary comparison

After updating analysis code to accept N=200:

```powershell
.\.venv\Scripts\python.exe src/compare_methods.py `
  --questions data/full_questions_200_new.csv `
  --responses data/full_200_new_model_responses.csv `
  --human-labels data/full_200_new_human_labels.csv `
  --audit data/full_fact_audit_200_new.csv `
  --output-dir results/verification_200_new_full
```

**Predeclared analysis rules**

- Primary: three-class macro-F1 on 200 labels.
- Secondary: agreement, Cohen's kappa, per-class precision/recall/F1/support, confusion matrices.
- Hypothesis rule (unchanged): Outdated recall exceeds Irrelevant recall **and** the 95% bootstrap CI for the difference lies wholly above 0; observed difference ≤ 0 → not supported; positive difference whose CI includes 0 → inconclusive.
- If any human class has support 0: three-class macro-F1 is **not estimable** — do not redraw the sample.
- Error analysis: categorize all proposed-matcher errors if fewer than 30; if 30 or more, either all errors or a predeclared sampling rule.
- Ablation: exact versus year-token on the same 200.
- Exploratory reference expansion: separate directory and name only.
- Also report (descriptive, secondary): metrics stratified by source (SituatedQA vs House), without using that split to retune.

---

## Implementation list (code and docs)

1. **`src/compare_methods.py`** — allow 200 rows (or `--expected-n 200`); keep ID-set equality checks.
2. **`src/prepare_ai_assisted_label_draft.py`** (if reused) — same N and new paths.
3. **`docs/build_assignment4_part3.py`** — point to `results/verification_200_new_full/`, use N=200 narrative, disclose mix, prior-ID overlap, and this amendment.
4. Align `docs/new_200_experiment_plan.md` and the annotation protocol so primary evaluation is described as 200 labels under Option B.
5. **Do not change for primary:** matcher rules, token threshold 0.25, bootstrap seed `20261028`, Holm over three McNemars, prompt/model freeze.
6. **Skip for Option B primary:** creating `verification_questions_200_new.csv` as the primary set; filtering responses down to 50.

---

## Appendix A fields to record

- Approval date and how approval was given
- Moodle original protocol upload: 30 October 2026, 11:37 AM
- Prior 122/50 amendment date: 1 November 2026
- This Option B freeze date: ____
- Question / audit / House hashes (table above)
- Response file hash and metadata hash
- Human-label snapshot hash
- Analysis script hash and results directory
- Model, provider, temperature, tools, delay, wall-clock
- Annotator identity/date(s); second-annotator subset size if any
- Statement that evaluation labels were not used to revise rules, thresholds, or references before the primary result

---

## Reporting outline (Part 3 under this amendment)

1. State Option B amendment and 122 + 78 composition.
2. Execution: one fresh 200-response Groq run; 200 blind labels.
3. Table: four methods — macro-F1, 95% CI, agreement /200, kappa.
4. Proposed per-class metrics and confusion matrix.
5. Paired differences versus three baselines, McNemar, and Holm.
6. Hypothesis decision under the frozen rule.
7. Error analysis and year-token ablation.
8. Limitations: House topic concentration; overlap with prior pilot/verification IDs; label provenance; single model/prompt; class imbalance.
9. Archive note: previous 50-label SituatedQA primary result is separate and not silently replaced.
10. Exploratory analyses clearly labeled non-primary.

---

## Bottom line

Approved Option B evaluates the matcher on all 200 mixed-source questions with 200 blind labels. Keep methods frozen; change N, files, Part 3 narrative, and the hard `!= 50` gate in `compare_methods.py`. Do not treat automatic labels on 200 as accuracy. Preserve old 50-label artifacts.
