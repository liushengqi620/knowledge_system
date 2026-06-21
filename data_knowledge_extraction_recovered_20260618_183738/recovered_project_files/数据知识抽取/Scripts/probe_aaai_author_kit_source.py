from __future__ import annotations

import argparse
import json
import ssl
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / "knowledge_exports" / "aaai_author_kit_source_probe.json"

DEFAULT_URLS = [
    "https://aaai.org/conference/aaai/aaai-27/",
    "https://aaai.org/authorkit27/",
    "https://aaai.org/authorkit26/",
    "https://aaai.org/wp-content/uploads/2026/03/AAAI-27-Author-Kit.zip",
    "https://aaai.org/wp-content/uploads/2026/03/AAAI27-Author-Kit.zip",
    "https://aaai.org/wp-content/uploads/2026/03/aaai2027.zip",
    "https://aaai.org/wp-content/uploads/2026/05/AAAI-27-Author-Kit.zip",
    "https://aaai.org/wp-content/uploads/2026/05/aaai2027.zip",
    "https://aaai.org/wp-content/uploads/2026/06/AAAI-27-Author-Kit.zip",
    "https://aaai.org/wp-content/uploads/2026/06/aaai2027.zip",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/zip,*/*;q=0.8",
}


def _probe(url: str, timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(url, headers=HEADERS, method="HEAD")
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=ssl.create_default_context()) as response:
            headers = response.headers
            return {
                "url": url,
                "status_code": response.status,
                "content_type": headers.get("Content-Type", ""),
                "content_length": headers.get("Content-Length", ""),
                "location": headers.get("Location", ""),
                "error": "",
            }
    except urllib.error.HTTPError as exc:
        headers = exc.headers
        return {
            "url": url,
            "status_code": exc.code,
            "content_type": headers.get("Content-Type", "") if headers else "",
            "content_length": headers.get("Content-Length", "") if headers else "",
            "location": headers.get("Location", "") if headers else "",
            "error": str(exc.reason),
        }
    except Exception as exc:  # pragma: no cover - depends on host network state.
        return {
            "url": url,
            "status_code": None,
            "content_type": "",
            "content_length": "",
            "location": "",
            "error": type(exc).__name__ + ": " + str(exc),
        }


def build_probe_report(urls: list[str], output_path: Path, timeout: float) -> dict[str, Any]:
    results = [_probe(url, timeout) for url in urls]
    report = {
        "status": "completed",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "output_path": output_path.as_posix(),
        "method": "HEAD requests with browser-like User-Agent; no credentials or cookies.",
        "probe_results": results,
        "interpretation": (
            "A 200/3xx response for an official author-kit URL means the kit may be downloadable in this environment. "
            "403/404/None means the template must still be obtained through another official access route before "
            "the paper package can be marked official AAAI-formatted."
        ),
    }
    return report


def write_probe_report(output_path: Path, urls: list[str], timeout: float) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report = build_probe_report(urls, output_path, timeout)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Probe official AAAI author-kit URLs for template availability.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--url", action="append", default=None, help="Override URLs to probe; can be repeated.")
    parser.add_argument("--timeout", type=float, default=15.0)
    args = parser.parse_args(argv)
    path = write_probe_report(args.output, args.url or DEFAULT_URLS, args.timeout)
    print(path)


if __name__ == "__main__":
    main()
