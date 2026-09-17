import unittest
from unittest import mock

from minagent.agent import Agent, MaxStepsExceeded
from minagent.config import Config
from minagent.models import Step, ToolCall
from minagent.session import Session
from minagent.tools.base import Tool, ToolError
from minagent.tools.calculator import calculator_tool
from minagent.tools.registry import ToolRegistry


def _final(content):
    return {"choices": [{"message": {"role": "assistant", "content": content}, "finish_reason": "stop"}]}


def _tool_call(name="calculator", arguments='{"expression": "1+2"}', call_id="c1"):
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": call_id,
                            "type": "function",
                            "function": {"name": name, "arguments": arguments},
                        }
                    ],
                },
                "finish_reason": "tool_calls",
            }
        ]
    }


class TestAgent(unittest.TestCase):
    def setUp(self):
        self.config = Config(api_key="test-key", max_steps=5)
        self.llm = mock.MagicMock()
        self.registry = ToolRegistry()
        self.registry.register(calculator_tool)
        self.agent = Agent(self.config, self.llm, self.registry)
        self.session = Session("s1", "sys")

    def test_direct_reply(self):
        self.llm.chat.return_value = _final("你好！")
        result = self.agent.run(self.session, "hi")
        self.assertEqual(result, "你好！")
        self.assertIn({"role": "assistant", "content": "你好！"}, self.session.messages())

    def test_single_tool_call_then_final(self):
        self.llm.chat.side_effect = [
            _tool_call(arguments='{"expression": "2+3"}'),
            _final("结果是 5"),
        ]
        result = self.agent.run(self.session, "算 2+3")
        self.assertEqual(result, "结果是 5")

        msgs = self.session.messages()
        roles = [m["role"] for m in msgs]
        self.assertIn("tool", roles)

        tool_msg = next(m for m in msgs if m["role"] == "tool")
        self.assertEqual(tool_msg["content"], "2+3 = 5")

    def test_multiple_tool_calls_in_sequence(self):
        self.llm.chat.side_effect = [
            _tool_call(arguments='{"expression": "1+1"}', call_id="c1"),
            _tool_call(arguments='{"expression": "10*10"}', call_id="c2"),
            _final("算完了"),
        ]
        result = self.agent.run(self.session, "连续计算")
        self.assertEqual(result, "算完了")
        self.assertEqual(self.llm.chat.call_count, 3)

    def test_broken_tool_result_does_not_crash(self):
        boom = Tool(
            name="boom",
            description="总是失败",
            parameters={"type": "object", "properties": {}},
            func=lambda session: (_ for _ in ()).throw(ToolError("爆炸")),
        )
        self.registry.register(boom)
        self.llm.chat.side_effect = [
            _tool_call(name="boom", arguments="{}"),
            _final("工具失败但我会继续"),
        ]
        result = self.agent.run(self.session, "触发失败工具")
        self.assertEqual(result, "工具失败但我会继续")

        tool_msg = next(m for m in self.session.messages() if m["role"] == "tool")
        self.assertIn("工具执行错误", tool_msg["content"])

    def test_max_steps_exceeded(self):
        self.config.max_steps = 2
        agent = Agent(self.config, self.llm, self.registry)
        self.llm.chat.side_effect = [
            _tool_call(call_id=f"c{i}") for i in range(3)
        ]
        with self.assertRaises(MaxStepsExceeded):
            agent.run(self.session, "死循环")

    def test_context_compression_triggered(self):
        config = Config(api_key="k", max_steps=5, max_context_messages=6, keep_recent_messages=2)
        agent = Agent(config, self.llm, self.registry)
        session = Session("s1", "sys")

        def fake_chat(messages, tools=None, **kwargs):
            if tools is None:
                return _final("这是一段摘要")
            return _final("本轮回答")

        self.llm.chat.side_effect = fake_chat
        for i in range(8):
            agent.run(session, f"问题{i}")

        summary_msgs = [m for m in session.messages() if "早期对话摘要" in m.get("content", "")]
        self.assertGreaterEqual(len(summary_msgs), 1)


if __name__ == "__main__":
    unittest.main()