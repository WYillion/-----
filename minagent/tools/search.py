"""search 工具：mock 实现，返回模拟搜索结果，证明工具链路可用。"""

from __future__ import annotations

from minagent.tools.base import Tool


def mock_search(session, query: str) -> str:
    return (
        f"[mock 搜索结果] 关于「{query}」共找到 3 条模拟结果：\n"
        f"1. {query} - 官方文档（模拟）\n"
        f"2. {query} 实践指南 - 技术博客（模拟）\n"
        f"3. {query} 常见问题 - 社区问答（模拟）"
    )


search_tool = Tool(
    name="search",
    description="搜索信息，返回相关结果（当前为 mock 实现，可替换为真实搜索）。",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "要搜索的关键词或问题"},
        },
        "required": ["query"],
    },
    func=mock_search,
)