from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.multioutput import MultiOutputClassifier
from sklearn.pipeline import make_pipeline

from run_major_quality_abnormality_experiment import (
    BINARY_IN,
    LABEL_DISPLAY,
    MAIN_LABELS,
    MULTILABEL_IN,
    build_tree,
    binary_positive_proba,
    json_sanitize,
    multioutput_positive_proba,
    select_feature_columns,
    tune_binary_threshold,
    tune_multilabel_thresholds,
)


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "knowledge_exports" / "rule_temporal_ablation_v1"
FIGURE_DIR = OUT_DIR / "figures"


@dataclass(frozen=True)
class FixedRule:
    name: str
    column: str
    lower: float | None = None
    upper: float | None = None
    scale: float | None = None


@dataclass(frozen=True)
class FittedRule:
    name: str
    column: str
    lower: float | None
    upper: float | None
    scale: float


@dataclass(frozen=True)
class ExperimentConfig:
    name: str
    split: str
    use_rule_margin: bool
    use_temporal: bool
    description: str


DEFAULT_RULES = [
    FixedRule("superheat_window", "过热度/℃", lower=0.0, upper=150.0),
    FixedRule("superheat_alias_window", "superheat", lower=0.0, upper=150.0),
    FixedRule("mold_level_range", "液面波动极差/mm", upper=12.0),
    FixedRule("mold_level_ge7_count", "液面波动的个数≥±7mm", upper=2.0),
    FixedRule("mold_level_ge10_count", "液面波动的个数≥±10mm", upper=1.0),
    FixedRule("cast_speed_range", "拉速波动/(m/min)", upper=0.08),
    FixedRule("td_weight_range", "中间包吨位波动/t", upper=8.0),
    FixedRule("heat_exchange_ew_diff", "东西拔热量差/℃", upper=90.0),
    FixedRule("heat_exchange_ns_diff", "南北拔热量差/℃", upper=90.0),
]

TEMPORAL_PRIORITY_COLUMNS = [
    "过热度/℃",
    "TD_avg_temp",
    "中间包吨位平均值/t",
    "中间包吨位波动/t",
    "拉速平均值/(m/min)",
    "拉速波动/(m/min)",
    "液面波动极差/mm",
    "液面波动均值/mm",
    "液面波动的个数≥±7mm",
    "液面波动的个数≥±10mm",
    "上水口流量波动/(L/min)",
    "上滑板流量波动/(L/min)",
    "塞棒氩气流量波动/(L/min)",
    "塞棒氩气压力波动/kPa",
    "塞棒开口度平均值/mm",
    "东西拔热量差/℃",
    "南北拔热量差/℃",
    "结晶器电磁搅拌电流波动/A",
]

CONFIGS = [
    ExperimentConfig(
        "base_static_group",
        "group",
        False,
        False,
        "Static process features with group split.",
    ),
    ExperimentConfig(
        "rule_margin_group",
        "group",
        True,
        False,
        "Static process features plus signed normalized rule-margin features.",
    ),
    ExperimentConfig(
        "temporal_group",
        "group",
        False,
        True,
        "Static process features plus line-wise historical lag, delta, and rolling features.",
    ),
    ExperimentConfig(
        "rule_temporal_group",
        "group",
        True,
        True,
        "Static process features plus rule-margin and temporal propagation features.",
    ),
    ExperimentConfig(
        "base_static_time",
        "time_holdout",
        False,
        False,
        "Static process features with chronological holdout.",
    ),
    ExperimentConfig(
        "rule_margin_time",
        "time_holdout",
        True,
        False,
        "Rule-margin features under chronological holdout.",
    ),
    ExperimentConfig(
        "temporal_time",
        "time_holdout",
        False,
        True,
        "Temporal propagation features under chronological holdout.",
    ),
    ExperimentConfig(
        "rule_temporal_time",
        "time_holdout",
        True,
        True,
        "Rule-margin plus temporal propagation features under chronological holdout.",
    ),
]


