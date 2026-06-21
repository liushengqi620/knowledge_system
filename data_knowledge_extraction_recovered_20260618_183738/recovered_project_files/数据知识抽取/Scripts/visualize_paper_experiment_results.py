from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
from typing import Any


EXPECTED_FIGURES = [
    "main_multi_benchmark_results.png",
    "main_multi_benchmark_delta.png",
    "reliability_ablation_summary.png",
    "tep_mechanism_ablation.png",
    "tep_matched_baselines.png",
    "skab_external_baselines.png",
    "hydraulic_four_target_results.png",
    "cmapss_rul_matched_results.png",
]


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def build_experiment_tables() -> dict[str, list[dict[str, Any]]]:
    return {
        "main_multi_benchmark": [
            {"dataset": "TEP", "main": 0.9122, "main_std": 0.0134, "proposed": 0.9549, "proposed_std": 0.0023, "delta": 0.0428},
            {"dataset": "SKAB", "main": 0.8193, "main_std": 0.0283, "proposed": 0.8209, "proposed_std": 0.0220, "delta": 0.0016},
            {"dataset": "Hydraulic", "main": 0.9773, "main_std": 0.0321, "proposed": 0.9784, "proposed_std": 0.0301, "delta": 0.0011},
            {
                "dataset": "C-MAPSS",
                "main": 1.0000,
                "main_std": 0.0,
                "proposed": 20.6822 / 18.2840,
                "proposed_std": 0.0,
                "delta": (20.6822 / 18.2840) - 1.0,
            },
        ],
        "reliability_ablation": [
            {"case": "anchor", "dataset": "SKAB", "metric": 0.8193, "std": 0.0283, "baseline": 0.8193, "note": "native-audited anchor"},
            {"case": "LLM verifier", "dataset": "SKAB", "metric": 0.8209, "std": 0.0220, "baseline": 0.8193, "note": "condition verifier"},
            {"case": "prior-only", "dataset": "SKAB", "metric": 0.8327, "std": 0.0477, "baseline": 0.8343, "note": "historical raw prior"},
            {"case": "all-edge", "dataset": "SKAB", "metric": 0.8528, "std": 0.0322, "baseline": 0.8343, "note": "historical dense graph"},
            {"case": "source-pruned e5", "dataset": "SKAB", "metric": 0.7093, "std": 0.0572, "baseline": 0.6730, "note": "source complexity pruning"},
            {"case": "rul cap/window", "dataset": "C-MAPSS", "metric": 20.6822 / 18.2840, "std": 0.0, "baseline": 1.0, "note": "pseudo-terminal validated RMSE; path closed"},
        ],
        "tep_mechanism_ablation": [
            {"variant": "Full", "target_f1": 0.9549, "std": 0.0023, "delta": 0.0000},
            {"variant": "No expert/seq graph", "target_f1": 0.7432, "std": 0.0102, "delta": -0.2118},
            {"variant": "No LLM graph", "target_f1": 0.9337, "std": 0.0229, "delta": -0.0212},
            {"variant": "All edges/no reliability", "target_f1": 0.9260, "std": 0.0344, "delta": -0.0290},
            {"variant": "No residual verifier", "target_f1": 0.9398, "std": 0.0160, "delta": -0.0151},
            {"variant": "No pairwise guard", "target_f1": 0.9122, "std": 0.0134, "delta": -0.0428},
        ],
        "tep_matched_baselines": [
            {"method": "TCN NoGraph", "target_f1": 0.5754, "std": 0.0141, "family": "TCN"},
            {"method": "TCN ResidualGraph", "target_f1": 0.6034, "std": 0.0096, "family": "TCN"},
            {"method": "GRU NoGraph", "target_f1": 0.6150, "std": 0.0030, "family": "GRU"},
            {"method": "GRU ResidualGraph", "target_f1": 0.6217, "std": 0.0073, "family": "GRU"},
            {"method": "FT NoGraph", "target_f1": 0.4644, "std": 0.0110, "family": "FT"},
            {"method": "FT ResidualGraph", "target_f1": 0.5136, "std": 0.0218, "family": "FT"},
            {"method": "GDN ResidualGraph", "target_f1": 0.5179, "std": 0.0372, "family": "GDN"},
            {"method": "MTAD-GAT ResidualGraph", "target_f1": 0.6447, "std": 0.0038, "family": "MTAD-GAT"},
            {"method": "Strict Mechanism", "target_f1": 0.9549, "std": 0.0023, "family": "Ours"},
        ],
        "skab_external_baselines": [
            {"method": "USAD-style", "macro_f1": 0.4759, "binary_f1": 0.4062, "far": 52.3516, "mar": 49.6254},
            {"method": "TranAD-style", "macro_f1": 0.5366, "binary_f1": 0.4675, "far": 46.5718, "mar": 41.5024},
            {"method": "GDN-style", "macro_f1": 0.5409, "binary_f1": 0.4248, "far": 37.0108, "mar": 53.9256},
            {"method": "MTAD-GAT-style", "macro_f1": 0.5310, "binary_f1": 0.4672, "far": 47.8332, "mar": 40.0434},
            {"method": "Ours", "macro_f1": 0.8209, "binary_f1": 0.7788, "far": 8.3906, "mar": 28.6639},
        ],
        "hydraulic_four_target": [
            {"target": "Cooler", "main": 1.0000, "safe": 1.0000, "main_std": 0.0000, "safe_std": 0.0000},
            {"target": "Valve", "main": 0.9280, "safe": 0.9315, "main_std": 0.0272, "safe_std": 0.0237},
            {"target": "Pump", "main": 0.9960, "safe": 0.9960, "main_std": 0.0030, "safe_std": 0.0030},
            {"target": "Accumulator", "main": 0.9850, "safe": 0.9860, "main_std": 0.0028, "safe_std": 0.0037},
        ],
        "cmapss_rul_matched": [
            {"method": "HistGB", "rmse": 23.4635, "rmse_std": 0.1624, "mae": 15.3453, "score": 13625.12},
            {"method": "ExtraTrees", "rmse": 23.8914, "rmse_std": 0.1563, "mae": 15.8278, "score": 13690.52},
            {"method": "TCN w80/c125", "rmse": 25.8894, "rmse_std": 0.2915, "mae": 18.3569, "score": 19477.53},
            {"method": "GRU w80/c125", "rmse": 20.7559, "rmse_std": 0.1402, "mae": 13.3039, "score": 7531.00},
            {"method": "GRU w80/c150", "rmse": 18.4365, "rmse_std": 0.1686, "mae": 12.5441, "score": 6428.78},
            {"method": "GRU w160/c150", "rmse": 18.0617, "rmse_std": 0.3621, "mae": 12.0648, "score": 6525.46},
            {"method": "GRU w160/c150 pseudo", "rmse": 18.2840, "rmse_std": 0.1324, "mae": None, "score": 6619.39},
            {"method": "AnchorPath w80/c150", "rmse": 18.6666, "rmse_std": 0.2067, "mae": 12.6793, "score": 6981.54},
        ],
    }


