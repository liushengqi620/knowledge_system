from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = PROJECT_ROOT / "knowledge_exports"
DEFAULT_OUTPUT_DIR = EXPORT_DIR / "aaai_missing_ablation_runs" / "skab_cf_subset_smoke_summary"
BRANCH_DIRS = {
    "cf_standard": EXPORT_DIR / "aaai_missing_ablation_runs" / "skab_cf_guarded_subset_smoke",
    "no_cf": EXPORT_DIR / "aaai_missing_ablation_runs" / "skab_no_counterfactual_guard_subset_smoke",
    "cf_consistency": EXPORT_DIR / "aaai_missing_ablation_runs" / "skab_cf_guarded_subset_consistency_smoke",
}
FORMAL_OUTPUT_DIR = EXPORT_DIR / "aaai_missing_ablation_runs" / "skab_cf_subset_formal_summary"
FORMAL_BRANCH_DIRS = {
    "cf_standard": EXPORT_DIR / "aaai_missing_ablation_runs" / "skab_cf_guarded_subset_formal",
    "no_cf": EXPORT_DIR / "aaai_missing_ablation_runs" / "skab_no_counterfactual_guard",
}


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _exists(path: Path | str) -> bool:
    return os.path.exists(_fs_path(path))


def _read_json(path: Path | str) -> dict[str, Any] | None:
    if not _exists(path):
        return None
    with open(_fs_path(path), encoding="utf-8") as handle:
        return json.load(handle)


def _write_text(path: Path | str, text: str) -> None:
    with open(_fs_path(path), "w", encoding="utf-8") as handle:
        handle.write(text)


def _mean_std(values: list[float]) -> dict[str, float]:
    return {
        "mean": float(mean(values)) if values else 0.0,
        "std": float(pstdev(values)) if len(values) > 1 else 0.0,
    }


def _edge_labels(data: Mapping[str, Any]) -> list[str]:
    return [
        "{source}->{target}@{lag}".format(source=edge.get("source"), target=edge.get("target"), lag=edge.get("lag"))
        for edge in data.get("dynamic_edges", [])
    ]


