# Assignment 4: proposed amendment to the frozen protocol

**Status:** Superseded by the [approved amendment record](protocol_amendment_record.md) after the student reported instructor approval on 1 November 2026. The original Moodle submission was uploaded on Friday, 30 October 2026 at 11:37 AM.

## Text for “Deviations from the Frozen Protocol”

After the protocol freeze and before collecting any full-study model responses or held-out human labels, the dated fact audit of all 200 selected SituatedQA questions found 122 valid questions and 78 exclusions. The exclusion reasons and evidence are recorded in `data/full_fact_audit.csv` and `data/situatedqa_exclusions.csv`. All 20 pilot questions are among the 122 verified questions. Of the 50 originally reserved non-pilot verification questions, 33 remain valid and 17 were excluded. Only five eligible questions were left outside the original selection, so replacing all 78 exclusions while preserving the frozen 200-question count is impossible.

**Proposed sample change.** Use the 122 verified questions already in the original 200-question list, in their original file order, as the amended full-study set. This includes the 20 pilot questions; 102 verified non-pilot questions remain. Do not introduce new question IDs. Keep the original frozen files unchanged as an archive. Write the amended question list to a new versioned file and record its SHA-256 hash, row count, and creation date after approval.

**Proposed verification-set change.** Retain the 33 valid IDs from the original 50-question verification list. Fill the 17 vacancies from the other 69 verified non-pilot questions. Construct that pool in the order in which IDs occur in the original `data/full_questions.csv`, shuffle it with Python `random.Random(19).shuffle`, and take its first 17 rows. This yields 50 verified, non-pilot questions. Record the new list, selection code version, SHA-256 hash, and date after approval. Complete this selection before collecting full-study model responses or held-out labels.

**Experimental procedure and analysis.** Run the frozen answer-collection procedure on the amended 122-question list using the prespecified model, prompt, temperature, and other settings. Keep the pilot analysis separate from the final held-out analysis. Apply the four prespecified classification conditions to the same full-study responses. Obtain blind human labels for the amended 50-question verification set. Keep the prespecified primary outcome (three-class macro-F1 on those 50 labels), secondary metrics, bootstrap confidence intervals, McNemar tests, Holm correction, and prohibition on tuning against the held-out labels. Report the reduced full-study size and the audit exclusions as limitations. No full-study responses or held-out labels were examined in making this proposal.

**Approval and record.** Obtain instructor approval for the changed sample size, IDs, and verification list before generating the amended canonical files or collecting full-study responses. Record the approval date, amended file hashes, code version, and this deviation in Appendix A and the final report. Preserve the original submitted lists and hashes for comparison:

- `data/full_questions.csv`: `db1c148c02c80a95435a5d230f020de2fcb3077786231b5863916ae9f9b45f2b`
- `data/verification_questions.csv`: `abe91b5efc54ea95a5f12071567d1eaa7e4c5e51171f3c3ee0c5f71871dba13f`
