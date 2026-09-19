"""命令行入口：交互式 REPL，支持多 session 切换。"""

from __future__ import annotations

import logging
import sys

from minagent.agent import Agent, AgentError, MaxStepsExceeded
from minagent.config import Config
from minagent.llm import LLMClient
from minagent.session import SessionManager
from minagent.tools.calculator import calculator_tool
from minagent.tools.registry import ToolRegistry
from minagent.tools.search import search_tool
from minagent.tools.todo import todo_tool

SYSTEM_PROMPT = (
    "你是一个乐于助人的 AI 助手。你可以调用工具完成任务："
    "calculator 做数学计算，search 搜索信息，todo 管理待办。"
    "需要计算或查询时请调用对应工具，闲聊或总结时直接回答。"
)


def build_agent(config: Config) -> tuple[Agent, SessionManager]:
    registry = ToolRegistry()
    registry.register(calculator_tool)
    registry.register(search_tool)
    registry.register(todo_tool)

    llm = LLMClient(
        config.base_url,
        config.api_key,
        config.model,
        config.timeout,
        config.auth_header,
        config.auth_prefix,
        config.max_tokens,
    )
    agent = Agent(config, llm, registry)
    manager = SessionManager(SYSTEM_PROMPT)
    return agent, manager


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    config = Config.from_env()
    if not config.api_key:
        print("错误：未设置 DEEPSEEK_API_KEY / MINAGENT_API_KEY 环境变量")
        sys.exit(1)

    agent, manager = build_agent(config)
    current = manager.create()
    print(f"已创建 session: {current.session_id}")

    print("输入消息开始对话；命令：/new 新建会话  /list 列出会话  /switch <id> 切换  /exit 退出")

    while True:
        try:
            raw = input(f"[{current.session_id}] > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not raw:
            continue
        if raw == "/exit":
            break
        if raw == "/new":
            current = manager.create()
            print(f"已切换到新 session: {current.session_id}")
            continue
        if raw == "/list":
            print("会话列表:", ", ".join(manager.list_ids()) or "（空）")
            continue
        if raw.startswith("/switch"):
            parts = raw.split()
            if len(parts) != 2:
                print("用法: /switch <session_id>")
                continue
            try:
                current = manager.get(parts[1])
                print(f"已切换到 session: {current.session_id}")
            except KeyError as exc:
                print(exc)
            continue

        try:
            answer = agent.run(current, raw)
            print(f"[agent] {answer}")
        except AgentError as exc:
            print(f"[错误] {exc}")
        except MaxStepsExceeded as exc:
            print(f"[错误] {exc}")


if __name__ == "__main__":
    main()