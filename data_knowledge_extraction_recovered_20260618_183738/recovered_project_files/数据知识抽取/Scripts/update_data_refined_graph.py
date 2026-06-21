from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from config import CONFIG
from data_processing import load_and_process_data
from feature_extraction import base_feature_columns
from prior_loop import run_prior_auto_relax


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _line_filter(df: pd.DataFrame, caster_id: str | None, strand_parity: str | None) -> pd.DataFrame:
    out = df
    if caster_id is not None and "铸机号" in out.columns:
        out = out.loc[out["铸机号"].astype("string").str.strip() == str(caster_id).strip()].copy()
    if strand_parity is not None and "奇偶流区分" in out.columns:
        out = out.loc[out["奇偶流区分"].astype("string").str.strip() == str(strand_parity).strip()].copy()
    return out


def _auto_line(df: pd.DataFrame) -> tuple[str | None, str | None]:
    if not {"铸机号", "奇偶流区分", "defect_label"}.issubset(df.columns):
        return None, None
    rows: list[tuple[int, int, str, str]] = []
    for (caster, parity), g in df.groupby(["铸机号", "奇偶流区分"], dropna=True):
        y = pd.to_numeric(g["defect_label"], errors="coerce").fillna(0).astype(int)
        rows.append((len(g), int(y.sum()), str(caster).strip(), str(parity).strip()))
    rows.sort(key=lambda x: (min(x[1], x[0] - x[1]), x[0]), reverse=True)
    return (rows[0][2], rows[0][3]) if rows else (None, None)


def _numeric_matrix(df: pd.DataFrame, cols: list[str]) -> tuple[np.ndarray, list[str]]:
    clean_cols: list[str] = []
    arrays: list[np.ndarray] = []
    for col in cols:
        x = pd.to_numeric(df[col], errors="coerce").to_numpy(dtype=np.float64)
        finite = np.isfinite(x)
        if int(finite.sum()) < max(20, int(0.2 * len(x))):
            continue
        med = float(np.nanmedian(x[finite])) if finite.any() else 0.0
        x = np.where(finite, x, med)
        std = float(np.std(x))
        if std <= 1e-9:
            continue
        arrays.append((x - float(np.mean(x))) / std)
        clean_cols.append(col)
    if not arrays:
        return np.zeros((len(df), 0), dtype=np.float32), []
    return np.column_stack(arrays).astype(np.float32), clean_cols


def _corr_at_lag(x: np.ndarray, y: np.ndarray, lag: int) -> float:
    if lag <= 0:
        a, b = x, y
    else:
        a, b = x[:-lag], y[lag:]
    if len(a) < 20:
        return 0.0
    av = float(np.std(a))
    bv = float(np.std(b))
    if av <= 1e-9 or bv <= 1e-9:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def _best_lag(x: np.ndarray, y: np.ndarray, max_lag: int) -> tuple[int, float]:
    vals = [(lag, _corr_at_lag(x, y, lag)) for lag in range(max_lag + 1)]
    vals.sort(key=lambda z: abs(z[1]), reverse=True)
    return vals[0]


def _window_stability(x: np.ndarray, y: np.ndarray, lag: int, windows: int, min_abs_corr: float) -> tuple[float, float, int]:
    n = len(x)
    if n < windows * 20:
        return 0.0, 0.0, 0
    vals: list[float] = []
    for idx in np.array_split(np.arange(n), windows):
        if len(idx) <= lag + 20:
            continue
        xv = x[idx]
        yv = y[idx]
        vals.append(_corr_at_lag(xv, yv, lag))
    if not vals:
        return 0.0, 0.0, 0
    arr = np.asarray(vals, dtype=np.float64)
    mean_abs = float(np.mean(np.abs(arr)))
    support = int(np.sum(np.abs(arr) >= min_abs_corr * 0.6))
    stability = float(np.clip((mean_abs / (mean_abs + float(np.std(np.abs(arr))) + 1e-6)) * (support / max(len(arr), 1)), 0.0, 1.0))
    return stability, mean_abs, support


def _relation_type(src: str, dst: str) -> str:
    text = f"{src} {dst}".lower()
    if "level" in text or "speed" in text or "weight" in text:
        if "range" in text or "control" in text:
            return "control_feedback"
    if "quality" in text or "defect" in text or "fault" in text:
        return "quality_effect"
    if "corr" in text:
        return "correlation"
    return "causal_lag"


