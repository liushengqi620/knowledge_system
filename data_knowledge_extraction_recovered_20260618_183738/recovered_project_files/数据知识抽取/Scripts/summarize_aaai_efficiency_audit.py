from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = PROJECT_ROOT / "knowledge_exports"
FORMAL_RUN_ROOT = EXPORT_DIR / "aaai_formal_public_runs"


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _exists(path: Path | str) -> bool:
    return os.path.exists(_fs_path(path))


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


def _mean(rows: Iterable[dict[str, Any]], key: str) -> float | None:
    values = [float(row[key]) for row in rows if row.get(key) is not None]
    return float(np.mean(values)) if values else None


def _std(rows: Iterable[dict[str, Any]], key: str) -> float | None:
    values = [float(row[key]) for row in rows if row.get(key) is not None]
    return float(np.std(values)) if values else None


def _fmt(value: float | None, digits: int = 4) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.{digits}f}"


def _metric_from_payload(payload: dict[str, Any]) -> tuple[str, float | None]:
    primary = payload.get("primary_test_metrics") or {}
    if primary.get("rul_rmse") is not None:
        return "RUL RMSE", float(primary["rul_rmse"])
    if primary.get("macro_f1") is not None:
        return "Macro-F1", float(primary["macro_f1"])
    sample = payload.get("sample_multiclass_metrics") or {}
    if sample.get("target_defect_macro_f1") is not None:
        return "Target-F1", float(sample["target_defect_macro_f1"])
    return "primary", None


@dataclass(frozen=True)
class PublicRunSpec:
    dataset: str
    branch: str
    run_dir: str
    filename_prefix: str
    paper_use: str


PUBLIC_RUN_SPECS = (
    PublicRunSpec(
        dataset="SKAB",
        branch="strong_anchor",
        run_dir="skab_strong_anchor_w48_e40",
        filename_prefix="ms_gse_rpf_skab_anomaly_full_prior-none_seed",
        paper_use="formal anomaly anchor efficiency",
    ),
    PublicRunSpec(
        dataset="SKAB",
        branch="llm_condition_candidate_gate",
        run_dir="skab_llm_condition_candidate_gate_w48_e40",
        filename_prefix="ms_gse_rpf_skab_anomaly_full_prior-none_seed",
        paper_use="formal LLM condition-verifier efficiency",
    ),
    PublicRunSpec(
        dataset="C-MAPSS",
        branch="original_rul_anchor",
        run_dir="cmapss_original_rul_terminal_anchor_w48_e20",
        filename_prefix="ms_gse_rpf_cmapss_rul_full_prior-none_seed",
        paper_use="terminal RUL anchor efficiency",
    ),
    PublicRunSpec(
        dataset="C-MAPSS",
        branch="anchorpath_bigru_cls020",
        run_dir="cmapss_rul_anchorpath_bigru_cls020_w80_e20",
        filename_prefix="ms_gse_rpf_cmapss_rul_full_prior-none_seed",
        paper_use="terminal RUL proposed-branch efficiency",
    ),
)


def _seed_files(run_dir: Path, filename_prefix: str) -> list[Path]:
    if not _exists(run_dir):
        return []
    names = [
        name
        for name in os.listdir(_fs_path(run_dir))
        if name.startswith(filename_prefix) and name.endswith(".json")
    ]
    return [run_dir / name for name in sorted(names)]


def summarize_public_run(spec: PublicRunSpec, run_root: Path = FORMAL_RUN_ROOT) -> dict[str, Any]:
    run_dir = Path(run_root) / spec.run_dir
    seed_rows: list[dict[str, Any]] = []
    for path in _seed_files(run_dir, spec.filename_prefix):
        payload = _read_json(path)
        efficiency = payload.get("efficiency") or {}
        metric_name, metric_value = _metric_from_payload(payload)
        seed_rows.append(
            {
                "seed": int(payload.get("seed", -1)),
                "path": path.as_posix(),
                "metric_name": metric_name,
                "metric_value": metric_value,
                "parameters": efficiency.get("parameters"),
                "train_seconds": efficiency.get("train_seconds"),
                "train_samples_per_second": efficiency.get("train_samples_per_second"),
                "test_inference_seconds": efficiency.get("test_inference_seconds"),
                "test_inference_samples_per_second": efficiency.get("test_inference_samples_per_second"),
                "device": payload.get("device") or efficiency.get("device") or "recorded-by-run",
            }
        )
    status = "measured" if seed_rows and all(row.get("test_inference_samples_per_second") is not None for row in seed_rows) else "missing"
    return {
        "dataset": spec.dataset,
        "branch": spec.branch,
        "source": str(run_dir),
        "status": status,
        "paper_use": spec.paper_use,
        "n_runs": len(seed_rows),
        "metric_name": seed_rows[0]["metric_name"] if seed_rows else "primary",
        "metric_mean": _mean(seed_rows, "metric_value"),
        "metric_std": _std(seed_rows, "metric_value"),
        "parameters_mean": _mean(seed_rows, "parameters"),
        "parameters_std": _std(seed_rows, "parameters"),
        "train_seconds_mean": _mean(seed_rows, "train_seconds"),
        "train_seconds_std": _std(seed_rows, "train_seconds"),
        "train_samples_per_second_mean": _mean(seed_rows, "train_samples_per_second"),
        "test_inference_seconds_mean": _mean(seed_rows, "test_inference_seconds"),
        "test_inference_samples_per_second_mean": _mean(seed_rows, "test_inference_samples_per_second"),
        "devices": sorted({str(row.get("device")) for row in seed_rows if row.get("device")}),
        "seed_rows": sorted(seed_rows, key=lambda row: row["seed"]),
    }


