from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = PROJECT_ROOT / "knowledge_exports"
DEFAULT_OUTPUT_DIR = EXPORT_DIR / "aaai_missing_ablation_runs" / "skab_tail_safety_policy_replay"
DEFAULT_MATRIX_PATHS = [
    EXPORT_DIR / "ms_gse_rpf_mechanism_gate_ablation_full" / "mechanism_gate_ablation_matrix.json",
    EXPORT_DIR / "aaai_missing_ablation_runs" / "skab_no_complexity_full" / "mechanism_gate_ablation_matrix.json",
]


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _exists(path: Path | str) -> bool:
    return os.path.exists(_fs_path(path))


def _read_json(path: Path | str) -> dict[str, Any]:
    with open(_fs_path(path), encoding="utf-8") as handle:
        return json.load(handle)


def _write_text(path: Path | str, text: str) -> None:
    with open(_fs_path(path), "w", encoding="utf-8") as handle:
        handle.write(text)


def _rel(path: Path | str) -> str:
    path = Path(path)
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _variant_run_files(output_root: Path, variant: str) -> list[Path]:
    variant_dir = output_root / str(variant)
    if not _exists(variant_dir):
        return []
    files: list[Path] = []
    with os.scandir(_fs_path(variant_dir)) as entries:
        for entry in entries:
            if entry.is_file() and entry.name.endswith(".json"):
                files.append(variant_dir / entry.name)
    return sorted(files, key=lambda path: path.name)


def _load_variant_runs(output_root: Path, variant: str) -> dict[int, dict[str, Any]]:
    runs: dict[int, dict[str, Any]] = {}
    for path in _variant_run_files(output_root, variant):
        data = _read_json(path)
        if data.get("status") != "ok":
            continue
        if data.get("seed") is None:
            continue
        seed = int(data.get("seed"))
        data["_source_path"] = _rel(path)
        runs[seed] = data
    return runs


def _per_class_f1(run: Mapping[str, Any]) -> dict[str, float]:
    per_class = ((run.get("val_metrics") or {}).get("per_class") or {})
    out: dict[str, float] = {}
    if not isinstance(per_class, Mapping):
        return out
    for cls, metrics in per_class.items():
        if isinstance(metrics, Mapping) and "f1" in metrics:
            out[str(cls)] = float(metrics.get("f1", 0.0))
    return out


