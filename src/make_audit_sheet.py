"""Create a fact-checking sheet for selected SituatedQA questions."""

import argparse
import csv
from pathlib import Path

from date_compare import read_csv


ROOT = Path(__file__).resolve().parents[1]
FIELDS = (
    "id", "question", "current_answer", "historical_answers",
    "status", "evidence_url", "notes",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path, default=ROOT / "data/sample_questions.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "data/fact_audit.csv")
    parser.add_argument("--previous", type=Path,
                        help="Copy matching statuses and evidence from an earlier audit sheet")
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"Audit sheet already exists: {args.output}; refusing to overwrite it")
    questions = read_csv(args.questions, ("id", "question", "current_answer", "historical_answers"))
    previous = {}
    if args.previous:
        previous = {row["id"]: row for row in read_csv(args.previous, ("id", "status"))}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in questions:
            old = previous.get(row["id"], {})
            if any(old.get(field) != row[field] for field in
                   ("question", "current_answer", "historical_answers")):
                old = {}
            writer.writerow({
                "id": row["id"],
                "question": row["question"],
                "current_answer": row["current_answer"],
                "historical_answers": row["historical_answers"],
                "status": old.get("status", "pending"),
                "evidence_url": old.get("evidence_url", ""),
                "notes": old.get("notes", ""),
            })
    print(f"Wrote {len(questions)} pending fact checks to {args.output}")


if __name__ == "__main__":
    main()
