from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
INPUT = (
    ROOT
    / "knowledge_exports"
    / "quality_traceability_dataset_v8_quality_abnormal_event_cleanconflict"
    / "y_quality_label.csv"
)
OUT_DIR = ROOT / "knowledge_exports" / "visualizations"
PNG_OUT = OUT_DIR / "reason_mechanism_phi_heatmap.png"
CSV_OUT = OUT_DIR / "reason_mechanism_phi_matrix.csv"
COUNT_OUT = OUT_DIR / "reason_mechanism_cooccurrence_counts.csv"

MECHANISM_ORDER = [
    "transition_tundish",
    "mold_level_slag_risk",
    "temperature_flux",
    "speed_stopper_flow",
    "process_fluctuation",
    "unknown_or_mixed_reason",
]

DISPLAY_NAMES = {
    "transition_tundish": "Transition/tundish",
    "mold_level_slag_risk": "Mold level/slag",
    "temperature_flux": "Temp/flux",
    "speed_stopper_flow": "Speed/flow",
    "process_fluctuation": "Process fluct.",
    "unknown_or_mixed_reason": "Unknown/mixed",
}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def parse_mechanisms(value: object) -> set[str]:
    if pd.isna(value):
        return set()
    parts = [p.strip() for p in str(value).split(";") if p.strip()]
    return {p for p in parts if p not in {"none", "no_reason_evidence"}}


def phi_matrix(binary: pd.DataFrame) -> pd.DataFrame:
    values = binary.to_numpy(dtype=float)
    corr = np.corrcoef(values, rowvar=False)
    corr = np.nan_to_num(corr, nan=0.0)
    np.fill_diagonal(corr, 1.0)
    return pd.DataFrame(corr, index=binary.columns, columns=binary.columns)


def cooccurrence_matrix(binary: pd.DataFrame) -> pd.DataFrame:
    values = binary.to_numpy(dtype=int)
    counts = values.T @ values
    return pd.DataFrame(counts, index=binary.columns, columns=binary.columns)


def diverging_color(v: float) -> tuple[int, int, int]:
    v = max(-1.0, min(1.0, float(v)))
    if v >= 0:
        t = v
        r0, g0, b0 = 248, 249, 251
        r1, g1, b1 = 178, 34, 34
    else:
        t = -v
        r0, g0, b0 = 248, 249, 251
        r1, g1, b1 = 36, 96, 160
    return (
        int(r0 + (r1 - r0) * t),
        int(g0 + (g1 - g0) * t),
        int(b0 + (b1 - b0) * t),
    )


def draw_heatmap(corr: pd.DataFrame, support: pd.Series, n_samples: int) -> None:
    labels = list(corr.index)
    n = len(labels)
    cell = 92
    left = 270
    top = 150
    right = 70
    bottom = 110
    width = left + n * cell + right
    height = top + n * cell + bottom

    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    title_font = font(24, bold=True)
    subtitle_font = font(14)
    label_font = font(13)
    value_font = font(14, bold=True)
    small_font = font(12)

    draw.text((28, 24), "Reason Mechanism Correlation Heatmap", fill=(32, 45, 60), font=title_font)
    subtitle = f"Phi correlation on reason_mechanism_set, n={n_samples:,}; diagonal shows self-correlation"
    draw.text((28, 62), subtitle, fill=(92, 104, 116), font=subtitle_font)

    for j, label in enumerate(labels):
        name = DISPLAY_NAMES.get(label, label)
        x = left + j * cell + cell // 2
        bbox = draw.textbbox((0, 0), name, font=label_font)
        draw.text((x - (bbox[2] - bbox[0]) // 2, top - 38), name, fill=(40, 48, 56), font=label_font)

    for i, label in enumerate(labels):
        name = DISPLAY_NAMES.get(label, label)
        y = top + i * cell + cell // 2
        bbox = draw.textbbox((0, 0), name, font=label_font)
        draw.text((left - 18 - (bbox[2] - bbox[0]), y - 8), name, fill=(40, 48, 56), font=label_font)
        sup = f"n={int(support[label]):,}"
        bbox2 = draw.textbbox((0, 0), sup, font=small_font)
        draw.text((left - 18 - (bbox2[2] - bbox2[0]), y + 12), sup, fill=(120, 126, 134), font=small_font)

    for i, row in enumerate(labels):
        for j, col in enumerate(labels):
            v = float(corr.loc[row, col])
            x0 = left + j * cell
            y0 = top + i * cell
            draw.rectangle((x0, y0, x0 + cell, y0 + cell), fill=diverging_color(v), outline=(220, 224, 228))
            text = f"{v:.2f}"
            bbox = draw.textbbox((0, 0), text, font=value_font)
            text_color = (255, 255, 255) if abs(v) > 0.55 else (30, 40, 50)
            draw.text(
                (x0 + (cell - (bbox[2] - bbox[0])) / 2, y0 + (cell - (bbox[3] - bbox[1])) / 2 - 2),
                text,
                fill=text_color,
                font=value_font,
            )

    legend_x = left
    legend_y = top + n * cell + 42
    legend_w = n * cell
    legend_h = 18
    for k in range(legend_w):
        v = -1 + 2 * k / max(1, legend_w - 1)
        draw.line((legend_x + k, legend_y, legend_x + k, legend_y + legend_h), fill=diverging_color(v))
    draw.rectangle((legend_x, legend_y, legend_x + legend_w, legend_y + legend_h), outline=(180, 184, 190))
    for text, frac in [("-1", 0), ("0", 0.5), ("+1", 1)]:
        x = legend_x + int(frac * legend_w)
        bbox = draw.textbbox((0, 0), text, font=small_font)
        draw.text((x - (bbox[2] - bbox[0]) / 2, legend_y + 24), text, fill=(70, 78, 86), font=small_font)
    draw.text((legend_x, legend_y - 24), "Phi correlation", fill=(70, 78, 86), font=small_font)

    PNG_OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(PNG_OUT)


def main() -> None:
    df = pd.read_csv(INPUT, usecols=["reason_available", "reason_mechanism_set"], low_memory=False)
    df = df[df["reason_available"].fillna(0).astype(int) == 1].copy()
    mechanism_sets = df["reason_mechanism_set"].map(parse_mechanisms)

    all_mechanisms = sorted({m for s in mechanism_sets for m in s})
    ordered = [m for m in MECHANISM_ORDER if m in all_mechanisms]
    ordered += [m for m in all_mechanisms if m not in ordered]

    binary = pd.DataFrame({m: [int(m in s) for s in mechanism_sets] for m in ordered})
    support = binary.sum().sort_values(ascending=False)
    keep = [m for m in ordered if support[m] >= 50]
    binary = binary[keep]
    support = binary.sum()

    corr = phi_matrix(binary)
    counts = cooccurrence_matrix(binary)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    corr.to_csv(CSV_OUT, encoding="utf-8-sig")
    counts.to_csv(COUNT_OUT, encoding="utf-8-sig")
    draw_heatmap(corr, support, len(binary))

    print(f"input={INPUT}")
    print(f"n_reason_samples={len(binary)}")
    print(f"mechanisms={','.join(keep)}")
    print(f"png={PNG_OUT}")
    print(f"matrix={CSV_OUT}")
    print(f"counts={COUNT_OUT}")


if __name__ == "__main__":
    main()
