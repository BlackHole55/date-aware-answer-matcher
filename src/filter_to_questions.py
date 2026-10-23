"""Filter a response CSV to exactly the IDs in a selected question CSV."""

import argparse
import csv
from pathlib import Path

from date_compare import read_csv


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    questions = read_csv(args.questions, ("id",))
    rows = read_csv(args.input, ("id",))
    by_id = {row["id"]: row for row in rows}
    missing = [row["id"] for row in questions if row["id"] not in by_id]
    if missing:
        raise ValueError(f"Input is missing {len(missing)} selected IDs: {missing[:5]}")
    if args.input.resolve() == args.output.resolve():
        parser.error("Input and output must be different files")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(by_id[question["id"]] for question in questions)
    print(f"Wrote {len(questions)} rows to {args.output}")


if __name__ == "__main__":
    main()
