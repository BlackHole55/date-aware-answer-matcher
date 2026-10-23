import csv
import contextlib
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from date_compare import classify, join_and_classify  # noqa: E402
from evaluate import compute_metrics  # noqa: E402
from fact_audit import require_verified  # noqa: E402
from generate_responses import get_answer, load_env_file  # noqa: E402
from select_sample import eligible_items, select_items  # noqa: E402


class PipelineTests(unittest.TestCase):
    def test_env_file_reads_values_without_executing_them(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / ".env"
            path.write_text("# settings\nLLM_MODEL='openai/gpt-oss-120b'\nLLM_API_KEY=test=key\n", encoding="utf-8")
            self.assertEqual(load_env_file(path), {
                "LLM_MODEL": "openai/gpt-oss-120b", "LLM_API_KEY": "test=key"
            })

    def test_groq_uses_official_client_without_tools(self):
        calls = []

        class FakeGroq:
            def __init__(self, **kwargs):
                calls.append(kwargs)
                self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=self.create))

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def create(self, **kwargs):
                calls.append(kwargs)
                message = types.SimpleNamespace(content="  Answer  ")
                return types.SimpleNamespace(choices=[types.SimpleNamespace(message=message)])

        fake_module = types.SimpleNamespace(Groq=FakeGroq, APIStatusError=Exception)
        with patch.dict(sys.modules, {"groq": fake_module}):
            answer = get_answer("https://api.groq.com/openai/v1", "test-model", "test-key", "A?", 15)
        self.assertEqual(answer, "Answer")
        self.assertEqual(calls[0]["base_url"], "https://api.groq.com")
        self.assertEqual(calls[1]["tool_choice"], "none")
        self.assertEqual(calls[1]["temperature"], 0)

    def test_groq_sdk_builds_chat_url_once(self):
        try:
            import groq
            import httpx
        except ImportError:
            self.skipTest("Groq SDK is not installed in this Python environment")

        urls = []

        def respond(request):
            urls.append(str(request.url))
            return httpx.Response(200, json={
                "id": "test", "object": "chat.completion", "created": 0, "model": "test-model",
                "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": "Answer"}}],
            })

        with groq.Groq(
            api_key="test-key", base_url="https://api.groq.com",
            http_client=httpx.Client(transport=httpx.MockTransport(respond)),
        ) as client:
            client.chat.completions.create(model="test-model", messages=[{"role": "user", "content": "A?"}])
        self.assertEqual(urls, ["https://api.groq.com/openai/v1/chat/completions"])

    def test_current_answer_has_priority_and_substrings_do_not_match(self):
        self.assertEqual(classify("  NEW YORK. ", "New York", ["York"]), "Correct")
        self.assertEqual(classify("York", "New York", ["York"]), "Outdated")
        self.assertEqual(classify("New", "New York", ["York"]), "Irrelevant")

    def test_missing_response_is_not_scored(self):
        questions = [{"id": "a", "current_answer": "New", "historical_answers": "Old"}]
        with self.assertRaisesRegex(ValueError, "Missing model answer"):
            join_and_classify(questions, [{"id": "a", "model_answer": ""}])

    def test_agreement_and_kappa(self):
        rows = [
            {"human_label": "Correct", "auto_label": "Correct"},
            {"human_label": "Outdated", "auto_label": "Outdated"},
            {"human_label": "Irrelevant", "auto_label": "Irrelevant"},
        ]
        metrics, matrix = compute_metrics(rows)
        self.assertEqual(metrics["agreement"], 1)
        self.assertEqual(metrics["cohens_kappa"], 1)
        self.assertEqual(matrix["Outdated"]["Outdated"], 1)
        self.assertEqual(metrics["per_class"]["Irrelevant"]["f1"], 1)

    def test_situatedqa_selection_requires_a_distinct_earlier_answer(self):
        records = [
            {"id": 1, "date": "2010", "question": "who leads A", "answer": ["Old"]},
            {"id": 1, "date": "2020", "question": "who leads A", "edited_question": "who leads A as of 2020", "answer": ["New"]},
            {"id": 2, "date": "2010", "question": "who leads B", "answer": ["Same"]},
            {"id": 2, "date": "2020", "question": "who leads B", "edited_question": "who leads B as of 2020", "answer": ["Same"]},
            {"id": 3, "date": "2010", "question": "who leads C today", "answer": ["Old"]},
            {"id": 3, "date": "2020", "question": "who leads C today", "edited_question": "who leads C today as of 2020", "answer": ["New"]},
            {"id": 4, "date": "2010", "question": "who leads D", "answer": ["Old"]},
            {"id": 4, "date": "2020", "question": "who leads D", "edited_question": "who leads D as of 2020", "answer": ["New"]},
            {"id": 4, "date": "April 17, 2020", "question": "who leads D", "answer": ["Other"]},
        ]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "source.jsonl"
            path.write_text("\n".join(json.dumps(row) for row in records), encoding="utf-8")
            items = eligible_items((("train", path),), 2020)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], "sq-train-1")
        self.assertEqual(items[0]["historical_answers"], "Old")

    def test_excluding_a_candidate_preserves_other_sample_order(self):
        items = [{"id": str(i)} for i in range(8)]
        original = select_items(items, 4, 7)
        revised = select_items(items, 4, 7, {original[1]["id"]})
        self.assertEqual(revised[:3], [original[0], original[2], original[3]])

    def test_situatedqa_requires_verified_audit(self):
        questions = [{"id": "sq-train-1", "source_dataset": "SituatedQA temporal QA"}]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "audit.csv"
            path.write_text("id,status\nsq-train-1,pending\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must be verified"):
                require_verified(questions, path)
            path.write_text("id,status\nsq-train-1,verified\n", encoding="utf-8")
            require_verified(questions, path)

    def test_notebook_evaluates_complete_synthetic_inputs(self):
        if importlib.util.find_spec("IPython") is None:
            self.skipTest("Jupyter dependencies are not installed in this Python environment")
        project = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "src").mkdir()
            (root / "data").mkdir()
            for name in ("date_compare.py", "evaluate.py"):
                shutil.copy2(project / "src" / name, root / "src" / name)

            def write_rows(name, fieldnames, rows):
                with (root / "data" / name).open("w", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)

            questions = [
                {"id": "a", "question": "A", "current_answer": "new a", "historical_answers": "old a"},
                {"id": "b", "question": "B", "current_answer": "new b", "historical_answers": "old b"},
                {"id": "c", "question": "C", "current_answer": "new c", "historical_answers": "old c"},
            ]
            write_rows("sample_questions.csv", list(questions[0]), questions)
            write_rows("model_responses.csv", ["id", "model_answer"], [
                {"id": "a", "model_answer": "new a"},
                {"id": "b", "model_answer": "old b"},
                {"id": "c", "model_answer": "other"},
            ])
            write_rows("human_labels.csv", ["id", "human_label"], [
                {"id": "a", "human_label": "Correct"},
                {"id": "b", "human_label": "Outdated"},
                {"id": "c", "human_label": "Irrelevant"},
            ])
            notebook = json.loads((project / "notebooks" / "pilot_run.ipynb").read_text(encoding="utf-8"))
            previous = Path.cwd()
            try:
                os.chdir(root)
                scope = {}
                with contextlib.redirect_stdout(io.StringIO()):
                    for cell in notebook["cells"]:
                        if cell["cell_type"] == "code":
                            exec(compile("".join(cell["source"]), "pilot_run.ipynb", "exec"), scope)
            finally:
                os.chdir(previous)
            metrics = json.loads((root / "results" / "metrics.json").read_text(encoding="utf-8"))
            self.assertEqual(metrics["n"], 3)
            self.assertEqual(metrics["agreement"], 1)


if __name__ == "__main__":
    unittest.main()
