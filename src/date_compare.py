"""Deterministic three-class matching of short model answers."""

import argparse
import csv
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LABELS = ("Correct", "Outdated", "Irrelevant")


def normalize(value):
    value = unicodedata.normalize("NFKC", value or "").casefold().strip()
    value = re.sub(r"\s+", " ", value)
    return value.strip(" \t\r\n.,;:!?'\"()[]{}")


def classify(model_answer, current_answer, historical_answers):
    answer = normalize(model_answer)
    if not answer:
        return "Irrelevant"
    if answer == normalize(current_answer):
        return "Correct"
    if any(answer == normalize(past) for past in historical_answers):
        return "Outdated"
    return "Irrelevant"


def read_csv(path, required):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not set(required).issubset(reader.fieldnames):
            raise ValueError(f"{path} needs columns: {', '.join(required)}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"{path} has no data rows")
    for row in rows:
        row["id"] = row["id"].strip()
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)) or any(not item for item in ids):
        raise ValueError(f"{path} has duplicate or blank IDs")
    return rows


def join_and_classify(questions, responses):
    by_id = {r["id"]: r for r in responses}
    question_ids = {r["id"] for r in questions}
    if set(by_id) != question_ids:
        missing = sorted(question_ids - set(by_id))
        extra = sorted(set(by_id) - question_ids)
        raise ValueError(f"Response IDs must exactly match question IDs; missing={missing[:5]}, extra={extra[:5]}")
    output = []
    for question in questions:
        response = by_id[question["id"]]
        if not question["current_answer"].strip() or not question["historical_answers"].strip():
            raise ValueError(f"Missing benchmark answer for {question['id']}")
        if not response["model_answer"].strip():
            raise ValueError(f"Missing model answer for {question['id']}")
        past = [x.strip() for x in question["historical_answers"].split("|") if x.strip()]
        output.append({
            **question,
            "model_answer": response["model_answer"],
            "auto_label": classify(response["model_answer"], question["current_answer"], past),
        })
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path, default=ROOT / "data/sample_questions.csv")
    parser.add_argument("--responses", type=Path, default=ROOT / "data/model_responses.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "data/auto_labels.csv")
    args = parser.parse_args()
    questions = read_csv(args.questions, ("id", "current_answer", "historical_answers"))
    responses = read_csv(args.responses, ("id", "model_answer"))
    rows = join_and_classify(questions, responses)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} automatic labels to {args.output}")


if __name__ == "__main__":
    main()
