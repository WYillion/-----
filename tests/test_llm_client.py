import json
import unittest
from unittest import mock

from minagent.llm import LLMClient, LLMError, parse_step


class TestLLMClientRequest(unittest.TestCase):
    def _capture_request(self, client):
        captured = {}

        def fake_urlopen(request, timeout=None):
            captured["headers"] = dict(request.headers)
            captured["data"] = json.loads(request.data.decode("utf-8"))

            ctx = mock.MagicMock()
            body = b'{"choices": [{"message": {"role": "assistant", "content": "hi"}, "finish_reason": "stop"}]}'
            ctx.__enter__.return_value.read.return_value = body
            return ctx

        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
            client.chat([{"role": "user", "content": "hello"}])
        return captured

    def test_endpoint(self):
        client = LLMClient(
            "https://note3-prev-api.askdiandian.com/v1", "ak", "dots3-note-prev",
        )
        self.assertEqual(
            client.endpoint,
            "https://note3-prev-api.askdiandian.com/v1/chat/completions",
        )

    def test_uses_api_key_header_not_authorization(self):
        client = LLMClient(
            "https://note3-prev-api.askdiandian.com/v1", "ak_test", "dots3-note-prev",
        )
        captured = self._capture_request(client)
        lower = {k.lower(): v for k, v in captured["headers"].items()}
        self.assertEqual(lower["api-key"], "ak_test")
        self.assertNotIn("authorization", lower)

    def test_payload_contains_model_and_messages(self):
        client = LLMClient(
            "https://x/v1", "ak", "dots3-note-prev", max_tokens=1024,
        )
        captured = self._capture_request(client)
        self.assertEqual(captured["data"]["model"], "dots3-note-prev")
        self.assertEqual(captured["data"]["messages"], [{"role": "user", "content": "hello"}])
        self.assertEqual(captured["data"]["stream"], False)
        self.assertEqual(captured["data"]["max_tokens"], 1024)

    def test_payload_includes_tools(self):
        client = LLMClient("https://x/v1", "ak", "m")
        captured = {}
        tools = [{"type": "function", "function": {"name": "t", "description": "", "parameters": {}}}]

        def fake_urlopen(request, timeout=None):
            captured["data"] = json.loads(request.data.decode("utf-8"))
            ctx = mock.MagicMock()
            ctx.__enter__.return_value.read.return_value = b'{"choices": []}'
            return ctx

        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
            client.chat([{"role": "user", "content": "x"}], tools=tools)
        self.assertEqual(captured["data"]["tools"], tools)


class TestLLMClientErrors(unittest.TestCase):
    def test_http_error_reports_status(self):
        import urllib.error

        client = LLMClient("https://x/v1", "ak", "m")

        def fake_urlopen(request, timeout=None):
            raise urllib.error.HTTPError(
                client.endpoint, 401, "Unauthorized", {}, None,
            )

        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
            with self.assertRaises(LLMError):
                client.chat([{"role": "user", "content": "x"}])


if __name__ == "__main__":
    unittest.main()