def summarize_tep_sequence_file(
    path: Path,
    *,
    branch_prefix: str,
    variants: tuple[str, ...] = ("no_graph", "residual_gated_lagged"),
) -> list[dict[str, Any]]:
    if not _exists(path):
        return [
            {
                "dataset": "TEP",
                "branch": f"{branch_prefix}:{variant}",
                "source": str(path),
                "status": "missing",
                "paper_use": "TEP sequence efficiency",
                "n_runs": 0,
                "metric_name": "Target-F1",
                "metric_mean": None,
                "metric_std": None,
                "parameters_mean": None,
                "parameters_std": None,
                "train_seconds_mean": None,
                "train_seconds_std": None,
                "train_samples_per_second_mean": None,
                "test_inference_seconds_mean": None,
                "test_inference_samples_per_second_mean": None,
                "devices": [],
                "seed_rows": [],
            }
            for variant in variants
        ]
    payload = _read_json(path)
    rows: list[dict[str, Any]] = []
    for variant in variants:
        seed_rows: list[dict[str, Any]] = []
        for record in payload.get("records", []):
            if record.get("variant") != variant:
                continue
            result = record.get("result") or {}
            diag = result.get("train_diagnostics") or {}
            metric_name, metric_value = _metric_from_payload(result)
            seed_rows.append(
                {
                    "seed": int(record.get("seed", -1)),
                    "path": str(record.get("path") or path),
                    "metric_name": metric_name,
                    "metric_value": metric_value,
                    "parameters": diag.get("parameters"),
                    "train_seconds": diag.get("train_seconds"),
                    "train_samples_per_second": diag.get("train_samples_per_second"),
                    "test_inference_seconds": diag.get("test_inference_seconds"),
                    "test_inference_samples_per_second": diag.get("test_inference_samples_per_second"),
                    "device": diag.get("device"),
                }
            )
        measured = seed_rows and all(row.get("test_inference_samples_per_second") is not None for row in seed_rows)
        status = "measured" if measured else "needs_timed_rerun"
        rows.append(
            {
                "dataset": "TEP",
                "branch": f"{branch_prefix}:{variant}",
                "source": str(path),
                "status": status,
                "paper_use": "TEP sequence graph efficiency" if measured else "performance-only legacy run; rerun after timing patch",
                "n_runs": len(seed_rows),
                "metric_name": seed_rows[0]["metric_name"] if seed_rows else "Target-F1",
                "metric_mean": _mean(seed_rows, "metric_value"),
                "metric_std": _std(seed_rows, "metric_value"),
                "parameters_mean": _mean(seed_rows, "parameters"),
                "parameters_std": _std(seed_rows, "parameters"),
                "train_seconds_mean": _mean(seed_rows, "train_seconds"),
                "train_seconds_std": _std(seed_rows, "train_seconds"),
                "train_samples_per_second_mean": _mean(seed_rows, "train_samples_per_second"),
                "test_inference_seconds_mean": _mean(seed_rows, "test_inference_seconds"),
                "test_inference_samples_per_second_mean": _mean(seed_rows, "test_inference_samples_per_second"),
                "devices": sorted({str(row.get("device")) for row in seed_rows if row.get("device")}),
                "seed_rows": sorted(seed_rows, key=lambda row: row["seed"]),
            }
        )
    return rows


