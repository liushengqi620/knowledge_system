from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _mean_std(values: list[float]) -> str:
    if not values:
        return "n/a"
    return f"{mean(values):.4f} +/- {pstdev(values):.4f}"


def _metric(run: dict[str, Any], key: str, metric: str) -> float | None:
    value = run.get(key)
    if not isinstance(value, dict):
        return None
    if metric not in value:
        return None
    return float(value[metric])


def _learned_reliability_row(files: list[Path]) -> dict[str, Any]:
    baseline: list[float] = []
    learned: list[float] = []
    deltas: list[float] = []
    seeds: list[int] = []
    for path in files:
        data = _load(path)
        baseline.append(float(data["baseline"]["metrics"]["macro_f1"]))
        learned.append(float(data["dynamic_llm_kg"]["metrics"]["macro_f1"]))
        deltas.append(float(data.get("macro_f1_delta", learned[-1] - baseline[-1])))
        seeds.append(int(data.get("seed", -1)))
    return {
        "term": "Validation-benefit admission",
        "dataset": "SKAB",
        "evidence": f"baseline {_mean_std(baseline)} -> learned reliability {_mean_std(learned)}",
        "effect": _mean_std(deltas),
        "role": "Shows that candidate LLM/graph evidence is admitted by validation usefulness rather than trusted globally.",
        "strength": f"main; n={len(files)} seeds {','.join(str(seed) for seed in seeds)}",
    }


def _counterfactual_row(named_files: list[tuple[str, Path]]) -> dict[str, Any]:
    rows: list[tuple[str, float, str, int]] = []
    for label, path in named_files:
        data = _load(path)
        dynamic = data["dynamic_llm_kg"]
        cf = data.get("edge_counterfactual", {}) or {}
        rows.append(
            (
                label,
                float(dynamic["metrics"]["macro_f1"]),
                str(cf.get("mode", "none")),
                int(cf.get("n_changed_edges", 0)),
            )
        )
    if not rows:
        return {
            "term": "Counterfactual edge consistency",
            "dataset": "SKAB",
            "evidence": "missing",
            "effect": "missing",
            "role": "No counterfactual files were provided.",
            "strength": "missing",
        }
    original = rows[0][1]
    perturbations = rows[1:]
    drops = [value - original for _label, value, _mode, _changed in perturbations]
    detail = "; ".join(
        f"{label}/{mode}/changed={changed}: {value:.4f} ({value - original:+.4f})"
        for label, value, mode, changed in perturbations
    )
    return {
        "term": "Counterfactual edge consistency",
        "dataset": "SKAB",
        "evidence": f"original {original:.4f}; {detail}",
        "effect": _mean_std(drops) if drops else "+0.0000",
        "role": "Tests whether edge direction, lag, and target assignment are decision-relevant instead of decorative.",
        "strength": f"main perturbation; n={len(perturbations)} perturbations",
    }


def _cmapss_row(files: list[Path]) -> dict[str, Any]:
    main_values: list[float] = []
    fixed_ere_values: list[float] = []
    tail_values: list[float] = []
    nondeg = 0
    total = 0
    subsets: list[str] = []
    for path in files:
        data = _load(path)
        subsets.append(str(data.get("subset", path.stem)))
        for run in data.get("runs", []) or []:
            main = _metric(run, "main", "macro_f1")
            fixed = _metric(run, "ere_reliability_routing", "macro_f1")
            tail = _metric(run, "tail_guarded_ere_reliability_routing", "macro_f1")
            if tail is None:
                tail = fixed
            if main is not None:
                main_values.append(main)
            if fixed is not None:
                fixed_ere_values.append(fixed)
            if main is not None and tail is not None:
                total += 1
                tail_values.append(tail)
                if tail >= main:
                    nondeg += 1
    fixed_delta = [fixed - base for fixed, base in zip(fixed_ere_values, main_values)]
    return {
        "term": "Low-tail non-degradation",
        "dataset": "C-MAPSS",
        "evidence": f"main {_mean_std(main_values)} -> FixedERE {_mean_std(fixed_ere_values)}; TailGuardedERE {_mean_std(tail_values)}",
        "effect": f"FixedERE delta {_mean_std(fixed_delta)}; tail non-deg {nondeg}/{total}",
        "role": "Validates that reliability routing is constrained by low-tail safety, not only mean validation gain.",
        "strength": f"main; subsets={','.join(subsets)}",
    }


