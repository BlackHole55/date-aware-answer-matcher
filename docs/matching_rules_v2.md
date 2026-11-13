# Version 2 automatic matching rule

`src/date_compare_v2.py` implements the proposed comparison condition in the Assignment 4 protocol draft. The original `src/date_compare.py` remains the exact-match baseline.

Version 2 applies the original normalization and exact-match priority first. If neither reference matches exactly, it looks for a reference answer that consists solely of a four-digit year. A year can match only when it occurs as a standalone four-digit token in the normalized model response. If the response contains two different reference years, the result is `Irrelevant`; otherwise the matching current year gives `Correct` and a matching historical year gives `Outdated`. Other responses remain `Irrelevant`.

Run the versioned classifier on the pilot with:

```powershell
python src/date_compare_v2.py --output data/auto_labels_v2.csv
```

For descriptive pilot metrics, run the evaluator with separate output paths:

```powershell
python src/evaluate.py --matcher year-token --analysis data/analysis_table_v2.csv --results results/v2
```

This narrow extension can recognize a year in a phrase such as `April 2019 (Masters)` when the reference is `2019`. It does not resolve aliases, incorrect facts, explanatory phrases without a standalone reference year, or responses that name an earlier year absent from `historical_answers`. It also cannot determine whether a mentioned year is asserted or negated. Human review remains necessary.

Pilot agreement after a rule change is descriptive because the pilot informed the revision. Evaluate the frozen rule on the held-out 50-item verification subset only after the remaining facts are audited and human labels are assigned blind. Preserve both versions' outputs for the planned comparison.

## Post-collection reference-coverage finding (1 November 2026)

All 122 amended full-study rows, including all 50 held-out rows, contain exactly one distinct `historical_answers` value. The selector loops over all distinct earlier answers in the source records; it does not truncate them to one. The source records for these selected IDs themselves provide only one distinct older answer, even where that answer is repeated across several dates. Thus the exact and year-token matchers can return `Irrelevant` for a factually earlier valid response that is absent from the source reference field.

This is a measured limitation of the frozen primary matching conditions. Human annotators should use dated evidence and the class definitions in [annotation_protocol.md](annotation_protocol.md), not the number of source historical references, to decide whether a response is `Outdated`. A separate provisional AI review identifies five possible held-out examples, but the human annotator should not open it until all labels are finalized. Those AI judgments are not human labels. Any sourced-reference expansion chosen after seeing full-study responses is exploratory and must be reported separately from the frozen primary comparison.

An [exploratory sourced-reference expansion](exploratory_reference_expansion.md) has been prepared for 15 full-study questions. Its separate matcher can be evaluated after human labels are finalized; five of those questions are in the held-out verification set.

The human-label sheet had 12 nonblank label cells when this clarification was recorded; their values were not inspected or changed. The annotator should revisit any labels assigned solely by checking membership in `historical_answers`, using the same dated-evidence standard, before finalizing all 50 labels. This clarifies the existing `Outdated` definition and does not alter the frozen automatic matcher.
