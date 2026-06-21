from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any


VERSION = "official-external-repo-checkout-audit-v1"
CHECKED_ON = "2026-06-21"
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_SNAPSHOT = (
    REPO_ROOT
    / "knowledge_exports"
    / "external_baseline_official_repos"
    / "official_external_repo_snapshot.json"
)
DEFAULT_OUTPUT_DIR = REPO_ROOT / "knowledge_exports" / "external_baseline_official_repos"
DEFAULT_CHECKOUT_ROOT = Path.home() / "aaai_external_baseline_checkouts"


ENTRYPOINT_PATTERNS = [
    re.compile(r"(^|/)(main|run|train|test|evaluate|exp)[^/]*\.py$", re.IGNORECASE),
    re.compile(r"(^|/)scripts?/[^/]+\.py$", re.IGNORECASE),
]
DEPENDENCY_PATTERNS = [
    re.compile(r"(^|/)requirements.*\.txt$", re.IGNORECASE),
    re.compile(r"(^|/)environment.*\.ya?ml$", re.IGNORECASE),
    re.compile(r"(^|/)setup\.py$", re.IGNORECASE),
    re.compile(r"(^|/)pyproject\.toml$", re.IGNORECASE),
]
DATA_INTERFACE_PATTERNS = [
    re.compile(r"data", re.IGNORECASE),
    re.compile(r"loader", re.IGNORECASE),
    re.compile(r"dataset", re.IGNORECASE),
]


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _run_git(args: list[str], *, cwd: Path | None = None, timeout: int = 120) -> tuple[int, str, str]:
    result = subprocess.run(
        ["git", *args],
        cwd=_fs_path(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def _load_snapshot(path: Path) -> dict[str, Any]:
    with open(_fs_path(path), encoding="utf-8") as handle:
        return json.load(handle)


def _relative_files(root: Path, *, max_files: int = 2000) -> list[str]:
    files: list[str] = []
    if not root.exists():
        return files
    for path in root.rglob("*"):
        if ".git" in path.parts:
            continue
        if path.is_file():
            files.append(path.relative_to(root).as_posix())
            if len(files) >= max_files:
                break
    return sorted(files)


def _select_matches(files: list[str], patterns: list[re.Pattern[str]], *, limit: int = 20) -> list[str]:
    matches: list[str] = []
    for file in files:
        normalized = file.replace("\\", "/")
        if any(pattern.search(normalized) for pattern in patterns):
            matches.append(file)
            if len(matches) >= limit:
                break
    return matches


def _model_files(files: list[str], *, limit: int = 30) -> list[str]:
    matches = [
        file
        for file in files
        if file.lower().endswith(".py")
        and any(token in file.lower() for token in ["model", "network", "layer", "attention", "graph", "patch"])
    ]
    return matches[:limit]


def _data_interface_files(files: list[str], *, limit: int = 30) -> list[str]:
    matches = [
        file
        for file in files
        if file.lower().endswith((".py", ".sh", ".md", ".txt", ".yaml", ".yml"))
        and any(pattern.search(file) for pattern in DATA_INTERFACE_PATTERNS)
    ]
    return matches[:limit]


def _read_first_lines(path: Path, *, max_lines: int = 80) -> list[str]:
    try:
        with open(_fs_path(path), encoding="utf-8", errors="replace") as handle:
            lines = []
            for _ in range(max_lines):
                line = handle.readline()
                if not line:
                    break
                lines.append(line.rstrip())
            return lines
    except OSError:
        return []


def _dependency_preview(root: Path, dependency_files: list[str]) -> dict[str, list[str]]:
    preview: dict[str, list[str]] = {}
    for relative in dependency_files[:5]:
        preview[relative] = _read_first_lines(root / relative, max_lines=40)
    return preview


def _protocol_wrapper_status(name: str) -> str:
    normalized = str(name).strip().lower()
    if normalized == "patchtst" and (REPO_ROOT / "Scripts" / "run_patchtst_tep_official_wrapper.py").exists():
        return "official_source_adapted_backbone_wrapper_available_not_official_score"
    if normalized == "anomaly transformer" and (REPO_ROOT / "Scripts" / "run_anomaly_transformer_skab_official_wrapper.py").exists():
        return "patched_skab_official_source_wrapper_available_not_official_score"
    if normalized == "graph wavenet" and (REPO_ROOT / "Scripts" / "run_graph_wavenet_tep_official_wrapper.py").exists():
        return "official_source_adapted_graph_temporal_wrapper_available_not_official_score"
    return "not_implemented"


def _checkout_one(
    row: dict[str, Any],
    *,
    checkout_root: Path,
    timeout: int,
    skip_clone: bool,
) -> dict[str, Any]:
    name = row["name"]
    repo_url = row["repo_url"]
    branch = row.get("resolved_default_branch", "")
    expected_commit = row.get("resolved_head_commit", "")
    checkout_dir = checkout_root / _slug(name)
    status = "not_checked_out"
    error = ""
    clone_command = ""

    if not checkout_dir.exists() and not skip_clone:
        os.makedirs(_fs_path(checkout_root), exist_ok=True)
        clone_command = f"git clone --depth 1 --branch {branch} {repo_url} {checkout_dir}"
        code, _stdout, stderr = _run_git(
            ["clone", "--depth", "1", "--branch", branch, repo_url, str(checkout_dir.resolve())],
            timeout=timeout,
        )
        if code != 0:
            error = stderr
    elif not checkout_dir.exists() and skip_clone:
        error = "checkout missing and --skip-clone was requested"

    git_dir = checkout_dir / ".git"
    actual_commit = ""
    if checkout_dir.exists() and git_dir.exists():
        code, stdout, stderr = _run_git(["rev-parse", "HEAD"], cwd=checkout_dir, timeout=timeout)
        if code == 0:
            actual_commit = stdout
            status = "checkout_verified" if actual_commit == expected_commit else "checkout_commit_mismatch"
        else:
            status = "checkout_unreadable"
            error = stderr
    elif checkout_dir.exists():
        status = "path_exists_without_git"

    files = _relative_files(checkout_dir)
    dependency_files = _select_matches(files, DEPENDENCY_PATTERNS)
    entrypoints = _select_matches(files, ENTRYPOINT_PATTERNS)
    data_files = _data_interface_files(files)
    model_files = _model_files(files)
    return {
        "name": name,
        "repo_url": repo_url,
        "expected_branch": branch,
        "expected_commit": expected_commit,
        "checkout_dir": str(checkout_dir),
        "checkout_status": status,
        "actual_commit": actual_commit,
        "commit_matches_snapshot": bool(expected_commit and actual_commit == expected_commit),
        "clone_command": clone_command,
        "error": error,
        "file_count_audited": len(files),
        "dependency_files": dependency_files,
        "dependency_preview": _dependency_preview(checkout_dir, dependency_files),
        "entrypoint_candidates": entrypoints,
        "data_interface_candidates": data_files,
        "model_file_candidates": model_files,
        "official_external_score": False,
        "protocol_wrapper_status": _protocol_wrapper_status(str(name)),
        "remaining_protocol_gaps": [
            "map official data loader to project train/validation/test split",
            "freeze preprocessing and normalization equivalence",
            "expose validation-only threshold and seed-level prediction artifacts",
            "match official training budget or declare a local matched-budget adapter",
        ],
    }


def build_checkout_audit_payload(
    *,
    source_snapshot: Path = DEFAULT_SOURCE_SNAPSHOT,
    checkout_root: Path = DEFAULT_CHECKOUT_ROOT,
    timeout: int = 120,
    skip_clone: bool = False,
) -> dict[str, Any]:
    snapshot = _load_snapshot(source_snapshot)
    rows = [
        _checkout_one(
            row,
            checkout_root=checkout_root,
            timeout=timeout,
            skip_clone=skip_clone,
        )
        for row in snapshot.get("rows", [])
    ]
    all_verified = all(row["checkout_status"] == "checkout_verified" for row in rows)
    any_checked_out = any(row["checkout_status"] == "checkout_verified" for row in rows)
    if all_verified:
        overall_status = "official_repo_checkouts_verified"
    elif any_checked_out:
        overall_status = "official_repo_checkouts_partial"
    else:
        overall_status = "official_repo_checkouts_missing"
    return {
        "version": VERSION,
        "checked_on": CHECKED_ON,
        "source_snapshot": str(source_snapshot),
        "checkout_root": str(checkout_root),
        "overall_status": overall_status,
        "claim_gate": "Verified checkouts prove source-code provenance only. They are not official external scores until dataset adapters, thresholds, metrics, seeds, and budgets are reproduced.",
        "rows": rows,
    }


def render_checkout_audit_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Official External Repository Checkout Audit",
        "",
        f"- Version: {payload['version']}",
        f"- Checked on: {payload['checked_on']}",
        f"- Overall status: {payload['overall_status']}",
        f"- Claim gate: {payload['claim_gate']}",
        "",
        "| Method | Status | Branch | Expected commit | Actual commit | Entrypoints | Dependencies | Data interfaces | Protocol wrapper |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for row in payload["rows"]:
        lines.append(
            "| {name} | {status} | {branch} | {expected} | {actual} | {entrypoints} | {deps} | {data} | {wrapper} |".format(
                name=row["name"],
                status=row["checkout_status"],
                branch=row["expected_branch"],
                expected=row["expected_commit"][:12],
                actual=row["actual_commit"][:12],
                entrypoints=", ".join(row["entrypoint_candidates"][:4]),
                deps=", ".join(row["dependency_files"][:4]),
                data=", ".join(row["data_interface_candidates"][:4]),
                wrapper=row["protocol_wrapper_status"],
            )
        )
    lines.extend(["", "## Per-Method Notes", ""])
    for row in payload["rows"]:
        lines.extend(
            [
                f"### {row['name']}",
                "",
                f"- Checkout directory: `{row['checkout_dir']}`",
                f"- Commit matches snapshot: {row['commit_matches_snapshot']}",
                f"- Official external score: {row['official_external_score']}",
                "- Remaining protocol gaps:",
            ]
        )
        lines.extend(f"  - {gap}" for gap in row["remaining_protocol_gaps"])
        if row["model_file_candidates"]:
            lines.append("- Model file candidates:")
            lines.extend(f"  - `{path}`" for path in row["model_file_candidates"][:8])
        lines.append("")
    return "\n".join(lines)


def build_checkout_audit(
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    *,
    source_snapshot: Path = DEFAULT_SOURCE_SNAPSHOT,
    checkout_root: Path = DEFAULT_CHECKOUT_ROOT,
    timeout: int = 120,
    skip_clone: bool = False,
) -> list[Path]:
    output_dir = Path(output_dir)
    os.makedirs(_fs_path(output_dir), exist_ok=True)
    payload = build_checkout_audit_payload(
        source_snapshot=source_snapshot,
        checkout_root=checkout_root,
        timeout=timeout,
        skip_clone=skip_clone,
    )
    json_path = output_dir / "official_external_repo_checkout_audit.json"
    md_path = output_dir / "official_external_repo_checkout_audit.md"
    with open(_fs_path(json_path), "w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    with open(_fs_path(md_path), "w", encoding="utf-8") as handle:
        handle.write(render_checkout_audit_markdown(payload))
    return [json_path, md_path]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Clone/check official external baseline repositories and audit their interfaces.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--source-snapshot", type=Path, default=DEFAULT_SOURCE_SNAPSHOT)
    parser.add_argument("--checkout-root", type=Path, default=DEFAULT_CHECKOUT_ROOT)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--skip-clone", action="store_true")
    args = parser.parse_args(argv)
    for path in build_checkout_audit(
        args.output_dir,
        source_snapshot=args.source_snapshot,
        checkout_root=args.checkout_root,
        timeout=args.timeout,
        skip_clone=args.skip_clone,
    ):
        print(path)


if __name__ == "__main__":
    main()