def build_data_refined_edges(
    x: np.ndarray,
    cols: list[str],
    *,
    max_lag: int,
    min_abs_corr: float,
    direction_margin: float,
    top_k: int,
    windows: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []
    n_features = len(cols)
    for i in range(n_features):
        xi = x[:, i]
        for j in range(n_features):
            if i == j:
                continue
            yj = x[:, j]
            lag_f, corr_f = _best_lag(xi, yj, max_lag)
            lag_r, corr_r = _best_lag(yj, xi, max_lag)
            f_abs = abs(corr_f)
            r_abs = abs(corr_r)
            direction_supported = f_abs >= max(min_abs_corr, r_abs + direction_margin)
            if not direction_supported:
                continue
            stability, window_abs_corr, support = _window_stability(
                xi,
                yj,
                lag_f,
                windows,
                min_abs_corr,
            )
            margin = max(0.0, f_abs - r_abs)
            score = float(np.clip(0.62 * f_abs + 0.26 * stability + 0.12 * margin, 0.0, 1.0))
            confidence = float(np.clip(0.35 + 0.45 * f_abs + 0.20 * stability, 0.0, 1.0))
            candidates.append(
                {
                    "from": cols[i],
                    "to": cols[j],
                    "lag": int(lag_f),
                    "forward_corr": float(corr_f),
                    "forward_abs_corr": float(f_abs),
                    "reverse_best_lag": int(lag_r),
                    "reverse_best_abs_corr": float(r_abs),
                    "direction_margin": float(margin),
                    "direction_supported": True,
                    "window_abs_corr": float(window_abs_corr),
                    "window_support": int(support),
                    "stability": float(stability),
                    "score": score,
                    "weight": score,
                    "confidence": confidence,
                    "causal_strength": float(np.clip(0.55 * f_abs + 0.45 * margin, 0.0, 1.0)),
                    "relation_type": _relation_type(cols[i], cols[j]),
                    "source": "data_refined_lag_corr",
                    "rationale_id": f"data_lag_corr_{i}_{j}",
                    "legal": True,
                }
            )
    candidates.sort(key=lambda r: (-float(r["score"]), -float(r["confidence"])))
    edges = candidates[:top_k]
    return edges, candidates


def main() -> None:
    parser = argparse.ArgumentParser(description="Update graph prior from current casting data.")
    parser.add_argument("--caster-id", default=None)
    parser.add_argument("--strand-parity", default=None)
    parser.add_argument("--max-lag", type=int, default=5)
    parser.add_argument("--min-abs-corr", type=float, default=0.08)
    parser.add_argument("--direction-margin", type=float, default=0.015)
    parser.add_argument("--top-k", type=int, default=80)
    parser.add_argument("--windows", type=int, default=5)
    parser.add_argument("--output", default=str(CONFIG.get("data_refined_prior_path", "knowledge_exports/graph_update/data_refined_graph_prior.json")))
    args = parser.parse_args()

    cfg = dict(CONFIG)
    df = load_and_process_data(str(cfg.get("file_path")))
    caster = args.caster_id
    parity = args.strand_parity
    if caster is None and parity is None:
        caster, parity = _auto_line(df)
        if caster is not None and parity is not None:
            print(f"图更新自动选择线路：铸机号={caster}，奇偶流区分={parity}")
    df = _line_filter(df, caster, parity)
    df, _rules = run_prior_auto_relax(df, cfg)
    if "process_time" in df.columns:
        df = df.sort_values("process_time", kind="stable").reset_index(drop=True)

    feature_cols = base_feature_columns(df)
    x, cols = _numeric_matrix(df, feature_cols)
    if x.shape[1] < 2:
        raise RuntimeError("Not enough numeric feature columns for graph update.")

    edges, candidates = build_data_refined_edges(
        x,
        cols,
        max_lag=max(0, int(args.max_lag)),
        min_abs_corr=float(args.min_abs_corr),
        direction_margin=float(args.direction_margin),
        top_k=max(1, int(args.top_k)),
        windows=max(2, int(args.windows)),
    )

    out = Path(args.output)
    if not out.is_absolute():
        out = PROJECT_ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "source": "data_refined_lag_correlation",
        "line_filter": {"caster_id": caster, "strand_parity": parity},
        "rows": int(len(df)),
        "num_features": int(len(cols)),
        "max_lag": int(args.max_lag),
        "min_abs_corr": float(args.min_abs_corr),
        "direction_margin": float(args.direction_margin),
        "top_k": int(args.top_k),
        "edges": edges,
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    csv_path = out.with_suffix(".candidates.csv")
    pd.DataFrame(candidates).to_csv(csv_path, index=False, encoding="utf-8-sig")
    top_csv_path = out.with_suffix(".top_edges.csv")
    pd.DataFrame(edges).to_csv(top_csv_path, index=False, encoding="utf-8-sig")

    print(f"数据驱动图先验已更新：{out}")
    print(f"候选边明细：{csv_path}")
    print(f"Top 边明细：{top_csv_path}")
    print(f"有效特征数={len(cols)}，候选边={len(candidates)}，写入边={len(edges)}")
    for row in edges[:10]:
        print(
            f"  {row['from']} -> {row['to']} "
            f"lag={row['lag']} weight={row['weight']:.3f} "
            f"corr={row['forward_corr']:.3f} stability={row['stability']:.3f}"
        )


if __name__ == "__main__":
    main()
