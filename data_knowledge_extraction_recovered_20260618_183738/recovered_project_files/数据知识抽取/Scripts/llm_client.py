from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any, Mapping, Sequence


def llm_configured(api_key: str | None) -> bool:
    key = str(api_key or "").strip()
    return bool(key and key.lower() not in {"your_api_key", "sk-xxx", "changeme"})


def _chat_url(base_url: str) -> str:
    root = str(base_url or "").strip().rstrip("/")
    if not root:
        root = "https://api.n1n.ai/v1"
    return f"{root}/chat/completions"


def _extract_content(payload: Mapping[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0]
    if not isinstance(first, Mapping):
        return ""
    message = first.get("message")
    if isinstance(message, Mapping):
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, Mapping) and isinstance(item.get("text"), str):
                    parts.append(str(item["text"]))
            return "\n".join(parts)
    text = first.get("text")
    return str(text or "")


def post_chat_completions(
    *,
    api_key: str,
    base_url: str,
    model: str,
    messages: Sequence[Mapping[str, str]],
    temperature: float = 0.2,
    timeout_sec: float = 45.0,
    max_retries: int = 1,
) -> str:
    if not llm_configured(api_key):
        raise RuntimeError("LLM API key is not configured")
    body = json.dumps(
        {
            "model": model,
            "messages": list(messages),
            "temperature": temperature,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        _chat_url(base_url),
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
            ),
        },
    )
    last_error: Exception | None = None
    for attempt in range(max(1, int(max_retries) + 1)):
        try:
            with urllib.request.urlopen(request, timeout=float(timeout_sec)) as response:
                payload = json.loads(response.read().decode("utf-8"))
            content = _extract_content(payload)
            if not content.strip():
                raise RuntimeError("LLM response did not contain assistant content")
            return content
        except urllib.error.HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8", errors="replace")
            except Exception:
                detail = ""
            if detail:
                last_error = RuntimeError(f"HTTP Error {exc.code}: {exc.reason}; body={detail[:800]}")
            else:
                last_error = exc
            if attempt >= int(max_retries):
                break
            time.sleep(0.5 * (attempt + 1))
        except (urllib.error.URLError, TimeoutError, RuntimeError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt >= int(max_retries):
                break
            time.sleep(0.5 * (attempt + 1))
    raise RuntimeError(f"LLM request failed: {last_error}")
