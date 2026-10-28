"""Shared fixtures for prompt-batch tests: a mock OpenAI-compatible endpoint.

The mock endpoint runs on a local port and answers POST /v1/chat/completions
with an echo-style completion, so tests never call a real LLM or use keys.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class _MockHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_POST(self):  # noqa: N802 - http.server override
        if self.path != "/v1/chat/completions":
            self._respond(404, {"error": {"message": "not found", "type": "not_found"}})
            return
        length = int(self.headers.get("Content-Length", 0) or 0)
        body = self.rfile.read(length)
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self._respond(400, {"error": {"message": "invalid JSON", "type": "bad_request"}})
            return
        messages = payload.get("messages", []) if isinstance(payload, dict) else []
        last_content = ""
        if messages:
            last_content = str(messages[-1].get("content", ""))
        reply = f"Mock completion for: {last_content}"
        self._respond(
            200,
            {
                "id": "chatcmpl-mock",
                "object": "chat.completion",
                "model": payload.get("model", "mock-model") if isinstance(payload, dict) else "mock-model",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": reply},
                        "finish_reason": "stop",
                    }
                ],
            },
        )

    def _respond(self, code: int, obj: dict) -> None:
        data = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):  # silence test-server noise
        return None


def start_mock_endpoint():
    """Start the mock endpoint and return (server, base_url). Call server.shutdown() when done."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), _MockHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    return server, f"http://127.0.0.1:{port}"
