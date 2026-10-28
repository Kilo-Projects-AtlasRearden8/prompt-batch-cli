"""Batch orchestration: run one template over many inputs, with retries and optional concurrency."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from .template import render_template


@dataclass
class Result:
    """Outcome for a single batch item."""

    index: int
    input: str
    output: str = ""
    model: str = ""
    endpoint: str = ""
    duration_ms: float = 0.0
    status: str = "pending"  # pending | ok | failed
    error: str = ""

    def to_row(self) -> dict[str, str]:
        return {
            "index": str(self.index),
            "input": self.input,
            "output": self.output,
            "model": self.model,
            "endpoint": self.endpoint,
            "duration_ms": f"{self.duration_ms:.0f}",
            "status": self.status,
            "error": self.error,
        }


def run_one(client, template: str, input_text: str, retries: int = 0):
    """Run one input through the template and client, retrying on failure.

    Returns ``(output, model, endpoint, duration_ms, error)``.
    """
    prompt = render_template(template, input_text)
    last_error = ""
    for _attempt in range(retries + 1):
        start = time.perf_counter()
        try:
            completion = client.chat([{"role": "user", "content": prompt}])
            duration_ms = (time.perf_counter() - start) * 1000
            return completion.text, completion.model, completion.endpoint, duration_ms, ""
        except Exception as exc:  # noqa: BLE001 - any endpoint failure is a retryable batch error
            last_error = str(exc)
    return "", "", "", 0.0, last_error


def run_batch(client, template: str, inputs: list[str], retries: int = 0, concurrency: int = 1) -> list[Result]:
    """Run *inputs* through *template* and return a :class:`Result` per input.

    Results preserve input order. ``concurrency > 1`` runs items in parallel
    using a thread pool; the default is sequential so local endpoints stay
    responsive.
    """
    results: list[Result] = [Result(index=i, input=text) for i, text in enumerate(inputs)]

    def process(result: Result) -> Result:
        output, model, endpoint, duration_ms, error = run_one(client, template, result.input, retries=retries)
        result.output = output
        result.model = model
        result.endpoint = endpoint
        result.duration_ms = duration_ms
        result.status = "failed" if error else "ok"
        result.error = error
        return result

    if concurrency and concurrency > 1:
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = {pool.submit(process, result): result.index for result in results}
            for future in as_completed(futures):
                results[futures[future]] = future.result()
    else:
        for result in results:
            process(result)

    results.sort(key=lambda result: result.index)
    return results
