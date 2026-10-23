# SituatedQA temporal QA source

Downloaded on **2026-10-22** from the official [SituatedQA repository](https://github.com/mikejqzhang/SituatedQA), `master/data/qa_data/`:

- [`temp.train.jsonl`](https://raw.githubusercontent.com/mikejqzhang/SituatedQA/master/data/qa_data/temp.train.jsonl) saved as `situatedqa_temp_train.jsonl`; SHA-256 `e9d837cb75fd1fa35a1609e6397b20ab0ba2f73bda524e2ed8f5a41cab8c1084`; 6,009 rows.
- [`temp.dev.jsonl`](https://raw.githubusercontent.com/mikejqzhang/SituatedQA/master/data/qa_data/temp.dev.jsonl) saved as `situatedqa_temp_dev.jsonl`; SHA-256 `d1e5bc51a1e775ed7ea569ff76368c0f54d180b49e81c251a22ff3dc7d57a8b7`; 3,423 rows.

The original files are retained unchanged. The official test split was not used. The dataset is described in Zhang and Choi, *SituatedQA: Incorporating Extra-Linguistic Contexts into QA*, EMNLP 2021; see the [project site](https://situatedqa.github.io/) and [datasheet](https://situatedqa.github.io/src/situatedqa_datasheet.pdf).

The project selects candidates with a single 2020 answer and at least one distinct earlier single answer. It excludes conflicting dated answers within 2020, conflicting same-year older answers, composite earlier answers, and several wording patterns that are often ambiguous for this task. The downloaded files yield 224 structurally eligible candidates with the current selector. A separate [exclusion log](../situatedqa_exclusions.csv) now records 19 further rows found wrong or unsuitable during inspection, leaving 205. **This is still not factual verification of the remaining rows.** The 20 pilot rows have been fact checked; the other 180 rows in the full-study selection remain pending.

The older TempLAMA source and its provenance are documented in [README.md](README.md). Its selected question files and collected responses are under `data/legacy_templama/`.
