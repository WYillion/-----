"""运行时配置，从环境变量或 .env 文件加载。"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _load_env_file(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass
class Config:
    base_url: str = "https://note3-prev-api.askdiandian.com/v1"
    api_key: str = ""
    model: str = "dots3-note-prev"
    auth_header: str = "api-key"
    auth_prefix: str = ""
    max_tokens: int = 0
    max_steps: int = 10
    max_context_messages: int = 20
    keep_recent_messages: int = 6
    timeout: int = 60

    @classmethod
    def from_env(cls) -> "Config":
        _load_env_file()
        return cls(
            base_url=os.getenv(
                "MINAGENT_BASE_URL", "https://note3-prev-api.askdiandian.com/v1"
            ).rstrip("/"),
            api_key=os.getenv("MINAGENT_API_KEY", os.getenv("DEEPSEEK_API_KEY", "")),
            model=os.getenv("MINAGENT_MODEL", "dots3-note-prev"),
            auth_header=os.getenv("MINAGENT_AUTH_HEADER", "api-key"),
            auth_prefix=os.getenv("MINAGENT_AUTH_PREFIX", ""),
            max_tokens=int(os.getenv("MINAGENT_MAX_TOKENS", "0")),
            max_steps=int(os.getenv("MINAGENT_MAX_STEPS", "10")),
            max_context_messages=int(os.getenv("MINAGENT_MAX_CONTEXT_MESSAGES", "20")),
            keep_recent_messages=int(os.getenv("MINAGENT_KEEP_RECENT_MESSAGES", "6")),
            timeout=int(os.getenv("MINAGENT_TIMEOUT", "60")),
        )