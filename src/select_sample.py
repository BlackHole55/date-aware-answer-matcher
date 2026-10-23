"""Select dated answer changes from the official SituatedQA temporal data."""

import argparse
import csv
import json
import random
import re
from collections import defaultdict
from pathlib import Path

from date_compare import normalize, read_csv


ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILES = (
    ("train", ROOT / "data/raw_benchmark/situatedqa_temp_train.jsonl"),
    ("dev", ROOT / "data/raw_benchmark/situatedqa_temp_dev.jsonl"),
)
FIELDNAMES = (
    "id", "question", "current_answer", "historical_answers",
    "reference_year", "source_dataset", "source_split", "source_id",
    "source_date", "historical_dates",
)
# These phrasings can refer to the reader's present or an unclear time span,
# even when the dataset appends "as of 2020".
AMBIGUOUS_WORDING = re.compile(
    r"\b(today|now|currently|last year|this year|next year|last season|"
    r"this season|next season|yesterday|tomorrow|ago|upcoming|record|"
    r"most|highest|best|largest|longest|contestants|teams|ranked|"
    r"ranking|episode)\b|\b(has|have) (won|ever)\b|\bwho (are|have)\b|"
    r"\b(last|previous) (presidential )?election\b|"
    r"\b(last|past) [0-9]+ (years|championships|times)\b",
    re.IGNORECASE,
)


def read_sources(source_files):
    grouped = defaultdict(list)
    for split, path in source_files:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                try:
                    row = json.loads(line)
                    source_id = str(row["id"])
                    question = row["question"].strip()
                    date = str(row["date"]).strip()
                    answers = row["answer"]
                    if not question or not date or not isinstance(answers, list):
                        raise ValueError("blank question/date or invalid answer list")
                except (ValueError, KeyError, TypeError, AttributeError) as exc:
                    raise ValueError(f"Invalid SituatedQA row in {path} at line {line_number}") from exc
                grouped[(split, source_id)].append(row)
    return grouped


def eligible_items(source_files=SOURCE_FILES, reference_year=2020):
    """Return conservative candidates; dated facts still require human audit."""
    year = str(reference_year)
    items = []
    for (split, source_id), rows in read_sources(source_files).items():
        current_rows = [row for row in rows if str(row["date"]) == year]
        if len(current_rows) != 1 or len(current_rows[0]["answer"]) != 1:
            continue
        current = current_rows[0]
        current_answer = current["answer"][0].strip()
        original_question = current["question"].strip()
        if (not current_answer or "|" in current_answer or
                AMBIGUOUS_WORDING.search(original_question)):
            continue

        # A different answer within the same calendar year makes a year-only
        # question ambiguous. Exact-date contexts use "Month DD, YYYY".
        if any(
            str(row["date"]).endswith(", " + year)
            and any(normalize(answer) != normalize(current_answer) for answer in row["answer"])
            for row in rows
        ):
            continue

        older_rows = [
            row for row in rows
            if str(row["date"]).isdigit()
            and len(str(row["date"])) == 4
            and int(row["date"]) < reference_year
            and len(row["answer"]) == 1
        ]
        # Reject conflicting answers assigned to the same earlier year.
        by_year = defaultdict(set)
        for row in older_rows:
            by_year[str(row["date"])].add(normalize(row["answer"][0]))
        if any(len(answers) > 1 for answers in by_year.values()):
            continue

        historical = []
        historical_dates = []
        seen = {normalize(current_answer)}
        for row in sorted(older_rows, key=lambda item: int(item["date"]), reverse=True):
            answer = row["answer"][0].strip()
            key = normalize(answer)
            if (not answer or "|" in answer or " / " in answer or not key
                    or key in seen or normalize(current_answer) in key):
                continue
            seen.add(key)
            historical.append(answer)
            historical_dates.append(str(row["date"]))
        if not historical:
            continue

        edited = current.get("edited_question", "").strip()
        question = edited if year in edited else f"{original_question} as of {year}"
        items.append({
            "id": f"sq-{split}-{source_id}",
            "question": question,
            "current_answer": current_answer,
            "historical_answers": "|".join(historical),
            "reference_year": year,
            "source_dataset": "SituatedQA temporal QA",
            "source_split": split,
            "source_id": source_id,
            "source_date": year,
            "historical_dates": "|".join(historical_dates),
        })
    return items


def select_items(items, size, seed, excluded_ids=()):
    ordered = sorted(items, key=lambda row: row["id"])
    random.Random(seed).shuffle(ordered)
    ordered = [row for row in ordered if row["id"] not in excluded_ids]
    if size < 1 or size > len(ordered):
        raise ValueError(f"Requested {size} items; {len(ordered)} candidates are available")
    return ordered[:size]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, default=SOURCE_FILES[0][1])
    parser.add_argument("--dev", type=Path, default=SOURCE_FILES[1][1])
    parser.add_argument("--output", type=Path, default=ROOT / "data/sample_questions.csv")
    parser.add_argument("--reference-year", type=int, default=2020)
    parser.add_argument("--size", type=int, default=20)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--exclude-audit", type=Path, action="append", default=[],
                        help="Audit CSV; rows with status=excluded are removed. May be repeated.")
    args = parser.parse_args()
    candidates = eligible_items((("train", args.train), ("dev", args.dev)), args.reference_year)
    excluded_ids = set()
    permanent_exclusions = ROOT / "data/situatedqa_exclusions.csv"
    audit_paths = ([permanent_exclusions] if permanent_exclusions.exists() else []) + args.exclude_audit
    for audit_path in audit_paths:
        audits = read_csv(audit_path, ("id", "status"))
        excluded_ids.update(row["id"] for row in audits if row["status"].strip().lower() == "excluded")
    selected = select_items(candidates, args.size, args.seed, excluded_ids)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(selected)
    print(f"Wrote {len(selected)} SituatedQA candidates to {args.output} from {len(candidates)} eligible rows")


if __name__ == "__main__":
    main()
