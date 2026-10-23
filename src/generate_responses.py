"""Collect short answers from an OpenAI-compatible chat API, including local Ollama."""

import argparse
import csv
from datetime import datetime, timezone
import importlib.util
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from date_compare import read_csv
from fact_audit import require_verified


ROOT = Path(__file__).resolve().parents[1]
PROMPT = "Answer the following question with a short factual answer only:\n{question}"


def load_env_file(path):
    """Read simple KEY=VALUE settings without executing shell syntax."""
    if not path.exists():
        return {}
    values = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if not separator or not key.isidentifier():
            raise ValueError(f"Invalid .env setting on line {line_number}")
        if value.startswith(("'", '"')):
            if len(value) < 2 or value[-1] != value[0]:
                raise ValueError(f"Unclosed quoted .env value on line {line_number}")
            value = value[1:-1]
        values[key] = value
    return values


def get_answer(base_url, model, api_key, question, timeout):
    if urllib.parse.urlparse(base_url).hostname == "api.groq.com":
        return get_groq_answer(base_url, model, api_key, question, timeout)

    endpoint = base_url.rstrip("/") + "/chat/completions"
    payload = json.dumps({
        "model": model,
        "temperature": 0,
        "messages": [{"role": "user", "content": PROMPT.format(question=question)}],
    }).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(endpoint, payload, headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read(500).decode("utf-8", errors="replace")
        raise RuntimeError(f"API returned HTTP {exc.code}: {detail}") from exc
    try:
        answer = data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError, AttributeError) as exc:
        raise ValueError("API response lacked a text answer") from exc
    if not answer:
        raise ValueError("API returned an empty answer")
    return answer


def get_groq_answer(base_url, model, api_key, question, timeout):
    try:
        from groq import APIStatusError, Groq
    except ImportError as exc:
        raise RuntimeError("Install the official Groq client first: python -m pip install -r requirements.txt") from exc

    # The Groq SDK appends /openai/v1 itself. Give it only the URL origin.
    parsed = urllib.parse.urlsplit(base_url)
    api_origin = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))
    try:
        with Groq(api_key=api_key, base_url=api_origin, timeout=timeout) as client:
            response = client.chat.completions.create(
                model=model,
                temperature=0,
                tool_choice="none",
                messages=[{"role": "user", "content": PROMPT.format(question=question)}],
            )
    except APIStatusError as exc:
        detail = exc.response.text[:500]
        raise RuntimeError(f"Groq returned HTTP {exc.status_code}: {detail}") from exc

    answer = response.choices[0].message.content
    if not answer or not answer.strip():
        raise ValueError("Groq returned an empty answer")
    return answer.strip()


def save_answers(path, answers, ordered_ids):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "model_answer"])
        writer.writeheader()
        writer.writerows({"id": item, "model_answer": answers[item]} for item in ordered_ids if item in answers)
    temporary.replace(path)


def main():
    file_settings = load_env_file(ROOT / ".env")

    def setting(name, fallback=None):
        return os.getenv(name) or file_settings.get(name) or fallback

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path, default=ROOT / "data/sample_questions.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "data/model_responses.csv")
    parser.add_argument("--base-url", default=setting("LLM_BASE_URL", "http://localhost:11434/v1"))
    parser.add_argument("--model", default=setting("LLM_MODEL"))
    parser.add_argument("--api-key-env", default="LLM_API_KEY")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--delay", type=float, default=0)
    parser.add_argument("--audit", type=Path, default=ROOT / "data/fact_audit.csv")
    args = parser.parse_args()
    if not args.model:
        parser.error("Set --model or LLM_MODEL")
    api_key = setting(args.api_key_env)
    if urllib.parse.urlparse(args.base_url).hostname == "api.groq.com" and not api_key:
        parser.error("Add LLM_API_KEY to the project .env file before calling Groq")
    if urllib.parse.urlparse(args.base_url).hostname == "api.groq.com" and importlib.util.find_spec("groq") is None:
        parser.error("Install the official Groq client: python -m pip install -r requirements.txt")
    questions = read_csv(args.questions, ("id", "question"))
    try:
        require_verified(questions, args.audit)
    except ValueError as exc:
        parser.error(str(exc))
    ordered_ids = [r["id"] for r in questions]
    answers = {}
    metadata_path = args.output.with_suffix(".metadata.json")
    metadata = {
        "model": args.model,
        "base_url": args.base_url,
        "temperature": 0,
        "prompt": PROMPT,
        "question_file": str(args.questions.resolve()),
    }
    if args.output.exists():
        if not metadata_path.exists():
            parser.error("Existing answers have no metadata; preserve or rename them before a new collection")
        previous = json.loads(metadata_path.read_text(encoding="utf-8"))
        if any(previous.get(key) != value for key, value in metadata.items()):
            parser.error("Existing answers used a different model, URL, prompt, or question file")
        answers = {r["id"]: r["model_answer"] for r in read_csv(args.output, ("id", "model_answer"))}
        if set(answers) - set(ordered_ids):
            parser.error("Existing output contains IDs outside the selected sample")
    else:
        metadata["started_at_utc"] = datetime.now(timezone.utc).isoformat()
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    for index, question in enumerate(questions, 1):
        if question["id"] in answers and answers[question["id"]].strip():
            continue
        answers[question["id"]] = get_answer(
            args.base_url, args.model, api_key, question["question"], args.timeout
        )
        save_answers(args.output, answers, ordered_ids)
        print(f"Saved {index}/{len(questions)}: {question['id']}")
        if args.delay:
            time.sleep(args.delay)
    print(f"Completed {len(questions)} responses")


if __name__ == "__main__":
    main()