def _load_pyplot():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "legend.fontsize": 9,
            "figure.dpi": 150,
        }
    )
    return plt


def _annotate_bars(ax: Any, bars: Any, fmt: str = "{:.3f}") -> None:
    for bar in bars:
        height = float(bar.get_height())
        ax.annotate(
            fmt.format(height),
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
        )


def _save_main_results(output_dir: Path, tables: dict[str, list[dict[str, Any]]]) -> Path:
    plt = _load_pyplot()
    rows = tables["main_multi_benchmark"]
    labels = [row["dataset"] for row in rows]
    x = range(len(rows))
    width = 0.36
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    bars_main = ax.bar([i - width / 2 for i in x], [row["main"] for row in rows], width, yerr=[row["main_std"] for row in rows], label="Anchor/Main", color="#4e79a7", capsize=3)
    bars_prop = ax.bar([i + width / 2 for i in x], [row["proposed"] for row in rows], width, yerr=[row["proposed_std"] for row in rows], label="Reliable Route", color="#59a14f", capsize=3)
    ax.set_title("Main Multi-Benchmark Results")
    ax.set_ylabel("Primary score / normalized RMSE gain")
    ax.set_xticks(list(x), labels)
    ax.set_ylim(0.72, 1.18)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(loc="lower right")
    _annotate_bars(ax, bars_main)
    _annotate_bars(ax, bars_prop)
    fig.tight_layout()
    path = output_dir / "main_multi_benchmark_results.png"
    fig.savefig(_fs_path(path), bbox_inches="tight")
    plt.close(fig)
    return path


def _save_main_delta(output_dir: Path, tables: dict[str, list[dict[str, Any]]]) -> Path:
    plt = _load_pyplot()
    rows = tables["main_multi_benchmark"]
    rows_sorted = sorted(rows, key=lambda row: row["delta"])
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    bars = ax.barh([row["dataset"] for row in rows_sorted], [row["delta"] for row in rows_sorted], color="#f28e2b")
    ax.set_title("Reliable Route Gain over Anchor")
    ax.set_xlabel("Delta primary score")
    ax.axvline(0, color="#333333", linewidth=0.8)
    ax.grid(axis="x", alpha=0.25)
    for bar in bars:
        width = float(bar.get_width())
        ax.annotate(f"+{width:.4f}", xy=(width, bar.get_y() + bar.get_height() / 2), xytext=(4, 0), textcoords="offset points", va="center", fontsize=8)
    fig.tight_layout()
    path = output_dir / "main_multi_benchmark_delta.png"
    fig.savefig(_fs_path(path), bbox_inches="tight")
    plt.close(fig)
    return path


