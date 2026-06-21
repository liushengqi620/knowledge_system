from __future__ import annotations

from collections import Counter, OrderedDict
from typing import Any, Mapping, Sequence

import numpy as np


def _as_1d_int(values: Sequence[Any] | np.ndarray) -> np.ndarray:
    return np.asarray(values, dtype=int).reshape(-1)


def _as_2d_float(values: Sequence[Sequence[float]] | np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.ndim != 2:
        raise ValueError("class_probabilities must be a 2-D array")
    return arr


def _resolve_class_names(n_classes: int, class_names: Sequence[str] | None) -> list[str]:
    if class_names is None:
        return [str(i) for i in range(n_classes)]
    names = [str(x) for x in class_names]
    if len(names) != n_classes:
        raise ValueError("class_names length must match the probability dimension")
    return names


def _safe_div(num: float, den: float) -> float:
    return float(num / den) if den else 0.0


def _average_precision_binary(y_true_binary: np.ndarray, scores: np.ndarray) -> float | None:
    positives = int(np.sum(y_true_binary == 1))
    negatives = int(np.sum(y_true_binary == 0))
    if positives == 0 or negatives == 0:
        return None
    order = np.argsort(-scores, kind="mergesort")
    sorted_true = y_true_binary[order]
    hit_count = 0
    precision_sum = 0.0
    for rank, label in enumerate(sorted_true, start=1):
        if int(label) == 1:
            hit_count += 1
            precision_sum += hit_count / rank
    return float(precision_sum / positives)


def _topk_accuracy(y_true: np.ndarray, proba: np.ndarray, top_k: int) -> float:
    if len(y_true) == 0:
        return 0.0
    k = int(max(1, min(top_k, proba.shape[1])))
    topk = np.argsort(-proba, axis=1, kind="mergesort")[:, :k]
    return float(np.mean([int(label) in topk[i] for i, label in enumerate(y_true)]))


def _wrong_class_alarm_rate(y_true: np.ndarray, y_pred: np.ndarray, *, normal_class_id: int) -> float:
    abnormal_alarm = (y_true != int(normal_class_id)) & (y_pred != int(normal_class_id))
    wrong_alarm = abnormal_alarm & (y_pred != y_true)
    return _safe_div(float(np.sum(wrong_alarm)), float(np.sum(abnormal_alarm)))


def compute_multiclass_metrics(
    y_true: Sequence[int] | np.ndarray,
    class_probabilities: Sequence[Sequence[float]] | np.ndarray,
    *,
    class_names: Sequence[str] | None = None,
    normal_class_id: int = 0,
    top_k: int = 2,
) -> dict[str, Any]:
    """Compute sample-level metrics for multiclass quality-event warning."""
    y = _as_1d_int(y_true)
    proba = _as_2d_float(class_probabilities)
    if len(y) != len(proba):
        raise ValueError("y_true and class_probabilities must have the same row count")
    names = _resolve_class_names(proba.shape[1], class_names)
    pred = np.argmax(proba, axis=1).astype(int)

    per_class: dict[str, dict[str, float | int | None]] = {}
    recalls: list[float] = []
    precisions: list[float] = []
    f1s: list[float] = []
    for class_id, name in enumerate(names):
        true_pos = (y == class_id)
        pred_pos = (pred == class_id)
        tp = int(np.sum(true_pos & pred_pos))
        fp = int(np.sum(~true_pos & pred_pos))
        fn = int(np.sum(true_pos & ~pred_pos))
        precision = _safe_div(tp, tp + fp)
        recall = _safe_div(tp, tp + fn)
        f1 = _safe_div(2.0 * precision * recall, precision + recall)
        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)
        per_class[name] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": int(np.sum(true_pos)),
            "auc_pr": _average_precision_binary(true_pos.astype(int), proba[:, class_id]),
        }

    return {
        "accuracy": float(np.mean(pred == y)) if len(y) else 0.0,
        "macro_precision": float(np.mean(precisions)) if precisions else 0.0,
        "macro_recall": float(np.mean(recalls)) if recalls else 0.0,
        "macro_f1": float(np.mean(f1s)) if f1s else 0.0,
        "balanced_accuracy": float(np.mean(recalls)) if recalls else 0.0,
        "top2_accuracy": _topk_accuracy(y, proba, top_k),
        "wrong_class_alarm_rate": _wrong_class_alarm_rate(y, pred, normal_class_id=int(normal_class_id)),
        "normal_class_id": int(normal_class_id),
        "class_names": names,
        "per_class": per_class,
    }


