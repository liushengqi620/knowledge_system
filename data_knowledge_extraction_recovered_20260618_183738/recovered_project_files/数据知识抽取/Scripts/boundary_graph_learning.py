from __future__ import annotations

from typing import Mapping, Sequence

import numpy as np
import pandas as pd

from research_types import GraphEdge


def _corr(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 3 or len(b) < 3:
        return 0.0
    aa = np.asarray(a, dtype=float)
    bb = np.asarray(b, dtype=float)
    if float(np.std(aa)) <= 1e-9 or float(np.std(bb)) <= 1e-9:
        return 0.0
    return float(np.nan_to_num(np.corrcoef(aa, bb)[0, 1], nan=0.0))


def _rank_corr(a: np.ndarray, b: np.ndarray) -> float:
    return _corr(pd.Series(a).rank().to_numpy(dtype=float), pd.Series(b).rank().to_numpy(dtype=float))


def _r2_against(y: np.ndarray, pred: np.ndarray) -> float:
    yy = np.asarray(y, dtype=float)
    pp = np.asarray(pred, dtype=float)
    denom = float(np.sum((yy - float(np.mean(yy))) ** 2))
    if denom <= 1e-9:
        return 0.0
    rss = float(np.sum((yy - pp) ** 2))
    return 1.0 - (rss / denom)


def _lag_gain(src: np.ndarray, dst: np.ndarray, lag: int) -> float:
    if lag <= 0 or len(src) <= lag + 5:
        return 0.0
    y_future = dst[lag:]
    dst_now = dst[:-lag]
    src_now = src[:-lag]
    base = _r2_against(y_future, dst_now)
    source = _r2_against(y_future, src_now)
    return float(max(0.0, source - base))


def _boundary_enrichment(src: np.ndarray, dst: np.ndarray, boundary_mask: np.ndarray, lag: int) -> float:
    if lag <= 0 or len(src) <= lag + 5:
        return 0.0
    s = src[:-lag]
    d = dst[lag:]
    b = boundary_mask[lag:]
    if int(np.sum(b)) < 3 or int(np.sum(~b)) < 3:
        return 0.0
    boundary_dep = max(abs(_corr(s[b], d[b])), abs(_rank_corr(s[b], d[b])))
    clear_dep = max(abs(_corr(s[~b], d[~b])), abs(_rank_corr(s[~b], d[~b])))
    return float(max(0.0, boundary_dep - clear_dep))


def _window_stability(src: np.ndarray, dst: np.ndarray, lag: int, windows: int = 4) -> float:
    if lag <= 0 or len(src) <= lag + 5:
        return 0.0
    n = len(src) - lag
    if n < windows * 3:
        return 0.0
    vals: list[float] = []
    for idx in np.array_split(np.arange(n), max(1, int(windows))):
        if len(idx) < 3:
            continue
        vals.append(abs(_corr(src[idx], dst[idx + lag])))
    if not vals:
        return 0.0
    vals_arr = np.asarray(vals, dtype=float)
    return float(np.clip(np.mean(vals_arr) * (1.0 - np.std(vals_arr)), 0.0, 1.0))


def learn_boundary_coupling_graph(
    df: pd.DataFrame,
    feature_cols: Sequence[str],
    rule_margin: Sequence[float] | np.ndarray | pd.Series,
    *,
    max_lag: int = 3,
    eps: float = 0.25,
    top_k: int = 36,
    direction_prior: Mapping[tuple[str, str], float] | None = None,
) -> list[GraphEdge]:
    cols = [str(c) for c in feature_cols if str(c) in df.columns]
    if len(cols) < 2:
        return []
    x = df[cols].apply(pd.to_numeric, errors="coerce")
    x = x.fillna(x.median(numeric_only=True)).fillna(0.0)
    margin = np.asarray(rule_margin, dtype=float).reshape(-1)
    if len(margin) != len(x):
        raise ValueError("rule_margin length must match df rows.")
    boundary_mask = np.abs(margin) <= float(eps)
    prior = dict(direction_prior or {})
    candidates: list[tuple[float, GraphEdge]] = []
    values = {col: x[col].to_numpy(dtype=float) for col in cols}
    for src in cols:
        for dst in cols:
            if src == dst:
                continue
            src_arr = values[src]
            dst_arr = values[dst]
            best: dict[str, float | int] | None = None
            for lag in range(1, max(1, int(max_lag)) + 1):
                gain = _lag_gain(src_arr, dst_arr, lag)
                boundary = _boundary_enrichment(src_arr, dst_arr, boundary_mask, lag)
                weak = max(abs(_corr(src_arr[:-lag], dst_arr[lag:])), abs(_rank_corr(src_arr[:-lag], dst_arr[lag:])))
                stability = _window_stability(src_arr, dst_arr, lag)
                process = float(np.clip(prior.get((src, dst), 0.0), 0.0, 1.0))
                score = (
                    0.30 * gain
                    + 0.25 * boundary
                    + 0.20 * stability
                    + 0.15 * process
                    + 0.10 * weak
                )
                if best is None or score > float(best["score"]):
                    best = {
                        "score": float(score),
                        "lag": int(lag),
                        "gain": float(gain),
                        "boundary": float(boundary),
                        "weak": float(weak),
                        "stability": float(stability),
                        "process": float(process),
                    }
            if best is None or float(best["score"]) <= 0:
                continue
            evidence = {
                "weak_corr": float(np.clip(best["weak"], 0.0, 1.0)),
                "lag_predictive_gain": float(np.clip(best["gain"], 0.0, 1.0)),
                "boundary_enrichment": float(np.clip(best["boundary"], 0.0, 1.0)),
                "stability": float(np.clip(best["stability"], 0.0, 1.0)),
                "process_direction": float(np.clip(best["process"], 0.0, 1.0)),
            }
            edge = GraphEdge(
                from_node=src,
                to_node=dst,
                weight=float(np.clip(best["score"], 0.0, 1.0)),
                confidence=float(np.clip(0.5 + 0.5 * max(evidence.values()), 0.0, 1.0)),
                source="boundary_graph_learning",
                rationale_id=f"boundary_lag{int(best['lag'])}_{src}_to_{dst}",
                relation_type="event_precursor",
                lag=int(best["lag"]),
                causal_strength=float(np.clip(best["gain"], 0.0, 1.0)),
                stability=float(np.clip(best["stability"], 0.0, 1.0)),
                evidence=evidence,
                dominant_source="lag_predictive_gain"
                if evidence["lag_predictive_gain"] >= evidence["boundary_enrichment"]
                else "boundary_enrichment",
            )
            candidates.append((float(best["score"]), edge))
    candidates.sort(key=lambda item: (-item[0], item[1].from_node, item[1].to_node))
    return [edge for _score, edge in candidates[: max(1, int(top_k))]]
