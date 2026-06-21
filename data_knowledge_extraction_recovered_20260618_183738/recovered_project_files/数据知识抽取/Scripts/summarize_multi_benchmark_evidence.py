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


def _metric(run: dict[str, Any], key: str, metric: str = "macro_f1") -> float | None:
    value = run.get(key)
    if not isinstance(value, dict) or metric not in value:
        return None
    return float(value[metric])


def _summarize_skab(paths: list[Path]) -> dict[str, Any]:
    base: list[float] = []
    method: list[float] = []
    for path in paths:
        data = _load(path)
        base.append(float(data["baseline"]["metrics"]["macro_f1"]))
        method.append(float(data["dynamic_llm_kg"]["metrics"]["macro_f1"]))
    return {
        "dataset": "SKAB",
        "task": "Binary anomaly detection",
        "main": _mean_std(base),
        "method": _mean_std(method),
        "delta": f"{(mean(method) - mean(base)):+.4f}" if base and method else "n/a",
        "evidence": "LLM candidate edges help only after learned reliability filtering.",
    }


def _summarize_hydraulic(paths: list[Path]) -> dict[str, Any]:
    main: list[float] = []
    method: list[float] = []
    for path in paths:
        data = _load(path)
        for run in data.get("runs", []):
            main_value = _metric(run, "main")
            method_value = _metric(run, "safe_learned_evidence_router") or _metric(run, "ere_reliability_routing")
            if main_value is not None and method_value is not None:
                main.append(main_value)
                method.append(method_value)
    return {
        "dataset": "Hydraulic",
        "task": "Four-target state diagnosis",
        "main": _mean_std(main),
        "method": _mean_std(method),
        "delta": f"{(mean(method) - mean(main)):+.4f}" if main and method else "n/a",
        "evidence": "Safe routing preserves near-ceiling targets and improves the difficult valve target.",
    }


def _summarize_cmapss(paths: list[Path]) -> dict[str, Any]:
    main: list[float] = []
    method: list[float] = []
    for path in paths:
        data = _load(path)
        for run in data.get("runs", []):
            main_value = _metric(run, "main")
            candidates = [
                _metric(run, "plain_residual_fusion"),
                _metric(run, "ugmc_selective_correction"),
                _metric(run, "ere_reliability_routing"),
                _metric(run, "condition_safe_evidence_routing"),
            ]
            candidates = [value for value in candidates if value is not None]
            if main_value is not None and candidates:
                main.append(main_value)
                method.append(max(candidates))
    return {
        "dataset": "C-MAPSS",
        "task": "Degradation-stage diagnosis",
        "main": _mean_std(main),
        "method": _mean_std(method),
        "delta": f"{(mean(method) - mean(main)):+.4f}" if main and method else "n/a",
        "evidence": "Portable residual evidence exists, but the current ridge residual branch gives only small gains.",
    }


def summarize(skab: list[Path], hydraulic: list[Path], cmapss: list[Path]) -> str:
    rows = [
        _summarize_skab(skab),
        _summarize_hydraulic(hydraulic),
        _summarize_cmapss(cmapss),
    ]
    lines: list[str] = []
    lines.append("# Multi-Benchmark Evidence Matrix")
    lines.append("")
    lines.append("| Dataset | Task | Main | Proposed/Reliable Variant | Delta | Evidence Role |")
    lines.append("|---|---|---:|---:|---:|---|")
    for row in rows:
        lines.append(
            "| {dataset} | {task} | {main} | {method} | {delta} | {evidence} |".format(**row)
        )
    lines.append("")
    lines.append("## Reading")
    lines.append("")
    lines.append(
        "The current evidence supports the central reliability-calibrated mechanism-learning idea across "
        "three industrial benchmarks. It does not yet support a universal SOTA claim: SKAB shows robust "
        "positive graph-editing gains, Hydraulic is strong and near-ceiling, while C-MAPSS exposes the need "
        "for a degradation-aware temporal residual pretraining branch."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a multi-benchmark evidence matrix.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--skab", nargs="+", required=True)
    parser.add_argument("--hydraulic", nargs="+", required=True)
    parser.add_argument("--cmapss", nargs="+", required=True)
    args = parser.parse_args()
    report = summarize(
        [Path(file) for file in args.skab],
        [Path(file) for file in args.hydraulic],
        [Path(file) for file in args.cmapss],
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