def _ordered_event_groups(event_ids: Sequence[Any] | np.ndarray) -> OrderedDict[str, list[int]]:
    groups: OrderedDict[str, list[int]] = OrderedDict()
    for idx, raw_event_id in enumerate(np.asarray(event_ids, dtype=object).reshape(-1)):
        key = str(raw_event_id)
        groups.setdefault(key, []).append(idx)
    return groups


def _event_true_class(labels: np.ndarray, *, normal_class_id: int) -> int:
    abnormal = [int(x) for x in labels if int(x) != int(normal_class_id)]
    if not abnormal:
        return int(normal_class_id)
    return Counter(abnormal).most_common(1)[0][0]


def compute_event_level_multiclass_metrics(
    y_true: Sequence[int] | np.ndarray,
    class_probabilities: Sequence[Sequence[float]] | np.ndarray,
    *,
    event_ids: Sequence[Any] | np.ndarray,
    horizons: Sequence[float] | np.ndarray | None = None,
    class_names: Sequence[str] | None = None,
    normal_class_id: int = 0,
) -> dict[str, Any]:
    """Aggregate point predictions into event-level multiclass warning metrics."""
    y = _as_1d_int(y_true)
    proba = _as_2d_float(class_probabilities)
    event_arr = np.asarray(event_ids, dtype=object).reshape(-1)
    if len(y) != len(proba) or len(y) != len(event_arr):
        raise ValueError("y_true, class_probabilities and event_ids must have the same row count")
    horizon_arr = None if horizons is None else np.asarray(horizons, dtype=float).reshape(-1)
    if horizon_arr is not None and len(horizon_arr) != len(y):
        raise ValueError("horizons must have the same row count as y_true")
    names = _resolve_class_names(proba.shape[1], class_names)

    groups = _ordered_event_groups(event_arr)
    event_records: list[dict[str, Any]] = []
    for event_id, idxs in groups.items():
        idx = np.asarray(idxs, dtype=int)
        true_class = _event_true_class(y[idx], normal_class_id=int(normal_class_id))
        event_scores = np.nanmax(proba[idx], axis=0)
        pred_class = int(np.argmax(event_scores))
        lead_time = None
        if true_class != int(normal_class_id) and pred_class == true_class and horizon_arr is not None:
            row_pred = np.argmax(proba[idx], axis=1)
            hit_horizons = horizon_arr[idx][(row_pred == true_class) & np.isfinite(horizon_arr[idx]) & (horizon_arr[idx] > 0)]
            if len(hit_horizons):
                lead_time = float(np.max(hit_horizons))
        event_records.append(
            {
                "event_id": event_id,
                "true_class_id": int(true_class),
                "pred_class_id": int(pred_class),
                "true_class": names[int(true_class)] if 0 <= int(true_class) < len(names) else str(true_class),
                "pred_class": names[int(pred_class)] if 0 <= int(pred_class) < len(names) else str(pred_class),
                "lead_time": lead_time,
            }
        )

    abnormal_events = [r for r in event_records if r["true_class_id"] != int(normal_class_id)]
    normal_events = [r for r in event_records if r["true_class_id"] == int(normal_class_id)]
    correct_abnormal = [r for r in abnormal_events if r["pred_class_id"] == r["true_class_id"]]
    missed = [r for r in abnormal_events if r["pred_class_id"] == int(normal_class_id)]
    false_alarms = [r for r in normal_events if r["pred_class_id"] != int(normal_class_id)]
    abnormal_alarms = [r for r in abnormal_events if r["pred_class_id"] != int(normal_class_id)]
    wrong_class_alarms = [r for r in abnormal_alarms if r["pred_class_id"] != r["true_class_id"]]

    per_class_event: dict[str, dict[str, float | int]] = {}
    recalls: list[float] = []
    for class_id, name in enumerate(names):
        if class_id == int(normal_class_id):
            continue
        cls_events = [r for r in abnormal_events if r["true_class_id"] == class_id]
        cls_correct = [r for r in cls_events if r["pred_class_id"] == class_id]
        cls_recall = _safe_div(len(cls_correct), len(cls_events))
        if cls_events:
            recalls.append(cls_recall)
        per_class_event[name] = {
            "event_recall": cls_recall,
            "support_events": int(len(cls_events)),
            "correct_events": int(len(cls_correct)),
        }

    lead_times = [float(r["lead_time"]) for r in correct_abnormal if r.get("lead_time") is not None]
    return {
        "event_recall": _safe_div(len(correct_abnormal), len(abnormal_events)),
        "event_macro_recall": float(np.mean(recalls)) if recalls else 0.0,
        "false_alarm_rate": _safe_div(len(false_alarms), len(normal_events)),
        "wrong_class_alarm_rate": _safe_div(len(wrong_class_alarms), len(abnormal_alarms)),
        "missed_event_rate": _safe_div(len(missed), len(abnormal_events)),
        "average_lead_time": float(np.mean(lead_times)) if lead_times else 0.0,
        "median_lead_time": float(np.median(lead_times)) if lead_times else 0.0,
        "n_events": int(len(event_records)),
        "n_abnormal_events": int(len(abnormal_events)),
        "per_class_event": per_class_event,
    }


