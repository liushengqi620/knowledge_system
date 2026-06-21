from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "knowledge_exports" / "ms_gse_rpf_mechanism_gate_ablation"


def _fs_path(path: Path) -> str:
    if os.name == "nt":
        resolved = str(Path(path).resolve())
        if not resolved.startswith("\\\\?\\"):
            return "\\\\?\\" + resolved
    return str(path)


@dataclass(frozen=True)
class VariantSpec:
    name: str
    role: str
    claim: str
    flags: tuple[str, ...]


def skab_variant_specs() -> list[VariantSpec]:
    return [
        VariantSpec(
            name="no_mechanism",
            role="baseline",
            claim="No expert mechanism evidence is available to RPF or the graph.",
            flags=("--evidence-prior-mode", "none", "--prior-strength", "0"),
        ),
        VariantSpec(
            name="raw_expert_graph",
            role="negative_control",
            claim="Raw expert edges are injected into the dynamic graph without admission.",
            flags=("--evidence-prior-mode", "expert", "--prior-strength", "0.05"),
        ),
        VariantSpec(
            name="late_expert_path",
            role="late_mechanism",
            claim="Expert evidence is retained as late path-side evidence without graph bias.",
            flags=("--evidence-prior-mode", "expert", "--prior-strength", "0"),
        ),
        VariantSpec(
            name="expert_candidate_no_gate",
            role="ungated_candidate",
            claim="Expert edges are moved out of the graph but admitted as raw RPF candidates.",
            flags=(
                "--evidence-prior-mode",
                "expert",
                "--prior-strength",
                "0",
                "--external-edge-candidate-only",
                "--external-candidate-families",
                "expert",
                "--candidate-coverage-fraction",
                "0.08",
            ),
        ),
        VariantSpec(
            name="expert_candidate_data_gate",
            role="mechanism_gate",
            claim="Expert candidate edges are admitted only through train-only evidence support.",
            flags=(
                "--evidence-prior-mode",
                "expert",
                "--prior-strength",
                "0",
                "--external-edge-candidate-only",
                "--external-candidate-families",
                "expert",
                "--external-family-calibration-floor",
                "0.10",
                "--external-family-min-data-support",
                "0.10",
                "--candidate-coverage-fraction",
                "0.08",
                "--use-task-salience",
                "--salience-mode",
                "class",
                "--algorithmic-evidence-top-k",
                "8",
                "--use-candidate-prior-admission",
                "--candidate-prior-admission-target",
                "coverage_feature",
                "--candidate-prior-admission-support-mode",
                "relative_evidence",
                "--candidate-prior-admission-floor",
                "0.05",
                "--candidate-prior-admission-threshold",
                "0.35",
                "--candidate-prior-admission-scale",
                "0.50",
            ),
        ),
        VariantSpec(
            name="expert_candidate_data_gate_consistency",
            role="mechanism_gate_plus_path_consistency",
            claim="Data-admitted expert candidates are further filtered by path-proposal consistency.",
            flags=(
                "--evidence-prior-mode",
                "expert",
                "--prior-strength",
                "0",
                "--external-edge-candidate-only",
                "--external-candidate-families",
                "expert",
                "--external-family-calibration-floor",
                "0.10",
                "--external-family-min-data-support",
                "0.10",
                "--candidate-coverage-fraction",
                "0.08",
                "--use-task-salience",
                "--salience-mode",
                "class",
                "--algorithmic-evidence-top-k",
                "8",
                "--use-candidate-prior-admission",
                "--candidate-prior-admission-target",
                "coverage_feature",
                "--candidate-prior-admission-support-mode",
                "relative_evidence",
                "--candidate-prior-admission-floor",
                "0.05",
                "--candidate-prior-admission-threshold",
                "0.35",
                "--candidate-prior-admission-scale",
                "0.50",
                "--use-path-proposal-consistency",
                "--path-proposal-consistency-support-mode",
                "evidence_admit",
                "--path-proposal-consistency-strength",
                "0.30",
                "--path-proposal-consistency-floor",
                "0.10",
            ),
        ),
        VariantSpec(
            name="expert_llm_candidate_data_gate_no_complexity",
            role="no_complexity_penalty",
            claim=(
                "Expert and LLM candidate families keep the same data-support admission, but source-family "
                "complexity scaling is disabled."
            ),
            flags=(
                "--evidence-prior-mode",
                "expert_llm",
                "--prior-strength",
                "0",
                "--external-edge-candidate-only",
                "--external-candidate-families",
                "expert,llm",
                "--external-family-calibration-floor",
                "0.10",
                "--external-family-min-data-support",
                "0.00",
                "--external-candidate-llm-scale",
                "0.70",
                "--external-candidate-default-scale",
                "0.85",
                "--disable-source-complexity-penalty",
                "--candidate-coverage-fraction",
                "0.08",
                "--use-task-salience",
                "--salience-mode",
                "class",
                "--algorithmic-evidence-top-k",
                "8",
                "--use-candidate-prior-admission",
                "--candidate-prior-admission-target",
                "coverage_feature",
                "--candidate-prior-admission-support-mode",
                "relative_evidence",
                "--candidate-prior-admission-floor",
                "0.05",
                "--candidate-prior-admission-threshold",
                "0.35",
                "--candidate-prior-admission-scale",
                "0.50",
            ),
        ),
        VariantSpec(
            name="expert_llm_candidate_data_gate_complexity_guarded",
            role="complexity_guarded_twin",
            claim=(
                "Expert and LLM candidate families use the same candidate pool as the no-complexity row, "
                "but keep source-family complexity scaling."
            ),
            flags=(
                "--evidence-prior-mode",
                "expert_llm",
                "--prior-strength",
                "0",
                "--external-edge-candidate-only",
                "--external-candidate-families",
                "expert,llm",
                "--external-family-calibration-floor",
                "0.10",
                "--external-family-min-data-support",
                "0.00",
                "--external-candidate-llm-scale",
                "0.70",
                "--external-candidate-default-scale",
                "0.85",
                "--candidate-coverage-fraction",
                "0.08",
                "--use-task-salience",
                "--salience-mode",
                "class",
                "--algorithmic-evidence-top-k",
                "8",
                "--use-candidate-prior-admission",
                "--candidate-prior-admission-target",
                "coverage_feature",
                "--candidate-prior-admission-support-mode",
                "relative_evidence",
                "--candidate-prior-admission-floor",
                "0.05",
                "--candidate-prior-admission-threshold",
                "0.35",
                "--candidate-prior-admission-scale",
                "0.50",
            ),
        ),
        VariantSpec(
            name="algorithmic_candidate_gate_control",
            role="algorithmic_control",
            claim="Data-derived candidate admission without expert mechanism evidence.",
            flags=(
                "--evidence-prior-mode",
                "none",
                "--prior-strength",
                "0",
                "--algorithmic-edge-prior-mode",
                "edge_dual_lattice",
                "--algorithmic-edge-prior-top-k",
                "12",
                "--algorithmic-edge-prior-group-top-k",
                "3",
                "--algorithmic-edge-prior-max-lag",
                "3",
                "--algorithmic-edge-prior-strength",
                "0.05",
                "--algorithmic-edge-prior-candidate-only",
                "--candidate-coverage-fraction",
                "0.08",
                "--use-task-salience",
                "--salience-mode",
                "class",
                "--algorithmic-evidence-top-k",
                "8",
                "--use-candidate-prior-admission",
                "--candidate-prior-admission-target",
                "coverage_feature",
                "--candidate-prior-admission-support-mode",
                "relative_evidence",
                "--candidate-prior-admission-floor",
                "0.05",
                "--candidate-prior-admission-threshold",
                "0.35",
                "--candidate-prior-admission-scale",
                "0.50",
            ),
        ),
    ]


