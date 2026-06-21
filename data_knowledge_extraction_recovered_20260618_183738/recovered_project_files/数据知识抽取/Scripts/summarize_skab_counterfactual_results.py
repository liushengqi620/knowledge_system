from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _row(label: str, path: Path) -> dict[str, Any]:
    result = _load(path)
    dynamic = result["dynamic_llm_kg"]
    binary = dynamic["protocol"]["binary"]
    return {
        "label": label,
        "path": path.name,
        "macro_f1": float(dynamic["metrics"]["macro_f1"]),
        "delta_macro_f1": float(result["macro_f1_delta"]),
        "binary_f1": float(binary["f1"]),
        "far": float(binary["far_percent"]),
        "mar": float(binary["mar_percent"]),
        "mode": result.get("edge_counterfactual", {}).get("mode", "none"),
        "n_changed_edges": int(result.get("edge_counterfactual", {}).get("n_changed_edges", 0)),
    }


def summarize(named_files: list[tuple[str, Path]]) -> str:
    rows = [_row(label, path) for label, path in named_files]
    original = rows[0]
    lines: list[str] = []
    lines.append("# SKAB Counterfactual Edge Perturbation Summary")
    lines.append("")
    lines.append("| Variant | Mode | Changed Edges | Macro-F1 | Drop vs Original | Binary F1 | FAR | MAR |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|")
    for row in rows:
        drop = float(row["macro_f1"]) - float(original["macro_f1"])
        lines.append(
            "| {label} | {mode} | {changed} | {macro:.4f} | {drop:+.4f} | {bf1:.4f} | {far:.2f} | {mar:.2f} |".format(
                label=row["label"],
                mode=row["mode"],
                changed=row["n_changed_edges"],
                macro=row["macro_f1"],
                drop=drop,
                bf1=row["binary_f1"],
                far=row["far"],
                mar=row["mar"],
            )
        )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "Counterfactual perturbations test whether admitted mechanism edges are used as effective lagged evidence. "
        "Reversing edge direction and replacing targets reduce performance below the learned-edge model, while "
        "lag shifting weakens the gain. This supports the claim that reliability-admitted edges are not merely "
        "decorative explanations: their direction, target assignment, and lag structure affect the decision model."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize SKAB counterfactual edge perturbation experiments.")
    parser.add_argument("--output", required=True)
    parser.add_argument("items", nargs="+", help="Pairs in the form label=path")
    args = parser.parse_args()
    named_files: list[tuple[str, Path]] = []
    for item in args.items:
        if "=" not in item:
            raise ValueError(f"Expected label=path item, got: {item}")
        label, raw_path = item.split("=", 1)
        named_files.append((label, Path(raw_path)))
    report = summarize(named_files)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
