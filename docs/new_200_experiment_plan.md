# Plan: new 200-question date-aware answer experiment

## Objective and boundary

Evaluate whether the date-aware matcher labels short model answers as
`Correct`, `Outdated`, or `Irrelevant` for a **new 200-question corpus**.
Use `data/full_questions_200_new.csv`: 122 audited SituatedQA questions and
78 source-backed U.S. House district questions. The House questions ask about
15 December 2020 and have a distinct answer documented on 4 January 2011.
This mixed-source study is separate from the instructor-approved 122-question
run and its existing 50-label evaluation.

The primary result will be three-class macro-F1 on a newly selected,
human-labeled 50-question verification subset. Full-corpus automatic label
counts describe the 200 model responses; they are not accuracy estimates.
Freeze this plan, the question file, reference answers, matcher versions,
sampling procedure, model settings, and analysis code **before** inspecting
new responses or labels.

## 1. Final fact and file checks

1. Re-run `src/assemble_new_200_questions.py`. Confirm exactly 200 unique
   question IDs and 200 matching audit rows with `status=verified`. Record the
   SHA-256 hashes listed in `docs/new_200_question_set.md`.
2. Review the 78 House source rows against the two official Clerk rosters,
   using the page and text-line locators in
   `data/house_roster_78_verified.csv`. Check the named person, district
   number, both dates, and footnotes. Record reviewer and date. Resolve any
   error before model collection; preserve a dated exclusion/correction log
   and regenerate the combined set if a row changes.
3. Check that no question has a blank answer, a duplicate prompt, or an
   earlier answer that is also valid for the specified 2020 district and
   date. District numbers identify seats; their geographic boundaries may
   have changed between 2011 and 2020.

**Gate:** A frozen, source-backed 200-row question file and audit file.

## 2. Freeze a new verification subset

The prior 20-question pilot and prior 50-question verification set have
already informed this project. Exclude their IDs from the **new primary
verification subset**. This leaves 130 eligible questions: 52 SituatedQA and
78 House. Before collecting new responses, sort eligible IDs within source,
use `random.Random(20261103)` to sample **31 SituatedQA and 19 House**
questions without replacement, and save them in full-question-file order as
`data/verification_questions_200_new.csv`. These counts approximate the
122:78 source mix of the full corpus. Save the selection script, seed, file
hash, and excluded prior IDs. Do not revise the subset after seeing answers,
predictions, or human labels.

The 50-item result estimates performance on this reserved subset. Its
exclusion of previously used IDs and its source stratification should be
reported when interpreting generalizability to all 200 questions.

**Gate:** Exactly 50 frozen IDs, no pilot or prior-verification overlap, and
31/19 source counts.

## 3. Collect one model answer per question

Use the prior named model (`openai/gpt-oss-120b` through Groq), the exact
short-answer prompt in `src/generate_responses.py`, temperature 0, and tool
choice `none` for all 200 questions. Collect all 200 afresh so their
responses share one run's settings and timing. Save to a new response path
and retain its `.metadata.json` file. Set the request delay after checking
the provider's rate limit at run time. If that model is unavailable, freeze
one replacement model and collect all 200 with it.

```powershell
.\.venv\Scripts\python.exe src/generate_responses.py `
  --questions data/full_questions_200_new.csv `
  --audit data/full_fact_audit_200_new.csv `
  --output data/full_200_new_model_responses.csv `
  --base-url https://api.groq.com/openai/v1 `
  --model openai/gpt-oss-120b `
  --delay 2.1
```

The `2.1` second delay is the previous project setting, subject to the
run-time rate-limit check. Record model identifier, provider, prompt,
temperature, tool setting, run times, code version, and file hashes. Check
that the saved response IDs match all 200 question IDs exactly and that every
answer is nonblank. Do not use the prior 122 responses in a file presented as
one fresh run.

**Gate:** 200 nonblank responses with reproducible metadata.

## 4. Apply the frozen matchers

Run the existing exact and exact-plus-year-token matchers on the same
200-response file. Save outputs under new names:

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

Also retain the two frozen baselines from `src/compare_methods.py`:
Always Correct and SQuAD-style token overlap. Make no reference additions,
threshold changes, or alias rules based on the new verification responses.
Check one prediction per question for each method.

## 5. Obtain blind human labels

Filter the 200 responses to the frozen 50 IDs:

```powershell
.\.venv\Scripts\python.exe src/filter_to_questions.py `
  --questions data/verification_questions_200_new.csv `
  --input data/full_200_new_model_responses.csv `
  --output data/verification_200_new_model_responses.csv
```

Prepare an annotation sheet
with ID, question, model answer, 2020 answer, historical answer, and source
evidence, but **no automatic predictions**. Have an annotator apply
`docs/annotation_protocol.md` independently, recording `Correct`,
`Outdated`, or `Irrelevant`, notes for ambiguous cases, and evidence for
unlisted historical answers. Record annotator identity and date; preserve
their original decisions. A second annotator should independently label a
subset, with initial agreement and any reconciliation recorded separately.

In House cases, an earlier representative is `Outdated` only when the
response clearly names that person for the specified numbered district and
the person was no longer its representative on 15 December 2020. Accept clear
name variants in human labels; the automatic exact rule remains unchanged.

**Gate:** 50 nonblank labels, the original blind sheet preserved, and no
automatic labels shown to the annotator.

## 6. Analyze and report

Use `src/compare_methods.py` with the **new** 50 questions, filtered
responses, blind labels, new audit, and a new output directory. It requires
exactly 50 rows, so verify all input IDs before running:

```powershell
.\.venv\Scripts\python.exe src/compare_methods.py `
  --questions data/verification_questions_200_new.csv `
  --responses data/verification_200_new_model_responses.csv `
  --human-labels data/verification_200_new_human_labels.csv `
  --audit data/full_fact_audit_200_new.csv `
  --output-dir results/verification_200_new
```

Predeclare
three-class macro-F1 as primary. Report agreement, Cohen's kappa, per-class
precision/recall/F1/support, confusion matrices, and the two source-specific
descriptive breakdowns. Use the comparison script's 10,000 class-stratified
bootstrap resamples and frozen seed `20261028` for 95% intervals. Compare the proposed matcher
with the three baselines using paired macro-F1 differences, exact McNemar
tests on correct/incorrect decisions, and Holm correction across the three
tests. The current script requires all three human classes. Before looking
at labels, specify a not-estimable output path if a class is absent; do not
redraw the verification sample after viewing labels.

Review every proposed-matcher disagreement with the blind label. Classify
errors such as aliases, longer responses, missing historical references,
date ambiguity, and incorrect source facts. Keep any revised matcher or
expanded reference list in a separately named exploratory analysis.

Report the 122/78 source mix, the House topic concentration, selection seed,
fact-audit procedure, model collection settings, 50-item primary sample,
uncertainty intervals, and limitations. Present the prior 122-question
evaluation separately. If this new mixed-source set is to replace the
approved assignment sample, obtain instructor approval for that protocol
change before presenting its results as the approved study.