def parse_process_sequence_key(value: Any) -> dict[str, str]:
    parts = str(value).split("|")
    return {
        "caster_id": parts[0] if len(parts) > 0 and parts[0] else "unknown",
        "strand_id": parts[1] if len(parts) > 1 and parts[1] else "unknown",
        "heat_id": parts[2] if len(parts) > 2 and parts[2] else "unknown",
    }


def safe_feature_name(name: str) -> str:
    text = str(name)
    text = text.replace("℃", "C").replace("≥", "ge").replace("≤", "le").replace("±", "pm")
    text = re.sub(r"[^\w\u4e00-\u9fff]+", "_", text, flags=re.UNICODE)
    return text.strip("_")[:80]


def robust_scale(series: pd.Series) -> float:
    x = pd.to_numeric(series, errors="coerce")
    x = x[np.isfinite(x)]
    if x.empty:
        return 1.0
    q75, q25 = x.quantile([0.75, 0.25])
    iqr = float(q75 - q25)
    if iqr > 1e-9:
        return iqr
    std = float(x.std(ddof=0))
    return std if std > 1e-9 else 1.0


class RuleMarginTransformer:
    def __init__(self, rules: Sequence[FittedRule]):
        if not rules:
            raise ValueError("No fitted rules are available for rule-margin features.")
        self.rules_ = list(rules)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        raw_margins: dict[str, pd.Series] = {}
        for rule in self.rules_:
            x = pd.to_numeric(df[rule.column], errors="coerce")
            candidates: list[pd.Series] = []
            if rule.upper is not None:
                candidates.append((x - float(rule.upper)) / rule.scale)
            if rule.lower is not None:
                candidates.append((float(rule.lower) - x) / rule.scale)
            raw_margins[rule.name] = pd.concat(candidates, axis=1).max(axis=1)

        margins = pd.DataFrame(raw_margins, index=df.index).replace([np.inf, -np.inf], np.nan)
        filled = margins.fillna(-np.inf)
        values = filled.to_numpy(dtype=float)
        active_idx = np.argmax(values, axis=1)
        rule_margin = values[np.arange(len(values)), active_idx]
        finite_margin = np.where(np.isfinite(rule_margin), rule_margin, np.nan)

        out = pd.DataFrame(index=df.index)
        out["rule_margin"] = finite_margin
        out["rule_margin_abs"] = np.abs(finite_margin)
        out["rule_violation"] = np.maximum(finite_margin, 0.0)
        out["rule_boundary_score"] = np.exp(-np.abs(finite_margin))
        out["rule_near_boundary_eps025"] = (np.abs(finite_margin) <= 0.25).astype(float)
        for rule in self.rules_:
            out[f"margin__{safe_feature_name(rule.name)}"] = margins[rule.name]
        return out


def fit_rule_margin_transformer(
    df: pd.DataFrame,
    train_idx: Sequence[int] | np.ndarray,
    rules: Sequence[FixedRule] = DEFAULT_RULES,
) -> RuleMarginTransformer:
    train = df.iloc[np.asarray(train_idx, dtype=int)]
    fitted: list[FittedRule] = []
    seen_columns: set[str] = set()
    for rule in rules:
        if rule.column not in df.columns or rule.column in seen_columns:
            continue
        seen_columns.add(rule.column)
        scale = float(rule.scale) if rule.scale is not None else robust_scale(train[rule.column])
        fitted.append(
            FittedRule(
                name=rule.name,
                column=rule.column,
                lower=rule.lower,
                upper=rule.upper,
                scale=max(scale, 1e-9),
            )
        )
    return RuleMarginTransformer(fitted)