def build_summary(
    seeds: list[int] | None = None,
    branch_dirs: Mapping[str, Path] = BRANCH_DIRS,
    *,
    summary_kind: str = "smoke",
) -> dict[str, Any]:
    seeds = seeds or [42, 43, 44]
    rows: list[dict[str, Any]] = []
    for seed in seeds:
        for branch, directory in branch_dirs.items():
            data = _read_json(Path(directory) / f"seed{int(seed)}.json")
            if data is None:
                rows.append({"seed": int(seed), "branch": branch, "status": "missing"})
                continue
            policy = data.get("edge_policy", {}) or {}
            rows.append(
                {
                    "seed": int(seed),
                    "branch": branch,
                    "status": str(data.get("status", "unknown")),
                    "test_macro_f1": float(data.get("dynamic_llm_kg", {}).get("metrics", {}).get("macro_f1", 0.0)),
                    "test_gain": float(data.get("macro_f1_delta", 0.0)),
                    "validation_gain": float(policy.get("validation_macro_f1_gain", 0.0) or 0.0),
                    "kept_edges": int(policy.get("n_kept_edges", 0) or 0),
                    "admitted": bool(policy.get("admitted", False)),
                    "counterfactual_max_macro_drop": float(policy.get("counterfactual_max_macro_drop", 0.0) or 0.0),
                    "counterfactual_passing_modes": list(policy.get("counterfactual_passing_modes", []) or []),
                    "edge_labels": _edge_labels(data),
                }
            )
    aggregates: dict[str, Any] = {}
    for branch in branch_dirs:
        branch_rows = [row for row in rows if row.get("branch") == branch and row.get("status") == "ok"]
        aggregates[branch] = {
            "n": len(branch_rows),
            "test_macro_f1": _mean_std([float(row["test_macro_f1"]) for row in branch_rows]),
            "test_gain": _mean_std([float(row["test_gain"]) for row in branch_rows]),
            "validation_gain": _mean_std([float(row["validation_gain"]) for row in branch_rows]),
            "kept_edges": _mean_std([float(row["kept_edges"]) for row in branch_rows]),
        }
    if aggregates.get("cf_standard", {}).get("n", 0) and aggregates.get("no_cf", {}).get("n", 0):
        cf_by_seed = {row["seed"]: row for row in rows if row.get("branch") == "cf_standard" and row.get("status") == "ok"}
        no_cf_by_seed = {row["seed"]: row for row in rows if row.get("branch") == "no_cf" and row.get("status") == "ok"}
        diffs = [
            float(cf_by_seed[seed]["test_macro_f1"] - no_cf_by_seed[seed]["test_macro_f1"])
            for seed in sorted(set(cf_by_seed) & set(no_cf_by_seed))
        ]
    else:
        diffs = []
    complete = bool(rows) and all(row.get("status") == "ok" for row in rows)
    status_prefix = "complete" if complete else "partial"
    return {
        "schema": "skab_cf_subset_summary_v2",
        "summary_kind": summary_kind,
        "status": f"{status_prefix}_{summary_kind}",
        "seeds": seeds,
        "rows": rows,
        "aggregates": aggregates,
        "cf_minus_no_cf_test_macro_f1": _mean_std(diffs),
        "interpretation": (
            "Validation-positive edge subsets make the CF/no-CF comparison runnable. If CF and no-CF stay close, "
            "the main performance driver is the validation-admitted candidate itself; CF should be described as "
            "a reliability/interpretability guard rather than the primary source of accuracy."
        ),
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        f"# SKAB CF/No-CF Subset {str(report.get('summary_kind', 'smoke')).title()} Summary",
        "",
        f"- Status: {report.get('status')}",
        f"- Seeds: {', '.join(str(seed) for seed in report.get('seeds', []))}",
        f"- CF minus no-CF test Macro-F1: {report.get('cf_minus_no_cf_test_macro_f1', {}).get('mean', 0.0):+.4f} +/- {report.get('cf_minus_no_cf_test_macro_f1', {}).get('std', 0.0):.4f}",
        "",
        "| Branch | N | Test Macro-F1 | Test Gain | Val Gain | Kept Edges |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for branch, agg in report.get("aggregates", {}).items():
        lines.append(
            "| {branch} | {n} | {test:.4f} +/- {test_std:.4f} | {gain:+.4f} +/- {gain_std:.4f} | {vgain:+.4f} +/- {vgain_std:.4f} | {kept:.2f} +/- {kept_std:.2f} |".format(
                branch=branch,
                n=int(agg.get("n", 0)),
                test=float(agg.get("test_macro_f1", {}).get("mean", 0.0)),
                test_std=float(agg.get("test_macro_f1", {}).get("std", 0.0)),
                gain=float(agg.get("test_gain", {}).get("mean", 0.0)),
                gain_std=float(agg.get("test_gain", {}).get("std", 0.0)),
                vgain=float(agg.get("validation_gain", {}).get("mean", 0.0)),
                vgain_std=float(agg.get("validation_gain", {}).get("std", 0.0)),
                kept=float(agg.get("kept_edges", {}).get("mean", 0.0)),
                kept_std=float(agg.get("kept_edges", {}).get("std", 0.0)),
            )
        )
    lines.extend(["", "| Seed | Branch | Test Macro-F1 | Test Gain | Val Gain | Kept | CF Max Drop | Edges |", "|---:|---|---:|---:|---:|---:|---:|---|"])
    for row in report.get("rows", []):
        lines.append(
            "| {seed} | {branch} | {test} | {gain} | {vgain} | {kept} | {cfmax} | {edges} |".format(
                seed=row.get("seed"),
                branch=row.get("branch"),
                test="n/a" if row.get("status") != "ok" else f"{float(row.get('test_macro_f1', 0.0)):.4f}",
                gain="n/a" if row.get("status") != "ok" else f"{float(row.get('test_gain', 0.0)):+.4f}",
                vgain="n/a" if row.get("status") != "ok" else f"{float(row.get('validation_gain', 0.0)):+.4f}",
                kept="n/a" if row.get("status") != "ok" else int(row.get("kept_edges", 0)),
                cfmax="n/a" if row.get("status") != "ok" else f"{float(row.get('counterfactual_max_macro_drop', 0.0)):.4f}",
                edges=", ".join(row.get("edge_labels", []) or []),
            )
        )
    lines.extend(["", "## Interpretation", "", str(report.get("interpretation", "")), ""])
    return "\n".join(lines)


def write_summary(
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    *,
    branch_dirs: Mapping[str, Path] = BRANCH_DIRS,
    summary_kind: str = "smoke",
    output_stem: str | None = None,
) -> list[Path]:
    output_dir = Path(output_dir)
    os.makedirs(_fs_path(output_dir), exist_ok=True)
    report = build_summary(branch_dirs=branch_dirs, summary_kind=summary_kind)
    stem = output_stem or f"skab_cf_subset_{summary_kind}_summary"
    json_path = output_dir / f"{stem}.json"
    md_path = output_dir / f"{stem}.md"
    _write_text(json_path, json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    _write_text(md_path, render_markdown(report))
    return [json_path, md_path]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Summarize SKAB CF/no-CF subset smoke outputs.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--mode", choices=["smoke", "formal"], default="smoke")
    args = parser.parse_args(argv)
    if args.mode == "formal":
        branch_dirs = FORMAL_BRANCH_DIRS
        output_dir = FORMAL_OUTPUT_DIR if args.output_dir == DEFAULT_OUTPUT_DIR else args.output_dir
        summary_kind = "formal"
    else:
        branch_dirs = BRANCH_DIRS
        output_dir = args.output_dir
        summary_kind = "smoke"
    for path in write_summary(output_dir, branch_dirs=branch_dirs, summary_kind=summary_kind):
        print(path)


if __name__ == "__main__":
    main()
