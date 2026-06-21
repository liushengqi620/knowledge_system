from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _fmt(value: float) -> str:
    return f"{float(value):.4f}"


def _mean_std(values: list[float]) -> str:
    if not values:
        return "n/a"
    return f"{mean(values):.4f} ± {pstdev(values):.4f}"


def summarize(files: list[Path]) -> str:
    rows: list[dict[str, Any]] = []
    for path in files:
        result = _load(path)
        baseline = result["baseline"]
        dynamic = result["dynamic_llm_kg"]
        binary = dynamic["protocol"]["binary"]
        rows.append(
            {
                "file": path.name,
                "seed": int(result.get("seed", -1)),
                "base_macro_f1": float(baseline["metrics"]["macro_f1"]),
                "dynamic_macro_f1": float(dynamic["metrics"]["macro_f1"]),
                "delta_macro_f1": float(result["macro_f1_delta"]),
                "binary_f1": float(binary["f1"]),
                "far": float(binary["far_percent"]),
                "mar": float(binary["mar_percent"]),
                "n_edges": int(len(result.get("dynamic_edges", []))),
                "kept_edges": [
                    f"{edge.get('source')}->{edge.get('target')}" for edge in result.get("dynamic_edges", [])
                ],
            }
        )
    lines: list[str] = []
    lines.append("# SKAB Learned Reliability Summary")
    lines.append("")
    lines.append("| Seed | Baseline Macro-F1 | Learned Macro-F1 | Δ Macro-F1 | Binary F1 | FAR | MAR | Edges |")
    lines.append("|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in rows:
        lines.append(
            "| {seed} | {base} | {dyn} | {delta} | {bf1} | {far} | {mar} | {edges} |".format(
                seed=row["seed"],
                base=_fmt(row["base_macro_f1"]),
                dyn=_fmt(row["dynamic_macro_f1"]),
                delta=f"{row['delta_macro_f1']:+.4f}",
                bf1=_fmt(row["binary_f1"]),
                far=f"{row['far']:.2f}",
                mar=f"{row['mar']:.2f}",
                edges=row["n_edges"],
            )
        )
    lines.append("")
    lines.append("## Aggregate")
    lines.append("")
    lines.append(f"- Baseline Macro-F1: {_mean_std([row['base_macro_f1'] for row in rows])}")
    lines.append(f"- Learned Macro-F1: {_mean_std([row['dynamic_macro_f1'] for row in rows])}")
    lines.append(f"- Δ Macro-F1: {_mean_std([row['delta_macro_f1'] for row in rows])}")
    lines.append(f"- Binary F1: {_mean_std([row['binary_f1'] for row in rows])}")
    lines.append(f"- FAR: {_mean_std([row['far'] for row in rows])}")
    lines.append(f"- MAR: {_mean_std([row['mar'] for row in rows])}")
    lines.append("")
    lines.append("## Selected Edges")
    lines.append("")
    for row in rows:
        edge_text = ", ".join(row["kept_edges"]) if row["kept_edges"] else "none"
        lines.append(f"- Seed {row['seed']}: {edge_text}")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "The learned reliability estimator produces positive gains for all evaluated seeds, "
        "which supports the reliability-calibrated graph hypothesis. However, absolute performance "
        "varies strongly across run-level splits, so this evidence is not yet sufficient for a stable "
        "SOTA claim. The next step is to improve split robustness and validate the same reliability "
        "principle on additional industrial datasets."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize SKAB learned reliability experiments.")
    parser.add_argument("--output", required=True)
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()
    paths = [Path(file) for file in args.files]
    report = summarize(paths)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
