from __future__ import annotations

import argparse
import json
import os
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable

from aaai_external_baseline_alignment_decision import PRIMARY_SOURCE_SNAPSHOT


VERSION = "official-external-repo-snapshot-v1"
CHECKED_ON = "2026-06-21"
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "knowledge_exports" / "external_baseline_official_repos"


JsonFetcher = Callable[[str, int], Any]
LsRemoteRunner = Callable[[str, int], str]


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _github_owner_repo(repo_url: str) -> tuple[str, str] | None:
    parsed = urllib.parse.urlparse(repo_url)
    if parsed.netloc.lower() != "github.com":
        return None
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        return None
    owner = parts[0]
    repo = parts[1]
    if repo.endswith(".git"):
        repo = repo[:-4]
    return owner, repo


def _github_api_url(repo_url: str) -> str | None:
    owner_repo = _github_owner_repo(repo_url)
    if owner_repo is None:
        return None
    owner, repo = owner_repo
    return f"https://api.github.com/repos/{owner}/{repo}"


def _fetch_json(url: str, timeout: int) -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "codex-aaai-external-baseline-snapshot",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _git_ls_remote(repo_url: str, timeout: int) -> str:
    result = subprocess.run(
        ["git", "ls-remote", "--symref", repo_url, "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result.stdout


def _parse_ls_remote(output: str) -> dict[str, str]:
    default_branch = ""
    head_commit = ""
    for line in output.splitlines():
        if line.startswith("ref:") and "\tHEAD" in line:
            ref = line.split()[1]
            if ref.startswith("refs/heads/"):
                default_branch = ref.removeprefix("refs/heads/")
        elif line.endswith("\tHEAD"):
            head_commit = line.split("\t", 1)[0].strip()
    return {
        "default_branch": default_branch,
        "head_commit": head_commit,
    }


def _root_file_flags(contents: Any) -> dict[str, Any]:
    names: list[str] = []
    if isinstance(contents, list):
        for item in contents:
            if isinstance(item, dict) and isinstance(item.get("name"), str):
                names.append(item["name"])
    lowered = [name.lower() for name in names]
    readme_files = [name for name in names if name.lower().startswith("readme")]
    license_files = [
        name
        for name in names
        if name.lower().startswith("license") or name.lower().startswith("copying")
    ]
    return {
        "root_file_count": len(names),
        "has_readme": bool(readme_files) or "readme.md" in lowered,
        "has_license_file": bool(license_files),
        "readme_files": readme_files,
        "license_files": license_files,
    }


def _snapshot_one_repo(
    name: str,
    source: dict[str, str],
    *,
    allow_network: bool,
    timeout: int,
    json_fetcher: JsonFetcher = _fetch_json,
    ls_remote_runner: LsRemoteRunner = _git_ls_remote,
) -> dict[str, Any]:
    repo_url = source["repo_url"]
    git_status: dict[str, Any] = {
        "git_accessible": False,
        "default_branch": "",
        "head_commit": "",
        "error": "",
    }
    api_status: dict[str, Any] = {
        "github_api_accessible": False,
        "api_url": _github_api_url(repo_url) or "",
        "default_branch": "",
        "license_key": "",
        "description": "",
        "pushed_at": "",
        "updated_at": "",
        "error": "",
    }
    root_files: dict[str, Any] = {
        "root_file_count": 0,
        "has_readme": False,
        "has_license_file": False,
        "readme_files": [],
        "license_files": [],
    }

    if allow_network:
        try:
            git_status.update(_parse_ls_remote(ls_remote_runner(repo_url, timeout)))
            git_status["git_accessible"] = bool(git_status["head_commit"])
        except (subprocess.SubprocessError, OSError, TimeoutError) as exc:
            git_status["error"] = f"{type(exc).__name__}: {exc}"

        api_url = api_status["api_url"]
        if api_url:
            try:
                metadata = json_fetcher(api_url, timeout)
                if isinstance(metadata, dict):
                    api_status.update(
                        {
                            "github_api_accessible": True,
                            "default_branch": str(metadata.get("default_branch") or ""),
                            "license_key": str((metadata.get("license") or {}).get("key") or ""),
                            "description": str(metadata.get("description") or ""),
                            "pushed_at": str(metadata.get("pushed_at") or ""),
                            "updated_at": str(metadata.get("updated_at") or ""),
                        }
                    )
                    branch = api_status["default_branch"] or git_status["default_branch"]
                    if branch:
                        contents_url = f"{api_url}/contents?ref={urllib.parse.quote(branch)}"
                        root_files = _root_file_flags(json_fetcher(contents_url, timeout))
            except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
                api_status["error"] = f"{type(exc).__name__}: {exc}"

    resolved_branch = git_status["default_branch"] or api_status["default_branch"]
    snapshot_status = (
        "repo_head_resolved"
        if git_status["git_accessible"] and git_status["head_commit"]
        else "source_only_unresolved"
    )
    return {
        "name": name,
        "paper_url": source["paper_url"],
        "repo_url": repo_url,
        "venue": source["venue"],
        "official_task": source["official_task"],
        "snapshot_status": snapshot_status,
        "resolved_default_branch": resolved_branch,
        "resolved_head_commit": git_status["head_commit"],
        "git": git_status,
        "github_api": api_status,
        "root_files": root_files,
        "official_external_score": False,
        "protocol_reproduction_status": "not_started_from_snapshot",
        "claim_boundary": "This snapshot records code provenance only; it is not an official external score or protocol reproduction.",
    }


def build_official_repo_snapshot_payload(
    *,
    sources: dict[str, dict[str, str]] | None = None,
    allow_network: bool = True,
    timeout: int = 30,
    json_fetcher: JsonFetcher = _fetch_json,
    ls_remote_runner: LsRemoteRunner = _git_ls_remote,
) -> dict[str, Any]:
    sources = sources or PRIMARY_SOURCE_SNAPSHOT
    rows = [
        _snapshot_one_repo(
            name,
            source,
            allow_network=allow_network,
            timeout=timeout,
            json_fetcher=json_fetcher,
            ls_remote_runner=ls_remote_runner,
        )
        for name, source in sources.items()
    ]
    all_resolved = all(row["snapshot_status"] == "repo_head_resolved" for row in rows)
    return {
        "version": VERSION,
        "checked_on": CHECKED_ON,
        "allow_network": allow_network,
        "overall_status": "official_repo_heads_resolved" if all_resolved else "official_repo_snapshot_partial",
        "claim_gate": "Repository snapshots are provenance evidence only and remain blocked for public-score claims until exact external protocol reproduction is implemented.",
        "rows": rows,
    }


def render_official_repo_snapshot_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Official External Repository Snapshot",
        "",
        f"- Version: {payload['version']}",
        f"- Checked on: {payload['checked_on']}",
        f"- Overall status: {payload['overall_status']}",
        f"- Claim gate: {payload['claim_gate']}",
        "",
        "| Method | Venue | Repository | Branch | HEAD commit | Snapshot status | Protocol status | README | License |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for row in payload["rows"]:
        root_files = row["root_files"]
        commit = row["resolved_head_commit"][:12] if row["resolved_head_commit"] else ""
        lines.append(
            "| {name} | {venue} | {repo} | {branch} | {commit} | {status} | {protocol} | {readme} | {license} |".format(
                name=row["name"],
                venue=row["venue"],
                repo=row["repo_url"],
                branch=row["resolved_default_branch"],
                commit=commit,
                status=row["snapshot_status"],
                protocol=row["protocol_reproduction_status"],
                readme="yes" if root_files["has_readme"] else "no",
                license="yes" if root_files["has_license_file"] or row["github_api"]["license_key"] else "no",
            )
        )
    lines.extend(["", "## Claim Boundary", "", payload["claim_gate"], ""])
    return "\n".join(lines)


def build_official_repo_snapshot(
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    *,
    allow_network: bool = True,
    timeout: int = 30,
) -> list[Path]:
    output_dir = Path(output_dir)
    os.makedirs(_fs_path(output_dir), exist_ok=True)
    payload = build_official_repo_snapshot_payload(allow_network=allow_network, timeout=timeout)
    json_path = output_dir / "official_external_repo_snapshot.json"
    md_path = output_dir / "official_external_repo_snapshot.md"
    with open(_fs_path(json_path), "w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    with open(_fs_path(md_path), "w", encoding="utf-8") as handle:
        handle.write(render_official_repo_snapshot_markdown(payload))
    return [json_path, md_path]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Snapshot official external baseline repositories.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Write a source-only artifact without network or git remote access.",
    )
    args = parser.parse_args(argv)
    for path in build_official_repo_snapshot(
        args.output_dir,
        allow_network=not args.offline,
        timeout=args.timeout,
    ):
        print(path)


if __name__ == "__main__":
    main()
