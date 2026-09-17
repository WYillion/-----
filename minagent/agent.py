"""Agent Runtime：从零实现的 ReAct 主循环。"""

from __future__ import annotations

import logging
from typing import Optional

from minagent.config import Config
from minagent.llm import LLMClient, parse_step
from minagent.memory import compress_messages
from minagent.models import Step
from minagent.session import Session
from minagent.tools.registry import ToolRegistry

logger = logging.getLogger("minagent.agent")


class MaxStepsExceeded(RuntimeError):
    """工具调用循环超过最大轮次限制。"""


class AgentError(RuntimeError):
    """Agent 运行中的通用错误。"""


class Agent:
    def __init__(
        self,
        config: Config,
        llm: LLMClient,
        registry: ToolRegistry,
    ) -> None:
        self.config = config
        self.llm = llm
        self.registry = registry

    def run(self, session: Session, user_input: str) -> str:
        """接收用户输入，循环执行直到返回最终答案或超限。"""
        session.add_user(user_input)

        for step_idx in range(self.config.max_steps):
            self._maybe_compress(session)

            try:
                response = self.llm.chat(
                    session.messages(),
                    tools=self.registry.to_openai_list(),
                )
            except Exception as exc:
                raise AgentError(f"LLM 调用失败: {exc}") from exc

            step = parse_step(response)
            self._log_step(session.session_id, step_idx, step)

            if step.has_tool_calls:
                session.add_assistant_tool_calls(step)
                for tool_call in step.tool_calls:
                    result = self._execute_tool(session, tool_call)
                    session.add_tool_result(
                        tool_call.id, tool_call.name, result,
                    )
                continue

            if step.is_final:
                session.add_assistant(step.content)
                return step.content

            raise AgentError("模型既没有输出内容，也没有工具调用")

        raise MaxStepsExceeded(
            f"超过最大轮次限制（{self.config.max_steps}），可能陷入工具调用循环"
        )

    def _execute_tool(self, session: Session, tool_call) -> str:
        try:
            result = self.registry.execute(
                tool_call.name, tool_call.arguments, session,
            )
            logger.info(
                "[session=%s] 工具调用 %s(%s) -> %s",
                session.session_id, tool_call.name, tool_call.arguments, result,
            )
            return result
        except Exception as exc:
            error = f"工具执行错误: {exc}"
            logger.warning(
                "[session=%s] 工具调用失败 %s(%s): %s",
                session.session_id, tool_call.name, tool_call.arguments, exc,
            )
            return error

    def _maybe_compress(self, session: Session) -> None:
        messages = session.messages()
        if len(messages) <= self.config.max_context_messages:
            return
        logger.info(
            "[session=%s] 消息数 %d 超过阈值 %d，触发压缩",
            session.session_id, len(messages), self.config.max_context_messages,
        )
        session.replace_messages(
            compress_messages(
                messages,
                self.config.keep_recent_messages,
                self._summarize,
            )
        )

    def _summarize(self, transcript: str) -> str:
        prompt = (
            "请把下面这段对话压缩成一段简洁摘要，保留关键事实、用户偏好、"
            "未完成的任务和重要数字，去掉寒暄与重复内容：\n\n" + transcript
        )
        try:
            response = self.llm.chat([{"role": "user", "content": prompt}])
            step = parse_step(response)
            return step.content or transcript
        except Exception as exc:
            logger.warning("摘要生成失败，回退为原始文本: %s", exc)
            return transcript

    @staticmethod
    def _log_step(session_id: str, step_idx: int, step: Step) -> None:
        if step.reasoning:
            logger.info("[session=%s] 第 %d 步思考: %s", session_id, step_idx, step.reasoning)
        if step.tool_calls:
            for tc in step.tool_calls:
                logger.info(
                    "[session=%s] 第 %d 步决定调用工具: %s(%s)",
                    session_id, step_idx, tc.name, tc.arguments,
                )
        elif step.content:
            logger.info("[session=%s] 第 %d 步给出最终答案", session_id, step_idx)