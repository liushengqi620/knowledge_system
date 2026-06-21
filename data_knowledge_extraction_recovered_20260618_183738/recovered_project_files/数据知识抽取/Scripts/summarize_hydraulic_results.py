from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


METHODS = [
    ("main", "Main"),
    ("ugmc_selective_correction", "UGMC"),
    ("learned_evidence_router", "Learned"),
    ("safe_learned_evidence_router", "SafeLearned"),
    ("ere_reliability_routing", "ERE"),
]


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _mean_std(values: list[float]) -> str:
    if not values:
        return "n/a"
    return f"{mean(values):.4f} +/- {pstdev(values):.4f}"


def summarize(files: list[Path]) -> str:
    rows: list[dict[str, Any]] = []
    for path in files:
        data = _load(path)
        target = str(data.get("target", path.stem))
        runs = data.get("runs", [])
        row: dict[str, Any] = {"target": target, "n_runs": len(runs)}
        for key, label in METHODS:
            values = [
                float(run[key]["macro_f1"])
                for run in runs
                if isinstance(run.get(key), dict) and "macro_f1" in run[key]
            ]
            row[label] = _mean_std(values)
        rows.append(row)
    lines: list[str] = []
    lines.append("# Hydraulic Four-Target Summary")
    lines.append("")
    lines.append("| Target | Runs | Main | UGMC | Learned | SafeLearned | ERE |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for row in rows:
        lines.append(
            "| {target} | {n_runs} | {Main} | {UGMC} | {Learned} | {SafeLearned} | {ERE} |".format(**row)
        )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "Hydraulic validates the industrial state-diagnosis side of the framework. "
        "Cooler and pump are near-ceiling tasks, accumulator is also strong, while valve remains the most "
        "informative target for reliability-routing analysis. Safe learned routing preserves the strong main "
        "classifier when auxiliary evidence is risky, which is consistent with the reliability-calibrated "
        "mechanism-learning principle."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize Hydraulic benchmark results.")
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
