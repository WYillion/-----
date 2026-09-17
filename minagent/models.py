"""Agent 内部使用的数据模型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass
class Step:
    """一轮 LLM 输出的解析结果：思考过程 / 工具调用 / 最终答案。"""

    content: Optional[str] = None
    reasoning: Optional[str] = None
    tool_calls: list[ToolCall] = field(default_factory=list)

    @property
    def has_tool_calls(self) -> bool:
        return bool(self.tool_calls)

    @property
    def is_final(self) -> bool:
        return bool(self.content) and not self.tool_calls