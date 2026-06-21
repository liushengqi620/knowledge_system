from __future__ import annotations

import argparse
import json
import os
import shutil
import statistics
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = REPO_ROOT / "knowledge_exports"
DEFAULT_OUTPUT_DIR = EXPORT_DIR
ARTIFACT_DIR_NAME = "aaai_seed_level_ablation_artifacts"

FORMAL_PROTOCOL_JSON = EXPORT_DIR / "aaai_formal_public_protocol" / "aaai_formal_public_protocol.json"
TEP_SEQUENCE_JSONS = [
    EXPORT_DIR / "tep_gdn_20k_e10_recovered.json",
    EXPORT_DIR / "tep_mtad_20k_e10_recovered.json",
]
MECHANISM_GATE_SOURCES = [
    (
        "skab_mechanism_gate",
        EXPORT_DIR / "ms_gse_rpf_mechanism_gate_ablation_full" / "mechanism_gate_ablation_matrix.json",
        Path("C:/kg_runs/mechanism_gate_full_matrix"),
    ),
    (
        "skab_no_complexity_full",
        EXPORT_DIR / "aaai_missing_ablation_runs" / "skab_no_complexity_full" / "mechanism_gate_ablation_matrix.json",
        Path("C:/kg_runs/aaai_no_complexity_full"),
    ),
]


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _exists(path: Path | str) -> bool:
    return os.path.exists(_fs_path(path))


def _load_json(path: Path | str) -> Any:
    with open(_fs_path(path), encoding="utf-8") as handle:
        return json.load(handle)


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _mean(values: list[float]) -> float | None:
    return statistics.mean(values) if values else None


def _std(values: list[float]) -> float | None:
    return statistics.pstdev(values) if len(values) > 1 else 0.0 if values else None


def _rel(path: Path | str) -> str:
    path = Path(path)
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _copy_artifact(source: Path, artifact_root: Path, group: str, variant: str, seed: int | str) -> str | None:
    if not _exists(source):
        return None
    destination = artifact_root / group / variant / f"seed{seed}_{source.name}"
    os.makedirs(_fs_path(destination.parent), exist_ok=True)
    shutil.copy2(_fs_path(source), _fs_path(destination))
    return _rel(destination)


def _metric_row(
    group: str,
    variant: str,
    dataset: str,
    metric_name: str,
    direction: str,
    seed_metrics: dict[str, float],
    artifact_paths: dict[str, str],
    source_summary: str,
    planned_ablation_link: str,
    note: str,
) -> dict[str, Any]:
    values = [value for _, value in sorted(seed_metrics.items())]
    return {
        "group": group,
        "variant": variant,
        "dataset": dataset,
        "metric_name": metric_name,
        "metric_direction": direction,
        "n_seeds": len(seed_metrics),
        "seeds": sorted(seed_metrics.keys(), key=str),
        "seed_metrics": seed_metrics,
        "mean": _mean(values),
        "std": _std(values),
        "artifact_paths": artifact_paths,
        "source_summary": source_summary,
        "planned_ablation_link": planned_ablation_link,
        "note": note,
    }


def _formal_protocol_rows(artifact_root: Path) -> list[dict[str, Any]]:
    if not _exists(FORMAL_PROTOCOL_JSON):
        return []
    data = _load_json(FORMAL_PROTOCOL_JSON)
    rows = []
    for run in data.get("runs", []):
        status = run.get("status", {})
        seed_metrics: dict[str, float] = {}
        artifact_paths: dict[str, str] = {}
        for seed, seed_record in (status.get("runs") or {}).items():
            metric = _safe_float(seed_record.get("metric"))
            if metric is None:
                continue
            seed_metrics[str(seed)] = metric
            copied = _copy_artifact(Path(seed_record.get("path", "")), artifact_root, "formal_public_protocol", run["name"], seed)
            if copied:
                artifact_paths[str(seed)] = copied
        if not seed_metrics:
            continue
        direction = "lower_is_better" if status.get("metric_name") == "rul_rmse" else "higher_is_better"
        planned_link = "Anchor only / Full model / RUL transfer"
        if "llm" in run["name"]:
            planned_link = "LLM only safety/control"
        elif "anchorpath" in run["name"] or "bitemp" in run["name"] or "tempmix" in run["name"]:
            planned_link = "Lag/residual only / Full model"
        rows.append(
            _metric_row(
                "formal_public_protocol",
                run["name"],
                run.get("dataset", ""),
                status.get("metric_name", run.get("expected_metric", "")),
                direction,
                seed_metrics,
                artifact_paths,
                _rel(FORMAL_PROTOCOL_JSON),
                planned_link,
                run.get("claim_use", ""),
            )
        )
    return rows