def _save_reliability_ablation(output_dir: Path, tables: dict[str, list[dict[str, Any]]]) -> Path:
    plt = _load_pyplot()
    rows = tables["reliability_ablation"]
    labels = [row["case"] for row in rows]
    values = [row["metric"] for row in rows]
    baselines = [row["baseline"] for row in rows]
    fig, ax = plt.subplots(figsize=(9.2, 4.8))
    bars = ax.bar(labels, values, yerr=[row["std"] for row in rows], color=["#59a14f", "#bab0ac", "#edc948", "#b07aa1", "#76b7b2", "#9c755f"], capsize=3)
    ax.scatter(labels, baselines, color="#e15759", marker="D", label="Reference baseline", zorder=3)
    ax.set_title("Reliability Admission Ablations")
    ax.set_ylabel("Score")
    ax.set_ylim(0.60, 0.90)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(loc="lower right")
    ax.tick_params(axis="x", rotation=22)
    _annotate_bars(ax, bars)
    fig.tight_layout()
    path = output_dir / "reliability_ablation_summary.png"
    fig.savefig(_fs_path(path), bbox_inches="tight")
    plt.close(fig)
    return path


def _save_tep_ablation(output_dir: Path, tables: dict[str, list[dict[str, Any]]]) -> Path:
    plt = _load_pyplot()
    rows = tables["tep_mechanism_ablation"]
    rows_sorted = sorted(rows, key=lambda row: row["target_f1"])
    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    colors = ["#e15759" if row["variant"] != "Full" else "#59a14f" for row in rows_sorted]
    bars = ax.barh([row["variant"] for row in rows_sorted], [row["target_f1"] for row in rows_sorted], xerr=[row["std"] for row in rows_sorted], color=colors, capsize=3)
    ax.set_title("TEP Mechanism Ablation")
    ax.set_xlabel("Target-F1")
    ax.set_xlim(0.70, 0.98)
    ax.grid(axis="x", alpha=0.25)
    for bar in bars:
        width = float(bar.get_width())
        ax.annotate(f"{width:.3f}", xy=(width, bar.get_y() + bar.get_height() / 2), xytext=(4, 0), textcoords="offset points", va="center", fontsize=8)
    fig.tight_layout()
    path = output_dir / "tep_mechanism_ablation.png"
    fig.savefig(_fs_path(path), bbox_inches="tight")
    plt.close(fig)
    return path


def _save_tep_baselines(output_dir: Path, tables: dict[str, list[dict[str, Any]]]) -> Path:
    plt = _load_pyplot()
    rows = tables["tep_matched_baselines"]
    fig, ax = plt.subplots(figsize=(10.2, 5.2))
    colors = ["#59a14f" if row["family"] == "Ours" else "#4e79a7" if "ResidualGraph" in row["method"] else "#bab0ac" for row in rows]
    bars = ax.bar([row["method"] for row in rows], [row["target_f1"] for row in rows], yerr=[row["std"] for row in rows], color=colors, capsize=3)
    ax.set_title("TEP Matched Strong Baselines")
    ax.set_ylabel("Target-F1")
    ax.set_ylim(0.20, 1.02)
    ax.grid(axis="y", alpha=0.25)
    ax.tick_params(axis="x", rotation=38)
    _annotate_bars(ax, bars)
    fig.tight_layout()
    path = output_dir / "tep_matched_baselines.png"
    fig.savefig(_fs_path(path), bbox_inches="tight")
    plt.close(fig)
    return path


def _save_skab_baselines(output_dir: Path, tables: dict[str, list[dict[str, Any]]]) -> Path:
    plt = _load_pyplot()
    rows = tables["skab_external_baselines"]
    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    bars = ax.bar([row["method"] for row in rows], [row["macro_f1"] for row in rows], color=["#bab0ac", "#bab0ac", "#bab0ac", "#bab0ac", "#59a14f"])
    ax.set_title("SKAB Matched External-Style Baselines")
    ax.set_ylabel("Macro-F1")
    ax.set_ylim(0.35, 0.90)
    ax.grid(axis="y", alpha=0.25)
    ax.tick_params(axis="x", rotation=20)
    _annotate_bars(ax, bars)
    fig.tight_layout()
    path = output_dir / "skab_external_baselines.png"
    fig.savefig(_fs_path(path), bbox_inches="tight")
    plt.close(fig)
    return path


