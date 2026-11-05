"""Run the four frozen held-out conditions and prespecified paired analysis."""

import argparse
import csv
import hashlib
import json
import math
import random
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from date_compare import LABELS, join_and_classify, read_csv
from date_compare_v2 import join_and_classify_v2
from evaluate import compute_metrics
from fact_audit import require_verified


ROOT = Path(__file__).resolve().parents[1]
METHODS = ("always_correct", "exact", "token_overlap", "proposed_year_token")
BASELINES = METHODS[:-1]
BOOTSTRAP_SEED = 20261028
BOOTSTRAP_REPLICATES = 10000
TOKEN_THRESHOLD = 1 / 4
ARTICLES = {"a", "an", "the"}
ALLOWED_N = frozenset({50, 200})


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def squad_tokens(value):
    value = unicodedata.normalize("NFKC", value or "").casefold()
    value = "".join(char for char in value if not unicodedata.category(char).startswith("P"))
    return [word for word in value.split() if word not in ARTICLES]


def token_f1(response, reference):
    response_tokens = squad_tokens(response)
    reference_tokens = squad_tokens(reference)
    if not response_tokens or not reference_tokens:
        return 0.0
    common = sum((Counter(response_tokens) & Counter(reference_tokens)).values())
    return 2 * common / (len(response_tokens) + len(reference_tokens))


def classify_token_overlap(response, current, historical):
    scores = [(token_f1(response, current), "Correct")]
    scores.extend((token_f1(response, answer), "Outdated") for answer in historical)
    highest = max(score for score, _ in scores)
    winners = [label for score, label in scores if abs(score - highest) < 1e-12]
    return winners[0] if highest >= TOKEN_THRESHOLD and len(winners) == 1 else "Irrelevant"


def score_rows(human_labels, predictions, indices):
    rows = [{"human_label": human_labels[i], "auto_label": predictions[i]} for i in indices]
    metrics, matrix = compute_metrics(rows)
    metrics["macro_f1"] = sum(metrics["per_class"][label]["f1"] for label in LABELS) / len(LABELS)
    metrics["confusion_matrix"] = matrix
    metrics["prediction_counts"] = dict(Counter(predictions[i] for i in indices))
    return metrics


def percentile(values, fraction):
    values = sorted(values)
    position = (len(values) - 1) * fraction
    low = int(math.floor(position))
    high = int(math.ceil(position))
    return values[low] + (position - low) * (values[high] - values[low])


def interval(values):
    return [percentile(values, 0.025), percentile(values, 0.975)]


def exact_mcnemar(human_labels, proposed, baseline):
    better = sum(p == h and b != h for h, p, b in zip(human_labels, proposed, baseline))
    worse = sum(p != h and b == h for h, p, b in zip(human_labels, proposed, baseline))
    discordant = better + worse
    if not discordant:
        p_value = 1.0
    else:
        tail = sum(math.comb(discordant, k) for k in range(min(better, worse) + 1))
        p_value = min(1.0, 2 * tail / (2 ** discordant))
    return {"proposed_correct_baseline_wrong": better,
            "proposed_wrong_baseline_correct": worse,
            "discordant_total": discordant, "exact_p_value": p_value}


