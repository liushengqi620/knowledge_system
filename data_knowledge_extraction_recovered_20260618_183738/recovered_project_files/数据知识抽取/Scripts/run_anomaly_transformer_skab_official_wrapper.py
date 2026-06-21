from __future__ import annotations

import argparse
import copy
import importlib
import json
import os
import random
import sys
import time
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support
from torch.utils.data import DataLoader, Dataset

VERSION = "anomaly-transformer-official-source-skab-wrapper-v1"
CHECKED_ON = "2026-06-21"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ADAPTER_ROOT = (
    PROJECT_ROOT
    / "knowledge_exports"
    / "external_baseline_protocol_runs"
    / "anomaly_transformer_official_skab_adapter"
)
DEFAULT_CHECKOUT = Path.home() / "aaai_external_baseline_checkouts" / "anomaly_transformer"
DEFAULT_OUTPUT = (
    PROJECT_ROOT
    / "knowledge_exports"
    / "external_baseline_protocol_runs"
    / "anomaly_transformer_official_skab_wrapper_smoke.json"
)
OFFICIAL_COMMIT = "b0ee470c8012"
POSITIVE_PROBA_THRESHOLD = float(np.nextafter(0.5, 1.0))


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _split_ints(raw: str | Sequence[int]) -> list[int]:
    if isinstance(raw, str):
        values = [int(part.strip()) for part in raw.replace(";", ",").split(",") if part.strip()]
    else:
        values = [int(item) for item in raw]
    return values or [42]


def _seed_everything(seed: int) -> None:
    random.seed(int(seed))
    np.random.seed(int(seed))
    torch.manual_seed(int(seed))
    torch.cuda.manual_seed_all(int(seed))


def _load_official_model(checkout: Path):
    checkout = Path(checkout).resolve()
    if not (checkout / "model" / "AnomalyTransformer.py").exists():
        raise FileNotFoundError(f"Official Anomaly Transformer checkout not found: {checkout}")
    if str(checkout) not in sys.path:
        sys.path.insert(0, str(checkout))
    module = importlib.import_module("model.AnomalyTransformer")
    return module.AnomalyTransformer


def _read_features(path: Path) -> np.ndarray:
    frame = pd.read_csv(_fs_path(path))
    features = frame.drop(columns=[col for col in ["timestamp", "record_id"] if col in frame.columns])
    return features.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0.0).to_numpy(dtype=np.float32)


def _read_labels(path: Path) -> np.ndarray:
    frame = pd.read_csv(_fs_path(path))
    label_col = "label" if "label" in frame.columns else frame.columns[-1]
    return pd.to_numeric(frame[label_col], errors="coerce").fillna(0).astype(int).to_numpy(dtype=np.int64)


def _standardize(train: np.ndarray, *arrays: np.ndarray) -> tuple[np.ndarray, ...]:
    mean = train.mean(axis=0, keepdims=True)
    std = train.std(axis=0, keepdims=True)
    std = np.where(std < 1e-6, 1.0, std)
    return tuple(((arr - mean) / std).astype(np.float32) for arr in (train, *arrays))


def _windows(data: np.ndarray, *, win_size: int, step: int = 1) -> tuple[np.ndarray, np.ndarray]:
    n_rows = int(len(data))
    if n_rows < int(win_size):
        raise ValueError(f"Not enough rows ({n_rows}) for win_size={win_size}")
    starts = np.arange(0, n_rows - int(win_size) + 1, int(step), dtype=np.int64)
    offsets = np.arange(int(win_size), dtype=np.int64)
    indices = starts[:, None] + offsets[None, :]
    return data[indices].astype(np.float32), indices.astype(np.int64)


