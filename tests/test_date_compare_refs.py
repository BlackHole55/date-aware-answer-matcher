import csv
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from date_compare_refs import classify_with_references, load_references  # noqa: E402


class SourcedReferenceTests(unittest.TestCase):
    def test_added_years_match_but_conflicting_years_do_not(self):
        self.assertEqual(classify_with_references(
            "December 2018 (the Armed Forces Bowl)", ["Liberty Bowl"], ["Armed Forces Bowl", "2018"]
        ), "Outdated")
        self.assertEqual(classify_with_references(
            "2019 or 2017", ["2019"], ["2017"]
        ), "Irrelevant")

    def test_exact_added_alias_matches(self):
        self.assertEqual(classify_with_references(
            "Pinstripe Bowl", ["Independence"], ["Quick Lane", "Pinstripe Bowl"]
        ), "Outdated")

    def test_rejects_conflicting_reference_labels(self):
        question = [{"id": "a", "current_answer": "2019", "historical_answers": "2017"}]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "references.csv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["id", "label", "answer", "evidence_url", "reason"])
                writer.writeheader()
                writer.writerow({"id": "a", "label": "Outdated", "answer": "2019", "evidence_url": "https://example.com", "reason": "test"})
            with self.assertRaisesRegex(ValueError, "overlap"):
                load_references(path, question)


if __name__ == "__main__":
    unittest.main()
