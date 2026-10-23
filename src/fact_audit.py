"""Require human verification of SituatedQA facts before collection or scoring."""

from pathlib import Path

from date_compare import read_csv


def require_verified(questions, audit_path):
    if not any(row.get("source_dataset") == "SituatedQA temporal QA" for row in questions):
        return
    audit_path = Path(audit_path)
    if not audit_path.exists():
        raise ValueError(
            f"Fact audit is missing: {audit_path}. Fill the audit sheet before using SituatedQA questions."
        )
    audit_rows = read_csv(audit_path, ("id", "status"))
    by_id = {row["id"]: row["status"].strip().lower() for row in audit_rows}
    pending = [row["id"] for row in questions if by_id.get(row["id"]) != "verified"]
    if pending:
        raise ValueError(
            f"All selected SituatedQA facts must be verified before use; "
            f"{len(pending)} pending/excluded/missing IDs, including {pending[:5]}"
        )