class _WindowDataset(Dataset):
    def __init__(self, windows: np.ndarray, labels: np.ndarray | None = None, indices: np.ndarray | None = None) -> None:
        self.windows = torch.from_numpy(np.asarray(windows, dtype=np.float32))
        self.labels = None if labels is None else torch.from_numpy(np.asarray(labels, dtype=np.int64))
        self.indices = None if indices is None else torch.from_numpy(np.asarray(indices, dtype=np.int64))

    def __len__(self) -> int:
        return int(self.windows.shape[0])

    def __getitem__(self, index: int):
        if self.labels is None:
            return self.windows[index]
        return self.windows[index], self.labels[index], self.indices[index]


def my_kl_loss(p: torch.Tensor, q: torch.Tensor) -> torch.Tensor:
    res = p * (torch.log(p + 0.0001) - torch.log(q + 0.0001))
    return torch.mean(torch.sum(res, dim=-1), dim=1)


def _association_losses(series: list[torch.Tensor], prior: list[torch.Tensor], win_size: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    series_loss = 0.0
    prior_loss = 0.0
    series_score = 0.0
    prior_score = 0.0
    for u in range(len(prior)):
        normalized_prior = prior[u] / torch.unsqueeze(torch.sum(prior[u], dim=-1), dim=-1).repeat(1, 1, 1, win_size)
        series_loss = series_loss + (
            torch.mean(my_kl_loss(series[u], normalized_prior.detach()))
            + torch.mean(my_kl_loss(normalized_prior.detach(), series[u]))
        )
        prior_loss = prior_loss + (
            torch.mean(my_kl_loss(normalized_prior, series[u].detach()))
            + torch.mean(my_kl_loss(series[u].detach(), normalized_prior))
        )
        series_score = series_score + my_kl_loss(series[u], normalized_prior.detach())
        prior_score = prior_score + my_kl_loss(normalized_prior, series[u].detach())
    denom = max(len(prior), 1)
    return series_loss / denom, prior_loss / denom, series_score, prior_score


def _train_model(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    *,
    device: torch.device,
    win_size: int,
    epochs: int,
    learning_rate: float,
    k: float,
) -> tuple[nn.Module, dict[str, Any]]:
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=float(learning_rate))
    best_state = copy.deepcopy(model.state_dict())
    best_val = float("inf")
    history: list[dict[str, float]] = []
    for epoch in range(max(1, int(epochs))):
        model.train()
        train_losses: list[float] = []
        start_time = time.time()
        for batch in train_loader:
            batch = batch.float().to(device)
            optimizer.zero_grad()
            output, series, prior, _sigmas = model(batch)
            series_loss, prior_loss, _series_score, _prior_score = _association_losses(series, prior, win_size)
            rec_loss = criterion(output, batch)
            loss1 = rec_loss - float(k) * series_loss
            loss2 = rec_loss + float(k) * prior_loss
            loss1.backward(retain_graph=True)
            loss2.backward()
            optimizer.step()
            train_losses.append(float(loss1.detach().cpu().item()))
        val_loss = _validation_loss(model, val_loader, device=device, win_size=win_size, k=k)
        if val_loss < best_val:
            best_val = float(val_loss)
            best_state = copy.deepcopy(model.state_dict())
        history.append(
            {
                "epoch": float(epoch + 1),
                "train_loss": float(np.mean(train_losses)) if train_losses else 0.0,
                "validation_loss": float(val_loss),
                "epoch_seconds": float(time.time() - start_time),
            }
        )
    model.load_state_dict(best_state)
    return model, {"best_validation_loss": float(best_val), "history": history}


def _validation_loss(model: nn.Module, loader: DataLoader, *, device: torch.device, win_size: int, k: float) -> float:
    model.eval()
    criterion = nn.MSELoss()
    losses: list[float] = []
    with torch.no_grad():
        for batch, _labels, _indices in loader:
            batch = batch.float().to(device)
            output, series, prior, _sigmas = model(batch)
            series_loss, _prior_loss, _series_score, _prior_score = _association_losses(series, prior, win_size)
            rec_loss = criterion(output, batch)
            losses.append(float((rec_loss - float(k) * series_loss).detach().cpu().item()))
    return float(np.mean(losses)) if losses else float("inf")


