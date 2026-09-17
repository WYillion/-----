"""LLM 客户端与输出解析：基于标准库直连 OpenAI-compatible 接口。"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Optional

from minagent.models import Step, ToolCall


class LLMError(RuntimeError):
    """LLM 调用或响应解析出错。"""


class LLMClient:
    def __init__(self, base_url: str, api_key: str, model: str, timeout: int = 60) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    @property
    def endpoint(self) -> str:
        return self.base_url + "/chat/completions"

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: Optional[float] = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools
        if temperature is not None:
            payload["temperature"] = temperature

        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=data,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise LLMError(f"HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise LLMError(f"网络错误: {exc.reason}") from exc
        except Exception as exc:
            raise LLMError(f"请求失败: {exc}") from exc

        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            raise LLMError(f"响应不是合法 JSON: {body[:200]}") from exc


def parse_step(response: dict[str, Any]) -> Step:
    """解析一轮 LLM 响应，提取思考过程、工具调用或最终答案。"""
    choices = response.get("choices") or []
    if not choices:
        raise LLMError(f"LLM 响应缺少 choices: {response}")

    message = choices[0].get("message") or {}

    tool_calls: list[ToolCall] = []
    for tc in message.get("tool_calls") or []:
        function = tc.get("function") or {}
        raw_args = function.get("arguments") or "{}"
        try:
            arguments = json.loads(raw_args)
        except (json.JSONDecodeError, TypeError):
            arguments = {}
        tool_calls.append(
            ToolCall(
                id=tc.get("id", ""),
                name=function.get("name", ""),
                arguments=arguments,
            )
        )

    return Step(
        content=message.get("content"),
        reasoning=message.get("reasoning_content"),
        tool_calls=tool_calls,
    )