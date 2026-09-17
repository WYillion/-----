"""运行时配置，全部从环境变量加载。"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Config:
    base_url: str = "https://api.deepseek.com"
    api_key: str = ""
    model: str = "deepseek-chat"
    max_steps: int = 10
    max_context_messages: int = 20
    keep_recent_messages: int = 6
    timeout: int = 60

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            base_url=os.getenv("MINAGENT_BASE_URL", "https://api.deepseek.com").rstrip("/"),
            api_key=os.getenv("MINAGENT_API_KEY", os.getenv("DEEPSEEK_API_KEY", "")),
            model=os.getenv("MINAGENT_MODEL", "deepseek-chat"),
            max_steps=int(os.getenv("MINAGENT_MAX_STEPS", "10")),
            max_context_messages=int(os.getenv("MINAGENT_MAX_CONTEXT_MESSAGES", "20")),
            keep_recent_messages=int(os.getenv("MINAGENT_KEEP_RECENT_MESSAGES", "6")),
            timeout=int(os.getenv("MINAGENT_TIMEOUT", "60")),
        )