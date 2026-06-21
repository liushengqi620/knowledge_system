#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate clean chart-only result insets for EAPA figures.

The output intentionally removes decorative frames, badges, flow arrows, and
large explanatory panels. It keeps only chart/matrix content suitable for
embedding into a larger mechanism figure.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "figures" / "eapa_result_insets_clean"

COLORS = {
    "ink": "#172033",
    "muted": "#64748B",
    "red": "#C81E1E",
    "red_light": "#FECACA",
    "purple": "#5B2DB7",
    "teal": "#008C89",
    "orange": "#D26400",
    "green": "#147A35",
    "gold": "#A66A00",
}


def apply_style():
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "mathtext.fontset": "dejavusans",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.edgecolor": "#CBD5E1",
            "xtick.color": COLORS["muted"],
            "ytick.color": COLORS["muted"],
            "axes.labelcolor": COLORS["muted"],
        }
    )


def save(fig, name):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_DIR / f"{name}.png", dpi=420, bbox_inches="tight", pad_inches=0.04)
    fig.savefig(OUT_DIR / f"{name}.pdf", bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)


def draw_error_bar():
    labels = ["Entity", "Relation", "Validity"]
    values = [0.153, 0.098, 0.040]

    fig, ax = plt.subplots(figsize=(3.4, 2.1))
    ax.barh(labels, values, color=[COLORS["red"], "#E34B4B", "#F17A7A"], height=0.46)
    ax.set_xlim(0, 0.18)
    ax.set_xlabel("Error rate", fontsize=8)
    ax.tick_params(labelsize=8)
    ax.invert_yaxis()
    ax.grid(axis="x", color="#E2E8F0", linewidth=0.7)
    for y, v in enumerate(values):
        ax.text(v + 0.004, y, f"{v:.3f}", va="center", ha="left", fontsize=8, color=COLORS["ink"])
    ax.set_title("Error profile", fontsize=9, color=COLORS["ink"], fontweight="bold", pad=6)
    save(fig, "01_error_profile_bar")


def draw_pattern_bar():
    labels = ["P1", "P2", "P3", "Other"]
    values = [0.10, 0.14, 0.19, 0.12]

    fig, ax = plt.subplots(figsize=(3.2, 2.1))
    bars = ax.bar(labels, values, color=COLORS["purple"], width=0.55)
    ax.set_ylim(0, 0.22)
    ax.set_ylabel("Frequency", fontsize=8)
    ax.tick_params(labelsize=8)
    ax.grid(axis="y", color="#E2E8F0", linewidth=0.7)
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.006, f"{v:.2f}", ha="center", va="bottom", fontsize=7, color=COLORS["ink"])
    ax.set_title("Dominant patterns", fontsize=9, color=COLORS["ink"], fontweight="bold", pad=6)
    save(fig, "02_dominant_patterns_bar")


def draw_attribution_heatmap():
    atoms = ["uF2", "uS3", "uS7", "uD2", "uV4"]
    patterns = ["P1", "P2", "P3"]
    values = np.array(
        [
            [0.25, 0.15, 0.05],
            [0.68, 0.44, 0.10],
            [0.24, 0.90, 0.86],
            [0.38, 0.68, 0.36],
            [0.08, 0.50, 0.92],
        ]
    )

    fig, ax = plt.subplots(figsize=(2.6, 2.6))
    im = ax.imshow(values, cmap="YlGnBu", vmin=0, vmax=1)
    ax.set_xticks(range(len(patterns)), patterns)
    ax.set_yticks(range(len(atoms)), atoms)
    ax.tick_params(labelsize=8)
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            color = "white" if values[i, j] > 0.65 else COLORS["ink"]
            ax.text(j, i, f"{values[i, j]:.2f}", ha="center", va="center", fontsize=7, color=color)
    ax.set_title("Atom attribution", fontsize=9, color=COLORS["ink"], fontweight="bold", pad=6)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.tick_params(labelsize=7, colors=COLORS["muted"])
    cbar.set_label("Score", fontsize=7, color=COLORS["muted"])
    save(fig, "03_attribution_heatmap")


