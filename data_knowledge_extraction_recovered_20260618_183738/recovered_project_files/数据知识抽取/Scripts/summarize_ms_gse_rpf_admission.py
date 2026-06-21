from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Mapping, Sequence

from summarize_ms_gse_rpf_results import aggregate


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RESULT_DIR = PROJECT_ROOT / "knowledge_exports" / "ms_gse_rpf"


def _fs_path(path: Path) -> str:
    if os.name == "nt":
        resolved = str(Path(path).resolve())
        if not resolved.startswith("\\\\?\\"):
            return "\\\\?\\" + resolved
    return str(path)


def _read_json(path: Path) -> dict[str, Any]:
    with open(_fs_path(path), "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    payload["_path"] = str(path)
    return payload


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
    return sorted(files, key=lambda item: item.name)


def _metric(row: Mapping[str, Any], split: str, key: str = "macro_f1") -> float:
    if split == "val":
        metrics = row.get("thresholded_val_metrics") or row.get("val_metrics") or {}
    elif split == "test":
        metrics = row.get("primary_test_metrics") or row.get("test_metrics") or {}
    else:
        raise ValueError(f"Unknown split: {split}")
    return float(metrics.get(key, 0.0))


def _load_rows_from_dir(
    result_dir: Path,
    *,
    dataset: str,
    target: str,
    variant: str,
    filename_contains: str,
    n_rows_total: int | None,
    candidate_name: str,
) -> dict[int, dict[str, Any]]:
    rows: dict[int, dict[str, Any]] = {}
    file_filter = "" if str(filename_contains).strip().lower() in {"", "__all__", "*", "all"} else str(filename_contains)
    for path in _iter_result_files(result_dir):
        if file_filter and file_filter not in path.name:
            continue
        row = _read_json(path)
        if str(row.get("dataset")) != str(dataset):
            continue
        if str(row.get("target")) != str(target):
            continue
        if str(row.get("variant")) != str(variant):
            continue
        if n_rows_total is not None and int(row.get("n_rows_total", -1)) != int(n_rows_total):
            continue
        seed = int(row.get("seed"))
        row["_candidate"] = str(candidate_name)
        rows[seed] = row
    return rows


def _parse_candidate(text: str) -> tuple[str, Path]:
    if "=" not in str(text):
        path = Path(text)
        return path.name, path
    name, value = str(text).split("=", 1)
    return name.strip(), Path(value.strip())


def _parse_penalty(text: str) -> tuple[str, float]:
    if "=" not in str(text):
        raise ValueError("Candidate penalty must use name=value format.")
    name, value = str(text).split("=", 1)
    return name.strip(), float(value)


def _candidate_source_family(name: str) -> str:
    key = str(name or "baseline").strip().lower()
    if key == "baseline":
        return "baseline"
    if "llm" in key:
        return "llm"
    if "expert" in key:
        return "expert"
    if (
        key.startswith("alg")
        or "algorithm" in key
        or "edge" in key
        or "path" in key
        or "class" in key
        or "blend" in key
        or "salience" in key
        or "static" in key
        or "lag" in key
        or "multihop" in key
    ):
        return "algorithmic"
    return "other"


def select_admitted_runs(
    baseline_rows: Mapping[int, Mapping[str, Any]],
    candidate_sets: Mapping[str, Mapping[int, Mapping[str, Any]]],
    *,
    min_val_gain: float = 0.0,
    metric_key: str = "macro_f1",
    candidate_penalties: Mapping[str, float] | None = None,
    candidate_stability_scores: Mapping[str, float] | None = None,
    stability_bonus_weight: float = 0.0,
    candidate_path_overlap_scores: Mapping[str, float] | None = None,
    path_disruption_penalty_weight: float = 0.0,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    admitted: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    penalties = {str(key): float(value) for key, value in dict(candidate_penalties or {}).items()}
    stability_scores = {str(key): float(value) for key, value in dict(candidate_stability_scores or {}).items()}
    path_overlap_scores = {str(key): float(value) for key, value in dict(candidate_path_overlap_scores or {}).items()}
    stability_weight = max(0.0, float(stability_bonus_weight))
    path_disruption_weight = max(0.0, float(path_disruption_penalty_weight))
    for seed in sorted(baseline_rows):
        baseline = dict(baseline_rows[seed])
        baseline["_candidate"] = str(baseline.get("_candidate", "baseline"))
        base_val = _metric(baseline, "val", metric_key)
        base_stability = float(stability_scores.get("baseline", 0.0))
        base_path_overlap = float(path_overlap_scores.get("baseline", 1.0))
        base_path_disruption_penalty = float(path_disruption_weight * max(0.0, 1.0 - base_path_overlap))
        base_adjusted = float(base_val + stability_weight * base_stability - base_path_disruption_penalty)
        best = baseline
        best_val = base_val
        best_score = base_adjusted
        considered = [
            {
                "candidate": str(baseline.get("_candidate", "baseline")),
                "val_metric": float(base_val),
                "candidate_penalty": 0.0,
                "stability_score": float(base_stability),
                "stability_bonus_weight": float(stability_weight),
                "stability_bonus": float(stability_weight * base_stability),
                "baseline_path_jaccard": float(base_path_overlap),
                "path_disruption_penalty_weight": float(path_disruption_weight),
                "path_disruption_penalty": float(base_path_disruption_penalty),
                "adjusted_val_metric": float(base_adjusted),
                "test_macro_f1": _metric(baseline, "test", "macro_f1"),
                "selected": False,
            }
        ]
        for name, rows in sorted(candidate_sets.items()):
            if seed not in rows:
                continue
            row = dict(rows[seed])
            row["_candidate"] = str(row.get("_candidate", name))
            val_metric = _metric(row, "val", metric_key)
            penalty = float(penalties.get(str(name), 0.0))
            stability = float(stability_scores.get(str(name), 0.0))
            stability_bonus = float(stability_weight * stability)
            path_overlap = float(path_overlap_scores.get(str(name), 0.0))
            path_disruption_penalty = float(path_disruption_weight * max(0.0, 1.0 - path_overlap))
            adjusted_val = float(val_metric - penalty + stability_bonus - path_disruption_penalty)
            considered.append(
                {
                    "candidate": str(name),
                    "val_metric": float(val_metric),
                    "candidate_penalty": penalty,
                    "stability_score": stability,
                    "stability_bonus_weight": float(stability_weight),
                    "stability_bonus": stability_bonus,
                    "baseline_path_jaccard": float(path_overlap),
                    "path_disruption_penalty_weight": float(path_disruption_weight),
                    "path_disruption_penalty": path_disruption_penalty,
                    "adjusted_val_metric": adjusted_val,
                    "test_macro_f1": _metric(row, "test", "macro_f1"),
                    "selected": False,
                }
            )
            if adjusted_val >= base_adjusted + float(min_val_gain) and adjusted_val > best_score:
                best = row
                best_val = float(val_metric)
                best_score = adjusted_val
        admitted.append(best)
        for item in considered:
            item["selected"] = item["candidate"] == str(best.get("_candidate", "baseline"))
            item["source_family"] = _candidate_source_family(str(item["candidate"]))
        decisions.append(
            {
                "seed": int(seed),
                "baseline_val_metric": float(base_val),
                "selected_candidate": str(best.get("_candidate", "baseline")),
                "selected_source_family": _candidate_source_family(str(best.get("_candidate", "baseline"))),
                "selected_val_metric": float(best_val),
                "selected_adjusted_val_metric": float(best_score),
                "selected_test_macro_f1": _metric(best, "test", "macro_f1"),
                "selected_test_balanced_accuracy": _metric(best, "test", "balanced_accuracy"),
                "considered": considered,
            }
        )
    return [dict(row) for row in admitted], decisions


def _mean_std(values: Sequence[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    return float(mean(values)), float(pstdev(values))


def _candidate_stability_scores(candidate_sets: Mapping[str, Mapping[int, Mapping[str, Any]]]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for name, rows in candidate_sets.items():
        if len(rows) < 2:
            scores[str(name)] = 0.0
            continue
        try:
            summary = aggregate([dict(row) for row in rows.values()])
        except Exception:
            scores[str(name)] = 0.0
            continue
        if not summary:
            scores[str(name)] = 0.0
            continue
        value = summary[0].get("top10_group_path_jaccard", summary[0].get("top10_path_jaccard", 0.0))
        scores[str(name)] = float(value or 0.0)
    return scores


def _row_group_path_set(row: Mapping[str, Any], *, top_k: int = 10) -> set[str]:
    paths: set[str] = set()
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
            paths.add(key)
    return paths


def _rows_group_path_set(rows: Mapping[int, Mapping[str, Any]], *, top_k: int = 10) -> set[str]:
    combined: set[str] = set()
    for row in rows.values():
        combined.update(_row_group_path_set(row, top_k=top_k))
    return combined


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    return float(len(left & right) / max(1, len(left | right)))


def _candidate_baseline_path_overlap_scores(
    baseline_rows: Mapping[int, Mapping[str, Any]],
    candidate_sets: Mapping[str, Mapping[int, Mapping[str, Any]]],
    *,
    top_k: int = 10,
) -> dict[str, float]:
    baseline_paths = _rows_group_path_set(baseline_rows, top_k=top_k)
    scores = {"baseline": 1.0}
    for name, rows in candidate_sets.items():
        scores[str(name)] = _jaccard(baseline_paths, _rows_group_path_set(rows, top_k=top_k))
    return scores


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
    values: dict[str, float] = {}
    for cls, payload in raw.items():
        if isinstance(payload, Mapping) and key in payload:
            values[str(cls)] = float(payload.get(key, 0.0))
    return values


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


def build_candidate_certificates(
    baseline_rows: Mapping[int, Mapping[str, Any]],
    candidate_sets: Mapping[str, Mapping[int, Mapping[str, Any]]],
    *,
    metric_key: str = "macro_f1",
    candidate_penalties: Mapping[str, float] | None = None,
    candidate_stability_scores: Mapping[str, float] | None = None,
    stability_bonus_weight: float = 0.0,
    candidate_path_overlap_scores: Mapping[str, float] | None = None,
    path_disruption_penalty_weight: float = 0.0,
    min_mean_val_gain: float = 0.0,
    max_seed_val_drop: float = 0.0,
    max_low_tail_f1_drop: float = 0.02,
    low_tail_quantile: float = 0.10,
    min_baseline_path_jaccard: float = 0.0,
) -> dict[str, dict[str, Any]]:
    penalties = {str(key): float(value) for key, value in dict(candidate_penalties or {}).items()}
    stability_scores = {str(key): float(value) for key, value in dict(candidate_stability_scores or {}).items()}
    path_overlap_scores = {str(key): float(value) for key, value in dict(candidate_path_overlap_scores or {}).items()}
    path_disruption_weight = max(0.0, float(path_disruption_penalty_weight))
    certificates: dict[str, dict[str, Any]] = {}
    for name, rows in sorted(candidate_sets.items()):
        common_seeds = sorted(seed for seed in baseline_rows if seed in rows)
        seed_val_gains: list[float] = []
        low_tail_deltas: list[float] = []
        class_delta_count = 0
        for seed in common_seeds:
            baseline = baseline_rows[seed]
            candidate = rows[seed]
            seed_val_gains.append(_metric(candidate, "val", metric_key) - _metric(baseline, "val", metric_key))
            base_classes = _per_class_values(baseline, "val", "f1")
            cand_classes = _per_class_values(candidate, "val", "f1")
            shared_classes = sorted(set(base_classes) & set(cand_classes))
            class_delta_count += len(shared_classes)
            for cls in shared_classes:
                low_tail_deltas.append(float(cand_classes[cls] - base_classes[cls]))
        mean_gain = float(mean(seed_val_gains)) if seed_val_gains else 0.0
        min_seed_gain = float(min(seed_val_gains)) if seed_val_gains else 0.0
        tail_gain = _quantile(low_tail_deltas, float(low_tail_quantile)) if low_tail_deltas else 0.0
        penalty = float(penalties.get(str(name), 0.0))
        stability = float(stability_scores.get(str(name), 0.0))
        path_overlap = float(path_overlap_scores.get(str(name), 0.0))
        path_disruption_penalty = float(path_disruption_weight * max(0.0, 1.0 - path_overlap))
        score = float(mean_gain - penalty + max(0.0, float(stability_bonus_weight)) * stability - path_disruption_penalty)
        admitted = (
            bool(common_seeds)
            and mean_gain >= float(min_mean_val_gain)
            and min_seed_gain >= -float(max_seed_val_drop)
            and tail_gain >= -float(max_low_tail_f1_drop)
            and path_overlap >= float(min_baseline_path_jaccard)
        )
        reasons: list[str] = []
        if not common_seeds:
            reasons.append("no_common_seed")
        if mean_gain < float(min_mean_val_gain):
            reasons.append("mean_validation_gain_below_threshold")
        if min_seed_gain < -float(max_seed_val_drop):
            reasons.append("seed_level_validation_drop")
        if tail_gain < -float(max_low_tail_f1_drop):
            reasons.append("low_tail_class_harm")
        if path_overlap < float(min_baseline_path_jaccard):
            reasons.append("baseline_path_overlap_below_threshold")
        certificates[str(name)] = {
            "candidate": str(name),
            "source_family": _candidate_source_family(str(name)),
            "common_seeds": [int(seed) for seed in common_seeds],
            "n_common_seeds": int(len(common_seeds)),
            "mean_val_gain": mean_gain,
            "min_seed_val_gain": min_seed_gain,
            "low_tail_val_f1_gain": tail_gain,
            "low_tail_quantile": float(low_tail_quantile),
            "class_delta_count": int(class_delta_count),
            "candidate_penalty": penalty,
            "stability_score": stability,
            "stability_bonus_weight": float(stability_bonus_weight),
            "baseline_path_jaccard": path_overlap,
            "path_disruption_penalty_weight": float(path_disruption_weight),
            "path_disruption_penalty": path_disruption_penalty,
            "certificate_score": score,
            "admitted": bool(admitted),
            "reject_reasons": reasons,
            "thresholds": {
                "min_mean_val_gain": float(min_mean_val_gain),
                "max_seed_val_drop": float(max_seed_val_drop),
                "max_low_tail_f1_drop": float(max_low_tail_f1_drop),
                "min_baseline_path_jaccard": float(min_baseline_path_jaccard),
            },
        }
    return certificates


def build_admission_report(
    *,
    baseline_dir: Path,
    candidates: Sequence[tuple[str, Path]],
    dataset: str,
    target: str,
    variant: str,
    filename_contains: str,
    n_rows_total: int | None,
    min_val_gain: float,
    metric_key: str,
    candidate_penalties: Mapping[str, float] | None = None,
    stability_bonus_weight: float = 0.0,
    path_disruption_penalty_weight: float = 0.0,
    path_overlap_top_k: int = 10,
    require_candidate_certificate: bool = False,
    certificate_min_mean_val_gain: float = 0.0,
    certificate_max_seed_val_drop: float = 0.0,
    certificate_max_low_tail_f1_drop: float = 0.02,
    certificate_low_tail_quantile: float = 0.10,
    certificate_min_baseline_path_jaccard: float = 0.0,
) -> dict[str, Any]:
    baseline_rows = _load_rows_from_dir(
        baseline_dir,
        dataset=dataset,
        target=target,
        variant=variant,
        filename_contains=filename_contains,
        n_rows_total=n_rows_total,
        candidate_name="baseline",
    )
    candidate_sets = {
        name: _load_rows_from_dir(
            path,
            dataset=dataset,
            target=target,
            variant=variant,
            filename_contains=filename_contains,
            n_rows_total=n_rows_total,
            candidate_name=name,
        )
        for name, path in candidates
    }
    stability_scores = _candidate_stability_scores({"baseline": baseline_rows, **candidate_sets})
    path_overlap_scores = _candidate_baseline_path_overlap_scores(
        baseline_rows,
        candidate_sets,
        top_k=int(path_overlap_top_k),
    )
    candidate_certificates = build_candidate_certificates(
        baseline_rows,
        candidate_sets,
        metric_key=metric_key,
        candidate_penalties=candidate_penalties,
        candidate_stability_scores=stability_scores,
        stability_bonus_weight=stability_bonus_weight,
        candidate_path_overlap_scores=path_overlap_scores,
        path_disruption_penalty_weight=path_disruption_penalty_weight,
        min_mean_val_gain=certificate_min_mean_val_gain,
        max_seed_val_drop=certificate_max_seed_val_drop,
        max_low_tail_f1_drop=certificate_max_low_tail_f1_drop,
        low_tail_quantile=certificate_low_tail_quantile,
        min_baseline_path_jaccard=certificate_min_baseline_path_jaccard,
    )
    selectable_candidate_sets = {
        name: rows
        for name, rows in candidate_sets.items()
        if (not bool(require_candidate_certificate)) or bool(candidate_certificates.get(str(name), {}).get("admitted", False))
    }
    admitted, decisions = select_admitted_runs(
        baseline_rows,
        selectable_candidate_sets,
        min_val_gain=min_val_gain,
        metric_key=metric_key,
        candidate_penalties=candidate_penalties,
        candidate_stability_scores=stability_scores,
        stability_bonus_weight=stability_bonus_weight,
        candidate_path_overlap_scores=path_overlap_scores,
        path_disruption_penalty_weight=path_disruption_penalty_weight,
    )
    admitted_payloads: list[dict[str, Any]] = []
    decisions_by_seed = {int(item["seed"]): item for item in decisions}
    for row in admitted:
        seed = int(row.get("seed"))
        payload = {key: value for key, value in dict(row).items() if not str(key).startswith("_")}
        payload["variant"] = f"{payload.get('variant')}_admitted"
        payload["admission"] = {
            "schema": "ms_gse_rpf_validation_admission_decision_v1",
            "selected_candidate": str(row.get("_candidate", "baseline")),
            "source_result_path": str(row.get("_path", "")),
            "selection_metric": str(metric_key),
            "min_val_gain": float(min_val_gain),
            "candidate_penalties": {str(key): float(value) for key, value in dict(candidate_penalties or {}).items()},
            "candidate_stability_scores": stability_scores,
            "stability_bonus_weight": float(stability_bonus_weight),
            "candidate_baseline_path_jaccard": path_overlap_scores,
            "path_overlap_top_k": int(path_overlap_top_k),
            "path_disruption_penalty_weight": float(path_disruption_penalty_weight),
            "require_candidate_certificate": bool(require_candidate_certificate),
            "candidate_certificate": candidate_certificates.get(str(row.get("_candidate", "baseline")), {}),
            "decision": decisions_by_seed.get(seed, {}),
        }
        admitted_payloads.append(payload)
    macro, macro_std = _mean_std([_metric(row, "test", "macro_f1") for row in admitted])
    bal, bal_std = _mean_std([_metric(row, "test", "balanced_accuracy") for row in admitted])
    speed, speed_std = _mean_std(
        [float((row.get("efficiency") or {}).get("test_inference_samples_per_second", 0.0)) for row in admitted]
    )
    salience_mass, salience_mass_std = _mean_std(
        [
            float((((row.get("diagnostics") or {}).get("test_diagnostics") or {}).get("mean_path_salience_weight")) or 0.0)
            for row in admitted
        ]
    )
    aggregate_summary = aggregate(admitted_payloads)
    selected_candidates: dict[str, int] = {}
    selected_families: dict[str, int] = {}
    for decision in decisions:
        candidate = str(decision.get("selected_candidate", "baseline"))
        family = str(decision.get("selected_source_family", _candidate_source_family(candidate)))
        selected_candidates[candidate] = selected_candidates.get(candidate, 0) + 1
        selected_families[family] = selected_families.get(family, 0) + 1
    return {
        "schema": "ms_gse_rpf_validation_admission_v1",
        "dataset": str(dataset),
        "target": str(target),
        "variant": str(variant),
        "selection_metric": str(metric_key),
        "min_val_gain": float(min_val_gain),
        "baseline_dir": str(baseline_dir),
        "candidate_dirs": {name: str(path) for name, path in candidates},
        "candidate_penalties": {str(key): float(value) for key, value in dict(candidate_penalties or {}).items()},
        "candidate_stability_scores": stability_scores,
        "stability_bonus_weight": float(stability_bonus_weight),
        "candidate_baseline_path_jaccard": path_overlap_scores,
        "path_overlap_top_k": int(path_overlap_top_k),
        "path_disruption_penalty_weight": float(path_disruption_penalty_weight),
        "require_candidate_certificate": bool(require_candidate_certificate),
        "candidate_certificates": candidate_certificates,
        "selected_candidate_counts": selected_candidates,
        "selected_source_family_counts": selected_families,
        "n_admitted_runs": int(len(admitted)),
        "summary": {
            "macro_f1_mean": macro,
            "macro_f1_std": macro_std,
            "balanced_accuracy_mean": bal,
            "balanced_accuracy_std": bal_std,
            "inference_samples_per_second_mean": speed,
            "inference_samples_per_second_std": speed_std,
            "salience_mass_mean": salience_mass,
            "salience_mass_std": salience_mass_std,
            "aggregate": aggregate_summary,
        },
        "decisions": decisions,
        "admitted_runs": admitted_payloads,
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    summary = report.get("summary") or {}
    aggregate_summary = list(summary.get("aggregate") or [])
    agg = aggregate_summary[0] if aggregate_summary else {}
    lines = [
        "# MS-GSE + RPF Validation Admission",
        "",
        f"- dataset: {report.get('dataset')}",
        f"- target: {report.get('target')}",
        f"- selection metric: validation {report.get('selection_metric')}",
        f"- min validation gain: {float(report.get('min_val_gain', 0.0)):.4f}",
        f"- candidate penalties: {report.get('candidate_penalties') or {}}",
        f"- stability bonus weight: {float(report.get('stability_bonus_weight', 0.0)):.4f}",
        f"- candidate stability scores: {report.get('candidate_stability_scores') or {}}",
        f"- require candidate certificate: {bool(report.get('require_candidate_certificate', False))}",
        f"- candidate baseline path Jaccard: {report.get('candidate_baseline_path_jaccard') or {}}",
        f"- path disruption penalty weight: {float(report.get('path_disruption_penalty_weight', 0.0)):.4f}",
        f"- selected candidate counts: {report.get('selected_candidate_counts') or {}}",
        f"- selected source-family counts: {report.get('selected_source_family_counts') or {}}",
        "",
        "| Runs | Macro-F1 | Balanced Acc. | Group Path Jaccard | Salience mass | Inference/s |",
        "|---:|---:|---:|---:|---:|---:|",
        "| {runs} | {macro:.4f} +/- {macro_std:.4f} | {bal:.4f} +/- {bal_std:.4f} | {group_jaccard} | {sal:.4f} +/- {sal_std:.4f} | {speed:.1f} |".format(
            runs=int(report.get("n_admitted_runs", 0)),
            macro=float(summary.get("macro_f1_mean", 0.0)),
            macro_std=float(summary.get("macro_f1_std", 0.0)),
            bal=float(summary.get("balanced_accuracy_mean", 0.0)),
            bal_std=float(summary.get("balanced_accuracy_std", 0.0)),
            group_jaccard="n/a"
            if agg.get("top10_group_path_jaccard") is None
            else f"{float(agg.get('top10_group_path_jaccard')):.4f}",
            sal=float(summary.get("salience_mass_mean", 0.0)),
            sal_std=float(summary.get("salience_mass_std", 0.0)),
            speed=float(summary.get("inference_samples_per_second_mean", 0.0)),
        ),
        "",
        "## Seed Decisions",
        "",
        "| Seed | Selected | Val metric | Test Macro-F1 | Test Bal. Acc. | Considered |",
        "|---:|---|---:|---:|---:|---|",
    ]
    certificates = dict(report.get("candidate_certificates") or {})
    if certificates:
        lines[-4:-4] = [
            "## Candidate Certificates",
            "",
            "| Candidate | Family | Admit | Mean Val Gain | Min Seed Gain | Low-Tail Class F1 Gain | Path Jaccard | Common Seeds | Reject Reasons |",
            "|---|---|---:|---:|---:|---:|---:|---:|---|",
        ]
        insert_at = lines.index("## Seed Decisions")
        certificate_lines: list[str] = []
        for name, cert in sorted(certificates.items()):
            reasons = ", ".join(str(item) for item in cert.get("reject_reasons", [])) or "-"
            certificate_lines.append(
                "| {candidate} | {family} | {admit} | {mean_gain:.4f} | {min_seed:.4f} | {tail_gain:.4f} | {path_jaccard:.4f} | {seeds} | {reasons} |".format(
                    candidate=name,
                    family=cert.get("source_family", _candidate_source_family(name)),
                    admit="yes" if bool(cert.get("admitted", False)) else "no",
                    mean_gain=float(cert.get("mean_val_gain", 0.0)),
                    min_seed=float(cert.get("min_seed_val_gain", 0.0)),
                    tail_gain=float(cert.get("low_tail_val_f1_gain", 0.0)),
                    path_jaccard=float(cert.get("baseline_path_jaccard", 0.0)),
                    seeds=int(cert.get("n_common_seeds", 0)),
                    reasons=reasons,
                )
            )
        lines[insert_at:insert_at] = certificate_lines + [""]
    for decision in report.get("decisions") or []:
        considered = ", ".join(
            f"{item['candidate']}={float(item['val_metric']):.4f}"
            + (
                f"->adj{float(item.get('adjusted_val_metric', item['val_metric'])):.4f}"
                if (
                    float(item.get("candidate_penalty", 0.0)) > 0.0
                    or float(item.get("stability_bonus", 0.0)) > 0.0
                    or float(item.get("path_disruption_penalty", 0.0)) > 0.0
                )
                else ""
            )
            for item in decision.get("considered", [])
        )
        lines.append(
            "| {seed} | {selected} | {val:.4f} | {macro:.4f} | {bal:.4f} | {considered} |".format(
                seed=int(decision.get("seed")),
                selected=decision.get("selected_candidate"),
                val=float(decision.get("selected_val_metric", 0.0)),
                macro=float(decision.get("selected_test_macro_f1", 0.0)),
                bal=float(decision.get("selected_test_balanced_accuracy", 0.0)),
                considered=considered,
            )
        )
    lines.append("")
    return "\n".join(lines)


def _write_selected_runs(report: Mapping[str, Any], output_dir: Path) -> list[Path]:
    selected_dir = output_dir / "selected_runs"
    os.makedirs(_fs_path(selected_dir), exist_ok=True)
    written: list[Path] = []
    for row in report.get("admitted_runs") or []:
        dataset = str(row.get("dataset", "dataset"))
        target = str(row.get("target", "target"))
        variant = str(row.get("variant", "full_admitted"))
        seed = int(row.get("seed", 0))
        path = selected_dir / f"ms_gse_rpf_{dataset}_{target}_{variant}_prior-admitted_seed{seed}.json"
        with open(_fs_path(path), "w", encoding="utf-8") as handle:
            json.dump(dict(row), handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        written.append(path)
    return written


def write_report(report: Mapping[str, Any], output_dir: Path, *, write_selected_runs: bool = True) -> list[Path]:
    os.makedirs(_fs_path(output_dir), exist_ok=True)
    json_path = output_dir / "ms_gse_rpf_validation_admission.json"
    md_path = output_dir / "ms_gse_rpf_validation_admission.md"
    with open(_fs_path(json_path), "w", encoding="utf-8") as handle:
        json.dump(dict(report), handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    with open(_fs_path(md_path), "w", encoding="utf-8") as handle:
        handle.write(render_markdown(report))
    written = [json_path, md_path]
    if bool(write_selected_runs):
        written.extend(_write_selected_runs(report, output_dir))
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Select MS-GSE + RPF candidate runs by validation admission.")
    parser.add_argument("--baseline-dir", type=Path, default=DEFAULT_RESULT_DIR)
    parser.add_argument("--candidate", action="append", default=[], help="Candidate in name=dir form. Can be repeated.")
    parser.add_argument("--candidate-penalty", action="append", default=[], help="Candidate source-burden penalty in name=value form.")
    parser.add_argument("--dataset", default="hydraulic")
    parser.add_argument("--target", default="valve")
    parser.add_argument("--variant", default="full")
    parser.add_argument("--filename-contains", default="prior-none", help="Filename substring filter; use __all__ to disable.")
    parser.add_argument("--n-rows-total", type=int, default=None)
    parser.add_argument("--min-val-gain", type=float, default=0.0)
    parser.add_argument("--metric", default="macro_f1")
    parser.add_argument(
        "--stability-bonus-weight",
        type=float,
        default=0.0,
        help="Add weight * top10 group-path Jaccard as a candidate-level stability bonus in the validation admission score.",
    )
    parser.add_argument(
        "--path-overlap-top-k",
        type=int,
        default=10,
        help="Top-k evidence paths per run used to measure candidate overlap with baseline explanations.",
    )
    parser.add_argument(
        "--path-disruption-penalty-weight",
        type=float,
        default=0.0,
        help="Subtract weight * (1 - baseline path Jaccard) from candidate validation admission score.",
    )
    parser.add_argument(
        "--require-candidate-certificate",
        action="store_true",
        help="Filter candidates by a validation certificate before per-seed admission.",
    )
    parser.add_argument(
        "--certificate-min-mean-val-gain",
        type=float,
        default=0.0,
        help="Minimum mean validation gain over common seeds required by the candidate certificate.",
    )
    parser.add_argument(
        "--certificate-max-seed-val-drop",
        type=float,
        default=0.0,
        help="Maximum allowed validation drop on any common seed for the candidate certificate.",
    )
    parser.add_argument(
        "--certificate-max-low-tail-f1-drop",
        type=float,
        default=0.02,
        help="Maximum allowed low-tail per-class validation F1 drop for the candidate certificate.",
    )
    parser.add_argument(
        "--certificate-low-tail-quantile",
        type=float,
        default=0.10,
        help="Quantile used for low-tail per-class validation F1 certificate.",
    )
    parser.add_argument(
        "--certificate-min-baseline-path-jaccard",
        type=float,
        default=0.0,
        help="Minimum candidate-vs-baseline top-path Jaccard required by the candidate certificate.",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RESULT_DIR / "validation_admission")
    parser.add_argument("--no-selected-runs", action="store_true", help="Do not materialize selected admitted run JSON files.")
    args = parser.parse_args()

    report = build_admission_report(
        baseline_dir=Path(args.baseline_dir),
        candidates=[_parse_candidate(text) for text in args.candidate],
        dataset=str(args.dataset),
        target=str(args.target),
        variant=str(args.variant),
        filename_contains=str(args.filename_contains),
        n_rows_total=args.n_rows_total,
        min_val_gain=float(args.min_val_gain),
        metric_key=str(args.metric),
        candidate_penalties=dict(_parse_penalty(text) for text in args.candidate_penalty),
        stability_bonus_weight=float(args.stability_bonus_weight),
        path_disruption_penalty_weight=float(args.path_disruption_penalty_weight),
        path_overlap_top_k=int(args.path_overlap_top_k),
        require_candidate_certificate=bool(args.require_candidate_certificate),
        certificate_min_mean_val_gain=float(args.certificate_min_mean_val_gain),
        certificate_max_seed_val_drop=float(args.certificate_max_seed_val_drop),
        certificate_max_low_tail_f1_drop=float(args.certificate_max_low_tail_f1_drop),
        certificate_low_tail_quantile=float(args.certificate_low_tail_quantile),
        certificate_min_baseline_path_jaccard=float(args.certificate_min_baseline_path_jaccard),
    )
    for path in write_report(report, Path(args.output_dir), write_selected_runs=not bool(args.no_selected_runs)):
        print(path)
    print(render_markdown(report))


if __name__ == "__main__":
    main()
