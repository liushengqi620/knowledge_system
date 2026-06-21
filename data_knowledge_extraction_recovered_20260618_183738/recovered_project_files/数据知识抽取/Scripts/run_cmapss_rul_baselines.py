from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from run_public_ms_gse_rpf_experiment import (
    _limit_indices,
    apply_regime_prototype_residuals,
    build_causal_windows,
    build_rul_prediction_records,
    build_rul_targets,
    build_split,
    load_ready_task,
    resolve_torch_device,
    rul_regression_metrics,
    scale_windows,
    select_cmapss_terminal_rul_indices,
    summarize_rul_by_subset,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_READY_ROOT = PROJECT_ROOT / "knowledge_exports" / "public_benchmark_ready"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "knowledge_exports" / "cmapss_rul_matched_baselines"
DEEP_BASELINES = {"gru_sequence", "lstm_sequence", "tcn_sequence"}
PUBLISHED_STYLE_REFERENCES = {
    "lstm_sequence": "lstm_rul_2017",
}


def _fs_path(path: Path) -> str:
    if os.name == "nt":
        resolved = str(Path(path).resolve())
        if not resolved.startswith("\\\\?\\"):
            return "\\\\?\\" + resolved
    return str(path)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    os.makedirs(_fs_path(path.parent), exist_ok=True)
    with open(_fs_path(path), "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def _write_text(path: Path, text: str) -> None:
    os.makedirs(_fs_path(path.parent), exist_ok=True)
    with open(_fs_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def _split_seeds(value: str) -> list[int]:
    return [int(part.strip()) for part in value.replace(";", ",").split(",") if part.strip()]


def summarize_windows(windows: np.ndarray) -> np.ndarray:
    arr = np.asarray(windows, dtype=np.float32)
    last = arr[:, -1, :]
    mean = arr.mean(axis=1)
    std = arr.std(axis=1)
    delta = arr[:, -1, :] - arr[:, 0, :]
    min_v = arr.min(axis=1)
    max_v = arr.max(axis=1)
    return np.concatenate([last, mean, std, delta, min_v, max_v], axis=1).astype(np.float32)


class GRURULRegressor(nn.Module):
    def __init__(self, n_features: int, hidden_dim: int, layers: int, dropout: float) -> None:
        super().__init__()
        self.gru = nn.GRU(
            input_size=int(n_features),
            hidden_size=int(hidden_dim),
            num_layers=max(1, int(layers)),
            dropout=float(dropout) if int(layers) > 1 else 0.0,
            batch_first=True,
        )
        self.head = nn.Sequential(
            nn.LayerNorm(int(hidden_dim)),
            nn.Dropout(float(dropout)),
            nn.Linear(int(hidden_dim), int(hidden_dim)),
            nn.GELU(),
            nn.Linear(int(hidden_dim), 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _hidden = self.gru(x)
        return torch.sigmoid(self.head(out[:, -1, :])).squeeze(-1)


class LSTMRULRegressor(nn.Module):
    def __init__(self, n_features: int, hidden_dim: int, layers: int, dropout: float) -> None:
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=int(n_features),
            hidden_size=int(hidden_dim),
            num_layers=max(1, int(layers)),
            dropout=float(dropout) if int(layers) > 1 else 0.0,
            batch_first=True,
        )
        self.head = nn.Sequential(
            nn.LayerNorm(int(hidden_dim)),
            nn.Dropout(float(dropout)),
            nn.Linear(int(hidden_dim), int(hidden_dim)),
            nn.GELU(),
            nn.Linear(int(hidden_dim), 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _hidden = self.lstm(x)
        return torch.sigmoid(self.head(out[:, -1, :])).squeeze(-1)


class CausalTemporalBlock(nn.Module):
    def __init__(self, channels: int, kernel_size: int, dilation: int, dropout: float) -> None:
        super().__init__()
        padding = int(dilation) * (int(kernel_size) - 1)
        self.conv = nn.Conv1d(int(channels), int(channels), int(kernel_size), padding=padding, dilation=int(dilation))
        self.norm = nn.BatchNorm1d(int(channels))
        self.dropout = nn.Dropout(float(dropout))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        y = self.conv(x)
        y = y[:, :, : x.shape[-1]]
        y = self.dropout(F.gelu(self.norm(y)))
        return x + y


class TCNRULRegressor(nn.Module):
    def __init__(self, n_features: int, hidden_dim: int, layers: int, dropout: float) -> None:
        super().__init__()
        self.input_proj = nn.Conv1d(int(n_features), int(hidden_dim), kernel_size=1)
        blocks = [
            CausalTemporalBlock(int(hidden_dim), kernel_size=3, dilation=2 ** i, dropout=float(dropout))
            for i in range(max(1, int(layers)))
        ]
        self.blocks = nn.Sequential(*blocks)
        self.head = nn.Sequential(
            nn.LayerNorm(int(hidden_dim)),
            nn.Dropout(float(dropout)),
            nn.Linear(int(hidden_dim), int(hidden_dim)),
            nn.GELU(),
            nn.Linear(int(hidden_dim), 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        y = x.transpose(1, 2)
        y = self.blocks(self.input_proj(y))
        return torch.sigmoid(self.head(y[:, :, -1])).squeeze(-1)


def build_model(name: str, *, seed: int) -> Any:
    if name == "ridge_summary":
        return make_pipeline(StandardScaler(), Ridge(alpha=10.0))
    if name == "histgb_summary":
        return HistGradientBoostingRegressor(
            max_iter=350,
            learning_rate=0.045,
            max_leaf_nodes=31,
            l2_regularization=0.05,
            random_state=int(seed),
        )
    if name == "extra_trees_summary":
        return ExtraTreesRegressor(
            n_estimators=160,
            max_features=0.50,
            min_samples_leaf=2,
            n_jobs=-1,
            random_state=int(seed),
        )
    if name in DEEP_BASELINES:
        return None
    raise ValueError(f"Unknown C-MAPSS RUL baseline: {name}")


def build_deep_model(name: str, *, n_features: int, hidden_dim: int, layers: int, dropout: float) -> nn.Module:
    if name == "gru_sequence":
        return GRURULRegressor(n_features=n_features, hidden_dim=hidden_dim, layers=layers, dropout=dropout)
    if name == "lstm_sequence":
        return LSTMRULRegressor(n_features=n_features, hidden_dim=hidden_dim, layers=layers, dropout=dropout)
    if name == "tcn_sequence":
        return TCNRULRegressor(n_features=n_features, hidden_dim=hidden_dim, layers=layers, dropout=dropout)
    raise ValueError(f"Unknown deep C-MAPSS RUL baseline: {name}")


def _metric_mean(rows: Sequence[dict[str, Any]], key: str) -> float | None:
    values = [float(row[key]) for row in rows if row.get(key) is not None]
    return float(np.mean(values)) if values else None


def _metric_std(rows: Sequence[dict[str, Any]], key: str) -> float | None:
    values = [float(row[key]) for row in rows if row.get(key) is not None]
    return float(np.std(values)) if values else None


def _predict_deep(model: nn.Module, x: np.ndarray, *, batch_size: int, device: torch.device, rul_cap: float) -> np.ndarray:
    model.eval()
    chunks: list[np.ndarray] = []
    x_t = torch.from_numpy(np.asarray(x, dtype=np.float32))
    batch = max(8, int(batch_size))
    with torch.no_grad():
        for start in range(0, len(x_t), batch):
            pred = model(x_t[start : start + batch].to(device)).detach().cpu().numpy()
            chunks.append(pred)
    norm = np.concatenate(chunks).astype(np.float32)
    return np.clip(norm, 0.0, 1.0) * float(max(1.0, rul_cap))


def fit_deep_baseline(
    name: str,
    *,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray,
    y_val: np.ndarray,
    x_test: np.ndarray,
    seed: int,
    rul_cap: float,
    device: str,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    hidden_dim: int,
    layers: int,
    dropout: float,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    torch.manual_seed(int(seed))
    rng = np.random.default_rng(int(seed))
    train_device = resolve_torch_device(device)
    model = build_deep_model(
        name,
        n_features=int(x_train.shape[2]),
        hidden_dim=int(hidden_dim),
        layers=int(layers),
        dropout=float(dropout),
    ).to(train_device)
    opt = torch.optim.AdamW(model.parameters(), lr=float(learning_rate), weight_decay=1.0e-4)
    x_t = torch.from_numpy(np.asarray(x_train, dtype=np.float32)).to(train_device)
    cap = float(max(1.0, rul_cap))
    y_t = torch.from_numpy((np.clip(np.asarray(y_train, dtype=np.float32), 0.0, cap) / cap).astype(np.float32)).to(train_device)
    batch = max(8, min(int(batch_size), len(x_train)))
    best_state: dict[str, torch.Tensor] | None = None
    best_rmse = float("inf")
    losses: list[float] = []
    val_rmse_history: list[float] = []
    start_time = time.perf_counter()
    for _epoch in range(max(1, int(epochs))):
        order = rng.permutation(len(x_train))
        model.train()
        epoch_losses: list[float] = []
        for start in range(0, len(order), batch):
            idx = torch.from_numpy(order[start : start + batch].astype(np.int64)).to(train_device)
            opt.zero_grad()
            pred = model(x_t[idx])
            loss = F.mse_loss(pred, y_t[idx])
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 3.0)
            opt.step()
            epoch_losses.append(float(loss.detach().cpu().item()))
        losses.append(float(np.mean(epoch_losses)) if epoch_losses else 0.0)
        val_pred = _predict_deep(model, x_val, batch_size=batch, device=train_device, rul_cap=cap)
        val_metrics = rul_regression_metrics(y_val, val_pred) or {}
        val_rmse = float(val_metrics.get("rul_rmse", float("inf")))
        val_rmse_history.append(val_rmse)
        if val_rmse <= best_rmse:
            best_rmse = val_rmse
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
    train_seconds = max(1.0e-9, time.perf_counter() - start_time)
    if best_state is not None:
        model.load_state_dict(best_state)
    val_pred = _predict_deep(model, x_val, batch_size=batch, device=train_device, rul_cap=cap)
    test_pred = _predict_deep(model, x_test, batch_size=batch, device=train_device, rul_cap=cap)
    diagnostics = {
        "model_family": name,
        "published_style_reference": PUBLISHED_STYLE_REFERENCES.get(name),
        "published_alignment_status": "published_style_local_matched_not_exact_reproduction"
        if name in PUBLISHED_STYLE_REFERENCES
        else "local_matched_control",
        "parameters": int(sum(p.numel() for p in model.parameters() if p.requires_grad)),
        "device": str(train_device),
        "epochs": int(epochs),
        "batch_size": int(batch),
        "learning_rate": float(learning_rate),
        "hidden_dim": int(hidden_dim),
        "layers": int(layers),
        "dropout": float(dropout),
        "loss_tail": losses[-5:],
        "val_rul_rmse_history_tail": val_rmse_history[-5:],
        "best_val_rul_rmse": float(best_rmse),
        "train_seconds": float(train_seconds),
        "train_samples_per_second": float((len(x_train) * max(1, int(epochs))) / train_seconds),
    }
    return val_pred, test_pred, diagnostics


def run_one(
    *,
    baseline: str,
    seed: int,
    ready_root: Path,
    output_dir: Path,
    window_size: int,
    max_rows_per_split: int | None,
    rul_cap: float,
    use_regime_residuals: bool,
    regime_prototype_k: int,
    regime_healthy_stage_max: int,
    device: str = "auto",
    epochs: int = 25,
    batch_size: int = 256,
    learning_rate: float = 1.0e-3,
    hidden_dim: int = 64,
    layers: int = 2,
    dropout: float = 0.10,
) -> dict[str, Any]:
    task = load_ready_task(Path(ready_root), "cmapss", target="rul")
    split = build_split(task, seed=int(seed))
    train_idx = _limit_indices(split.train_idx, split.y_internal, seed=seed, limit=max_rows_per_split)
    val_idx = _limit_indices(split.val_idx, split.y_internal, seed=seed + 1, limit=max_rows_per_split)
    test_idx = select_cmapss_terminal_rul_indices(task, split.test_idx)
    model_task = task
    regime_diag: dict[str, Any] = {"enabled": False}
    if bool(use_regime_residuals):
        model_task, regime_diag = apply_regime_prototype_residuals(
            task,
            train_idx,
            split.y_internal,
            n_regimes=regime_prototype_k,
            healthy_stage_max=regime_healthy_stage_max,
            seed=seed,
        )
    windows = build_causal_windows(model_task, window_size=window_size)
    x_train, x_val, x_test = scale_windows(windows, train_idx=train_idx, val_idx=val_idx, test_idx=test_idx)
    rul_all = build_rul_targets(task)
    if rul_all is None:
        raise ValueError("C-MAPSS ready task is missing RUL targets.")
    y_train_raw = np.asarray(rul_all[train_idx], dtype=np.float32)
    y_val = np.asarray(rul_all[val_idx], dtype=np.float32)
    y_test = np.asarray(rul_all[test_idx], dtype=np.float32)
    y_train = np.clip(y_train_raw, 0.0, float(max(1.0, rul_cap))).astype(np.float32)
    baseline_diagnostics: dict[str, Any]
    if baseline in DEEP_BASELINES:
        val_pred, test_pred, baseline_diagnostics = fit_deep_baseline(
            baseline,
            x_train=x_train,
            y_train=y_train_raw,
            x_val=x_val,
            y_val=y_val,
            x_test=x_test,
            seed=seed,
            rul_cap=rul_cap,
            device=device,
            epochs=epochs,
            batch_size=batch_size,
            learning_rate=learning_rate,
            hidden_dim=hidden_dim,
            layers=layers,
            dropout=dropout,
        )
        feature_dim = int(x_train.shape[2])
    else:
        x_train_feat = summarize_windows(x_train)
        x_val_feat = summarize_windows(x_val)
        x_test_feat = summarize_windows(x_test)
        model = build_model(baseline, seed=seed)
        start = time.perf_counter()
        model.fit(x_train_feat, y_train)
        train_seconds = max(1.0e-9, time.perf_counter() - start)
        val_pred = np.clip(np.asarray(model.predict(x_val_feat), dtype=np.float32), 0.0, float(max(1.0, rul_cap)))
        test_pred = np.clip(np.asarray(model.predict(x_test_feat), dtype=np.float32), 0.0, float(max(1.0, rul_cap)))
        baseline_diagnostics = {
            "model_family": baseline,
            "device": "cpu",
            "train_seconds": float(train_seconds),
            "train_samples_per_second": float(len(train_idx) / train_seconds),
        }
        feature_dim = int(x_train_feat.shape[1])
    val_metrics = rul_regression_metrics(y_val, val_pred)
    test_metrics = rul_regression_metrics(y_test, test_pred)
    records = build_rul_prediction_records(
        task.meta,
        test_idx,
        y_test,
        test_pred,
        prediction_source=baseline,
    )
    result = {
        "status": "ok",
        "dataset": "cmapss",
        "target": "rul",
        "baseline": baseline,
        "seed": int(seed),
        "protocol": "matched_terminal_test_unit_rul_baseline",
        "window_size": int(window_size),
        "rul_cap": float(rul_cap),
        "train_size": int(len(train_idx)),
        "val_size": int(len(val_idx)),
        "test_size": int(len(test_idx)),
        "feature_dim": int(feature_dim),
        "split_protocol": split.split_protocol,
        "rul_eval_protocol": "terminal_test_unit",
        "regime_prototype": regime_diag,
        "baseline_diagnostics": baseline_diagnostics,
        "train_seconds": float(baseline_diagnostics.get("train_seconds", 0.0)),
        "train_samples_per_second": float(baseline_diagnostics.get("train_samples_per_second", 0.0)),
        "val_rul_metrics": val_metrics,
        "primary_test_metrics": test_metrics,
        "rul_prediction_records": records,
        "rul_subset_metrics": summarize_rul_by_subset(records),
    }
    path = Path(output_dir) / baseline / f"cmapss_rul_{baseline}_seed{int(seed)}.json"
    _write_json(path, result)
    return result


def summarize_results(results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    by_name: dict[str, list[dict[str, Any]]] = {}
    for result in results:
        by_name.setdefault(str(result["baseline"]), []).append(result)
    rows: list[dict[str, Any]] = []
    subset_rows: list[dict[str, Any]] = []
    for name, group in sorted(by_name.items()):
        metric_rows = [dict(item["primary_test_metrics"], seed=item["seed"]) for item in group]
        rows.append(
            {
                "baseline": name,
                "n_seeds": int(len(group)),
                "rmse_mean": _metric_mean(metric_rows, "rul_rmse"),
                "rmse_std": _metric_std(metric_rows, "rul_rmse"),
                "mae_mean": _metric_mean(metric_rows, "rul_mae"),
                "mae_std": _metric_std(metric_rows, "rul_mae"),
                "score_mean": _metric_mean(metric_rows, "rul_score"),
                "score_std": _metric_std(metric_rows, "rul_score"),
                "train_seconds_mean": float(np.mean([float(item["train_seconds"]) for item in group])),
            }
        )
        subsets = sorted(
            {
                str(row.get("subset"))
                for item in group
                for row in (item.get("rul_subset_metrics") or {}).get("rows", [])
            }
        )
        for subset in subsets:
            group_rows = [
                row
                for item in group
                for row in (item.get("rul_subset_metrics") or {}).get("rows", [])
                if str(row.get("subset")) == subset
            ]
            subset_rows.append(
                {
                    "baseline": name,
                    "subset": subset,
                    "n_seeds": int(len(group_rows)),
                    "rmse_mean": _metric_mean(group_rows, "rul_rmse"),
                    "rmse_std": _metric_std(group_rows, "rul_rmse"),
                    "mae_mean": _metric_mean(group_rows, "rul_mae"),
                    "score_mean": _metric_mean(group_rows, "rul_score"),
                }
            )
    return {"schema": "cmapss_rul_matched_baselines_v1", "overall": rows, "subset_summary": subset_rows}


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# C-MAPSS Matched RUL Baselines",
        "",
        "All baselines use the same ready data, grouped train/validation split, terminal test-unit evaluation, capped RUL supervision, and window-summary features.",
        "",
        "## Overall",
        "",
        "| Baseline | Seeds | RMSE mean | RMSE std | MAE mean | Score mean | Train seconds mean |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary["overall"]:
        lines.append(
            "| {baseline} | {n_seeds} | {rmse:.4f} | {rmse_std:.4f} | {mae:.4f} | {score:.2f} | {train:.2f} |".format(
                baseline=row["baseline"],
                n_seeds=int(row["n_seeds"]),
                rmse=float(row["rmse_mean"] or 0.0),
                rmse_std=float(row["rmse_std"] or 0.0),
                mae=float(row["mae_mean"] or 0.0),
                score=float(row["score_mean"] or 0.0),
                train=float(row["train_seconds_mean"] or 0.0),
            )
        )
    lines.extend(["", "## Subset Summary", "", "| Baseline | Subset | RMSE mean | RMSE std | MAE mean | Score mean |", "|---|---|---:|---:|---:|---:|"])
    for row in summary["subset_summary"]:
        lines.append(
            "| {baseline} | {subset} | {rmse:.4f} | {rmse_std:.4f} | {mae:.4f} | {score:.2f} |".format(
                baseline=row["baseline"],
                subset=row["subset"],
                rmse=float(row["rmse_mean"] or 0.0),
                rmse_std=float(row["rmse_std"] or 0.0),
                mae=float(row["mae_mean"] or 0.0),
                score=float(row["score_mean"] or 0.0),
            )
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ready-root", type=Path, default=DEFAULT_READY_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--seeds", type=str, default="42,43,44")
    parser.add_argument("--baselines", type=str, default="ridge_summary,histgb_summary,extra_trees_summary")
    parser.add_argument("--window-size", type=int, default=80)
    parser.add_argument("--max-rows-per-split", type=int, default=12000)
    parser.add_argument("--rul-cap", type=float, default=125.0)
    parser.add_argument("--use-regime-prototype-residuals", action="store_true")
    parser.add_argument("--regime-prototype-k", type=int, default=6)
    parser.add_argument("--regime-healthy-stage-max", type=int, default=0)
    parser.add_argument("--device", type=str, default="auto")
    parser.add_argument("--epochs", type=int, default=25)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--learning-rate", type=float, default=1.0e-3)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--layers", type=int, default=2)
    parser.add_argument("--dropout", type=float, default=0.10)
    args = parser.parse_args()

    seeds = _split_seeds(args.seeds)
    baselines = [part.strip() for part in str(args.baselines).replace(";", ",").split(",") if part.strip()]
    results = []
    for baseline in baselines:
        for seed in seeds:
            result = run_one(
                baseline=baseline,
                seed=int(seed),
                ready_root=Path(args.ready_root),
                output_dir=Path(args.output_dir),
                window_size=int(args.window_size),
                max_rows_per_split=int(args.max_rows_per_split) if int(args.max_rows_per_split) > 0 else None,
                rul_cap=float(args.rul_cap),
                use_regime_residuals=bool(args.use_regime_prototype_residuals),
                regime_prototype_k=int(args.regime_prototype_k),
                regime_healthy_stage_max=int(args.regime_healthy_stage_max),
                device=str(args.device),
                epochs=int(args.epochs),
                batch_size=int(args.batch_size),
                learning_rate=float(args.learning_rate),
                hidden_dim=int(args.hidden_dim),
                layers=int(args.layers),
                dropout=float(args.dropout),
            )
            metrics = result["primary_test_metrics"]
            print(
                f"{baseline} seed={seed} rmse={metrics['rul_rmse']:.4f} "
                f"mae={metrics['rul_mae']:.4f} score={metrics['rul_score']:.2f}"
            )
            results.append(result)
    summary = summarize_results(results)
    _write_json(Path(args.output_dir) / "cmapss_rul_matched_baselines_summary.json", summary)
    _write_text(Path(args.output_dir) / "cmapss_rul_matched_baselines_summary.md", render_markdown(summary))
    print(str(Path(args.output_dir) / "cmapss_rul_matched_baselines_summary.json"))
    print(str(Path(args.output_dir) / "cmapss_rul_matched_baselines_summary.md"))


if __name__ == "__main__":
    main()
