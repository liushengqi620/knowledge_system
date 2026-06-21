from __future__ import annotations

import argparse
import json
import math
import os
import re
import time
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.cluster import KMeans
from sklearn.feature_selection import f_classif
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, precision_recall_fscore_support, precision_score, recall_score
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.preprocessing import StandardScaler

from ms_gse_rpf_model import (
    MSGSERPFConfig,
    MSGSERPFNet,
    class_balanced_weights,
    count_trainable_parameters,
    graph_regularization,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_READY_ROOT = PROJECT_ROOT / "knowledge_exports" / "public_benchmark_ready"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "knowledge_exports" / "ms_gse_rpf"


def _fs_path(path: Path) -> str:
    if os.name == "nt":
        resolved = str(Path(path).resolve())
        if not resolved.startswith("\\\\?\\"):
            return "\\\\?\\" + resolved
    return str(path)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    Path(_fs_path(path.parent)).mkdir(parents=True, exist_ok=True)
    with open(_fs_path(path), "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def validation_gain_admission_decision(
    *,
    candidate_metric: float,
    baseline_metric: float,
    min_gain: float = 0.0,
    metric_name: str = "macro_f1",
) -> dict[str, Any]:
    candidate_value = float(candidate_metric)
    baseline_value = float(baseline_metric)
    gain = candidate_value - baseline_value
    threshold = float(min_gain)
    selected = "candidate" if gain >= threshold else "baseline"
    return {
        "enabled": True,
        "metric": str(metric_name),
        "candidate_metric": candidate_value,
        "baseline_metric": baseline_value,
        "validation_gain": float(gain),
        "min_gain": threshold,
        "selected": selected,
        "admitted": selected == "candidate",
    }


def resolve_torch_device(device: str = "auto") -> torch.device:
    requested = str(device or "auto").strip().lower()
    if requested == "auto":
        requested = "cuda" if torch.cuda.is_available() else "cpu"
    if requested.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but the installed PyTorch build does not expose CUDA.")
    return torch.device(requested)


def _safe_slug(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in str(value)).strip("_") or "none"


@dataclass
class ReadyTask:
    dataset: str
    target: str
    task: str
    x: pd.DataFrame
    meta: pd.DataFrame
    labels: np.ndarray
    feature_cols: list[str]
    group_cols: list[str]
    order_col: str | None
    ready_dir: Path


@dataclass
class SplitBundle:
    train_idx: np.ndarray
    val_idx: np.ndarray
    test_idx: np.ndarray
    classes: list[int]
    y_internal: np.ndarray
    class_id_mapping: dict[str, int]
    split_protocol: str
    validation_group_cols: list[str]


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(_fs_path(path), low_memory=False)


def _numeric_feature_columns(x: pd.DataFrame, exclude: set[str]) -> list[str]:
    cols: list[str] = []
    for col in x.columns:
        if str(col) in exclude:
            continue
        values = pd.to_numeric(x[col], errors="coerce")
        if values.notna().mean() > 0.0 and values.nunique(dropna=True) > 1:
            cols.append(str(col))
    if not cols:
        raise ValueError("No numeric model features found.")
    return cols


STAT_SUFFIXES = ("_last_minus_first", "_mean", "_std", "_min", "_max")


def feature_group_name(feature: str) -> str:
    name = str(feature)
    for suffix in STAT_SUFFIXES:
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def infer_feature_group_ids(feature_cols: Sequence[str]) -> np.ndarray:
    group_to_id: dict[str, int] = {}
    ids: list[int] = []
    for col in feature_cols:
        group = feature_group_name(str(col))
        if group not in group_to_id:
            group_to_id[group] = len(group_to_id)
        ids.append(group_to_id[group])
    return np.asarray(ids, dtype=np.int64)


def resolve_path_budget(max_paths: int, n_feature_groups: int, *, auto_path_budget: bool = False) -> int:
    requested = max(1, int(max_paths))
    if not bool(auto_path_budget):
        return requested
    group_budget = min(24, 2 * max(1, int(n_feature_groups)))
    return max(requested, int(group_budget))


def _spread_group_scores(scores: np.ndarray, feature_group_ids: np.ndarray) -> np.ndarray:
    values = np.asarray(scores, dtype=np.float64)
    group_scores = np.zeros_like(values, dtype=np.float64)
    groups = np.asarray(feature_group_ids, dtype=np.int64)
    for group in sorted(np.unique(groups)):
        mask = groups == int(group)
        group_scores[mask] = float(np.max(values[mask])) if np.any(mask) else 0.0
    return np.asarray(np.clip(group_scores, 0.0, 1.0), dtype=np.float32)


def _train_order_values(task: ReadyTask, train_idx: np.ndarray) -> np.ndarray | None:
    if not task.order_col:
        return None
    if task.order_col in task.meta.columns:
        values = pd.to_numeric(task.meta[task.order_col], errors="coerce")
    elif task.order_col in task.x.columns:
        values = pd.to_numeric(task.x[task.order_col], errors="coerce")
    else:
        return None
    order = values.iloc[np.asarray(train_idx, dtype=np.int64)].to_numpy(dtype=np.float64)
    if np.isfinite(order).sum() < 3 or float(np.nanmax(order) - np.nanmin(order)) <= 0.0:
        return None
    fill = float(np.nanmedian(order[np.isfinite(order)]))
    return np.nan_to_num(order, nan=fill, posinf=fill, neginf=fill)


def _rank_abs_correlation(x_train: np.ndarray, order: np.ndarray) -> np.ndarray:
    if x_train.shape[0] != len(order) or x_train.shape[0] < 3:
        return np.zeros(x_train.shape[1], dtype=np.float64)
    feature_rank = pd.DataFrame(x_train).rank(axis=0, method="average").to_numpy(dtype=np.float64)
    order_rank = pd.Series(order).rank(method="average").to_numpy(dtype=np.float64)
    feature_rank = feature_rank - np.nanmean(feature_rank, axis=0, keepdims=True)
    order_rank = order_rank - float(np.nanmean(order_rank))
    numerator = np.nansum(feature_rank * order_rank[:, None], axis=0)
    denom = np.sqrt(np.nansum(feature_rank * feature_rank, axis=0) * float(np.nansum(order_rank * order_rank)))
    corr = np.divide(numerator, denom, out=np.zeros_like(numerator), where=denom > 1.0e-12)
    return np.nan_to_num(np.abs(corr), nan=0.0, posinf=0.0, neginf=0.0)


def _node_pair_evidence(
    salience: np.ndarray,
    lifecycle_salience: np.ndarray | None,
    *,
    task: ReadyTask,
    lifecycle_weight: float,
    order_anchor_weight: float,
) -> np.ndarray:
    node = np.asarray(salience, dtype=np.float32)
    node_for_pair = node.copy()
    order_idx = None
    if task.order_col in task.feature_cols:
        order_idx = int(task.feature_cols.index(str(task.order_col)))
        node_for_pair[order_idx] = min(float(node_for_pair[order_idx]), float(np.clip(order_anchor_weight, 0.0, 1.0)))
    evidence = np.maximum(node_for_pair[:, None], node_for_pair[None, :]).astype(np.float32)
    if lifecycle_salience is not None and len(lifecycle_salience) == len(node):
        life = np.asarray(lifecycle_salience, dtype=np.float32)
        coherence = np.sqrt(np.maximum(0.0, life[:, None] * life[None, :])).astype(np.float32)
        evidence = np.maximum(evidence, float(lifecycle_weight) * coherence)
        if order_idx is not None:
            anchor = float(np.clip(order_anchor_weight, 0.0, 1.0))
            evidence[:, order_idx] = np.maximum(evidence[:, order_idx], anchor * life)
            evidence[order_idx, :] = np.maximum(evidence[order_idx, :], anchor * life)
    np.fill_diagonal(evidence, 0.0)
    return np.asarray(np.clip(evidence, 0.0, 1.0), dtype=np.float32)


def compute_train_group_salience(
    task: ReadyTask,
    train_idx: np.ndarray,
    y_internal: np.ndarray,
    feature_group_ids: np.ndarray,
    *,
    mode: str = "class",
    lifecycle_weight: float = 0.50,
    order_anchor_weight: float = 0.35,
    evidence_top_k: int = 0,
) -> tuple[np.ndarray, dict[str, Any]]:
    values = task.x[task.feature_cols].apply(pd.to_numeric, errors="coerce")
    train_values = values.iloc[np.asarray(train_idx, dtype=np.int64)].copy()
    medians = train_values.median(numeric_only=True)
    x_train = train_values.fillna(medians).fillna(0.0).to_numpy(dtype=np.float64)
    y_train = np.asarray(y_internal, dtype=np.int64)[np.asarray(train_idx, dtype=np.int64)]
    requested_mode = str(mode or "class").strip().lower()
    effective_mode = requested_mode
    if effective_mode == "auto":
        effective_mode = "class_lifecycle" if task.dataset == "cmapss" and task.order_col else "class"

    if len(np.unique(y_train)) < 2 or x_train.shape[1] == 0:
        class_salience = np.zeros(len(task.feature_cols), dtype=np.float32)
    else:
        with np.errstate(all="ignore"), warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            scores, _p = f_classif(x_train, y_train)
        scores = np.nan_to_num(scores, nan=0.0, posinf=0.0, neginf=0.0)
        scores = np.maximum(scores, 0.0)
        transformed = np.log1p(scores)
        if float(np.max(transformed)) > 0.0:
            transformed = transformed / float(np.max(transformed))
        class_salience = _spread_group_scores(transformed, feature_group_ids)

    lifecycle_salience: np.ndarray | None = None
    lifecycle_enabled = effective_mode in {"lifecycle", "class_lifecycle"}
    if lifecycle_enabled:
        order = _train_order_values(task, train_idx)
        if order is not None:
            lifecycle_raw = _rank_abs_correlation(x_train, order)
            if float(np.max(lifecycle_raw)) > 0.0:
                lifecycle_raw = lifecycle_raw / float(np.max(lifecycle_raw))
            lifecycle_salience = _spread_group_scores(lifecycle_raw, feature_group_ids)
        else:
            lifecycle_salience = np.zeros(len(task.feature_cols), dtype=np.float32)

    weight = float(np.clip(lifecycle_weight, 0.0, 1.0))
    if effective_mode == "lifecycle":
        salience = np.asarray(lifecycle_salience if lifecycle_salience is not None else class_salience, dtype=np.float32)
    elif effective_mode == "class_lifecycle" and lifecycle_salience is not None:
        salience = np.asarray((1.0 - weight) * class_salience + weight * lifecycle_salience, dtype=np.float32)
        if float(np.max(salience)) > 0.0:
            salience = salience / float(np.max(salience))
    else:
        salience = class_salience

    path_salience = np.asarray(salience, dtype=np.float32).copy()
    top_k = int(evidence_top_k)
    if top_k > 0 and top_k < len(path_salience):
        keep = np.zeros(len(path_salience), dtype=bool)
        top_idx = np.argsort(-path_salience)[:top_k]
        keep[top_idx] = True
        if task.order_col in task.feature_cols:
            keep[int(task.feature_cols.index(str(task.order_col)))] = True
        path_salience = np.where(keep, path_salience, 0.0).astype(np.float32)

    path_evidence = _node_pair_evidence(
        path_salience,
        lifecycle_salience,
        task=task,
        lifecycle_weight=weight,
        order_anchor_weight=order_anchor_weight,
    )
    top_features = [
        {
            "feature": str(task.feature_cols[int(idx)]),
            "salience": float(salience[int(idx)]),
            "class_salience": float(class_salience[int(idx)]),
            "lifecycle_salience": float(lifecycle_salience[int(idx)]) if lifecycle_salience is not None else 0.0,
        }
        for idx in np.argsort(-salience)[:10]
        if float(salience[int(idx)]) > 0.0
    ]
    return salience, {
        "enabled": True,
        "source": "train_only_algorithmic_path_evidence",
        "mode": effective_mode,
        "requested_mode": requested_mode,
        "lifecycle_weight": weight,
        "order_anchor_weight": float(np.clip(order_anchor_weight, 0.0, 1.0)),
        "evidence_top_k": top_k,
        "order_col": task.order_col,
        "lifecycle_enabled": bool(lifecycle_enabled and lifecycle_salience is not None),
        "max_salience": float(np.max(salience)) if len(salience) else 0.0,
        "mean_salience": float(np.mean(salience)) if len(salience) else 0.0,
        "mean_class_salience": float(np.mean(class_salience)) if len(class_salience) else 0.0,
        "mean_lifecycle_salience": float(np.mean(lifecycle_salience)) if lifecycle_salience is not None and len(lifecycle_salience) else 0.0,
        "path_salience_nonzero": int(np.count_nonzero(path_salience)),
        "path_evidence_density": float(np.mean(path_evidence > 0.0)) if path_evidence.size else 0.0,
        "path_evidence_mean": float(np.mean(path_evidence)) if path_evidence.size else 0.0,
        "path_evidence_matrix": path_evidence,
        "top_features": top_features,
    }


def compute_train_class_path_evidence(
    x_train: np.ndarray,
    y_train: np.ndarray,
    feature_group_ids: np.ndarray,
    *,
    n_classes: int,
    top_k: int = 0,
    mode: str = "static",
    max_lag: int = 0,
    lag_weight: float = 0.50,
    family_k: int = 0,
    family_weight: float = 0.0,
    focus_mode: str = "none",
    focus_classes: Sequence[int] | None = None,
    focus_k: int = 0,
    focus_nonfocus_weight: float = 0.0,
) -> tuple[np.ndarray, dict[str, Any]]:
    x = np.asarray(x_train, dtype=np.float32)
    y = np.asarray(y_train, dtype=np.int64).reshape(-1)
    n_features = int(x.shape[2]) if x.ndim == 3 else 0
    class_evidence = np.zeros((int(n_classes), n_features, n_features), dtype=np.float32)
    if x.ndim != 3 or len(y) != x.shape[0] or n_features == 0:
        return class_evidence, {"enabled": False, "status": "invalid_input"}

    descriptors = [
        x[:, -1, :],
        np.mean(x, axis=1),
        x[:, -1, :] - x[:, 0, :],
        np.std(x, axis=1),
    ]
    desc = np.stack(descriptors, axis=1).astype(np.float32)
    groups = np.asarray(feature_group_ids, dtype=np.int64)
    evidence_mode = str(mode or "static").strip().lower()
    if evidence_mode not in {"static", "lag", "static_lag"}:
        evidence_mode = "static"
    lag_limit = max(0, min(int(max_lag), int(x.shape[1]) - 1))
    lag_mix = float(np.clip(lag_weight, 0.0, 1.0))
    top_features_by_class: dict[str, list[int]] = {}
    nonzero_by_class: dict[str, int] = {}
    top_edges_by_class: dict[str, list[dict[str, float | int]]] = {}
    node_by_class = np.zeros((int(n_classes), n_features), dtype=np.float32)
    train_separation_by_class = np.zeros(int(n_classes), dtype=np.float32)
    class_centroid_by_class = np.zeros((int(n_classes), n_features), dtype=np.float32)
    valid_class = np.zeros(int(n_classes), dtype=bool)
    lag_support_values: list[float] = []
    for cls in range(int(n_classes)):
        pos = y == int(cls)
        neg = ~pos
        if int(pos.sum()) < 2 or int(neg.sum()) < 2:
            continue
        pos_mean = np.nanmean(desc[pos], axis=0)
        neg_mean = np.nanmean(desc[neg], axis=0)
        class_centroid_by_class[cls] = np.nanmean(pos_mean, axis=0).astype(np.float32)
        pooled_std = np.nanstd(desc, axis=0) + 1.0e-6
        effect = np.nanmax(np.abs(pos_mean - neg_mean) / pooled_std, axis=0)
        effect = np.nan_to_num(effect, nan=0.0, posinf=0.0, neginf=0.0)
        effect = np.maximum(effect, 0.0)
        if effect.size:
            top_count = max(1, min(8, int(effect.size)))
            train_separation_by_class[cls] = float(np.mean(np.sort(effect)[-top_count:]))
        if float(np.max(effect)) > 0.0:
            effect = effect / float(np.max(effect))
        node = _spread_group_scores(effect, groups)
        if int(top_k) > 0 and int(top_k) < n_features:
            keep = np.zeros(n_features, dtype=bool)
            keep[np.argsort(-node)[: int(top_k)]] = True
            node = np.where(keep, node, 0.0).astype(np.float32)
        node_by_class[cls] = node
        valid_class[cls] = bool(np.count_nonzero(node) > 0)
        pair = np.maximum(node[:, None], node[None, :]).astype(np.float32)
        np.fill_diagonal(pair, 0.0)
        if evidence_mode in {"lag", "static_lag"} and lag_limit > 0:
            lag_support = _class_lag_support_matrix(x[pos], node, lag_limit)
            lag_support_values.extend(float(v) for v in lag_support[lag_support > 0.0].reshape(-1)[:500])
            lag_pair = pair * lag_support
            if evidence_mode == "lag":
                pair = lag_pair
            else:
                pair = ((1.0 - lag_mix) * pair + lag_mix * lag_pair).astype(np.float32)
        class_evidence[cls] = np.asarray(np.clip(pair, 0.0, 1.0), dtype=np.float32)
        top_features_by_class[str(cls)] = [int(i) for i in np.argsort(-node)[:10] if float(node[int(i)]) > 0.0]
        nonzero_by_class[str(cls)] = int(np.count_nonzero(node))
        flat = class_evidence[cls].reshape(-1)
        top_edges: list[dict[str, float | int]] = []
        for flat_idx in np.argsort(-flat)[:10]:
            score = float(flat[int(flat_idx)])
            if score <= 0.0:
                continue
            target_idx = int(flat_idx // n_features)
            source_idx = int(flat_idx % n_features)
            if target_idx == source_idx:
                continue
            top_edges.append({"target": target_idx, "source": source_idx, "score": score})
        top_edges_by_class[str(cls)] = top_edges

    family_neighbors_by_class: dict[str, list[dict[str, float | int]]] = {}
    family_count_by_class: dict[str, int] = {}
    family_mix = float(np.clip(family_weight, 0.0, 1.0))
    family_enabled = int(family_k) > 0 and family_mix > 0.0 and int(np.count_nonzero(valid_class)) > 1
    if family_enabled:
        norms = np.linalg.norm(node_by_class, axis=1, keepdims=True) + 1.0e-12
        normalized = node_by_class / norms
        similarity = normalized @ normalized.T
        similarity = np.nan_to_num(similarity, nan=0.0, posinf=0.0, neginf=0.0)
        np.fill_diagonal(similarity, -1.0)
        for cls in range(int(n_classes)):
            if not bool(valid_class[cls]):
                continue
            candidates = [
                int(idx)
                for idx in np.argsort(-similarity[cls])
                if idx != cls and bool(valid_class[int(idx)]) and float(similarity[cls, int(idx)]) > 0.0
            ][: int(family_k)]
            if not candidates:
                family_neighbors_by_class[str(cls)] = []
                family_count_by_class[str(cls)] = 0
                continue
            weights = np.asarray([max(0.0, float(similarity[cls, idx])) for idx in candidates], dtype=np.float32)
            if float(np.sum(weights)) <= 1.0e-8:
                weights = np.ones(len(candidates), dtype=np.float32)
            weights = weights / float(np.sum(weights))
            family_proto = np.zeros_like(class_evidence[cls])
            for idx, weight in zip(candidates, weights):
                family_proto += float(weight) * class_evidence[int(idx)]
            class_evidence[cls] = np.asarray(
                np.clip((1.0 - family_mix) * class_evidence[cls] + family_mix * family_proto, 0.0, 1.0),
                dtype=np.float32,
            )
            family_neighbors_by_class[str(cls)] = [
                {"class": int(idx), "similarity": float(similarity[cls, int(idx)])}
                for idx in candidates
            ]
            family_count_by_class[str(cls)] = int(len(candidates))

    valid_indices_for_distance = [int(cls) for cls in range(int(n_classes)) if bool(valid_class[cls])]
    if len(valid_indices_for_distance) > 1:
        global_scale = np.nanstd(desc.reshape(-1, n_features), axis=0).astype(np.float32) + 1.0e-6
        for cls in valid_indices_for_distance:
            distances = []
            for other in valid_indices_for_distance:
                if other == cls:
                    continue
                diff = (class_centroid_by_class[cls] - class_centroid_by_class[other]) / global_scale
                distances.append(float(np.sqrt(np.mean(diff * diff))))
            if distances:
                train_separation_by_class[cls] = float(min(distances))

    focus_name = str(focus_mode or "none").strip().lower()
    if focus_name not in {"none", "explicit", "low_train_separation"}:
        focus_name = "none"
    explicit_focus = {
        int(cls)
        for cls in _parse_optional_ints(focus_classes)
        if 0 <= int(cls) < int(n_classes)
    }
    if focus_name == "none" and explicit_focus:
        focus_name = "explicit"
    focus_set: set[int] = set()
    if focus_name == "explicit":
        focus_set = set(explicit_focus)
    elif focus_name == "low_train_separation":
        valid_indices = [
            int(cls)
            for cls in range(int(n_classes))
            if bool(valid_class[cls]) and float(train_separation_by_class[cls]) > 0.0
        ]
        k = int(focus_k) if int(focus_k) > 0 else max(1, min(len(valid_indices), int(round(max(1, int(n_classes)) * 0.25))))
        focus_set = set(sorted(valid_indices, key=lambda cls: float(train_separation_by_class[cls]))[:k])
        focus_set.update(explicit_focus)
    focus_mix = float(np.clip(focus_nonfocus_weight, 0.0, 1.0))
    focus_enabled = focus_name != "none" and bool(focus_set)
    if focus_enabled:
        for cls in range(int(n_classes)):
            if int(cls) not in focus_set:
                class_evidence[cls] = np.asarray(focus_mix * class_evidence[cls], dtype=np.float32)

    return class_evidence, {
        "enabled": True,
        "source": "train_only_class_conditioned_path_evidence"
        if evidence_mode == "static"
        else "train_only_class_conditioned_lag_path_evidence",
        "mode": evidence_mode,
        "top_k": int(top_k),
        "max_lag": int(lag_limit),
        "lag_weight": float(lag_mix),
        "family_enabled": bool(family_enabled),
        "family_k": int(family_k),
        "family_weight": float(family_mix),
        "focus_enabled": bool(focus_enabled),
        "focus_mode": str(focus_name),
        "focus_k": int(focus_k),
        "focus_classes": [int(cls) for cls in sorted(focus_set)],
        "focus_nonfocus_weight": float(focus_mix),
        "n_classes": int(n_classes),
        "n_features": n_features,
        "mean_evidence": float(np.mean(class_evidence)) if class_evidence.size else 0.0,
        "density": float(np.mean(class_evidence > 0.0)) if class_evidence.size else 0.0,
        "mean_lag_support": float(np.mean(lag_support_values)) if lag_support_values else 0.0,
        "nonzero_features_by_class": nonzero_by_class,
        "family_neighbor_count_by_class": family_count_by_class,
        "family_neighbors_by_class": family_neighbors_by_class,
        "train_separation_by_class": {str(cls): float(train_separation_by_class[cls]) for cls in range(int(n_classes))},
        "top_feature_indices_by_class": top_features_by_class,
        "top_edge_indices_by_class": top_edges_by_class,
    }


def compute_train_stable_path_evidence(
    x_train: np.ndarray,
    y_train: np.ndarray,
    feature_group_ids: np.ndarray,
    *,
    n_classes: int,
    split_count: int = 4,
    min_vote_fraction: float = 0.50,
    strength: float = 0.50,
    top_k: int = 0,
    edge_top_k: int = 4,
    mode: str = "static_lag",
    max_lag: int = 3,
    lag_weight: float = 0.50,
    family_k: int = 0,
    family_weight: float = 0.0,
    focus_mode: str = "none",
    focus_classes: Sequence[int] | None = None,
    focus_k: int = 0,
    focus_nonfocus_weight: float = 0.0,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Build train-only path evidence that survives stratified train-subset resampling."""

    x = np.asarray(x_train, dtype=np.float32)
    y = np.asarray(y_train, dtype=np.int64).reshape(-1)
    n_features = int(x.shape[2]) if x.ndim == 3 else 0
    stable_class_evidence = np.zeros((int(n_classes), n_features, n_features), dtype=np.float32)
    if x.ndim != 3 or len(y) != x.shape[0] or n_features == 0:
        return np.zeros((n_features, n_features), dtype=np.float32), {
            "enabled": False,
            "status": "invalid_input",
        }

    splits = max(2, int(split_count))
    fold_ids = np.zeros(len(y), dtype=np.int64)
    for cls in np.unique(y):
        cls_idx = np.where(y == int(cls))[0]
        if len(cls_idx) == 0:
            continue
        fold_ids[cls_idx] = np.arange(len(cls_idx), dtype=np.int64) % splits

    evidence_sum = np.zeros_like(stable_class_evidence)
    vote_count = np.zeros_like(stable_class_evidence)
    class_valid_splits = np.zeros(int(n_classes), dtype=np.float32)
    split_diagnostics: list[dict[str, Any]] = []
    for split_id in range(splits):
        subset_mask = fold_ids != int(split_id)
        if int(np.count_nonzero(subset_mask)) < max(4, int(n_classes) * 2):
            split_diagnostics.append({"split": int(split_id), "used": False, "reason": "too_few_rows"})
            continue
        local_y = y[subset_mask]
        class_valid = np.zeros(int(n_classes), dtype=bool)
        for cls in range(int(n_classes)):
            pos = local_y == int(cls)
            neg = ~pos
            class_valid[cls] = bool(int(pos.sum()) >= 2 and int(neg.sum()) >= 2)
        if not bool(np.any(class_valid)):
            split_diagnostics.append({"split": int(split_id), "used": False, "reason": "no_valid_class"})
            continue
        local_evidence, local_diag = compute_train_class_path_evidence(
            x[subset_mask],
            local_y,
            feature_group_ids,
            n_classes=int(n_classes),
            top_k=int(top_k),
            mode=str(mode or "static_lag"),
            max_lag=int(max_lag),
            lag_weight=float(lag_weight),
            family_k=int(family_k),
            family_weight=float(family_weight),
            focus_mode=str(focus_mode or "none"),
            focus_classes=_parse_optional_ints(focus_classes),
            focus_k=int(focus_k),
            focus_nonfocus_weight=float(focus_nonfocus_weight),
        )
        evidence_sum += local_evidence
        vote_count += (local_evidence > 0.0).astype(np.float32)
        class_valid_splits += class_valid.astype(np.float32)
        split_diagnostics.append(
            {
                "split": int(split_id),
                "used": True,
                "valid_classes": int(np.count_nonzero(class_valid)),
                "density": float(local_diag.get("density", 0.0)),
                "mean_evidence": float(local_diag.get("mean_evidence", 0.0)),
            }
        )

    valid_den = np.maximum(class_valid_splits[:, None, None], 1.0)
    mean_evidence = evidence_sum / valid_den
    vote_fraction = vote_count / valid_den
    min_vote = float(np.clip(min_vote_fraction, 0.0, 1.0))
    stable_mask = vote_fraction >= min_vote
    stable_class_evidence = np.asarray(mean_evidence * vote_fraction * stable_mask, dtype=np.float32)
    diagonal = np.arange(n_features)
    stable_class_evidence[:, diagonal, diagonal] = 0.0
    edge_budget = int(edge_top_k)
    if edge_budget > 0:
        for cls in range(int(n_classes)):
            stable_class_evidence[cls] = _cap_edges_by_endpoint_and_group(
                stable_class_evidence[cls],
                edge_budget,
                feature_group_ids,
                group_top_k=0,
            )
    global_evidence = np.max(stable_class_evidence, axis=0) if stable_class_evidence.size else np.zeros((n_features, n_features), dtype=np.float32)
    if edge_budget > 0:
        global_evidence = _cap_edges_by_endpoint_and_group(
            global_evidence,
            edge_budget,
            feature_group_ids,
            group_top_k=0,
        )
    if float(np.max(global_evidence)) > 0.0:
        global_evidence = np.asarray(global_evidence / float(np.max(global_evidence)), dtype=np.float32)
    evidence_strength = float(np.clip(strength, 0.0, 1.0))
    stable_class_evidence = np.asarray(stable_class_evidence * evidence_strength, dtype=np.float32)
    global_evidence = np.asarray(global_evidence * evidence_strength, dtype=np.float32)
    np.fill_diagonal(global_evidence, 0.0)

    flat = global_evidence.reshape(-1)
    top_edges: list[dict[str, float | int]] = []
    for flat_idx in np.argsort(-flat)[:20]:
        score = float(flat[int(flat_idx)])
        if score <= 0.0:
            continue
        target_idx = int(flat_idx // n_features)
        source_idx = int(flat_idx % n_features)
        if target_idx == source_idx:
            continue
        top_edges.append(
            {
                "target": target_idx,
                "source": source_idx,
                "score": score,
                "vote_fraction": float(np.max(vote_fraction[:, target_idx, source_idx])) if vote_fraction.size else 0.0,
            }
        )

    return global_evidence.astype(np.float32), {
        "enabled": True,
        "source": "train_only_cross_split_stable_path_evidence",
        "split_count": int(splits),
        "used_splits": int(sum(1 for item in split_diagnostics if item.get("used"))),
        "min_vote_fraction": float(min_vote),
        "strength": float(evidence_strength),
        "top_k": int(top_k),
        "edge_top_k": int(edge_budget),
        "mode": str(mode or "static_lag"),
        "max_lag": int(max_lag),
        "lag_weight": float(np.clip(lag_weight, 0.0, 1.0)),
        "family_k": int(family_k),
        "family_weight": float(np.clip(family_weight, 0.0, 1.0)),
        "focus_mode": str(focus_mode or "none"),
        "focus_k": int(focus_k),
        "focus_classes": [int(cls) for cls in _parse_optional_ints(focus_classes)],
        "focus_nonfocus_weight": float(np.clip(focus_nonfocus_weight, 0.0, 1.0)),
        "class_valid_splits": {str(cls): int(class_valid_splits[cls]) for cls in range(int(n_classes))},
        "mean_vote_fraction": float(np.mean(vote_fraction[stable_mask])) if bool(np.any(stable_mask)) else 0.0,
        "density": float(np.mean(global_evidence > 0.0)) if global_evidence.size else 0.0,
        "mean_evidence": float(np.mean(global_evidence)) if global_evidence.size else 0.0,
        "class_density": float(np.mean(stable_class_evidence > 0.0)) if stable_class_evidence.size else 0.0,
        "top_edge_indices": top_edges,
        "split_diagnostics": split_diagnostics,
        "path_evidence_matrix": global_evidence.astype(np.float32),
        "class_path_evidence_matrix": stable_class_evidence.astype(np.float32),
        "class_stability_matrix": vote_fraction.astype(np.float32),
    }


def apply_class_evidence_quality_certificate(
    class_path_evidence: np.ndarray | None,
    stable_class_stability: np.ndarray | None,
    *,
    focus_classes: Sequence[int] | None = None,
    mode: str = "focus_stability",
    floor: float = 0.15,
    threshold: float = 0.75,
    temperature: float = 0.05,
) -> tuple[np.ndarray | None, dict[str, Any]]:
    evidence = None if class_path_evidence is None else np.asarray(class_path_evidence, dtype=np.float32)
    stability = None if stable_class_stability is None else np.asarray(stable_class_stability, dtype=np.float32)
    if evidence is None or evidence.ndim != 3:
        return class_path_evidence, {"enabled": False, "status": "missing_class_path_evidence"}
    if stability is None or tuple(stability.shape) != tuple(evidence.shape):
        return class_path_evidence, {"enabled": False, "status": "missing_stability_matrix"}

    n_classes = int(evidence.shape[0])
    cert_mode = str(mode or "focus_stability").strip().lower()
    if cert_mode not in {"focus_stability", "all_stability"}:
        cert_mode = "focus_stability"
    focus_set = {
        int(cls)
        for cls in _parse_optional_ints(focus_classes)
        if 0 <= int(cls) < n_classes
    }
    certified_classes = set(range(n_classes)) if cert_mode == "all_stability" or not focus_set else set(focus_set)

    cert_floor = float(np.clip(floor, 0.0, 1.0))
    cert_threshold = float(np.clip(threshold, 0.0, 1.0))
    cert_temperature = float(max(1.0e-3, temperature))
    raw_stability = np.nan_to_num(stability, nan=0.0, posinf=0.0, neginf=0.0)
    soft_gate = cert_floor + (1.0 - cert_floor) / (
        1.0 + np.exp(-(raw_stability - cert_threshold) / cert_temperature)
    )
    gate = np.ones_like(evidence, dtype=np.float32)
    for cls in certified_classes:
        gate[int(cls)] = soft_gate[int(cls)]
    filtered = np.asarray(np.clip(evidence * gate, 0.0, 1.0), dtype=np.float32)

    class_gate_mean = {str(cls): float(np.mean(gate[int(cls)])) for cls in range(n_classes)}
    class_retained_mass: dict[str, float] = {}
    for cls in range(n_classes):
        before = float(np.sum(evidence[int(cls)]))
        after = float(np.sum(filtered[int(cls)]))
        class_retained_mass[str(cls)] = float(after / before) if before > 1.0e-8 else 1.0
    return filtered, {
        "enabled": True,
        "source": "train_only_class_evidence_quality_certificate",
        "mode": cert_mode,
        "floor": float(cert_floor),
        "threshold": float(cert_threshold),
        "temperature": float(cert_temperature),
        "focus_classes": [int(cls) for cls in sorted(focus_set)],
        "certified_classes": [int(cls) for cls in sorted(certified_classes)],
        "mean_gate": float(np.mean(gate)),
        "mean_stability": float(np.mean(raw_stability)),
        "input_mean_evidence": float(np.mean(evidence)),
        "output_mean_evidence": float(np.mean(filtered)),
        "input_density": float(np.mean(evidence > 0.0)),
        "output_density": float(np.mean(filtered > 0.0)),
        "class_gate_mean": class_gate_mean,
        "class_retained_mass": class_retained_mass,
    }


def apply_path_family_quality_certificate(
    class_path_evidence: np.ndarray | None,
    path_family_support: np.ndarray | None,
    feature_group_ids: np.ndarray,
    *,
    stable_class_stability: np.ndarray | None = None,
    focus_classes: Sequence[int] | None = None,
    mode: str = "focus_path_family",
    floor: float = 0.15,
    threshold: float = 0.25,
    temperature: float = 0.05,
    direct_weight: float = 1.0,
    group_weight: float = 0.50,
    stability_weight: float = 0.0,
    family_k: int = 0,
    family_weight: float = 0.0,
) -> tuple[np.ndarray | None, dict[str, Any]]:
    evidence = None if class_path_evidence is None else np.asarray(class_path_evidence, dtype=np.float32)
    support = None if path_family_support is None else np.asarray(path_family_support, dtype=np.float32)
    if evidence is None or evidence.ndim != 3:
        return class_path_evidence, {"enabled": False, "status": "missing_class_path_evidence"}
    n_classes, n_features, _n_features_b = evidence.shape
    if support is None:
        return class_path_evidence, {"enabled": False, "status": "missing_path_family_support"}
    if support.ndim == 2 and tuple(support.shape) == (n_features, n_features):
        direct_support_by_class = np.repeat(_normalize_edge_prior(support)[None, :, :], int(n_classes), axis=0)
    elif support.ndim == 3 and tuple(support.shape) == (int(n_classes), n_features, n_features):
        direct_support_by_class = np.stack([_normalize_edge_prior(support[int(cls)]) for cls in range(int(n_classes))], axis=0)
    else:
        return class_path_evidence, {"enabled": False, "status": "invalid_path_family_support_shape"}

    cert_mode = str(mode or "focus_path_family").strip().lower()
    if cert_mode not in {"focus_path_family", "all_path_family", "focus_fault_family", "all_fault_family"}:
        cert_mode = "focus_path_family"
    focus_set = {
        int(cls)
        for cls in _parse_optional_ints(focus_classes)
        if 0 <= int(cls) < int(n_classes)
    }
    certified_classes = (
        set(range(int(n_classes)))
        if cert_mode in {"all_path_family", "all_fault_family"} or not focus_set
        else set(focus_set)
    )

    groups = np.asarray(feature_group_ids, dtype=np.int64)
    if groups.ndim != 1 or int(groups.size) != int(n_features):
        groups = np.arange(n_features, dtype=np.int64)
    unique_groups, group_inverse = np.unique(groups, return_inverse=True)
    n_groups = int(len(unique_groups))
    expanded_group_support_by_class = np.zeros_like(direct_support_by_class, dtype=np.float32)
    for cls in range(int(n_classes)):
        group_pair_support = np.zeros((n_groups, n_groups), dtype=np.float32)
        direct_support = direct_support_by_class[int(cls)]
        for target_idx in range(n_features):
            target_group = int(group_inverse[target_idx])
            for source_idx in range(n_features):
                if target_idx == source_idx:
                    continue
                source_group = int(group_inverse[source_idx])
                group_pair_support[target_group, source_group] = max(
                    float(group_pair_support[target_group, source_group]),
                    float(direct_support[target_idx, source_idx]),
                )
        expanded_group_support_by_class[int(cls)] = group_pair_support[group_inverse[:, None], group_inverse[None, :]]
        np.fill_diagonal(expanded_group_support_by_class[int(cls)], 0.0)

    direct_scale = float(max(0.0, direct_weight))
    group_scale = float(max(0.0, group_weight))
    stability_scale = float(max(0.0, stability_weight))
    family_scale = float(max(0.0, family_weight))
    neighbor_k = max(0, int(family_k))
    family_support = np.zeros_like(evidence, dtype=np.float32)
    family_neighbors_by_class: dict[str, list[dict[str, float | int]]] = {}
    if family_scale > 0.0 and neighbor_k > 0 and int(n_classes) > 1:
        flattened = np.nan_to_num(evidence.reshape(int(n_classes), -1), nan=0.0, posinf=0.0, neginf=0.0)
        norms = np.linalg.norm(flattened, axis=1, keepdims=True) + 1.0e-12
        normalized = flattened / norms
        similarity = normalized @ normalized.T
        similarity = np.nan_to_num(similarity, nan=0.0, posinf=0.0, neginf=0.0)
        np.fill_diagonal(similarity, -1.0)
        for cls in range(int(n_classes)):
            candidates = [
                int(idx)
                for idx in np.argsort(-similarity[int(cls)])
                if idx != int(cls) and float(similarity[int(cls), int(idx)]) > 0.0
            ][:neighbor_k]
            family_neighbors_by_class[str(cls)] = [
                {"class": int(idx), "similarity": float(similarity[int(cls), int(idx)])}
                for idx in candidates
            ]
            if not candidates:
                continue
            weights = np.asarray([max(0.0, float(similarity[int(cls), idx])) for idx in candidates], dtype=np.float32)
            if float(np.sum(weights)) <= 1.0e-8:
                weights = np.ones(len(candidates), dtype=np.float32)
            weights = weights / float(np.sum(weights))
            for idx, weight in zip(candidates, weights):
                family_support[int(cls)] += float(weight) * evidence[int(idx)]
        family_support = np.asarray(np.clip(family_support, 0.0, 1.0), dtype=np.float32)
    else:
        for cls in range(int(n_classes)):
            family_neighbors_by_class[str(cls)] = []

    path_family_support_by_class = np.maximum(
        np.clip(direct_scale * direct_support_by_class, 0.0, 1.0),
        np.clip(group_scale * expanded_group_support_by_class, 0.0, 1.0),
    ).astype(np.float32)
    if cert_mode in {"focus_fault_family", "all_fault_family"} and family_scale > 0.0:
        path_family_support_by_class = np.maximum(
            path_family_support_by_class,
            np.clip(family_scale * family_support, 0.0, 1.0),
        ).astype(np.float32)
    stability = None if stable_class_stability is None else np.asarray(stable_class_stability, dtype=np.float32)
    has_stability = stability is not None and tuple(stability.shape) == tuple(evidence.shape) and stability_scale > 0.0

    cert_floor = float(np.clip(floor, 0.0, 1.0))
    cert_threshold = float(np.clip(threshold, 0.0, 1.0))
    cert_temperature = float(max(1.0e-3, temperature))
    gate = np.ones_like(evidence, dtype=np.float32)
    support_by_class: dict[str, float] = {}
    for cls in range(int(n_classes)):
        class_support = path_family_support_by_class[int(cls)]
        if has_stability:
            assert stability is not None
            class_support = np.maximum(
                class_support,
                np.clip(stability_scale * np.nan_to_num(stability[cls], nan=0.0, posinf=0.0, neginf=0.0), 0.0, 1.0),
            )
        support_by_class[str(cls)] = float(np.mean(class_support))
        if int(cls) not in certified_classes:
            continue
        gate[int(cls)] = cert_floor + (1.0 - cert_floor) / (
            1.0 + np.exp(-(class_support - cert_threshold) / cert_temperature)
        )
    filtered = np.asarray(np.clip(evidence * gate, 0.0, 1.0), dtype=np.float32)

    class_retained_mass: dict[str, float] = {}
    class_active_gate_mean: dict[str, float] = {}
    class_protection_risk: dict[str, float] = {}
    raw_protection = np.zeros(int(n_classes), dtype=np.float32)
    for cls in range(int(n_classes)):
        before = float(np.sum(evidence[int(cls)]))
        after = float(np.sum(filtered[int(cls)]))
        retained = float(after / before) if before > 1.0e-8 else 1.0
        active_mask = evidence[int(cls)] > 1.0e-8
        active_gate = float(np.mean(gate[int(cls)][active_mask])) if np.any(active_mask) else 1.0
        risk = float(np.clip(1.0 - min(retained, active_gate), 0.0, 1.0))
        if int(cls) not in certified_classes:
            risk = 0.0
        class_retained_mass[str(cls)] = retained
        class_active_gate_mean[str(cls)] = active_gate
        class_protection_risk[str(cls)] = risk
        raw_protection[int(cls)] = risk
    max_protection = float(np.max(raw_protection)) if raw_protection.size else 0.0
    if max_protection > 1.0e-8:
        class_proposal_protection_weight = raw_protection / max_protection
    else:
        class_proposal_protection_weight = raw_protection
    return filtered, {
        "enabled": True,
        "source": "train_only_path_family_quality_certificate",
        "mode": cert_mode,
        "floor": float(cert_floor),
        "threshold": float(cert_threshold),
        "temperature": float(cert_temperature),
        "direct_weight": float(direct_scale),
        "group_weight": float(group_scale),
        "stability_weight": float(stability_scale),
        "family_k": int(neighbor_k),
        "family_weight": float(family_scale),
        "focus_classes": [int(cls) for cls in sorted(focus_set)],
        "certified_classes": [int(cls) for cls in sorted(certified_classes)],
        "mean_gate": float(np.mean(gate)),
        "mean_direct_support": float(np.mean(direct_support_by_class)),
        "mean_group_support": float(np.mean(expanded_group_support_by_class)),
        "mean_family_support": float(np.mean(family_support)),
        "mean_global_support": float(np.mean(path_family_support_by_class)),
        "input_mean_evidence": float(np.mean(evidence)),
        "output_mean_evidence": float(np.mean(filtered)),
        "input_density": float(np.mean(evidence > 0.0)),
        "output_density": float(np.mean(filtered > 0.0)),
        "class_support_mean": support_by_class,
        "class_active_gate_mean": class_active_gate_mean,
        "class_protection_risk": class_protection_risk,
        "class_proposal_protection_weight": [
            float(value) for value in np.asarray(class_proposal_protection_weight, dtype=np.float32).reshape(-1)
        ],
        "family_neighbors_by_class": family_neighbors_by_class,
        "class_retained_mass": class_retained_mass,
    }


def apply_stable_class_edge_overlay(
    prior_adjacency: np.ndarray | None,
    stable_path_evidence: np.ndarray | None,
    stable_class_path_evidence: np.ndarray | None,
    feature_group_ids: np.ndarray,
    *,
    focus_classes: Sequence[int] | None = None,
    scale: float = 0.25,
    top_k: int = 8,
    group_top_k: int = 2,
    focus_weight: float = 1.25,
    nonfocus_weight: float = 0.50,
    mode: str = "max",
) -> tuple[np.ndarray | None, dict[str, Any]]:
    prior = None if prior_adjacency is None else np.asarray(prior_adjacency, dtype=np.float32)
    if prior is None or prior.ndim != 2 or prior.shape[0] != prior.shape[1] or prior.size == 0:
        return prior_adjacency, {"enabled": False, "status": "missing_prior_adjacency"}
    n_features = int(prior.shape[0])

    overlay_sources: list[np.ndarray] = []
    global_evidence = None if stable_path_evidence is None else np.asarray(stable_path_evidence, dtype=np.float32)
    if global_evidence is not None and tuple(global_evidence.shape) == (n_features, n_features):
        global_overlay = _normalize_edge_prior(np.nan_to_num(global_evidence, nan=0.0, posinf=0.0, neginf=0.0))
        if float(np.max(global_overlay)) > 0.0:
            overlay_sources.append(global_overlay)

    class_evidence = None if stable_class_path_evidence is None else np.asarray(stable_class_path_evidence, dtype=np.float32)
    n_classes = int(class_evidence.shape[0]) if class_evidence is not None and class_evidence.ndim == 3 else 0
    focus_set = {
        int(cls)
        for cls in _parse_optional_ints(focus_classes)
        if 0 <= int(cls) < max(0, n_classes)
    }
    if class_evidence is not None and tuple(class_evidence.shape[1:]) == (n_features, n_features):
        class_overlay = np.zeros((n_features, n_features), dtype=np.float32)
        for cls in range(n_classes):
            if focus_set:
                class_scale = float(focus_weight) if int(cls) in focus_set else float(nonfocus_weight)
            else:
                class_scale = 1.0
            if class_scale <= 0.0:
                continue
            cls_matrix = np.nan_to_num(class_evidence[int(cls)], nan=0.0, posinf=0.0, neginf=0.0)
            class_overlay = np.maximum(class_overlay, np.clip(class_scale * cls_matrix, 0.0, 1.0)).astype(np.float32)
        class_overlay = _normalize_edge_prior(class_overlay)
        if float(np.max(class_overlay)) > 0.0:
            overlay_sources.append(class_overlay)

    if not overlay_sources:
        return prior_adjacency, {
            "enabled": False,
            "status": "empty_stable_class_overlay",
            "input_edges": int(np.count_nonzero(prior > 0.0)),
        }

    overlay = np.maximum.reduce(overlay_sources).astype(np.float32)
    groups = np.asarray(feature_group_ids, dtype=np.int64).reshape(-1)
    if int(groups.size) != n_features:
        groups = np.arange(n_features, dtype=np.int64)
    overlay = _cap_edges_by_endpoint_and_group(
        overlay,
        int(top_k),
        groups,
        group_top_k=int(group_top_k),
    )
    overlay = _normalize_edge_prior(overlay)
    overlay_scale = float(np.clip(scale, 0.0, 1.0))
    overlay_scaled = np.asarray(overlay_scale * overlay, dtype=np.float32)

    combine_mode = str(mode or "max").strip().lower()
    if combine_mode not in {"max", "add"}:
        combine_mode = "max"
    if combine_mode == "add":
        merged = np.clip(prior + overlay_scaled, 0.0, 1.0).astype(np.float32)
    else:
        merged = np.maximum(prior, overlay_scaled).astype(np.float32)
    np.fill_diagonal(merged, 0.0)

    prior_mask = prior > 0.0
    overlay_mask = overlay > 0.0
    new_mask = overlay_mask & ~prior_mask
    return merged, {
        "enabled": True,
        "source": "train_only_stable_class_edge_overlay",
        "status": "ok",
        "mode": combine_mode,
        "scale": float(overlay_scale),
        "top_k": int(top_k),
        "group_top_k": int(group_top_k),
        "focus_weight": float(max(0.0, focus_weight)),
        "nonfocus_weight": float(max(0.0, nonfocus_weight)),
        "focus_classes": [int(cls) for cls in sorted(focus_set)],
        "input_edges": int(np.count_nonzero(prior_mask)),
        "overlay_edges": int(np.count_nonzero(overlay_mask)),
        "new_edges": int(np.count_nonzero(new_mask)),
        "overlap_edges": int(np.count_nonzero(overlay_mask & prior_mask)),
        "output_edges": int(np.count_nonzero(merged > 0.0)),
        "mean_overlay": float(np.mean(overlay[overlay_mask])) if bool(np.any(overlay_mask)) else 0.0,
        "mean_prior": float(np.mean(prior[prior_mask])) if bool(np.any(prior_mask)) else 0.0,
        "top_edge_indices": _top_edge_records(overlay, limit=20),
    }


def apply_graph_prior_core_certificate(
    prior_adjacency: np.ndarray | None,
    class_path_evidence: np.ndarray | None,
    feature_group_ids: np.ndarray,
    *,
    stable_class_stability: np.ndarray | None = None,
    focus_classes: Sequence[int] | None = None,
    floor: float = 0.05,
    threshold: float = 0.35,
    temperature: float = 0.05,
    top_k: int = 8,
    group_top_k: int = 3,
    direct_weight: float = 1.0,
    group_weight: float = 0.40,
    stability_weight: float = 0.50,
    prior_weight: float = 0.20,
    focus_weight: float = 1.25,
    nonfocus_weight: float = 0.50,
) -> tuple[np.ndarray | None, dict[str, Any]]:
    prior = None if prior_adjacency is None else _normalize_edge_prior(np.asarray(prior_adjacency, dtype=np.float32))
    if prior is None or prior.ndim != 2 or prior.shape[0] != prior.shape[1] or prior.size == 0:
        return prior_adjacency, {"enabled": False, "status": "missing_prior_adjacency"}
    n_features = int(prior.shape[0])
    input_edges = int(np.count_nonzero(prior > 0.0))
    if input_edges <= 0:
        return prior_adjacency, {"enabled": False, "status": "empty_prior_adjacency", "input_edges": 0}

    groups = np.asarray(feature_group_ids, dtype=np.int64).reshape(-1)
    if int(groups.size) != n_features:
        groups = np.arange(n_features, dtype=np.int64)
    evidence = None if class_path_evidence is None else np.asarray(class_path_evidence, dtype=np.float32)
    stability = None if stable_class_stability is None else np.asarray(stable_class_stability, dtype=np.float32)
    n_classes = int(evidence.shape[0]) if evidence is not None and evidence.ndim == 3 else 0
    focus_set = {
        int(cls)
        for cls in _parse_optional_ints(focus_classes)
        if 0 <= int(cls) < max(0, n_classes)
    }

    direct_support = np.zeros_like(prior, dtype=np.float32)
    if evidence is not None and evidence.ndim == 3 and tuple(evidence.shape[1:]) == (n_features, n_features):
        raw_evidence = np.nan_to_num(evidence, nan=0.0, posinf=0.0, neginf=0.0)
        for cls in range(int(raw_evidence.shape[0])):
            class_scale = float(focus_weight) if focus_set and int(cls) in focus_set else float(nonfocus_weight if focus_set else 1.0)
            if class_scale <= 0.0:
                continue
            direct_support = np.maximum(
                direct_support,
                np.clip(float(direct_weight) * class_scale * raw_evidence[int(cls)], 0.0, 1.0),
            ).astype(np.float32)

    unique_groups, group_inverse = np.unique(groups, return_inverse=True)
    n_groups = int(len(unique_groups))
    group_pair_support = np.zeros((n_groups, n_groups), dtype=np.float32)
    for target_idx in range(n_features):
        target_group = int(group_inverse[target_idx])
        for source_idx in range(n_features):
            if target_idx == source_idx:
                continue
            source_group = int(group_inverse[source_idx])
            group_pair_support[target_group, source_group] = max(
                float(group_pair_support[target_group, source_group]),
                float(direct_support[target_idx, source_idx]),
            )
    expanded_group_support = group_pair_support[group_inverse[:, None], group_inverse[None, :]]
    np.fill_diagonal(expanded_group_support, 0.0)

    stability_support = np.zeros_like(prior, dtype=np.float32)
    if stability is not None and stability.ndim == 3 and tuple(stability.shape[1:]) == (n_features, n_features):
        raw_stability = np.nan_to_num(stability, nan=0.0, posinf=0.0, neginf=0.0)
        for cls in range(int(raw_stability.shape[0])):
            class_scale = float(focus_weight) if focus_set and int(cls) in focus_set else float(nonfocus_weight if focus_set else 1.0)
            if class_scale <= 0.0:
                continue
            stability_support = np.maximum(
                stability_support,
                np.clip(class_scale * raw_stability[int(cls)], 0.0, 1.0),
            ).astype(np.float32)

    support = np.maximum.reduce(
        [
            np.clip(direct_support, 0.0, 1.0),
            np.clip(float(group_weight) * expanded_group_support, 0.0, 1.0),
            np.clip(float(stability_weight) * stability_support, 0.0, 1.0),
            np.clip(float(prior_weight) * prior, 0.0, 1.0),
        ]
    ).astype(np.float32)
    cert_floor = float(np.clip(floor, 0.0, 1.0))
    cert_threshold = float(np.clip(threshold, 0.0, 1.0))
    cert_temperature = float(max(1.0e-3, temperature))
    gate = cert_floor + (1.0 - cert_floor) / (1.0 + np.exp(-(support - cert_threshold) / cert_temperature))
    raw_core = np.asarray(prior * gate, dtype=np.float32)
    if float(np.max(support)) >= cert_threshold:
        supported_mask = support >= max(0.0, cert_threshold)
        soft_mask = support >= max(cert_floor, cert_threshold * 0.5)
        raw_core = np.where(supported_mask, raw_core, np.where(soft_mask, raw_core * 0.5, 0.0)).astype(np.float32)
    core = _cap_edges_by_endpoint_and_group(
        raw_core,
        int(top_k),
        groups,
        group_top_k=int(group_top_k),
    )
    if int(np.count_nonzero(core > 0.0)) == 0:
        core = _cap_edges_by_endpoint_and_group(prior, int(top_k), groups, group_top_k=int(group_top_k))
        status = "fallback_to_ranked_prior"
    else:
        status = "ok"

    output_edges = int(np.count_nonzero(core > 0.0))
    input_mass = float(np.sum(prior))
    output_mass = float(np.sum(core))
    return core.astype(np.float32), {
        "enabled": True,
        "source": "train_only_graph_prior_core_certificate",
        "status": status,
        "floor": float(cert_floor),
        "threshold": float(cert_threshold),
        "temperature": float(cert_temperature),
        "top_k": int(top_k),
        "group_top_k": int(group_top_k),
        "direct_weight": float(max(0.0, direct_weight)),
        "group_weight": float(max(0.0, group_weight)),
        "stability_weight": float(max(0.0, stability_weight)),
        "prior_weight": float(max(0.0, prior_weight)),
        "focus_weight": float(max(0.0, focus_weight)),
        "nonfocus_weight": float(max(0.0, nonfocus_weight)),
        "focus_classes": [int(cls) for cls in sorted(focus_set)],
        "input_edges": int(input_edges),
        "output_edges": int(output_edges),
        "compression_ratio": float(output_edges / max(1, input_edges)),
        "input_mass": float(input_mass),
        "output_mass": float(output_mass),
        "retained_mass": float(output_mass / input_mass) if input_mass > 1.0e-8 else 0.0,
        "mean_gate": float(np.mean(gate)),
        "mean_support": float(np.mean(support)),
        "mean_direct_support": float(np.mean(direct_support)),
        "mean_group_support": float(np.mean(expanded_group_support)),
        "mean_stability_support": float(np.mean(stability_support)),
        "mean_prior_support": float(np.mean(prior)),
        "supported_edges": int(np.count_nonzero(support >= cert_threshold)),
        "top_edge_indices": _top_edge_records(core, limit=20),
    }


def _safe_abs_corr_matrix(source: np.ndarray, target: np.ndarray) -> np.ndarray:
    left = np.asarray(source, dtype=np.float64)
    right = np.asarray(target, dtype=np.float64)
    if left.ndim != 2 or right.ndim != 2 or left.shape[0] != right.shape[0] or left.shape[0] < 3:
        return np.zeros((right.shape[1] if right.ndim == 2 else 0, left.shape[1] if left.ndim == 2 else 0), dtype=np.float32)
    left = np.nan_to_num(left, nan=0.0, posinf=0.0, neginf=0.0)
    right = np.nan_to_num(right, nan=0.0, posinf=0.0, neginf=0.0)
    left = left - np.mean(left, axis=0, keepdims=True)
    right = right - np.mean(right, axis=0, keepdims=True)
    denom = np.sqrt(np.sum(right * right, axis=0, keepdims=True).T @ np.sum(left * left, axis=0, keepdims=True))
    numer = right.T @ left
    corr = np.divide(numer, denom, out=np.zeros_like(numer), where=denom > 1.0e-12)
    return np.asarray(np.clip(np.abs(corr), 0.0, 1.0), dtype=np.float32)


def _window_slope_descriptor(x: np.ndarray) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float32)
    if arr.ndim != 3 or arr.shape[1] < 2:
        return np.zeros((arr.shape[0] if arr.ndim >= 1 else 0, arr.shape[2] if arr.ndim == 3 else 0), dtype=np.float32)
    time = np.linspace(-1.0, 1.0, int(arr.shape[1]), dtype=np.float32)
    denom = float(np.sum(time * time))
    if denom <= 1.0e-12:
        return np.zeros((arr.shape[0], arr.shape[2]), dtype=np.float32)
    centered = arr - np.mean(arr, axis=1, keepdims=True)
    return np.asarray(np.einsum("ntf,t->nf", centered, time, optimize=True) / denom, dtype=np.float32)


def _descriptor_edge_matrix(x: np.ndarray, *, extended: bool = False) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float32)
    n_features = int(arr.shape[2]) if arr.ndim == 3 else 0
    if arr.ndim != 3 or arr.shape[0] < 3 or n_features < 2:
        return np.zeros((n_features, n_features), dtype=np.float32)
    descriptors = [
        arr[:, -1, :],
        np.mean(arr, axis=1),
        arr[:, -1, :] - arr[:, 0, :],
    ]
    if extended:
        descriptors.extend(
            [
                np.std(arr, axis=1),
                _window_slope_descriptor(arr),
            ]
        )
    component = np.zeros((n_features, n_features), dtype=np.float32)
    for descriptor in descriptors:
        component = np.maximum(component, _safe_abs_corr_matrix(descriptor, descriptor))
    return _normalize_edge_prior(component)


def _lagged_dependency_edge_matrix(x: np.ndarray, *, max_lag: int) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float32)
    n_features = int(arr.shape[2]) if arr.ndim == 3 else 0
    lag_limit = max(0, min(int(max_lag), int(arr.shape[1]) - 1)) if arr.ndim == 3 else 0
    component = np.zeros((n_features, n_features), dtype=np.float32)
    if arr.ndim != 3 or arr.shape[0] < 2 or n_features < 2 or lag_limit <= 0:
        return component
    for lag in range(1, lag_limit + 1):
        source = arr[:, :-lag, :].reshape(-1, n_features)
        target = arr[:, lag:, :].reshape(-1, n_features)
        component = np.maximum(component, _safe_abs_corr_matrix(source, target))
        target_delta = (arr[:, lag:, :] - arr[:, :-lag, :]).reshape(-1, n_features)
        component = np.maximum(component, _safe_abs_corr_matrix(source, target_delta))
    return _normalize_edge_prior(component)


def _directed_lag_asymmetry_edge_matrix(x: np.ndarray, *, max_lag: int) -> np.ndarray:
    base = _lagged_dependency_edge_matrix(x, max_lag=max_lag)
    if base.ndim != 2 or base.shape[0] != base.shape[1] or base.size == 0:
        return base
    reverse = base.T
    asymmetry = np.divide(
        base - reverse,
        base + reverse + 1.0e-6,
        out=np.zeros_like(base, dtype=np.float32),
        where=(base + reverse) > 1.0e-6,
    )
    directed = base * (0.50 + 0.50 * np.clip(asymmetry, 0.0, 1.0))
    return _normalize_edge_prior(directed)


def _innovation_dependency_edge_matrix(x: np.ndarray, *, max_lag: int) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float32)
    n_features = int(arr.shape[2]) if arr.ndim == 3 else 0
    if arr.ndim != 3 or arr.shape[0] < 2 or arr.shape[1] < 3 or n_features < 2:
        return np.zeros((n_features, n_features), dtype=np.float32)
    delta = arr[:, 1:, :] - arr[:, :-1, :]
    lag_limit = max(0, min(int(max_lag), int(delta.shape[1]) - 1))
    component = np.zeros((n_features, n_features), dtype=np.float32)
    for lag in range(0, lag_limit + 1):
        if lag == 0:
            source_delta = delta.reshape(-1, n_features)
            target_delta = delta.reshape(-1, n_features)
        else:
            source_delta = delta[:, :-lag, :].reshape(-1, n_features)
            target_delta = delta[:, lag:, :].reshape(-1, n_features)
        component = np.maximum(component, _safe_abs_corr_matrix(source_delta, target_delta))
        component = np.maximum(component, 0.50 * _safe_abs_corr_matrix(np.abs(source_delta), np.abs(target_delta)))
    return _normalize_edge_prior(component)


def _class_lag_dependency_edge_matrix(
    x: np.ndarray,
    y: np.ndarray,
    *,
    max_lag: int,
    n_classes: int | None = None,
) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float32)
    labels = np.asarray(y, dtype=np.int64).reshape(-1)
    n_features = int(arr.shape[2]) if arr.ndim == 3 else 0
    if arr.ndim != 3 or arr.shape[0] < 4 or n_features < 2 or len(labels) != arr.shape[0]:
        return np.zeros((n_features, n_features), dtype=np.float32)
    class_limit = int(n_classes) if n_classes is not None else (int(np.max(labels)) + 1 if len(labels) else 0)
    component = np.zeros((n_features, n_features), dtype=np.float32)
    total = max(1, int(arr.shape[0]))
    for cls in range(class_limit):
        mask = labels == int(cls)
        count = int(np.count_nonzero(mask))
        if count < 3:
            continue
        class_component = _lagged_dependency_edge_matrix(arr[mask], max_lag=max_lag)
        if float(np.max(class_component)) <= 0.0:
            continue
        support = min(1.0, math.sqrt(float(count) / float(total)))
        component = np.maximum(component, float(support) * class_component)
    return _normalize_edge_prior(component)


def _partial_residual_edge_matrix(values: np.ndarray, *, ridge: float = 0.05) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64)
    n_features = int(arr.shape[1]) if arr.ndim == 2 else 0
    if arr.ndim != 2 or arr.shape[0] < 4 or n_features < 2:
        return np.zeros((n_features, n_features), dtype=np.float32)
    arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
    arr = arr - np.mean(arr, axis=0, keepdims=True)
    std = np.std(arr, axis=0, keepdims=True)
    arr = np.divide(arr, std, out=np.zeros_like(arr), where=std > 1.0e-12)
    corr = (arr.T @ arr) / max(1, int(arr.shape[0]) - 1)
    corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
    corr = 0.5 * (corr + corr.T)
    try:
        precision = np.linalg.pinv(corr + float(max(ridge, 1.0e-6)) * np.eye(n_features, dtype=np.float64))
    except np.linalg.LinAlgError:
        return np.zeros((n_features, n_features), dtype=np.float32)
    diag = np.maximum(np.diag(precision), 1.0e-12)
    denom = np.sqrt(np.outer(diag, diag))
    partial = np.divide(-precision, denom, out=np.zeros_like(precision), where=denom > 1.0e-12)
    partial = np.abs(partial)
    np.fill_diagonal(partial, 0.0)
    return _normalize_edge_prior(partial)


def _fault_response_edge_matrix(x: np.ndarray, y: np.ndarray, *, n_classes: int | None = None) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float32)
    labels = np.asarray(y, dtype=np.int64).reshape(-1)
    n_features = int(arr.shape[2]) if arr.ndim == 3 else 0
    if arr.ndim != 3 or arr.shape[0] < 4 or n_features < 2 or len(labels) != arr.shape[0]:
        return np.zeros((n_features, n_features), dtype=np.float32)
    unique, counts = np.unique(labels, return_counts=True)
    if unique.size < 2:
        return np.zeros((n_features, n_features), dtype=np.float32)
    baseline = 0 if np.any(unique == 0) else int(unique[int(np.argmax(counts))])
    baseline_mask = labels == baseline
    if int(np.count_nonzero(baseline_mask)) < 2:
        return np.zeros((n_features, n_features), dtype=np.float32)
    baseline_profile = np.mean(arr[baseline_mask], axis=0)
    component = np.zeros((n_features, n_features), dtype=np.float32)
    class_limit = int(n_classes) if n_classes is not None else int(np.max(labels)) + 1
    for cls in range(class_limit):
        if cls == baseline:
            continue
        class_mask = labels == int(cls)
        if int(np.count_nonzero(class_mask)) < 2:
            continue
        profile = np.mean(arr[class_mask], axis=0) - baseline_profile
        response = np.abs(profile)
        if profile.shape[0] > 1:
            trend = np.zeros_like(response, dtype=np.float32)
            trend[1:, :] = np.abs(profile[1:, :] - profile[:-1, :])
            signal = response + 0.5 * trend
        else:
            signal = response
        amplitude = np.max(signal, axis=0)
        max_amp = float(np.max(amplitude)) if amplitude.size else 0.0
        if max_amp <= 1.0e-12:
            continue
        amplitude = np.asarray(amplitude / max_amp, dtype=np.float32)
        peak = np.argmax(signal, axis=0).astype(np.int64)
        source_peak = peak.reshape(1, -1)
        target_peak = peak.reshape(-1, 1)
        lag = target_peak - source_peak
        order = np.empty_like(lag, dtype=np.float32)
        forward = lag >= 0
        order[forward] = 1.0 / (1.0 + lag[forward].astype(np.float32))
        order[~forward] = 0.25 / (1.0 + np.abs(lag[~forward]).astype(np.float32))
        local = amplitude.reshape(-1, 1) * amplitude.reshape(1, -1) * order.astype(np.float32)
        component = np.maximum(component, local.astype(np.float32))
    return _normalize_edge_prior(component)


def _stable_edge_vote_matrix(
    x: np.ndarray,
    y: np.ndarray,
    *,
    max_lag: int,
    top_k: int,
    n_classes: int | None = None,
) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float32)
    labels = np.asarray(y, dtype=np.int64).reshape(-1)
    n_features = int(arr.shape[2]) if arr.ndim == 3 else 0
    if arr.ndim != 3 or arr.shape[0] < 8 or n_features < 2 or len(labels) != arr.shape[0]:
        return np.zeros((n_features, n_features), dtype=np.float32)
    split_count = min(4, max(2, int(arr.shape[0]) // 4))
    vote = np.zeros((n_features, n_features), dtype=np.float32)
    weighted = np.zeros((n_features, n_features), dtype=np.float32)
    max_edges = min(n_features * (n_features - 1), n_features * max(4, int(top_k) if int(top_k) > 0 else 8))
    row_ids = np.arange(arr.shape[0])
    for split_idx in range(split_count):
        mask = (row_ids % split_count) != split_idx
        if int(np.count_nonzero(mask)) < 4:
            continue
        desc = _descriptor_edge_matrix(arr[mask], extended=True)
        lag = _lagged_dependency_edge_matrix(arr[mask], max_lag=max_lag)
        response = _fault_response_edge_matrix(arr[mask], labels[mask], n_classes=n_classes)
        component = _normalize_edge_prior(0.35 * desc + 0.45 * lag + 0.20 * response)
        if float(np.max(component)) <= 0.0:
            continue
        keep = np.zeros_like(component, dtype=bool)
        flat = component.reshape(-1)
        kept = 0
        for flat_idx in np.argsort(-flat):
            score = float(flat[int(flat_idx)])
            if score <= 0.0:
                break
            target_idx = int(flat_idx // n_features)
            source_idx = int(flat_idx % n_features)
            if target_idx == source_idx:
                continue
            keep[target_idx, source_idx] = True
            kept += 1
            if kept >= max_edges:
                break
        vote += keep.astype(np.float32)
        weighted += np.where(keep, component, 0.0).astype(np.float32)
    if float(np.max(vote)) <= 0.0:
        return np.zeros((n_features, n_features), dtype=np.float32)
    stability = (vote / float(split_count)) * weighted
    return _normalize_edge_prior(stability)


def _class_lag_support_matrix(x_class: np.ndarray, node_salience: np.ndarray, max_lag: int) -> np.ndarray:
    x = np.asarray(x_class, dtype=np.float32)
    node = np.asarray(node_salience, dtype=np.float32).reshape(-1)
    n_features = int(x.shape[2]) if x.ndim == 3 else int(node.shape[0])
    support = np.zeros((n_features, n_features), dtype=np.float32)
    if x.ndim != 3 or x.shape[0] < 2 or x.shape[1] < 2 or x.shape[2] != n_features:
        return support
    active = np.flatnonzero(node > 0.0)
    if active.size < 2:
        return support
    local_support = np.zeros((int(active.size), int(active.size)), dtype=np.float32)
    lag_limit = max(1, min(int(max_lag), int(x.shape[1]) - 1))
    for lag in range(1, lag_limit + 1):
        source = x[:, :-lag, active].reshape(-1, int(active.size))
        target = x[:, lag:, active].reshape(-1, int(active.size))
        local_support = np.maximum(local_support, _safe_abs_corr_matrix(source, target))
        target_delta = (x[:, lag:, active] - x[:, :-lag, active]).reshape(-1, int(active.size))
        local_support = np.maximum(local_support, _safe_abs_corr_matrix(source, target_delta))
    np.fill_diagonal(local_support, 0.0)
    if float(np.max(local_support)) > 0.0:
        local_support = local_support / float(np.max(local_support))
    support[np.ix_(active, active)] = local_support
    return np.asarray(np.clip(support, 0.0, 1.0), dtype=np.float32)


def _normalize_edge_prior(matrix: np.ndarray) -> np.ndarray:
    arr = np.asarray(matrix, dtype=np.float32)
    if arr.ndim != 2:
        return np.zeros((0, 0), dtype=np.float32)
    arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
    arr = np.maximum(arr, 0.0)
    if arr.shape[0] == arr.shape[1]:
        np.fill_diagonal(arr, 0.0)
    max_value = float(np.max(arr)) if arr.size else 0.0
    if max_value > 1.0e-12:
        arr = arr / max_value
    return np.asarray(np.clip(arr, 0.0, 1.0), dtype=np.float32)


def _cap_edges_by_endpoint(matrix: np.ndarray, top_k: int) -> np.ndarray:
    arr = _normalize_edge_prior(matrix)
    if arr.ndim != 2 or arr.shape[0] != arr.shape[1] or arr.size == 0:
        return arr
    k = int(top_k)
    n_features = int(arr.shape[0])
    if k <= 0 or k >= n_features - 1:
        return arr
    capped = np.zeros_like(arr, dtype=np.float32)
    target_counts = np.zeros(n_features, dtype=np.int64)
    source_counts = np.zeros(n_features, dtype=np.int64)
    for flat_idx in np.argsort(-arr.reshape(-1)):
        score = float(arr.reshape(-1)[int(flat_idx)])
        if score <= 0.0:
            break
        target_idx = int(flat_idx // n_features)
        source_idx = int(flat_idx % n_features)
        if target_idx == source_idx:
            continue
        if int(target_counts[target_idx]) >= k or int(source_counts[source_idx]) >= k:
            continue
        capped[target_idx, source_idx] = score
        target_counts[target_idx] += 1
        source_counts[source_idx] += 1
    return capped


def _cap_edges_by_endpoint_and_group(
    matrix: np.ndarray,
    top_k: int,
    feature_group_ids: np.ndarray,
    *,
    group_top_k: int = 0,
) -> np.ndarray:
    arr = _normalize_edge_prior(matrix)
    if arr.ndim != 2 or arr.shape[0] != arr.shape[1] or arr.size == 0:
        return arr
    if int(group_top_k) <= 0:
        return _cap_edges_by_endpoint(arr, int(top_k))
    n_features = int(arr.shape[0])
    groups = np.asarray(feature_group_ids, dtype=np.int64).reshape(-1)
    if len(groups) != n_features:
        groups = np.arange(n_features, dtype=np.int64)
    feature_k = int(top_k)
    group_k = int(group_top_k)
    capped = np.zeros_like(arr, dtype=np.float32)
    target_counts = np.zeros(n_features, dtype=np.int64)
    source_counts = np.zeros(n_features, dtype=np.int64)
    incoming_groups: dict[int, set[int]] = {}
    outgoing_groups: dict[int, set[int]] = {}
    flat = arr.reshape(-1)
    for flat_idx in np.argsort(-flat):
        score = float(flat[int(flat_idx)])
        if score <= 0.0:
            break
        target_idx = int(flat_idx // n_features)
        source_idx = int(flat_idx % n_features)
        if target_idx == source_idx:
            continue
        if feature_k > 0 and (int(target_counts[target_idx]) >= feature_k or int(source_counts[source_idx]) >= feature_k):
            continue
        target_group = int(groups[target_idx])
        source_group = int(groups[source_idx])
        target_sources = incoming_groups.setdefault(target_group, set())
        source_targets = outgoing_groups.setdefault(source_group, set())
        if source_group not in target_sources and len(target_sources) >= group_k:
            continue
        if target_group not in source_targets and len(source_targets) >= group_k:
            continue
        capped[target_idx, source_idx] = score
        target_counts[target_idx] += 1
        source_counts[source_idx] += 1
        target_sources.add(source_group)
        source_targets.add(target_group)
    return capped


def _cap_edges_by_global_budget(matrix: np.ndarray, max_edges: int) -> np.ndarray:
    arr = _normalize_edge_prior(matrix)
    if arr.ndim != 2 or arr.shape[0] != arr.shape[1] or arr.size == 0:
        return arr
    budget = int(max_edges)
    if budget <= 0 or int(np.count_nonzero(arr > 0.0)) <= budget:
        return arr
    capped = np.zeros_like(arr, dtype=np.float32)
    n_features = int(arr.shape[0])
    kept = 0
    flat = arr.reshape(-1)
    for flat_idx in np.argsort(-flat):
        score = float(flat[int(flat_idx)])
        if score <= 0.0:
            break
        target_idx = int(flat_idx // n_features)
        source_idx = int(flat_idx % n_features)
        if target_idx == source_idx:
            continue
        capped[target_idx, source_idx] = score
        kept += 1
        if kept >= budget:
            break
    return capped


def _top_edge_records(matrix: np.ndarray, *, limit: int = 20) -> list[dict[str, float | int]]:
    arr = np.asarray(matrix, dtype=np.float32)
    if arr.ndim != 2 or arr.shape[0] != arr.shape[1] or arr.size == 0:
        return []
    n_features = int(arr.shape[0])
    records: list[dict[str, float | int]] = []
    for flat_idx in np.argsort(-arr.reshape(-1))[: max(0, int(limit)) * 4 + 1]:
        score = float(arr.reshape(-1)[int(flat_idx)])
        if score <= 0.0:
            break
        target_idx = int(flat_idx // n_features)
        source_idx = int(flat_idx % n_features)
        if target_idx == source_idx:
            continue
        records.append({"target": target_idx, "source": source_idx, "score": score})
        if len(records) >= int(limit):
            break
    return records


def _top_edge_bank_records(
    matrix: np.ndarray,
    vote_count: np.ndarray,
    selected_masks: Mapping[str, np.ndarray],
    *,
    limit: int = 20,
) -> list[dict[str, Any]]:
    arr = np.asarray(matrix, dtype=np.float32)
    votes = np.asarray(vote_count, dtype=np.float32)
    if arr.ndim != 2 or arr.shape[0] != arr.shape[1] or arr.size == 0:
        return []
    n_features = int(arr.shape[0])
    records: list[dict[str, Any]] = []
    flat = arr.reshape(-1)
    for flat_idx in np.argsort(-flat)[: max(0, int(limit)) * 6 + 1]:
        score = float(flat[int(flat_idx)])
        if score <= 0.0:
            break
        target_idx = int(flat_idx // n_features)
        source_idx = int(flat_idx % n_features)
        if target_idx == source_idx:
            continue
        sources = [
            str(name)
            for name, mask in selected_masks.items()
            if np.asarray(mask).shape == arr.shape and bool(np.asarray(mask)[target_idx, source_idx])
        ]
        records.append(
            {
                "target": target_idx,
                "source": source_idx,
                "score": score,
                "votes": int(votes[target_idx, source_idx]),
                "sources": sources,
            }
        )
        if len(records) >= int(limit):
            break
    return records


def _component_edge_bank_prior(
    components: Mapping[str, np.ndarray],
    weights: Mapping[str, float],
    feature_group_ids: np.ndarray,
    *,
    top_k: int,
    group_top_k: int,
    min_votes: int = 2,
    single_view_scale: float = 0.55,
    vote_boost: float = 0.15,
    global_budget_multiplier: float = 0.0,
) -> tuple[np.ndarray, dict[str, Any]]:
    if not components:
        return np.zeros((0, 0), dtype=np.float32), {"enabled": False, "status": "empty_components"}
    first = next(iter(components.values()))
    n_features = int(np.asarray(first).shape[0]) if np.asarray(first).ndim == 2 else 0
    if n_features < 2:
        return np.zeros((n_features, n_features), dtype=np.float32), {"enabled": False, "status": "invalid_shape"}

    per_component_k = int(top_k) if int(top_k) > 0 else max(1, n_features - 1)
    selected_masks: dict[str, np.ndarray] = {}
    selected_scores: dict[str, np.ndarray] = {}
    weighted_sum = np.zeros((n_features, n_features), dtype=np.float32)
    weight_sum = np.zeros((n_features, n_features), dtype=np.float32)
    vote_count = np.zeros((n_features, n_features), dtype=np.float32)
    component_edge_counts: dict[str, int] = {}
    dynamic_single_mask = np.zeros((n_features, n_features), dtype=bool)
    dynamic_single_sources = {"lag", "fault_response", "stability"}

    for key, raw_component in components.items():
        component = _normalize_edge_prior(raw_component)
        if component.shape != (n_features, n_features) or float(np.max(component)) <= 0.0:
            continue
        component_weight = max(0.0, float(weights.get(key, 1.0)))
        if component_weight <= 0.0:
            continue
        selected = _cap_edges_by_endpoint_and_group(
            component,
            per_component_k,
            feature_group_ids,
            group_top_k=int(group_top_k),
        )
        mask = selected > 0.0
        if not np.any(mask):
            continue
        selected_masks[str(key)] = mask
        selected_scores[str(key)] = selected
        weighted_sum += component_weight * selected
        weight_sum += component_weight * mask.astype(np.float32)
        vote_count += mask.astype(np.float32)
        component_edge_counts[str(key)] = int(np.count_nonzero(mask))
        if str(key) in dynamic_single_sources:
            dynamic_single_mask |= mask

    if not selected_masks:
        return np.zeros((n_features, n_features), dtype=np.float32), {
            "enabled": False,
            "status": "empty_after_component_caps",
            "component_edge_counts": component_edge_counts,
        }

    consensus_score = np.divide(
        weighted_sum,
        weight_sum,
        out=np.zeros_like(weighted_sum, dtype=np.float32),
        where=weight_sum > 1.0e-12,
    )
    component_count = max(1, len(selected_masks))
    required_votes = max(1, min(int(min_votes), component_count))
    corroborated_mask = vote_count >= float(required_votes)
    single_mask = (vote_count == 1.0) & dynamic_single_mask
    single_scale = float(np.clip(single_view_scale, 0.0, 1.0))
    keep_mask = corroborated_mask | (single_mask & (single_scale > 0.0))
    boost = max(0.0, float(vote_boost))
    prior = consensus_score * (1.0 + boost * np.maximum(vote_count - 1.0, 0.0))
    prior = np.where(corroborated_mask, prior, prior * single_scale).astype(np.float32)
    prior = np.where(keep_mask, prior, 0.0).astype(np.float32)
    prior = _normalize_edge_prior(prior)
    pre_final_edges = int(np.count_nonzero(prior > 0.0))
    prior = _cap_edges_by_endpoint_and_group(
        prior,
        int(top_k),
        feature_group_ids,
        group_top_k=int(group_top_k),
    )
    global_budget = 0
    if float(global_budget_multiplier) > 0.0:
        global_budget = max(1, int(round(float(global_budget_multiplier) * n_features)))
        prior = _cap_edges_by_global_budget(prior, global_budget)
    final_mask = prior > 0.0
    final_votes = np.where(final_mask, vote_count, 0.0).astype(np.float32)
    return prior, {
        "enabled": bool(np.any(final_mask)),
        "status": "ok" if np.any(final_mask) else "empty_after_final_cap",
        "component_edge_counts": component_edge_counts,
        "component_count": int(component_count),
        "min_votes": int(required_votes),
        "single_view_scale": float(single_scale),
        "vote_boost": float(boost),
        "global_budget_multiplier": float(max(0.0, global_budget_multiplier)),
        "global_budget": int(global_budget),
        "pre_final_edges": int(pre_final_edges),
        "corroborated_edges": int(np.count_nonzero(final_mask & (vote_count >= float(required_votes)))),
        "single_view_edges": int(np.count_nonzero(final_mask & (vote_count == 1.0))),
        "mean_votes": float(np.mean(final_votes[final_mask])) if np.any(final_mask) else 0.0,
        "max_votes": int(np.max(final_votes)) if np.any(final_mask) else 0,
        "selected_masks": selected_masks,
        "top_edge_indices": _top_edge_bank_records(prior, vote_count, selected_masks, limit=20),
    }


def _component_edge_pool_prior(
    components: Mapping[str, np.ndarray],
    weights: Mapping[str, float],
    feature_group_ids: np.ndarray,
    *,
    top_k: int,
    group_top_k: int,
    pool_multiplier: float = 2.0,
    min_score: float = 0.0,
    min_votes: int = 2,
    single_view_scale: float = 0.35,
    vote_boost: float = 0.12,
    rank_weight: float = 0.35,
    global_budget_multiplier: float = 0.0,
) -> tuple[np.ndarray, dict[str, Any]]:
    if not components:
        return np.zeros((0, 0), dtype=np.float32), {"enabled": False, "status": "empty_components"}
    first = next(iter(components.values()))
    n_features = int(np.asarray(first).shape[0]) if np.asarray(first).ndim == 2 else 0
    if n_features < 2:
        return np.zeros((n_features, n_features), dtype=np.float32), {"enabled": False, "status": "invalid_shape"}

    multiplier = max(1.0, float(pool_multiplier))
    base_k = int(top_k) if int(top_k) > 0 else max(1, n_features - 1)
    pool_k = min(max(1, n_features - 1), max(base_k, int(round(base_k * multiplier))))
    base_group_k = int(group_top_k)
    pool_group_k = 0
    if base_group_k > 0:
        pool_group_k = max(base_group_k, int(round(base_group_k * multiplier)))

    min_component_score = float(np.clip(min_score, 0.0, 1.0))
    required_votes = max(1, int(min_votes))
    single_scale = float(np.clip(single_view_scale, 0.0, 1.0))
    boost = max(0.0, float(vote_boost))
    rank_mix = float(np.clip(rank_weight, 0.0, 1.0))
    selected_masks: dict[str, np.ndarray] = {}
    score_sum = np.zeros((n_features, n_features), dtype=np.float32)
    rank_sum = np.zeros((n_features, n_features), dtype=np.float32)
    weight_sum = np.zeros((n_features, n_features), dtype=np.float32)
    vote_count = np.zeros((n_features, n_features), dtype=np.float32)
    component_edge_counts: dict[str, int] = {}
    family_by_component = {
        "correlation": "structural",
        "residual": "structural",
        "lag": "dynamic",
        "directed_lag": "dynamic",
        "innovation": "dynamic",
        "class_lag": "dynamic",
        "stability": "dynamic",
        "class": "task",
        "fault_response": "task",
    }
    family_masks = {
        "structural": np.zeros((n_features, n_features), dtype=bool),
        "dynamic": np.zeros((n_features, n_features), dtype=bool),
        "task": np.zeros((n_features, n_features), dtype=bool),
    }

    for key, raw_component in components.items():
        component = _normalize_edge_prior(raw_component)
        if component.shape != (n_features, n_features) or float(np.max(component)) <= 0.0:
            continue
        component_weight = max(0.0, float(weights.get(key, 1.0)))
        if component_weight <= 0.0:
            continue
        selected = _cap_edges_by_endpoint_and_group(
            component,
            pool_k,
            feature_group_ids,
            group_top_k=int(pool_group_k),
        )
        if min_component_score > 0.0:
            selected = np.where(selected >= min_component_score, selected, 0.0).astype(np.float32)
        mask = selected > 0.0
        edge_count = int(np.count_nonzero(mask))
        if edge_count <= 0:
            continue
        selected_masks[str(key)] = mask
        component_edge_counts[str(key)] = edge_count
        score_sum += component_weight * selected
        weight_sum += component_weight * mask.astype(np.float32)
        vote_count += mask.astype(np.float32)
        family_masks[family_by_component.get(str(key), "dynamic")] |= mask

        ranks = np.zeros_like(selected, dtype=np.float32)
        flat_selected = selected.reshape(-1)
        rank = 0
        for flat_idx in np.argsort(-flat_selected):
            score = float(flat_selected[int(flat_idx)])
            if score <= 0.0:
                break
            target_idx = int(flat_idx // n_features)
            source_idx = int(flat_idx % n_features)
            if target_idx == source_idx:
                continue
            denom = max(1, edge_count - 1)
            ranks[target_idx, source_idx] = 1.0 - float(rank) / float(denom)
            rank += 1
        rank_sum += component_weight * ranks

    if not selected_masks:
        return np.zeros((n_features, n_features), dtype=np.float32), {
            "enabled": False,
            "status": "empty_after_pool_selection",
            "component_edge_counts": component_edge_counts,
        }

    score_consensus = np.divide(
        score_sum,
        weight_sum,
        out=np.zeros_like(score_sum, dtype=np.float32),
        where=weight_sum > 1.0e-12,
    )
    rank_consensus = np.divide(
        rank_sum,
        weight_sum,
        out=np.zeros_like(rank_sum, dtype=np.float32),
        where=weight_sum > 1.0e-12,
    )
    fused = (1.0 - rank_mix) * score_consensus + rank_mix * rank_consensus
    multi_vote_mask = vote_count >= float(required_votes)
    weak_mask = (vote_count == 1.0) & (single_scale > 0.0)
    keep_mask = multi_vote_mask | weak_mask
    prior = fused * np.where(multi_vote_mask, 1.0, single_scale).astype(np.float32)
    prior = prior * (1.0 + boost * np.maximum(vote_count - 1.0, 0.0))
    prior = np.where(keep_mask, prior, 0.0).astype(np.float32)
    prior = _normalize_edge_prior(prior)
    pre_final_edges = int(np.count_nonzero(prior > 0.0))
    prior = _cap_edges_by_endpoint_and_group(
        prior,
        int(top_k),
        feature_group_ids,
        group_top_k=int(group_top_k),
    )
    global_budget = 0
    if float(global_budget_multiplier) > 0.0:
        global_budget = max(1, int(round(float(global_budget_multiplier) * n_features)))
        prior = _cap_edges_by_global_budget(prior, global_budget)
    final_mask = prior > 0.0
    final_votes = np.where(final_mask, vote_count, 0.0).astype(np.float32)
    family_names = ["structural", "dynamic", "task"]
    family_prior_matrices = []
    family_density: dict[str, float] = {}
    for family_name in family_names:
        family_prior = np.where(final_mask & family_masks[family_name], prior, 0.0).astype(np.float32)
        family_prior = _normalize_edge_prior(family_prior)
        family_prior_matrices.append(family_prior)
        family_density[family_name] = float(np.mean(family_prior > 0.0)) if family_prior.size else 0.0
    return prior, {
        "enabled": bool(np.any(final_mask)),
        "status": "ok" if np.any(final_mask) else "empty_after_final_cap",
        "component_edge_counts": component_edge_counts,
        "component_count": int(len(selected_masks)),
        "pool_multiplier": float(multiplier),
        "pool_top_k": int(pool_k),
        "pool_group_top_k": int(pool_group_k),
        "min_score": float(min_component_score),
        "min_votes": int(required_votes),
        "single_view_scale": float(single_scale),
        "vote_boost": float(boost),
        "rank_weight": float(rank_mix),
        "global_budget_multiplier": float(max(0.0, global_budget_multiplier)),
        "global_budget": int(global_budget),
        "pre_final_edges": int(pre_final_edges),
        "corroborated_edges": int(np.count_nonzero(final_mask & multi_vote_mask)),
        "single_view_edges": int(np.count_nonzero(final_mask & (vote_count == 1.0))),
        "mean_votes": float(np.mean(final_votes[final_mask])) if np.any(final_mask) else 0.0,
        "max_votes": int(np.max(final_votes)) if np.any(final_mask) else 0,
        "family_names": family_names,
        "family_density": family_density,
        "family_prior_matrices": np.stack(family_prior_matrices, axis=0).astype(np.float32),
        "selected_masks": selected_masks,
        "top_edge_indices": _top_edge_bank_records(prior, vote_count, selected_masks, limit=20),
    }


def _component_edge_cert_pool_prior(
    components: Mapping[str, np.ndarray],
    weights: Mapping[str, float],
    feature_group_ids: np.ndarray,
    *,
    top_k: int,
    group_top_k: int,
    pool_multiplier: float = 2.0,
    min_score: float = 0.0,
    min_votes: int = 2,
    single_view_scale: float = 0.35,
    vote_boost: float = 0.12,
    rank_weight: float = 0.35,
    global_budget_multiplier: float = 0.0,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Build a broad edge pool, then keep only mechanism-certified candidates."""

    if not components:
        return np.zeros((0, 0), dtype=np.float32), {"enabled": False, "status": "empty_components"}
    first = next(iter(components.values()))
    n_features = int(np.asarray(first).shape[0]) if np.asarray(first).ndim == 2 else 0
    if n_features < 2:
        return np.zeros((n_features, n_features), dtype=np.float32), {"enabled": False, "status": "invalid_shape"}

    multiplier = max(1.0, float(pool_multiplier))
    base_k = int(top_k) if int(top_k) > 0 else max(1, n_features - 1)
    pool_k = min(max(1, n_features - 1), max(base_k, int(round(base_k * multiplier))))
    base_group_k = int(group_top_k)
    pool_group_k = max(base_group_k, int(round(base_group_k * multiplier))) if base_group_k > 0 else 0
    final_top_k = int(top_k) if int(top_k) > 0 else 0
    final_group_top_k = int(group_top_k)
    min_component_score = float(np.clip(min_score, 0.0, 1.0))
    required_votes = max(1, int(min_votes))
    single_scale = float(np.clip(single_view_scale, 0.0, 1.0))
    boost = max(0.0, float(vote_boost))
    rank_mix = float(np.clip(rank_weight, 0.0, 1.0))

    family_by_component = {
        "correlation": "structural",
        "residual": "structural",
        "lag": "dynamic",
        "directed_lag": "dynamic",
        "innovation": "dynamic",
        "class_lag": "dynamic",
        "stability": "dynamic",
        "class": "task",
        "fault_response": "task",
    }
    family_names = ["structural", "dynamic", "task"]
    family_weights = {"structural": 0.60, "dynamic": 1.10, "task": 1.15}
    selected_masks: dict[str, np.ndarray] = {}
    selected_scores: dict[str, np.ndarray] = {}
    family_masks = {name: np.zeros((n_features, n_features), dtype=bool) for name in family_names}
    family_score = {name: np.zeros((n_features, n_features), dtype=np.float32) for name in family_names}
    score_sum = np.zeros((n_features, n_features), dtype=np.float32)
    rank_sum = np.zeros((n_features, n_features), dtype=np.float32)
    weight_sum = np.zeros((n_features, n_features), dtype=np.float32)
    vote_count = np.zeros((n_features, n_features), dtype=np.float32)
    component_edge_counts: dict[str, int] = {}

    for key, raw_component in components.items():
        component = _normalize_edge_prior(raw_component)
        if component.shape != (n_features, n_features) or float(np.max(component)) <= 0.0:
            continue
        component_weight = max(0.0, float(weights.get(key, 1.0)))
        if component_weight <= 0.0:
            continue
        selected = _cap_edges_by_endpoint_and_group(
            component,
            pool_k,
            feature_group_ids,
            group_top_k=int(pool_group_k),
        )
        if min_component_score > 0.0:
            selected = np.where(selected >= min_component_score, selected, 0.0).astype(np.float32)
        mask = selected > 0.0
        edge_count = int(np.count_nonzero(mask))
        if edge_count <= 0:
            continue
        family = family_by_component.get(str(key), "dynamic")
        selected_masks[str(key)] = mask
        selected_scores[str(key)] = selected
        component_edge_counts[str(key)] = edge_count
        family_masks[family] |= mask
        family_score[family] = np.maximum(family_score[family], selected).astype(np.float32)
        score_sum += component_weight * selected
        weight_sum += component_weight * mask.astype(np.float32)
        vote_count += mask.astype(np.float32)

        ranks = np.zeros_like(selected, dtype=np.float32)
        flat_selected = selected.reshape(-1)
        rank = 0
        for flat_idx in np.argsort(-flat_selected):
            score = float(flat_selected[int(flat_idx)])
            if score <= 0.0:
                break
            target_idx = int(flat_idx // n_features)
            source_idx = int(flat_idx % n_features)
            if target_idx == source_idx:
                continue
            denom = max(1, edge_count - 1)
            ranks[target_idx, source_idx] = 1.0 - float(rank) / float(denom)
            rank += 1
        rank_sum += component_weight * ranks

    if not selected_masks:
        return np.zeros((n_features, n_features), dtype=np.float32), {
            "enabled": False,
            "status": "empty_after_cert_pool_selection",
            "component_edge_counts": component_edge_counts,
        }

    score_consensus = np.divide(
        score_sum,
        weight_sum,
        out=np.zeros_like(score_sum, dtype=np.float32),
        where=weight_sum > 1.0e-12,
    )
    rank_consensus = np.divide(
        rank_sum,
        weight_sum,
        out=np.zeros_like(rank_sum, dtype=np.float32),
        where=weight_sum > 1.0e-12,
    )
    fused = (1.0 - rank_mix) * score_consensus + rank_mix * rank_consensus

    structural_mask = family_masks["structural"]
    dynamic_mask = family_masks["dynamic"]
    task_mask = family_masks["task"]
    dynamic_support = family_score["dynamic"]
    task_support = family_score["task"]
    structural_support = family_score["structural"]
    stability_support = np.asarray(selected_scores.get("stability", np.zeros_like(fused)), dtype=np.float32)
    family_count = (
        structural_mask.astype(np.float32)
        + dynamic_mask.astype(np.float32)
        + task_mask.astype(np.float32)
    )

    multi_vote_mask = vote_count >= float(required_votes)
    dynamic_task_agreement = dynamic_mask & task_mask
    stability_mask = stability_support > 0.0
    stability_guarded = stability_mask & (dynamic_mask | task_mask | multi_vote_mask)
    structural_bridge = structural_mask & (dynamic_mask | task_mask | stability_mask) & (vote_count >= 2.0)
    single_dynamic_task = (vote_count == 1.0) & (dynamic_mask | task_mask)
    certified_single = single_dynamic_task & (stability_support >= 0.25)
    keep_mask = (
        dynamic_task_agreement
        | stability_guarded
        | (multi_vote_mask & (dynamic_mask | task_mask | structural_bridge))
        | certified_single
        | structural_bridge
    )

    mechanism_support = np.maximum.reduce(
        [
            dynamic_support,
            task_support,
            stability_support,
            0.50 * structural_support * structural_bridge.astype(np.float32),
        ]
    ).astype(np.float32)
    agreement_support = np.sqrt(np.clip(dynamic_support * task_support, 0.0, 1.0)).astype(np.float32)
    vote_support = np.clip(vote_count / float(max(1, required_votes)), 0.0, 1.0).astype(np.float32)
    certificate = np.maximum.reduce(
        [
            stability_support,
            agreement_support,
            mechanism_support * vote_support,
            0.35 * family_count,
        ]
    ).astype(np.float32)
    certificate = np.clip(certificate, 0.0, 1.0)
    scale = np.where(
        dynamic_task_agreement,
        1.0,
        np.where(
            stability_guarded,
            0.95,
            np.where(multi_vote_mask, 0.80, np.where(certified_single, single_scale, 0.45 * single_scale)),
        ),
    ).astype(np.float32)
    family_bonus = 1.0 + 0.10 * np.maximum(family_count - 1.0, 0.0)
    vote_gain = 1.0 + boost * np.minimum(np.maximum(vote_count - 1.0, 0.0), 2.0)
    prior = fused * scale * (0.45 + 0.55 * certificate) * family_bonus * vote_gain
    prior = np.where(keep_mask, prior, 0.0).astype(np.float32)

    directed_support = np.zeros((n_features, n_features), dtype=np.float32)
    for directional_key in ("directed_lag", "innovation", "class_lag", "fault_response", "lag", "stability"):
        if directional_key in selected_scores:
            directed_support = np.maximum(directed_support, np.asarray(selected_scores[directional_key], dtype=np.float32))
    reciprocal_scale = 0.0
    reciprocal_margin = 0.05
    reciprocal_pairs_before = int(np.count_nonzero((prior > 0.0) & (prior.T > 0.0)) // 2)
    for target_idx in range(n_features):
        for source_idx in range(target_idx + 1, n_features):
            forward = float(prior[target_idx, source_idx])
            backward = float(prior[source_idx, target_idx])
            if forward <= 0.0 or backward <= 0.0:
                continue
            forward_direction = float(directed_support[target_idx, source_idx])
            backward_direction = float(directed_support[source_idx, target_idx])
            margin = forward_direction - backward_direction
            if margin >= reciprocal_margin:
                prior[source_idx, target_idx] = backward * reciprocal_scale
            elif margin <= -reciprocal_margin:
                prior[target_idx, source_idx] = forward * reciprocal_scale
            elif forward >= backward:
                prior[source_idx, target_idx] = backward * reciprocal_scale
            else:
                prior[target_idx, source_idx] = forward * reciprocal_scale

    prior = _normalize_edge_prior(prior)
    pre_final_edges = int(np.count_nonzero(prior > 0.0))
    family_pre_edges: dict[str, int] = {}
    family_edge_counts: dict[str, int] = {}
    family_prior_matrices: list[np.ndarray] = []
    for family_name in family_names:
        family_prior = np.where(
            family_masks[family_name],
            prior * float(family_weights[family_name]),
            0.0,
        ).astype(np.float32)
        family_prior = _normalize_edge_prior(family_prior)
        family_pre_edges[family_name] = int(np.count_nonzero(family_prior > 0.0))
        family_prior = _cap_edges_by_endpoint_and_group(
            family_prior,
            final_top_k,
            feature_group_ids,
            group_top_k=final_group_top_k,
        )
        family_prior_matrices.append(family_prior)
        family_edge_counts[family_name] = int(np.count_nonzero(family_prior > 0.0))

    prior = np.maximum.reduce(family_prior_matrices).astype(np.float32)
    prior = _normalize_edge_prior(prior)
    prior = _cap_edges_by_endpoint_and_group(
        prior,
        final_top_k,
        feature_group_ids,
        group_top_k=final_group_top_k,
    )
    global_budget = 0
    if float(global_budget_multiplier) > 0.0:
        global_budget = max(1, int(round(float(global_budget_multiplier) * n_features)))
        prior = _cap_edges_by_global_budget(prior, global_budget)

    final_mask = prior > 0.0
    reciprocal_pairs_after = int(np.count_nonzero(final_mask & final_mask.T) // 2)
    final_votes = np.where(final_mask, vote_count, 0.0).astype(np.float32)
    final_family_count = np.where(final_mask, family_count, 0.0).astype(np.float32)
    final_certificate = np.where(final_mask, certificate, 0.0).astype(np.float32)
    final_family_priors = []
    family_density: dict[str, float] = {}
    for family_name in family_names:
        family_prior = np.where(final_mask & family_masks[family_name], prior, 0.0).astype(np.float32)
        family_prior = _normalize_edge_prior(family_prior)
        final_family_priors.append(family_prior)
        family_density[family_name] = float(np.mean(family_prior > 0.0)) if family_prior.size else 0.0

    return prior, {
        "enabled": bool(np.any(final_mask)),
        "status": "ok" if np.any(final_mask) else "empty_after_final_cap",
        "component_edge_counts": component_edge_counts,
        "component_count": int(len(selected_masks)),
        "pool_multiplier": float(multiplier),
        "pool_top_k": int(pool_k),
        "pool_group_top_k": int(pool_group_k),
        "min_score": float(min_component_score),
        "min_votes": int(required_votes),
        "single_view_scale": float(single_scale),
        "vote_boost": float(boost),
        "rank_weight": float(rank_mix),
        "family_weights": family_weights,
        "global_budget_multiplier": float(max(0.0, global_budget_multiplier)),
        "global_budget": int(global_budget),
        "pre_final_edges": int(pre_final_edges),
        "family_pre_edges": family_pre_edges,
        "family_edge_counts": family_edge_counts,
        "corroborated_edges": int(np.count_nonzero(final_mask & multi_vote_mask)),
        "dynamic_task_agreement_edges": int(np.count_nonzero(final_mask & dynamic_task_agreement)),
        "stability_guarded_edges": int(np.count_nonzero(final_mask & stability_guarded)),
        "structural_bridge_edges": int(np.count_nonzero(final_mask & structural_bridge)),
        "certified_single_edges": int(np.count_nonzero(final_mask & certified_single)),
        "structural_edges": int(np.count_nonzero(final_mask & structural_mask)),
        "dynamic_edges": int(np.count_nonzero(final_mask & dynamic_mask)),
        "task_edges": int(np.count_nonzero(final_mask & task_mask)),
        "reciprocal_pairs_before": int(reciprocal_pairs_before),
        "reciprocal_pairs_after": int(reciprocal_pairs_after),
        "reciprocal_scale": float(reciprocal_scale),
        "reciprocal_margin": float(reciprocal_margin),
        "mean_votes": float(np.mean(final_votes[final_mask])) if np.any(final_mask) else 0.0,
        "mean_family_count": float(np.mean(final_family_count[final_mask])) if np.any(final_mask) else 0.0,
        "mean_certificate": float(np.mean(final_certificate[final_mask])) if np.any(final_mask) else 0.0,
        "max_votes": int(np.max(final_votes)) if np.any(final_mask) else 0,
        "family_names": family_names,
        "family_density": family_density,
        "family_prior_matrices": np.stack(final_family_priors, axis=0).astype(np.float32),
        "selected_masks": selected_masks,
        "top_edge_indices": _top_edge_bank_records(prior, vote_count, selected_masks, limit=20),
    }


def _component_edge_canvas_prior(
    components: Mapping[str, np.ndarray],
    weights: Mapping[str, float],
    feature_group_ids: np.ndarray,
    *,
    top_k: int,
    group_top_k: int,
    pool_multiplier: float = 2.0,
    min_score: float = 0.0,
    min_votes: int = 2,
    single_view_scale: float = 0.35,
    vote_boost: float = 0.12,
    rank_weight: float = 0.35,
    global_budget_multiplier: float = 0.0,
) -> tuple[np.ndarray, dict[str, Any]]:
    if not components:
        return np.zeros((0, 0), dtype=np.float32), {"enabled": False, "status": "empty_components"}
    first = next(iter(components.values()))
    n_features = int(np.asarray(first).shape[0]) if np.asarray(first).ndim == 2 else 0
    if n_features < 2:
        return np.zeros((n_features, n_features), dtype=np.float32), {"enabled": False, "status": "invalid_shape"}

    multiplier = max(1.0, float(pool_multiplier))
    base_k = int(top_k) if int(top_k) > 0 else max(1, n_features - 1)
    pool_k = min(max(1, n_features - 1), max(base_k, int(round(base_k * multiplier))))
    base_group_k = int(group_top_k)
    pool_group_k = max(base_group_k, int(round(base_group_k * multiplier))) if base_group_k > 0 else 0
    min_component_score = float(np.clip(min_score, 0.0, 1.0))
    required_votes = max(1, int(min_votes))
    single_scale = float(np.clip(single_view_scale, 0.0, 1.0))
    structural_single_scale = 0.35 * single_scale
    boost = max(0.0, float(vote_boost))
    rank_mix = float(np.clip(rank_weight, 0.0, 1.0))

    family_by_component = {
        "correlation": "structural",
        "residual": "structural",
        "lag": "dynamic",
        "directed_lag": "dynamic",
        "innovation": "dynamic",
        "class_lag": "dynamic",
        "stability": "dynamic",
        "class": "task",
        "fault_response": "task",
    }
    family_masks = {
        "structural": np.zeros((n_features, n_features), dtype=bool),
        "dynamic": np.zeros((n_features, n_features), dtype=bool),
        "task": np.zeros((n_features, n_features), dtype=bool),
    }
    selected_masks: dict[str, np.ndarray] = {}
    score_sum = np.zeros((n_features, n_features), dtype=np.float32)
    rank_sum = np.zeros((n_features, n_features), dtype=np.float32)
    weight_sum = np.zeros((n_features, n_features), dtype=np.float32)
    vote_count = np.zeros((n_features, n_features), dtype=np.float32)
    component_edge_counts: dict[str, int] = {}

    for key, raw_component in components.items():
        component = _normalize_edge_prior(raw_component)
        if component.shape != (n_features, n_features) or float(np.max(component)) <= 0.0:
            continue
        component_weight = max(0.0, float(weights.get(key, 1.0)))
        if component_weight <= 0.0:
            continue
        selected = _cap_edges_by_endpoint_and_group(
            component,
            pool_k,
            feature_group_ids,
            group_top_k=int(pool_group_k),
        )
        if min_component_score > 0.0:
            selected = np.where(selected >= min_component_score, selected, 0.0).astype(np.float32)
        mask = selected > 0.0
        edge_count = int(np.count_nonzero(mask))
        if edge_count <= 0:
            continue
        selected_masks[str(key)] = mask
        component_edge_counts[str(key)] = edge_count
        score_sum += component_weight * selected
        weight_sum += component_weight * mask.astype(np.float32)
        vote_count += mask.astype(np.float32)
        family = family_by_component.get(str(key), "dynamic")
        family_masks[family] |= mask

        ranks = np.zeros_like(selected, dtype=np.float32)
        flat_selected = selected.reshape(-1)
        rank = 0
        for flat_idx in np.argsort(-flat_selected):
            score = float(flat_selected[int(flat_idx)])
            if score <= 0.0:
                break
            target_idx = int(flat_idx // n_features)
            source_idx = int(flat_idx % n_features)
            if target_idx == source_idx:
                continue
            denom = max(1, edge_count - 1)
            ranks[target_idx, source_idx] = 1.0 - float(rank) / float(denom)
            rank += 1
        rank_sum += component_weight * ranks

    if not selected_masks:
        return np.zeros((n_features, n_features), dtype=np.float32), {
            "enabled": False,
            "status": "empty_after_canvas_selection",
            "component_edge_counts": component_edge_counts,
        }

    score_consensus = np.divide(
        score_sum,
        weight_sum,
        out=np.zeros_like(score_sum, dtype=np.float32),
        where=weight_sum > 1.0e-12,
    )
    rank_consensus = np.divide(
        rank_sum,
        weight_sum,
        out=np.zeros_like(rank_sum, dtype=np.float32),
        where=weight_sum > 1.0e-12,
    )
    fused = (1.0 - rank_mix) * score_consensus + rank_mix * rank_consensus
    structural_mask = family_masks["structural"]
    dynamic_mask = family_masks["dynamic"]
    task_mask = family_masks["task"]
    family_count = (
        structural_mask.astype(np.float32)
        + dynamic_mask.astype(np.float32)
        + task_mask.astype(np.float32)
    )
    multi_vote_mask = vote_count >= float(required_votes)
    dynamic_or_task = dynamic_mask | task_mask
    single_dynamic_task = (vote_count == 1.0) & dynamic_or_task
    single_structural = (vote_count == 1.0) & structural_mask & ~dynamic_or_task
    keep_mask = multi_vote_mask | (single_dynamic_task & (single_scale > 0.0)) | (single_structural & (structural_single_scale > 0.0))
    scale = np.where(
        multi_vote_mask,
        1.0,
        np.where(single_dynamic_task, single_scale, structural_single_scale),
    ).astype(np.float32)
    family_bonus = 1.0 + 0.08 * np.maximum(family_count - 1.0, 0.0)
    vote_saturation = 1.0 / (1.0 + 0.18 * np.maximum(vote_count - 3.0, 0.0))
    emergent_dynamic_task_bonus = 1.0 + 0.12 * (dynamic_or_task & (vote_count <= 3.0)).astype(np.float32)
    prior = fused * scale
    prior = prior * (1.0 + boost * np.maximum(vote_count - 1.0, 0.0))
    prior = prior * family_bonus * vote_saturation * emergent_dynamic_task_bonus
    prior = np.where(keep_mask, prior, 0.0).astype(np.float32)
    prior = _normalize_edge_prior(prior)
    pre_final_edges = int(np.count_nonzero(prior > 0.0))
    prior = _cap_edges_by_endpoint_and_group(
        prior,
        int(top_k),
        feature_group_ids,
        group_top_k=int(group_top_k),
    )
    global_budget = 0
    if float(global_budget_multiplier) > 0.0:
        global_budget = max(1, int(round(float(global_budget_multiplier) * n_features)))
        prior = _cap_edges_by_global_budget(prior, global_budget)
    final_mask = prior > 0.0
    final_votes = np.where(final_mask, vote_count, 0.0).astype(np.float32)
    final_family_count = np.where(final_mask, family_count, 0.0).astype(np.float32)
    family_names = ["structural", "dynamic", "task"]
    family_prior_matrices = []
    family_density: dict[str, float] = {}
    for family_name in family_names:
        family_prior = np.where(final_mask & family_masks[family_name], prior, 0.0).astype(np.float32)
        family_prior = _normalize_edge_prior(family_prior)
        family_prior_matrices.append(family_prior)
        family_density[family_name] = float(np.mean(family_prior > 0.0)) if family_prior.size else 0.0
    return prior, {
        "enabled": bool(np.any(final_mask)),
        "status": "ok" if np.any(final_mask) else "empty_after_final_cap",
        "component_edge_counts": component_edge_counts,
        "component_count": int(len(selected_masks)),
        "pool_multiplier": float(multiplier),
        "pool_top_k": int(pool_k),
        "pool_group_top_k": int(pool_group_k),
        "min_score": float(min_component_score),
        "min_votes": int(required_votes),
        "single_view_scale": float(single_scale),
        "structural_single_view_scale": float(structural_single_scale),
        "vote_boost": float(boost),
        "rank_weight": float(rank_mix),
        "family_bonus_per_extra_family": 0.08,
        "vote_saturation_after_votes": 3,
        "emergent_dynamic_task_bonus": 0.12,
        "global_budget_multiplier": float(max(0.0, global_budget_multiplier)),
        "global_budget": int(global_budget),
        "pre_final_edges": int(pre_final_edges),
        "corroborated_edges": int(np.count_nonzero(final_mask & multi_vote_mask)),
        "single_dynamic_task_edges": int(np.count_nonzero(final_mask & single_dynamic_task)),
        "single_structural_edges": int(np.count_nonzero(final_mask & single_structural)),
        "structural_edges": int(np.count_nonzero(final_mask & structural_mask)),
        "dynamic_edges": int(np.count_nonzero(final_mask & dynamic_mask)),
        "task_edges": int(np.count_nonzero(final_mask & task_mask)),
        "mean_votes": float(np.mean(final_votes[final_mask])) if np.any(final_mask) else 0.0,
        "mean_family_count": float(np.mean(final_family_count[final_mask])) if np.any(final_mask) else 0.0,
        "max_votes": int(np.max(final_votes)) if np.any(final_mask) else 0,
        "family_names": family_names,
        "family_density": family_density,
        "family_prior_matrices": np.stack(family_prior_matrices, axis=0).astype(np.float32),
        "selected_masks": selected_masks,
        "top_edge_indices": _top_edge_bank_records(prior, vote_count, selected_masks, limit=20),
    }


def _component_edge_universe_prior(
    components: Mapping[str, np.ndarray],
    weights: Mapping[str, float],
    feature_group_ids: np.ndarray,
    *,
    top_k: int,
    group_top_k: int,
    pool_multiplier: float = 2.0,
    min_score: float = 0.0,
    min_votes: int = 2,
    single_view_scale: float = 0.35,
    vote_boost: float = 0.12,
    rank_weight: float = 0.35,
    global_budget_multiplier: float = 0.0,
) -> tuple[np.ndarray, dict[str, Any]]:
    if not components:
        return np.zeros((0, 0), dtype=np.float32), {"enabled": False, "status": "empty_components"}
    first = next(iter(components.values()))
    n_features = int(np.asarray(first).shape[0]) if np.asarray(first).ndim == 2 else 0
    if n_features < 2:
        return np.zeros((n_features, n_features), dtype=np.float32), {"enabled": False, "status": "invalid_shape"}

    multiplier = max(1.0, float(pool_multiplier))
    base_k = int(top_k) if int(top_k) > 0 else max(1, n_features - 1)
    pool_k = min(max(1, n_features - 1), max(base_k, int(round(base_k * multiplier))))
    base_group_k = int(group_top_k)
    pool_group_k = max(base_group_k, int(round(base_group_k * multiplier))) if base_group_k > 0 else 0
    family_quota_top_k = int(top_k) if int(top_k) > 0 else 0
    final_top_k = 0 if int(top_k) <= 0 else max(int(top_k), int(math.ceil(float(top_k) * 1.5)))
    family_quota_group_top_k = int(group_top_k)
    final_group_top_k = 0 if int(group_top_k) <= 0 else max(int(group_top_k), int(math.ceil(float(group_top_k) * 1.5)))
    min_component_score = float(np.clip(min_score, 0.0, 1.0))
    required_votes = max(1, int(min_votes))
    single_scale = float(np.clip(single_view_scale, 0.0, 1.0))
    structural_single_scale = 0.45 * single_scale
    boost = max(0.0, float(vote_boost))
    rank_mix = float(np.clip(rank_weight, 0.0, 1.0))

    family_by_component = {
        "correlation": "structural",
        "residual": "structural",
        "lag": "dynamic",
        "directed_lag": "dynamic",
        "innovation": "dynamic",
        "class_lag": "dynamic",
        "stability": "dynamic",
        "class": "task",
        "fault_response": "task",
    }
    family_names = ["structural", "dynamic", "task"]
    family_weights = {"structural": 0.80, "dynamic": 1.05, "task": 1.05}
    family_masks = {name: np.zeros((n_features, n_features), dtype=bool) for name in family_names}
    selected_masks: dict[str, np.ndarray] = {}
    score_sum = np.zeros((n_features, n_features), dtype=np.float32)
    rank_sum = np.zeros((n_features, n_features), dtype=np.float32)
    weight_sum = np.zeros((n_features, n_features), dtype=np.float32)
    vote_count = np.zeros((n_features, n_features), dtype=np.float32)
    component_edge_counts: dict[str, int] = {}
    family_component_counts = {name: 0 for name in family_names}

    for key, raw_component in components.items():
        component = _normalize_edge_prior(raw_component)
        if component.shape != (n_features, n_features) or float(np.max(component)) <= 0.0:
            continue
        component_weight = max(0.0, float(weights.get(key, 1.0)))
        if component_weight <= 0.0:
            continue
        selected = _cap_edges_by_endpoint_and_group(
            component,
            pool_k,
            feature_group_ids,
            group_top_k=int(pool_group_k),
        )
        if min_component_score > 0.0:
            selected = np.where(selected >= min_component_score, selected, 0.0).astype(np.float32)
        mask = selected > 0.0
        edge_count = int(np.count_nonzero(mask))
        if edge_count <= 0:
            continue
        family = family_by_component.get(str(key), "dynamic")
        selected_masks[str(key)] = mask
        component_edge_counts[str(key)] = edge_count
        family_component_counts[family] += 1
        family_masks[family] |= mask
        score_sum += component_weight * selected
        weight_sum += component_weight * mask.astype(np.float32)
        vote_count += mask.astype(np.float32)

        ranks = np.zeros_like(selected, dtype=np.float32)
        flat_selected = selected.reshape(-1)
        rank = 0
        for flat_idx in np.argsort(-flat_selected):
            score = float(flat_selected[int(flat_idx)])
            if score <= 0.0:
                break
            target_idx = int(flat_idx // n_features)
            source_idx = int(flat_idx % n_features)
            if target_idx == source_idx:
                continue
            denom = max(1, edge_count - 1)
            ranks[target_idx, source_idx] = 1.0 - float(rank) / float(denom)
            rank += 1
        rank_sum += component_weight * ranks

    if not selected_masks:
        return np.zeros((n_features, n_features), dtype=np.float32), {
            "enabled": False,
            "status": "empty_after_universe_selection",
            "component_edge_counts": component_edge_counts,
        }

    score_consensus = np.divide(
        score_sum,
        weight_sum,
        out=np.zeros_like(score_sum, dtype=np.float32),
        where=weight_sum > 1.0e-12,
    )
    rank_consensus = np.divide(
        rank_sum,
        weight_sum,
        out=np.zeros_like(rank_sum, dtype=np.float32),
        where=weight_sum > 1.0e-12,
    )
    fused = (1.0 - rank_mix) * score_consensus + rank_mix * rank_consensus
    family_count = sum(mask.astype(np.float32) for mask in family_masks.values())
    multi_vote_mask = vote_count >= float(required_votes)
    dynamic_or_task = family_masks["dynamic"] | family_masks["task"]
    single_dynamic_task = (vote_count == 1.0) & dynamic_or_task
    single_structural = (vote_count == 1.0) & family_masks["structural"] & ~dynamic_or_task
    scale = np.where(
        multi_vote_mask,
        1.0,
        np.where(single_dynamic_task, single_scale, structural_single_scale),
    ).astype(np.float32)
    vote_gain = 1.0 + boost * np.minimum(np.maximum(vote_count - 1.0, 0.0), 2.0)
    family_gain = 1.0 + 0.06 * np.maximum(family_count - 1.0, 0.0)
    base_score = fused * scale * vote_gain * family_gain

    pre_family_edges: dict[str, int] = {}
    family_edge_counts: dict[str, int] = {}
    pre_family_prior_matrices: list[np.ndarray] = []
    for family_name in family_names:
        family_prior = np.where(family_masks[family_name], base_score * family_weights[family_name], 0.0).astype(np.float32)
        if family_name == "structural":
            family_prior = np.where(single_structural, family_prior * 0.75, family_prior).astype(np.float32)
        family_prior = _normalize_edge_prior(family_prior)
        pre_family_edges[family_name] = int(np.count_nonzero(family_prior > 0.0))
        family_prior = _cap_edges_by_endpoint_and_group(
            family_prior,
            family_quota_top_k,
            feature_group_ids,
            group_top_k=family_quota_group_top_k,
        )
        pre_family_prior_matrices.append(family_prior)
        family_edge_counts[family_name] = int(np.count_nonzero(family_prior > 0.0))

    prior = np.maximum.reduce(pre_family_prior_matrices).astype(np.float32)
    prior = _normalize_edge_prior(prior)
    pre_final_edges = int(np.count_nonzero(prior > 0.0))
    prior = _cap_edges_by_endpoint_and_group(
        prior,
        final_top_k,
        feature_group_ids,
        group_top_k=final_group_top_k,
    )
    global_budget = 0
    if float(global_budget_multiplier) > 0.0:
        global_budget = max(1, int(round(float(global_budget_multiplier) * n_features)))
        prior = _cap_edges_by_global_budget(prior, global_budget)

    final_mask = prior > 0.0
    final_votes = np.where(final_mask, vote_count, 0.0).astype(np.float32)
    final_family_count = np.where(final_mask, family_count, 0.0).astype(np.float32)
    family_prior_matrices = []
    family_density: dict[str, float] = {}
    for family_name in family_names:
        family_prior = np.where(final_mask & family_masks[family_name], prior, 0.0).astype(np.float32)
        family_prior = _normalize_edge_prior(family_prior)
        family_prior_matrices.append(family_prior)
        family_density[family_name] = float(np.mean(family_prior > 0.0)) if family_prior.size else 0.0
    return prior, {
        "enabled": bool(np.any(final_mask)),
        "status": "ok" if np.any(final_mask) else "empty_after_final_cap",
        "component_edge_counts": component_edge_counts,
        "component_count": int(len(selected_masks)),
        "family_component_counts": family_component_counts,
        "pool_multiplier": float(multiplier),
        "pool_top_k": int(pool_k),
        "pool_group_top_k": int(pool_group_k),
        "family_quota_top_k": int(family_quota_top_k),
        "family_quota_group_top_k": int(family_quota_group_top_k),
        "final_top_k": int(final_top_k),
        "final_group_top_k": int(final_group_top_k),
        "min_score": float(min_component_score),
        "min_votes": int(required_votes),
        "single_view_scale": float(single_scale),
        "structural_single_view_scale": float(structural_single_scale),
        "vote_boost": float(boost),
        "rank_weight": float(rank_mix),
        "family_weights": family_weights,
        "global_budget_multiplier": float(max(0.0, global_budget_multiplier)),
        "global_budget": int(global_budget),
        "pre_family_edges": pre_family_edges,
        "family_edge_counts": family_edge_counts,
        "pre_final_edges": int(pre_final_edges),
        "corroborated_edges": int(np.count_nonzero(final_mask & multi_vote_mask)),
        "single_dynamic_task_edges": int(np.count_nonzero(final_mask & single_dynamic_task)),
        "single_structural_edges": int(np.count_nonzero(final_mask & single_structural)),
        "mean_votes": float(np.mean(final_votes[final_mask])) if np.any(final_mask) else 0.0,
        "mean_family_count": float(np.mean(final_family_count[final_mask])) if np.any(final_mask) else 0.0,
        "max_votes": int(np.max(final_votes)) if np.any(final_mask) else 0,
        "family_names": family_names,
        "family_density": family_density,
        "family_prior_matrices": np.stack(family_prior_matrices, axis=0).astype(np.float32),
        "selected_masks": selected_masks,
        "top_edge_indices": _top_edge_bank_records(prior, vote_count, selected_masks, limit=20),
    }


def _component_edge_sieve_prior(
    components: Mapping[str, np.ndarray],
    weights: Mapping[str, float],
    feature_group_ids: np.ndarray,
    *,
    top_k: int,
    group_top_k: int,
    pool_multiplier: float = 2.0,
    min_score: float = 0.0,
    min_votes: int = 2,
    single_view_scale: float = 0.35,
    vote_boost: float = 0.12,
    rank_weight: float = 0.35,
    global_budget_multiplier: float = 0.0,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Build a broad train-only edge canvas, then keep only mechanism-stable edges."""

    if not components:
        return np.zeros((0, 0), dtype=np.float32), {"enabled": False, "status": "empty_components"}
    first = next(iter(components.values()))
    n_features = int(np.asarray(first).shape[0]) if np.asarray(first).ndim == 2 else 0
    if n_features < 2:
        return np.zeros((n_features, n_features), dtype=np.float32), {"enabled": False, "status": "invalid_shape"}

    multiplier = max(1.0, float(pool_multiplier))
    base_k = int(top_k) if int(top_k) > 0 else max(1, n_features - 1)
    pool_k = min(max(1, n_features - 1), max(base_k, int(round(base_k * multiplier))))
    base_group_k = int(group_top_k)
    pool_group_k = max(base_group_k, int(round(base_group_k * multiplier))) if base_group_k > 0 else 0
    required_votes = max(1, int(min_votes))
    single_scale = float(np.clip(single_view_scale, 0.0, 1.0))
    structural_single_scale = 0.25 * single_scale
    boost = max(0.0, float(vote_boost))
    rank_mix = float(np.clip(rank_weight, 0.0, 1.0))
    min_component_score = float(np.clip(min_score, 0.0, 1.0))

    family_by_component = {
        "correlation": "structural",
        "residual": "structural",
        "lag": "dynamic",
        "directed_lag": "dynamic",
        "innovation": "dynamic",
        "class_lag": "dynamic",
        "stability": "dynamic",
        "class": "task",
        "fault_response": "task",
    }
    family_names = ["structural", "dynamic", "task"]
    family_masks = {name: np.zeros((n_features, n_features), dtype=bool) for name in family_names}
    selected_masks: dict[str, np.ndarray] = {}
    selected_scores: dict[str, np.ndarray] = {}
    score_sum = np.zeros((n_features, n_features), dtype=np.float32)
    rank_sum = np.zeros((n_features, n_features), dtype=np.float32)
    weight_sum = np.zeros((n_features, n_features), dtype=np.float32)
    vote_count = np.zeros((n_features, n_features), dtype=np.float32)
    component_edge_counts: dict[str, int] = {}

    for key, raw_component in components.items():
        component = _normalize_edge_prior(raw_component)
        if component.shape != (n_features, n_features) or float(np.max(component)) <= 0.0:
            continue
        component_weight = max(0.0, float(weights.get(key, 1.0)))
        if component_weight <= 0.0:
            continue
        selected = _cap_edges_by_endpoint_and_group(
            component,
            pool_k,
            feature_group_ids,
            group_top_k=int(pool_group_k),
        )
        if min_component_score > 0.0:
            selected = np.where(selected >= min_component_score, selected, 0.0).astype(np.float32)
        mask = selected > 0.0
        edge_count = int(np.count_nonzero(mask))
        if edge_count <= 0:
            continue
        family = family_by_component.get(str(key), "dynamic")
        selected_masks[str(key)] = mask
        selected_scores[str(key)] = selected
        component_edge_counts[str(key)] = edge_count
        family_masks[family] |= mask
        score_sum += component_weight * selected
        weight_sum += component_weight * mask.astype(np.float32)
        vote_count += mask.astype(np.float32)

        ranks = np.zeros_like(selected, dtype=np.float32)
        flat_selected = selected.reshape(-1)
        rank = 0
        for flat_idx in np.argsort(-flat_selected):
            score = float(flat_selected[int(flat_idx)])
            if score <= 0.0:
                break
            target_idx = int(flat_idx // n_features)
            source_idx = int(flat_idx % n_features)
            if target_idx == source_idx:
                continue
            denom = max(1, edge_count - 1)
            ranks[target_idx, source_idx] = 1.0 - float(rank) / float(denom)
            rank += 1
        rank_sum += component_weight * ranks

    if not selected_masks:
        return np.zeros((n_features, n_features), dtype=np.float32), {
            "enabled": False,
            "status": "empty_after_sieve_selection",
            "component_edge_counts": component_edge_counts,
        }

    score_consensus = np.divide(
        score_sum,
        weight_sum,
        out=np.zeros_like(score_sum, dtype=np.float32),
        where=weight_sum > 1.0e-12,
    )
    rank_consensus = np.divide(
        rank_sum,
        weight_sum,
        out=np.zeros_like(rank_sum, dtype=np.float32),
        where=weight_sum > 1.0e-12,
    )
    fused = (1.0 - rank_mix) * score_consensus + rank_mix * rank_consensus
    structural_mask = family_masks["structural"]
    dynamic_mask = family_masks["dynamic"]
    task_mask = family_masks["task"]
    family_count = (
        structural_mask.astype(np.float32)
        + dynamic_mask.astype(np.float32)
        + task_mask.astype(np.float32)
    )
    stability_support = selected_scores.get("stability", np.zeros((n_features, n_features), dtype=np.float32))
    stability_mask = stability_support > 0.0
    multi_vote_mask = vote_count >= float(required_votes)
    dynamic_or_task = dynamic_mask | task_mask
    single_dynamic_task = (vote_count == 1.0) & dynamic_or_task
    single_structural = (vote_count == 1.0) & structural_mask & ~dynamic_or_task
    multi_family_mask = family_count >= 2.0
    stability_guarded = stability_mask & (dynamic_or_task | multi_vote_mask)
    corroborated_mechanism = multi_vote_mask & (dynamic_or_task | multi_family_mask)
    keep_mask = (
        stability_guarded
        | corroborated_mechanism
        | (single_dynamic_task & stability_mask & (single_scale > 0.0))
        | (single_structural & multi_family_mask & (structural_single_scale > 0.0))
    )
    scale = np.where(
        stability_guarded,
        1.0,
        np.where(corroborated_mechanism, 0.80, np.where(single_dynamic_task, single_scale, structural_single_scale)),
    ).astype(np.float32)
    family_bonus = 1.0 + 0.08 * np.maximum(family_count - 1.0, 0.0)
    stability_bonus = 0.55 + 0.45 * np.maximum(stability_support, multi_family_mask.astype(np.float32) * 0.50)
    prior = fused * scale
    prior = prior * (1.0 + boost * np.minimum(np.maximum(vote_count - 1.0, 0.0), 2.0))
    prior = prior * family_bonus * stability_bonus
    prior = np.where(keep_mask, prior, 0.0).astype(np.float32)
    directed_support = np.zeros((n_features, n_features), dtype=np.float32)
    for directional_key in ("directed_lag", "innovation", "class_lag", "fault_response", "lag", "stability"):
        if directional_key in selected_scores:
            directed_support = np.maximum(directed_support, np.asarray(selected_scores[directional_key], dtype=np.float32))
    reciprocal_scale = 0.0
    reciprocal_margin = 0.05
    reciprocal_pairs_before = int(np.count_nonzero((prior > 0.0) & (prior.T > 0.0)) // 2)
    for target_idx in range(n_features):
        for source_idx in range(target_idx + 1, n_features):
            forward = float(prior[target_idx, source_idx])
            backward = float(prior[source_idx, target_idx])
            if forward <= 0.0 or backward <= 0.0:
                continue
            forward_direction = float(directed_support[target_idx, source_idx])
            backward_direction = float(directed_support[source_idx, target_idx])
            margin = forward_direction - backward_direction
            if margin >= reciprocal_margin:
                prior[source_idx, target_idx] = backward * reciprocal_scale
            elif margin <= -reciprocal_margin:
                prior[target_idx, source_idx] = forward * reciprocal_scale
            elif forward >= backward:
                prior[source_idx, target_idx] = backward * reciprocal_scale
            else:
                prior[target_idx, source_idx] = forward * reciprocal_scale
    prior = _normalize_edge_prior(prior)
    pre_final_edges = int(np.count_nonzero(prior > 0.0))
    prior = _cap_edges_by_endpoint_and_group(
        prior,
        int(top_k),
        feature_group_ids,
        group_top_k=int(group_top_k),
    )
    global_budget = 0
    if float(global_budget_multiplier) > 0.0:
        global_budget = max(1, int(round(float(global_budget_multiplier) * n_features)))
        prior = _cap_edges_by_global_budget(prior, global_budget)

    final_mask = prior > 0.0
    reciprocal_pairs_after = int(np.count_nonzero(final_mask & final_mask.T) // 2)
    final_votes = np.where(final_mask, vote_count, 0.0).astype(np.float32)
    final_family_count = np.where(final_mask, family_count, 0.0).astype(np.float32)
    family_prior_matrices = []
    family_density: dict[str, float] = {}
    for family_name in family_names:
        family_prior = np.where(final_mask & family_masks[family_name], prior, 0.0).astype(np.float32)
        family_prior = _normalize_edge_prior(family_prior)
        family_prior_matrices.append(family_prior)
        family_density[family_name] = float(np.mean(family_prior > 0.0)) if family_prior.size else 0.0
    return prior, {
        "enabled": bool(np.any(final_mask)),
        "status": "ok" if np.any(final_mask) else "empty_after_final_cap",
        "component_edge_counts": component_edge_counts,
        "component_count": int(len(selected_masks)),
        "pool_multiplier": float(multiplier),
        "pool_top_k": int(pool_k),
        "pool_group_top_k": int(pool_group_k),
        "min_score": float(min_component_score),
        "min_votes": int(required_votes),
        "single_view_scale": float(single_scale),
        "structural_single_view_scale": float(structural_single_scale),
        "vote_boost": float(boost),
        "rank_weight": float(rank_mix),
        "global_budget_multiplier": float(max(0.0, global_budget_multiplier)),
        "global_budget": int(global_budget),
        "pre_final_edges": int(pre_final_edges),
        "reciprocal_pairs_before": int(reciprocal_pairs_before),
        "reciprocal_pairs_after": int(reciprocal_pairs_after),
        "reciprocal_scale": float(reciprocal_scale),
        "reciprocal_margin": float(reciprocal_margin),
        "stability_guarded_edges": int(np.count_nonzero(final_mask & stability_guarded)),
        "corroborated_mechanism_edges": int(np.count_nonzero(final_mask & corroborated_mechanism)),
        "single_dynamic_task_edges": int(np.count_nonzero(final_mask & single_dynamic_task)),
        "single_structural_edges": int(np.count_nonzero(final_mask & single_structural)),
        "structural_edges": int(np.count_nonzero(final_mask & structural_mask)),
        "dynamic_edges": int(np.count_nonzero(final_mask & dynamic_mask)),
        "task_edges": int(np.count_nonzero(final_mask & task_mask)),
        "mean_votes": float(np.mean(final_votes[final_mask])) if np.any(final_mask) else 0.0,
        "mean_family_count": float(np.mean(final_family_count[final_mask])) if np.any(final_mask) else 0.0,
        "max_votes": int(np.max(final_votes)) if np.any(final_mask) else 0,
        "mean_stability_support": float(np.mean(stability_support[final_mask])) if np.any(final_mask) else 0.0,
        "family_names": family_names,
        "family_density": family_density,
        "family_prior_matrices": np.stack(family_prior_matrices, axis=0).astype(np.float32),
        "selected_masks": selected_masks,
        "top_edge_indices": _top_edge_bank_records(prior, vote_count, selected_masks, limit=20),
    }


def _expand_edge_prior_by_group_lattice(
    prior: np.ndarray,
    feature_group_ids: np.ndarray,
    *,
    feature_affinity: np.ndarray | None = None,
    expansion_scale: float = 0.55,
    endpoint_floor: float = 0.35,
    neighbor_top_k: int = 2,
    neighbor_scale: float = 0.35,
) -> tuple[np.ndarray, dict[str, Any]]:
    base = _normalize_edge_prior(prior)
    if base.ndim != 2 or base.shape[0] != base.shape[1]:
        return base, {"enabled": False, "status": "invalid_shape"}
    n_features = int(base.shape[0])
    groups = np.asarray(feature_group_ids, dtype=np.int64).reshape(-1)
    if len(groups) != n_features:
        groups = np.arange(n_features, dtype=np.int64)
    unique_groups, group_inverse = np.unique(groups, return_inverse=True)
    n_groups = int(len(unique_groups))

    group_pair_strength = np.zeros((n_groups, n_groups), dtype=np.float32)
    for target_idx, source_idx in np.argwhere(base > 0.0):
        if int(target_idx) == int(source_idx):
            continue
        target_group = int(group_inverse[int(target_idx)])
        source_group = int(group_inverse[int(source_idx)])
        group_pair_strength[target_group, source_group] = max(
            float(group_pair_strength[target_group, source_group]),
            float(base[int(target_idx), int(source_idx)]),
        )

    target_endpoint = np.max(base, axis=1) if base.size else np.zeros(n_features, dtype=np.float32)
    source_endpoint = np.max(base, axis=0) if base.size else np.zeros(n_features, dtype=np.float32)
    endpoint_support = np.sqrt(np.maximum(target_endpoint[:, None], 0.0) * np.maximum(source_endpoint[None, :], 0.0))
    endpoint_scale = float(np.clip(endpoint_floor, 0.0, 1.0)) + (1.0 - float(np.clip(endpoint_floor, 0.0, 1.0))) * endpoint_support
    group_expanded = group_pair_strength[group_inverse[:, None], group_inverse[None, :]] * endpoint_scale
    np.fill_diagonal(group_expanded, 0.0)
    group_expanded = np.asarray(
        np.clip(float(np.clip(expansion_scale, 0.0, 1.0)) * group_expanded, 0.0, 1.0),
        dtype=np.float32,
    )

    affinity_expanded = np.zeros_like(base, dtype=np.float32)
    affinity = None if feature_affinity is None else _normalize_edge_prior(np.asarray(feature_affinity, dtype=np.float32))
    if affinity is not None and tuple(affinity.shape) == tuple(base.shape) and float(np.max(affinity)) > 0.0:
        affinity = np.maximum(affinity, affinity.T).astype(np.float32)
        np.fill_diagonal(affinity, 0.0)
        affinity = _normalize_edge_prior(affinity)
        k = max(0, min(int(neighbor_top_k), max(0, n_features - 1)))
        scale = float(np.clip(neighbor_scale, 0.0, 1.0))
        if k > 0 and scale > 0.0:
            for target_idx, source_idx in np.argwhere(base > 0.0):
                target_idx = int(target_idx)
                source_idx = int(source_idx)
                edge_score = float(base[target_idx, source_idx])
                if edge_score <= 0.0 or target_idx == source_idx:
                    continue
                target_neighbors = np.argsort(-affinity[:, target_idx])[:k]
                source_neighbors = np.argsort(-affinity[:, source_idx])[:k]
                for neigh_target in target_neighbors:
                    neigh_target = int(neigh_target)
                    if neigh_target == source_idx or neigh_target == target_idx:
                        continue
                    score = edge_score * scale * float(affinity[neigh_target, target_idx])
                    affinity_expanded[neigh_target, source_idx] = max(float(affinity_expanded[neigh_target, source_idx]), score)
                for neigh_source in source_neighbors:
                    neigh_source = int(neigh_source)
                    if neigh_source == target_idx or neigh_source == source_idx:
                        continue
                    score = edge_score * scale * float(affinity[neigh_source, source_idx])
                    affinity_expanded[target_idx, neigh_source] = max(float(affinity_expanded[target_idx, neigh_source]), score)
                for neigh_target in target_neighbors[: max(1, k // 2)]:
                    neigh_target = int(neigh_target)
                    if neigh_target == target_idx:
                        continue
                    for neigh_source in source_neighbors[: max(1, k // 2)]:
                        neigh_source = int(neigh_source)
                        if neigh_source == source_idx or neigh_target == neigh_source:
                            continue
                        score = edge_score * scale * 0.50 * math.sqrt(
                            max(0.0, float(affinity[neigh_target, target_idx]))
                            * max(0.0, float(affinity[neigh_source, source_idx]))
                        )
                        affinity_expanded[neigh_target, neigh_source] = max(
                            float(affinity_expanded[neigh_target, neigh_source]),
                            score,
                        )
    np.fill_diagonal(affinity_expanded, 0.0)
    expanded = np.maximum(group_expanded, affinity_expanded).astype(np.float32)
    expanded_only = (expanded > 0.0) & ~(base > 0.0)
    return expanded, {
        "enabled": bool(np.any(expanded > 0.0)),
        "status": "ok" if np.any(expanded > 0.0) else "empty_expansion",
        "n_groups": int(n_groups),
        "group_pair_count": int(np.count_nonzero(group_pair_strength > 0.0)),
        "expansion_scale": float(np.clip(expansion_scale, 0.0, 1.0)),
        "endpoint_floor": float(np.clip(endpoint_floor, 0.0, 1.0)),
        "neighbor_top_k": int(max(0, neighbor_top_k)),
        "neighbor_scale": float(np.clip(neighbor_scale, 0.0, 1.0)),
        "affinity_enabled": bool(affinity is not None and tuple(affinity.shape) == tuple(base.shape) and float(np.max(affinity)) > 0.0),
        "group_expanded_edges": int(np.count_nonzero(group_expanded > 0.0)),
        "affinity_expanded_edges": int(np.count_nonzero(affinity_expanded > 0.0)),
        "expanded_edges": int(np.count_nonzero(expanded > 0.0)),
        "expanded_only_edges": int(np.count_nonzero(expanded_only)),
        "mean_group_pair_strength": float(np.mean(group_pair_strength[group_pair_strength > 0.0]))
        if np.any(group_pair_strength > 0.0)
        else 0.0,
        "top_edge_indices": _top_edge_records(expanded, limit=20),
    }


def _feature_affinity_from_edge_components(components: Mapping[str, np.ndarray]) -> np.ndarray | None:
    affinity: np.ndarray | None = None
    for key in ("correlation", "residual", "lag", "directed_lag", "innovation", "stability"):
        raw_component = components.get(key)
        if raw_component is None:
            continue
        component = _normalize_edge_prior(raw_component)
        if component.ndim != 2 or component.shape[0] != component.shape[1] or float(np.max(component)) <= 0.0:
            continue
        symmetric = np.maximum(component, component.T).astype(np.float32)
        affinity = symmetric if affinity is None else np.maximum(affinity, symmetric).astype(np.float32)
    if affinity is None:
        return None
    np.fill_diagonal(affinity, 0.0)
    affinity = _normalize_edge_prior(affinity)
    return affinity if float(np.max(affinity)) > 0.0 else None


def _component_edge_lattice_prior(
    components: Mapping[str, np.ndarray],
    weights: Mapping[str, float],
    feature_group_ids: np.ndarray,
    *,
    top_k: int,
    group_top_k: int,
    pool_multiplier: float = 2.0,
    min_score: float = 0.0,
    min_votes: int = 2,
    single_view_scale: float = 0.35,
    vote_boost: float = 0.12,
    rank_weight: float = 0.35,
    global_budget_multiplier: float = 0.0,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Build a direct edge universe, then widen it through feature-group mechanism families."""

    direct_prior, direct_diag = _component_edge_universe_prior(
        components,
        weights,
        feature_group_ids,
        top_k=int(top_k),
        group_top_k=int(group_top_k),
        pool_multiplier=max(1.0, float(pool_multiplier)),
        min_score=float(min_score),
        min_votes=int(min_votes),
        single_view_scale=float(single_view_scale),
        vote_boost=float(vote_boost),
        rank_weight=float(rank_weight),
        global_budget_multiplier=0.0,
    )
    if not bool(direct_diag.get("enabled", False)):
        return direct_prior, {
            "enabled": False,
            "status": str(direct_diag.get("status", "empty_direct_universe")),
            "direct_universe": {key: value for key, value in direct_diag.items() if key not in {"selected_masks", "family_prior_matrices"}},
        }

    expansion_scale = float(np.clip(0.30 + 0.55 * float(np.clip(single_view_scale, 0.0, 1.0)), 0.25, 0.80))
    endpoint_floor = float(np.clip(0.20 + 0.40 * float(np.clip(single_view_scale, 0.0, 1.0)), 0.20, 0.65))
    lattice_prior, lattice_diag = _expand_edge_prior_by_group_lattice(
        direct_prior,
        feature_group_ids,
        feature_affinity=_feature_affinity_from_edge_components(components),
        expansion_scale=expansion_scale,
        endpoint_floor=endpoint_floor,
        neighbor_top_k=max(1, min(3, int(round(math.sqrt(max(1, int(direct_prior.shape[0]))) / 2.0)))),
        neighbor_scale=float(np.clip(0.20 + 0.35 * float(np.clip(single_view_scale, 0.0, 1.0)), 0.20, 0.55)),
    )
    merged = np.maximum(_normalize_edge_prior(direct_prior), lattice_prior).astype(np.float32)
    merged = _normalize_edge_prior(merged)
    pre_final_edges = int(np.count_nonzero(merged > 0.0))
    final_top_k = 0 if int(top_k) <= 0 else max(int(top_k), int(math.ceil(float(top_k) * 1.5)))
    final_group_top_k = 0 if int(group_top_k) <= 0 else max(int(group_top_k), int(math.ceil(float(group_top_k) * 1.5)))
    merged = _cap_edges_by_endpoint_and_group(
        merged,
        final_top_k,
        feature_group_ids,
        group_top_k=final_group_top_k,
    )
    global_budget = 0
    if float(global_budget_multiplier) > 0.0:
        global_budget = max(1, int(round(float(global_budget_multiplier) * int(merged.shape[0]))))
        merged = _cap_edges_by_global_budget(merged, global_budget)

    final_mask = merged > 0.0
    family_names = [str(name) for name in direct_diag.get("family_names", ["structural", "dynamic", "task"])]
    raw_family = direct_diag.get("family_prior_matrices")
    family_prior_matrices: list[np.ndarray] = []
    if raw_family is not None:
        raw_family_arr = np.asarray(raw_family, dtype=np.float32)
        if raw_family_arr.ndim == 3 and raw_family_arr.shape[1:] == merged.shape:
            for idx in range(int(raw_family_arr.shape[0])):
                family_prior_matrices.append(_normalize_edge_prior(np.where(final_mask, raw_family_arr[idx], 0.0)))
    if not family_prior_matrices:
        family_names = ["direct_universe"]
        family_prior_matrices = [_normalize_edge_prior(np.where(final_mask, direct_prior, 0.0))]
    lattice_family = _normalize_edge_prior(np.where(final_mask, lattice_prior, 0.0))
    family_names = [*family_names, "group_lattice"]
    family_prior_matrices.append(lattice_family)

    direct_mask = _normalize_edge_prior(direct_prior) > 0.0
    lattice_mask = lattice_prior > 0.0
    return merged, {
        "enabled": bool(np.any(final_mask)),
        "status": "ok" if np.any(final_mask) else "empty_after_final_cap",
        "direct_edges": int(np.count_nonzero(direct_mask)),
        "lattice_edges": int(np.count_nonzero(lattice_mask)),
        "expanded_only_edges": int(np.count_nonzero(lattice_mask & ~direct_mask)),
        "pre_final_edges": int(pre_final_edges),
        "final_edges": int(np.count_nonzero(final_mask)),
        "final_top_k": int(final_top_k),
        "final_group_top_k": int(final_group_top_k),
        "global_budget_multiplier": float(max(0.0, global_budget_multiplier)),
        "global_budget": int(global_budget),
        "pool_multiplier": float(max(1.0, pool_multiplier)),
        "min_score": float(np.clip(min_score, 0.0, 1.0)),
        "min_votes": int(max(1, min_votes)),
        "single_view_scale": float(np.clip(single_view_scale, 0.0, 1.0)),
        "vote_boost": float(max(0.0, vote_boost)),
        "rank_weight": float(np.clip(rank_weight, 0.0, 1.0)),
        "group_lattice": lattice_diag,
        "direct_universe": {key: value for key, value in direct_diag.items() if key not in {"selected_masks", "family_prior_matrices"}},
        "family_names": family_names,
        "family_density": {
            str(name): float(np.mean(matrix > 0.0)) if matrix.size else 0.0
            for name, matrix in zip(family_names, family_prior_matrices)
        },
        "family_prior_matrices": np.stack(family_prior_matrices, axis=0).astype(np.float32),
        "top_edge_indices": _top_edge_records(merged, limit=20),
    }


def _overlay_edge_prior_without_replacement(
    base_prior: np.ndarray,
    overlay_prior: np.ndarray,
    feature_group_ids: np.ndarray,
    *,
    top_k: int,
    group_top_k: int,
    overlay_scale: float = 0.35,
    overlay_budget_multiplier: float = 1.0,
) -> tuple[np.ndarray, dict[str, Any]]:
    base = _normalize_edge_prior(base_prior)
    overlay = _normalize_edge_prior(overlay_prior)
    if base.ndim != 2 or overlay.ndim != 2 or base.shape != overlay.shape or base.shape[0] != base.shape[1]:
        return base, {"enabled": False, "status": "shape_mismatch"}
    n_features = int(base.shape[0])
    groups = np.asarray(feature_group_ids, dtype=np.int64).reshape(-1)
    if len(groups) != n_features:
        groups = np.arange(n_features, dtype=np.int64)

    merged = base.copy()
    base_mask = merged > 0.0
    target_counts = np.count_nonzero(base_mask, axis=1).astype(np.int64)
    source_counts = np.count_nonzero(base_mask, axis=0).astype(np.int64)
    base_top_k = int(top_k)
    target_limit = 0
    if base_top_k > 0:
        target_limit = max(base_top_k, int(math.ceil(float(base_top_k) * 1.25)))
    base_group_k = int(group_top_k)
    group_limit = 0
    if base_group_k > 0:
        group_limit = max(base_group_k, int(math.ceil(float(base_group_k) * 1.25)))
    incoming_groups: dict[int, set[int]] = {}
    outgoing_groups: dict[int, set[int]] = {}
    for target_idx, source_idx in np.argwhere(base_mask):
        target_group = int(groups[int(target_idx)])
        source_group = int(groups[int(source_idx)])
        incoming_groups.setdefault(target_group, set()).add(source_group)
        outgoing_groups.setdefault(source_group, set()).add(target_group)

    scale = float(np.clip(overlay_scale, 0.0, 1.0))
    extra_budget = max(1, int(round(max(0.0, float(overlay_budget_multiplier)) * n_features)))
    overlay_only = np.where(base_mask, 0.0, overlay).astype(np.float32)
    added = 0
    rejected_endpoint = 0
    rejected_group = 0
    flat = overlay_only.reshape(-1)
    for flat_idx in np.argsort(-flat):
        score = float(flat[int(flat_idx)])
        if score <= 0.0 or added >= extra_budget:
            break
        target_idx = int(flat_idx // n_features)
        source_idx = int(flat_idx % n_features)
        if target_idx == source_idx:
            continue
        if target_limit > 0 and (int(target_counts[target_idx]) >= target_limit or int(source_counts[source_idx]) >= target_limit):
            rejected_endpoint += 1
            continue
        target_group = int(groups[target_idx])
        source_group = int(groups[source_idx])
        target_sources = incoming_groups.setdefault(target_group, set())
        source_targets = outgoing_groups.setdefault(source_group, set())
        if group_limit > 0:
            if source_group not in target_sources and len(target_sources) >= group_limit:
                rejected_group += 1
                continue
            if target_group not in source_targets and len(source_targets) >= group_limit:
                rejected_group += 1
                continue
        merged[target_idx, source_idx] = scale * score
        target_counts[target_idx] += 1
        source_counts[source_idx] += 1
        target_sources.add(source_group)
        source_targets.add(target_group)
        added += 1

    merged = _normalize_edge_prior(merged)
    return merged, {
        "enabled": True,
        "status": "ok",
        "base_edges": int(np.count_nonzero(base > 0.0)),
        "overlay_edges": int(np.count_nonzero(overlay > 0.0)),
        "added_overlay_edges": int(added),
        "rejected_endpoint_edges": int(rejected_endpoint),
        "rejected_group_edges": int(rejected_group),
        "overlay_scale": float(scale),
        "overlay_budget_multiplier": float(max(0.0, overlay_budget_multiplier)),
        "overlay_budget": int(extra_budget),
        "target_limit": int(target_limit),
        "group_limit": int(group_limit),
        "final_edges": int(np.count_nonzero(merged > 0.0)),
        "top_edge_indices": _top_edge_records(merged, limit=20),
    }


def compute_train_algorithmic_edge_prior(
    x_train: np.ndarray,
    y_train: np.ndarray,
    feature_group_ids: np.ndarray,
    *,
    n_classes: int | None = None,
    mode: str = "none",
    top_k: int = 0,
    group_top_k: int = 0,
    max_lag: int = 3,
    class_weight: float = 0.25,
    lag_weight: float = 0.45,
    corr_weight: float = 0.30,
    residual_weight: float = 0.30,
    response_weight: float = 0.25,
    stability_weight: float = 0.20,
    bank_min_votes: int = 2,
    bank_single_view_scale: float = 0.55,
    bank_vote_boost: float = 0.15,
    bank_global_budget_multiplier: float = 0.0,
    pool_multiplier: float = 2.0,
    pool_min_score: float = 0.0,
    pool_rank_weight: float = 0.35,
) -> tuple[np.ndarray | None, dict[str, Any]]:
    x = np.asarray(x_train, dtype=np.float32)
    y = np.asarray(y_train, dtype=np.int64).reshape(-1)
    n_features = int(x.shape[2]) if x.ndim == 3 else 0
    name = str(mode or "none").strip().lower()
    if name == "bank":
        name = "edge_bank"
    if name == "certified_edge_pool":
        name = "edge_cert_pool"
    edge_canvas_modes = {
        "edge_canvas",
        "edge_universe",
        "edge_sieve",
        "edge_overlay",
        "edge_lattice",
        "edge_dual_lattice",
        "edge_guarded_lattice",
        "edge_cert_pool",
    }
    broad_modes = {"multiview", "edge_bank", "edge_pool", "edge_cert_overlay", *edge_canvas_modes}
    fused_modes = {"hybrid", *broad_modes}
    if name not in {"none", "correlation", "lag", "class", "hybrid", "multiview", "edge_bank", "edge_pool", "edge_canvas", "edge_universe", "edge_sieve", "edge_overlay", "edge_lattice", "edge_dual_lattice", "edge_guarded_lattice", "edge_cert_pool", "edge_cert_overlay"}:
        name = "none"
    if name == "none":
        return None, {"enabled": False, "mode": "none", "matched_edges": 0}
    if x.ndim != 3 or x.shape[0] < 3 or n_features < 2 or len(y) != x.shape[0]:
        return None, {"enabled": False, "mode": name, "status": "invalid_input", "matched_edges": 0}

    components: dict[str, np.ndarray] = {}
    weights: dict[str, float] = {}
    if name in {"correlation", *fused_modes}:
        corr_component = _descriptor_edge_matrix(x, extended=name in broad_modes)
        if float(np.max(corr_component)) > 0.0:
            components["correlation"] = corr_component
            weights["correlation"] = float(corr_weight) if name in fused_modes else 1.0

    lag_limit = max(0, min(int(max_lag), int(x.shape[1]) - 1))
    if name in {"lag", *fused_modes} and lag_limit > 0:
        lag_component = _lagged_dependency_edge_matrix(x, max_lag=lag_limit)
        if float(np.max(lag_component)) > 0.0:
            components["lag"] = lag_component
            weights["lag"] = float(lag_weight) if name in fused_modes else 1.0
        if name in edge_canvas_modes:
            directed_lag_component = _directed_lag_asymmetry_edge_matrix(x, max_lag=lag_limit)
            if float(np.max(directed_lag_component)) > 0.0:
                components["directed_lag"] = directed_lag_component
                weights["directed_lag"] = 0.75 * float(lag_weight)
            innovation_component = _innovation_dependency_edge_matrix(x, max_lag=lag_limit)
            if float(np.max(innovation_component)) > 0.0:
                components["innovation"] = innovation_component
                weights["innovation"] = 0.65 * float(lag_weight)

    if name in {"class", *fused_modes}:
        inferred_classes = int(n_classes) if n_classes is not None else (int(np.max(y)) + 1 if len(y) else 0)
        groups = np.asarray(feature_group_ids, dtype=np.int64).reshape(-1)
        if len(groups) != n_features:
            groups = np.arange(n_features, dtype=np.int64)
        class_evidence, class_diag = compute_train_class_path_evidence(
            x,
            y,
            groups,
            n_classes=inferred_classes,
            top_k=0,
            mode="static",
        )
        class_component = _normalize_edge_prior(np.max(class_evidence, axis=0) if class_evidence is not None and class_evidence.size else np.zeros((n_features, n_features), dtype=np.float32))
        if float(np.max(class_component)) > 0.0:
            components["class"] = class_component
            weights["class"] = float(class_weight) if name in fused_modes else 1.0
        if name in edge_canvas_modes and lag_limit > 0:
            class_lag_component = _class_lag_dependency_edge_matrix(
                x,
                y,
                max_lag=lag_limit,
                n_classes=inferred_classes,
            )
            if float(np.max(class_lag_component)) > 0.0:
                components["class_lag"] = class_lag_component
                weights["class_lag"] = 0.50 * float(lag_weight) + 0.50 * float(class_weight)
    else:
        class_diag = {"enabled": False}

    if name in broad_modes:
        descriptor_rows = [
            x[:, -1, :],
            np.mean(x, axis=1),
            x[:, -1, :] - x[:, 0, :],
            np.std(x, axis=1),
            _window_slope_descriptor(x),
        ]
        residual_component = _partial_residual_edge_matrix(np.concatenate(descriptor_rows, axis=0))
        if float(np.max(residual_component)) > 0.0:
            components["residual"] = residual_component
            weights["residual"] = float(residual_weight)
        response_component = _fault_response_edge_matrix(x, y, n_classes=int(n_classes) if n_classes is not None else None)
        if float(np.max(response_component)) > 0.0:
            components["fault_response"] = response_component
            weights["fault_response"] = float(response_weight)
        stability_component = _stable_edge_vote_matrix(
            x,
            y,
            max_lag=lag_limit,
            top_k=int(top_k),
            n_classes=int(n_classes) if n_classes is not None else None,
        )
        if float(np.max(stability_component)) > 0.0:
            components["stability"] = stability_component
            weights["stability"] = float(stability_weight)

    if not components:
        return None, {
            "enabled": False,
            "mode": name,
            "status": "empty_components",
            "max_lag": int(lag_limit),
            "matched_edges": 0,
        }

    selected_weights = {key: max(0.0, float(weights.get(key, 0.0))) for key in components}
    total_weight = float(sum(selected_weights.values()))
    if total_weight <= 1.0e-12:
        selected_weights = {key: 1.0 for key in components}
        total_weight = float(len(selected_weights))
    edge_bank_diagnostics: dict[str, Any] = {"enabled": False}
    edge_pool_diagnostics: dict[str, Any] = {"enabled": False}
    edge_canvas_diagnostics: dict[str, Any] = {"enabled": False}
    edge_universe_diagnostics: dict[str, Any] = {"enabled": False}
    edge_sieve_diagnostics: dict[str, Any] = {"enabled": False}
    edge_overlay_diagnostics: dict[str, Any] = {"enabled": False}
    edge_lattice_diagnostics: dict[str, Any] = {"enabled": False}
    edge_dual_lattice_diagnostics: dict[str, Any] = {"enabled": False}
    edge_guarded_lattice_diagnostics: dict[str, Any] = {"enabled": False}
    edge_cert_pool_diagnostics: dict[str, Any] = {"enabled": False}
    edge_cert_overlay_diagnostics: dict[str, Any] = {"enabled": False}
    edge_family_prior_matrices: np.ndarray | None = None
    path_candidate_prior_matrix: np.ndarray | None = None
    edge_family_prior_names: list[str] = []
    if name == "edge_bank":
        prior, edge_bank_diagnostics = _component_edge_bank_prior(
            components,
            selected_weights,
            feature_group_ids,
            top_k=int(top_k),
            group_top_k=int(group_top_k),
            min_votes=int(bank_min_votes),
            single_view_scale=float(bank_single_view_scale),
            vote_boost=float(bank_vote_boost),
            global_budget_multiplier=float(bank_global_budget_multiplier),
        )
        uncapped_edges = int(edge_bank_diagnostics.get("pre_final_edges", np.count_nonzero(prior > 0.0)))
    elif name == "edge_pool":
        prior, edge_pool_diagnostics = _component_edge_pool_prior(
            components,
            selected_weights,
            feature_group_ids,
            top_k=int(top_k),
            group_top_k=int(group_top_k),
            pool_multiplier=float(pool_multiplier),
            min_score=float(pool_min_score),
            min_votes=int(bank_min_votes),
            single_view_scale=float(bank_single_view_scale),
            vote_boost=float(bank_vote_boost),
            rank_weight=float(pool_rank_weight),
            global_budget_multiplier=float(bank_global_budget_multiplier),
        )
        uncapped_edges = int(edge_pool_diagnostics.get("pre_final_edges", np.count_nonzero(prior > 0.0)))
        raw_family_priors = edge_pool_diagnostics.get("family_prior_matrices")
        if raw_family_priors is not None:
            edge_family_prior_matrices = np.asarray(raw_family_priors, dtype=np.float32)
        edge_family_prior_names = [str(name) for name in edge_pool_diagnostics.get("family_names", [])]
    elif name == "edge_cert_pool":
        prior, edge_cert_pool_diagnostics = _component_edge_cert_pool_prior(
            components,
            selected_weights,
            feature_group_ids,
            top_k=int(top_k),
            group_top_k=int(group_top_k),
            pool_multiplier=float(pool_multiplier),
            min_score=float(pool_min_score),
            min_votes=int(bank_min_votes),
            single_view_scale=float(bank_single_view_scale),
            vote_boost=float(bank_vote_boost),
            rank_weight=float(pool_rank_weight),
            global_budget_multiplier=float(bank_global_budget_multiplier),
        )
        uncapped_edges = int(edge_cert_pool_diagnostics.get("pre_final_edges", np.count_nonzero(prior > 0.0)))
        raw_family_priors = edge_cert_pool_diagnostics.get("family_prior_matrices")
        if raw_family_priors is not None:
            edge_family_prior_matrices = np.asarray(raw_family_priors, dtype=np.float32)
        edge_family_prior_names = [str(name) for name in edge_cert_pool_diagnostics.get("family_names", [])]
    elif name == "edge_cert_overlay":
        base_prior, edge_pool_diagnostics = _component_edge_pool_prior(
            components,
            selected_weights,
            feature_group_ids,
            top_k=int(top_k),
            group_top_k=int(group_top_k),
            pool_multiplier=float(pool_multiplier),
            min_score=float(pool_min_score),
            min_votes=int(bank_min_votes),
            single_view_scale=float(bank_single_view_scale),
            vote_boost=float(bank_vote_boost),
            rank_weight=float(pool_rank_weight),
            global_budget_multiplier=float(bank_global_budget_multiplier),
        )
        cert_prior, edge_cert_pool_diagnostics = _component_edge_cert_pool_prior(
            components,
            selected_weights,
            feature_group_ids,
            top_k=int(top_k),
            group_top_k=int(group_top_k),
            pool_multiplier=float(pool_multiplier),
            min_score=float(pool_min_score),
            min_votes=int(bank_min_votes),
            single_view_scale=float(bank_single_view_scale),
            vote_boost=float(bank_vote_boost),
            rank_weight=float(pool_rank_weight),
            global_budget_multiplier=float(bank_global_budget_multiplier),
        )
        candidate_prior, edge_cert_overlay_diagnostics = _overlay_edge_prior_without_replacement(
            base_prior,
            cert_prior,
            feature_group_ids,
            top_k=int(top_k),
            group_top_k=int(group_top_k),
            overlay_scale=max(0.15, min(0.35, float(bank_single_view_scale))),
            overlay_budget_multiplier=0.50,
        )
        prior = _normalize_edge_prior(base_prior)
        path_candidate_prior_matrix = _normalize_edge_prior(candidate_prior)
        edge_cert_overlay_diagnostics["graph_edges"] = int(np.count_nonzero(prior > 0.0))
        edge_cert_overlay_diagnostics["path_candidate_edges"] = int(np.count_nonzero(path_candidate_prior_matrix > 0.0))
        edge_cert_overlay_diagnostics["graph_uses_base_prior"] = True
        uncapped_edges = int(edge_cert_overlay_diagnostics.get("base_edges", np.count_nonzero(prior > 0.0)))
        pool_family = edge_pool_diagnostics.get("family_prior_matrices")
        cert_family = edge_cert_pool_diagnostics.get("family_prior_matrices")
        if pool_family is not None and cert_family is not None:
            pool_family_arr = np.asarray(pool_family, dtype=np.float32)
            cert_family_arr = np.asarray(cert_family, dtype=np.float32)
            if pool_family_arr.shape == cert_family_arr.shape:
                merged_family = np.maximum(pool_family_arr, 0.30 * cert_family_arr).astype(np.float32)
                edge_family_prior_matrices = np.stack(
                    [_normalize_edge_prior(merged_family[idx]) for idx in range(int(merged_family.shape[0]))],
                    axis=0,
                ).astype(np.float32)
        if edge_family_prior_matrices is None and pool_family is not None:
            edge_family_prior_matrices = np.asarray(pool_family, dtype=np.float32)
        edge_family_prior_names = [str(name) for name in edge_pool_diagnostics.get("family_names", ["structural", "dynamic", "task"])]
    elif name == "edge_canvas":
        prior, edge_canvas_diagnostics = _component_edge_canvas_prior(
            components,
            selected_weights,
            feature_group_ids,
            top_k=int(top_k),
            group_top_k=int(group_top_k),
            pool_multiplier=float(pool_multiplier),
            min_score=float(pool_min_score),
            min_votes=int(bank_min_votes),
            single_view_scale=float(bank_single_view_scale),
            vote_boost=float(bank_vote_boost),
            rank_weight=float(pool_rank_weight),
            global_budget_multiplier=float(bank_global_budget_multiplier),
        )
        uncapped_edges = int(edge_canvas_diagnostics.get("pre_final_edges", np.count_nonzero(prior > 0.0)))
        raw_family_priors = edge_canvas_diagnostics.get("family_prior_matrices")
        if raw_family_priors is not None:
            edge_family_prior_matrices = np.asarray(raw_family_priors, dtype=np.float32)
        edge_family_prior_names = [str(name) for name in edge_canvas_diagnostics.get("family_names", [])]
    elif name == "edge_universe":
        prior, edge_universe_diagnostics = _component_edge_universe_prior(
            components,
            selected_weights,
            feature_group_ids,
            top_k=int(top_k),
            group_top_k=int(group_top_k),
            pool_multiplier=float(pool_multiplier),
            min_score=float(pool_min_score),
            min_votes=int(bank_min_votes),
            single_view_scale=float(bank_single_view_scale),
            vote_boost=float(bank_vote_boost),
            rank_weight=float(pool_rank_weight),
            global_budget_multiplier=float(bank_global_budget_multiplier),
        )
        uncapped_edges = int(edge_universe_diagnostics.get("pre_final_edges", np.count_nonzero(prior > 0.0)))
        raw_family_priors = edge_universe_diagnostics.get("family_prior_matrices")
        if raw_family_priors is not None:
            edge_family_prior_matrices = np.asarray(raw_family_priors, dtype=np.float32)
        edge_family_prior_names = [str(name) for name in edge_universe_diagnostics.get("family_names", [])]
    elif name == "edge_sieve":
        prior, edge_sieve_diagnostics = _component_edge_sieve_prior(
            components,
            selected_weights,
            feature_group_ids,
            top_k=int(top_k),
            group_top_k=int(group_top_k),
            pool_multiplier=float(pool_multiplier),
            min_score=float(pool_min_score),
            min_votes=int(bank_min_votes),
            single_view_scale=float(bank_single_view_scale),
            vote_boost=float(bank_vote_boost),
            rank_weight=float(pool_rank_weight),
            global_budget_multiplier=float(bank_global_budget_multiplier),
        )
        uncapped_edges = int(edge_sieve_diagnostics.get("pre_final_edges", np.count_nonzero(prior > 0.0)))
        raw_family_priors = edge_sieve_diagnostics.get("family_prior_matrices")
        if raw_family_priors is not None:
            edge_family_prior_matrices = np.asarray(raw_family_priors, dtype=np.float32)
        edge_family_prior_names = [str(name) for name in edge_sieve_diagnostics.get("family_names", [])]
    elif name == "edge_lattice":
        prior, edge_lattice_diagnostics = _component_edge_lattice_prior(
            components,
            selected_weights,
            feature_group_ids,
            top_k=int(top_k),
            group_top_k=int(group_top_k),
            pool_multiplier=float(pool_multiplier),
            min_score=float(pool_min_score),
            min_votes=int(bank_min_votes),
            single_view_scale=float(bank_single_view_scale),
            vote_boost=float(bank_vote_boost),
            rank_weight=float(pool_rank_weight),
            global_budget_multiplier=float(bank_global_budget_multiplier),
        )
        uncapped_edges = int(edge_lattice_diagnostics.get("pre_final_edges", np.count_nonzero(prior > 0.0)))
        raw_family_priors = edge_lattice_diagnostics.get("family_prior_matrices")
        if raw_family_priors is not None:
            edge_family_prior_matrices = np.asarray(raw_family_priors, dtype=np.float32)
        edge_family_prior_names = [str(name) for name in edge_lattice_diagnostics.get("family_names", [])]
    elif name == "edge_dual_lattice":
        core_prior, edge_pool_diagnostics = _component_edge_pool_prior(
            components,
            selected_weights,
            feature_group_ids,
            top_k=int(top_k),
            group_top_k=int(group_top_k),
            pool_multiplier=float(pool_multiplier),
            min_score=float(pool_min_score),
            min_votes=int(bank_min_votes),
            single_view_scale=float(bank_single_view_scale),
            vote_boost=float(bank_vote_boost),
            rank_weight=float(pool_rank_weight),
            global_budget_multiplier=float(bank_global_budget_multiplier),
        )
        exploratory_prior, edge_lattice_diagnostics = _component_edge_lattice_prior(
            components,
            selected_weights,
            feature_group_ids,
            top_k=int(top_k),
            group_top_k=int(group_top_k),
            pool_multiplier=max(1.0, float(pool_multiplier)),
            min_score=float(pool_min_score),
            min_votes=int(bank_min_votes),
            single_view_scale=float(bank_single_view_scale),
            vote_boost=float(bank_vote_boost),
            rank_weight=float(pool_rank_weight),
            global_budget_multiplier=0.0,
        )
        prior = _normalize_edge_prior(core_prior)
        if not np.any(prior > 0.0) and np.any(exploratory_prior > 0.0):
            prior = _cap_edges_by_endpoint_and_group(
                exploratory_prior,
                int(top_k),
                feature_group_ids,
                group_top_k=int(group_top_k),
            )
            if float(bank_global_budget_multiplier) > 0.0:
                prior = _cap_edges_by_global_budget(
                    prior,
                    max(1, int(round(float(bank_global_budget_multiplier) * int(prior.shape[0])))),
                )
            prior = _normalize_edge_prior(prior)
        path_candidate_prior_matrix = _normalize_edge_prior(
            np.maximum(prior, np.asarray(exploratory_prior, dtype=np.float32))
        )
        core_mask = prior > 0.0
        candidate_mask = path_candidate_prior_matrix > 0.0
        edge_dual_lattice_diagnostics = {
            "enabled": bool(np.any(core_mask) or np.any(candidate_mask)),
            "status": "ok" if np.any(core_mask) or np.any(candidate_mask) else "empty_after_dual_lattice",
            "graph_uses_core_prior": bool(np.any(core_mask)),
            "core_edges": int(np.count_nonzero(core_mask)),
            "exploratory_edges": int(np.count_nonzero(np.asarray(exploratory_prior) > 0.0)),
            "path_candidate_edges": int(np.count_nonzero(candidate_mask)),
            "expanded_candidate_edges": int(np.count_nonzero(candidate_mask & ~core_mask)),
            "core_source": "edge_pool" if bool(edge_pool_diagnostics.get("enabled", False)) else "lattice_fallback",
            "exploratory_source": "edge_lattice",
            "top_edge_indices": _top_edge_records(path_candidate_prior_matrix, limit=20),
        }
        uncapped_edges = int(edge_pool_diagnostics.get("pre_final_edges", np.count_nonzero(prior > 0.0)))
        raw_family_priors = edge_lattice_diagnostics.get("family_prior_matrices")
        if raw_family_priors is not None:
            edge_family_prior_matrices = np.asarray(raw_family_priors, dtype=np.float32)
        else:
            pool_family = edge_pool_diagnostics.get("family_prior_matrices")
            if pool_family is not None:
                edge_family_prior_matrices = np.asarray(pool_family, dtype=np.float32)
        edge_family_prior_names = [
            str(name)
            for name in edge_lattice_diagnostics.get(
                "family_names",
                edge_pool_diagnostics.get("family_names", ["structural", "dynamic", "task"]),
            )
        ]
    elif name == "edge_guarded_lattice":
        core_prior, edge_pool_diagnostics = _component_edge_pool_prior(
            components,
            selected_weights,
            feature_group_ids,
            top_k=int(top_k),
            group_top_k=int(group_top_k),
            pool_multiplier=float(pool_multiplier),
            min_score=float(pool_min_score),
            min_votes=int(bank_min_votes),
            single_view_scale=float(bank_single_view_scale),
            vote_boost=float(bank_vote_boost),
            rank_weight=float(pool_rank_weight),
            global_budget_multiplier=float(bank_global_budget_multiplier),
        )
        guarded_top_k = 0 if int(top_k) <= 0 else max(int(top_k), int(math.ceil(float(top_k) * 1.5)))
        guarded_group_top_k = (
            0
            if int(group_top_k) <= 0
            else max(int(group_top_k), int(math.ceil(float(group_top_k) * 1.5)))
        )
        guarded_prior, edge_sieve_diagnostics = _component_edge_sieve_prior(
            components,
            selected_weights,
            feature_group_ids,
            top_k=guarded_top_k,
            group_top_k=guarded_group_top_k,
            pool_multiplier=max(1.0, float(pool_multiplier)),
            min_score=float(pool_min_score),
            min_votes=max(2, int(bank_min_votes)),
            single_view_scale=float(bank_single_view_scale),
            vote_boost=float(bank_vote_boost),
            rank_weight=float(pool_rank_weight),
            global_budget_multiplier=0.0,
        )
        prior = _normalize_edge_prior(core_prior)
        if not np.any(prior > 0.0) and np.any(guarded_prior > 0.0):
            prior = _cap_edges_by_endpoint_and_group(
                guarded_prior,
                int(top_k),
                feature_group_ids,
                group_top_k=int(group_top_k),
            )
            if float(bank_global_budget_multiplier) > 0.0:
                prior = _cap_edges_by_global_budget(
                    prior,
                    max(1, int(round(float(bank_global_budget_multiplier) * int(prior.shape[0])))),
                )
            prior = _normalize_edge_prior(prior)
        path_candidate_prior_matrix = _normalize_edge_prior(
            np.maximum(prior, np.asarray(guarded_prior, dtype=np.float32))
        )
        core_mask = prior > 0.0
        guarded_mask = np.asarray(guarded_prior, dtype=np.float32) > 0.0
        candidate_mask = path_candidate_prior_matrix > 0.0
        edge_guarded_lattice_diagnostics = {
            "enabled": bool(np.any(core_mask) or np.any(candidate_mask)),
            "status": "ok" if np.any(core_mask) or np.any(candidate_mask) else "empty_after_guarded_lattice",
            "graph_uses_core_prior": bool(np.any(core_mask)),
            "core_edges": int(np.count_nonzero(core_mask)),
            "guarded_edges": int(np.count_nonzero(guarded_mask)),
            "path_candidate_edges": int(np.count_nonzero(candidate_mask)),
            "expanded_candidate_edges": int(np.count_nonzero(candidate_mask & ~core_mask)),
            "core_source": "edge_pool" if bool(edge_pool_diagnostics.get("enabled", False)) else "sieve_fallback",
            "guarded_source": "edge_sieve",
            "guarded_top_k": int(guarded_top_k),
            "guarded_group_top_k": int(guarded_group_top_k),
            "top_edge_indices": _top_edge_records(path_candidate_prior_matrix, limit=20),
        }
        uncapped_edges = int(edge_pool_diagnostics.get("pre_final_edges", np.count_nonzero(prior > 0.0)))
        raw_family_priors = edge_sieve_diagnostics.get("family_prior_matrices")
        if raw_family_priors is not None:
            edge_family_prior_matrices = np.asarray(raw_family_priors, dtype=np.float32)
        else:
            pool_family = edge_pool_diagnostics.get("family_prior_matrices")
            if pool_family is not None:
                edge_family_prior_matrices = np.asarray(pool_family, dtype=np.float32)
        edge_family_prior_names = [
            str(name)
            for name in edge_sieve_diagnostics.get(
                "family_names",
                edge_pool_diagnostics.get("family_names", ["structural", "dynamic", "task"]),
            )
        ]
    elif name == "edge_overlay":
        base_prior, edge_pool_diagnostics = _component_edge_pool_prior(
            components,
            selected_weights,
            feature_group_ids,
            top_k=int(top_k),
            group_top_k=int(group_top_k),
            pool_multiplier=float(pool_multiplier),
            min_score=float(pool_min_score),
            min_votes=int(bank_min_votes),
            single_view_scale=float(bank_single_view_scale),
            vote_boost=float(bank_vote_boost),
            rank_weight=float(pool_rank_weight),
            global_budget_multiplier=float(bank_global_budget_multiplier),
        )
        overlay_prior, edge_sieve_diagnostics = _component_edge_sieve_prior(
            components,
            selected_weights,
            feature_group_ids,
            top_k=int(top_k),
            group_top_k=int(group_top_k),
            pool_multiplier=float(pool_multiplier),
            min_score=float(pool_min_score),
            min_votes=int(bank_min_votes),
            single_view_scale=float(bank_single_view_scale),
            vote_boost=float(bank_vote_boost),
            rank_weight=float(pool_rank_weight),
            global_budget_multiplier=float(bank_global_budget_multiplier),
        )
        prior, edge_overlay_diagnostics = _overlay_edge_prior_without_replacement(
            base_prior,
            overlay_prior,
            feature_group_ids,
            top_k=int(top_k),
            group_top_k=int(group_top_k),
            overlay_scale=max(0.20, min(0.50, float(bank_single_view_scale))),
            overlay_budget_multiplier=1.0,
        )
        uncapped_edges = int(edge_overlay_diagnostics.get("final_edges", np.count_nonzero(prior > 0.0)))
        pool_family = edge_pool_diagnostics.get("family_prior_matrices")
        sieve_family = edge_sieve_diagnostics.get("family_prior_matrices")
        if pool_family is not None and sieve_family is not None:
            pool_family_arr = np.asarray(pool_family, dtype=np.float32)
            sieve_family_arr = np.asarray(sieve_family, dtype=np.float32)
            if pool_family_arr.shape == sieve_family_arr.shape:
                merged_family = np.maximum(pool_family_arr, 0.35 * sieve_family_arr).astype(np.float32)
                edge_family_prior_matrices = np.stack(
                    [_normalize_edge_prior(merged_family[idx]) for idx in range(int(merged_family.shape[0]))],
                    axis=0,
                ).astype(np.float32)
        if edge_family_prior_matrices is None and pool_family is not None:
            edge_family_prior_matrices = np.asarray(pool_family, dtype=np.float32)
        edge_family_prior_names = [str(name) for name in edge_pool_diagnostics.get("family_names", ["structural", "dynamic", "task"])]
    else:
        prior = np.zeros((n_features, n_features), dtype=np.float32)
        for key, component in components.items():
            prior += float(selected_weights[key] / total_weight) * np.asarray(component, dtype=np.float32)
        prior = _normalize_edge_prior(prior)
        uncapped_edges = int(np.count_nonzero(prior > 0.0))
        prior = _cap_edges_by_endpoint_and_group(prior, int(top_k), feature_group_ids, group_top_k=int(group_top_k))
    matched_edges = int(np.count_nonzero(prior > 0.0))
    group_pairs = 0
    groups = np.asarray(feature_group_ids, dtype=np.int64).reshape(-1)
    if len(groups) == n_features and matched_edges > 0:
        group_pair_set = {
            (int(groups[target_idx]), int(groups[source_idx]))
            for target_idx, source_idx in np.argwhere(prior > 0.0)
            if target_idx != source_idx
        }
        group_pairs = int(len(group_pair_set))
    return prior, {
        "enabled": bool(matched_edges > 0),
        "source": "train_only_algorithmic_edge_prior",
        "mode": name,
        "status": "ok" if matched_edges > 0 else "empty_after_top_k",
        "top_k": int(top_k),
        "group_top_k": int(group_top_k),
        "max_lag": int(lag_limit),
        "n_features": int(n_features),
        "components": list(components.keys()),
        "component_weights": {key: float(selected_weights[key] / total_weight) for key in components},
        "component_density": {key: float(np.mean(value > 0.0)) for key, value in components.items()},
        "component_top_edge_indices": {key: _top_edge_records(value, limit=8) for key, value in components.items()},
        "edge_bank": {key: value for key, value in edge_bank_diagnostics.items() if key != "selected_masks"},
        "edge_pool": {key: value for key, value in edge_pool_diagnostics.items() if key not in {"selected_masks", "family_prior_matrices"}},
        "edge_canvas": {key: value for key, value in edge_canvas_diagnostics.items() if key not in {"selected_masks", "family_prior_matrices"}},
        "edge_universe": {key: value for key, value in edge_universe_diagnostics.items() if key not in {"selected_masks", "family_prior_matrices"}},
        "edge_sieve": {key: value for key, value in edge_sieve_diagnostics.items() if key not in {"selected_masks", "family_prior_matrices"}},
        "edge_overlay": {key: value for key, value in edge_overlay_diagnostics.items() if key not in {"selected_masks", "family_prior_matrices"}},
        "edge_lattice": {key: value for key, value in edge_lattice_diagnostics.items() if key not in {"selected_masks", "family_prior_matrices"}},
        "edge_dual_lattice": {key: value for key, value in edge_dual_lattice_diagnostics.items() if key not in {"selected_masks", "family_prior_matrices"}},
        "edge_guarded_lattice": {key: value for key, value in edge_guarded_lattice_diagnostics.items() if key not in {"selected_masks", "family_prior_matrices"}},
        "edge_cert_pool": {key: value for key, value in edge_cert_pool_diagnostics.items() if key not in {"selected_masks", "family_prior_matrices"}},
        "edge_cert_overlay": {key: value for key, value in edge_cert_overlay_diagnostics.items() if key not in {"selected_masks", "family_prior_matrices"}},
        "edge_family_prior_names": edge_family_prior_names,
        "_edge_family_prior_matrices": edge_family_prior_matrices,
        "_path_candidate_prior_matrix": path_candidate_prior_matrix,
        "class_component_enabled": bool(class_diag.get("enabled", False)),
        "mean_prior": float(np.mean(prior)) if prior.size else 0.0,
        "max_prior": float(np.max(prior)) if prior.size else 0.0,
        "density": float(np.mean(prior > 0.0)) if prior.size else 0.0,
        "uncapped_edges": int(uncapped_edges),
        "matched_edges": int(matched_edges),
        "group_pair_count": int(group_pairs),
        "top_edge_indices": (
            edge_overlay_diagnostics.get("top_edge_indices", _top_edge_records(prior, limit=20))
            if name == "edge_overlay"
            else edge_bank_diagnostics.get(
                "top_edge_indices",
                edge_dual_lattice_diagnostics.get(
                    "top_edge_indices",
                    edge_guarded_lattice_diagnostics.get(
                        "top_edge_indices",
                        edge_pool_diagnostics.get(
                            "top_edge_indices",
                            edge_canvas_diagnostics.get(
                                "top_edge_indices",
                                edge_universe_diagnostics.get(
                                    "top_edge_indices",
                                    edge_sieve_diagnostics.get("top_edge_indices", _top_edge_records(prior, limit=20)),
                                ),
                            ),
                        ),
                    ),
                ),
            )
        ),
    }


def _data_support_for_external_edges(algorithmic_prior: np.ndarray) -> np.ndarray:
    alg = _normalize_edge_prior(algorithmic_prior)
    if alg.ndim != 2 or alg.shape[0] != alg.shape[1] or alg.size == 0:
        return alg
    incoming_strength = np.max(alg, axis=1, keepdims=True)
    outgoing_strength = np.max(alg, axis=0, keepdims=True)
    endpoint_support = np.sqrt(np.clip(incoming_strength @ outgoing_strength, 0.0, 1.0)).astype(np.float32)
    reverse_support = 0.50 * alg.T
    support = np.maximum.reduce([alg, endpoint_support * 0.60, reverse_support]).astype(np.float32)
    np.fill_diagonal(support, 0.0)
    return _normalize_edge_prior(support)


def _calibrate_external_edge_family_priors(
    external_family_priors: np.ndarray | None,
    external_family_names: Sequence[str] | None,
    algorithmic_prior: np.ndarray | None,
    *,
    floor: float = 0.15,
    min_support: float = 0.0,
) -> tuple[np.ndarray | None, list[str], dict[str, Any]]:
    if external_family_priors is None:
        return None, [], {"enabled": False, "status": "missing_external_families"}
    families = np.asarray(external_family_priors, dtype=np.float32)
    if families.ndim != 3 or families.shape[1] != families.shape[2]:
        return None, [], {"enabled": False, "status": "invalid_external_family_shape"}
    names = [str(name) for name in (external_family_names or [])]
    if len(names) != int(families.shape[0]):
        names = [f"external_{idx}" for idx in range(int(families.shape[0]))]
    data_support = (
        _data_support_for_external_edges(np.asarray(algorithmic_prior, dtype=np.float32))
        if algorithmic_prior is not None
        else np.zeros(families.shape[1:], dtype=np.float32)
    )
    support_floor = float(np.clip(floor, 0.0, 1.0))
    support_threshold = float(np.clip(min_support, 0.0, 1.0))
    calibrated: list[np.ndarray] = []
    kept_names: list[str] = []
    family_edges_before: dict[str, int] = {}
    family_edges: dict[str, int] = {}
    family_mean_support: dict[str, float] = {}
    family_retained_fraction: dict[str, float] = {}
    for idx, raw_family in enumerate(families):
        family = _normalize_edge_prior(raw_family)
        mask = family > 0.0
        if not bool(np.any(mask)):
            continue
        support = data_support if tuple(data_support.shape) == tuple(family.shape) else np.zeros_like(family)
        retained_mask = mask
        if support_threshold > 0.0:
            retained_mask = mask & (support >= support_threshold)
        if not bool(np.any(retained_mask)):
            name = names[idx]
            family_edges_before[name] = int(np.count_nonzero(mask))
            family_edges[name] = 0
            family_mean_support[name] = float(np.mean(support[mask])) if bool(np.any(mask)) else 0.0
            family_retained_fraction[name] = 0.0
            continue
        gate = support_floor + (1.0 - support_floor) * np.clip(support, 0.0, 1.0)
        calibrated_family = _normalize_edge_prior(np.where(retained_mask, family * gate, 0.0))
        if not bool(np.any(calibrated_family > 0.0)):
            continue
        name = names[idx]
        kept_names.append(name)
        calibrated.append(calibrated_family)
        family_edges_before[name] = int(np.count_nonzero(mask))
        family_edges[name] = int(np.count_nonzero(calibrated_family > 0.0))
        family_mean_support[name] = float(np.mean(support[mask])) if bool(np.any(mask)) else 0.0
        family_retained_fraction[name] = float(np.count_nonzero(retained_mask)) / max(1, int(np.count_nonzero(mask)))
    if not calibrated:
        return None, [], {"enabled": False, "status": "empty_after_external_family_calibration"}
    return np.stack(calibrated, axis=0).astype(np.float32), kept_names, {
        "enabled": True,
        "status": "ok",
        "floor": float(support_floor),
        "min_support": float(support_threshold),
        "family_edges_before": family_edges_before,
        "family_edges": family_edges,
        "family_mean_data_support": family_mean_support,
        "family_retained_fraction": family_retained_fraction,
        "mean_data_support": float(np.mean(data_support[data_support > 0.0])) if bool(np.any(data_support > 0.0)) else 0.0,
    }


def _clip_edge_prior_values(matrix: np.ndarray | None) -> np.ndarray | None:
    if matrix is None:
        return None
    arr = np.asarray(matrix, dtype=np.float32)
    if arr.ndim != 2 or arr.shape[0] != arr.shape[1] or arr.size == 0:
        return None
    arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
    arr = np.clip(arr, 0.0, 1.0).astype(np.float32)
    np.fill_diagonal(arr, 0.0)
    return arr


def _source_family_candidate_scale(
    name: str,
    *,
    expert_scale: float,
    llm_scale: float,
    default_scale: float,
) -> float:
    family = str(name or "").strip().lower()
    if "llm" in family or "language" in family or "gpt" in family:
        return float(np.clip(llm_scale, 0.0, 1.0))
    if "expert" in family or "physics" in family or "domain" in family or "rule" in family:
        return float(np.clip(expert_scale, 0.0, 1.0))
    return float(np.clip(default_scale, 0.0, 1.0))


def _aggregate_external_candidate_prior(
    external_family_priors: np.ndarray | None,
    external_family_names: Sequence[str] | None,
    *,
    expert_scale: float = 1.0,
    llm_scale: float = 0.70,
    default_scale: float = 0.85,
) -> tuple[np.ndarray | None, dict[str, Any]]:
    if external_family_priors is None:
        return None, {"enabled": False, "status": "missing_external_families"}
    families = np.asarray(external_family_priors, dtype=np.float32)
    if families.ndim != 3 or families.shape[1] != families.shape[2]:
        return None, {"enabled": False, "status": "invalid_external_family_shape"}
    names = [str(name) for name in (external_family_names or [])]
    if len(names) != int(families.shape[0]):
        names = [f"external_{idx}" for idx in range(int(families.shape[0]))]
    n_features = int(families.shape[1])
    combined = np.zeros((n_features, n_features), dtype=np.float32)
    family_scales: dict[str, float] = {}
    family_edges: dict[str, int] = {}
    for idx, raw_family in enumerate(families):
        family = _normalize_edge_prior(raw_family)
        if not bool(np.any(family > 0.0)):
            continue
        name = names[idx]
        scale = _source_family_candidate_scale(
            name,
            expert_scale=expert_scale,
            llm_scale=llm_scale,
            default_scale=default_scale,
        )
        scaled = np.clip(family * scale, 0.0, 1.0).astype(np.float32)
        combined = np.maximum(combined, scaled).astype(np.float32)
        family_scales[name] = float(scale)
        family_edges[name] = int(np.count_nonzero(scaled > 0.0))
    combined = _clip_edge_prior_values(combined)
    if combined is None or not bool(np.any(combined > 0.0)):
        return None, {
            "enabled": False,
            "status": "empty_after_external_candidate_aggregation",
            "family_scales": family_scales,
            "family_edges": family_edges,
        }
    return combined, {
        "enabled": True,
        "status": "ok",
        "family_names": names,
        "family_scales": family_scales,
        "family_edges": family_edges,
        "candidate_edge_count": int(np.count_nonzero(combined > 0.0)),
        "mean_candidate_prior": float(np.mean(combined[combined > 0.0])) if bool(np.any(combined > 0.0)) else 0.0,
        "top_edge_indices": _top_edge_records(combined, limit=20),
    }


def _resolve_external_candidate_scales(
    *,
    expert_scale: float,
    llm_scale: float,
    default_scale: float,
    disable_source_complexity_penalty: bool = False,
) -> tuple[float, float, float, dict[str, Any]]:
    requested = {
        "expert": float(np.clip(expert_scale, 0.0, 1.0)),
        "llm": float(np.clip(llm_scale, 0.0, 1.0)),
        "default": float(np.clip(default_scale, 0.0, 1.0)),
    }
    if bool(disable_source_complexity_penalty):
        effective = {"expert": 1.0, "llm": 1.0, "default": 1.0}
    else:
        effective = dict(requested)
    return effective["expert"], effective["llm"], effective["default"], {
        "enabled": not bool(disable_source_complexity_penalty),
        "disabled_for_ablation": bool(disable_source_complexity_penalty),
        "requested_scales": requested,
        "effective_scales": effective,
    }


def _parse_external_candidate_families(value: str | Sequence[str] | None) -> set[str]:
    if value is None:
        return {"expert", "llm"}
    if isinstance(value, str):
        raw_parts = value.replace(";", ",").split(",")
    else:
        raw_parts = [str(item) for item in value]
    families = {str(part).strip().lower() for part in raw_parts if str(part).strip()}
    if not families or "all" in families:
        return {"expert", "llm"}
    if "none" in families:
        return set()
    normalized: set[str] = set()
    for family in families:
        if "llm" in family or "language" in family or "gpt" in family:
            normalized.add("llm")
        elif "expert" in family or "physics" in family or "domain" in family or "rule" in family:
            normalized.add("expert")
        else:
            normalized.add(family)
    return normalized


def _split_external_family_priors(
    external_family_priors: np.ndarray | None,
    external_family_names: Sequence[str] | None,
    *,
    candidate_families: set[str],
) -> tuple[np.ndarray | None, list[str], np.ndarray | None, list[str], dict[str, Any]]:
    if external_family_priors is None:
        return None, [], None, [], {"enabled": False, "status": "missing_external_families"}
    families = np.asarray(external_family_priors, dtype=np.float32)
    if families.ndim != 3 or families.shape[1] != families.shape[2]:
        return None, [], None, [], {"enabled": False, "status": "invalid_external_family_shape"}
    names = [str(name) for name in (external_family_names or [])]
    if len(names) != int(families.shape[0]):
        names = [f"external_{idx}" for idx in range(int(families.shape[0]))]
    core_matrices: list[np.ndarray] = []
    core_names: list[str] = []
    candidate_matrices: list[np.ndarray] = []
    candidate_names: list[str] = []
    candidate_set = {str(name).strip().lower() for name in candidate_families}
    for idx, raw_family in enumerate(families):
        matrix = _normalize_edge_prior(raw_family)
        if not bool(np.any(matrix > 0.0)):
            continue
        name = names[idx]
        canonical = _parse_external_candidate_families([name])
        is_candidate = bool(canonical & candidate_set)
        if is_candidate:
            candidate_matrices.append(matrix)
            candidate_names.append(name)
        else:
            core_matrices.append(matrix)
            core_names.append(name)
    core = np.stack(core_matrices, axis=0).astype(np.float32) if core_matrices else None
    candidate = np.stack(candidate_matrices, axis=0).astype(np.float32) if candidate_matrices else None
    return core, core_names, candidate, candidate_names, {
        "enabled": True,
        "status": "ok",
        "candidate_families": sorted(candidate_set),
        "core_family_names": core_names,
        "candidate_family_names": candidate_names,
        "core_family_count": int(len(core_names)),
        "candidate_family_count": int(len(candidate_names)),
    }


def _mask_external_prior_by_family_support(
    external_prior: np.ndarray | None,
    core_family_priors: np.ndarray | None,
) -> np.ndarray | None:
    prior = _clip_edge_prior_values(external_prior)
    if prior is None or core_family_priors is None:
        return None
    families = np.asarray(core_family_priors, dtype=np.float32)
    if families.ndim != 3 or families.shape[1:] != prior.shape:
        return None
    support = np.max(families, axis=0) > 0.0
    core_prior = np.where(support, prior, 0.0).astype(np.float32)
    return _clip_edge_prior_values(core_prior)


def _merge_path_candidate_prior_matrices(
    base_candidate_prior: np.ndarray | None,
    external_candidate_prior: np.ndarray | None,
) -> tuple[np.ndarray | None, dict[str, Any]]:
    base = _clip_edge_prior_values(base_candidate_prior)
    external = _clip_edge_prior_values(external_candidate_prior)
    if base is None and external is None:
        return None, {"enabled": False, "status": "missing_candidate_priors"}
    if base is None:
        assert external is not None
        combined = external.copy()
    elif external is None:
        combined = base.copy()
    elif tuple(base.shape) != tuple(external.shape):
        return base, {
            "enabled": False,
            "status": "shape_mismatch",
            "base_candidate_edges": int(np.count_nonzero(base > 0.0)),
            "external_candidate_edges": int(np.count_nonzero(external > 0.0)),
        }
    else:
        combined = np.maximum(base, external).astype(np.float32)
    combined = _clip_edge_prior_values(combined)
    assert combined is not None
    return combined, {
        "enabled": True,
        "status": "ok",
        "base_candidate_edges": int(np.count_nonzero(base > 0.0)) if base is not None else 0,
        "external_candidate_edges": int(np.count_nonzero(external > 0.0)) if external is not None else 0,
        "combined_candidate_edges": int(np.count_nonzero(combined > 0.0)),
        "external_added_edges": int(
            np.count_nonzero((combined > 0.0) & ~(base > 0.0))
            if base is not None and external is not None
            else (np.count_nonzero(combined > 0.0) if base is None else 0)
        ),
        "top_edge_indices": _top_edge_records(combined, limit=20),
    }


def _class_scope_matches(scope: Any, class_label: Any, class_index: int) -> bool:
    if scope is None:
        return True
    if isinstance(scope, str):
        tokens = [item.strip().lower() for item in re.split(r"[,;/|]+", scope) if item.strip()]
    elif isinstance(scope, Sequence) and not isinstance(scope, (bytes, bytearray)):
        tokens = [str(item).strip().lower() for item in scope if str(item).strip()]
    else:
        tokens = [str(scope).strip().lower()]
    if not tokens:
        return True
    if any(token in {"all", "*", "any", "global", "default"} for token in tokens):
        return True
    label = str(class_label).strip().lower()
    idx = str(int(class_index)).strip().lower()
    candidates = {
        label,
        idx,
        f"class_{idx}",
        f"class_{label}",
        f"fault_{idx}",
        f"fault_{label}",
        f"label_{idx}",
        f"label_{label}",
    }
    return any(token in candidates for token in tokens)


def _condition_records_to_class_matrix(
    records: Sequence[Mapping[str, Any]] | None,
    *,
    feature_cols: Sequence[str],
    class_labels: Sequence[Any],
    activation: str,
) -> np.ndarray:
    n_classes = int(len(class_labels))
    n_features = int(len(feature_cols))
    matrix = np.zeros((n_classes, n_features, n_features), dtype=np.float32)
    if not records:
        return matrix
    feature_index = {str(feature): idx for idx, feature in enumerate(feature_cols)}
    expected_activation = str(activation)
    for record in records:
        if not isinstance(record, Mapping):
            continue
        record_activation = _llm_condition_activation(
            str(record.get("condition_activation", record.get("activation", record.get("decision", ""))))
        )
        if record_activation != expected_activation:
            continue
        source = str(record.get("source", "")).strip()
        target = str(record.get("target", "")).strip()
        if source not in feature_index or target not in feature_index or source == target:
            continue
        strength = _llm_condition_strength(record)
        if strength <= 0.0:
            continue
        src_idx = int(feature_index[source])
        tgt_idx = int(feature_index[target])
        scope = record.get("class_scope", "all")
        for class_idx, class_label in enumerate(class_labels):
            if _class_scope_matches(scope, class_label, class_idx):
                matrix[int(class_idx), tgt_idx, src_idx] = max(float(matrix[int(class_idx), tgt_idx, src_idx]), strength)
    return np.asarray(np.clip(matrix, 0.0, 1.0), dtype=np.float32)


def apply_llm_expert_condition_verifier_to_class_evidence(
    class_path_evidence: np.ndarray | None,
    *,
    condition_activate_matrix: np.ndarray | None,
    condition_suppress_matrix: np.ndarray | None,
    condition_records: Sequence[Mapping[str, Any]] | None,
    data_support_matrix: np.ndarray | None,
    feature_cols: Sequence[str],
    class_labels: Sequence[Any],
    weight: float = 0.50,
    min_data_support: float = 0.05,
    floor: float = 0.10,
) -> tuple[np.ndarray | None, dict[str, Any]]:
    n_classes = int(len(class_labels))
    n_features = int(len(feature_cols))
    if n_classes <= 0 or n_features <= 1:
        return class_path_evidence, {"enabled": False, "status": "invalid_shape"}
    activate = _condition_records_to_class_matrix(
        condition_records,
        feature_cols=feature_cols,
        class_labels=class_labels,
        activation="activate",
    )
    suppress = _condition_records_to_class_matrix(
        condition_records,
        feature_cols=feature_cols,
        class_labels=class_labels,
        activation="suppress",
    )
    global_activate = None if condition_activate_matrix is None else _normalize_edge_prior(condition_activate_matrix)
    global_suppress = None if condition_suppress_matrix is None else _normalize_edge_prior(condition_suppress_matrix)
    if not np.any(activate > 0.0) and global_activate is not None and tuple(global_activate.shape) == (n_features, n_features):
        activate = np.repeat(global_activate[None, :, :], n_classes, axis=0).astype(np.float32)
    if not np.any(suppress > 0.0) and global_suppress is not None and tuple(global_suppress.shape) == (n_features, n_features):
        suppress = np.repeat(global_suppress[None, :, :], n_classes, axis=0).astype(np.float32)
    if not np.any(activate > 0.0) and not np.any(suppress > 0.0):
        return class_path_evidence, {"enabled": False, "status": "empty_condition_verifier"}

    support = None if data_support_matrix is None else _normalize_edge_prior(data_support_matrix)
    if support is None or tuple(support.shape) != (n_features, n_features):
        if float(min_data_support) > 0.0:
            return class_path_evidence, {
                "enabled": False,
                "status": "missing_data_support",
                "condition_activate_edges": int(np.count_nonzero(activate > 0.0)),
                "condition_suppress_edges": int(np.count_nonzero(suppress > 0.0)),
            }
        support = np.ones((n_features, n_features), dtype=np.float32)
    support = np.asarray(np.clip(support, 0.0, 1.0), dtype=np.float32)
    support_mask = support >= float(min_data_support)
    if float(min_data_support) <= 0.0:
        support_mask = support_mask | ((np.max(activate, axis=0) > 0.0) | (np.max(suppress, axis=0) > 0.0))
    data_gate = np.where(support_mask, np.maximum(support, float(floor)), 0.0).astype(np.float32)

    if class_path_evidence is None:
        evidence = np.zeros((n_classes, n_features, n_features), dtype=np.float32)
    else:
        evidence = np.asarray(class_path_evidence, dtype=np.float32)
        if evidence.ndim != 3 or tuple(evidence.shape[1:]) != (n_features, n_features):
            return class_path_evidence, {"enabled": False, "status": "invalid_class_evidence_shape"}
        if int(evidence.shape[0]) != n_classes:
            return class_path_evidence, {"enabled": False, "status": "class_count_mismatch"}
        evidence = evidence.copy()

    activate_overlay = np.clip(activate * data_gate[None, :, :] * float(weight), 0.0, 1.0)
    suppress_gate = np.clip(suppress * data_gate[None, :, :] * float(weight), 0.0, 1.0)
    before_edges = int(np.count_nonzero(evidence > 0.0))
    evidence = np.maximum(evidence, activate_overlay).astype(np.float32)
    if np.any(suppress_gate > 0.0):
        evidence = (evidence * (1.0 - 0.50 * suppress_gate)).astype(np.float32)
    np.clip(evidence, 0.0, 1.0, out=evidence)
    return evidence, {
        "enabled": True,
        "status": "ok",
        "weight": float(weight),
        "min_data_support": float(min_data_support),
        "floor": float(floor),
        "condition_activate_edges": int(np.count_nonzero(np.max(activate, axis=0) > 0.0)),
        "condition_suppress_edges": int(np.count_nonzero(np.max(suppress, axis=0) > 0.0)),
        "data_supported_edges": int(np.count_nonzero(data_gate > 0.0)),
        "class_evidence_edges_before": int(before_edges),
        "class_evidence_edges_after": int(np.count_nonzero(evidence > 0.0)),
        "top_activate_edges": _top_edge_records(np.max(activate_overlay, axis=0), limit=20),
        "top_suppress_edges": _top_edge_records(np.max(suppress_gate, axis=0), limit=20),
    }


def apply_llm_expert_condition_verifier_to_candidate_prior(
    candidate_prior: np.ndarray | None,
    *,
    condition_activate_matrix: np.ndarray | None,
    condition_suppress_matrix: np.ndarray | None,
    condition_records: Sequence[Mapping[str, Any]] | None,
    data_support_matrix: np.ndarray | None,
    feature_cols: Sequence[str],
    class_labels: Sequence[Any],
    weight: float = 0.50,
    min_data_support: float = 0.05,
    floor: float = 0.10,
) -> tuple[np.ndarray | None, dict[str, Any]]:
    n_features = int(len(feature_cols))
    created_from_verifier = candidate_prior is None
    if candidate_prior is None:
        candidate = np.zeros((n_features, n_features), dtype=np.float32)
    else:
        candidate = np.asarray(candidate_prior, dtype=np.float32)
    if candidate.ndim != 2 or tuple(candidate.shape) != (n_features, n_features):
        return candidate_prior, {"enabled": False, "status": "invalid_candidate_prior_shape"}
    activate_class = _condition_records_to_class_matrix(
        condition_records,
        feature_cols=feature_cols,
        class_labels=class_labels,
        activation="activate",
    )
    suppress_class = _condition_records_to_class_matrix(
        condition_records,
        feature_cols=feature_cols,
        class_labels=class_labels,
        activation="suppress",
    )
    activate = np.max(activate_class, axis=0) if activate_class.size else np.zeros_like(candidate)
    suppress = np.max(suppress_class, axis=0) if suppress_class.size else np.zeros_like(candidate)
    if condition_activate_matrix is not None and tuple(np.asarray(condition_activate_matrix).shape) == (n_features, n_features):
        activate = np.maximum(activate, _normalize_edge_prior(np.asarray(condition_activate_matrix, dtype=np.float32)))
    if condition_suppress_matrix is not None and tuple(np.asarray(condition_suppress_matrix).shape) == (n_features, n_features):
        suppress = np.maximum(suppress, _normalize_edge_prior(np.asarray(condition_suppress_matrix, dtype=np.float32)))
    if not np.any(activate > 0.0) and not np.any(suppress > 0.0):
        return candidate_prior, {"enabled": False, "status": "empty_condition_verifier"}
    support = _normalize_edge_prior(candidate)
    if data_support_matrix is not None and tuple(np.asarray(data_support_matrix).shape) == (n_features, n_features):
        support = np.maximum(support, _normalize_edge_prior(np.asarray(data_support_matrix, dtype=np.float32)))
    support = np.asarray(np.clip(support, 0.0, 1.0), dtype=np.float32)
    existing_mask = candidate > 0.0
    verified_condition_mask = (activate > 0.0) | (suppress > 0.0)
    support_mask = support >= float(min_data_support)
    admissible = (existing_mask | verified_condition_mask) & support_mask
    if not np.any(admissible):
        return candidate_prior, {
            "enabled": False,
            "status": "no_data_supported_verified_expert_or_candidate_overlap",
            "condition_activate_edges": int(np.count_nonzero(activate > 0.0)),
            "condition_suppress_edges": int(np.count_nonzero(suppress > 0.0)),
            "candidate_edges": int(np.count_nonzero(existing_mask)),
            "created_from_verifier": bool(created_from_verifier),
            "data_supported_verified_condition_edges": int(np.count_nonzero(verified_condition_mask & support_mask)),
        }
    gate = np.where(admissible, np.maximum(support, float(floor)), 0.0).astype(np.float32)
    strength = float(np.clip(weight, 0.0, 1.0))
    activate_gate = np.clip(activate * gate * strength, 0.0, 1.0)
    suppress_gate = np.clip(suppress * gate * strength, 0.0, 1.0)
    adjusted = candidate.copy()
    adjusted = np.maximum(adjusted, adjusted + activate_gate * (1.0 - adjusted)).astype(np.float32)
    if np.any(suppress_gate > 0.0):
        adjusted = (adjusted * (1.0 - 0.50 * suppress_gate)).astype(np.float32)
    np.clip(adjusted, 0.0, 1.0, out=adjusted)
    changed = np.abs(adjusted - candidate) > 1.0e-8
    if not np.any(changed):
        return candidate_prior, {
            "enabled": False,
            "status": "no_effect_after_reliability_admission",
            "target": "candidate_gate",
            "weight": float(weight),
            "min_data_support": float(min_data_support),
            "floor": float(floor),
            "candidate_edges": int(np.count_nonzero(existing_mask)),
            "created_from_verifier": bool(created_from_verifier),
            "admissible_candidate_edges": int(np.count_nonzero(existing_mask & support_mask)),
            "data_supported_verified_condition_edges": int(np.count_nonzero(verified_condition_mask & support_mask)),
            "condition_activate_edges": int(np.count_nonzero(activate > 0.0)),
            "condition_suppress_edges": int(np.count_nonzero(suppress > 0.0)),
        }
    return adjusted, {
        "enabled": True,
        "status": "ok",
        "target": "candidate_gate",
        "weight": float(weight),
        "min_data_support": float(min_data_support),
        "floor": float(floor),
        "candidate_edges": int(np.count_nonzero(existing_mask)),
        "created_from_verifier": bool(created_from_verifier),
        "admissible_candidate_edges": int(np.count_nonzero(existing_mask & support_mask)),
        "data_supported_verified_condition_edges": int(np.count_nonzero(verified_condition_mask & support_mask)),
        "verified_expert_candidate_edges": int(np.count_nonzero((adjusted > 0.0) & ~existing_mask & (activate > 0.0))),
        "condition_activate_edges": int(np.count_nonzero(activate > 0.0)),
        "condition_suppress_edges": int(np.count_nonzero(suppress > 0.0)),
        "adjusted_edges": int(np.count_nonzero(changed)),
        "top_activate_edges": _top_edge_records(activate_gate, limit=20),
        "top_suppress_edges": _top_edge_records(suppress_gate, limit=20),
    }


def _merge_edge_family_prior_matrices(
    algorithmic_families: np.ndarray | None,
    algorithmic_family_names: Sequence[str] | None,
    external_families: np.ndarray | None,
    external_family_names: Sequence[str] | None,
) -> tuple[np.ndarray | None, list[str]]:
    matrices: list[np.ndarray] = []
    names: list[str] = []
    if algorithmic_families is not None:
        arr = np.asarray(algorithmic_families, dtype=np.float32)
        if arr.ndim == 3 and arr.shape[1] == arr.shape[2]:
            alg_names = [str(name) for name in (algorithmic_family_names or [])]
            if len(alg_names) != int(arr.shape[0]):
                alg_names = [f"data_{idx}" for idx in range(int(arr.shape[0]))]
            for idx in range(int(arr.shape[0])):
                matrix = _normalize_edge_prior(arr[idx])
                if bool(np.any(matrix > 0.0)):
                    matrices.append(matrix)
                    names.append(alg_names[idx])
    if external_families is not None:
        arr = np.asarray(external_families, dtype=np.float32)
        if arr.ndim == 3 and arr.shape[1] == arr.shape[2]:
            ext_names = [str(name) for name in (external_family_names or [])]
            if len(ext_names) != int(arr.shape[0]):
                ext_names = [f"external_{idx}" for idx in range(int(arr.shape[0]))]
            for idx in range(int(arr.shape[0])):
                matrix = _normalize_edge_prior(arr[idx])
                if bool(np.any(matrix > 0.0)):
                    matrices.append(matrix)
                    names.append(ext_names[idx])
    if not matrices:
        return None, []
    return np.stack(matrices, axis=0).astype(np.float32), names


def combine_algorithmic_and_external_priors(
    external_prior: np.ndarray | None,
    algorithmic_prior: np.ndarray | None,
    *,
    mode: str = "max",
    external_isolated_scale: float = 1.0,
    overlap_boost: float = 0.0,
    nonanchor_algorithmic_scale: float = 1.0,
) -> tuple[np.ndarray | None, dict[str, Any]]:
    name = str(mode or "max").strip().lower()
    if name in {"source_calibrated", "tri_source", "data_certified_external"}:
        name = "tri_source_calibrated"
    if name not in {"max", "corroborated_max", "anchored_subgraph", "tri_source_calibrated"}:
        name = "max"
    if algorithmic_prior is None:
        return external_prior, {"enabled": False, "mode": name, "status": "no_algorithmic_prior"}
    alg = np.asarray(algorithmic_prior, dtype=np.float32)
    if alg.ndim != 2 or alg.shape[0] != alg.shape[1]:
        return external_prior, {"enabled": False, "mode": name, "status": "invalid_algorithmic_prior"}
    if external_prior is None:
        return alg.copy(), {
            "enabled": True,
            "mode": name,
            "status": "algorithmic_only",
            "algorithmic_edges": int(np.count_nonzero(alg > 0.0)),
            "external_edges": 0,
            "overlap_edges": 0,
            "combined_edge_count": int(np.count_nonzero(alg > 0.0)),
        }
    ext = np.asarray(external_prior, dtype=np.float32)
    if ext.shape != alg.shape:
        return external_prior, {"enabled": False, "mode": name, "status": "shape_mismatch"}
    alg = np.nan_to_num(alg, nan=0.0, posinf=0.0, neginf=0.0)
    ext = np.nan_to_num(ext, nan=0.0, posinf=0.0, neginf=0.0)
    alg = np.maximum(alg, 0.0)
    ext = np.maximum(ext, 0.0)
    alg_mask = alg > 0.0
    ext_mask = ext > 0.0
    overlap = alg_mask & ext_mask
    if name == "max":
        combined = np.maximum(ext, alg)
        data_support = np.zeros_like(alg, dtype=np.float32)
    else:
        isolated_scale = float(np.clip(external_isolated_scale, 0.0, 1.0))
        boost = max(0.0, float(overlap_boost))
        data_support = _data_support_for_external_edges(alg)
        if name == "anchored_subgraph":
            anchor_nodes = np.flatnonzero(np.any(ext_mask, axis=0) | np.any(ext_mask, axis=1))
            anchor_edge_mask = np.zeros_like(alg_mask, dtype=bool)
            if anchor_nodes.size:
                anchor_edge_mask[:, anchor_nodes] = True
                anchor_edge_mask[anchor_nodes, :] = True
            background_scale = float(np.clip(nonanchor_algorithmic_scale, 0.0, 1.0))
            combined = alg * np.where(anchor_edge_mask, 1.0, background_scale).astype(np.float32)
        else:
            anchor_nodes = np.asarray([], dtype=np.int64)
            anchor_edge_mask = alg_mask
            background_scale = 1.0
            combined = alg.copy()
        if name == "tri_source_calibrated":
            anchor_nodes = np.flatnonzero(np.any(ext_mask, axis=0) | np.any(ext_mask, axis=1))
            anchor_edge_mask = alg_mask
            background_scale = 1.0
            unsupported_floor = 0.15
            external_gate = unsupported_floor + (1.0 - unsupported_floor) * np.clip(data_support, 0.0, 1.0)
            combined = alg.copy()
            external_scaled = ext * external_gate.astype(np.float32) * isolated_scale
            combined = np.maximum(combined, np.where(ext_mask, external_scaled, 0.0).astype(np.float32))
        else:
            combined[ext_mask & ~alg_mask] = ext[ext_mask & ~alg_mask] * isolated_scale
        overlap_values = np.maximum(alg[overlap], ext[overlap])
        if boost > 0.0 and overlap_values.size:
            overlap_values = np.clip(overlap_values + boost * np.minimum(alg[overlap], ext[overlap]), 0.0, 1.0)
        combined[overlap] = overlap_values
    if combined.shape[0] == combined.shape[1]:
        np.fill_diagonal(combined, 0.0)
    combined = np.asarray(np.clip(combined, 0.0, 1.0), dtype=np.float32)
    return combined, {
        "enabled": True,
        "mode": name,
        "status": "ok",
        "external_isolated_scale": float(np.clip(external_isolated_scale, 0.0, 1.0)),
        "overlap_boost": max(0.0, float(overlap_boost)),
        "nonanchor_algorithmic_scale": float(np.clip(nonanchor_algorithmic_scale, 0.0, 1.0)),
        "algorithmic_edges": int(np.count_nonzero(alg_mask)),
        "external_edges": int(np.count_nonzero(ext_mask)),
        "overlap_edges": int(np.count_nonzero(overlap)),
        "algorithmic_only_edges": int(np.count_nonzero(alg_mask & ~ext_mask)),
        "external_only_edges": int(np.count_nonzero(ext_mask & ~alg_mask)),
        "external_data_supported_edges": int(np.count_nonzero(ext_mask & (data_support >= 0.25))),
        "external_data_unsupported_edges": int(np.count_nonzero(ext_mask & (data_support < 0.25))),
        "mean_external_data_support": float(np.mean(data_support[ext_mask])) if bool(np.any(ext_mask)) else 0.0,
        "anchor_node_count": int(len(anchor_nodes)) if name == "anchored_subgraph" else 0,
        "anchor_algorithmic_edge_count": int(np.count_nonzero(alg_mask & anchor_edge_mask)) if name == "anchored_subgraph" else 0,
        "nonanchor_algorithmic_edge_count": int(np.count_nonzero(alg_mask & ~anchor_edge_mask)) if name == "anchored_subgraph" else 0,
        "combined_edge_count": int(np.count_nonzero(combined > 0.0)),
        "mean_combined_prior": float(np.mean(combined)) if combined.size else 0.0,
        "top_edge_indices": _top_edge_records(combined, limit=20),
    }


def _safe_abs_corr(a: np.ndarray, b: np.ndarray) -> float:
    left = np.asarray(a, dtype=np.float64).reshape(-1)
    right = np.asarray(b, dtype=np.float64).reshape(-1)
    mask = np.isfinite(left) & np.isfinite(right)
    if int(mask.sum()) < 3:
        return 0.0
    left = left[mask] - float(np.mean(left[mask]))
    right = right[mask] - float(np.mean(right[mask]))
    denom = float(np.sqrt(np.sum(left * left) * np.sum(right * right)))
    if denom <= 1.0e-12:
        return 0.0
    return float(abs(np.sum(left * right) / denom))


def calibrate_prior_adjacency_from_windows(
    prior_adjacency: np.ndarray | None,
    x_train: np.ndarray,
    *,
    max_lag: int = 3,
    min_support: float = 0.0,
    strength: float = 1.0,
) -> tuple[np.ndarray | None, dict[str, Any]]:
    if prior_adjacency is None:
        return None, {"enabled": False, "status": "no_prior"}
    prior = np.asarray(prior_adjacency, dtype=np.float32)
    x = np.asarray(x_train, dtype=np.float32)
    if prior.ndim != 2 or x.ndim != 3 or prior.shape[0] != x.shape[2] or prior.shape[1] != x.shape[2]:
        return prior_adjacency, {"enabled": False, "status": "invalid_shape"}
    calibrated = prior.copy()
    support = np.zeros_like(prior, dtype=np.float32)
    edge_positions = np.argwhere(prior > 0.0)
    lag_limit = max(0, min(int(max_lag), int(x.shape[1]) - 1))
    for target_idx, source_idx in edge_positions:
        source = x[:, :, int(source_idx)]
        target = x[:, :, int(target_idx)]
        scores = [_safe_abs_corr(source, target)]
        source_delta = source[:, -1] - source[:, 0]
        target_delta = target[:, -1] - target[:, 0]
        scores.append(_safe_abs_corr(source_delta, target_delta))
        for lag in range(1, lag_limit + 1):
            scores.append(_safe_abs_corr(source[:, :-lag], target[:, lag:]))
            scores.append(_safe_abs_corr(target[:, :-lag], source[:, lag:]))
        edge_support = float(max(scores)) if scores else 0.0
        support[int(target_idx), int(source_idx)] = edge_support
        if edge_support < float(min_support):
            calibrated[int(target_idx), int(source_idx)] = 0.0
        else:
            mix = float(np.clip(strength, 0.0, 1.0))
            calibrated[int(target_idx), int(source_idx)] = float(prior[int(target_idx), int(source_idx)]) * (
                (1.0 - mix) + mix * edge_support
            )
    kept = int(np.count_nonzero(calibrated > 0.0))
    support_values = support[prior > 0.0]
    return calibrated.astype(np.float32), {
        "enabled": True,
        "source": "train_only_prior_edge_support",
        "max_lag": int(max_lag),
        "min_support": float(min_support),
        "strength": float(np.clip(strength, 0.0, 1.0)),
        "n_edges_before": int(len(edge_positions)),
        "n_edges_after": kept,
        "mean_support": float(np.mean(support_values)) if support_values.size else 0.0,
        "max_support": float(np.max(support_values)) if support_values.size else 0.0,
    }


def load_ready_task(ready_root: Path, dataset: str, *, target: str | None = None) -> ReadyTask:
    name = str(dataset).strip().lower()
    root = Path(ready_root) / name
    x = _read_csv(root / "X_process_features.csv")
    y = _read_csv(root / "y_labels.csv")
    if len(x) != len(y):
        raise ValueError(f"{name}: X/y row mismatch: {len(x)} != {len(y)}")
    meta = y.copy()
    if name == "tep":
        label_col = "event_quality_class_id"
        group_cols = [col for col in ("source_split", "source_file") if col in meta.columns]
        order_col = "sample_index"
        task = "tep_fault_diagnosis"
        exclude = {"record_id"}
    elif name == "skab":
        label_col = "anomaly"
        group_cols = ["run_id"]
        order_col = "sample_index"
        task = "skab_binary_anomaly_detection"
        exclude = {"record_id", "run_id", "run_group", "sample_index"}
    elif name == "hydraulic":
        label_col = str(target or "cooler")
        group_cols = []
        order_col = None
        task = f"hydraulic_component_state_{label_col}"
        exclude = {"record_id"}
    elif name == "cmapss":
        target_name = str(target or "degradation_stage_id").strip().lower()
        if target_name in {"rul", "rul_regression", "original_rul"}:
            if "degradation_stage_id" not in meta.columns:
                raise ValueError(f"{name}: degradation_stage_id is required as an auxiliary label for RUL training.")
            label_col = "degradation_stage_id"
            task = "cmapss_original_rul_regression"
            target_name = "rul"
        else:
            label_col = "degradation_stage_id"
            task = "cmapss_degradation_stage_classification"
        group_cols = [col for col in ("subset", "split_role", "unit") if col in meta.columns]
        order_col = "cycle"
        # `cycle` is an observed lifecycle coordinate and is essential for degradation-stage evidence.
        exclude = {"record_id", "subset_id", "unit"}
    else:
        raise ValueError(f"Unknown ready dataset: {dataset}")
    if label_col not in meta.columns:
        raise ValueError(f"{name}: label column {label_col!r} not found.")
    labels = pd.to_numeric(meta[label_col], errors="coerce").fillna(0).astype(int).to_numpy()
    feature_cols = _numeric_feature_columns(x, exclude)
    return ReadyTask(
        dataset=name,
        target=target_name if name == "cmapss" else label_col,
        task=task,
        x=x,
        meta=meta,
        labels=labels,
        feature_cols=feature_cols,
        group_cols=group_cols,
        order_col=order_col if order_col in set(meta.columns) | set(x.columns) else None,
        ready_dir=root,
    )


def _edge_source_allowed(source: str, mode: str) -> bool:
    src = str(source).lower()
    name = str(mode).strip().lower()
    if name in {"none", ""}:
        return False
    if name == "all":
        return True
    if name == "llm":
        return "llm" in src
    if name == "expert":
        return "llm" not in src
    if name == "expert_llm":
        return "llm" in src or "expert" in src or "prior" in src or "physics" in src
    return False


def _edge_source_family(source: str) -> str:
    src = str(source or "").lower()
    if "llm" in src or "language" in src or "gpt" in src:
        return "llm"
    if "expert" in src or "physics" in src or "prior" in src or "domain" in src or "rule" in src:
        return "expert"
    return "expert"


LLM_EXPERT_GRAPH_CORRECTION_SOURCE = "llm_expert_graph_dynamic_correction"
LLM_EXPERT_CONDITION_VERIFIER_SOURCE = "llm_expert_condition_verifier"


def _llm_correction_operation(value: str) -> str:
    op = str(value or "").strip().lower().replace("-", "_")
    aliases = {
        "update": "revise",
        "modify": "revise",
        "lower": "downweight",
        "down_weight": "downweight",
        "decrease": "downweight",
        "delete": "remove",
        "drop": "remove",
    }
    op = aliases.get(op, op)
    return op if op in {"add", "revise", "downweight", "remove"} else ""


def _collect_llm_expert_graph_corrections(payload: Mapping[str, Any]) -> dict[str, Any]:
    by_id: dict[str, list[dict[str, Any]]] = {}
    by_pair: dict[tuple[str, str], list[dict[str, Any]]] = {}
    corrections: list[dict[str, Any]] = []
    for edge in payload.get("edges", []) or []:
        if not isinstance(edge, Mapping):
            continue
        evidence_source = str(edge.get("evidence_source", ""))
        if str(evidence_source).lower() != LLM_EXPERT_GRAPH_CORRECTION_SOURCE:
            continue
        op = _llm_correction_operation(str(edge.get("correction_operation", "")))
        if op:
            corrections.append(dict(edge))
    metadata = payload.get("llm_expert_graph_correction_metadata", {})
    if isinstance(metadata, Mapping):
        for bundle in metadata.values():
            if not isinstance(bundle, Mapping):
                continue
            for correction in bundle.get("metadata_only_corrections", []) or []:
                if isinstance(correction, Mapping):
                    corrections.append(dict(correction))
    actionable = 0
    for correction in corrections:
        op = _llm_correction_operation(str(correction.get("correction_operation", correction.get("operation", ""))))
        if not op or op == "add":
            continue
        correction["correction_operation"] = op
        indexed = False
        edge_id = str(correction.get("corrects_edge_id", "")).strip()
        if edge_id:
            by_id.setdefault(edge_id, []).append(correction)
            indexed = True
        source = str(correction.get("source", "")).strip()
        target = str(correction.get("target", "")).strip()
        if source and target:
            by_pair.setdefault((source, target), []).append(correction)
            indexed = True
        if indexed:
            actionable += 1
    return {
        "by_id": by_id,
        "by_pair": by_pair,
        "n_corrections": int(len(corrections)),
        "n_actionable_corrections": int(actionable),
    }


def _apply_llm_expert_graph_correction_to_edge(
    edge: Mapping[str, Any],
    *,
    source: str,
    target: str,
    reliability: float,
    correction_index: Mapping[str, Any],
) -> tuple[float, str | None]:
    evidence_source = str(edge.get("evidence_source", ""))
    if str(evidence_source).lower() == LLM_EXPERT_GRAPH_CORRECTION_SOURCE:
        return float(reliability), None
    edge_id = str(edge.get("edge_id", "")).strip()
    corrections: list[Mapping[str, Any]] = []
    by_id = correction_index.get("by_id", {}) if isinstance(correction_index, Mapping) else {}
    by_pair = correction_index.get("by_pair", {}) if isinstance(correction_index, Mapping) else {}
    if isinstance(by_id, Mapping) and edge_id:
        corrections.extend(by_id.get(edge_id, []) or [])
    if isinstance(by_pair, Mapping):
        corrections.extend(by_pair.get((str(source), str(target)), []) or [])
    if not corrections:
        return float(reliability), None
    for correction in corrections:
        op = _llm_correction_operation(str(correction.get("correction_operation", correction.get("operation", ""))))
        if op == "remove":
            return 0.0, "remove"
    adjusted = float(reliability)
    applied = None
    for correction in corrections:
        op = _llm_correction_operation(str(correction.get("correction_operation", correction.get("operation", ""))))
        if op not in {"revise", "downweight"}:
            continue
        correction_strength = float(correction.get("reliability", adjusted) or adjusted)
        correction_strength = float(np.clip(correction_strength, 0.0, 1.0))
        adjusted = min(adjusted, correction_strength)
        applied = op if applied is None else applied
    return float(adjusted), applied


def _llm_condition_activation(value: str) -> str:
    activation = str(value or "uncertain").strip().lower().replace("-", "_")
    aliases = {
        "active": "activate",
        "enable": "activate",
        "enabled": "activate",
        "support": "activate",
        "supported": "activate",
        "verify": "activate",
        "verified": "activate",
        "deactivate": "suppress",
        "disable": "suppress",
        "disabled": "suppress",
        "downweight": "suppress",
        "remove": "suppress",
        "reject": "suppress",
        "abstain": "uncertain",
        "unknown": "uncertain",
        "conditional": "uncertain",
    }
    activation = aliases.get(activation, activation)
    return activation if activation in {"activate", "suppress", "uncertain"} else "uncertain"


def _collect_llm_expert_condition_verifications(payload: Mapping[str, Any]) -> dict[str, Any]:
    by_id: dict[str, list[dict[str, Any]]] = {}
    by_pair: dict[tuple[str, str], list[dict[str, Any]]] = {}
    records: list[dict[str, Any]] = []
    for edge in payload.get("edges", []) or []:
        if not isinstance(edge, Mapping):
            continue
        evidence_source = str(edge.get("evidence_source", ""))
        if str(evidence_source).lower() != LLM_EXPERT_CONDITION_VERIFIER_SOURCE:
            continue
        records.append(dict(edge))
    metadata = payload.get("llm_expert_condition_verifier_metadata", {})
    if isinstance(metadata, Mapping):
        for bundle in metadata.values():
            if not isinstance(bundle, Mapping):
                continue
            for record in bundle.get("condition_verifications", []) or []:
                if isinstance(record, Mapping):
                    records.append(dict(record))
    actionable = 0
    activation_counts = {"activate": 0, "suppress": 0, "uncertain": 0}
    for record in records:
        activation = _llm_condition_activation(
            str(record.get("condition_activation", record.get("activation", record.get("decision", ""))))
        )
        record["condition_activation"] = activation
        activation_counts[activation] = activation_counts.get(activation, 0) + 1
        indexed = False
        edge_id = str(record.get("expert_edge_id", record.get("corrects_edge_id", ""))).strip()
        if edge_id:
            by_id.setdefault(edge_id, []).append(record)
            indexed = True
        source = str(record.get("source", "")).strip()
        target = str(record.get("target", "")).strip()
        if source and target:
            by_pair.setdefault((source, target), []).append(record)
            indexed = True
        if indexed and activation in {"activate", "suppress"}:
            actionable += 1
    return {
        "by_id": by_id,
        "by_pair": by_pair,
        "records": records,
        "n_verifications": int(len(records)),
        "n_actionable_verifications": int(actionable),
        "activation_counts": activation_counts,
    }


def _llm_condition_strength(record: Mapping[str, Any]) -> float:
    reliability = record.get("reliability", None)
    if reliability is not None:
        return float(np.clip(float(reliability or 0.0), 0.0, 1.0))
    confidence = float(record.get("confidence", 0.0) or 0.0)
    activation_score = float(record.get("activation_score", record.get("score", confidence)) or 0.0)
    return float(np.clip(confidence * activation_score, 0.0, 1.0))


def load_knowledge_graph_prior(
    task: ReadyTask,
    *,
    mode: str,
    min_reliability: float = 0.0,
    group_expansion: bool = False,
    group_expansion_strength: float = 0.5,
) -> tuple[np.ndarray | None, dict[str, Any]]:
    name = str(mode).strip().lower()
    prior_enabled = name not in {"", "none"}
    path = task.ready_dir / "knowledge_model" / "knowledge_graph.json"
    if not path.exists():
        # Deep Windows paths often need the extended prefix even when Path.exists fails.
        try:
            with open(_fs_path(path), "r", encoding="utf-8") as fh:
                payload = json.load(fh)
        except FileNotFoundError:
            return None, {"enabled": False, "mode": name or "none", "status": "missing", "path": str(path), "matched_edges": 0}
    else:
        with open(_fs_path(path), "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    feature_index = {str(feature): i for i, feature in enumerate(task.feature_cols)}
    group_to_features: dict[str, list[str]] = {}
    for feature in task.feature_cols:
        group_to_features.setdefault(feature_group_name(str(feature)), []).append(str(feature))
    prior = np.zeros((len(task.feature_cols), len(task.feature_cols)), dtype=np.float32)
    family_priors: dict[str, np.ndarray] = {
        "expert": np.zeros_like(prior, dtype=np.float32),
        "llm": np.zeros_like(prior, dtype=np.float32),
    }
    correction_index = _collect_llm_expert_graph_corrections(payload)
    condition_index = _collect_llm_expert_condition_verifications(payload)
    condition_activate = np.zeros_like(prior, dtype=np.float32)
    condition_suppress = np.zeros_like(prior, dtype=np.float32)
    dynamic_correction_counts = {"remove": 0, "downweight": 0, "revise": 0}
    condition_match_counts = {"activate": 0, "suppress": 0, "uncertain": 0}
    source_counts: dict[str, int] = {}
    family_counts: dict[str, int] = {}
    matched = 0
    expanded = 0
    skipped = 0
    for edge in payload.get("edges", []) or []:
        evidence_source = str(edge.get("evidence_source", ""))
        source = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        if source not in feature_index or target not in feature_index:
            skipped += 1
            continue
        reliability = float(edge.get("reliability", 0.0) or 0.0)
        src_idx = feature_index[source]
        tgt_idx = feature_index[target]
        family = _edge_source_family(evidence_source)
        if family == "expert":
            edge_id = str(edge.get("edge_id", "")).strip()
            condition_records: list[Mapping[str, Any]] = []
            by_id = condition_index.get("by_id", {}) if isinstance(condition_index, Mapping) else {}
            by_pair = condition_index.get("by_pair", {}) if isinstance(condition_index, Mapping) else {}
            if isinstance(by_id, Mapping) and edge_id:
                condition_records.extend(by_id.get(edge_id, []) or [])
            if isinstance(by_pair, Mapping):
                condition_records.extend(by_pair.get((str(source), str(target)), []) or [])
            deduped_records: list[Mapping[str, Any]] = []
            seen_records: set[tuple[str, str, str, str, str]] = set()
            for record in condition_records:
                key = (
                    str(record.get("expert_edge_id", record.get("corrects_edge_id", ""))).strip(),
                    str(record.get("source", "")).strip(),
                    str(record.get("target", "")).strip(),
                    str(record.get("condition_activation", record.get("activation", record.get("decision", "")))).strip(),
                    str(record.get("reliability", record.get("confidence", record.get("activation_score", "")))).strip(),
                )
                if key in seen_records:
                    continue
                seen_records.add(key)
                deduped_records.append(record)
            condition_records = deduped_records
            for record in condition_records:
                activation = _llm_condition_activation(
                    str(record.get("condition_activation", record.get("activation", record.get("decision", ""))))
                )
                strength = _llm_condition_strength(record)
                if strength <= 0.0:
                    continue
                condition_match_counts[activation] = condition_match_counts.get(activation, 0) + 1
                if activation == "activate":
                    condition_activate[tgt_idx, src_idx] = max(float(condition_activate[tgt_idx, src_idx]), strength)
                elif activation == "suppress":
                    condition_suppress[tgt_idx, src_idx] = max(float(condition_suppress[tgt_idx, src_idx]), strength)
        if not prior_enabled or not _edge_source_allowed(evidence_source, name):
            skipped += 1
            continue
        reliability, applied_correction = _apply_llm_expert_graph_correction_to_edge(
            edge,
            source=source,
            target=target,
            reliability=reliability,
            correction_index=correction_index,
        )
        if applied_correction == "remove":
            dynamic_correction_counts["remove"] += 1
            skipped += 1
            continue
        if applied_correction in {"downweight", "revise"}:
            dynamic_correction_counts[applied_correction] += 1
        if reliability < float(min_reliability):
            skipped += 1
            continue
        # Dynamic graph rows are targets attending to source variables.
        prior[tgt_idx, src_idx] = max(float(prior[tgt_idx, src_idx]), reliability)
        family_priors[family][tgt_idx, src_idx] = max(float(family_priors[family][tgt_idx, src_idx]), reliability)
        source_counts[evidence_source] = source_counts.get(evidence_source, 0) + 1
        family_counts[family] = family_counts.get(family, 0) + 1
        matched += 1
        if bool(group_expansion):
            source_group = feature_group_name(source)
            target_group = feature_group_name(target)
            expanded_reliability = reliability * float(group_expansion_strength)
            for expanded_source in group_to_features.get(source_group, []):
                for expanded_target in group_to_features.get(target_group, []):
                    if expanded_source == source and expanded_target == target:
                        continue
                    expanded_src_idx = feature_index[expanded_source]
                    expanded_tgt_idx = feature_index[expanded_target]
                    prior[expanded_tgt_idx, expanded_src_idx] = max(
                        float(prior[expanded_tgt_idx, expanded_src_idx]),
                        expanded_reliability,
                    )
                    family_priors[family][expanded_tgt_idx, expanded_src_idx] = max(
                        float(family_priors[family][expanded_tgt_idx, expanded_src_idx]),
                        expanded_reliability,
                    )
                    expanded += 1
    if matched == 0:
        return None, {
            "enabled": False,
            "mode": name,
            "status": "metadata_only" if not prior_enabled else "no_matched_edges",
            "path": str(path),
            "matched_edges": 0,
            "skipped_edges": int(skipped),
            "llm_expert_graph_dynamic_corrections": {
                "enabled": bool(correction_index.get("n_corrections", 0)),
                "n_corrections": int(correction_index.get("n_corrections", 0)),
                "n_actionable_corrections": int(correction_index.get("n_actionable_corrections", 0)),
                "applied": dynamic_correction_counts,
            },
            "llm_expert_condition_verifier": {
                "enabled": bool(condition_index.get("n_verifications", 0)),
                "n_verifications": int(condition_index.get("n_verifications", 0)),
                "n_actionable_verifications": int(condition_index.get("n_actionable_verifications", 0)),
                "matched": condition_match_counts,
                "activation_counts": condition_index.get("activation_counts", {}),
                "activate_edges": int(np.count_nonzero(condition_activate > 0.0)),
                "suppress_edges": int(np.count_nonzero(condition_suppress > 0.0)),
            },
            "_llm_expert_condition_activate_matrix": _normalize_edge_prior(condition_activate),
            "_llm_expert_condition_suppress_matrix": _normalize_edge_prior(condition_suppress),
            "_llm_expert_condition_records": condition_index.get("records", []),
        }
    family_names = [family for family in ("expert", "llm") if bool(np.any(family_priors[family] > 0.0))]
    family_matrices = (
        np.stack([_normalize_edge_prior(family_priors[family]) for family in family_names], axis=0).astype(np.float32)
        if family_names
        else None
    )
    return prior, {
        "enabled": True,
        "mode": name,
        "status": "ok",
        "path": str(path),
        "matched_edges": int(matched),
        "expanded_edges": int(expanded),
        "skipped_edges": int(skipped),
        "source_counts": source_counts,
        "source_family_counts": family_counts,
        "source_family_names": family_names,
        "min_reliability": float(min_reliability),
        "group_expansion": bool(group_expansion),
        "group_expansion_strength": float(group_expansion_strength),
        "llm_expert_graph_dynamic_corrections": {
            "enabled": bool(correction_index.get("n_corrections", 0)),
            "n_corrections": int(correction_index.get("n_corrections", 0)),
            "n_actionable_corrections": int(correction_index.get("n_actionable_corrections", 0)),
            "applied": dynamic_correction_counts,
        },
        "llm_expert_condition_verifier": {
            "enabled": bool(condition_index.get("n_verifications", 0)),
            "n_verifications": int(condition_index.get("n_verifications", 0)),
            "n_actionable_verifications": int(condition_index.get("n_actionable_verifications", 0)),
            "matched": condition_match_counts,
            "activation_counts": condition_index.get("activation_counts", {}),
            "activate_edges": int(np.count_nonzero(condition_activate > 0.0)),
            "suppress_edges": int(np.count_nonzero(condition_suppress > 0.0)),
        },
        "_llm_expert_condition_activate_matrix": _normalize_edge_prior(condition_activate),
        "_llm_expert_condition_suppress_matrix": _normalize_edge_prior(condition_suppress),
        "_llm_expert_condition_records": condition_index.get("records", []),
        "_external_family_prior_matrices": family_matrices,
        "_external_family_prior_names": family_names,
    }


def build_causal_windows(task: ReadyTask, *, window_size: int) -> np.ndarray:
    values = task.x[task.feature_cols].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=np.float64)
    values = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
    width = max(2, int(window_size))
    windows = np.zeros((len(values), width, len(task.feature_cols)), dtype=np.float32)
    meta = task.meta.reset_index(drop=True)
    if task.group_cols:
        group_frame = meta[task.group_cols].astype(str).copy()
        group_frame["_idx"] = np.arange(len(meta), dtype=np.int64)
        groups = [group["_idx"].to_numpy(dtype=np.int64) for _key, group in group_frame.groupby(task.group_cols, sort=False)]
    else:
        groups = [np.arange(len(meta), dtype=np.int64)]
    for group_idx in groups:
        if task.order_col:
            order_source = meta if task.order_col in meta.columns else task.x
            order_values = pd.to_numeric(order_source.iloc[group_idx][task.order_col], errors="coerce").fillna(0).to_numpy()
            group_idx = group_idx[np.argsort(order_values, kind="stable")]
        group_values = values[group_idx]
        if len(group_values) == 0:
            continue
        for pos, row_idx in enumerate(group_idx):
            start = max(0, pos - width + 1)
            segment = group_values[start : pos + 1]
            if len(segment) < width:
                pad = np.repeat(segment[:1], width - len(segment), axis=0)
                segment = np.vstack([pad, segment])
            windows[int(row_idx)] = segment[-width:]
    return windows


def _stratified_train_val_split(indices: np.ndarray, labels: np.ndarray, *, seed: int, val_fraction: float) -> tuple[np.ndarray, np.ndarray]:
    idx = np.asarray(indices, dtype=np.int64)
    y = np.asarray(labels, dtype=int)[idx]
    if len(idx) <= 2:
        return idx, np.empty(0, dtype=np.int64)
    encoded = pd.factorize(y)[0]
    counts = np.bincount(encoded)
    stratify = y if len(counts) > 1 and int(counts.min()) >= 2 else None
    train_idx, val_idx = train_test_split(
        idx,
        test_size=float(val_fraction),
        random_state=int(seed),
        stratify=stratify,
    )
    return np.asarray(train_idx, dtype=np.int64), np.asarray(val_idx, dtype=np.int64)


def _group_key_values(meta: pd.DataFrame, indices: np.ndarray, group_cols: Sequence[str]) -> np.ndarray:
    idx = np.asarray(indices, dtype=np.int64)
    cols = [str(col) for col in group_cols if str(col) in meta.columns]
    if not cols:
        return np.asarray([str(i) for i in idx], dtype=object)
    frame = meta.iloc[idx][cols].astype(str)
    return frame.agg("\x1f".join, axis=1).to_numpy(dtype=object)


def _grouped_train_val_split(
    indices: np.ndarray,
    labels: np.ndarray,
    meta: pd.DataFrame,
    group_cols: Sequence[str],
    *,
    seed: int,
    val_fraction: float,
) -> tuple[np.ndarray, np.ndarray]:
    idx = np.asarray(indices, dtype=np.int64)
    y = np.asarray(labels, dtype=int)
    groups = _group_key_values(meta, idx, group_cols)
    if len(np.unique(groups)) < 2:
        return _stratified_train_val_split(idx, y, seed=seed, val_fraction=val_fraction)

    all_classes = set(map(int, np.unique(y[idx])))
    best: tuple[np.ndarray, np.ndarray] | None = None
    best_coverage = -1
    for offset in range(50):
        splitter = GroupShuffleSplit(n_splits=1, test_size=float(val_fraction), random_state=int(seed) + offset)
        train_pos, val_pos = next(splitter.split(idx, y[idx], groups=groups))
        train_idx = idx[np.asarray(train_pos, dtype=np.int64)]
        val_idx = idx[np.asarray(val_pos, dtype=np.int64)]
        if len(train_idx) == 0 or len(val_idx) == 0:
            continue
        coverage = len(set(map(int, np.unique(y[val_idx]))) & all_classes)
        if coverage > best_coverage:
            best = (train_idx, val_idx)
            best_coverage = coverage
        if coverage == len(all_classes):
            return train_idx, val_idx
    if best is not None:
        return best
    return _stratified_train_val_split(idx, y, seed=seed, val_fraction=val_fraction)


def _blocked_group_train_val_split(
    indices: np.ndarray,
    labels: np.ndarray,
    meta: pd.DataFrame,
    group_cols: Sequence[str],
    *,
    order_col: str | None,
    seed: int,
    val_fraction: float,
) -> tuple[np.ndarray, np.ndarray]:
    idx = np.asarray(indices, dtype=np.int64)
    cols = [str(col) for col in group_cols if str(col) in meta.columns]
    if not cols:
        return _stratified_train_val_split(idx, labels, seed=seed, val_fraction=val_fraction)
    frame = meta.iloc[idx][cols].astype(str).copy()
    frame["_idx"] = idx
    train_parts: list[np.ndarray] = []
    val_parts: list[np.ndarray] = []
    for _key, group in frame.groupby(cols, sort=False):
        group_idx = group["_idx"].to_numpy(dtype=np.int64)
        if order_col and order_col in meta.columns:
            order = pd.to_numeric(meta.iloc[group_idx][order_col], errors="coerce").fillna(0).to_numpy()
            group_idx = group_idx[np.argsort(order, kind="stable")]
        if len(group_idx) <= 1:
            train_parts.append(group_idx)
            continue
        n_val = max(1, int(math.ceil(len(group_idx) * float(val_fraction))))
        n_val = min(n_val, len(group_idx) - 1)
        train_parts.append(group_idx[:-n_val])
        val_parts.append(group_idx[-n_val:])
    train_idx = np.concatenate(train_parts) if train_parts else np.empty(0, dtype=np.int64)
    val_idx = np.concatenate(val_parts) if val_parts else np.empty(0, dtype=np.int64)
    if len(train_idx) == 0 or len(val_idx) == 0:
        return _stratified_train_val_split(idx, labels, seed=seed, val_fraction=val_fraction)
    return train_idx.astype(np.int64), val_idx.astype(np.int64)


def _split_skab_runs(meta: pd.DataFrame, *, seed: int, test_size: float, val_fraction: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    runs = np.array(sorted(meta["run_id"].astype(str).unique()), dtype=object)
    rng = np.random.default_rng(int(seed))
    rng.shuffle(runs)
    n_test = max(1, int(math.ceil(len(runs) * float(test_size))))
    test_runs = set(map(str, runs[:n_test]))
    rest = runs[n_test:]
    n_val = max(1, int(math.ceil(len(rest) * float(val_fraction)))) if len(rest) > 1 else 0
    val_runs = set(map(str, rest[:n_val]))
    train_runs = set(map(str, rest[n_val:]))
    if not train_runs and len(rest) > 0:
        train_runs = {str(rest[0])}
        val_runs = set(map(str, rest[1:]))
    run_col = meta["run_id"].astype(str)
    return (
        np.flatnonzero(run_col.isin(train_runs).to_numpy()),
        np.flatnonzero(run_col.isin(val_runs).to_numpy()),
        np.flatnonzero(run_col.isin(test_runs).to_numpy()),
    )


def build_split(task: ReadyTask, *, seed: int, test_size: float = 0.25, val_fraction: float = 0.20) -> SplitBundle:
    raw_labels = np.asarray(task.labels, dtype=int)
    original_classes = [int(c) for c in sorted(np.unique(raw_labels))]
    class_to_internal = {cls: i for i, cls in enumerate(original_classes)}
    y_internal = np.asarray([class_to_internal[int(v)] for v in raw_labels], dtype=np.int64)
    all_idx = np.arange(len(raw_labels), dtype=np.int64)

    split_protocol = "stratified_random"
    validation_group_cols: list[str] = []

    if task.dataset in {"tep", "cmapss"} and "split_role" in task.meta.columns:
        split_role = task.meta["split_role"].astype(str).str.lower()
        test_idx = np.flatnonzero(split_role.eq("test").to_numpy())
        train_val_idx = np.flatnonzero(~split_role.eq("test").to_numpy())
        if task.dataset == "cmapss":
            validation_group_cols = [col for col in ("subset", "unit") if col in task.meta.columns]
            train_idx, val_idx = _grouped_train_val_split(
                train_val_idx,
                y_internal,
                task.meta,
                validation_group_cols,
                seed=seed,
                val_fraction=val_fraction,
            )
            split_protocol = "official_test_grouped_unit_validation"
        elif task.dataset == "tep":
            validation_group_cols = [col for col in ("source_split", "source_file") if col in task.meta.columns]
            train_idx, val_idx = _blocked_group_train_val_split(
                train_val_idx,
                y_internal,
                task.meta,
                validation_group_cols,
                order_col=task.order_col,
                seed=seed,
                val_fraction=val_fraction,
            )
            split_protocol = "official_test_blocked_source_validation"
        else:
            train_idx, val_idx = _stratified_train_val_split(train_val_idx, y_internal, seed=seed, val_fraction=val_fraction)
    elif task.dataset == "skab" and "run_id" in task.meta.columns:
        train_idx, val_idx, test_idx = _split_skab_runs(task.meta, seed=seed, test_size=test_size, val_fraction=val_fraction)
        split_protocol = "run_group_validation_test_split"
        validation_group_cols = ["run_id"]
    else:
        encoded = pd.factorize(y_internal)[0]
        counts = np.bincount(encoded)
        stratify = y_internal if len(counts) > 1 and int(counts.min()) >= 2 else None
        train_val_idx, test_idx = train_test_split(
            all_idx,
            test_size=float(test_size),
            random_state=int(seed),
            stratify=stratify,
        )
        train_idx, val_idx = _stratified_train_val_split(train_val_idx, y_internal, seed=seed + 17, val_fraction=val_fraction)

    if len(val_idx) == 0:
        train_idx, val_idx = _stratified_train_val_split(train_idx, y_internal, seed=seed + 23, val_fraction=max(0.10, val_fraction))
        split_protocol = f"{split_protocol}_fallback_stratified"
        validation_group_cols = []

    return SplitBundle(
        train_idx=np.asarray(train_idx, dtype=np.int64),
        val_idx=np.asarray(val_idx, dtype=np.int64),
        test_idx=np.asarray(test_idx, dtype=np.int64),
        classes=list(range(len(original_classes))),
        y_internal=y_internal,
        class_id_mapping={str(i): int(cls) for cls, i in class_to_internal.items()},
        split_protocol=split_protocol,
        validation_group_cols=validation_group_cols,
    )


def _limit_indices(indices: np.ndarray, labels: np.ndarray, *, seed: int, limit: int | None) -> np.ndarray:
    idx = np.asarray(indices, dtype=np.int64)
    if limit is None or int(limit) <= 0 or len(idx) <= int(limit):
        return idx
    rng = np.random.default_rng(int(seed))
    selected: list[np.ndarray] = []
    y = np.asarray(labels, dtype=int)
    per_class = max(1, int(limit) // max(1, len(np.unique(y[idx]))))
    for cls in sorted(np.unique(y[idx])):
        cls_idx = idx[y[idx] == cls]
        take = min(len(cls_idx), per_class)
        selected.append(rng.choice(cls_idx, size=take, replace=False))
    out = np.concatenate(selected) if selected else idx[: int(limit)]
    if len(out) < int(limit):
        remaining = np.setdiff1d(idx, out, assume_unique=False)
        if len(remaining) > 0:
            fill = rng.choice(remaining, size=min(len(remaining), int(limit) - len(out)), replace=False)
            out = np.concatenate([out, fill])
    rng.shuffle(out)
    return np.asarray(out[: int(limit)], dtype=np.int64)


def select_cmapss_terminal_rul_indices(task: ReadyTask, indices: np.ndarray) -> np.ndarray:
    idx = np.asarray(indices, dtype=np.int64)
    required = {"subset", "unit", "cycle"}
    if task.dataset != "cmapss" or not required.issubset(set(task.meta.columns)) or len(idx) == 0:
        return idx
    meta = task.meta.iloc[idx].copy()
    meta["_global_idx"] = idx
    meta["_cycle_numeric"] = pd.to_numeric(meta["cycle"], errors="coerce")
    meta["_unit_key"] = meta["unit"].astype(str)
    meta["_subset_key"] = meta["subset"].astype(str)
    terminal_rows = meta.groupby(["_subset_key", "_unit_key"], sort=True)["_cycle_numeric"].idxmax()
    selected = meta.loc[terminal_rows, "_global_idx"].to_numpy(dtype=np.int64)
    return np.asarray(np.sort(selected), dtype=np.int64)


def scale_windows(
    windows: np.ndarray,
    *,
    train_idx: np.ndarray,
    val_idx: np.ndarray,
    test_idx: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    feature_dim = windows.shape[2]
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    train_flat = windows[train_idx].reshape(-1, feature_dim)
    scaler.fit(imputer.fit_transform(train_flat))

    def _scale(idx: np.ndarray) -> np.ndarray:
        flat = windows[idx].reshape(-1, feature_dim)
        scaled = scaler.transform(imputer.transform(flat)).reshape(len(idx), windows.shape[1], feature_dim)
        return np.nan_to_num(scaled, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)

    return _scale(train_idx), _scale(val_idx), _scale(test_idx)


def summarize_classification(
    y_true: Sequence[int] | np.ndarray,
    proba: np.ndarray,
    *,
    positive_threshold: float | None = None,
) -> dict[str, Any]:
    y = np.asarray(y_true, dtype=int).reshape(-1)
    p = np.asarray(proba, dtype=float)
    if positive_threshold is not None and p.ndim == 2 and p.shape[1] == 2:
        pred = (p[:, 1] >= float(positive_threshold)).astype(int)
    else:
        pred = np.argmax(p, axis=1)
    average = "binary" if len(np.unique(y)) <= 2 and set(np.unique(y)).issubset({0, 1}) else "macro"
    metrics = {
        "accuracy": float(accuracy_score(y, pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
        "macro_f1": float(f1_score(y, pred, average="macro", zero_division=0)),
        "macro_precision": float(precision_score(y, pred, average="macro", zero_division=0)),
        "macro_recall": float(recall_score(y, pred, average="macro", zero_division=0)),
        "positive_f1": float(f1_score(y, pred, average=average, zero_division=0)),
        "positive_precision": float(precision_score(y, pred, average=average, zero_division=0)),
        "positive_recall": float(recall_score(y, pred, average=average, zero_division=0)),
    }
    if len(np.unique(y)) > 2:
        distance = np.abs(pred.astype(int) - y.astype(int))
        metrics["ordinal_mae"] = float(np.mean(distance))
        metrics["within_one_stage_accuracy"] = float(np.mean(distance <= 1))
    labels = list(range(int(p.shape[1]))) if p.ndim == 2 else sorted(int(v) for v in np.unique(y))
    per_precision, per_recall, per_f1, per_support = precision_recall_fscore_support(
        y,
        pred,
        labels=labels,
        zero_division=0,
    )
    metrics["per_class"] = {
        str(int(label)): {
            "precision": float(per_precision[pos]),
            "recall": float(per_recall[pos]),
            "f1": float(per_f1[pos]),
            "support": int(per_support[pos]),
        }
        for pos, label in enumerate(labels)
    }
    return metrics


def tune_binary_threshold(
    y_true: Sequence[int] | np.ndarray,
    proba: np.ndarray,
    *,
    positive_recall_weight: float = 0.25,
) -> float | None:
    y = np.asarray(y_true, dtype=int).reshape(-1)
    p = np.asarray(proba, dtype=float)
    if p.ndim != 2 or p.shape[1] != 2 or not set(np.unique(y)).issubset({0, 1}):
        return None
    best_threshold = 0.5
    best_score = -1.0
    scores = p[:, 1]
    for threshold in np.linspace(0.02, 0.98, 97):
        pred = (scores >= float(threshold)).astype(int)
        macro = f1_score(y, pred, average="macro", zero_division=0)
        pos_recall = recall_score(y, pred, zero_division=0)
        score = float(macro + float(positive_recall_weight) * pos_recall)
        if score > best_score:
            best_score = score
            best_threshold = float(threshold)
    return float(best_threshold)


def ordinal_emd_loss(
    logits: torch.Tensor,
    target: torch.Tensor,
    *,
    class_weights: torch.Tensor | None = None,
) -> torch.Tensor:
    if logits.ndim != 2:
        raise ValueError("Ordinal loss expects logits with shape [batch, classes].")
    n_classes = int(logits.shape[1])
    if n_classes <= 2:
        return logits.new_tensor(0.0)
    labels = target.to(device=logits.device, dtype=torch.long).clamp(0, n_classes - 1)
    proba = torch.softmax(logits, dim=1)
    cumulative = torch.cumsum(proba, dim=1)[:, :-1]
    thresholds = torch.arange(n_classes - 1, device=logits.device).view(1, -1)
    target_cumulative = thresholds.ge(labels.view(-1, 1)).to(dtype=logits.dtype)
    per_sample = torch.mean((cumulative - target_cumulative) ** 2, dim=1)
    if class_weights is not None and class_weights.numel() == n_classes:
        weights = class_weights.to(device=logits.device, dtype=logits.dtype)[labels]
        return torch.sum(per_sample * weights) / torch.clamp(torch.sum(weights), min=1.0e-6)
    return torch.mean(per_sample)


def ordinal_boundary_bce_loss(
    logits: torch.Tensor,
    target: torch.Tensor,
    *,
    class_weights: torch.Tensor | None = None,
    focal_gamma: float = 0.0,
    boundary_focus: float = 0.0,
) -> torch.Tensor:
    if logits.ndim != 2:
        raise ValueError("Ordinal boundary loss expects logits with shape [batch, classes].")
    n_classes = int(logits.shape[1])
    if n_classes <= 2:
        return logits.new_tensor(0.0)
    labels = target.to(device=logits.device, dtype=torch.long).clamp(0, n_classes - 1)
    proba = torch.softmax(logits, dim=1)
    greater_than = torch.flip(torch.cumsum(torch.flip(proba, dims=[1]), dim=1), dims=[1])[:, 1:]
    greater_than = greater_than.clamp(1.0e-6, 1.0 - 1.0e-6)
    thresholds = torch.arange(n_classes - 1, device=logits.device).view(1, -1)
    binary_target = labels.view(-1, 1).gt(thresholds).to(dtype=logits.dtype)
    per_boundary = F.binary_cross_entropy(greater_than, binary_target, reduction="none")
    gamma = float(max(0.0, focal_gamma))
    if gamma > 1.0e-8:
        pt = binary_target * greater_than + (1.0 - binary_target) * (1.0 - greater_than)
        per_boundary = per_boundary * torch.pow(torch.clamp(1.0 - pt, min=0.0, max=1.0), gamma)
    focus = float(max(0.0, boundary_focus))
    if focus > 0.0:
        centers = thresholds.to(dtype=logits.dtype) + 0.5
        distance = torch.abs(centers - labels.view(-1, 1).to(dtype=logits.dtype))
        boundary_weight = 1.0 + focus / (1.0 + distance)
        boundary_weight = boundary_weight / torch.clamp(boundary_weight.mean(dim=1, keepdim=True), min=1.0e-6)
        per_boundary = per_boundary * boundary_weight
    per_sample = per_boundary.mean(dim=1)
    if class_weights is not None and class_weights.numel() == n_classes:
        weights = class_weights.to(device=logits.device, dtype=logits.dtype)[labels]
        return torch.sum(per_sample * weights) / torch.clamp(torch.sum(weights), min=1.0e-6)
    return torch.mean(per_sample)


def supervised_classification_loss(
    logits: torch.Tensor,
    target: torch.Tensor,
    *,
    class_weights: torch.Tensor | None = None,
    focal_gamma: float = 0.0,
    label_smoothing: float = 0.0,
) -> torch.Tensor:
    smoothing = float(min(0.30, max(0.0, label_smoothing)))
    gamma = float(max(0.0, focal_gamma))
    weights = class_weights.to(device=logits.device, dtype=logits.dtype) if class_weights is not None else None
    if gamma <= 1.0e-8:
        return F.cross_entropy(logits, target, weight=weights, label_smoothing=smoothing)
    ce = F.cross_entropy(
        logits,
        target,
        weight=weights,
        label_smoothing=smoothing,
        reduction="none",
    )
    labels = target.to(device=logits.device, dtype=torch.long).clamp(0, logits.shape[1] - 1)
    proba = torch.softmax(logits, dim=1).gather(1, labels.view(-1, 1)).squeeze(1)
    focal = torch.pow(torch.clamp(1.0 - proba, min=0.0, max=1.0), gamma)
    return torch.mean(focal * ce)


def _temporal_prototype_features(windows: np.ndarray) -> np.ndarray:
    values = np.asarray(windows, dtype=np.float32)
    if values.ndim != 3:
        raise ValueError("Prototype evidence expects windows with shape [samples, time, features].")
    last = values[:, -1, :]
    mean = values.mean(axis=1)
    std = values.std(axis=1)
    delta = values[:, -1, :] - values[:, 0, :]
    if values.shape[1] > 1:
        time_axis = np.linspace(-1.0, 1.0, num=values.shape[1], dtype=np.float32).reshape(1, -1, 1)
        centered = values - mean[:, None, :]
        slope = np.sum(centered * time_axis, axis=1) / max(float(np.sum(time_axis * time_axis)), 1.0e-6)
    else:
        slope = np.zeros_like(last)
    features = np.concatenate([last, mean, std, delta, slope], axis=1)
    return np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)


def prototype_distance_evidence(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_eval: np.ndarray,
    *,
    n_classes: int,
    shrinkage: float = 0.10,
) -> tuple[np.ndarray, dict[str, Any]]:
    train_features = _temporal_prototype_features(x_train)
    eval_features = _temporal_prototype_features(x_eval)
    labels = np.asarray(y_train, dtype=np.int64).reshape(-1)
    n_cls = int(max(1, n_classes))
    global_center = train_features.mean(axis=0)
    global_var = np.var(train_features, axis=0) + 1.0e-3
    centers = np.zeros((n_cls, train_features.shape[1]), dtype=np.float32)
    scales = np.zeros_like(centers)
    counts: list[int] = []
    for cls in range(n_cls):
        cls_features = train_features[labels == cls]
        counts.append(int(len(cls_features)))
        if len(cls_features) == 0:
            centers[cls] = global_center
            scales[cls] = global_var
            continue
        centers[cls] = cls_features.mean(axis=0)
        cls_var = np.var(cls_features, axis=0) + 1.0e-3
        mix = float(min(0.95, max(0.0, shrinkage)))
        scales[cls] = (1.0 - mix) * cls_var + mix * global_var
    diff = eval_features[:, None, :] - centers[None, :, :]
    distance = np.mean((diff * diff) / np.maximum(scales[None, :, :], 1.0e-4), axis=2)
    return distance.astype(np.float64), {
        "feature_mode": "last_mean_std_delta_slope",
        "n_features": int(train_features.shape[1]),
        "class_counts": [int(value) for value in counts],
        "shrinkage": float(min(0.95, max(0.0, shrinkage))),
    }


def _softmax_numpy(logits: np.ndarray) -> np.ndarray:
    z = np.asarray(logits, dtype=np.float64)
    z = z - np.max(z, axis=1, keepdims=True)
    exp = np.exp(np.clip(z, -80.0, 80.0))
    return exp / np.maximum(np.sum(exp, axis=1, keepdims=True), 1.0e-12)


def _sigmoid_numpy(logits: np.ndarray) -> np.ndarray:
    z = np.asarray(logits, dtype=np.float64)
    z = np.clip(z, -80.0, 80.0)
    return 1.0 / (1.0 + np.exp(-z))


def _normalize_proba(proba: np.ndarray) -> np.ndarray:
    p = np.asarray(proba, dtype=np.float64)
    p = np.clip(p, 1.0e-12, 1.0)
    return p / np.maximum(np.sum(p, axis=1, keepdims=True), 1.0e-12)


def _parse_float_grid(text: str | Sequence[float], *, default: Sequence[float]) -> list[float]:
    if isinstance(text, str):
        values = [part.strip() for part in text.split(",") if part.strip()]
        out = [float(value) for value in values]
    else:
        out = [float(value) for value in text]
    out = [float(value) for value in out if np.isfinite(float(value)) and float(value) > 0.0]
    return out or [float(value) for value in default]


def _validation_primary_metrics(y_true: Sequence[int] | np.ndarray, proba: np.ndarray) -> dict[str, Any]:
    threshold = tune_binary_threshold(y_true, proba)
    metrics = summarize_classification(y_true, proba)
    if threshold is not None:
        thresholded = summarize_classification(y_true, proba, positive_threshold=threshold)
        return {
            "metrics": thresholded,
            "threshold": float(threshold),
            "raw_metrics": metrics,
        }
    return {"metrics": metrics, "threshold": None, "raw_metrics": metrics}


def apply_prototype_posterior_fusion(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray,
    y_val: np.ndarray,
    x_test: np.ndarray,
    val_proba: np.ndarray,
    test_proba: np.ndarray,
    *,
    n_classes: int,
    max_blend: float = 0.50,
    blend_steps: int = 11,
    temperature_grid: str | Sequence[float] = (0.25, 0.50, 1.0, 2.0, 4.0),
    min_val_gain: float = 0.0,
    shrinkage: float = 0.10,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    base_val = _normalize_proba(val_proba)
    base_test = _normalize_proba(test_proba)
    val_distance, evidence_diag = prototype_distance_evidence(
        x_train,
        y_train,
        x_val,
        n_classes=n_classes,
        shrinkage=shrinkage,
    )
    test_distance, _ = prototype_distance_evidence(
        x_train,
        y_train,
        x_test,
        n_classes=n_classes,
        shrinkage=shrinkage,
    )
    temperatures = _parse_float_grid(temperature_grid, default=(0.25, 0.50, 1.0, 2.0, 4.0))
    max_weight = float(min(1.0, max(0.0, max_blend)))
    steps = max(2, int(blend_steps))
    blend_grid = np.linspace(0.0, max_weight, num=steps, dtype=np.float64)
    base_selection = _validation_primary_metrics(y_val, base_val)
    base_metrics = base_selection["metrics"]
    base_score = float(base_metrics["macro_f1"])
    best_score = base_score
    best_bal = float(base_metrics["balanced_accuracy"])
    best_threshold = base_selection["threshold"]
    best_temperature = float(temperatures[0])
    best_blend = 0.0
    best_val = base_val
    best_test = base_test
    candidates: list[dict[str, float]] = []
    log_base_val = np.log(np.clip(base_val, 1.0e-12, 1.0))
    log_base_test = np.log(np.clip(base_test, 1.0e-12, 1.0))
    for temperature in temperatures:
        proto_val = _softmax_numpy(-val_distance / max(float(temperature), 1.0e-6))
        proto_test = _softmax_numpy(-test_distance / max(float(temperature), 1.0e-6))
        log_proto_val = np.log(np.clip(proto_val, 1.0e-12, 1.0))
        log_proto_test = np.log(np.clip(proto_test, 1.0e-12, 1.0))
        for blend in blend_grid:
            if blend <= 1.0e-12:
                fused_val = base_val
            else:
                fused_val = _softmax_numpy((1.0 - float(blend)) * log_base_val + float(blend) * log_proto_val)
            selection = _validation_primary_metrics(y_val, fused_val)
            metrics = selection["metrics"]
            score = float(metrics["macro_f1"])
            bal = float(metrics["balanced_accuracy"])
            candidates.append(
                {
                    "temperature": float(temperature),
                    "blend": float(blend),
                    "macro_f1": score,
                    "balanced_accuracy": bal,
                    "threshold": selection["threshold"],
                }
            )
            better = score > best_score + 1.0e-12 or (
                abs(score - best_score) <= 1.0e-12 and float(blend) < best_blend
            )
            if better:
                best_score = score
                best_bal = bal
                best_threshold = selection["threshold"]
                best_temperature = float(temperature)
                best_blend = float(blend)
                best_val = fused_val
                if blend <= 1.0e-12:
                    best_test = base_test
                else:
                    best_test = _softmax_numpy(
                        (1.0 - float(blend)) * log_base_test + float(blend) * log_proto_test
                    )
    val_gain = float(best_score - base_score)
    if best_blend <= 1.0e-12 or val_gain < float(min_val_gain):
        best_score = base_score
        best_bal = float(base_metrics["balanced_accuracy"])
        best_threshold = base_selection["threshold"]
        best_blend = 0.0
        best_val = base_val
        best_test = base_test
    candidates.sort(key=lambda item: (-item["macro_f1"], -item["balanced_accuracy"], item["blend"]))
    diagnostics = {
        "enabled": True,
        "source": "train_only_temporal_class_prototypes",
        "accepted": bool(best_blend > 0.0),
        "selected_blend": float(best_blend),
        "selected_temperature": float(best_temperature),
        "selected_validation_threshold": best_threshold,
        "max_blend": float(max_weight),
        "blend_steps": int(steps),
        "temperature_grid": [float(value) for value in temperatures],
        "min_val_gain": float(min_val_gain),
        "base_val_macro_f1": float(base_score),
        "selected_val_macro_f1": float(best_score),
        "selected_val_balanced_accuracy": float(best_bal),
        "val_macro_f1_gain": float(best_score - base_score),
        "top_candidates": candidates[:8],
        "evidence": evidence_diag,
    }
    return best_val.astype(np.float64), best_test.astype(np.float64), diagnostics


def one_class_normality_evidence(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_eval: np.ndarray,
    *,
    normal_class: int = 0,
    shrinkage: float = 0.15,
) -> tuple[np.ndarray, dict[str, Any]]:
    train_features = _temporal_prototype_features(x_train)
    eval_features = _temporal_prototype_features(x_eval)
    labels = np.asarray(y_train, dtype=np.int64).reshape(-1)
    normal = train_features[labels == int(normal_class)]
    if len(normal) < 2:
        normal = train_features
    center = np.median(normal, axis=0)
    normal_mad = 1.4826 * np.median(np.abs(normal - center[None, :]), axis=0) + 1.0e-3
    global_std = np.std(train_features, axis=0) + 1.0e-3
    mix = float(min(0.95, max(0.0, shrinkage)))
    scale = np.maximum((1.0 - mix) * normal_mad + mix * global_std, 1.0e-3)
    normal_distance = np.mean(((normal - center[None, :]) / scale[None, :]) ** 2, axis=1)
    eval_distance = np.mean(((eval_features - center[None, :]) / scale[None, :]) ** 2, axis=1)
    distance_center = float(np.median(normal_distance))
    q25, q75 = np.percentile(normal_distance, [25.0, 75.0])
    distance_scale = max(float(q75 - q25), float(distance_center), 1.0)
    z_score = (eval_distance - distance_center) / distance_scale
    return np.asarray(z_score, dtype=np.float64), {
        "feature_mode": "last_mean_std_delta_slope",
        "normal_class": int(normal_class),
        "normal_count": int(len(normal)),
        "n_features": int(train_features.shape[1]),
        "shrinkage": float(mix),
        "normal_distance_median": float(distance_center),
        "normal_distance_iqr": float(distance_scale),
    }


def apply_one_class_posterior_fusion(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray,
    y_val: np.ndarray,
    x_test: np.ndarray,
    val_proba: np.ndarray,
    test_proba: np.ndarray,
    *,
    n_classes: int,
    normal_class: int = 0,
    max_blend: float = 0.35,
    blend_steps: int = 8,
    temperature_grid: str | Sequence[float] = (0.25, 0.50, 1.0, 2.0),
    threshold_grid: str | Sequence[float] = (-0.50, 0.0, 0.50, 1.0, 1.50, 2.0, 3.0),
    min_val_gain: float = 0.0,
    shrinkage: float = 0.15,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    base_val = _normalize_proba(val_proba)
    base_test = _normalize_proba(test_proba)
    if int(n_classes) != 2:
        return base_val, base_test, {"enabled": False, "status": "requires_binary_task", "n_classes": int(n_classes)}
    labels = np.asarray(y_train, dtype=np.int64).reshape(-1)
    if int(np.count_nonzero(labels == int(normal_class))) < 2:
        return base_val, base_test, {"enabled": False, "status": "insufficient_normal_samples"}
    val_score, evidence_diag = one_class_normality_evidence(
        x_train,
        y_train,
        x_val,
        normal_class=normal_class,
        shrinkage=shrinkage,
    )
    test_score, _ = one_class_normality_evidence(
        x_train,
        y_train,
        x_test,
        normal_class=normal_class,
        shrinkage=shrinkage,
    )
    temperatures = _parse_float_grid(temperature_grid, default=(0.25, 0.50, 1.0, 2.0))
    if isinstance(threshold_grid, str):
        thresholds = [float(part.strip()) for part in threshold_grid.split(",") if part.strip()]
    else:
        thresholds = [float(value) for value in threshold_grid]
    thresholds = [float(value) for value in thresholds if np.isfinite(float(value))]
    thresholds = thresholds or [0.0, 0.50, 1.0, 1.50, 2.0]
    max_weight = float(min(1.0, max(0.0, max_blend)))
    steps = max(2, int(blend_steps))
    blend_grid = np.linspace(0.0, max_weight, num=steps, dtype=np.float64)
    base_selection = _validation_primary_metrics(y_val, base_val)
    base_metrics = base_selection["metrics"]
    base_score = float(base_metrics["macro_f1"])
    best_score = base_score
    best_bal = float(base_metrics["balanced_accuracy"])
    best_threshold = base_selection["threshold"]
    best_temperature = float(temperatures[0])
    best_distance_threshold = float(thresholds[0])
    best_blend = 0.0
    best_val = base_val
    best_test = base_test
    log_base_val = np.log(np.clip(base_val, 1.0e-12, 1.0))
    log_base_test = np.log(np.clip(base_test, 1.0e-12, 1.0))
    candidates: list[dict[str, float]] = []
    for temperature in temperatures:
        temp = max(float(temperature), 1.0e-6)
        for distance_threshold in thresholds:
            val_anomaly = _sigmoid_numpy((val_score - float(distance_threshold)) / temp)
            test_anomaly = _sigmoid_numpy((test_score - float(distance_threshold)) / temp)
            normal_idx = int(normal_class)
            anomaly_idx = 1 - normal_idx
            one_val = np.zeros_like(base_val, dtype=np.float64)
            one_test = np.zeros_like(base_test, dtype=np.float64)
            one_val[:, anomaly_idx] = val_anomaly
            one_val[:, normal_idx] = 1.0 - val_anomaly
            one_test[:, anomaly_idx] = test_anomaly
            one_test[:, normal_idx] = 1.0 - test_anomaly
            log_one_val = np.log(np.clip(one_val, 1.0e-12, 1.0))
            log_one_test = np.log(np.clip(one_test, 1.0e-12, 1.0))
            for blend in blend_grid:
                if blend <= 1.0e-12:
                    fused_val = base_val
                else:
                    fused_val = _softmax_numpy((1.0 - float(blend)) * log_base_val + float(blend) * log_one_val)
                selection = _validation_primary_metrics(y_val, fused_val)
                metrics = selection["metrics"]
                score = float(metrics["macro_f1"])
                bal = float(metrics["balanced_accuracy"])
                candidates.append(
                    {
                        "temperature": float(temperature),
                        "distance_threshold": float(distance_threshold),
                        "blend": float(blend),
                        "macro_f1": score,
                        "balanced_accuracy": bal,
                        "threshold": selection["threshold"],
                    }
                )
                better = score > best_score + 1.0e-12 or (
                    abs(score - best_score) <= 1.0e-12 and float(blend) < best_blend
                )
                if better:
                    best_score = score
                    best_bal = bal
                    best_threshold = selection["threshold"]
                    best_temperature = float(temperature)
                    best_distance_threshold = float(distance_threshold)
                    best_blend = float(blend)
                    best_val = fused_val
                    best_test = (
                        base_test
                        if blend <= 1.0e-12
                        else _softmax_numpy((1.0 - float(blend)) * log_base_test + float(blend) * log_one_test)
                    )
    val_gain = float(best_score - base_score)
    if best_blend <= 1.0e-12 or val_gain < float(min_val_gain):
        best_score = base_score
        best_bal = float(base_metrics["balanced_accuracy"])
        best_threshold = base_selection["threshold"]
        best_blend = 0.0
        best_val = base_val
        best_test = base_test
    candidates.sort(key=lambda item: (-item["macro_f1"], -item["balanced_accuracy"], item["blend"]))
    return best_val.astype(np.float64), best_test.astype(np.float64), {
        "enabled": True,
        "source": "train_only_one_class_normality",
        "accepted": bool(best_blend > 0.0),
        "selected_blend": float(best_blend),
        "selected_temperature": float(best_temperature),
        "selected_distance_threshold": float(best_distance_threshold),
        "selected_validation_threshold": best_threshold,
        "max_blend": float(max_weight),
        "blend_steps": int(steps),
        "temperature_grid": [float(value) for value in temperatures],
        "distance_threshold_grid": [float(value) for value in thresholds],
        "min_val_gain": float(min_val_gain),
        "base_val_macro_f1": float(base_score),
        "selected_val_macro_f1": float(best_score),
        "selected_val_balanced_accuracy": float(best_bal),
        "val_macro_f1_gain": float(best_score - base_score),
        "top_candidates": candidates[:8],
        "evidence": evidence_diag,
    }


def _ordinal_threshold_posterior(
    scores: np.ndarray,
    thresholds: Sequence[float],
    *,
    n_classes: int,
    smoothing: float,
) -> np.ndarray:
    score = np.asarray(scores, dtype=np.float64).reshape(-1)
    edges = np.asarray(thresholds, dtype=np.float64).reshape(-1)
    pred = np.searchsorted(edges, score, side="right").clip(0, int(n_classes) - 1)
    eps = float(np.clip(smoothing, 0.0, 0.45))
    posterior = np.full((len(score), int(n_classes)), eps / max(1, int(n_classes) - 1), dtype=np.float64)
    posterior[np.arange(len(score)), pred.astype(int)] = 1.0 - eps
    return _normalize_proba(posterior)


def _ordinal_threshold_candidates(scores: np.ndarray, *, n_classes: int, max_candidates: int = 21) -> list[tuple[float, ...]]:
    score = np.asarray(scores, dtype=np.float64).reshape(-1)
    if len(score) == 0 or int(n_classes) <= 2:
        return []
    percentiles = np.linspace(2.5, 97.5, num=max(7, min(int(max_candidates), 31)))
    values = np.percentile(score, percentiles)
    values = np.concatenate([values, np.linspace(0.0, float(n_classes - 1), num=int(n_classes) * 3 + 1)])
    values = np.unique(np.round(values.astype(np.float64), 6))
    values = values[np.isfinite(values)]
    values = values[(values > -0.50) & (values < float(n_classes) - 0.50)]
    if len(values) < int(n_classes) - 1:
        values = np.linspace(0.5, float(n_classes) - 1.5, num=int(n_classes) - 1)
    from itertools import combinations

    candidates = [tuple(float(v) for v in combo) for combo in combinations(values.tolist(), int(n_classes) - 1)]
    if not candidates:
        candidates = [tuple(np.linspace(0.5, float(n_classes) - 1.5, num=int(n_classes) - 1).tolist())]
    return candidates


def apply_ordinal_threshold_posterior_calibration(
    y_val: np.ndarray,
    val_proba: np.ndarray,
    test_proba: np.ndarray,
    *,
    n_classes: int,
    max_blend: float = 0.50,
    blend_steps: int = 11,
    smoothing: float = 0.03,
    min_val_gain: float = 0.0,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    base_val = _normalize_proba(val_proba)
    base_test = _normalize_proba(test_proba)
    n_cls = int(n_classes)
    if n_cls <= 2:
        return base_val, base_test, {"enabled": False, "status": "requires_multiclass_ordinal", "n_classes": n_cls}
    class_axis = np.arange(n_cls, dtype=np.float64)
    val_score = base_val @ class_axis
    test_score = base_test @ class_axis
    threshold_candidates = _ordinal_threshold_candidates(val_score, n_classes=n_cls, max_candidates=21)
    max_weight = float(min(1.0, max(0.0, max_blend)))
    steps = max(2, int(blend_steps))
    blend_grid = np.linspace(0.0, max_weight, num=steps, dtype=np.float64)
    base_selection = _validation_primary_metrics(y_val, base_val)
    base_metrics = base_selection["metrics"]
    base_score = float(base_metrics["macro_f1"])
    best_score = base_score
    best_bal = float(base_metrics["balanced_accuracy"])
    best_blend = 0.0
    best_thresholds: tuple[float, ...] = tuple()
    best_val = base_val
    best_test = base_test
    log_base_val = np.log(np.clip(base_val, 1.0e-12, 1.0))
    log_base_test = np.log(np.clip(base_test, 1.0e-12, 1.0))
    candidates: list[dict[str, Any]] = []
    for thresholds in threshold_candidates:
        ordinal_val = _ordinal_threshold_posterior(val_score, thresholds, n_classes=n_cls, smoothing=smoothing)
        ordinal_test = _ordinal_threshold_posterior(test_score, thresholds, n_classes=n_cls, smoothing=smoothing)
        log_ordinal_val = np.log(np.clip(ordinal_val, 1.0e-12, 1.0))
        log_ordinal_test = np.log(np.clip(ordinal_test, 1.0e-12, 1.0))
        for blend in blend_grid:
            if blend <= 1.0e-12:
                fused_val = base_val
            else:
                fused_val = _softmax_numpy((1.0 - float(blend)) * log_base_val + float(blend) * log_ordinal_val)
            selection = _validation_primary_metrics(y_val, fused_val)
            metrics = selection["metrics"]
            score = float(metrics["macro_f1"])
            bal = float(metrics["balanced_accuracy"])
            if len(candidates) < 256 or score >= best_score:
                candidates.append(
                    {
                        "thresholds": [float(value) for value in thresholds],
                        "blend": float(blend),
                        "macro_f1": score,
                        "balanced_accuracy": bal,
                    }
                )
            better = score > best_score + 1.0e-12 or (
                abs(score - best_score) <= 1.0e-12 and float(blend) < best_blend
            )
            if better:
                best_score = score
                best_bal = bal
                best_blend = float(blend)
                best_thresholds = tuple(float(value) for value in thresholds)
                best_val = fused_val
                best_test = (
                    base_test
                    if blend <= 1.0e-12
                    else _softmax_numpy((1.0 - float(blend)) * log_base_test + float(blend) * log_ordinal_test)
                )
    val_gain = float(best_score - base_score)
    if best_blend <= 1.0e-12 or val_gain < float(min_val_gain):
        best_score = base_score
        best_bal = float(base_metrics["balanced_accuracy"])
        best_blend = 0.0
        best_thresholds = tuple()
        best_val = base_val
        best_test = base_test
    candidates.sort(key=lambda item: (-float(item["macro_f1"]), -float(item["balanced_accuracy"]), float(item["blend"])))
    return best_val.astype(np.float64), best_test.astype(np.float64), {
        "enabled": True,
        "source": "validation_tuned_expected_stage_thresholds",
        "accepted": bool(best_blend > 0.0),
        "selected_blend": float(best_blend),
        "selected_thresholds": [float(value) for value in best_thresholds],
        "max_blend": float(max_weight),
        "blend_steps": int(steps),
        "smoothing": float(np.clip(smoothing, 0.0, 0.45)),
        "candidate_threshold_count": int(len(threshold_candidates)),
        "min_val_gain": float(min_val_gain),
        "base_val_macro_f1": float(base_score),
        "selected_val_macro_f1": float(best_score),
        "selected_val_balanced_accuracy": float(best_bal),
        "val_macro_f1_gain": float(best_score - base_score),
        "top_candidates": candidates[:8],
    }


def build_health_index_targets(
    task: ReadyTask,
    *,
    rul_cap: float = 125.0,
) -> np.ndarray | None:
    if "rul" not in task.meta.columns:
        return None
    rul = pd.to_numeric(task.meta["rul"], errors="coerce").to_numpy(dtype=np.float64)
    finite = np.isfinite(rul)
    if not bool(np.any(finite)):
        return None
    fill = float(np.nanmedian(rul[finite]))
    values = np.nan_to_num(rul, nan=fill, posinf=fill, neginf=fill)
    cap = float(max(1.0, rul_cap))
    health = 1.0 - np.clip(values, 0.0, cap) / cap
    return np.asarray(np.clip(health, 0.0, 1.0), dtype=np.float32)


def health_mae(y_true: np.ndarray | None, y_pred: np.ndarray | None) -> float | None:
    if y_true is None or y_pred is None:
        return None
    true = np.asarray(y_true, dtype=np.float32).reshape(-1)
    pred = np.asarray(y_pred, dtype=np.float32).reshape(-1)
    if true.shape != pred.shape or true.size == 0:
        return None
    return float(np.mean(np.abs(true - pred)))


def build_rul_targets(task: ReadyTask) -> np.ndarray | None:
    if "rul" not in task.meta.columns:
        return None
    rul = pd.to_numeric(task.meta["rul"], errors="coerce").to_numpy(dtype=np.float64)
    finite = np.isfinite(rul)
    if not bool(np.any(finite)):
        return None
    fill = float(np.nanmedian(rul[finite]))
    values = np.nan_to_num(rul, nan=fill, posinf=fill, neginf=fill)
    return np.asarray(np.maximum(values, 0.0), dtype=np.float32)


def build_capped_rul_targets(task: ReadyTask, *, rul_cap: float = 125.0) -> np.ndarray | None:
    rul = build_rul_targets(task)
    if rul is None:
        return None
    cap = float(max(1.0, rul_cap))
    return np.asarray(np.clip(rul, 0.0, cap) / cap, dtype=np.float32)


def rul_regression_metrics(
    y_true: np.ndarray | None,
    y_pred: np.ndarray | None,
) -> dict[str, float] | None:
    if y_true is None or y_pred is None:
        return None
    true = np.asarray(y_true, dtype=np.float64).reshape(-1)
    pred = np.asarray(y_pred, dtype=np.float64).reshape(-1)
    if true.shape != pred.shape or true.size == 0:
        return None
    finite = np.isfinite(true) & np.isfinite(pred)
    if not bool(np.any(finite)):
        return None
    true = true[finite]
    pred = pred[finite]
    err = pred - true
    score = np.where(err < 0.0, np.exp(-err / 13.0) - 1.0, np.exp(err / 10.0) - 1.0)
    return {
        "rul_mae": float(np.mean(np.abs(err))),
        "rul_rmse": float(np.sqrt(np.mean(err * err))),
        "rul_score": float(np.sum(score)),
    }


def build_rul_prediction_records(
    meta: pd.DataFrame,
    indices: np.ndarray,
    y_true: np.ndarray | None,
    y_pred: np.ndarray | None,
    *,
    prediction_source: str,
) -> list[dict[str, Any]]:
    if y_true is None or y_pred is None:
        return []
    true = np.asarray(y_true, dtype=np.float64).reshape(-1)
    pred = np.asarray(y_pred, dtype=np.float64).reshape(-1)
    idx = np.asarray(indices, dtype=np.int64).reshape(-1)
    if true.shape != pred.shape or true.shape != idx.shape:
        return []
    rows: list[dict[str, Any]] = []
    view = meta.iloc[idx].reset_index(drop=True)
    for pos, row in view.iterrows():
        item: dict[str, Any] = {
            "row_index": int(idx[pos]),
            "rul_true": float(true[pos]),
            "rul_pred": float(pred[pos]),
            "rul_error": float(pred[pos] - true[pos]),
            "prediction_source": str(prediction_source),
        }
        for col in ("record_id", "subset", "split_role", "unit", "cycle"):
            if col in view.columns:
                value = row[col]
                if pd.isna(value):
                    item[col] = None
                elif col in {"unit", "cycle"}:
                    item[col] = int(value)
                else:
                    item[col] = str(value)
        rows.append(item)
    return rows


def build_classification_prediction_records(
    meta: pd.DataFrame,
    indices: np.ndarray,
    y_true: np.ndarray,
    proba: np.ndarray,
    *,
    class_id_mapping: Mapping[str, int] | Mapping[int, int] | None = None,
    positive_threshold: float | None = None,
) -> list[dict[str, Any]]:
    idx = np.asarray(indices, dtype=np.int64).reshape(-1)
    y = np.asarray(y_true, dtype=np.int64).reshape(-1)
    p = np.asarray(proba, dtype=np.float64)
    if p.ndim != 2 or len(idx) != len(y) or len(idx) != p.shape[0]:
        return []
    inverse_mapping: dict[int, int] = {}
    if class_id_mapping:
        for raw, internal in dict(class_id_mapping).items():
            try:
                inverse_mapping[int(internal)] = int(raw)
            except (TypeError, ValueError):
                continue
    if p.shape[1] == 2 and positive_threshold is not None:
        pred = (p[:, 1] >= float(positive_threshold)).astype(np.int64)
    else:
        pred = np.argmax(p, axis=1).astype(np.int64)
    threshold_value = None if positive_threshold is None else float(positive_threshold)
    rows: list[dict[str, Any]] = []
    view = meta.iloc[idx].reset_index(drop=True)
    metadata_cols = [
        "record_id",
        "subset",
        "split_role",
        "unit",
        "cycle",
        "run_id",
        "run_group",
        "datetime",
        "anomaly",
        "changepoint",
    ]
    for pos, row in view.iterrows():
        y_true_internal = int(y[pos])
        y_pred_internal = int(pred[pos])
        item: dict[str, Any] = {
            "row_index": int(idx[pos]),
            "y_true_internal": y_true_internal,
            "y_pred_internal": y_pred_internal,
            "y_true_original": int(inverse_mapping.get(y_true_internal, y_true_internal)),
            "y_pred_original": int(inverse_mapping.get(y_pred_internal, y_pred_internal)),
            "proba": [float(value) for value in p[pos].reshape(-1)],
            "positive_score": float(p[pos, 1]) if p.shape[1] == 2 else None,
            "positive_threshold": threshold_value,
        }
        for col in metadata_cols:
            if col not in view.columns:
                continue
            value = row[col]
            if pd.isna(value):
                item[col] = None
            elif col in {"unit", "cycle", "anomaly", "changepoint"}:
                item[col] = int(value)
            else:
                item[col] = str(value)
        rows.append(item)
    return rows


def summarize_rul_by_subset(records: Sequence[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        return {"enabled": False, "rows": []}
    frame = pd.DataFrame(list(records))
    if "subset" not in frame.columns:
        return {"enabled": False, "rows": []}
    rows: list[dict[str, Any]] = []
    for subset, group in frame.groupby("subset", sort=True):
        metrics = rul_regression_metrics(group["rul_true"].to_numpy(), group["rul_pred"].to_numpy()) or {}
        rows.append(
            {
                "subset": str(subset),
                "n_units": int(group["unit"].nunique()) if "unit" in group.columns else int(len(group)),
                "n_samples": int(len(group)),
                **{key: float(value) for key, value in metrics.items()},
            }
        )
    return {"enabled": True, "rows": rows}


def predict_rul_from_health(health_pred: np.ndarray | None, *, rul_cap: float) -> np.ndarray | None:
    if health_pred is None:
        return None
    cap = float(max(1.0, rul_cap))
    health = np.asarray(health_pred, dtype=np.float32).reshape(-1)
    return np.asarray((1.0 - np.clip(health, 0.0, 1.0)) * cap, dtype=np.float32)


def predict_rul_from_normalized(rul_norm_pred: np.ndarray | None, *, rul_cap: float) -> np.ndarray | None:
    if rul_norm_pred is None:
        return None
    cap = float(max(1.0, rul_cap))
    norm = np.asarray(rul_norm_pred, dtype=np.float32).reshape(-1)
    return np.asarray(np.clip(norm, 0.0, 1.0) * cap, dtype=np.float32)


def apply_regime_prototype_residuals(
    task: ReadyTask,
    train_idx: np.ndarray,
    y_internal: np.ndarray,
    *,
    n_regimes: int = 6,
    healthy_stage_max: int = 0,
    seed: int = 42,
) -> tuple[ReadyTask, dict[str, Any]]:
    regime_cols = [col for col in task.feature_cols if str(col).startswith("op_setting")]
    residual_cols = [
        col
        for col in task.feature_cols
        if col not in set(regime_cols) and str(col) != str(task.order_col or "")
    ]
    if not regime_cols or not residual_cols:
        return task, {
            "enabled": False,
            "reason": "missing_regime_or_residual_columns",
            "regime_cols": regime_cols,
            "residual_cols": residual_cols,
        }

    idx_train = np.asarray(train_idx, dtype=np.int64)
    values = task.x[task.feature_cols].apply(pd.to_numeric, errors="coerce")
    train_values = values.iloc[idx_train]
    medians = train_values.median(numeric_only=True)
    filled = values.fillna(medians).fillna(0.0)

    regime_values = filled[regime_cols].to_numpy(dtype=np.float64)
    train_regime_values = regime_values[idx_train]
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    train_regime_scaled = scaler.fit_transform(imputer.fit_transform(train_regime_values))
    all_regime_scaled = scaler.transform(imputer.transform(regime_values))
    requested_k = max(1, int(n_regimes))
    actual_k = min(requested_k, max(1, len(idx_train)))
    if actual_k <= 1:
        regime_id = np.zeros(len(task.x), dtype=np.int64)
    else:
        kmeans = KMeans(n_clusters=actual_k, random_state=int(seed), n_init=10)
        kmeans.fit(train_regime_scaled)
        regime_id = kmeans.predict(all_regime_scaled).astype(np.int64)

    feature_index = {str(col): pos for pos, col in enumerate(task.feature_cols)}
    residual_positions = [feature_index[str(col)] for col in residual_cols]
    filled_matrix = filled[task.feature_cols].to_numpy(dtype=np.float64)
    out_matrix = filled_matrix.copy()
    y = np.asarray(y_internal, dtype=np.int64)
    train_health_mask = y[idx_train] <= int(healthy_stage_max)
    global_healthy_idx = idx_train[train_health_mask]
    if len(global_healthy_idx) == 0:
        global_healthy_idx = idx_train
    baseline_counts: dict[str, int] = {}
    for regime in sorted(np.unique(regime_id[idx_train])):
        regime_train_idx = idx_train[regime_id[idx_train] == int(regime)]
        baseline_idx = regime_train_idx[y[regime_train_idx] <= int(healthy_stage_max)]
        if len(baseline_idx) == 0:
            baseline_idx = global_healthy_idx
        if len(baseline_idx) == 0:
            baseline_idx = regime_train_idx
        baseline_counts[str(int(regime))] = int(len(baseline_idx))
        baseline = np.nanmedian(filled_matrix[baseline_idx][:, residual_positions], axis=0)
        sample_mask = regime_id == int(regime)
        out_matrix[np.ix_(sample_mask, residual_positions)] = (
            filled_matrix[np.ix_(sample_mask, residual_positions)] - baseline.reshape(1, -1)
        )

    x_new = task.x.copy()
    for col, pos in zip(residual_cols, residual_positions):
        x_new[str(col)] = out_matrix[:, pos].astype(np.float32)
    return (
        ReadyTask(
            dataset=task.dataset,
            target=task.target,
            task=task.task,
            x=x_new,
            meta=task.meta,
            labels=task.labels,
            feature_cols=task.feature_cols,
            group_cols=task.group_cols,
            order_col=task.order_col,
            ready_dir=task.ready_dir,
        ),
        {
            "enabled": True,
            "source": "train_only_regime_healthy_prototype_residuals",
            "regime_cols": list(map(str, regime_cols)),
            "residual_cols": list(map(str, residual_cols)),
            "n_residual_cols": int(len(residual_cols)),
            "requested_regimes": int(requested_k),
            "actual_regimes": int(actual_k),
            "healthy_stage_max": int(healthy_stage_max),
            "global_healthy_count": int(len(global_healthy_idx)),
            "baseline_counts": baseline_counts,
        },
    )


def name_top_paths(index_rows: Sequence[Mapping[str, Any]], feature_cols: Sequence[str], *, limit: int = 20) -> list[dict[str, Any]]:
    names = list(map(str, feature_cols))
    out: list[dict[str, Any]] = []
    for row in list(index_rows)[: int(limit)]:
        src = int(row.get("source_index", -1))
        bridge = int(row.get("bridge_index", -1))
        dst = int(row.get("target_index", -1))
        src_name = names[src] if 0 <= src < len(names) else f"feature_{src}"
        bridge_name = names[bridge] if 0 <= bridge < len(names) else ""
        dst_name = names[dst] if 0 <= dst < len(names) else f"feature_{dst}"
        path = f"{src_name} -> {bridge_name} -> {dst_name}" if bridge_name else f"{src_name} -> {dst_name}"
        out.append(
            {
                **dict(row),
                "source": src_name,
                "bridge": bridge_name,
                "target": dst_name,
                "path": path,
                "group_path": (
                    "{} -> {} -> {}".format(
                        feature_group_name(src_name),
                        feature_group_name(bridge_name),
                        feature_group_name(dst_name),
                    )
                    if bridge_name
                    else "{} -> {}".format(feature_group_name(src_name), feature_group_name(dst_name))
                ),
            }
        )
    return out


def _variant_config(
    *,
    variant: str,
    n_features: int,
    n_classes: int,
    hidden_dim: int,
    dropout: float,
    graph_top_k: int,
    max_paths: int,
    prior_strength: float,
    path_coverage_mode: str = "target_group",
    coverage_dedup_mode: str = "soft",
    coverage_redundancy_penalty: float = 0.05,
    deduplicate_exact_paths: bool = False,
    use_task_salience: bool = False,
    salience_selection_strength: float = 0.0,
    salience_coverage_fraction: float = 0.0,
    use_temporal_descriptors: bool = False,
    temporal_descriptor_weight: float = 0.50,
    temporal_encoder_mode: str = "multi_scale_causal",
    use_temporal_mixer: bool = False,
    temporal_mixer_type: str = "conv",
    temporal_mixer_depth: int = 3,
    use_rul_temporal_anchor_fusion: bool = False,
    rul_anchor_residual_scale: float = 1.0,
    rul_anchor_gate_bias: float = -1.0,
    use_multihop_paths: bool = False,
    multihop_path_fraction: float = 0.25,
    use_context_router: bool = True,
    prior_coverage_fraction: float = 0.0,
    candidate_coverage_fraction: float = 0.0,
    use_class_conditioned_evidence: bool = False,
    class_evidence_gate_threshold: float = 0.0,
    class_evidence_gate_temperature: float = 0.05,
    class_evidence_gate_floor: float = 0.0,
    class_evidence_router_temperature: float = 1.0,
    class_evidence_router_top_k: int = 0,
    use_class_conditioned_prior_admission: bool = False,
    class_prior_admission_floor: float = 0.10,
    use_adaptive_prior_admission: bool = False,
    adaptive_prior_admission_threshold: float = 0.20,
    adaptive_prior_admission_temperature: float = 0.05,
    use_candidate_prior_admission: bool = False,
    candidate_prior_admission_floor: float = 0.05,
    candidate_prior_admission_threshold: float = 0.50,
    candidate_prior_admission_temperature: float = 0.05,
    candidate_prior_admission_support_mode: str = "relative_evidence",
    candidate_prior_admission_scale: float = 0.50,
    candidate_prior_admission_min_support: float = 0.0,
    candidate_prior_admission_protected_min_support: float = 0.0,
    candidate_prior_admission_target: str = "coverage",
    use_edge_family_router: bool = False,
    edge_family_count: int = 3,
    edge_family_router_temperature: float = 1.0,
    edge_family_router_floor: float = 0.05,
    edge_family_router_blend: float = 1.0,
    edge_family_router_balance_weight: float = 0.0,
    use_edge_calibrator: bool = False,
    edge_calibrator_floor: float = 0.05,
    edge_calibrator_init_bias: float = 2.0,
    use_path_reliability_calibrator: bool = False,
    path_reliability_context_scale: float = 1.0,
    use_learned_path_admission: bool = False,
    path_admission_strength: float = 1.0,
    use_path_prior_consistency: bool = False,
    path_prior_consistency_strength: float = 0.0,
    path_prior_consistency_threshold: float = 0.25,
    path_prior_consistency_temperature: float = 0.05,
    path_prior_consistency_support_mode: str = "max",
    path_prior_consistency_class_floor: float = 0.25,
    use_path_evidence_consistency: bool = False,
    path_evidence_consistency_strength: float = 0.0,
    path_evidence_consistency_threshold: float = 0.35,
    path_evidence_consistency_temperature: float = 0.05,
    path_evidence_consistency_floor: float = 0.0,
    path_evidence_consistency_support_mode: str = "absolute",
    use_path_proposal_consistency: bool = False,
    path_proposal_consistency_strength: float = 0.0,
    path_proposal_consistency_threshold: float = 0.35,
    path_proposal_consistency_temperature: float = 0.05,
    path_proposal_consistency_floor: float = 0.10,
    path_proposal_consistency_support_mode: str = "max",
    path_proposal_consistency_protected_strength: float = 0.0,
    path_proposal_retention_fraction: float = 0.0,
) -> MSGSERPFConfig:
    name = str(variant).strip().lower()
    scales = (3, 5, 9)
    use_graph = True
    use_reliability = True
    use_path_fusion = True
    use_residual_evidence = False
    if name == "single_scale":
        scales = (5,)
    elif name == "no_graph":
        use_graph = False
    elif name == "no_reliability":
        use_reliability = False
    elif name == "no_path_fusion":
        use_path_fusion = False
    elif name == "with_residual_evidence":
        use_residual_evidence = True
    elif name == "no_residual_evidence":
        use_residual_evidence = False
    elif name != "full":
        raise ValueError(f"Unknown MS-GSE/RPF variant: {variant}")
    return MSGSERPFConfig(
        n_features=n_features,
        n_classes=n_classes,
        hidden_dim=hidden_dim,
        scales=scales,
        temporal_encoder_mode=str(temporal_encoder_mode or "multi_scale_causal"),
        graph_top_k=graph_top_k,
        max_paths=max_paths,
        dropout=dropout,
        use_graph=use_graph,
        use_reliability=use_reliability,
        use_path_fusion=use_path_fusion,
        use_residual_evidence=use_residual_evidence,
        use_temporal_descriptors=bool(use_temporal_descriptors),
        temporal_descriptor_weight=float(temporal_descriptor_weight),
        use_temporal_mixer=bool(use_temporal_mixer),
        temporal_mixer_type=str(temporal_mixer_type or "conv"),
        temporal_mixer_depth=int(temporal_mixer_depth),
        use_rul_temporal_anchor_fusion=bool(use_rul_temporal_anchor_fusion),
        rul_anchor_residual_scale=float(rul_anchor_residual_scale),
        rul_anchor_gate_bias=float(rul_anchor_gate_bias),
        prior_strength=float(prior_strength) if use_graph else 0.0,
        path_coverage_mode=str(path_coverage_mode or "target_group"),
        coverage_dedup_mode=str(coverage_dedup_mode or "soft"),
        coverage_redundancy_penalty=float(coverage_redundancy_penalty),
        deduplicate_exact_paths=bool(deduplicate_exact_paths),
        use_task_salience=bool(use_task_salience),
        salience_selection_strength=float(salience_selection_strength),
        salience_coverage_fraction=float(salience_coverage_fraction),
        use_multihop_paths=bool(use_multihop_paths),
        multihop_path_fraction=float(multihop_path_fraction),
        use_context_router=bool(use_context_router),
        prior_coverage_fraction=float(prior_coverage_fraction),
        candidate_coverage_fraction=float(candidate_coverage_fraction),
        use_class_conditioned_evidence=bool(use_class_conditioned_evidence),
        class_evidence_gate_threshold=float(class_evidence_gate_threshold),
        class_evidence_gate_temperature=float(class_evidence_gate_temperature),
        class_evidence_gate_floor=float(class_evidence_gate_floor),
        class_evidence_router_temperature=float(class_evidence_router_temperature),
        class_evidence_router_top_k=int(class_evidence_router_top_k),
        use_class_conditioned_prior_admission=bool(use_class_conditioned_prior_admission),
        class_prior_admission_floor=float(class_prior_admission_floor),
        use_adaptive_prior_admission=bool(use_adaptive_prior_admission),
        adaptive_prior_admission_threshold=float(adaptive_prior_admission_threshold),
        adaptive_prior_admission_temperature=float(adaptive_prior_admission_temperature),
        use_candidate_prior_admission=bool(use_candidate_prior_admission),
        candidate_prior_admission_floor=float(candidate_prior_admission_floor),
        candidate_prior_admission_threshold=float(candidate_prior_admission_threshold),
        candidate_prior_admission_temperature=float(candidate_prior_admission_temperature),
        candidate_prior_admission_support_mode=str(candidate_prior_admission_support_mode or "relative_evidence"),
        candidate_prior_admission_scale=float(candidate_prior_admission_scale),
        candidate_prior_admission_min_support=float(candidate_prior_admission_min_support),
        candidate_prior_admission_protected_min_support=float(candidate_prior_admission_protected_min_support),
        candidate_prior_admission_target=str(candidate_prior_admission_target or "coverage"),
        use_edge_family_router=bool(use_edge_family_router),
        edge_family_count=max(1, int(edge_family_count)),
        edge_family_router_temperature=float(edge_family_router_temperature),
        edge_family_router_floor=float(edge_family_router_floor),
        edge_family_router_blend=float(edge_family_router_blend),
        use_edge_calibrator=bool(use_edge_calibrator),
        edge_calibrator_floor=float(edge_calibrator_floor),
        edge_calibrator_init_bias=float(edge_calibrator_init_bias),
        use_path_reliability_calibrator=bool(use_path_reliability_calibrator),
        path_reliability_context_scale=float(path_reliability_context_scale),
        use_learned_path_admission=bool(use_learned_path_admission),
        path_admission_strength=float(path_admission_strength),
        use_path_prior_consistency=bool(use_path_prior_consistency),
        path_prior_consistency_strength=float(path_prior_consistency_strength),
        path_prior_consistency_threshold=float(path_prior_consistency_threshold),
        path_prior_consistency_temperature=float(path_prior_consistency_temperature),
        path_prior_consistency_support_mode=str(path_prior_consistency_support_mode or "max"),
        path_prior_consistency_class_floor=float(path_prior_consistency_class_floor),
        use_path_evidence_consistency=bool(use_path_evidence_consistency),
        path_evidence_consistency_strength=float(path_evidence_consistency_strength),
        path_evidence_consistency_threshold=float(path_evidence_consistency_threshold),
        path_evidence_consistency_temperature=float(path_evidence_consistency_temperature),
        path_evidence_consistency_floor=float(path_evidence_consistency_floor),
        path_evidence_consistency_support_mode=str(path_evidence_consistency_support_mode or "absolute"),
        use_path_proposal_consistency=bool(use_path_proposal_consistency),
        path_proposal_consistency_strength=float(path_proposal_consistency_strength),
        path_proposal_consistency_threshold=float(path_proposal_consistency_threshold),
        path_proposal_consistency_temperature=float(path_proposal_consistency_temperature),
        path_proposal_consistency_floor=float(path_proposal_consistency_floor),
        path_proposal_consistency_support_mode=str(path_proposal_consistency_support_mode or "max"),
        path_proposal_consistency_protected_strength=float(path_proposal_consistency_protected_strength),
        path_proposal_retention_fraction=float(path_proposal_retention_fraction),
    )


def _predict_proba(
    model: MSGSERPFNet,
    x: np.ndarray,
    *,
    batch_size: int,
    device: torch.device,
    collect_paths: bool = False,
) -> tuple[np.ndarray, dict[str, Any]]:
    model.eval()
    chunks: list[np.ndarray] = []
    diag_accum: dict[str, list[float]] = {
        "mean_edge_weight": [],
        "mean_path_reliability": [],
        "mean_path_reliability_context": [],
        "mean_reliability_gain": [],
        "mean_path_prior_weight": [],
        "mean_path_salience_weight": [],
        "mean_path_context_importance": [],
        "mean_path_entropy": [],
        "mean_path_duplicate_rate": [],
        "mean_class_evidence_admission": [],
        "mean_class_prior_admission": [],
        "mean_class_prior_admission_trust": [],
        "mean_rpf_prior": [],
        "mean_edge_calibrator_gate": [],
        "mean_calibrated_prior": [],
        "mean_edge_family_router_max_weight": [],
        "mean_edge_family_router_entropy": [],
        "mean_edge_family_routed_prior": [],
        "mean_path_admission_gate": [],
        "mean_path_admission_adjustment": [],
        "mean_path_prior_consistency_support": [],
        "mean_path_prior_consistency_gate": [],
        "mean_path_prior_consistency_adjustment": [],
        "mean_path_evidence_consistency_support": [],
        "mean_path_evidence_consistency_gate": [],
        "mean_path_evidence_consistency_adjustment": [],
        "mean_path_proposal_consistency_support": [],
        "mean_path_proposal_consistency_gate": [],
        "mean_path_proposal_consistency_effective_strength": [],
        "mean_candidate_prior_admission_mask": [],
        "mean_candidate_protected_class_mass": [],
        "mean_rul_anchor_gate": [],
        "mean_abs_rul_anchor_delta": [],
    }
    pair_stats: dict[tuple[int, int, int], dict[str, float]] = {}
    x_t = torch.from_numpy(np.asarray(x, dtype=np.float32))
    batch = max(8, int(batch_size))
    start_time = time.perf_counter()
    with torch.no_grad():
        for start in range(0, len(x_t), batch):
            out = model(x_t[start : start + batch].to(device), return_diagnostics=True)
            chunks.append(torch.softmax(out["logits"], dim=1).cpu().numpy())
            diag = out.get("diagnostics", {}) or {}
            edge_weight = diag.get("path_edge_weight")
            prior_weight = diag.get("path_prior_weight")
            salience_weight = diag.get("path_salience_weight")
            context_importance = diag.get("path_context_importance")
            reliability = diag.get("path_reliability")
            reliability_context = diag.get("path_reliability_context")
            reliability_gain = diag.get("path_reliability_gain")
            duplicate_rate = diag.get("path_duplicate_rate")
            class_evidence_admission = diag.get("class_evidence_admission")
            class_prior_admission_gate = diag.get("class_prior_admission_gate")
            class_prior_admission_trust = diag.get("class_prior_admission_trust")
            rpf_prior = diag.get("rpf_prior_adjacency")
            edge_calibrator_gate = diag.get("edge_calibrator_gate")
            calibrated_prior = diag.get("calibrated_prior_adjacency")
            edge_family_router_weights = diag.get("edge_family_router_weights")
            edge_family_routed_prior = diag.get("edge_family_routed_prior")
            path_admission_gate = diag.get("path_admission_gate")
            path_admission_adjustment = diag.get("path_admission_adjustment")
            path_prior_consistency_support = diag.get("path_prior_consistency_support")
            path_prior_consistency_gate = diag.get("path_prior_consistency_gate")
            path_prior_consistency_adjustment = diag.get("path_prior_consistency_adjustment")
            path_evidence_consistency_support = diag.get("path_evidence_consistency_support")
            path_evidence_consistency_gate = diag.get("path_evidence_consistency_gate")
            path_evidence_consistency_adjustment = diag.get("path_evidence_consistency_adjustment")
            path_proposal_consistency_support = diag.get("path_proposal_consistency_support")
            path_proposal_consistency_gate = diag.get("path_proposal_consistency_gate")
            path_proposal_consistency_effective_strength = diag.get(
                "path_proposal_consistency_effective_strength"
            )
            candidate_prior_admission_mask = diag.get("candidate_prior_admission_mask")
            candidate_protected_class_mass = diag.get("candidate_protected_class_mass")
            rul_anchor_gate = diag.get("rul_anchor_gate")
            rul_anchor_delta = diag.get("rul_anchor_delta")
            weights = diag.get("path_weights")
            if edge_weight is not None and edge_weight.numel() > 0:
                diag_accum["mean_edge_weight"].append(float(edge_weight.mean().cpu().item()))
            if reliability is not None and reliability.numel() > 0:
                diag_accum["mean_path_reliability"].append(float(reliability.mean().cpu().item()))
            if reliability_context is not None and reliability_context.numel() > 0:
                diag_accum["mean_path_reliability_context"].append(float(reliability_context.abs().mean().cpu().item()))
            if reliability_gain is not None and reliability_gain.numel() > 0:
                diag_accum["mean_reliability_gain"].append(float(reliability_gain.mean().cpu().item()))
            if prior_weight is not None and prior_weight.numel() > 0:
                diag_accum["mean_path_prior_weight"].append(float(prior_weight.mean().cpu().item()))
            if salience_weight is not None and salience_weight.numel() > 0:
                diag_accum["mean_path_salience_weight"].append(float(salience_weight.mean().cpu().item()))
            if context_importance is not None and context_importance.numel() > 0:
                diag_accum["mean_path_context_importance"].append(float(context_importance.abs().mean().cpu().item()))
            if weights is not None and weights.numel() > 0:
                entropy = -(weights * torch.log(torch.clamp(weights, min=1e-6))).sum(dim=1).mean()
                diag_accum["mean_path_entropy"].append(float(entropy.cpu().item()))
            if duplicate_rate is not None and duplicate_rate.numel() > 0:
                diag_accum["mean_path_duplicate_rate"].append(float(duplicate_rate.mean().cpu().item()))
            if class_evidence_admission is not None and class_evidence_admission.numel() > 0:
                diag_accum["mean_class_evidence_admission"].append(float(class_evidence_admission.mean().cpu().item()))
            if class_prior_admission_gate is not None and class_prior_admission_gate.numel() > 0:
                positive_prior_gate = class_prior_admission_gate[class_prior_admission_gate > 0.0]
                if positive_prior_gate.numel() > 0:
                    diag_accum["mean_class_prior_admission"].append(float(positive_prior_gate.mean().cpu().item()))
            if class_prior_admission_trust is not None and class_prior_admission_trust.numel() > 0:
                diag_accum["mean_class_prior_admission_trust"].append(float(class_prior_admission_trust.mean().cpu().item()))
            if rpf_prior is not None and rpf_prior.numel() > 0:
                positive_rpf_prior = rpf_prior[rpf_prior > 0.0]
                if positive_rpf_prior.numel() > 0:
                    diag_accum["mean_rpf_prior"].append(float(positive_rpf_prior.mean().cpu().item()))
            if edge_calibrator_gate is not None and edge_calibrator_gate.numel() > 0:
                positive_gate = edge_calibrator_gate[edge_calibrator_gate > 0.0]
                if positive_gate.numel() > 0:
                    diag_accum["mean_edge_calibrator_gate"].append(float(positive_gate.mean().cpu().item()))
            if calibrated_prior is not None and calibrated_prior.numel() > 0:
                positive_prior = calibrated_prior[calibrated_prior > 0.0]
                if positive_prior.numel() > 0:
                    diag_accum["mean_calibrated_prior"].append(float(positive_prior.mean().cpu().item()))
            if edge_family_router_weights is not None and edge_family_router_weights.numel() > 0:
                diag_accum["mean_edge_family_router_max_weight"].append(
                    float(torch.max(edge_family_router_weights, dim=1).values.mean().cpu().item())
                )
                family_entropy = -(
                    edge_family_router_weights
                    * torch.log(torch.clamp(edge_family_router_weights, min=1.0e-8))
                ).sum(dim=1).mean()
                diag_accum["mean_edge_family_router_entropy"].append(float(family_entropy.cpu().item()))
            if edge_family_routed_prior is not None and edge_family_routed_prior.numel() > 0:
                positive_family_prior = edge_family_routed_prior[edge_family_routed_prior > 0.0]
                if positive_family_prior.numel() > 0:
                    diag_accum["mean_edge_family_routed_prior"].append(float(positive_family_prior.mean().cpu().item()))
            if path_admission_gate is not None and path_admission_gate.numel() > 0:
                diag_accum["mean_path_admission_gate"].append(float(path_admission_gate.mean().cpu().item()))
            if path_admission_adjustment is not None and path_admission_adjustment.numel() > 0:
                diag_accum["mean_path_admission_adjustment"].append(float(path_admission_adjustment.abs().mean().cpu().item()))
            if path_prior_consistency_support is not None and path_prior_consistency_support.numel() > 0:
                diag_accum["mean_path_prior_consistency_support"].append(
                    float(path_prior_consistency_support.mean().cpu().item())
                )
            if path_prior_consistency_gate is not None and path_prior_consistency_gate.numel() > 0:
                diag_accum["mean_path_prior_consistency_gate"].append(float(path_prior_consistency_gate.mean().cpu().item()))
            if path_prior_consistency_adjustment is not None and path_prior_consistency_adjustment.numel() > 0:
                diag_accum["mean_path_prior_consistency_adjustment"].append(
                    float(path_prior_consistency_adjustment.abs().mean().cpu().item())
                )
            if path_evidence_consistency_support is not None and path_evidence_consistency_support.numel() > 0:
                diag_accum["mean_path_evidence_consistency_support"].append(
                    float(path_evidence_consistency_support.mean().cpu().item())
                )
            if path_evidence_consistency_gate is not None and path_evidence_consistency_gate.numel() > 0:
                diag_accum["mean_path_evidence_consistency_gate"].append(
                    float(path_evidence_consistency_gate.mean().cpu().item())
                )
            if path_evidence_consistency_adjustment is not None and path_evidence_consistency_adjustment.numel() > 0:
                diag_accum["mean_path_evidence_consistency_adjustment"].append(
                    float(path_evidence_consistency_adjustment.abs().mean().cpu().item())
                )
            if path_proposal_consistency_support is not None and path_proposal_consistency_support.numel() > 0:
                diag_accum["mean_path_proposal_consistency_support"].append(
                    float(path_proposal_consistency_support.mean().cpu().item())
                )
            if path_proposal_consistency_gate is not None and path_proposal_consistency_gate.numel() > 0:
                diag_accum["mean_path_proposal_consistency_gate"].append(
                    float(path_proposal_consistency_gate.mean().cpu().item())
                )
            if (
                path_proposal_consistency_effective_strength is not None
                and path_proposal_consistency_effective_strength.numel() > 0
            ):
                diag_accum["mean_path_proposal_consistency_effective_strength"].append(
                    float(path_proposal_consistency_effective_strength.mean().cpu().item())
                )
            if candidate_prior_admission_mask is not None and candidate_prior_admission_mask.numel() > 0:
                diag_accum["mean_candidate_prior_admission_mask"].append(
                    float(candidate_prior_admission_mask.float().mean().cpu().item())
                )
            if candidate_protected_class_mass is not None and candidate_protected_class_mass.numel() > 0:
                diag_accum["mean_candidate_protected_class_mass"].append(
                    float(candidate_protected_class_mass.mean().cpu().item())
                )
            if rul_anchor_gate is not None and rul_anchor_gate.numel() > 0:
                diag_accum["mean_rul_anchor_gate"].append(float(rul_anchor_gate.mean().cpu().item()))
            if rul_anchor_delta is not None and rul_anchor_delta.numel() > 0:
                diag_accum["mean_abs_rul_anchor_delta"].append(float(rul_anchor_delta.abs().mean().cpu().item()))
            if collect_paths and weights is not None and weights.numel() > 0:
                sources = diag.get("path_source")
                targets = diag.get("path_target")
                bridges = diag.get("path_bridge")
                hop_counts = diag.get("path_hop_count")
                if sources is not None and targets is not None and reliability is not None and edge_weight is not None:
                    if prior_weight is None:
                        prior_weight = torch.zeros_like(edge_weight)
                    if salience_weight is None:
                        salience_weight = torch.zeros_like(edge_weight)
                    if bridges is None:
                        bridges = torch.full_like(sources, -1)
                    if hop_counts is None:
                        hop_counts = torch.ones_like(sources)
                    src_np = sources.cpu().numpy()
                    dst_np = targets.cpu().numpy()
                    bridge_np = bridges.cpu().numpy()
                    hop_np = hop_counts.cpu().numpy()
                    w_np = weights.cpu().numpy()
                    rel_np = reliability.cpu().numpy()
                    edge_np = edge_weight.cpu().numpy()
                    prior_np = prior_weight.cpu().numpy()
                    sal_np = salience_weight.cpu().numpy()
                    for row in range(src_np.shape[0]):
                        for col in range(src_np.shape[1]):
                            key = (int(src_np[row, col]), int(bridge_np[row, col]), int(dst_np[row, col]))
                            stat = pair_stats.setdefault(
                                key,
                                {
                                    "count": 0.0,
                                    "weight_sum": 0.0,
                                    "reliability_sum": 0.0,
                                    "edge_weight_sum": 0.0,
                                    "prior_weight_sum": 0.0,
                                    "salience_weight_sum": 0.0,
                                    "hop_count_sum": 0.0,
                                },
                            )
                            stat["count"] += 1.0
                            stat["weight_sum"] += float(w_np[row, col])
                            stat["reliability_sum"] += float(rel_np[row, col])
                            stat["edge_weight_sum"] += float(edge_np[row, col])
                            stat["prior_weight_sum"] += float(prior_np[row, col])
                            stat["salience_weight_sum"] += float(sal_np[row, col])
                            stat["hop_count_sum"] += float(hop_np[row, col])
    elapsed = max(1e-9, time.perf_counter() - start_time)
    diagnostics = {
        key: (float(np.mean(values)) if values else None)
        for key, values in diag_accum.items()
    }
    diagnostics["inference_seconds"] = float(elapsed)
    diagnostics["inference_samples_per_second"] = float(len(x) / elapsed)
    if collect_paths:
        rows: list[dict[str, Any]] = []
        for (source, bridge, target), stat in pair_stats.items():
            count = max(1.0, float(stat["count"]))
            rows.append(
                {
                    "source_index": int(source),
                    "bridge_index": int(bridge),
                    "target_index": int(target),
                    "count": int(stat["count"]),
                    "mean_weight": float(stat["weight_sum"] / count),
                    "mean_reliability": float(stat["reliability_sum"] / count),
                    "mean_edge_weight": float(stat["edge_weight_sum"] / count),
                    "mean_prior_weight": float(stat["prior_weight_sum"] / count),
                    "mean_salience_weight": float(stat.get("salience_weight_sum", 0.0) / count),
                    "mean_hop_count": float(stat.get("hop_count_sum", count) / count),
                }
            )
        rows.sort(key=lambda item: (-float(item["mean_weight"]), -float(item["mean_reliability"])))
        diagnostics["top_path_index_pairs"] = rows[:50]
    return np.vstack(chunks).astype(np.float64), diagnostics


def _predict_health(model: MSGSERPFNet, x: np.ndarray, *, batch_size: int, device: torch.device) -> np.ndarray:
    model.eval()
    chunks: list[np.ndarray] = []
    x_t = torch.from_numpy(np.asarray(x, dtype=np.float32))
    batch = max(8, int(batch_size))
    with torch.no_grad():
        for start in range(0, len(x_t), batch):
            out = model(x_t[start : start + batch].to(device), return_diagnostics=False)
            chunks.append(out["health_pred"].detach().cpu().numpy())
    return np.concatenate(chunks).astype(np.float32)


def _predict_rul_norm(
    model: MSGSERPFNet,
    x: np.ndarray,
    *,
    batch_size: int,
    device: torch.device,
    output_key: str = "rul_norm_pred",
) -> np.ndarray | None:
    model.eval()
    chunks: list[np.ndarray] = []
    x_t = torch.from_numpy(np.asarray(x, dtype=np.float32))
    batch = max(8, int(batch_size))
    with torch.no_grad():
        for start in range(0, len(x_t), batch):
            out = model(x_t[start : start + batch].to(device), return_diagnostics=False)
            value = out.get(str(output_key))
            if value is None:
                return None
            chunks.append(value.detach().cpu().numpy())
    return np.concatenate(chunks).astype(np.float32)


def train_model(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray,
    y_val: np.ndarray,
    x_test: np.ndarray,
    *,
    config: MSGSERPFConfig,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    classification_loss_weight: float,
    forecast_weight: float,
    graph_weight: float,
    focal_loss_gamma: float,
    label_smoothing: float,
    ordinal_loss_weight: float,
    ordinal_boundary_loss_weight: float,
    ordinal_boundary_focal_gamma: float,
    ordinal_boundary_focus: float,
    path_entropy_weight: float,
    path_aux_weight: float,
    coarse_aux_weight: float,
    evidence_router_aux_weight: float,
    edge_family_router_balance_weight: float,
    edge_calibrator_reg_weight: float,
    path_reliability_context_reg_weight: float,
    path_admission_reg_weight: float,
    health_aux_weight: float,
    rul_loss_weight: float,
    prior_adjacency: np.ndarray | None,
    path_candidate_prior: np.ndarray | None,
    edge_family_prior_matrices: np.ndarray | None,
    feature_group_ids: np.ndarray | None,
    task_salience: np.ndarray | None,
    path_evidence: np.ndarray | None,
    class_path_evidence: np.ndarray | None,
    candidate_protected_classes: Sequence[int] | None,
    candidate_protected_class_weights: np.ndarray | None,
    path_target_mask: np.ndarray | None,
    path_source_mask: np.ndarray | None,
    path_bridge_mask: np.ndarray | None,
    health_train: np.ndarray | None,
    health_val: np.ndarray | None,
    health_test: np.ndarray | None,
    rul_train_norm: np.ndarray | None,
    seed: int,
    rul_val: np.ndarray | None = None,
    rul_test: np.ndarray | None = None,
    health_rul_cap: float = 125.0,
    path_candidate_prior_baseline: np.ndarray | None = None,
    use_path_candidate_prior_validation_admission: bool = False,
    path_candidate_prior_validation_min_gain: float = 0.0,
    device: str = "auto",
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    torch.manual_seed(int(seed))
    train_device = resolve_torch_device(device)
    if train_device.type == "cpu":
        torch.set_num_threads(1)
    model = MSGSERPFNet(config)
    training_path_candidate_prior = (
        path_candidate_prior_baseline
        if bool(use_path_candidate_prior_validation_admission) and path_candidate_prior is not None
        else path_candidate_prior
    )
    model.set_graph_prior(prior_adjacency)
    model.set_path_candidate_prior(training_path_candidate_prior)
    model.set_edge_family_priors(edge_family_prior_matrices if bool(config.use_edge_family_router) else None)
    model.set_feature_groups(feature_group_ids)
    model.set_task_salience(task_salience)
    model.set_path_evidence(path_evidence)
    model.set_class_path_evidence(class_path_evidence)
    if candidate_protected_class_weights is not None:
        model.set_candidate_protected_class_weights(candidate_protected_class_weights)
    else:
        model.set_candidate_protected_classes(candidate_protected_classes)
    model.set_path_target_mask(path_target_mask)
    model.set_path_source_mask(path_source_mask)
    model.set_path_bridge_mask(path_bridge_mask)
    model.to(train_device)
    opt = torch.optim.AdamW(model.parameters(), lr=float(learning_rate), weight_decay=1e-4)
    class_weights = class_balanced_weights(y_train, config.n_classes).to(train_device)
    focal_gamma = float(max(0.0, focal_loss_gamma))
    smoothing = float(min(0.30, max(0.0, label_smoothing)))
    coarse_targets = (np.asarray(y_train, dtype=np.int64) > 0).astype(np.int64) if int(config.n_classes) > 2 else np.asarray(y_train, dtype=np.int64)
    coarse_weights = class_balanced_weights(coarse_targets, 2).to(train_device)
    x_t = torch.from_numpy(np.asarray(x_train, dtype=np.float32)).to(train_device)
    y_t = torch.from_numpy(np.asarray(y_train, dtype=np.int64)).to(train_device)
    coarse_t = torch.from_numpy(coarse_targets.astype(np.int64)).to(train_device)
    health_t = torch.from_numpy(np.asarray(health_train, dtype=np.float32)).to(train_device) if health_train is not None else None
    rul_t = torch.from_numpy(np.asarray(rul_train_norm, dtype=np.float32)).to(train_device) if rul_train_norm is not None else None
    rng = np.random.default_rng(int(seed))
    batch = max(8, min(int(batch_size), len(y_train)))
    best_state: dict[str, torch.Tensor] | None = None
    best_val = -float("inf")
    losses: list[float] = []
    val_history: list[float] = []
    val_rul_history: list[float] = []
    use_direct_rul = bool(float(rul_loss_weight) > 0.0 and rul_t is not None and rul_val is not None)
    train_start = time.perf_counter()
    for _epoch in range(max(1, int(epochs))):
        order = rng.permutation(len(y_train))
        epoch_loss: list[float] = []
        model.train()
        for start in range(0, len(order), batch):
            idx = torch.from_numpy(order[start : start + batch].astype(np.int64)).to(train_device)
            batch_x = x_t[idx]
            batch_y = y_t[idx]
            opt.zero_grad()
            out = model(batch_x, return_diagnostics=True)
            loss = float(classification_loss_weight) * supervised_classification_loss(
                out["logits"],
                batch_y,
                class_weights=class_weights,
                focal_gamma=focal_gamma,
                label_smoothing=smoothing,
            )
            if float(path_aux_weight) > 0.0:
                loss = loss + float(path_aux_weight) * supervised_classification_loss(
                    out["path_aux_logits"],
                    batch_y,
                    class_weights=class_weights,
                    focal_gamma=focal_gamma,
                    label_smoothing=smoothing,
                )
            if float(coarse_aux_weight) > 0.0:
                loss = loss + float(coarse_aux_weight) * supervised_classification_loss(
                    out["coarse_logits"],
                    coarse_t[idx],
                    class_weights=coarse_weights,
                    focal_gamma=focal_gamma,
                    label_smoothing=smoothing,
                )
            if float(evidence_router_aux_weight) > 0.0 and out.get("evidence_router_logits") is not None:
                loss = loss + float(evidence_router_aux_weight) * supervised_classification_loss(
                    out["evidence_router_logits"],
                    batch_y,
                    class_weights=class_weights,
                    focal_gamma=focal_gamma,
                    label_smoothing=smoothing,
                )
            if float(edge_family_router_balance_weight) > 0.0:
                family_weights = out["diagnostics"].get("edge_family_router_weights")
                if family_weights is not None and family_weights.numel() > 0:
                    n_families = max(1, int(family_weights.shape[1]))
                    family_kl = torch.sum(
                        family_weights
                        * (
                            torch.log(torch.clamp(family_weights, min=1.0e-8))
                            + math.log(float(n_families))
                        ),
                        dim=1,
                    ).mean()
                    loss = loss + float(edge_family_router_balance_weight) * family_kl
            if float(edge_calibrator_reg_weight) > 0.0 and out.get("edge_calibrator_reg_loss") is not None:
                loss = loss + float(edge_calibrator_reg_weight) * out["edge_calibrator_reg_loss"]
            if float(health_aux_weight) > 0.0 and health_t is not None:
                batch_health = health_t[idx]
                loss = loss + float(health_aux_weight) * F.mse_loss(out["health_pred"], batch_health)
            if float(rul_loss_weight) > 0.0 and rul_t is not None:
                batch_rul = rul_t[idx]
                loss = loss + float(rul_loss_weight) * F.mse_loss(out["rul_norm_pred"], batch_rul)
                if out.get("temporal_rul_norm_pred") is not None:
                    loss = loss + float(rul_loss_weight) * F.mse_loss(out["temporal_rul_norm_pred"], batch_rul)
                if out.get("anchor_rul_norm_pred") is not None:
                    loss = loss + float(rul_loss_weight) * F.mse_loss(out["anchor_rul_norm_pred"], batch_rul)
            if float(ordinal_loss_weight) > 0.0:
                loss = loss + float(ordinal_loss_weight) * ordinal_emd_loss(
                    out["logits"],
                    batch_y,
                    class_weights=class_weights,
                )
            if float(ordinal_boundary_loss_weight) > 0.0:
                loss = loss + float(ordinal_boundary_loss_weight) * ordinal_boundary_bce_loss(
                    out["logits"],
                    batch_y,
                    class_weights=class_weights,
                    focal_gamma=ordinal_boundary_focal_gamma,
                    boundary_focus=ordinal_boundary_focus,
                )
            if float(forecast_weight) > 0.0:
                loss = loss + float(forecast_weight) * F.mse_loss(out["reconstruction"], batch_x[:, -1, :])
            if float(graph_weight) > 0.0:
                loss = loss + float(graph_weight) * graph_regularization(out["diagnostics"]["adjacency"])
            if float(path_entropy_weight) > 0.0:
                path_weights = out["diagnostics"].get("path_weights")
                if path_weights is not None and path_weights.numel() > 0:
                    entropy = -(path_weights * torch.log(torch.clamp(path_weights, min=1.0e-8))).sum(dim=1).mean()
                    loss = loss + float(path_entropy_weight) * entropy
            if float(path_reliability_context_reg_weight) > 0.0:
                reliability_context = out["diagnostics"].get("path_reliability_context")
                if reliability_context is not None and reliability_context.numel() > 0:
                    loss = loss + float(path_reliability_context_reg_weight) * torch.mean(reliability_context * reliability_context)
            if float(path_admission_reg_weight) > 0.0:
                path_admission_adjustment = out["diagnostics"].get("path_admission_adjustment")
                if path_admission_adjustment is not None and path_admission_adjustment.numel() > 0:
                    loss = loss + float(path_admission_reg_weight) * torch.mean(path_admission_adjustment * path_admission_adjustment)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 3.0)
            opt.step()
            epoch_loss.append(float(loss.detach().cpu().item()))
        losses.append(float(np.mean(epoch_loss)) if epoch_loss else 0.0)
        val_proba, _diag = _predict_proba(model, x_val, batch_size=batch, device=train_device, collect_paths=False)
        val_macro = summarize_classification(y_val, val_proba)["macro_f1"]
        val_history.append(float(val_macro))
        selection_metric = float(val_macro)
        if use_direct_rul:
            val_rul_norm_pred = _predict_rul_norm(model, x_val, batch_size=batch, device=train_device)
            val_rul_pred = predict_rul_from_normalized(val_rul_norm_pred, rul_cap=health_rul_cap)
            val_rul_metric = rul_regression_metrics(rul_val, val_rul_pred)
            val_rul_rmse = float((val_rul_metric or {}).get("rul_rmse", float("inf")))
            val_temporal_rul_norm_pred = _predict_rul_norm(
                model,
                x_val,
                batch_size=batch,
                device=train_device,
                output_key="temporal_rul_norm_pred",
            )
            val_temporal_rul_pred = predict_rul_from_normalized(val_temporal_rul_norm_pred, rul_cap=health_rul_cap)
            val_temporal_rul_metric = rul_regression_metrics(rul_val, val_temporal_rul_pred)
            val_temporal_rul_rmse = float((val_temporal_rul_metric or {}).get("rul_rmse", float("inf")))
            val_anchor_rul_norm_pred = _predict_rul_norm(
                model,
                x_val,
                batch_size=batch,
                device=train_device,
                output_key="anchor_rul_norm_pred",
            )
            val_anchor_rul_pred = predict_rul_from_normalized(val_anchor_rul_norm_pred, rul_cap=health_rul_cap)
            val_anchor_rul_metric = rul_regression_metrics(rul_val, val_anchor_rul_pred)
            val_anchor_rul_rmse = float((val_anchor_rul_metric or {}).get("rul_rmse", float("inf")))
            val_rul_rmse = min(val_rul_rmse, val_temporal_rul_rmse)
            val_rul_rmse = min(val_rul_rmse, val_anchor_rul_rmse)
            val_rul_history.append(val_rul_rmse)
            selection_metric = -val_rul_rmse
        if selection_metric >= best_val:
            best_val = float(selection_metric)
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
    train_seconds = max(1e-9, time.perf_counter() - train_start)
    if best_state is not None:
        model.load_state_dict(best_state)
    candidate_prior_validation_admission = {
        "enabled": False,
        "requested": bool(use_path_candidate_prior_validation_admission),
    }
    if bool(use_path_candidate_prior_validation_admission) and path_candidate_prior is not None:
        model.set_path_candidate_prior(path_candidate_prior)
        candidate_val_proba, candidate_val_diag = _predict_proba(
            model,
            x_val,
            batch_size=batch,
            device=train_device,
            collect_paths=True,
        )
        candidate_metric = float(summarize_classification(y_val, candidate_val_proba)["macro_f1"])
        model.set_path_candidate_prior(path_candidate_prior_baseline)
        baseline_val_proba, baseline_val_diag = _predict_proba(
            model,
            x_val,
            batch_size=batch,
            device=train_device,
            collect_paths=True,
        )
        baseline_metric = float(summarize_classification(y_val, baseline_val_proba)["macro_f1"])
        candidate_prior_validation_admission = validation_gain_admission_decision(
            candidate_metric=candidate_metric,
            baseline_metric=baseline_metric,
            min_gain=path_candidate_prior_validation_min_gain,
            metric_name="macro_f1",
        )
        if bool(candidate_prior_validation_admission["admitted"]):
            model.set_path_candidate_prior(path_candidate_prior)
            val_proba, val_diag = candidate_val_proba, candidate_val_diag
        else:
            model.set_path_candidate_prior(path_candidate_prior_baseline)
            val_proba, val_diag = baseline_val_proba, baseline_val_diag
    else:
        model.set_path_candidate_prior(path_candidate_prior)
        val_proba, val_diag = _predict_proba(model, x_val, batch_size=batch, device=train_device, collect_paths=True)
    test_proba, test_diag = _predict_proba(model, x_test, batch_size=batch, device=train_device, collect_paths=True)
    val_health_pred = _predict_health(model, x_val, batch_size=batch, device=train_device) if health_val is not None else None
    test_health_pred = _predict_health(model, x_test, batch_size=batch, device=train_device) if health_test is not None else None
    val_health_rul_pred = predict_rul_from_health(val_health_pred, rul_cap=health_rul_cap)
    test_health_rul_pred = predict_rul_from_health(test_health_pred, rul_cap=health_rul_cap)
    val_direct_rul_norm_pred = _predict_rul_norm(model, x_val, batch_size=batch, device=train_device) if use_direct_rul else None
    test_direct_rul_norm_pred = _predict_rul_norm(model, x_test, batch_size=batch, device=train_device) if use_direct_rul else None
    val_temporal_rul_norm_pred = (
        _predict_rul_norm(
            model,
            x_val,
            batch_size=batch,
            device=train_device,
            output_key="temporal_rul_norm_pred",
        )
        if use_direct_rul
        else None
    )
    test_temporal_rul_norm_pred = (
        _predict_rul_norm(
            model,
            x_test,
            batch_size=batch,
            device=train_device,
            output_key="temporal_rul_norm_pred",
        )
        if use_direct_rul
        else None
    )
    val_anchor_rul_norm_pred = (
        _predict_rul_norm(
            model,
            x_val,
            batch_size=batch,
            device=train_device,
            output_key="anchor_rul_norm_pred",
        )
        if use_direct_rul
        else None
    )
    test_anchor_rul_norm_pred = (
        _predict_rul_norm(
            model,
            x_test,
            batch_size=batch,
            device=train_device,
            output_key="anchor_rul_norm_pred",
        )
        if use_direct_rul
        else None
    )
    val_direct_rul_pred = predict_rul_from_normalized(val_direct_rul_norm_pred, rul_cap=health_rul_cap)
    test_direct_rul_pred = predict_rul_from_normalized(test_direct_rul_norm_pred, rul_cap=health_rul_cap)
    val_temporal_rul_pred = predict_rul_from_normalized(val_temporal_rul_norm_pred, rul_cap=health_rul_cap)
    test_temporal_rul_pred = predict_rul_from_normalized(test_temporal_rul_norm_pred, rul_cap=health_rul_cap)
    val_anchor_rul_pred = predict_rul_from_normalized(val_anchor_rul_norm_pred, rul_cap=health_rul_cap)
    test_anchor_rul_pred = predict_rul_from_normalized(test_anchor_rul_norm_pred, rul_cap=health_rul_cap)
    val_health_rul_metrics = rul_regression_metrics(rul_val, val_health_rul_pred)
    test_health_rul_metrics = rul_regression_metrics(rul_test, test_health_rul_pred)
    val_direct_rul_metrics = rul_regression_metrics(rul_val, val_direct_rul_pred)
    test_direct_rul_metrics = rul_regression_metrics(rul_test, test_direct_rul_pred)
    val_temporal_rul_metrics = rul_regression_metrics(rul_val, val_temporal_rul_pred)
    test_temporal_rul_metrics = rul_regression_metrics(rul_test, test_temporal_rul_pred)
    val_anchor_rul_metrics = rul_regression_metrics(rul_val, val_anchor_rul_pred)
    test_anchor_rul_metrics = rul_regression_metrics(rul_test, test_anchor_rul_pred)
    rul_prediction_source = "health_index_inverse"
    val_rul_pred = val_health_rul_pred
    test_rul_pred = test_health_rul_pred
    if use_direct_rul:
        candidates = [
            (
                "direct_rul_head",
                val_direct_rul_pred,
                test_direct_rul_pred,
                float((val_direct_rul_metrics or {}).get("rul_rmse", float("inf"))),
            ),
            (
                "temporal_rul_head",
                val_temporal_rul_pred,
                test_temporal_rul_pred,
                float((val_temporal_rul_metrics or {}).get("rul_rmse", float("inf"))),
            ),
            (
                "anchor_rul_head",
                val_anchor_rul_pred,
                test_anchor_rul_pred,
                float((val_anchor_rul_metrics or {}).get("rul_rmse", float("inf"))),
            ),
        ]
        candidates = [item for item in candidates if item[1] is not None and item[2] is not None and math.isfinite(item[3])]
        if candidates:
            rul_prediction_source, val_rul_pred, test_rul_pred, _best_rmse = min(candidates, key=lambda item: item[3])
    val_rul_metrics = rul_regression_metrics(rul_val, val_rul_pred)
    test_rul_metrics = rul_regression_metrics(rul_test, test_rul_pred)
    diagnostics = {
        "model_family": model.model_family,
        "parameters": count_trainable_parameters(model),
        "epochs": int(epochs),
        "batch_size": int(batch),
        "device": str(train_device),
        "cuda_available": bool(torch.cuda.is_available()),
        "loss_tail": losses[-5:],
        "val_macro_f1_history_tail": val_history[-5:],
        "val_rul_rmse_history_tail": val_rul_history[-5:],
        "best_val_selection_metric": float(best_val),
        "best_val_selection_metric_name": "negative_rul_rmse" if use_direct_rul else "macro_f1",
        "best_val_macro_f1": float(max(val_history)) if val_history else None,
        "best_val_rul_rmse": float(min(val_rul_history)) if val_rul_history else None,
        "train_seconds": float(train_seconds),
        "train_samples_per_second": float((len(y_train) * max(1, int(epochs))) / train_seconds),
        "classification_loss_weight": float(classification_loss_weight),
        "focal_loss_gamma": float(focal_gamma),
        "label_smoothing": float(smoothing),
        "ordinal_loss_weight": float(ordinal_loss_weight),
        "ordinal_boundary_loss_weight": float(ordinal_boundary_loss_weight),
        "ordinal_boundary_focal_gamma": float(ordinal_boundary_focal_gamma),
        "ordinal_boundary_focus": float(ordinal_boundary_focus),
        "path_entropy_weight": float(path_entropy_weight),
        "path_aux_weight": float(path_aux_weight),
        "coarse_aux_weight": float(coarse_aux_weight),
        "evidence_router_aux_weight": float(evidence_router_aux_weight),
        "edge_family_router_balance_weight": float(edge_family_router_balance_weight),
        "edge_calibrator_reg_weight": float(edge_calibrator_reg_weight),
        "path_reliability_context_reg_weight": float(path_reliability_context_reg_weight),
        "path_admission_reg_weight": float(path_admission_reg_weight),
        "health_aux_weight": float(health_aux_weight),
        "rul_loss_weight": float(rul_loss_weight),
        "direct_rul_enabled": bool(use_direct_rul),
        "rul_prediction_source": rul_prediction_source,
        "val_health_mae": health_mae(health_val, val_health_pred),
        "test_health_mae": health_mae(health_test, test_health_pred),
        "health_rul_cap": float(health_rul_cap),
        "val_rul_metrics": val_rul_metrics,
        "test_rul_metrics": test_rul_metrics,
        "test_rul_true": [float(value) for value in np.asarray(rul_test, dtype=np.float64).reshape(-1)]
        if rul_test is not None
        else None,
        "test_rul_pred": [float(value) for value in np.asarray(test_rul_pred, dtype=np.float64).reshape(-1)]
        if test_rul_pred is not None
        else None,
        "val_health_rul_metrics": val_health_rul_metrics,
        "test_health_rul_metrics": test_health_rul_metrics,
        "val_direct_rul_metrics": val_direct_rul_metrics,
        "test_direct_rul_metrics": test_direct_rul_metrics,
        "val_temporal_rul_metrics": val_temporal_rul_metrics,
        "test_temporal_rul_metrics": test_temporal_rul_metrics,
        "val_anchor_rul_metrics": val_anchor_rul_metrics,
        "test_anchor_rul_metrics": test_anchor_rul_metrics,
        "validation_diagnostics": val_diag,
        "test_diagnostics": test_diag,
        "candidate_prior_validation_admission": candidate_prior_validation_admission,
        "config": {
            "hidden_dim": int(config.hidden_dim),
            "scales": list(config.scales),
            "graph_top_k": int(config.graph_top_k),
            "max_paths": int(config.max_paths),
            "use_graph": bool(config.use_graph),
            "use_reliability": bool(config.use_reliability),
            "use_path_fusion": bool(config.use_path_fusion),
            "use_residual_evidence": bool(config.use_residual_evidence),
            "use_temporal_descriptors": bool(config.use_temporal_descriptors),
            "temporal_descriptor_weight": float(config.temporal_descriptor_weight),
            "use_rul_temporal_anchor_fusion": bool(config.use_rul_temporal_anchor_fusion),
            "rul_anchor_residual_scale": float(config.rul_anchor_residual_scale),
            "rul_anchor_gate_bias": float(config.rul_anchor_gate_bias),
            "prior_strength": float(config.prior_strength),
            "path_coverage_mode": str(config.path_coverage_mode),
            "coverage_dedup_mode": str(config.coverage_dedup_mode),
            "coverage_redundancy_penalty": float(config.coverage_redundancy_penalty),
            "deduplicate_exact_paths": bool(config.deduplicate_exact_paths),
            "use_task_salience": bool(config.use_task_salience),
            "salience_selection_strength": float(config.salience_selection_strength),
            "salience_coverage_fraction": float(config.salience_coverage_fraction),
            "use_multihop_paths": bool(config.use_multihop_paths),
            "multihop_path_fraction": float(config.multihop_path_fraction),
            "use_context_router": bool(config.use_context_router),
            "prior_coverage_fraction": float(config.prior_coverage_fraction),
            "candidate_coverage_fraction": float(config.candidate_coverage_fraction),
            "path_candidate_prior_enabled": bool(model.path_candidate_prior.numel()),
            "path_candidate_prior_requested": bool(path_candidate_prior is not None),
            "path_candidate_prior_used_during_training": bool(training_path_candidate_prior is not None),
            "path_candidate_prior_baseline_enabled": bool(path_candidate_prior_baseline is not None),
            "use_class_conditioned_evidence": bool(config.use_class_conditioned_evidence),
            "use_class_conditioned_prior_admission": bool(config.use_class_conditioned_prior_admission),
            "class_prior_admission_floor": float(config.class_prior_admission_floor),
            "use_adaptive_prior_admission": bool(config.use_adaptive_prior_admission),
            "adaptive_prior_admission_threshold": float(config.adaptive_prior_admission_threshold),
            "adaptive_prior_admission_temperature": float(config.adaptive_prior_admission_temperature),
            "use_candidate_prior_admission": bool(config.use_candidate_prior_admission),
            "candidate_prior_admission_floor": float(config.candidate_prior_admission_floor),
            "candidate_prior_admission_threshold": float(config.candidate_prior_admission_threshold),
            "candidate_prior_admission_temperature": float(config.candidate_prior_admission_temperature),
            "candidate_prior_admission_support_mode": str(config.candidate_prior_admission_support_mode),
            "candidate_prior_admission_scale": float(config.candidate_prior_admission_scale),
            "candidate_prior_admission_min_support": float(config.candidate_prior_admission_min_support),
            "candidate_prior_admission_protected_min_support": float(
                config.candidate_prior_admission_protected_min_support
            ),
            "candidate_prior_admission_target": str(config.candidate_prior_admission_target),
            "use_edge_family_router": bool(config.use_edge_family_router),
            "edge_family_count": int(config.edge_family_count),
            "edge_family_router_temperature": float(config.edge_family_router_temperature),
            "edge_family_router_floor": float(config.edge_family_router_floor),
            "edge_family_router_blend": float(config.edge_family_router_blend),
            "use_edge_calibrator": bool(config.use_edge_calibrator),
            "edge_calibrator_floor": float(config.edge_calibrator_floor),
            "edge_calibrator_init_bias": float(config.edge_calibrator_init_bias),
            "use_path_reliability_calibrator": bool(config.use_path_reliability_calibrator),
            "path_reliability_context_scale": float(config.path_reliability_context_scale),
            "use_learned_path_admission": bool(config.use_learned_path_admission),
            "path_admission_strength": float(config.path_admission_strength),
            "use_path_prior_consistency": bool(config.use_path_prior_consistency),
            "path_prior_consistency_strength": float(config.path_prior_consistency_strength),
            "path_prior_consistency_threshold": float(config.path_prior_consistency_threshold),
            "path_prior_consistency_temperature": float(config.path_prior_consistency_temperature),
            "path_prior_consistency_support_mode": str(config.path_prior_consistency_support_mode),
            "path_prior_consistency_class_floor": float(config.path_prior_consistency_class_floor),
            "use_path_evidence_consistency": bool(config.use_path_evidence_consistency),
            "path_evidence_consistency_strength": float(config.path_evidence_consistency_strength),
            "path_evidence_consistency_threshold": float(config.path_evidence_consistency_threshold),
            "path_evidence_consistency_temperature": float(config.path_evidence_consistency_temperature),
            "path_evidence_consistency_floor": float(config.path_evidence_consistency_floor),
            "path_evidence_consistency_support_mode": str(config.path_evidence_consistency_support_mode),
            "use_path_proposal_consistency": bool(config.use_path_proposal_consistency),
            "path_proposal_consistency_strength": float(config.path_proposal_consistency_strength),
            "path_proposal_consistency_threshold": float(config.path_proposal_consistency_threshold),
            "path_proposal_consistency_temperature": float(config.path_proposal_consistency_temperature),
            "path_proposal_consistency_floor": float(config.path_proposal_consistency_floor),
            "path_proposal_consistency_support_mode": str(config.path_proposal_consistency_support_mode),
            "path_proposal_consistency_protected_strength": float(
                config.path_proposal_consistency_protected_strength
            ),
            "path_proposal_retention_fraction": float(config.path_proposal_retention_fraction),
            "n_feature_groups": int(len(np.unique(feature_group_ids))) if feature_group_ids is not None else 0,
            "n_path_target_allowed": int(np.asarray(path_target_mask, dtype=bool).sum()) if path_target_mask is not None else 0,
            "n_path_source_allowed": int(np.asarray(path_source_mask, dtype=bool).sum()) if path_source_mask is not None else 0,
            "n_path_bridge_allowed": int(np.asarray(path_bridge_mask, dtype=bool).sum()) if path_bridge_mask is not None else 0,
        },
    }
    return val_proba, test_proba, diagnostics


def run_ready_task(
    task: ReadyTask,
    *,
    output_dir: Path,
    variant: str,
    seed: int,
    window_size: int,
    hidden_dim: int,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    max_rows_per_split: int | None,
    forecast_weight: float,
    graph_weight: float,
    focal_loss_gamma: float,
    label_smoothing: float,
    ordinal_loss_weight: float,
    path_entropy_weight: float,
    graph_top_k: int,
    max_paths: int,
    evidence_prior_mode: str,
    prior_strength: float,
    prior_min_reliability: float,
    classification_loss_weight: float = 1.0,
    ordinal_boundary_loss_weight: float = 0.0,
    ordinal_boundary_focal_gamma: float = 0.0,
    ordinal_boundary_focus: float = 0.0,
    use_prototype_posterior_fusion: bool = False,
    prototype_fusion_max_blend: float = 0.50,
    prototype_fusion_blend_steps: int = 11,
    prototype_fusion_temperature_grid: str = "0.25,0.50,1.00,2.00,4.00",
    prototype_fusion_min_val_gain: float = 0.0,
    use_one_class_posterior_fusion: bool = False,
    one_class_fusion_max_blend: float = 0.35,
    one_class_fusion_blend_steps: int = 8,
    one_class_fusion_temperature_grid: str = "0.25,0.50,1.00,2.00",
    one_class_fusion_threshold_grid: str = "-0.50,0.00,0.50,1.00,1.50,2.00,3.00",
    one_class_fusion_min_val_gain: float = 0.0,
    use_ordinal_posterior_calibration: bool = False,
    ordinal_posterior_max_blend: float = 0.50,
    ordinal_posterior_blend_steps: int = 11,
    ordinal_posterior_smoothing: float = 0.03,
    ordinal_posterior_min_val_gain: float = 0.0,
    algorithmic_edge_prior_mode: str = "none",
    algorithmic_edge_prior_top_k: int = 0,
    algorithmic_edge_prior_group_top_k: int = 0,
    algorithmic_edge_prior_max_lag: int = 3,
    algorithmic_edge_prior_strength: float = 0.0,
    algorithmic_edge_prior_class_weight: float = 0.25,
    algorithmic_edge_prior_lag_weight: float = 0.45,
    algorithmic_edge_prior_corr_weight: float = 0.30,
    algorithmic_edge_prior_residual_weight: float = 0.30,
    algorithmic_edge_prior_response_weight: float = 0.25,
    algorithmic_edge_prior_stability_weight: float = 0.20,
    algorithmic_edge_prior_bank_min_votes: int = 2,
    algorithmic_edge_prior_bank_single_view_scale: float = 0.55,
    algorithmic_edge_prior_bank_vote_boost: float = 0.15,
    algorithmic_edge_prior_bank_global_budget_multiplier: float = 0.0,
    algorithmic_edge_prior_pool_multiplier: float = 2.0,
    algorithmic_edge_prior_pool_min_score: float = 0.0,
    algorithmic_edge_prior_pool_rank_weight: float = 0.35,
    algorithmic_edge_prior_candidate_only: bool = False,
    prior_algorithmic_combine_mode: str = "max",
    prior_external_isolated_scale: float = 1.0,
    prior_overlap_boost: float = 0.0,
    prior_nonanchor_algorithmic_scale: float = 1.0,
    device: str = "auto",
    prior_coverage_fraction: float = 0.0,
    candidate_coverage_fraction: float = 0.0,
    calibrate_prior_edges: bool = False,
    prior_calibration_max_lag: int = 3,
    prior_calibration_min_support: float = 0.0,
    prior_calibration_strength: float = 1.0,
    external_edge_candidate_only: bool = False,
    external_candidate_families: str = "expert,llm",
    external_family_calibration_floor: float = 0.15,
    external_family_min_data_support: float = 0.0,
    external_candidate_expert_scale: float = 1.0,
    external_candidate_llm_scale: float = 0.70,
    external_candidate_default_scale: float = 0.85,
    disable_source_complexity_penalty: bool = False,
    use_llm_expert_condition_verifier: bool = False,
    llm_condition_verifier_weight: float = 0.50,
    llm_condition_verifier_min_data_support: float = 0.05,
    llm_condition_verifier_floor: float = 0.10,
    llm_condition_verifier_target: str = "candidate_gate",
    use_llm_condition_verifier_validation_admission: bool = False,
    llm_condition_verifier_min_val_gain: float = 0.0,
    path_aux_weight: float = 0.0,
    coarse_aux_weight: float = 0.0,
    evidence_router_aux_weight: float = 0.0,
    health_aux_weight: float = 0.0,
    rul_loss_weight: float = 0.0,
    health_rul_cap: float = 125.0,
    prior_group_expansion: bool = False,
    prior_group_expansion_strength: float = 0.5,
    dropout: float = 0.10,
    auto_path_budget: bool = False,
    path_coverage_mode: str = "target_group",
    coverage_dedup_mode: str = "soft",
    coverage_redundancy_penalty: float = 0.05,
    deduplicate_exact_paths: bool = False,
    use_task_salience: bool = False,
    salience_mode: str = "class",
    lifecycle_salience_weight: float = 0.50,
    order_anchor_evidence_weight: float = 0.35,
    algorithmic_evidence_top_k: int = 0,
    salience_selection_strength: float = 0.0,
    salience_coverage_fraction: float = 0.0,
    use_temporal_descriptors: bool = False,
    temporal_descriptor_weight: float = 0.50,
    temporal_encoder_mode: str = "multi_scale_causal",
    use_temporal_mixer: bool = False,
    temporal_mixer_type: str = "conv",
    temporal_mixer_depth: int = 3,
    use_rul_temporal_anchor_fusion: bool = False,
    rul_anchor_residual_scale: float = 1.0,
    rul_anchor_gate_bias: float = -1.0,
    use_multihop_paths: bool = False,
    multihop_path_fraction: float = 0.25,
    use_context_router: bool = True,
    use_class_conditioned_evidence: bool = False,
    class_evidence_top_k: int = 0,
    class_evidence_mode: str = "static",
    class_evidence_max_lag: int = 0,
    class_evidence_lag_weight: float = 0.50,
    class_evidence_family_k: int = 0,
    class_evidence_family_weight: float = 0.0,
    class_evidence_focus_mode: str = "none",
    class_evidence_focus_classes: str | Sequence[int] | None = None,
    class_evidence_focus_k: int = 0,
    class_evidence_focus_nonfocus_weight: float = 0.0,
    class_evidence_gate_threshold: float = 0.0,
    class_evidence_gate_temperature: float = 0.05,
    class_evidence_gate_floor: float = 0.0,
    class_evidence_router_temperature: float = 1.0,
    class_evidence_router_top_k: int = 0,
    use_stable_path_evidence: bool = False,
    stable_path_evidence_splits: int = 4,
    stable_path_evidence_min_vote_fraction: float = 0.50,
    stable_path_evidence_strength: float = 0.50,
    stable_path_evidence_top_k: int = 0,
    stable_path_evidence_edge_top_k: int = 4,
    stable_path_evidence_mode: str = "static_lag",
    stable_path_evidence_max_lag: int = 3,
    stable_path_evidence_lag_weight: float = 0.50,
    stable_path_evidence_path_mode: str = "max",
    stable_path_evidence_class_mode: str = "filter",
    stable_path_evidence_class_floor: float = 0.25,
    use_class_evidence_quality_certificate: bool = False,
    class_evidence_quality_mode: str = "focus_stability",
    class_evidence_quality_floor: float = 0.15,
    class_evidence_quality_threshold: float = 0.75,
    class_evidence_quality_temperature: float = 0.05,
    use_path_family_quality_certificate: bool = False,
    path_family_quality_mode: str = "focus_path_family",
    path_family_quality_floor: float = 0.15,
    path_family_quality_threshold: float = 0.25,
    path_family_quality_temperature: float = 0.05,
    path_family_quality_direct_weight: float = 1.0,
    path_family_quality_group_weight: float = 0.50,
    path_family_quality_stability_weight: float = 0.0,
    path_family_quality_family_k: int = 0,
    path_family_quality_family_weight: float = 0.0,
    use_path_family_protected_proposal_weights: bool = False,
    use_stable_class_edge_overlay: bool = False,
    stable_class_edge_overlay_scale: float = 0.25,
    stable_class_edge_overlay_top_k: int = 8,
    stable_class_edge_overlay_group_top_k: int = 2,
    stable_class_edge_overlay_focus_weight: float = 1.25,
    stable_class_edge_overlay_nonfocus_weight: float = 0.50,
    stable_class_edge_overlay_mode: str = "max",
    use_certified_graph_prior_core: bool = False,
    use_separate_path_candidate_prior: bool = False,
    graph_prior_core_floor: float = 0.05,
    graph_prior_core_threshold: float = 0.35,
    graph_prior_core_temperature: float = 0.05,
    graph_prior_core_top_k: int = 8,
    graph_prior_core_group_top_k: int = 3,
    graph_prior_core_direct_weight: float = 1.0,
    graph_prior_core_group_weight: float = 0.40,
    graph_prior_core_stability_weight: float = 0.50,
    graph_prior_core_prior_weight: float = 0.20,
    graph_prior_core_focus_weight: float = 1.25,
    graph_prior_core_nonfocus_weight: float = 0.50,
    use_class_conditioned_prior_admission: bool = False,
    class_prior_admission_floor: float = 0.10,
    use_adaptive_prior_admission: bool = False,
    adaptive_prior_admission_threshold: float = 0.20,
    adaptive_prior_admission_temperature: float = 0.05,
    use_candidate_prior_admission: bool = False,
    candidate_prior_admission_floor: float = 0.05,
    candidate_prior_admission_threshold: float = 0.50,
    candidate_prior_admission_temperature: float = 0.05,
    candidate_prior_admission_support_mode: str = "relative_evidence",
    candidate_prior_admission_scale: float = 0.50,
    candidate_prior_admission_min_support: float = 0.0,
    candidate_prior_admission_protected_min_support: float = 0.0,
    candidate_prior_admission_target: str = "coverage",
    use_edge_family_router: bool = False,
    edge_family_router_temperature: float = 1.0,
    edge_family_router_floor: float = 0.05,
    edge_family_router_blend: float = 1.0,
    edge_family_router_balance_weight: float = 0.0,
    use_edge_calibrator: bool = False,
    edge_calibrator_floor: float = 0.05,
    edge_calibrator_init_bias: float = 2.0,
    edge_calibrator_reg_weight: float = 0.0,
    use_path_reliability_calibrator: bool = False,
    path_reliability_context_scale: float = 1.0,
    path_reliability_context_reg_weight: float = 0.0,
    use_learned_path_admission: bool = False,
    path_admission_strength: float = 1.0,
    path_admission_reg_weight: float = 0.0,
    use_path_prior_consistency: bool = False,
    path_prior_consistency_strength: float = 0.0,
    path_prior_consistency_threshold: float = 0.25,
    path_prior_consistency_temperature: float = 0.05,
    path_prior_consistency_support_mode: str = "max",
    path_prior_consistency_class_floor: float = 0.25,
    use_path_evidence_consistency: bool = False,
    path_evidence_consistency_strength: float = 0.0,
    path_evidence_consistency_threshold: float = 0.35,
    path_evidence_consistency_temperature: float = 0.05,
    path_evidence_consistency_floor: float = 0.0,
    path_evidence_consistency_support_mode: str = "absolute",
    use_path_proposal_consistency: bool = False,
    path_proposal_consistency_strength: float = 0.0,
    path_proposal_consistency_threshold: float = 0.35,
    path_proposal_consistency_temperature: float = 0.05,
    path_proposal_consistency_floor: float = 0.10,
    path_proposal_consistency_support_mode: str = "max",
    path_proposal_consistency_protected_strength: float = 0.0,
    path_proposal_retention_fraction: float = 0.0,
    protect_order_anchor_target: bool = False,
    protect_order_anchor_path_nodes: bool = False,
    use_regime_prototype_residuals: bool = False,
    regime_prototype_k: int = 6,
    regime_healthy_stage_max: int = 0,
) -> dict[str, Any]:
    split = build_split(task, seed=seed)
    cmapss_rul_primary = bool(task.dataset == "cmapss" and str(task.target).lower() == "rul")
    train_idx = _limit_indices(split.train_idx, split.y_internal, seed=seed, limit=max_rows_per_split)
    val_idx = _limit_indices(split.val_idx, split.y_internal, seed=seed + 1, limit=max_rows_per_split)
    if cmapss_rul_primary:
        test_idx = select_cmapss_terminal_rul_indices(task, split.test_idx)
    else:
        test_idx = _limit_indices(split.test_idx, split.y_internal, seed=seed + 2, limit=max_rows_per_split)
    model_task = task
    regime_diagnostics: dict[str, Any] = {"enabled": False}
    if bool(use_regime_prototype_residuals):
        model_task, regime_diagnostics = apply_regime_prototype_residuals(
            task,
            train_idx,
            split.y_internal,
            n_regimes=regime_prototype_k,
            healthy_stage_max=regime_healthy_stage_max,
            seed=seed,
        )
    windows = build_causal_windows(model_task, window_size=window_size)
    x_train, x_val, x_test = scale_windows(windows, train_idx=train_idx, val_idx=val_idx, test_idx=test_idx)
    y_train = split.y_internal[train_idx]
    y_val = split.y_internal[val_idx]
    y_test = split.y_internal[test_idx]
    effective_health_aux_weight = float(health_aux_weight)
    health_aux_auto_enabled = False
    if cmapss_rul_primary and effective_health_aux_weight <= 0.0:
        effective_health_aux_weight = 1.0
        health_aux_auto_enabled = True
    health_all = build_health_index_targets(task, rul_cap=health_rul_cap) if effective_health_aux_weight > 0.0 else None
    health_train = health_all[train_idx] if health_all is not None else None
    health_val = health_all[val_idx] if health_all is not None else None
    health_test = health_all[test_idx] if health_all is not None else None
    rul_all = build_rul_targets(task) if cmapss_rul_primary else None
    rul_norm_all = build_capped_rul_targets(task, rul_cap=health_rul_cap) if cmapss_rul_primary else None
    rul_train_norm = rul_norm_all[train_idx] if rul_norm_all is not None else None
    rul_val = rul_all[val_idx] if rul_all is not None else None
    rul_test = rul_all[test_idx] if rul_all is not None else None
    feature_group_ids = infer_feature_group_ids(model_task.feature_cols)
    n_feature_groups = int(len(np.unique(feature_group_ids)))
    path_target_mask = None
    path_source_mask = None
    path_bridge_mask = None
    protected_order_anchor = None
    if (bool(protect_order_anchor_target) or bool(protect_order_anchor_path_nodes)) and model_task.order_col and str(model_task.order_col) in list(map(str, model_task.feature_cols)):
        order_idx = int(list(map(str, model_task.feature_cols)).index(str(model_task.order_col)))
        path_target_mask = np.ones(len(model_task.feature_cols), dtype=bool)
        path_target_mask[order_idx] = False
        protected_order_anchor = str(model_task.order_col)
        if bool(protect_order_anchor_path_nodes):
            path_source_mask = np.ones(len(model_task.feature_cols), dtype=bool)
            path_source_mask[order_idx] = False
            path_bridge_mask = np.ones(len(model_task.feature_cols), dtype=bool)
            path_bridge_mask[order_idx] = False
    task_salience, salience_diagnostics = (
        compute_train_group_salience(
            model_task,
            train_idx,
            split.y_internal,
            feature_group_ids,
            mode=salience_mode,
            lifecycle_weight=lifecycle_salience_weight,
            order_anchor_weight=order_anchor_evidence_weight,
            evidence_top_k=algorithmic_evidence_top_k,
        )
        if bool(use_task_salience)
        else (None, {"enabled": False})
    )
    path_evidence = None
    if bool(use_task_salience) and isinstance(salience_diagnostics, dict):
        raw_path_evidence = salience_diagnostics.pop("path_evidence_matrix", None)
        if raw_path_evidence is not None:
            path_evidence = np.asarray(raw_path_evidence, dtype=np.float32)
    class_path_evidence, class_evidence_diagnostics = (
        compute_train_class_path_evidence(
            x_train,
            y_train,
            feature_group_ids,
            n_classes=len(split.classes),
            top_k=class_evidence_top_k,
            mode=class_evidence_mode,
            max_lag=class_evidence_max_lag,
            lag_weight=class_evidence_lag_weight,
            family_k=class_evidence_family_k,
            family_weight=class_evidence_family_weight,
            focus_mode=class_evidence_focus_mode,
            focus_classes=_parse_optional_ints(class_evidence_focus_classes),
            focus_k=class_evidence_focus_k,
            focus_nonfocus_weight=class_evidence_focus_nonfocus_weight,
        )
        if bool(use_class_conditioned_evidence)
        else (None, {"enabled": False})
    )
    stable_path_evidence, stable_path_evidence_diagnostics = (
        compute_train_stable_path_evidence(
            x_train,
            y_train,
            feature_group_ids,
            n_classes=len(split.classes),
            split_count=stable_path_evidence_splits,
            min_vote_fraction=stable_path_evidence_min_vote_fraction,
            strength=stable_path_evidence_strength,
            top_k=stable_path_evidence_top_k,
            edge_top_k=stable_path_evidence_edge_top_k,
            mode=stable_path_evidence_mode,
            max_lag=stable_path_evidence_max_lag,
            lag_weight=stable_path_evidence_lag_weight,
            family_k=class_evidence_family_k,
            family_weight=class_evidence_family_weight,
            focus_mode=class_evidence_focus_mode,
            focus_classes=_parse_optional_ints(class_evidence_focus_classes),
            focus_k=class_evidence_focus_k,
            focus_nonfocus_weight=class_evidence_focus_nonfocus_weight,
        )
        if bool(use_stable_path_evidence)
        else (None, {"enabled": False})
    )
    stable_class_path_evidence = None
    stable_class_stability = None
    if bool(use_stable_path_evidence) and isinstance(stable_path_evidence_diagnostics, dict):
        raw_stable_path = stable_path_evidence_diagnostics.pop("path_evidence_matrix", None)
        raw_stable_class = stable_path_evidence_diagnostics.pop("class_path_evidence_matrix", None)
        raw_stable_stability = stable_path_evidence_diagnostics.pop("class_stability_matrix", None)
        path_mode = str(stable_path_evidence_path_mode or "max").strip().lower()
        if path_mode not in {"off", "max", "replace"}:
            path_mode = "max"
        stable_path_evidence_diagnostics["path_mode"] = path_mode
        if raw_stable_path is not None:
            stable_path_evidence = np.asarray(raw_stable_path, dtype=np.float32)
            if path_mode == "replace":
                path_evidence = stable_path_evidence
            elif path_mode == "max":
                path_evidence = (
                    stable_path_evidence
                    if path_evidence is None
                    else np.maximum(np.asarray(path_evidence, dtype=np.float32), stable_path_evidence)
                )
        if raw_stable_class is not None:
            stable_class_path_evidence = np.asarray(raw_stable_class, dtype=np.float32)
        if raw_stable_stability is not None:
            stable_class_stability = np.asarray(raw_stable_stability, dtype=np.float32)
        class_mode = str(stable_path_evidence_class_mode or "filter").strip().lower()
        if class_mode not in {"off", "max", "filter", "replace"}:
            class_mode = "filter"
        stable_path_evidence_diagnostics["class_mode"] = class_mode
        stable_path_evidence_diagnostics["class_floor"] = float(np.clip(stable_path_evidence_class_floor, 0.0, 1.0))
        if (
            bool(use_class_conditioned_evidence)
            and stable_class_path_evidence is not None
            and class_mode != "off"
        ):
            if class_path_evidence is None or class_mode == "replace":
                class_path_evidence = stable_class_path_evidence
            elif class_mode == "max":
                class_path_evidence = np.maximum(np.asarray(class_path_evidence, dtype=np.float32), stable_class_path_evidence)
            else:
                floor = float(np.clip(stable_path_evidence_class_floor, 0.0, 1.0))
                if stable_class_stability is not None and tuple(stable_class_stability.shape) == tuple(np.asarray(class_path_evidence).shape):
                    gate = floor + (1.0 - floor) * np.clip(stable_class_stability, 0.0, 1.0)
                    class_path_evidence = np.maximum(np.asarray(class_path_evidence, dtype=np.float32) * gate, stable_class_path_evidence)
                else:
                    class_path_evidence = np.maximum(
                        np.asarray(class_path_evidence, dtype=np.float32) * floor,
                        stable_class_path_evidence,
                    )
    class_evidence_quality_diagnostics: dict[str, Any] = {"enabled": False}
    if bool(use_class_evidence_quality_certificate):
        focus_for_certificate = (
            (class_evidence_diagnostics or {}).get("focus_classes")
            if isinstance(class_evidence_diagnostics, dict)
            else []
        )
        class_path_evidence, class_evidence_quality_diagnostics = apply_class_evidence_quality_certificate(
            class_path_evidence,
            stable_class_stability,
            focus_classes=focus_for_certificate,
            mode=class_evidence_quality_mode,
            floor=class_evidence_quality_floor,
            threshold=class_evidence_quality_threshold,
            temperature=class_evidence_quality_temperature,
        )
    actual_max_paths = resolve_path_budget(
        int(max_paths),
        n_feature_groups,
        auto_path_budget=bool(auto_path_budget),
    )
    prior_adjacency, prior_diagnostics = load_knowledge_graph_prior(
        task,
        mode=evidence_prior_mode,
        min_reliability=prior_min_reliability,
        group_expansion=bool(prior_group_expansion),
        group_expansion_strength=float(prior_group_expansion_strength),
    )
    external_family_prior_matrices = prior_diagnostics.pop("_external_family_prior_matrices", None)
    external_family_prior_matrices = (
        np.asarray(external_family_prior_matrices, dtype=np.float32)
        if external_family_prior_matrices is not None and np.asarray(external_family_prior_matrices).ndim == 3
        else None
    )
    external_family_prior_names = [str(name) for name in prior_diagnostics.pop("_external_family_prior_names", [])]
    llm_condition_activate_matrix = prior_diagnostics.pop("_llm_expert_condition_activate_matrix", None)
    llm_condition_activate_matrix = (
        _normalize_edge_prior(np.asarray(llm_condition_activate_matrix, dtype=np.float32))
        if llm_condition_activate_matrix is not None and np.asarray(llm_condition_activate_matrix).ndim == 2
        else None
    )
    llm_condition_suppress_matrix = prior_diagnostics.pop("_llm_expert_condition_suppress_matrix", None)
    llm_condition_suppress_matrix = (
        _normalize_edge_prior(np.asarray(llm_condition_suppress_matrix, dtype=np.float32))
        if llm_condition_suppress_matrix is not None and np.asarray(llm_condition_suppress_matrix).ndim == 2
        else None
    )
    llm_condition_records = prior_diagnostics.pop("_llm_expert_condition_records", [])
    if not isinstance(llm_condition_records, Sequence) or isinstance(llm_condition_records, (str, bytes, bytearray)):
        llm_condition_records = []
    prior_calibration_diagnostics: dict[str, Any] = {"enabled": False}
    if bool(calibrate_prior_edges) and prior_adjacency is not None:
        prior_adjacency, prior_calibration_diagnostics = calibrate_prior_adjacency_from_windows(
            prior_adjacency,
            x_train,
            max_lag=prior_calibration_max_lag,
            min_support=prior_calibration_min_support,
            strength=prior_calibration_strength,
        )
    algorithmic_prior, algorithmic_prior_diagnostics = compute_train_algorithmic_edge_prior(
        x_train,
        y_train,
        feature_group_ids,
        n_classes=len(split.classes),
        mode=algorithmic_edge_prior_mode,
        top_k=algorithmic_edge_prior_top_k,
        group_top_k=algorithmic_edge_prior_group_top_k,
        max_lag=algorithmic_edge_prior_max_lag,
        class_weight=algorithmic_edge_prior_class_weight,
        lag_weight=algorithmic_edge_prior_lag_weight,
        corr_weight=algorithmic_edge_prior_corr_weight,
        residual_weight=algorithmic_edge_prior_residual_weight,
        response_weight=algorithmic_edge_prior_response_weight,
        stability_weight=algorithmic_edge_prior_stability_weight,
        bank_min_votes=algorithmic_edge_prior_bank_min_votes,
        bank_single_view_scale=algorithmic_edge_prior_bank_single_view_scale,
        bank_vote_boost=algorithmic_edge_prior_bank_vote_boost,
        bank_global_budget_multiplier=algorithmic_edge_prior_bank_global_budget_multiplier,
        pool_multiplier=algorithmic_edge_prior_pool_multiplier,
        pool_min_score=algorithmic_edge_prior_pool_min_score,
        pool_rank_weight=algorithmic_edge_prior_pool_rank_weight,
    )
    edge_family_prior_matrices = algorithmic_prior_diagnostics.pop("_edge_family_prior_matrices", None)
    edge_family_prior_matrices = (
        np.asarray(edge_family_prior_matrices, dtype=np.float32)
        if edge_family_prior_matrices is not None and np.asarray(edge_family_prior_matrices).ndim == 3
        else None
    )
    edge_family_prior_names = [str(name) for name in algorithmic_prior_diagnostics.get("edge_family_prior_names", [])]
    algorithmic_path_candidate_prior = algorithmic_prior_diagnostics.pop("_path_candidate_prior_matrix", None)
    algorithmic_path_candidate_prior = (
        _normalize_edge_prior(np.asarray(algorithmic_path_candidate_prior, dtype=np.float32))
        if algorithmic_path_candidate_prior is not None and np.asarray(algorithmic_path_candidate_prior).ndim == 2
        else None
    )
    llm_condition_candidate_prior_baseline = (
        np.asarray(algorithmic_path_candidate_prior, dtype=np.float32).copy()
        if algorithmic_path_candidate_prior is not None
        else None
    )
    llm_condition_verifier_diagnostics: dict[str, Any] = {"enabled": False}
    if bool(use_llm_expert_condition_verifier):
        llm_condition_target = str(llm_condition_verifier_target or "candidate_gate").strip().lower()
        if llm_condition_target in {"candidate", "gate", "candidate_prior", "candidate_admission"}:
            llm_condition_target = "candidate_gate"
        if llm_condition_target in {"class", "class_path", "path_evidence"}:
            llm_condition_target = "class_evidence"
        if llm_condition_target not in {"candidate_gate", "class_evidence", "both"}:
            llm_condition_target = "candidate_gate"
        support_parts: list[np.ndarray] = []
        for candidate_support in (algorithmic_path_candidate_prior, algorithmic_prior, stable_path_evidence, path_evidence):
            if candidate_support is None:
                continue
            candidate_arr = np.asarray(candidate_support, dtype=np.float32)
            if candidate_arr.ndim == 2 and candidate_arr.shape[0] == candidate_arr.shape[1]:
                support_parts.append(_normalize_edge_prior(candidate_arr))
        verifier_support_diagnostics: dict[str, Any] = {"enabled": False}
        has_condition_evidence = (
            (llm_condition_activate_matrix is not None and bool(np.any(llm_condition_activate_matrix > 0.0)))
            or (llm_condition_suppress_matrix is not None and bool(np.any(llm_condition_suppress_matrix > 0.0)))
        )
        if not support_parts and bool(has_condition_evidence):
            verifier_support, verifier_support_diagnostics = compute_train_algorithmic_edge_prior(
                x_train,
                y_train,
                feature_group_ids,
                n_classes=len(split.classes),
                mode="hybrid",
                top_k=0,
                group_top_k=0,
                max_lag=max(1, int(algorithmic_edge_prior_max_lag)),
                class_weight=algorithmic_edge_prior_class_weight,
                lag_weight=algorithmic_edge_prior_lag_weight,
                corr_weight=algorithmic_edge_prior_corr_weight,
                residual_weight=algorithmic_edge_prior_residual_weight,
                response_weight=algorithmic_edge_prior_response_weight,
                stability_weight=algorithmic_edge_prior_stability_weight,
                bank_min_votes=algorithmic_edge_prior_bank_min_votes,
                bank_single_view_scale=algorithmic_edge_prior_bank_single_view_scale,
                bank_vote_boost=algorithmic_edge_prior_bank_vote_boost,
                bank_global_budget_multiplier=0.0,
                pool_multiplier=algorithmic_edge_prior_pool_multiplier,
                pool_min_score=algorithmic_edge_prior_pool_min_score,
                pool_rank_weight=algorithmic_edge_prior_pool_rank_weight,
            )
            if verifier_support is not None:
                verifier_support_arr = np.asarray(verifier_support, dtype=np.float32)
                if verifier_support_arr.ndim == 2 and verifier_support_arr.shape[0] == verifier_support_arr.shape[1]:
                    support_parts.append(_normalize_edge_prior(verifier_support_arr))
                    verifier_support_diagnostics = {
                        **dict(verifier_support_diagnostics or {}),
                        "enabled": True,
                        "source": "train_only_verifier_data_support_fallback",
                    }
        data_support_matrix = None
        if support_parts:
            data_support_matrix = support_parts[0]
            for support in support_parts[1:]:
                if tuple(support.shape) == tuple(data_support_matrix.shape):
                    data_support_matrix = np.maximum(data_support_matrix, support).astype(np.float32)
        candidate_gate_diagnostics: dict[str, Any] = {"enabled": False, "status": "not_requested"}
        class_gate_diagnostics: dict[str, Any] = {"enabled": False, "status": "not_requested"}
        if llm_condition_target in {"candidate_gate", "both"}:
            candidate_for_verifier = (
                algorithmic_path_candidate_prior
                if algorithmic_path_candidate_prior is not None
                else algorithmic_prior
            )
            algorithmic_path_candidate_prior, candidate_gate_diagnostics = (
                apply_llm_expert_condition_verifier_to_candidate_prior(
                    candidate_for_verifier,
                    condition_activate_matrix=llm_condition_activate_matrix,
                    condition_suppress_matrix=llm_condition_suppress_matrix,
                    condition_records=llm_condition_records,
                    data_support_matrix=data_support_matrix,
                    feature_cols=model_task.feature_cols,
                    class_labels=split.classes,
                    weight=llm_condition_verifier_weight,
                    min_data_support=llm_condition_verifier_min_data_support,
                    floor=llm_condition_verifier_floor,
                )
            )
        if llm_condition_target in {"class_evidence", "both"}:
            class_path_evidence, class_gate_diagnostics = apply_llm_expert_condition_verifier_to_class_evidence(
                class_path_evidence,
                condition_activate_matrix=llm_condition_activate_matrix,
                condition_suppress_matrix=llm_condition_suppress_matrix,
                condition_records=llm_condition_records,
                data_support_matrix=data_support_matrix,
                feature_cols=model_task.feature_cols,
                class_labels=split.classes,
                weight=llm_condition_verifier_weight,
                min_data_support=llm_condition_verifier_min_data_support,
                floor=llm_condition_verifier_floor,
            )
        llm_condition_verifier_diagnostics = {
            "enabled": bool(candidate_gate_diagnostics.get("enabled", False))
            or bool(class_gate_diagnostics.get("enabled", False)),
            "status": "ok"
            if bool(candidate_gate_diagnostics.get("enabled", False))
            or bool(class_gate_diagnostics.get("enabled", False))
            else "not_admitted",
            "target": llm_condition_target,
            "data_support": {
                "enabled": data_support_matrix is not None,
                "source_count": int(len(support_parts)),
                "fallback": {
                    key: value
                    for key, value in dict(verifier_support_diagnostics or {}).items()
                    if key
                    not in {
                        "_edge_family_prior_matrices",
                        "_path_candidate_prior_matrix",
                    }
                },
                "edge_count": int(np.count_nonzero(data_support_matrix > 0.0)) if data_support_matrix is not None else 0,
            },
            "candidate_gate": candidate_gate_diagnostics,
            "class_evidence": class_gate_diagnostics,
        }
    edge_family_count = int(edge_family_prior_matrices.shape[0]) if edge_family_prior_matrices is not None else 3
    loaded_external_edge_count = int(np.count_nonzero(np.asarray(prior_adjacency) > 0.0)) if prior_adjacency is not None else 0
    calibrated_external_families, calibrated_external_names, external_family_calibration_diagnostics = (
        _calibrate_external_edge_family_priors(
            external_family_prior_matrices,
            external_family_prior_names,
            algorithmic_prior,
            floor=external_family_calibration_floor,
            min_support=external_family_min_data_support,
        )
    )
    candidate_family_set = _parse_external_candidate_families(external_candidate_families)
    core_external_families, core_external_names, candidate_external_families, candidate_external_names, external_family_split_diagnostics = (
        _split_external_family_priors(
            calibrated_external_families,
            calibrated_external_names,
            candidate_families=candidate_family_set,
        )
    )
    graph_external_prior = (
        _mask_external_prior_by_family_support(prior_adjacency, core_external_families)
        if bool(external_edge_candidate_only)
        else prior_adjacency
    )
    effective_external_expert_scale, effective_external_llm_scale, effective_external_default_scale, source_complexity_diagnostics = (
        _resolve_external_candidate_scales(
            expert_scale=external_candidate_expert_scale,
            llm_scale=external_candidate_llm_scale,
            default_scale=external_candidate_default_scale,
            disable_source_complexity_penalty=disable_source_complexity_penalty,
        )
    )
    external_candidate_prior, external_candidate_diagnostics = _aggregate_external_candidate_prior(
        candidate_external_families if bool(external_edge_candidate_only) else calibrated_external_families,
        candidate_external_names if bool(external_edge_candidate_only) else calibrated_external_names,
        expert_scale=effective_external_expert_scale,
        llm_scale=effective_external_llm_scale,
        default_scale=effective_external_default_scale,
    )
    external_candidate_diagnostics = {
        **dict(external_candidate_diagnostics or {}),
        "source_complexity_penalty": source_complexity_diagnostics,
    }
    external_path_candidate_merge_diagnostics: dict[str, Any] = {"enabled": False}
    prior_algorithmic_combine_diagnostics: dict[str, Any] = {"enabled": False}
    if algorithmic_prior is not None and bool(algorithmic_prior_diagnostics.get("enabled", False)):
        if bool(algorithmic_edge_prior_candidate_only):
            base_candidate = (
                algorithmic_path_candidate_prior
                if algorithmic_path_candidate_prior is not None
                else np.asarray(algorithmic_prior, dtype=np.float32)
            )
            algorithmic_path_candidate_prior = _normalize_edge_prior(
                np.maximum(np.asarray(base_candidate, dtype=np.float32), np.asarray(algorithmic_prior, dtype=np.float32))
            )
            prior_algorithmic_combine_diagnostics = {
                "enabled": True,
                "mode": "candidate_only",
                "status": "algorithmic_prior_kept_as_path_candidate",
                "algorithmic_edges": int(np.count_nonzero(np.asarray(algorithmic_prior) > 0.0)),
                "path_candidate_edges": int(np.count_nonzero(algorithmic_path_candidate_prior > 0.0)),
                "external_edges": int(loaded_external_edge_count),
                "combined_edge_count": int(np.count_nonzero(np.asarray(graph_external_prior) > 0.0)) if graph_external_prior is not None else 0,
            }
            prior_diagnostics = {
                **prior_diagnostics,
                "combined_with_algorithmic_edge_prior": False,
                "algorithmic_candidate_only": True,
                "algorithmic_candidate_edge_count": int(np.count_nonzero(algorithmic_path_candidate_prior > 0.0)),
            }
            if bool(external_edge_candidate_only):
                prior_adjacency = graph_external_prior
                prior_diagnostics = {
                    **prior_diagnostics,
                    "external_edge_candidate_only": True,
                    "external_graph_prior_removed": graph_external_prior is None,
                    "external_core_edge_count": int(np.count_nonzero(np.asarray(graph_external_prior) > 0.0))
                    if graph_external_prior is not None
                    else 0,
                }
        elif bool(external_edge_candidate_only):
            prior_adjacency, prior_algorithmic_combine_diagnostics = combine_algorithmic_and_external_priors(
                graph_external_prior,
                algorithmic_prior,
                mode=prior_algorithmic_combine_mode,
                external_isolated_scale=prior_external_isolated_scale,
                overlap_boost=prior_overlap_boost,
                nonanchor_algorithmic_scale=prior_nonanchor_algorithmic_scale,
            )
            prior_algorithmic_combine_diagnostics = {
                **prior_algorithmic_combine_diagnostics,
                "mode": "external_candidate_only",
                "status": "candidate_families_removed_from_graph_prior",
                "external_candidate_edges": int(np.count_nonzero(external_candidate_prior > 0.0))
                if external_candidate_prior is not None
                else 0,
                "external_core_edges": int(np.count_nonzero(np.asarray(graph_external_prior) > 0.0))
                if graph_external_prior is not None
                else 0,
            }
            prior_diagnostics = {
                **prior_diagnostics,
                "combined_with_algorithmic_edge_prior": True,
                "algorithmic_combine_mode": "external_candidate_only",
                "external_edge_candidate_only": True,
                "external_core_edge_count": int(np.count_nonzero(np.asarray(graph_external_prior) > 0.0))
                if graph_external_prior is not None
                else 0,
                "combined_edge_count": int(np.count_nonzero(np.asarray(prior_adjacency) > 0.0)) if prior_adjacency is not None else 0,
            }
        else:
            prior_adjacency, prior_algorithmic_combine_diagnostics = combine_algorithmic_and_external_priors(
                graph_external_prior,
                algorithmic_prior,
                mode=prior_algorithmic_combine_mode,
                external_isolated_scale=prior_external_isolated_scale,
                overlap_boost=prior_overlap_boost,
                nonanchor_algorithmic_scale=prior_nonanchor_algorithmic_scale,
            )
            prior_diagnostics = {
                **prior_diagnostics,
                "combined_with_algorithmic_edge_prior": True,
                "algorithmic_combine_mode": str(prior_algorithmic_combine_mode or "max"),
                "combined_edge_count": int(np.count_nonzero(np.asarray(prior_adjacency) > 0.0)) if prior_adjacency is not None else 0,
            }
    elif bool(external_edge_candidate_only):
        prior_algorithmic_combine_diagnostics = {
            "enabled": True,
            "mode": "external_candidate_only",
            "status": "external_prior_kept_as_path_candidate_without_algorithmic_prior",
            "algorithmic_edges": 0,
            "external_edges": int(loaded_external_edge_count),
            "external_candidate_edges": int(np.count_nonzero(external_candidate_prior > 0.0))
            if external_candidate_prior is not None
            else 0,
            "external_core_edges": int(np.count_nonzero(np.asarray(graph_external_prior) > 0.0))
            if graph_external_prior is not None
            else 0,
            "combined_edge_count": int(np.count_nonzero(np.asarray(graph_external_prior) > 0.0))
            if graph_external_prior is not None
            else 0,
        }
        prior_adjacency = graph_external_prior
        prior_diagnostics = {
            **prior_diagnostics,
            "combined_with_algorithmic_edge_prior": False,
            "algorithmic_combine_mode": "external_candidate_only",
            "external_edge_candidate_only": True,
            "external_graph_prior_removed": graph_external_prior is None,
            "external_core_edge_count": int(np.count_nonzero(np.asarray(graph_external_prior) > 0.0))
            if graph_external_prior is not None
            else 0,
            "combined_edge_count": int(np.count_nonzero(np.asarray(prior_adjacency) > 0.0)) if prior_adjacency is not None else 0,
        }
    if bool(external_edge_candidate_only):
        algorithmic_path_candidate_prior, external_path_candidate_merge_diagnostics = _merge_path_candidate_prior_matrices(
            algorithmic_path_candidate_prior,
            external_candidate_prior,
        )
        llm_condition_candidate_prior_baseline, _baseline_external_merge = _merge_path_candidate_prior_matrices(
            llm_condition_candidate_prior_baseline,
            external_candidate_prior,
        )
    if not bool(external_edge_candidate_only):
        edge_family_prior_matrices, edge_family_prior_names = _merge_edge_family_prior_matrices(
            edge_family_prior_matrices,
            edge_family_prior_names,
            calibrated_external_families,
            calibrated_external_names,
        )
    edge_family_count = int(edge_family_prior_matrices.shape[0]) if edge_family_prior_matrices is not None else 3
    if edge_family_prior_names:
        algorithmic_prior_diagnostics["edge_family_prior_names"] = edge_family_prior_names
        prior_diagnostics = {
            **prior_diagnostics,
            "combined_edge_family_names": edge_family_prior_names,
        }
    prior_diagnostics = {
        **prior_diagnostics,
        "external_family_calibration": external_family_calibration_diagnostics,
        "external_family_split": external_family_split_diagnostics,
        "external_candidate_prior": external_candidate_diagnostics,
        "external_path_candidate_merge": external_path_candidate_merge_diagnostics,
        "external_edge_candidate_only": bool(external_edge_candidate_only),
        "llm_expert_condition_verifier_admission": llm_condition_verifier_diagnostics,
    }
    stable_class_edge_overlay_diagnostics: dict[str, Any] = {"enabled": False}
    if bool(use_stable_class_edge_overlay):
        focus_for_overlay = (
            (class_evidence_diagnostics or {}).get("focus_classes")
            if isinstance(class_evidence_diagnostics, dict)
            else []
        )
        prior_adjacency, stable_class_edge_overlay_diagnostics = apply_stable_class_edge_overlay(
            prior_adjacency,
            stable_path_evidence,
            stable_class_path_evidence,
            feature_group_ids,
            focus_classes=focus_for_overlay,
            scale=stable_class_edge_overlay_scale,
            top_k=stable_class_edge_overlay_top_k,
            group_top_k=stable_class_edge_overlay_group_top_k,
            focus_weight=stable_class_edge_overlay_focus_weight,
            nonfocus_weight=stable_class_edge_overlay_nonfocus_weight,
            mode=stable_class_edge_overlay_mode,
        )
        prior_diagnostics = {
            **prior_diagnostics,
            "stable_class_edge_overlay": stable_class_edge_overlay_diagnostics,
            "stable_class_edge_overlay_edge_count": int(np.count_nonzero(np.asarray(prior_adjacency) > 0.0))
            if prior_adjacency is not None
            else 0,
        }
    path_family_quality_diagnostics: dict[str, Any] = {"enabled": False}
    if bool(use_path_family_quality_certificate):
        focus_for_certificate = (
            (class_evidence_diagnostics or {}).get("focus_classes")
            if isinstance(class_evidence_diagnostics, dict)
            else []
        )
        class_path_evidence, path_family_quality_diagnostics = apply_path_family_quality_certificate(
            class_path_evidence,
            prior_adjacency,
            feature_group_ids,
            stable_class_stability=stable_class_stability,
            focus_classes=focus_for_certificate,
            mode=path_family_quality_mode,
            floor=path_family_quality_floor,
            threshold=path_family_quality_threshold,
            temperature=path_family_quality_temperature,
            direct_weight=path_family_quality_direct_weight,
            group_weight=path_family_quality_group_weight,
            stability_weight=path_family_quality_stability_weight,
            family_k=path_family_quality_family_k,
            family_weight=path_family_quality_family_weight,
        )
    candidate_protected_class_weights: np.ndarray | None = None
    if bool(use_path_family_protected_proposal_weights):
        raw_protection_weights = (
            path_family_quality_diagnostics.get("class_proposal_protection_weight")
            if isinstance(path_family_quality_diagnostics, dict)
            else None
        )
        if raw_protection_weights is not None:
            protection_weights = np.asarray(raw_protection_weights, dtype=np.float32).reshape(-1)
            if int(protection_weights.size) == len(split.classes) and float(np.max(protection_weights)) > 0.0:
                candidate_protected_class_weights = np.clip(protection_weights, 0.0, 1.0).astype(np.float32)
    graph_prior_core_diagnostics: dict[str, Any] = {"enabled": False}
    path_candidate_prior = algorithmic_path_candidate_prior
    if bool(use_certified_graph_prior_core):
        raw_candidate_prior = (
            np.asarray(algorithmic_path_candidate_prior, dtype=np.float32).copy()
            if algorithmic_path_candidate_prior is not None
            else (None if prior_adjacency is None else np.asarray(prior_adjacency, dtype=np.float32).copy())
        )
        focus_for_certificate = (
            (class_evidence_diagnostics or {}).get("focus_classes")
            if isinstance(class_evidence_diagnostics, dict)
            else []
        )
        prior_adjacency, graph_prior_core_diagnostics = apply_graph_prior_core_certificate(
            prior_adjacency,
            class_path_evidence,
            feature_group_ids,
            stable_class_stability=stable_class_stability,
            focus_classes=focus_for_certificate,
            floor=graph_prior_core_floor,
            threshold=graph_prior_core_threshold,
            temperature=graph_prior_core_temperature,
            top_k=graph_prior_core_top_k,
            group_top_k=graph_prior_core_group_top_k,
            direct_weight=graph_prior_core_direct_weight,
            group_weight=graph_prior_core_group_weight,
            stability_weight=graph_prior_core_stability_weight,
            prior_weight=graph_prior_core_prior_weight,
            focus_weight=graph_prior_core_focus_weight,
            nonfocus_weight=graph_prior_core_nonfocus_weight,
        )
        if bool(use_separate_path_candidate_prior) or algorithmic_path_candidate_prior is not None:
            path_candidate_prior = raw_candidate_prior
    elif bool(use_separate_path_candidate_prior) and path_candidate_prior is None:
        path_candidate_prior = None if prior_adjacency is None else np.asarray(prior_adjacency, dtype=np.float32).copy()
    effective_prior_strength = float(prior_strength)
    if (
        bool(algorithmic_prior_diagnostics.get("enabled", False))
        and not bool(algorithmic_edge_prior_candidate_only)
        and float(algorithmic_edge_prior_strength) > 0.0
    ):
        effective_prior_strength = max(effective_prior_strength, float(algorithmic_edge_prior_strength))
    condition_verifier_class_evidence_enabled = bool(
        isinstance(llm_condition_verifier_diagnostics, Mapping)
        and (
            llm_condition_verifier_diagnostics.get("class_evidence", {})
            if isinstance(llm_condition_verifier_diagnostics.get("class_evidence", {}), Mapping)
            else {}
        ).get("enabled", False)
        and class_path_evidence is not None
    )
    config = _variant_config(
        variant=variant,
        n_features=x_train.shape[2],
        n_classes=len(split.classes),
        hidden_dim=hidden_dim,
        dropout=dropout,
        graph_top_k=graph_top_k,
        max_paths=actual_max_paths,
        prior_strength=effective_prior_strength,
        path_coverage_mode=path_coverage_mode,
        coverage_dedup_mode=coverage_dedup_mode,
        coverage_redundancy_penalty=coverage_redundancy_penalty,
        deduplicate_exact_paths=deduplicate_exact_paths,
        use_task_salience=(
            bool(use_task_salience)
            or bool(use_class_conditioned_evidence)
            or bool(use_stable_path_evidence)
            or condition_verifier_class_evidence_enabled
        ),
        salience_selection_strength=salience_selection_strength,
        salience_coverage_fraction=salience_coverage_fraction,
        use_temporal_descriptors=use_temporal_descriptors,
        temporal_descriptor_weight=temporal_descriptor_weight,
        temporal_encoder_mode=temporal_encoder_mode,
        use_temporal_mixer=use_temporal_mixer,
        temporal_mixer_type=temporal_mixer_type,
        temporal_mixer_depth=temporal_mixer_depth,
        use_rul_temporal_anchor_fusion=use_rul_temporal_anchor_fusion,
        rul_anchor_residual_scale=rul_anchor_residual_scale,
        rul_anchor_gate_bias=rul_anchor_gate_bias,
        use_multihop_paths=use_multihop_paths,
        multihop_path_fraction=multihop_path_fraction,
        use_context_router=use_context_router,
        prior_coverage_fraction=prior_coverage_fraction,
        candidate_coverage_fraction=candidate_coverage_fraction,
        use_class_conditioned_evidence=bool(use_class_conditioned_evidence) or condition_verifier_class_evidence_enabled,
        class_evidence_gate_threshold=class_evidence_gate_threshold,
        class_evidence_gate_temperature=class_evidence_gate_temperature,
        class_evidence_gate_floor=class_evidence_gate_floor,
        class_evidence_router_temperature=class_evidence_router_temperature,
        class_evidence_router_top_k=class_evidence_router_top_k,
        use_class_conditioned_prior_admission=use_class_conditioned_prior_admission,
        class_prior_admission_floor=class_prior_admission_floor,
        use_adaptive_prior_admission=use_adaptive_prior_admission,
        adaptive_prior_admission_threshold=adaptive_prior_admission_threshold,
        adaptive_prior_admission_temperature=adaptive_prior_admission_temperature,
        use_candidate_prior_admission=use_candidate_prior_admission,
        candidate_prior_admission_floor=candidate_prior_admission_floor,
        candidate_prior_admission_threshold=candidate_prior_admission_threshold,
        candidate_prior_admission_temperature=candidate_prior_admission_temperature,
        candidate_prior_admission_support_mode=candidate_prior_admission_support_mode,
        candidate_prior_admission_scale=candidate_prior_admission_scale,
        candidate_prior_admission_min_support=candidate_prior_admission_min_support,
        candidate_prior_admission_protected_min_support=candidate_prior_admission_protected_min_support,
        candidate_prior_admission_target=candidate_prior_admission_target,
        use_edge_family_router=bool(use_edge_family_router) and edge_family_prior_matrices is not None,
        edge_family_count=edge_family_count,
        edge_family_router_temperature=edge_family_router_temperature,
        edge_family_router_floor=edge_family_router_floor,
        edge_family_router_blend=edge_family_router_blend,
        use_edge_calibrator=use_edge_calibrator,
        edge_calibrator_floor=edge_calibrator_floor,
        edge_calibrator_init_bias=edge_calibrator_init_bias,
        use_path_reliability_calibrator=use_path_reliability_calibrator,
        path_reliability_context_scale=path_reliability_context_scale,
        use_learned_path_admission=use_learned_path_admission,
        path_admission_strength=path_admission_strength,
        use_path_prior_consistency=use_path_prior_consistency,
        path_prior_consistency_strength=path_prior_consistency_strength,
        path_prior_consistency_threshold=path_prior_consistency_threshold,
        path_prior_consistency_temperature=path_prior_consistency_temperature,
        path_prior_consistency_support_mode=path_prior_consistency_support_mode,
        path_prior_consistency_class_floor=path_prior_consistency_class_floor,
        use_path_evidence_consistency=use_path_evidence_consistency,
        path_evidence_consistency_strength=path_evidence_consistency_strength,
        path_evidence_consistency_threshold=path_evidence_consistency_threshold,
        path_evidence_consistency_temperature=path_evidence_consistency_temperature,
        path_evidence_consistency_floor=path_evidence_consistency_floor,
        path_evidence_consistency_support_mode=path_evidence_consistency_support_mode,
        use_path_proposal_consistency=use_path_proposal_consistency,
        path_proposal_consistency_strength=path_proposal_consistency_strength,
        path_proposal_consistency_threshold=path_proposal_consistency_threshold,
        path_proposal_consistency_temperature=path_proposal_consistency_temperature,
        path_proposal_consistency_floor=path_proposal_consistency_floor,
        path_proposal_consistency_support_mode=path_proposal_consistency_support_mode,
        path_proposal_consistency_protected_strength=path_proposal_consistency_protected_strength,
        path_proposal_retention_fraction=path_proposal_retention_fraction,
    )
    llm_condition_candidate_gate_enabled = bool(
        isinstance(llm_condition_verifier_diagnostics, Mapping)
        and isinstance(llm_condition_verifier_diagnostics.get("candidate_gate", {}), Mapping)
        and bool(llm_condition_verifier_diagnostics.get("candidate_gate", {}).get("enabled", False))
    )
    use_candidate_validation_admission = bool(use_llm_condition_verifier_validation_admission) and bool(
        llm_condition_candidate_gate_enabled
    )
    val_proba, test_proba, diagnostics = train_model(
        x_train,
        y_train,
        x_val,
        y_val,
        x_test,
        config=config,
        epochs=epochs,
        batch_size=batch_size,
        learning_rate=learning_rate,
        classification_loss_weight=classification_loss_weight,
        forecast_weight=forecast_weight,
        graph_weight=graph_weight,
        focal_loss_gamma=focal_loss_gamma,
        label_smoothing=label_smoothing,
        ordinal_loss_weight=ordinal_loss_weight,
        ordinal_boundary_loss_weight=ordinal_boundary_loss_weight,
        ordinal_boundary_focal_gamma=ordinal_boundary_focal_gamma,
        ordinal_boundary_focus=ordinal_boundary_focus,
        path_entropy_weight=path_entropy_weight,
        path_aux_weight=path_aux_weight,
        coarse_aux_weight=coarse_aux_weight,
        evidence_router_aux_weight=evidence_router_aux_weight,
        edge_family_router_balance_weight=edge_family_router_balance_weight,
        edge_calibrator_reg_weight=edge_calibrator_reg_weight,
        path_reliability_context_reg_weight=path_reliability_context_reg_weight,
        path_admission_reg_weight=path_admission_reg_weight,
        health_aux_weight=effective_health_aux_weight,
        rul_loss_weight=rul_loss_weight,
        prior_adjacency=prior_adjacency,
        path_candidate_prior=path_candidate_prior,
        edge_family_prior_matrices=edge_family_prior_matrices,
        feature_group_ids=feature_group_ids,
        task_salience=task_salience,
        path_evidence=path_evidence,
        class_path_evidence=class_path_evidence,
        candidate_protected_classes=(
            (class_evidence_diagnostics or {}).get("focus_classes")
            if isinstance(class_evidence_diagnostics, dict)
            else None
        ),
        candidate_protected_class_weights=candidate_protected_class_weights,
        path_target_mask=path_target_mask,
        path_source_mask=path_source_mask,
        path_bridge_mask=path_bridge_mask,
        health_train=health_train,
        health_val=health_val,
        health_test=health_test,
        rul_train_norm=rul_train_norm,
        seed=seed,
        rul_val=rul_val,
        rul_test=rul_test,
        health_rul_cap=health_rul_cap,
        path_candidate_prior_baseline=(
            llm_condition_candidate_prior_baseline if use_candidate_validation_admission else None
        ),
        use_path_candidate_prior_validation_admission=use_candidate_validation_admission,
        path_candidate_prior_validation_min_gain=llm_condition_verifier_min_val_gain,
        device=device,
    )
    if bool((diagnostics.get("candidate_prior_validation_admission") or {}).get("enabled", False)):
        prior_diagnostics = {
            **prior_diagnostics,
            "llm_condition_verifier_validation_admission": diagnostics["candidate_prior_validation_admission"],
        }
    base_val_proba = np.asarray(val_proba, dtype=np.float64)
    base_test_proba = np.asarray(test_proba, dtype=np.float64)
    prototype_fusion_diagnostics: dict[str, Any] = {"enabled": False}
    if bool(use_prototype_posterior_fusion):
        val_proba, test_proba, prototype_fusion_diagnostics = apply_prototype_posterior_fusion(
            x_train,
            y_train,
            x_val,
            y_val,
            x_test,
            base_val_proba,
            base_test_proba,
            n_classes=len(split.classes),
            max_blend=prototype_fusion_max_blend,
            blend_steps=prototype_fusion_blend_steps,
            temperature_grid=prototype_fusion_temperature_grid,
            min_val_gain=prototype_fusion_min_val_gain,
        )
    one_class_fusion_diagnostics: dict[str, Any] = {"enabled": False}
    if bool(use_one_class_posterior_fusion):
        val_proba, test_proba, one_class_fusion_diagnostics = apply_one_class_posterior_fusion(
            x_train,
            y_train,
            x_val,
            y_val,
            x_test,
            val_proba,
            test_proba,
            n_classes=len(split.classes),
            max_blend=one_class_fusion_max_blend,
            blend_steps=one_class_fusion_blend_steps,
            temperature_grid=one_class_fusion_temperature_grid,
            threshold_grid=one_class_fusion_threshold_grid,
            min_val_gain=one_class_fusion_min_val_gain,
        )
    ordinal_posterior_diagnostics: dict[str, Any] = {"enabled": False}
    if bool(use_ordinal_posterior_calibration):
        val_proba, test_proba, ordinal_posterior_diagnostics = apply_ordinal_threshold_posterior_calibration(
            y_val,
            val_proba,
            test_proba,
            n_classes=len(split.classes),
            max_blend=ordinal_posterior_max_blend,
            blend_steps=ordinal_posterior_blend_steps,
            smoothing=ordinal_posterior_smoothing,
            min_val_gain=ordinal_posterior_min_val_gain,
        )
    base_val_metrics = summarize_classification(y_val, base_val_proba)
    base_test_metrics = summarize_classification(y_test, base_test_proba)
    tuned_threshold = tune_binary_threshold(y_val, val_proba)
    val_metrics = summarize_classification(y_val, val_proba)
    test_metrics = summarize_classification(y_test, test_proba)
    thresholded_val_metrics = (
        summarize_classification(y_val, val_proba, positive_threshold=tuned_threshold)
        if tuned_threshold is not None
        else None
    )
    thresholded_test_metrics = (
        summarize_classification(y_test, test_proba, positive_threshold=tuned_threshold)
        if tuned_threshold is not None
        else None
    )
    primary_metric_family = "classification"
    primary_test_metrics = thresholded_test_metrics or test_metrics
    if cmapss_rul_primary and diagnostics.get("test_rul_metrics"):
        primary_metric_family = "rul_regression"
        primary_test_metrics = {
            **dict(diagnostics.get("test_rul_metrics") or {}),
            "health_mae": diagnostics.get("test_health_mae"),
            "aux_macro_f1": float(test_metrics.get("macro_f1", 0.0)),
            "aux_balanced_accuracy": float(test_metrics.get("balanced_accuracy", 0.0)),
        }
    rul_prediction_records = build_rul_prediction_records(
        task.meta,
        test_idx,
        diagnostics.get("test_rul_true"),
        diagnostics.get("test_rul_pred"),
        prediction_source=str(diagnostics.get("rul_prediction_source") or "unknown"),
    )
    rul_subset_metrics = summarize_rul_by_subset(rul_prediction_records)
    classification_prediction_records = (
        []
        if cmapss_rul_primary
        else build_classification_prediction_records(
            task.meta,
            test_idx,
            y_test,
            test_proba,
            class_id_mapping=split.class_id_mapping,
            positive_threshold=tuned_threshold,
        )
    )
    result = {
        "status": "ok",
        "dataset": model_task.dataset,
        "target": model_task.target,
        "task": model_task.task,
        "variant": str(variant),
        "seed": int(seed),
        "protocol": "ready_csv_causal_windows_same_backbone",
        "primary_metric_family": primary_metric_family,
        "split_protocol": split.split_protocol,
        "validation_group_cols": list(split.validation_group_cols),
        "n_rows_total": int(len(task.labels)),
        "n_features": int(len(model_task.feature_cols)),
        "window_size": int(window_size),
        "train_size": int(len(train_idx)),
        "val_size": int(len(val_idx)),
        "test_size": int(len(test_idx)),
        "rul_eval_protocol": "terminal_test_unit" if cmapss_rul_primary else None,
        "class_id_mapping": split.class_id_mapping,
        "class_distribution_total": {str(int(k)): int(v) for k, v in pd.Series(task.labels).value_counts().sort_index().items()},
        "evidence_prior": prior_diagnostics,
        "prior_edge_calibration": prior_calibration_diagnostics,
        "algorithmic_edge_prior": algorithmic_prior_diagnostics,
        "prior_algorithmic_combination": prior_algorithmic_combine_diagnostics,
        "task_salience": salience_diagnostics,
        "class_conditioned_evidence": class_evidence_diagnostics,
        "stable_path_evidence": stable_path_evidence_diagnostics,
        "class_evidence_quality_certificate": class_evidence_quality_diagnostics,
        "path_family_quality_certificate": path_family_quality_diagnostics,
        "candidate_protected_class_weighting": {
            "enabled": bool(candidate_protected_class_weights is not None),
            "source": "path_family_quality_certificate"
            if candidate_protected_class_weights is not None
            else "focus_classes",
            "weights": (
                [float(value) for value in candidate_protected_class_weights.reshape(-1)]
                if candidate_protected_class_weights is not None
                else []
            ),
        },
        "stable_class_edge_overlay": stable_class_edge_overlay_diagnostics,
        "graph_prior_core_certificate": graph_prior_core_diagnostics,
        "prototype_posterior_fusion": prototype_fusion_diagnostics,
        "one_class_posterior_fusion": one_class_fusion_diagnostics,
        "ordinal_posterior_calibration": ordinal_posterior_diagnostics,
        "base_val_metrics": base_val_metrics,
        "base_test_metrics": base_test_metrics,
        "val_metrics": val_metrics,
        "test_metrics": test_metrics,
        "positive_threshold": tuned_threshold,
        "thresholded_val_metrics": thresholded_val_metrics,
        "thresholded_test_metrics": thresholded_test_metrics,
        "primary_test_metrics": primary_test_metrics,
        "classification_prediction_records": classification_prediction_records,
        "rul_prediction_records": rul_prediction_records,
        "rul_subset_metrics": rul_subset_metrics,
        "efficiency": {
            "parameters": diagnostics["parameters"],
            "train_seconds": diagnostics["train_seconds"],
            "train_samples_per_second": diagnostics["train_samples_per_second"],
            "classification_loss_weight": diagnostics["classification_loss_weight"],
            "ordinal_loss_weight": diagnostics["ordinal_loss_weight"],
            "ordinal_boundary_loss_weight": diagnostics["ordinal_boundary_loss_weight"],
            "ordinal_boundary_focal_gamma": diagnostics["ordinal_boundary_focal_gamma"],
            "ordinal_boundary_focus": diagnostics["ordinal_boundary_focus"],
            "path_entropy_weight": diagnostics["path_entropy_weight"],
            "path_aux_weight": diagnostics["path_aux_weight"],
            "coarse_aux_weight": diagnostics["coarse_aux_weight"],
            "evidence_router_aux_weight": diagnostics["evidence_router_aux_weight"],
            "edge_calibrator_reg_weight": diagnostics["edge_calibrator_reg_weight"],
            "path_reliability_context_reg_weight": diagnostics["path_reliability_context_reg_weight"],
            "path_admission_reg_weight": diagnostics["path_admission_reg_weight"],
            "health_aux_weight": diagnostics["health_aux_weight"],
            "rul_loss_weight": diagnostics["rul_loss_weight"],
            "direct_rul_enabled": diagnostics["direct_rul_enabled"],
            "rul_prediction_source": diagnostics["rul_prediction_source"],
            "val_health_mae": diagnostics["val_health_mae"],
            "test_health_mae": diagnostics["test_health_mae"],
            "health_rul_cap": diagnostics["health_rul_cap"],
            "val_rul_metrics": diagnostics["val_rul_metrics"],
            "test_rul_metrics": diagnostics["test_rul_metrics"],
            "val_health_rul_metrics": diagnostics["val_health_rul_metrics"],
            "test_health_rul_metrics": diagnostics["test_health_rul_metrics"],
            "val_direct_rul_metrics": diagnostics["val_direct_rul_metrics"],
            "test_direct_rul_metrics": diagnostics["test_direct_rul_metrics"],
            "val_temporal_rul_metrics": diagnostics["val_temporal_rul_metrics"],
            "test_temporal_rul_metrics": diagnostics["test_temporal_rul_metrics"],
            "val_anchor_rul_metrics": diagnostics["val_anchor_rul_metrics"],
            "test_anchor_rul_metrics": diagnostics["test_anchor_rul_metrics"],
            "val_rul_mae": (diagnostics.get("val_rul_metrics") or {}).get("rul_mae"),
            "val_rul_rmse": (diagnostics.get("val_rul_metrics") or {}).get("rul_rmse"),
            "val_rul_score": (diagnostics.get("val_rul_metrics") or {}).get("rul_score"),
            "test_rul_mae": (diagnostics.get("test_rul_metrics") or {}).get("rul_mae"),
            "test_rul_rmse": (diagnostics.get("test_rul_metrics") or {}).get("rul_rmse"),
            "test_rul_score": (diagnostics.get("test_rul_metrics") or {}).get("rul_score"),
            "test_inference_seconds": diagnostics["test_diagnostics"]["inference_seconds"],
            "test_inference_samples_per_second": diagnostics["test_diagnostics"]["inference_samples_per_second"],
            "edge_family_router_balance_weight": diagnostics["edge_family_router_balance_weight"],
        },
        "path_budget": {
            "requested_max_paths": int(max_paths),
            "actual_max_paths": int(actual_max_paths),
            "auto_path_budget": bool(auto_path_budget),
            "n_feature_groups": int(n_feature_groups),
            "path_coverage_mode": str(path_coverage_mode or "target_group"),
            "coverage_dedup_mode": str(coverage_dedup_mode or "soft"),
            "coverage_redundancy_penalty": float(coverage_redundancy_penalty),
            "deduplicate_exact_paths": bool(deduplicate_exact_paths),
            "ordinal_loss_weight": float(ordinal_loss_weight),
            "ordinal_boundary_loss_weight": float(ordinal_boundary_loss_weight),
            "ordinal_boundary_focal_gamma": float(ordinal_boundary_focal_gamma),
            "ordinal_boundary_focus": float(ordinal_boundary_focus),
            "path_entropy_weight": float(path_entropy_weight),
            "path_aux_weight": float(path_aux_weight),
            "coarse_aux_weight": float(coarse_aux_weight),
            "evidence_router_aux_weight": float(evidence_router_aux_weight),
            "health_aux_weight": float(effective_health_aux_weight),
            "health_aux_requested_weight": float(health_aux_weight),
            "health_aux_auto_enabled": bool(health_aux_auto_enabled),
            "health_rul_cap": float(health_rul_cap),
            "health_aux_enabled": bool(health_all is not None),
            "rul_loss_weight": float(rul_loss_weight),
            "classification_loss_weight": float(classification_loss_weight),
            "direct_rul_enabled": bool(float(rul_loss_weight) > 0.0 and rul_train_norm is not None),
            "cmapss_rul_primary": bool(cmapss_rul_primary),
            "cmapss_terminal_test_eval": bool(cmapss_rul_primary),
            "use_task_salience": bool(use_task_salience),
            "salience_mode": str(salience_mode or "class"),
            "lifecycle_salience_weight": float(lifecycle_salience_weight),
            "order_anchor_evidence_weight": float(order_anchor_evidence_weight),
            "algorithmic_evidence_top_k": int(algorithmic_evidence_top_k),
            "salience_selection_strength": float(salience_selection_strength),
            "salience_coverage_fraction": float(salience_coverage_fraction),
            "use_temporal_descriptors": bool(use_temporal_descriptors),
            "temporal_descriptor_weight": float(temporal_descriptor_weight),
            "temporal_encoder_mode": str(config.temporal_encoder_mode),
            "use_temporal_mixer": bool(use_temporal_mixer),
            "temporal_mixer_type": str(temporal_mixer_type or "conv"),
            "temporal_mixer_depth": int(temporal_mixer_depth),
            "use_rul_temporal_anchor_fusion": bool(use_rul_temporal_anchor_fusion),
            "rul_anchor_residual_scale": float(rul_anchor_residual_scale),
            "rul_anchor_gate_bias": float(rul_anchor_gate_bias),
            "use_prototype_posterior_fusion": bool(use_prototype_posterior_fusion),
            "prototype_fusion_max_blend": float(prototype_fusion_max_blend),
            "prototype_fusion_blend_steps": int(prototype_fusion_blend_steps),
            "prototype_fusion_temperature_grid": str(prototype_fusion_temperature_grid),
            "prototype_fusion_min_val_gain": float(prototype_fusion_min_val_gain),
            "use_one_class_posterior_fusion": bool(use_one_class_posterior_fusion),
            "one_class_fusion_max_blend": float(one_class_fusion_max_blend),
            "one_class_fusion_blend_steps": int(one_class_fusion_blend_steps),
            "one_class_fusion_temperature_grid": str(one_class_fusion_temperature_grid),
            "one_class_fusion_threshold_grid": str(one_class_fusion_threshold_grid),
            "one_class_fusion_min_val_gain": float(one_class_fusion_min_val_gain),
            "use_ordinal_posterior_calibration": bool(use_ordinal_posterior_calibration),
            "ordinal_posterior_max_blend": float(ordinal_posterior_max_blend),
            "ordinal_posterior_blend_steps": int(ordinal_posterior_blend_steps),
            "ordinal_posterior_smoothing": float(ordinal_posterior_smoothing),
            "ordinal_posterior_min_val_gain": float(ordinal_posterior_min_val_gain),
            "use_multihop_paths": bool(use_multihop_paths),
            "multihop_path_fraction": float(multihop_path_fraction),
            "use_context_router": bool(use_context_router),
            "prior_coverage_fraction": float(prior_coverage_fraction),
            "candidate_coverage_fraction": float(candidate_coverage_fraction),
            "focal_loss_gamma": float(focal_loss_gamma),
            "label_smoothing": float(label_smoothing),
            "calibrate_prior_edges": bool(calibrate_prior_edges),
            "prior_calibration_max_lag": int(prior_calibration_max_lag),
            "prior_calibration_min_support": float(prior_calibration_min_support),
            "prior_calibration_strength": float(prior_calibration_strength),
            "algorithmic_edge_prior_mode": str(algorithmic_edge_prior_mode or "none"),
            "algorithmic_edge_prior_top_k": int(algorithmic_edge_prior_top_k),
            "algorithmic_edge_prior_group_top_k": int(algorithmic_edge_prior_group_top_k),
            "algorithmic_edge_prior_max_lag": int(algorithmic_edge_prior_max_lag),
            "algorithmic_edge_prior_strength": float(algorithmic_edge_prior_strength),
            "algorithmic_edge_prior_class_weight": float(algorithmic_edge_prior_class_weight),
            "algorithmic_edge_prior_lag_weight": float(algorithmic_edge_prior_lag_weight),
            "algorithmic_edge_prior_corr_weight": float(algorithmic_edge_prior_corr_weight),
            "algorithmic_edge_prior_residual_weight": float(algorithmic_edge_prior_residual_weight),
            "algorithmic_edge_prior_response_weight": float(algorithmic_edge_prior_response_weight),
            "algorithmic_edge_prior_stability_weight": float(algorithmic_edge_prior_stability_weight),
            "algorithmic_edge_prior_bank_min_votes": int(algorithmic_edge_prior_bank_min_votes),
            "algorithmic_edge_prior_bank_single_view_scale": float(algorithmic_edge_prior_bank_single_view_scale),
            "algorithmic_edge_prior_bank_vote_boost": float(algorithmic_edge_prior_bank_vote_boost),
            "algorithmic_edge_prior_bank_global_budget_multiplier": float(algorithmic_edge_prior_bank_global_budget_multiplier),
            "algorithmic_edge_prior_pool_multiplier": float(algorithmic_edge_prior_pool_multiplier),
            "algorithmic_edge_prior_pool_min_score": float(algorithmic_edge_prior_pool_min_score),
            "algorithmic_edge_prior_pool_rank_weight": float(algorithmic_edge_prior_pool_rank_weight),
            "algorithmic_edge_prior_candidate_only": bool(algorithmic_edge_prior_candidate_only),
            "prior_algorithmic_combine_mode": str(prior_algorithmic_combine_mode or "max"),
            "prior_external_isolated_scale": float(prior_external_isolated_scale),
            "prior_overlap_boost": float(prior_overlap_boost),
            "prior_nonanchor_algorithmic_scale": float(prior_nonanchor_algorithmic_scale),
            "external_edge_candidate_only": bool(external_edge_candidate_only),
            "external_candidate_families": sorted(_parse_external_candidate_families(external_candidate_families)),
            "external_family_calibration_floor": float(external_family_calibration_floor),
            "external_family_min_data_support": float(external_family_min_data_support),
            "external_candidate_expert_scale": float(external_candidate_expert_scale),
            "external_candidate_llm_scale": float(external_candidate_llm_scale),
            "external_candidate_default_scale": float(external_candidate_default_scale),
            "disable_source_complexity_penalty": bool(disable_source_complexity_penalty),
            "effective_external_candidate_expert_scale": float(effective_external_expert_scale),
            "effective_external_candidate_llm_scale": float(effective_external_llm_scale),
            "effective_external_candidate_default_scale": float(effective_external_default_scale),
            "use_llm_expert_condition_verifier": bool(use_llm_expert_condition_verifier),
            "llm_condition_verifier_weight": float(llm_condition_verifier_weight),
            "llm_condition_verifier_min_data_support": float(llm_condition_verifier_min_data_support),
            "llm_condition_verifier_floor": float(llm_condition_verifier_floor),
            "llm_condition_verifier_target": str(llm_condition_verifier_target or "candidate_gate"),
            "use_llm_condition_verifier_validation_admission": bool(
                use_llm_condition_verifier_validation_admission
            ),
            "llm_condition_verifier_min_val_gain": float(llm_condition_verifier_min_val_gain),
            "use_class_conditioned_evidence": bool(use_class_conditioned_evidence),
            "effective_use_class_conditioned_evidence": bool(
                use_class_conditioned_evidence
            ) or bool(condition_verifier_class_evidence_enabled),
            "class_evidence_top_k": int(class_evidence_top_k),
            "class_evidence_mode": str(class_evidence_mode or "static"),
            "class_evidence_max_lag": int(class_evidence_max_lag),
            "class_evidence_lag_weight": float(class_evidence_lag_weight),
            "class_evidence_family_k": int(class_evidence_family_k),
            "class_evidence_family_weight": float(class_evidence_family_weight),
            "class_evidence_focus_mode": str(class_evidence_focus_mode or "none"),
            "class_evidence_focus_classes": [int(cls) for cls in _parse_optional_ints(class_evidence_focus_classes)],
            "class_evidence_focus_k": int(class_evidence_focus_k),
            "class_evidence_focus_nonfocus_weight": float(class_evidence_focus_nonfocus_weight),
            "class_evidence_gate_threshold": float(class_evidence_gate_threshold),
            "class_evidence_gate_temperature": float(class_evidence_gate_temperature),
            "class_evidence_gate_floor": float(class_evidence_gate_floor),
            "class_evidence_router_temperature": float(class_evidence_router_temperature),
            "class_evidence_router_top_k": int(class_evidence_router_top_k),
            "use_stable_path_evidence": bool(use_stable_path_evidence),
            "stable_path_evidence_splits": int(stable_path_evidence_splits),
            "stable_path_evidence_min_vote_fraction": float(stable_path_evidence_min_vote_fraction),
            "stable_path_evidence_strength": float(stable_path_evidence_strength),
            "stable_path_evidence_top_k": int(stable_path_evidence_top_k),
            "stable_path_evidence_edge_top_k": int(stable_path_evidence_edge_top_k),
            "stable_path_evidence_mode": str(stable_path_evidence_mode or "static_lag"),
            "stable_path_evidence_max_lag": int(stable_path_evidence_max_lag),
            "stable_path_evidence_lag_weight": float(stable_path_evidence_lag_weight),
            "stable_path_evidence_path_mode": str(stable_path_evidence_path_mode or "max"),
            "stable_path_evidence_class_mode": str(stable_path_evidence_class_mode or "filter"),
            "stable_path_evidence_class_floor": float(stable_path_evidence_class_floor),
            "use_class_evidence_quality_certificate": bool(use_class_evidence_quality_certificate),
            "class_evidence_quality_mode": str(class_evidence_quality_mode or "focus_stability"),
            "class_evidence_quality_floor": float(class_evidence_quality_floor),
            "class_evidence_quality_threshold": float(class_evidence_quality_threshold),
            "class_evidence_quality_temperature": float(class_evidence_quality_temperature),
            "use_path_family_quality_certificate": bool(use_path_family_quality_certificate),
            "path_family_quality_mode": str(path_family_quality_mode or "focus_path_family"),
            "path_family_quality_floor": float(path_family_quality_floor),
            "path_family_quality_threshold": float(path_family_quality_threshold),
            "path_family_quality_temperature": float(path_family_quality_temperature),
            "path_family_quality_direct_weight": float(path_family_quality_direct_weight),
            "path_family_quality_group_weight": float(path_family_quality_group_weight),
            "path_family_quality_stability_weight": float(path_family_quality_stability_weight),
            "path_family_quality_family_k": int(path_family_quality_family_k),
            "path_family_quality_family_weight": float(path_family_quality_family_weight),
            "use_path_family_protected_proposal_weights": bool(use_path_family_protected_proposal_weights),
            "candidate_protected_class_weights": (
                [float(value) for value in candidate_protected_class_weights.reshape(-1)]
                if candidate_protected_class_weights is not None
                else []
            ),
            "use_stable_class_edge_overlay": bool(use_stable_class_edge_overlay),
            "stable_class_edge_overlay_scale": float(stable_class_edge_overlay_scale),
            "stable_class_edge_overlay_top_k": int(stable_class_edge_overlay_top_k),
            "stable_class_edge_overlay_group_top_k": int(stable_class_edge_overlay_group_top_k),
            "stable_class_edge_overlay_focus_weight": float(stable_class_edge_overlay_focus_weight),
            "stable_class_edge_overlay_nonfocus_weight": float(stable_class_edge_overlay_nonfocus_weight),
            "stable_class_edge_overlay_mode": str(stable_class_edge_overlay_mode or "max"),
            "use_certified_graph_prior_core": bool(use_certified_graph_prior_core),
            "use_separate_path_candidate_prior": bool(use_separate_path_candidate_prior),
            "graph_prior_core_floor": float(graph_prior_core_floor),
            "graph_prior_core_threshold": float(graph_prior_core_threshold),
            "graph_prior_core_temperature": float(graph_prior_core_temperature),
            "graph_prior_core_top_k": int(graph_prior_core_top_k),
            "graph_prior_core_group_top_k": int(graph_prior_core_group_top_k),
            "graph_prior_core_direct_weight": float(graph_prior_core_direct_weight),
            "graph_prior_core_group_weight": float(graph_prior_core_group_weight),
            "graph_prior_core_stability_weight": float(graph_prior_core_stability_weight),
            "graph_prior_core_prior_weight": float(graph_prior_core_prior_weight),
            "graph_prior_core_focus_weight": float(graph_prior_core_focus_weight),
            "graph_prior_core_nonfocus_weight": float(graph_prior_core_nonfocus_weight),
            "use_class_conditioned_prior_admission": bool(use_class_conditioned_prior_admission),
            "class_prior_admission_floor": float(class_prior_admission_floor),
            "use_adaptive_prior_admission": bool(use_adaptive_prior_admission),
            "adaptive_prior_admission_threshold": float(adaptive_prior_admission_threshold),
            "adaptive_prior_admission_temperature": float(adaptive_prior_admission_temperature),
            "use_candidate_prior_admission": bool(use_candidate_prior_admission),
            "candidate_prior_admission_floor": float(candidate_prior_admission_floor),
            "candidate_prior_admission_threshold": float(candidate_prior_admission_threshold),
            "candidate_prior_admission_temperature": float(candidate_prior_admission_temperature),
            "candidate_prior_admission_support_mode": str(candidate_prior_admission_support_mode or "relative_evidence"),
            "candidate_prior_admission_scale": float(candidate_prior_admission_scale),
            "candidate_prior_admission_min_support": float(candidate_prior_admission_min_support),
            "candidate_prior_admission_protected_min_support": float(candidate_prior_admission_protected_min_support),
            "candidate_prior_admission_target": str(candidate_prior_admission_target or "coverage"),
            "use_edge_family_router": bool(config.use_edge_family_router),
            "edge_family_names": [str(name) for name in algorithmic_prior_diagnostics.get("edge_family_prior_names", [])],
            "edge_family_router_temperature": float(edge_family_router_temperature),
            "edge_family_router_floor": float(edge_family_router_floor),
            "edge_family_router_blend": float(edge_family_router_blend),
            "edge_family_router_balance_weight": float(edge_family_router_balance_weight),
            "use_edge_calibrator": bool(use_edge_calibrator),
            "edge_calibrator_floor": float(edge_calibrator_floor),
            "edge_calibrator_init_bias": float(edge_calibrator_init_bias),
            "edge_calibrator_reg_weight": float(edge_calibrator_reg_weight),
            "use_path_reliability_calibrator": bool(use_path_reliability_calibrator),
            "path_reliability_context_scale": float(path_reliability_context_scale),
            "path_reliability_context_reg_weight": float(path_reliability_context_reg_weight),
            "use_learned_path_admission": bool(use_learned_path_admission),
            "path_admission_strength": float(path_admission_strength),
            "path_admission_reg_weight": float(path_admission_reg_weight),
            "use_path_prior_consistency": bool(use_path_prior_consistency),
            "path_prior_consistency_strength": float(path_prior_consistency_strength),
            "path_prior_consistency_threshold": float(path_prior_consistency_threshold),
            "path_prior_consistency_temperature": float(path_prior_consistency_temperature),
            "path_prior_consistency_support_mode": str(path_prior_consistency_support_mode or "max"),
            "path_prior_consistency_class_floor": float(path_prior_consistency_class_floor),
            "use_path_evidence_consistency": bool(use_path_evidence_consistency),
            "path_evidence_consistency_strength": float(path_evidence_consistency_strength),
            "path_evidence_consistency_threshold": float(path_evidence_consistency_threshold),
            "path_evidence_consistency_temperature": float(path_evidence_consistency_temperature),
            "path_evidence_consistency_floor": float(path_evidence_consistency_floor),
            "path_evidence_consistency_support_mode": str(path_evidence_consistency_support_mode or "absolute"),
            "use_path_proposal_consistency": bool(use_path_proposal_consistency),
            "path_proposal_consistency_strength": float(path_proposal_consistency_strength),
            "path_proposal_consistency_threshold": float(path_proposal_consistency_threshold),
            "path_proposal_consistency_temperature": float(path_proposal_consistency_temperature),
            "path_proposal_consistency_floor": float(path_proposal_consistency_floor),
            "path_proposal_consistency_support_mode": str(path_proposal_consistency_support_mode or "max"),
            "path_proposal_consistency_protected_strength": float(path_proposal_consistency_protected_strength),
            "path_proposal_retention_fraction": float(path_proposal_retention_fraction),
            "protect_order_anchor_target": bool(protect_order_anchor_target),
            "protect_order_anchor_path_nodes": bool(protect_order_anchor_path_nodes),
            "protected_order_anchor": protected_order_anchor,
            "use_regime_prototype_residuals": bool(use_regime_prototype_residuals),
            "regime_prototype_k": int(regime_prototype_k),
            "regime_healthy_stage_max": int(regime_healthy_stage_max),
        },
        "regime_prototype": regime_diagnostics,
        "top_evidence_paths": name_top_paths(
            diagnostics.get("test_diagnostics", {}).get("top_path_index_pairs", []),
            model_task.feature_cols,
            limit=20,
        ),
        "diagnostics": diagnostics,
    }
    prior_tag = _safe_slug(str(evidence_prior_mode))
    if float(prior_strength) > 0.0 and prior_tag != "none":
        prior_tag = f"{prior_tag}_s{float(prior_strength):.2f}".replace(".", "p")
    if float(prior_coverage_fraction) > 0.0 and prior_tag != "none":
        prior_tag = f"{prior_tag}_cover{float(prior_coverage_fraction):.2f}".replace(".", "p")
    if bool(algorithmic_prior_diagnostics.get("enabled", False)):
        alg_tag = _safe_slug(str(algorithmic_prior_diagnostics.get("mode", algorithmic_edge_prior_mode)))
        alg_tag = f"alg-{alg_tag}_s{float(algorithmic_edge_prior_strength):.2f}".replace(".", "p")
        prior_tag = alg_tag if prior_tag == "none" else f"{prior_tag}_{alg_tag}"
    out = output_dir / f"ms_gse_rpf_{task.dataset}_{task.target}_{variant}_prior-{prior_tag}_seed{int(seed)}.json"
    _write_json(out, result)
    return result


def aggregate_runs(runs: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    by_key: dict[str, list[Mapping[str, Any]]] = {}
    for run in runs:
        key = f"{run.get('dataset')}:{run.get('target')}:{run.get('variant')}"
        by_key.setdefault(key, []).append(run)
    summary: dict[str, Any] = {}
    for key, rows in by_key.items():
        speed = [float(row["efficiency"]["test_inference_samples_per_second"]) for row in rows]
        first_family = str(rows[0].get("primary_metric_family", "classification"))
        if first_family == "rul_regression":
            rul_mae = [float((row.get("primary_test_metrics") or {}).get("rul_mae", 0.0)) for row in rows]
            rul_rmse = [float((row.get("primary_test_metrics") or {}).get("rul_rmse", 0.0)) for row in rows]
            rul_score = [float((row.get("primary_test_metrics") or {}).get("rul_score", 0.0)) for row in rows]
            aux_macro = [float((row.get("primary_test_metrics") or {}).get("aux_macro_f1", 0.0)) for row in rows]
            summary[key] = {
                "n_runs": int(len(rows)),
                "primary_metric_family": first_family,
                "rul_mae_mean": float(np.mean(rul_mae)),
                "rul_mae_std": float(np.std(rul_mae)),
                "rul_rmse_mean": float(np.mean(rul_rmse)),
                "rul_rmse_std": float(np.std(rul_rmse)),
                "rul_score_mean": float(np.mean(rul_score)),
                "rul_score_std": float(np.std(rul_score)),
                "aux_macro_f1_mean": float(np.mean(aux_macro)),
                "test_inference_samples_per_second_mean": float(np.mean(speed)),
            }
        else:
            macro = [float(row.get("primary_test_metrics", row["test_metrics"])["macro_f1"]) for row in rows]
            bal = [float(row.get("primary_test_metrics", row["test_metrics"])["balanced_accuracy"]) for row in rows]
            summary[key] = {
                "n_runs": int(len(rows)),
                "primary_metric_family": first_family,
                "macro_f1_mean": float(np.mean(macro)),
                "macro_f1_std": float(np.std(macro)),
                "balanced_accuracy_mean": float(np.mean(bal)),
                "balanced_accuracy_std": float(np.std(bal)),
                "test_inference_samples_per_second_mean": float(np.mean(speed)),
            }
    return summary


def _split_csv(text: str) -> list[str]:
    return [part.strip() for part in str(text).split(",") if part.strip()]


def _split_ints(text: str) -> list[int]:
    return [int(part.strip()) for part in str(text).split(",") if part.strip()]


def _parse_optional_ints(text: str | Sequence[int] | None) -> list[int]:
    if text is None:
        return []
    if isinstance(text, str):
        return [int(part.strip()) for part in text.split(",") if part.strip()]
    return [int(value) for value in text]


def main() -> None:
    parser = argparse.ArgumentParser(description="Train MS-GSE + RPF on the unified public benchmark ready datasets.")
    parser.add_argument("--ready-root", type=str, default=str(DEFAULT_READY_ROOT))
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--dataset", type=str, default="tep", choices=["tep", "skab", "hydraulic", "cmapss", "all"])
    parser.add_argument(
        "--variant",
        type=str,
        default="full",
        choices=[
            "full",
            "single_scale",
            "no_graph",
            "no_reliability",
            "no_path_fusion",
            "with_residual_evidence",
            "no_residual_evidence",
        ],
    )
    parser.add_argument("--seeds", type=str, default="42")
    parser.add_argument("--hydraulic-targets", type=str, default="cooler,valve,internal_pump_leakage,hydraulic_accumulator")
    parser.add_argument(
        "--cmapss-target",
        type=str,
        default="degradation_stage_id",
        choices=["degradation_stage_id", "rul"],
        help="C-MAPSS target protocol. Use rul for the original RUL regression task; stage classification remains auxiliary.",
    )
    parser.add_argument("--window-size", type=int, default=32)
    parser.add_argument("--hidden-dim", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--learning-rate", type=float, default=0.001)
    parser.add_argument("--max-rows-per-split", type=int, default=5000)
    parser.add_argument(
        "--device",
        type=str,
        default="auto",
        help="Training device: auto, cpu, cuda, or cuda:0. auto uses CUDA only when the installed PyTorch build supports it.",
    )
    parser.add_argument("--forecast-weight", type=float, default=0.05)
    parser.add_argument("--graph-weight", type=float, default=0.02)
    parser.add_argument(
        "--focal-loss-gamma",
        type=float,
        default=0.0,
        help="Use focal cross-entropy with this gamma to emphasize hard fault classes. 0 disables focal scaling.",
    )
    parser.add_argument(
        "--label-smoothing",
        type=float,
        default=0.0,
        help="Apply label smoothing to supervised classification losses. Values above 0.30 are clipped.",
    )
    parser.add_argument(
        "--use-prototype-posterior-fusion",
        action="store_true",
        help="Fuse network posterior with train-only temporal class-prototype posterior using validation-selected strength.",
    )
    parser.add_argument("--prototype-fusion-max-blend", type=float, default=0.50)
    parser.add_argument("--prototype-fusion-blend-steps", type=int, default=11)
    parser.add_argument(
        "--prototype-fusion-temperature-grid",
        type=str,
        default="0.25,0.50,1.00,2.00,4.00",
    )
    parser.add_argument(
        "--prototype-fusion-min-val-gain",
        type=float,
        default=0.0,
        help="Require this validation Macro-F1 gain before accepting nonzero prototype posterior fusion.",
    )
    parser.add_argument(
        "--use-one-class-posterior-fusion",
        action="store_true",
        help="For binary anomaly tasks, fuse the network posterior with a train-only normality-distance posterior.",
    )
    parser.add_argument("--one-class-fusion-max-blend", type=float, default=0.35)
    parser.add_argument("--one-class-fusion-blend-steps", type=int, default=8)
    parser.add_argument("--one-class-fusion-temperature-grid", type=str, default="0.25,0.50,1.00,2.00")
    parser.add_argument("--one-class-fusion-threshold-grid", type=str, default="-0.50,0.00,0.50,1.00,1.50,2.00,3.00")
    parser.add_argument(
        "--one-class-fusion-min-val-gain",
        type=float,
        default=0.0,
        help="Require this validation Macro-F1 gain before accepting one-class posterior fusion.",
    )
    parser.add_argument(
        "--use-ordinal-posterior-calibration",
        action="store_true",
        help="For ordered multiclass tasks, tune expected-stage thresholds on validation and fuse the ordinal posterior.",
    )
    parser.add_argument("--ordinal-posterior-max-blend", type=float, default=0.50)
    parser.add_argument("--ordinal-posterior-blend-steps", type=int, default=11)
    parser.add_argument("--ordinal-posterior-smoothing", type=float, default=0.03)
    parser.add_argument(
        "--ordinal-posterior-min-val-gain",
        type=float,
        default=0.0,
        help="Require this validation Macro-F1 gain before accepting ordinal posterior calibration.",
    )
    parser.add_argument(
        "--ordinal-loss-weight",
        type=float,
        default=0.0,
        help="Add cumulative ordinal EMD loss for ordered stage labels. Use as an explicit degradation-task ablation.",
    )
    parser.add_argument(
        "--ordinal-boundary-loss-weight",
        type=float,
        default=0.0,
        help="Add cumulative boundary BCE loss for ordered multiclass degradation stages.",
    )
    parser.add_argument(
        "--ordinal-boundary-focal-gamma",
        type=float,
        default=0.0,
        help="Focal gamma applied to ordinal boundary BCE.",
    )
    parser.add_argument(
        "--ordinal-boundary-focus",
        type=float,
        default=0.0,
        help="Extra weight for decision boundaries near the true ordered class.",
    )
    parser.add_argument(
        "--path-entropy-weight",
        type=float,
        default=0.0,
        help="Penalize high RPF path-weight entropy to encourage sparse auditable path fusion.",
    )
    parser.add_argument(
        "--path-aux-weight",
        type=float,
        default=0.0,
        help="Add an auxiliary classification loss on the fused RPF path context so selected paths must be task-predictive.",
    )
    parser.add_argument(
        "--coarse-aux-weight",
        type=float,
        default=0.0,
        help="Add a coarse class-0 versus nonzero-state auxiliary loss on the fused node+path context.",
    )
    parser.add_argument(
        "--evidence-router-aux-weight",
        type=float,
        default=0.0,
        help="Supervise the class-conditioned evidence router with the task label.",
    )
    parser.add_argument(
        "--use-class-conditioned-evidence",
        action="store_true",
        help="Use train-only class-conditioned path evidence prototypes and route them per sample before RPF.",
    )
    parser.add_argument(
        "--class-evidence-top-k",
        type=int,
        default=0,
        help="Keep only the top-k features per class when building train-only class-conditioned path evidence. 0 keeps all.",
    )
    parser.add_argument(
        "--class-evidence-mode",
        type=str,
        default="static",
        choices=["static", "lag", "static_lag"],
        help="Class-conditioned path evidence type. static keeps the previous feature-pair prototypes; lag adds directed train-only temporal support.",
    )
    parser.add_argument(
        "--class-evidence-max-lag",
        type=int,
        default=0,
        help="Maximum lag used by --class-evidence-mode lag/static_lag. 0 disables lag support.",
    )
    parser.add_argument(
        "--class-evidence-lag-weight",
        type=float,
        default=0.50,
        help="Mixture weight for lagged support when --class-evidence-mode static_lag.",
    )
    parser.add_argument(
        "--class-evidence-family-k",
        type=int,
        default=0,
        help="Blend each class path prototype with this many train-only nearest fault-family prototypes. 0 disables family smoothing.",
    )
    parser.add_argument(
        "--class-evidence-family-weight",
        type=float,
        default=0.0,
        help="Blend weight for train-only fault-family path prototypes.",
    )
    parser.add_argument(
        "--class-evidence-focus-mode",
        type=str,
        default="none",
        choices=["none", "explicit", "low_train_separation"],
        help="Restrict class-conditioned evidence to explicit or train-only low-separation classes.",
    )
    parser.add_argument(
        "--class-evidence-focus-classes",
        type=str,
        default="",
        help="Comma-separated class ids that keep full class evidence when focus mode is explicit or as anchors for low_train_separation.",
    )
    parser.add_argument(
        "--class-evidence-focus-k",
        type=int,
        default=0,
        help="Number of low train-separation classes to focus when --class-evidence-focus-mode low_train_separation. 0 uses 25%% of valid classes.",
    )
    parser.add_argument(
        "--class-evidence-focus-nonfocus-weight",
        type=float,
        default=0.0,
        help="Residual weight kept for non-focused class evidence. 0 removes non-focused evidence.",
    )
    parser.add_argument(
        "--class-evidence-gate-threshold",
        type=float,
        default=0.0,
        help="Sample-level router confidence threshold for admitting class-conditioned path evidence. 0 disables attenuation.",
    )
    parser.add_argument(
        "--class-evidence-gate-temperature",
        type=float,
        default=0.05,
        help="Temperature for the sample-level class-evidence admission gate.",
    )
    parser.add_argument(
        "--class-evidence-gate-floor",
        type=float,
        default=0.0,
        help="Minimum retained fraction for class-conditioned evidence after sample-level gating.",
    )
    parser.add_argument(
        "--class-evidence-router-temperature",
        type=float,
        default=1.0,
        help="Softmax temperature for routing class-conditioned evidence. Lower values sharpen fault-mechanism selection.",
    )
    parser.add_argument(
        "--class-evidence-router-top-k",
        type=int,
        default=0,
        help="Keep only the top-k routed class-evidence prototypes per sample. 0 keeps all classes.",
    )
    parser.add_argument(
        "--use-stable-path-evidence",
        action="store_true",
        help="Build train-only cross-split stable path evidence and use it as RPF path admission evidence.",
    )
    parser.add_argument(
        "--stable-path-evidence-splits",
        type=int,
        default=4,
        help="Number of stratified train-subset folds used to test path-evidence stability.",
    )
    parser.add_argument(
        "--stable-path-evidence-min-vote-fraction",
        type=float,
        default=0.50,
        help="Minimum fraction of train-subset reconstructions that must recover an edge before it is admitted.",
    )
    parser.add_argument(
        "--stable-path-evidence-strength",
        type=float,
        default=0.50,
        help="Scale applied to admitted stable path evidence before it is merged into RPF evidence channels.",
    )
    parser.add_argument(
        "--stable-path-evidence-top-k",
        type=int,
        default=0,
        help="Keep only the top-k features per class inside each stability split. 0 keeps all.",
    )
    parser.add_argument(
        "--stable-path-evidence-edge-top-k",
        type=int,
        default=4,
        help="Endpoint cap applied after stable path evidence is reconstructed. 0 keeps all stable edges.",
    )
    parser.add_argument(
        "--stable-path-evidence-mode",
        type=str,
        default="static_lag",
        choices=["static", "lag", "static_lag"],
        help="Evidence family used inside each stability split.",
    )
    parser.add_argument("--stable-path-evidence-max-lag", type=int, default=3)
    parser.add_argument("--stable-path-evidence-lag-weight", type=float, default=0.50)
    parser.add_argument(
        "--stable-path-evidence-path-mode",
        type=str,
        default="max",
        choices=["off", "max", "replace"],
        help="How stable path evidence modifies the global RPF path-evidence matrix. off computes stability diagnostics only.",
    )
    parser.add_argument(
        "--stable-path-evidence-class-mode",
        type=str,
        default="filter",
        choices=["off", "max", "filter", "replace"],
        help="How stable evidence modifies class-conditioned path evidence when that module is enabled.",
    )
    parser.add_argument(
        "--stable-path-evidence-class-floor",
        type=float,
        default=0.25,
        help="For class-mode=filter, minimum retained fraction for class evidence that is not stable across train splits.",
    )
    parser.add_argument(
        "--use-class-evidence-quality-certificate",
        action="store_true",
        help="Filter class-conditioned path evidence by train-only cross-split stability before it can affect RPF.",
    )
    parser.add_argument(
        "--class-evidence-quality-mode",
        type=str,
        default="focus_stability",
        choices=["focus_stability", "all_stability"],
        help="Apply the certificate only to focused low-tail classes or to all class evidence.",
    )
    parser.add_argument("--class-evidence-quality-floor", type=float, default=0.15)
    parser.add_argument("--class-evidence-quality-threshold", type=float, default=0.75)
    parser.add_argument("--class-evidence-quality-temperature", type=float, default=0.05)
    parser.add_argument(
        "--use-path-family-quality-certificate",
        action="store_true",
        help="Filter class-conditioned path evidence by algorithmic/expert path-family support before RPF use.",
    )
    parser.add_argument(
        "--path-family-quality-mode",
        type=str,
        default="focus_path_family",
        choices=["focus_path_family", "all_path_family", "focus_fault_family", "all_fault_family"],
        help="Apply the path-family certificate only to focused low-tail classes or to all class evidence.",
    )
    parser.add_argument("--path-family-quality-floor", type=float, default=0.15)
    parser.add_argument("--path-family-quality-threshold", type=float, default=0.25)
    parser.add_argument("--path-family-quality-temperature", type=float, default=0.05)
    parser.add_argument("--path-family-quality-direct-weight", type=float, default=1.0)
    parser.add_argument("--path-family-quality-group-weight", type=float, default=0.50)
    parser.add_argument("--path-family-quality-stability-weight", type=float, default=0.0)
    parser.add_argument(
        "--path-family-quality-family-k",
        type=int,
        default=0,
        help="For fault-family certificate modes, use this many nearest class path prototypes as family support.",
    )
    parser.add_argument(
        "--path-family-quality-family-weight",
        type=float,
        default=0.0,
        help="Support weight from nearest fault-family path prototypes inside path-family quality certification.",
    )
    parser.add_argument(
        "--use-path-family-protected-proposal-weights",
        action="store_true",
        help=(
            "Use path-family certificate risk as continuous class weights for candidate-edge support floors "
            "and protected path-proposal consistency instead of a binary focus-class mask."
        ),
    )
    parser.add_argument(
        "--use-stable-class-edge-overlay",
        action="store_true",
        help="Overlay cross-split stable class path evidence onto the initialized edge prior before RPF path admission.",
    )
    parser.add_argument("--stable-class-edge-overlay-scale", type=float, default=0.25)
    parser.add_argument("--stable-class-edge-overlay-top-k", type=int, default=8)
    parser.add_argument("--stable-class-edge-overlay-group-top-k", type=int, default=2)
    parser.add_argument("--stable-class-edge-overlay-focus-weight", type=float, default=1.25)
    parser.add_argument("--stable-class-edge-overlay-nonfocus-weight", type=float, default=0.50)
    parser.add_argument(
        "--stable-class-edge-overlay-mode",
        type=str,
        default="max",
        choices=["max", "add"],
        help="How stable class overlay edges combine with the initialized prior.",
    )
    parser.add_argument(
        "--use-certified-graph-prior-core",
        action="store_true",
        help="Compress broad initialized edge priors into a certified graph-core prior using class/path evidence before graph bias.",
    )
    parser.add_argument(
        "--use-separate-path-candidate-prior",
        action="store_true",
        help="Keep the broad initialized edge prior as the RPF candidate pool while graph bias uses the certified core.",
    )
    parser.add_argument(
        "--use-candidate-prior-admission",
        action="store_true",
        help="Treat the broad path-candidate prior as an evidence-gated overlay instead of replacing the RPF base prior.",
    )
    parser.add_argument(
        "--candidate-prior-admission-floor",
        type=float,
        default=0.05,
        help="Minimum retained candidate-prior fraction when evidence support is weak.",
    )
    parser.add_argument(
        "--candidate-prior-admission-threshold",
        type=float,
        default=0.50,
        help="Evidence-support threshold for admitting candidate-prior edges into RPF.",
    )
    parser.add_argument(
        "--candidate-prior-admission-temperature",
        type=float,
        default=0.05,
        help="Temperature of the evidence-to-admission gate for candidate-prior overlay edges.",
    )
    parser.add_argument(
        "--candidate-prior-admission-support-mode",
        type=str,
        default="relative_evidence",
        choices=["absolute", "relative", "relative_evidence"],
        help="Use raw evidence support or per-sample relative evidence before gating candidate-prior edges.",
    )
    parser.add_argument(
        "--candidate-prior-admission-scale",
        type=float,
        default=0.50,
        help="Maximum candidate-prior overlay strength after admission gating.",
    )
    parser.add_argument(
        "--candidate-prior-admission-min-support",
        type=float,
        default=0.0,
        help="Hard evidence support floor for admitted candidate edges. 0 keeps soft-only gating.",
    )
    parser.add_argument(
        "--candidate-prior-admission-protected-min-support",
        type=float,
        default=0.0,
        help="Higher candidate evidence support floor interpolated by routed mass on focus/low-tail classes.",
    )
    parser.add_argument(
        "--candidate-prior-admission-target",
        type=str,
        default="coverage",
        choices=["coverage", "feature", "coverage_feature", "proposal", "proposal_feature"],
        help=(
            "Where admitted candidate-prior edges enter RPF: coverage can reserve path slots, "
            "feature only changes selected-path prior features, proposal uses a separate candidate path quota, "
            "and *_feature modes also expose candidate prior as a path feature."
        ),
    )
    parser.add_argument("--graph-prior-core-floor", type=float, default=0.05)
    parser.add_argument("--graph-prior-core-threshold", type=float, default=0.35)
    parser.add_argument("--graph-prior-core-temperature", type=float, default=0.05)
    parser.add_argument("--graph-prior-core-top-k", type=int, default=8)
    parser.add_argument("--graph-prior-core-group-top-k", type=int, default=3)
    parser.add_argument("--graph-prior-core-direct-weight", type=float, default=1.0)
    parser.add_argument("--graph-prior-core-group-weight", type=float, default=0.40)
    parser.add_argument("--graph-prior-core-stability-weight", type=float, default=0.50)
    parser.add_argument("--graph-prior-core-prior-weight", type=float, default=0.20)
    parser.add_argument("--graph-prior-core-focus-weight", type=float, default=1.25)
    parser.add_argument("--graph-prior-core-nonfocus-weight", type=float, default=0.50)
    parser.add_argument(
        "--use-class-conditioned-prior-admission",
        action="store_true",
        help="Use routed class path evidence to admit a sample-wise subset of prior edges for RPF path coverage.",
    )
    parser.add_argument(
        "--class-prior-admission-floor",
        type=float,
        default=0.10,
        help="Minimum retained prior fraction for class-conditioned RPF prior admission.",
    )
    parser.add_argument(
        "--use-adaptive-prior-admission",
        action="store_true",
        help="Blend class-filtered and broad RPF priors by the sample-level class-router confidence.",
    )
    parser.add_argument(
        "--adaptive-prior-admission-threshold",
        type=float,
        default=0.20,
        help="Class-router confidence threshold above which class-conditioned prior filtering is trusted.",
    )
    parser.add_argument(
        "--adaptive-prior-admission-temperature",
        type=float,
        default=0.05,
        help="Temperature of the confidence-to-trust gate for --use-adaptive-prior-admission.",
    )
    parser.add_argument(
        "--use-edge-family-router",
        action="store_true",
        help="Route structural/dynamic/task algorithmic edge-family priors per sample before RPF prior admission.",
    )
    parser.add_argument("--edge-family-router-temperature", type=float, default=1.0)
    parser.add_argument("--edge-family-router-floor", type=float, default=0.05)
    parser.add_argument("--edge-family-router-blend", type=float, default=1.0)
    parser.add_argument(
        "--edge-family-router-balance-weight",
        type=float,
        default=0.0,
        help="KL-to-uniform regularization weight for edge-family routing burden balance.",
    )
    parser.add_argument(
        "--use-edge-calibrator",
        action="store_true",
        help="Learn a sample-wise gate over candidate prior edges before graph/RPF use them.",
    )
    parser.add_argument(
        "--edge-calibrator-floor",
        type=float,
        default=0.05,
        help="Minimum retained fraction for an admitted candidate edge in the learnable edge calibrator.",
    )
    parser.add_argument(
        "--edge-calibrator-init-bias",
        type=float,
        default=2.0,
        help="Initial logit bias for the edge calibrator gate. Larger values start closer to the raw prior.",
    )
    parser.add_argument(
        "--edge-calibrator-reg-weight",
        type=float,
        default=0.0,
        help="Penalize the learnable edge calibrator for deviating from the raw candidate prior.",
    )
    parser.add_argument(
        "--classification-loss-weight",
        type=float,
        default=1.0,
        help="Weight of the internal classification loss. RUL-first branches can lower this to keep labels auxiliary.",
    )
    parser.add_argument(
        "--health-aux-weight",
        type=float,
        default=0.0,
        help="Add an auxiliary health-index regression loss derived from capped RUL when the dataset provides a rul column.",
    )
    parser.add_argument(
        "--rul-loss-weight",
        type=float,
        default=0.0,
        help="Add a direct capped-RUL regression loss and use validation RMSE for model selection on C-MAPSS RUL.",
    )
    parser.add_argument(
        "--health-rul-cap",
        type=float,
        default=125.0,
        help="RUL cap used to construct health index = 1 - min(rul, cap) / cap for --health-aux-weight.",
    )
    parser.add_argument(
        "--use-regime-prototype-residuals",
        action="store_true",
        help="For operating-regime datasets, subtract train-only healthy regime prototypes from sensor channels before RPF.",
    )
    parser.add_argument(
        "--regime-prototype-k",
        type=int,
        default=6,
        help="Number of operating-regime prototypes used by --use-regime-prototype-residuals.",
    )
    parser.add_argument(
        "--regime-healthy-stage-max",
        type=int,
        default=0,
        help="Largest internal class id treated as healthy when estimating regime prototypes.",
    )
    parser.add_argument(
        "--use-multihop-paths",
        action="store_true",
        help="Allocate part of the RPF budget to compressed source-bridge-target two-hop evidence paths.",
    )
    parser.add_argument(
        "--multihop-path-fraction",
        type=float,
        default=0.25,
        help="Fraction of max_paths reserved for two-hop candidates when --use-multihop-paths is enabled.",
    )
    parser.add_argument(
        "--disable-context-router",
        action="store_true",
        help="Disable sample-context-conditioned RPF routing for ablation against local path-token routing.",
    )
    parser.add_argument(
        "--use-path-reliability-calibrator",
        action="store_true",
        help="Add a zero-initialized sample-context residual to RPF path reliability logits.",
    )
    parser.add_argument(
        "--path-reliability-context-reg-weight",
        type=float,
        default=0.0,
        help="L2 penalty on the sample-context residual used by --use-path-reliability-calibrator.",
    )
    parser.add_argument(
        "--path-reliability-context-scale",
        type=float,
        default=1.0,
        help="Tanh-bounded maximum absolute residual added to RPF path reliability logits.",
    )
    parser.add_argument(
        "--use-learned-path-admission",
        action="store_true",
        help="Add a zero-initialized learned admission residual to RPF path-fusion logits using path, prior, class/stability evidence, and sample context.",
    )
    parser.add_argument(
        "--path-admission-strength",
        type=float,
        default=1.0,
        help="Maximum tanh-bounded logit adjustment contributed by --use-learned-path-admission.",
    )
    parser.add_argument(
        "--path-admission-reg-weight",
        type=float,
        default=0.0,
        help="L2 penalty on learned path-admission adjustments.",
    )
    parser.add_argument(
        "--use-path-prior-consistency",
        action="store_true",
        help="Add a deterministic RPF logit adjustment for prior paths according to dynamic/salience support.",
    )
    parser.add_argument(
        "--path-prior-consistency-strength",
        type=float,
        default=0.0,
        help="Maximum prior-weighted logit adjustment from --use-path-prior-consistency.",
    )
    parser.add_argument("--path-prior-consistency-threshold", type=float, default=0.25)
    parser.add_argument("--path-prior-consistency-temperature", type=float, default=0.05)
    parser.add_argument(
        "--path-prior-consistency-support-mode",
        type=str,
        default="max",
        choices=["max", "dynamic", "agreement", "class_blend"],
        help=(
            "Support used by path-prior consistency: dynamic graph only, max(dynamic,class evidence), "
            "agreement=min(dynamic,class evidence), or class_blend=dynamic*(floor+(1-floor)*class evidence)."
        ),
    )
    parser.add_argument(
        "--path-prior-consistency-class-floor",
        type=float,
        default=0.25,
        help="For class_blend support mode, retain this fraction of dynamic support when class evidence is weak.",
    )
    parser.add_argument(
        "--use-path-evidence-consistency",
        action="store_true",
        help="Add a deterministic RPF logit adjustment from routed path/class evidence, independent of prior coverage.",
    )
    parser.add_argument(
        "--path-evidence-consistency-strength",
        type=float,
        default=0.0,
        help="Maximum path-evidence-scaled logit adjustment from --use-path-evidence-consistency.",
    )
    parser.add_argument("--path-evidence-consistency-threshold", type=float, default=0.35)
    parser.add_argument("--path-evidence-consistency-temperature", type=float, default=0.05)
    parser.add_argument(
        "--path-evidence-consistency-floor",
        type=float,
        default=0.0,
        help="Minimum adjustment scale for selected paths when evidence consistency is enabled. 0 keeps unsupported paths neutral.",
    )
    parser.add_argument(
        "--path-evidence-consistency-support-mode",
        type=str,
        default="absolute",
        choices=["absolute", "relative"],
        help="Use raw path evidence support or normalize selected-path support by the per-sample maximum before gating.",
    )
    parser.add_argument(
        "--use-path-proposal-consistency",
        action="store_true",
        help="Downweight RPF path proposals whose dynamic edge score is not supported by prior or class/salience evidence.",
    )
    parser.add_argument(
        "--path-proposal-consistency-strength",
        type=float,
        default=0.0,
        help="How strongly proposal consistency gates candidate path-selection scores. 0 keeps default proposal ranking.",
    )
    parser.add_argument("--path-proposal-consistency-threshold", type=float, default=0.35)
    parser.add_argument("--path-proposal-consistency-temperature", type=float, default=0.05)
    parser.add_argument("--path-proposal-consistency-floor", type=float, default=0.10)
    parser.add_argument(
        "--path-proposal-consistency-support-mode",
        type=str,
        default="max",
        choices=["max", "salience", "prior", "relative_evidence", "evidence_admit", "agreement", "class_blend"],
        help="Evidence used to gate path proposals before RPF selection.",
    )
    parser.add_argument(
        "--path-proposal-consistency-protected-strength",
        type=float,
        default=0.0,
        help="Interpolate proposal-consistency strength toward this value for routed low-tail/focus-class samples.",
    )
    parser.add_argument(
        "--path-proposal-retention-fraction",
        type=float,
        default=0.0,
        help="When proposal consistency is enabled, retain this fraction of global proposal slots from the ungated dynamic ranking.",
    )
    parser.add_argument(
        "--protect-order-anchor-target",
        action="store_true",
        help="For ordered lifecycle tasks, prevent the order coordinate, such as C-MAPSS cycle, from being selected as an RPF target node.",
    )
    parser.add_argument(
        "--protect-order-anchor-path-nodes",
        action="store_true",
        help="For ordered lifecycle tasks, prevent the order coordinate from appearing as source, target, or bridge in selected RPF evidence paths.",
    )
    parser.add_argument("--graph-top-k", type=int, default=8)
    parser.add_argument("--max-paths", type=int, default=32)
    parser.add_argument(
        "--auto-path-budget",
        action="store_true",
        help="Raise max_paths to a small feature-group-aware budget. Off by default for protocol stability.",
    )
    parser.add_argument(
        "--path-coverage-mode",
        type=str,
        default="target_group",
        choices=["target_group", "group_pair", "group_pair_inclusive"],
        help="Coverage selector used by RPF. group_pair variants are explicit ablations, not the default.",
    )
    parser.add_argument(
        "--coverage-dedup-mode",
        type=str,
        default="soft",
        choices=["none", "soft", "hard"],
        help="How coverage paths handle globally selected edges. soft penalizes redundancy; hard is an ablation.",
    )
    parser.add_argument(
        "--coverage-redundancy-penalty",
        type=float,
        default=0.05,
        help="Penalty subtracted from globally selected edges when --coverage-dedup-mode soft.",
    )
    parser.add_argument(
        "--deduplicate-exact-paths",
        action="store_true",
        help="Replace exact duplicate direct RPF path candidates while still allowing soft redundancy among related paths.",
    )
    parser.add_argument(
        "--use-task-salience",
        action="store_true",
        help="Use train-only algorithmic path evidence as a soft RPF path feature.",
    )
    parser.add_argument(
        "--salience-mode",
        type=str,
        default="class",
        choices=["class", "lifecycle", "class_lifecycle", "auto"],
        help="Algorithmic evidence source. auto uses lifecycle evidence for ordered degradation tasks only.",
    )
    parser.add_argument(
        "--lifecycle-salience-weight",
        type=float,
        default=0.50,
        help="Weight of lifecycle trend salience when --salience-mode class_lifecycle or auto enables it.",
    )
    parser.add_argument(
        "--order-anchor-evidence-weight",
        type=float,
        default=0.35,
        help="Caps the lifecycle order coordinate as a path-evidence anchor so ordered tasks do not route every path through it.",
    )
    parser.add_argument(
        "--algorithmic-evidence-top-k",
        type=int,
        default=0,
        help="Keep only the top-k train-only salience variables in the algorithmic path-evidence matrix. 0 keeps all.",
    )
    parser.add_argument(
        "--salience-selection-strength",
        type=float,
        default=0.0,
        help="Optional soft path-proposal strength for algorithmic evidence. 0 keeps evidence as a path feature only.",
    )
    parser.add_argument(
        "--salience-coverage-fraction",
        type=float,
        default=0.0,
        help="Reserve this fraction of direct RPF proposals for sample-level train-only salience/class-evidence paths.",
    )
    parser.add_argument("--evidence-prior-mode", type=str, default="none", choices=["none", "expert", "llm", "expert_llm", "all"])
    parser.add_argument("--prior-strength", type=float, default=0.0)
    parser.add_argument("--prior-min-reliability", type=float, default=0.0)
    parser.add_argument(
        "--algorithmic-edge-prior-mode",
        type=str,
        default="none",
        choices=[
            "none",
            "correlation",
            "lag",
            "class",
            "hybrid",
            "multiview",
            "edge_bank",
            "bank",
            "edge_pool",
            "edge_canvas",
            "edge_universe",
            "edge_sieve",
            "edge_overlay",
            "edge_lattice",
            "edge_dual_lattice",
            "edge_guarded_lattice",
            "edge_cert_pool",
            "edge_cert_overlay",
            "certified_edge_pool",
        ],
        help="Initialize a train-only global edge prior. edge_cert_overlay preserves edge_pool anchors and overlays a small mechanism-certified edge budget.",
    )
    parser.add_argument(
        "--algorithmic-edge-prior-top-k",
        type=int,
        default=0,
        help="Greedily keep at most top-k algorithmic prior edges per target and per source. 0 keeps all nonzero edges.",
    )
    parser.add_argument(
        "--algorithmic-edge-prior-group-top-k",
        type=int,
        default=0,
        help="Optional group-level cap for algorithmic prior edges. 0 disables group cap; positive values limit distinct source/target groups per group.",
    )
    parser.add_argument(
        "--algorithmic-edge-prior-max-lag",
        type=int,
        default=3,
        help="Maximum lag for directed train-only algorithmic edge prior support.",
    )
    parser.add_argument(
        "--algorithmic-edge-prior-strength",
        type=float,
        default=0.0,
        help="Minimum graph-prior strength used when algorithmic edge prior is enabled.",
    )
    parser.add_argument("--algorithmic-edge-prior-class-weight", type=float, default=0.25)
    parser.add_argument("--algorithmic-edge-prior-lag-weight", type=float, default=0.45)
    parser.add_argument("--algorithmic-edge-prior-corr-weight", type=float, default=0.30)
    parser.add_argument("--algorithmic-edge-prior-residual-weight", type=float, default=0.30)
    parser.add_argument("--algorithmic-edge-prior-response-weight", type=float, default=0.25)
    parser.add_argument("--algorithmic-edge-prior-stability-weight", type=float, default=0.20)
    parser.add_argument(
        "--algorithmic-edge-prior-bank-min-votes",
        type=int,
        default=2,
        help="For edge_bank mode, require this many evidence sources before an edge is fully admitted.",
    )
    parser.add_argument(
        "--algorithmic-edge-prior-bank-single-view-scale",
        type=float,
        default=0.55,
        help="For edge_bank mode, keep one-source dynamic edges at this strength; 0 drops them.",
    )
    parser.add_argument(
        "--algorithmic-edge-prior-bank-vote-boost",
        type=float,
        default=0.15,
        help="For edge_bank mode, boost edges with more evidence-source votes by this factor per extra vote.",
    )
    parser.add_argument(
        "--algorithmic-edge-prior-bank-global-budget-multiplier",
        type=float,
        default=0.0,
        help="For edge_bank mode, keep at most round(multiplier * n_features) final prior edges. 0 disables this cap.",
    )
    parser.add_argument(
        "--algorithmic-edge-prior-pool-multiplier",
        type=float,
        default=2.0,
        help="For edge_pool mode, expand each evidence source's preselection top-k by this multiplier before final caps.",
    )
    parser.add_argument(
        "--algorithmic-edge-prior-pool-min-score",
        type=float,
        default=0.0,
        help="For edge_pool mode, drop per-source candidate edges below this normalized component score.",
    )
    parser.add_argument(
        "--algorithmic-edge-prior-pool-rank-weight",
        type=float,
        default=0.35,
        help="For edge_pool mode, mix rank consistency with raw component strength when scoring candidate edges.",
    )
    parser.add_argument(
        "--algorithmic-edge-prior-candidate-only",
        action="store_true",
        help="Keep train-only algorithmic edges as path candidates instead of merging them into the main graph prior.",
    )
    parser.add_argument(
        "--prior-algorithmic-combine-mode",
        type=str,
        default="max",
        choices=["max", "corroborated_max", "anchored_subgraph", "tri_source_calibrated"],
        help="How expert/LLM priors combine with train-only algorithmic edge priors. tri_source_calibrated treats expert/LLM edges as data-calibrated candidate families.",
    )
    parser.add_argument(
        "--prior-external-isolated-scale",
        type=float,
        default=1.0,
        help="When --prior-algorithmic-combine-mode corroborated_max, multiply external-only expert/LLM edges by this factor.",
    )
    parser.add_argument(
        "--prior-overlap-boost",
        type=float,
        default=0.0,
        help="When --prior-algorithmic-combine-mode is corroborated, add this fraction of min(external, algorithmic) to overlapping edges.",
    )
    parser.add_argument(
        "--prior-nonanchor-algorithmic-scale",
        type=float,
        default=1.0,
        help="When --prior-algorithmic-combine-mode anchored_subgraph, multiply algorithmic edges away from external prior endpoints by this factor.",
    )
    parser.add_argument(
        "--prior-coverage-fraction",
        type=float,
        default=0.0,
        help="Reserve this fraction of direct RPF path proposals for expert/LLM prior edges; final weights still use dynamic evidence and reliability.",
    )
    parser.add_argument(
        "--candidate-coverage-fraction",
        type=float,
        default=0.0,
        help="Reserve a separate small fraction of direct RPF path proposals for admitted exploratory candidate edges.",
    )
    parser.add_argument(
        "--calibrate-prior-edges",
        action="store_true",
        help="Reweight expert/LLM prior edges by train-only lagged temporal support before they enter RPF.",
    )
    parser.add_argument("--prior-calibration-max-lag", type=int, default=3)
    parser.add_argument("--prior-calibration-min-support", type=float, default=0.0)
    parser.add_argument("--prior-calibration-strength", type=float, default=1.0)
    parser.add_argument(
        "--external-edge-candidate-only",
        action="store_true",
        help=(
            "Keep expert/LLM edges out of the graph prior and inject them only as data-calibrated "
            "RPF path candidates."
        ),
    )
    parser.add_argument(
        "--external-candidate-families",
        type=str,
        default="expert,llm",
        help="Comma-separated external families moved to the candidate pool when --external-edge-candidate-only is enabled.",
    )
    parser.add_argument(
        "--external-family-calibration-floor",
        type=float,
        default=0.15,
        help="Minimum retained gate for expert/LLM family edges during data-support calibration.",
    )
    parser.add_argument(
        "--external-family-min-data-support",
        type=float,
        default=0.0,
        help="Drop expert/LLM candidate edges below this data-support score after family calibration.",
    )
    parser.add_argument(
        "--external-candidate-expert-scale",
        type=float,
        default=1.0,
        help="Path-candidate strength multiplier for calibrated expert edges.",
    )
    parser.add_argument(
        "--external-candidate-llm-scale",
        type=float,
        default=0.70,
        help="Path-candidate strength multiplier for calibrated LLM edges.",
    )
    parser.add_argument(
        "--external-candidate-default-scale",
        type=float,
        default=0.85,
        help="Path-candidate strength multiplier for other external edge families.",
    )
    parser.add_argument(
        "--disable-source-complexity-penalty",
        action="store_true",
        help=(
            "Ablation switch: remove source-family candidate scaling by setting all external candidate family "
            "scales to 1.0 while preserving data-support calibration and candidate admission thresholds."
        ),
    )
    parser.add_argument(
        "--use-llm-expert-condition-verifier",
        action="store_true",
        help=(
            "Use metadata-only LLM verification of existing expert edges as a data-admitted class/path evidence gate. "
            "This does not add LLM edges to the graph."
        ),
    )
    parser.add_argument(
        "--llm-condition-verifier-weight",
        type=float,
        default=0.50,
        help="Strength of admitted LLM expert-edge condition gates when fused into class path evidence.",
    )
    parser.add_argument(
        "--llm-condition-verifier-min-data-support",
        type=float,
        default=0.05,
        help="Minimum train-only data/algorithmic edge support required before an LLM condition gate can activate.",
    )
    parser.add_argument(
        "--llm-condition-verifier-floor",
        type=float,
        default=0.10,
        help="Small support floor applied after data-support admission for verified expert-edge gates.",
    )
    parser.add_argument(
        "--llm-condition-verifier-target",
        type=str,
        default="candidate_gate",
        choices=["candidate_gate", "class_evidence", "both"],
        help=(
            "Where to apply LLM expert-condition verifier evidence. The main branch uses candidate_gate so LLM "
            "conditions only recalibrate data-supported algorithmic candidate edges; class_evidence is kept for ablation."
        ),
    )
    parser.add_argument(
        "--use-llm-condition-verifier-validation-admission",
        action="store_true",
        help=(
            "After training, compare LLM-verifier candidate overlay against the baseline candidate prior on validation "
            "and deploy the overlay only when the validation Macro-F1 gain passes the configured floor."
        ),
    )
    parser.add_argument(
        "--llm-condition-verifier-min-val-gain",
        type=float,
        default=0.0,
        help="Minimum validation Macro-F1 gain required before deploying the LLM verifier candidate overlay.",
    )
    parser.add_argument(
        "--prior-group-expansion",
        action="store_true",
        help="Expand exact expert/LLM feature priors to same sensor-group statistic variants as a weak prior feature.",
    )
    parser.add_argument("--prior-group-expansion-strength", type=float, default=0.5)
    parser.add_argument("--dropout", type=float, default=0.10)
    parser.add_argument(
        "--use-temporal-descriptors",
        action="store_true",
        help="Enable explicit last/mean/std/delta/slope temporal descriptor evidence as an ablation module.",
    )
    parser.add_argument(
        "--disable-temporal-descriptors",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument("--temporal-descriptor-weight", type=float, default=0.50)
    parser.add_argument(
        "--temporal-encoder-mode",
        type=str,
        default="multi_scale_causal",
        choices=[
            "single_scale_causal",
            "multi_scale_causal",
            "single_scale_bidirectional",
            "multi_scale_bidirectional",
        ],
        help=(
            "Temporal tokenizer mode before graph construction. Use multi_scale_causal as the main directed-lag "
            "model; bidirectional modes are ablations within the historical input window."
        ),
    )
    parser.add_argument(
        "--use-temporal-mixer",
        action="store_true",
        help="Add a global dilated temporal convolution mixer as a strong supervised backbone branch.",
    )
    parser.add_argument(
        "--temporal-mixer-type",
        type=str,
        default="conv",
        choices=["conv", "gru", "bigru"],
        help="Global temporal mixer branch used when --use-temporal-mixer is enabled.",
    )
    parser.add_argument(
        "--temporal-mixer-depth",
        type=int,
        default=3,
        help="Number of residual dilated temporal mixer blocks when --use-temporal-mixer is enabled.",
    )
    parser.add_argument(
        "--use-rul-temporal-anchor-fusion",
        action="store_true",
        help=(
            "For C-MAPSS RUL, predict from a temporal anchor plus a reliability-gated path residual head "
            "instead of forcing paths to directly dominate the RUL head."
        ),
    )
    parser.add_argument(
        "--rul-anchor-residual-scale",
        type=float,
        default=1.0,
        help="Maximum logit-scale residual contributed by the path branch to the temporal RUL anchor.",
    )
    parser.add_argument(
        "--rul-anchor-gate-bias",
        type=float,
        default=-1.0,
        help="Initial bias for the path residual gate; negative values make the anchor branch conservative.",
    )
    args = parser.parse_args()

    ready_root = Path(args.ready_root)
    output_dir = Path(args.output_dir)
    datasets = ["tep", "skab", "hydraulic", "cmapss"] if args.dataset == "all" else [str(args.dataset)]
    runs: list[dict[str, Any]] = []
    for dataset in datasets:
        if dataset == "hydraulic":
            targets = _split_csv(args.hydraulic_targets)
        elif dataset == "cmapss":
            targets = [str(args.cmapss_target)]
        else:
            targets = [None]
        for target in targets:
            task = load_ready_task(ready_root, dataset, target=target)
            for seed in _split_ints(args.seeds):
                result = run_ready_task(
                    task,
                    output_dir=output_dir,
                    variant=str(args.variant),
                    seed=int(seed),
                    window_size=int(args.window_size),
                    hidden_dim=int(args.hidden_dim),
                    epochs=int(args.epochs),
                    batch_size=int(args.batch_size),
                    learning_rate=float(args.learning_rate),
                    max_rows_per_split=int(args.max_rows_per_split) if int(args.max_rows_per_split) > 0 else None,
                    classification_loss_weight=float(args.classification_loss_weight),
                    device=str(args.device),
                    forecast_weight=float(args.forecast_weight),
                    graph_weight=float(args.graph_weight),
                    focal_loss_gamma=float(args.focal_loss_gamma),
                    label_smoothing=float(args.label_smoothing),
                    use_prototype_posterior_fusion=bool(args.use_prototype_posterior_fusion),
                    prototype_fusion_max_blend=float(args.prototype_fusion_max_blend),
                    prototype_fusion_blend_steps=int(args.prototype_fusion_blend_steps),
                    prototype_fusion_temperature_grid=str(args.prototype_fusion_temperature_grid),
                    prototype_fusion_min_val_gain=float(args.prototype_fusion_min_val_gain),
                    use_one_class_posterior_fusion=bool(args.use_one_class_posterior_fusion),
                    one_class_fusion_max_blend=float(args.one_class_fusion_max_blend),
                    one_class_fusion_blend_steps=int(args.one_class_fusion_blend_steps),
                    one_class_fusion_temperature_grid=str(args.one_class_fusion_temperature_grid),
                    one_class_fusion_threshold_grid=str(args.one_class_fusion_threshold_grid),
                    one_class_fusion_min_val_gain=float(args.one_class_fusion_min_val_gain),
                    use_ordinal_posterior_calibration=bool(args.use_ordinal_posterior_calibration),
                    ordinal_posterior_max_blend=float(args.ordinal_posterior_max_blend),
                    ordinal_posterior_blend_steps=int(args.ordinal_posterior_blend_steps),
                    ordinal_posterior_smoothing=float(args.ordinal_posterior_smoothing),
                    ordinal_posterior_min_val_gain=float(args.ordinal_posterior_min_val_gain),
                    ordinal_loss_weight=float(args.ordinal_loss_weight),
                    ordinal_boundary_loss_weight=float(args.ordinal_boundary_loss_weight),
                    ordinal_boundary_focal_gamma=float(args.ordinal_boundary_focal_gamma),
                    ordinal_boundary_focus=float(args.ordinal_boundary_focus),
                    path_entropy_weight=float(args.path_entropy_weight),
                    path_aux_weight=float(args.path_aux_weight),
                    coarse_aux_weight=float(args.coarse_aux_weight),
                    evidence_router_aux_weight=float(args.evidence_router_aux_weight),
                    health_aux_weight=float(args.health_aux_weight),
                    rul_loss_weight=float(args.rul_loss_weight),
                    health_rul_cap=float(args.health_rul_cap),
                    graph_top_k=int(args.graph_top_k),
                    max_paths=int(args.max_paths),
                    evidence_prior_mode=str(args.evidence_prior_mode),
                    prior_strength=float(args.prior_strength),
                    prior_min_reliability=float(args.prior_min_reliability),
                    algorithmic_edge_prior_mode=str(args.algorithmic_edge_prior_mode),
                    algorithmic_edge_prior_top_k=int(args.algorithmic_edge_prior_top_k),
                    algorithmic_edge_prior_group_top_k=int(args.algorithmic_edge_prior_group_top_k),
                    algorithmic_edge_prior_max_lag=int(args.algorithmic_edge_prior_max_lag),
                    algorithmic_edge_prior_strength=float(args.algorithmic_edge_prior_strength),
                    algorithmic_edge_prior_class_weight=float(args.algorithmic_edge_prior_class_weight),
                    algorithmic_edge_prior_lag_weight=float(args.algorithmic_edge_prior_lag_weight),
                    algorithmic_edge_prior_corr_weight=float(args.algorithmic_edge_prior_corr_weight),
                    algorithmic_edge_prior_residual_weight=float(args.algorithmic_edge_prior_residual_weight),
                    algorithmic_edge_prior_response_weight=float(args.algorithmic_edge_prior_response_weight),
                    algorithmic_edge_prior_stability_weight=float(args.algorithmic_edge_prior_stability_weight),
                    algorithmic_edge_prior_bank_min_votes=int(args.algorithmic_edge_prior_bank_min_votes),
                    algorithmic_edge_prior_bank_single_view_scale=float(args.algorithmic_edge_prior_bank_single_view_scale),
                    algorithmic_edge_prior_bank_vote_boost=float(args.algorithmic_edge_prior_bank_vote_boost),
                    algorithmic_edge_prior_bank_global_budget_multiplier=float(args.algorithmic_edge_prior_bank_global_budget_multiplier),
                    algorithmic_edge_prior_pool_multiplier=float(args.algorithmic_edge_prior_pool_multiplier),
                    algorithmic_edge_prior_pool_min_score=float(args.algorithmic_edge_prior_pool_min_score),
                    algorithmic_edge_prior_pool_rank_weight=float(args.algorithmic_edge_prior_pool_rank_weight),
                    algorithmic_edge_prior_candidate_only=bool(args.algorithmic_edge_prior_candidate_only),
                    prior_algorithmic_combine_mode=str(args.prior_algorithmic_combine_mode),
                    prior_external_isolated_scale=float(args.prior_external_isolated_scale),
                    prior_overlap_boost=float(args.prior_overlap_boost),
                    prior_nonanchor_algorithmic_scale=float(args.prior_nonanchor_algorithmic_scale),
                    prior_coverage_fraction=float(args.prior_coverage_fraction),
                    candidate_coverage_fraction=float(args.candidate_coverage_fraction),
                    calibrate_prior_edges=bool(args.calibrate_prior_edges),
                    prior_calibration_max_lag=int(args.prior_calibration_max_lag),
                    prior_calibration_min_support=float(args.prior_calibration_min_support),
                    prior_calibration_strength=float(args.prior_calibration_strength),
                    external_edge_candidate_only=bool(args.external_edge_candidate_only),
                    external_candidate_families=str(args.external_candidate_families),
                    external_family_calibration_floor=float(args.external_family_calibration_floor),
                    external_family_min_data_support=float(args.external_family_min_data_support),
                    external_candidate_expert_scale=float(args.external_candidate_expert_scale),
                    external_candidate_llm_scale=float(args.external_candidate_llm_scale),
                    external_candidate_default_scale=float(args.external_candidate_default_scale),
                    disable_source_complexity_penalty=bool(args.disable_source_complexity_penalty),
                    use_llm_expert_condition_verifier=bool(args.use_llm_expert_condition_verifier),
                    llm_condition_verifier_weight=float(args.llm_condition_verifier_weight),
                    llm_condition_verifier_min_data_support=float(args.llm_condition_verifier_min_data_support),
                    llm_condition_verifier_floor=float(args.llm_condition_verifier_floor),
                    llm_condition_verifier_target=str(args.llm_condition_verifier_target),
                    use_llm_condition_verifier_validation_admission=bool(
                        args.use_llm_condition_verifier_validation_admission
                    ),
                    llm_condition_verifier_min_val_gain=float(args.llm_condition_verifier_min_val_gain),
                    prior_group_expansion=bool(args.prior_group_expansion),
                    prior_group_expansion_strength=float(args.prior_group_expansion_strength),
                    dropout=float(args.dropout),
                    auto_path_budget=bool(args.auto_path_budget),
                    path_coverage_mode=str(args.path_coverage_mode),
                    coverage_dedup_mode=str(args.coverage_dedup_mode),
                    coverage_redundancy_penalty=float(args.coverage_redundancy_penalty),
                    deduplicate_exact_paths=bool(args.deduplicate_exact_paths),
                    use_task_salience=bool(args.use_task_salience),
                    salience_mode=str(args.salience_mode),
                    lifecycle_salience_weight=float(args.lifecycle_salience_weight),
                    order_anchor_evidence_weight=float(args.order_anchor_evidence_weight),
                    algorithmic_evidence_top_k=int(args.algorithmic_evidence_top_k),
                    salience_selection_strength=float(args.salience_selection_strength),
                    salience_coverage_fraction=float(args.salience_coverage_fraction),
                    use_temporal_descriptors=bool(args.use_temporal_descriptors) and not bool(args.disable_temporal_descriptors),
                    temporal_descriptor_weight=float(args.temporal_descriptor_weight),
                    temporal_encoder_mode=str(args.temporal_encoder_mode),
                    use_temporal_mixer=bool(args.use_temporal_mixer),
                    temporal_mixer_type=str(args.temporal_mixer_type),
                    temporal_mixer_depth=int(args.temporal_mixer_depth),
                    use_rul_temporal_anchor_fusion=bool(args.use_rul_temporal_anchor_fusion),
                    rul_anchor_residual_scale=float(args.rul_anchor_residual_scale),
                    rul_anchor_gate_bias=float(args.rul_anchor_gate_bias),
                    use_multihop_paths=bool(args.use_multihop_paths),
                    multihop_path_fraction=float(args.multihop_path_fraction),
                    use_context_router=not bool(args.disable_context_router),
                    use_class_conditioned_evidence=bool(args.use_class_conditioned_evidence),
                    class_evidence_top_k=int(args.class_evidence_top_k),
                    class_evidence_mode=str(args.class_evidence_mode),
                    class_evidence_max_lag=int(args.class_evidence_max_lag),
                    class_evidence_lag_weight=float(args.class_evidence_lag_weight),
                    class_evidence_family_k=int(args.class_evidence_family_k),
                    class_evidence_family_weight=float(args.class_evidence_family_weight),
                    class_evidence_focus_mode=str(args.class_evidence_focus_mode),
                    class_evidence_focus_classes=str(args.class_evidence_focus_classes),
                    class_evidence_focus_k=int(args.class_evidence_focus_k),
                    class_evidence_focus_nonfocus_weight=float(args.class_evidence_focus_nonfocus_weight),
                    class_evidence_gate_threshold=float(args.class_evidence_gate_threshold),
                    class_evidence_gate_temperature=float(args.class_evidence_gate_temperature),
                    class_evidence_gate_floor=float(args.class_evidence_gate_floor),
                    class_evidence_router_temperature=float(args.class_evidence_router_temperature),
                    class_evidence_router_top_k=int(args.class_evidence_router_top_k),
                    use_stable_path_evidence=bool(args.use_stable_path_evidence),
                    stable_path_evidence_splits=int(args.stable_path_evidence_splits),
                    stable_path_evidence_min_vote_fraction=float(args.stable_path_evidence_min_vote_fraction),
                    stable_path_evidence_strength=float(args.stable_path_evidence_strength),
                    stable_path_evidence_top_k=int(args.stable_path_evidence_top_k),
                    stable_path_evidence_edge_top_k=int(args.stable_path_evidence_edge_top_k),
                    stable_path_evidence_mode=str(args.stable_path_evidence_mode),
                    stable_path_evidence_max_lag=int(args.stable_path_evidence_max_lag),
                    stable_path_evidence_lag_weight=float(args.stable_path_evidence_lag_weight),
                    stable_path_evidence_path_mode=str(args.stable_path_evidence_path_mode),
                    stable_path_evidence_class_mode=str(args.stable_path_evidence_class_mode),
                    stable_path_evidence_class_floor=float(args.stable_path_evidence_class_floor),
                    use_class_evidence_quality_certificate=bool(args.use_class_evidence_quality_certificate),
                    class_evidence_quality_mode=str(args.class_evidence_quality_mode),
                    class_evidence_quality_floor=float(args.class_evidence_quality_floor),
                    class_evidence_quality_threshold=float(args.class_evidence_quality_threshold),
                    class_evidence_quality_temperature=float(args.class_evidence_quality_temperature),
                    use_path_family_quality_certificate=bool(args.use_path_family_quality_certificate),
                    path_family_quality_mode=str(args.path_family_quality_mode),
                    path_family_quality_floor=float(args.path_family_quality_floor),
                    path_family_quality_threshold=float(args.path_family_quality_threshold),
                    path_family_quality_temperature=float(args.path_family_quality_temperature),
                    path_family_quality_direct_weight=float(args.path_family_quality_direct_weight),
                    path_family_quality_group_weight=float(args.path_family_quality_group_weight),
                    path_family_quality_stability_weight=float(args.path_family_quality_stability_weight),
                    path_family_quality_family_k=int(args.path_family_quality_family_k),
                    path_family_quality_family_weight=float(args.path_family_quality_family_weight),
                    use_path_family_protected_proposal_weights=bool(
                        args.use_path_family_protected_proposal_weights
                    ),
                    use_stable_class_edge_overlay=bool(args.use_stable_class_edge_overlay),
                    stable_class_edge_overlay_scale=float(args.stable_class_edge_overlay_scale),
                    stable_class_edge_overlay_top_k=int(args.stable_class_edge_overlay_top_k),
                    stable_class_edge_overlay_group_top_k=int(args.stable_class_edge_overlay_group_top_k),
                    stable_class_edge_overlay_focus_weight=float(args.stable_class_edge_overlay_focus_weight),
                    stable_class_edge_overlay_nonfocus_weight=float(args.stable_class_edge_overlay_nonfocus_weight),
                    stable_class_edge_overlay_mode=str(args.stable_class_edge_overlay_mode),
                    use_certified_graph_prior_core=bool(args.use_certified_graph_prior_core),
                    use_separate_path_candidate_prior=bool(args.use_separate_path_candidate_prior),
                    graph_prior_core_floor=float(args.graph_prior_core_floor),
                    graph_prior_core_threshold=float(args.graph_prior_core_threshold),
                    graph_prior_core_temperature=float(args.graph_prior_core_temperature),
                    graph_prior_core_top_k=int(args.graph_prior_core_top_k),
                    graph_prior_core_group_top_k=int(args.graph_prior_core_group_top_k),
                    graph_prior_core_direct_weight=float(args.graph_prior_core_direct_weight),
                    graph_prior_core_group_weight=float(args.graph_prior_core_group_weight),
                    graph_prior_core_stability_weight=float(args.graph_prior_core_stability_weight),
                    graph_prior_core_prior_weight=float(args.graph_prior_core_prior_weight),
                    graph_prior_core_focus_weight=float(args.graph_prior_core_focus_weight),
                    graph_prior_core_nonfocus_weight=float(args.graph_prior_core_nonfocus_weight),
                    use_candidate_prior_admission=bool(args.use_candidate_prior_admission),
                    candidate_prior_admission_floor=float(args.candidate_prior_admission_floor),
                    candidate_prior_admission_threshold=float(args.candidate_prior_admission_threshold),
                    candidate_prior_admission_temperature=float(args.candidate_prior_admission_temperature),
                    candidate_prior_admission_support_mode=str(args.candidate_prior_admission_support_mode),
                    candidate_prior_admission_scale=float(args.candidate_prior_admission_scale),
                    candidate_prior_admission_min_support=float(args.candidate_prior_admission_min_support),
                    candidate_prior_admission_protected_min_support=float(
                        args.candidate_prior_admission_protected_min_support
                    ),
                    candidate_prior_admission_target=str(args.candidate_prior_admission_target),
                    use_class_conditioned_prior_admission=bool(args.use_class_conditioned_prior_admission),
                    class_prior_admission_floor=float(args.class_prior_admission_floor),
                    use_adaptive_prior_admission=bool(args.use_adaptive_prior_admission),
                    adaptive_prior_admission_threshold=float(args.adaptive_prior_admission_threshold),
                    adaptive_prior_admission_temperature=float(args.adaptive_prior_admission_temperature),
                    use_edge_family_router=bool(args.use_edge_family_router),
                    edge_family_router_temperature=float(args.edge_family_router_temperature),
                    edge_family_router_floor=float(args.edge_family_router_floor),
                    edge_family_router_blend=float(args.edge_family_router_blend),
                    edge_family_router_balance_weight=float(args.edge_family_router_balance_weight),
                    use_edge_calibrator=bool(args.use_edge_calibrator),
                    edge_calibrator_floor=float(args.edge_calibrator_floor),
                    edge_calibrator_init_bias=float(args.edge_calibrator_init_bias),
                    edge_calibrator_reg_weight=float(args.edge_calibrator_reg_weight),
                    use_path_reliability_calibrator=bool(args.use_path_reliability_calibrator),
                    path_reliability_context_scale=float(args.path_reliability_context_scale),
                    path_reliability_context_reg_weight=float(args.path_reliability_context_reg_weight),
                    use_learned_path_admission=bool(args.use_learned_path_admission),
                    path_admission_strength=float(args.path_admission_strength),
                    path_admission_reg_weight=float(args.path_admission_reg_weight),
                    use_path_prior_consistency=bool(args.use_path_prior_consistency),
                    path_prior_consistency_strength=float(args.path_prior_consistency_strength),
                    path_prior_consistency_threshold=float(args.path_prior_consistency_threshold),
                    path_prior_consistency_temperature=float(args.path_prior_consistency_temperature),
                    path_prior_consistency_support_mode=str(args.path_prior_consistency_support_mode),
                    path_prior_consistency_class_floor=float(args.path_prior_consistency_class_floor),
                    use_path_evidence_consistency=bool(args.use_path_evidence_consistency),
                    path_evidence_consistency_strength=float(args.path_evidence_consistency_strength),
                    path_evidence_consistency_threshold=float(args.path_evidence_consistency_threshold),
                    path_evidence_consistency_temperature=float(args.path_evidence_consistency_temperature),
                    path_evidence_consistency_floor=float(args.path_evidence_consistency_floor),
                    path_evidence_consistency_support_mode=str(args.path_evidence_consistency_support_mode),
                    use_path_proposal_consistency=bool(args.use_path_proposal_consistency),
                    path_proposal_consistency_strength=float(args.path_proposal_consistency_strength),
                    path_proposal_consistency_threshold=float(args.path_proposal_consistency_threshold),
                    path_proposal_consistency_temperature=float(args.path_proposal_consistency_temperature),
                    path_proposal_consistency_floor=float(args.path_proposal_consistency_floor),
                    path_proposal_consistency_support_mode=str(args.path_proposal_consistency_support_mode),
                    path_proposal_consistency_protected_strength=float(
                        args.path_proposal_consistency_protected_strength
                    ),
                    path_proposal_retention_fraction=float(args.path_proposal_retention_fraction),
                    protect_order_anchor_target=bool(args.protect_order_anchor_target),
                    protect_order_anchor_path_nodes=bool(args.protect_order_anchor_path_nodes),
                    use_regime_prototype_residuals=bool(args.use_regime_prototype_residuals),
                    regime_prototype_k=int(args.regime_prototype_k),
                    regime_healthy_stage_max=int(args.regime_healthy_stage_max),
                )
                runs.append(result)
                if str(result.get("primary_metric_family", "classification")) == "rul_regression":
                    print(
                        "{dataset}:{target} seed={seed} variant={variant} prior={prior} rul_rmse={rmse:.4f} rul_mae={mae:.4f} rul_score={score:.2f} ips={ips:.1f}".format(
                            dataset=result["dataset"],
                            target=result["target"],
                            seed=result["seed"],
                            variant=result["variant"],
                            prior=(result.get("evidence_prior") or {}).get("mode", "none"),
                            rmse=float(result["primary_test_metrics"].get("rul_rmse", 0.0)),
                            mae=float(result["primary_test_metrics"].get("rul_mae", 0.0)),
                            score=float(result["primary_test_metrics"].get("rul_score", 0.0)),
                            ips=result["efficiency"]["test_inference_samples_per_second"],
                        )
                    )
                else:
                    print(
                        "{dataset}:{target} seed={seed} variant={variant} prior={prior} macro_f1={macro:.4f} bal_acc={bal:.4f} ips={ips:.1f}".format(
                            dataset=result["dataset"],
                            target=result["target"],
                            seed=result["seed"],
                            variant=result["variant"],
                            prior=(result.get("evidence_prior") or {}).get("mode", "none"),
                            macro=result["primary_test_metrics"]["macro_f1"],
                            bal=result["primary_test_metrics"]["balanced_accuracy"],
                            ips=result["efficiency"]["test_inference_samples_per_second"],
                        )
                    )
    payload = {
        "status": "ok",
        "model": "MS-GSE + RPF",
        "variant": str(args.variant),
        "runs": runs,
        "summary": aggregate_runs(runs),
    }
    summary_path = output_dir / f"ms_gse_rpf_{args.dataset}_{args.variant}_summary.json"
    _write_json(summary_path, payload)


if __name__ == "__main__":
    main()