def _tep_sequence_rows(artifact_root: Path) -> list[dict[str, Any]]:
    rows = []
    for summary_path in TEP_SEQUENCE_JSONS:
        if not _exists(summary_path):
            continue
        data = _load_json(summary_path)
        model = data.get("model_name", summary_path.stem)
        grouped: dict[str, dict[str, float]] = {}
        artifacts: dict[str, dict[str, str]] = {}
        for record in data.get("records", []):
            variant = record.get("variant", "")
            seed = str(record.get("seed"))
            result = record.get("result", {})
            metric = _safe_float(
                result.get("sample_multiclass_metrics", {}).get("target_defect_macro_f1")
            )
            if metric is None:
                continue
            grouped.setdefault(variant, {})[seed] = metric
            copied = _copy_artifact(Path(record.get("path", "")), artifact_root, f"tep_sequence_{model}", variant, seed)
            if copied:
                artifacts.setdefault(variant, {})[seed] = copied
        for variant, seed_metrics in grouped.items():
            planned_link = {
                "no_graph": "Anchor only / Graph only control",
                "all_lagged": "Unfiltered evidence",
                "reliable_lagged": "No complexity penalty control / reliability pruning",
                "residual_gated_lagged": "Lag/residual only / Full graph-temporal route",
            }.get(variant, "Graph-temporal ablation")
            rows.append(
                _metric_row(
                    f"tep_sequence_{model}",
                    variant,
                    "TEP",
                    "target_defect_macro_f1",
                    "higher_is_better",
                    seed_metrics,
                    artifacts.get(variant, {}),
                    _rel(summary_path),
                    planned_link,
                    "Recovered full-budget sequence graph ablation under the matched TEP protocol.",
                )
            )
    return rows


def _mechanism_gate_rows_for_source(
    artifact_root: Path,
    *,
    group_name: str,
    summary_path: Path,
    run_root: Path,
) -> list[dict[str, Any]]:
    if not _exists(summary_path):
        return []
    data = _load_json(summary_path)
    rows = []
    for item in data.get("summary", []):
        variant = item.get("variant", "")
        seed_metrics: dict[str, float] = {}
        artifact_paths: dict[str, str] = {}
        run_dir = run_root / variant
        for seed in item.get("seeds", []):
            seed_files = sorted(run_dir.glob(f"*seed{seed}.json"))
            seed_files = [path for path in seed_files if path.name != "ms_gse_rpf_skab_full_summary.json"]
            if not seed_files:
                continue
            seed_data = _load_json(seed_files[0])
            metric = _safe_float(
                seed_data.get("primary_test_metrics", {}).get("macro_f1")
                or seed_data.get("thresholded_test_metrics", {}).get("macro_f1")
                or seed_data.get("test_metrics", {}).get("macro_f1")
            )
            if metric is None:
                continue
            seed_metrics[str(seed)] = metric
            copied = _copy_artifact(seed_files[0], artifact_root, "skab_mechanism_gate", variant, seed)
            if copied:
                artifact_paths[str(seed)] = copied
        if not seed_metrics:
            continue
        rows.append(
            _metric_row(
                group_name,
                variant,
                "SKAB",
                "macro_f1",
                "higher_is_better",
                seed_metrics,
                artifact_paths,
                _rel(summary_path),
                _mechanism_variant_link(variant),
                (
                    f"val_gain={item.get('mean_val_gain_vs_baseline')}; "
                    f"low_tail_gain={item.get('low_tail_val_f1_gain')}; "
                    f"path_jaccard={item.get('baseline_path_jaccard')}; "
                    f"source_complexity={item.get('source_complexity')}; "
                    f"status={item.get('status')}"
                ),
            )
        )
    return rows