def _save_hydraulic(output_dir: Path, tables: dict[str, list[dict[str, Any]]]) -> Path:
    plt = _load_pyplot()
    rows = tables["hydraulic_four_target"]
    labels = [row["target"] for row in rows]
    x = range(len(rows))
    width = 0.36
    fig, ax = plt.subplots(figsize=(8.0, 4.8))
    bars_main = ax.bar([i - width / 2 for i in x], [row["main"] for row in rows], width, yerr=[row["main_std"] for row in rows], color="#4e79a7", label="Main", capsize=3)
    bars_safe = ax.bar([i + width / 2 for i in x], [row["safe"] for row in rows], width, yerr=[row["safe_std"] for row in rows], color="#59a14f", label="SafeLearned", capsize=3)
    ax.set_title("Hydraulic Four-Target State Diagnosis")
    ax.set_ylabel("Target score")
    ax.set_xticks(list(x), labels)
    ax.set_ylim(0.90, 1.01)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(loc="lower right")
    _annotate_bars(ax, bars_main)
    _annotate_bars(ax, bars_safe)
    fig.tight_layout()
    path = output_dir / "hydraulic_four_target_results.png"
    fig.savefig(_fs_path(path), bbox_inches="tight")
    plt.close(fig)
    return path


def _save_cmapss_rul(output_dir: Path, tables: dict[str, list[dict[str, Any]]]) -> Path:
    plt = _load_pyplot()
    rows = tables["cmapss_rul_matched"]
    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    colors = ["#bab0ac", "#bab0ac", "#bab0ac", "#4e79a7", "#76b7b2", "#59a14f", "#8cd17d", "#e15759"]
    bars = ax.bar([row["method"] for row in rows], [row["rmse"] for row in rows], yerr=[row["rmse_std"] for row in rows], color=colors, capsize=3)
    ax.set_title("C-MAPSS Original RUL Matched Baselines")
    ax.set_ylabel("Terminal RMSE (lower is better)")
    ax.set_ylim(17.4, 27.0)
    ax.grid(axis="y", alpha=0.25)
    ax.tick_params(axis="x", rotation=20)
    _annotate_bars(ax, bars, fmt="{:.2f}")
    fig.tight_layout()
    path = output_dir / "cmapss_rul_matched_results.png"
    fig.savefig(_fs_path(path), bbox_inches="tight")
    plt.close(fig)
    return path


