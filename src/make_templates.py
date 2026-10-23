"""Make blank response and human-annotation sheets with the selected IDs."""

import argparse
import csv
from pathlib import Path

from date_compare import read_csv


ROOT = Path(__file__).resolve().parents[1]


def write_template(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path, default=ROOT / "data/sample_questions.csv")
    parser.add_argument("--prefix", default="pilot")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/templates")
    args = parser.parse_args()
    questions = read_csv(args.questions, ("id", "question"))
    response_path = args.output_dir / f"{args.prefix}_model_responses.csv"
    human_path = args.output_dir / f"{args.prefix}_human_labels.csv"
    write_template(response_path, ["id", "model_answer"],
                   ({"id": row["id"], "model_answer": ""} for row in questions))
    write_template(human_path, ["id", "human_label", "notes", "evidence_url"],
                   ({"id": row["id"], "human_label": "", "notes": "", "evidence_url": ""} for row in questions))
    print(f"Wrote {response_path} and {human_path}")


if __name__ == "__main__":
    main()
