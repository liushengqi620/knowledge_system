from __future__ import annotations

import argparse
import os
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


@dataclass(frozen=True)
class FigureSpec:
    figure_id: str
    title: str
    filename_stem: str
    caption: str
    renderer: Callable[[Path], list[Path]]


PALETTE = {
    "ink": "#263238",
    "muted": "#62727b",
    "blue": "#D7E8F7",
    "blue_edge": "#4F7FA8",
    "green": "#DCEEE4",
    "green_edge": "#4C8B63",
    "gold": "#F4E7C4",
    "gold_edge": "#A3782B",
    "rose": "#F1D7D8",
    "rose_edge": "#A65C61",
    "gray": "#EEF1F3",
    "gray_edge": "#7C8A93",
}


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _new_canvas(width: float = 12.0, height: float = 6.8):
    fig, ax = plt.subplots(figsize=(width, height), dpi=160)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor("white")
    return fig, ax


def _box(ax, xy, wh, text, fill, edge, fontsize=9, weight="normal"):
    x, y = xy
    w, h = wh
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.012,rounding_size=0.012",
        linewidth=1.15,
        facecolor=fill,
        edgecolor=edge,
    )
    ax.add_patch(patch)
    ax.text(
        x + w / 2,
        y + h / 2,
        textwrap.fill(text, width=max(12, int(w * 60))),
        ha="center",
        va="center",
        fontsize=fontsize,
        fontweight=weight,
        color=PALETTE["ink"],
    )
    return patch


def _arrow(ax, start, end, color=None, rad=0.0, lw=1.15):
    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=12,
        linewidth=lw,
        color=color or PALETTE["muted"],
        connectionstyle=f"arc3,rad={rad}",
        shrinkA=4,
        shrinkB=4,
    )
    ax.add_patch(arrow)


def _save(fig, output_dir: Path, stem: str) -> list[Path]:
    os.makedirs(_fs_path(output_dir), exist_ok=True)
    svg = output_dir / f"{stem}.svg"
    png = output_dir / f"{stem}.png"
    pdf = output_dir / f"{stem}.pdf"
    fig.savefig(_fs_path(svg), bbox_inches="tight", transparent=False)
    fig.savefig(_fs_path(png), bbox_inches="tight", dpi=300, transparent=False)
    fig.savefig(_fs_path(pdf), bbox_inches="tight", transparent=False)
    plt.close(fig)
    return [svg, png, pdf]


def _render_figure1(output_dir: Path) -> list[Path]:
    fig, ax = _new_canvas(13.2, 7.2)
    ax.text(0.02, 0.96, "Figure 1. Reliability-Calibrated Mechanism Evidence Fusion", fontsize=13, fontweight="bold", color=PALETTE["ink"])

    _box(ax, (0.04, 0.62), (0.16, 0.12), "Industrial time-series window x_i", PALETTE["gray"], PALETTE["gray_edge"], 9)
    _box(ax, (0.27, 0.72), (0.16, 0.11), "Strong anchor model f_0", PALETTE["blue"], PALETTE["blue_edge"], 9, "bold")
    _box(ax, (0.51, 0.73), (0.14, 0.10), "Anchor prediction p_0(i)", PALETTE["blue"], PALETTE["blue_edge"], 9)
    _box(ax, (0.27, 0.47), (0.16, 0.11), "Residual dynamics r_i", PALETTE["gray"], PALETTE["gray_edge"], 9)

    sources = [
        ("Expert knowledge", 0.06, 0.38),
        ("LLM weak-class verifier", 0.06, 0.25),
        ("Lagged statistical relations", 0.06, 0.12),
        ("Graph paths and source-pruned edges", 0.27, 0.20),
    ]
    for text, x, y in sources:
        _box(ax, (x, y), (0.16, 0.085), text, PALETTE["gold"], PALETTE["gold_edge"], 8.5)

    _box(ax, (0.50, 0.32), (0.18, 0.14), "Candidate mechanism evidence m_k", PALETTE["green"], PALETTE["green_edge"], 9, "bold")
    _box(ax, (0.74, 0.32), (0.16, 0.11), "Mechanism challengers f_k", PALETTE["green"], PALETTE["green_edge"], 9)
    _box(ax, (0.74, 0.55), (0.16, 0.11), "Challenger predictions p_k(i)", PALETTE["green"], PALETTE["green_edge"], 9)
    _box(ax, (0.51, 0.55), (0.16, 0.11), "Reliability certificate R_k", PALETTE["rose"], PALETTE["rose_edge"], 9)
    _box(ax, (0.74, 0.72), (0.16, 0.11), "Evidence Reliability Estimator q_psi(i,k)", PALETTE["rose"], PALETTE["rose_edge"], 8.5, "bold")
    _box(ax, (0.52, 0.12), (0.16, 0.10), "Admitted evidence A_R", PALETTE["rose"], PALETTE["rose_edge"], 9)
    _box(ax, (0.74, 0.12), (0.16, 0.10), "Reliability-gated router", PALETTE["rose"], PALETTE["rose_edge"], 9)
    _box(ax, (0.89, 0.47), (0.09, 0.12), "Final prediction p*(i)", PALETTE["blue"], PALETTE["blue_edge"], 9, "bold")

    _arrow(ax, (0.20, 0.68), (0.27, 0.78))
    _arrow(ax, (0.43, 0.78), (0.51, 0.78))
    _arrow(ax, (0.20, 0.66), (0.27, 0.52))
    _arrow(ax, (0.43, 0.52), (0.50, 0.39))
    for _, x, y in sources:
        _arrow(ax, (x + 0.16, y + 0.043), (0.50, 0.39))
    _arrow(ax, (0.68, 0.39), (0.74, 0.38))
    _arrow(ax, (0.82, 0.43), (0.82, 0.55))
    _arrow(ax, (0.90, 0.60), (0.89, 0.55))
    _arrow(ax, (0.65, 0.78), (0.74, 0.78))
    _arrow(ax, (0.59, 0.55), (0.60, 0.22))
    _arrow(ax, (0.68, 0.17), (0.74, 0.17))
    _arrow(ax, (0.82, 0.22), (0.90, 0.48))
    _arrow(ax, (0.65, 0.78), (0.90, 0.56), rad=-0.12)

    return _save(fig, output_dir, "figure1_reliability_calibrated_mechanism_fusion")


