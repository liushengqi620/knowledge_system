from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from multiclass_event_evaluation import summarize_multiclass_event_evaluation

try:
    from run_kiepgl_multiclass_experiment import (
        PROJECT_ROOT,
        apply_class_logit_biases,
        build_event_horizons,
        build_event_ids,
        load_class_mapping,
        load_multiclass_dataset,
        split_indices_from_metadata,
        tune_weak_class_biases_on_validation,
    )
except Exception:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent

    def build_event_ids(y: Sequence[int] | np.ndarray, *, normal_class_id: int = 0) -> np.ndarray:
        labels = np.asarray(y, dtype=int).reshape(-1)
        ids: list[str] = []
        active_event_start: int | None = None
        active_class: int | None = None
        for i, label in enumerate(labels):
            class_id = int(label)
            if class_id == int(normal_class_id):
                active_event_start = None
                active_class = None
                ids.append(f"normal_{i}")
                continue
            if active_event_start is None or active_class != class_id:
                active_event_start = i
                active_class = class_id
            ids.append(f"event_{active_event_start}")
        return np.asarray(ids, dtype=object)

    def build_event_horizons(y: Sequence[int] | np.ndarray, *, normal_class_id: int = 0) -> np.ndarray:
        labels = np.asarray(y, dtype=int).reshape(-1)
        horizons = np.full(len(labels), -1.0, dtype=float)
        i = 0
        while i < len(labels):
            if int(labels[i]) == int(normal_class_id):
                i += 1
                continue
            j = i + 1
            while j < len(labels) and int(labels[j]) == int(labels[i]):
                j += 1
            horizons[i:j] = np.arange(j - i, 0, -1, dtype=float)
            i = j
        return horizons

    def load_class_mapping(dataset_dir: Path) -> tuple[list[int], list[str]]:
        raw = json.loads((Path(dataset_dir) / "class_name_mapping.json").read_text(encoding="utf-8"))
        classes = sorted(raw.get("classes", []), key=lambda row: int(row["class_id"]))
        return [int(row["class_id"]) for row in classes], [str(row["class_name"]) for row in classes]

    def load_multiclass_dataset(
        dataset_dir: Path,
        *,
        max_rows: int | None = None,
        sample_mode: str = "stratified",
        seed: int = 42,
        feature_set: str = "raw",
    ) -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray]:
        x = pd.read_csv(Path(dataset_dir) / "X_process_features.csv")
        y = pd.read_csv(Path(dataset_dir) / "y_quality_label.csv")
        n = min(len(x), len(y))
        x = x.iloc[:n].reset_index(drop=True)
        y = y.iloc[:n].reset_index(drop=True)
        labels = pd.to_numeric(y["event_quality_class_id"], errors="coerce").fillna(0).astype(int).to_numpy()
        if max_rows is not None and int(max_rows) > 0 and int(max_rows) < n:
            if str(sample_mode) == "stratified":
                rng = np.random.default_rng(int(seed))
                keep: list[int] = []
                per_class = max(1, int(max_rows) // max(1, len(np.unique(labels))))
                for class_id in sorted(np.unique(labels)):
                    idx = np.flatnonzero(labels == int(class_id))
                    take = min(len(idx), per_class)
                    keep.extend(rng.choice(idx, size=take, replace=False).tolist())
                if len(keep) < int(max_rows):
                    rest = np.setdiff1d(np.arange(n), np.asarray(keep, dtype=np.int64), assume_unique=False)
                    take = min(len(rest), int(max_rows) - len(keep))
                    keep.extend(rng.choice(rest, size=take, replace=False).tolist())
                selected = np.asarray(sorted(keep[: int(max_rows)]), dtype=np.int64)
            else:
                selected = np.arange(int(max_rows), dtype=np.int64)
            x = x.iloc[selected].reset_index(drop=True)
            y = y.iloc[selected].reset_index(drop=True)
            labels = labels[selected]
        return x, y, labels

    def split_indices_from_metadata(
        y_meta: pd.DataFrame,
        *,
        test_size: float = 0.2,
        val_fraction: float = 0.2,
        split_mode: str = "metadata",
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        n = len(y_meta)
        idx = np.arange(n, dtype=np.int64)
        if "split_role" in y_meta.columns:
            role = y_meta["split_role"].astype(str).str.lower().to_numpy()
            test_idx = idx[role == "test"]
            train_pool = idx[role != "test"]
        else:
            test_n = max(1, int(round(n * float(test_size))))
            train_pool = idx[:-test_n]
            test_idx = idx[-test_n:]
        val_n = max(1, int(round(len(train_pool) * float(val_fraction)))) if len(train_pool) > 1 else 0
        val_idx = train_pool[-val_n:] if val_n else np.asarray([], dtype=np.int64)
        train_idx = train_pool[:-val_n] if val_n else train_pool
        return train_idx.astype(np.int64), val_idx.astype(np.int64), test_idx.astype(np.int64)

    def apply_class_logit_biases(proba: np.ndarray, biases: Mapping[int, float]) -> np.ndarray:
        arr = np.asarray(proba, dtype=float)
        logits = np.log(np.clip(arr, 1e-12, 1.0))
        for class_id, bias in dict(biases).items():
            cid = int(class_id)
            if 0 <= cid < logits.shape[1]:
                logits[:, cid] += float(bias)
        logits -= logits.max(axis=1, keepdims=True)
        exp = np.exp(logits)
        return exp / np.maximum(exp.sum(axis=1, keepdims=True), 1e-12)

    def tune_weak_class_biases_on_validation(
        y_val: np.ndarray,
        val_proba: np.ndarray,
        *,
        class_names: Sequence[str],
        weak_class_names: Sequence[str],
        bias_grid: Sequence[float],
    ) -> dict[str, Any]:
        weak_ids = [i for i, name in enumerate(class_names) if str(name) in set(map(str, weak_class_names))]
        base_pred = np.asarray(val_proba).argmax(axis=1)
        base_score = float(np.mean(base_pred == np.asarray(y_val, dtype=int)))
        selected: dict[int, float] = {}
        best_score = base_score
        for cid in weak_ids:
            best_bias = 0.0
            for bias in bias_grid:
                candidate = apply_class_logit_biases(val_proba, {cid: float(bias)})
                score = float(np.mean(candidate.argmax(axis=1) == np.asarray(y_val, dtype=int)))
                if score > best_score + 1e-12:
                    best_score = score
                    best_bias = float(bias)
            if best_bias != 0.0:
                selected[int(cid)] = best_bias
        return {
            "enabled": True,
            "base_validation_accuracy": base_score,
            "best_validation_accuracy": best_score,
            "selected_bias_by_class_id": selected,
        }


DEFAULT_TEP_DATASET_DIR = PROJECT_ROOT / "knowledge_exports" / "tep_fault_diagnosis_dataset"


def _fs_path(path: Path | str) -> Path:
    p = Path(path)
    if os.name != "nt":
        return p
    raw = str(p if p.is_absolute() else p.resolve())
    if raw.startswith("\\\\?\\"):
        return Path(raw)
    return Path("\\\\?\\" + raw)


@dataclass
class SequenceSplit:
    x_train: np.ndarray
    y_train: np.ndarray
    x_val: np.ndarray
    y_val: np.ndarray
    x_test: np.ndarray
    y_test: np.ndarray
    idx_train: np.ndarray
    idx_val: np.ndarray
    idx_test: np.ndarray
    feature_cols: list[str]


def _group_keys(y_meta: pd.DataFrame) -> list[str]:
    keys = [col for col in ("source_split", "source_file") if col in y_meta.columns]
    return keys or [col for col in ("event_bag_id", "fault_id") if col in y_meta.columns]


def build_causal_run_windows(
    x: pd.DataFrame,
    y_meta: pd.DataFrame,
    feature_cols: Sequence[str],
    *,
    window_size: int = 32,
) -> np.ndarray:
    """Build [row, time, variable] windows using only past/current samples within each TEP run."""

    cols = [str(c) for c in feature_cols if str(c) in x.columns]
    if not cols:
        raise ValueError("No feature columns available for sequence windows.")
    w = max(2, int(window_size))
    values = x[cols].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=np.float64)
    values = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
    out = np.zeros((len(x), w, len(cols)), dtype=np.float32)
    keys = _group_keys(y_meta)
    if keys:
        grouped = y_meta.reset_index().groupby(keys, sort=False, group_keys=False)
        groups = [group["index"].to_numpy(dtype=np.int64) for _name, group in grouped]
    else:
        groups = [np.arange(len(x), dtype=np.int64)]
    for group_idx in groups:
        if "sample_index" in y_meta.columns:
            order_values = pd.to_numeric(y_meta.iloc[group_idx]["sample_index"], errors="coerce").fillna(0).to_numpy()
            group_idx = group_idx[np.argsort(order_values, kind="stable")]
        group_values = values[group_idx]
        if len(group_values) == 0:
            continue
        for pos, row_idx in enumerate(group_idx):
            start = max(0, pos - w + 1)
            segment = group_values[start : pos + 1]
            if len(segment) < w:
                pad = np.repeat(segment[:1], w - len(segment), axis=0)
                segment = np.vstack([pad, segment])
            out[int(row_idx)] = segment[-w:]
    return out


def prepare_sequence_split(
    dataset_dir: Path,
    *,
    max_rows: int | None = None,
    sample_mode: str = "stratified",
    seed: int = 42,
    window_size: int = 32,
) -> SequenceSplit:
    x, y_meta, labels = load_multiclass_dataset(
        dataset_dir,
        max_rows=max_rows,
        sample_mode=sample_mode,
        seed=seed,
        feature_set="raw",
    )
    feature_cols = [str(c) for c in x.columns if pd.api.types.is_numeric_dtype(x[c])]
    windows = build_causal_run_windows(x, y_meta, feature_cols, window_size=window_size)
    idx_train, idx_val, idx_test = split_indices_from_metadata(
        y_meta,
        test_size=0.2,
        val_fraction=0.2,
        split_mode="metadata" if "split_role" in y_meta.columns else "stratified_time_ordered",
    )
    train_flat = windows[idx_train].reshape(len(idx_train), -1)
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    train_scaled = scaler.fit_transform(imputer.fit_transform(train_flat))

    def _scale(idx: np.ndarray) -> np.ndarray:
        flat = windows[idx].reshape(len(idx), -1)
        scaled = scaler.transform(imputer.transform(flat))
        return scaled.reshape(len(idx), windows.shape[1], windows.shape[2]).astype(np.float32)

    return SequenceSplit(
        x_train=train_scaled.reshape(len(idx_train), windows.shape[1], windows.shape[2]).astype(np.float32),
        y_train=labels[idx_train].astype(np.int64),
        x_val=_scale(idx_val),
        y_val=labels[idx_val].astype(np.int64),
        x_test=_scale(idx_test),
        y_test=labels[idx_test].astype(np.int64),
        idx_train=idx_train,
        idx_val=idx_val,
        idx_test=idx_test,
        feature_cols=feature_cols,
    )


def _candidate_prior_edges(prior_name: str) -> tuple[list[dict[str, Any]], str]:
    """Fallback TEP mechanism edges used when recovered exports miss the prior file."""

    try:
        from build_tep_knowledge_prior import expert_edges, llm_candidate_edges
    except Exception as exc:  # pragma: no cover - only used when the prior builder is unavailable.
        return [], f"generated_prior_unavailable:{type(exc).__name__}"

    name = str(prior_name).lower()
    if "llm" in name and "expert" not in name:
        return llm_candidate_edges(), "generated_tep_llm_prior"
    if "expert" in name and "llm" not in name:
        return expert_edges(), "generated_tep_expert_prior"
    return expert_edges() + llm_candidate_edges(), "generated_tep_expert_llm_prior"


def _edge_score(edge: Mapping[str, Any]) -> float:
    weight = float(edge.get("weight", 1.0) or 0.0)
    confidence = float(edge.get("confidence", 1.0) or 0.0)
    evidence = edge.get("evidence", {}) or {}
    if isinstance(evidence, Mapping) and evidence:
        support = max(float(v or 0.0) for v in evidence.values())
    else:
        support = confidence
    return max(0.0, min(1.0, weight * max(confidence, support)))


def load_graph_adjacency(
    dataset_dir: Path,
    feature_cols: Sequence[str],
    *,
    prior_name: str = "tep_expert_llm_graph_prior.json",
    reliability_threshold: float = 0.0,
    max_edges: int | None = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    cols = [str(c) for c in feature_cols]
    index = {name: i for i, name in enumerate(cols)}
    path = Path(dataset_dir) / str(prior_name)
    source = "file"
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        edges = [dict(edge) for edge in (payload.get("edges", []) or [])]
    else:
        edges, source = _candidate_prior_edges(prior_name)

    candidates: list[tuple[float, str, str]] = []
    for edge in edges:
        src = str(edge.get("from", edge.get("source", "")))
        dst = str(edge.get("to", edge.get("target", "")))
        if src not in index or dst not in index or src == dst:
            continue
        score = _edge_score(edge)
        if score > 0.0:
            candidates.append((score, src, dst))

    threshold = max(0.0, min(1.0, float(reliability_threshold)))
    selected = [item for item in candidates if item[0] >= threshold]
    selected.sort(key=lambda item: item[0], reverse=True)
    if max_edges is not None and int(max_edges) > 0:
        selected = selected[: int(max_edges)]

    adjacency = np.zeros((len(cols), len(cols)), dtype=np.float32)
    for score, src, dst in selected:
        adjacency[index[src], index[dst]] = max(float(adjacency[index[src], index[dst]]), float(score))

    diagnostics = {
        "enabled": True,
        "status": "ok" if candidates else "empty",
        "source": source,
        "path": str(path),
        "candidate_edges": int(len(candidates)),
        "matched_edges": int(len(selected)),
        "pruned_edges": int(max(0, len(candidates) - len(selected))),
        "reliability_threshold": float(threshold),
        "max_edges": int(max_edges) if max_edges is not None and int(max_edges) > 0 else None,
        "n_features": int(len(cols)),
    }
    return adjacency, diagnostics


def _graph_message(windows: np.ndarray, adjacency: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    arr = np.asarray(windows, dtype=np.float32)
    graph = np.asarray(adjacency, dtype=np.float32)
    if graph.ndim != 2 or graph.shape[0] != arr.shape[2] or graph.shape[1] != arr.shape[2]:
        raise ValueError("Graph adjacency shape must match the sequence feature dimension.")
    col_sum = graph.sum(axis=0, keepdims=True)
    active = (col_sum.reshape(-1) > 1e-12).astype(np.float32)
    normalized = np.divide(graph, np.maximum(col_sum, 1e-12), out=np.zeros_like(graph), where=col_sum > 1e-12)
    neighbor = np.einsum("btf,fg->btg", arr, normalized, optimize=True).astype(np.float32)
    return neighbor, active


def apply_graph_filter_to_windows(
    windows: np.ndarray,
    adjacency: np.ndarray | None,
    *,
    strength: float = 0.0,
) -> np.ndarray:
    arr = np.asarray(windows, dtype=np.float32)
    alpha = max(0.0, min(1.0, float(strength)))
    if alpha <= 0.0 or adjacency is None:
        return arr.copy()
    neighbor, active = _graph_message(arr, adjacency)
    mask = active.reshape(1, 1, -1)
    return (arr * (1.0 - alpha * mask) + neighbor * (alpha * mask)).astype(np.float32)


def _standardized_lagged_graph_residuals(
    x_train: np.ndarray,
    x_val: np.ndarray,
    x_test: np.ndarray,
    adjacency: np.ndarray | None,
    *,
    strength: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    alpha = max(0.0, min(1.0, float(strength)))
    if adjacency is None or alpha <= 0.0:
        return (
            np.zeros_like(x_train, dtype=np.float32),
            np.zeros_like(x_val, dtype=np.float32),
            np.zeros_like(x_test, dtype=np.float32),
            {"residual_channel_enabled": False, "reason": "missing_or_zero_strength_graph"},
        )

    def _resid(arr: np.ndarray) -> np.ndarray:
        base = np.asarray(arr, dtype=np.float32)
        neighbor, active = _graph_message(base, adjacency)
        return (alpha * (neighbor - base) * active.reshape(1, 1, -1)).astype(np.float32)

    train_resid = _resid(x_train)
    mean = train_resid.mean(axis=(0, 1), keepdims=True)
    std = train_resid.std(axis=(0, 1), keepdims=True) + 1e-6

    def _standardize(arr: np.ndarray) -> np.ndarray:
        out = (_resid(arr) - mean) / std
        return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)

    return (
        _standardize(x_train),
        _standardize(x_val),
        _standardize(x_test),
        {
            "residual_channel_enabled": True,
            "residual_channel_features": int(x_train.shape[2]),
            "active_graph_edges": int(np.count_nonzero(np.asarray(adjacency) > 0.0)),
            "strength": float(alpha),
        },
    )


class _TCNSequenceModule(nn.Module):
    def __init__(self, n_features: int, n_classes: int, hidden_dim: int) -> None:
        super().__init__()
        hidden = max(16, int(hidden_dim))
        self.net = nn.Sequential(
            nn.Conv1d(n_features, hidden, kernel_size=5, padding=2),
            nn.BatchNorm1d(hidden),
            nn.GELU(),
            nn.Conv1d(hidden, hidden, kernel_size=3, padding=2, dilation=2),
            nn.BatchNorm1d(hidden),
            nn.GELU(),
            nn.Conv1d(hidden, hidden, kernel_size=3, padding=4, dilation=4),
            nn.GELU(),
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
            nn.Linear(hidden, n_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x.transpose(1, 2))


class _GRUSequenceModule(nn.Module):
    def __init__(self, n_features: int, n_classes: int, hidden_dim: int) -> None:
        super().__init__()
        hidden = max(16, int(hidden_dim))
        self.gru = nn.GRU(n_features, hidden, num_layers=1, batch_first=True, bidirectional=True)
        self.attn = nn.Linear(hidden * 2, 1)
        self.head = nn.Sequential(
            nn.LayerNorm(hidden * 2),
            nn.Linear(hidden * 2, hidden),
            nn.GELU(),
            nn.Linear(hidden, n_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        seq, _h = self.gru(x)
        weights = torch.softmax(self.attn(seq), dim=1)
        return self.head(torch.sum(seq * weights, dim=1))


class _FTSequenceModule(nn.Module):
    def __init__(self, n_features: int, n_classes: int, hidden_dim: int) -> None:
        super().__init__()
        hidden = max(16, int(hidden_dim))
        self.value_proj = nn.Linear(3, hidden)
        self.feature_embedding = nn.Parameter(torch.randn(n_features, hidden) * 0.02)
        self.cls = nn.Parameter(torch.zeros(1, 1, hidden))
        n_heads = 4 if hidden % 4 == 0 else 2
        layer = nn.TransformerEncoderLayer(
            d_model=hidden,
            nhead=n_heads,
            dim_feedforward=hidden * 2,
            dropout=0.10,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.encoder = nn.TransformerEncoder(layer, num_layers=2)
        self.head = nn.Sequential(nn.LayerNorm(hidden), nn.Linear(hidden, n_classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        last = x[:, -1, :]
        mean = x.mean(dim=1)
        slope = x[:, -1, :] - x[:, 0, :]
        tokens = self.value_proj(torch.stack([last, mean, slope], dim=-1)) + self.feature_embedding.unsqueeze(0)
        cls = self.cls.expand(tokens.shape[0], -1, -1)
        encoded = self.encoder(torch.cat([cls, tokens], dim=1))
        return self.head(encoded[:, 0])


class _PatchTSTStyleSequenceModule(nn.Module):
    def __init__(self, n_features: int, n_classes: int, hidden_dim: int) -> None:
        super().__init__()
        hidden = max(16, int(hidden_dim))
        self.model_family = "patchtst_style_channel_independent_patch_transformer"
        self.patch_len = 8
        self.stride = 4
        self.patch_proj = nn.Sequential(
            nn.Linear(self.patch_len, hidden),
            nn.GELU(),
            nn.LayerNorm(hidden),
        )
        n_heads = 4 if hidden % 4 == 0 else 2
        if hidden % n_heads != 0:
            n_heads = 1
        layer = nn.TransformerEncoderLayer(
            d_model=hidden,
            nhead=n_heads,
            dim_feedforward=hidden * 2,
            dropout=0.10,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.encoder = nn.TransformerEncoder(layer, num_layers=2)
        self.channel_score = nn.Linear(hidden, 1)
        self.head = nn.Sequential(
            nn.LayerNorm(hidden * 2),
            nn.Linear(hidden * 2, hidden),
            nn.GELU(),
            nn.Linear(hidden, n_classes),
        )

    def _position_encoding(self, n_patches: int, hidden: int, device: torch.device) -> torch.Tensor:
        pos = torch.linspace(0.0, 1.0, steps=max(1, int(n_patches)), device=device).unsqueeze(1)
        freq = torch.arange(1, hidden + 1, device=device, dtype=pos.dtype).unsqueeze(0)
        return torch.sin(pos * freq).unsqueeze(0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch, steps, features = x.shape
        patch_len = min(int(self.patch_len), max(2, int(steps)))
        stride = max(1, min(int(self.stride), patch_len))
        if steps < self.patch_len:
            pad = x[:, :1, :].expand(batch, self.patch_len - steps, features)
            x = torch.cat([pad, x], dim=1)
            steps = x.shape[1]
            patch_len = self.patch_len
        patches = x.unfold(dimension=1, size=patch_len, step=stride)
        if patch_len < self.patch_len:
            pad_width = self.patch_len - patch_len
            patches = torch.nn.functional.pad(patches, (0, pad_width))
        # [B, patches, features, patch_len] -> [B * features, patches, patch_len]
        patches = patches.permute(0, 2, 1, 3).reshape(batch * features, patches.shape[1], self.patch_len)
        tokens = self.patch_proj(patches)
        tokens = tokens + self._position_encoding(tokens.shape[1], tokens.shape[2], tokens.device)
        encoded = self.encoder(tokens)
        channel_repr = encoded.mean(dim=1).reshape(batch, features, -1)
        weights = torch.softmax(self.channel_score(channel_repr), dim=1)
        weighted = torch.sum(channel_repr * weights, dim=1)
        pooled = torch.cat([weighted, channel_repr.mean(dim=1)], dim=1)
        return self.head(pooled)


class _AnomalyTransformerStyleSequenceModule(nn.Module):
    def __init__(self, n_features: int, n_classes: int, hidden_dim: int) -> None:
        super().__init__()
        hidden = max(16, int(hidden_dim))
        self.model_family = "anomaly_transformer_style_association_discrepancy"
        self.input_proj = nn.Linear(n_features, hidden)
        n_heads = 4 if hidden % 4 == 0 else 2
        if hidden % n_heads != 0:
            n_heads = 1
        self.series_attention = nn.MultiheadAttention(hidden, n_heads, dropout=0.10, batch_first=True)
        self.log_sigma = nn.Parameter(torch.tensor(0.0, dtype=torch.float32))
        self.ffn = nn.Sequential(
            nn.LayerNorm(hidden),
            nn.Linear(hidden, hidden * 2),
            nn.GELU(),
            nn.Linear(hidden * 2, hidden),
        )
        self.token_score = nn.Linear(hidden, 1)
        self.head = nn.Sequential(
            nn.LayerNorm(hidden * 2),
            nn.Linear(hidden * 2, hidden),
            nn.GELU(),
            nn.Linear(hidden, n_classes),
        )

    def _position_encoding(self, steps: int, hidden: int, device: torch.device) -> torch.Tensor:
        pos = torch.arange(max(1, int(steps)), device=device, dtype=torch.float32).unsqueeze(1)
        div = torch.exp(torch.arange(0, hidden, 2, device=device, dtype=torch.float32) * (-np.log(10000.0) / max(1, hidden)))
        pe = torch.zeros(max(1, int(steps)), hidden, device=device)
        pe[:, 0::2] = torch.sin(pos * div)
        pe[:, 1::2] = torch.cos(pos * div[: pe[:, 1::2].shape[1]])
        return pe.unsqueeze(0)

    def _prior_attention(self, steps: int, device: torch.device) -> torch.Tensor:
        idx = torch.arange(max(1, int(steps)), device=device, dtype=torch.float32)
        dist = torch.abs(idx[:, None] - idx[None, :])
        sigma = torch.nn.functional.softplus(self.log_sigma) + 1.0
        return torch.softmax(-(dist**2) / (2.0 * sigma * sigma), dim=-1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        tokens = self.input_proj(x)
        tokens = tokens + self._position_encoding(tokens.shape[1], tokens.shape[2], tokens.device)
        series, attn = self.series_attention(tokens, tokens, tokens, need_weights=True, average_attn_weights=False)
        series = series + self.ffn(series)
        prior = self._prior_attention(tokens.shape[1], tokens.device).unsqueeze(0)
        series_assoc = attn.mean(dim=1)
        discrepancy = torch.abs(series_assoc - prior).mean(dim=-1)
        weights = torch.softmax(self.token_score(series).squeeze(-1) + discrepancy, dim=1)
        focused = torch.sum(series * weights.unsqueeze(-1), dim=1)
        pooled = torch.cat([focused, series.mean(dim=1)], dim=1)
        return self.head(pooled)


class _GraphWaveNetStyleSequenceModule(nn.Module):
    def __init__(self, n_features: int, n_classes: int, hidden_dim: int) -> None:
        super().__init__()
        hidden = max(16, int(hidden_dim))
        self.model_family = "graph_wavenet_style_adaptive_dilated_graph_temporal"
        self.graph_wavenet_adaptive_adjacency_shape = [int(n_features), int(n_features)]
        self.input_proj = nn.Conv2d(1, hidden, kernel_size=(1, 1))
        self.nodevec1 = nn.Parameter(torch.randn(n_features, hidden) * 0.02)
        self.nodevec2 = nn.Parameter(torch.randn(hidden, n_features) * 0.02)
        dilations = [1, 2, 4]
        self.filter_convs = nn.ModuleList()
        self.gate_convs = nn.ModuleList()
        self.graph_convs = nn.ModuleList()
        self.norms = nn.ModuleList()
        for dilation in dilations:
            self.filter_convs.append(nn.Conv2d(hidden, hidden, kernel_size=(1, 2), dilation=(1, dilation), padding=(0, dilation)))
            self.gate_convs.append(nn.Conv2d(hidden, hidden, kernel_size=(1, 2), dilation=(1, dilation), padding=(0, dilation)))
            self.graph_convs.append(nn.Conv2d(hidden, hidden, kernel_size=(1, 1)))
            self.norms.append(nn.BatchNorm2d(hidden))
        self.head = nn.Sequential(
            nn.LayerNorm(hidden * 2),
            nn.Linear(hidden * 2, hidden),
            nn.GELU(),
            nn.Linear(hidden, n_classes),
        )

    def _adaptive_adjacency(self) -> torch.Tensor:
        score = torch.relu(torch.matmul(self.nodevec1, self.nodevec2))
        score = score.masked_fill(torch.eye(score.shape[0], dtype=torch.bool, device=score.device), 0.0)
        return torch.softmax(score, dim=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = self.input_proj(x.transpose(1, 2).unsqueeze(1))
        skip: torch.Tensor | None = None
        adjacency = self._adaptive_adjacency()
        for filter_conv, gate_conv, graph_conv, norm in zip(self.filter_convs, self.gate_convs, self.graph_convs, self.norms):
            residual = h
            gated = torch.tanh(filter_conv(h)) * torch.sigmoid(gate_conv(h))
            if gated.shape[-1] > residual.shape[-1]:
                gated = gated[..., -residual.shape[-1] :]
            residual = residual[..., -gated.shape[-1] :]
            neighbor = torch.einsum("bcnt,nm->bcmt", gated, adjacency)
            h = norm(residual + gated + graph_conv(neighbor))
            pooled_step = h.mean(dim=-1)
            skip = pooled_step if skip is None else skip + pooled_step
        node_context = h.mean(dim=-1).mean(dim=2)
        skip_context = skip.mean(dim=2) if skip is not None else node_context
        return self.head(torch.cat([node_context, skip_context], dim=1))


class _GDNStyleSequenceModule(nn.Module):
    def __init__(self, n_features: int, n_classes: int, hidden_dim: int) -> None:
        super().__init__()
        hidden = max(16, int(hidden_dim))
        self.model_family = "gdn_style_sequence_graph"
        self.gdn_top_k = max(1, min(8, int(np.sqrt(max(1, n_features))) + 1, max(1, n_features - 1)))
        self.gdn_adjacency_shape = [int(n_features), int(n_features)]
        self.value_proj = nn.Sequential(
            nn.Linear(4, hidden),
            nn.GELU(),
            nn.LayerNorm(hidden),
        )
        self.node_embedding = nn.Parameter(torch.randn(n_features, hidden) * 0.02)
        self.head = nn.Sequential(
            nn.LayerNorm(hidden * 3),
            nn.Linear(hidden * 3, hidden),
            nn.GELU(),
            nn.Linear(hidden, n_classes),
        )

    def _learned_adjacency(self) -> torch.Tensor:
        emb = torch.nn.functional.normalize(self.node_embedding, dim=1)
        score = torch.matmul(emb, emb.transpose(0, 1))
        score = score.masked_fill(torch.eye(score.shape[0], dtype=torch.bool, device=score.device), -1e9)
        k = max(1, min(int(self.gdn_top_k), score.shape[1] - 1))
        top_values, top_idx = torch.topk(score, k=k, dim=1)
        sparse = torch.full_like(score, -1e9)
        sparse.scatter_(1, top_idx, top_values)
        return torch.softmax(sparse, dim=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        last = x[:, -1, :]
        mean = x.mean(dim=1)
        std = x.std(dim=1, unbiased=False)
        slope = x[:, -1, :] - x[:, 0, :]
        node = self.value_proj(torch.stack([last, mean, std, slope], dim=-1)) + self.node_embedding.unsqueeze(0)
        adjacency = self._learned_adjacency()
        neighbor = torch.einsum("ij,bjd->bid", adjacency, node)
        pooled = torch.cat([node, neighbor, node - neighbor], dim=-1).mean(dim=1)
        return self.head(pooled)


class _MTADGATStyleSequenceModule(nn.Module):
    def __init__(self, n_features: int, n_classes: int, hidden_dim: int) -> None:
        super().__init__()
        hidden = max(16, int(hidden_dim))
        self.model_family = "mtad_gat_style_temporal_feature_attention"
        self.gru = nn.GRU(n_features, hidden, num_layers=1, batch_first=True, bidirectional=True)
        self.temporal_attn = nn.Linear(hidden * 2, 1)
        self.temporal_proj = nn.Linear(hidden * 2, hidden)
        self.value_proj = nn.Linear(3, hidden)
        self.feature_embedding = nn.Parameter(torch.randn(n_features, hidden) * 0.02)
        n_heads = 4 if hidden % 4 == 0 else 2
        self.feature_attn = nn.MultiheadAttention(hidden, n_heads, dropout=0.10, batch_first=True)
        self.fusion_gate = nn.Sequential(nn.Linear(hidden * 2, hidden), nn.GELU(), nn.Linear(hidden, hidden))
        self.head = nn.Sequential(
            nn.LayerNorm(hidden),
            nn.Linear(hidden, hidden),
            nn.GELU(),
            nn.Linear(hidden, n_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        seq, _h = self.gru(x)
        weights = torch.softmax(self.temporal_attn(seq), dim=1)
        temporal = self.temporal_proj(torch.sum(seq * weights, dim=1))
        last = x[:, -1, :]
        mean = x.mean(dim=1)
        slope = x[:, -1, :] - x[:, 0, :]
        tokens = self.value_proj(torch.stack([last, mean, slope], dim=-1)) + self.feature_embedding.unsqueeze(0)
        feature_tokens, _attn = self.feature_attn(tokens, tokens, tokens, need_weights=False)
        feature_context = feature_tokens.mean(dim=1)
        gate = torch.sigmoid(self.fusion_gate(torch.cat([temporal, feature_context], dim=1)))
        fused = gate * temporal + (1.0 - gate) * feature_context
        return self.head(fused)


class _NormalDynamicsForecaster(nn.Module):
    def __init__(self, n_features: int, hidden_dim: int) -> None:
        super().__init__()
        hidden = max(16, int(hidden_dim))
        self.gru = nn.GRU(n_features, hidden, num_layers=1, batch_first=True, bidirectional=True)
        self.decoder = nn.Sequential(
            nn.LayerNorm(hidden * 2),
            nn.Linear(hidden * 2, hidden),
            nn.GELU(),
            nn.Linear(hidden, n_features),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        _seq, h = self.gru(x)
        context = torch.cat([h[-2], h[-1]], dim=1)
        return self.decoder(context)


class _ResidualGatedSequenceModule(nn.Module):
    def __init__(
        self,
        model_name: str,
        *,
        base_features: int,
        residual_features: int,
        n_classes: int,
        hidden_dim: int,
        gate_init: float = -3.0,
    ) -> None:
        super().__init__()
        self.model_family = f"{_normalise_model_name(model_name)}_residual_gated_lagged_graph"
        self.base_features = int(base_features)
        self.residual_features = int(residual_features)
        self.base_model = _build_sequence_module(model_name, base_features, n_classes, hidden_dim)
        self.residual_model = _build_sequence_module(model_name, residual_features, n_classes, hidden_dim)
        self.graph_gate_logit = nn.Parameter(torch.tensor(float(gate_init), dtype=torch.float32))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        base = x[:, :, : self.base_features]
        residual = x[:, :, self.base_features : self.base_features + self.residual_features]
        return self.base_model(base) + torch.sigmoid(self.graph_gate_logit) * self.residual_model(residual)


def _normalise_model_name(model_name: str) -> str:
    return str(model_name).strip().lower().replace("-", "_")


def _build_sequence_module(model_name: str, n_features: int, n_classes: int, hidden_dim: int) -> nn.Module:
    name = _normalise_model_name(model_name)
    if name == "tcn":
        model = _TCNSequenceModule(n_features, n_classes, hidden_dim)
        setattr(model, "model_family", "tcn_temporal_convolution")
        return model
    if name in {"gru", "temporal_gru"}:
        model = _GRUSequenceModule(n_features, n_classes, hidden_dim)
        setattr(model, "model_family", "bidirectional_gru_attention")
        return model
    if name in {"ft", "ft_transformer", "fttransformer"}:
        model = _FTSequenceModule(n_features, n_classes, hidden_dim)
        setattr(model, "model_family", "ft_transformer_feature_attention")
        return model
    if name in {"patchtst", "patch_tst", "patch-tst"}:
        return _PatchTSTStyleSequenceModule(n_features, n_classes, hidden_dim)
    if name in {"anomaly_transformer", "anomalytransformer", "anomaly-transformer"}:
        return _AnomalyTransformerStyleSequenceModule(n_features, n_classes, hidden_dim)
    if name in {"graph_wavenet", "graphwavenet", "graph-wavenet", "gwnet"}:
        return _GraphWaveNetStyleSequenceModule(n_features, n_classes, hidden_dim)
    if name in {"gdn", "gdn_style"}:
        return _GDNStyleSequenceModule(n_features, n_classes, hidden_dim)
    if name in {"mtad_gat", "mtadgat", "mtad-gat"}:
        return _MTADGATStyleSequenceModule(n_features, n_classes, hidden_dim)
    raise ValueError(f"Unknown sequence model: {model_name}")


def _class_weights(y: np.ndarray, n_classes: int) -> torch.Tensor:
    counts = np.bincount(y.astype(int), minlength=n_classes).astype(np.float64)
    present = counts[counts > 0]
    mean_count = float(np.mean(present)) if present.size else 1.0
    weights = np.ones(n_classes, dtype=np.float32)
    for i, count in enumerate(counts):
        if count > 0:
            weights[i] = float(np.sqrt(mean_count / count))
    return torch.from_numpy(weights)


def _resolve_device(device: str | torch.device | None) -> torch.device:
    raw = "auto" if device is None else str(device)
    if raw == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if raw.startswith("cuda") and not torch.cuda.is_available():
        return torch.device("cpu")
    return torch.device(raw)


def _append_normal_residual_features(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray,
    x_test: np.ndarray,
    *,
    hidden_dim: int,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    seed: int,
    device: torch.device,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    normal_idx_np = np.flatnonzero(np.asarray(y_train, dtype=np.int64) == 0)
    if normal_idx_np.size == 0 or int(epochs) <= 0:
        return x_train, x_val, x_test, {
            "normal_residual_features_enabled": False,
            "reason": "disabled_or_no_normal_training_rows",
            "normal_pretrain_loss_tail": [],
        }

    rng = np.random.default_rng(int(seed) + 17)
    forecaster = _NormalDynamicsForecaster(x_train.shape[2], hidden_dim).to(device)
    opt = torch.optim.AdamW(forecaster.parameters(), lr=float(learning_rate), weight_decay=1e-4)
    loss_fn = nn.MSELoss()
    x_t = torch.from_numpy(np.asarray(x_train, dtype=np.float32)).to(device)
    batch = max(8, min(int(batch_size), int(normal_idx_np.size)))
    losses: list[float] = []
    forecaster.train()
    for _epoch in range(max(1, int(epochs))):
        order = rng.permutation(normal_idx_np)
        epoch_loss: list[float] = []
        for start in range(0, len(order), batch):
            idx = torch.from_numpy(order[start : start + batch].astype(np.int64)).to(device)
            source = x_t[idx]
            masked = source.clone()
            target = source[:, -1, :]
            masked[:, -1, :] = 0.0
            opt.zero_grad()
            loss = loss_fn(forecaster(masked), target)
            loss.backward()
            opt.step()
            epoch_loss.append(float(loss.detach().cpu().item()))
        losses.append(float(np.mean(epoch_loss)) if epoch_loss else 0.0)

    def _residual_features(arr: np.ndarray) -> np.ndarray:
        x_all = torch.from_numpy(np.asarray(arr, dtype=np.float32)).to(device)
        chunks: list[np.ndarray] = []
        step = max(16, int(batch_size))
        forecaster.eval()
        with torch.no_grad():
            for start in range(0, len(x_all), step):
                source = x_all[start : start + step]
                masked = source.clone()
                target = source[:, -1, :]
                masked[:, -1, :] = 0.0
                residual = torch.abs(target - forecaster(masked)).detach().cpu().numpy()
                chunks.append(residual.astype(np.float32))
        return np.repeat(np.vstack(chunks)[:, None, :], arr.shape[1], axis=1).astype(np.float32)

    train_resid = _residual_features(x_train)
    resid_mean = train_resid.mean(axis=(0, 1), keepdims=True)
    resid_std = train_resid.std(axis=(0, 1), keepdims=True) + 1e-6

    def _augment(arr: np.ndarray) -> np.ndarray:
        resid = (_residual_features(arr) - resid_mean) / resid_std
        resid = np.nan_to_num(resid, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)
        return np.concatenate([arr.astype(np.float32), resid], axis=2).astype(np.float32)

    return _augment(x_train), _augment(x_val), _augment(x_test), {
        "normal_residual_features_enabled": True,
        "normal_rows": int(normal_idx_np.size),
        "original_n_features": int(x_train.shape[2]),
        "augmented_n_features": int(x_train.shape[2] * 2),
        "normal_pretrain_loss_tail": losses[-5:],
    }


def train_sequence_model(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray,
    x_test: np.ndarray,
    *,
    model_name: str,
    n_classes: int,
    hidden_dim: int = 64,
    epochs: int = 20,
    batch_size: int = 512,
    learning_rate: float = 0.001,
    seed: int = 42,
    device: str | torch.device | None = "auto",
    graph_adjacency: np.ndarray | None = None,
    graph_strength: float = 0.0,
    lagged_graph_fusion_mode: str = "direct_filter",
    normal_residual_features: bool = False,
    normal_pretrain_epochs: int = 0,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    torch.manual_seed(int(seed))
    actual_device = _resolve_device(device)
    if actual_device.type == "cpu":
        torch.set_num_threads(1)
    mode = str(lagged_graph_fusion_mode or "direct_filter").strip().lower()
    graph_alpha = max(0.0, min(1.0, float(graph_strength)))
    graph_diag: dict[str, Any] = {
        "graph_strength": float(graph_alpha),
        "lagged_graph_fusion_mode": mode,
    }
    base_train = np.asarray(x_train, dtype=np.float32)
    base_val = np.asarray(x_val, dtype=np.float32)
    base_test = np.asarray(x_test, dtype=np.float32)
    residual_train: np.ndarray | None = None
    residual_val: np.ndarray | None = None
    residual_test: np.ndarray | None = None
    residual_diag: dict[str, Any] = {"residual_channel_enabled": False}

    if graph_adjacency is not None and graph_alpha > 0.0:
        if mode in {"residual_channel", "residual_gated", "gate_residual"}:
            residual_train, residual_val, residual_test, residual_diag = _standardized_lagged_graph_residuals(
                base_train,
                base_val,
                base_test,
                graph_adjacency,
                strength=graph_alpha,
            )
        else:
            base_train = apply_graph_filter_to_windows(base_train, graph_adjacency, strength=graph_alpha)
            base_val = apply_graph_filter_to_windows(base_val, graph_adjacency, strength=graph_alpha)
            base_test = apply_graph_filter_to_windows(base_test, graph_adjacency, strength=graph_alpha)
    graph_diag.update(residual_diag)

    residual_feature_diag: dict[str, Any]
    if bool(normal_residual_features):
        base_train, base_val, base_test, residual_feature_diag = _append_normal_residual_features(
            base_train,
            y_train,
            base_val,
            base_test,
            hidden_dim=hidden_dim,
            epochs=int(normal_pretrain_epochs),
            batch_size=batch_size,
            learning_rate=learning_rate,
            seed=seed,
            device=actual_device,
        )
    else:
        residual_feature_diag = {
            "normal_residual_features_enabled": False,
            "normal_pretrain_loss_tail": [],
        }

    if residual_train is not None and residual_val is not None and residual_test is not None:
        model = _ResidualGatedSequenceModule(
            model_name,
            base_features=base_train.shape[2],
            residual_features=residual_train.shape[2],
            n_classes=n_classes,
            hidden_dim=hidden_dim,
        )
        train_input = np.concatenate([base_train, residual_train], axis=2).astype(np.float32)
        val_input = np.concatenate([base_val, residual_val], axis=2).astype(np.float32)
        test_input = np.concatenate([base_test, residual_test], axis=2).astype(np.float32)
    else:
        model = _build_sequence_module(model_name, base_train.shape[2], n_classes, hidden_dim)
        train_input = base_train
        val_input = base_val
        test_input = base_test

    model = model.to(actual_device)
    parameters = int(sum(p.numel() for p in model.parameters() if p.requires_grad))
    opt = torch.optim.AdamW(model.parameters(), lr=float(learning_rate), weight_decay=1e-4)
    loss_fn = nn.CrossEntropyLoss(weight=_class_weights(y_train, n_classes).to(actual_device))
    x_t = torch.from_numpy(np.asarray(train_input, dtype=np.float32)).to(actual_device)
    y_t = torch.from_numpy(np.asarray(y_train, dtype=np.int64)).to(actual_device)
    rng = np.random.default_rng(int(seed))
    losses: list[float] = []
    batch = max(16, min(int(batch_size), len(y_train)))
    train_started = time.perf_counter()
    model.train()
    for _epoch in range(max(1, int(epochs))):
        order = rng.permutation(len(y_train))
        epoch_loss: list[float] = []
        for start in range(0, len(order), batch):
            idx = torch.from_numpy(order[start : start + batch].astype(np.int64)).to(actual_device)
            opt.zero_grad()
            loss = loss_fn(model(x_t[idx]), y_t[idx])
            loss.backward()
            opt.step()
            epoch_loss.append(float(loss.detach().cpu().item()))
        losses.append(float(np.mean(epoch_loss)) if epoch_loss else 0.0)
    train_seconds = max(time.perf_counter() - train_started, 1e-12)

    def _predict(x_arr: np.ndarray) -> np.ndarray:
        model.eval()
        chunks: list[np.ndarray] = []
        x_all = torch.from_numpy(np.asarray(x_arr, dtype=np.float32)).to(actual_device)
        with torch.no_grad():
            for start in range(0, len(x_all), batch):
                logits = model(x_all[start : start + batch])
                chunks.append(torch.softmax(logits, dim=1).cpu().numpy())
        return np.vstack(chunks).astype(np.float64)

    val_proba = _predict(val_input)
    test_started = time.perf_counter()
    test_proba = _predict(test_input)
    test_inference_seconds = max(time.perf_counter() - test_started, 1e-12)

    diagnostics: dict[str, Any] = {
        "loss_tail": losses[-5:],
        "epochs": int(epochs),
        "device": str(actual_device),
        "model_family": str(getattr(model, "model_family", getattr(getattr(model, "base_model", None), "model_family", model_name))),
        "input_features": int(train_input.shape[2]),
        "parameters": int(parameters),
        "train_seconds": float(train_seconds),
        "train_samples_per_second": float((len(y_train) * max(1, int(epochs))) / train_seconds),
        "test_inference_seconds": float(test_inference_seconds),
        "test_inference_samples_per_second": float(len(test_input) / test_inference_seconds) if len(test_input) else 0.0,
        **graph_diag,
        **residual_feature_diag,
    }
    if hasattr(model, "graph_gate_logit"):
        diagnostics["residual_graph_gate"] = float(torch.sigmoid(model.graph_gate_logit.detach()).cpu().item())
    for attr in ("gdn_adjacency_shape", "gdn_top_k", "graph_wavenet_adaptive_adjacency_shape"):
        value = getattr(model, attr, None)
        if value is None and hasattr(model, "base_model"):
            value = getattr(model.base_model, attr, None)
        if value is not None:
            diagnostics[attr] = value

    return val_proba, test_proba, diagnostics


def _apply_optional_weak_rerank(
    y_val: np.ndarray,
    val_proba: np.ndarray,
    test_proba: np.ndarray,
    class_names: Sequence[str],
) -> tuple[np.ndarray, dict[str, Any]]:
    weak = [
        "reaction_kinetics",
        "stream_4_valve_fixed",
        "condenser_cooling_water_inlet_temperature_random_variation",
        "reactor_cooling_water_valve",
        "unknown_fault_16",
        "unknown_fault_17",
    ]
    tuning = tune_weak_class_biases_on_validation(
        y_val,
        val_proba,
        class_names=class_names,
        weak_class_names=weak,
        bias_grid=[0.0, 0.2, 0.4, 0.6, 0.8],
    )
    biases = dict(tuning.get("selected_bias_by_class_id", {}) or {})
    if biases:
        return apply_class_logit_biases(test_proba, biases), {**tuning, "applied": True}
    return test_proba, {**tuning, "applied": False}


def _add_target_defect_macro_f1(sample_metrics: dict[str, Any], class_names: Sequence[str]) -> None:
    per_class = sample_metrics.get("per_class", {}) or {}
    values: list[float] = []
    for class_id, class_name in enumerate(class_names):
        if int(class_id) == int(sample_metrics.get("normal_class_id", 0)):
            continue
        row = per_class.get(str(class_name), {}) or {}
        if int(row.get("support", 0) or 0) > 0:
            values.append(float(row.get("f1", 0.0) or 0.0))
    sample_metrics["target_defect_macro_f1"] = float(np.mean(values)) if values else None


def run_sequence_head_experiment(
    *,
    dataset_dir: Path,
    output_path: Path,
    max_rows: int | None,
    model_name: str,
    window_size: int,
    hidden_dim: int,
    epochs: int,
    batch_size: int,
    seed: int,
    apply_llm_rerank: bool,
    device: str | torch.device | None = "auto",
    normal_pretrain_epochs: int = 0,
    normal_residual_features: bool = False,
    graph_strength: float = 0.0,
    graph_prior_name: str = "tep_expert_llm_graph_prior.json",
    use_lagged_graph: bool = False,
    graph_reliability_threshold: float = 0.0,
    graph_max_edges: int | None = None,
    lagged_graph_fusion_mode: str = "direct_filter",
) -> dict[str, Any]:
    class_ids, class_names = load_class_mapping(dataset_dir)
    split = prepare_sequence_split(
        dataset_dir,
        max_rows=max_rows,
        sample_mode="stratified",
        seed=seed,
        window_size=window_size,
    )
    graph_adjacency: np.ndarray | None = None
    graph_constraint: dict[str, Any] = {"enabled": False}
    if bool(use_lagged_graph) and float(graph_strength) > 0.0:
        graph_adjacency, graph_constraint = load_graph_adjacency(
            dataset_dir,
            split.feature_cols,
            prior_name=graph_prior_name,
            reliability_threshold=graph_reliability_threshold,
            max_edges=graph_max_edges,
        )
        graph_constraint = {
            **graph_constraint,
            "strength": float(graph_strength),
            "fusion_mode": str(lagged_graph_fusion_mode),
        }
    val_proba, test_proba, train_diag = train_sequence_model(
        split.x_train,
        split.y_train,
        split.x_val,
        split.x_test,
        model_name=model_name,
        n_classes=len(class_ids),
        hidden_dim=hidden_dim,
        epochs=epochs,
        batch_size=batch_size,
        seed=seed,
        device=device,
        graph_adjacency=graph_adjacency,
        graph_strength=float(graph_strength),
        lagged_graph_fusion_mode=lagged_graph_fusion_mode,
        normal_residual_features=bool(normal_residual_features),
        normal_pretrain_epochs=int(normal_pretrain_epochs),
    )
    weak_tuning: dict[str, Any] = {"enabled": False}
    final_proba = test_proba
    if bool(apply_llm_rerank):
        final_proba, weak_tuning = _apply_optional_weak_rerank(split.y_val, val_proba, test_proba, class_names)
    # Re-load y_meta for event ids/horizons after the same max_rows sampling.
    _x, y_meta, _labels = load_multiclass_dataset(
        dataset_dir,
        max_rows=max_rows,
        sample_mode="stratified",
        seed=seed,
        feature_set="raw",
    )
    event_ids = (
        y_meta.iloc[split.idx_test]["event_bag_id"].astype(str).to_numpy(dtype=object)
        if "event_bag_id" in y_meta.columns
        else build_event_ids(split.y_test)
    )
    horizons = (
        pd.to_numeric(y_meta.iloc[split.idx_test]["lead_horizon_min"], errors="coerce").fillna(-1.0).to_numpy(dtype=float)
        if "lead_horizon_min" in y_meta.columns
        else build_event_horizons(split.y_test)
    )
    evaluation = summarize_multiclass_event_evaluation(
        split.y_test,
        final_proba,
        class_names=class_names,
        event_ids=event_ids,
        horizons=horizons,
        top_paths_by_class={},
    )
    _add_target_defect_macro_f1(evaluation["sample_multiclass_metrics"], class_names)
    result = {
        "status": "ok",
        "model_name": str(model_name),
        "protocol": "metadata_split_role_strict_sequence_windows",
        "n_rows": int(len(_labels)),
        "window_size": int(window_size),
        "n_features": int(len(split.feature_cols)),
        "hidden_dim": int(hidden_dim),
        "epochs": int(epochs),
        "train_diagnostics": train_diag,
        "graph_constraint": graph_constraint,
        "llm_weak_rerank": weak_tuning,
        "sample_multiclass_metrics": evaluation["sample_multiclass_metrics"],
        "event_warning_metrics": evaluation["event_warning_metrics"],
        "path_explanation_metrics": evaluation["path_explanation_metrics"],
    }
    output_io = _fs_path(output_path)
    output_io.parent.mkdir(parents=True, exist_ok=True)
    output_io.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run strict TEP sequence-head replacements for tree models.")
    parser.add_argument("--dataset-dir", type=str, default=str(DEFAULT_TEP_DATASET_DIR))
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--model", type=str, choices=["tcn", "gru", "ft_transformer", "patchtst", "anomaly_transformer", "graph_wavenet", "gdn", "mtad_gat"], required=True)
    parser.add_argument("--max-rows", type=int, default=5000)
    parser.add_argument("--window-size", type=int, default=32)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", type=str, default="auto")
    parser.add_argument("--apply-llm-rerank", action="store_true")
    parser.add_argument("--normal-pretrain-epochs", type=int, default=0)
    parser.add_argument("--normal-residual-features", action="store_true")
    parser.add_argument("--graph-strength", type=float, default=0.0)
    parser.add_argument("--graph-prior", type=str, default="tep_expert_llm_graph_prior.json")
    parser.add_argument("--use-lagged-graph", action="store_true")
    parser.add_argument("--graph-reliability-threshold", type=float, default=0.0)
    parser.add_argument("--graph-max-edges", type=int, default=0)
    parser.add_argument("--lagged-graph-fusion-mode", type=str, default="direct_filter", choices=["direct_filter", "residual_channel"])
    args = parser.parse_args()
    result = run_sequence_head_experiment(
        dataset_dir=Path(args.dataset_dir),
        output_path=Path(args.output),
        max_rows=int(args.max_rows) if int(args.max_rows) > 0 else None,
        model_name=str(args.model),
        window_size=int(args.window_size),
        hidden_dim=int(args.hidden_dim),
        epochs=int(args.epochs),
        batch_size=int(args.batch_size),
        seed=int(args.seed),
        device=str(args.device),
        apply_llm_rerank=bool(args.apply_llm_rerank),
        normal_pretrain_epochs=int(args.normal_pretrain_epochs),
        normal_residual_features=bool(args.normal_residual_features),
        graph_strength=float(args.graph_strength),
        graph_prior_name=str(args.graph_prior),
        use_lagged_graph=bool(args.use_lagged_graph),
        graph_reliability_threshold=float(args.graph_reliability_threshold),
        graph_max_edges=int(args.graph_max_edges) if int(args.graph_max_edges) > 0 else None,
        lagged_graph_fusion_mode=str(args.lagged_graph_fusion_mode),
    )
    sample = result["sample_multiclass_metrics"]
    event = result["event_warning_metrics"]
    print(
        f"{result['model_name']}: macro_f1={sample.get('macro_f1')}, "
        f"target_f1={sample.get('target_defect_macro_f1')}, "
        f"event_macro_recall={event.get('event_macro_recall')}"
    )


if __name__ == "__main__":
    main()
