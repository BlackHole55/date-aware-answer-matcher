# Automatic matching rules

For each verified SituatedQA question, the classifier compares the short model response to the selected dataset answer for 2020 and then to distinct earlier answers. It applies Unicode NFKC normalization, case folding, whitespace collapse, and removal of punctuation at the two ends. It does **not** use substring or fuzzy matching.

The priority is fixed:

1. Exact normalized match to the verified 2020 answer: `Correct`.
2. Exact normalized match to a verified earlier answer: `Outdated`.
3. Any other nonempty response: `Irrelevant`.

The input join requires a nonempty response for every selected ID. A blank CSV cell means missing data and causes an error. `evaluate.py` also requires `status=verified` in the corresponding fact-audit CSV for every selected SituatedQA ID.

This rule is intentionally conservative. An alias, alternative number format, or extra phrase may be judged `Correct` or `Outdated` by a human but `Irrelevant` by the matcher. Record these as disagreements. Do not tune a rule on the pilot and report the same pilot agreement as an unbiased estimate; version any change and evaluate on the untouched 50-item subset.
