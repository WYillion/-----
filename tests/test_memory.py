import unittest

from minagent.memory import (
    compress_messages,
    estimate_messages_tokens,
    estimate_tokens,
)


class TestEstimateTokens(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(estimate_tokens(""), 0)

    def test_english(self):
        self.assertGreater(estimate_tokens("hello world"), 0)

    def test_chinese(self):
        self.assertEqual(estimate_tokens("你好世界"), 4)

    def test_messages_total(self):
        msgs = [{"role": "user", "content": "你好"}]
        self.assertGreater(estimate_messages_tokens(msgs), 0)


class TestCompressMessages(unittest.TestCase):
    def _messages(self):
        return [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "u2"},
            {"role": "assistant", "content": "a2"},
            {"role": "user", "content": "u3"},
            {"role": "assistant", "content": "a3"},
        ]

    def test_no_compress_when_short(self):
        msgs = self._messages()
        result = compress_messages(msgs, keep_recent=10, summarize_fn=lambda t: "S")
        self.assertEqual(len(result), len(msgs))

    def test_compress_keeps_system_and_recent(self):
        msgs = self._messages()
        result = compress_messages(msgs, keep_recent=2, summarize_fn=lambda t: "摘要")
        self.assertEqual(result[0]["role"], "system")
        self.assertIn("早期对话摘要", result[1]["content"])
        self.assertEqual([m["role"] for m in result[2:]], ["user", "assistant"])
        self.assertEqual(result[2]["content"], "u3")
        self.assertEqual(result[3]["content"], "a3")

    def test_summary_function_receives_middle(self):
        msgs = self._messages()
        captured = {}

        def summarize(text):
            captured["text"] = text
            return "S"

        compress_messages(msgs, keep_recent=2, summarize_fn=summarize)
        self.assertIn("u1", captured["text"])
        self.assertIn("a2", captured["text"])
        self.assertNotIn("u3", captured["text"])


if __name__ == "__main__":
    unittest.main()