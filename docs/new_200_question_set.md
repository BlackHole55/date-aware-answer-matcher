# New 200-question experiment set

This is a **new, mixed-source experiment set**. It does not replace the frozen
200-question SituatedQA selection, the approved 122-question amendment, the
50-question verification subset, or their saved responses and results.

The question file is `data/full_questions_200_new.csv`; its matching fact
audit is `data/full_fact_audit_200_new.csv`. The first 122 questions, in their
existing order, are the audited questions from
`data/full_questions_amended.csv`. The remaining 78 are new U.S. House
district questions in `data/house_roster_78_verified.csv`. All 200 audit rows
have `status=verified`.

Frozen SHA-256 hashes for this set:

- Questions: `3a50905fdbe919a5b61e2291248c654437464ae6e2c0fe8a40af47cf1993e67d`
- Audit: `ff05019314b5b14c042e1e7a610228e6876761d84fa959179a42d9bb6f373cdc`
- House source rows: `a262e442b1808896908cf51b9300e01c4c013b75cebb7a36a7b93e4c3b75b3e9`

## How the 78 new facts were checked

The new questions ask who represented a state's numbered U.S. House district
**on December 15, 2020**. The current answer comes from the [Clerk's official
116th Congress member list dated December 15, 2020](https://historycms.house.gov/WorkArea/DownloadAsset.aspx?id=25769816718).
The historical answer comes from the [Clerk's official 111th Congress final
member list dated January 4, 2011](https://historycms.house.gov/WorkArea/DownloadAsset.aspx?id=41208).
Each source row records the PDF page and extracted text line for both names.
Only numbered districts with a named representative in both lists and
different names were eligible. Vacancies and at-large seats were excluded.
The 78 selected districts span 43 states. A numbered district may have had
different boundaries in 2011 and 2020; the question refers to the numbered
seat, not a fixed geographic area.

To spread the additional questions across states, the extraction selected
one eligible district from each of the 43 states with a dated answer change,
then a second district from 35 of those states. The selection used a fixed
linear-congruential pseudorandom sequence initialized to `20201103`; the
selected IDs and both source locators are frozen in
`data/house_roster_78_verified.csv`. The two official rosters are the
evidence for the name/date claims; no model answer or automatic label was
used in selection.

## Regenerate and use

From the project root:

```powershell
.\.venv\Scripts\python.exe src/assemble_new_200_questions.py
.\.venv\Scripts\python.exe src/make_templates.py --questions data/full_questions_200_new.csv --prefix full_200_new
```

The assembly script validates the 122 existing audit records, the 78 new
source records, distinct dated answers, all required evidence fields, and
unique IDs and question texts. It writes the combined question and audit CSVs
without altering the approved 122-question files.

For new model collection, use the combined file with
`--questions data/full_questions_200_new.csv` and
`--audit data/full_fact_audit_200_new.csv`, and choose a **new output path**.
If reusing the already collected 122 model responses, retain their original
metadata and document exactly how the 78 new responses were collected and
merged. The earlier 50 human labels do not evaluate the full new sample.

Because 78 of 200 questions concern U.S. House seats, this corpus has a
different topic mix from the SituatedQA-only study. Report it as a new
experiment, including the two source counts, and obtain a new blind
verification sample if estimating classifier performance on this corpus.
