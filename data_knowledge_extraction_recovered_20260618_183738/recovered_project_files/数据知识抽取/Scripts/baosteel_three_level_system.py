from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline

from multiclass_event_evaluation import compute_multiclass_metrics


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASET_DIR = (
    PROJECT_ROOT
    / "knowledge_exports"
    / "quality_traceability_dataset_v8_quality_core_event_line_2_1_hierarchical_mixed_neg3"
)
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "knowledge_exports" / "baosteel_three_level_system_v1"

META_COLUMNS = {
    "sample_id",
    "event_bag_id",
    "precursor_stage",
    "lead_horizon_min",
    "lead_horizon_max",
    "caster_id",
    "strand_parity",
    "caster_strand_interaction",
}

ABNORMAL_CLASSES = [
    "temperature_flux",
    "mold_level_slag_risk",
    "speed_stopper_flow",
    "process_fluctuation",
    "heat_transfer_imbalance",
    "transition_tundish",
]

VARIABLE_GROUP_ALIASES = {
    "temperature": {"temp", "temperature", "superheat", "liquidus", "过热", "温度", "液相线"},
    "flux": {"flux", "cover_flux", "slag", "保护渣", "覆盖剂"},
    "mold_level": {"mold_level", "液面"},
    "casting_speed": {"cast_speed", "拉速"},
    "stopper": {"stopper", "塞棒"},
    "nozzle_flow": {"nozzle", "flow", "水口", "滑板", "流量"},
    "argon_pressure": {"argon", "氩", "pressure", "压力"},
    "tundish_weight": {"td_weight", "tundish", "中间包", "大包", "钢水量", "吨位"},
    "sequence_transition": {"sequence", "transition", "交接", "连浇", "镇静"},
    "heat_transfer": {"heat_exchange", "heat_transfer", "热交换", "拔热"},
    "ems_taper_oscillation": {"ems", "taper", "oscillation", "电磁", "锥度", "振动"},
}

GROUP_TO_CONTEXT = {
    "temperature": ("tundish", "thermal_state", "temperature_flux"),
    "flux": ("mold", "slag_flux_state", "temperature_flux"),
    "mold_level": ("mold", "mold_level_stability", "mold_level_slag_risk"),
    "casting_speed": ("caster", "casting_speed_stability", "speed_stopper_flow"),
    "stopper": ("flow_control", "flow_control_stability", "speed_stopper_flow"),
    "nozzle_flow": ("flow_control", "flow_control_stability", "speed_stopper_flow"),
    "argon_pressure": ("flow_control", "argon_flow_stability", "speed_stopper_flow"),
    "tundish_weight": ("tundish", "process_operation", "process_fluctuation"),
    "sequence_transition": ("tundish", "tundish_transition", "transition_tundish"),
    "heat_transfer": ("mold_heat_transfer", "heat_transfer_uniformity", "heat_transfer_imbalance"),
    "ems_taper_oscillation": ("mold", "oscillation_ems_state", "heat_transfer_imbalance"),
}

CLASS_RECOMMENDATIONS = {
    "temperature_flux": {
        "summary": "温度-保护渣相关边界失稳风险。",
        "checks": ["复核中包温度、液相线温度和过热度窗口趋势", "检查保护渣加入量和保护渣总量是否突变"],
        "adjustments": ["优先稳定过热度目标区间", "避免保护渣补加节奏与温度波动叠加"],
    },
    "mold_level_slag_risk": {
        "summary": "结晶器液面-保护渣卷渣或液面波动风险。",
        "checks": ["复核液面极差、液面大幅波动次数和拉速变化", "检查保护渣消耗与液面波动是否同步"],
        "adjustments": ["平滑拉速调整", "加强液面控制并核查保护渣状态"],
    },
    "speed_stopper_flow": {
        "summary": "拉速-塞棒-水口流量控制链路失稳风险。",
        "checks": ["检查拉速波动、塞棒开口度和上水口/滑板流量", "复核氩气压力和流量是否异常"],
        "adjustments": ["降低流量控制扰动", "同步校核塞棒、水口和氩气控制参数"],
    },
    "process_fluctuation": {
        "summary": "中包/连浇过程参数复合波动风险。",
        "checks": ["检查中包吨位波动、连浇炉数和交接部信息", "确认是否处于过渡或操作扰动阶段"],
        "adjustments": ["优先稳定中包液位和过渡段操作", "将复合波动样本纳入重点复核"],
    },
    "heat_transfer_imbalance": {
        "summary": "结晶器传热不均或振动/电磁搅拌相关风险。",
        "checks": ["复核东西/南北拔热量差和四面热交换", "检查电磁搅拌、锥度和振动频率"],
        "adjustments": ["检查结晶器冷却均匀性", "复核振动和电磁搅拌参数设定"],
    },
    "transition_tundish": {
        "summary": "换包或中包过渡上下文风险。",
        "checks": ["核对交接部位置、长度、连浇炉数和中包吨位", "判断异常是否与过渡段重叠"],
        "adjustments": ["将过渡段作为上下文风险管理", "加强过渡前后温度和液位复核"],
    },
}


def _json_sanitize(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not np.isfinite(value):
            return None
        return value
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, np.ndarray):
        return [_json_sanitize(x) for x in value.tolist()]
    if isinstance(value, Mapping):
        return {str(k): _json_sanitize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_sanitize(x) for x in value]
    return str(value)


def _read_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_json_sanitize(payload), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _split_set(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, (list, tuple, set)):
        raw = value
    else:
        raw = str(value).split(";")
    out: set[str] = set()
    for item in raw:
        text = str(item).strip()
        if text and text.lower() not in {"nan", "none", "null", "missing", "no_reason_evidence"}:
            out.add(text)
    return out


