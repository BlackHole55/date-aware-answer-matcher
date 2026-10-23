# Automatic matching rules

The classifier compares the short model answer with the selected benchmark answer for 2020 and then with distinct earlier answers. It applies Unicode NFKC normalization, case folding, whitespace collapse, and removal of punctuation at the two ends. It does **not** use substring or fuzzy matching.

Priority is fixed:

1. An exact normalized 2020 answer is `Correct`.
2. An exact normalized earlier answer is `Outdated`.
3. Any other nonempty response is `Irrelevant`.

The output join requires a nonempty answer for every selected ID. A blank CSV cell is missing data and causes an error. The `classify` function itself maps an empty string to `Irrelevant` so its three-class behavior remains defined, but incomplete input files are never scored.

This rule is deliberately conservative. For example, `Nine Network` will not match `Nine`, and `the Republican Party` will not match `Republican Party`. It avoids a worse false match such as `York` matching `New York`. Human annotators may label verified aliases and paraphrases according to the protocol. Disagreements should be coded as alias, extra text, benchmark error, overlapping historical fact, model error, or other before any rule change.

Do not tune the matching rules against the pilot's human labels and then report pilot agreement as an unbiased estimate. If the rules change, version them and evaluate on a held-out set.
