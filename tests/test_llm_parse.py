import unittest

from minagent.llm import LLMError, parse_step


class TestParseStep(unittest.TestCase):
    def test_final_answer(self):
        response = {
            "choices": [{"message": {"role": "assistant", "content": "你好"}, "finish_reason": "stop"}]
        }
        step = parse_step(response)
        self.assertTrue(step.is_final)
        self.assertFalse(step.has_tool_calls)
        self.assertEqual(step.content, "你好")

    def test_tool_call(self):
        response = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "c1",
                                "type": "function",
                                "function": {
                                    "name": "calculator",
                                    "arguments": '{"expression": "1+2"}',
                                },
                            }
                        ],
                    },
                    "finish_reason": "tool_calls",
                }
            ]
        }
        step = parse_step(response)
        self.assertTrue(step.has_tool_calls)
        self.assertEqual(step.tool_calls[0].name, "calculator")
        self.assertEqual(step.tool_calls[0].arguments["expression"], "1+2")

    def test_reasoning_content(self):
        response = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "结果",
                        "reasoning_content": "先思考再回答",
                    },
                    "finish_reason": "stop",
                }
            ]
        }
        step = parse_step(response)
        self.assertEqual(step.reasoning, "先思考再回答")

    def test_malformed_arguments_becomes_empty(self):
        response = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "c1",
                                "type": "function",
                                "function": {"name": "x", "arguments": "not json"},
                            }
                        ],
                    },
                    "finish_reason": "tool_calls",
                }
            ]
        }
        step = parse_step(response)
        self.assertEqual(step.tool_calls[0].arguments, {})

    def test_missing_choices_raises(self):
        with self.assertRaises(LLMError):
            parse_step({"choices": []})


if __name__ == "__main__":
    unittest.main()