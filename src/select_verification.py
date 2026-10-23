"""Preselect a held-out verification subset, excluding pilot IDs."""

import argparse
import csv
import random
from pathlib import Path

from date_compare import read_csv


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full", type=Path, default=ROOT / "data/full_questions.csv")
    parser.add_argument("--pilot", type=Path, default=ROOT / "data/sample_questions.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "data/verification_questions.csv")
    parser.add_argument("--size", type=int, default=50)
    parser.add_argument("--seed", type=int, default=19)
    args = parser.parse_args()
    if args.size < 1:
        parser.error("--size must be positive")
    full = read_csv(args.full, ("id",))
    pilot_ids = {r["id"] for r in read_csv(args.pilot, ("id",))}
    pool = [row for row in full if row["id"] not in pilot_ids]
    if args.size > len(pool):
        parser.error(f"Requested {args.size} verification items; only {len(pool)} non-pilot items exist")
    random.Random(args.seed).shuffle(pool)
    selected = pool[:args.size]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(full[0]))
        writer.writeheader()
        writer.writerows(selected)
    print(f"Wrote {len(selected)} verification items to {args.output}")


if __name__ == "__main__":
    main()
