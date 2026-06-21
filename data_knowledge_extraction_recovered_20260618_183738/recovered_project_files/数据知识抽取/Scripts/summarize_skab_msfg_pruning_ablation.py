from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


MODE_ORDER = [
    "original_full_msfg",
    "full_pruned_kg",
    "no_llm_pruned_kg",
    "expert_only_pruned_kg",
    "llm_only",
    "data_only",
]


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _mean_std(values: list[float]) -> str:
    if not values:
        return "n/a"
    return f"{mean(values):.4f} +/- {pstdev(values):.4f}"


def _mode_sort_key(mode: str) -> tuple[int, str]:
    return (MODE_ORDER.index(mode) if mode in MODE_ORDER else len(MODE_ORDER), mode)


def _collect_runs(paths: list[Path]) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    for path in paths:
        data = _load(path)
        for run in data.get("runs", []) or []:
            row = dict(run)
            row["_source_file"] = path.name
            runs.append(row)
    return runs


def summarize(paths: list[Path]) -> str:
    runs = _collect_runs(paths)
    by_mode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_seed_mode: dict[tuple[int, str], dict[str, Any]] = {}
    for run in runs:
        mode = str(run.get("mode", "unknown"))
        by_mode[mode].append(run)
        if "seed" in run:
            by_seed_mode[(int(run["seed"]), mode)] = run
    original_by_seed = {
        seed: run
        for (seed, mode), run in by_seed_mode.items()
        if mode == "original_full_msfg"
    }

    lines: list[str] = []
    lines.append("# SKAB MSFG Source-Pruning Ablation Summary")
    lines.append("")
    lines.append("| Mode | Runs | Macro-F1 | Delta vs Original | Point-Adjusted F1 | FAR % | Fused Edges |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for mode in sorted(by_mode, key=_mode_sort_key):
        rows = by_mode[mode]
        macro = [float(row["macro_f1"]) for row in rows]
        point = [float(row["point_adjusted_f1"]) for row in rows if "point_adjusted_f1" in row]
        far = [float(row["far_percent"]) for row in rows if "far_percent" in row]
        fused = [
            float(row.get("fusion", {}).get("n_fused_edges", 0.0))
            for row in rows
            if isinstance(row.get("fusion"), dict)
        ]
        deltas: list[float] = []
        for row in rows:
            seed = row.get("seed")
            if seed is None:
                continue
            original = original_by_seed.get(int(seed))
            if original is None:
                continue
            deltas.append(float(row["macro_f1"]) - float(original["macro_f1"]))
        delta_text = "+0.0000" if mode == "original_full_msfg" else _mean_std(deltas)
        if mode != "original_full_msfg" and deltas:
            delta_text = delta_text.replace("0.", "+0.", 1) if not delta_text.startswith("-") else delta_text
        lines.append(
            "| {mode} | n={n} | {macro} | {delta} | {point} | {far} | {fused} |".format(
                mode=mode,
                n=len(rows),
                macro=_mean_std(macro),
                delta=delta_text,
                point=_mean_std(point),
                far=_mean_std(far),
                fused=_mean_std(fused),
            )
        )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "This table isolates source-role behavior in the SKAB multi-source fusion graph. "
        "The original full MSFG is the unpruned reference. Reliability pruning removes unsupported source-specific edges, "
        "while no-LLM, expert-only, LLM-only, and data-only modes test whether each source family can stand alone. "
        "Because this run uses a low e1 sequence budget, it supports the reliability-term argument but should be upgraded "
        "before final SOTA claims."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize SKAB MSFG source/pruning ablation JSON files.")
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
