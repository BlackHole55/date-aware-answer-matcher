# Human annotation protocol

**Unit:** one free-form model response to one SituatedQA question asking for an answer **as of 2020**. `current_answer` in the CSV is the dataset's proposed 2020 answer; `historical_answers` contains proposed earlier answers. Neither field is authoritative until the fact audit is complete.

## First: verify the source fact

Before collecting or labeling model responses, use `data/fact_audit.csv` for the pilot and `data/full_fact_audit.csv` for the full study. Check the exact question wording, that the proposed 2020 answer was valid in 2020, and that each earlier answer had ceased to be valid by then. Use dated, attributable evidence. Set `status=verified` only when the distinction is defensible; otherwise set `status=excluded` with the reason. The scripts reject pending or excluded selected rows. Replace excluded rows before collection or scoring.

Watch for questions with multiple valid answers, an event that changed during 2020, an older answer that remained valid, or a dataset answer that responds to a different interpretation of the question. A year-only question may need a clearer date to be valid; document or exclude it rather than guessing.

## Then: label the model answer blind

Do not view `auto_label` while assigning human labels. For every verified question and nonblank response, use exactly one of:

- **Correct:** the response clearly gives the answer valid for the question's 2020 interpretation, including an unambiguous alias or short explanatory phrase.
- **Outdated:** the response gives only an answer that was valid earlier and had ceased to be valid by 2020.
- **Irrelevant:** the response gives another answer, refuses, or is too vague or mixed to determine the answer valid in 2020.

If a response mentions both the 2020 and an older answer, label it `Correct` only when it clearly identifies the 2020 answer as the one valid in 2020. Otherwise use `Irrelevant` and explain the ambiguity. A blank model-response cell means collection is incomplete; the evaluator will reject it.

Record `id,human_label` in `data/human_labels.csv` for the pilot or `data/verification_human_labels.csv` for the held-out subset. Keep useful `notes` and `evidence_url` in those files. For the full study, have a second person independently label a subset if available; save initial decisions, reconcile disagreements, and report the number of differing decisions. Report the reference year, audit exclusions, sample size, model/provider, prompt, and annotation date with each result.
