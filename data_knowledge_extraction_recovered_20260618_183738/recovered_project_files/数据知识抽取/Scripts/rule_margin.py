from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class RuleSpec:
    name: str
    column: str
    lower: float | None = None
    upper: float | None = None
    scale: float | None = None
    group_keys: tuple[str, ...] = ()


def _safe_scale(series: pd.Series) -> float:
    x = pd.to_numeric(series, errors="coerce")
    finite = x[np.isfinite(x)]
    if finite.empty:
        return 1.0
    q75, q25 = finite.quantile([0.75, 0.25])
    iqr = float(q75 - q25)
    if iqr > 1e-9:
        return iqr
    std = float(finite.std(ddof=0))
    return std if std > 1e-9 else 1.0


def _rule_scale(df: pd.DataFrame, rule: RuleSpec, default_scale_mode: str) -> pd.Series:
    if rule.scale is not None and float(rule.scale) > 0:
        return pd.Series(float(rule.scale), index=df.index, dtype=float)
    if rule.group_keys and default_scale_mode.endswith("_by_regime"):
        valid_keys = [key for key in rule.group_keys if key in df.columns]
        if valid_keys:
            return (
                df.groupby(valid_keys, dropna=False)[rule.column]
                .transform(_safe_scale)
                .astype(float)
                .replace(0.0, 1.0)
            )
    return pd.Series(_safe_scale(df[rule.column]), index=df.index, dtype=float)


def _signed_rule_margin(df: pd.DataFrame, rule: RuleSpec, scale_mode: str) -> pd.Series:
    if rule.column not in df.columns:
        raise KeyError(f"Rule column not found: {rule.column}")
    x = pd.to_numeric(df[rule.column], errors="coerce")
    scale = _rule_scale(df, rule, scale_mode).replace(0.0, 1.0)
    candidates: list[pd.Series] = []
    if rule.upper is not None:
        candidates.append((x - float(rule.upper)) / scale)
    if rule.lower is not None:
        candidates.append((float(rule.lower) - x) / scale)
    if not candidates:
        raise ValueError(f"Rule {rule.name!r} must define lower and/or upper.")
    margin = pd.concat(candidates, axis=1).max(axis=1)
    return margin.replace([np.inf, -np.inf], np.nan).fillna(-np.inf)


def compute_rule_margin(
    df: pd.DataFrame,
    rules: Sequence[RuleSpec],
    *,
    scale_mode: str = "iqr_by_regime",
) -> pd.DataFrame:
    if not rules:
        raise ValueError("At least one RuleSpec is required.")
    margins = pd.DataFrame(
        {rule.name: _signed_rule_margin(df, rule, scale_mode) for rule in rules},
        index=df.index,
    )
    values = margins.to_numpy(dtype=float)
    active_idx = np.argmax(values, axis=1)
    active_rules = [rules[int(i)] for i in active_idx]
    rule_margin = values[np.arange(len(values)), active_idx]
    out = pd.DataFrame(index=df.index)
    out["rule_margin"] = rule_margin
    out["rule_margin_abs"] = np.abs(rule_margin)
    out["active_rule"] = [rule.name for rule in active_rules]
    out["active_rule_column"] = [rule.column for rule in active_rules]
    out["rule_margin_scale_source"] = [
        "fixed" if rule.scale is not None else scale_mode for rule in active_rules
    ]
    return out


def assign_boundary_region(margin: pd.Series | np.ndarray, eps: float) -> pd.Series:
    m = pd.Series(margin, dtype=float)
    e = max(0.0, float(eps))
    region = np.where(
        m < -e,
        "clear_normal",
        np.where(
            m < 0.0,
            "normal_boundary",
            np.where(m <= e, "abnormal_boundary", "clear_abnormal"),
        ),
    )
    return pd.Series(region, index=m.index, dtype=object)


def summarize_boundary_regions(
    margin: pd.Series | np.ndarray,
    eps_list: Sequence[float],
) -> pd.DataFrame:
    m = pd.Series(margin, dtype=float)
    rows: list[dict[str, float | int]] = []
    n = int(len(m))
    for eps in eps_list:
        regions = assign_boundary_region(m, float(eps))
        counts = regions.value_counts().to_dict()
        boundary_n = int(
            counts.get("normal_boundary", 0) + counts.get("abnormal_boundary", 0)
        )
        rows.append(
            {
                "eps": float(eps),
                "n": n,
                "clear_normal_n": int(counts.get("clear_normal", 0)),
                "normal_boundary_n": int(counts.get("normal_boundary", 0)),
                "abnormal_boundary_n": int(counts.get("abnormal_boundary", 0)),
                "clear_abnormal_n": int(counts.get("clear_abnormal", 0)),
                "boundary_n": boundary_n,
                "boundary_ratio": float(boundary_n / n) if n else 0.0,
            }
        )
    return pd.DataFrame(rows)
