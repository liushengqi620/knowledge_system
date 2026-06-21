from __future__ import annotations

import argparse
import json
import os
import ssl
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_URL = "https://aaai.org/authorkit27/"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "knowledge_exports" / "official_aaai_template"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    "Accept": "application/zip,*/*;q=0.8",
}


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _safe_extract(zip_path: Path, extract_dir: Path) -> list[Path]:
    extracted: list[Path] = []
    root = extract_dir.resolve()
    with zipfile.ZipFile(_fs_path(zip_path)) as archive:
        for member in archive.infolist():
            target = (extract_dir / member.filename).resolve()
            if root not in target.parents and target != root:
                raise ValueError(f"Unsafe zip member path: {member.filename}")
            if member.is_dir():
                os.makedirs(_fs_path(target), exist_ok=True)
                continue
            os.makedirs(_fs_path(target.parent), exist_ok=True)
            with archive.open(member) as source, open(_fs_path(target), "wb") as destination:
                destination.write(source.read())
            extracted.append(extract_dir / member.filename)
    return extracted


def download_author_kit(url: str, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / "aaai27_author_kit.zip"
    request = urllib.request.Request(url, headers=HEADERS, method="GET")
    with urllib.request.urlopen(request, timeout=60, context=ssl.create_default_context()) as response:
        content_type = response.headers.get("Content-Type", "")
        payload = response.read()
    zip_path.write_bytes(payload)
    if not zipfile.is_zipfile(_fs_path(zip_path)):
        raise ValueError(f"Downloaded payload is not a zip file: {zip_path} ({content_type})")
    extracted = _safe_extract(zip_path, output_dir)
    report = {
        "status": "downloaded_and_extracted",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_url": url,
        "content_type": content_type,
        "zip_path": zip_path.as_posix(),
        "output_dir": output_dir.as_posix(),
        "extracted_files": sorted(path.as_posix() for path in extracted),
    }
    report_path = output_dir / "aaai27_author_kit_download_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Download and extract the official AAAI author kit.")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    report = download_author_kit(args.url, args.output_dir)
    print(report["zip_path"])
    for path in report["extracted_files"]:
        print(path)


if __name__ == "__main__":
    main()
