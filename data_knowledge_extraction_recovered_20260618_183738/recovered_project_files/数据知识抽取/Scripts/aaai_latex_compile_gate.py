from __future__ import annotations

import argparse
import json
import os
import shutil
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


def _read(path: Path) -> str:
    if not os.path.exists(_fs_path(path)):
        return ""
    with open(_fs_path(path), encoding="utf-8", errors="replace") as handle:
        return handle.read()


def _exists_min(path: Path, min_size: int = 1) -> bool:
    try:
        return os.path.exists(_fs_path(path)) and os.stat(_fs_path(path)).st_size >= min_size
    except OSError:
        return False


def _latest_log_path(package_dir: Path) -> Path | None:
    candidates = list(package_dir.glob("pdflatex_pass*.log")) + [package_dir / "main.log"]
    existing = [path for path in candidates if os.path.exists(_fs_path(path))]
    if not existing:
        return None
    return max(existing, key=lambda path: os.stat(_fs_path(path)).st_mtime)


def _mtime(path: Path) -> float | None:
    try:
        return os.stat(_fs_path(path)).st_mtime
    except OSError:
        return None


def _latest_log_text(package_dir: Path) -> str:
    path = _latest_log_path(package_dir)
    return _read(path) if path else ""


def _ensure_user_miktex_on_path() -> None:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        return
    for candidate in [
        Path(local_app_data) / "Programs" / "MiKTeX" / "miktex" / "bin" / "x64",
        Path(local_app_data) / "Programs" / "MiKTeX" / "miktex" / "bin",
    ]:
        if not candidate.exists():
            continue
        text = str(candidate)
        path_parts = os.environ.get("PATH", "").split(os.pathsep)
        if text not in path_parts:
            os.environ["PATH"] = text + os.pathsep + os.environ.get("PATH", "")


def build_compile_gate(package_dir: Path | str = DEFAULT_PACKAGE_DIR) -> dict[str, Any]:
    package_dir = Path(package_dir)
    tex = _read(package_dir / "main.tex")
    _ensure_user_miktex_on_path()
    pdflatex = shutil.which("pdflatex")
    bibtex = shutil.which("bibtex")
    official_style_ready = (
        r"\usepackage[submission]{aaai2027}" in tex
        and (package_dir / "aaai2027.sty").exists()
        and (package_dir / "aaai2027.bst").exists()
    )
    latest_log_path = _latest_log_path(package_dir)
    latest_log = _read(latest_log_path) if latest_log_path else ""
    pdf_path = package_dir / "main.pdf"
    tex_mtime = _mtime(package_dir / "main.tex")
    pdf_mtime = _mtime(pdf_path)
    log_mtime = _mtime(latest_log_path) if latest_log_path else None
    compiled_pdf = _exists_min(pdf_path, 1000)
    artifacts_fresh = bool(
        compiled_pdf
        and tex_mtime is not None
        and pdf_mtime is not None
        and log_mtime is not None
        and pdf_mtime >= tex_mtime
        and log_mtime >= tex_mtime
    )
    latex_errors = latest_log.count("LaTeX Error")
    fatal_errors = latest_log.count("Fatal error")
    undefined_refs = latest_log.count("undefined") + latest_log.count("Undefined")
    overfull_hboxes = latest_log.count("Overfull \\hbox")
    underfull_boxes = latest_log.count("Underfull \\hbox") + latest_log.count("Underfull \\vbox")
    if not official_style_ready:
        status = "blocked_official_style_not_integrated"
    elif not pdflatex or not bibtex:
        status = "blocked_missing_latex_toolchain"
    elif artifacts_fresh and not latex_errors and not fatal_errors and not undefined_refs and not overfull_hboxes:
        status = "compiled_clean"
    elif artifacts_fresh and not latex_errors and not fatal_errors and not undefined_refs:
        status = "compiled_with_layout_warnings"
    else:
        status = "ready_to_compile"
    return {
        "status": status,
        "package_dir": package_dir.as_posix(),
        "official_style_ready": official_style_ready,
        "pdflatex": pdflatex,
        "bibtex": bibtex,
        "compiled_pdf": compiled_pdf,
        "artifacts_fresh": artifacts_fresh,
        "pdf_path": pdf_path.as_posix() if compiled_pdf else None,
        "latest_log_path": latest_log_path.as_posix() if latest_log_path else None,
        "tex_mtime": tex_mtime,
        "pdf_mtime": pdf_mtime,
        "log_mtime": log_mtime,
        "latex_errors": latex_errors,
        "fatal_errors": fatal_errors,
        "undefined_references_or_citations": undefined_refs,
        "overfull_hbox_count": overfull_hboxes,
        "underfull_box_count": underfull_boxes,
        "expected_commands": [
            "pdflatex -interaction=nonstopmode main.tex",
            "bibtex main",
            "pdflatex -interaction=nonstopmode main.tex",
            "pdflatex -interaction=nonstopmode main.tex",
        ],
        "required_actions": _required_actions(status),
    }


def _required_actions(status: str) -> list[str]:
    if status == "blocked_official_style_not_integrated":
        return ["Regenerate the LaTeX package after the official AAAI author kit is present."]
    if status == "blocked_missing_latex_toolchain":
        return ["Install a LaTeX distribution with pdflatex and bibtex, then run the expected commands from the package directory."]
    if status == "compiled_with_layout_warnings":
        return ["Reduce overfull hbox warnings, then recompile and inspect all floats."]
    if status == "compiled_clean":
        return ["Inspect all floats manually or with rendered page images before final submission polishing."]
    if status == "ready_to_compile":
        return ["Run the expected LaTeX/BibTeX command sequence, save the log, and inspect all floats."]
    return []


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# AAAI LaTeX Compile Gate",
        "",
        f"- Status: {report['status']}",
        f"- Official style ready: {report['official_style_ready']}",
        f"- pdflatex: `{report['pdflatex']}`",
        f"- bibtex: `{report['bibtex']}`",
        f"- Compiled PDF: {report['compiled_pdf']}",
        f"- Artifacts fresh: {report['artifacts_fresh']}",
        f"- Latest log: `{report['latest_log_path']}`",
        f"- LaTeX errors: {report['latex_errors']}",
        f"- Fatal errors: {report['fatal_errors']}",
        f"- Undefined references/citations: {report['undefined_references_or_citations']}",
        f"- Overfull hbox count: {report['overfull_hbox_count']}",
        f"- Underfull box count: {report['underfull_box_count']}",
        "",
        "## Expected Commands",
        "",
    ]
    lines.extend(f"- `{command}`" for command in report["expected_commands"])
    lines.extend(["", "## Required Actions", ""])
    if report["required_actions"]:
        lines.extend(f"- {action}" for action in report["required_actions"])
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def write_compile_gate(output_dir: Path | str) -> list[Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_compile_gate(output_dir)
    json_path = output_dir / "aaai_latex_compile_gate.json"
    md_path = output_dir / "aaai_latex_compile_gate.md"
    with open(_fs_path(json_path), "w", encoding="utf-8") as handle:
        handle.write(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    with open(_fs_path(md_path), "w", encoding="utf-8") as handle:
        handle.write(render_markdown(report))
    return [json_path, md_path]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Audit whether the AAAI LaTeX draft is ready to compile.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_PACKAGE_DIR)
    args = parser.parse_args(argv)
    for path in write_compile_gate(args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
