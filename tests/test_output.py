import csv
import io
import os
import tempfile
import unittest

from prompt_batch.batch import Result
from prompt_batch.output import write_csv, write_markdown


class OutputTest(unittest.TestCase):
    def test_markdown_contains_inputs_and_outputs(self):
        results = [
            Result(index=0, input="hello", output="hi there", model="m", endpoint="e", duration_ms=12.5, status="ok"),
            Result(index=1, input="bad", output="", model="m", endpoint="e", duration_ms=0.0, status="failed", error="boom"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "results.md")
            write_markdown(results, path, template="$input", endpoint="e", model="m")
            text = open(path, encoding="utf-8").read()
        self.assertIn("# Batch Results", text)
        self.assertIn("hello", text)
        self.assertIn("hi there", text)
        self.assertIn("bad", text)
        self.assertIn("boom", text)

    def test_csv_roundtrip(self):
        results = [
            Result(index=0, input="hello", output="hi", model="m", endpoint="e", duration_ms=12.0, status="ok"),
            Result(index=1, input="bad", output="", model="m", endpoint="e", duration_ms=0.0, status="failed", error="boom"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "results.csv")
            write_csv(results, path)
            text = open(path, encoding="utf-8").read()
        rows = list(csv.DictReader(io.StringIO(text)))
        self.assertEqual([r["status"] for r in rows], ["ok", "failed"])
        self.assertEqual(rows[0]["input"], "hello")
        self.assertEqual(rows[1]["error"], "boom")


if __name__ == "__main__":
    unittest.main()