def common_skab_flags(
    *,
    seeds: str,
    output_dir: Path,
    device: str,
    profile: str,
) -> list[str]:
    if profile == "smoke":
        hidden_dim = "16"
        window_size = "16"
        max_rows = "400"
        epochs = "1"
        batch_size = "128"
        graph_top_k = "4"
        max_paths = "8"
    elif profile == "quick":
        hidden_dim = "32"
        window_size = "32"
        max_rows = "2000"
        epochs = "3"
        batch_size = "256"
        graph_top_k = "6"
        max_paths = "12"
    else:
        hidden_dim = "64"
        window_size = "48"
        max_rows = "8000"
        epochs = "25"
        batch_size = "256"
        graph_top_k = "8"
        max_paths = "16"
    return [
        "Scripts\\run_public_ms_gse_rpf_experiment.py",
        "--dataset",
        "skab",
        "--variant",
        "full",
        "--seeds",
        str(seeds),
        "--output-dir",
        str(output_dir),
        "--device",
        str(device),
        "--hidden-dim",
        hidden_dim,
        "--window-size",
        window_size,
        "--max-rows-per-split",
        max_rows,
        "--epochs",
        epochs,
        "--batch-size",
        batch_size,
        "--graph-top-k",
        graph_top_k,
        "--max-paths",
        max_paths,
        "--forecast-weight",
        "0.05",
        "--graph-weight",
        "0.02",
        "--use-prototype-posterior-fusion",
        "--prototype-fusion-max-blend",
        "0.30",
        "--prototype-fusion-blend-steps",
        "7",
        "--prototype-fusion-temperature-grid",
        "0.25,0.50,1.00,2.00",
        "--prototype-fusion-min-val-gain",
        "0.003",
    ]


