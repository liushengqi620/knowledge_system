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


def summarize(path: Path) -> str:
    data = _load(path)
    methods = [str(method) for method in data.get("methods", [])]
    rows: list[dict[str, Any]] = []
    for method in methods:
        macro: list[float] = []
        binary_f1: list[float] = []
        far: list[float] = []
        mar: list[float] = []
        for run in data.get("runs", []):
            item = run.get(method)
            if not isinstance(item, dict):
                continue
            metrics = item.get("metrics", {})
            protocol = item.get("protocol", {}).get("binary", {})
            if "macro_f1" in metrics:
                macro.append(float(metrics["macro_f1"]))
            if "f1" in protocol:
                binary_f1.append(float(protocol["f1"]))
            if "far_percent" in protocol:
                far.append(float(protocol["far_percent"]))
            if "mar_percent" in protocol:
                mar.append(float(protocol["mar_percent"]))
        rows.append(
            {
                "method": method,
                "macro": _mean_std(macro),
                "binary_f1": _mean_std(binary_f1),
                "far": _mean_std(far),
                "mar": _mean_std(mar),
                "runs": len(macro),
            }
        )
    lines: list[str] = []
    lines.append("# SKAB External Reconstruction Baselines")
    lines.append("")
    lines.append("| Method | Macro-F1 | Binary F1 | FAR | MAR | Runs |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for row in rows:
        lines.append(
            "| {method} | {macro} | {binary_f1} | {far} | {mar} | {runs} |".format(**row)
        )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "USAD-style, TranAD-style, and Anomaly-Transformer-style reconstruction/association-discrepancy baselines "
        "are external-style anomaly baselines under the same SKAB run-level split. Their high FAR/MAR shows that "
        "raw reconstruction or association discrepancy alone does not solve the protocol-stable SKAB setting. "
        "They should be reported as preliminary external-style baselines, with official GDN/MTAD-GAT/TranAD/USAD/"
        "Anomaly-Transformer replications still desirable."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize SKAB external reconstruction baselines.")
    parser.add_argument("--output", required=True)
    parser.add_argument("file")
    args = parser.parse_args()
    report = summarize(Path(args.file))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