def _render_figure2(output_dir: Path) -> list[Path]:
    fig, ax = _new_canvas(12.6, 6.4)
    ax.text(0.02, 0.95, "Figure 2. Evidence Reliability Admission Loop", fontsize=13, fontweight="bold", color=PALETTE["ink"])

    _box(ax, (0.05, 0.43), (0.13, 0.12), "Candidate m_k", PALETTE["gray"], PALETTE["gray_edge"], 9, "bold")
    factors = [
        ("Validation benefit Delta M_k", 0.26, 0.73),
        ("Low-tail benefit Q_alpha", 0.26, 0.58),
        ("Counterfactual sensitivity CF_k", 0.26, 0.43),
        ("Invariance / stability I_k", 0.26, 0.28),
        ("Source trust T_k", 0.26, 0.13),
        ("Complexity penalty C_k", 0.48, 0.13),
    ]
    for text, x, y in factors:
        _box(ax, (x, y), (0.17, 0.10), text, PALETTE["gold"], PALETTE["gold_edge"], 8.5)

    _box(ax, (0.52, 0.42), (0.14, 0.13), "Reliability certificate R_k", PALETTE["rose"], PALETTE["rose_edge"], 9, "bold")
    _box(ax, (0.72, 0.42), (0.14, 0.13), "Pass thresholds?", PALETTE["rose"], PALETTE["rose_edge"], 9, "bold")
    _box(ax, (0.86, 0.62), (0.12, 0.11), "Admit into A_R", PALETTE["green"], PALETTE["green_edge"], 9)
    _box(ax, (0.86, 0.23), (0.12, 0.11), "Reject / fallback to anchor", PALETTE["gray"], PALETTE["gray_edge"], 8.5)

    for text, x, y in factors:
        _arrow(ax, (0.18, 0.49), (x, y + 0.05), rad=0.02)
        _arrow(ax, (x + 0.17, y + 0.05), (0.52, 0.49), rad=0.02)
    _arrow(ax, (0.66, 0.49), (0.72, 0.49))
    _arrow(ax, (0.86, 0.52), (0.86, 0.66))
    _arrow(ax, (0.86, 0.45), (0.86, 0.29))
    _arrow(ax, (0.92, 0.62), (0.92, 0.55), rad=-0.18)
    ax.text(0.88, 0.57, "allowed to\nchallenge p_0", fontsize=8, ha="center", color=PALETTE["muted"])
    ax.text(0.78, 0.60, "yes", fontsize=8.5, fontweight="bold", color=PALETTE["green_edge"])
    ax.text(0.78, 0.36, "no", fontsize=8.5, fontweight="bold", color=PALETTE["gray_edge"])

    return _save(fig, output_dir, "figure2_evidence_reliability_admission_loop")


