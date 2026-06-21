from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

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
OUT_DIR = ROOT / "knowledge_exports" / "major_quality_abnormality_robustness_v1"
FIGURE_DIR = OUT_DIR / "figures"

DERIVED_ALIAS_COLUMNS = {
    "TD_weight_mean",
    "TD_weight_range",
    "TD_avg_temp",
    "cast_speed_mean",
    "cast_speed_range",
    "liquidus_temp",
    "superheat",
    "cover_flux_1",
    "cover_flux_2",
    "cover_flux_total",
    "cover_flux_ratio",
    "cover_flux_zero_flag",
    "mold_level_range",
    "mold_level_mean",
    "mold_level_ge7",
    "mold_level_ge10",
    "tundish_sequence_count",
    "heat_exchange_mean",
    "heat_exchange_ew_diff",
    "heat_exchange_ns_diff",
}

PALETTE = {
    "blue": (54, 111, 196),
    "teal": (32, 145, 140),
    "orange": (245, 124, 0),
    "purple": (126, 87, 194),
    "red": (211, 47, 47),
    "green": (67, 160, 71),
    "gray": (100, 112, 128),
    "light": (235, 239, 245),
    "grid": (220, 226, 235),
    "text": (35, 43, 55),
    "muted": (98, 110, 126),
    "bg": (255, 255, 255),
}


@dataclass(frozen=True)
class ExperimentConfig:
    name: str
    split: str
    feature_policy: str
    description: str


CONFIGS = [
    ExperimentConfig(
        name="group_all_features",
        split="group",
        feature_policy="all_process_features",
        description="Group split with all non-leakage process features.",
    ),
    ExperimentConfig(
        name="time_all_features",
        split="time_holdout",
        feature_policy="all_process_features",
        description="Chronological holdout: Jan-Aug train, Sep-Oct validation, Nov-Dec test.",
    ),
    ExperimentConfig(
        name="group_no_derived_alias",
        split="group",
        feature_policy="no_derived_alias",
        description="Group split after removing English derived alias features.",
    ),
    ExperimentConfig(
        name="time_no_derived_alias",
        split="time_holdout",
        feature_policy="no_derived_alias",
        description="Chronological holdout after removing English derived alias features.",
    ),
]


