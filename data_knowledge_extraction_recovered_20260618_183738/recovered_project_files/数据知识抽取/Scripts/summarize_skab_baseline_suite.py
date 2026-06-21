from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


METHOD_LABELS = {
    "extra_trees": "ExtraTrees",
    "ft_transformer": "FT-Transformer",
    "tcn": "TCN",
    "time_context_tcn": "TimeContext-TCN",
    "graph_tcn": "Graph-TCN",
    "msfg_tcn": "MSFG-TCN",
    "msfg_time_context_tcn": "MSFG-TimeContext-TCN",
    "msfg_gru": "MSFG-GRU",
    "run_prefix_context_main": "RunPrefix",
    "run_prefix_change_context_main": "RunPrefix+Change",
    "time_context_main": "TimeContext-Main",
    "adaptive_graph_tcn_fusion": "AdaptiveGraphTCN-Fusion",
    "adaptive_graph_tcn_hysteresis": "AdaptiveGraphTCN-Hysteresis",
}


DEFAULT_METHODS = list(METHOD_LABELS)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _mean_std(values: list[float]) -> str:
    if not values:
        return "n/a"
    return f"{mean(values):.4f} +/- {pstdev(values):.4f}"


def _metric(run: dict[str, Any], method: str, metric: str) -> float | None:
    value = run.get(method)
    if not isinstance(value, dict) or metric not in value:
        return None
    return float(value[metric])


def _file_label(path: Path, data: dict[str, Any]) -> str:
    if "route" in path.stem:
        return "route_e5"
    if "e12" in path.stem:
        return "main_compare_e12"
    if "e5" in path.stem:
        return "main_compare_e5"
    return str(data.get("task") or path.stem)


def summarize(files: list[Path], methods: list[str]) -> str:
    lines: list[str] = []
    lines.append("# SKAB Baseline Suite Summary")
    lines.append("")
    lines.append("| File | Method | Macro-F1 | Positive F1 | Runs |")
    lines.append("|---|---|---:|---:|---:|")
    best_rows: list[dict[str, Any]] = []
    for path in files:
        data = _load(path)
        runs = list(data.get("runs", []))
        file_label = _file_label(path, data)
        for method in methods:
            macro_values = [
                value
                for value in (_metric(run, method, "macro_f1") for run in runs)
                if value is not None
            ]
            if not macro_values:
                continue
            f1_values = [
                value
                for value in (_metric(run, method, "positive_f1") for run in runs)
                if value is not None
            ]
            row = {
                "file": file_label,
                "method": METHOD_LABELS.get(method, method),
                "macro": _mean_std(macro_values),
                "positive": _mean_std(f1_values),
                "runs": len(macro_values),
                "macro_mean": mean(macro_values),
            }
            best_rows.append(row)
            lines.append(
                "| {file} | {method} | {macro} | {positive} | {runs} |".format(**row)
            )
    lines.append("")
    if best_rows:
        best = max(best_rows, key=lambda row: float(row["macro_mean"]))
        lines.append("## Best Internal Baseline")
        lines.append("")
        lines.append(
            f"- {best['file']} / {best['method']}: Macro-F1 {best['macro']}, Positive F1 {best['positive']}."
        )
        lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "This table is an internal matched-protocol discriminator comparison for SKAB. "
        "It is useful for showing whether graph-temporal inputs help relative to plain TCN, "
        "FT-Transformer, and ExtraTrees. It is not a substitute for official external baselines "
        "such as GDN, MTAD-GAT, TranAD, USAD, or Anomaly Transformer."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize SKAB first-layer baseline comparisons.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--methods", default=",".join(DEFAULT_METHODS))
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()
    methods = [item.strip() for item in str(args.methods).split(",") if item.strip()]
    report = summarize([Path(file) for file in args.files], methods)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
