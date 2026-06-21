from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from cmapss_mdfa_source_profile import MDFA_SOURCE, SUBSETS
from run_public_ms_gse_rpf_experiment import resolve_torch_device, rul_regression_metrics, summarize_rul_by_subset


PROJECT_ROOT = Path(__file__).absolute().parents[1]
DEFAULT_RAW_DIR = PROJECT_ROOT / "knowledge_exports" / "public_datasets" / "cmapss" / "raw" / "extracted"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "knowledge_exports" / "cmapss_mdfa_source_matched"
VERSION = "cmapss-mdfa-source-matched-runner-v1"
SENSOR_NAMES = [f"s{i}" for i in range(1, 22)]
RAW_FEATURE_NAMES = ["setting1", "setting2", "setting3"] + SENSOR_NAMES
COMMON_DEGRADATION_SENSORS = [2, 3, 4, 7, 8, 9, 11, 12, 13, 14, 15, 17, 20, 21]
COMMON_DEGRADATION_SENSOR_INDICES = [3 + sensor_id - 1 for sensor_id in COMMON_DEGRADATION_SENSORS]
MDFA_TABLE4_KEY_SENSOR_CODES = ["Ps30", "T24", "T30", "P30", "Phi", "Nf", "Nc", "W31", "W32"]
MDFA_TABLE4_KEY_SENSOR_IDS = [11, 2, 3, 7, 12, 8, 9, 20, 21]
MDFA_TABLE4_KEY_SENSOR_INDICES = [3 + sensor_id - 1 for sensor_id in MDFA_TABLE4_KEY_SENSOR_IDS]
FEATURE_POLICIES = {
    "all24_pca": {"indices": list(range(24)), "pca": True},
    "sensor21_pca": {"indices": list(range(3, 24)), "pca": True},
    "mdfa_key_sensors_raw": {"indices": MDFA_TABLE4_KEY_SENSOR_INDICES, "pca": False},
    "mdfa_key_sensors_pca": {"indices": MDFA_TABLE4_KEY_SENSOR_INDICES, "pca": True},
    "common_sensors_raw": {"indices": COMMON_DEGRADATION_SENSOR_INDICES, "pca": False},
    "common_sensors_pca": {"indices": COMMON_DEGRADATION_SENSOR_INDICES, "pca": True},
    "settings_common_sensors_raw": {"indices": [0, 1, 2] + COMMON_DEGRADATION_SENSOR_INDICES, "pca": False},
    "settings_common_sensors_pca": {"indices": [0, 1, 2] + COMMON_DEGRADATION_SENSOR_INDICES, "pca": True},
}
CONDITION_NORMALIZATION_POLICIES = ("none", "kmeans6_settings", "kmeans4_trajectory")
TEMPORAL_FEATURE_MODES = ("level", "level_diff")