def _base_feature_name(column: str) -> str:
    text = str(column)
    for suffix in ("_mean", "_std", "_last", "_trend"):
        if text.endswith(suffix):
            return text[: -len(suffix)]
    return text


def infer_variable_group(feature_name: str, feature_groups: Mapping[str, Sequence[str]] | None = None) -> str:
    base = _base_feature_name(feature_name)
    lower = base.lower()
    for group, members in dict(feature_groups or {}).items():
        for member in members:
            member_text = str(member)
            if member_text and (member_text == base or member_text in base or member_text.lower() in lower):
                inferred = _keyword_variable_group(base)
                return inferred if inferred != "process_operation" else str(group)
    return _keyword_variable_group(base)


def _keyword_variable_group(feature_name: str) -> str:
    lower = feature_name.lower()
    for group, aliases in VARIABLE_GROUP_ALIASES.items():
        if any(alias.lower() in lower or alias in feature_name for alias in aliases):
            return group
    return "process_operation"


def _class_for_group(group: str) -> str:
    return GROUP_TO_CONTEXT.get(group, ("process", "process_operation", "process_fluctuation"))[2]


def build_multihop_path_templates(
    feature_columns: Sequence[str],
    feature_groups: Mapping[str, Sequence[str]] | None = None,
) -> list[dict[str, Any]]:
    """Build full-chain KIEP-GL display paths from window features."""
    paths: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for column in feature_columns:
        feature = str(column)
        if feature in META_COLUMNS:
            continue
        group = infer_variable_group(feature, feature_groups)
        equipment, state, mechanism = GROUP_TO_CONTEXT.get(group, ("process", "process_operation", "process_fluctuation"))
        key = (feature, mechanism)
        if key in seen:
            continue
        seen.add(key)
        recommendation = CLASS_RECOMMENDATIONS.get(mechanism, CLASS_RECOMMENDATIONS["process_fluctuation"])
        nodes = [
            {"id": feature, "label": feature, "layer": "window_feature"},
            {"id": group, "label": group, "layer": "variable_group"},
            {"id": equipment, "label": equipment, "layer": "equipment_zone"},
            {"id": state, "label": state, "layer": "process_state"},
            {"id": mechanism, "label": mechanism, "layer": "defect_mechanism"},
            {"id": mechanism, "label": mechanism, "layer": "event_quality_class"},
            {
                "id": f"action_{mechanism}",
                "label": recommendation["summary"],
                "layer": "correction_action",
            },
        ]
        paths.append(
            {
                "path_id": f"path_{len(paths):04d}_{group}_{mechanism}",
                "feature": feature,
                "variable_group": group,
                "equipment_zone": equipment,
                "process_state": state,
                "defect_mechanism": mechanism,
                "event_target": mechanism,
                "stage": "unknown",
                "nodes": nodes,
                "edges": [
                    {"source": nodes[i]["id"], "target": nodes[i + 1]["id"], "relation": "hierarchical_trace"}
                    for i in range(len(nodes) - 1)
                ],
                "inferred_middle_layer": False,
            }
        )
    paths.sort(key=lambda p: (p["defect_mechanism"], p["variable_group"], p["feature"]))
    return paths


def compute_three_level_path_metrics(
    top_paths_by_event: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    reason_mechanisms_by_event: Mapping[str, Any],
    reason_variable_groups_by_event: Mapping[str, Any],
    reason_stages_by_event: Mapping[str, Any],
    top_k: int = 3,
) -> dict[str, Any]:
    """Quantify mechanism, variable-group, stage and completeness alignment."""
    mechanism_hits = 0
    variable_hits = 0
    stage_hits = 0
    n_reason_events = 0
    occlusion_scores: list[float] = []
    comprehensiveness_scores: list[float] = []
    per_event: dict[str, Any] = {}

    required_layers = {
        "window_feature",
        "variable_group",
        "equipment_zone",
        "process_state",
        "defect_mechanism",
    }
    all_event_ids = set(str(x) for x in top_paths_by_event)
    all_event_ids.update(str(x) for x in reason_mechanisms_by_event)
    for event_id in sorted(all_event_ids):
        paths = list(top_paths_by_event.get(event_id, []) or [])[: max(1, int(top_k))]
        if not paths:
            continue
        path_mechanisms = {str(p.get("defect_mechanism", "")) for p in paths if p.get("defect_mechanism")}
        path_groups = {str(p.get("variable_group", "")) for p in paths if p.get("variable_group")}
        path_stages = {str(p.get("stage", "")) for p in paths if p.get("stage")}
        for path in paths:
            occlusion_scores.append(float(path.get("path_occlusion_drop", 0.0) or 0.0))
            layers = {str(node.get("layer")) for node in path.get("nodes", []) if isinstance(node, Mapping)}
            comprehensiveness_scores.append(len(layers & required_layers) / len(required_layers))

        reason_mechanisms = _split_set(reason_mechanisms_by_event.get(event_id))
        reason_groups = _split_set(reason_variable_groups_by_event.get(event_id))
        reason_stages = _split_set(reason_stages_by_event.get(event_id))
        if reason_mechanisms:
            n_reason_events += 1
            mechanism_hit = bool(path_mechanisms & reason_mechanisms)
            variable_hit = bool(path_groups & reason_groups) if reason_groups else False
            stage_hit = bool(path_stages & reason_stages) or any(
                str(p.get("process_state", "")) in reason_stages or str(p.get("equipment_zone", "")) in reason_stages
                for p in paths
            )
            mechanism_hits += int(mechanism_hit)
            variable_hits += int(variable_hit)
            stage_hits += int(stage_hit)
            per_event[event_id] = {
                "mechanism_hit": float(mechanism_hit),
                "variable_group_hit": float(variable_hit),
                "stage_hit": float(stage_hit),
                "predicted_mechanisms": sorted(path_mechanisms),
                "predicted_variable_groups": sorted(path_groups),
                "reason_mechanisms": sorted(reason_mechanisms),
                "reason_variable_groups": sorted(reason_groups),
                "reason_stages": sorted(reason_stages),
            }

    denom = float(n_reason_events)
    return {
        "top_k": int(top_k),
        "n_events_with_paths": int(sum(1 for paths in top_paths_by_event.values() if paths)),
        "n_reason_events": int(n_reason_events),
        "mechanism_alignment_at_k": float(mechanism_hits / denom) if denom else 0.0,
        "variable_group_alignment_at_k": float(variable_hits / denom) if denom else 0.0,
        "stage_alignment_at_k": float(stage_hits / denom) if denom else 0.0,
        "average_occlusion_drop_at_k": float(np.mean(occlusion_scores)) if occlusion_scores else 0.0,
        "path_comprehensiveness": float(np.mean(comprehensiveness_scores)) if comprehensiveness_scores else 0.0,
        "path_consistency_score": _path_consistency_score(top_paths_by_event),
        "per_event": per_event,
    }


