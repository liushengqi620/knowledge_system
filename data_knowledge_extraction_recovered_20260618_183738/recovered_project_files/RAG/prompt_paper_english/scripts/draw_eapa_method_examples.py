#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Draw optimized standalone versions of Figure 4(a) and Figure 4(b).

The script intentionally writes new files and does not update LaTeX sources.
"""

from __future__ import annotations

from pathlib import Path
import textwrap

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle


ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "figures"

OUT_A_PNG = FIG_DIR / "eapa_method_example_a_optimized.png"
OUT_A_PDF = FIG_DIR / "eapa_method_example_a_optimized.pdf"
OUT_B_PNG = FIG_DIR / "eapa_method_example_b_visual.png"
OUT_B_PDF = FIG_DIR / "eapa_method_example_b_visual.pdf"

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
    "white": "#FFFFFF",
}


def setup(figsize):
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


def rounded(ax, x, y, w, h, fc, ec, lw=1.3, radius=0.018):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle=f"round,pad=0.006,rounding_size={radius}",
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


def wrapped(ax, x, y, text, width=34, size=7, color=None, weight=None, ha="left", va="top", linespacing=1.12):
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


def arrow(ax, start, end, color=None, lw=1.5, ms=12, style="-|>"):
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle=style,
            mutation_scale=ms,
            linewidth=lw,
            color=color or COLORS["muted"],
            shrinkA=2,
            shrinkB=2,
        )
    )


def tiny_badge(ax, x, y, text, color, w=0.044):
    rounded(ax, x, y, w, 0.034, color, color, lw=0.6, radius=0.007)
    label(ax, x + w / 2, y + 0.017, text, 7.4, "white", "bold")


def stage_title(ax, x, y, w, h, num, title, color):
    tiny_badge(ax, x + 0.012, y + h - 0.048, str(num), color, w=0.038)
    label(ax, x + 0.060, y + h - 0.030, title, 8.7, color, "bold", ha="left")


def mini_error_profile(ax, x, y, w, h):
    rounded(ax, x, y, w, h, COLORS["red_light"], COLORS["red"], lw=1.2)
    stage_title(ax, x, y, w, h, 1, "Aggregated Error Profile", COLORS["red"])
    label(ax, x + 0.060, y + h - 0.078, r"$E = E_{entity}+E_{relation}+E_{validity}$", 10.0, COLORS["ink"], ha="left")
    items = [("Entity", 0.45), ("Relation", 0.78), ("Validity", 0.52)]
    bx = x + 0.052
    for i, (name, val) in enumerate(items):
        yy = y + 0.090 + i * 0.052
        label(ax, bx, yy + 0.010, name, 5.6, COLORS["muted"], "bold", ha="left")
        ax.add_patch(Rectangle((bx + 0.075, yy), 0.122, 0.018, facecolor="#FEE2E2", edgecolor="none"))
        ax.add_patch(Rectangle((bx + 0.075, yy), 0.122 * val, 0.018, facecolor=COLORS["red"], edgecolor="none"))
    rounded(ax, x + w - 0.125, y + 0.078, 0.088, 0.110, "white", COLORS["red"], lw=1.0, radius=0.012)
    label(ax, x + w - 0.081, y + 0.147, "KHR", 6.4, COLORS["muted"], "bold")
    label(ax, x + w - 0.081, y + 0.105, "0.291", 11.0, COLORS["red"], "bold")


def mini_patterns(ax, x, y, w, h):
    rounded(ax, x, y, w, h, COLORS["purple_light"], COLORS["purple"], lw=1.2)
    stage_title(ax, x, y, w, h, 2, "Dominant Error Patterns", COLORS["purple"])
    bars = [0.34, 0.50, 0.72, 0.92, 0.63]
    for i, b in enumerate(bars):
        ax.add_patch(Rectangle((x + 0.050 + i * 0.030, y + 0.073), 0.018, b * 0.115, facecolor=COLORS["purple"], edgecolor="none"))
    cards = [
        ("P1", "missing causal triples"),
        ("P2", "entity boundary mismatch"),
        ("P3", "implicit relation chain"),
    ]
    for i, (pid, txt) in enumerate(cards):
        yy = y + 0.177 - i * 0.050
        rounded(ax, x + 0.230, yy, w - 0.260, 0.036, "white", COLORS["purple"], lw=0.9, radius=0.008)
        label(ax, x + 0.247, yy + 0.018, f"{pid}: {txt}", 5.8, COLORS["purple"], "bold", ha="left")


def mini_atom_space(ax, x, y, w, h):
    rounded(ax, x, y, w, h, COLORS["teal_light"], COLORS["teal"], lw=1.2)
    stage_title(ax, x, y, w, h, 3, "Atom Space and Attribution", COLORS["teal"])
    labels = ["uF2", "uS3", "uS7", "uD2", "uV4"]
    vals = [
        [0.2, 0.1, 0.0],
        [0.6, 0.4, 0.1],
        [0.2, 0.9, 0.8],
        [0.3, 0.7, 0.3],
        [0.1, 0.5, 0.9],
    ]
    hx, hy = x + 0.060, y + 0.060
    cw, ch = 0.030, 0.028
    for j, head in enumerate(["P1", "P2", "P3"]):
        label(ax, hx + 0.088 + j * cw, hy + 5.0 * ch + 0.010, head, 5.4, COLORS["muted"], "bold")
    for i, row in enumerate(vals):
        label(ax, hx, hy + (4 - i) * ch + 0.014, labels[i], 5.5, COLORS["teal"], "bold", ha="left")
        for j, val in enumerate(row):
            col = (1 - val, 0.96 - 0.40 * val, 0.94 - 0.45 * val)
            ax.add_patch(Rectangle((hx + 0.080 + j * cw, hy + (4 - i) * ch), cw - 0.002, ch - 0.002, facecolor=col, edgecolor="white", linewidth=0.4))
    wrapped(ax, x + 0.215, y + 0.155, "Selected atom:\nuD2 causal example\n+ uS7 relation schema", 24, 5.8, COLORS["teal"], "bold")


def mini_counterfactual(ax, x, y, w, h):
    rounded(ax, x, y, w, h, COLORS["orange_light"], COLORS["orange"], lw=1.2)
    stage_title(ax, x, y, w, h, 4, "Counterfactual Candidate Set", COLORS["orange"])
    rows = [
        ("Enhance", "+0.021", "-0.034", "Accept", COLORS["green"]),
        ("Replace", "+0.016", "+0.011", "Repair", COLORS["gold"]),
        ("Weaken", "-0.008", "0.000", "Reject", COLORS["red"]),
        ("Delete", "-0.030", "+0.025", "Rollback", COLORS["red"]),
    ]
    headers = ["Move", "dJ", "dKHR", "Decision"]
    tx, ty = x + 0.030, y + 0.060
    colw = [0.082, 0.061, 0.069, 0.081]
    for j, head in enumerate(headers):
        label(ax, tx + sum(colw[:j]) + colw[j] / 2, ty + 0.155, head, 5.2, "white", "bold")
        ax.add_patch(Rectangle((tx + sum(colw[:j]), ty + 0.138), colw[j], 0.034, facecolor=COLORS["orange"], edgecolor="white", linewidth=0.6))
    for i, row in enumerate(rows):
        yy = ty + 0.104 - i * 0.034
        for j, txt in enumerate(row[:4]):
            fc = COLORS["green_light"] if i == 0 else COLORS["gold_light"] if i == 1 else COLORS["red_light"]
            ax.add_patch(Rectangle((tx + sum(colw[:j]), yy), colw[j], 0.034, facecolor=fc, edgecolor="white", linewidth=0.6))
            label(ax, tx + sum(colw[:j]) + colw[j] / 2, yy + 0.017, txt, 4.9, row[4] if j == 3 else COLORS["ink"], "bold" if j in (0, 3) else None)
    rounded(ax, x + w - 0.108, y + 0.075, 0.077, 0.093, "white", COLORS["orange"], lw=0.9, radius=0.010)
    label(ax, x + w - 0.070, y + 0.136, r"$G(p_c)$", 7.2, COLORS["ink"], "bold")
    label(ax, x + w - 0.070, y + 0.105, r"$+dJ-dKHR-risk$", 4.8, COLORS["muted"])


def mini_local_update(ax, x, y, w, h):
    rounded(ax, x, y, w, h, COLORS["green_light"], COLORS["green"], lw=1.2)
    stage_title(ax, x, y, w, h, 5, "Accepted Local Update", COLORS["green"])
    rounded(ax, x + 0.034, y + 0.060, 0.120, 0.116, "white", COLORS["line"], lw=0.9, radius=0.010)
    rounded(ax, x + w - 0.158, y + 0.060, 0.120, 0.116, "white", COLORS["green"], lw=1.0, radius=0.010)
    label(ax, x + 0.094, y + 0.150, "Before", 5.8, COLORS["muted"], "bold")
    wrapped(ax, x + 0.050, y + 0.126, "ambiguous cue:\n\"lead to\" relation", 18, 5.6, COLORS["ink"])
    label(ax, x + w / 2, y + 0.118, "Enhance uD2", 6.6, COLORS["green"], "bold")
    arrow(ax, (x + 0.166, y + 0.115), (x + w - 0.170, y + 0.115), COLORS["green"], lw=1.3, ms=10)
    label(ax, x + w - 0.098, y + 0.150, "After", 5.8, COLORS["green"], "bold")
    wrapped(ax, x + w - 0.142, y + 0.126, "causal factor ->\nresulting defect", 18, 5.6, COLORS["ink"])


def mini_gate(ax, x, y, w, h):
    rounded(ax, x, y, w, h, COLORS["gold_light"], COLORS["gold"], lw=1.2)
    stage_title(ax, x, y, w, h, 6, "Protection Pool Gate", COLORS["gold"])
    checks = [
        ("Schema atom", True),
        ("Direction atom", True),
        ("JSON atom", True),
        ("Evidence atom", True),
    ]
    for i, (txt, ok) in enumerate(checks):
        yy = y + 0.168 - i * 0.038
        rounded(ax, x + 0.050, yy, 0.185, 0.027, "white", COLORS["green"] if ok else COLORS["red"], lw=0.8, radius=0.006)
        label(ax, x + 0.060, yy + 0.014, "OK", 4.8, COLORS["green"], "bold", ha="left")
        label(ax, x + 0.092, yy + 0.014, txt, 5.2, COLORS["ink"], ha="left")
    rounded(ax, x + w - 0.134, y + 0.075, 0.092, 0.086, "white", COLORS["green"], lw=1.0, radius=0.011)
    label(ax, x + w - 0.088, y + 0.123, "Accept", 7.0, COLORS["green"], "bold")
    label(ax, x + w - 0.088, y + 0.097, "write-back", 5.4, COLORS["green"], "bold")


def draw_fig4a():
    fig, ax = setup((14.6, 7.2))
    label(ax, 0.030, 0.965, "EAPA Prompt-Atom Optimization with Result Insets", 13.0, COLORS["ink"], "bold", ha="left")
    label(ax, 0.030, 0.930, "From batch-level errors to local atom updates, candidate validation, and protection-gated write-back.", 8.2, COLORS["muted"], ha="left")

    xs = [0.020, 0.350, 0.680]
    ys = [0.555, 0.190]
    w, h = 0.300, 0.290
    mini_error_profile(ax, xs[0], ys[0], w, h)
    mini_patterns(ax, xs[1], ys[0], w, h)
    mini_atom_space(ax, xs[2], ys[0], w, h)
    mini_counterfactual(ax, xs[0], ys[1], w, h)
    mini_local_update(ax, xs[1], ys[1], w, h)
    mini_gate(ax, xs[2], ys[1], w, h)

    arrow(ax, (xs[0] + w, ys[0] + h / 2), (xs[1], ys[0] + h / 2), COLORS["muted"])
    arrow(ax, (xs[1] + w, ys[0] + h / 2), (xs[2], ys[0] + h / 2), COLORS["muted"])
    arrow(ax, (xs[2] + w / 2, ys[0]), (xs[2] + w / 2, ys[1] + h), COLORS["muted"])
    arrow(ax, (xs[2], ys[1] + h / 2), (xs[1] + w, ys[1] + h / 2), COLORS["muted"])
    arrow(ax, (xs[1], ys[1] + h / 2), (xs[0] + w, ys[1] + h / 2), COLORS["muted"])

    rounded(ax, 0.185, 0.045, 0.630, 0.075, "white", COLORS["line"], lw=1.0, radius=0.012)
    label(ax, 0.500, 0.086, "Displayed result insets", 7.2, COLORS["ink"], "bold")
    label(
        ax,
        0.500,
        0.060,
        "error distribution + dominant patterns + attribution heatmap + candidate matrix + before/after update + protection decision",
        6.6,
        COLORS["muted"],
    )

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_A_PNG, dpi=420, bbox_inches="tight")
    fig.savefig(OUT_A_PDF, bbox_inches="tight")
    plt.close(fig)


def pipeline_case(ax, x, y, w, h, idx, title, evidence, wrong, atom, edit, corrected, accent):
    rounded(ax, x, y, w, h, "white", accent, lw=1.2, radius=0.018)
    tiny_badge(ax, x + 0.014, y + h - 0.052, str(idx), accent, w=0.036)
    label(ax, x + 0.058, y + h - 0.034, title, 8.6, accent, "bold", ha="left")

    lane_y = y + 0.050
    box_h = h - 0.128
    gap = 0.018
    widths = [0.220, 0.235, 0.165, 0.180, 0.170]
    starts = [x + 0.020]
    for part in widths[:-1]:
        starts.append(starts[-1] + w * part + gap)

    specs = [
        ("Evidence", evidence, COLORS["blue_light"], COLORS["blue"]),
        ("Flat error", wrong, COLORS["red_light"], COLORS["red"]),
        ("Atom", atom, COLORS["teal_light"], COLORS["teal"]),
        ("Edit", edit, COLORS["orange_light"], COLORS["orange"]),
        ("Corrected output", corrected, COLORS["green_light"], COLORS["green"]),
    ]
    for i, (head, body, fill, col) in enumerate(specs):
        bw = w * widths[i]
        rounded(ax, starts[i], lane_y, bw, box_h, fill, col, lw=0.9, radius=0.010)
        label(ax, starts[i] + 0.012, lane_y + box_h - 0.026, head, 5.9, col, "bold", ha="left")
        wrapped(ax, starts[i] + 0.012, lane_y + box_h - 0.050, body, width=25 if i != 4 else 24, size=5.7, color=COLORS["ink"])
        if i < len(specs) - 1:
            arrow(ax, (starts[i] + bw + 0.003, lane_y + box_h / 2), (starts[i + 1] - 0.005, lane_y + box_h / 2), COLORS["muted"], lw=1.0, ms=9)


def draw_fig4b():
    fig, ax = setup((14.6, 6.6))
    label(ax, 0.030, 0.965, "Motivating Error Cases as Local Update Pipelines", 13.0, COLORS["red"], "bold", ha="left")
    label(ax, 0.030, 0.930, "The table is converted into visual case flows: evidence -> flat-prompt error -> attributed atom -> edit -> corrected extraction.", 8.1, COLORS["muted"], ha="left")

    cases = [
        (
            "Implicit causal chain",
            '"Casting speed increased, leading to longitudinal cracks."',
            "Direction reversal:\ncracks -> cause -> casting speed",
            "uS7 direction rule\nuV4 direction check",
            "Enhance causal example\nand direction wording.",
            "casting speed increase\n-> cause ->\nlongitudinal cracks",
            COLORS["red"],
        ),
        (
            "Unsupported inference",
            '"Mold powder viscosity was too low."',
            "Generates a defect\nnot stated in text.",
            "uV5 evidence check\nuD3 negative example",
            "Replace evidence rule;\nadd no-inference case.",
            "retain supported entity;\nreject unsupported triple",
            COLORS["purple"],
        ),
        (
            "Schema / format violation",
            '"Secondary cooling water flow decreased."',
            "Missing JSON fields\nor illegal relation type.",
            "uS9 JSON field atom\nuV2 schema check",
            "Protect JSON keys;\nenhance validity check.",
            "schema-valid JSON\nwith allowed labels",
            COLORS["orange"],
        ),
    ]
    for i, case in enumerate(cases, start=1):
        y = 0.675 - (i - 1) * 0.265
        pipeline_case(ax, 0.020, y, 0.960, 0.225, i, *case)

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_B_PNG, dpi=420, bbox_inches="tight")
    fig.savefig(OUT_B_PDF, bbox_inches="tight")
    plt.close(fig)


def main():
    draw_fig4a()
    draw_fig4b()
    print(f"Saved {OUT_A_PNG}")
    print(f"Saved {OUT_A_PDF}")
    print(f"Saved {OUT_B_PNG}")
    print(f"Saved {OUT_B_PDF}")


if __name__ == "__main__":
    main()
