import os
import tempfile
import unittest

from prompt_batch.cli import main
from tests.conftest import start_mock_endpoint


class CliTest(unittest.TestCase):
    def setUp(self):
        self.server, self.base_url = start_mock_endpoint()
        self.addCleanup(self.server.shutdown)

    def _write(self, name, content):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)
        return path

    def test_cli_writes_md_and_csv(self):
        self.tmp = tempfile.mkdtemp()
        inputs = self._write("inputs.txt", "one\ntwo\nthree\n")
        template = self._write("template.txt", "Prompt: $input\n")
        rc = main(
            [
                "--inputs",
                inputs,
                "--template",
                template,
                "--output",
                os.path.join(self.tmp, "out"),
                "--format",
                "both",
                "--base-url",
                self.base_url,
                "--model",
                "mock-model",
            ]
        )
        self.assertEqual(rc, 0)
        md = open(os.path.join(self.tmp, "out", "results.md"), encoding="utf-8").read()
        csv_text = open(os.path.join(self.tmp, "out", "results.csv"), encoding="utf-8").read()
        self.assertIn("Prompt: one", md)
        self.assertIn("Mock completion for: Prompt: one", md)
        self.assertIn("one", csv_text)
        self.assertIn("three", csv_text)

    def test_cli_reports_failed_items_without_crash(self):
        self.tmp = tempfile.mkdtemp()
        inputs = self._write("inputs.txt", "good\n")
        template = self._write("template.txt", "$input\n")
        rc = main(
            [
                "--inputs",
                inputs,
                "--template",
                template,
                "--output",
                os.path.join(self.tmp, "out"),
                "--format",
                "csv",
                "--base-url",
                "http://127.0.0.1:1",
                "--model",
                "mock-model",
            ]
        )
        self.assertEqual(rc, 1)
        csv_text = open(os.path.join(self.tmp, "out", "results.csv"), encoding="utf-8").read()
        self.assertIn("failed", csv_text)


if __name__ == "__main__":
    unittest.main()
