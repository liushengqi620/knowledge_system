"""Smoke test for the OpenAI-compatible LLM gateway configured in env."""
from __future__ import annotations

import argparse
import sys

from config import CONFIG
from llm_client import llm_configured, post_chat_completions


def main() -> int:
    parser = argparse.ArgumentParser(description="Test LLM API connectivity.")
    parser.add_argument(
        "--prompt",
        default="Reply only with: API connected",
        help="Short prompt used for the connectivity test.",
    )
    parser.add_argument(
        "--timeout-sec",
        type=float,
        default=float(CONFIG.get("llm_timeout_sec", 90)),
        help="Request timeout in seconds.",
    )
    args = parser.parse_args()

    api_key = str(CONFIG.get("llm_api_key", "")).strip()
    base_url = str(CONFIG.get("llm_base_url", "https://api.n1n.ai/v1")).rstrip("/")
    model = str(CONFIG.get("llm_model", "gpt-5.5")).strip()

    if not llm_configured(api_key):
        print("LLM_API_KEY is not configured. Check project root .env.")
        return 2

    print(f"LLM base URL: {base_url}")
    print(f"LLM model: {model}")
    print("LLM API key: <set>")

    reply = post_chat_completions(
        api_key=api_key,
        base_url=base_url,
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a concise API connectivity test assistant.",
            },
            {"role": "user", "content": args.prompt},
        ],
        temperature=0.0,
        timeout_sec=args.timeout_sec,
        max_retries=1,
    )
    print("LLM reply:")
    print(reply.strip())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"LLM connection test failed: {exc}", file=sys.stderr)
        raise
