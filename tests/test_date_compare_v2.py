import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from date_compare_v2 import classify_v2, join_and_classify_v2  # noqa: E402


class YearTokenTests(unittest.TestCase):
    def test_exact_match_still_has_priority(self):
        self.assertEqual(classify_v2("2019", "2019", ["2017"]), "Correct")
        self.assertEqual(classify_v2("2017", "2019", ["2017"]), "Outdated")

    def test_year_in_longer_response(self):
        self.assertEqual(classify_v2("April 2019 (Masters)", "2019", ["2008"]), "Correct")
        self.assertEqual(classify_v2("In 2017 it happened", "2019", ["2017"]), "Outdated")

    def test_year_must_be_standalone_and_reference_must_be_year_only(self):
        self.assertEqual(classify_v2("20190", "2019", ["2017"]), "Irrelevant")
        self.assertEqual(classify_v2("the 2019 season", "2019-20", ["2016-17"]), "Irrelevant")

    def test_conflicting_reference_years_are_irrelevant(self):
        self.assertEqual(classify_v2("2019 or 2017", "2019", ["2017"]), "Irrelevant")

    def test_join_keeps_original_columns_and_order(self):
        questions = [{"id": "a", "current_answer": "2019", "historical_answers": "2008", "question": "When?"}]
        responses = [{"id": "a", "model_answer": "April 2019"}]
        self.assertEqual(join_and_classify_v2(questions, responses), [{
            **questions[0], "model_answer": "April 2019", "auto_label": "Correct"
        }])


if __name__ == "__main__":
    unittest.main()
