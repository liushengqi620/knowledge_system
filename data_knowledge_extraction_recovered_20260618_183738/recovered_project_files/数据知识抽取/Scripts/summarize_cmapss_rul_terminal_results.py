from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RUN_ROOT = PROJECT_ROOT / "knowledge_exports" / "aaai_formal_public_runs"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "knowledge_exports" / "cmapss_rul_terminal_report"


def _fs_path(path: Path) -> str:
    if os.name == "nt":
        resolved = str(Path(path).resolve())
        if not resolved.startswith("\\\\?\\"):
            return "\\\\?\\" + resolved
    return str(path)


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


def _result_files(run_dir: Path) -> list[Path]:
    if not os.path.isdir(_fs_path(run_dir)):
        return []
    files = []
    for name in os.listdir(_fs_path(run_dir)):
        if name.startswith("ms_gse_rpf_cmapss_rul_") and name.endswith(".json") and "_seed" in name:
            files.append(run_dir / name)
    return sorted(files)


def _metric_mean(rows: Sequence[dict[str, Any]], key: str) -> float | None:
    values = [float(row[key]) for row in rows if row.get(key) is not None]
    return float(np.mean(values)) if values else None


def _metric_std(rows: Sequence[dict[str, Any]], key: str) -> float | None:
    values = [float(row[key]) for row in rows if row.get(key) is not None]
    return float(np.std(values)) if values else None


def summarize_run(run_dir: Path, *, name: str) -> dict[str, Any]:
    seed_rows: list[dict[str, Any]] = []
    subset_seed_rows: list[dict[str, Any]] = []
    for path in _result_files(run_dir):
        payload = _read_json(path)
        primary = payload.get("primary_test_metrics") or {}
        seed = int(payload.get("seed", -1))
        seed_rows.append(
            {
                "seed": seed,
                "path": str(path),
                "rul_rmse": float(primary.get("rul_rmse")),
                "rul_mae": float(primary.get("rul_mae")),
                "rul_score": float(primary.get("rul_score")),
                "test_size": int(payload.get("test_size", 0)),
                "rul_eval_protocol": payload.get("rul_eval_protocol"),
                "prediction_source": (payload.get("efficiency") or {}).get("rul_prediction_source"),
            }
        )
        subset_metrics = payload.get("rul_subset_metrics") or {}
        for subset_row in subset_metrics.get("rows", []):
            subset_seed_rows.append({"seed": seed, **subset_row})

    subset_summary: list[dict[str, Any]] = []
    subsets = sorted({str(row.get("subset")) for row in subset_seed_rows})
    for subset in subsets:
        rows = [row for row in subset_seed_rows if str(row.get("subset")) == subset]
        subset_summary.append(
            {
                "subset": subset,
                "n_seeds": int(len(rows)),
                "n_units": int(max(int(row.get("n_units", 0)) for row in rows)) if rows else 0,
                "rmse_mean": _metric_mean(rows, "rul_rmse"),
                "rmse_std": _metric_std(rows, "rul_rmse"),
                "mae_mean": _metric_mean(rows, "rul_mae"),
                "mae_std": _metric_std(rows, "rul_mae"),
                "score_mean": _metric_mean(rows, "rul_score"),
                "score_std": _metric_std(rows, "rul_score"),
            }
        )

    return {
        "name": name,
        "run_dir": str(run_dir),
        "n_seeds": int(len(seed_rows)),
        "seed_rows": sorted(seed_rows, key=lambda row: row["seed"]),
        "overall": {
            "rmse_mean": _metric_mean(seed_rows, "rul_rmse"),
            "rmse_std": _metric_std(seed_rows, "rul_rmse"),
            "mae_mean": _metric_mean(seed_rows, "rul_mae"),
            "mae_std": _metric_std(seed_rows, "rul_mae"),
            "score_mean": _metric_mean(seed_rows, "rul_score"),
            "score_std": _metric_std(seed_rows, "rul_score"),
        },
        "subset_seed_rows": sorted(subset_seed_rows, key=lambda row: (str(row.get("subset")), int(row.get("seed", -1)))),
        "subset_summary": subset_summary,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# C-MAPSS Terminal RUL Report",
        "",
        "All rows use terminal test-unit evaluation. RMSE/MAE lower is better; score lower is better.",
        "",
        "## Overall",
        "",
        "| Branch | Seeds | RMSE mean | RMSE std | MAE mean | Score mean |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for run in report["runs"]:
        overall = run["overall"]
        lines.append(
            "| {name} | {n_seeds} | {rmse:.4f} | {rmse_std:.4f} | {mae:.4f} | {score:.2f} |".format(
                name=run["name"],
                n_seeds=run["n_seeds"],
                rmse=float(overall["rmse_mean"] or 0.0),
                rmse_std=float(overall["rmse_std"] or 0.0),
                mae=float(overall["mae_mean"] or 0.0),
                score=float(overall["score_mean"] or 0.0),
            )
        )
    lines.extend(["", "## Subset Summary", ""])
    for run in report["runs"]:
        lines.extend(
            [
                f"### {run['name']}",
                "",
                "| Subset | Units | RMSE mean | RMSE std | MAE mean | Score mean |",
                "|---|---:|---:|---:|---:|---:|",
            ]
        )
        for row in run["subset_summary"]:
            lines.append(
                "| {subset} | {units} | {rmse:.4f} | {rmse_std:.4f} | {mae:.4f} | {score:.2f} |".format(
                    subset=row["subset"],
                    units=int(row["n_units"]),
                    rmse=float(row["rmse_mean"] or 0.0),
                    rmse_std=float(row["rmse_std"] or 0.0),
                    mae=float(row["mae_mean"] or 0.0),
                    score=float(row["score_mean"] or 0.0),
                )
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_report(run_root: Path) -> dict[str, Any]:
    specs = [
        ("cmapss_original_rul_anchor", "cmapss_original_rul_terminal_anchor_w48_e20"),
        ("cmapss_rul_direct_regime_tempmix", "cmapss_rul_direct_regime_tempmix_w80_e20"),
        ("cmapss_rul_direct_regime_bitempmix", "cmapss_rul_direct_regime_bitempmix_w80_e20"),
        ("cmapss_rul_anchorpath_bigru_cls020", "cmapss_rul_anchorpath_bigru_cls020_w80_e20"),
    ]
    return {
        "schema": "cmapss_terminal_rul_report_v1",
        "runs": [summarize_run(Path(run_root) / subdir, name=name) for name, subdir in specs],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    report = build_report(Path(args.run_root))
    json_path = Path(args.output_dir) / "cmapss_terminal_rul_report.json"
    md_path = Path(args.output_dir) / "cmapss_terminal_rul_report.md"
    _write_json(json_path, report)
    _write_text(md_path, render_markdown(report))
    print(str(json_path))
    print(str(md_path))


if __name__ == "__main__":
    main()