def holm_adjust(p_values):
    ordered = sorted(p_values, key=p_values.get)
    adjusted = {}
    previous = 0.0
    for rank, name in enumerate(ordered):
        previous = max(previous, min(1.0, (len(ordered) - rank) * p_values[name]))
        adjusted[name] = previous
    return adjusted


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path, default=ROOT / "data/verification_questions_amended.csv")
    parser.add_argument("--responses", type=Path, default=ROOT / "data/verification_model_responses.csv")
    parser.add_argument("--human-labels", type=Path, default=ROOT / "data/verification_amended_human_labels.csv")
    parser.add_argument("--audit", type=Path, default=ROOT / "data/full_fact_audit.csv")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    args.questions = args.questions.resolve()
    args.responses = args.responses.resolve()
    args.human_labels = args.human_labels.resolve()
    args.audit = args.audit.resolve()
    if args.output_dir is not None:
        args.output_dir = args.output_dir.resolve()

    questions = read_csv(args.questions, ("id", "current_answer", "historical_answers"))
    responses = read_csv(args.responses, ("id", "model_answer"))
    humans = read_csv(args.human_labels, ("id", "human_label"))
    require_verified(questions, args.audit)
    question_ids = [row["id"] for row in questions]
    response_by_id = {row["id"]: row for row in responses}
    human_by_id = {row["id"]: row for row in humans}
    if set(response_by_id) != set(question_ids) or set(human_by_id) != set(question_ids):
        raise ValueError("Question, response, and human-label ID sets must match exactly")
    if len(questions) not in ALLOWED_N:
        raise ValueError(
            f"The prespecified analysis requires {sorted(ALLOWED_N)} questions; "
            f"got {len(questions)}"
        )
    human_labels = [human_by_id[item]["human_label"].strip() for item in question_ids]
    if any(label not in LABELS for label in human_labels):
        raise ValueError("Every held-out item needs one valid human label")
    if set(human_labels) != set(LABELS):
        raise ValueError("Three-class macro-F1 is not estimable when a human class is absent")

    exact_rows = join_and_classify(questions, responses)
    proposed_rows = join_and_classify_v2(questions, responses)
    exact_by_id = {row["id"]: row["auto_label"] for row in exact_rows}
    proposed_by_id = {row["id"]: row["auto_label"] for row in proposed_rows}
    predictions = {
        "always_correct": ["Correct"] * len(questions),
        "exact": [exact_by_id[item] for item in question_ids],
        "token_overlap": [
            classify_token_overlap(
                response_by_id[row["id"]]["model_answer"], row["current_answer"],
                [answer.strip() for answer in row["historical_answers"].split("|") if answer.strip()]
            ) for row in questions
        ],
        "proposed_year_token": [proposed_by_id[item] for item in question_ids],
    }
    all_indices = list(range(len(questions)))
    results = {name: score_rows(human_labels, predictions[name], all_indices) for name in METHODS}

    strata = {label: [i for i, human in enumerate(human_labels) if human == label] for label in LABELS}
    rng = random.Random(BOOTSTRAP_SEED)
    boot_macro = {name: [] for name in METHODS}
    boot_differences = {name: [] for name in BASELINES}
    boot_recall_difference = []
    for _ in range(BOOTSTRAP_REPLICATES):
        indices = [rng.choice(strata[label]) for label in LABELS for _ in strata[label]]
        replicate = {name: score_rows(human_labels, predictions[name], indices) for name in METHODS}
        for name in METHODS:
            boot_macro[name].append(replicate[name]["macro_f1"])
        for name in BASELINES:
            boot_differences[name].append(replicate["proposed_year_token"]["macro_f1"] - replicate[name]["macro_f1"])
        proposed_classes = replicate["proposed_year_token"]["per_class"]
        boot_recall_difference.append(proposed_classes["Outdated"]["recall"] - proposed_classes["Irrelevant"]["recall"])

    for name in METHODS:
        results[name]["macro_f1_95pct_class_stratified_bootstrap_ci"] = interval(boot_macro[name])
    comparisons = {}
    for name in BASELINES:
        comparisons[name] = {
            "macro_f1_difference_proposed_minus_baseline": results["proposed_year_token"]["macro_f1"] - results[name]["macro_f1"],
            "macro_f1_difference_95pct_bootstrap_ci": interval(boot_differences[name]),
            "mcnemar": exact_mcnemar(human_labels, predictions["proposed_year_token"], predictions[name]),
        }
    adjusted = holm_adjust({name: value["mcnemar"]["exact_p_value"] for name, value in comparisons.items()})
    for name in BASELINES:
        comparisons[name]["mcnemar"]["holm_adjusted_p_value"] = adjusted[name]

    per_class = results["proposed_year_token"]["per_class"]
    recall_difference = per_class["Outdated"]["recall"] - per_class["Irrelevant"]["recall"]
    recall_ci = interval(boot_recall_difference)
    if recall_difference <= 0:
        decision = "not_supported"
    elif recall_ci[0] > 0:
        decision = "supported"
    else:
        decision = "inconclusive"

    label_hash = sha256(args.human_labels)
    output_dir = args.output_dir or ROOT / "results" / f"verification_primary_{label_hash[:8]}"
    if output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing analysis: {output_dir}")
    output_dir.mkdir(parents=True)
    summary = {
        "status": "Computed from provided human-label file; provenance is self-reported by the student",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_files": {str(path.relative_to(ROOT)): sha256(path) for path in
                        (args.questions, args.responses, args.human_labels, args.audit)},
        "analysis_script_sha256": sha256(Path(__file__)),
        "n": len(questions),
        "human_class_support": dict(Counter(human_labels)),
        "bootstrap": {"kind": "class-stratified percentile", "replicates": BOOTSTRAP_REPLICATES,
                      "seed": BOOTSTRAP_SEED, "percentile_interpolation": "linear at (n-1)*p"},
        "methods": results,
        "proposed_vs_baselines": comparisons,
        "hypothesis": {"outdated_minus_irrelevant_recall": recall_difference,
                       "95pct_bootstrap_ci": recall_ci, "decision": decision},
    }
    (output_dir / "comparison.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    with (output_dir / "paired_predictions.csv").open("w", encoding="utf-8", newline="") as handle:
        fieldnames = ["id", "question", "model_answer", "human_label", *METHODS]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for i, question in enumerate(questions):
            writer.writerow({
                "id": question["id"], "question": question["question"],
                "model_answer": response_by_id[question["id"]]["model_answer"],
                "human_label": human_labels[i],
                **{name: predictions[name][i] for name in METHODS},
            })
    print(f"Wrote {output_dir.relative_to(ROOT)}")
    print(f"Proposed macro-F1: {results['proposed_year_token']['macro_f1']:.4f}; "
          f"95% CI {results['proposed_year_token']['macro_f1_95pct_class_stratified_bootstrap_ci']}")
    print(f"Outdated minus Irrelevant recall: {recall_difference:.4f}; 95% CI {recall_ci}; {decision}")


if __name__ == "__main__":
    main()
