"""Minimal HTTP client for OpenAI-compatible /v1/chat/completions endpoints.

No API key is required by default, which keeps local endpoints such as Ollama
working out of the box. Every network call goes through the standard library
only, so the package installs offline with zero dependencies.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Iterable


class LLMError(Exception):
    """Raised when the LLM endpoint is unreachable or returns an error."""


@dataclass(frozen=True)
class Completion:
    """A single chat completion returned by the endpoint."""

    text: str
    model: str
    endpoint: str


class OpenAICompatibleClient:
    """Client for any OpenAI-compatible chat completions endpoint (Ollama by default)."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3",
        api_key: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout
        self.endpoint = f"{self.base_url}/v1/chat/completions"

    def chat(self, messages: Iterable[dict[str, str]], model: str | None = None) -> Completion:
        """Send a chat completion request and return the assistant's text."""
        payload = {
            "model": model or self.model,
            "messages": [
                {"role": str(message.get("role", "user")), "content": str(message.get("content", ""))}
                for message in messages
            ],
            "stream": False,
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        if self.api_key:
            request.add_header("Authorization", f"Bearer {self.api_key}")

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            raise LLMError(f"endpoint {self.endpoint} returned HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise LLMError(f"could not reach endpoint {self.endpoint}: {exc}") from exc

        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as exc:
            raise LLMError(f"endpoint {self.endpoint} returned invalid JSON: {body!r}") from exc

        if isinstance(parsed, dict) and "error" in parsed:
            raise LLMError(f"endpoint {self.endpoint} returned error: {parsed['error']}")

        choices = parsed.get("choices") if isinstance(parsed, dict) else None
        if not choices:
            raise LLMError(f"endpoint {self.endpoint} returned no choices: {parsed!r}")

        message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
        text = message.get("content", "")
        if text is None:
            text = ""
        used_model = parsed.get("model", model or self.model) if isinstance(parsed, dict) else model or self.model

        return Completion(text=str(text), model=str(used_model), endpoint=self.endpoint)
