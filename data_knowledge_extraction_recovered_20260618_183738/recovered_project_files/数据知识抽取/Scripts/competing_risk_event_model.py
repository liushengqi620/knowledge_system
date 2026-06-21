from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
import torch
import torch.nn as nn


COMPETING_RISK_CAUSE_GROUPS = [
    "temperature_flux",
    "mold_level_slag_risk",
    "process_fluctuation",
    "speed_stopper_flow",
    "heat_transfer_imbalance",
]

CAUSE_CLASS_ID = {
    "temperature_flux": 1,
    "mold_level_slag_risk": 2,
    "process_fluctuation": 3,
    "speed_stopper_flow": 4,
    "heat_transfer_imbalance": 5,
}

CLASS_ID_TO_CAUSE = {v: k for k, v in CAUSE_CLASS_ID.items()}

STAGE_NAMES = ["late", "mid", "early"]
STAGE_TO_ID = {name: i for i, name in enumerate(STAGE_NAMES)}


def _safe_class_ids(y: pd.DataFrame) -> np.ndarray:
    return pd.to_numeric(y.get("event_quality_class_id"), errors="coerce").fillna(0).astype(int).to_numpy()


def build_candidate_cause_mask(y: pd.DataFrame) -> np.ndarray:
    n = int(len(y))
    mask = np.zeros((n, len(COMPETING_RISK_CAUSE_GROUPS)), dtype=np.float32)
    group_col = y.get("quality_abnormal_groups")
    if group_col is not None:
        for i, raw in enumerate(group_col.astype("string").fillna("").tolist()):
            groups = {item.strip() for item in str(raw).split(";") if item.strip()}
            for j, group in enumerate(COMPETING_RISK_CAUSE_GROUPS):
                if group in groups:
                    mask[i, j] = 1.0
    class_ids = _safe_class_ids(y)
    for i, class_id in enumerate(class_ids):
        if mask[i].sum() > 0:
            continue
        cause = CLASS_ID_TO_CAUSE.get(int(class_id))
        if cause is not None:
            mask[i, COMPETING_RISK_CAUSE_GROUPS.index(cause)] = 1.0
    return mask


def stage_ids_from_series(values: Sequence[Any] | pd.Series) -> np.ndarray:
    out: list[int] = []
    for raw in list(values):
        key = str(raw).strip().lower()
        out.append(int(STAGE_TO_ID.get(key, 0)))
    return np.asarray(out, dtype=np.int64)


class _CompetingRiskNet(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, output_dim: int, dropout: float) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.SiLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


