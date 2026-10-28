"""Command-line interface for prompt-batch.

Usage:

    prompt-batch --inputs inputs.txt --template template.txt --output batch_out
    prompt-batch --inputs items.csv --input-column review --template "Summarize: $input" --model llama3 --format both

Reads inputs from a text file (one item per line) or a CSV file, renders one
prompt template per input through an OpenAI-compatible endpoint (Ollama by
default), and writes Markdown and/or CSV results. No API key is needed for
local endpoints.
"""

from __future__ import annotations

import argparse
import csv
import sys
from typing import Iterable, Sequence

from .batch import run_batch
from .client import LLMError, OpenAICompatibleClient
from .output import write_csv, write_markdown
from .template import TemplateError, render_template

DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3"
DEFAULT_OUTPUT_DIR = "batch_out"
DEFAULT_FORMAT = "both"
DEFAULT_CONCURRENCY = 1
DEFAULT_RETRIES = 0


def _read_inputs(path: str, input_column: str | None) -> list[str]:
    """Read batch inputs from a text file, CSV file, or stdin ("-")."""
    if path == "-":
        raw = sys.stdin.read()
        return [line.rstrip("\n") for line in raw.splitlines() if line.strip()]

    lower = path.lower()
    if lower.endswith(".csv"):
        column = input_column or "input"
        with open(path, "r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames and column not in reader.fieldnames:
                raise SystemExit(f"CSV column '{column}' not found in {path} (columns: {reader.fieldnames})")
            inputs = []
            for row in reader:
                value = (row.get(column) or "").strip()
                if value:
                    inputs.append(value)
        return inputs

    with open(path, "r", encoding="utf-8") as handle:
        return [line.rstrip("\n") for line in handle if line.strip()]


def _read_template(value: str) -> str:
    """Read a template from a file path if it exists, otherwise use it inline."""
    try:
        with open(value, "r", encoding="utf-8") as handle:
            return handle.read()
    except OSError:
        return value


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prompt-batch",
        description="Run one prompt template over many inputs through an OpenAI-compatible endpoint (default Ollama).",
    )
    parser.add_argument("--inputs", required=True, help="Input file: .txt (one item per line) or .csv, or '-' for stdin")
    parser.add_argument(
        "--input-column",
        default=None,
        help="Column name when --inputs is a CSV file (default: 'input')",
    )
    parser.add_argument("--template", required=True, help="Prompt template file path or inline text using $input")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_DIR, help="Output directory (default: batch_out)")
    parser.add_argument(
        "--format",
        choices=["md", "csv", "both"],
        default=DEFAULT_FORMAT,
        help="Result format(s) to write (default: both)",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model name (default: {DEFAULT_MODEL})")
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"Endpoint base URL (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument("--api-key", default=None, help="Bearer API key (optional; local endpoints usually do not need one)")
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY, help="Parallel workers (default: 1, sequential)")
    parser.add_argument("--retries", type=int, default=DEFAULT_RETRIES, help="Retries per failed item (default: 0)")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    template = _read_template(args.template)
    try:
        render_template(template, "probe")
    except TemplateError as exc:
        print(f"error: invalid template: {exc}", file=sys.stderr)
        return 2

    try:
        inputs = _read_inputs(args.inputs, args.input_column)
    except (OSError, csv.Error, SystemExit) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not inputs:
        print("error: no inputs found", file=sys.stderr)
        return 2

    client = OpenAICompatibleClient(
        base_url=args.base_url,
        model=args.model,
        api_key=args.api_key,
    )

    print(f"Running {len(inputs)} inputs through {client.endpoint} (model: {args.model}) ...")
    try:
        results = run_batch(client, template, inputs, retries=args.retries, concurrency=args.concurrency)
    except LLMError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    import os

    os.makedirs(args.output, exist_ok=True)
    wrote: list[str] = []
    if args.format in ("md", "both"):
        md_path = os.path.join(args.output, "results.md")
        write_markdown(results, md_path, template=template, endpoint=client.endpoint, model=args.model)
        wrote.append(md_path)
    if args.format in ("csv", "both"):
        csv_path = os.path.join(args.output, "results.csv")
        write_csv(results, csv_path)
        wrote.append(csv_path)

    succeeded = sum(1 for item in results if item.status == "ok")
    failed = len(results) - succeeded
    print(f"Done: {succeeded} succeeded, {failed} failed.")
    for path in wrote:
        print(f"Wrote {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
