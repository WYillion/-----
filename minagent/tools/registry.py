"""工具注册表：注册、查询、生成 Schema 列表并执行工具。"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from minagent.tools.base import Tool, ToolError

if TYPE_CHECKING:
    from minagent.session import Session


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"工具 {tool.name} 已注册，不能重复注册")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise ToolError(f"未注册的工具: {name}")
        return self._tools[name]

    def names(self) -> list[str]:
        return list(self._tools.keys())

    def to_openai_list(self) -> list[dict[str, Any]]:
        return [tool.to_openai() for tool in self._tools.values()]

    def execute(self, name: str, arguments: dict[str, Any], session: "Session") -> str:
        tool = self.get(name)
        try:
            return tool.run(session, **arguments)
        except TypeError as exc:
            raise ToolError(f"工具 {name} 参数不匹配: {exc}") from exc