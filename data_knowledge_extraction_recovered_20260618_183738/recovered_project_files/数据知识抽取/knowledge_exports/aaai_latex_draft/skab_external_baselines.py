from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.metrics import f1_score

from public_benchmark_experiment import (
    DEFAULT_PUBLIC_DATASET_ROOT,
    PROJECT_ROOT,
    build_skab_causal_sequence_windows,
    load_skab_dataset,
    scale_skab_named_sequence_windows,
    split_skab_runs,
    summarize_classification,
    summarize_skab_protocol_detection,
)


def _valid_time_mask(windows: np.ndarray, valid_mask_index: int | None) -> np.ndarray:
    arr = np.asarray(windows, dtype=np.float32)
    if valid_mask_index is None:
        return np.ones(arr.shape[:2], dtype=np.float32)
    return (arr[:, :, int(valid_mask_index)] > 0.5).astype(np.float32)


def _data_channels(windows: np.ndarray, valid_mask_index: int | None) -> tuple[np.ndarray, list[int]]:
    arr = np.asarray(windows, dtype=np.float32)
    channels = [idx for idx in range(arr.shape[2]) if idx != valid_mask_index]
    return arr[:, :, channels].astype(np.float32), channels


def masked_reconstruction_scores(
    windows: np.ndarray,
    reconstructed: np.ndarray,
    *,
    valid_mask_index: int | None = None,
) -> np.ndarray:
    actual, channels = _data_channels(windows, valid_mask_index)
    pred = np.asarray(reconstructed, dtype=np.float32)[:, :, channels]
    valid = _valid_time_mask(windows, valid_mask_index)
    squared = (actual - pred) ** 2
    weighted = squared * valid[:, :, None]
    denom = np.maximum(np.sum(valid, axis=1) * actual.shape[2], 1.0)
    return (np.sum(weighted, axis=(1, 2)) / denom).astype(np.float64)


def tune_score_threshold(
    y_val: Sequence[int] | np.ndarray,
    scores: Sequence[float] | np.ndarray,
    *,
    threshold_grid: Sequence[float] | None = None,
) -> dict[str, float]:
    y = np.asarray(y_val, dtype=np.int64).reshape(-1)
    s = np.asarray(scores, dtype=np.float64).reshape(-1)
    if len(y) != len(s):
        raise ValueError("y_val and scores must have matching lengths")
    if threshold_grid is None:
        qs = np.linspace(0.50, 0.995, 80)
        grid = np.unique(np.quantile(s, qs)).astype(float)
    else:
        grid = np.asarray(list(threshold_grid), dtype=float)
    if grid.size == 0:
        grid = np.asarray([float(np.median(s))], dtype=float)
    best = {"threshold": float(grid[0]), "f1": -1.0}
    for threshold in grid:
        pred = (s >= float(threshold)).astype(np.int64)
        f1 = float(f1_score(y, pred, zero_division=0))
        if f1 > float(best["f1"]):
            best = {"threshold": float(threshold), "f1": f1}
    scale = float(np.percentile(s, 75) - np.percentile(s, 25))
    if not np.isfinite(scale) or scale <= 1e-8:
        scale = float(np.std(s))
    if not np.isfinite(scale) or scale <= 1e-8:
        scale = 1.0
    best["scale"] = float(scale)
    best["score_min"] = float(np.min(s)) if len(s) else 0.0
    best["score_max"] = float(np.max(s)) if len(s) else 0.0
    return best


def scores_to_binary_proba(
    scores: Sequence[float] | np.ndarray,
    tuning: dict[str, Any],
) -> np.ndarray:
    s = np.asarray(scores, dtype=np.float64).reshape(-1)
    threshold = float(tuning.get("threshold", np.median(s) if len(s) else 0.0))
    scale = max(float(tuning.get("scale", np.std(s) if len(s) else 1.0) or 1.0), 1e-6)
    z = np.clip((s - threshold) / scale, -50.0, 50.0)
    p1 = 1.0 / (1.0 + np.exp(-z))
    return np.column_stack([1.0 - p1, p1]).astype(np.float64)