@dataclass
class CompetingRiskEventModel:
    hidden_dim: int = 64
    learning_rate: float = 2e-3
    weight_decay: float = 1e-4
    max_epochs: int = 80
    batch_size: int = 512
    dropout: float = 0.10
    random_state: int = 42

    def _standardize_fit(self, x: np.ndarray) -> np.ndarray:
        arr = np.asarray(x, dtype=np.float32)
        self.mean_ = np.nanmean(arr, axis=0)
        self.scale_ = np.nanstd(arr, axis=0)
        self.scale_ = np.where(np.isfinite(self.scale_) & (self.scale_ > 1e-6), self.scale_, 1.0)
        arr = np.where(np.isfinite(arr), arr, self.mean_)
        return ((arr - self.mean_) / self.scale_).astype(np.float32)

    def _standardize(self, x: np.ndarray) -> np.ndarray:
        arr = np.asarray(x, dtype=np.float32)
        arr = np.where(np.isfinite(arr), arr, self.mean_)
        return ((arr - self.mean_) / self.scale_).astype(np.float32)

    def _loss(
        self,
        logits: torch.Tensor,
        candidate_mask: torch.Tensor,
        stage_ids: torch.Tensor,
        risk_label: torch.Tensor,
        sample_weight: torch.Tensor,
    ) -> torch.Tensor:
        prob = torch.softmax(logits, dim=1)
        normal_prob = prob[:, 0]
        joint = prob[:, 1:].reshape(-1, len(COMPETING_RISK_CAUSE_GROUPS), len(STAGE_NAMES))
        row_idx = torch.arange(len(stage_ids), device=logits.device)
        stage_joint = joint[row_idx, :, stage_ids]
        candidate_mass = torch.sum(stage_joint * candidate_mask, dim=1)
        likelihood = torch.where(risk_label > 0.5, candidate_mass, normal_prob)
        loss = -torch.log(torch.clamp(likelihood, 1e-8, 1.0))
        return torch.mean(loss * sample_weight)

    def fit(
        self,
        x: np.ndarray,
        candidate_cause_mask: np.ndarray,
        stage_ids: np.ndarray,
        risk_label: np.ndarray,
        sample_weight: np.ndarray | None = None,
    ) -> "CompetingRiskEventModel":
        torch.manual_seed(int(self.random_state))
        np.random.seed(int(self.random_state))
        x_arr = self._standardize_fit(np.asarray(x, dtype=np.float32))
        mask = np.asarray(candidate_cause_mask, dtype=np.float32)
        stages = np.asarray(stage_ids, dtype=np.int64).reshape(-1)
        risk = np.asarray(risk_label, dtype=np.float32).reshape(-1)
        if len(x_arr) != len(mask) or len(x_arr) != len(stages) or len(x_arr) != len(risk):
            raise ValueError("x, candidate_cause_mask, stage_ids and risk_label must have the same row count")
        if sample_weight is None:
            weights = np.ones(len(x_arr), dtype=np.float32)
        else:
            weights = np.asarray(sample_weight, dtype=np.float32).reshape(-1)
        output_dim = 1 + len(COMPETING_RISK_CAUSE_GROUPS) * len(STAGE_NAMES)
        self.model_ = _CompetingRiskNet(x_arr.shape[1], int(self.hidden_dim), output_dim, float(self.dropout))
        opt = torch.optim.AdamW(self.model_.parameters(), lr=float(self.learning_rate), weight_decay=float(self.weight_decay))
        x_t = torch.from_numpy(x_arr)
        mask_t = torch.from_numpy(mask)
        stage_t = torch.from_numpy(stages)
        risk_t = torch.from_numpy(risk)
        weight_t = torch.from_numpy(weights)
        n = len(x_arr)
        batch_size = max(8, min(int(self.batch_size), n))
        rng = np.random.default_rng(int(self.random_state))
        self.model_.train()
        for _epoch in range(max(1, int(self.max_epochs))):
            order = rng.permutation(n)
            for start in range(0, n, batch_size):
                idx = torch.from_numpy(order[start : start + batch_size].astype(np.int64))
                opt.zero_grad()
                logits = self.model_(x_t[idx])
                loss = self._loss(logits, mask_t[idx], stage_t[idx], risk_t[idx], weight_t[idx])
                loss.backward()
                opt.step()
        return self

    def predict_proba(self, x: np.ndarray) -> dict[str, np.ndarray]:
        if not hasattr(self, "model_"):
            raise RuntimeError("CompetingRiskEventModel must be fit before predict_proba.")
        self.model_.eval()
        x_t = torch.from_numpy(self._standardize(np.asarray(x, dtype=np.float32)))
        with torch.no_grad():
            joint = torch.softmax(self.model_(x_t), dim=1).cpu().numpy()
        normal = joint[:, :1]
        event_joint = joint[:, 1:].reshape(-1, len(COMPETING_RISK_CAUSE_GROUPS), len(STAGE_NAMES))
        cause_prob = event_joint.sum(axis=2)
        stage_prob = event_joint.sum(axis=1)
        class_prob = np.concatenate([normal, cause_prob], axis=1)
        class_prob = class_prob / np.clip(class_prob.sum(axis=1, keepdims=True), 1e-8, None)
        return {
            "joint_probabilities": joint.astype(np.float32),
            "class_probabilities": class_prob.astype(np.float32),
            "stage_probabilities": stage_prob.astype(np.float32),
            "risk_probability": (1.0 - normal.reshape(-1)).astype(np.float32),
        }


def candidate_mask_frame(mask: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame(
        {
            f"candidate_cause_{group}": mask[:, i].astype("int8")
            for i, group in enumerate(COMPETING_RISK_CAUSE_GROUPS)
        }
    )
