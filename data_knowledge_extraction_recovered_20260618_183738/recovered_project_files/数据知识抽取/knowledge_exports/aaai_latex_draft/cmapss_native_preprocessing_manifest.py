from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "knowledge_exports" / "aaai_exact_native_protocol_gate"
DEFAULT_RUN_ROOT = REPO_ROOT / "knowledge_exports" / "aaai_formal_public_runs"
DEFAULT_BASELINE_ROOT = REPO_ROOT / "knowledge_exports" / "cmapss_rul_deep_baselines_regime_w80"
DEFAULT_BASELINE_ROOTS = [
    DEFAULT_BASELINE_ROOT,
    REPO_ROOT / "knowledge_exports" / "cmapss_rul_deep_baselines_regime_w80_cap150",
    REPO_ROOT / "knowledge_exports" / "cmapss_rul_deep_baselines_regime_w160_cap150",
    REPO_ROOT / "knowledge_exports" / "cmapss_lstm_published_style_w80_cap125",
]
DEFAULT_ALIGNMENT_ARTIFACT = DEFAULT_OUTPUT_DIR / "cmapss_published_baseline_alignment.json"
VERSION = "cmapss-native-preprocessing-manifest-v1"
EXPECTED_SUBSETS = {"FD001", "FD002", "FD003", "FD004"}


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _read_json(path: Path) -> dict[str, Any]:
    with open(_fs_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    os.makedirs(_fs_path(path.parent), exist_ok=True)
    with open(_fs_path(path), "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def _write_text(path: Path, text: str) -> None:
    os.makedirs(_fs_path(path.parent), exist_ok=True)
    with open(_fs_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def _result_files(root: Path) -> list[Path]:
    if not os.path.isdir(_fs_path(root)):
        return []
    files: list[Path] = []
    for dirpath, _dirnames, filenames in os.walk(_fs_path(root)):
        current = Path(dirpath)
        for name in filenames:
            if name.endswith(".json") and "cmapss" in name and "_seed" in name:
                files.append(current / name)
    return sorted(files)


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _mean(values: Iterable[float | None]) -> float | None:
    vals = [float(v) for v in values if v is not None]
    return sum(vals) / len(vals) if vals else None


def _extract_cap(payload: dict[str, Any]) -> float | None:
    for key in ("rul_cap", "health_rul_cap"):
        if key in payload:
            return _safe_float(payload.get(key))
    for parent in ("diagnostics", "efficiency", "baseline_diagnostics"):
        value = payload.get(parent)
        if isinstance(value, dict):
            cap = _safe_float(value.get("health_rul_cap") or value.get("rul_cap"))
            if cap is not None:
                return cap
    return None


def _alignment_artifact_present(path: Path) -> bool:
    if not os.path.exists(_fs_path(path)):
        return False
    try:
        payload = _read_json(path)
    except (OSError, json.JSONDecodeError):
        return False
    gates = payload.get("gates") if isinstance(payload.get("gates"), dict) else {}
    return bool(gates.get("alignment_artifact_present")) and bool(payload.get("published_reference_registry"))


def _branch_name(path: Path, payload: dict[str, Any]) -> str:
    if payload.get("baseline"):
        return str(payload["baseline"])
    parent = path.parent.name
    if parent.startswith("cmapss_"):
        return parent
    return f"{payload.get('dataset', 'cmapss')}_{payload.get('target', 'rul')}_{parent}"


def _artifact_row(path: Path) -> dict[str, Any]:
    payload = _read_json(path)
    records = payload.get("rul_prediction_records") or []
    subsets = sorted({str(row.get("subset")) for row in records if row.get("subset") is not None})
    split_roles = sorted({str(row.get("split_role")) for row in records if row.get("split_role") is not None})
    subset_metrics = payload.get("rul_subset_metrics") or {}
    subset_metric_rows = subset_metrics.get("rows") if isinstance(subset_metrics, dict) else []
    metrics = payload.get("primary_test_metrics") or {}
    diag = payload.get("diagnostics") if isinstance(payload.get("diagnostics"), dict) else {}
    baseline_diag = payload.get("baseline_diagnostics") if isinstance(payload.get("baseline_diagnostics"), dict) else {}
    return {
        "branch": _branch_name(path, payload),
        "seed": int(payload.get("seed", -1)),
        "source": str(path),
        "protocol": payload.get("protocol"),
        "split_protocol": payload.get("split_protocol"),
        "rul_eval_protocol": payload.get("rul_eval_protocol"),
        "rul_cap": _extract_cap(payload),
        "window_size": int(payload.get("window_size", 0) or 0),
        "records": int(len(records)),
        "subsets": subsets,
        "split_roles": split_roles,
        "subset_metric_rows": int(len(subset_metric_rows or [])),
        "all_records_terminal_test": bool(records) and set(split_roles).issubset({"test"}),
        "fd001_fd004_present": EXPECTED_SUBSETS.issubset(set(subsets)),
        "train_only_regime_or_scaling_declared": bool(payload.get("regime_prototype"))
        or "regime" in str(diag).lower()
        or "regime" in str(baseline_diag).lower(),
        "primary_rul_metric": all(key in metrics for key in ("rul_rmse", "rul_mae", "rul_score")),
        "rul_rmse": _safe_float(metrics.get("rul_rmse")),
        "rul_mae": _safe_float(metrics.get("rul_mae")),
        "rul_score": _safe_float(metrics.get("rul_score")),
    }


def build_cmapss_native_preprocessing_manifest(
    run_root: Path = DEFAULT_RUN_ROOT,
    baseline_root: Path | Iterable[Path] = tuple(DEFAULT_BASELINE_ROOTS),
    alignment_artifact: Path = DEFAULT_ALIGNMENT_ARTIFACT,
) -> dict[str, Any]:
    if isinstance(baseline_root, (str, Path)):
        baseline_roots = [Path(baseline_root)]
    else:
        baseline_roots = [Path(root) for root in baseline_root]
    files = _result_files(Path(run_root))
    for root in baseline_roots:
        files.extend(_result_files(root))
    rows = [_artifact_row(path) for path in files]
    primary_rows = [row for row in rows if row["records"] > 0]
    gates = {
        "native_fd001_fd004_split_present": bool(primary_rows) and all(row["fd001_fd004_present"] for row in primary_rows),
        "terminal_test_unit_records_present": bool(primary_rows)
        and all(row["rul_eval_protocol"] == "terminal_test_unit" for row in primary_rows)
        and all(row["all_records_terminal_test"] for row in primary_rows),
        "rul_cap_declared": bool(primary_rows) and all(row["rul_cap"] is not None for row in primary_rows),
        "subset_rmse_score_present": bool(primary_rows) and all(row["subset_metric_rows"] >= 4 for row in primary_rows),
        "primary_task_is_continuous_rul": bool(primary_rows) and all(row["primary_rul_metric"] for row in primary_rows),
        "train_only_preprocessing_declared": bool(primary_rows) and all(row["train_only_regime_or_scaling_declared"] for row in primary_rows),
        "published_baseline_alignment_present": _alignment_artifact_present(Path(alignment_artifact)),
    }
    missing = [name for name, value in gates.items() if not value]
    status = "native_preprocessing_manifest_complete" if not missing else "native_preprocessing_manifest_partial"

    branch_configs: dict[str, set[tuple[float | None, int]]] = {}
    for row in primary_rows:
        branch_configs.setdefault(str(row["branch"]), set()).add((row["rul_cap"], int(row["window_size"])))

    branch_summary: list[dict[str, Any]] = []
    grouped_keys = sorted({(str(row["branch"]), row["rul_cap"], int(row["window_size"])) for row in primary_rows})
    for branch, cap_value, window_size in grouped_keys:
        branch_rows = [
            row
            for row in primary_rows
            if str(row["branch"]) == branch
            and row["rul_cap"] == cap_value
            and int(row["window_size"]) == int(window_size)
        ]
        display_branch = branch
        if len(branch_configs.get(branch, set())) > 1:
            cap_text = "none" if cap_value is None else f"{float(cap_value):g}"
            display_branch = f"{branch}_w{int(window_size)}_cap{cap_text}"
        branch_summary.append(
            {
                "branch": display_branch,
                "n_seeds": len({int(row["seed"]) for row in branch_rows}),
                "rul_cap_values": sorted({float(row["rul_cap"]) for row in branch_rows if row["rul_cap"] is not None}),
                "window_sizes": sorted({int(row["window_size"]) for row in branch_rows}),
                "subsets": sorted(set().union(*(set(row["subsets"]) for row in branch_rows))),
                "rmse_mean": _mean(row["rul_rmse"] for row in branch_rows),
                "score_mean": _mean(row["rul_score"] for row in branch_rows),
                "records_per_seed_min": min(int(row["records"]) for row in branch_rows),
            }
        )

    return {
        "version": VERSION,
        "status": status,
        "claim_boundary": (
            "This manifest verifies the current C-MAPSS native preprocessing evidence. It does not authorize "
            "literature-wide SOTA wording until published-compatible baselines are reproduced and matched budget is aligned."
        ),
        "expected_subsets": sorted(EXPECTED_SUBSETS),
        "gates": gates,
        "missing_gates": missing,
        "branch_summary": branch_summary,
        "rows": rows,
        "next_actions": [
            "Use the published-baseline alignment table to select exact baselines for reproduction.",
            "Archive the exact preprocessing configuration: selected sensors, scaler fit scope, RUL cap, regime prototype fit scope, and validation unit split.",
            "Use subset-specific FD001-FD004 RMSE and RUL score as the primary C-MAPSS table; pooled metrics remain secondary.",
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# C-MAPSS Native Preprocessing Manifest",
        "",
        f"- Version: {payload['version']}",
        f"- Status: `{payload['status']}`",
        f"- Claim boundary: {payload['claim_boundary']}",
        f"- Expected subsets: {', '.join(payload['expected_subsets'])}",
        "",
        "## Gate Status",
        "",
        "| Gate | Status |",
        "|---|---|",
    ]
    for name, value in payload["gates"].items():
        lines.append(f"| {name} | {'pass' if value else 'missing'} |")
    lines.extend(["", "## Branch Summary", "", "| Branch | Seeds | RUL cap | Windows | Subsets | RMSE | Score | Records/seed min |", "|---|---:|---|---|---|---:|---:|---:|"])
    for row in payload["branch_summary"]:
        lines.append(
            "| {branch} | {seeds} | {cap} | {windows} | {subsets} | {rmse:.4f} | {score:.2f} | {records} |".format(
                branch=row["branch"],
                seeds=row["n_seeds"],
                cap=", ".join(str(value) for value in row["rul_cap_values"]) or "-",
                windows=", ".join(str(value) for value in row["window_sizes"]) or "-",
                subsets=", ".join(row["subsets"]),
                rmse=float(row["rmse_mean"] or 0.0),
                score=float(row["score_mean"] or 0.0),
                records=int(row["records_per_seed_min"]),
            )
        )
    lines.extend(["", "## Next Actions", ""])
    lines.extend(f"- {item}" for item in payload["next_actions"])
    return "\n".join(lines).rstrip() + "\n"


def write_cmapss_native_preprocessing_manifest(output_dir: Path | str = DEFAULT_OUTPUT_DIR) -> list[Path]:
    output_dir = Path(output_dir)
    os.makedirs(_fs_path(output_dir), exist_ok=True)
    payload = build_cmapss_native_preprocessing_manifest()
    json_path = output_dir / "cmapss_native_preprocessing_manifest.json"
    md_path = output_dir / "cmapss_native_preprocessing_manifest.md"
    _write_json(json_path, payload)
    _write_text(md_path, render_markdown(payload))
    return [json_path, md_path]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Write C-MAPSS native preprocessing manifest from current RUL artifacts.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    for path in write_cmapss_native_preprocessing_manifest(args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
