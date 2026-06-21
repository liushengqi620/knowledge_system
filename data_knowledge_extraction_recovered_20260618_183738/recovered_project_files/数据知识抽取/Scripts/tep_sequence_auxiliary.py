from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler


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
        for pos, row_idx in enumerate(group_idx):
            start = max(0, pos - w + 1)
            segment = group_values[start : pos + 1]
            if len(segment) < w:
                pad = np.repeat(segment[:1], w - len(segment), axis=0)
                segment = np.vstack([pad, segment])
            out[int(row_idx)] = segment[-w:]
    return out


def load_graph_adjacency(
    dataset_dir: Path,
    feature_cols: Sequence[str],
    *,
    prior_name: str = "tep_expert_llm_graph_prior.json",
) -> tuple[np.ndarray, dict[str, Any]]:
    cols = [str(c) for c in feature_cols]
    index = {name: i for i, name in enumerate(cols)}
    adjacency = np.zeros((len(cols), len(cols)), dtype=np.float32)
    path = Path(dataset_dir) / str(prior_name)
    if not path.exists():
        return adjacency, {"status": "missing", "path": str(path), "matched_edges": 0}
    payload = json.loads(path.read_text(encoding="utf-8"))
    matched = 0
    for edge in payload.get("edges", []) or []:
        src = str(edge.get("from", ""))
        dst = str(edge.get("to", ""))
        if src not in index or dst not in index:
            continue
        weight = float(edge.get("weight", 1.0) or 0.0)
        confidence = float(edge.get("confidence", 1.0) or 1.0)
        score = max(0.0, min(1.0, weight * confidence))
        if score <= 0.0:
            continue
        adjacency[index[src], index[dst]] = max(float(adjacency[index[src], index[dst]]), score)
        matched += 1
    return adjacency, {"status": "ok", "path": str(path), "matched_edges": int(matched), "n_features": int(len(cols))}


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
    graph = np.asarray(adjacency, dtype=np.float32)
    if graph.ndim != 2 or graph.shape[0] != arr.shape[2] or graph.shape[1] != arr.shape[2]:
        raise ValueError("Graph adjacency shape must match the sequence feature dimension.")
    col_sum = graph.sum(axis=0, keepdims=True)
    active = (col_sum.reshape(-1) > 1e-12).astype(np.float32)
    normalized = np.divide(graph, np.maximum(col_sum, 1e-12), out=np.zeros_like(graph), where=col_sum > 1e-12)
    neighbor = np.einsum("btf,fg->btg", arr, normalized, optimize=True).astype(np.float32)
    mask = active.reshape(1, 1, -1)
    return (arr * (1.0 - alpha * mask) + neighbor * (alpha * mask)).astype(np.float32)