def draw_candidate_metric_matrix():
    moves = ["Enhance", "Replace", "Weaken", "Delete"]
    metrics = ["dJ", "dKHR", "dQ", "Risk"]
    values = np.array(
        [
            [0.021, -0.034, 0.018, 0.20],
            [0.016, 0.011, -0.006, 0.55],
            [-0.008, 0.000, -0.003, 0.55],
            [-0.030, 0.025, -0.018, 0.90],
        ]
    )
    display = np.array(
        [
            [0.75, 0.85, 0.75, 0.20],
            [0.68, 0.35, 0.40, 0.55],
            [0.35, 0.50, 0.42, 0.55],
            [0.18, 0.25, 0.20, 0.90],
        ]
    )

    fig, ax = plt.subplots(figsize=(3.7, 2.6))
    im = ax.imshow(display, cmap="RdYlGn_r", vmin=0, vmax=1)
    ax.set_xticks(range(len(metrics)), metrics)
    ax.set_yticks(range(len(moves)), moves)
    ax.tick_params(labelsize=8)
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            text = f"{values[i, j]:+.3f}" if j < 3 else ["Low", "Med", "Med", "High"][i]
            ax.text(j, i, text, ha="center", va="center", fontsize=7, color=COLORS["ink"])
    ax.set_title("Candidate metrics", fontsize=9, color=COLORS["ink"], fontweight="bold", pad=6)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.tick_params(labelsize=7, colors=COLORS["muted"])
    cbar.set_label("Decision cost", fontsize=7, color=COLORS["muted"])
    save(fig, "04_candidate_metric_matrix")


def draw_update_delta_bar():
    labels = ["Before", "After"]
    rel_f1 = [0.765, 0.843]
    khr = [0.291, 0.038]

    x = np.arange(len(labels))
    width = 0.32
    fig, ax1 = plt.subplots(figsize=(3.4, 2.3))
    ax1.bar(x - width / 2, rel_f1, width, color=COLORS["green"], label="RE F1")
    ax1.set_ylim(0, 1.0)
    ax1.set_ylabel("RE F1", fontsize=8, color=COLORS["green"])
    ax1.tick_params(axis="y", labelsize=8, colors=COLORS["green"])
    ax1.set_xticks(x, labels)
    ax1.tick_params(axis="x", labelsize=8)
    ax1.grid(axis="y", color="#E2E8F0", linewidth=0.7)

    ax2 = ax1.twinx()
    ax2.bar(x + width / 2, khr, width, color=COLORS["red"], label="KHR")
    ax2.set_ylim(0, 0.35)
    ax2.set_ylabel("KHR", fontsize=8, color=COLORS["red"])
    ax2.tick_params(axis="y", labelsize=8, colors=COLORS["red"])
    ax2.spines["top"].set_visible(False)

    ax1.set_title("Update effect", fontsize=9, color=COLORS["ink"], fontweight="bold", pad=6)
    save(fig, "05_update_effect_bar")


def draw_protection_check_bar():
    labels = ["Schema", "Direction", "JSON", "Evidence"]
    pass_rate = [1.00, 1.00, 1.00, 1.00]

    fig, ax = plt.subplots(figsize=(3.2, 2.1))
    bars = ax.bar(labels, pass_rate, color=COLORS["green"], width=0.55)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("Pass", fontsize=8)
    ax.tick_params(labelsize=8)
    ax.grid(axis="y", color="#E2E8F0", linewidth=0.7)
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width() / 2, 1.03, "OK", ha="center", va="bottom", fontsize=7, color=COLORS["green"], fontweight="bold")
    ax.set_title("Protection checks", fontsize=9, color=COLORS["ink"], fontweight="bold", pad=6)
    save(fig, "06_protection_check_bar")


def main():
    apply_style()
    draw_error_bar()
    draw_pattern_bar()
    draw_attribution_heatmap()
    draw_candidate_metric_matrix()
    draw_update_delta_bar()
    draw_protection_check_bar()
    print(f"Saved clean result insets to {OUT_DIR}")


if __name__ == "__main__":
    main()