def build_skab_external_prediction_records(
    meta: Any,
    y_true: Sequence[int] | np.ndarray,
    proba: np.ndarray,
    scores: Sequence[float] | np.ndarray,
    *,
    score_threshold: float,
    positive_threshold: float = 0.5,
) -> list[dict[str, Any]]:
    y_arr = np.asarray(y_true, dtype=np.int64).reshape(-1)
    p_arr = np.asarray(proba, dtype=np.float64)
    s_arr = np.asarray(scores, dtype=np.float64).reshape(-1)
    if p_arr.ndim != 2 or p_arr.shape[0] != len(y_arr) or len(s_arr) != len(y_arr):
        raise ValueError("meta, y_true, proba, and scores must describe the same number of rows")
    pred = (p_arr[:, 1] >= float(positive_threshold)).astype(np.int64)
    records: list[dict[str, Any]] = []
    for idx in range(len(y_arr)):
        row = meta.iloc[idx] if hasattr(meta, "iloc") else {}
        run_id = str(row.get("run_id", "unknown")) if hasattr(row, "get") else "unknown"
        sample_index = row.get("sample_index", idx) if hasattr(row, "get") else idx
        record_id = row.get("record_id", None) if hasattr(row, "get") else None
        if record_id is None:
            record_id = f"skab_{run_id}_{int(sample_index):05d}"
        record: dict[str, Any] = {
            "row_index": int(idx),
            "record_id": str(record_id),
            "y_true_original": int(y_arr[idx]),
            "y_pred_original": int(pred[idx]),
            "proba": [float(value) for value in p_arr[idx].tolist()],
            "positive_score": float(p_arr[idx, 1]),
            "positive_threshold": float(positive_threshold),
            "anomaly_score": float(s_arr[idx]),
            "anomaly_score_threshold": float(score_threshold),
            "run_id": run_id,
            "sample_index": int(sample_index),
        }
        for col in ("run_group", "anomaly", "changepoint"):
            if hasattr(row, "get") and row.get(col, None) is not None:
                value = row.get(col)
                try:
                    record[col] = int(value)
                except (TypeError, ValueError):
                    record[col] = str(value)
        records.append(record)
    return records


def _masked_mse(pred: torch.Tensor, target: torch.Tensor, valid: torch.Tensor) -> torch.Tensor:
    squared = (pred - target) ** 2
    weighted = squared * valid.unsqueeze(-1)
    denom = torch.clamp(torch.sum(valid) * target.shape[-1], min=1.0)
    return torch.sum(weighted) / denom


