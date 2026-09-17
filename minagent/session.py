"""Session 与 SessionManager：多窗口会话隔离与消息历史管理。"""

from __future__ import annotations

import json
import uuid
from typing import Any

from minagent.models import Step


class Session:
    """一个独立会话，持有自己的消息历史与工具状态。"""

    def __init__(self, session_id: str, system_prompt: str) -> None:
        self.session_id = session_id
        self.state: dict[str, Any] = {}
        self._messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt}
        ]

    def add_user(self, content: str) -> None:
        self._messages.append({"role": "user", "content": content})

    def add_assistant(self, content: str) -> None:
        self._messages.append({"role": "assistant", "content": content})

    def add_assistant_tool_calls(self, step: Step) -> None:
        message: dict[str, Any] = {"role": "assistant", "content": step.content}
        message["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.name,
                    "arguments": json.dumps(tc.arguments, ensure_ascii=False),
                },
            }
            for tc in step.tool_calls
        ]
        self._messages.append(message)

    def add_tool_result(self, tool_call_id: str, name: str, content: str) -> None:
        self._messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "name": name,
                "content": content,
            }
        )

    def messages(self) -> list[dict[str, Any]]:
        return list(self._messages)

    def replace_messages(self, messages: list[dict[str, Any]]) -> None:
        self._messages = list(messages)


class SessionManager:
    """管理多个会话，按 session_id 隔离，可随时切换回任意窗口继续聊。"""

    def __init__(self, system_prompt: str) -> None:
        self.system_prompt = system_prompt
        self._sessions: dict[str, Session] = {}

    def create(self, session_id: str = None) -> Session:
        sid = session_id or uuid.uuid4().hex[:8]
        if sid in self._sessions:
            raise ValueError(f"session {sid} 已存在")
        session = Session(sid, self.system_prompt)
        self._sessions[sid] = session
        return session

    def get(self, session_id: str) -> Session:
        if session_id not in self._sessions:
            raise KeyError(f"session {session_id} 不存在")
        return self._sessions[session_id]

    def list_ids(self) -> list[str]:
        return list(self._sessions.keys())