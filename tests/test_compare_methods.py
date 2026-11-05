import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from compare_methods import classify_token_overlap, exact_mcnemar, holm_adjust, token_f1  # noqa: E402


class FrozenComparisonTests(unittest.TestCase):
    def test_token_normalization_and_threshold(self):
        self.assertEqual(token_f1("The Mercedes Benz Stadium!", "mercedes benz stadium"), 1)
        self.assertEqual(classify_token_overlap("August 11, 2018", "August 11 2018", ["2013"]), "Correct")
        self.assertEqual(classify_token_overlap("unrelated", "current", ["historical"]), "Irrelevant")

    def test_reference_tie_is_irrelevant(self):
        self.assertEqual(classify_token_overlap("2018", "2018 season", ["2018 cup"]), "Irrelevant")

    def test_exact_mcnemar_uses_paired_correctness(self):
        result = exact_mcnemar(
            ["Correct", "Outdated", "Irrelevant", "Correct"],
            ["Correct", "Outdated", "Irrelevant", "Irrelevant"],
            ["Irrelevant", "Irrelevant", "Irrelevant", "Correct"],
        )
        self.assertEqual(result["proposed_correct_baseline_wrong"], 2)
        self.assertEqual(result["proposed_wrong_baseline_correct"], 1)
        self.assertEqual(result["exact_p_value"], 1.0)

    def test_holm_adjustment_is_monotone_in_p_order(self):
        self.assertEqual(holm_adjust({"a": 0.01, "b": 0.04, "c": 0.9}),
                         {"a": 0.03, "b": 0.08, "c": 0.9})


if __name__ == "__main__":
    unittest.main()