def build_efficiency_report(
    *,
    formal_run_root: Path = FORMAL_RUN_ROOT,
    export_dir: Path = EXPORT_DIR,
) -> dict[str, Any]:
    rows = [summarize_public_run(spec, formal_run_root) for spec in PUBLIC_RUN_SPECS]
    gdn_timed = Path(export_dir) / "tep_gdn_20k_e10_timed.json"
    gdn_legacy = Path(export_dir) / "tep_gdn_20k_e10_recovered.json"
    mtad_timed = Path(export_dir) / "tep_mtad_20k_e10_timed.json"
    mtad_legacy = Path(export_dir) / "tep_mtad_20k_e10_recovered.json"
    rows.extend(
        summarize_tep_sequence_file(
            gdn_timed if _exists(gdn_timed) else gdn_legacy,
            branch_prefix="GDN20k",
        )
    )
    rows.extend(
        summarize_tep_sequence_file(
            mtad_timed if _exists(mtad_timed) else mtad_legacy,
            branch_prefix="MTADGAT20k",
        )
    )
    full_timed_available = _exists(gdn_timed) and _exists(mtad_timed)
    smoke_path = Path(export_dir) / "tep_gdn_efficiency_smoke.json"
    if _exists(smoke_path) and not full_timed_available:
        rows.extend(
            summarize_tep_sequence_file(
                smoke_path,
                branch_prefix="GDN600TimingSmoke",
                variants=("no_graph", "residual_gated_lagged"),
            )
        )
    missing = [f"{row['dataset']}:{row['branch']}" for row in rows if row["status"] != "measured"]
    notes = ["Measured rows report values read from per-seed JSON artifacts."]
    if full_timed_available:
        notes.extend(
            [
                "TEP GDN/MTAD full-budget efficiency is now read from timed rerun artifacts, not the legacy performance-only files.",
                "Smoke timing rows are omitted once full-budget timed artifacts are present.",
            ]
        )
    else:
        notes.extend(
            [
                "TEP full-budget legacy rows predate the timing patch and must be rerun before they can be used as formal efficiency claims.",
                "The GDN600TimingSmoke rows verify the new timing instrumentation only and are not formal paper efficiency results.",
            ]
        )
    return {
        "schema": "aaai_efficiency_audit_v1",
        "rows": rows,
        "status": "complete" if not missing else "partial",
        "missing_or_legacy_efficiency": missing,
        "timed_rerun_commands": [
            "python Scripts/run_tep_sequence_graph_ablation.py --output knowledge_exports/tep_gdn_20k_e10_timed.json --model gdn --seeds 42,43,44 --max-rows 20000 --window-size 16 --hidden-dim 64 --epochs 10 --batch-size 512 --include-residual-gated --variants no_graph,residual_gated_lagged --resume --device auto",
            "python Scripts/run_tep_sequence_graph_ablation.py --output knowledge_exports/tep_mtad_20k_e10_timed.json --model mtad_gat --seeds 42,43,44 --max-rows 20000 --window-size 16 --hidden-dim 64 --epochs 10 --batch-size 512 --include-residual-gated --variants no_graph,residual_gated_lagged --resume --device auto",
        ],
        "notes": notes,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# AAAI Efficiency Audit",
        "",
        f"- Status: `{report['status']}`",
        "",
        "This audit separates measured efficiency evidence from legacy performance-only runs. "
        "Training time, inference throughput, and parameter count are read from seed-level JSON artifacts when available.",
        "",
        "## Efficiency Table",
        "",
        "| Dataset | Branch | Status | Runs | Metric | Params | Train seconds | Train samples/s | Test infer seconds | Test samples/s | Device | Paper use |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in report["rows"]:
        metric = f"{row['metric_name']} {_fmt(row['metric_mean'])}"
        devices = ", ".join(row.get("devices") or []) or "n/a"
        lines.append(
            "| {dataset} | {branch} | {status} | {runs} | {metric} | {params} | {train_sec} | {train_sps} | {infer_sec} | {infer_sps} | {device} | {paper_use} |".format(
                dataset=row["dataset"],
                branch=row["branch"],
                status=row["status"],
                runs=int(row["n_runs"]),
                metric=metric,
                params=_fmt(row["parameters_mean"], 0),
                train_sec=_fmt(row["train_seconds_mean"], 2),
                train_sps=_fmt(row["train_samples_per_second_mean"], 1),
                infer_sec=_fmt(row["test_inference_seconds_mean"], 4),
                infer_sps=_fmt(row["test_inference_samples_per_second_mean"], 1),
                device=devices,
                paper_use=row["paper_use"],
            )
        )
    lines.extend(["", "## Missing Or Legacy Efficiency", ""])
    if report["missing_or_legacy_efficiency"]:
        lines.extend(f"- {item}" for item in report["missing_or_legacy_efficiency"])
    else:
        lines.append("- none")
    lines.extend(["", "## Timed Rerun Commands", ""])
    for command in report.get("timed_rerun_commands", []):
        lines.append(f"- `{command}`")
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {note}" for note in report["notes"])
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Summarize AAAI efficiency evidence from JSON artifacts.")
    parser.add_argument("--formal-run-root", type=Path, default=FORMAL_RUN_ROOT)
    parser.add_argument("--export-dir", type=Path, default=EXPORT_DIR)
    parser.add_argument("--output-dir", type=Path, default=EXPORT_DIR)
    args = parser.parse_args(argv)
    report = build_efficiency_report(formal_run_root=args.formal_run_root, export_dir=args.export_dir)
    json_path = Path(args.output_dir) / "aaai_efficiency_audit.json"
    md_path = Path(args.output_dir) / "aaai_efficiency_audit.md"
    _write_json(json_path, report)
    _write_text(md_path, render_markdown(report))
    print(json_path)
    print(md_path)


if __name__ == "__main__":
    main()
