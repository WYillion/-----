"""工具抽象：每个工具包含名称、描述与参数 Schema，LLM 基于 Schema 自主决策调用。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from minagent.session import Session


class ToolError(Exception):
    """工具执行期间发生的错误。"""


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)
    func: Optional[Callable[..., str]] = field(default=None, repr=False)

    def to_openai(self) -> dict[str, Any]:
        """转换为 OpenAI-compatible 的 tools 参数格式。"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def run(self, session: "Session", **kwargs: Any) -> str:
        if self.func is None:
            raise ToolError(f"工具 {self.name} 没有绑定实现")
        return str(self.func(session, **kwargs))