class _GRUSequenceModule(nn.Module):
    def __init__(self, n_features: int, n_classes: int, hidden_dim: int) -> None:
        super().__init__()
        hidden = max(16, int(hidden_dim))
        self.encoder_dim = hidden * 2
        self.gru = nn.GRU(n_features, hidden, num_layers=1, batch_first=True, bidirectional=True)
        self.attn = nn.Linear(hidden * 2, 1)
        self.head = nn.Sequential(
            nn.LayerNorm(hidden * 2),
            nn.Linear(hidden * 2, hidden),
            nn.GELU(),
            nn.Linear(hidden, n_classes),
        )

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        seq, _h = self.gru(x)
        weights = torch.softmax(self.attn(seq), dim=1)
        return torch.sum(seq * weights, dim=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.head(self.encode(x))


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


def _class_weights(y: np.ndarray, n_classes: int) -> torch.Tensor:
    counts = np.bincount(y.astype(int), minlength=n_classes).astype(np.float64)
    present = counts[counts > 0]
    mean_count = float(np.mean(present)) if present.size else 1.0
    weights = np.ones(n_classes, dtype=np.float32)
    for i, count in enumerate(counts):
        if count > 0:
            weights[i] = float(np.sqrt(mean_count / count))
    return torch.from_numpy(weights)


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
    graph_adjacency: np.ndarray | None,
    graph_strength: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[float], dict[str, Any]]:
    normal_idx_np = np.flatnonzero(np.asarray(y_train, dtype=np.int64) == 0)
    if normal_idx_np.size == 0:
        return x_train, x_val, x_test, [], {"normal_residual_features_enabled": False, "reason": "no_normal_training_rows"}
    rng = np.random.default_rng(int(seed) + 17)
    forecaster = _NormalDynamicsForecaster(x_train.shape[2], hidden_dim)
    opt = torch.optim.AdamW(forecaster.parameters(), lr=float(learning_rate), weight_decay=1e-4)
    loss_fn = nn.MSELoss()
    x_t = torch.from_numpy(np.asarray(x_train, dtype=np.float32))
    batch = max(8, min(int(batch_size), int(normal_idx_np.size)))
    losses: list[float] = []
    forecaster.train()
    for _epoch in range(max(1, int(epochs))):
        order = rng.permutation(normal_idx_np)
        epoch_loss: list[float] = []
        for start in range(0, len(order), batch):
            idx = torch.from_numpy(order[start : start + batch].astype(np.int64))
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
        x_all = torch.from_numpy(np.asarray(arr, dtype=np.float32))
        chunks: list[np.ndarray] = []
        forecaster.eval()
        with torch.no_grad():
            for start in range(0, len(x_all), max(16, int(batch_size))):
                source = x_all[start : start + max(16, int(batch_size))]
                masked = source.clone()
                target = source[:, -1, :]
                masked[:, -1, :] = 0.0
                residual = torch.abs(target - forecaster(masked)).cpu().numpy()
                chunks.append(residual.astype(np.float32))
        residuals = np.vstack(chunks).astype(np.float32)
        if graph_adjacency is not None and float(graph_strength) > 0.0:
            residuals = apply_graph_filter_to_windows(
                residuals[:, None, :],
                graph_adjacency,
                strength=graph_strength,
            )[:, 0, :]
        return np.repeat(residuals[:, None, :], arr.shape[1], axis=1).astype(np.float32)

    train_resid = _residual_features(x_train)
    resid_mean = train_resid.mean(axis=(0, 1), keepdims=True)
    resid_std = train_resid.std(axis=(0, 1), keepdims=True) + 1e-6

    def _augment(arr: np.ndarray) -> np.ndarray:
        resid = (_residual_features(arr) - resid_mean) / resid_std
        resid = np.nan_to_num(resid, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)
        return np.concatenate([arr.astype(np.float32), resid], axis=2).astype(np.float32)

    diagnostics = {
        "normal_residual_features_enabled": True,
        "original_n_features": int(x_train.shape[2]),
        "augmented_n_features": int(x_train.shape[2] * 2),
        "normal_rows": int(normal_idx_np.size),
    }
    return _augment(x_train), _augment(x_val), _augment(x_test), losses, diagnostics