def add_line_keys(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "process_sequence_key" in out.columns:
        parsed = out["process_sequence_key"].map(parse_process_sequence_key)
        out["temporal_caster_id"] = [item["caster_id"] for item in parsed]
        out["temporal_strand_id"] = [item["strand_id"] for item in parsed]
    else:
        out["temporal_caster_id"] = "unknown"
        out["temporal_strand_id"] = "unknown"
    return out


def choose_temporal_columns(feature_cols: Sequence[str], max_features: int) -> list[str]:
    available = [col for col in TEMPORAL_PRIORITY_COLUMNS if col in feature_cols]
    if len(available) >= max_features:
        return available[:max_features]
    for col in feature_cols:
        if col not in available:
            available.append(col)
        if len(available) >= max_features:
            break
    return available


def add_temporal_history_features(
    df: pd.DataFrame,
    base_feature_cols: Sequence[str],
    *,
    max_features: int = 18,
) -> tuple[pd.DataFrame, list[str]]:
    out = add_line_keys(df)
    time = pd.to_datetime(out["process_time"], errors="coerce") if "process_time" in out.columns else pd.Series(pd.NaT, index=out.index)
    out["_temporal_time"] = time
    order_cols = ["temporal_caster_id", "temporal_strand_id", "_temporal_time", "record_id" if "record_id" in out.columns else out.index.name]
    sort_cols = [col for col in order_cols if isinstance(col, str) and col in out.columns]
    sorted_idx = out.sort_values(sort_cols, kind="mergesort").index
    sorted_out = out.loc[sorted_idx].copy()
    group_cols = ["temporal_caster_id", "temporal_strand_id"]
    temporal_cols: list[str] = []
    selected = choose_temporal_columns(base_feature_cols, max_features=max_features)
    grouped = sorted_out.groupby(group_cols, dropna=False, sort=False)

    for col in selected:
        safe = safe_feature_name(col)
        values = pd.to_numeric(sorted_out[col], errors="coerce")
        lag_name = f"hist_lag1__{safe}"
        delta_name = f"hist_delta1__{safe}"
        roll_mean_name = f"hist_roll3_mean__{safe}"
        roll_std_name = f"hist_roll3_std__{safe}"
        sorted_out[lag_name] = grouped[col].shift(1)
        sorted_out[delta_name] = values - pd.to_numeric(sorted_out[lag_name], errors="coerce")
        sorted_out[roll_mean_name] = grouped[col].shift(1).groupby([sorted_out[c] for c in group_cols], sort=False).rolling(3, min_periods=1).mean().reset_index(level=[0, 1], drop=True)
        sorted_out[roll_std_name] = grouped[col].shift(1).groupby([sorted_out[c] for c in group_cols], sort=False).rolling(3, min_periods=2).std().reset_index(level=[0, 1], drop=True)
        temporal_cols.extend([lag_name, delta_name, roll_mean_name, roll_std_name])

    restored = sorted_out.sort_index()
    restored = restored.drop(columns=["_temporal_time"], errors="ignore")
    return restored, temporal_cols


def ordered_fraction_split(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    idx = np.arange(len(df))
    train_end = int(len(idx) * 0.60)
    val_end = int(len(idx) * 0.80)
    return idx[:train_end], idx[train_end:val_end], idx[val_end:], "ordered_60_20_20"


def group_split_indices(df: pd.DataFrame, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    idx = np.arange(len(df))
    group_col = "process_sequence_key"
    if group_col not in df.columns or df[group_col].nunique(dropna=False) < 5:
        return ordered_fraction_split(df)
    groups = df[group_col].astype(str).fillna("group_unknown").to_numpy()
    first = GroupShuffleSplit(n_splits=1, test_size=0.40, random_state=seed)
    train_idx, temp_idx = next(first.split(idx, groups=groups))
    second = GroupShuffleSplit(n_splits=1, test_size=0.50, random_state=seed + 1)
    val_rel, test_rel = next(second.split(temp_idx, groups=groups[temp_idx]))
    return train_idx, temp_idx[val_rel], temp_idx[test_rel], "group:process_sequence_key"


def time_holdout_split_indices(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    if "process_time" not in df.columns:
        return ordered_fraction_split(df)
    time = pd.to_datetime(df["process_time"], errors="coerce")
    order = np.argsort(time.fillna(pd.Timestamp.max).to_numpy())
    sorted_time = time.iloc[order]
    train_idx = order[np.asarray(sorted_time < pd.Timestamp("2022-09-01"))]
    val_idx = order[np.asarray((sorted_time >= pd.Timestamp("2022-09-01")) & (sorted_time < pd.Timestamp("2022-11-01")))]
    test_idx = order[np.asarray(sorted_time >= pd.Timestamp("2022-11-01"))]
    if min(len(train_idx), len(val_idx), len(test_idx)) < 100:
        sorted_df = df.iloc[order].reset_index(drop=False)
        train_rel, val_rel, test_rel, _ = ordered_fraction_split(sorted_df)
        original_idx = sorted_df["index"].to_numpy()
        return original_idx[train_rel], original_idx[val_rel], original_idx[test_rel], "ordered_time_fallback"
    return train_idx, val_idx, test_idx, "time_holdout:train_2022-01_08,val_09_10,test_11_12"


def split_indices(df: pd.DataFrame, config: ExperimentConfig, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    if config.split == "group":
        return group_split_indices(df, seed)
    if config.split == "time_holdout":
        return time_holdout_split_indices(df)
    raise ValueError(f"Unknown split: {config.split}")


def enrich_features(
    df: pd.DataFrame,
    base_feature_cols: Sequence[str],
    train_idx: Sequence[int] | np.ndarray,
    config: ExperimentConfig,
) -> tuple[pd.DataFrame, list[str], dict[str, Any]]:
    out = df.copy()
    feature_cols = list(base_feature_cols)
    diagnostics: dict[str, Any] = {}

    if config.use_temporal:
        out, temporal_cols = add_temporal_history_features(out, base_feature_cols)
        feature_cols.extend(temporal_cols)
        diagnostics["temporal_feature_count"] = int(len(temporal_cols))
        diagnostics["temporal_base_features"] = choose_temporal_columns(base_feature_cols, max_features=18)
    else:
        diagnostics["temporal_feature_count"] = 0

    if config.use_rule_margin:
        transformer = fit_rule_margin_transformer(out, train_idx)
        margin_df = transformer.transform(out)
        out = pd.concat([out, margin_df], axis=1)
        rule_cols = [col for col in margin_df.columns if pd.api.types.is_numeric_dtype(margin_df[col])]
        feature_cols.extend(rule_cols)
        diagnostics["rule_feature_count"] = int(len(rule_cols))
        diagnostics["rule_scales"] = {rule.name: rule.scale for rule in transformer.rules_}
        diagnostics["boundary_summary"] = boundary_sensitivity_summary(margin_df["rule_margin"], [0.10, 0.25, 0.50, 1.00])
    else:
        diagnostics["rule_feature_count"] = 0
    return out, feature_cols, diagnostics


def boundary_sensitivity_summary(margin: pd.Series, eps_values: Iterable[float]) -> list[dict[str, Any]]:
    m = pd.to_numeric(margin, errors="coerce")
    rows: list[dict[str, Any]] = []
    for eps in eps_values:
        eps = float(eps)
        normal_boundary = ((m < 0.0) & (m >= -eps)).sum()
        abnormal_boundary = ((m >= 0.0) & (m <= eps)).sum()
        rows.append(
            {
                "eps": eps,
                "normal_boundary_n": int(normal_boundary),
                "abnormal_boundary_n": int(abnormal_boundary),
                "boundary_n": int(normal_boundary + abnormal_boundary),
                "boundary_ratio": float((normal_boundary + abnormal_boundary) / len(m)) if len(m) else 0.0,
                "violation_ratio": float((m > 0.0).mean()),
            }
        )
    return rows


def safe_roc_auc(y_true: np.ndarray, score: np.ndarray) -> float | None:
    if len(np.unique(y_true)) < 2:
        return None
    return float(roc_auc_score(y_true, score))


def safe_average_precision(y_true: np.ndarray, score: np.ndarray) -> float | None:
    if int(np.sum(y_true == 1)) == 0:
        return None
    return float(average_precision_score(y_true, score))


def macro_average_precision(y_true: np.ndarray, score: np.ndarray) -> float | None:
    values = [safe_average_precision(y_true[:, idx], score[:, idx]) for idx in range(y_true.shape[1])]
    values = [v for v in values if v is not None]
    return float(np.mean(values)) if values else None


def per_label_metrics(y_true: np.ndarray, pred: np.ndarray, score: np.ndarray) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for idx, label in enumerate(MAIN_LABELS):
        out[label] = {
            "display_name": LABEL_DISPLAY[label],
            "support": int(np.sum(y_true[:, idx] == 1)),
            "precision": float(precision_score(y_true[:, idx], pred[:, idx], zero_division=0)),
            "recall": float(recall_score(y_true[:, idx], pred[:, idx], zero_division=0)),
            "f1": float(f1_score(y_true[:, idx], pred[:, idx], zero_division=0)),
            "average_precision": safe_average_precision(y_true[:, idx], score[:, idx]),
        }
    return out


def run_binary(
    df: pd.DataFrame,
    config: ExperimentConfig,
    *,
    seed: int,
    n_estimators: int,
    n_jobs: int,
) -> tuple[dict[str, Any], pd.DataFrame]:
    base_features = select_feature_columns(df)
    y = df["major_abnormality_label"].astype(int).to_numpy()
    train_idx, val_idx, test_idx, split_name = split_indices(df, config, seed)
    feature_df, feature_cols, diagnostics = enrich_features(df, base_features, train_idx, config)
    model = make_pipeline(SimpleImputer(strategy="median"), build_tree(seed, n_estimators, n_jobs))
    model.fit(feature_df.iloc[train_idx][feature_cols], y[train_idx])

    val_score = binary_positive_proba(model, feature_df.iloc[val_idx][feature_cols])
    threshold, val_f1 = tune_binary_threshold(y[val_idx], val_score)
    test_score = binary_positive_proba(model, feature_df.iloc[test_idx][feature_cols])
    test_pred = (test_score >= threshold).astype(int)
    metrics = {
        "task": "binary",
        "experiment": config.name,
        "split_strategy": split_name,
        "description": config.description,
        "n_features": int(len(feature_cols)),
        "train_rows": int(len(train_idx)),
        "val_rows": int(len(val_idx)),
        "test_rows": int(len(test_idx)),
        "positive_rate_test": float(np.mean(y[test_idx])),
        "threshold": float(threshold),
        "validation_f1_at_threshold": float(val_f1),
        "accuracy": float(accuracy_score(y[test_idx], test_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y[test_idx], test_pred)),
        "precision": float(precision_score(y[test_idx], test_pred, zero_division=0)),
        "recall": float(recall_score(y[test_idx], test_pred, zero_division=0)),
        "f1": float(f1_score(y[test_idx], test_pred, zero_division=0)),
        "roc_auc": safe_roc_auc(y[test_idx], test_score),
        "average_precision": safe_average_precision(y[test_idx], test_score),
        "confusion_matrix": confusion_matrix(y[test_idx], test_pred).tolist(),
        "feature_diagnostics": diagnostics,
    }
    tree = model.named_steps["extratreesclassifier"]
    importance = pd.DataFrame({"feature": feature_cols, "importance": tree.feature_importances_})
    importance.insert(0, "experiment", config.name)
    importance.insert(1, "task", "binary")
    return metrics, importance.sort_values("importance", ascending=False)


def run_multilabel(
    df: pd.DataFrame,
    config: ExperimentConfig,
    *,
    seed: int,
    n_estimators: int,
    n_jobs: int,
) -> tuple[dict[str, Any], pd.DataFrame]:
    base_features = [col for col in select_feature_columns(df) if col in df.columns]
    y = df[MAIN_LABELS].astype(int).to_numpy()
    train_idx, val_idx, test_idx, split_name = split_indices(df, config, seed)
    feature_df, feature_cols, diagnostics = enrich_features(df, base_features, train_idx, config)
    base = make_pipeline(SimpleImputer(strategy="median"), build_tree(seed, n_estimators, n_jobs))
    model = MultiOutputClassifier(base, n_jobs=1)
    model.fit(feature_df.iloc[train_idx][feature_cols], y[train_idx])

    val_score = multioutput_positive_proba(model, feature_df.iloc[val_idx][feature_cols])
    thresholds = tune_multilabel_thresholds(y[val_idx], val_score)
    test_score = multioutput_positive_proba(model, feature_df.iloc[test_idx][feature_cols])
    test_pred = (test_score >= np.asarray(thresholds)[None, :]).astype(int)
    metrics = {
        "task": "multilabel",
        "experiment": config.name,
        "split_strategy": split_name,
        "description": config.description,
        "n_features": int(len(feature_cols)),
        "train_rows": int(len(train_idx)),
        "val_rows": int(len(val_idx)),
        "test_rows": int(len(test_idx)),
        "micro_precision": float(precision_score(y[test_idx], test_pred, average="micro", zero_division=0)),
        "micro_recall": float(recall_score(y[test_idx], test_pred, average="micro", zero_division=0)),
        "micro_f1": float(f1_score(y[test_idx], test_pred, average="micro", zero_division=0)),
        "macro_precision": float(precision_score(y[test_idx], test_pred, average="macro", zero_division=0)),
        "macro_recall": float(recall_score(y[test_idx], test_pred, average="macro", zero_division=0)),
        "macro_f1": float(f1_score(y[test_idx], test_pred, average="macro", zero_division=0)),
        "sample_f1": float(f1_score(y[test_idx], test_pred, average="samples", zero_division=0)),
        "subset_accuracy": float(accuracy_score(y[test_idx], test_pred)),
        "mean_average_precision": macro_average_precision(y[test_idx], test_score),
        "thresholds": {label: float(thresholds[idx]) for idx, label in enumerate(MAIN_LABELS)},
        "per_label": per_label_metrics(y[test_idx], test_pred, test_score),
        "feature_diagnostics": diagnostics,
    }
    importances = [estimator.named_steps["extratreesclassifier"].feature_importances_ for estimator in model.estimators_]
    importance = pd.DataFrame({"feature": feature_cols, "importance": np.vstack(importances).mean(axis=0)})
    importance.insert(0, "experiment", config.name)
    importance.insert(1, "task", "multilabel")
    return metrics, importance.sort_values("importance", ascending=False)


def flatten_results(results: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for item in results:
        rows.append(
            {
                key: value
                for key, value in item.items()
                if key not in {"confusion_matrix", "thresholds", "per_label", "feature_diagnostics", "description"}
            }
        )
    return pd.DataFrame(rows)


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/msyhbd.ttc") if bold else Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def draw_metric_panel(path: Path, summary: pd.DataFrame, task: str, metrics: Sequence[str]) -> None:
    labels = summary[summary["task"] == task]["experiment"].tolist()
    width, height = 1900, 1060
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((60, 42), f"{task} rule-margin / temporal ablation", font=font(42, True), fill=(30, 38, 50))
    draw.text((60, 100), "Compare static baseline, boundary margin, temporal history, and their combination.", font=font(24), fill=(88, 100, 116))
    left, right, top, bottom = 110, 1800, 200, 790
    colors = [(54, 111, 196), (32, 145, 140), (245, 124, 0), (126, 87, 194)]
    for tick in [0.0, 0.25, 0.50, 0.75, 1.0]:
        y = bottom - int((bottom - top) * tick)
        draw.line((left, y, right, y), fill=(222, 228, 236), width=1)
        draw.text((42, y - 12), f"{tick:.2f}", font=font(19), fill=(100, 112, 128))
    data = summary[summary["task"] == task].reset_index(drop=True)
    group_w = (right - left) / max(1, len(data))
    bar_w = min(42, int(group_w / (len(metrics) + 1)))
    for row_idx, row in data.iterrows():
        center = left + int(group_w * row_idx + group_w / 2)
        for metric_idx, metric in enumerate(metrics):
            value = row.get(metric)
            value = 0.0 if value is None or pd.isna(value) else float(value)
            x0 = center - int(len(metrics) * bar_w / 2) + metric_idx * bar_w
            y0 = bottom - int((bottom - top) * max(0.0, min(1.0, value)))
            draw.rounded_rectangle((x0, y0, x0 + bar_w - 7, bottom), radius=5, fill=colors[metric_idx % len(colors)])
        draw.multiline_text(
            (center - 100, bottom + 25),
            str(labels[row_idx]).replace("_", "\n"),
            font=font(17),
            fill=(35, 43, 55),
            align="center",
            spacing=2,
        )
    legend_x, legend_y = 400, 970
    for metric_idx, metric in enumerate(metrics):
        draw.rounded_rectangle((legend_x, legend_y, legend_x + 24, legend_y + 24), radius=4, fill=colors[metric_idx % len(colors)])
        draw.text((legend_x + 34, legend_y - 4), metric, font=font(21), fill=(35, 43, 55))
        legend_x += 270
    img.save(path, quality=95)


def save_figures(summary: pd.DataFrame) -> dict[str, str]:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    figures = {
        "binary_ablation": FIGURE_DIR / "binary_rule_temporal_ablation.png",
        "multilabel_ablation": FIGURE_DIR / "multilabel_rule_temporal_ablation.png",
    }
    draw_metric_panel(figures["binary_ablation"], summary, "binary", ["f1", "roc_auc", "average_precision", "balanced_accuracy"])
    draw_metric_panel(figures["multilabel_ablation"], summary, "multilabel", ["micro_f1", "macro_f1", "mean_average_precision", "sample_f1"])
    return {key: str(value) for key, value in figures.items()}


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n-estimators", type=int, default=50)
    parser.add_argument("--n-jobs", type=int, default=1)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    binary_df = pd.read_csv(BINARY_IN, low_memory=False)
    multilabel_df = pd.read_csv(MULTILABEL_IN, low_memory=False)
    results: list[dict[str, Any]] = []
    importances: list[pd.DataFrame] = []

    for config in CONFIGS:
        binary_metrics, binary_importance = run_binary(
            binary_df,
            config,
            seed=args.seed,
            n_estimators=args.n_estimators,
            n_jobs=args.n_jobs,
        )
        multilabel_metrics, multilabel_importance = run_multilabel(
            multilabel_df,
            config,
            seed=args.seed,
            n_estimators=args.n_estimators,
            n_jobs=args.n_jobs,
        )
        results.extend([binary_metrics, multilabel_metrics])
        importances.extend([binary_importance, multilabel_importance])
        print(f"finished {config.name}")

    summary = flatten_results(results)
    summary_path = OUT_DIR / "rule_temporal_ablation_summary.csv"
    importances_path = OUT_DIR / "rule_temporal_ablation_feature_importance.csv"
    result_path = OUT_DIR / "rule_temporal_ablation_seed42.json"
    boundary_path = OUT_DIR / "rule_margin_boundary_sensitivity.csv"
    figures = save_figures(summary)

    boundary_rows: list[dict[str, Any]] = []
    for item in results:
        diag = item.get("feature_diagnostics", {})
        for row in diag.get("boundary_summary", []):
            boundary_rows.append({"task": item["task"], "experiment": item["experiment"], **row})
    pd.DataFrame(boundary_rows).to_csv(boundary_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    pd.concat(importances, ignore_index=True).to_csv(importances_path, index=False, encoding="utf-8-sig")
    payload = {
        "created_at": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "seed": int(args.seed),
        "n_estimators": int(args.n_estimators),
        "n_jobs": int(args.n_jobs),
        "experiments": [config.__dict__ for config in CONFIGS],
        "results": results,
        "summary_csv": str(summary_path),
        "feature_importance_csv": str(importances_path),
        "boundary_sensitivity_csv": str(boundary_path),
        "figures": figures,
    }
    result_path.write_text(json.dumps(json_sanitize(payload), ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(json_sanitize(payload), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
