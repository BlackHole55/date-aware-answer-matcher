"""Join model and human labels, then compute agreement statistics."""

import argparse
import csv
import json
from pathlib import Path

from date_compare import LABELS, join_and_classify, read_csv
from fact_audit import require_verified


ROOT = Path(__file__).resolve().parents[1]


def compute_metrics(rows):
    n = len(rows)
    if not n:
        raise ValueError("No annotated rows to evaluate")
    matrix = {human: {auto: 0 for auto in LABELS} for human in LABELS}
    for row in rows:
        matrix[row["human_label"]][row["auto_label"]] += 1
    agreement = sum(matrix[label][label] for label in LABELS) / n
    human_totals = {label: sum(matrix[label].values()) for label in LABELS}
    auto_totals = {label: sum(matrix[human][label] for human in LABELS) for label in LABELS}
    expected = sum(human_totals[label] * auto_totals[label] for label in LABELS) / (n * n)
    kappa = (agreement - expected) / (1 - expected) if expected < 1 else None
    per_class = {}
    for label in LABELS:
        tp = matrix[label][label]
        precision = tp / auto_totals[label] if auto_totals[label] else 0.0
        recall = tp / human_totals[label] if human_totals[label] else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[label] = {
            "support": human_totals[label], "precision": precision,
            "recall": recall, "f1": f1,
        }
    return {"n": n, "agreement": agreement, "cohens_kappa": kappa, "per_class": per_class}, matrix


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path, default=ROOT / "data/sample_questions.csv")
    parser.add_argument("--responses", type=Path, default=ROOT / "data/model_responses.csv")
    parser.add_argument("--human-labels", type=Path, default=ROOT / "data/human_labels.csv")
    parser.add_argument("--analysis", type=Path, default=ROOT / "data/analysis_table.csv")
    parser.add_argument("--results", type=Path, default=ROOT / "results")
    parser.add_argument("--audit", type=Path, default=ROOT / "data/fact_audit.csv")
    args = parser.parse_args()
    questions = read_csv(args.questions, ("id", "current_answer", "historical_answers"))
    try:
        require_verified(questions, args.audit)
    except ValueError as exc:
        parser.error(str(exc))
    responses = read_csv(args.responses, ("id", "model_answer"))
    humans = read_csv(args.human_labels, ("id", "human_label"))
    rows = join_and_classify(questions, responses)
    by_id = {r["id"]: r for r in humans}
    if set(by_id) != {r["id"] for r in rows}:
        raise ValueError("Human label IDs must exactly match question IDs")
    for row in rows:
        label = by_id[row["id"]]["human_label"].strip()
        if label not in LABELS:
            raise ValueError(f"Invalid or missing human label for {row['id']}: {label!r}")
        row["human_label"] = label
    metrics, matrix = compute_metrics(rows)
    args.analysis.parent.mkdir(parents=True, exist_ok=True)
    args.results.mkdir(parents=True, exist_ok=True)
    with args.analysis.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (args.results / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    with (args.results / "confusion_matrix.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["human\\auto", *LABELS])
        for human in LABELS:
            writer.writerow([human, *(matrix[human][auto] for auto in LABELS)])
    print(json.dumps(metrics, indent=2))
    for label in LABELS:
        example = next((r for r in rows if r["auto_label"] == label), None)
        if example:
            print(f"{label} example: {example['id']} | {example['model_answer']}")


if __name__ == "__main__":
    main()