def _path_consistency_score(top_paths_by_event: Mapping[str, Sequence[Mapping[str, Any]]]) -> float:
    family_by_event: dict[str, set[str]] = defaultdict(set)
    for event_id, paths in top_paths_by_event.items():
        base_id = str(event_id).rsplit("__", 1)[0]
        for path in list(paths or [])[:1]:
            family_by_event[base_id].add(str(path.get("path_template_id") or path.get("path_id") or ""))
    scores = []
    for families in family_by_event.values():
        if not families:
            continue
        scores.append(1.0 / len(families))
    return float(np.mean(scores)) if scores else 0.0


def _load_dataset(dataset_dir: Path, max_rows: int | None = None) -> tuple[pd.DataFrame, pd.DataFrame, list[str], dict[str, Any]]:
    x_path = dataset_dir / "X_event_precursor_windows.csv"
    y_path = dataset_dir / "y_hierarchical_event_label.csv"
    if not x_path.is_file() or not y_path.is_file():
        raise FileNotFoundError(f"Dataset files not found in {dataset_dir}")
    read_kwargs = {"encoding": "utf-8-sig"}
    if max_rows is not None and int(max_rows) > 0:
        read_kwargs["nrows"] = int(max_rows)
    x = pd.read_csv(x_path, **read_kwargs)
    y = pd.read_csv(y_path, **read_kwargs)
    if len(x) != len(y) and "sample_id" in x.columns and "sample_id" in y.columns:
        merged = x.merge(y, on="sample_id", suffixes=("", "_label"))
        x = merged[[c for c in x.columns if c in merged.columns]].copy()
        y = merged[[c for c in y.columns if c in merged.columns or c == "sample_id"]].copy()
    n = min(len(x), len(y))
    x = x.iloc[:n].reset_index(drop=True)
    y = y.iloc[:n].reset_index(drop=True)
    mapping = _read_json(dataset_dir / "class_name_mapping.json", {"classes": []})
    classes = _class_names_from_mapping(mapping, y)
    return x, y, classes, mapping


def _class_names_from_mapping(mapping: Mapping[str, Any], y: pd.DataFrame) -> list[str]:
    classes = sorted(
        [dict(item) for item in mapping.get("classes", [])],
        key=lambda item: int(item.get("class_id", 0)),
    )
    names = [str(item.get("class_name", item.get("class_id"))) for item in classes]
    if names:
        return names
    if "event_quality_class_id" in y.columns and "event_quality_class" in y.columns:
        pairs = (
            y[["event_quality_class_id", "event_quality_class"]]
            .dropna()
            .drop_duplicates()
            .sort_values("event_quality_class_id")
            .itertuples(index=False)
        )
        return [str(name) for _, name in pairs]
    max_id = int(pd.to_numeric(y.get("event_quality_class_id", pd.Series([0])), errors="coerce").fillna(0).max())
    return [str(i) for i in range(max_id + 1)]


def _numeric_feature_frame(x: pd.DataFrame) -> pd.DataFrame:
    out = x.drop(columns=[c for c in META_COLUMNS if c in x.columns], errors="ignore").copy()
    for col in list(out.columns):
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out.select_dtypes(include=[np.number]).replace([np.inf, -np.inf], np.nan)


def _split_indices(y: Sequence[int], random_state: int) -> tuple[np.ndarray, np.ndarray]:
    arr = np.asarray(y, dtype=int)
    idx = np.arange(len(arr))
    if len(arr) < 8 or len(set(arr.tolist())) < 2:
        return idx, idx
    counts = Counter(arr.tolist())
    stratify = arr if min(counts.values()) >= 2 else None
    train_idx, test_idx = train_test_split(
        idx,
        test_size=0.35,
        random_state=int(random_state),
        stratify=stratify,
    )
    return np.asarray(train_idx, dtype=int), np.asarray(test_idx, dtype=int)


def _fit_classifier(x: pd.DataFrame, y: np.ndarray, n_estimators: int, random_state: int) -> Any:
    model = make_pipeline(
        SimpleImputer(strategy="median"),
        ExtraTreesClassifier(
            n_estimators=int(n_estimators),
            random_state=int(random_state),
            class_weight="balanced",
            n_jobs=1,
            min_samples_leaf=1,
        ),
    )
    model.fit(x, y)
    return model


def _aligned_proba(model: Any, x: pd.DataFrame, expected_classes: Sequence[int]) -> np.ndarray:
    raw = np.asarray(model.predict_proba(x), dtype=float)
    classes = np.asarray(model.named_steps["extratreesclassifier"].classes_, dtype=int)
    expected = [int(c) for c in expected_classes]
    out = np.zeros((len(x), len(expected)), dtype=float)
    pos = {class_id: i for i, class_id in enumerate(expected)}
    for src, class_id in enumerate(classes):
        if int(class_id) in pos:
            out[:, pos[int(class_id)]] = raw[:, src]
    denom = out.sum(axis=1, keepdims=True)
    return out / np.where(denom > 0, denom, 1.0)