def _path_mechanism(path: Mapping[str, Any]) -> str | None:
    for key in ("defect_mechanism", "event_quality_class", "class_name", "target_class"):
        value = path.get(key)
        if value is not None and str(value).strip():
            return str(value)
    return None


def compute_path_explanation_metrics(
    top_paths_by_class: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    true_classes: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Evaluate whether returned paths cover and agree with the target classes."""
    if true_classes is None:
        classes = list(top_paths_by_class.keys())
    else:
        classes = [str(x) for x in true_classes]
    per_class: dict[str, dict[str, float | int]] = {}
    hits = 0
    matched_paths = 0
    total_paths = 0
    for class_name in classes:
        paths = list(top_paths_by_class.get(class_name, []) or [])
        if paths:
            hits += 1
        class_matches = 0
        for path in paths:
            mechanism = _path_mechanism(path)
            if mechanism == class_name:
                class_matches += 1
        matched_paths += class_matches
        total_paths += len(paths)
        per_class[class_name] = {
            "path_hit": float(1.0 if paths else 0.0),
            "n_paths": int(len(paths)),
            "matched_paths": int(class_matches),
            "knowledge_consistency": _safe_div(class_matches, len(paths)),
        }
    return {
        "path_hit_rate": _safe_div(hits, len(classes)),
        "knowledge_consistency": _safe_div(matched_paths, total_paths),
        "n_true_classes": int(len(classes)),
        "n_paths": int(total_paths),
        "per_class": per_class,
    }


def summarize_multiclass_event_evaluation(
    y_true: Sequence[int] | np.ndarray,
    class_probabilities: Sequence[Sequence[float]] | np.ndarray,
    *,
    class_names: Sequence[str] | None = None,
    event_ids: Sequence[Any] | np.ndarray | None = None,
    horizons: Sequence[float] | np.ndarray | None = None,
    top_paths_by_class: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
    normal_class_id: int = 0,
    top_k: int = 2,
) -> dict[str, Any]:
    """Return the three-layer evaluation summary used by KIEP-GL experiments."""
    y = _as_1d_int(y_true)
    proba = _as_2d_float(class_probabilities)
    names = _resolve_class_names(proba.shape[1], class_names)
    sample_metrics = compute_multiclass_metrics(
        y,
        proba,
        class_names=names,
        normal_class_id=int(normal_class_id),
        top_k=int(top_k),
    )
    event_metrics = (
        compute_event_level_multiclass_metrics(
            y,
            proba,
            event_ids=event_ids,
            horizons=horizons,
            class_names=names,
            normal_class_id=int(normal_class_id),
        )
        if event_ids is not None
        else {}
    )
    abnormal_class_names = sorted(
        {names[int(label)] for label in y if int(label) != int(normal_class_id) and 0 <= int(label) < len(names)}
    )
    path_metrics = compute_path_explanation_metrics(top_paths_by_class or {}, true_classes=abnormal_class_names)
    return {
        "sample_multiclass_metrics": sample_metrics,
        "event_warning_metrics": event_metrics,
        "path_explanation_metrics": path_metrics,
    }
