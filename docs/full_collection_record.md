# Full-study model collection record

On 1 November 2026, the amended 122-question list was sent to Groq using `src/generate_responses.py`. The command used `--questions data/full_questions_amended.csv --output data/full_model_responses.csv --audit data/full_fact_audit.csv --delay 2.1`. The run completed with 122 saved, nonblank answers. The output IDs match the amended list exactly, in order.

- Model: `openai/gpt-oss-120b`.
- Endpoint: `https://api.groq.com/openai/v1`.
- Temperature: `0`; tool choice: `none`.
- Prompt: `Answer the following question with a short factual answer only:` followed by a newline and the question.
- Started: `2026-11-01T05:16:02.715415+00:00`, from `data/full_model_responses.metadata.json`.
- `data/full_model_responses.csv` SHA-256: `5cda83c0de8910ef4d2ad988e5da4c8366e9437b84c630bbd5b5c8715c8e2dac`.
- `data/full_model_responses.metadata.json` SHA-256: `15d539988644192700eab2ac4190d09015d8ecbf2a9657153dae37bba28f76d9`.

The 50 amended verification IDs were filtered from the completed response file into `data/verification_model_responses.csv` (50 nonblank answers; SHA-256 `8f0fa0f3bba536335d8eca0799f679e5dc1ea0216a71106b825d8da7e3f5116c`). The blind annotation sheet is `data/verification_amended_human_labels.csv` (initial SHA-256 `54a3447a8baddee8fa88dff1d459f3db1ffc0b9f04b0865221a790b9b54a9a10`). It includes the question, model response, and audited reference answers, with empty `human_label` cells and no automatic labels. Record the annotator and labeling date when those cells are completed; its hash will then change.
