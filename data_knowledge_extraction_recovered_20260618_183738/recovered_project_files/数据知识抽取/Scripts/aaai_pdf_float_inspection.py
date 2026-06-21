from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE_DIR = REPO_ROOT / "knowledge_exports" / "aaai_latex_draft"


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _runtime_bin_candidates() -> list[Path]:
    home = Path.home()
    return [
        home
        / ".cache"
        / "codex-runtimes"
        / "codex-primary-runtime"
        / "dependencies"
        / "native"
        / "poppler"
        / "Library"
        / "bin",
        home / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "bin",
    ]


def _find_binary(name: str) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    exe_names = [name] if os.name != "nt" else [f"{name}.exe", f"{name}.cmd", f"{name}.bat"]
    for directory in _runtime_bin_candidates():
        for exe_name in exe_names:
            candidate = directory / exe_name
            if candidate.exists():
                return str(candidate)
    return None


def _png_dimensions(path: Path) -> tuple[int, int] | None:
    with open(_fs_path(path), "rb") as handle:
        header = handle.read(24)
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    width = int.from_bytes(header[16:20], "big")
    height = int.from_bytes(header[20:24], "big")
    return width, height


def build_pdf_float_inspection(
    package_dir: Path | str = DEFAULT_PACKAGE_DIR,
    *,
    mark_inspected: bool = False,
) -> dict[str, Any]:
    package_dir = Path(package_dir)
    pdf_path = package_dir / "main.pdf"
    render_dir = package_dir / "pdf_float_inspection"
    os.makedirs(_fs_path(render_dir), exist_ok=True)
    pdftoppm = _find_binary("pdftoppm")
    if not os.path.exists(_fs_path(pdf_path)):
        return {
            "status": "missing_pdf",
            "pdf_path": pdf_path.as_posix(),
            "render_dir": render_dir.as_posix(),
            "pdftoppm": pdftoppm,
            "pages": [],
            "issues": ["main.pdf is missing"],
        }
    if not pdftoppm:
        return {
            "status": "blocked_missing_pdftoppm",
            "pdf_path": pdf_path.as_posix(),
            "render_dir": render_dir.as_posix(),
            "pdftoppm": None,
            "pages": [],
            "issues": ["pdftoppm is unavailable"],
        }

    prefix = render_dir / "main_page"
    result = subprocess.run(
        [pdftoppm, "-png", _fs_path(pdf_path), _fs_path(prefix)],
        capture_output=True,
        text=True,
        check=False,
    )
    pages = sorted(render_dir.glob("main_page-*.png"))
    page_rows: list[dict[str, Any]] = []
    issues: list[str] = []
    for page in pages:
        dimensions = _png_dimensions(page)
        size = os.stat(_fs_path(page)).st_size if os.path.exists(_fs_path(page)) else 0
        if dimensions is None:
            issues.append(f"{page.name} is not a valid PNG")
            width = height = 0
        else:
            width, height = dimensions
        if size < 10_000:
            issues.append(f"{page.name} is unexpectedly small")
        page_rows.append(
            {
                "path": page.as_posix(),
                "bytes": int(size),
                "width": int(width),
                "height": int(height),
            }
        )
    if result.returncode != 0:
        issues.append(f"pdftoppm exited with {result.returncode}: {result.stderr.strip()}")
    if not pages:
        issues.append("no rendered pages were produced")

    if issues:
        status = "rendered_with_issues"
    elif mark_inspected:
        status = "inspected_clean"
    else:
        status = "rendered_pending_manual_inspection"
    return {
        "status": status,
        "pdf_path": pdf_path.as_posix(),
        "render_dir": render_dir.as_posix(),
        "pdftoppm": pdftoppm,
        "page_count": len(page_rows),
        "pages": page_rows,
        "issues": issues,
        "manual_inspection_note": (
            "Rendered pages were manually inspected for clipped text, overlapping floats, unreadable tables, and broken figures."
            if mark_inspected and not issues
            else "Manual visual inspection is still required before final submission."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# AAAI PDF Float Inspection",
        "",
        f"- Status: {report['status']}",
        f"- PDF: `{report['pdf_path']}`",
        f"- Render dir: `{report['render_dir']}`",
        f"- Page count: {report.get('page_count', 0)}",
        "",
        "## Issues",
        "",
    ]
    if report.get("issues"):
        lines.extend(f"- {issue}" for issue in report["issues"])
    else:
        lines.append("- none")
    lines.extend(["", "## Rendered Pages", "", "| Page | Size | Dimensions |", "|---|---:|---:|"])
    for index, page in enumerate(report.get("pages", []), start=1):
        lines.append(f"| `{page['path']}` | {page['bytes']} | {page['width']}x{page['height']} |")
    lines.extend(["", "## Manual Note", "", str(report.get("manual_inspection_note", "")), ""])
    return "\n".join(lines)


def write_pdf_float_inspection(
    package_dir: Path | str = DEFAULT_PACKAGE_DIR,
    *,
    mark_inspected: bool = False,
) -> list[Path]:
    package_dir = Path(package_dir)
    report = build_pdf_float_inspection(package_dir, mark_inspected=mark_inspected)
    json_path = package_dir / "aaai_pdf_float_inspection.json"
    md_path = package_dir / "aaai_pdf_float_inspection.md"
    with open(_fs_path(json_path), "w", encoding="utf-8") as handle:
        handle.write(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    with open(_fs_path(md_path), "w", encoding="utf-8") as handle:
        handle.write(render_markdown(report))
    return [json_path, md_path]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Render and inspect the AAAI PDF floats.")
    parser.add_argument("--package-dir", type=Path, default=DEFAULT_PACKAGE_DIR)
    parser.add_argument("--mark-inspected", action="store_true")
    args = parser.parse_args(argv)
    for path in write_pdf_float_inspection(args.package_dir, mark_inspected=args.mark_inspected):
        print(path)


if __name__ == "__main__":
    main()
