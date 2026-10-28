import unittest

from prompt_batch.batch import Result, run_batch
from prompt_batch.client import LLMError


class StubClient:
    """Client that returns canned completions or raises, as configured."""

    def __init__(self, outputs=None, fail_on=None, model="stub-model", endpoint="http://stub"):
        self.outputs = outputs or {}
        self.fail_on = set(fail_on or [])
        self.model = model
        self.endpoint = endpoint
        self.calls = 0

    def chat(self, messages, model=None):  # noqa: ARG002
        self.calls += 1
        prompt = messages[-1]["content"] if messages else ""
        if prompt in self.fail_on:
            raise LLMError("stub failure")
        return type("C", (), {"text": self.outputs.get(prompt, f"echo {prompt}"), "model": self.model, "endpoint": self.endpoint})()


class RunBatchTest(unittest.TestCase):
    def test_runs_all_inputs_in_order(self):
        client = StubClient()
        results = run_batch(client, "Reverse: $input", ["a", "b", "c"])
        self.assertEqual(len(results), 3)
        self.assertEqual([r.input for r in results], ["a", "b", "c"])
        self.assertTrue(all(r.status == "ok" for r in results))
        self.assertEqual([r.output for r in results], ["echo Reverse: a", "echo Reverse: b", "echo Reverse: c"])

    def test_failed_items_record_error_and_status(self):
        client = StubClient(fail_on=["b"])
        results = run_batch(client, "$input", ["a", "b", "c"])
        self.assertEqual([r.status for r in results], ["ok", "failed", "ok"])
        self.assertEqual(results[1].output, "")
        self.assertIn("stub failure", results[1].error)

    def test_retries_attempted_on_failure(self):
        client = StubClient(fail_on={"a"})
        results = run_batch(client, "$input", ["a"], retries=2)
        self.assertEqual(results[0].status, "failed")
        # initial attempt + 2 retries = 3 calls
        self.assertEqual(client.calls, 3)

    def test_concurrency_returns_all_results(self):
        client = StubClient()
        results = run_batch(client, "$input", list(range(10)), concurrency=4)
        self.assertEqual(len(results), 10)
        self.assertTrue(all(r.status == "ok" for r in results))
        self.assertEqual([r.index for r in results], list(range(10)))


if __name__ == "__main__":
    unittest.main()
