from __future__ import annotations

import os
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _read_env_files() -> dict[str, str]:
    values: dict[str, str] = {}
    for path in (PROJECT_ROOT / ".env", PROJECT_ROOT / ".env.local", Path(__file__).resolve().parent / ".env"):
        if not path.is_file():
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip().lstrip("\ufeff")] = value.strip().strip('"').strip("'")
    return values


_FILE_ENV = _read_env_files()


def _env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
        value = _FILE_ENV.get(name)
        if value:
            return value
    return default


CONFIG: dict[str, Any] = {
    "llm_api_key": _env("STEEL_LLM_API_KEY", "LLM_API_KEY", "OPENAI_API_KEY"),
    "llm_base_url": _env("STEEL_LLM_API_URL", "LLM_BASE_URL", "OPENAI_BASE_URL", default="https://api.n1n.ai/v1"),
    "llm_model": _env("STEEL_LLM_MODEL", "LLM_MODEL", "OPENAI_MODEL", default="gpt-5.5"),
    "llm_timeout_sec": float(_env("STEEL_LLM_TIMEOUT_SEC", "LLM_TIMEOUT_SEC", default="45")),
}
