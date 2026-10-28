# Date Aware Answer Matcher on SituatedQA

This project evaluates a deterministic matcher for answers to questions anchored to 2020. It labels one LLM's responses as **Correct**, **Outdated**, or **Irrelevant**, then compares those labels with blind human judgments.

## Setup

From the project root in PowerShell:

```powershell
if (-not (Test-Path .venv\Scripts\python.exe)) { py -3.11 -m venv .venv }
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Saved pilot results can be reproduced without an API key:

```powershell
.\.venv\Scripts\python.exe src/evaluate.py --matcher exact
.\.venv\Scripts\python.exe src/evaluate.py --matcher year-token --analysis data/analysis_table_v2.csv --results results/v2
```

For new model calls, use `.env.example` to configure a private `.env` file. Never commit the API key.