def _write_flat_csv(output_dir: Path, tables: dict[str, list[dict[str, Any]]]) -> Path:
    path = output_dir / "experiment_visualization_source_data.csv"
    fieldnames = ["group", "name", "metric_a", "metric_b", "metric_c", "std_a", "std_b", "delta", "note"]
    with open(_fs_path(path), "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in tables["main_multi_benchmark"]:
            writer.writerow({"group": "main_multi_benchmark", "name": row["dataset"], "metric_a": row["main"], "metric_b": row["proposed"], "std_a": row["main_std"], "std_b": row["proposed_std"], "delta": row["delta"], "note": "anchor vs reliable route"})
        for row in tables["reliability_ablation"]:
            writer.writerow({"group": "reliability_ablation", "name": row["case"], "metric_a": row["baseline"], "metric_b": row["metric"], "std_b": row["std"], "delta": row["metric"] - row["baseline"], "note": row["note"]})
        for row in tables["tep_mechanism_ablation"]:
            writer.writerow({"group": "tep_mechanism_ablation", "name": row["variant"], "metric_a": row["target_f1"], "std_a": row["std"], "delta": row["delta"], "note": "target_f1"})
        for row in tables["tep_matched_baselines"]:
            writer.writerow({"group": "tep_matched_baselines", "name": row["method"], "metric_a": row["target_f1"], "std_a": row["std"], "note": row["family"]})
        for row in tables["skab_external_baselines"]:
            writer.writerow({"group": "skab_external_baselines", "name": row["method"], "metric_a": row["macro_f1"], "metric_b": row["binary_f1"], "metric_c": row["far"], "note": f"MAR={row['mar']:.4f}"})
        for row in tables["hydraulic_four_target"]:
            writer.writerow({"group": "hydraulic_four_target", "name": row["target"], "metric_a": row["main"], "metric_b": row["safe"], "std_a": row["main_std"], "std_b": row["safe_std"], "delta": row["safe"] - row["main"], "note": "main vs safe learned"})
        for row in tables["cmapss_rul_matched"]:
            writer.writerow({"group": "cmapss_rul_matched", "name": row["method"], "metric_a": row["rmse"], "metric_b": row["mae"], "metric_c": row["score"], "std_a": row["rmse_std"], "note": "terminal RUL regression"})
    return path


def render_visualization_report(output_dir: Path) -> str:
    lines: list[str] = []
    lines.append("# Paper Experiment Result Visualizations")
    lines.append("")
    lines.append(
        "This directory visualizes the consolidated paper-level experiment results under the current matched-protocol setting. "
        "The figures support the method-evidence narrative and the TEP SOTA candidate claim under matched protocol; they are not official universal SOTA evidence."
    )
    lines.append("")
    lines.append("## Figure Index")
    lines.append("")
    descriptions = {
        "main_multi_benchmark_results.png": "Anchor/Main vs reliable route on TEP, SKAB, Hydraulic, and C-MAPSS; C-MAPSS uses the pseudo-terminal validation-safe RMSE rerun because lower is better.",
        "main_multi_benchmark_delta.png": "Absolute gain of the reliable route over the anchor.",
        "reliability_ablation_summary.png": "Reliability admission, prior-only, all-edge, counterfactual, pruning, and low-tail contrasts.",
        "tep_mechanism_ablation.png": "TEP mechanism ablation proving expert/LLM/reliability/residual modules are not decorative.",
        "tep_matched_baselines.png": "TEP matched strong baselines and the strict mechanism result.",
        "skab_external_baselines.png": "SKAB matched external-style reconstruction baselines versus the learned reliability route.",
        "hydraulic_four_target_results.png": "Hydraulic four-target main vs SafeLearned comparison.",
        "cmapss_rul_matched_results.png": "C-MAPSS original terminal RUL RMSE with cap/window repair, pseudo-terminal validation-safe rerun, PHM score trade-off, and non-admitted AnchorPath challenger.",
    }
    for figure_name in EXPECTED_FIGURES:
        figure_path = output_dir / figure_name
        lines.append(f"| `{figure_name}` | {descriptions[figure_name]} |")
        if not lines[-2].startswith("| Figure"):
            pass
    lines.insert(lines.index("| `main_multi_benchmark_results.png` | Anchor/Main vs reliable route on TEP, SKAB, Hydraulic, and C-MAPSS; C-MAPSS uses the pseudo-terminal validation-safe RMSE rerun because lower is better. |"), "| Figure | Meaning |")
    lines.insert(lines.index("| Figure | Meaning |") + 1, "|---|---|")
    lines.append("")
    lines.append("## Claim Boundary")
    lines.append("")
    lines.append(
        "Use these plots as manuscript visual evidence for matched-protocol experiments. TEP is the current strongest SOTA candidate, "
        "while SKAB, Hydraulic, and C-MAPSS support reliability filtering, non-degradation, and RMSE-oriented original-task RUL transfer with the C-MAPSS PHM score trade-off disclosed. "
        "Do not describe the plots as official universal SOTA until external split, preprocessing, metric, threshold, delay, and budget alignment is completed."
    )
    lines.append("")
    lines.append("## Source Data")
    lines.append("")
    lines.append("The flattened plotting table is saved as `experiment_visualization_source_data.csv`.")
    lines.append("")
    return "\n".join(lines)


def generate_all_visualizations(output_dir: Path) -> list[Path]:
    os.makedirs(_fs_path(output_dir), exist_ok=True)
    tables = build_experiment_tables()
    artifacts = [
        _save_main_results(output_dir, tables),
        _save_main_delta(output_dir, tables),
        _save_reliability_ablation(output_dir, tables),
        _save_tep_ablation(output_dir, tables),
        _save_tep_baselines(output_dir, tables),
        _save_skab_baselines(output_dir, tables),
        _save_hydraulic(output_dir, tables),
        _save_cmapss_rul(output_dir, tables),
        _write_flat_csv(output_dir, tables),
    ]
    report = render_visualization_report(output_dir)
    report_path = output_dir / "experiment_visualization_report.md"
    with open(_fs_path(report_path), "w", encoding="utf-8") as handle:
        handle.write(report)
    artifacts.append(report_path)
    return artifacts


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate paper-level experiment result visualizations.")
    parser.add_argument("--output-dir", default="knowledge_exports/paper_experiment_visualizations")
    args = parser.parse_args(argv)
    artifacts = generate_all_visualizations(Path(args.output_dir))
    for artifact in artifacts:
        print(artifact)


if __name__ == "__main__":
    main()