def font(size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/msyhbd.ttc") if bold else Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def safe_float(value: Any) -> float | None:
    try:
        out = float(value)
    except Exception:
        return None
    if not np.isfinite(out):
        return None
    return out


def safe_roc_auc(y_true: np.ndarray, score: np.ndarray) -> float | None:
    if len(np.unique(y_true)) < 2:
        return None
    return float(roc_auc_score(y_true, score))


def safe_average_precision(y_true: np.ndarray, score: np.ndarray) -> float | None:
    if int(np.sum(y_true == 1)) == 0:
        return None
    return float(average_precision_score(y_true, score))


def select_features(df: pd.DataFrame, policy: str) -> list[str]:
    features = select_feature_columns(df)
    if policy == "all_process_features":
        return features
    if policy == "no_derived_alias":
        return [col for col in features if col not in DERIVED_ALIAS_COLUMNS]
    raise ValueError(f"Unknown feature policy: {policy}")


def group_split_indices(df: pd.DataFrame, *, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    idx = np.arange(len(df))
    group_col = "process_sequence_key"
    if group_col not in df.columns or df[group_col].nunique(dropna=False) < 5:
        return ordered_fraction_split(df, split_name="ordered_fallback")
    groups = df[group_col].astype(str).fillna("group_unknown").to_numpy()
    train_split = GroupShuffleSplit(n_splits=1, test_size=0.40, random_state=seed)
    train_idx, temp_idx = next(train_split.split(idx, groups=groups))
    temp_groups = groups[temp_idx]
    val_test_split = GroupShuffleSplit(n_splits=1, test_size=0.50, random_state=seed + 1)
    val_rel, test_rel = next(val_test_split.split(temp_idx, groups=temp_groups))
    return train_idx, temp_idx[val_rel], temp_idx[test_rel], "group:process_sequence_key"


def ordered_fraction_split(df: pd.DataFrame, *, split_name: str = "ordered_60_20_20") -> tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    order = np.arange(len(df))
    n = len(order)
    train_end = int(n * 0.60)
    val_end = int(n * 0.80)
    return order[:train_end], order[train_end:val_end], order[val_end:], split_name


def time_holdout_split_indices(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    if "process_time" not in df.columns:
        return ordered_fraction_split(df, split_name="ordered_60_20_20_no_time")
    time = pd.to_datetime(df["process_time"], errors="coerce")
    order = np.argsort(time.fillna(pd.Timestamp.max).to_numpy())
    sorted_time = time.iloc[order]
    train_mask = sorted_time < pd.Timestamp("2022-09-01")
    val_mask = (sorted_time >= pd.Timestamp("2022-09-01")) & (sorted_time < pd.Timestamp("2022-11-01"))
    test_mask = sorted_time >= pd.Timestamp("2022-11-01")
    train_idx = order[np.asarray(train_mask)]
    val_idx = order[np.asarray(val_mask)]
    test_idx = order[np.asarray(test_mask)]
    if min(len(train_idx), len(val_idx), len(test_idx)) < 100:
        sorted_df = df.iloc[order].reset_index(drop=False)
        train_rel, val_rel, test_rel, name = ordered_fraction_split(sorted_df, split_name="ordered_60_20_20_time_fallback")
        original_idx = sorted_df["index"].to_numpy()
        return original_idx[train_rel], original_idx[val_rel], original_idx[test_rel], name
    return train_idx, val_idx, test_idx, "time_holdout:train_2022-01_08,val_09_10,test_11_12"


def split_indices(df: pd.DataFrame, config: ExperimentConfig, *, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    if config.split == "group":
        return group_split_indices(df, seed=seed)
    if config.split == "time_holdout":
        return time_holdout_split_indices(df)
    raise ValueError(f"Unknown split: {config.split}")


def run_binary(
    df: pd.DataFrame,
    config: ExperimentConfig,
    *,
    seed: int,
    n_estimators: int,
    n_jobs: int,
) -> tuple[dict[str, Any], pd.DataFrame]:
    feature_cols = select_features(df, config.feature_policy)
    y = df["major_abnormality_label"].astype(int).to_numpy()
    train_idx, val_idx, test_idx, split_name = split_indices(df, config, seed=seed)
    model = make_pipeline(SimpleImputer(strategy="median"), build_tree(seed, n_estimators, n_jobs))
    model.fit(df.iloc[train_idx][feature_cols], y[train_idx])

    val_score = binary_positive_proba(model, df.iloc[val_idx][feature_cols])
    threshold, val_f1 = tune_binary_threshold(y[val_idx], val_score)
    test_score = binary_positive_proba(model, df.iloc[test_idx][feature_cols])
    test_pred = (test_score >= threshold).astype(int)
    metrics = {
        "task": "binary",
        "experiment": config.name,
        "split_strategy": split_name,
        "feature_policy": config.feature_policy,
        "description": config.description,
        "n_features": int(len(feature_cols)),
        "train_rows": int(len(train_idx)),
        "val_rows": int(len(val_idx)),
        "test_rows": int(len(test_idx)),
        "positive_rate_train": float(np.mean(y[train_idx])),
        "positive_rate_val": float(np.mean(y[val_idx])),
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
    }
    tree = model.named_steps["extratreesclassifier"]
    importance = pd.DataFrame({"feature": feature_cols, "importance": tree.feature_importances_})
    importance.insert(0, "experiment", config.name)
    importance.insert(1, "task", "binary")
    return metrics, importance.sort_values("importance", ascending=False)


def per_label_metrics(y_true: np.ndarray, pred: np.ndarray, score: np.ndarray) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for idx, label in enumerate(MAIN_LABELS):
        yt = y_true[:, idx]
        yp = pred[:, idx]
        out[label] = {
            "display_name": LABEL_DISPLAY[label],
            "support": int(np.sum(yt == 1)),
            "positive_rate_test": float(np.mean(yt)),
            "precision": float(precision_score(yt, yp, zero_division=0)),
            "recall": float(recall_score(yt, yp, zero_division=0)),
            "f1": float(f1_score(yt, yp, zero_division=0)),
            "average_precision": safe_average_precision(yt, score[:, idx]),
        }
    return out


def macro_average_precision_from_labels(y_true: np.ndarray, score: np.ndarray) -> float | None:
    values = [safe_average_precision(y_true[:, idx], score[:, idx]) for idx in range(y_true.shape[1])]
    finite = [v for v in values if v is not None]
    return float(np.mean(finite)) if finite else None


def run_multilabel(
    df: pd.DataFrame,
    config: ExperimentConfig,
    *,
    seed: int,
    n_estimators: int,
    n_jobs: int,
) -> tuple[dict[str, Any], pd.DataFrame]:
    feature_cols = [col for col in select_features(df, config.feature_policy) if col in df.columns]
    y = df[MAIN_LABELS].astype(int).to_numpy()
    train_idx, val_idx, test_idx, split_name = split_indices(df, config, seed=seed)
    base = make_pipeline(SimpleImputer(strategy="median"), build_tree(seed, n_estimators, n_jobs))
    model = MultiOutputClassifier(base, n_jobs=1)
    model.fit(df.iloc[train_idx][feature_cols], y[train_idx])

    val_score = multioutput_positive_proba(model, df.iloc[val_idx][feature_cols])
    thresholds = tune_multilabel_thresholds(y[val_idx], val_score)
    test_score = multioutput_positive_proba(model, df.iloc[test_idx][feature_cols])
    test_pred = (test_score >= np.asarray(thresholds)[None, :]).astype(int)

    metrics = {
        "task": "multilabel",
        "experiment": config.name,
        "split_strategy": split_name,
        "feature_policy": config.feature_policy,
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
        "mean_average_precision": macro_average_precision_from_labels(y[test_idx], test_score),
        "thresholds": {label: float(thresholds[idx]) for idx, label in enumerate(MAIN_LABELS)},
        "per_label": per_label_metrics(y[test_idx], test_pred, test_score),
    }
    importances = []
    for estimator in model.estimators_:
        importances.append(estimator.named_steps["extratreesclassifier"].feature_importances_)
    importance_arr = np.vstack(importances)
    importance = pd.DataFrame({"feature": feature_cols, "importance": importance_arr.mean(axis=0)})
    importance.insert(0, "experiment", config.name)
    importance.insert(1, "task", "multilabel")
    return metrics, importance.sort_values("importance", ascending=False)


def draw_text_fit(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font_obj: ImageFont.ImageFont,
    *,
    max_width: int,
    fill: tuple[int, int, int] = PALETTE["text"],
) -> None:
    if draw.textlength(text, font=font_obj) <= max_width:
        draw.text(xy, text, font=font_obj, fill=fill)
        return
    clipped = text
    while clipped and draw.textlength(clipped + "...", font=font_obj) > max_width:
        clipped = clipped[:-1]
    draw.text(xy, clipped + "...", font=font_obj, fill=fill)


def canvas(title: str, subtitle: str, *, width: int = 1600, height: int = 950) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (width, height), PALETTE["bg"])
    draw = ImageDraw.Draw(img)
    draw.text((62, 42), title, font=font(42, bold=True), fill=PALETTE["text"])
    draw.text((62, 98), subtitle, font=font(24), fill=PALETTE["muted"])
    draw.line((62, 142, width - 62, 142), fill=PALETTE["grid"], width=2)
    return img, draw


def save_metric_comparison(
    path: Path,
    title: str,
    subtitle: str,
    summary: pd.DataFrame,
    *,
    task: str,
    metrics: list[str],
) -> None:
    fig, draw = canvas(title, subtitle, width=1720, height=980)
    data = summary[summary["task"] == task].copy()
    left = 120
    right = 1640
    top = 210
    bottom = 760
    chart_w = right - left
    chart_h = bottom - top
    exp_names = data["experiment"].tolist()
    colors = [PALETTE["blue"], PALETTE["teal"], PALETTE["orange"], PALETTE["purple"]]
    for tick in [0.0, 0.25, 0.50, 0.75, 1.0]:
        y = bottom - int(chart_h * tick)
        draw.line((left, y, right, y), fill=PALETTE["grid"], width=1)
        draw.text((58, y - 12), f"{tick:.2f}", font=font(20), fill=PALETTE["muted"])
    group_w = chart_w / max(1, len(exp_names))
    bar_w = min(54, int(group_w / (len(metrics) + 1)))
    for exp_idx, exp in enumerate(exp_names):
        center = left + int(group_w * exp_idx + group_w / 2)
        for metric_idx, metric in enumerate(metrics):
            value = safe_float(data.iloc[exp_idx][metric]) or 0.0
            x0 = center - int(len(metrics) * bar_w / 2) + metric_idx * bar_w
            y0 = bottom - int(chart_h * value)
            draw.rounded_rectangle((x0, y0, x0 + bar_w - 8, bottom), radius=6, fill=colors[metric_idx % len(colors)])
        label = exp.replace("_", "\n")
        draw.multiline_text((center - 95, bottom + 26), label, font=font(18), fill=PALETTE["text"], align="center", spacing=2)
    legend_x = 390
    legend_y = 875
    for metric_idx, metric in enumerate(metrics):
        draw.rounded_rectangle((legend_x, legend_y, legend_x + 26, legend_y + 26), radius=5, fill=colors[metric_idx % len(colors)])
        draw.text((legend_x + 38, legend_y - 3), metric, font=font(22), fill=PALETTE["text"])
        legend_x += 250
    fig.save(path, quality=95)


def save_generalization_drop(path: Path, summary: pd.DataFrame) -> None:
    fig, draw = canvas("泛化差距与特征去重消融", "以 group_all_features 为参照，展示严格验证下的指标变化", width=1650, height=920)
    baseline = summary[(summary["task"] == "binary") & (summary["experiment"] == "group_all_features")]["f1"].iloc[0]
    rows = summary[summary["task"] == "binary"].copy()
    rows["f1_drop"] = baseline - rows["f1"]
    labels = rows["experiment"].tolist()
    values = rows["f1_drop"].tolist()
    left_label = 90
    left_bar = 560
    right = 1430
    top = 210
    row_gap = 95
    max_v = max(max(values), 0.01) * 1.15
    for idx, (label, value) in enumerate(zip(labels, values)):
        y = top + idx * row_gap
        draw_text_fit(draw, (left_label, y), label, font(24), max_width=430)
        draw.rounded_rectangle((left_bar, y, right, y + 38), radius=10, fill=PALETTE["light"])
        bar_w = int((right - left_bar) * value / max_v) if max_v else 0
        color = PALETTE["green"] if value <= 0.03 else PALETTE["orange"] if value <= 0.10 else PALETTE["red"]
        draw.rounded_rectangle((left_bar, y, left_bar + bar_w, y + 38), radius=10, fill=color)
        draw.text((right + 20, y - 2), f"{value:.3f}", font=font(24, bold=True), fill=PALETTE["text"])
    draw.text((90, 795), "注：数值越小越好。时间外推下降越小，说明模型越不依赖随机切分下的分布相似性。", font=font(22), fill=PALETTE["muted"])
    fig.save(path, quality=95)


def save_figures(summary: pd.DataFrame) -> dict[str, str]:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    figures = {
        "binary_metrics": FIGURE_DIR / "robustness_binary_metrics.png",
        "multilabel_metrics": FIGURE_DIR / "robustness_multilabel_metrics.png",
        "generalization_drop": FIGURE_DIR / "robustness_generalization_drop.png",
    }
    save_metric_comparison(
        figures["binary_metrics"],
        "主要异常二分类鲁棒性实验",
        "Group split、时间外推与去重复派生特征消融对比",
        summary,
        task="binary",
        metrics=["f1", "roc_auc", "average_precision", "balanced_accuracy"],
    )
    save_metric_comparison(
        figures["multilabel_metrics"],
        "五类主要异常多标签鲁棒性实验",
        "Group split、时间外推与去重复派生特征消融对比",
        summary,
        task="multilabel",
        metrics=["micro_f1", "macro_f1", "mean_average_precision", "sample_f1"],
    )
    save_generalization_drop(figures["generalization_drop"], summary)
    return {name: str(path) for name, path in figures.items()}


def flatten_summary(results: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for item in results:
        row = {
            key: value
            for key, value in item.items()
            if key
            not in {
                "per_label",
                "thresholds",
                "confusion_matrix",
                "description",
            }
        }
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    binary_df = pd.read_csv(BINARY_IN, low_memory=False)
    multilabel_df = pd.read_csv(MULTILABEL_IN, low_memory=False)
    results: list[dict[str, Any]] = []
    importances: list[pd.DataFrame] = []
    seed = 42
    n_estimators = 60
    n_jobs = 1

    for config in CONFIGS:
        binary_metrics, binary_importance = run_binary(
            binary_df,
            config,
            seed=seed,
            n_estimators=n_estimators,
            n_jobs=n_jobs,
        )
        multilabel_metrics, multilabel_importance = run_multilabel(
            multilabel_df,
            config,
            seed=seed,
            n_estimators=n_estimators,
            n_jobs=n_jobs,
        )
        results.extend([binary_metrics, multilabel_metrics])
        importances.extend([binary_importance, multilabel_importance])
        print(f"finished {config.name}")

    summary = flatten_summary(results)
    summary_path = OUT_DIR / "robustness_summary.csv"
    importances_path = OUT_DIR / "robustness_feature_importance.csv"
    result_path = OUT_DIR / "robustness_experiments_seed42.json"
    figures = save_figures(summary)
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    pd.concat(importances, ignore_index=True).to_csv(importances_path, index=False, encoding="utf-8-sig")
    payload = {
        "created_at": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "seed": seed,
        "n_estimators": n_estimators,
        "n_jobs": n_jobs,
        "experiments": [config.__dict__ for config in CONFIGS],
        "results": results,
        "summary_csv": str(summary_path),
        "feature_importance_csv": str(importances_path),
        "figures": figures,
    }
    result_path.write_text(json.dumps(json_sanitize(payload), ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(json_sanitize(payload), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
