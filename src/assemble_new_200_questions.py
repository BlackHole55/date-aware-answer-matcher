"""Assemble a new 200-question study from audited SituatedQA and House facts."""

import csv
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITUATED_QUESTIONS = ROOT / "data/full_questions_amended.csv"
SITUATED_AUDIT = ROOT / "data/full_fact_audit.csv"
HOUSE_QUESTIONS = ROOT / "data/house_roster_78_verified.csv"
OUTPUT_QUESTIONS = ROOT / "data/full_questions_200_new.csv"
OUTPUT_AUDIT = ROOT / "data/full_fact_audit_200_new.csv"

QUESTION_FIELDS = (
    "id", "question", "current_answer", "historical_answers",
    "reference_year", "source_dataset", "source_split", "source_id",
    "source_date", "historical_dates",
)
AUDIT_FIELDS = (
    "id", "question", "current_answer", "historical_answers", "status",
    "evidence_url", "historical_evidence_url", "notes",
    "source_2020_page", "source_2011_page",
    "source_2020_line", "source_2011_line",
)
CURRENT_ROSTER = "https://historycms.house.gov/WorkArea/DownloadAsset.aspx?id=25769816718"
HISTORICAL_ROSTER = "https://historycms.house.gov/WorkArea/DownloadAsset.aspx?id=41208"


def read_rows(path, required):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not set(required) <= set(reader.fieldnames):
            raise ValueError(f"{path} is missing required columns")
        rows = list(reader)
    ids = [row["id"] for row in rows]
    if any(not item for item in ids) or len(ids) != len(set(ids)):
        raise ValueError(f"{path} contains blank or duplicate IDs")
    return rows


def write_rows(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def normalized(value):
    return unicodedata.normalize("NFKC", value).casefold().strip()


def main():
    situated = read_rows(SITUATED_QUESTIONS, QUESTION_FIELDS)
    source_audit = read_rows(SITUATED_AUDIT, AUDIT_FIELDS[:6])
    house = read_rows(HOUSE_QUESTIONS, QUESTION_FIELDS + (
        "evidence_2020_url", "evidence_2011_url",
        "source_2020_page", "source_2011_page",
        "source_2020_line", "source_2011_line",
    ))
    if len(situated) != 122 or len(house) != 78:
        raise ValueError("Expected exactly 122 audited SituatedQA and 78 House questions")

    by_id = {row["id"]: row for row in source_audit}
    for question in situated:
        audit = by_id.get(question["id"])
        if audit is None or audit["status"].strip().lower() != "verified":
            raise ValueError(f"Unverified SituatedQA question: {question['id']}")
        for field in ("question", "current_answer", "historical_answers"):
            if audit[field] != question[field]:
                raise ValueError(f"Audit mismatch for {question['id']}: {field}")
        if not audit["evidence_url"].strip():
            raise ValueError(f"Missing evidence for {question['id']}")

    for question in house:
        if (question["reference_year"] != "2020"
                or question["source_date"] != "2020-12-15"
                or question["historical_dates"] != "2011-01-04"
                or question["source_dataset"] != "US House official member lists"
                or question["evidence_2020_url"] != CURRENT_ROSTER
                or question["evidence_2011_url"] != HISTORICAL_ROSTER):
            raise ValueError(f"Incorrect roster provenance for {question['id']}")
        if not all(question[field].strip() for field in QUESTION_FIELDS):
            raise ValueError(f"Incomplete House question: {question['id']}")
        if normalized(question["current_answer"]) == normalized(question["historical_answers"]):
            raise ValueError(f"No dated answer change for {question['id']}")
        for field in ("source_2020_page", "source_2011_page",
                      "source_2020_line", "source_2011_line"):
            if int(question[field]) <= 0:
                raise ValueError(f"Invalid evidence locator for {question['id']}")

    all_questions = situated + house
    ids = [row["id"] for row in all_questions]
    if len(ids) != len(set(ids)):
        raise ValueError("The combined question set contains duplicate IDs")
    prompts = [normalized(row["question"]) for row in all_questions]
    if len(prompts) != len(set(prompts)):
        raise ValueError("The combined question set contains duplicate questions")

    audit_rows = [
        {field: by_id[row["id"]].get(field, "") for field in AUDIT_FIELDS}
        for row in situated
    ]
    for row in house:
        audit_rows.append({
            "id": row["id"],
            "question": row["question"],
            "current_answer": row["current_answer"],
            "historical_answers": row["historical_answers"],
            "status": "verified",
            "evidence_url": row["evidence_2020_url"],
            "historical_evidence_url": row["evidence_2011_url"],
            "notes": (
                "Official House rosters identify the representative for this "
                "numbered district on 2020-12-15 and 2011-01-04. "
                "The two names differ. District boundaries may have changed."
            ),
            "source_2020_page": row["source_2020_page"],
            "source_2011_page": row["source_2011_page"],
            "source_2020_line": row["source_2020_line"],
            "source_2011_line": row["source_2011_line"],
        })

    write_rows(OUTPUT_QUESTIONS, QUESTION_FIELDS, all_questions)
    write_rows(OUTPUT_AUDIT, AUDIT_FIELDS, audit_rows)
    print(f"Wrote {len(all_questions)} verified questions to {OUTPUT_QUESTIONS}")
    print(f"Wrote {len(audit_rows)} audit records to {OUTPUT_AUDIT}")


if __name__ == "__main__":
    main()