def _train_gru_sequence_model(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray,
    x_test: np.ndarray,
    *,
    n_classes: int,
    hidden_dim: int,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    seed: int,
    pretrain_epochs: int,
    graph_adjacency: np.ndarray | None,
    graph_strength: float,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    torch.manual_seed(int(seed))
    torch.set_num_threads(1)
    if graph_adjacency is not None and float(graph_strength) > 0.0:
        x_train = apply_graph_filter_to_windows(x_train, graph_adjacency, strength=graph_strength)
        x_val = apply_graph_filter_to_windows(x_val, graph_adjacency, strength=graph_strength)
        x_test = apply_graph_filter_to_windows(x_test, graph_adjacency, strength=graph_strength)
    x_train, x_val, x_test, pretrain_losses, residual_diag = _append_normal_residual_features(
        x_train,
        y_train,
        x_val,
        x_test,
        hidden_dim=hidden_dim,
        epochs=pretrain_epochs,
        batch_size=batch_size,
        learning_rate=learning_rate,
        seed=seed,
        graph_adjacency=graph_adjacency,
        graph_strength=graph_strength,
    )
    model = _GRUSequenceModule(x_train.shape[2], n_classes, hidden_dim)
    opt = torch.optim.AdamW(model.parameters(), lr=float(learning_rate), weight_decay=1e-4)
    loss_fn = nn.CrossEntropyLoss(weight=_class_weights(y_train, n_classes))
    x_t = torch.from_numpy(np.asarray(x_train, dtype=np.float32))
    y_t = torch.from_numpy(np.asarray(y_train, dtype=np.int64))
    rng = np.random.default_rng(int(seed))
    batch = max(16, min(int(batch_size), len(y_train)))
    losses: list[float] = []
    model.train()
    for _epoch in range(max(1, int(epochs))):
        order = rng.permutation(len(y_train))
        epoch_loss: list[float] = []
        for start in range(0, len(order), batch):
            idx = torch.from_numpy(order[start : start + batch].astype(np.int64))
            opt.zero_grad()
            loss = loss_fn(model(x_t[idx]), y_t[idx])
            loss.backward()
            opt.step()
            epoch_loss.append(float(loss.detach().cpu().item()))
        losses.append(float(np.mean(epoch_loss)) if epoch_loss else 0.0)

    def _predict(x_arr: np.ndarray) -> np.ndarray:
        model.eval()
        chunks: list[np.ndarray] = []
        x_all = torch.from_numpy(np.asarray(x_arr, dtype=np.float32))
        with torch.no_grad():
            for start in range(0, len(x_all), batch):
                logits = model(x_all[start : start + batch])
                chunks.append(torch.softmax(logits, dim=1).cpu().numpy())
        return np.vstack(chunks).astype(np.float64)

    diagnostics = {
        "loss_tail": losses[-5:],
        "normal_pretrain_loss_tail": pretrain_losses[-5:],
        "epochs": int(epochs),
        "normal_pretrain_epochs": int(pretrain_epochs),
        "graph_strength": float(graph_strength),
        **residual_diag,
    }
    return _predict(x_val), _predict(x_test), diagnostics


def _scale_windows(
    windows: np.ndarray,
    idx_train: np.ndarray,
    idx_val: np.ndarray,
    idx_test: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    train_flat = windows[idx_train].reshape(len(idx_train), -1)
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    scaler.fit(imputer.fit_transform(train_flat))

    def _scale(idx: np.ndarray) -> np.ndarray:
        flat = windows[idx].reshape(len(idx), -1)
        scaled = scaler.transform(imputer.transform(flat))
        return scaled.reshape(len(idx), windows.shape[1], windows.shape[2]).astype(np.float32)

    return _scale(idx_train), _scale(idx_val), _scale(idx_test)


def _align_proba(proba: np.ndarray, class_ids: Sequence[int], n_classes: int) -> np.ndarray:
    arr = np.asarray(proba, dtype=float)
    expected = [int(x) for x in class_ids]
    if expected == list(range(n_classes)):
        return arr
    out = np.zeros((arr.shape[0], len(expected)), dtype=float)
    for src, class_id in enumerate(range(n_classes)):
        if class_id in expected:
            out[:, expected.index(class_id)] = arr[:, src]
    row_sum = out.sum(axis=1, keepdims=True)
    np.divide(out, np.where(row_sum > 0, row_sum, 1.0), out=out)
    return out


def train_sequence_residual_auxiliary_branch(
    x: pd.DataFrame,
    y_meta: pd.DataFrame,
    labels: np.ndarray,
    *,
    idx_train: np.ndarray,
    idx_val: np.ndarray,
    idx_test: np.ndarray,
    dataset_dir: Path,
    class_ids: Sequence[int],
    config: Mapping[str, Any],
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    if str(config.get("sequence_residual_aux_model", "gru")).strip().lower() not in {"gru", "temporal_gru"}:
        return np.empty((0, 0)), np.empty((0, 0)), {"status": "skipped", "reason": "unsupported_sequence_model"}
    feature_cols = [str(c) for c in x.columns if pd.api.types.is_numeric_dtype(x[c])]
    windows = build_causal_run_windows(
        x,
        y_meta,
        feature_cols,
        window_size=int(config.get("sequence_residual_aux_window_size", 32)),
    )
    graph_adjacency = None
    graph_diagnostics: dict[str, Any] = {"enabled": False}
    graph_strength = float(config.get("sequence_residual_aux_graph_strength", 0.0))
    if graph_strength > 0.0:
        graph_adjacency, graph_diagnostics = load_graph_adjacency(
            Path(dataset_dir),
            feature_cols,
            prior_name=str(config.get("sequence_residual_aux_graph_prior", "tep_expert_llm_graph_prior.json")),
        )
        graph_diagnostics = {**graph_diagnostics, "enabled": True, "strength": graph_strength}
    x_train, x_val, x_test = _scale_windows(
        windows,
        np.asarray(idx_train, dtype=np.int64),
        np.asarray(idx_val, dtype=np.int64),
        np.asarray(idx_test, dtype=np.int64),
    )
    n_classes = max(int(max(class_ids)) + 1 if class_ids else 0, int(np.max(labels)) + 1)
    val_proba, test_proba, train_diag = _train_gru_sequence_model(
        x_train,
        np.asarray(labels, dtype=np.int64)[idx_train],
        x_val,
        x_test,
        n_classes=n_classes,
        hidden_dim=int(config.get("sequence_residual_aux_hidden_dim", 64)),
        epochs=int(config.get("sequence_residual_aux_epochs", 20)),
        batch_size=int(config.get("sequence_residual_aux_batch_size", 512)),
        learning_rate=float(config.get("sequence_residual_aux_learning_rate", 0.001)),
        seed=int(seed),
        pretrain_epochs=int(config.get("sequence_residual_aux_pretrain_epochs", 10)),
        graph_adjacency=graph_adjacency,
        graph_strength=graph_strength,
    )
    diagnostics = {
        "status": "ok",
        "model": "gru_normal_residual",
        "n_features": int(len(feature_cols)),
        "window_size": int(config.get("sequence_residual_aux_window_size", 32)),
        "graph_constraint": graph_diagnostics,
        "train_diagnostics": train_diag,
    }
    return _align_proba(val_proba, class_ids, n_classes), _align_proba(test_proba, class_ids, n_classes), diagnostics
