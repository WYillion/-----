import unittest

from minagent.models import Step, ToolCall
from minagent.session import Session, SessionManager


class TestSession(unittest.TestCase):
    def test_messages_start_with_system(self):
        session = Session("s1", "sys")
        self.assertEqual(session.messages(), [{"role": "system", "content": "sys"}])

    def test_add_user_assistant(self):
        session = Session("s1", "sys")
        session.add_user("你好")
        session.add_assistant("你好呀")
        roles = [m["role"] for m in session.messages()]
        self.assertEqual(roles, ["system", "user", "assistant"])

    def test_add_tool_call_and_result(self):
        session = Session("s1", "sys")
        step = Step(tool_calls=[ToolCall(id="c1", name="calculator", arguments={"expression": "1+1"})])
        session.add_assistant_tool_calls(step)
        session.add_tool_result("c1", "calculator", "1+1 = 2")

        msgs = session.messages()
        self.assertEqual(msgs[-2]["role"], "assistant")
        self.assertEqual(msgs[-2]["tool_calls"][0]["id"], "c1")
        self.assertEqual(msgs[-1]["role"], "tool")
        self.assertEqual(msgs[-1]["tool_call_id"], "c1")

    def test_sessions_are_isolated(self):
        s1 = Session("s1", "sys")
        s2 = Session("s2", "sys")
        s1.add_user("窗口1的消息")
        self.assertEqual(len(s1.messages()), 2)
        self.assertEqual(len(s2.messages()), 1)


class TestSessionManager(unittest.TestCase):
    def test_create_and_get(self):
        manager = SessionManager("sys")
        a = manager.create("a")
        b = manager.create("b")
        self.assertIs(manager.get("a"), a)
        self.assertIs(manager.get("b"), b)
        self.assertEqual(set(manager.list_ids()), {"a", "b"})

    def test_duplicate_id_raises(self):
        manager = SessionManager("sys")
        manager.create("x")
        with self.assertRaises(ValueError):
            manager.create("x")

    def test_missing_session_raises(self):
        manager = SessionManager("sys")
        with self.assertRaises(KeyError):
            manager.get("missing")


if __name__ == "__main__":
    unittest.main()