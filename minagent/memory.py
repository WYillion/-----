"""Context 管理：token 估算与基础的对话压缩。"""

from __future__ import annotations

from typing import Any, Callable


def estimate_tokens(text: str) -> int:
    """粗略 token 估算：英文按 4 字符一个 token，对中文做更保守估算。"""
    if not text:
        return 0
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    other = len(text) - cjk
    return max(1, cjk + other // 4)


def estimate_messages_tokens(messages: list[dict[str, Any]]) -> int:
    return sum(estimate_tokens(str(msg)) for msg in messages)


def compress_messages(
    messages: list[dict[str, Any]],
    keep_recent: int,
    summarize_fn: Callable[[str], str],
) -> list[dict[str, Any]]:
    """基础压缩：保留 system 消息与最近 keep_recent 条原文，中间部分压缩为摘要。"""
    if len(messages) <= keep_recent + 2:
        return messages

    head = messages[:1]
    tail = messages[len(messages) - keep_recent:]
    middle = messages[1: len(messages) - keep_recent]

    lines = []
    for msg in middle:
        content = msg.get("content") or ""
        if msg.get("role") == "tool":
            lines.append(f"[工具结果] {msg.get('name')}: {content}")
        elif msg.get("tool_calls"):
            lines.append("[assistant 发起工具调用]")
        else:
            lines.append(f"{msg.get('role')}: {content}")
    transcript = "\n".join(lines)

    summary = summarize_fn(transcript)
    summary_msg = {"role": "system", "content": f"[早期对话摘要]\n{summary}"}
    return head + [summary_msg] + tail