@dataclass(frozen=True)
class CmapssRawSubset:
    subset: str
    train: np.ndarray
    test: np.ndarray
    test_rul: np.ndarray


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    os.makedirs(_fs_path(path.parent), exist_ok=True)
    with open(_fs_path(path), "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def _read_json_if_present(path: Path) -> dict[str, Any] | None:
    if not os.path.exists(_fs_path(path)):
        return None
    with open(_fs_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_text(path: Path, text: str) -> None:
    os.makedirs(_fs_path(path.parent), exist_ok=True)
    with open(_fs_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def _split_csv(value: str) -> list[str]:
    return [part.strip() for part in str(value).replace(";", ",").split(",") if part.strip()]


def _split_seeds(value: str) -> list[int]:
    return [int(part) for part in _split_csv(value)]


def _subset_result_path(output_dir: Path, seed: int, subset: str) -> Path:
    return Path(output_dir) / f"cmapss_mdfa_source_matched_seed{int(seed)}_{subset}.json"


def _load_numeric(path: Path) -> np.ndarray:
    if not os.path.exists(_fs_path(path)):
        raise FileNotFoundError(path)
    arr = np.loadtxt(_fs_path(path), dtype=np.float32)
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)
    return np.asarray(arr, dtype=np.float32)


def load_raw_subset(raw_dir: Path, subset: str) -> CmapssRawSubset:
    raw_dir = Path(raw_dir)
    train = _load_numeric(raw_dir / f"train_{subset}.txt")
    test = _load_numeric(raw_dir / f"test_{subset}.txt")
    rul = _load_numeric(raw_dir / f"RUL_{subset}.txt").reshape(-1)
    return CmapssRawSubset(subset=str(subset), train=train, test=test, test_rul=np.asarray(rul, dtype=np.float32))


def _unit_values(frame: np.ndarray) -> np.ndarray:
    return np.asarray(sorted(np.unique(frame[:, 0].astype(np.int64))), dtype=np.int64)


def _rows_for_units(frame: np.ndarray, units: Sequence[int]) -> np.ndarray:
    mask = np.isin(frame[:, 0].astype(np.int64), np.asarray(units, dtype=np.int64))
    return frame[mask]


def train_unit_split(frame: np.ndarray, *, seed: int, val_fraction: float) -> tuple[np.ndarray, np.ndarray]:
    units = _unit_values(frame)
    if float(val_fraction) <= 0.0:
        return units, units
    if len(units) < 4:
        split = max(1, int(round(len(units) * (1.0 - float(val_fraction)))))
        return units[:split], units[split:]
    train_units, val_units = train_test_split(
        units,
        test_size=float(val_fraction),
        random_state=int(seed),
        shuffle=True,
    )
    return np.asarray(sorted(train_units), dtype=np.int64), np.asarray(sorted(val_units), dtype=np.int64)


def _feature_policy_spec(feature_policy: str) -> dict[str, Any]:
    if feature_policy not in FEATURE_POLICIES:
        raise ValueError(f"Unknown feature_policy={feature_policy!r}; expected one of {sorted(FEATURE_POLICIES)}")
    spec = FEATURE_POLICIES[str(feature_policy)]
    indices = [int(index) for index in spec["indices"]]
    return {
        "feature_policy": str(feature_policy),
        "indices": indices,
        "feature_names": [RAW_FEATURE_NAMES[index] for index in indices],
        "pca": bool(spec["pca"]),
    }


def _select_raw_features(rows: np.ndarray, spec: dict[str, Any]) -> np.ndarray:
    raw_features = rows[:, 2:].astype(np.float32)
    return raw_features[:, list(spec["indices"])]


def _settings_matrix(rows: np.ndarray) -> np.ndarray:
    return rows[:, 2:5].astype(np.float32)


def _unit_trajectory_summaries(rows: np.ndarray, raw_features: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    units = rows[:, 0].astype(np.int64)
    cycles = rows[:, 1].astype(np.float32)
    summary_units: list[int] = []
    summaries: list[np.ndarray] = []
    for unit in sorted(np.unique(units)):
        idx = np.where(units == unit)[0]
        idx = idx[np.argsort(cycles[idx])]
        unit_features = raw_features[idx].astype(np.float32)
        if len(unit_features) == 0:
            continue
        head_n = max(1, int(np.ceil(len(unit_features) * 0.2)))
        tail_n = max(1, int(np.ceil(len(unit_features) * 0.2)))
        first = unit_features[0]
        last = unit_features[-1]
        head_mean = np.mean(unit_features[:head_n], axis=0)
        tail_mean = np.mean(unit_features[-tail_n:], axis=0)
        mean = np.mean(unit_features, axis=0)
        std = np.std(unit_features, axis=0)
        slope = (last - first) / max(1.0, float(len(unit_features) - 1))
        summaries.append(np.concatenate([mean, std, last, tail_mean - head_mean, slope], axis=0).astype(np.float32))
        summary_units.append(int(unit))
    if not summaries:
        return np.zeros(0, dtype=np.int64), np.zeros((0, raw_features.shape[1] * 5), dtype=np.float32)
    return np.asarray(summary_units, dtype=np.int64), np.stack(summaries).astype(np.float32)


def _labels_from_unit_labels(rows: np.ndarray, unit_labels: dict[int, int]) -> np.ndarray:
    return np.asarray([unit_labels.get(int(unit), 0) for unit in rows[:, 0].astype(np.int64)], dtype=np.int64)


def _condition_labels(rows: np.ndarray, preprocessor: dict[str, Any]) -> np.ndarray:
    condition_model = preprocessor.get("condition_model")
    label_source = str(preprocessor.get("condition_label_source") or "none")
    if condition_model is None:
        return np.zeros(len(rows), dtype=np.int64)
    if label_source == "settings":
        setting_scaler = preprocessor.get("condition_setting_scaler")
        if setting_scaler is None:
            return np.zeros(len(rows), dtype=np.int64)
        settings = setting_scaler.transform(_settings_matrix(rows))
        return np.asarray(condition_model.predict(settings), dtype=np.int64)
    if label_source == "trajectory":
        feature_spec = preprocessor.get("feature_spec")
        raw_features = _select_raw_features(rows, feature_spec) if feature_spec else rows[:, 2:].astype(np.float32)
        units, summaries = _unit_trajectory_summaries(rows, raw_features)
        if len(units) == 0:
            return np.zeros(len(rows), dtype=np.int64)
        summary_scaler = preprocessor.get("condition_trajectory_scaler")
        if summary_scaler is None:
            return np.zeros(len(rows), dtype=np.int64)
        labels = np.asarray(condition_model.predict(summary_scaler.transform(summaries)), dtype=np.int64)
        return _labels_from_unit_labels(rows, {int(unit): int(label) for unit, label in zip(units, labels)})
    return np.zeros(len(rows), dtype=np.int64)


def _fit_condition_normalizer(
    train_rows: np.ndarray,
    raw_features: np.ndarray,
    *,
    policy: str,
) -> dict[str, Any]:
    condition_policy = str(policy)
    if condition_policy == "kmeans6_settings":
        setting_scaler = StandardScaler()
        settings = setting_scaler.fit_transform(_settings_matrix(train_rows))
        cluster_count = max(1, min(6, len(train_rows)))
        condition_model = KMeans(n_clusters=cluster_count, random_state=0, n_init=10)
        labels = np.asarray(condition_model.fit_predict(settings), dtype=np.int64)
        condition_payload: dict[str, Any] = {
            "condition_label_source": "settings",
            "condition_setting_scaler": setting_scaler,
            "condition_model": condition_model,
            "condition_cluster_count": int(cluster_count),
        }
    elif condition_policy == "kmeans4_trajectory":
        units, summaries = _unit_trajectory_summaries(train_rows, raw_features)
        cluster_count = max(1, min(4, len(units)))
        summary_scaler = StandardScaler()
        scaled_summaries = summary_scaler.fit_transform(summaries)
        condition_model = KMeans(n_clusters=cluster_count, random_state=0, n_init=10)
        unit_cluster_labels = np.asarray(condition_model.fit_predict(scaled_summaries), dtype=np.int64)
        labels = _labels_from_unit_labels(
            train_rows,
            {int(unit): int(label) for unit, label in zip(units, unit_cluster_labels)},
        )
        condition_payload = {
            "condition_label_source": "trajectory",
            "condition_trajectory_scaler": summary_scaler,
            "condition_model": condition_model,
            "condition_cluster_count": int(cluster_count),
        }
    else:
        raise ValueError(f"Unsupported condition normalizer policy={condition_policy!r}")
    imputers: list[SimpleImputer] = []
    scalers: list[StandardScaler] = []
    for condition_id in range(cluster_count):
        mask = labels == condition_id
        cluster_features = raw_features[mask] if np.any(mask) else raw_features
        imputer = SimpleImputer(strategy="median")
        scaler = StandardScaler()
        imputed = imputer.fit_transform(cluster_features)
        scaler.fit(imputed)
        imputers.append(imputer)
        scalers.append(scaler)
    condition_payload.update(
        {
        "condition_imputers": imputers,
        "condition_scalers": scalers,
        }
    )
    return condition_payload


def _apply_condition_normalizer(rows: np.ndarray, raw_features: np.ndarray, preprocessor: dict[str, Any]) -> np.ndarray:
    labels = _condition_labels(rows, preprocessor)
    normalized = np.zeros_like(raw_features, dtype=np.float32)
    imputers = preprocessor["condition_imputers"]
    scalers = preprocessor["condition_scalers"]
    for condition_id in range(int(preprocessor["condition_cluster_count"])):
        mask = labels == condition_id
        if not np.any(mask):
            continue
        imputed = imputers[condition_id].transform(raw_features[mask])
        normalized[mask] = scalers[condition_id].transform(imputed).astype(np.float32)
    return normalized


def _condition_onehot(rows: np.ndarray, preprocessor: dict[str, Any]) -> np.ndarray:
    labels = _condition_labels(rows, preprocessor)
    cluster_count = int(preprocessor.get("condition_cluster_count") or 1)
    onehot = np.zeros((len(rows), cluster_count), dtype=np.float32)
    if len(rows):
        onehot[np.arange(len(rows)), np.clip(labels, 0, cluster_count - 1)] = 1.0
    return onehot


def _fit_preprocessor(
    train_rows: np.ndarray,
    *,
    pca_variance: float,
    feature_policy: str,
    condition_normalization: str = "none",
    append_condition_onehot: bool = False,
) -> dict[str, Any]:
    spec = _feature_policy_spec(str(feature_policy))
    raw_features = _select_raw_features(train_rows, spec)
    condition_policy = str(condition_normalization)
    if condition_policy not in CONDITION_NORMALIZATION_POLICIES:
        raise ValueError(
            f"Unknown condition_normalization={condition_policy!r}; expected one of {CONDITION_NORMALIZATION_POLICIES}"
        )
    condition_payload: dict[str, Any] = {}
    imputer = None
    scaler = None
    if condition_policy in {"kmeans6_settings", "kmeans4_trajectory"}:
        condition_payload = _fit_condition_normalizer(train_rows, raw_features, policy=condition_policy)
        condition_payload["feature_spec"] = spec
        scaled = _apply_condition_normalizer(train_rows, raw_features, condition_payload)
    else:
        imputer = SimpleImputer(strategy="median")
        scaler = StandardScaler()
        imputed = imputer.fit_transform(raw_features)
        scaled = scaler.fit_transform(imputed)
    pca = None
    if spec["pca"]:
        pca = PCA(n_components=float(pca_variance), svd_solver="full")
        pca.fit(scaled)
    payload = {
        "imputer": imputer,
        "scaler": scaler,
        "pca": pca,
        "feature_spec": spec,
        "condition_normalization": condition_policy,
        "append_condition_onehot": bool(append_condition_onehot),
    }
    payload.update(condition_payload)
    return payload


def _legacy_fit_preprocessor(train_rows: np.ndarray, *, pca_variance: float) -> dict[str, Any]:
    raw_features = train_rows[:, 2:].astype(np.float32)
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    pca = PCA(n_components=float(pca_variance), svd_solver="full")
    imputed = imputer.fit_transform(raw_features)
    scaled = scaler.fit_transform(imputed)
    pca.fit(scaled)
    return {"imputer": imputer, "scaler": scaler, "pca": pca}


def _transform_rows(rows: np.ndarray, preprocessor: dict[str, Any]) -> np.ndarray:
    feature_spec = preprocessor.get("feature_spec")
    raw_features = _select_raw_features(rows, feature_spec) if feature_spec else rows[:, 2:].astype(np.float32)
    if str(preprocessor.get("condition_normalization") or "none") in {"kmeans6_settings", "kmeans4_trajectory"}:
        scaled = _apply_condition_normalizer(rows, raw_features, preprocessor)
    else:
        imputed = preprocessor["imputer"].transform(raw_features)
        scaled = preprocessor["scaler"].transform(imputed)
    pca = preprocessor.get("pca")
    transformed = pca.transform(scaled) if pca is not None else scaled
    if bool(preprocessor.get("append_condition_onehot")):
        transformed = np.concatenate([transformed, _condition_onehot(rows, preprocessor)], axis=1)
    return np.asarray(transformed, dtype=np.float32)


def _train_rul(frame: np.ndarray) -> np.ndarray:
    units = frame[:, 0].astype(np.int64)
    cycles = frame[:, 1].astype(np.float32)
    max_by_unit = {unit: float(np.max(cycles[units == unit])) for unit in np.unique(units)}
    return np.asarray([max_by_unit[int(unit)] - float(cycle) for unit, cycle in zip(units, cycles)], dtype=np.float32)


def _left_padded_window(features: np.ndarray, end_pos: int, window_size: int) -> np.ndarray:
    start = max(0, int(end_pos) - int(window_size) + 1)
    window = features[start : int(end_pos) + 1]
    if len(window) >= int(window_size):
        return np.asarray(window[-int(window_size) :], dtype=np.float32)
    pad = np.repeat(window[:1], int(window_size) - len(window), axis=0)
    return np.concatenate([pad, window], axis=0).astype(np.float32)


def _augment_temporal_window(window: np.ndarray, mode: str) -> np.ndarray:
    arr = np.asarray(window, dtype=np.float32)
    mode = str(mode)
    if mode == "level":
        return arr
    if mode == "level_diff":
        diff = np.diff(arr, axis=0, prepend=arr[:1])
        return np.concatenate([arr, diff.astype(np.float32)], axis=1).astype(np.float32)
    raise ValueError(f"Unknown temporal_feature_mode={mode!r}; expected one of {TEMPORAL_FEATURE_MODES}")


def build_train_windows(
    rows: np.ndarray,
    preprocessor: dict[str, Any],
    *,
    window_size: int,
    temporal_feature_mode: str = "level",
    max_windows: int | None,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, list[dict[str, Any]]]:
    order = np.lexsort((rows[:, 1], rows[:, 0]))
    rows = rows[order]
    features = _transform_rows(rows, preprocessor)
    rul = _train_rul(rows)
    units = rows[:, 0].astype(np.int64)
    windows: list[np.ndarray] = []
    targets: list[float] = []
    metadata: list[dict[str, Any]] = []
    offset = 0
    for unit in sorted(np.unique(units)):
        unit_idx = np.where(units == unit)[0]
        unit_features = features[unit_idx]
        for local_pos, global_pos in enumerate(unit_idx):
            window = _left_padded_window(unit_features, local_pos, int(window_size))
            windows.append(_augment_temporal_window(window, str(temporal_feature_mode)))
            targets.append(float(rul[global_pos]))
            metadata.append({"unit": int(unit), "cycle": int(rows[global_pos, 1])})
            offset += 1
    if max_windows is not None and int(max_windows) > 0 and len(windows) > int(max_windows):
        rng = np.random.default_rng(int(seed))
        selected = np.sort(rng.choice(np.arange(len(windows)), size=int(max_windows), replace=False))
        windows = [windows[int(i)] for i in selected]
        targets = [targets[int(i)] for i in selected]
        metadata = [metadata[int(i)] for i in selected]
    return np.stack(windows).astype(np.float32), np.asarray(targets, dtype=np.float32), metadata


def build_terminal_test_windows(
    subset: CmapssRawSubset,
    preprocessor: dict[str, Any],
    *,
    window_size: int,
    temporal_feature_mode: str = "level",
) -> tuple[np.ndarray, np.ndarray, list[dict[str, Any]]]:
    rows = subset.test[np.lexsort((subset.test[:, 1], subset.test[:, 0]))]
    features = _transform_rows(rows, preprocessor)
    units = rows[:, 0].astype(np.int64)
    windows: list[np.ndarray] = []
    targets: list[float] = []
    metadata: list[dict[str, Any]] = []
    for unit in sorted(np.unique(units)):
        unit_idx = np.where(units == unit)[0]
        unit_features = features[unit_idx]
        local_pos = len(unit_idx) - 1
        global_pos = int(unit_idx[local_pos])
        rul_pos = int(unit) - 1
        if rul_pos < 0 or rul_pos >= len(subset.test_rul):
            raise ValueError(f"Missing RUL label for {subset.subset} unit {unit}")
        window = _left_padded_window(unit_features, local_pos, int(window_size))
        windows.append(_augment_temporal_window(window, str(temporal_feature_mode)))
        targets.append(float(subset.test_rul[rul_pos]))
        metadata.append({"subset": subset.subset, "unit": int(unit), "cycle": int(rows[global_pos, 1])})
    return np.stack(windows).astype(np.float32), np.asarray(targets, dtype=np.float32), metadata


class MDFARULRegressor(nn.Module):
    def __init__(self, n_features: int, hidden_dim: int, dropout: float, dilation_rates: Sequence[int] = (1, 2, 4)) -> None:
        super().__init__()
        self.branches = nn.ModuleList(
            [
                nn.Conv1d(int(n_features), int(hidden_dim), kernel_size=3, padding=int(rate), dilation=int(rate))
                for rate in dilation_rates
            ]
        )
        self.global_branch = nn.Conv1d(int(n_features), int(hidden_dim), kernel_size=1)
        cat_dim = int(hidden_dim) * (len(dilation_rates) + 1)
        attn_mid = max(4, cat_dim // 4)
        self.channel_attention = nn.Sequential(
            nn.AdaptiveAvgPool1d(1),
            nn.Conv1d(cat_dim, attn_mid, kernel_size=1),
            nn.ReLU(),
            nn.Conv1d(attn_mid, cat_dim, kernel_size=1),
            nn.Sigmoid(),
        )
        self.spatial_attention = nn.Sequential(
            nn.Conv1d(1, 1, kernel_size=3, padding=1),
            nn.Sigmoid(),
        )
        self.fusion = nn.Sequential(
            nn.Conv1d(cat_dim, int(hidden_dim), kernel_size=1),
            nn.GELU(),
            nn.Dropout(float(dropout)),
        )
        self.head = nn.Sequential(
            nn.LayerNorm(int(hidden_dim) * 2),
            nn.Dropout(float(dropout)),
            nn.Linear(int(hidden_dim) * 2, int(hidden_dim)),
            nn.GELU(),
            nn.Linear(int(hidden_dim), 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        y = x.transpose(1, 2)
        branches = [F.gelu(branch(y)[..., : y.shape[-1]]) for branch in self.branches]
        pooled = torch.mean(y, dim=-1, keepdim=True).expand(-1, -1, y.shape[-1])
        branches.append(F.gelu(self.global_branch(pooled)))
        z = torch.cat(branches, dim=1)
        z = z * self.channel_attention(z)
        z = z * self.spatial_attention(torch.mean(z, dim=1, keepdim=True))
        z = self.fusion(z)
        summary = torch.cat([z[:, :, -1], torch.mean(z, dim=-1)], dim=1)
        return torch.sigmoid(self.head(summary)).squeeze(-1)


class MDFA2DRULRegressor(nn.Module):
    def __init__(self, n_features: int, hidden_dim: int, dropout: float, dilation_rates: Sequence[int] = (1, 2, 4)) -> None:
        super().__init__()
        self.branches = nn.ModuleList(
            [
                nn.Conv2d(1, int(hidden_dim), kernel_size=(3, 3), padding=(int(rate), 1), dilation=(int(rate), 1))
                for rate in dilation_rates
            ]
        )
        self.global_branch = nn.Conv2d(1, int(hidden_dim), kernel_size=1)
        cat_dim = int(hidden_dim) * (len(dilation_rates) + 1)
        attn_mid = max(4, cat_dim // 4)
        self.channel_attention = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Conv2d(cat_dim, attn_mid, kernel_size=1),
            nn.ReLU(),
            nn.Conv2d(attn_mid, cat_dim, kernel_size=1),
            nn.Sigmoid(),
        )
        self.spatial_attention = nn.Sequential(
            nn.Conv2d(1, 1, kernel_size=1),
            nn.Sigmoid(),
        )
        self.fusion = nn.Sequential(
            nn.Conv2d(cat_dim, int(hidden_dim), kernel_size=1),
            nn.GELU(),
            nn.Dropout(float(dropout)),
        )
        self.head = nn.Sequential(
            nn.LayerNorm(int(hidden_dim) * 2),
            nn.Dropout(float(dropout)),
            nn.Linear(int(hidden_dim) * 2, int(hidden_dim)),
            nn.GELU(),
            nn.Linear(int(hidden_dim), 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        y = x.unsqueeze(1)
        branches = [F.gelu(branch(y)[..., : y.shape[-2], : y.shape[-1]]) for branch in self.branches]
        pooled = torch.mean(y, dim=2, keepdim=True).expand(-1, -1, y.shape[-2], y.shape[-1])
        branches.append(F.gelu(self.global_branch(pooled)))
        z = torch.cat(branches, dim=1)
        z = z * self.channel_attention(z)
        z = z * self.spatial_attention(torch.mean(z, dim=1, keepdim=True))
        z = self.fusion(z)
        last_time = torch.mean(z[:, :, -1, :], dim=-1)
        global_summary = torch.mean(z, dim=(-2, -1))
        summary = torch.cat([last_time, global_summary], dim=1)
        return torch.sigmoid(self.head(summary)).squeeze(-1)


class SnapshotEnsembleRULRegressor(nn.Module):
    def __init__(self, members: Sequence[nn.Module]) -> None:
        super().__init__()
        self.members = nn.ModuleList(list(members))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        preds = [member(x) for member in self.members]
        return torch.stack(preds, dim=0).mean(dim=0)


def _build_mdfa_model(
    *,
    formulation: str,
    n_features: int,
    hidden_dim: int,
    dropout: float,
) -> nn.Module:
    model_cls = MDFA2DRULRegressor if str(formulation) == "source_2d" else MDFARULRegressor
    return model_cls(
        n_features=int(n_features),
        hidden_dim=int(hidden_dim),
        dropout=float(dropout),
        dilation_rates=tuple(MDFA_SOURCE["published_architecture"]["dilation_rates"]),
    )


def _clone_state_dict(model: nn.Module) -> dict[str, torch.Tensor]:
    return {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}


def _model_from_state(
    *,
    formulation: str,
    n_features: int,
    hidden_dim: int,
    dropout: float,
    state: dict[str, torch.Tensor],
    device: torch.device,
) -> nn.Module:
    model = _build_mdfa_model(
        formulation=str(formulation),
        n_features=int(n_features),
        hidden_dim=int(hidden_dim),
        dropout=float(dropout),
    ).to(device)
    model.load_state_dict(state)
    model.eval()
    return model


def _predict(model: nn.Module, x: np.ndarray, *, batch_size: int, device: torch.device, rul_cap: float) -> np.ndarray:
    model.eval()
    chunks: list[np.ndarray] = []
    x_tensor = torch.from_numpy(np.asarray(x, dtype=np.float32))
    with torch.no_grad():
        for start in range(0, len(x_tensor), int(batch_size)):
            pred = model(x_tensor[start : start + int(batch_size)].to(device)).detach().cpu().numpy()
            chunks.append(pred)
    norm = np.concatenate(chunks).astype(np.float32)
    return np.clip(norm, 0.0, 1.0) * float(max(1.0, rul_cap))


def fit_mdfa(
    *,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray,
    y_val: np.ndarray,
    seed: int,
    rul_cap: float,
    device: str,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    hidden_dim: int,
    dropout: float,
    conv_formulation: str,
    lr_scheduler: str,
    snapshot_ensemble_k: int = 1,
    snapshot_ensemble_min_val_rmse_delta: float = 0.0,
) -> tuple[nn.Module, dict[str, Any]]:
    torch.manual_seed(int(seed))
    rng = np.random.default_rng(int(seed))
    train_device = resolve_torch_device(device)
    formulation = str(conv_formulation)
    model = _build_mdfa_model(
        formulation=formulation,
        n_features=int(x_train.shape[2]),
        hidden_dim=int(hidden_dim),
        dropout=float(dropout),
    ).to(train_device)
    opt = torch.optim.Adam(model.parameters(), lr=float(learning_rate))
    scheduler = None
    if str(lr_scheduler) == "reduce_on_plateau":
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, mode="min", factor=0.5, patience=8, min_lr=1.0e-6)
    cap = float(max(1.0, rul_cap))
    x_t = torch.from_numpy(np.asarray(x_train, dtype=np.float32)).to(train_device)
    y_t = torch.from_numpy((np.clip(np.asarray(y_train, dtype=np.float32), 0.0, cap) / cap).astype(np.float32)).to(train_device)
    batch = max(4, min(int(batch_size), len(x_train)))
    best_state: dict[str, torch.Tensor] | None = None
    top_states: list[tuple[float, dict[str, torch.Tensor]]] = []
    ensemble_k = max(1, int(snapshot_ensemble_k))
    best_rmse = float("inf")
    losses: list[float] = []
    val_history: list[float] = []
    lr_history: list[float] = []
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
        val_pred = _predict(model, x_val, batch_size=batch, device=train_device, rul_cap=cap)
        val_rmse = float((rul_regression_metrics(y_val, val_pred) or {}).get("rul_rmse", float("inf")))
        val_history.append(val_rmse)
        if scheduler is not None:
            scheduler.step(val_rmse)
        lr_history.append(float(opt.param_groups[0]["lr"]))
        state = _clone_state_dict(model)
        if val_rmse <= best_rmse:
            best_rmse = val_rmse
            best_state = state
        if ensemble_k > 1:
            top_states.append((float(val_rmse), state))
            top_states = sorted(top_states, key=lambda item: item[0])[:ensemble_k]
    train_seconds = max(1.0e-9, time.perf_counter() - start_time)
    if best_state is not None:
        model.load_state_dict(best_state)
    snapshot_diag: dict[str, Any] = {
        "requested_k": int(ensemble_k),
        "applied": False,
        "reason": "disabled" if ensemble_k <= 1 else "not_evaluated",
        "member_val_rmses": [float(value) for value, _state in top_states],
        "base_best_val_rmse": float(best_rmse),
        "min_val_rmse_delta": float(snapshot_ensemble_min_val_rmse_delta),
    }
    if ensemble_k > 1 and len(top_states) > 1:
        members = [
            _model_from_state(
                formulation=formulation,
                n_features=int(x_train.shape[2]),
                hidden_dim=int(hidden_dim),
                dropout=float(dropout),
                state=state,
                device=train_device,
            )
            for _rmse, state in top_states
        ]
        ensemble_model = SnapshotEnsembleRULRegressor(members).to(train_device)
        ensemble_val_pred = _predict(ensemble_model, x_val, batch_size=batch, device=train_device, rul_cap=cap)
        ensemble_val_metrics = rul_regression_metrics(y_val, ensemble_val_pred) or {}
        ensemble_val_rmse = float(ensemble_val_metrics.get("rul_rmse", float("inf")))
        delta = float(best_rmse - ensemble_val_rmse)
        applied = bool(delta >= float(snapshot_ensemble_min_val_rmse_delta))
        snapshot_diag.update(
            {
                "applied": applied,
                "reason": "validation_rmse_delta_pass" if applied else "validation_rmse_delta_guard_failed",
                "ensemble_val_metrics": ensemble_val_metrics,
                "ensemble_val_rmse": ensemble_val_rmse,
                "val_rmse_delta": delta,
            }
        )
        if applied:
            model = ensemble_model
    diagnostics = {
        "model_family": "mdfa_2025_source_matched_candidate",
        "source_id": "mdfa_2025",
        "published_alignment_status": "source_matched_candidate_not_exact_reproduction",
        "parameters": int(sum(p.numel() for p in model.parameters() if p.requires_grad)),
        "snapshot_ensemble": snapshot_diag,
        "device": str(train_device),
        "epochs": int(epochs),
        "batch_size": int(batch),
        "learning_rate": float(learning_rate),
        "hidden_dim": int(hidden_dim),
        "dropout": float(dropout),
        "conv_formulation": formulation,
        "lr_scheduler": str(lr_scheduler),
        "dilation_rates": list(MDFA_SOURCE["published_architecture"]["dilation_rates"]),
        "loss_tail": losses[-5:],
        "val_rul_rmse_history_tail": val_history[-5:],
        "learning_rate_tail": lr_history[-5:],
        "best_val_rul_rmse": float(best_rmse),
        "train_seconds": float(train_seconds),
        "train_samples_per_second": float((len(x_train) * max(1, int(epochs))) / train_seconds),
    }
    return model, diagnostics


def _prediction_records(metadata: Sequence[dict[str, Any]], y_true: np.ndarray, y_pred: np.ndarray) -> list[dict[str, Any]]:
    return _prediction_records_with_raw(metadata, y_true, y_true, y_pred)


def _prediction_records_with_raw(
    metadata: Sequence[dict[str, Any]],
    y_true_effective: np.ndarray,
    y_true_raw: np.ndarray,
    y_pred: np.ndarray,
    *,
    split_role: str = "test",
    subset_name: str | None = None,
    y_pred_base: np.ndarray | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, (meta, true, raw_true, pred) in enumerate(zip(metadata, y_true_effective, y_true_raw, y_pred)):
        subset = str(meta.get("subset") or subset_name or "")
        item = {
            "row_index": int(idx),
            "record_id": f"{subset}_unit{int(meta['unit'])}_{split_role}{int(idx)}",
            "subset": subset,
            "split_role": str(split_role),
            "unit": int(meta["unit"]),
            "cycle": int(meta["cycle"]),
            "rul_true": float(true),
            "rul_true_raw": float(raw_true),
            "rul_pred": float(pred),
            "rul_error": float(pred - true),
            "prediction_source": "mdfa_2025_source_matched_candidate",
        }
        if y_pred_base is not None:
            item["rul_pred_base"] = float(np.asarray(y_pred_base, dtype=np.float32)[idx])
            item["rul_error_base"] = float(item["rul_pred_base"] - float(true))
        rows.append(item)
    return rows


def _fit_output_calibration(
    *,
    policy: str,
    y_val: np.ndarray,
    val_pred: np.ndarray,
    rul_cap: float,
    min_val_rmse_delta: float,
) -> dict[str, Any]:
    base_metrics = rul_regression_metrics(y_val, val_pred) or {}
    base_rmse = float(base_metrics.get("rul_rmse", float("inf")))
    policy = str(policy)
    if policy == "none":
        return {
            "policy": "none",
            "applied": False,
            "reason": "disabled",
            "base_val_metrics": base_metrics,
            "calibrated_val_metrics": base_metrics,
            "val_rmse_delta": 0.0,
        }
    if policy != "affine_val":
        raise ValueError(f"Unknown output_calibration={policy!r}; expected 'none' or 'affine_val'")
    y = np.asarray(y_val, dtype=np.float32).reshape(-1)
    pred = np.asarray(val_pred, dtype=np.float32).reshape(-1)
    if len(y) < 2 or float(np.std(pred)) < 1.0e-8:
        return {
            "policy": policy,
            "applied": False,
            "reason": "insufficient_or_degenerate_validation_predictions",
            "base_val_metrics": base_metrics,
            "calibrated_val_metrics": base_metrics,
            "val_rmse_delta": 0.0,
        }
    design = np.stack([pred, np.ones_like(pred)], axis=1)
    slope, intercept = np.linalg.lstsq(design, y, rcond=None)[0]
    cap = float(max(1.0, rul_cap))
    calibrated_val = np.clip(float(slope) * pred + float(intercept), 0.0, cap).astype(np.float32)
    calibrated_metrics = rul_regression_metrics(y, calibrated_val) or {}
    calibrated_rmse = float(calibrated_metrics.get("rul_rmse", float("inf")))
    delta = float(base_rmse - calibrated_rmse)
    applied = bool(delta >= float(min_val_rmse_delta))
    return {
        "policy": policy,
        "applied": applied,
        "reason": "validation_rmse_delta_pass" if applied else "validation_rmse_delta_guard_failed",
        "slope": float(slope),
        "intercept": float(intercept),
        "clip_min": 0.0,
        "clip_max": cap,
        "min_val_rmse_delta": float(min_val_rmse_delta),
        "base_val_metrics": base_metrics,
        "calibrated_val_metrics": calibrated_metrics,
        "val_rmse_delta": delta,
    }


def _apply_output_calibration(pred: np.ndarray, calibration: dict[str, Any]) -> np.ndarray:
    if not bool(calibration.get("applied")):
        return np.asarray(pred, dtype=np.float32)
    slope = float(calibration.get("slope", 1.0))
    intercept = float(calibration.get("intercept", 0.0))
    clip_min = float(calibration.get("clip_min", 0.0))
    clip_max = float(calibration.get("clip_max", 1.0e9))
    return np.clip(slope * np.asarray(pred, dtype=np.float32) + intercept, clip_min, clip_max).astype(np.float32)


def _run_config(
    *,
    subset_name: str,
    seed: int,
    window_size: int,
    pca_variance: float,
    feature_policy: str,
    temporal_feature_mode: str,
    condition_normalization: str,
    append_condition_onehot: bool,
    val_fraction: float,
    max_train_windows: int | None,
    max_val_windows: int | None,
    rul_cap: float,
    cap_eval_rul: bool,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    hidden_dim: int,
    dropout: float,
    conv_formulation: str,
    lr_scheduler: str,
    output_calibration: str,
    calibration_min_val_rmse_delta: float,
    snapshot_ensemble_k: int,
    snapshot_ensemble_min_val_rmse_delta: float,
) -> dict[str, Any]:
    return {
        "subset": str(subset_name),
        "seed": int(seed),
        "window_size": int(window_size),
        "pca_variance": float(pca_variance),
        "feature_policy": str(feature_policy),
        "temporal_feature_mode": str(temporal_feature_mode),
        "condition_normalization": str(condition_normalization),
        "append_condition_onehot": bool(append_condition_onehot),
        "val_fraction": float(val_fraction),
        "max_train_windows": int(max_train_windows) if max_train_windows is not None else None,
        "max_val_windows": int(max_val_windows) if max_val_windows is not None else None,
        "rul_cap": float(rul_cap),
        "cap_eval_rul": bool(cap_eval_rul),
        "epochs": int(epochs),
        "batch_size": int(batch_size),
        "learning_rate": float(learning_rate),
        "hidden_dim": int(hidden_dim),
        "dropout": float(dropout),
        "conv_formulation": str(conv_formulation),
        "lr_scheduler": str(lr_scheduler),
        "output_calibration": str(output_calibration),
        "calibration_min_val_rmse_delta": float(calibration_min_val_rmse_delta),
        "snapshot_ensemble_k": int(snapshot_ensemble_k),
        "snapshot_ensemble_min_val_rmse_delta": float(snapshot_ensemble_min_val_rmse_delta),
        "dilation_rates": list(MDFA_SOURCE["published_architecture"]["dilation_rates"]),
    }


def _cached_result_matches(result: dict[str, Any] | None, expected_config: dict[str, Any]) -> bool:
    if not isinstance(result, dict):
        return False
    cached_config = result.get("run_config")
    if not isinstance(cached_config, dict):
        return False
    for key, expected in expected_config.items():
        observed = cached_config.get(key)
        if isinstance(expected, float):
            if abs(float(observed) - expected) > 1.0e-12:
                return False
        else:
            if observed != expected:
                return False
    return True


def run_subset(
    *,
    subset_name: str,
    seed: int,
    raw_dir: Path,
    window_size: int,
    pca_variance: float,
    feature_policy: str,
    temporal_feature_mode: str = "level",
    condition_normalization: str = "none",
    append_condition_onehot: bool = False,
    val_fraction: float,
    max_train_windows: int | None,
    max_val_windows: int | None,
    rul_cap: float,
    cap_eval_rul: bool,
    device: str,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    hidden_dim: int,
    dropout: float,
    conv_formulation: str,
    lr_scheduler: str,
    output_calibration: str = "none",
    calibration_min_val_rmse_delta: float = 0.0,
    snapshot_ensemble_k: int = 1,
    snapshot_ensemble_min_val_rmse_delta: float = 0.0,
) -> dict[str, Any]:
    subset = load_raw_subset(Path(raw_dir), subset_name)
    train_units, val_units = train_unit_split(subset.train, seed=int(seed), val_fraction=float(val_fraction))
    train_rows = _rows_for_units(subset.train, train_units)
    val_rows = _rows_for_units(subset.train, val_units)
    preprocessor = _fit_preprocessor(
        train_rows,
        pca_variance=float(pca_variance),
        feature_policy=str(feature_policy),
        condition_normalization=str(condition_normalization),
        append_condition_onehot=bool(append_condition_onehot),
    )
    x_train, y_train, _train_meta = build_train_windows(
        train_rows,
        preprocessor,
        window_size=int(window_size),
        temporal_feature_mode=str(temporal_feature_mode),
        max_windows=max_train_windows,
        seed=int(seed),
    )
    x_val, y_val, _val_meta = build_train_windows(
        val_rows,
        preprocessor,
        window_size=int(window_size),
        temporal_feature_mode=str(temporal_feature_mode),
        max_windows=max_val_windows,
        seed=int(seed) + 1,
    )
    x_test, y_test, test_meta = build_terminal_test_windows(
        subset,
        preprocessor,
        window_size=int(window_size),
        temporal_feature_mode=str(temporal_feature_mode),
    )
    y_val_effective = np.minimum(y_val, float(rul_cap)).astype(np.float32) if cap_eval_rul else y_val
    y_test_effective = np.minimum(y_test, float(rul_cap)).astype(np.float32) if cap_eval_rul else y_test
    model, diagnostics = fit_mdfa(
        x_train=x_train,
        y_train=y_train,
        x_val=x_val,
        y_val=y_val_effective,
        seed=int(seed),
        rul_cap=float(rul_cap),
        device=str(device),
        epochs=int(epochs),
        batch_size=int(batch_size),
        learning_rate=float(learning_rate),
        hidden_dim=int(hidden_dim),
        dropout=float(dropout),
        conv_formulation=str(conv_formulation),
        lr_scheduler=str(lr_scheduler),
        snapshot_ensemble_k=int(snapshot_ensemble_k),
        snapshot_ensemble_min_val_rmse_delta=float(snapshot_ensemble_min_val_rmse_delta),
    )
    train_device = resolve_torch_device(device)
    val_pred_base = _predict(model, x_val, batch_size=int(batch_size), device=train_device, rul_cap=float(rul_cap))
    test_pred_base = _predict(model, x_test, batch_size=int(batch_size), device=train_device, rul_cap=float(rul_cap))
    calibration = _fit_output_calibration(
        policy=str(output_calibration),
        y_val=y_val_effective,
        val_pred=val_pred_base,
        rul_cap=float(rul_cap),
        min_val_rmse_delta=float(calibration_min_val_rmse_delta),
    )
    val_pred = _apply_output_calibration(val_pred_base, calibration)
    test_pred = _apply_output_calibration(test_pred_base, calibration)
    records = _prediction_records_with_raw(
        test_meta,
        y_test_effective,
        y_test,
        test_pred,
        split_role="test",
        subset_name=subset_name,
        y_pred_base=test_pred_base,
    )
    val_records = _prediction_records_with_raw(
        _val_meta,
        y_val_effective,
        y_val,
        val_pred,
        split_role="validation",
        subset_name=subset_name,
        y_pred_base=val_pred_base,
    )
    pca = preprocessor.get("pca")
    feature_spec = preprocessor["feature_spec"]
    config = _run_config(
        subset_name=subset_name,
        seed=int(seed),
        window_size=int(window_size),
        pca_variance=float(pca_variance),
        feature_policy=str(feature_policy),
        temporal_feature_mode=str(temporal_feature_mode),
        condition_normalization=str(condition_normalization),
        append_condition_onehot=bool(append_condition_onehot),
        val_fraction=float(val_fraction),
        max_train_windows=max_train_windows,
        max_val_windows=max_val_windows,
        rul_cap=float(rul_cap),
        cap_eval_rul=bool(cap_eval_rul),
        epochs=int(epochs),
        batch_size=int(batch_size),
        learning_rate=float(learning_rate),
        hidden_dim=int(hidden_dim),
        dropout=float(dropout),
        conv_formulation=str(conv_formulation),
        lr_scheduler=str(lr_scheduler),
        output_calibration=str(output_calibration),
        calibration_min_val_rmse_delta=float(calibration_min_val_rmse_delta),
        snapshot_ensemble_k=int(snapshot_ensemble_k),
        snapshot_ensemble_min_val_rmse_delta=float(snapshot_ensemble_min_val_rmse_delta),
    )
    diagnostics["output_calibration"] = calibration
    return {
        "subset": subset_name,
        "seed": int(seed),
        "protocol": "mdfa_2025_source_matched_candidate",
        "alignment_status": "source_matched_candidate_not_exact_reproduction",
        "run_config": config,
        "train_units": [int(value) for value in train_units],
        "val_units": [int(value) for value in val_units],
        "test_units": int(len(np.unique(subset.test[:, 0].astype(np.int64)))),
        "window_size": int(window_size),
        "rul_cap": float(rul_cap),
        "cap_eval_rul": bool(cap_eval_rul),
        "conv_formulation": str(conv_formulation),
        "train_windows": int(len(x_train)),
        "val_windows": int(len(x_val)),
        "test_windows": int(len(x_test)),
        "raw_feature_dim": int(subset.train.shape[1] - 2),
        "selected_raw_feature_dim": int(len(feature_spec["indices"])),
        "selected_feature_names": list(feature_spec["feature_names"]),
        "feature_policy": str(feature_policy),
        "temporal_feature_mode": str(temporal_feature_mode),
        "condition_normalization": str(condition_normalization),
        "append_condition_onehot": bool(append_condition_onehot),
        "condition_cluster_count": int(preprocessor.get("condition_cluster_count") or 1),
        "uses_pca": bool(feature_spec["pca"]),
        "pca_feature_dim": int((pca.n_components_ if pca is not None else len(feature_spec["indices"]))),
        "model_input_feature_dim": int(x_train.shape[2]),
        "pca_variance_threshold": float(pca_variance),
        "pca_explained_variance_ratio_sum": float(np.sum(pca.explained_variance_ratio_)) if pca is not None else None,
        "preprocessing_policy": (
            f"train_unit_only_{feature_policy}_{condition_normalization}"
            f"{'_condition_onehot' if append_condition_onehot else ''}"
        ),
        "rul_label_policy": "piecewise_rul_cap_125_eval_capped" if cap_eval_rul else "piecewise_train_cap_prediction_cap_eval_raw",
        "base_val_rul_metrics": rul_regression_metrics(y_val_effective, val_pred_base),
        "val_rul_metrics": rul_regression_metrics(y_val_effective, val_pred),
        "base_primary_test_metrics": rul_regression_metrics(y_test_effective, test_pred_base),
        "primary_test_metrics": rul_regression_metrics(y_test_effective, test_pred),
        "validation_prediction_records": val_records,
        "rul_prediction_records": records,
        "diagnostics": diagnostics,
    }


def summarize_results(results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    records = [row for result in results for row in result.get("rul_prediction_records", [])]
    subset_rows = []
    for result in sorted(results, key=lambda item: (str(item["subset"]), int(item["seed"]))):
        metrics = result.get("primary_test_metrics") or {}
        subset_rows.append(
            {
                "subset": result["subset"],
                "seed": int(result["seed"]),
                "rul_rmse": float(metrics.get("rul_rmse", 0.0)),
                "rul_mae": float(metrics.get("rul_mae", 0.0)),
                "rul_score": float(metrics.get("rul_score", 0.0)),
                "pca_feature_dim": int(result["pca_feature_dim"]),
                "model_input_feature_dim": int(result.get("model_input_feature_dim", result["pca_feature_dim"])),
                "feature_policy": str(result.get("feature_policy") or ""),
                "temporal_feature_mode": str(result.get("temporal_feature_mode") or "level"),
                "condition_normalization": str(result.get("condition_normalization") or "none"),
                "append_condition_onehot": bool(result.get("append_condition_onehot") or False),
                "train_seconds": float((result.get("diagnostics") or {}).get("train_seconds", 0.0)),
            }
        )
    metrics = rul_regression_metrics(
        np.asarray([row["rul_true"] for row in records], dtype=np.float32),
        np.asarray([row["rul_pred"] for row in records], dtype=np.float32),
    )
    return {
        "schema": VERSION,
        "status": "source_matched_candidate_not_exact_reproduction",
        "claim_boundary": (
            "This run uses MDFA 2025 published hyperparameters and raw C-MAPSS FD001-FD004 files, but remains "
            "a source-matched candidate until PCA/key-sensor details and matched budget are finalized."
        ),
        "source": {
            "id": MDFA_SOURCE["id"],
            "url": MDFA_SOURCE["url"],
            "published_hyperparameters": MDFA_SOURCE["published_hyperparameters"],
            "published_architecture": MDFA_SOURCE["published_architecture"],
            "published_mdfa_results": MDFA_SOURCE["published_mdfa_results"],
        },
        "overall_metrics": metrics,
        "subset_seed_rows": subset_rows,
        "rul_subset_metrics": summarize_rul_by_subset(records),
        "n_prediction_records": int(len(records)),
    }


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# C-MAPSS MDFA Source-Matched Candidate",
        "",
        f"- Status: `{summary['status']}`",
        f"- Claim boundary: {summary['claim_boundary']}",
        "",
        "## Overall",
        "",
    ]
    metrics = summary.get("overall_metrics") or {}
    lines.append(
        "- RMSE={rmse:.4f}, MAE={mae:.4f}, Score={score:.2f}, prediction records={records}".format(
            rmse=float(metrics.get("rul_rmse", 0.0)),
            mae=float(metrics.get("rul_mae", 0.0)),
            score=float(metrics.get("rul_score", 0.0)),
            records=int(summary.get("n_prediction_records", 0)),
        )
    )
    lines.extend(
        [
            "",
            "## Subset/Seed Rows",
            "",
            "| Subset | Seed | RMSE | MAE | Score | Feature policy | Temporal mode | Condition policy | PCA/Input dim | Train seconds |",
            "|---|---:|---:|---:|---:|---|---|---|---:|---:|",
        ]
    )
    for row in summary["subset_seed_rows"]:
        lines.append(
            "| {subset} | {seed} | {rmse:.4f} | {mae:.4f} | {score:.2f} | {feature} | {temporal} | {condition}{onehot} | {pca}/{input_dim} | {train:.2f} |".format(
                subset=row["subset"],
                seed=int(row["seed"]),
                rmse=float(row["rul_rmse"]),
                mae=float(row["rul_mae"]),
                score=float(row["rul_score"]),
                feature=str(row.get("feature_policy") or "-"),
                temporal=str(row.get("temporal_feature_mode") or "level"),
                condition=str(row.get("condition_normalization") or "none"),
                onehot="+onehot" if bool(row.get("append_condition_onehot")) else "",
                pca=int(row["pca_feature_dim"]),
                input_dim=int(row.get("model_input_feature_dim", row["pca_feature_dim"])),
                train=float(row["train_seconds"]),
            )
        )
    return "\n".join(lines).rstrip() + "\n"


def run_experiment(
    *,
    raw_dir: Path,
    output_dir: Path,
    subsets: Sequence[str],
    seeds: Sequence[int],
    window_size: int,
    pca_variance: float,
    feature_policy: str,
    temporal_feature_mode: str = "level",
    condition_normalization: str = "none",
    append_condition_onehot: bool = False,
    val_fraction: float,
    max_train_windows: int | None,
    max_val_windows: int | None,
    rul_cap: float,
    cap_eval_rul: bool,
    device: str,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    hidden_dim: int,
    dropout: float,
    conv_formulation: str,
    lr_scheduler: str,
    output_calibration: str = "none",
    calibration_min_val_rmse_delta: float = 0.0,
    snapshot_ensemble_k: int = 1,
    snapshot_ensemble_min_val_rmse_delta: float = 0.0,
    resume: bool = False,
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    output_dir = Path(output_dir)
    os.makedirs(_fs_path(output_dir), exist_ok=True)
    for seed in seeds:
        seed_payload = {
            "schema": VERSION,
            "seed": int(seed),
            "subsets": [],
            "source": MDFA_SOURCE,
        }
        for subset in subsets:
            expected_config = _run_config(
                subset_name=str(subset),
                seed=int(seed),
                window_size=int(window_size),
                pca_variance=float(pca_variance),
                feature_policy=str(feature_policy),
                temporal_feature_mode=str(temporal_feature_mode),
                condition_normalization=str(condition_normalization),
                append_condition_onehot=bool(append_condition_onehot),
                val_fraction=float(val_fraction),
                max_train_windows=max_train_windows,
                max_val_windows=max_val_windows,
                rul_cap=float(rul_cap),
                cap_eval_rul=bool(cap_eval_rul),
                epochs=int(epochs),
                batch_size=int(batch_size),
                learning_rate=float(learning_rate),
                hidden_dim=int(hidden_dim),
                dropout=float(dropout),
                conv_formulation=str(conv_formulation),
                lr_scheduler=str(lr_scheduler),
                output_calibration=str(output_calibration),
                calibration_min_val_rmse_delta=float(calibration_min_val_rmse_delta),
                snapshot_ensemble_k=int(snapshot_ensemble_k),
                snapshot_ensemble_min_val_rmse_delta=float(snapshot_ensemble_min_val_rmse_delta),
            )
            subset_path = _subset_result_path(output_dir, int(seed), str(subset))
            cached = _read_json_if_present(subset_path) if resume else None
            if resume and _cached_result_matches(cached, expected_config):
                result = cached
                print(f"{subset} seed={int(seed)} cached={subset_path}")
            else:
                result = run_subset(
                    subset_name=str(subset),
                    seed=int(seed),
                    raw_dir=Path(raw_dir),
                    window_size=int(window_size),
                    pca_variance=float(pca_variance),
                    feature_policy=str(feature_policy),
                    temporal_feature_mode=str(temporal_feature_mode),
                    condition_normalization=str(condition_normalization),
                    append_condition_onehot=bool(append_condition_onehot),
                    val_fraction=float(val_fraction),
                    max_train_windows=max_train_windows,
                    max_val_windows=max_val_windows,
                    rul_cap=float(rul_cap),
                    cap_eval_rul=bool(cap_eval_rul),
                    device=str(device),
                    epochs=int(epochs),
                    batch_size=int(batch_size),
                    learning_rate=float(learning_rate),
                    hidden_dim=int(hidden_dim),
                    dropout=float(dropout),
                    conv_formulation=str(conv_formulation),
                    lr_scheduler=str(lr_scheduler),
                    output_calibration=str(output_calibration),
                    calibration_min_val_rmse_delta=float(calibration_min_val_rmse_delta),
                    snapshot_ensemble_k=int(snapshot_ensemble_k),
                    snapshot_ensemble_min_val_rmse_delta=float(snapshot_ensemble_min_val_rmse_delta),
                )
                _write_json(subset_path, result)
            print(
                "{subset} seed={seed} rmse={rmse:.4f} score={score:.2f}".format(
                    subset=subset,
                    seed=int(seed),
                    rmse=float((result["primary_test_metrics"] or {}).get("rul_rmse", 0.0)),
                    score=float((result["primary_test_metrics"] or {}).get("rul_score", 0.0)),
                )
            )
            seed_payload["subsets"].append(result)
            results.append(result)
            _write_json(output_dir / f"cmapss_mdfa_source_matched_seed{int(seed)}.json", seed_payload)
            partial_summary = summarize_results(results)
            partial_summary["expected_subset_seed_count"] = int(len(subsets) * len(seeds))
            partial_summary["completed_subset_seed_count"] = int(len(results))
            partial_summary["run_complete"] = bool(len(results) == len(subsets) * len(seeds))
            _write_json(output_dir / "cmapss_mdfa_source_matched_summary.json", partial_summary)
            _write_text(output_dir / "cmapss_mdfa_source_matched_summary.md", render_markdown(partial_summary))
    summary = summarize_results(results)
    summary["expected_subset_seed_count"] = int(len(subsets) * len(seeds))
    summary["completed_subset_seed_count"] = int(len(results))
    summary["run_complete"] = bool(len(results) == len(subsets) * len(seeds))
    _write_json(output_dir / "cmapss_mdfa_source_matched_summary.json", summary)
    _write_text(output_dir / "cmapss_mdfa_source_matched_summary.md", render_markdown(summary))
    return summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run source-matched MDFA 2025 candidate on raw C-MAPSS files.")
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--subsets", type=str, default="FD001,FD002,FD003,FD004")
    parser.add_argument("--seeds", type=str, default="42")
    parser.add_argument("--window-size", type=int, default=int(MDFA_SOURCE["published_hyperparameters"]["window_size"]))
    parser.add_argument("--pca-variance", type=float, default=0.95)
    parser.add_argument("--feature-policy", choices=sorted(FEATURE_POLICIES), default="all24_pca")
    parser.add_argument("--temporal-feature-mode", choices=TEMPORAL_FEATURE_MODES, default="level")
    parser.add_argument("--condition-normalization", choices=CONDITION_NORMALIZATION_POLICIES, default="none")
    parser.add_argument("--append-condition-onehot", action="store_true")
    parser.add_argument("--val-fraction", type=float, default=0.20)
    parser.add_argument("--max-train-windows-per-subset", type=int, default=0)
    parser.add_argument("--max-val-windows-per-subset", type=int, default=0)
    parser.add_argument("--rul-cap", type=float, default=125.0)
    parser.add_argument("--no-cap-eval-rul", action="store_true", help="Evaluate against raw test RUL labels instead of source-style capped labels.")
    parser.add_argument("--device", type=str, default="auto")
    parser.add_argument("--epochs", type=int, default=int(MDFA_SOURCE["published_hyperparameters"]["epochs"]))
    parser.add_argument("--batch-size", type=int, default=int(MDFA_SOURCE["published_hyperparameters"]["batch_size"]))
    parser.add_argument("--learning-rate", type=float, default=float(MDFA_SOURCE["published_hyperparameters"]["learning_rate"]))
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--dropout", type=float, default=float(MDFA_SOURCE["published_hyperparameters"]["dropout"]))
    parser.add_argument("--conv-formulation", choices=["source_2d", "temporal_1d"], default="source_2d")
    parser.add_argument("--lr-scheduler", choices=["none", "reduce_on_plateau"], default="none")
    parser.add_argument("--output-calibration", choices=["none", "affine_val"], default="none")
    parser.add_argument("--calibration-min-val-rmse-delta", type=float, default=0.0)
    parser.add_argument("--snapshot-ensemble-k", type=int, default=1)
    parser.add_argument("--snapshot-ensemble-min-val-rmse-delta", type=float, default=0.0)
    parser.add_argument("--resume", action="store_true", help="Reuse completed seed/subset result files when the run config matches.")
    args = parser.parse_args(argv)
    summary = run_experiment(
        raw_dir=Path(args.raw_dir),
        output_dir=Path(args.output_dir),
        subsets=_split_csv(args.subsets),
        seeds=_split_seeds(args.seeds),
        window_size=int(args.window_size),
        pca_variance=float(args.pca_variance),
        feature_policy=str(args.feature_policy),
        temporal_feature_mode=str(args.temporal_feature_mode),
        condition_normalization=str(args.condition_normalization),
        append_condition_onehot=bool(args.append_condition_onehot),
        val_fraction=float(args.val_fraction),
        max_train_windows=int(args.max_train_windows_per_subset) if int(args.max_train_windows_per_subset) > 0 else None,
        max_val_windows=int(args.max_val_windows_per_subset) if int(args.max_val_windows_per_subset) > 0 else None,
        rul_cap=float(args.rul_cap),
        cap_eval_rul=not bool(args.no_cap_eval_rul),
        device=str(args.device),
        epochs=int(args.epochs),
        batch_size=int(args.batch_size),
        learning_rate=float(args.learning_rate),
        hidden_dim=int(args.hidden_dim),
        dropout=float(args.dropout),
        conv_formulation=str(args.conv_formulation),
        lr_scheduler=str(args.lr_scheduler),
        output_calibration=str(args.output_calibration),
        calibration_min_val_rmse_delta=float(args.calibration_min_val_rmse_delta),
        snapshot_ensemble_k=int(args.snapshot_ensemble_k),
        snapshot_ensemble_min_val_rmse_delta=float(args.snapshot_ensemble_min_val_rmse_delta),
        resume=bool(args.resume),
    )
    print(str(Path(args.output_dir) / "cmapss_mdfa_source_matched_summary.json"))
    print(render_markdown(summary))


if __name__ == "__main__":
    main()
