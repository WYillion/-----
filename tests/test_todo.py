import unittest

from minagent.session import Session
from minagent.tools.base import ToolError
from minagent.tools.todo import todo_tool


class TestTodoTool(unittest.TestCase):
    def setUp(self):
        self.session = Session("s1", "system")

    def do(self, **kwargs):
        return todo_tool.run(self.session, **kwargs)

    def test_add_and_list(self):
        self.assertIn("买菜", self.do(action="add", task="买菜"))
        self.assertIn("买菜", self.do(action="list"))

    def test_add_requires_task(self):
        with self.assertRaises(ToolError):
            self.do(action="add")

    def test_done_and_index(self):
        self.do(action="add", task="写周报")
        out = self.do(action="done", index=0)
        self.assertIn("完成", out)
        self.assertIn("[x]", self.do(action="list"))

    def test_bad_index(self):
        with self.assertRaises(ToolError):
            self.do(action="done", index=5)

    def test_state_isolated_per_session(self):
        other = Session("s2", "system")
        self.do(action="add", task="会话1的待办")
        self.assertIn("会话1的待办", self.do(action="list"))
        self.assertIn("（暂无待办）", todo_tool.run(other, action="list"))


if __name__ == "__main__":
    unittest.main()