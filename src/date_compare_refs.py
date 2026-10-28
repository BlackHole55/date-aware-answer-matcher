"""Exploratory matcher using independently sourced pilot reference variants."""

import argparse
import csv
from collections import defaultdict
from pathlib import Path

from date_compare import ROOT, join_and_classify, normalize, read_csv
from date_compare_v2 import YEAR, YEAR_ONLY


DEFAULT_REFERENCES = ROOT / "data/pilot_reference_supplement.csv"
REQUIRED = {"id", "label", "answer", "evidence_url", "reason"}


def load_references(path, questions):
    """Load sourced variants, rejecting unknown IDs and contradictory labels."""
    questions_by_id = {question["id"]: question for question in questions}
    additions = defaultdict(lambda: {"Correct": [], "Outdated": []})
    seen = {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not REQUIRED.issubset(reader.fieldnames):
            raise ValueError(f"{path} needs columns: {', '.join(sorted(REQUIRED))}")
        for line, row in enumerate(reader, start=2):
            item_id = (row["id"] or "").strip()
            label = (row["label"] or "").strip()
            answer = (row["answer"] or "").strip()
            source = (row["evidence_url"] or "").strip()
            reason = (row["reason"] or "").strip()
            if item_id not in questions_by_id or label not in additions[item_id] or not answer:
                raise ValueError(f"Invalid reference ID, label, or answer on line {line}")
            if not source.startswith("https://") or not reason:
                raise ValueError(f"Reference on line {line} needs an HTTPS evidence URL and reason")
            key = (item_id, normalize(answer))
            if key in seen:
                raise ValueError(f"Duplicate or conflicting reference for {item_id}: {answer!r}")
            seen[key] = label
            additions[item_id][label].append(answer)

    for item_id, question in questions_by_id.items():
        current = [question["current_answer"], *additions[item_id]["Correct"]]
        past = [*question["historical_answers"].split("|"), *additions[item_id]["Outdated"]]
        if {normalize(x) for x in current} & {normalize(x) for x in past}:
            raise ValueError(f"Current and historical references overlap for {item_id}")
    return additions


def classify_with_references(model_answer, current_answers, historical_answers):
    """Exact matching first, then one unambiguous year-only reference."""
    answer = normalize(model_answer)
    if not answer:
        return "Irrelevant"
    current = {normalize(value) for value in current_answers}
    past = {normalize(value) for value in historical_answers}
    if answer in current:
        return "Correct"
    if answer in past:
        return "Outdated"

    year_labels = {}
    for year in current:
        if YEAR_ONLY.fullmatch(year):
            year_labels[year] = "Correct"
    for year in past:
        if YEAR_ONLY.fullmatch(year):
            if year in year_labels:
                return "Irrelevant"
            year_labels[year] = "Outdated"
    matches = set(YEAR.findall(answer)) & year_labels.keys()
    return year_labels[next(iter(matches))] if len(matches) == 1 else "Irrelevant"


def join_and_classify_refs(questions, responses, references):
    rows = join_and_classify(questions, responses)
    for row in rows:
        additions = references.get(row["id"], {"Correct": [], "Outdated": []})
        current = [row["current_answer"], *additions["Correct"]]
        past = [*row["historical_answers"].split("|"), *additions["Outdated"]]
        row["auto_label"] = classify_with_references(row["model_answer"], current, past)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path, default=ROOT / "data/sample_questions.csv")
    parser.add_argument("--responses", type=Path, default=ROOT / "data/model_responses.csv")
    parser.add_argument("--references", type=Path, default=DEFAULT_REFERENCES)
    parser.add_argument("--output", type=Path, default=ROOT / "data/auto_labels_refs.csv")
    args = parser.parse_args()
    questions = read_csv(args.questions, ("id", "current_answer", "historical_answers"))
    responses = read_csv(args.responses, ("id", "model_answer"))
    references = load_references(args.references, questions)
    rows = join_and_classify_refs(questions, responses, references)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} exploratory reference labels to {args.output}")


if __name__ == "__main__":
    main()
