"""Version 2: exact matching, then unambiguous four-digit-year matching."""

import argparse
import csv
import re
from pathlib import Path

from date_compare import ROOT, classify, join_and_classify, normalize, read_csv


YEAR = re.compile(r"(?<!\d)[0-9]{4}(?!\d)")
YEAR_ONLY = re.compile(r"[0-9]{4}")


def classify_v2(model_answer, current_answer, historical_answers):
    """Apply the frozen exact rule before the prespecified year-token extension."""
    exact_label = classify(model_answer, current_answer, historical_answers)
    if exact_label != "Irrelevant":
        return exact_label

    response_years = set(YEAR.findall(normalize(model_answer)))
    if not response_years:
        return "Irrelevant"

    current_year = normalize(current_answer)
    historical_years = {normalize(answer) for answer in historical_answers}
    historical_years = {year for year in historical_years if YEAR_ONLY.fullmatch(year)}
    reference_years = historical_years.copy()
    if YEAR_ONLY.fullmatch(current_year):
        reference_years.add(current_year)

    matched = response_years & reference_years
    if len(matched) != 1:
        return "Irrelevant"
    year = next(iter(matched))
    return "Correct" if year == current_year else "Outdated"


def join_and_classify_v2(questions, responses):
    """Reuse version 1's validated join, changing only the matching rule."""
    rows = join_and_classify(questions, responses)
    for row in rows:
        historical = [answer.strip() for answer in row["historical_answers"].split("|") if answer.strip()]
        row["auto_label"] = classify_v2(row["model_answer"], row["current_answer"], historical)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path, default=ROOT / "data/sample_questions.csv")
    parser.add_argument("--responses", type=Path, default=ROOT / "data/model_responses.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "data/auto_labels_v2.csv")
    args = parser.parse_args()
    questions = read_csv(args.questions, ("id", "current_answer", "historical_answers"))
    responses = read_csv(args.responses, ("id", "model_answer"))
    rows = join_and_classify_v2(questions, responses)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} version 2 automatic labels to {args.output}")


if __name__ == "__main__":
    main()