class _USADStyleAutoencoder(nn.Module):
    def __init__(self, n_steps: int, n_features: int, hidden_dim: int) -> None:
        super().__init__()
        in_dim = int(n_steps * n_features)
        hidden = max(8, int(hidden_dim))
        latent = max(4, hidden // 2)
        self.encoder = nn.Sequential(nn.Linear(in_dim, hidden), nn.ReLU(), nn.Linear(hidden, latent), nn.ReLU())
        self.decoder1 = nn.Sequential(nn.Linear(latent, hidden), nn.ReLU(), nn.Linear(hidden, in_dim))
        self.decoder2 = nn.Sequential(nn.Linear(latent, hidden), nn.ReLU(), nn.Linear(hidden, in_dim))
        self.n_steps = int(n_steps)
        self.n_features = int(n_features)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        flat = x.reshape(x.shape[0], -1)
        z = self.encoder(flat)
        rec1 = self.decoder1(z).reshape(-1, self.n_steps, self.n_features)
        rec2 = self.decoder2(z).reshape(-1, self.n_steps, self.n_features)
        z2 = self.encoder(rec1.reshape(rec1.shape[0], -1))
        rec2_after_rec1 = self.decoder2(z2).reshape(-1, self.n_steps, self.n_features)
        return rec1, rec2, rec2_after_rec1


class _TransformerReconstructor(nn.Module):
    def __init__(self, n_features: int, hidden_dim: int) -> None:
        super().__init__()
        hidden = max(8, int(hidden_dim))
        heads = 4 if hidden % 4 == 0 else 2
        if hidden % heads != 0:
            heads = 1
        self.input = nn.Linear(int(n_features), hidden)
        layer = nn.TransformerEncoderLayer(
            d_model=hidden,
            nhead=heads,
            dim_feedforward=max(hidden * 2, 16),
            dropout=0.05,
            batch_first=True,
            activation="gelu",
        )
        self.encoder = nn.TransformerEncoder(layer, num_layers=1)
        self.output = nn.Linear(hidden, int(n_features))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.output(self.encoder(self.input(x)))


class _AnomalyTransformerStyleReconstructor(nn.Module):
    def __init__(self, n_steps: int, n_features: int, hidden_dim: int) -> None:
        super().__init__()
        hidden = max(8, int(hidden_dim))
        self.input = nn.Linear(int(n_features), hidden)
        self.query = nn.Linear(hidden, hidden)
        self.key = nn.Linear(hidden, hidden)
        self.value = nn.Linear(hidden, hidden)
        self.output = nn.Linear(hidden, int(n_features))
        self.log_sigma = nn.Parameter(torch.log(torch.tensor(max(1.0, float(n_steps) / 4.0))))
        self.n_steps = int(n_steps)
        self.hidden_dim = int(hidden)

    def _prior(
        self,
        batch_size: int,
        valid: torch.Tensor | None,
        *,
        device: torch.device,
        dtype: torch.dtype,
    ) -> torch.Tensor:
        pos = torch.arange(self.n_steps, device=device, dtype=dtype)
        dist2 = (pos[:, None] - pos[None, :]) ** 2
        sigma = F.softplus(self.log_sigma).to(device=device, dtype=dtype) + 1e-3
        prior = torch.exp(-dist2 / (2.0 * sigma * sigma))
        prior = prior.unsqueeze(0).expand(int(batch_size), -1, -1).clone()
        if valid is not None:
            prior = prior * valid.to(device=device, dtype=dtype).unsqueeze(1)
        return prior / torch.clamp(prior.sum(dim=-1, keepdim=True), min=1e-6)

    def forward(self, x: torch.Tensor, valid: torch.Tensor | None = None) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        hidden = F.gelu(self.input(x))
        q = self.query(hidden)
        k = self.key(hidden)
        v = self.value(hidden)
        logits = torch.matmul(q, k.transpose(1, 2)) / max(float(self.hidden_dim) ** 0.5, 1.0)
        if valid is not None:
            key_mask = valid.to(device=logits.device, dtype=torch.bool).unsqueeze(1)
            logits = logits.masked_fill(~key_mask, -1e4)
        series = torch.softmax(logits, dim=-1)
        reconstructed = self.output(torch.matmul(series, v))
        prior = self._prior(x.shape[0], valid, device=x.device, dtype=x.dtype)
        return reconstructed, series, prior


def _association_discrepancy(series: torch.Tensor, prior: torch.Tensor, valid: torch.Tensor) -> torch.Tensor:
    series_safe = torch.clamp(series, min=1e-6)
    prior_safe = torch.clamp(prior, min=1e-6)
    kl_series_prior = torch.sum(series_safe * (torch.log(series_safe) - torch.log(prior_safe)), dim=-1)
    kl_prior_series = torch.sum(prior_safe * (torch.log(prior_safe) - torch.log(series_safe)), dim=-1)
    row_score = 0.5 * (kl_series_prior + kl_prior_series)
    weighted = row_score * valid
    denom = torch.clamp(torch.sum(valid, dim=1), min=1.0)
    return torch.sum(weighted, dim=1) / denom


def _prepare_reconstruction_data(
    windows: np.ndarray,
    *,
    valid_mask_index: int | None,
) -> tuple[np.ndarray, np.ndarray, list[int]]:
    data, channels = _data_channels(windows, valid_mask_index)
    valid = _valid_time_mask(windows, valid_mask_index)
    return (data * valid[:, :, None]).astype(np.float32), valid.astype(np.float32), channels


def _insert_reconstruction_channels(
    template: np.ndarray,
    data_reconstruction: np.ndarray,
    channels: Sequence[int],
) -> np.ndarray:
    out = np.asarray(template, dtype=np.float32).copy()
    for local_idx, channel_idx in enumerate(channels):
        out[:, :, int(channel_idx)] = data_reconstruction[:, :, int(local_idx)]
    return out


def _batch_indices(n_rows: int, batch_size: int, rng: np.random.Generator) -> list[np.ndarray]:
    order = rng.permutation(n_rows)
    batch = max(8, min(int(batch_size), max(n_rows, 1)))
    return [order[start : start + batch] for start in range(0, n_rows, batch)]


def fit_usad_style_scores(
    train_windows: np.ndarray,
    val_windows: np.ndarray,
    test_windows: np.ndarray,
    *,
    valid_mask_index: int | None,
    hidden_dim: int = 64,
    epochs: int = 8,
    batch_size: int = 512,
    learning_rate: float = 0.001,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    train_x, train_valid, channels = _prepare_reconstruction_data(train_windows, valid_mask_index=valid_mask_index)
    torch.manual_seed(int(seed))
    torch.set_num_threads(1)
    model = _USADStyleAutoencoder(train_x.shape[1], train_x.shape[2], int(hidden_dim))
    opt = torch.optim.AdamW(model.parameters(), lr=float(learning_rate), weight_decay=1e-4)
    x_t = torch.from_numpy(train_x)
    valid_t = torch.from_numpy(train_valid)
    rng = np.random.default_rng(int(seed))
    losses: list[float] = []
    model.train()
    for _epoch in range(max(1, int(epochs))):
        epoch_losses: list[float] = []
        for idx_np in _batch_indices(len(train_x), batch_size, rng):
            idx = torch.from_numpy(idx_np.astype(np.int64))
            opt.zero_grad()
            rec1, rec2, rec2_after_rec1 = model(x_t[idx])
            loss = (
                _masked_mse(rec1, x_t[idx], valid_t[idx])
                + _masked_mse(rec2, x_t[idx], valid_t[idx])
                + 0.5 * _masked_mse(rec2_after_rec1, x_t[idx], valid_t[idx])
            )
            loss.backward()
            opt.step()
            epoch_losses.append(float(loss.detach().cpu().item()))
        losses.append(float(np.mean(epoch_losses)) if epoch_losses else 0.0)

    def _score(windows: np.ndarray) -> np.ndarray:
        data, _valid, _channels = _prepare_reconstruction_data(windows, valid_mask_index=valid_mask_index)
        model.eval()
        preds: list[np.ndarray] = []
        with torch.no_grad():
            for start in range(0, len(data), max(16, int(batch_size))):
                xb = torch.from_numpy(data[start : start + max(16, int(batch_size))])
                rec1, rec2, _rec2_after = model(xb)
                preds.append(((rec1 + rec2) / 2.0).cpu().numpy())
        rec_data = np.concatenate(preds, axis=0) if preds else np.zeros_like(data)
        reconstructed = _insert_reconstruction_channels(windows, rec_data, channels)
        return masked_reconstruction_scores(windows, reconstructed, valid_mask_index=valid_mask_index)

    return _score(val_windows), _score(test_windows), {
        "model": "usad_style",
        "epochs": int(epochs),
        "hidden_dim": int(hidden_dim),
        "loss_final": float(losses[-1]) if losses else 0.0,
        "loss_history": [float(v) for v in losses],
    }


def fit_transformer_reconstruction_scores(
    train_windows: np.ndarray,
    val_windows: np.ndarray,
    test_windows: np.ndarray,
    *,
    valid_mask_index: int | None,
    hidden_dim: int = 64,
    epochs: int = 8,
    batch_size: int = 512,
    learning_rate: float = 0.001,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    train_x, train_valid, channels = _prepare_reconstruction_data(train_windows, valid_mask_index=valid_mask_index)
    torch.manual_seed(int(seed))
    torch.set_num_threads(1)
    model = _TransformerReconstructor(train_x.shape[2], int(hidden_dim))
    opt = torch.optim.AdamW(model.parameters(), lr=float(learning_rate), weight_decay=1e-4)
    x_t = torch.from_numpy(train_x)
    valid_t = torch.from_numpy(train_valid)
    rng = np.random.default_rng(int(seed))
    losses: list[float] = []
    model.train()
    for _epoch in range(max(1, int(epochs))):
        epoch_losses: list[float] = []
        for idx_np in _batch_indices(len(train_x), batch_size, rng):
            idx = torch.from_numpy(idx_np.astype(np.int64))
            opt.zero_grad()
            rec = model(x_t[idx])
            loss = _masked_mse(rec, x_t[idx], valid_t[idx])
            loss.backward()
            opt.step()
            epoch_losses.append(float(loss.detach().cpu().item()))
        losses.append(float(np.mean(epoch_losses)) if epoch_losses else 0.0)

    def _score(windows: np.ndarray) -> np.ndarray:
        data, _valid, _channels = _prepare_reconstruction_data(windows, valid_mask_index=valid_mask_index)
        model.eval()
        preds: list[np.ndarray] = []
        with torch.no_grad():
            for start in range(0, len(data), max(16, int(batch_size))):
                xb = torch.from_numpy(data[start : start + max(16, int(batch_size))])
                preds.append(model(xb).cpu().numpy())
        rec_data = np.concatenate(preds, axis=0) if preds else np.zeros_like(data)
        reconstructed = _insert_reconstruction_channels(windows, rec_data, channels)
        return masked_reconstruction_scores(windows, reconstructed, valid_mask_index=valid_mask_index)

    return _score(val_windows), _score(test_windows), {
        "model": "tranad_style_transformer",
        "epochs": int(epochs),
        "hidden_dim": int(hidden_dim),
        "loss_final": float(losses[-1]) if losses else 0.0,
        "loss_history": [float(v) for v in losses],
    }


def fit_anomaly_transformer_style_scores(
    train_windows: np.ndarray,
    val_windows: np.ndarray,
    test_windows: np.ndarray,
    *,
    valid_mask_index: int | None,
    hidden_dim: int = 64,
    epochs: int = 8,
    batch_size: int = 512,
    learning_rate: float = 0.001,
    seed: int = 42,
    association_weight: float = 0.10,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    train_x, train_valid, channels = _prepare_reconstruction_data(train_windows, valid_mask_index=valid_mask_index)
    torch.manual_seed(int(seed))
    torch.set_num_threads(1)
    model = _AnomalyTransformerStyleReconstructor(train_x.shape[1], train_x.shape[2], int(hidden_dim))
    opt = torch.optim.AdamW(model.parameters(), lr=float(learning_rate), weight_decay=1e-4)
    x_t = torch.from_numpy(train_x)
    valid_t = torch.from_numpy(train_valid)
    rng = np.random.default_rng(int(seed))
    losses: list[float] = []
    recon_losses: list[float] = []
    assoc_losses: list[float] = []
    model.train()
    for _epoch in range(max(1, int(epochs))):
        epoch_losses: list[float] = []
        epoch_recon: list[float] = []
        epoch_assoc: list[float] = []
        for idx_np in _batch_indices(len(train_x), batch_size, rng):
            idx = torch.from_numpy(idx_np.astype(np.int64))
            opt.zero_grad()
            reconstructed, series, prior = model(x_t[idx], valid_t[idx])
            recon = _masked_mse(reconstructed, x_t[idx], valid_t[idx])
            assoc = torch.mean(_association_discrepancy(series, prior, valid_t[idx]))
            loss = recon + 0.05 * assoc
            loss.backward()
            opt.step()
            epoch_losses.append(float(loss.detach().cpu().item()))
            epoch_recon.append(float(recon.detach().cpu().item()))
            epoch_assoc.append(float(assoc.detach().cpu().item()))
        losses.append(float(np.mean(epoch_losses)) if epoch_losses else 0.0)
        recon_losses.append(float(np.mean(epoch_recon)) if epoch_recon else 0.0)
        assoc_losses.append(float(np.mean(epoch_assoc)) if epoch_assoc else 0.0)

    def _score(windows: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        data, valid, _channels = _prepare_reconstruction_data(windows, valid_mask_index=valid_mask_index)
        model.eval()
        rec_chunks: list[np.ndarray] = []
        assoc_chunks: list[np.ndarray] = []
        with torch.no_grad():
            for start in range(0, len(data), max(16, int(batch_size))):
                xb = torch.from_numpy(data[start : start + max(16, int(batch_size))])
                vb = torch.from_numpy(valid[start : start + max(16, int(batch_size))])
                reconstructed, series, prior = model(xb, vb)
                rec_chunks.append(reconstructed.cpu().numpy())
                assoc_chunks.append(_association_discrepancy(series, prior, vb).cpu().numpy())
        rec_data = np.concatenate(rec_chunks, axis=0) if rec_chunks else np.zeros_like(data)
        assoc_score = np.concatenate(assoc_chunks, axis=0).astype(np.float64) if assoc_chunks else np.zeros(len(data), dtype=np.float64)
        reconstructed_full = _insert_reconstruction_channels(windows, rec_data, channels)
        recon_score = masked_reconstruction_scores(windows, reconstructed_full, valid_mask_index=valid_mask_index)
        combined = recon_score + float(association_weight) * assoc_score
        return combined.astype(np.float64), recon_score.astype(np.float64), assoc_score.astype(np.float64)

    val_scores, val_recon, val_assoc = _score(val_windows)
    test_scores, test_recon, test_assoc = _score(test_windows)
    return val_scores, test_scores, {
        "model": "anomaly_transformer_style_association_discrepancy",
        "epochs": int(epochs),
        "hidden_dim": int(hidden_dim),
        "association_weight": float(association_weight),
        "loss_final": float(losses[-1]) if losses else 0.0,
        "reconstruction_loss_final": float(recon_losses[-1]) if recon_losses else 0.0,
        "association_loss_final": float(assoc_losses[-1]) if assoc_losses else 0.0,
        "loss_history": [float(v) for v in losses],
        "score_components": {
            "val_reconstruction_mean": float(np.mean(val_recon)) if len(val_recon) else 0.0,
            "val_association_mean": float(np.mean(val_assoc)) if len(val_assoc) else 0.0,
            "test_reconstruction_mean": float(np.mean(test_recon)) if len(test_recon) else 0.0,
            "test_association_mean": float(np.mean(test_assoc)) if len(test_assoc) else 0.0,
        },
    }


def _split_csv_ints(raw: str) -> list[int]:
    return [int(item.strip()) for item in str(raw).split(",") if item.strip()]


def _split_csv(raw: str) -> list[str]:
    return [item.strip() for item in str(raw).split(",") if item.strip()]


def run_skab_external_baselines(
    dataset_root: Path,
    output_path: Path,
    *,
    seeds: Sequence[int],
    methods: Sequence[str] = ("usad", "tranad"),
    window_size: int = 32,
    epochs: int = 8,
    hidden_dim: int = 64,
    batch_size: int = 512,
    learning_rate: float = 0.001,
    association_weight: float = 0.10,
) -> dict[str, Any]:
    x_raw, y, meta = load_skab_dataset(dataset_root)
    windows, feature_cols = build_skab_causal_sequence_windows(
        x_raw.reset_index(drop=True),
        meta.reset_index(drop=True),
        window_size=int(window_size),
        include_valid_mask=True,
    )
    valid_mask_index = feature_cols.index("valid_mask") if "valid_mask" in feature_cols else None
    methods_normalized = [str(method).strip().lower() for method in methods]
    runs: list[dict[str, Any]] = []
    for seed in seeds:
        train_runs, val_runs, test_runs = split_skab_runs(meta, seed=int(seed), test_size=0.30, val_fraction=0.25)
        train_mask = meta["run_id"].astype(str).isin(train_runs).to_numpy(dtype=bool)
        val_mask = meta["run_id"].astype(str).isin(val_runs).to_numpy(dtype=bool)
        test_mask = meta["run_id"].astype(str).isin(test_runs).to_numpy(dtype=bool)
        scaled = scale_skab_named_sequence_windows(
            windows,
            feature_cols,
            train_mask=train_mask,
            passthrough_cols=("valid_mask",),
        )
        y_train = y[train_mask]
        y_val = y[val_mask]
        y_test = y[test_mask]
        train_windows = scaled[train_mask][y_train == 0]
        if len(train_windows) == 0:
            train_windows = scaled[train_mask]
        val_windows = scaled[val_mask]
        test_windows = scaled[test_mask]
        meta_test = meta.iloc[np.flatnonzero(test_mask)].reset_index(drop=True)
        run: dict[str, Any] = {
            "seed": int(seed),
            "train_runs": list(train_runs),
            "val_runs": list(val_runs),
            "test_runs": list(test_runs),
            "n_train_windows": int(len(train_windows)),
            "n_val_windows": int(len(val_windows)),
            "n_test_windows": int(len(test_windows)),
        }
        for method in methods_normalized:
            if method in {"usad", "usad_style"}:
                val_scores, test_scores, diagnostics = fit_usad_style_scores(
                    train_windows,
                    val_windows,
                    test_windows,
                    valid_mask_index=valid_mask_index,
                    hidden_dim=hidden_dim,
                    epochs=epochs,
                    batch_size=batch_size,
                    learning_rate=learning_rate,
                    seed=int(seed) + 1001,
                )
            elif method in {"tranad", "tranad_style", "transformer"}:
                val_scores, test_scores, diagnostics = fit_transformer_reconstruction_scores(
                    train_windows,
                    val_windows,
                    test_windows,
                    valid_mask_index=valid_mask_index,
                    hidden_dim=hidden_dim,
                    epochs=epochs,
                    batch_size=batch_size,
                    learning_rate=learning_rate,
                    seed=int(seed) + 2001,
                )
            elif method in {"anomaly_transformer", "anomaly-transformer", "anomaly_transformer_style"}:
                val_scores, test_scores, diagnostics = fit_anomaly_transformer_style_scores(
                    train_windows,
                    val_windows,
                    test_windows,
                    valid_mask_index=valid_mask_index,
                    hidden_dim=hidden_dim,
                    epochs=epochs,
                    batch_size=batch_size,
                    learning_rate=learning_rate,
                    seed=int(seed) + 3001,
                    association_weight=float(association_weight),
                )
            else:
                raise ValueError(f"Unknown SKAB external baseline method: {method}")
            tuning = tune_score_threshold(y_val, val_scores)
            test_proba = scores_to_binary_proba(test_scores, tuning)
            metrics = summarize_classification(y_test, test_proba, positive_threshold=0.5)
            protocol = summarize_skab_protocol_detection(
                y_test,
                test_proba,
                meta_test,
                positive_threshold=0.5,
            )
            run[str(method)] = {
                "metrics": metrics,
                "protocol": protocol,
                "threshold_tuning": tuning,
                "prediction_records": build_skab_external_prediction_records(
                    meta_test,
                    y_test,
                    test_proba,
                    test_scores,
                    score_threshold=float(tuning.get("threshold", 0.0)),
                    positive_threshold=0.5,
                ),
                "diagnostics": diagnostics,
                "score_summary": {
                    "val_mean": float(np.mean(val_scores)),
                    "test_mean": float(np.mean(test_scores)),
                    "test_p95": float(np.percentile(test_scores, 95)),
                },
            }
            print(
                f"seed={int(seed)} {method} macro={metrics['macro_f1']:.4f} "
                f"binary_f1={protocol['binary']['f1']:.4f} "
                f"far={protocol['binary']['far_percent']:.2f} mar={protocol['binary']['mar_percent']:.2f}"
            )
        runs.append(run)
    result = {
        "status": "ok",
        "task": "skab_external_reconstruction_baselines",
        "protocol": "run_level_skab_reconstruction_anomaly_baselines",
        "methods": methods_normalized,
        "seeds": [int(seed) for seed in seeds],
        "window_size": int(window_size),
        "epochs": int(epochs),
        "hidden_dim": int(hidden_dim),
        "association_weight": float(association_weight),
        "runs": runs,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SKAB USAD/TranAD/Anomaly-Transformer-style external reconstruction baselines.")
    parser.add_argument("--dataset-root", default=str(DEFAULT_PUBLIC_DATASET_ROOT))
    parser.add_argument("--output", default=str(PROJECT_ROOT / "knowledge_exports" / "skab_external_baselines.json"))
    parser.add_argument("--seeds", default="42")
    parser.add_argument("--methods", default="usad,tranad")
    parser.add_argument("--window-size", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--learning-rate", type=float, default=0.001)
    parser.add_argument("--association-weight", type=float, default=0.10)
    args = parser.parse_args()
    run_skab_external_baselines(
        Path(args.dataset_root),
        Path(args.output),
        seeds=_split_csv_ints(args.seeds),
        methods=_split_csv(args.methods),
        window_size=int(args.window_size),
        epochs=int(args.epochs),
        hidden_dim=int(args.hidden_dim),
        batch_size=int(args.batch_size),
        learning_rate=float(args.learning_rate),
        association_weight=float(args.association_weight),
    )


if __name__ == "__main__":
    main()
