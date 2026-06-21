"""Train quality traceability models with imbalance, drift, coupling and multi-label handling."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    hamming_loss,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier, export_text


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASET_DIR = PROJECT_ROOT / "knowledge_exports" / "quality_traceability_dataset_quality_code"
DEFAULT_INPUT = DEFAULT_DATASET_DIR / "xy_quality_traceability.csv"
DEFAULT_FEATURE_GROUPS = DEFAULT_DATASET_DIR / "feature_groups.json"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "knowledge_exports" / "quality_modeling_quality_code"

TIME_COL = "process_time"
LABEL_COL = "quality_multiclass_name"
NO_ABNORMAL_LABEL = "无品质异常"
MULTILABEL_COLS = [
    "quality_group_mold_level_slag_risk",
    "quality_group_process_fluctuation",
    "quality_group_speed_stopper_flow",
    "quality_group_heat_transfer_imbalance",
    "quality_group_temperature_flux",
]
MULTILABEL_CN = {
    "quality_group_mold_level_slag_risk": "液面波动/卷渣风险异常",
    "quality_group_process_fluctuation": "过程参数波动异常",
    "quality_group_speed_stopper_flow": "拉速/塞棒/流量控制异常",
    "quality_group_heat_transfer_imbalance": "结晶器传热不均异常",
    "quality_group_temperature_flux": "温度/保护渣质量异常",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, payload: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def feature_group_map(feature_groups: dict[str, list[str]]) -> dict[str, str]:
    out: dict[str, str] = {}
    for group, cols in feature_groups.items():
        for col in cols:
            out[col] = group
    return out


def make_time_split(
    df: pd.DataFrame,
    *,
    train_end: str,
    val_end: str,
) -> pd.Series:
    month = df[TIME_COL].dt.to_period("M").astype(str)
    split = pd.Series("test", index=df.index, dtype="object")
    split.loc[month <= train_end] = "train"
    split.loc[(month > train_end) & (month <= val_end)] = "val"
    split.loc[month > val_end] = "test"
    return split


def remove_highly_correlated_features(
    x_train: pd.DataFrame,
    feature_to_group: dict[str, str],
    threshold: float,
) -> tuple[list[str], list[dict[str, Any]]]:
    if threshold <= 0 or threshold >= 1:
        return list(x_train.columns), []

    corr = x_train.corr(numeric_only=True).abs()
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
    dropped: set[str] = set()
    drop_records: list[dict[str, Any]] = []
    for col in upper.columns:
        if col in dropped:
            continue
        matches = upper.index[upper[col] >= threshold].tolist()
        for other in matches:
            if other in dropped:
                continue
            col_group = feature_to_group.get(col, "")
            other_group = feature_to_group.get(other, "")
            drop_col = col if col_group == "derived_process" and other_group != "derived_process" else other
            keep_col = other if drop_col == col else col
            dropped.add(drop_col)
            drop_records.append(
                {
                    "dropped_feature": drop_col,
                    "kept_feature": keep_col,
                    "abs_correlation": float(upper.loc[other, col]),
                    "dropped_group": feature_to_group.get(drop_col, ""),
                    "kept_group": feature_to_group.get(keep_col, ""),
                }
            )
    kept = [c for c in x_train.columns if c not in dropped]
    return kept, drop_records


def split_summary(df: pd.DataFrame, split: pd.Series) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for name in ["train", "val", "test"]:
        part = df.loc[split.eq(name)]
        if part.empty:
            continue
        row: dict[str, Any] = {
            "split": name,
            "rows": int(len(part)),
            "time_min": str(part[TIME_COL].min()),
            "time_max": str(part[TIME_COL].max()),
            "abnormal_rate": float(part[LABEL_COL].ne(NO_ABNORMAL_LABEL).mean()),
        }
        counts = part[LABEL_COL].value_counts()
        for label, count in counts.items():
            row[f"label__{label}"] = int(count)
        rows.append(row)
    return pd.DataFrame(rows)


def report_to_frame(report: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for label, metrics in report.items():
        if isinstance(metrics, dict):
            row = {"label": label}
            row.update(metrics)
            rows.append(row)
    return pd.DataFrame(rows)


def binary_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray | None) -> dict[str, Any]:
    report = classification_report(
        y_true,
        y_pred,
        target_names=["正常", "异常"],
        output_dict=True,
        zero_division=0,
    )
    out: dict[str, Any] = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "classification_report": report,
    }
    if y_prob is not None:
        out["roc_auc"] = float(roc_auc_score(y_true, y_prob))
        out["pr_auc"] = float(average_precision_score(y_true, y_prob))
    return out


def multiclass_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    labels: list[str],
) -> dict[str, Any]:
    report = classification_report(
        y_true,
        y_pred,
        labels=np.arange(len(labels)),
        target_names=labels,
        output_dict=True,
        zero_division=0,
    )
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "classification_report": report,
    }


def module_importance(
    feature_importance: pd.DataFrame,
    feature_to_group: dict[str, str],
) -> pd.DataFrame:
    out = feature_importance.copy()
    out["feature_group"] = out["feature"].map(feature_to_group).fillna("unknown")
    grouped = (
        out.groupby("feature_group", as_index=False)["importance"]
        .sum()
        .sort_values("importance", ascending=False)
    )
    total = grouped["importance"].sum()
    grouped["importance_share"] = grouped["importance"] / total if total else 0.0
    return grouped


def logistic_by_class_importance(
    pipeline: Pipeline,
    labels: list[str],
    feature_names: list[str],
    top_n: int,
) -> pd.DataFrame:
    clf = pipeline.named_steps["clf"]
    coef = np.asarray(clf.coef_)
    rows: list[dict[str, Any]] = []
    for class_idx, label in enumerate(labels):
        values = coef[class_idx]
        order = np.argsort(np.abs(values))[::-1][:top_n]
        for rank, idx in enumerate(order, start=1):
            rows.append(
                {
                    "label": label,
                    "rank": rank,
                    "feature": feature_names[idx],
                    "coef": float(values[idx]),
                    "abs_coef": float(abs(values[idx])),
                    "direction": "positive" if values[idx] >= 0 else "negative",
                }
            )
    return pd.DataFrame(rows)


def train_rules(
    x_train: pd.DataFrame,
    y_train: pd.Series,
    labels: list[str],
    output_path: Path,
    max_depth: int,
) -> dict[str, str]:
    rules: dict[str, str] = {}
    for label in labels:
        target = y_train.eq(label).astype(int)
        if target.nunique() < 2:
            continue
        tree = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "clf",
                    DecisionTreeClassifier(
                        max_depth=max_depth,
                        min_samples_leaf=80,
                        class_weight="balanced",
                        random_state=42,
                    ),
                ),
            ]
        )
        tree.fit(x_train, target)
        clf = tree.named_steps["clf"]
        rules[label] = export_text(clf, feature_names=list(x_train.columns), max_depth=max_depth)
    save_json(output_path, rules)
    return rules


def write_markdown_summary(
    path: Path,
    *,
    split_df: pd.DataFrame,
    binary_test: dict[str, Any],
    multiclass_test: dict[str, Any],
    multilabel_metrics_payload: dict[str, Any],
    module_df: pd.DataFrame,
    dropped_count: int,
) -> None:
    lines = [
        "# 品质异常主任务模型报告",
        "",
        "## 解决的问题",
        "",
        "- 类别不平衡：二分类、多分类、浅层规则模型均使用 `class_weight=balanced` 或 `balanced_subsample`；评价使用 Macro F1、Balanced Accuracy 和每类召回。",
        "- 时间漂移：按 `process_time` 做时间外推切分，训练集为早期月份，验证/测试集为后续月份。",
        "- 参数强耦合：按训练集相关系数做高相关特征裁剪，并按工艺模块聚合特征重要性。",
        "- 多异常共存：除单标签主任务外，额外训练 7 个异常大类 one-vs-rest 多标签模型。",
        "",
        "## 数据切分",
        "",
        split_df.to_markdown(index=False),
        "",
        "## 测试集指标",
        "",
        f"- 二分类 Balanced Accuracy: {binary_test['balanced_accuracy']:.4f}",
        f"- 二分类 Macro F1: {binary_test['macro_f1']:.4f}",
        f"- 二分类 PR-AUC: {binary_test.get('pr_auc', float('nan')):.4f}",
        f"- 多分类 Balanced Accuracy: {multiclass_test['balanced_accuracy']:.4f}",
        f"- 多分类 Macro F1: {multiclass_test['macro_f1']:.4f}",
        f"- 多标签 Macro F1: {multilabel_metrics_payload['macro_f1']:.4f}",
        f"- 多标签 Hamming Loss: {multilabel_metrics_payload['hamming_loss']:.4f}",
        "",
        "## 主要工艺模块重要性",
        "",
        module_df.head(10).to_markdown(index=False),
        "",
        f"高相关裁剪删除特征数：{dropped_count}",
        "",
        "详细分类报告、混淆矩阵、特征重要性和规则已写入同目录 CSV/JSON 文件。",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train quality traceability models.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--feature-groups", type=Path, default=DEFAULT_FEATURE_GROUPS)
    parser.add_argument("--multiclass-labels", type=Path, default=None)
    parser.add_argument("--multilabel-labels", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--train-end", default="2022-08")
    parser.add_argument("--val-end", default="2022-10")
    parser.add_argument("--corr-threshold", type=float, default=0.995)
    parser.add_argument("--rf-trees", type=int, default=160)
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--save-models", action="store_true")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    feature_groups = load_json(args.feature_groups)
    feature_to_group = feature_group_map(feature_groups)
    feature_cols = [c for cols in feature_groups.values() for c in cols]
    feature_cols = list(dict.fromkeys(feature_cols))

    df = pd.read_csv(args.input, low_memory=False)
    dataset_dir = args.input.parent

    multiclass_path = args.multiclass_labels or dataset_dir / "y_quality_multiclass.csv"
    if multiclass_path.is_file() and "record_id" in df.columns:
        y_multiclass = pd.read_csv(multiclass_path, low_memory=False)
        merge_cols = [
            col
            for col in [
                "record_id",
                "quality_multiclass_code",
                "quality_multiclass_id",
                "quality_multiclass_name",
            ]
            if col in y_multiclass.columns
        ]
        if "record_id" in merge_cols and LABEL_COL in merge_cols:
            df = df.drop(columns=[c for c in merge_cols if c != "record_id" and c in df.columns])
            df = df.merge(y_multiclass[merge_cols], on="record_id", how="left")

    multilabel_path = args.multilabel_labels or dataset_dir / "y_quality_multilabel.csv"
    if multilabel_path.is_file() and "record_id" in df.columns:
        y_multilabel = pd.read_csv(multilabel_path, low_memory=False)
        extra_cols = ["quality_target_label_count", "has_multiple_quality_targets"]
        merge_cols = ["record_id"] + [
            col for col in [*MULTILABEL_COLS, *extra_cols] if col in y_multilabel.columns
        ]
        df = df.drop(columns=[c for c in merge_cols if c != "record_id" and c in df.columns])
        df = df.merge(y_multilabel[merge_cols], on="record_id", how="left")

    if LABEL_COL not in df.columns and "quality_abnormal_group_cn" in df.columns:
        df[LABEL_COL] = df["quality_abnormal_group_cn"]
    df[TIME_COL] = pd.to_datetime(df[TIME_COL], errors="coerce")
    df = df.dropna(subset=[TIME_COL, LABEL_COL]).copy()
    feature_cols = [c for c in feature_cols if c in df.columns]
    for col in feature_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    split = make_time_split(df, train_end=args.train_end, val_end=args.val_end)
    split_df = split_summary(df, split)
    split_df.to_csv(args.output_dir / "split_summary.csv", index=False, encoding="utf-8-sig")

    x_all = df[feature_cols]
    x_train_raw = x_all.loc[split.eq("train")]
    kept_features, dropped_records = remove_highly_correlated_features(
        x_train_raw,
        feature_to_group,
        args.corr_threshold,
    )
    pd.DataFrame(dropped_records).to_csv(
        args.output_dir / "dropped_correlated_features.csv",
        index=False,
        encoding="utf-8-sig",
    )
    save_json(
        args.output_dir / "feature_preprocessing.json",
        {
            "original_feature_count": len(feature_cols),
            "kept_feature_count": len(kept_features),
            "correlation_threshold": args.corr_threshold,
            "dropped_feature_count": len(dropped_records),
            "kept_features": kept_features,
        },
    )

    x_train = x_all.loc[split.eq("train"), kept_features]
    x_val = x_all.loc[split.eq("val"), kept_features]
    x_test = x_all.loc[split.eq("test"), kept_features]
    y_train_label = df.loc[split.eq("train"), LABEL_COL].astype(str)
    y_val_label = df.loc[split.eq("val"), LABEL_COL].astype(str)
    y_test_label = df.loc[split.eq("test"), LABEL_COL].astype(str)

    # Binary abnormal detection: class imbalance handled by balanced class weights.
    y_train_bin = y_train_label.ne(NO_ABNORMAL_LABEL).astype(int).to_numpy()
    y_val_bin = y_val_label.ne(NO_ABNORMAL_LABEL).astype(int).to_numpy()
    y_test_bin = y_test_label.ne(NO_ABNORMAL_LABEL).astype(int).to_numpy()
    binary_model = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            (
                "clf",
                RandomForestClassifier(
                    n_estimators=args.rf_trees,
                    max_depth=None,
                    min_samples_leaf=30,
                    class_weight="balanced_subsample",
                    n_jobs=-1,
                    random_state=42,
                ),
            ),
        ]
    )
    binary_model.fit(x_train, y_train_bin)
    binary_val_pred = binary_model.predict(x_val)
    binary_test_pred = binary_model.predict(x_test)
    binary_val_prob = binary_model.predict_proba(x_val)[:, 1]
    binary_test_prob = binary_model.predict_proba(x_test)[:, 1]
    binary_val = binary_metrics(y_val_bin, binary_val_pred, binary_val_prob)
    binary_test = binary_metrics(y_test_bin, binary_test_pred, binary_test_prob)
    save_json(args.output_dir / "binary_model_report.json", {"val": binary_val, "test": binary_test})
    report_to_frame(binary_test["classification_report"]).to_csv(
        args.output_dir / "binary_classification_report_test.csv",
        index=False,
        encoding="utf-8-sig",
    )
    pd.DataFrame(
        confusion_matrix(y_test_bin, binary_test_pred),
        index=["true_normal", "true_abnormal"],
        columns=["pred_normal", "pred_abnormal"],
    ).to_csv(args.output_dir / "binary_confusion_matrix_test.csv", encoding="utf-8-sig")

    # Multiclass quality abnormal group model.
    label_encoder = LabelEncoder()
    y_train = label_encoder.fit_transform(y_train_label)
    y_val = label_encoder.transform(y_val_label)
    y_test = label_encoder.transform(y_test_label)
    labels = label_encoder.classes_.tolist()

    multiclass_rf = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            (
                "clf",
                RandomForestClassifier(
                    n_estimators=args.rf_trees,
                    max_depth=None,
                    min_samples_leaf=25,
                    class_weight="balanced_subsample",
                    n_jobs=-1,
                    random_state=43,
                ),
            ),
        ]
    )
    multiclass_rf.fit(x_train, y_train)
    val_pred = multiclass_rf.predict(x_val)
    test_pred = multiclass_rf.predict(x_test)
    test_pred_prob = multiclass_rf.predict_proba(x_test)
    multiclass_val = multiclass_metrics(y_val, val_pred, labels)
    multiclass_test = multiclass_metrics(y_test, test_pred, labels)
    save_json(
        args.output_dir / "multiclass_model_report.json",
        {"labels": labels, "val": multiclass_val, "test": multiclass_test},
    )
    report_to_frame(multiclass_test["classification_report"]).to_csv(
        args.output_dir / "multiclass_classification_report_test.csv",
        index=False,
        encoding="utf-8-sig",
    )
    pd.DataFrame(
        confusion_matrix(y_test, test_pred, labels=np.arange(len(labels))),
        index=[f"true__{x}" for x in labels],
        columns=[f"pred__{x}" for x in labels],
    ).to_csv(args.output_dir / "multiclass_confusion_matrix_test.csv", encoding="utf-8-sig")

    pred_df = pd.DataFrame(
        {
            "record_id": df.loc[split.eq("test"), "record_id"].to_numpy()
            if "record_id" in df.columns
            else np.arange(len(y_test)),
            "process_time": df.loc[split.eq("test"), TIME_COL].astype(str).to_numpy(),
            "binary_true_abnormal": y_test_bin,
            "binary_pred_abnormal": binary_test_pred,
            "binary_abnormal_probability": binary_test_prob,
            "true_label": y_test_label.to_numpy(),
            "pred_label": label_encoder.inverse_transform(test_pred),
            "pred_label_confidence": test_pred_prob.max(axis=1),
        }
    )
    for class_pos, class_id in enumerate(multiclass_rf.named_steps["clf"].classes_):
        class_label = label_encoder.inverse_transform([class_id])[0]
        pred_df[f"multiclass_probability__{class_label}"] = test_pred_prob[:, class_pos]
    pred_df.to_csv(args.output_dir / "multiclass_test_predictions.csv", index=False, encoding="utf-8-sig")

    rf_clf = multiclass_rf.named_steps["clf"]
    global_importance = pd.DataFrame(
        {
            "feature": kept_features,
            "importance": rf_clf.feature_importances_,
        }
    ).sort_values("importance", ascending=False)
    global_importance["feature_group"] = global_importance["feature"].map(feature_to_group).fillna("unknown")
    global_importance.to_csv(
        args.output_dir / "feature_importance_global.csv",
        index=False,
        encoding="utf-8-sig",
    )
    module_df = module_importance(global_importance[["feature", "importance"]], feature_to_group)
    module_df.to_csv(args.output_dir / "module_importance_global.csv", index=False, encoding="utf-8-sig")

    # Regularized linear model for signed class-wise explanations under strong coupling.
    logistic_model = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    max_iter=900,
                    class_weight="balanced",
                    solver="lbfgs",
                    n_jobs=-1,
                    random_state=44,
                ),
            ),
        ]
    )
    logistic_model.fit(x_train, y_train)
    by_class = logistic_by_class_importance(logistic_model, labels, kept_features, args.top_n)
    by_class["feature_group"] = by_class["feature"].map(feature_to_group).fillna("unknown")
    by_class.to_csv(args.output_dir / "feature_importance_by_class.csv", index=False, encoding="utf-8-sig")

    rules = train_rules(
        x_train,
        y_train_label,
        labels,
        args.output_dir / "quality_rules_by_class.json",
        max_depth=3,
    )

    # Multi-label abnormal-group model for samples with multiple quality codes.
    ml_cols = [c for c in MULTILABEL_COLS if c in df.columns]
    multilabel_payload: dict[str, Any] = {
        "status": "skipped",
        "reason": "No multilabel columns found.",
    }
    if ml_cols:
        yml_train = df.loc[split.eq("train"), ml_cols].apply(pd.to_numeric, errors="coerce").fillna(0).astype(int)
        yml_val = df.loc[split.eq("val"), ml_cols].apply(pd.to_numeric, errors="coerce").fillna(0).astype(int)
        yml_test = df.loc[split.eq("test"), ml_cols].apply(pd.to_numeric, errors="coerce").fillna(0).astype(int)
        multilabel_model = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                (
                    "clf",
                    OneVsRestClassifier(
                        LogisticRegression(
                            max_iter=700,
                            class_weight="balanced",
                            solver="lbfgs",
                            random_state=45,
                        ),
                        n_jobs=-1,
                    ),
                ),
            ]
        )
        multilabel_model.fit(x_train, yml_train)
        yml_pred = multilabel_model.predict(x_test)
        yml_prob = multilabel_model.predict_proba(x_test)
        micro_f1 = f1_score(yml_test, yml_pred, average="micro", zero_division=0)
        macro_f1 = f1_score(yml_test, yml_pred, average="macro", zero_division=0)
        precision, recall, f1, support = precision_recall_fscore_support(
            yml_test,
            yml_pred,
            average=None,
            zero_division=0,
        )
        per_label = pd.DataFrame(
            {
                "label_col": ml_cols,
                "label_cn": [MULTILABEL_CN.get(c, c) for c in ml_cols],
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "support": support,
            }
        )
        per_label.to_csv(args.output_dir / "multilabel_classification_report_test.csv", index=False, encoding="utf-8-sig")
        multilabel_payload = {
            "status": "ok",
            "micro_f1": float(micro_f1),
            "macro_f1": float(macro_f1),
            "hamming_loss": float(hamming_loss(yml_test, yml_pred)),
            "labels": ml_cols,
            "label_cn": {c: MULTILABEL_CN.get(c, c) for c in ml_cols},
        }
        for idx, col in enumerate(ml_cols):
            pred_df[f"multilabel_true__{col}"] = yml_test[col].to_numpy()
            pred_df[f"multilabel_pred__{col}"] = yml_pred[:, idx]
            pred_df[f"multilabel_probability__{col}"] = yml_prob[:, idx]
            pred_df[f"cascade_multilabel_pred__{col}"] = np.where(
                pred_df["binary_pred_abnormal"].eq(1),
                pred_df[f"multilabel_pred__{col}"],
                0,
            )
            pred_df[f"cascade_multilabel_score__{col}"] = (
                pred_df["binary_abnormal_probability"] * pred_df[f"multilabel_probability__{col}"]
            )
        save_json(args.output_dir / "multilabel_model_report.json", multilabel_payload)
    else:
        save_json(args.output_dir / "multilabel_model_report.json", multilabel_payload)

    pred_df["cascade_final_label"] = np.where(
        pred_df["binary_pred_abnormal"].eq(1),
        pred_df["pred_label"],
        NO_ABNORMAL_LABEL,
    )
    pred_df["cascade_main_class_score"] = np.where(
        pred_df["binary_pred_abnormal"].eq(1),
        pred_df["binary_abnormal_probability"] * pred_df["pred_label_confidence"],
        1.0 - pred_df["binary_abnormal_probability"],
    )
    top_class_features = by_class.sort_values(["label", "rank"]).groupby("label").head(5)
    class_evidence: dict[str, str] = {}
    class_modules: dict[str, str] = {}
    for label, part in top_class_features.groupby("label"):
        class_evidence[str(label)] = "; ".join(
            f"{row.feature}({row.direction},{row.abs_coef:.3f})"
            for row in part.itertuples(index=False)
        )
        class_modules[str(label)] = "; ".join(
            dict.fromkeys(str(value) for value in part["feature_group"] if str(value))
        )
    evidence_rows: list[dict[str, Any]] = []
    for row in pred_df.itertuples(index=False):
        row_dict = row._asdict()
        final_label = str(row_dict["cascade_final_label"])
        companion_scores = []
        for col in ml_cols:
            score_col = f"cascade_multilabel_score__{col}"
            if score_col not in row_dict:
                continue
            score = float(row_dict[score_col])
            if score > 0:
                companion_scores.append((MULTILABEL_CN.get(col, col), score))
        companion_scores.sort(key=lambda item: item[1], reverse=True)
        evidence_rows.append(
            {
                "record_id": row_dict["record_id"],
                "process_time": row_dict["process_time"],
                "cascade_final_label": final_label,
                "cascade_main_class_score": row_dict["cascade_main_class_score"],
                "binary_abnormal_probability": row_dict["binary_abnormal_probability"],
                "top_companion_abnormal_scores": "; ".join(
                    f"{name}:{score:.3f}" for name, score in companion_scores[:3]
                ),
                "top_class_evidence_features": class_evidence.get(final_label, ""),
                "evidence_feature_groups": class_modules.get(final_label, ""),
            }
        )
    pd.DataFrame(evidence_rows).to_csv(
        args.output_dir / "traceability_candidate_evidence_test.csv",
        index=False,
        encoding="utf-8-sig",
    )
    pred_df.to_csv(args.output_dir / "cascade_test_predictions.csv", index=False, encoding="utf-8-sig")

    evidence = {
        "input": str(args.input),
        "time_split": {
            "train_end": args.train_end,
            "val_end": args.val_end,
        },
        "features": {
            "original_count": len(feature_cols),
            "kept_count": len(kept_features),
            "dropped_correlated_count": len(dropped_records),
        },
        "labels": labels,
        "binary_test": {
            k: v for k, v in binary_test.items() if k != "classification_report"
        },
        "multiclass_test": {
            k: v for k, v in multiclass_test.items() if k != "classification_report"
        },
        "multilabel_test": multilabel_payload,
        "top_global_features": global_importance.head(args.top_n).to_dict("records"),
        "module_importance": module_df.to_dict("records"),
        "rules_available_for_labels": list(rules.keys()),
    }
    save_json(args.output_dir / "model_evidence_bundle.json", evidence)
    save_json(
        args.output_dir / "label_encoder.json",
        {"classes": labels, "class_to_id": {label: int(i) for i, label in enumerate(labels)}},
    )
    write_markdown_summary(
        args.output_dir / "model_quality_summary.md",
        split_df=split_df,
        binary_test=binary_test,
        multiclass_test=multiclass_test,
        multilabel_metrics_payload=multilabel_payload
        if multilabel_payload.get("status") == "ok"
        else {"macro_f1": 0.0, "hamming_loss": 1.0},
        module_df=module_df,
        dropped_count=len(dropped_records),
    )

    if args.save_models:
        model_dir = args.output_dir / "models"
        model_dir.mkdir(exist_ok=True)
        joblib.dump(binary_model, model_dir / "binary_random_forest.joblib")
        joblib.dump(multiclass_rf, model_dir / "multiclass_random_forest.joblib")
        joblib.dump(logistic_model, model_dir / "multiclass_logistic_explainer.joblib")
        if ml_cols and multilabel_payload.get("status") == "ok":
            joblib.dump(multilabel_model, model_dir / "multilabel_ovr_logistic.joblib")

    print(f"Quality modeling outputs written to: {args.output_dir}")
    print(f"Kept features: {len(kept_features)} / {len(feature_cols)}")
    print(f"Binary test macro F1: {binary_test['macro_f1']:.4f}")
    print(f"Multiclass test macro F1: {multiclass_test['macro_f1']:.4f}")
    if multilabel_payload.get("status") == "ok":
        print(f"Multilabel test macro F1: {multilabel_payload['macro_f1']:.4f}")


if __name__ == "__main__":
    main()
