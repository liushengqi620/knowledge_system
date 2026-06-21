from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from multiclass_event_evaluation import summarize_multiclass_event_evaluation
from tep_sequence_heads import (
    DEFAULT_TEP_DATASET_DIR,
    build_event_horizons,
    build_event_ids,
    load_class_mapping,
    load_multiclass_dataset,
    prepare_sequence_split,
)


VERSION = "graph-wavenet-official-source-tep-wrapper-v1"
CHECKED_ON = "2026-06-21"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CHECKOUT = Path.home() / "aaai_external_baseline_checkouts" / "graph_wavenet"
DEFAULT_OUTPUT = (
    PROJECT_ROOT
    / "knowledge_exports"
    / "external_baseline_protocol_runs"
    / "graph_wavenet_official_tep_wrapper_smoke.json"
)
OFFICIAL_COMMIT = "6b162e80c59a"


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


def _resolve_device(device: str | torch.device | None) -> torch.device:
    if device is None or str(device).lower() == "auto":
        return torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    return torch.device(device)


def _load_official_gwnet(checkout: Path):
    model_path = Path(checkout).resolve() / "model.py"
    if not model_path.exists():
        raise FileNotFoundError(f"Official Graph WaveNet model.py not found: {model_path}")
    spec = importlib.util.spec_from_file_location("official_graph_wavenet_model", _fs_path(model_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load official Graph WaveNet model from {model_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.gwnet


def _class_weights(labels: np.ndarray, n_classes: int) -> torch.Tensor:
    y = np.asarray(labels, dtype=np.int64).reshape(-1)
    counts = np.bincount(y, minlength=int(n_classes)).astype(np.float64)
    counts = np.maximum(counts, 1.0)
    weights = counts.sum() / (counts * float(n_classes))
    weights = weights / np.mean(weights)
    return torch.tensor(weights, dtype=torch.float32)


def _macro_f1(y_true: np.ndarray, y_pred: np.ndarray, *, class_ids: Sequence[int] | None = None) -> float:
    y = np.asarray(y_true, dtype=np.int64).reshape(-1)
    pred = np.asarray(y_pred, dtype=np.int64).reshape(-1)
    ids = sorted(set(y.tolist()) | set(pred.tolist())) if class_ids is None else [int(x) for x in class_ids]
    f1s: list[float] = []
    for class_id in ids:
        tp = float(np.sum((y == class_id) & (pred == class_id)))
        fp = float(np.sum((y != class_id) & (pred == class_id)))
        fn = float(np.sum((y == class_id) & (pred != class_id)))
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1s.append(2.0 * precision * recall / (precision + recall) if (precision + recall) else 0.0)
    return float(np.mean(f1s)) if f1s else 0.0


def _target_defect_macro_f1(y_true: np.ndarray, y_pred: np.ndarray, n_classes: int) -> float:
    abnormal = [class_id for class_id in range(int(n_classes)) if class_id != 0 and np.any(np.asarray(y_true) == class_id)]
    return _macro_f1(y_true, y_pred, class_ids=abnormal) if abnormal else 0.0


def _identity_support(num_nodes: int, device: torch.device) -> list[torch.Tensor]:
    return [torch.eye(int(num_nodes), dtype=torch.float32, device=device)]


def _kernel_pair(value: Any) -> tuple[int, int]:
    if isinstance(value, tuple):
        if len(value) == 2:
            return int(value[0]), int(value[1])
        if len(value) == 1:
            return 1, int(value[0])
    scalar = int(value)
    return 1, scalar


def _same_pair(value: Any) -> tuple[int, int]:
    if isinstance(value, tuple):
        if len(value) == 2:
            return int(value[0]), int(value[1])
        if len(value) == 1:
            first = int(value[0])
            return first, first
    scalar = int(value)
    return scalar, scalar


def _conv1d_to_conv2d(module: nn.Conv1d) -> nn.Conv2d:
    conv = nn.Conv2d(
        in_channels=int(module.in_channels),
        out_channels=int(module.out_channels),
        kernel_size=_kernel_pair(module.kernel_size),
        stride=_same_pair(module.stride),
        padding=_same_pair(module.padding),
        dilation=_same_pair(module.dilation),
        groups=int(module.groups),
        bias=module.bias is not None,
        padding_mode=str(module.padding_mode),
    )
    with torch.no_grad():
        conv.weight.copy_(module.weight)
        if module.bias is not None and conv.bias is not None:
            conv.bias.copy_(module.bias)
    return conv


def patch_official_graph_wavenet_conv1d_modules(backbone: nn.Module) -> dict[str, Any]:
    """Modern PyTorch compatibility patch for the official source's 4D forward path."""

    patched: dict[str, int] = {}
    for name in ("gate_convs", "residual_convs", "skip_convs"):
        modules = getattr(backbone, name, None)
        if modules is None:
            continue
        count = 0
        for idx, module in enumerate(list(modules)):
            if isinstance(module, nn.Conv1d):
                modules[idx] = _conv1d_to_conv2d(module)
                count += 1
        patched[name] = count
    return {
        "enabled": any(count > 0 for count in patched.values()),
        "reason": "official source defines Conv1d modules on a 4D [batch, channel, node, time] forward path",
        "replacement": "Conv1d modules are replaced with shape-equivalent Conv2d modules and copied weights",
        "patched_module_counts": patched,
    }


class OfficialGraphWaveNetClassifier(nn.Module):
    def __init__(
        self,
        official_gwnet_cls,
        *,
        device: torch.device,
        num_nodes: int,
        n_classes: int,
        encoder_dim: int = 16,
        residual_channels: int = 16,
        dilation_channels: int = 16,
        skip_channels: int = 64,
        end_channels: int = 128,
        blocks: int = 2,
        layers: int = 2,
        dropout: float = 0.1,
        adaptive_only: bool = True,
        classifier_dropout: float = 0.1,
    ) -> None:
        super().__init__()
        supports = None if bool(adaptive_only) else _identity_support(num_nodes, device)
        aptinit = None if bool(adaptive_only) else supports[0]
        self.backbone = official_gwnet_cls(
            device,
            int(num_nodes),
            dropout=float(dropout),
            supports=supports,
            gcn_bool=True,
            addaptadj=True,
            aptinit=aptinit,
            in_dim=1,
            out_dim=int(encoder_dim),
            residual_channels=int(residual_channels),
            dilation_channels=int(dilation_channels),
            skip_channels=int(skip_channels),
            end_channels=int(end_channels),
            blocks=int(blocks),
            layers=int(layers),
        )
        self.compatibility_patch = patch_official_graph_wavenet_conv1d_modules(self.backbone)
        self.classifier = nn.Sequential(
            nn.LayerNorm(int(encoder_dim)),
            nn.Dropout(float(classifier_dropout)),
            nn.Linear(int(encoder_dim), int(n_classes)),
        )
        self.model_family = "official_graph_wavenet_adaptive_adjacency_backbone_plus_lightweight_classifier"

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        graph_input = x.permute(0, 2, 1).unsqueeze(1)
        encoded = self.backbone(graph_input)
        if encoded.ndim != 4:
            raise RuntimeError("Official Graph WaveNet backbone must return [batch, channels, nodes, time]")
        pooled = encoded.mean(dim=(2, 3))
        return self.classifier(pooled)


def _adaptive_adjacency_summary(model: OfficialGraphWaveNetClassifier) -> dict[str, Any]:
    backbone = model.backbone
    if not hasattr(backbone, "nodevec1") or not hasattr(backbone, "nodevec2"):
        return {"adaptive_adjacency_available": False}
    with torch.no_grad():
        adj = torch.softmax(torch.relu(torch.mm(backbone.nodevec1, backbone.nodevec2)), dim=1).detach().cpu().numpy()
    return {
        "adaptive_adjacency_available": True,
        "shape": [int(adj.shape[0]), int(adj.shape[1])],
        "mean": float(np.mean(adj)),
        "std": float(np.std(adj)),
        "max": float(np.max(adj)),
        "row_sum_min": float(np.min(np.sum(adj, axis=1))),
        "row_sum_max": float(np.max(np.sum(adj, axis=1))),
    }


def _predict_proba(model: nn.Module, x: np.ndarray, *, device: torch.device, batch_size: int) -> np.ndarray:
    model.eval()
    loader = DataLoader(TensorDataset(torch.from_numpy(np.asarray(x, dtype=np.float32))), batch_size=int(batch_size), shuffle=False)
    chunks: list[np.ndarray] = []
    with torch.no_grad():
        for (batch_x,) in loader:
            logits = model(batch_x.to(device))
            chunks.append(torch.softmax(logits, dim=1).detach().cpu().numpy())
    return np.vstack(chunks).astype(np.float64)


@dataclass
class TrainResult:
    val_proba: np.ndarray
    test_proba: np.ndarray
    diagnostics: dict[str, Any]


def train_official_graph_wavenet_classifier(
    official_gwnet_cls,
    *,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray,
    y_val: np.ndarray,
    x_test: np.ndarray,
    n_classes: int,
    batch_size: int,
    epochs: int,
    learning_rate: float,
    seed: int,
    device: str | torch.device | None,
    encoder_dim: int,
    residual_channels: int,
    dilation_channels: int,
    skip_channels: int,
    end_channels: int,
    blocks: int,
    layers: int,
    dropout: float,
    adaptive_only: bool,
    classifier_dropout: float,
) -> TrainResult:
    _seed_everything(int(seed))
    actual_device = _resolve_device(device)
    if actual_device.type == "cpu":
        torch.set_num_threads(1)
    model = OfficialGraphWaveNetClassifier(
        official_gwnet_cls,
        device=actual_device,
        num_nodes=int(x_train.shape[2]),
        n_classes=int(n_classes),
        encoder_dim=int(encoder_dim),
        residual_channels=int(residual_channels),
        dilation_channels=int(dilation_channels),
        skip_channels=int(skip_channels),
        end_channels=int(end_channels),
        blocks=int(blocks),
        layers=int(layers),
        dropout=float(dropout),
        adaptive_only=bool(adaptive_only),
        classifier_dropout=float(classifier_dropout),
    ).to(actual_device)
    opt = torch.optim.AdamW(model.parameters(), lr=float(learning_rate), weight_decay=1e-4)
    loss_fn = nn.CrossEntropyLoss(weight=_class_weights(y_train, n_classes).to(actual_device))
    dataset = TensorDataset(torch.from_numpy(np.asarray(x_train, dtype=np.float32)), torch.from_numpy(np.asarray(y_train, dtype=np.int64)))
    generator = torch.Generator()
    generator.manual_seed(int(seed))
    loader = DataLoader(dataset, batch_size=max(16, min(int(batch_size), len(dataset))), shuffle=True, generator=generator)

    best_state = copy.deepcopy(model.state_dict())
    best_target = -1.0
    best_macro = -1.0
    history: list[dict[str, float]] = []
    train_started = time.perf_counter()
    for epoch in range(max(1, int(epochs))):
        model.train()
        losses: list[float] = []
        epoch_started = time.perf_counter()
        for batch_x, batch_y in loader:
            opt.zero_grad()
            logits = model(batch_x.to(actual_device))
            loss = loss_fn(logits, batch_y.to(actual_device))
            loss.backward()
            opt.step()
            losses.append(float(loss.detach().cpu().item()))
        val_proba_epoch = _predict_proba(model, x_val, device=actual_device, batch_size=int(batch_size))
        val_pred = val_proba_epoch.argmax(axis=1)
        target = _target_defect_macro_f1(y_val, val_pred, int(n_classes))
        macro = _macro_f1(y_val, val_pred, class_ids=list(range(int(n_classes))))
        if target > best_target + 1e-12 or (abs(target - best_target) <= 1e-12 and macro > best_macro):
            best_target = float(target)
            best_macro = float(macro)
            best_state = copy.deepcopy(model.state_dict())
        history.append(
            {
                "epoch": float(epoch + 1),
                "train_loss": float(np.mean(losses)) if losses else 0.0,
                "validation_target_defect_macro_f1": float(target),
                "validation_macro_f1": float(macro),
                "epoch_seconds": float(time.perf_counter() - epoch_started),
            }
        )
    model.load_state_dict(best_state)
    train_seconds = float(time.perf_counter() - train_started)
    val_proba = _predict_proba(model, x_val, device=actual_device, batch_size=int(batch_size))
    test_started = time.perf_counter()
    test_proba = _predict_proba(model, x_test, device=actual_device, batch_size=int(batch_size))
    test_seconds = float(time.perf_counter() - test_started)
    parameters = int(sum(p.numel() for p in model.parameters() if p.requires_grad))
    return TrainResult(
        val_proba=val_proba,
        test_proba=test_proba,
        diagnostics={
            "device": str(actual_device),
            "model_family": model.model_family,
            "parameters": int(parameters),
            "epochs": int(epochs),
            "best_validation_target_defect_macro_f1": float(best_target),
            "best_validation_macro_f1": float(best_macro),
            "history": history,
            "train_seconds": train_seconds,
            "train_samples_per_second": float((len(y_train) * max(1, int(epochs))) / max(train_seconds, 1e-12)),
            "test_inference_seconds": test_seconds,
            "test_inference_samples_per_second": float(len(x_test) / max(test_seconds, 1e-12)) if len(x_test) else 0.0,
            "adaptive_adjacency": _adaptive_adjacency_summary(model),
            "official_source_compatibility_patch": model.compatibility_patch,
        },
    )


def _evaluate_tep(
    *,
    dataset_dir: Path,
    max_rows: int | None,
    seed: int,
    y_test: np.ndarray,
    test_proba: np.ndarray,
    idx_test: np.ndarray,
    class_names: Sequence[str],
) -> dict[str, Any]:
    _x, y_meta, _labels = load_multiclass_dataset(
        dataset_dir,
        max_rows=max_rows,
        sample_mode="stratified",
        seed=int(seed),
        feature_set="raw",
    )
    event_ids = (
        y_meta.iloc[idx_test]["event_bag_id"].astype(str).to_numpy(dtype=object)
        if "event_bag_id" in y_meta.columns
        else build_event_ids(y_test)
    )
    horizons = (
        pd.to_numeric(y_meta.iloc[idx_test]["lead_horizon_min"], errors="coerce").fillna(-1.0).to_numpy(dtype=float)
        if "lead_horizon_min" in y_meta.columns
        else build_event_horizons(y_test)
    )
    evaluation = summarize_multiclass_event_evaluation(
        y_test,
        test_proba,
        class_names=class_names,
        event_ids=event_ids,
        horizons=horizons,
        top_paths_by_class={},
    )
    pred = np.asarray(test_proba).argmax(axis=1)
    evaluation["sample_multiclass_metrics"]["target_defect_macro_f1"] = _target_defect_macro_f1(
        y_test,
        pred,
        len(class_names),
    )
    return evaluation


def run_seed(
    *,
    seed: int,
    dataset_dir: Path,
    checkout: Path,
    max_rows: int | None,
    window_size: int,
    batch_size: int,
    epochs: int,
    learning_rate: float,
    encoder_dim: int,
    residual_channels: int,
    dilation_channels: int,
    skip_channels: int,
    end_channels: int,
    blocks: int,
    layers: int,
    dropout: float,
    adaptive_only: bool,
    classifier_dropout: float,
    device: str | torch.device | None,
) -> dict[str, Any]:
    _seed_everything(int(seed))
    class_ids, class_names = load_class_mapping(dataset_dir)
    split = prepare_sequence_split(
        dataset_dir,
        max_rows=max_rows,
        sample_mode="stratified",
        seed=int(seed),
        window_size=int(window_size),
    )
    official_gwnet_cls = _load_official_gwnet(checkout)
    train_result = train_official_graph_wavenet_classifier(
        official_gwnet_cls,
        x_train=split.x_train,
        y_train=split.y_train,
        x_val=split.x_val,
        y_val=split.y_val,
        x_test=split.x_test,
        n_classes=len(class_ids),
        batch_size=int(batch_size),
        epochs=int(epochs),
        learning_rate=float(learning_rate),
        seed=int(seed),
        device=device,
        encoder_dim=int(encoder_dim),
        residual_channels=int(residual_channels),
        dilation_channels=int(dilation_channels),
        skip_channels=int(skip_channels),
        end_channels=int(end_channels),
        blocks=int(blocks),
        layers=int(layers),
        dropout=float(dropout),
        adaptive_only=bool(adaptive_only),
        classifier_dropout=float(classifier_dropout),
    )
    evaluation = _evaluate_tep(
        dataset_dir=dataset_dir,
        max_rows=max_rows,
        seed=int(seed),
        y_test=split.y_test,
        test_proba=train_result.test_proba,
        idx_test=split.idx_test,
        class_names=class_names,
    )
    val_pred = train_result.val_proba.argmax(axis=1)
    return {
        "seed": int(seed),
        "dataset": "TEP",
        "official_checkout": str(Path(checkout).resolve()),
        "official_commit": OFFICIAL_COMMIT,
        "config": {
            "max_rows": int(max_rows) if max_rows is not None else None,
            "window_size": int(window_size),
            "batch_size": int(batch_size),
            "epochs": int(epochs),
            "learning_rate": float(learning_rate),
            "encoder_dim": int(encoder_dim),
            "residual_channels": int(residual_channels),
            "dilation_channels": int(dilation_channels),
            "skip_channels": int(skip_channels),
            "end_channels": int(end_channels),
            "blocks": int(blocks),
            "layers": int(layers),
            "dropout": float(dropout),
            "adaptive_only": bool(adaptive_only),
            "classifier_dropout": float(classifier_dropout),
        },
        "row_counts": {
            "train_rows": int(len(split.y_train)),
            "val_rows": int(len(split.y_val)),
            "test_rows": int(len(split.y_test)),
            "n_features": int(len(split.feature_cols)),
            "n_classes": int(len(class_ids)),
        },
        "validation": {
            "target_defect_macro_f1": _target_defect_macro_f1(split.y_val, val_pred, len(class_ids)),
            "macro_f1": _macro_f1(split.y_val, val_pred, class_ids=list(range(len(class_ids)))),
        },
        "training": train_result.diagnostics,
        "sample_multiclass_metrics": evaluation["sample_multiclass_metrics"],
        "event_warning_metrics": evaluation["event_warning_metrics"],
        "path_explanation_metrics": evaluation["path_explanation_metrics"],
        "protocol_alignment": {
            "official_source_backbone_used": True,
            "official_external_score": False,
            "official_native_task": "spatial-temporal traffic forecasting",
            "task_specific_head_added": True,
            "modern_pytorch_conv_compatibility_patch": True,
            "validation_only_model_selection": True,
            "test_labels_used_for_model_selection": False,
            "claim_boundary": "Official Graph WaveNet source backbone adapted with a lightweight TEP classification head; not an official Graph WaveNet paper benchmark score.",
        },
    }


def _mean_std(values: Sequence[float]) -> dict[str, float]:
    arr = np.asarray(values, dtype=np.float64)
    return {"mean": float(np.mean(arr)), "std": float(np.std(arr, ddof=0))}


def summarize_runs(runs: list[dict[str, Any]]) -> dict[str, Any]:
    if not runs:
        return {}
    return {
        "target_defect_macro_f1": _mean_std([run["sample_multiclass_metrics"]["target_defect_macro_f1"] for run in runs]),
        "macro_f1": _mean_std([run["sample_multiclass_metrics"]["macro_f1"] for run in runs]),
        "event_macro_recall": _mean_std([run["event_warning_metrics"]["event_macro_recall"] for run in runs]),
        "train_seconds": _mean_std([run["training"]["train_seconds"] for run in runs]),
    }


def build_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Graph WaveNet Official-Source TEP Wrapper",
        "",
        f"- Status: {payload['status']}",
        f"- Claim boundary: {payload['claim_boundary']}",
        "",
        "| Seed | Target-F1 | Macro-F1 | Event Macro-Recall | Train sec. |",
        "|---|---:|---:|---:|---:|",
    ]
    for run in payload["runs"]:
        lines.append(
            "| {seed} | {target:.4f} | {macro:.4f} | {event:.4f} | {sec:.2f} |".format(
                seed=run["seed"],
                target=run["sample_multiclass_metrics"]["target_defect_macro_f1"],
                macro=run["sample_multiclass_metrics"]["macro_f1"],
                event=run["event_warning_metrics"]["event_macro_recall"],
                sec=run["training"]["train_seconds"],
            )
        )
    lines.extend(["", "## Summary", "", "```json", json.dumps(payload.get("summary", {}), indent=2), "```", ""])
    return "\n".join(lines)


def run_wrapper(
    *,
    dataset_dir: Path,
    checkout: Path,
    output: Path,
    seeds: Sequence[int],
    max_rows: int | None,
    window_size: int,
    batch_size: int,
    epochs: int,
    learning_rate: float,
    encoder_dim: int,
    residual_channels: int,
    dilation_channels: int,
    skip_channels: int,
    end_channels: int,
    blocks: int,
    layers: int,
    dropout: float,
    adaptive_only: bool,
    classifier_dropout: float,
    device: str | torch.device | None,
) -> dict[str, Any]:
    runs = [
        run_seed(
            seed=int(seed),
            dataset_dir=dataset_dir,
            checkout=checkout,
            max_rows=max_rows,
            window_size=int(window_size),
            batch_size=int(batch_size),
            epochs=int(epochs),
            learning_rate=float(learning_rate),
            encoder_dim=int(encoder_dim),
            residual_channels=int(residual_channels),
            dilation_channels=int(dilation_channels),
            skip_channels=int(skip_channels),
            end_channels=int(end_channels),
            blocks=int(blocks),
            layers=int(layers),
            dropout=float(dropout),
            adaptive_only=bool(adaptive_only),
            classifier_dropout=float(classifier_dropout),
            device=device,
        )
        for seed in seeds
    ]
    payload = {
        "version": VERSION,
        "checked_on": CHECKED_ON,
        "status": "official_source_adapted_wrapper_executed",
        "dataset": "TEP",
        "baseline": "Graph WaveNet",
        "official_commit": OFFICIAL_COMMIT,
        "official_checkout": str(Path(checkout).resolve()),
        "claim_boundary": "Official Graph WaveNet source backbone adapted with a lightweight TEP classification head; not an official Graph WaveNet paper benchmark score.",
        "summary": summarize_runs(runs),
        "runs": runs,
    }
    os.makedirs(_fs_path(Path(output).parent), exist_ok=True)
    with open(_fs_path(output), "w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    with open(_fs_path(Path(output).with_suffix(".md")), "w", encoding="utf-8") as handle:
        handle.write(build_markdown(payload))
    return payload


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run official-source Graph WaveNet with a lightweight TEP classification head.")
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_TEP_DATASET_DIR)
    parser.add_argument("--checkout", type=Path, default=DEFAULT_CHECKOUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seeds", default="42")
    parser.add_argument("--max-rows", type=int, default=600)
    parser.add_argument("--window-size", type=int, default=16)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--encoder-dim", type=int, default=16)
    parser.add_argument("--residual-channels", type=int, default=16)
    parser.add_argument("--dilation-channels", type=int, default=16)
    parser.add_argument("--skip-channels", type=int, default=64)
    parser.add_argument("--end-channels", type=int, default=128)
    parser.add_argument("--blocks", type=int, default=2)
    parser.add_argument("--layers", type=int, default=2)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--classifier-dropout", type=float, default=0.1)
    parser.add_argument("--device", type=str, default="auto")
    parser.add_argument("--use-identity-support", action="store_true")
    args = parser.parse_args(argv)
    payload = run_wrapper(
        dataset_dir=args.dataset_dir,
        checkout=args.checkout,
        output=args.output,
        seeds=_split_ints(args.seeds),
        max_rows=int(args.max_rows) if int(args.max_rows) > 0 else None,
        window_size=int(args.window_size),
        batch_size=int(args.batch_size),
        epochs=int(args.epochs),
        learning_rate=float(args.learning_rate),
        encoder_dim=int(args.encoder_dim),
        residual_channels=int(args.residual_channels),
        dilation_channels=int(args.dilation_channels),
        skip_channels=int(args.skip_channels),
        end_channels=int(args.end_channels),
        blocks=int(args.blocks),
        layers=int(args.layers),
        dropout=float(args.dropout),
        adaptive_only=not bool(args.use_identity_support),
        classifier_dropout=float(args.classifier_dropout),
        device=str(args.device),
    )
    print(json.dumps({k: payload[k] for k in ["status", "summary", "claim_boundary"]}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
