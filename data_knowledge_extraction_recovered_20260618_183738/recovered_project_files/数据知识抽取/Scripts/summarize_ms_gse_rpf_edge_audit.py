from __future__ import annotations

import argparse
import json
import math
import os
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Iterable, Mapping


EDGE_SOURCE_FAMILY = {
    "correlation": "structural",
    "residual": "structural",
    "lag": "dynamic",
    "directed_lag": "dynamic",
    "innovation": "dynamic",
    "class_lag": "dynamic",
    "stability": "dynamic",
    "class": "task",
    "fault_response": "task",
}


def _fs_path(path: str | Path) -> str:
    resolved = os.path.abspath(os.fspath(path))
    if os.name == "nt" and not resolved.startswith("\\\\?\\"):
        return "\\\\?\\" + resolved
    return resolved


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return float(default)
        out = float(value)
    except (TypeError, ValueError):
        return float(default)
    if math.isnan(out) or math.isinf(out):
        return float(default)
    return out


def _mean_std(values: Iterable[float]) -> tuple[float, float]:
    vals = [float(v) for v in values]
    if not vals:
        return 0.0, 0.0
    return float(mean(vals)), float(pstdev(vals)) if len(vals) > 1 else 0.0


def _read_json(path: str | Path) -> dict[str, Any]:
    with open(_fs_path(path), "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, dict) else {}


def _write_json(path: str | Path, payload: Mapping[str, Any]) -> None:
    target = Path(path)
    os.makedirs(_fs_path(target.parent), exist_ok=True)
    with open(_fs_path(target), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _write_text(path: str | Path, text: str) -> None:
    target = Path(path)
    os.makedirs(_fs_path(target.parent), exist_ok=True)
    with open(_fs_path(target), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def _iter_json_files(result_dir: str | Path) -> list[Path]:
    root = Path(result_dir)
    try:
        names = os.listdir(_fs_path(root))
    except OSError:
        return []
    files = []
    for name in names:
        if str(name).lower().endswith(".json"):
            files.append(root / str(name))
    return sorted(files, key=lambda item: item.name)


def load_runs(
    result_dir: str | Path,
    *,
    dataset: str | None = None,
    target: str | None = None,
    variant: str | None = None,
    filename_contains: str = "__all__",
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in _iter_json_files(result_dir):
        if filename_contains and filename_contains != "__all__" and filename_contains not in path.name:
            continue
        try:
            row = _read_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        if "seed" not in row:
            continue
        if dataset and str(row.get("dataset")) != str(dataset):
            continue
        if target and str(row.get("target")) != str(target):
            continue
        if variant and str(row.get("variant")) != str(variant):
            continue
        row["_file"] = path.name
        rows.append(row)
    return sorted(rows, key=lambda item: int(item.get("seed", 0)))


def _metrics(row: Mapping[str, Any], split: str) -> Mapping[str, Any]:
    if split == "val":
        return row.get("val_metrics") or {}
    if split == "test":
        return row.get("primary_test_metrics") or row.get("test_metrics") or {}
    raise ValueError(f"Unsupported split: {split}")


def _metric(row: Mapping[str, Any], split: str, key: str) -> float:
    return _safe_float(_metrics(row, split).get(key), 0.0)


def _per_class_f1(row: Mapping[str, Any], split: str) -> dict[str, float]:
    raw = _metrics(row, split).get("per_class") or {}
    out: dict[str, float] = {}
    if not isinstance(raw, Mapping):
        return out
    for cls, values in raw.items():
        if isinstance(values, Mapping):
            out[str(cls)] = _safe_float(values.get("f1"), 0.0)
        else:
            out[str(cls)] = _safe_float(values, 0.0)
    return out


def _rows_by_seed(rows: Iterable[Mapping[str, Any]]) -> dict[int, Mapping[str, Any]]:
    return {int(row.get("seed", 0)): row for row in rows}


def _baseline_low_tail_classes(rows: list[Mapping[str, Any]], *, quantile: float, max_classes: int) -> list[dict[str, Any]]:
    by_class: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        for cls, f1 in _per_class_f1(row, "val").items():
            by_class[str(cls)].append(float(f1))
    scored = []
    for cls, values in by_class.items():
        avg, std = _mean_std(values)
        scored.append({"class": str(cls), "val_f1_mean": avg, "val_f1_std": std, "runs": len(values)})
    scored.sort(key=lambda item: (item["val_f1_mean"], item["class"]))
    if not scored:
        return []
    q_count = max(1, int(math.ceil(float(max(0.0, min(1.0, quantile))) * len(scored))))
    limit = max(1, int(max_classes)) if int(max_classes) > 0 else q_count
    return scored[: min(len(scored), max(q_count, limit))]


def _path_key(item: Mapping[str, Any]) -> str:
    return str(item.get("group_path") or item.get("path") or f"{item.get('source')} -> {item.get('target')}")


def _path_summary(rows: Iterable[Mapping[str, Any]], *, top_k: int) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    weights: dict[str, list[float]] = defaultdict(list)
    priors: dict[str, list[float]] = defaultdict(list)
    salience: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        for item in list(row.get("top_evidence_paths") or [])[: max(1, int(top_k))]:
            if not isinstance(item, Mapping):
                continue
            key = _path_key(item)
            counts[key] += 1
            weights[key].append(_safe_float(item.get("mean_weight"), 0.0))
            priors[key].append(_safe_float(item.get("mean_prior_weight"), 0.0))
            salience[key].append(_safe_float(item.get("mean_salience_weight"), 0.0))
    top_paths = []
    for key, count in counts.most_common(max(1, int(top_k))):
        weight_mean, _ = _mean_std(weights[key])
        prior_mean, _ = _mean_std(priors[key])
        salience_mean, _ = _mean_std(salience[key])
        top_paths.append(
            {
                "path": key,
                "count": int(count),
                "mean_weight": weight_mean,
                "mean_prior_weight": prior_mean,
                "mean_salience_weight": salience_mean,
            }
        )
    return {"top_paths": top_paths, "path_set": sorted(counts)}


def _path_jaccard(a_rows: Iterable[Mapping[str, Any]], b_rows: Iterable[Mapping[str, Any]], *, top_k: int) -> float:
    a = set(_path_summary(a_rows, top_k=top_k)["path_set"])
    b = set(_path_summary(b_rows, top_k=top_k)["path_set"])
    if not a and not b:
        return 1.0
    return float(len(a & b) / max(1, len(a | b)))


def _edge_prior_summary(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    mode_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    vote_counts: Counter[str] = Counter()
    densities: list[float] = []
    uncapped_edges: list[float] = []
    single_view_edges: list[float] = []
    corroborated_edges: list[float] = []
    mean_votes: list[float] = []
    component_edge_counts: Counter[str] = Counter()

    for row in rows:
        prior = row.get("algorithmic_edge_prior") or {}
        if not isinstance(prior, Mapping):
            continue
        mode = str(prior.get("mode") or "none")
        mode_counts[mode] += 1
        densities.append(_safe_float(prior.get("density"), 0.0))
        uncapped_edges.append(_safe_float(prior.get("uncapped_edges"), 0.0))
        active = prior.get(mode) if isinstance(prior.get(mode), Mapping) else None
        if active is None:
            for key in ("edge_cert_overlay", "edge_cert_pool", "edge_pool", "edge_universe", "edge_canvas", "edge_bank"):
                if isinstance(prior.get(key), Mapping):
                    active = prior.get(key)
                    break
        if isinstance(active, Mapping):
            single_view_edges.append(_safe_float(active.get("single_view_edges"), 0.0))
            single_view_edges.append(_safe_float(active.get("single_dynamic_task_edges"), 0.0))
            single_view_edges.append(_safe_float(active.get("certified_single_edges"), 0.0))
            corroborated_edges.append(_safe_float(active.get("corroborated_edges"), 0.0))
            corroborated_edges.append(_safe_float(active.get("dynamic_task_agreement_edges"), 0.0))
            mean_votes.append(_safe_float(active.get("mean_votes"), 0.0))
            for comp, count in (active.get("component_edge_counts") or {}).items():
                component_edge_counts[str(comp)] += int(_safe_float(count, 0.0))
        for edge in prior.get("top_edge_indices") or []:
            if not isinstance(edge, Mapping):
                continue
            vote_counts[str(int(_safe_float(edge.get("votes"), 0.0)))] += 1
            for source in edge.get("sources") or []:
                source_name = str(source)
                source_counts[source_name] += 1
                family_counts[EDGE_SOURCE_FAMILY.get(source_name, "other")] += 1

    density_mean, density_std = _mean_std(densities)
    uncapped_mean, _ = _mean_std(uncapped_edges)
    single_mean, _ = _mean_std([v for v in single_view_edges if v > 0.0])
    corroborated_mean, _ = _mean_std(corroborated_edges)
    votes_mean, _ = _mean_std(mean_votes)
    return {
        "modes": dict(mode_counts),
        "density_mean": density_mean,
        "density_std": density_std,
        "uncapped_edges_mean": uncapped_mean,
        "single_view_edges_mean": single_mean,
        "corroborated_edges_mean": corroborated_mean,
        "mean_votes": votes_mean,
        "top_edge_source_counts": dict(source_counts.most_common()),
        "top_edge_family_counts": dict(family_counts.most_common()),
        "top_edge_vote_counts": dict(vote_counts.most_common()),
        "component_edge_counts": dict(component_edge_counts.most_common()),
    }


def _candidate_report(
    name: str,
    baseline_rows: list[Mapping[str, Any]],
    candidate_rows: list[Mapping[str, Any]],
    *,
    low_tail_classes: list[str],
    path_top_k: int,
) -> dict[str, Any]:
    base_by_seed = _rows_by_seed(baseline_rows)
    cand_by_seed = _rows_by_seed(candidate_rows)
    common_seeds = sorted(set(base_by_seed) & set(cand_by_seed))

    val_gains = []
    test_gains = []
    bal_gains = []
    low_tail_val_gains = []
    low_tail_test_gains = []
    class_deltas: dict[str, list[float]] = defaultdict(list)
    test_class_deltas: dict[str, list[float]] = defaultdict(list)
    seed_rows = []
    for seed in common_seeds:
        base = base_by_seed[seed]
        cand = cand_by_seed[seed]
        val_gain = _metric(cand, "val", "macro_f1") - _metric(base, "val", "macro_f1")
        test_gain = _metric(cand, "test", "macro_f1") - _metric(base, "test", "macro_f1")
        bal_gain = _metric(cand, "test", "balanced_accuracy") - _metric(base, "test", "balanced_accuracy")
        val_gains.append(val_gain)
        test_gains.append(test_gain)
        bal_gains.append(bal_gain)
        base_val = _per_class_f1(base, "val")
        cand_val = _per_class_f1(cand, "val")
        base_test = _per_class_f1(base, "test")
        cand_test = _per_class_f1(cand, "test")
        seed_low_val = []
        seed_low_test = []
        for cls in low_tail_classes:
            if cls in base_val and cls in cand_val:
                delta = cand_val[cls] - base_val[cls]
                class_deltas[cls].append(delta)
                seed_low_val.append(delta)
            if cls in base_test and cls in cand_test:
                delta = cand_test[cls] - base_test[cls]
                test_class_deltas[cls].append(delta)
                seed_low_test.append(delta)
        if seed_low_val:
            low_tail_val_gains.append(float(mean(seed_low_val)))
        if seed_low_test:
            low_tail_test_gains.append(float(mean(seed_low_test)))
        seed_rows.append(
            {
                "seed": int(seed),
                "val_macro_f1_gain": float(val_gain),
                "test_macro_f1_gain": float(test_gain),
                "test_balanced_accuracy_gain": float(bal_gain),
                "low_tail_val_f1_gain": float(mean(seed_low_val)) if seed_low_val else 0.0,
                "low_tail_test_f1_gain": float(mean(seed_low_test)) if seed_low_test else 0.0,
            }
        )

    harmed_val = []
    for cls, values in class_deltas.items():
        avg, std = _mean_std(values)
        harmed_val.append({"class": cls, "val_f1_gain_mean": avg, "val_f1_gain_std": std})
    harmed_val.sort(key=lambda item: (item["val_f1_gain_mean"], item["class"]))
    harmed_test = []
    for cls, values in test_class_deltas.items():
        avg, std = _mean_std(values)
        harmed_test.append({"class": cls, "test_f1_gain_mean": avg, "test_f1_gain_std": std})
    harmed_test.sort(key=lambda item: (item["test_f1_gain_mean"], item["class"]))

    val_mean, val_std = _mean_std(val_gains)
    test_mean, test_std = _mean_std(test_gains)
    bal_mean, bal_std = _mean_std(bal_gains)
    low_val_mean, low_val_std = _mean_std(low_tail_val_gains)
    low_test_mean, low_test_std = _mean_std(low_tail_test_gains)
    base_summary = _path_summary(baseline_rows, top_k=path_top_k)
    cand_summary = _path_summary(candidate_rows, top_k=path_top_k)
    base_paths = set(base_summary["path_set"])
    new_paths = [path for path in cand_summary["top_paths"] if path["path"] not in base_paths]

    return {
        "name": name,
        "runs": len(common_seeds),
        "common_seeds": common_seeds,
        "val_macro_f1_gain_mean": val_mean,
        "val_macro_f1_gain_std": val_std,
        "test_macro_f1_gain_mean": test_mean,
        "test_macro_f1_gain_std": test_std,
        "test_balanced_accuracy_gain_mean": bal_mean,
        "test_balanced_accuracy_gain_std": bal_std,
        "low_tail_val_f1_gain_mean": low_val_mean,
        "low_tail_val_f1_gain_std": low_val_std,
        "low_tail_test_f1_gain_mean": low_test_mean,
        "low_tail_test_f1_gain_std": low_test_std,
        "seed_rows": seed_rows,
        "most_harmed_low_tail_val_classes": harmed_val[: min(8, len(harmed_val))],
        "most_harmed_low_tail_test_classes": harmed_test[: min(8, len(harmed_test))],
        "path_jaccard": _path_jaccard(baseline_rows, candidate_rows, top_k=path_top_k),
        "new_candidate_top_paths": new_paths[: min(10, len(new_paths))],
        "candidate_path_summary": cand_summary["top_paths"],
        "edge_prior_summary": _edge_prior_summary(candidate_rows),
    }


def build_edge_audit_report(
    *,
    baseline_dir: str | Path,
    candidates: list[tuple[str, str | Path]],
    dataset: str | None = None,
    target: str | None = None,
    variant: str | None = None,
    filename_contains: str = "__all__",
    low_tail_quantile: float = 0.25,
    max_low_tail_classes: int = 6,
    path_top_k: int = 10,
) -> dict[str, Any]:
    baseline_rows = load_runs(
        baseline_dir,
        dataset=dataset,
        target=target,
        variant=variant,
        filename_contains=filename_contains,
    )
    if not baseline_rows:
        raise ValueError(f"No baseline runs found in {baseline_dir}")
    low_tail = _baseline_low_tail_classes(
        baseline_rows,
        quantile=low_tail_quantile,
        max_classes=max_low_tail_classes,
    )
    low_tail_classes = [str(item["class"]) for item in low_tail]
    candidate_reports = []
    for name, path in candidates:
        rows = load_runs(
            path,
            dataset=dataset,
            target=target,
            variant=variant,
            filename_contains=filename_contains,
        )
        if not rows:
            candidate_reports.append({"name": name, "runs": 0, "error": f"No runs found in {path}"})
            continue
        candidate_reports.append(
            _candidate_report(
                name,
                baseline_rows,
                rows,
                low_tail_classes=low_tail_classes,
                path_top_k=path_top_k,
            )
        )
    base_val_mean, base_val_std = _mean_std(_metric(row, "val", "macro_f1") for row in baseline_rows)
    base_test_mean, base_test_std = _mean_std(_metric(row, "test", "macro_f1") for row in baseline_rows)
    base_bal_mean, base_bal_std = _mean_std(_metric(row, "test", "balanced_accuracy") for row in baseline_rows)
    return {
        "baseline_dir": os.fspath(baseline_dir),
        "dataset": dataset,
        "target": target,
        "variant": variant,
        "filename_contains": filename_contains,
        "low_tail_quantile": float(low_tail_quantile),
        "max_low_tail_classes": int(max_low_tail_classes),
        "path_top_k": int(path_top_k),
        "baseline": {
            "runs": len(baseline_rows),
            "seeds": [int(row.get("seed", 0)) for row in baseline_rows],
            "val_macro_f1_mean": base_val_mean,
            "val_macro_f1_std": base_val_std,
            "test_macro_f1_mean": base_test_mean,
            "test_macro_f1_std": base_test_std,
            "test_balanced_accuracy_mean": base_bal_mean,
            "test_balanced_accuracy_std": base_bal_std,
            "low_tail_classes": low_tail,
            "path_summary": _path_summary(baseline_rows, top_k=path_top_k)["top_paths"],
            "edge_prior_summary": _edge_prior_summary(baseline_rows),
        },
        "candidates": candidate_reports,
    }


def _fmt(value: Any, digits: int = 4) -> str:
    return f"{_safe_float(value):.{digits}f}"


def render_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# MS-GSE + RPF Edge/Path Audit",
        "",
        f"- dataset: {report.get('dataset') or '*'}",
        f"- target: {report.get('target') or '*'}",
        f"- variant: {report.get('variant') or '*'}",
        f"- low-tail quantile: {_fmt(report.get('low_tail_quantile'), 2)}",
        "",
    ]
    baseline = report.get("baseline") or {}
    lines.extend(
        [
            "## Baseline",
            "",
            "| Runs | Val Macro-F1 | Test Macro-F1 | Test Bal. Acc. |",
            "|---:|---:|---:|---:|",
            (
                f"| {int(baseline.get('runs', 0))} | "
                f"{_fmt(baseline.get('val_macro_f1_mean'))} +/- {_fmt(baseline.get('val_macro_f1_std'))} | "
                f"{_fmt(baseline.get('test_macro_f1_mean'))} +/- {_fmt(baseline.get('test_macro_f1_std'))} | "
                f"{_fmt(baseline.get('test_balanced_accuracy_mean'))} +/- {_fmt(baseline.get('test_balanced_accuracy_std'))} |"
            ),
            "",
            "## Baseline Low-Tail Classes",
            "",
            "| Class | Val F1 | Runs |",
            "|---|---:|---:|",
        ]
    )
    for item in baseline.get("low_tail_classes") or []:
        lines.append(f"| {item.get('class')} | {_fmt(item.get('val_f1_mean'))} +/- {_fmt(item.get('val_f1_std'))} | {item.get('runs', 0)} |")

    lines.extend(
        [
            "",
            "## Candidate Summary",
            "",
            "| Candidate | Runs | Val Gain | Test Gain | Test Bal. Gain | Low-Tail Val Gain | Low-Tail Test Gain | Path Jaccard |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for item in report.get("candidates") or []:
        if item.get("error"):
            lines.append(f"| {item.get('name')} | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |")
            continue
        lines.append(
            f"| {item.get('name')} | {int(item.get('runs', 0))} | "
            f"{_fmt(item.get('val_macro_f1_gain_mean'))} +/- {_fmt(item.get('val_macro_f1_gain_std'))} | "
            f"{_fmt(item.get('test_macro_f1_gain_mean'))} +/- {_fmt(item.get('test_macro_f1_gain_std'))} | "
            f"{_fmt(item.get('test_balanced_accuracy_gain_mean'))} +/- {_fmt(item.get('test_balanced_accuracy_gain_std'))} | "
            f"{_fmt(item.get('low_tail_val_f1_gain_mean'))} +/- {_fmt(item.get('low_tail_val_f1_gain_std'))} | "
            f"{_fmt(item.get('low_tail_test_f1_gain_mean'))} +/- {_fmt(item.get('low_tail_test_f1_gain_std'))} | "
            f"{_fmt(item.get('path_jaccard'))} |"
        )

    for item in report.get("candidates") or []:
        lines.extend(["", f"## Candidate: {item.get('name')}", ""])
        if item.get("error"):
            lines.append(str(item.get("error")))
            continue
        lines.extend(["### Most Harmed Low-Tail Validation Classes", "", "| Class | Val F1 Gain |", "|---|---:|"])
        for cls in item.get("most_harmed_low_tail_val_classes") or []:
            lines.append(f"| {cls.get('class')} | {_fmt(cls.get('val_f1_gain_mean'))} +/- {_fmt(cls.get('val_f1_gain_std'))} |")
        lines.extend(["", "### New Candidate Top Paths", "", "| Path | Count | Weight | Prior | Salience |", "|---|---:|---:|---:|---:|"])
        for path in item.get("new_candidate_top_paths") or []:
            lines.append(
                f"| {path.get('path')} | {int(path.get('count', 0))} | "
                f"{_fmt(path.get('mean_weight'))} | {_fmt(path.get('mean_prior_weight'))} | "
                f"{_fmt(path.get('mean_salience_weight'))} |"
            )
        edge = item.get("edge_prior_summary") or {}
        lines.extend(
            [
                "",
                "### Edge Prior Audit",
                "",
                f"- modes: `{edge.get('modes')}`",
                f"- density: `{_fmt(edge.get('density_mean'))} +/- {_fmt(edge.get('density_std'))}`",
                f"- uncapped edges mean: `{_fmt(edge.get('uncapped_edges_mean'), 1)}`",
                f"- corroborated edges mean: `{_fmt(edge.get('corroborated_edges_mean'), 1)}`",
                f"- single-view edges mean: `{_fmt(edge.get('single_view_edges_mean'), 1)}`",
                f"- top-edge family counts: `{edge.get('top_edge_family_counts')}`",
            ]
        )
    return "\n".join(lines) + "\n"


def _parse_candidate(raw: str) -> tuple[str, str]:
    if "=" in raw:
        name, path = raw.split("=", 1)
        return name.strip(), path.strip()
    path = raw.strip()
    return Path(path).name, path


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit MS-GSE + RPF edge/path candidates against a baseline.")
    parser.add_argument("--baseline-dir", required=True)
    parser.add_argument("--candidate", action="append", default=[], help="Candidate as name=dir. Can be repeated.")
    parser.add_argument("--dataset", default=None)
    parser.add_argument("--target", default=None)
    parser.add_argument("--variant", default=None)
    parser.add_argument("--filename-contains", default="__all__")
    parser.add_argument("--low-tail-quantile", type=float, default=0.25)
    parser.add_argument("--max-low-tail-classes", type=int, default=6)
    parser.add_argument("--path-top-k", type=int, default=10)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    candidates = [_parse_candidate(item) for item in args.candidate]
    report = build_edge_audit_report(
        baseline_dir=args.baseline_dir,
        candidates=candidates,
        dataset=args.dataset,
        target=args.target,
        variant=args.variant,
        filename_contains=args.filename_contains,
        low_tail_quantile=float(args.low_tail_quantile),
        max_low_tail_classes=int(args.max_low_tail_classes),
        path_top_k=int(args.path_top_k),
    )
    out_dir = Path(args.output_dir)
    _write_json(out_dir / "ms_gse_rpf_edge_audit.json", report)
    _write_text(out_dir / "ms_gse_rpf_edge_audit.md", render_markdown(report))
    print(out_dir / "ms_gse_rpf_edge_audit.json")
    print(out_dir / "ms_gse_rpf_edge_audit.md")


if __name__ == "__main__":
    main()
