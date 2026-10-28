import unittest

from prompt_batch.template import TemplateError, render_template


class TemplateTest(unittest.TestCase):
    def test_renders_input(self):
        self.assertEqual(
            render_template("Say: $input", "hello"),
            "Say: hello",
        )

    def test_multiple_occurrences(self):
        self.assertEqual(
            render_template("$input ... $input", "x"),
            "x ... x",
        )

    def test_dollar_escape(self):
        self.assertEqual(
            render_template("Cost: $$5 for $input", "tea"),
            "Cost: $5 for tea",
        )

    def test_unknown_variable_raises(self):
        with self.assertRaises(TemplateError):
            render_template("Say: $name", "hello")

    def test_malformed_template_raises(self):
        with self.assertRaises(TemplateError):
            render_template("Say: $", "hello")


if __name__ == "__main__":
    unittest.main()
