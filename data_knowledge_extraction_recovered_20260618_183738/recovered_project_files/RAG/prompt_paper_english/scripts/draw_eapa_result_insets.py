#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate standalone result inset figures for EAPA mechanism illustrations.

These files are intended as reusable subfigures for composing Figure 4(a)/(b).
The script does not modify any LaTeX source or overwrite existing full figures.
"""

from __future__ import annotations

from pathlib import Path
import textwrap

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "figures" / "eapa_result_insets"

COLORS = {
    "ink": "#172033",
    "muted": "#64748B",
    "line": "#CBD5E1",
    "red": "#C81E1E",
    "red_light": "#FFF1F1",
    "purple": "#5B2DB7",
    "purple_light": "#F5F0FF",
    "teal": "#008C89",
    "teal_light": "#EAF8F7",
    "orange": "#D26400",
    "orange_light": "#FFF2E6",
    "green": "#147A35",
    "green_light": "#EAF7EE",
    "gold": "#A66A00",
    "gold_light": "#FFF7DF",
    "blue": "#2563EB",
    "blue_light": "#EDF4FF",
}


def setup(figsize=(4.8, 2.8)):
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "mathtext.fontset": "dejavusans",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor("white")
    return fig, ax


def save(fig, name):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    png = OUT_DIR / f"{name}.png"
    pdf = OUT_DIR / f"{name}.pdf"
    fig.savefig(png, dpi=420, bbox_inches="tight", pad_inches=0.02)
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print(png)
    print(pdf)


def rounded(ax, x, y, w, h, fc, ec, lw=1.2, radius=0.035):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle=f"round,pad=0.008,rounding_size={radius}",
        facecolor=fc,
        edgecolor=ec,
        linewidth=lw,
    )
    ax.add_patch(patch)
    return patch


def label(ax, x, y, text, size=8, color=None, weight=None, ha="center", va="center", **kwargs):
    ax.text(
        x,
        y,
        text,
        fontsize=size,
        color=color or COLORS["ink"],
        fontweight=weight,
        ha=ha,
        va=va,
        family="DejaVu Sans",
        **kwargs,
    )


def wrapped(ax, x, y, text, width=28, size=7, color=None, weight=None, ha="left", va="top", linespacing=1.12):
    lines = []
    for part in str(text).splitlines():
        lines.extend(textwrap.wrap(part, width=width) if part.strip() else [""])
    label(
        ax,
        x,
        y,
        "\n".join(lines),
        size=size,
        color=color or COLORS["ink"],
        weight=weight,
        ha=ha,
        va=va,
        linespacing=linespacing,
    )


def arrow(ax, start, end, color=None, lw=1.5, ms=13):
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=ms,
            linewidth=lw,
            color=color or COLORS["muted"],
            shrinkA=2,
            shrinkB=2,
        )
    )


def draw_error_profile():
    fig, ax = setup((5.1, 3.0))
    rounded(ax, 0.02, 0.04, 0.96, 0.90, COLORS["red_light"], COLORS["red"], 1.5)
    label(ax, 0.07, 0.88, "1", 10, "white", "bold")
    rounded(ax, 0.04, 0.82, 0.06, 0.10, COLORS["red"], COLORS["red"], 0.8, 0.018)
    label(ax, 0.14, 0.875, "Aggregated Error Profile", 12.5, COLORS["red"], "bold", ha="left")
    label(ax, 0.50, 0.735, r"$E=E_{entity}+E_{relation}+E_{validity}$", 16, COLORS["ink"])

    items = [("Entity errors", 0.153), ("Relation errors", 0.098), ("Validity errors", 0.040)]
    max_val = 0.18
    for i, (name, val) in enumerate(items):
        yy = 0.540 - i * 0.145
        label(ax, 0.13, yy + 0.020, name, 8.0, COLORS["ink"], "bold", ha="left")
        ax.add_patch(Rectangle((0.43, yy), 0.30, 0.040, facecolor="#FECACA", edgecolor="none"))
        ax.add_patch(Rectangle((0.43, yy), 0.30 * val / max_val, 0.040, facecolor=COLORS["red"], edgecolor="none"))
        label(ax, 0.78, yy + 0.020, f"{val:.3f}", 8.2, COLORS["ink"], ha="left")
    rounded(ax, 0.76, 0.15, 0.16, 0.22, "white", COLORS["red"], 1.2, 0.025)
    label(ax, 0.84, 0.295, "KHR", 8.5, COLORS["muted"], "bold")
    label(ax, 0.84, 0.210, "0.291", 15, COLORS["red"], "bold")
    save(fig, "01_error_profile")


def draw_dominant_patterns():
    fig, ax = setup((5.1, 3.0))
    rounded(ax, 0.02, 0.04, 0.96, 0.90, COLORS["purple_light"], COLORS["purple"], 1.5)
    rounded(ax, 0.04, 0.82, 0.06, 0.10, COLORS["purple"], COLORS["purple"], 0.8, 0.018)
    label(ax, 0.07, 0.875, "2", 10, "white", "bold")
    label(ax, 0.14, 0.875, "Dominant Error Patterns", 12.5, COLORS["purple"], "bold", ha="left")
    values = [0.10, 0.14, 0.19, 0.12]
    labels = ["P1", "P2", "P3", "Others"]
    base_x = 0.13
    for i, val in enumerate(values):
        x = base_x + i * 0.105
        ax.add_patch(Rectangle((x, 0.22), 0.052, val * 2.60, facecolor=COLORS["purple"], edgecolor="none"))
        label(ax, x + 0.026, 0.175, labels[i], 7.5, COLORS["ink"], "bold")
    label(ax, 0.26, 0.700, "Error frequency", 8.0, COLORS["ink"], "bold")
    patterns = [
        ("P1", "missing causal triples"),
        ("P2", "boundary mismatch"),
        ("P3", "implicit relation chain"),
    ]
    for i, (pid, text) in enumerate(patterns):
        yy = 0.605 - i * 0.155
        rounded(ax, 0.62, yy, 0.28, 0.105, "white", COLORS["purple"], 1.0, 0.018)
        label(ax, 0.655, yy + 0.053, pid, 9, COLORS["purple"], "bold")
        wrapped(ax, 0.705, yy + 0.080, text, 15, 6.3, COLORS["ink"], "bold")
    save(fig, "02_dominant_patterns")


def draw_attribution_heatmap():
    fig, ax = setup((5.1, 3.0))
    rounded(ax, 0.02, 0.04, 0.96, 0.90, COLORS["teal_light"], COLORS["teal"], 1.5)
    rounded(ax, 0.04, 0.82, 0.06, 0.10, COLORS["teal"], COLORS["teal"], 0.8, 0.018)
    label(ax, 0.07, 0.875, "3", 10, "white", "bold")
    label(ax, 0.14, 0.875, "Atom Attribution Heatmap", 12.5, COLORS["teal"], "bold", ha="left")
    atoms = ["uF2", "uS3", "uS7", "uD2", "uV4"]
    vals = [
        [0.25, 0.15, 0.05],
        [0.68, 0.44, 0.10],
        [0.24, 0.90, 0.86],
        [0.38, 0.68, 0.36],
        [0.08, 0.50, 0.92],
    ]
    hx, hy = 0.18, 0.18
    cw, ch = 0.12, 0.105
    for j, head in enumerate(["P1", "P2", "P3"]):
        label(ax, hx + 0.18 + j * cw, hy + 5.2 * ch, head, 8, COLORS["muted"], "bold")
    for i, atom in enumerate(atoms):
        label(ax, hx, hy + (4 - i) * ch + ch / 2, atom, 8, COLORS["teal"], "bold", ha="left")
        for j, val in enumerate(vals[i]):
            col = (1 - val, 0.96 - 0.42 * val, 0.94 - 0.46 * val)
            ax.add_patch(
                Rectangle(
                    (hx + 0.15 + j * cw, hy + (4 - i) * ch),
                    cw - 0.006,
                    ch - 0.006,
                    facecolor=col,
                    edgecolor="white",
                    linewidth=0.8,
                )
            )
    rounded(ax, 0.66, 0.30, 0.26, 0.25, "white", COLORS["teal"], 1.1, 0.025)
    wrapped(ax, 0.69, 0.500, "Selected atom:\nuD2 causal example\nuS7 relation schema", 24, 7.0, COLORS["teal"], "bold")
    arrow(ax, (0.61, 0.43), (0.66, 0.43), COLORS["teal"], 1.3, 12)
    save(fig, "03_attribution_heatmap")


def draw_candidate_matrix():
    fig, ax = setup((5.1, 3.0))
    rounded(ax, 0.02, 0.04, 0.96, 0.90, COLORS["orange_light"], COLORS["orange"], 1.5)
    rounded(ax, 0.04, 0.82, 0.06, 0.10, COLORS["orange"], COLORS["orange"], 0.8, 0.018)
    label(ax, 0.07, 0.875, "4", 10, "white", "bold")
    label(ax, 0.14, 0.875, "Counterfactual Candidate Matrix", 12.0, COLORS["orange"], "bold", ha="left")

    headers = ["Move", "dJ", "dKHR", "dQ", "Risk", "Decision"]
    rows = [
        ["Enhance", "+0.021", "-0.034", "+0.018", "Low", "Accept"],
        ["Replace", "+0.016", "+0.011", "-0.006", "Medium", "Repair"],
        ["Weaken", "-0.008", "0.000", "-0.003", "Medium", "Reject"],
        ["Delete", "-0.030", "+0.025", "-0.018", "High", "Rollback"],
    ]
    x0, y0 = 0.08, 0.19
    widths = [0.19, 0.12, 0.14, 0.12, 0.14, 0.16]
    row_h = 0.115
    for j, head in enumerate(headers):
        xx = x0 + sum(widths[:j])
        ax.add_patch(Rectangle((xx, y0 + 4 * row_h), widths[j], row_h, facecolor=COLORS["orange"], edgecolor="white", linewidth=1))
        label(ax, xx + widths[j] / 2, y0 + 4.5 * row_h, head, 7.2, "white", "bold")
    for i, row in enumerate(rows):
        yy = y0 + (3 - i) * row_h
        for j, text in enumerate(row):
            xx = x0 + sum(widths[:j])
            fc = COLORS["green_light"] if i == 0 else COLORS["gold_light"] if i == 1 else COLORS["red_light"]
            ax.add_patch(Rectangle((xx, yy), widths[j], row_h, facecolor=fc, edgecolor="white", linewidth=1))
            color = COLORS["green"] if text == "Accept" else COLORS["gold"] if text == "Repair" else COLORS["red"] if text in ("Reject", "Rollback") else COLORS["ink"]
            label(ax, xx + widths[j] / 2, yy + row_h / 2, text, 7.0, color, "bold" if j in (0, 5) else None)
    rounded(ax, 0.655, 0.055, 0.27, 0.10, "white", COLORS["orange"], 1.0, 0.020)
    label(ax, 0.790, 0.105, r"$G(p_c)=+\Delta J-\Delta KHR-\Delta Q-Risk$", 7.2, COLORS["ink"], "bold")
    save(fig, "04_candidate_matrix")


def draw_local_update():
    fig, ax = setup((5.1, 3.0))
    rounded(ax, 0.02, 0.04, 0.96, 0.90, COLORS["green_light"], COLORS["green"], 1.5)
    rounded(ax, 0.04, 0.82, 0.06, 0.10, COLORS["green"], COLORS["green"], 0.8, 0.018)
    label(ax, 0.07, 0.875, "5", 10, "white", "bold")
    label(ax, 0.14, 0.875, "Accepted Local Update", 12.5, COLORS["green"], "bold", ha="left")
    label(ax, 0.50, 0.715, "Enhance uD2", 10, COLORS["green"], "bold")
    rounded(ax, 0.10, 0.28, 0.30, 0.30, "white", COLORS["line"], 1.0, 0.025)
    rounded(ax, 0.60, 0.28, 0.30, 0.30, "white", COLORS["green"], 1.2, 0.025)
    label(ax, 0.25, 0.515, "Before", 8, COLORS["muted"], "bold")
    wrapped(ax, 0.145, 0.455, "ambiguous cue:\n\"lead to\" relation", 22, 7.3)
    label(ax, 0.75, 0.515, "After", 8, COLORS["green"], "bold")
    wrapped(ax, 0.640, 0.455, "causal factor ->\nresulting defect", 22, 7.3)
    arrow(ax, (0.43, 0.43), (0.57, 0.43), COLORS["green"], 2.0, 18)
    rounded(ax, 0.65, 0.20, 0.20, 0.065, COLORS["green_light"], COLORS["green"], 0.9, 0.015)
    label(ax, 0.75, 0.232, "uD2 updated", 7.0, COLORS["green"], "bold")
    save(fig, "05_local_update_before_after")


def draw_protection_gate():
    fig, ax = setup((5.1, 3.0))
    rounded(ax, 0.02, 0.04, 0.96, 0.90, COLORS["gold_light"], COLORS["gold"], 1.5)
    rounded(ax, 0.04, 0.82, 0.06, 0.10, COLORS["gold"], COLORS["gold"], 0.8, 0.018)
    label(ax, 0.07, 0.875, "6", 10, "white", "bold")
    label(ax, 0.14, 0.875, "Protection Pool Gate", 12.5, COLORS["gold"], "bold", ha="left")
    checks = ["Schema atom", "Direction atom", "JSON atom", "Evidence atom"]
    for i, text in enumerate(checks):
        yy = 0.625 - i * 0.125
        rounded(ax, 0.12, yy, 0.50, 0.075, "white", COLORS["green"], 1.0, 0.018)
        label(ax, 0.17, yy + 0.038, "OK", 7, COLORS["green"], "bold")
        label(ax, 0.28, yy + 0.038, text, 7.5, COLORS["ink"], "bold", ha="left")
    arrow(ax, (0.64, 0.42), (0.72, 0.42), COLORS["green"], 1.8, 16)
    rounded(ax, 0.73, 0.30, 0.18, 0.24, "white", COLORS["green"], 1.3, 0.025)
    label(ax, 0.82, 0.455, "Accept", 12, COLORS["green"], "bold")
    label(ax, 0.82, 0.375, "write-back", 8.0, COLORS["green"], "bold")
    save(fig, "06_protection_gate")


def draw_case_pipeline(name, title, evidence, error, atom, edit, output, accent):
    fig, ax = setup((7.4, 1.75))
    rounded(ax, 0.015, 0.10, 0.97, 0.80, "white", accent, 1.5, 0.030)
    label(ax, 0.05, 0.72, title, 9.5, accent, "bold", ha="left")
    boxes = [
        ("Evidence", evidence, COLORS["blue_light"], COLORS["blue"]),
        ("Flat error", error, COLORS["red_light"], COLORS["red"]),
        ("Atom", atom, COLORS["teal_light"], COLORS["teal"]),
        ("Edit", edit, COLORS["orange_light"], COLORS["orange"]),
        ("Corrected", output, COLORS["green_light"], COLORS["green"]),
    ]
    x = 0.05
    widths = [0.18, 0.19, 0.18, 0.18, 0.18]
    for i, (head, body, fc, ec) in enumerate(boxes):
        bw = widths[i]
        rounded(ax, x, 0.24, bw, 0.34, fc, ec, 1.0, 0.020)
        label(ax, x + 0.015, 0.515, head, 6.4, ec, "bold", ha="left")
        wrapped(ax, x + 0.015, 0.450, body, 22, 6.2)
        if i < len(boxes) - 1:
            arrow(ax, (x + bw + 0.004, 0.41), (x + bw + 0.035, 0.41), COLORS["muted"], 1.1, 10)
        x += bw + 0.045
    save(fig, name)


def main():
    draw_error_profile()
    draw_dominant_patterns()
    draw_attribution_heatmap()
    draw_candidate_matrix()
    draw_local_update()
    draw_protection_gate()
    draw_case_pipeline(
        "07_case_implicit_causal_chain",
        "Implicit causal chain",
        '"Casting speed increased,\nleading to cracks."',
        "direction reversal:\ncracks -> cause -> speed",
        "uS7 direction rule\nuV4 check",
        "enhance causal\nexample",
        "speed -> cause\n-> cracks",
        COLORS["red"],
    )
    draw_case_pipeline(
        "08_case_unsupported_inference",
        "Unsupported inference",
        '"Mold powder viscosity\nwas too low."',
        "unsupported defect\nnot in text",
        "uV5 evidence check\nuD3 negative example",
        "replace evidence\nrule",
        "reject unsupported\ntriple",
        COLORS["purple"],
    )
    draw_case_pipeline(
        "09_case_schema_format_violation",
        "Schema / format violation",
        '"Secondary cooling water\nflow decreased."',
        "missing JSON fields\nor illegal relation type",
        "uS9 JSON atom\nuV2 schema check",
        "protect JSON keys\nand labels",
        "schema-valid\nJSON",
        COLORS["orange"],
    )


if __name__ == "__main__":
    main()
