from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "knowledge_exports" / "continuous_casting_grouped" / "categories" / "quality_label.csv"
OUT_DIR = ROOT / "knowledge_exports" / "visualizations"
PNG_OUT = OUT_DIR / "quality_abnormal_code_phi_heatmap.png"
CSV_OUT = OUT_DIR / "quality_abnormal_code_phi_matrix.csv"
COUNT_OUT = OUT_DIR / "quality_abnormal_code_cooccurrence_counts.csv"
TOP_N = 25

GROUP_MAPPING = ROOT / "knowledge_exports" / "continuous_casting_grouped" / "quality_abnormal_group_mapping.json"


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


def normalize_code(value: object) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if text.lower() in {"", "nan", "none", "missing"}:
        return None
    try:
        code = int(float(text))
    except ValueError:
        return None
    return None if code == 0 else str(code)


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


def color(v: float) -> tuple[int, int, int]:
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


def text_color(v: float) -> tuple[int, int, int]:
    return (255, 255, 255) if abs(v) > 0.55 else (28, 36, 45)


def draw_heatmap(corr: pd.DataFrame, support: pd.Series, n_samples: int) -> None:
    labels = list(corr.index)
    n = len(labels)
    cell = 34
    left = 110
    top = 130
    right = 40
    bottom = 90
    width = left + n * cell + right
    height = top + n * cell + bottom

    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    title_font = font(22, bold=True)
    subtitle_font = font(13)
    label_font = font(11)
    value_font = font(8, bold=True)
    small_font = font(10)

    draw.text((24, 20), f"Top {n} Quality Abnormal Code Correlation", fill=(32, 45, 60), font=title_font)
    draw.text(
        (24, 54),
        f"Phi correlation on codes from 品质异常代码1-5, n={n_samples:,}; top codes selected by frequency",
        fill=(92, 104, 116),
        font=subtitle_font,
    )

    for j, label in enumerate(labels):
        x = left + j * cell + cell // 2
        bbox = draw.textbbox((0, 0), label, font=label_font)
        draw.text((x - (bbox[2] - bbox[0]) / 2, top - 22), label, fill=(50, 58, 68), font=label_font)

    for i, label in enumerate(labels):
        y = top + i * cell + cell // 2
        bbox = draw.textbbox((0, 0), label, font=label_font)
        draw.text((left - 12 - (bbox[2] - bbox[0]), y - 7), label, fill=(50, 58, 68), font=label_font)

    for i, row in enumerate(labels):
        for j, col in enumerate(labels):
            v = float(corr.loc[row, col])
            x0 = left + j * cell
            y0 = top + i * cell
            draw.rectangle((x0, y0, x0 + cell, y0 + cell), fill=color(v), outline=(221, 225, 230))
            if i != j:
                text = f"{v:.2f}"
                bbox = draw.textbbox((0, 0), text, font=value_font)
                draw.text(
                    (x0 + (cell - (bbox[2] - bbox[0])) / 2, y0 + (cell - (bbox[3] - bbox[1])) / 2),
                    text,
                    fill=text_color(v),
                    font=value_font,
                )

    legend_x = left
    legend_y = top + n * cell + 35
    legend_w = min(520, n * cell)
    legend_h = 14
    for k in range(legend_w):
        v = -1 + 2 * k / max(1, legend_w - 1)
        draw.line((legend_x + k, legend_y, legend_x + k, legend_y + legend_h), fill=color(v))
    draw.rectangle((legend_x, legend_y, legend_x + legend_w, legend_y + legend_h), outline=(180, 184, 190))
    for text, frac in [("-1", 0), ("0", 0.5), ("+1", 1)]:
        x = legend_x + int(frac * legend_w)
        bbox = draw.textbbox((0, 0), text, font=small_font)
        draw.text((x - (bbox[2] - bbox[0]) / 2, legend_y + 18), text, fill=(70, 78, 86), font=small_font)
    draw.text((legend_x, legend_y - 19), "Phi correlation", fill=(70, 78, 86), font=small_font)

    support_lines = [f"{c}: n={int(support[c]):,}" for c in labels[:10]]
    draw.text((left + legend_w + 24, legend_y - 20), "Top supports", fill=(70, 78, 86), font=small_font)
    for k, line in enumerate(support_lines):
        draw.text((left + legend_w + 24, legend_y + 2 + k * 14), line, fill=(96, 104, 112), font=small_font)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    img.save(PNG_OUT)


def main() -> None:
    code_cols = [f"品质异常代码{i}" for i in range(1, 6)]
    df = pd.read_csv(INPUT, usecols=code_cols, low_memory=False)
    rows: list[set[str]] = []
    for _, row in df.iterrows():
        codes = {code for code in (normalize_code(row[col]) for col in code_cols) if code is not None}
        rows.append(codes)

    all_codes = pd.Series([code for codes in rows for code in codes])
    top_codes = all_codes.value_counts().head(TOP_N).index.tolist()
    top_codes = sorted(top_codes, key=lambda x: int(x))
    binary = pd.DataFrame({code: [int(code in codes) for codes in rows] for code in top_codes})
    support = binary.sum()
    corr = phi_matrix(binary)
    counts = cooccurrence_matrix(binary)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    corr.to_csv(CSV_OUT, encoding="utf-8-sig")
    counts.to_csv(COUNT_OUT, encoding="utf-8-sig")
    draw_heatmap(corr, support, len(binary))

    print(f"input={INPUT}")
    print(f"n_rows={len(binary)}")
    print(f"codes={','.join(top_codes)}")
    print(f"png={PNG_OUT}")
    print(f"matrix={CSV_OUT}")
    print(f"counts={COUNT_OUT}")


if __name__ == "__main__":
    main()