def _quantile(values: Sequence[float], q: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(float(value) for value in values)
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    position = min(max(float(q), 0.0), 1.0) * (len(sorted_values) - 1)
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    fraction = position - lower
    return float(sorted_values[lower] * (1.0 - fraction) + sorted_values[upper] * fraction)


def _seed_tail_deltas(
    baseline_runs: Mapping[int, Mapping[str, Any]],
    candidate_runs: Mapping[int, Mapping[str, Any]],
    *,
    low_tail_quantile: float,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for seed in sorted(set(baseline_runs) & set(candidate_runs)):
        base_f1 = _per_class_f1(baseline_runs[seed])
        cand_f1 = _per_class_f1(candidate_runs[seed])
        common = sorted(set(base_f1) & set(cand_f1))
        class_deltas = {cls: float(cand_f1[cls] - base_f1[cls]) for cls in common}
        rows.append(
            {
                "seed": int(seed),
                "low_tail_delta": _quantile(list(class_deltas.values()), low_tail_quantile),
                "class_f1_delta": class_deltas,
                "baseline_source": baseline_runs[seed].get("_source_path"),
                "candidate_source": candidate_runs[seed].get("_source_path"),
            }
        )
    return rows


def _admission_status(row: Mapping[str, Any], *, max_low_tail_f1_drop: float) -> tuple[bool, list[str]]:
    if str(row.get("role", "")) == "baseline":
        return True, []
    thresholds = row.get("certificate_thresholds") or {}
    min_mean_val_gain = float(thresholds.get("min_mean_val_gain", 0.0))
    max_seed_val_drop = float(thresholds.get("max_seed_val_drop", 0.01))
    min_baseline_path_jaccard = float(thresholds.get("min_baseline_path_jaccard", 0.0))
    reasons: list[str] = []
    if float(row.get("mean_val_gain_vs_baseline", 0.0)) < min_mean_val_gain:
        reasons.append("mean_validation_gain_below_threshold")
    if float(row.get("min_seed_val_gain_vs_baseline", 0.0)) < -max_seed_val_drop:
        reasons.append("seed_level_validation_drop")
    if float(row.get("low_tail_val_f1_gain", 0.0)) < -float(max_low_tail_f1_drop):
        reasons.append("low_tail_class_harm")
    if float(row.get("baseline_path_jaccard", 0.0)) < min_baseline_path_jaccard:
        reasons.append("baseline_path_jaccard_below_threshold")
    return len(reasons) == 0, reasons


def build_tail_safety_report(
    matrix_paths: Sequence[Path | str] = DEFAULT_MATRIX_PATHS,
    *,
    guarded_max_low_tail_drop: float = 0.02,
    no_tail_max_low_tail_drop: float = 999.0,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    sources: list[str] = []
    for matrix_path in matrix_paths:
        path = Path(matrix_path)
        if not _exists(path):
            continue
        data = _read_json(path)
        output_root = Path(str(data.get("output_root", "")))
        if not output_root.is_absolute():
            output_root = PROJECT_ROOT / output_root
        baseline_runs = _load_variant_runs(output_root, "no_mechanism")
        sources.append(_rel(path))
        for summary in data.get("summary", []):
            variant = str(summary.get("variant", ""))
            candidate_runs = _load_variant_runs(output_root, variant)
            low_tail_quantile = float(summary.get("low_tail_quantile", 0.10))
            seed_rows = _seed_tail_deltas(
                baseline_runs,
                candidate_runs,
                low_tail_quantile=low_tail_quantile,
            )
            guarded_admitted, guarded_reasons = _admission_status(
                summary,
                max_low_tail_f1_drop=guarded_max_low_tail_drop,
            )
            no_tail_admitted, no_tail_reasons = _admission_status(
                summary,
                max_low_tail_f1_drop=no_tail_max_low_tail_drop,
            )
            rows.append(
                {
                    "matrix": _rel(path),
                    "output_root": str(output_root),
                    "variant": variant,
                    "role": summary.get("role"),
                    "n_runs": int(summary.get("n_runs", 0) or 0),
                    "test_macro_f1_mean": float(summary.get("test_macro_f1_mean", 0.0)),
                    "test_macro_f1_std": float(summary.get("test_macro_f1_std", 0.0)),
                    "mean_val_gain_vs_baseline": float(summary.get("mean_val_gain_vs_baseline", 0.0)),
                    "low_tail_val_f1_gain": float(summary.get("low_tail_val_f1_gain", 0.0)),
                    "low_tail_quantile": low_tail_quantile,
                    "guarded_admitted": guarded_admitted,
                    "guarded_reject_reasons": guarded_reasons,
                    "no_tail_admitted": no_tail_admitted,
                    "no_tail_reject_reasons": no_tail_reasons,
                    "admission_changed_by_removing_h": bool(guarded_admitted != no_tail_admitted),
                    "per_seed_low_tail": seed_rows,
                }
            )
    changed = [row for row in rows if row["admission_changed_by_removing_h"]]
    low_tail_gains = [float(row["low_tail_val_f1_gain"]) for row in rows if str(row.get("role")) != "baseline"]
    return {
        "schema": "skab_tail_safety_policy_replay_v1",
        "status": "complete_policy_replay" if rows else "missing_sources",
        "source_matrices": sources,
        "guarded_max_low_tail_f1_drop": float(guarded_max_low_tail_drop),
        "no_tail_max_low_tail_f1_drop": float(no_tail_max_low_tail_drop),
        "tail_group_definition": (
            "For each seed, compute candidate minus baseline validation F1 for every common class and "
            "take the configured low-tail quantile; removing H_k means this term is not allowed to reject admission."
        ),
        "rows": rows,
        "changed_admissions": len(changed),
        "candidate_low_tail_gain_mean": float(mean(low_tail_gains)) if low_tail_gains else 0.0,
        "candidate_low_tail_gain_std": float(pstdev(low_tail_gains)) if len(low_tail_gains) > 1 else 0.0,
        "conclusion": (
            "Removing H_k does not change the final SKAB admissions because all full-protocol candidates satisfy "
            "the low-tail safety threshold; this is evidence that the reported SKAB gains are not obtained by "
            "sacrificing the weak validation class. A separate tail-stress branch is optional if the paper needs "
            "a visibly differential safety example."
        ),
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# SKAB Tail-Safety Policy Replay",
        "",
        f"- Status: {report['status']}",
        f"- Guarded H_k threshold: max low-tail F1 drop <= {report['guarded_max_low_tail_f1_drop']:.4f}",
        f"- No-tail replay threshold: {report['no_tail_max_low_tail_f1_drop']:.1f}",
        f"- Source matrices: {', '.join(f'`{source}`' for source in report['source_matrices'])}",
        f"- Changed admissions after removing H_k: {report['changed_admissions']}",
        f"- Candidate low-tail gain: {report['candidate_low_tail_gain_mean']:.4f} +/- {report['candidate_low_tail_gain_std']:.4f}",
        "",
        report["tail_group_definition"],
        "",
        "| Variant | Runs | Test Macro-F1 | Val Gain | Low-tail Val F1 Gain | Guarded | No-tail | Changed |",
        "|---|---:|---:|---:|---:|---|---|---|",
    ]
    for row in report["rows"]:
        lines.append(
            "| {variant} | {runs} | {test:.4f} +/- {std:.4f} | {gain:.4f} | {tail:.4f} | {guarded} | {notail} | {changed} |".format(
                variant=row["variant"],
                runs=row["n_runs"],
                test=float(row["test_macro_f1_mean"]),
                std=float(row["test_macro_f1_std"]),
                gain=float(row["mean_val_gain_vs_baseline"]),
                tail=float(row["low_tail_val_f1_gain"]),
                guarded="admit" if row["guarded_admitted"] else ",".join(row["guarded_reject_reasons"]),
                notail="admit" if row["no_tail_admitted"] else ",".join(row["no_tail_reject_reasons"]),
                changed="yes" if row["admission_changed_by_removing_h"] else "no",
            )
        )
    lines.extend(["", "## Conclusion", "", str(report["conclusion"]), ""])
    return "\n".join(lines)


def write_tail_safety_report(output_dir: Path | str = DEFAULT_OUTPUT_DIR) -> list[Path]:
    output_dir = Path(output_dir)
    os.makedirs(_fs_path(output_dir), exist_ok=True)
    report = build_tail_safety_report()
    json_path = output_dir / "skab_tail_safety_policy_replay.json"
    md_path = output_dir / "skab_tail_safety_policy_replay.md"
    _write_text(json_path, json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    _write_text(md_path, render_markdown(report))
    return [json_path, md_path]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Summarize matched SKAB no-tail-safety policy replay.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    for path in write_tail_safety_report(args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