def _pruned_kg_row(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "term": "Complexity/source pruning",
            "dataset": "SKAB",
            "evidence": "not provided",
            "effect": "missing",
            "role": "Still needed as strict multi-seed evidence.",
            "strength": "missing",
        }
    data = _load(path)
    rows = {str(run.get("mode", "")): run for run in data.get("runs", []) or []}
    original = rows.get("original_full_msfg") or rows.get("full_expert_llm_data") or next(iter(rows.values()), {})
    pruned = rows.get("full_pruned_kg") or rows.get("full_pruned_expert_llm_data") or original
    original_score = float(original.get("macro_f1", 0.0))
    pruned_score = float(pruned.get("macro_f1", 0.0))
    fused_edges = None
    fusion = pruned.get("fusion", {})
    if isinstance(fusion, dict) and "n_fused_edges" in fusion:
        fused_edges = int(fusion["n_fused_edges"])
    edge_text = f"; fused_edges={fused_edges}" if fused_edges is not None else ""
    return {
        "term": "Complexity/source pruning",
        "dataset": "SKAB",
        "evidence": f"original {original_score:.4f} -> pruned {pruned_score:.4f}{edge_text}",
        "effect": f"{pruned_score - original_score:+.4f}",
        "role": "Exploratory evidence that unsupported source-specific edges should be pruned before graph use.",
        "strength": "exploratory; seed42/e3",
    }


def summarize(
    *,
    learned_reliability_files: list[Path],
    counterfactual_files: list[tuple[str, Path]],
    cmapss_files: list[Path],
    pruned_kg_file: Path | None = None,
) -> str:
    rows = [
        _learned_reliability_row(learned_reliability_files),
        _counterfactual_row(counterfactual_files),
        _cmapss_row(cmapss_files),
        _pruned_kg_row(pruned_kg_file),
    ]
    lines: list[str] = []
    lines.append("# Reliability-Term Evidence Table")
    lines.append("")
    lines.append(
        "This table maps each reliability component to reproducible evidence. "
        "Main rows are suitable for the paper body; exploratory rows should remain appendix material until rerun with strict multi-seed protocols."
    )
    lines.append("")
    lines.append("| Reliability term | Dataset | Evidence | Effect | What it validates | Evidence strength |")
    lines.append("|---|---|---|---:|---|---|")
    for row in rows:
        lines.append(
            "| {term} | {dataset} | {evidence} | {effect} | {role} | {strength} |".format(**row)
        )
    lines.append("")
    lines.append("## Paper Claim")
    lines.append("")
    lines.append(
        "The reliability score is not merely an experience-weighted edge importance. It is an admission decision "
        "supported by validation benefit, counterfactual sensitivity, low-tail non-degradation, and source-aware "
        "complexity control. Current evidence is strongest for validation admission, counterfactual edge checks, "
        "and low-tail deployment safety; complexity/source pruning still needs strict multi-seed confirmation."
    )
    lines.append("")
    return "\n".join(lines)


def _parse_named_file(raw: str) -> tuple[str, Path]:
    if "=" not in raw:
        raise ValueError(f"Expected label=path item, got: {raw}")
    label, path = raw.split("=", 1)
    return label.strip(), Path(path.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize reliability-term evidence across public benchmarks.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--learned", nargs="+", required=True)
    parser.add_argument("--counterfactual", nargs="+", required=True, help="Items in label=path form.")
    parser.add_argument("--cmapss", nargs="+", required=True)
    parser.add_argument("--pruned-kg", default=None)
    args = parser.parse_args()
    report = summarize(
        learned_reliability_files=[Path(item) for item in args.learned],
        counterfactual_files=[_parse_named_file(item) for item in args.counterfactual],
        cmapss_files=[Path(item) for item in args.cmapss],
        pruned_kg_file=Path(args.pruned_kg) if args.pruned_kg else None,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
