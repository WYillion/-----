"""calculator 工具：基于 AST 的安全数学表达式求值，杜绝 eval 注入。"""

from __future__ import annotations

import ast
import operator
from typing import Any

from minagent.tools.base import Tool, ToolError

_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _eval_node(node: ast.expr) -> Any:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return _BINOPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
        return _UNARY[type(node.op)](_eval_node(node.operand))
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    raise ToolError(f"不支持的表达式节点: {ast.dump(node)}")


def _format_number(value: Any) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def safe_calc(expression: str) -> str:
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ToolError(f"表达式语法错误: {exc}") from exc
    try:
        result = _eval_node(tree)
    except (ToolError, ZeroDivisionError, OverflowError, ValueError) as exc:
        raise ToolError(f"计算失败: {exc}") from exc
    return f"{expression} = {_format_number(result)}"


calculator_tool = Tool(
    name="calculator",
    description="计算数学表达式，支持 + - * / // % ** 等运算，返回计算结果。",
    parameters={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "要计算的数学表达式，例如 (3 + 5) * 2",
            }
        },
        "required": ["expression"],
    },
    func=lambda session, expression: safe_calc(expression),
)