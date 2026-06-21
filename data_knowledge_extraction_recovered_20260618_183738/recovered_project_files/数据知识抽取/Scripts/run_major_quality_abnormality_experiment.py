from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.multioutput import MultiOutputClassifier
from sklearn.pipeline import make_pipeline


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "knowledge_exports" / "major_quality_abnormality_v1"
BINARY_IN = DATA_DIR / "xy_major_abnormality_with_clean_negative.csv"
MULTILABEL_IN = DATA_DIR / "xy_major_abnormality_multilabel.csv"
OUT_DIR = ROOT / "knowledge_exports" / "major_quality_abnormality_experiment_v1"

MAIN_LABELS = [
    "label_major_mold_level_slag_quality",
    "label_major_temperature_flux_quality",
    "label_major_heat_transfer_quality",
    "label_major_flow_control_anomaly",
    "label_major_process_parameter_anomaly",
]

LABEL_DISPLAY = {
    "label_major_mold_level_slag_quality": "液面/卷渣质量类",
    "label_major_temperature_flux_quality": "温度/保护剂质量类",
    "label_major_heat_transfer_quality": "传热不均质量类",
    "label_major_flow_control_anomaly": "拉速-塞棒/流量控制异常类",
    "label_major_process_parameter_anomaly": "过程参数异常类",
}

EXACT_EXCLUDE_COLUMNS = {
    "record_id",
    "source_row_id",
    "连铸处理号",
    "材料跟踪号",
    "记录识别码",
    "process_time",
    "process_sequence_key",
}

EXCLUDE_SUBSTRINGS = [
    "label",
    "quality",
    "defect",
    "reason",
    "steel_change",
    "disposition",
    "code",
    "class",
    "context",
    "major",
    "sample_role",
    "evidence",
    "group",
]


