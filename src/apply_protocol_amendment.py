"""Build the instructor-approved 122/50 lists without altering the frozen CSVs."""

import csv
import hashlib
import random
from pathlib import Path

from date_compare import read_csv


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FULL = DATA / "full_questions.csv"
VERIFICATION = DATA / "verification_questions.csv"
PILOT = DATA / "sample_questions.csv"
AUDIT = DATA / "full_fact_audit.csv"
AMENDED_FULL = DATA / "full_questions_amended.csv"
AMENDED_VERIFICATION = DATA / "verification_questions_amended.csv"
FROZEN_HASHES = {
    FULL: "db1c148c02c80a95435a5d230f020de2fcb3077786231b5863916ae9f9b45f2b",
    VERIFICATION: "abe91b5efc54ea95a5f12071567d1eaa7e4c5e51171f3c3ee0c5f71871dba13f",
    AUDIT: "2c0f5e31c05a036d866db6bb36359bab5006c825b03fe9567fb65c3e7ecd7330",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path, rows, fieldnames):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    for path, expected in FROZEN_HASHES.items():
        if sha256(path) != expected:
            raise ValueError(f"Frozen input hash changed: {path}")

    full = read_csv(FULL, ("id",))
    verification = read_csv(VERIFICATION, ("id",))
    pilot = read_csv(PILOT, ("id",))
    audit = read_csv(AUDIT, ("id", "status"))
    full_ids = {row["id"] for row in full}
    pilot_ids = {row["id"] for row in pilot}
    verification_ids = {row["id"] for row in verification}
    audit_by_id = {row["id"]: row["status"].strip().lower() for row in audit}

    if len(full) != 200 or len(pilot) != 20 or len(verification) != 50:
        raise ValueError("Frozen list sizes do not match the approved amendment")
    if set(audit_by_id) != full_ids or set(audit_by_id.values()) != {"verified", "excluded"}:
        raise ValueError("Every frozen full-study ID needs one final audit decision")
    if not pilot_ids <= full_ids or not verification_ids <= full_ids - pilot_ids:
        raise ValueError("Pilot or verification IDs do not match the frozen full list")

    amended_full = [row for row in full if audit_by_id[row["id"]] == "verified"]
    amended_ids = {row["id"] for row in amended_full}
    if len(amended_full) != 122 or not pilot_ids <= amended_ids:
        raise ValueError("Expected 122 verified full-study rows including all 20 pilot rows")

    kept_verification = [row for row in verification if row["id"] in amended_ids]
    if len(kept_verification) != 33:
        raise ValueError("Expected 33 verified IDs in the frozen verification list")
    remaining_pool = [
        row for row in amended_full
        if row["id"] not in pilot_ids and row["id"] not in verification_ids
    ]
    if len(remaining_pool) != 69:
        raise ValueError("Expected 69 verified non-pilot replacement candidates")
    random.Random(19).shuffle(remaining_pool)
    amended_verification = kept_verification + remaining_pool[:17]
    if len({row["id"] for row in amended_verification}) != 50:
        raise ValueError("Amended verification IDs are not unique")

    fieldnames = list(full[0])
    write_csv(AMENDED_FULL, amended_full, fieldnames)
    write_csv(AMENDED_VERIFICATION, amended_verification, fieldnames)
    for path, rows in ((AMENDED_FULL, amended_full), (AMENDED_VERIFICATION, amended_verification)):
        print(f"{path.relative_to(ROOT)}: {len(rows)} rows, SHA-256 {sha256(path)}")


if __name__ == "__main__":
    main()
