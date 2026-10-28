# Status: prompt-batch

## What was built

`prompt-batch` is a local-first Python CLI that runs one prompt template over
many inputs through a configurable OpenAI-compatible endpoint (Ollama by
default) and saves Markdown and/or CSV results. No API keys are required, and
no real credentials or personal data are used anywhere — tests run against a
mock endpoint.

Components:

* `src/prompt_batch/client.py` — stdlib-only HTTP client for
  `/v1/chat/completions` (default `http://localhost:11434`), with clear error
  reporting (`LLMError`).
* `src/prompt_batch/template.py` — `string.Template` rendering with `$input`
  placeholder.
* `src/prompt_batch/batch.py` — batch orchestration with retries, optional
  concurrency, ordered results, per-item status/error tracking.
* `src/prompt_batch/output.py` — `results.md` and `results.csv` writers.
* `src/prompt_batch/cli.py` — argparse CLI, `prompt-batch` entry point.
* `tests/` — 17 stdlib `unittest` tests with a mock OpenAI-compatible endpoint
  (no network, no keys).
* `examples/` — sample `inputs.txt` and `template.txt`.
* `LICENSE` — MIT, Copyright (c) 2026 Asdale Dynamics, LLC.
* `README.md` — install, usage, template syntax, credits Asdale Dynamics, LLC.

## How to run

```bash
pip install .                       # or pip install -e . for editable
prompt-batch --inputs examples/inputs.txt --template examples/template.txt \
  --output batch_out --format both
```

Options: `--model`, `--base-url` (default Ollama at
`http://localhost:11434`), `--api-key` (optional), `--concurrency`,
`--retries`, `--input-column` (CSV inputs), `--format md|csv|both`.

Direct run without install: `PYTHONPATH=src python3 -m prompt_batch.cli --help`.

Template syntax: write `$input` where each batch item goes; `$$` for a literal
dollar sign.

## Verification results

* `python3 -m unittest discover -s tests` → **17 tests, OK** (client,
  template, batch, output, CLI end-to-end against mock endpoint)
* `pip install .` → builds and installs successfully; `prompt-batch --help`
  works
* CLI smoke test against mock endpoint with 4 inputs, concurrency 3 → RC 0,
  `results.md` and `results.csv` written with all inputs and mock outputs

No `.github/workflows` files were added. Nothing was pushed or published.

## Known gaps

* Streaming responses are not supported (non-streaming chat completions only).
* No system-message option; template is the full user message content.
* Retries happen immediately with no backoff.
* Default endpoint must be running Ollama (or another compatible endpoint);
  connection failures are reported per-item rather than aborting the batch.
* Template syntax is Python `string.Template` (`$input`), not Jinja2.

## Credits

Built by Asdale Dynamics, LLC (Indiana, formed October 2026). MIT License,
Copyright (c) 2026 Asdale Dynamics, LLC.
