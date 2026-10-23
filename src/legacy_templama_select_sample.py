"""Select changed facts from the official TempLAMA JSONL test split."""

import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIELDNAMES = [
    "id", "question", "current_answer", "historical_answers",
    "reference_year", "relation", "source_id", "source_years",
]
DEFAULT_RELATIONS = ("P102", "P127", "P286", "P488", "P6")


def answer_names(record):
    return [item["name"].strip() for item in record.get("answer", []) if item.get("name", "").strip()]


def eligible_items(path, reference_year, relations=DEFAULT_RELATIONS):
    grouped = defaultdict(list)
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            try:
                record = json.loads(line)
                year = int(record["date"])
                source_id = record["id"].rsplit("_", 1)[0]
            except (ValueError, KeyError, TypeError) as exc:
                raise ValueError(f"Invalid source record at line {line_number}") from exc
            if year <= reference_year:
                grouped[source_id].append(record)

    items = []
    for source_id, records in grouped.items():
        current = [r for r in records if int(r["date"]) == reference_year]
        if len(current) != 1 or len(answer_names(current[0])) != 1:
            continue
        if current[0]["relation"] not in relations:
            continue
        current_name = answer_names(current[0])[0]
        older = sorted((r for r in records if int(r["date"]) < reference_year), key=lambda r: int(r["date"]))
        historical = []
        years = []
        for record in older:
            for name in answer_names(record):
                if name.casefold() != current_name.casefold() and name.casefold() not in {x.casefold() for x in historical}:
                    historical.append(name)
                    years.append(record["date"])
        if not historical or "|" in current_name or any("|" in name for name in historical):
            continue
        query = current[0]["query"].strip()
        if query.count("_X_") != 1:
            continue
        items.append({
            "id": source_id,
            "question": f"As of {reference_year}, fill in _X_: {query}",
            "current_answer": current_name,
            "historical_answers": "|".join(historical),
            "reference_year": str(reference_year),
            "relation": current[0]["relation"],
            "source_id": current[0]["id"],
            "source_years": "|".join(years),
        })
    return items


def stratified_sample(items, size, seed):
    if size > len(items):
        raise ValueError(f"Requested {size} items, but only {len(items)} are eligible")
    rng = random.Random(seed)
    by_relation = defaultdict(list)
    for item in items:
        by_relation[item["relation"]].append(item)
    for bucket in by_relation.values():
        rng.shuffle(bucket)
    result = []
    relations = sorted(by_relation)
    while len(result) < size:
        progress = False
        for relation in relations:
            if by_relation[relation] and len(result) < size:
                result.append(by_relation[relation].pop())
                progress = True
        if not progress:
            break
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data/raw_benchmark/templama_test.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "data/sample_questions.csv")
    parser.add_argument("--reference-year", type=int, default=2020)
    parser.add_argument("--size", type=int, default=20)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--relations", nargs="+", default=DEFAULT_RELATIONS,
                        help="Wikidata relation IDs to include")
    args = parser.parse_args()
    if args.size < 1:
        parser.error("--size must be positive")
    rows = stratified_sample(eligible_items(args.input, args.reference_year, args.relations), args.size, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} benchmark items to {args.output}")


if __name__ == "__main__":
    main()