def json_sanitize(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {str(k): json_sanitize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_sanitize(v) for v in value]
    return str(value)


def is_feature_column(column: str, series: pd.Series) -> bool:
    if column in EXACT_EXCLUDE_COLUMNS:
        return False
    lower = column.lower()
    if any(token in lower for token in EXCLUDE_SUBSTRINGS):
        return False
    return pd.api.types.is_numeric_dtype(series)


def select_feature_columns(df: pd.DataFrame) -> list[str]:
    features = [col for col in df.columns if is_feature_column(str(col), df[col])]
    if not features:
        raise ValueError("No numeric process feature columns were selected.")
    return features


def split_indices(
    df: pd.DataFrame,
    y: Sequence[Any] | np.ndarray,
    *,
    group_col: str = "process_sequence_key",
    random_state: int = 42,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    idx = np.arange(len(df))
    if group_col in df.columns and df[group_col].nunique(dropna=False) >= 5:
        groups = df[group_col].astype(str).fillna("group_unknown").to_numpy()
        train_split = GroupShuffleSplit(n_splits=1, test_size=0.40, random_state=random_state)
        train_idx, temp_idx = next(train_split.split(idx, groups=groups))
        temp_groups = groups[temp_idx]
        val_test_split = GroupShuffleSplit(n_splits=1, test_size=0.50, random_state=random_state + 1)
        val_rel, test_rel = next(val_test_split.split(temp_idx, groups=temp_groups))
        return train_idx, temp_idx[val_rel], temp_idx[test_rel], f"group:{group_col}"

    y_arr = np.asarray(y)
    train_idx, temp_idx = train_test_split(
        idx,
        test_size=0.40,
        random_state=random_state,
        stratify=y_arr if y_arr.ndim == 1 and len(np.unique(y_arr)) > 1 else None,
    )
    val_idx, test_idx = train_test_split(
        temp_idx,
        test_size=0.50,
        random_state=random_state + 1,
        stratify=y_arr[temp_idx] if y_arr.ndim == 1 and len(np.unique(y_arr[temp_idx])) > 1 else None,
    )
    return train_idx, val_idx, test_idx, "random_stratified"


def build_tree(seed: int, n_estimators: int) -> ExtraTreesClassifier:
    return ExtraTreesClassifier(
        n_estimators=int(n_estimators),
        random_state=int(seed),
        n_jobs=-1,
        class_weight="balanced",
        min_samples_leaf=2,
        max_features="sqrt",
    )


def tune_binary_threshold(y_true: np.ndarray, scores: np.ndarray) -> tuple[float, float]:
    best_threshold = 0.5
    best_f1 = -1.0
    for threshold in np.linspace(0.10, 0.90, 81):
        pred = (scores >= threshold).astype(int)
        score = f1_score(y_true, pred, zero_division=0)
        if score > best_f1:
            best_f1 = float(score)
            best_threshold = float(threshold)
    return best_threshold, best_f1


def binary_positive_proba(model: Any, x: pd.DataFrame) -> np.ndarray:
    classes = np.asarray(model.named_steps["extratreesclassifier"].classes_, dtype=int)
    proba = model.predict_proba(x)
    positive_col = int(np.where(classes == 1)[0][0]) if 1 in classes else proba.shape[1] - 1
    return np.asarray(proba[:, positive_col], dtype=float)


def run_binary(
    df: pd.DataFrame,
    *,
    feature_cols: list[str],
    seed: int,
    n_estimators: int,
) -> tuple[dict[str, Any], pd.DataFrame]:
    y = df["major_abnormality_label"].astype(int).to_numpy()
    train_idx, val_idx, test_idx, split_strategy = split_indices(df, y, random_state=seed)
    model = make_pipeline(SimpleImputer(strategy="median"), build_tree(seed, n_estimators))
    model.fit(df.iloc[train_idx][feature_cols], y[train_idx])

    val_scores = binary_positive_proba(model, df.iloc[val_idx][feature_cols])
    threshold, val_f1 = tune_binary_threshold(y[val_idx], val_scores)
    test_scores = binary_positive_proba(model, df.iloc[test_idx][feature_cols])
    test_pred = (test_scores >= threshold).astype(int)

    metrics = {
        "task": "major_abnormality_binary",
        "split_strategy": split_strategy,
        "n_rows": int(len(df)),
        "n_features": int(len(feature_cols)),
        "train_rows": int(len(train_idx)),
        "val_rows": int(len(val_idx)),
        "test_rows": int(len(test_idx)),
        "positive_rate_all": float(np.mean(y)),
        "positive_rate_test": float(np.mean(y[test_idx])),
        "threshold": threshold,
        "validation_f1_at_threshold": val_f1,
        "accuracy": float(accuracy_score(y[test_idx], test_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y[test_idx], test_pred)),
        "precision": float(precision_score(y[test_idx], test_pred, zero_division=0)),
        "recall": float(recall_score(y[test_idx], test_pred, zero_division=0)),
        "f1": float(f1_score(y[test_idx], test_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y[test_idx], test_scores)),
        "average_precision": float(average_precision_score(y[test_idx], test_scores)),
        "confusion_matrix": confusion_matrix(y[test_idx], test_pred).tolist(),
    }

    tree = model.named_steps["extratreesclassifier"]
    importance = pd.DataFrame(
        {
            "feature": feature_cols,
            "binary_importance": tree.feature_importances_,
        }
    ).sort_values("binary_importance", ascending=False)
    return metrics, importance


def multioutput_positive_proba(model: MultiOutputClassifier, x: pd.DataFrame) -> np.ndarray:
    columns: list[np.ndarray] = []
    for estimator in model.estimators_:
        tree = estimator.named_steps["extratreesclassifier"]
        classes = np.asarray(tree.classes_, dtype=int)
        proba = estimator.predict_proba(x)
        if 1 in classes:
            positive_col = int(np.where(classes == 1)[0][0])
            columns.append(np.asarray(proba[:, positive_col], dtype=float))
        else:
            columns.append(np.zeros(len(x), dtype=float))
    return np.vstack(columns).T


def tune_multilabel_thresholds(y_true: np.ndarray, scores: np.ndarray) -> list[float]:
    thresholds: list[float] = []
    for col in range(y_true.shape[1]):
        threshold, _ = tune_binary_threshold(y_true[:, col], scores[:, col])
        thresholds.append(threshold)
    return thresholds


def run_multilabel(
    df: pd.DataFrame,
    *,
    feature_cols: list[str],
    seed: int,
    n_estimators: int,
) -> tuple[dict[str, Any], pd.DataFrame]:
    y = df[MAIN_LABELS].astype(int).to_numpy()
    primary = df["major_primary_class_id"].astype(int).to_numpy() if "major_primary_class_id" in df.columns else y.argmax(axis=1)
    train_idx, val_idx, test_idx, split_strategy = split_indices(df, primary, random_state=seed)

    base = make_pipeline(SimpleImputer(strategy="median"), build_tree(seed, n_estimators))
    model = MultiOutputClassifier(base, n_jobs=-1)
    model.fit(df.iloc[train_idx][feature_cols], y[train_idx])

    val_scores = multioutput_positive_proba(model, df.iloc[val_idx][feature_cols])
    thresholds = tune_multilabel_thresholds(y[val_idx], val_scores)
    test_scores = multioutput_positive_proba(model, df.iloc[test_idx][feature_cols])
    test_pred = (test_scores >= np.asarray(thresholds)[None, :]).astype(int)

    per_label: dict[str, Any] = {}
    for idx, label in enumerate(MAIN_LABELS):
        precision, recall, f1, support = precision_recall_fscore_support(
            y[test_idx][:, idx],
            test_pred[:, idx],
            average="binary",
            zero_division=0,
        )
        try:
            ap = average_precision_score(y[test_idx][:, idx], test_scores[:, idx])
        except ValueError:
            ap = float("nan")
        per_label[label] = {
            "display_name": LABEL_DISPLAY[label],
            "threshold": float(thresholds[idx]),
            "support": int(support),
            "positive_rate_test": float(np.mean(y[test_idx][:, idx])),
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
            "average_precision": float(ap),
        }

    metrics = {
        "task": "major_abnormality_multilabel",
        "split_strategy": split_strategy,
        "n_rows": int(len(df)),
        "n_features": int(len(feature_cols)),
        "train_rows": int(len(train_idx)),
        "val_rows": int(len(val_idx)),
        "test_rows": int(len(test_idx)),
        "thresholds": {label: float(thresholds[idx]) for idx, label in enumerate(MAIN_LABELS)},
        "micro_precision": float(precision_score(y[test_idx], test_pred, average="micro", zero_division=0)),
        "micro_recall": float(recall_score(y[test_idx], test_pred, average="micro", zero_division=0)),
        "micro_f1": float(f1_score(y[test_idx], test_pred, average="micro", zero_division=0)),
        "macro_precision": float(precision_score(y[test_idx], test_pred, average="macro", zero_division=0)),
        "macro_recall": float(recall_score(y[test_idx], test_pred, average="macro", zero_division=0)),
        "macro_f1": float(f1_score(y[test_idx], test_pred, average="macro", zero_division=0)),
        "sample_f1": float(f1_score(y[test_idx], test_pred, average="samples", zero_division=0)),
        "subset_accuracy": float(accuracy_score(y[test_idx], test_pred)),
        "mean_average_precision": float(average_precision_score(y[test_idx], test_scores, average="macro")),
        "per_label": per_label,
    }

    importances = []
    for label, estimator in zip(MAIN_LABELS, model.estimators_):
        tree = estimator.named_steps["extratreesclassifier"]
        importances.append(tree.feature_importances_)
    importance_arr = np.vstack(importances)
    importance = pd.DataFrame({"feature": feature_cols, "multilabel_mean_importance": importance_arr.mean(axis=0)})
    for label, values in zip(MAIN_LABELS, importance_arr):
        importance[label] = values
    importance = importance.sort_values("multilabel_mean_importance", ascending=False)
    return metrics, importance


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n-estimators", type=int, default=160)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    binary_df = pd.read_csv(BINARY_IN, low_memory=False)
    multilabel_df = pd.read_csv(MULTILABEL_IN, low_memory=False)
    feature_cols = select_feature_columns(binary_df)
    multilabel_feature_cols = [col for col in feature_cols if col in multilabel_df.columns]

    binary_metrics, binary_importance = run_binary(
        binary_df,
        feature_cols=feature_cols,
        seed=args.seed,
        n_estimators=args.n_estimators,
    )
    multilabel_metrics, multilabel_importance = run_multilabel(
        multilabel_df,
        feature_cols=multilabel_feature_cols,
        seed=args.seed,
        n_estimators=args.n_estimators,
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result = {
        "created_at": timestamp,
        "data_dir": str(DATA_DIR),
        "model": {
            "family": "ExtraTreesClassifier",
            "n_estimators": int(args.n_estimators),
            "seed": int(args.seed),
            "imputation": "median",
            "feature_policy": "numeric process features only; labels, quality codes, reason/disposition fields and identifiers excluded",
        },
        "feature_columns": feature_cols,
        "binary": binary_metrics,
        "multilabel": multilabel_metrics,
    }

    result_path = OUT_DIR / f"major_quality_abnormality_experiment_seed{args.seed}.json"
    binary_imp_path = OUT_DIR / f"binary_feature_importance_seed{args.seed}.csv"
    multilabel_imp_path = OUT_DIR / f"multilabel_feature_importance_seed{args.seed}.csv"
    result_path.write_text(json.dumps(json_sanitize(result), ensure_ascii=False, indent=2), encoding="utf-8")
    binary_importance.to_csv(binary_imp_path, index=False, encoding="utf-8-sig")
    multilabel_importance.to_csv(multilabel_imp_path, index=False, encoding="utf-8-sig")

    print(json.dumps(json_sanitize(result), ensure_ascii=False, indent=2))
    print(f"result_path={result_path}")
    print(f"binary_feature_importance={binary_imp_path}")
    print(f"multilabel_feature_importance={multilabel_imp_path}")


if __name__ == "__main__":
    main()
