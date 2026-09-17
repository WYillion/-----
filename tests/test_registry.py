import unittest

from minagent.session import Session
from minagent.tools.base import Tool, ToolError
from minagent.tools.calculator import calculator_tool
from minagent.tools.registry import ToolRegistry


class TestRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = ToolRegistry()
        self.session = Session("s1", "system")

    def test_register_and_get(self):
        self.registry.register(calculator_tool)
        self.assertEqual(self.registry.get("calculator").name, "calculator")
        self.assertEqual(self.registry.names(), ["calculator"])

    def test_to_openai_list(self):
        self.registry.register(calculator_tool)
        tools = self.registry.to_openai_list()
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["type"], "function")
        self.assertEqual(tools[0]["function"]["name"], "calculator")
        self.assertIn("parameters", tools[0]["function"])

    def test_duplicate_register_raises(self):
        self.registry.register(calculator_tool)
        with self.assertRaises(ValueError):
            self.registry.register(calculator_tool)

    def test_unknown_tool_raises(self):
        with self.assertRaises(ToolError):
            self.registry.execute("nope", {}, self.session)

    def test_execute_success(self):
        self.registry.register(calculator_tool)
        result = self.registry.execute(
            "calculator", {"expression": "2+3"}, self.session,
        )
        self.assertEqual(result, "2+3 = 5")

    def test_execute_bad_arguments_raises(self):
        self.registry.register(calculator_tool)
        with self.assertRaises(ToolError):
            self.registry.execute("calculator", {}, self.session)


if __name__ == "__main__":
    unittest.main()