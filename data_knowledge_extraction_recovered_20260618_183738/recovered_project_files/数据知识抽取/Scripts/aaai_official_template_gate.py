from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = REPO_ROOT / "knowledge_exports"

DEFAULT_TEMPLATE_DIRS = [
    REPO_ROOT / "templates" / "aaai",
    REPO_ROOT / "aaai_template",
    EXPORT_DIR / "official_aaai_template",
    EXPORT_DIR / "aaai_template",
]

DEFAULT_SOURCE_PROBE = EXPORT_DIR / "aaai_author_kit_source_probe.json"

OFFICIAL_SOURCE_URLS = {
    "aaai27_conference_page": "https://aaai.org/conference/aaai/aaai-27/",
    "aaai27_author_kit": "https://aaai.org/authorkit27/",
    "aaai26_author_kit": "https://aaai.org/authorkit26/",
}


def _as_posix(paths: Iterable[Path]) -> list[str]:
    return [path.as_posix() for path in sorted(paths, key=lambda item: item.as_posix().lower())]


def _collect_files(roots: Iterable[Path], patterns: Iterable[str]) -> list[Path]:
    files: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        for pattern in patterns:
            files.update(path for path in root.rglob(pattern) if path.is_file())
    return sorted(files, key=lambda item: item.as_posix().lower())


def _load_source_probe(path: Path | None = DEFAULT_SOURCE_PROBE) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "status": "invalid_probe_json",
            "path": path.as_posix(),
            "error": str(exc),
        }
    if not isinstance(payload, dict):
        return {
            "status": "invalid_probe_json",
            "path": path.as_posix(),
            "error": "top-level JSON payload is not an object",
        }
    return payload


def _official_source_blocked(source_probe: dict[str, Any]) -> bool:
    rows = source_probe.get("probe_results", [])
    if not isinstance(rows, list):
        return False
    current_author_kit_ok = any(
        isinstance(row, dict)
        and "authorkit27" in str(row.get("url", "")).lower()
        and row.get("status_code") in {200, 301, 302, 303, 307, 308}
        for row in rows
    )
    if current_author_kit_ok:
        return False
    author_kit_rows = [
        row
        for row in rows
        if isinstance(row, dict)
        and "authorkit" in str(row.get("url", "")).lower()
        and row.get("status_code") not in {200, 301, 302, 303, 307, 308}
    ]
    return bool(author_kit_rows)