def build_command(
    spec: VariantSpec,
    *,
    output_root: Path,
    seeds: str = "42,43,44",
    device: str = "cuda",
    profile: str = "full",
    python_executable: str = "python",
) -> list[str]:
    output_dir = Path(output_root) / spec.name
    return [
        str(python_executable),
        "-B",
        *common_skab_flags(seeds=seeds, output_dir=output_dir, device=device, profile=profile),
        *spec.flags,
    ]


def render_shell_command(tokens: Sequence[str]) -> str:
    return " ".join(shlex.quote(str(token)) for token in tokens)


def _iter_result_files(result_dir: Path) -> list[Path]:
    root = Path(result_dir)
    files: list[Path] = []
    try:
        with os.scandir(_fs_path(root)) as entries:
            for entry in entries:
                if not entry.is_file():
                    continue
                name = str(entry.name)
                if name.startswith("ms_gse_rpf_") and "_seed" in name and name.endswith(".json"):
                    files.append(root / name)
    except FileNotFoundError:
        return []
    return sorted(files, key=lambda path: path.name)


def load_variant_runs(result_dir: Path) -> dict[int, dict[str, Any]]:
    rows: dict[int, dict[str, Any]] = {}
    for path in _iter_result_files(result_dir):
        with open(_fs_path(path), "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            continue
        payload["_path"] = str(path)
        rows[int(payload.get("seed", -1))] = payload
    return rows


def _metric(row: Mapping[str, Any], split: str, key: str = "macro_f1") -> float:
    if split == "val":
        metrics = row.get("thresholded_val_metrics") or row.get("val_metrics") or {}
    elif split == "test":
        metrics = row.get("primary_test_metrics") or row.get("test_metrics") or {}
    else:
        raise ValueError(f"Unknown split: {split}")
    return float(metrics.get(key, 0.0))


def _per_class_values(row: Mapping[str, Any], split: str, key: str = "f1") -> dict[str, float]:
    if split == "val":
        metrics = row.get("thresholded_val_metrics") or row.get("val_metrics") or {}
    elif split == "test":
        metrics = row.get("primary_test_metrics") or row.get("test_metrics") or {}
    else:
        raise ValueError(f"Unknown split: {split}")
    raw = metrics.get("per_class") or {}
    if not isinstance(raw, Mapping):
        return {}
    return {
        str(cls): float(payload.get(key, 0.0))
        for cls, payload in raw.items()
        if isinstance(payload, Mapping) and key in payload
    }


def _quantile(values: Sequence[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return float(ordered[0])
    clipped = min(1.0, max(0.0, float(q)))
    pos = clipped * (len(ordered) - 1)
    lo = int(pos)
    hi = min(len(ordered) - 1, lo + 1)
    frac = pos - lo
    return float((1.0 - frac) * ordered[lo] + frac * ordered[hi])


def _mean_std(values: Sequence[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    return float(mean(values)), float(pstdev(values))


def _group_path_set(rows: Mapping[int, Mapping[str, Any]], *, top_k: int = 10) -> set[str]:
    out: set[str] = set()
    for row in rows.values():
        for item in list(row.get("top_evidence_paths") or [])[: max(1, int(top_k))]:
            if not isinstance(item, Mapping):
                continue
            key = str(item.get("group_path") or item.get("path") or "")
            if not key:
                source = item.get("source")
                target = item.get("target")
                if source is not None and target is not None:
                    key = f"{source} -> {target}"
            if key:
                out.add(key)
    return out


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return float(len(a & b) / len(a | b))


def _source_complexity_stats(rows: Mapping[int, Mapping[str, Any]]) -> dict[str, Any]:
    candidate_counts: list[float] = []
    family_counts: list[float] = []
    disabled_flags: list[float] = []
    effective_llm_scales: list[float] = []
    for row in rows.values():
        evidence_prior = row.get("evidence_prior") if isinstance(row, Mapping) else {}
        if not isinstance(evidence_prior, Mapping):
            evidence_prior = {}
        external_candidate = evidence_prior.get("external_candidate_prior", {})
        if not isinstance(external_candidate, Mapping):
            external_candidate = {}
        edge_count = external_candidate.get("candidate_edge_count")
        if edge_count is not None:
            candidate_counts.append(float(edge_count))
        family_edges = external_candidate.get("family_edges", {})
        family_scales = external_candidate.get("family_scales", {})
        family_count = 0
        if isinstance(family_edges, Mapping):
            family_count = len([name for name, count in family_edges.items() if float(count or 0.0) > 0.0])
        if family_count == 0 and isinstance(family_scales, Mapping):
            family_count = len(family_scales)
        family_counts.append(float(family_count))
        source_penalty = external_candidate.get("source_complexity_penalty", {})
        if isinstance(source_penalty, Mapping):
            disabled_flags.append(1.0 if bool(source_penalty.get("disabled_for_ablation", False)) else 0.0)
            effective_scales = source_penalty.get("effective_scales", {})
            if isinstance(effective_scales, Mapping) and "llm" in effective_scales:
                effective_llm_scales.append(float(effective_scales.get("llm", 0.0)))
            continue
        config = row.get("diagnostics", {}).get("config", {}) if isinstance(row.get("diagnostics"), Mapping) else {}
        if isinstance(config, Mapping):
            disabled_flags.append(1.0 if bool(config.get("disable_source_complexity_penalty", False)) else 0.0)
            if "effective_external_candidate_llm_scale" in config:
                effective_llm_scales.append(float(config.get("effective_external_candidate_llm_scale", 0.0)))
    return {
        "mean_external_candidate_edges": float(mean(candidate_counts)) if candidate_counts else 0.0,
        "mean_external_source_families": float(mean(family_counts)) if family_counts else 0.0,
        "source_complexity_disabled_fraction": float(mean(disabled_flags)) if disabled_flags else 0.0,
        "mean_effective_llm_candidate_scale": float(mean(effective_llm_scales)) if effective_llm_scales else 0.0,
    }


def summarize_variant(
    spec: VariantSpec,
    rows: Mapping[int, Mapping[str, Any]],
    baseline_rows: Mapping[int, Mapping[str, Any]],
    *,
    expected_seeds: Sequence[int],
    min_mean_val_gain: float = 0.0,
    max_seed_val_drop: float = 0.01,
    max_low_tail_f1_drop: float = 0.02,
    low_tail_quantile: float = 0.10,
    min_baseline_path_jaccard: float = 0.0,
) -> dict[str, Any]:
    seeds = sorted(int(seed) for seed in rows)
    expected = [int(seed) for seed in expected_seeds]
    missing = [int(seed) for seed in expected if int(seed) not in rows]
    common = sorted(seed for seed in baseline_rows if seed in rows)
    val_values = [_metric(rows[seed], "val", "macro_f1") for seed in seeds]
    test_values = [_metric(rows[seed], "test", "macro_f1") for seed in seeds]
    bal_values = [_metric(rows[seed], "test", "balanced_accuracy") for seed in seeds]
    val_mean, val_std = _mean_std(val_values)
    test_mean, test_std = _mean_std(test_values)
    bal_mean, bal_std = _mean_std(bal_values)
    seed_val_gains = [
        float(_metric(rows[seed], "val", "macro_f1") - _metric(baseline_rows[seed], "val", "macro_f1"))
        for seed in common
    ]
    test_gains = [
        float(_metric(rows[seed], "test", "macro_f1") - _metric(baseline_rows[seed], "test", "macro_f1"))
        for seed in common
    ]
    low_tail_deltas: list[float] = []
    for seed in common:
        base_classes = _per_class_values(baseline_rows[seed], "val", "f1")
        cand_classes = _per_class_values(rows[seed], "val", "f1")
        for cls in sorted(set(base_classes) & set(cand_classes)):
            low_tail_deltas.append(float(cand_classes[cls] - base_classes[cls]))
    mean_val_gain = float(mean(seed_val_gains)) if seed_val_gains else 0.0
    min_seed_val_gain = float(min(seed_val_gains)) if seed_val_gains else 0.0
    mean_test_gain = float(mean(test_gains)) if test_gains else 0.0
    low_tail_gain = _quantile(low_tail_deltas, low_tail_quantile)
    path_jaccard = _jaccard(_group_path_set(baseline_rows), _group_path_set(rows))
    source_complexity = _source_complexity_stats(rows)
    is_baseline = spec.role == "baseline"
    has_all_expected = bool(expected) and all(seed in rows for seed in expected)
    admitted = (
        bool(common)
        and mean_val_gain >= float(min_mean_val_gain)
        and min_seed_val_gain >= -float(max_seed_val_drop)
        and low_tail_gain >= -float(max_low_tail_f1_drop)
        and path_jaccard >= float(min_baseline_path_jaccard)
    )
    if not rows:
        status = "missing"
    elif is_baseline:
        status = "baseline_complete" if has_all_expected else "baseline_partial"
    elif not has_all_expected:
        status = "partial"
    elif admitted:
        status = "admitted"
    else:
        status = "rejected"
    reject_reasons: list[str] = []
    if not rows:
        reject_reasons.append("no_runs")
    if not has_all_expected:
        reject_reasons.append("missing_expected_seeds")
    if not is_baseline and common and mean_val_gain < float(min_mean_val_gain):
        reject_reasons.append("mean_validation_gain_below_threshold")
    if not is_baseline and common and min_seed_val_gain < -float(max_seed_val_drop):
        reject_reasons.append("seed_level_validation_drop")
    if not is_baseline and common and low_tail_gain < -float(max_low_tail_f1_drop):
        reject_reasons.append("low_tail_class_harm")
    if not is_baseline and common and path_jaccard < float(min_baseline_path_jaccard):
        reject_reasons.append("path_overlap_below_threshold")
    return {
        "variant": spec.name,
        "role": spec.role,
        "claim": spec.claim,
        "status": status,
        "admitted": bool(admitted if not is_baseline else bool(rows)),
        "seeds": seeds,
        "missing_seeds": missing,
        "n_runs": int(len(rows)),
        "val_macro_f1_mean": val_mean,
        "val_macro_f1_std": val_std,
        "test_macro_f1_mean": test_mean,
        "test_macro_f1_std": test_std,
        "test_balanced_accuracy_mean": bal_mean,
        "test_balanced_accuracy_std": bal_std,
        "common_baseline_seeds": [int(seed) for seed in common],
        "mean_val_gain_vs_baseline": mean_val_gain,
        "min_seed_val_gain_vs_baseline": min_seed_val_gain,
        "mean_test_gain_vs_baseline": mean_test_gain,
        "low_tail_val_f1_gain": low_tail_gain,
        "low_tail_quantile": float(low_tail_quantile),
        "baseline_path_jaccard": path_jaccard,
        "source_complexity": source_complexity,
        "reject_reasons": reject_reasons,
        "certificate_thresholds": {
            "min_mean_val_gain": float(min_mean_val_gain),
            "max_seed_val_drop": float(max_seed_val_drop),
            "max_low_tail_f1_drop": float(max_low_tail_f1_drop),
            "min_baseline_path_jaccard": float(min_baseline_path_jaccard),
        },
    }


def summarize_matrix(
    *,
    output_root: Path,
    specs: Sequence[VariantSpec],
    expected_seeds: Sequence[int],
    baseline_name: str = "no_mechanism",
    min_mean_val_gain: float = 0.0,
    max_seed_val_drop: float = 0.01,
    max_low_tail_f1_drop: float = 0.02,
    min_baseline_path_jaccard: float = 0.0,
) -> list[dict[str, Any]]:
    loaded = {spec.name: load_variant_runs(Path(output_root) / spec.name) for spec in specs}
    baseline_rows = loaded.get(str(baseline_name), {})
    return [
        summarize_variant(
            spec,
            loaded.get(spec.name, {}),
            baseline_rows,
            expected_seeds=expected_seeds,
            min_mean_val_gain=min_mean_val_gain,
            max_seed_val_drop=max_seed_val_drop,
            max_low_tail_f1_drop=max_low_tail_f1_drop,
            min_baseline_path_jaccard=min_baseline_path_jaccard,
        )
        for spec in specs
    ]


def render_report(
    *,
    specs: Sequence[VariantSpec],
    commands: Mapping[str, Sequence[str]],
    summary: Sequence[Mapping[str, Any]],
    output_root: Path,
) -> str:
    lines: list[str] = []
    lines.append("# Mechanism Gate Ablation Matrix")
    lines.append("")
    lines.append(
        "This protocol isolates whether expert mechanism evidence helps because it is admitted by data-supported "
        "gates, rather than because raw edges are injected into the graph. Missing rows are not evidence."
    )
    lines.append("")
    lines.append(f"- output root: `{output_root}`")
    lines.append("- primary dataset: `SKAB`")
    lines.append("- certificate: validation gain, seed-level safety, low-tail F1 safety, and path-overlap diagnostics")
    lines.append("")
    lines.append("## Variants")
    lines.append("")
    lines.append("| Variant | Role | Claim | Command |")
    lines.append("|---|---|---|---|")
    spec_map = {spec.name: spec for spec in specs}
    for name, tokens in commands.items():
        spec = spec_map[name]
        lines.append(
            "| {name} | {role} | {claim} | `{cmd}` |".format(
                name=spec.name,
                role=spec.role,
                claim=spec.claim,
                cmd=render_shell_command(tokens),
            )
        )
    lines.append("")
    lines.append("## Current Evidence")
    lines.append("")
    lines.append("| Variant | Status | Runs | Test Macro-F1 | Val gain | Test gain | Low-tail val F1 gain | Path Jaccard | Source burden | Reject reasons |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---|---|")
    for row in summary:
        source_complexity = row.get("source_complexity", {}) if isinstance(row.get("source_complexity"), Mapping) else {}
        source_burden = (
            "edges={edges:.1f}; families={families:.1f}; disabled={disabled:.2f}; llm_scale={llm:.2f}".format(
                edges=float(source_complexity.get("mean_external_candidate_edges", 0.0)),
                families=float(source_complexity.get("mean_external_source_families", 0.0)),
                disabled=float(source_complexity.get("source_complexity_disabled_fraction", 0.0)),
                llm=float(source_complexity.get("mean_effective_llm_candidate_scale", 0.0)),
            )
        )
        lines.append(
            "| {variant} | {status} | {runs} | {test:.4f} +/- {test_std:.4f} | {vgain:.4f} | {tgain:.4f} | {tail:.4f} | {path:.4f} | {source_burden} | {reasons} |".format(
                variant=row.get("variant"),
                status=row.get("status"),
                runs=int(row.get("n_runs", 0)),
                test=float(row.get("test_macro_f1_mean", 0.0)),
                test_std=float(row.get("test_macro_f1_std", 0.0)),
                vgain=float(row.get("mean_val_gain_vs_baseline", 0.0)),
                tgain=float(row.get("mean_test_gain_vs_baseline", 0.0)),
                tail=float(row.get("low_tail_val_f1_gain", 0.0)),
                path=float(row.get("baseline_path_jaccard", 0.0)),
                source_burden=source_burden,
                reasons=", ".join(str(item) for item in row.get("reject_reasons", [])) or "none",
            )
        )
    lines.append("")
    lines.append("## Interpretation Rule")
    lines.append("")
    lines.append(
        "A mechanism-gating claim is paper-ready only if `expert_candidate_data_gate` or "
        "`expert_candidate_data_gate_consistency` is complete across the planned seeds, improves validation over "
        "`no_mechanism`, does not harm low-tail validation F1 beyond the threshold, and is better than "
        "`raw_expert_graph` or `expert_candidate_no_gate` under the same protocol."
    )
    lines.append("")
    return "\n".join(lines)


def write_outputs(output_dir: Path, payload: Mapping[str, Any], report: str) -> tuple[Path, Path]:
    Path(_fs_path(output_dir)).mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "mechanism_gate_ablation_matrix.json"
    md_path = output_dir / "mechanism_gate_ablation_matrix.md"
    with open(_fs_path(json_path), "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    with open(_fs_path(md_path), "w", encoding="utf-8") as handle:
        handle.write(report)
    return json_path, md_path


def parse_seeds(text: str) -> list[int]:
    return [int(part.strip()) for part in str(text).split(",") if part.strip()]


def filter_specs(specs: Sequence[VariantSpec], variants: str | Sequence[str] | None) -> list[VariantSpec]:
    if variants is None:
        return list(specs)
    if isinstance(variants, str):
        requested = {part.strip() for part in variants.replace(";", ",").split(",") if part.strip()}
    else:
        requested = {str(part).strip() for part in variants if str(part).strip()}
    if not requested:
        return list(specs)
    known = {spec.name for spec in specs}
    missing = sorted(requested - known)
    if missing:
        raise ValueError(f"Unknown mechanism-gate variant(s): {', '.join(missing)}")
    return [spec for spec in specs if spec.name in requested]


def variant_has_expected_runs(output_root: Path, variant_name: str, expected_seeds: Sequence[int]) -> bool:
    rows = load_variant_runs(Path(output_root) / str(variant_name))
    if not expected_seeds:
        return bool(rows)
    return all(int(seed) in rows for seed in expected_seeds)


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build and optionally execute the SKAB mechanism-gate ablation matrix.")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--seeds", type=str, default="42,43,44")
    parser.add_argument(
        "--variants",
        type=str,
        default="",
        help="Optional comma-separated subset of variants to build/execute.",
    )
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--profile", choices=["smoke", "quick", "full"], default="full")
    parser.add_argument("--python", type=str, default="python")
    parser.add_argument("--execute", action="store_true", help="Run every matrix command after writing the protocol.")
    parser.add_argument(
        "--skip-complete",
        action="store_true",
        help="When executing, skip a variant if all requested seed result JSON files already exist.",
    )
    parser.add_argument("--min-mean-val-gain", type=float, default=0.0)
    parser.add_argument("--max-seed-val-drop", type=float, default=0.01)
    parser.add_argument("--max-low-tail-f1-drop", type=float, default=0.02)
    parser.add_argument("--min-baseline-path-jaccard", type=float, default=0.0)
    args = parser.parse_args(list(argv) if argv is not None else None)

    specs = filter_specs(skab_variant_specs(), args.variants)
    commands = {
        spec.name: build_command(
            spec,
            output_root=args.output_root,
            seeds=args.seeds,
            device=args.device,
            profile=args.profile,
            python_executable=args.python,
        )
        for spec in specs
    }
    expected_seeds = parse_seeds(args.seeds)
    if bool(args.execute):
        for name, tokens in commands.items():
            if bool(args.skip_complete) and variant_has_expected_runs(args.output_root, name, expected_seeds):
                print(f"[mechanism-gate] skipping complete variant {name}", flush=True)
                continue
            print(f"[mechanism-gate] running {name}: {render_shell_command(tokens)}", flush=True)
            subprocess.run(list(tokens), cwd=PROJECT_ROOT, check=True)
    summary = summarize_matrix(
        output_root=args.output_root,
        specs=specs,
        expected_seeds=expected_seeds,
        min_mean_val_gain=float(args.min_mean_val_gain),
        max_seed_val_drop=float(args.max_seed_val_drop),
        max_low_tail_f1_drop=float(args.max_low_tail_f1_drop),
        min_baseline_path_jaccard=float(args.min_baseline_path_jaccard),
    )
    payload = {
        "schema": "mechanism_gate_ablation_matrix_v1",
        "output_root": str(args.output_root),
        "profile": str(args.profile),
        "seeds": expected_seeds,
        "skip_complete": bool(args.skip_complete),
        "commands": {name: list(tokens) for name, tokens in commands.items()},
        "variants": [spec.__dict__ for spec in specs],
        "summary": summary,
    }
    report = render_report(specs=specs, commands=commands, summary=summary, output_root=args.output_root)
    json_path, md_path = write_outputs(args.report_dir, payload, report)
    print(report)
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
