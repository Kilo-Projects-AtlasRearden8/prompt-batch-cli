import unittest

from prompt_batch.client import Completion, LLMError, OpenAICompatibleClient
from tests.conftest import start_mock_endpoint


class OpenAICompatibleClientTest(unittest.TestCase):
    def setUp(self):
        self.server, self.base_url = start_mock_endpoint()
        self.addCleanup(self.server.shutdown)

    def test_chat_returns_echo_text(self):
        client = OpenAICompatibleClient(base_url=self.base_url, model="mock-model")
        completion = client.chat([{"role": "user", "content": "Hello"}])
        self.assertIsInstance(completion, Completion)
        self.assertIn("Mock completion for: Hello", completion.text)
        self.assertEqual(completion.endpoint, f"{self.base_url}/v1/chat/completions")

    def test_chat_uses_requested_model(self):
        client = OpenAICompatibleClient(base_url=self.base_url, model="default-model")
        completion = client.chat([{"role": "user", "content": "hi"}], model="override-model")
        self.assertEqual(completion.model, "override-model")

    def test_chat_endpoint_error(self):
        client = OpenAICompatibleClient(base_url=self.base_url)

        class FailingClient(OpenAICompatibleClient):
            def chat(self, messages, model=None):  # noqa: ARG002
                raise LLMError("endpoint http://127.0.0.1:1 returned error: booom")

        with self.assertRaises(LLMError):
            FailingClient(base_url=self.base_url).chat([{"role": "user", "content": "hi"}])

    def test_unreachable_endpoint_raises_llm_error(self):
        client = OpenAICompatibleClient(base_url="http://127.0.0.1:1", timeout=2.0)
        with self.assertRaises(LLMError):
            client.chat([{"role": "user", "content": "hi"}])


if __name__ == "__main__":
    unittest.main()
