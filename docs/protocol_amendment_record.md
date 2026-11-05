# Assignment 4 — approved protocol amendment and implementation record

**Approval:** The student reported instructor approval on 1 November 2026. The exact approval timestamp and written approval record were not provided. The original protocol was uploaded to Moodle on Friday, 30 October 2026 at 11:37 AM.

## Reason and approved change

The fact audit was completed before collecting full-study model responses or held-out human labels. Of the 200 frozen questions, 122 were verified and 78 excluded. All 20 pilot questions were verified. The original 50-question verification list contained 33 verified questions and 17 exclusions. Only five eligible questions remained unused outside the original 200, so the frozen count of 200 could not be restored by replacement.

The amended full-study list contains the 122 verified original questions in original file order: 111 train and 11 development, including 20 pilot questions. No new question IDs were introduced. The amended 50-question verification list retains the 33 verified original verification IDs in their original order. It appends 17 IDs drawn from the other 69 verified non-pilot questions: take those candidates in original full-list order, apply Python `random.Random(19).shuffle`, and use the first 17. The final verification list has 45 train and five development questions and does not overlap the pilot.

The frozen model, prompt, collection settings, four classification conditions, blind annotation procedure, primary three-class macro-F1 on 50 human-labelled responses, secondary measures, bootstrap intervals, McNemar tests, Holm correction, and no held-out tuning rule remain as specified. Pilot analysis remains separate. The reduced full-study size and exclusions must be disclosed in the final report.

## Reproduction and file identity

Run `src/apply_protocol_amendment.py` from the project environment to regenerate the amended lists. It checks the two original frozen hashes and the audit hash before writing. Its SHA-256 is `e76e72b841033df2c138b70c52bfdd01c840f151b29202f932a9589b4abbb440`; repository HEAD at generation was `5263a3bb4e8f2fca5dbc72dbdcbda9a4c6d6bfaf` (the script and audit updates were uncommitted, so use their file hashes as the exact version record).

- Original `data/full_questions.csv`: 200 rows, SHA-256 `db1c148c02c80a95435a5d230f020de2fcb3077786231b5863916ae9f9b45f2b`.
- Original `data/verification_questions.csv`: 50 rows, SHA-256 `abe91b5efc54ea95a5f12071567d1eaa7e4c5e51171f3c3ee0c5f71871dba13f`.
- Audit `data/full_fact_audit.csv`: 200 rows, SHA-256 `2c0f5e31c05a036d866db6bb36359bab5006c825b03fe9567fb65c3e7ecd7330`.
- Amended `data/full_questions_amended.csv`: 122 rows, SHA-256 `47c376a61df033b41580091035ae5222aa4cc59bfa25abd3b364e3a7eb6ac474`.
- Amended `data/verification_questions_amended.csv`: 50 rows, SHA-256 `62345459e55ca6e0dc9aea8d5b1499bf0c9cab37187aed20ae4f6d6a50339d5f`.

The original submitted CSVs remain unchanged. Blank response and annotation templates for both amended lists are in `data/templates/` with `full_amended_` and `verification_amended_` prefixes. The exclusion decisions remain in `data/full_fact_audit.csv` and `data/situatedqa_exclusions.csv`.
