from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


METHODS = [
    ("main", "Main"),
    ("plain_residual_fusion", "PlainResidual"),
    ("ugmc_selective_correction", "UGMC"),
    ("contextual_residual_correction", "Contextual"),
    ("run_stable_evidence_routing", "RunStable"),
    ("benefit_stable_evidence_routing", "BenefitStable"),
    ("safe_benefit_stable_evidence_routing", "SafeBenefit"),
    ("condition_safe_evidence_routing", "ConditionSafe"),
    ("ere_reliability_routing", "ERE"),
]


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _mean_std(values: list[float]) -> str:
    if not values:
        return "n/a"
    return f"{mean(values):.4f} +/- {pstdev(values):.4f}"


def _metric(run: dict[str, Any], key: str, metric: str) -> float | None:
    value = run.get(key)
    if not isinstance(value, dict) or metric not in value:
        return None
    return float(value[metric])


def summarize(files: list[Path]) -> str:
    lines: list[str] = []
    lines.append("# C-MAPSS Summary")
    lines.append("")
    lines.append("| Dataset | Runs | Residual Mode | Main | PlainResidual | UGMC | Contextual | ERE | Best Delta |")
    lines.append("|---|---:|---|---:|---:|---:|---:|---:|---:|")

    interpretation_rows: list[str] = []
    for path in files:
        data = _load(path)
        runs = list(data.get("runs", []))
        dataset = f"cmapss_{data.get('subset', path.stem)}"
        residual_modes = sorted({str(run.get("selected_residual_family", run.get("residual_mode", ""))) for run in runs})
        main_values = [_metric(run, "main", "macro_f1") for run in runs]
        main_values = [value for value in main_values if value is not None]
        method_values: dict[str, list[float]] = {}
        for key, _label in METHODS:
            values = [_metric(run, key, "macro_f1") for run in runs]
            method_values[key] = [value for value in values if value is not None]
        best_key = max(
            method_values,
            key=lambda key: mean(method_values[key]) if method_values[key] else float("-inf"),
        )
        best_delta = (mean(method_values[best_key]) - mean(main_values)) if main_values and method_values[best_key] else 0.0
        row = {
            "dataset": dataset,
            "runs": len(runs),
            "residual_mode": ",".join(residual_modes),
            "main": _mean_std(method_values["main"]),
            "plain": _mean_std(method_values["plain_residual_fusion"]),
            "ugmc": _mean_std(method_values["ugmc_selective_correction"]),
            "contextual": _mean_std(method_values["contextual_residual_correction"]),
            "ere": _mean_std(method_values["ere_reliability_routing"]),
            "best_delta": f"{best_delta:+.4f}",
        }
        lines.append(
            "| {dataset} | {runs} | {residual_mode} | {main} | {plain} | {ugmc} | {contextual} | {ere} | {best_delta} |".format(
                **row
            )
        )
        interpretation_rows.append(
            f"- {dataset}: best candidate is {best_key} with Macro-F1 delta {best_delta:+.4f}."
        )

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.extend(interpretation_rows)
    lines.append(
        "- C-MAPSS is currently evidence of portability, not yet a SOTA claim: the reliability-corrected variants "
        "are close to the main classifier and only produce small gains under the ridge residual setting. "
        "The next useful upgrade is a degradation-aware temporal residual pretraining branch rather than reusing "
        "the SKAB graph-editing recipe directly."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize C-MAPSS benchmark results.")
    parser.add_argument("--output", required=True)
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()
    report = summarize([Path(file) for file in args.files])
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