def _binary_metrics(y_true: np.ndarray, proba: np.ndarray) -> dict[str, Any]:
    pred = (proba >= 0.5).astype(int)
    out = {
        "accuracy": float(accuracy_score(y_true, pred)),
        "f1": float(f1_score(y_true, pred, zero_division=0)),
        "recall": float(recall_score(y_true, pred, zero_division=0)),
        "positive_rate": float(np.mean(y_true == 1)) if len(y_true) else 0.0,
    }
    try:
        out["auc"] = float(roc_auc_score(y_true, proba)) if len(set(y_true.tolist())) > 1 else None
    except ValueError:
        out["auc"] = None
    return out


def _risk_level(probability: float) -> str:
    p = float(probability)
    if p >= 0.75:
        return "high"
    if p >= 0.45:
        return "medium"
    return "low"


def _boundary_features(x_num: pd.DataFrame) -> pd.DataFrame:
    med = x_num.median(axis=0, skipna=True)
    q75 = x_num.quantile(0.75)
    q25 = x_num.quantile(0.25)
    scale = (q75 - q25).replace(0.0, np.nan).fillna(x_num.std(axis=0).replace(0.0, np.nan)).fillna(1.0)
    z = ((x_num - med) / scale).abs()
    max_z = z.max(axis=1).fillna(0.0)
    active = z.idxmax(axis=1).fillna("")
    margin = max_z - 1.5
    status = np.where(margin >= 1.0, "boundary_violation", np.where(margin >= 0.0, "near_boundary", "safe"))
    return pd.DataFrame(
        {
            "rule_margin": margin.astype(float),
            "boundary_status": status,
            "active_rule_column": active.astype(str),
        },
        index=x_num.index,
    )


def _feature_importance(model: Any, feature_names: Sequence[str]) -> dict[str, float]:
    clf = model.named_steps.get("extratreesclassifier")
    values = getattr(clf, "feature_importances_", np.zeros(len(feature_names)))
    return {str(name): float(value) for name, value in zip(feature_names, values)}


def _top_risk_variables(row: pd.Series, importances: Mapping[str, float], limit: int = 5) -> list[dict[str, Any]]:
    scores = []
    for feature, importance in importances.items():
        value = row.get(feature)
        if pd.isna(value):
            continue
        scores.append({"feature": feature, "value": float(value), "importance": float(importance), "score": abs(float(value)) * float(importance)})
    scores.sort(key=lambda item: (-item["score"], item["feature"]))
    return scores[: int(limit)]


def _select_paths_for_row(
    row: pd.Series,
    *,
    templates: Sequence[Mapping[str, Any]],
    predicted_class: str,
    importances: Mapping[str, float],
    risk_probability: float,
    boundary_active_column: str,
    risk_model: Any | None,
    x_columns: Sequence[str],
    x_median: pd.Series,
    top_k: int,
) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    for template in templates:
        feature = str(template["feature"])
        mechanism = str(template["defect_mechanism"])
        value = row.get(feature, np.nan)
        if pd.isna(value):
            continue
        class_match = 1.0 if mechanism == predicted_class else 0.35
        boundary_bonus = 0.15 if feature == str(boundary_active_column) else 0.0
        score = (
            0.55 * float(importances.get(feature, 0.0))
            + 0.25 * min(1.0, abs(float(value)) / (abs(float(x_median.get(feature, 0.0))) + 1.0))
            + 0.20 * class_match
            + boundary_bonus
        )
        path = dict(template)
        path["path_template_id"] = f"{template['variable_group']}->{template['defect_mechanism']}"
        path["path_score"] = float(np.clip(score, 0.0, 1.0))
        path["stage"] = str(row.get("precursor_stage", template.get("stage", "unknown")))
        path["feature_value"] = float(value)
        path["path_occlusion_drop"] = _estimate_occlusion_drop(
            row,
            feature,
            risk_model=risk_model,
            x_columns=x_columns,
            x_median=x_median,
            baseline_probability=float(risk_probability),
        )
        ranked.append(path)
    ranked.sort(key=lambda item: (item["defect_mechanism"] != predicted_class, -float(item["path_score"])))
    return ranked[: max(1, int(top_k))]


def _estimate_occlusion_drop(
    row: pd.Series,
    feature: str,
    *,
    risk_model: Any | None,
    x_columns: Sequence[str],
    x_median: pd.Series,
    baseline_probability: float,
) -> float:
    if risk_model is None or feature not in x_columns:
        return 0.0
    x_row = pd.DataFrame([{col: row.get(col, np.nan) for col in x_columns}])
    x_occ = x_row.copy()
    x_occ.loc[:, feature] = float(x_median.get(feature, 0.0))
    try:
        occ_proba = _positive_probability(risk_model, x_occ)
        return float(max(0.0, baseline_probability - float(occ_proba[0])))
    except Exception:
        return 0.0


def _positive_probability(model: Any, x: pd.DataFrame) -> np.ndarray:
    proba = np.asarray(model.predict_proba(x), dtype=float)
    classes = np.asarray(model.named_steps["extratreesclassifier"].classes_, dtype=int)
    if 1 in classes:
        return proba[:, int(np.where(classes == 1)[0][0])]
    return np.zeros(len(x), dtype=float)