def _score_windows(
    model: nn.Module,
    loader: DataLoader,
    *,
    device: torch.device,
    win_size: int,
    temperature: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    model.eval()
    criterion = nn.MSELoss(reduction="none")
    score_chunks: list[np.ndarray] = []
    label_chunks: list[np.ndarray] = []
    index_chunks: list[np.ndarray] = []
    with torch.no_grad():
        for batch, labels, indices in loader:
            batch = batch.float().to(device)
            output, series, prior, _sigmas = model(batch)
            loss = torch.mean(criterion(batch, output), dim=-1)
            _series_loss, _prior_loss, series_score, prior_score = _association_losses(series, prior, win_size)
            metric = torch.softmax((-series_score - prior_score) * float(temperature), dim=-1)
            scores = metric * loss
            score_chunks.append(scores.detach().cpu().numpy())
            label_chunks.append(labels.numpy())
            index_chunks.append(indices.numpy())
    return (
        np.concatenate(score_chunks, axis=0).astype(np.float64),
        np.concatenate(label_chunks, axis=0).astype(np.int64),
        np.concatenate(index_chunks, axis=0).astype(np.int64),
    )


def _aggregate_rows(window_scores: np.ndarray, window_indices: np.ndarray, n_rows: int, *, method: str = "max") -> np.ndarray:
    out = np.full(int(n_rows), -np.inf if method == "max" else 0.0, dtype=np.float64)
    counts = np.zeros(int(n_rows), dtype=np.float64)
    flat_scores = window_scores.reshape(-1)
    flat_indices = window_indices.reshape(-1)
    if method == "max":
        np.maximum.at(out, flat_indices, flat_scores)
        missing = ~np.isfinite(out)
        if missing.any():
            out[missing] = float(np.nanmin(flat_scores)) if len(flat_scores) else 0.0
    else:
        np.add.at(out, flat_indices, flat_scores)
        np.add.at(counts, flat_indices, 1.0)
        out = out / np.maximum(counts, 1.0)
    return out


def _tune_threshold(labels: np.ndarray, scores: np.ndarray) -> dict[str, float]:
    y = np.asarray(labels, dtype=np.int64).reshape(-1)
    s = np.asarray(scores, dtype=np.float64).reshape(-1)
    grid = np.unique(np.quantile(s, np.linspace(0.50, 0.995, 100)))
    if grid.size == 0:
        grid = np.asarray([float(np.median(s))], dtype=np.float64)
    best = {"threshold": float(grid[0]), "binary_f1": -1.0, "macro_f1": -1.0}
    for threshold in grid:
        pred = (s > float(threshold)).astype(np.int64)
        binary = float(f1_score(y, pred, zero_division=0))
        macro = float(f1_score(y, pred, average="macro", zero_division=0))
        if binary > best["binary_f1"] or (binary == best["binary_f1"] and macro > best["macro_f1"]):
            best = {"threshold": float(threshold), "binary_f1": binary, "macro_f1": macro}
    scale = float(np.percentile(s, 75) - np.percentile(s, 25))
    if not np.isfinite(scale) or scale <= 1e-8:
        scale = float(np.std(s))
    if not np.isfinite(scale) or scale <= 1e-8:
        scale = 1.0
    best["scale"] = float(scale)
    return best


def _classification_metrics(labels: np.ndarray, scores: np.ndarray, threshold: float) -> dict[str, float]:
    y = np.asarray(labels, dtype=np.int64).reshape(-1)
    pred = (np.asarray(scores, dtype=np.float64).reshape(-1) > float(threshold)).astype(np.int64)
    precision, recall, binary_f1, _support = precision_recall_fscore_support(y, pred, average="binary", zero_division=0)
    return {
        "accuracy": float(accuracy_score(y, pred)),
        "precision": float(precision),
        "recall": float(recall),
        "binary_f1": float(binary_f1),
        "macro_f1": float(f1_score(y, pred, average="macro", zero_division=0)),
    }


def _scores_to_proba(scores: np.ndarray, threshold_info: dict[str, float]) -> np.ndarray:
    s = np.asarray(scores, dtype=np.float64).reshape(-1)
    threshold = float(threshold_info["threshold"])
    scale = max(float(threshold_info.get("scale", 1.0)), 1e-6)
    z = np.clip((s - threshold) / scale, -50.0, 50.0)
    p1 = 1.0 / (1.0 + np.exp(-z))
    return np.column_stack([1.0 - p1, p1])


def _build_prediction_records(
    *,
    labels: np.ndarray,
    scores: np.ndarray,
    threshold_info: dict[str, float],
    meta: pd.DataFrame | None,
) -> list[dict[str, Any]]:
    y_true = np.asarray(labels, dtype=np.int64).reshape(-1)
    anomaly_scores = np.asarray(scores, dtype=np.float64).reshape(-1)
    threshold = float(threshold_info["threshold"])
    proba = _scores_to_proba(anomaly_scores, threshold_info)
    y_pred = (anomaly_scores > threshold).astype(np.int64)
    records: list[dict[str, Any]] = []
    for row_index, (true, pred, score, prob) in enumerate(zip(y_true, y_pred, anomaly_scores, proba, strict=False)):
        meta_row = meta.iloc[row_index].to_dict() if meta is not None and row_index < len(meta) else {}
        run_id = str(meta_row.get("run_id", "unknown"))
        sample_index = int(meta_row.get("sample_index", row_index))
        record = {
            "row_index": int(row_index),
            "record_id": str(meta_row.get("record_id") or f"skab_{run_id}_{sample_index:05d}"),
            "y_true_original": int(true),
            "y_pred_original": int(pred),
            "proba": [float(prob[0]), float(prob[1])],
            "positive_score": float(prob[1]),
            "positive_threshold": POSITIVE_PROBA_THRESHOLD,
            "anomaly_score": float(score),
            "anomaly_score_threshold": threshold,
            "run_id": run_id,
            "sample_index": sample_index,
            "run_group": str(meta_row.get("run_group", "")),
            "anomaly": int(meta_row.get("anomaly", int(true))),
            "changepoint": int(meta_row.get("changepoint", 0)),
        }
        records.append(record)
    return records


def _summarize_skab_protocol_from_predictions(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    meta: pd.DataFrame,
    *,
    changepoint_window_steps: int = 60,
) -> dict[str, Any]:
    y = np.asarray(y_true, dtype=np.int64).reshape(-1)
    pred = np.asarray(y_pred, dtype=np.int64).reshape(-1)
    precision, recall, binary_f1, _support = precision_recall_fscore_support(y, pred, average="binary", zero_division=0)
    fp = int(np.sum((pred == 1) & (y == 0)))
    fn = int(np.sum((pred == 0) & (y == 1)))
    negatives = int(np.sum(y == 0))
    positives = int(np.sum(y == 1))
    binary = {
        "f1": float(binary_f1),
        "precision": float(precision),
        "recall": float(recall),
        "far_percent": float(100.0 * fp / max(1, negatives)),
        "mar_percent": float(100.0 * fn / max(1, positives)),
    }
    detected_runs = 0
    anomalous_runs = 0
    for _run_id, group in meta.assign(_y=y, _pred=pred).groupby("run_id", sort=False):
        if int(group["_y"].max()) <= 0:
            continue
        anomalous_runs += 1
        first_anomaly = int(group.loc[group["_y"].eq(1), "sample_index"].min())
        limit = first_anomaly + int(changepoint_window_steps)
        hit = bool(group[group["sample_index"].between(first_anomaly, limit)]["_pred"].max() > 0)
        detected_runs += int(hit)
    point_adjusted_f1 = binary["f1"] if anomalous_runs == 0 else float(detected_runs / max(1, anomalous_runs))
    return {
        "binary": binary,
        "point_adjusted": {
            "f1": point_adjusted_f1,
            "detected_runs": int(detected_runs),
            "anomalous_runs": int(anomalous_runs),
        },
        "right_window_changepoint": {
            "window_steps": int(changepoint_window_steps),
            "detected_runs": int(detected_runs),
            "anomalous_runs": int(anomalous_runs),
        },
    }


def run_seed(
    *,
    seed: int,
    adapter_root: Path,
    checkout: Path,
    win_size: int,
    batch_size: int,
    epochs: int,
    learning_rate: float,
    k: float,
    d_model: int,
    n_heads: int,
    e_layers: int,
    d_ff: int,
    temperature: float,
    aggregation: str,
) -> dict[str, Any]:
    if not torch.cuda.is_available():
        raise RuntimeError("Official Anomaly Transformer source hard-codes CUDA tensors; CUDA is required for this wrapper.")
    _seed_everything(int(seed))
    seed_root = Path(adapter_root) / f"seed_{int(seed)}" / "psm_compatible"
    train_raw = _read_features(seed_root / "train.csv")
    val_raw = _read_features(seed_root / "val.csv")
    test_raw = _read_features(seed_root / "test.csv")
    val_labels = _read_labels(seed_root / "val_label.csv")
    test_labels = _read_labels(seed_root / "test_label.csv")
    train_x, val_x, test_x = _standardize(train_raw, val_raw, test_raw)
    train_windows, _train_indices = _windows(train_x, win_size=win_size, step=1)
    val_windows, val_indices = _windows(val_x, win_size=win_size, step=1)
    test_windows, test_indices = _windows(test_x, win_size=win_size, step=1)
    val_window_labels = val_labels[val_indices]
    test_window_labels = test_labels[test_indices]

    train_loader = DataLoader(_WindowDataset(train_windows), batch_size=int(batch_size), shuffle=True, num_workers=0)
    val_loader = DataLoader(_WindowDataset(val_windows, val_window_labels, val_indices), batch_size=int(batch_size), shuffle=False, num_workers=0)
    test_loader = DataLoader(_WindowDataset(test_windows, test_window_labels, test_indices), batch_size=int(batch_size), shuffle=False, num_workers=0)

    AnomalyTransformer = _load_official_model(checkout)
    model = AnomalyTransformer(
        win_size=int(win_size),
        enc_in=int(train_x.shape[1]),
        c_out=int(train_x.shape[1]),
        d_model=int(d_model),
        n_heads=int(n_heads),
        e_layers=int(e_layers),
        d_ff=int(d_ff),
    ).cuda()
    device = torch.device("cuda:0")
    train_start = time.time()
    model, train_diag = _train_model(
        model,
        train_loader,
        val_loader,
        device=device,
        win_size=int(win_size),
        epochs=int(epochs),
        learning_rate=float(learning_rate),
        k=float(k),
    )
    train_seconds = float(time.time() - train_start)
    val_scores_win, val_labels_win, val_idx_win = _score_windows(model, val_loader, device=device, win_size=int(win_size), temperature=float(temperature))
    test_scores_win, test_labels_win, test_idx_win = _score_windows(model, test_loader, device=device, win_size=int(win_size), temperature=float(temperature))
    val_scores_row = _aggregate_rows(val_scores_win, val_idx_win, len(val_labels), method=str(aggregation))
    test_scores_row = _aggregate_rows(test_scores_win, test_idx_win, len(test_labels), method=str(aggregation))
    threshold = _tune_threshold(val_labels, val_scores_row)
    row_metrics = _classification_metrics(test_labels, test_scores_row, threshold["threshold"])
    flat_threshold = _tune_threshold(val_labels_win.reshape(-1), val_scores_win.reshape(-1))
    flat_metrics = _classification_metrics(test_labels_win.reshape(-1), test_scores_win.reshape(-1), flat_threshold["threshold"])
    meta_test_path = seed_root / "test_meta.csv"
    protocol: dict[str, Any] = {}
    meta_test = pd.read_csv(_fs_path(meta_test_path)) if meta_test_path.exists() else None
    if meta_test is not None:
        protocol = _summarize_skab_protocol_from_predictions(
            test_labels,
            (test_scores_row > float(threshold["threshold"])).astype(np.int64),
            meta_test,
        )
    return {
        "seed": int(seed),
        "adapter_dir": str(seed_root),
        "official_checkout": str(Path(checkout).resolve()),
        "official_commit": OFFICIAL_COMMIT,
        "device": str(device),
        "config": {
            "win_size": int(win_size),
            "batch_size": int(batch_size),
            "epochs": int(epochs),
            "learning_rate": float(learning_rate),
            "k": float(k),
            "d_model": int(d_model),
            "n_heads": int(n_heads),
            "e_layers": int(e_layers),
            "d_ff": int(d_ff),
            "temperature": float(temperature),
            "aggregation": str(aggregation),
        },
        "row_counts": {
            "train_rows": int(len(train_x)),
            "val_rows": int(len(val_x)),
            "test_rows": int(len(test_x)),
            "train_windows": int(len(train_windows)),
            "val_windows": int(len(val_windows)),
            "test_windows": int(len(test_windows)),
        },
        "training": {**train_diag, "train_seconds": train_seconds},
        "threshold": threshold,
        "flat_threshold": flat_threshold,
        "matched_row_level": {
            "metrics": row_metrics,
            "protocol": protocol,
            "threshold_tuning": threshold,
            "prediction_records": _build_prediction_records(
                labels=test_labels,
                scores=test_scores_row,
                threshold_info=threshold,
                meta=meta_test,
            ),
            "score_summary": {
                "val_mean": float(np.mean(val_scores_row)),
                "test_mean": float(np.mean(test_scores_row)),
                "test_p95": float(np.percentile(test_scores_row, 95)),
            },
        },
        "official_flattened_no_adjustment": {
            "metrics": flat_metrics,
            "score_summary": {
                "val_mean": float(np.mean(val_scores_win)),
                "test_mean": float(np.mean(test_scores_win)),
            },
        },
        "protocol_alignment": {
            "official_source_model_used": True,
            "official_external_score": False,
            "validation_only_thresholds": True,
            "point_adjustment": "disabled",
            "test_labels_used_for_threshold": False,
            "claim_boundary": "Official source architecture with patched SKAB validation-only protocol; not an official Anomaly Transformer paper benchmark score.",
        },
    }


def _summarize_runs(runs: list[dict[str, Any]]) -> dict[str, Any]:
    if not runs:
        return {}
    macro = np.asarray([run["matched_row_level"]["metrics"]["macro_f1"] for run in runs], dtype=np.float64)
    binary = np.asarray([run["matched_row_level"]["metrics"]["binary_f1"] for run in runs], dtype=np.float64)
    far = np.asarray([run["matched_row_level"]["protocol"].get("binary", {}).get("far_percent", np.nan) for run in runs], dtype=np.float64)
    mar = np.asarray([run["matched_row_level"]["protocol"].get("binary", {}).get("mar_percent", np.nan) for run in runs], dtype=np.float64)
    return {
        "macro_f1_mean": float(np.nanmean(macro)),
        "macro_f1_std": float(np.nanstd(macro, ddof=0)),
        "binary_f1_mean": float(np.nanmean(binary)),
        "binary_f1_std": float(np.nanstd(binary, ddof=0)),
        "far_percent_mean": float(np.nanmean(far)),
        "far_percent_std": float(np.nanstd(far, ddof=0)),
        "mar_percent_mean": float(np.nanmean(mar)),
        "mar_percent_std": float(np.nanstd(mar, ddof=0)),
    }


def build_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Anomaly Transformer Official-Source SKAB Wrapper",
        "",
        f"- Status: {payload['status']}",
        f"- Claim boundary: {payload['claim_boundary']}",
        "",
        "| Seed | Macro-F1 | Binary F1 | FAR% | MAR% | Train sec. |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for run in payload["runs"]:
        protocol = run["matched_row_level"]["protocol"].get("binary", {})
        lines.append(
            "| {seed} | {macro:.4f} | {binary:.4f} | {far:.2f} | {mar:.2f} | {sec:.2f} |".format(
                seed=run["seed"],
                macro=run["matched_row_level"]["metrics"]["macro_f1"],
                binary=run["matched_row_level"]["metrics"]["binary_f1"],
                far=protocol.get("far_percent", float("nan")),
                mar=protocol.get("mar_percent", float("nan")),
                sec=run["training"]["train_seconds"],
            )
        )
    lines.extend(["", "## Summary", "", "```json", json.dumps(payload.get("summary", {}), indent=2), "```", ""])
    return "\n".join(lines)


def run_wrapper(
    *,
    adapter_root: Path,
    checkout: Path,
    output: Path,
    seeds: Sequence[int],
    win_size: int,
    batch_size: int,
    epochs: int,
    learning_rate: float,
    k: float,
    d_model: int,
    n_heads: int,
    e_layers: int,
    d_ff: int,
    temperature: float,
    aggregation: str,
) -> dict[str, Any]:
    runs = [
        run_seed(
            seed=int(seed),
            adapter_root=adapter_root,
            checkout=checkout,
            win_size=win_size,
            batch_size=batch_size,
            epochs=epochs,
            learning_rate=learning_rate,
            k=k,
            d_model=d_model,
            n_heads=n_heads,
            e_layers=e_layers,
            d_ff=d_ff,
            temperature=temperature,
            aggregation=aggregation,
        )
        for seed in seeds
    ]
    payload = {
        "version": VERSION,
        "checked_on": CHECKED_ON,
        "status": "official_source_matched_wrapper_executed",
        "dataset": "SKAB",
        "baseline": "Anomaly Transformer",
        "official_commit": OFFICIAL_COMMIT,
        "adapter_root": str(adapter_root),
        "official_checkout": str(Path(checkout).resolve()),
        "claim_boundary": "Official source architecture with patched SKAB validation-only protocol; not an official Anomaly Transformer paper benchmark score.",
        "summary": _summarize_runs(runs),
        "runs": runs,
    }
    os.makedirs(_fs_path(Path(output).parent), exist_ok=True)
    with open(_fs_path(output), "w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    md_path = Path(output).with_suffix(".md")
    with open(_fs_path(md_path), "w", encoding="utf-8") as handle:
        handle.write(build_markdown(payload))
    return payload


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the verified official Anomaly Transformer source on prepared SKAB adapter files with validation-only thresholds.")
    parser.add_argument("--adapter-root", type=Path, default=DEFAULT_ADAPTER_ROOT)
    parser.add_argument("--checkout", type=Path, default=DEFAULT_CHECKOUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seeds", default="42")
    parser.add_argument("--win-size", type=int, default=48)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--k", type=float, default=3.0)
    parser.add_argument("--d-model", type=int, default=64)
    parser.add_argument("--n-heads", type=int, default=4)
    parser.add_argument("--e-layers", type=int, default=1)
    parser.add_argument("--d-ff", type=int, default=128)
    parser.add_argument("--temperature", type=float, default=50.0)
    parser.add_argument("--aggregation", choices=["max", "mean"], default="max")
    args = parser.parse_args(argv)
    payload = run_wrapper(
        adapter_root=args.adapter_root,
        checkout=args.checkout,
        output=args.output,
        seeds=_split_ints(args.seeds),
        win_size=int(args.win_size),
        batch_size=int(args.batch_size),
        epochs=int(args.epochs),
        learning_rate=float(args.learning_rate),
        k=float(args.k),
        d_model=int(args.d_model),
        n_heads=int(args.n_heads),
        e_layers=int(args.e_layers),
        d_ff=int(args.d_ff),
        temperature=float(args.temperature),
        aggregation=str(args.aggregation),
    )
    print(json.dumps({k: payload[k] for k in ["status", "summary", "claim_boundary"]}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
