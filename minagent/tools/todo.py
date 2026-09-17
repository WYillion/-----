"""todo 工具：有状态工具，状态隔离在各自 session 内，互不影响。"""

from __future__ import annotations

from minagent.tools.base import Tool, ToolError


def _fmt(items):
    if not items:
        return "（暂无待办）"
    lines = []
    for i, item in enumerate(items):
        mark = "[x]" if item["done"] else "[ ]"
        lines.append(f"{i}. {mark} {item['task']}")
    return "\n".join(lines)


def run_todo(session, action: str, task: str = None, index: int = None) -> str:
    items = session.state.setdefault("todo", [])

    if action == "add":
        if not task:
            raise ToolError("add 操作需要 task 参数")
        items.append({"task": task, "done": False})
        return f"已添加待办「{task}」，当前共 {len(items)} 项。"

    if action == "list":
        return "当前待办列表：\n" + _fmt(items)

    if action in ("done", "remove"):
        if index is None:
            raise ToolError(f"{action} 操作需要 index 参数（从 0 开始）")
        idx = int(index)
        if idx < 0 or idx >= len(items):
            raise ToolError(f"index {idx} 超出范围（0~{len(items) - 1}）")
        if action == "done":
            items[idx]["done"] = True
            return f"已将「{items[idx]['task']}」标记为完成。"
        removed = items.pop(idx)
        return f"已移除待办「{removed['task']}」。"

    raise ToolError(f"不支持的 action: {action}，可选 add / list / done / remove")


todo_tool = Tool(
    name="todo",
    description="管理待办事项列表，支持 add（添加）、list（查看）、done（完成）、remove（删除）。状态按会话隔离。",
    parameters={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["add", "list", "done", "remove"],
                "description": "要执行的操作",
            },
            "task": {"type": "string", "description": "add 时的待办内容"},
            "index": {"type": "integer", "description": "done/remove 时的待办序号（从 0 开始）"},
        },
        "required": ["action"],
    },
    func=run_todo,
)