def discover_template_assets(
    template_dirs: Iterable[Path] | None = None,
    source_probe_path: Path | None = DEFAULT_SOURCE_PROBE,
) -> dict[str, Any]:
    roots = [Path(path) for path in (template_dirs or DEFAULT_TEMPLATE_DIRS)]
    existing_roots = [root for root in roots if root.exists()]
    style_files = _collect_files(existing_roots, ["aaai*.sty", "aaai*.cls"])
    bibliography_files = _collect_files(existing_roots, ["aaai*.bst", "*.bst"])
    sample_files = _collect_files(
        existing_roots,
        ["*sample*.tex", "*author*.tex", "*aaai*.tex", "*Submission*.tex", "*CameraReady*.tex"],
    )
    source_probe = _load_source_probe(source_probe_path)
    source_blocked = _official_source_blocked(source_probe)

    if style_files:
        status = "ready_for_official_migration"
    elif source_blocked:
        status = "blocked_official_source_inaccessible"
    else:
        status = "blocked_missing_official_template"
    required_actions = []
    if not style_files:
        required_actions.extend(
            [
                "Place the official AAAI author-kit files in one of the scanned template directories.",
                "Re-run this gate so the package can verify the official style/class file before migration.",
            ]
        )
    if not style_files and source_blocked:
        required_actions.append(
            "The recorded official author-kit probe did not return a downloadable kit in this environment; "
            "retry from a browser or network that can access aaai.org, then place the official files locally."
        )
    if style_files and not bibliography_files:
        required_actions.append("Confirm whether the selected AAAI year requires a specific bibliography style file.")
    if style_files and not sample_files:
        required_actions.append("Add the official sample TeX file or manually verify the required preamble constraints.")

    return {
        "status": status,
        "official_template_detected_locally": bool(style_files),
        "scanned_template_dirs": _as_posix(roots),
        "existing_template_dirs": _as_posix(existing_roots),
        "style_or_class_files": _as_posix(style_files),
        "bibliography_style_files": _as_posix(bibliography_files),
        "sample_tex_files": _as_posix(sample_files),
        "official_source_urls": OFFICIAL_SOURCE_URLS,
        "official_source_probe": source_probe,
        "official_source_blocked": source_blocked,
        "required_actions": required_actions,
        "blocking_rule": (
            "Do not describe the generated paper package as official AAAI-formatted until "
            "an official style/class file is detected, the migrated source compiles, and "
            "all floats are inspected under the selected year's template."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Official AAAI Template Gate",
        "",
        f"- Status: {report['status']}",
        f"- Official template detected locally: {report['official_template_detected_locally']}",
        f"- Blocking rule: {report['blocking_rule']}",
        "",
        "## Scanned Directories",
        "",
    ]
    for directory in report["scanned_template_dirs"]:
        marker = "present" if directory in report["existing_template_dirs"] else "missing"
        lines.append(f"- `{directory}` ({marker})")

    lines.extend(["", "## Detected Assets", ""])
    for title, key in [
        ("Style or class files", "style_or_class_files"),
        ("Bibliography style files", "bibliography_style_files"),
        ("Sample TeX files", "sample_tex_files"),
    ]:
        lines.append(f"### {title}")
        if report[key]:
            lines.extend(f"- `{path}`" for path in report[key])
        else:
            lines.append("- none")
        lines.append("")

    lines.extend(["## Official Source Evidence", ""])
    for name, url in report["official_source_urls"].items():
        lines.append(f"- {name}: {url}")
    lines.append(f"- Official source blocked in recorded probe: {report['official_source_blocked']}")
    probe = report.get("official_source_probe") or {}
    if probe:
        probe_path = probe.get("path") or probe.get("output_path")
        if probe_path:
            lines.append(f"- Probe file: `{probe_path}`")
        rows = probe.get("probe_results", [])
        if isinstance(rows, list) and rows:
            lines.append("")
            lines.append("| URL | Status | Content-Type | Location |")
            lines.append("|---|---:|---|---|")
            for row in rows:
                if not isinstance(row, dict):
                    continue
                lines.append(
                    "| "
                    + str(row.get("url", ""))
                    + " | "
                    + str(row.get("status_code", ""))
                    + " | "
                    + str(row.get("content_type", ""))
                    + " | "
                    + str(row.get("location", ""))
                    + " |"
                )
        elif probe.get("status") == "invalid_probe_json":
            lines.append(f"- Probe read error: {probe.get('error')}")
    else:
        lines.append("- No local source probe JSON was found.")
    lines.append("")

    lines.extend(["## Required Actions", ""])
    if report["required_actions"]:
        lines.extend(f"- {action}" for action in report["required_actions"])
    else:
        lines.append("- Template assets are present; run the official migration compile and inspect all floats.")
    lines.append("")
    return "\n".join(lines)


def build_official_template_gate(
    output_dir: Path,
    template_dirs: Iterable[Path] | None = None,
    source_probe_path: Path | None = DEFAULT_SOURCE_PROBE,
) -> list[Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report = discover_template_assets(template_dirs, source_probe_path)

    json_path = output_dir / "aaai_official_template_gate.json"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    markdown_path = output_dir / "aaai_official_template_gate.md"
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    return [json_path, markdown_path]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Audit whether official AAAI template assets are available locally.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--template-dir", type=Path, action="append", default=None)
    parser.add_argument("--source-probe", type=Path, default=DEFAULT_SOURCE_PROBE)
    args = parser.parse_args(argv)
    for path in build_official_template_gate(args.output_dir, args.template_dir, args.source_probe):
        print(path)


if __name__ == "__main__":
    main()
