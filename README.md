# prompt-batch

Run one prompt template over many inputs through any OpenAI-compatible
endpoint (Ollama by default), and save the results as Markdown and/or CSV.
Local-first, tested, and beginner-friendly. No API keys required for local
endpoints.

Built and maintained by **Asdale Dynamics, LLC** (Indiana, formed October
2026) — beginner-friendly AI education, books, and practical local-LLM tools.
Part of the same spirit as Dylan Asdale's *The Massive AI Manual* and
dylanasdale.github.io: AI explained plain English, step by step, never
condescending.

## What it does

`prompt-batch` reads a list of inputs (one per line in a text file, or a
column in a CSV), renders a single prompt template that uses `$input` for each
item, sends each rendered prompt to a chat-completions endpoint, and writes
the results:

* `results.md` — human-readable Markdown with every input, output, model, and duration
* `results.csv` — machine-readable rows with status and errors for failed items

Run items sequentially (default, friendly to local endpoints) or with
concurrency. Failed items are retried according to `--retries` and recorded
with their error instead of aborting the whole batch.

## Install

No external dependencies; installs offline with pip:

```bash
pip install .
# or, for editable development:
pip install -e .
```

This provides the `prompt-batch` command. You can also run it directly:

```bash
python -m prompt_batch.cli --help
```

## Quick start

1. Start a local endpoint (Ollama is the default):

   ```bash
   ollama serve
   ollama pull llama3.2
   ```

2. Create your inputs (`examples/inputs.txt`):

   ```
   Explain retrieval-augmented generation in two sentences.
   What is a local LLM, and why use one?
   Give three tips for writing better prompts.
   ```

3. Create your template (`examples/template.txt`):

   ```
   You are a helpful writing assistant. Answer plainly, like a friend would.

   Question: $input
   Answer:
   ```

4. Run the batch:

   ```bash
   prompt-batch --inputs examples/inputs.txt --template examples/template.txt --output batch_out
   ```

5. Open `batch_out/results.md` or `batch_out/results.csv`.

## Usage

```
prompt-batch --inputs INPUTS --template TEMPLATE [options]
```

| Option | Default | Meaning |
|--------|---------|---------|
| `--inputs` | (required) | `.txt` with one item per line, `.csv`, or `-` for stdin |
| `--input-column` | `input` | Column name when `--inputs` is a CSV |
| `--template` | (required) | Template file path or inline text; uses `$input` as the placeholder |
| `--output` | `batch_out` | Directory for `results.md` and/or `results.csv` |
| `--format` | `both` | `md`, `csv`, or `both` |
| `--model` | `llama3` | Model name passed to the endpoint |
| `--base-url` | `http://localhost:11434` | OpenAI-compatible endpoint base URL |
| `--api-key` | (none) | Bearer token, only needed for endpoints that require auth |
| `--concurrency` | `1` | Parallel workers (1 = sequential) |
| `--retries` | `0` | Retries per failed item |

Environment variables are not required; every option is set on the command
line, which keeps behavior explicit and easy to audit.

### Template syntax

Templates use Python `string.Template` style: write `$input` where each item
goes. A literal dollar sign is `$$`.

Example:

```
Summarize the following in one sentence, plain English:

$input
```

## Output

`results.md` contains one section per item with its input, output, duration,
and model, plus a summary line. `results.csv` has columns:

`index, input, output, model, endpoint, duration_ms, status, error`

Failed items keep `status: failed` and the error message so you can inspect
and retry them without losing successful results.

## Local-first by design

* Default endpoint is Ollama on `localhost:11434` — nothing leaves your machine.
* No API key is configured or required by default.
* No network calls are made except to the endpoint you configure.
* Tests run against a mock endpoint; no real credentials or keys are used anywhere.

## License

MIT License. Copyright (c) 2026 Asdale Dynamics, LLC. See `LICENSE`.