def _mechanism_gate_rows(artifact_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for group_name, summary_path, run_root in MECHANISM_GATE_SOURCES:
        rows.extend(
            _mechanism_gate_rows_for_source(
                artifact_root,
                group_name=group_name,
                summary_path=summary_path,
                run_root=run_root,
            )
        )
    return rows


def _mechanism_variant_link(variant: str) -> str:
    return {
        "no_mechanism": "Anchor only / no expert graph",
        "raw_expert_graph": "Unfiltered evidence / raw expert graph",
        "late_expert_path": "Expert only / late path evidence",
        "expert_candidate_no_gate": "Expert only / no reliability gate",
        "expert_candidate_data_gate": "Expert only / reliability admission",
        "expert_candidate_data_gate_consistency": "Expert only / path consistency",
        "expert_llm_candidate_data_gate_no_complexity": "No complexity penalty / source-family scale removed",
        "expert_llm_candidate_data_gate_complexity_guarded": "No complexity penalty control / source-family scale retained",
        "algorithmic_candidate_gate_control": "Graph only / algorithmic control",
    }.get(variant, "Mechanism-gate ablation")


def build_seed_level_ablation_evidence(output_dir: Path | str = DEFAULT_OUTPUT_DIR) -> dict[str, Any]:
    output_dir = Path(output_dir)
    artifact_root = output_dir / ARTIFACT_DIR_NAME
    os.makedirs(_fs_path(artifact_root), exist_ok=True)
    rows = []
    rows.extend(_formal_protocol_rows(artifact_root))
    rows.extend(_tep_sequence_rows(artifact_root))
    rows.extend(_mechanism_gate_rows(artifact_root))
    complete_rows = [row for row in rows if row["n_seeds"] >= 3 and len(row["artifact_paths"]) >= 3]
    complete_variants = {row["variant"] for row in complete_rows}
    remaining_design_gaps = [
        "No-tail-safety intervention still needs a matched run removing only H_k.",
        "No-counterfactual-guard still needs a formal three-seed removal row, beyond the current CF-guarded smoke.",
    ]
    if "expert_llm_candidate_data_gate_no_complexity" not in complete_variants:
        remaining_design_gaps.append(
            "No-complexity-penalty now has a narrow source-family scaling ablation flag, but still needs a formal three-seed scored row."
        )
    return {
        "status": "partial" if rows else "missing",
        "completion_rule": (
            "Rows count as seed-level evidence when all three expected seeds have metrics and copied source JSON artifacts. "
            "This ledger does not by itself complete missing no-tail/no-counterfactual/no-complexity final interventions."
        ),
        "rows_total": len(rows),
        "complete_seed_level_rows": len(complete_rows),
        "artifact_root": _rel(artifact_root),
        "rows": rows,
        "remaining_design_gaps": remaining_design_gaps,
    }


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    if value is None:
        return "n/a"
    return str(value)


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# AAAI Seed-Level Ablation Evidence",
        "",
        f"- Status: {report['status']}",
        f"- Rows total: {report['rows_total']}",
        f"- Complete seed-level rows: {report['complete_seed_level_rows']}",
        f"- Artifact root: `{report['artifact_root']}`",
        f"- Completion rule: {report['completion_rule']}",
        "",
        "| Group | Variant | Dataset | Metric | Seeds | Mean | Std | Planned ablation link | Source |",
        "|---|---|---|---|---:|---:|---:|---|---|",
    ]
    for row in report["rows"]:
        lines.append(
            f"| {row['group']} | {row['variant']} | {row['dataset']} | {row['metric_name']} | "
            f"{row['n_seeds']} | {_fmt(row['mean'])} | {_fmt(row['std'])} | {row['planned_ablation_link']} | "
            f"`{row['source_summary']}` |"
        )
    lines.extend(["", "## Remaining Design Gaps", ""])
    lines.extend(f"- {gap}" for gap in report["remaining_design_gaps"])
    lines.append("")
    return "\n".join(lines)


def write_seed_level_ablation_evidence(output_dir: Path | str = DEFAULT_OUTPUT_DIR) -> list[Path]:
    output_dir = Path(output_dir)
    os.makedirs(_fs_path(output_dir), exist_ok=True)
    report = build_seed_level_ablation_evidence(output_dir)
    json_path = output_dir / "aaai_seed_level_ablation_evidence.json"
    md_path = output_dir / "aaai_seed_level_ablation_evidence.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return [json_path, md_path]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build a copied seed-level ablation evidence ledger.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    for path in write_seed_level_ablation_evidence(args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