def _recommendation(event_id: str, predicted_class: str, paths: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    spec = CLASS_RECOMMENDATIONS.get(predicted_class, CLASS_RECOMMENDATIONS["process_fluctuation"])
    evidence = [
        f"{path.get('feature')} -> {path.get('variable_group')} -> {path.get('defect_mechanism')}"
        for path in list(paths)[:3]
    ]
    return {
        "event_id": event_id,
        "risk_summary": spec["summary"],
        "suspected_path": evidence[0] if evidence else predicted_class,
        "evidence": evidence,
        "recommended_checks": list(spec["checks"]),
        "recommended_adjustments": list(spec["adjustments"]),
        "verification_actions": ["复核该事件 early/mid/late 窗口下路径稳定性", "对 top 路径关键变量进行遮蔽验证或人工复核"],
        "confidence": "medium" if predicted_class != "no_quality_abnormal" else "low",
        "source_snippets": ["本地专家规则模板", "模型路径证据", "rule_margin 边界证据"],
        "llm_generated_text": "",
    }


def _export_task_views(output_dir: Path, x: pd.DataFrame, y: pd.DataFrame, risk_proba: np.ndarray, class_proba: np.ndarray, class_names: Sequence[str]) -> None:
    task_dir = output_dir / "task_datasets"
    task_dir.mkdir(parents=True, exist_ok=True)
    base = pd.DataFrame(
        {
            "sample_id": x.get("sample_id", pd.Series(range(len(x)))),
            "event_bag_id": x.get("event_bag_id", pd.Series(range(len(x)))),
            "precursor_stage": x.get("precursor_stage", pd.Series(["unknown"] * len(x))),
            "lead_horizon_min": x.get("lead_horizon_min", pd.Series([np.nan] * len(x))),
        }
    )
    risk = base.copy()
    risk["risk_label"] = y.get("risk_label", y.get("event_is_abnormal", pd.Series([0] * len(y)))).astype(int).to_numpy()
    risk["risk_probability"] = risk_proba
    risk.to_csv(task_dir / "task1_risk_warning_dataset.csv", index=False, encoding="utf-8-sig")

    identify = base.copy()
    identify["event_quality_class"] = y.get("event_quality_class", pd.Series(["unknown"] * len(y))).astype(str)
    identify["predicted_class"] = [class_names[int(i)] if 0 <= int(i) < len(class_names) else str(i) for i in np.argmax(class_proba, axis=1)]
    identify["class_confidence"] = np.max(class_proba, axis=1)
    identify.to_csv(task_dir / "task2_abnormal_identification_dataset.csv", index=False, encoding="utf-8-sig")

    trace = base.copy()
    for col in ("reason_mechanism_set", "reason_stage_set", "reason_variable_group_set"):
        if col in y.columns:
            trace[col] = y[col].astype(str)
    trace.to_csv(task_dir / "task3_traceability_dataset.csv", index=False, encoding="utf-8-sig")


def _make_path_graph(templates: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[tuple[str, str], dict[str, Any]] = {}
    for path in templates:
        for node in path.get("nodes", []):
            nodes[str(node["id"])] = dict(node)
        for edge in path.get("edges", []):
            key = (str(edge["source"]), str(edge["target"]))
            edges[key] = dict(edge)
    return {"nodes": list(nodes.values()), "edges": list(edges.values()), "n_templates": int(len(templates))}


def _write_dashboard(output_dir: Path, dashboard_data: Mapping[str, Any]) -> None:
    dashboard_dir = output_dir / "dashboard"
    dashboard_dir.mkdir(parents=True, exist_ok=True)
    data_json = json.dumps(_json_sanitize(dashboard_data), ensure_ascii=False)
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>宝钢连铸三层次异常分析系统</title>
  <style>
    :root {{ color-scheme: light; --ink:#17202a; --muted:#5f6f7e; --line:#d9e1e8; --risk:#c83f31; --ok:#2d7d46; --blue:#1f6fb2; --gold:#a66b00; }}
    body {{ margin:0; font-family: "Microsoft YaHei", Arial, sans-serif; background:#f6f8fb; color:var(--ink); }}
    header {{ padding:22px 28px; background:#ffffff; border-bottom:1px solid var(--line); }}
    h1 {{ margin:0; font-size:24px; letter-spacing:0; }}
    main {{ display:grid; grid-template-columns: 300px 1fr; gap:18px; padding:18px; }}
    .panel {{ background:#fff; border:1px solid var(--line); border-radius:8px; padding:16px; }}
    .metrics {{ display:grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap:12px; }}
    .metric strong {{ display:block; font-size:22px; margin-top:4px; }}
    .event-list {{ display:flex; flex-direction:column; gap:8px; max-height:680px; overflow:auto; }}
    button.event {{ text-align:left; border:1px solid var(--line); background:#fff; border-radius:6px; padding:10px; cursor:pointer; }}
    button.event.active {{ border-color:var(--blue); box-shadow:0 0 0 2px rgba(31,111,178,.12); }}
    .tabs {{ display:flex; gap:8px; margin-bottom:12px; flex-wrap:wrap; }}
    .tab {{ border:1px solid var(--line); background:#fff; border-radius:6px; padding:8px 12px; cursor:pointer; }}
    .tab.active {{ background:#1f6fb2; color:#fff; border-color:#1f6fb2; }}
    .grid {{ display:grid; grid-template-columns: repeat(3, 1fr); gap:12px; }}
    .chain {{ display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin:10px 0; }}
    .node {{ border:1px solid var(--line); border-radius:6px; padding:8px 10px; background:#fafdff; font-size:13px; max-width:210px; overflow-wrap:anywhere; }}
    .node.window_feature {{ border-color:#8ab6d6; }}
    .node.variable_group {{ border-color:#7bbf8a; }}
    .node.equipment_zone {{ border-color:#b79bd8; }}
    .node.process_state {{ border-color:#d6a55f; }}
    .node.defect_mechanism {{ border-color:#d66d5f; }}
    .node.event_quality_class {{ border-color:#c83f31; font-weight:700; }}
    .node.correction_action {{ border-color:#516c86; background:#f2f6fa; }}
    .arrow {{ color:#7a8794; }}
    .badge {{ display:inline-block; border-radius:999px; padding:3px 8px; font-size:12px; background:#eef3f7; margin-right:6px; }}
    .risk {{ color:var(--risk); font-weight:700; }}
    .ok {{ color:var(--ok); font-weight:700; }}
    .muted {{ color:var(--muted); }}
    pre {{ white-space:pre-wrap; background:#f6f8fb; padding:12px; border-radius:6px; border:1px solid var(--line); }}
    @media (max-width: 900px) {{ main {{ grid-template-columns:1fr; }} .metrics,.grid {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
  <header>
    <h1>宝钢连铸三层次异常分析与路径溯源系统</h1>
    <div class="muted">异常预警 -> 异常识别 -> 异常溯源 -> 纠正建议</div>
  </header>
  <main>
    <aside class="panel">
      <h2>事件列表</h2>
      <div id="eventList" class="event-list"></div>
    </aside>
    <section>
      <div class="panel">
        <h2>系统总览</h2>
        <div id="metrics" class="metrics"></div>
      </div>
      <div class="panel" style="margin-top:18px;">
        <div class="tabs">
          <button class="tab active" data-tab="warning">异常预警</button>
          <button class="tab" data-tab="identify">异常识别</button>
          <button class="tab" data-tab="trace">异常溯源</button>
          <button class="tab" data-tab="recommend">纠正建议</button>
        </div>
        <div id="detail"></div>
      </div>
    </section>
  </main>
  <script>
  window.THREE_LEVEL_DATA = {data_json};
  const data = window.THREE_LEVEL_DATA;
  let selectedIndex = 0;
  let selectedTab = 'warning';
  const fmt = (x) => typeof x === 'number' ? x.toFixed(3) : (x ?? '');
  function renderMetrics() {{
    const m = data.metrics || {{}};
    const items = [
      ['预警 F1', m.risk_warning?.f1],
      ['预警 AUC', m.risk_warning?.auc],
      ['识别 Macro-F1', m.abnormal_identification?.macro_f1],
      ['路径对齐', m.traceability?.mechanism_alignment_at_k],
    ];
    document.getElementById('metrics').innerHTML = items.map(([k,v]) => `<div class="metric panel"><span class="muted">${{k}}</span><strong>${{fmt(v)}}</strong></div>`).join('');
  }}
  function renderList() {{
    const events = data.events || [];
    document.getElementById('eventList').innerHTML = events.map((e,i) => `
      <button class="event ${{i===selectedIndex?'active':''}}" onclick="selectedIndex=${{i}};renderAll();">
        <b>${{e.event_id}}</b><br>
        <span class="${{e.risk_warning?.risk_level === 'high' ? 'risk':'muted'}}">${{e.risk_warning?.risk_level}}</span>
        <span class="muted"> / ${{e.abnormal_identification?.primary_abnormal_class}}</span>
      </button>`).join('');
  }}
  function chain(path) {{
    return `<div class="chain">${{(path.nodes||[]).map((n,i) => `${{i?'<span class="arrow">-></span>':''}}<span class="node ${{n.layer}}">${{n.label||n.id}}<br><small class="muted">${{n.layer}}</small></span>`).join('')}}</div>
      <div><span class="badge">score ${{fmt(path.path_score)}}</span><span class="badge">occlusion ${{fmt(path.path_occlusion_drop)}}</span><span class="badge">${{path.stage}}</span></div>`;
  }}
  function renderDetail() {{
    const e = (data.events || [])[selectedIndex] || {{}};
    let html = '';
    if (selectedTab === 'warning') {{
      html = `<div class="grid">
        <div><b>风险概率</b><p class="risk">${{fmt(e.risk_warning?.risk_probability)}}</p></div>
        <div><b>风险等级</b><p>${{e.risk_warning?.risk_level}}</p></div>
        <div><b>边界状态</b><p>${{e.risk_warning?.boundary_status}}</p></div>
      </div><h3>关键风险变量</h3><pre>${{JSON.stringify(e.risk_warning?.top_risk_variables || [], null, 2)}}</pre>`;
    }} else if (selectedTab === 'identify') {{
      html = `<div class="grid">
        <div><b>主要异常类</b><p>${{e.abnormal_identification?.primary_abnormal_class}}</p></div>
        <div><b>类别置信度</b><p>${{fmt(e.abnormal_identification?.class_confidence)}}</p></div>
        <div><b>并发异常</b><p>${{(e.abnormal_identification?.multi_label_abnormal_groups||[]).join('; ')}}</p></div>
      </div><pre>${{JSON.stringify(e.abnormal_identification?.class_probability || {{}}, null, 2)}}</pre>`;
    }} else if (selectedTab === 'trace') {{
      html = `<h3>Top-k 多层路径</h3>${{(e.traceability?.top_k_paths || []).map(chain).join('')}}`;
    }} else {{
      html = `<h3>${{e.recommendation?.risk_summary || ''}}</h3>
        <b>检查项</b><ul>${{(e.recommendation?.recommended_checks||[]).map(x=>`<li>${{x}}</li>`).join('')}}</ul>
        <b>调整项</b><ul>${{(e.recommendation?.recommended_adjustments||[]).map(x=>`<li>${{x}}</li>`).join('')}}</ul>
        <b>证据</b><pre>${{JSON.stringify(e.recommendation?.evidence || [], null, 2)}}</pre>`;
    }}
    document.getElementById('detail').innerHTML = html;
  }}
  function renderTabs() {{
    document.querySelectorAll('.tab').forEach(btn => {{
      btn.classList.toggle('active', btn.dataset.tab === selectedTab);
      btn.onclick = () => {{ selectedTab = btn.dataset.tab; renderTabs(); renderDetail(); }};
    }});
  }}
  function renderAll() {{ renderMetrics(); renderList(); renderTabs(); renderDetail(); }}
  renderAll();
  </script>
</body>
</html>
"""
    (dashboard_dir / "index.html").write_text(html, encoding="utf-8")


def run_three_level_system(
    *,
    dataset_dir: str | Path = DEFAULT_DATASET_DIR,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    max_rows: int | None = None,
    n_estimators: int = 120,
    random_state: int = 42,
    top_k_paths: int = 3,
) -> dict[str, Any]:
    dataset_path = Path(dataset_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    x, y, class_names, _ = _load_dataset(dataset_path, max_rows=max_rows)
    feature_groups = _read_json(dataset_path / "feature_groups.json", {})
    x_num = _numeric_feature_frame(x)
    if x_num.empty:
        raise ValueError("No numeric feature columns were found for model training.")

    y_risk = pd.to_numeric(y.get("risk_label", y.get("event_is_abnormal", pd.Series([0] * len(y)))), errors="coerce").fillna(0).astype(int).to_numpy()
    y_class = pd.to_numeric(y.get("event_quality_class_id", pd.Series([0] * len(y))), errors="coerce").fillna(0).astype(int).to_numpy()
    expected_class_ids = list(range(max(max(y_class, default=0) + 1, len(class_names))))
    while len(class_names) < len(expected_class_ids):
        class_names.append(str(len(class_names)))

    train_idx, test_idx = _split_indices(y_risk, random_state)
    risk_model = _fit_classifier(x_num.iloc[train_idx], y_risk[train_idx], n_estimators, random_state)
    risk_proba_all = _positive_probability(risk_model, x_num)
    risk_metrics = _binary_metrics(y_risk[test_idx], risk_proba_all[test_idx])

    class_model = _fit_classifier(x_num.iloc[train_idx], y_class[train_idx], n_estimators, random_state + 13)
    class_proba_all = _aligned_proba(class_model, x_num, expected_class_ids)
    class_metrics = compute_multiclass_metrics(
        y_class[test_idx],
        class_proba_all[test_idx],
        class_names=class_names[: len(expected_class_ids)],
        normal_class_id=0,
    )
    class_pred = np.argmax(class_proba_all, axis=1)
    precision, recall, f1, support = precision_recall_fscore_support(
        y_class[test_idx],
        np.argmax(class_proba_all[test_idx], axis=1),
        labels=expected_class_ids,
        zero_division=0,
    )
    class_metrics["confusion_matrix"] = confusion_matrix(y_class[test_idx], np.argmax(class_proba_all[test_idx], axis=1), labels=expected_class_ids).tolist()
    class_metrics["per_class_array"] = [
        {
            "class_id": int(class_id),
            "class_name": class_names[int(class_id)] if int(class_id) < len(class_names) else str(class_id),
            "precision": float(precision[i]),
            "recall": float(recall[i]),
            "f1": float(f1[i]),
            "support": int(support[i]),
        }
        for i, class_id in enumerate(expected_class_ids)
    ]
    class_metrics["multilabel_hit_rate"] = _multilabel_hit_rate(y, class_pred, class_names)

    boundary = _boundary_features(x_num)
    risk_importance = _feature_importance(risk_model, x_num.columns)
    class_importance = _feature_importance(class_model, x_num.columns)
    combined_importance = {
        feature: 0.55 * risk_importance.get(feature, 0.0) + 0.45 * class_importance.get(feature, 0.0)
        for feature in x_num.columns
    }
    templates = build_multihop_path_templates(list(x_num.columns), feature_groups)
    x_median = x_num.median(axis=0, skipna=True).fillna(0.0)

    events: list[dict[str, Any]] = []
    recommendations: list[dict[str, Any]] = []
    top_paths_by_event: dict[str, list[dict[str, Any]]] = {}
    for row_idx in range(len(x)):
        event_id = str(x.loc[row_idx, "event_bag_id"] if "event_bag_id" in x.columns else y.loc[row_idx].get("event_bag_id", row_idx))
        pred_class_id = int(class_pred[row_idx])
        pred_class = class_names[pred_class_id] if pred_class_id < len(class_names) else str(pred_class_id)
        row_paths = _select_paths_for_row(
            x_num.iloc[row_idx],
            templates=templates,
            predicted_class=pred_class,
            importances=combined_importance,
            risk_probability=float(risk_proba_all[row_idx]),
            boundary_active_column=str(boundary.loc[row_idx, "active_rule_column"]),
            risk_model=risk_model,
            x_columns=list(x_num.columns),
            x_median=x_median,
            top_k=top_k_paths,
        )
        top_paths_by_event[event_id] = row_paths
        reco = _recommendation(event_id, pred_class, row_paths)
        recommendations.append(reco)
        probability_by_class = {
            class_names[i] if i < len(class_names) else str(i): float(class_proba_all[row_idx, i])
            for i in range(class_proba_all.shape[1])
        }
        event_record = {
            "event_id": event_id,
            "sample_id": str(x.loc[row_idx, "sample_id"] if "sample_id" in x.columns else row_idx),
            "precursor_stage": str(x.loc[row_idx, "precursor_stage"] if "precursor_stage" in x.columns else "unknown"),
            "lead_horizon_min": float(x.loc[row_idx, "lead_horizon_min"]) if "lead_horizon_min" in x.columns and pd.notna(x.loc[row_idx, "lead_horizon_min"]) else None,
            "risk_warning": {
                "risk_label": int(y_risk[row_idx]),
                "risk_probability": float(risk_proba_all[row_idx]),
                "risk_level": _risk_level(float(risk_proba_all[row_idx])),
                "boundary_status": str(boundary.loc[row_idx, "boundary_status"]),
                "rule_margin": float(boundary.loc[row_idx, "rule_margin"]),
                "active_rule_column": str(boundary.loc[row_idx, "active_rule_column"]),
                "top_risk_variables": _top_risk_variables(x_num.iloc[row_idx], combined_importance),
            },
            "abnormal_identification": {
                "primary_abnormal_class": pred_class,
                "true_abnormal_class": str(y.loc[row_idx, "event_quality_class"] if "event_quality_class" in y.columns else y_class[row_idx]),
                "class_probability": probability_by_class,
                "class_confidence": float(np.max(class_proba_all[row_idx])),
                "multi_label_abnormal_groups": sorted(_split_set(y.loc[row_idx, "quality_abnormal_groups"] if "quality_abnormal_groups" in y.columns else "")),
                "ambiguous_flag": bool(float(np.max(class_proba_all[row_idx])) < 0.55),
            },
            "traceability": {
                "top_k_paths": row_paths,
                "reason_mechanism_set": str(y.loc[row_idx, "reason_mechanism_set"] if "reason_mechanism_set" in y.columns else ""),
                "reason_stage_set": str(y.loc[row_idx, "reason_stage_set"] if "reason_stage_set" in y.columns else ""),
                "reason_variable_group_set": str(y.loc[row_idx, "reason_variable_group_set"] if "reason_variable_group_set" in y.columns else ""),
            },
            "recommendation": reco,
        }
        events.append(event_record)

    path_metrics = compute_three_level_path_metrics(
        top_paths_by_event,
        reason_mechanisms_by_event=_event_reason_map(x, y, "reason_mechanism_set"),
        reason_variable_groups_by_event=_event_reason_map(x, y, "reason_variable_group_set"),
        reason_stages_by_event=_event_reason_map(x, y, "reason_stage_set"),
        top_k=top_k_paths,
    )
    metrics = {
        "risk_warning": risk_metrics,
        "abnormal_identification": class_metrics,
        "traceability": path_metrics,
        "dataset": {
            "n_samples": int(len(x)),
            "n_features": int(x_num.shape[1]),
            "class_names": class_names[: len(expected_class_ids)],
            "boundary_region_ratio": boundary["boundary_status"].value_counts(normalize=True).to_dict(),
        },
    }
    dashboard_data = {
        "metrics": metrics,
        "events": events[: min(400, len(events))],
        "path_graph": _make_path_graph(templates),
        "recommendations": recommendations[: min(400, len(recommendations))],
    }

    _export_task_views(output_path, x, y, risk_proba_all, class_proba_all, class_names)
    _write_json(output_path / "model_metrics.json", metrics)
    _write_json(output_path / "path_metrics.json", path_metrics)
    _write_json(output_path / "path_graph.json", _make_path_graph(templates))
    _write_json(output_path / "correction_recommendations.json", recommendations)
    _write_json(output_path / "dashboard_data.json", dashboard_data)
    with (output_path / "event_explanations.jsonl").open("w", encoding="utf-8") as fh:
        for event in events:
            fh.write(json.dumps(_json_sanitize(event), ensure_ascii=False) + "\n")
    with (output_path / "correction_recommendations.jsonl").open("w", encoding="utf-8") as fh:
        for item in recommendations:
            fh.write(json.dumps(_json_sanitize(item), ensure_ascii=False) + "\n")
    _write_dashboard(output_path, dashboard_data)

    summary = {
        "status": "ok",
        "dataset_dir": str(dataset_path),
        "output_dir": str(output_path),
        "n_samples": int(len(x)),
        "n_features": int(x_num.shape[1]),
        "risk_f1": float(risk_metrics.get("f1", 0.0)),
        "identification_macro_f1": float(class_metrics.get("macro_f1", 0.0)),
        "path_mechanism_alignment_at_k": float(path_metrics.get("mechanism_alignment_at_k", 0.0)),
        "dashboard": str(output_path / "dashboard" / "index.html"),
    }
    _write_json(output_path / "system_summary.json", summary)
    return summary


def _event_reason_map(x: pd.DataFrame, y: pd.DataFrame, column: str) -> dict[str, Any]:
    if column not in y.columns:
        return {}
    out: dict[str, Any] = {}
    event_ids = x["event_bag_id"] if "event_bag_id" in x.columns else y.get("event_bag_id", pd.Series(range(len(y))))
    for event_id, value in zip(event_ids.astype(str), y[column]):
        if str(event_id) not in out or not _split_set(out[str(event_id)]):
            out[str(event_id)] = value
    return out


def _multilabel_hit_rate(y: pd.DataFrame, pred_ids: np.ndarray, class_names: Sequence[str]) -> float:
    if "quality_abnormal_groups" not in y.columns:
        return 0.0
    hits = 0
    total = 0
    for raw_groups, pred_id in zip(y["quality_abnormal_groups"], pred_ids):
        pred_name = class_names[int(pred_id)] if int(pred_id) < len(class_names) else str(pred_id)
        groups = _split_set(raw_groups)
        if not groups:
            continue
        total += 1
        hits += int(pred_name in groups or (pred_name == "no_quality_abnormal" and "no_quality_abnormal" in groups))
    return float(hits / total) if total else 0.0


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run Baosteel three-level warning, identification and traceability system.")
    parser.add_argument("--dataset-dir", default=str(DEFAULT_DATASET_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--max-rows", type=int, default=None)
    parser.add_argument("--n-estimators", type=int, default=120)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--top-k-paths", type=int, default=3)
    args = parser.parse_args(argv)
    summary = run_three_level_system(
        dataset_dir=args.dataset_dir,
        output_dir=args.output_dir,
        max_rows=args.max_rows,
        n_estimators=args.n_estimators,
        random_state=args.random_state,
        top_k_paths=args.top_k_paths,
    )
    print(json.dumps(_json_sanitize(summary), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
