"""Combine existing labels with AI suggestions in a separate, attributed draft."""

import csv
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HUMAN_SHEET = ROOT / "data/verification_amended_human_labels.csv"
AI_REVIEW = ROOT / "docs/ai_provisional_annotation_review.md"
OUTPUT = ROOT / "data/verification_ai_assisted_draft.json"
LABELS = {"Correct", "Outdated", "Irrelevant"}
ALLOWED_N = frozenset({50, 200})
AI_LINE = re.compile(r"^(\d+)\. `([^`]+)` — \*\*(Correct|Outdated|Irrelevant)", re.M)


def main():
    if OUTPUT.exists():
        raise FileExistsError(f"Refusing to overwrite {OUTPUT}")
    with HUMAN_SHEET.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    matches = AI_LINE.findall(AI_REVIEW.read_text(encoding="utf-8"))
    if len(rows) != len(matches) or len(rows) not in ALLOWED_N:
        raise ValueError(
            f"Expected matching human-sheet and AI-review lengths in "
            f"{sorted(ALLOWED_N)}; got {len(rows)} sheet rows and {len(matches)} AI entries"
        )

    draft = []
    for position, (row, (number, item_id, ai_label)) in enumerate(zip(rows, matches), 1):
        if int(number) != position or row["id"] != item_id:
            raise ValueError(f"AI review and human sheet differ at row {position}")
        existing_label = row["human_label"].strip()
        if existing_label and existing_label not in LABELS:
            raise ValueError(f"Invalid existing label at row {position}")
        draft.append({
            "row_number": position,
            "id": item_id,
            "question": row["question"],
            "model_answer": row["model_answer"],
            "current_answer": row["current_answer"],
            "historical_answers": row["historical_answers"],
            "proposed_label": existing_label or ai_label,
            "label_source": "existing_human_label_file" if existing_label else "AI_provisional_review",
            "requires_human_review": not bool(existing_label),
            "ai_suggestion": ai_label,
            "existing_notes": row["notes"],
            "existing_evidence_url": row["evidence_url"],
        })

    counts = Counter(item["label_source"] for item in draft)
    output = {
        "status": "AI-assisted draft; not an independent human-labeled set",
        "eligible_for_primary_human_evaluation": False,
        "source_human_sheet": str(HUMAN_SHEET.relative_to(ROOT)),
        "source_ai_review": str(AI_REVIEW.relative_to(ROOT)),
        "counts": dict(counts),
        "rows": draft,
    }
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}: {counts['existing_human_label_file']} existing, "
          f"{counts['AI_provisional_review']} AI-proposed; not valid for primary human evaluation")


if __name__ == "__main__":
    main()
