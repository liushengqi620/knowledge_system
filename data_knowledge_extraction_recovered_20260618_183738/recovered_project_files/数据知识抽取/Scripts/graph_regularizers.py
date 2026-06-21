from __future__ import annotations

from typing import Any, Sequence

import numpy as np


def _row_normalize(x: np.ndarray) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float64)
    denom = np.sum(arr, axis=1, keepdims=True)
    denom = np.where(denom <= 0, 1.0, denom)
    return arr / denom


def edge_prior_kl_loss(
    posterior: np.ndarray,
    prior: np.ndarray,
    *,
    mask: np.ndarray | None = None,
    eps: float = 1e-8,
) -> float:
    post = np.asarray(posterior, dtype=np.float64)
    base = np.asarray(prior, dtype=np.float64)
    if post.shape != base.shape:
        raise ValueError("posterior and prior must have the same shape.")
    if mask is not None:
        m = np.asarray(mask, dtype=np.float64)
        if m.shape != post.shape:
            raise ValueError("mask must match posterior shape.")
        post = post * m
        base = base * m
    post = _row_normalize(np.clip(post, eps, None))
    base = _row_normalize(np.clip(base, eps, None))
    return float(np.mean(np.sum(post * (np.log(post + eps) - np.log(base + eps)), axis=1)))


def invariance_loss_by_regime(
    path_scores: np.ndarray,
    regimes: Sequence[Any],
    *,
    top_k: int = 5,
) -> float:
    scores = np.nan_to_num(np.asarray(path_scores, dtype=np.float64), nan=0.0, posinf=1.0, neginf=0.0)
    if scores.ndim != 2 or scores.shape[0] == 0:
        return 0.0
    regime_arr = np.asarray([str(x) for x in regimes], dtype=object)
    if len(regime_arr) != scores.shape[0]:
        raise ValueError("regimes length must match path_scores rows.")
    unique = sorted(set(regime_arr.tolist()))
    if len(unique) <= 1:
        return 0.0
    k = max(1, min(int(top_k), scores.shape[1]))
    distributions: list[np.ndarray] = []
    for regime in unique:
        block = scores[regime_arr == regime]
        if block.size == 0:
            continue
        contrib = np.mean(block, axis=0)
        keep = np.argsort(-contrib)[:k]
        sparse = np.zeros_like(contrib)
        sparse[keep] = contrib[keep]
        total = float(np.sum(sparse)) or 1.0
        distributions.append(sparse / total)
    if len(distributions) <= 1:
        return 0.0
    stacked = np.vstack(distributions)
    center = np.mean(stacked, axis=0, keepdims=True)
    return float(np.mean(np.abs(stacked - center)))


def counterfactual_path_consistency_loss(
    baseline_risk: np.ndarray,
    occluded_risk: np.ndarray,
    *,
    target_drop: float = 0.05,
) -> float:
    base = np.asarray(baseline_risk, dtype=np.float64).reshape(-1)
    occ = np.asarray(occluded_risk, dtype=np.float64).reshape(-1)
    if base.shape != occ.shape:
        raise ValueError("baseline_risk and occluded_risk must have the same shape.")
    drop = base - occ
    penalty = np.maximum(0.0, float(target_drop) - drop)
    return float(np.mean(penalty ** 2))


def sparsity_loss(path_scores: np.ndarray) -> float:
    scores = np.asarray(path_scores, dtype=np.float64)
    if scores.size == 0:
        return 0.0
    return float(np.mean(np.abs(scores)))