def _render_figure3(output_dir: Path) -> list[Path]:
    fig, ax = _new_canvas(12.8, 6.0)
    ax.text(0.02, 0.95, "Figure 3. Anchor-Challenger Deployment Rule", fontsize=13, fontweight="bold", color=PALETTE["ink"])

    cols = [
        ("Window x_i", 0.08),
        ("Anchor f_0", 0.27),
        ("Admitted challengers A_R", 0.47),
        ("ERE q_psi(i,k)", 0.68),
        ("Output p*(i)", 0.88),
    ]
    for title, x in cols:
        _box(ax, (x - 0.065, 0.78), (0.13, 0.09), title, PALETTE["gray"], PALETTE["gray_edge"], 8.5, "bold")
        ax.plot([x, x], [0.18, 0.78], color="#C7CED3", lw=1.0, linestyle="--")

    steps = [
        ((0.08, 0.70), (0.27, 0.70), "compute p_0(i)"),
        ((0.08, 0.58), (0.47, 0.58), "compute p_k(i)"),
        ((0.27, 0.46), (0.68, 0.46), "anchor confidence + context"),
        ((0.47, 0.34), (0.68, 0.34), "challenger logits + mechanism features"),
        ((0.68, 0.25), (0.68, 0.20), "select k* if max q >= tau_q"),
    ]
    for start, end, label in steps:
        _arrow(ax, start, end)
        ax.text((start[0] + end[0]) / 2, start[1] + 0.025, label, ha="center", fontsize=8.2, color=PALETTE["muted"])

    _box(ax, (0.75, 0.47), (0.17, 0.10), "Reliable challenger exists", PALETTE["green"], PALETTE["green_edge"], 8.5)
    _box(ax, (0.75, 0.23), (0.17, 0.10), "No reliable challenger", PALETTE["gray"], PALETTE["gray_edge"], 8.5)
    _box(ax, (0.88, 0.58), (0.10, 0.10), "mix p_0 and p_k*", PALETTE["blue"], PALETTE["blue_edge"], 8.5)
    _box(ax, (0.88, 0.12), (0.10, 0.10), "fallback to p_0", PALETTE["blue"], PALETTE["blue_edge"], 8.5)

    _arrow(ax, (0.68, 0.30), (0.75, 0.52))
    _arrow(ax, (0.68, 0.23), (0.75, 0.28))
    _arrow(ax, (0.92, 0.52), (0.88, 0.63))
    _arrow(ax, (0.92, 0.28), (0.88, 0.17))

    ax.text(0.51, 0.08, "Deployment uses p_0 unless admitted evidence is locally reliable.", ha="center", fontsize=9.5, color=PALETTE["ink"])

    return _save(fig, output_dir, "figure3_anchor_challenger_deployment_rule")


def _write_index(output_dir: Path, figure_paths: Iterable[Path]) -> Path:
    index = output_dir / "core_paper_figures_rendered.md"
    by_name = {path.name: path for path in figure_paths}
    lines = [
        "# Rendered Core Paper Figures",
        "",
        "These submission-facing core method figures are generated by `Scripts/render_core_paper_figures.py`.",
        "Use the PDF files for LaTeX placement, SVG files for editable vector inspection, and PNG files for quick previews.",
        "",
        "| Figure | PDF | SVG | PNG | Caption |",
        "|---|---|---|---|---|",
    ]
    for number, spec in enumerate(CORE_FIGURES, start=1):
        pdf = f"{spec.filename_stem}.pdf"
        svg = f"{spec.filename_stem}.svg"
        png = f"{spec.filename_stem}.png"
        lines.append(f"| Figure {number}. {spec.title} | `{pdf}` | `{svg}` | `{png}` | {spec.caption} |")
        if pdf not in by_name or svg not in by_name or png not in by_name:
            raise RuntimeError(f"Missing rendered outputs for {spec.figure_id}")
    with open(_fs_path(index), "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    return index


def render_all_core_figures(output_dir: Path) -> list[Path]:
    output_dir = Path(output_dir)
    written: list[Path] = []
    for spec in CORE_FIGURES:
        written.extend(spec.renderer(output_dir))
    written.append(_write_index(output_dir, written))
    return written


CORE_FIGURES = [
    FigureSpec(
        figure_id="figure1",
        title="Reliability-Calibrated Mechanism Evidence Fusion",
        filename_stem="figure1_reliability_calibrated_mechanism_fusion",
        caption="A strong anchor remains the default predictor while expert, LLM, lagged, residual, and graph evidence must pass reliability admission before correction.",
        renderer=_render_figure1,
    ),
    FigureSpec(
        figure_id="figure2",
        title="Evidence Reliability Admission Loop",
        filename_stem="figure2_evidence_reliability_admission_loop",
        caption="Validation gain, low-tail behavior, counterfactual sensitivity, invariance, source trust, and complexity decide whether candidate evidence may affect deployment.",
        renderer=_render_figure2,
    ),
    FigureSpec(
        figure_id="figure3",
        title="Anchor-Challenger Deployment Rule",
        filename_stem="figure3_anchor_challenger_deployment_rule",
        caption="The deployed predictor falls back to the anchor unless an admitted challenger has sufficient local ERE reliability.",
        renderer=_render_figure3,
    ),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Render submission-facing core paper figures.")
    parser.add_argument(
        "--output-dir",
        default="knowledge_exports/paper_core_figures_rendered",
        type=Path,
        help="Directory for rendered PDF/SVG/PNG figures.",
    )
    args = parser.parse_args()
    written = render_all_core_figures(args.output_dir)
    for path in written:
        print(path)


if __name__ == "__main__":
    main()
