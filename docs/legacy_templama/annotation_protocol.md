# Human annotation protocol

**Unit:** one model answer to one TempLAMA cloze statement. The question asks for the answer **as of 2020**. Use the selected 2020 benchmark answer and the earlier answers as starting evidence, while checking doubtful or overlapping facts against a reliable source. The benchmark may contain errors.

Before labeling, check whether the statement has a unique answer for 2020 and whether each earlier answer had ceased to hold by then. Set aside and document a row whose source fact cannot be resolved. Replace it before freezing the evaluation sample; do not force it into a class.

Apply one label without looking at the automatic label:

- **Correct:** the response gives the 2020 answer, including an unambiguous alias or a short phrase containing that answer.
- **Outdated:** the response gives only a historically valid answer that no longer held in 2020.
- **Irrelevant:** the response gives another answer, a refusal, or an answer too vague or mixed to determine the 2020 answer.

If an answer mentions both the 2020 and an older answer, label `Correct` only when it clearly identifies the 2020 answer as the one valid in 2020. Otherwise, label `Irrelevant` and note ambiguity. A blank `model_answer` in the input CSV means collection is incomplete and should not be annotated or scored.

Record `id,human_label` in `data/human_labels.csv`. Optional extra columns such as `notes`, `evidence_url`, and `error_category` are preserved in the source annotation file, though the analysis export includes only `human_label`. Use one annotator for the pilot; for the full study, have a second person independently annotate a subset and reconcile disagreements. Report the reference year, sample size, excluded facts, model/provider, prompt, and annotation date with every metric.
