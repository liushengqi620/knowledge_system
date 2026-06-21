"""Build a full Baosteel-derived knowledge-extraction dataset.

The recovered Baosteel artifacts are structured modeling tables rather than
manual NER/RE corpora. This builder turns those processed tables into stable
industrial text records with weak entity/relation labels, PLM-style candidates,
deterministic splits, and a PLM-compatible training pool.

Default inputs are resolved relative to the recovered project layout:

- sibling `数据知识抽取/knowledge_exports/quality_traceability_dataset`
- sibling `数据知识抽取/knowledge_exports/baosteel_three_level_system_v1`
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator, TextIO


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RECOVERED_PROJECT_ROOT = PROJECT_ROOT.parent
DEFAULT_QUALITY_DIR = RECOVERED_PROJECT_ROOT / "数据知识抽取" / "knowledge_exports" / "quality_traceability_dataset"
DEFAULT_THREE_LEVEL_DIR = RECOVERED_PROJECT_ROOT / "数据知识抽取" / "knowledge_exports" / "baosteel_three_level_system_v1"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "baosteel_knowledge_extraction"

META_COLUMNS = {
    "record_id",
    "process_time",
    "连铸处理号",
    "材料跟踪号",
    "记录识别码",
}
Y_COLUMNS = {
    "quality_abnormal_label",
    "quality_abnormal_codes",
    "quality_abnormal_group",
    "quality_abnormal_group_cn",
    "quality_abnormal_groups",
    "quality_group_mold_level_slag_risk",
    "quality_group_process_fluctuation",
    "quality_group_speed_stopper_flow",
    "quality_group_heat_transfer_imbalance",
    "quality_group_transition_tundish",
    "quality_group_temperature_flux",
    "quality_group_other_quality_abnormal",
    "quality_label",
}

QUALITY_GROUP_CN = {
    "temperature_flux": "温度/保护剂质量类",
    "mold_level_slag_risk": "液面/卷渣质量类",
    "process_fluctuation": "过程参数异常类",
    "speed_stopper_flow": "拉速/塞棒/流量控制异常类",
    "heat_transfer_imbalance": "传热不均质量类",
    "transition_tundish": "交接过渡/质量状态类",
    "other_quality_abnormal": "其他品质异常类",
    "no_quality_abnormal": "未标记质量异常",
}

QUALITY_GROUP_STAGE = {
    "temperature_flux": "tundish_flux",
    "mold_level_slag_risk": "mold_level",
    "process_fluctuation": "process_window",
    "speed_stopper_flow": "casting_speed_stopper_flow",
    "heat_transfer_imbalance": "mold_heat_transfer",
    "transition_tundish": "tundish_transition",
    "other_quality_abnormal": "quality_review",
    "no_quality_abnormal": "normal_process",
}

FEATURE_GROUP_CN = {
    "flux": "保护剂与下渣",
    "tundish": "中间包",
    "casting_speed": "拉速",
    "mold_level": "结晶器液面",
    "nozzle_flow": "水口与滑板流量",
    "argon_and_pressure": "氩气与压力",
    "stopper": "塞棒开口度",
    "mold_heat_transfer": "结晶器传热",
    "mold_ems_taper_oscillation": "结晶器电磁搅拌/锥度/振动",
    "derived_process": "派生过程特征",
    "raw_process": "原始过程特征",
}

GROUP_PRIORITY_FEATURES = {
    "temperature_flux": [
        "TD_avg_temp",
        "liquidus_temp",
        "superheat",
        "cover_flux_total",
        "cover_flux_ratio",
        "覆盖剂1使用量/ppm",
        "覆盖剂2使用量/ppm",
    ],
    "mold_level_slag_risk": [
        "mold_level_range",
        "mold_level_mean",
        "mold_level_ge7",
        "mold_level_ge10",
        "液面波动极差/mm",
        "液面波动均值/mm",
    ],
    "process_fluctuation": [
        "cast_speed_range",
        "TD_weight_range",
        "heat_exchange_ew_diff",
        "heat_exchange_ns_diff",
        "拉速波动/(m/min)",
    ],
    "speed_stopper_flow": [
        "cast_speed_mean",
        "cast_speed_range",
        "塞棒开口度平均值/mm",
        "上水口流量波动/(L/min)",
        "上滑板流量波动/(L/min)",
    ],
    "heat_transfer_imbalance": [
        "heat_exchange_mean",
        "heat_exchange_ew_diff",
        "heat_exchange_ns_diff",
        "热交换平均(东)/℃",
        "热交换平均(西)/℃",
        "热交换平均(南)/℃",
        "热交换平均(北)/℃",
    ],
    "transition_tundish": [
        "tundish_sequence_count",
        "交接部开始位置/mm",
        "交接部长度/mm",
        "TD_weight_range",
        "中间包吨位波动/t",
    ],
    "other_quality_abnormal": [
        "TD_weight_mean",
        "TD_avg_temp",
        "cast_speed_mean",
        "mold_level_range",
        "heat_exchange_mean",
    ],
    "no_quality_abnormal": [
        "TD_weight_mean",
        "TD_avg_temp",
        "cast_speed_mean",
        "mold_level_range",
    ],
}

DEFAULT_FEATURE_PRIORITY = [
    "TD_weight_mean",
    "TD_weight_range",
    "TD_avg_temp",
    "cast_speed_mean",
    "cast_speed_range",
    "liquidus_temp",
    "superheat",
    "cover_flux_total",
    "mold_level_range",
    "mold_level_mean",
    "tundish_sequence_count",
    "heat_exchange_mean",
    "heat_exchange_ew_diff",
    "heat_exchange_ns_diff",
]

LAYER_ENTITY_TYPES = {
    "window_feature": "ProcessParameter",
    "variable_group": "ProcessParameter",
    "equipment_zone": "EquipmentState",
    "process_state": "EquipmentState",
    "defect_mechanism": "QualityMechanism",
    "event_quality_class": "QualityDefect",
    "correction_action": "Operation",
}

RELATION_TYPE_IDS = {
    "no_relation": 0,
    "associated_with": 1,
    "classified_as": 2,
    "hierarchical_trace": 3,
    "has_parameter": 4,
    "risk_evidence": 5,
    "recommended_check": 6,
    "recommended_adjustment": 7,
}


def _clean(value: Any) -> str:
    text = "" if value is None else str(value).strip()
    if text.lower() in {"", "nan", "none", "null", "missing"}:
        return ""
    return text


def _safe_float(value: Any) -> float | None:
    text = _clean(value)
    if not text:
        return None
    try:
        parsed = float(text)
    except ValueError:
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def _format_value(value: Any) -> str:
    parsed = _safe_float(value)
    if parsed is None:
        return _clean(value)
    if abs(parsed - round(parsed)) < 1e-9:
        return str(int(round(parsed)))
    return f"{parsed:.4f}".rstrip("0").rstrip(".")


def _bounded(value: float | None, default: float = 0.65) -> float:
    if value is None:
        return default
    return max(0.0, min(1.0, float(value)))


def _hash_split(split_group: str, seed: int, train_ratio: float, dev_ratio: float) -> str:
    digest = hashlib.sha1(f"{seed}:{split_group}".encode("utf-8")).hexdigest()
    bucket = int(digest[:12], 16) / float(0xFFFFFFFFFFFF)
    if bucket < train_ratio:
        return "train"
    if bucket < train_ratio + dev_ratio:
        return "dev"
    return "test"


def _feature_group(feature: str, feature_to_group: dict[str, str]) -> str:
    if feature in feature_to_group:
        return feature_to_group[feature]
    text = feature.lower()
    if "flux" in text or "覆盖剂" in feature:
        return "flux"
    if "td_" in text or "tundish" in text or "中间包" in feature:
        return "tundish"
    if "speed" in text or "拉速" in feature:
        return "casting_speed"
    if "mold_level" in text or "液面" in feature:
        return "mold_level"
    if "flow" in text or "流量" in feature:
        return "nozzle_flow"
    if "argon" in text or "pressure" in text or "氩" in feature or "压力" in feature:
        return "argon_and_pressure"
    if "stopper" in text or "塞棒" in feature:
        return "stopper"
    if "heat" in text or "热" in feature or "拔热" in feature:
        return "mold_heat_transfer"
    if "oscillation" in text or "ems" in text or "锥度" in feature or "振动" in feature:
        return "mold_ems_taper_oscillation"
    return "derived_process" if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", feature) else "raw_process"


def load_feature_groups(path: Path) -> tuple[dict[str, list[str]], dict[str, str]]:
    if not path.exists():
        return {}, {}
    groups = json.loads(path.read_text(encoding="utf-8-sig"))
    feature_to_group: dict[str, str] = {}
    for group, features in groups.items():
        for feature in features:
            feature_to_group[str(feature)] = str(group)
    return {str(k): [str(x) for x in v] for k, v in groups.items()}, feature_to_group


def select_features(
    row: dict[str, str],
    feature_columns: list[str],
    feature_to_group: dict[str, str],
    *,
    top_features: int,
) -> list[dict[str, str]]:
    groups = [_clean(x) for x in _clean(row.get("quality_abnormal_groups")).split(";") if _clean(x)]
    primary = _clean(row.get("quality_abnormal_group")) or "no_quality_abnormal"
    if primary not in groups:
        groups.insert(0, primary)

    priority: list[str] = []
    for group in groups:
        priority.extend(GROUP_PRIORITY_FEATURES.get(group, []))
    priority.extend(DEFAULT_FEATURE_PRIORITY)
    priority.extend(feature_columns)

    seen: set[str] = set()
    selected: list[dict[str, str]] = []
    for feature in priority:
        if feature in seen or feature not in row or feature in META_COLUMNS or feature in Y_COLUMNS:
            continue
        seen.add(feature)
        value = _clean(row.get(feature))
        if not value:
            continue
        selected.append(
            {
                "name": feature,
                "value": _format_value(value),
                "group": _feature_group(feature, feature_to_group),
            }
        )
        if len(selected) >= top_features:
            break
    return selected


@dataclass
class TextRecordBuilder:
    record_id: str
    parts: list[str] = field(default_factory=list)
    entities: list[dict[str, Any]] = field(default_factory=list)
    relations: list[dict[str, Any]] = field(default_factory=list)
    candidates: list[dict[str, Any]] = field(default_factory=list)
    _entity_index: int = 0
    _relation_index: int = 0
    _candidate_index: int = 0

    @property
    def text(self) -> str:
        return "".join(self.parts)

    def append(self, text: str) -> tuple[int, int]:
        start = len(self.text)
        self.parts.append(text)
        return start, start + len(text)

    def add_entity(
        self,
        surface: str,
        entity_type: str,
        *,
        source: str = "weak_rule",
        confidence: float | None = 0.65,
        normalization_id: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> str:
        start = len(self.text)
        self.parts.append(surface)
        end = len(self.text)
        self._entity_index += 1
        entity = {
            "entity_id": f"e{self._entity_index}",
            "text": surface,
            "type": entity_type,
            "start": start,
            "end": end,
            "source": source,
            "confidence": confidence,
            "normalization_id": normalization_id,
        }
        if extra:
            entity.update(extra)
        self.entities.append(entity)
        return entity["entity_id"]

    def add_relation(
        self,
        relation_type: str,
        head: str,
        tail: str,
        evidence_span: tuple[int, int],
        *,
        direction: str = "head_to_tail",
        source: str = "weak_rule",
        confidence: float | None = 0.65,
        extra: dict[str, Any] | None = None,
    ) -> str:
        self._relation_index += 1
        relation = {
            "relation_id": f"r{self._relation_index}",
            "type": relation_type,
            "head": head,
            "tail": tail,
            "direction": direction,
            "evidence_span": {"start": evidence_span[0], "end": evidence_span[1]},
            "source": source,
            "confidence": confidence,
        }
        if extra:
            relation.update(extra)
        self.relations.append(relation)
        return relation["relation_id"]

    def add_candidate(
        self,
        candidate_type: str,
        payload: dict[str, Any],
        evidence_span: tuple[int, int],
        *,
        confidence: float,
        uncertainty_type: str,
        prompt_atoms: list[str],
    ) -> str:
        self._candidate_index += 1
        candidate = {
            "candidate_id": f"c{self._candidate_index}",
            "candidate_type": candidate_type,
            "payload": payload,
            "confidence": _bounded(confidence),
            "uncertainty_type": uncertainty_type,
            "evidence_window": {"start": evidence_span[0], "end": evidence_span[1]},
            "prompt_atoms": prompt_atoms,
        }
        self.candidates.append(candidate)
        return candidate["candidate_id"]


def _candidate_uncertainty(group: str, confidence: float) -> str:
    if group in {"other_quality_abnormal", "no_quality_abnormal"}:
        return "schema_conflict"
    if confidence >= 0.8:
        return "high_confidence"
    if confidence < 0.5:
        return "low_confidence"
    return "evidence_missing"


def build_structured_record(
    row: dict[str, str],
    feature_columns: list[str],
    feature_to_group: dict[str, str],
    *,
    top_features: int,
) -> dict[str, Any]:
    raw_id = _clean(row.get("record_id")) or _clean(row.get("记录识别码")) or hashlib.sha1(
        json.dumps(row, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:12]
    record_id = f"baosteel-structured-{raw_id}"
    builder = TextRecordBuilder(record_id=record_id)

    process_time = _clean(row.get("process_time"))
    cast_id = _clean(row.get("连铸处理号"))
    material_id = _clean(row.get("材料跟踪号"))
    trace_id = _clean(row.get("记录识别码"))
    group = _clean(row.get("quality_abnormal_group")) or "no_quality_abnormal"
    group_cn = _clean(row.get("quality_abnormal_group_cn")) or QUALITY_GROUP_CN.get(group, group)
    groups_text = _clean(row.get("quality_abnormal_groups")) or group
    codes = _clean(row.get("quality_abnormal_codes")) or "未提供"
    quality_label = "质量异常" if _clean(row.get("quality_abnormal_label")) == "1" else "未标记质量异常"
    label_confidence = 0.78 if group not in {"other_quality_abnormal", "no_quality_abnormal"} else 0.58

    builder.append(f"宝钢质量追溯记录 {raw_id}：")
    if process_time:
        builder.append("时间 ")
        builder.add_entity(process_time, "TimeExpression", confidence=0.95, normalization_id=process_time)
        builder.append("，")
    if cast_id:
        builder.append("连铸处理号 ")
        builder.add_entity(cast_id, "ProcessBatch", confidence=0.9, normalization_id=cast_id)
        builder.append("，")
    if material_id:
        builder.append("材料跟踪号 ")
        builder.add_entity(material_id, "MaterialBatch", confidence=0.9, normalization_id=material_id)
        builder.append("，")
    builder.append("质量标签为 ")
    quality_eid = builder.add_entity(quality_label, "QualityIndicator", confidence=label_confidence, normalization_id=quality_label)
    builder.append("，主异常组为 ")
    group_eid = builder.add_entity(group_cn, "QualityDefect", confidence=label_confidence, normalization_id=group)
    builder.append(f"（{group}），异常代码为 ")
    code_eid = builder.add_entity(codes, "QualityIndicator", confidence=0.6, normalization_id=codes)
    builder.append(f"，多标签异常组为 {groups_text}。")

    feature_rows = select_features(row, feature_columns, feature_to_group, top_features=top_features)
    feature_eids: list[tuple[str, dict[str, str]]] = []
    feature_start = len(builder.text)
    builder.append("关键过程特征包括：")
    for idx, feature in enumerate(feature_rows):
        if idx:
            builder.append("；")
        surface = f"{feature['name']}={feature['value']}"
        eid = builder.add_entity(
            surface,
            "ProcessParameter",
            confidence=0.68,
            normalization_id=feature["name"],
            extra={"feature_group": feature["group"], "feature_value": feature["value"]},
        )
        feature_eids.append((eid, feature))
    if not feature_rows:
        builder.append("未选出可用过程特征")
    builder.append("。按弱标注规则，上述过程参数与主异常组存在关联，用于后续 PLM 候选生成和 LLM 证据约束。")
    feature_end = len(builder.text)

    full_span = (0, len(builder.text))
    builder.add_relation("classified_as", quality_eid, group_eid, full_span, confidence=label_confidence)
    builder.add_relation("associated_with", code_eid, group_eid, full_span, confidence=0.55)
    builder.add_candidate(
        "entity",
        {"entity_id": group_eid, "text": group_cn, "type": "QualityDefect", "normalization_id": group},
        full_span,
        confidence=label_confidence,
        uncertainty_type=_candidate_uncertainty(group, label_confidence),
        prompt_atoms=["schema_constraint", "entity_boundary", "evidence_span"],
    )
    for eid, feature in feature_eids:
        relation_id = builder.add_relation(
            "associated_with",
            eid,
            group_eid,
            (feature_start, feature_end),
            confidence=0.62,
            extra={"feature_group": feature["group"]},
        )
        builder.add_candidate(
            "relation",
            {
                "relation_id": relation_id,
                "head": eid,
                "tail": group_eid,
                "relation_type": "associated_with",
                "feature_group": feature["group"],
            },
            (feature_start, feature_end),
            confidence=0.62,
            uncertainty_type=_candidate_uncertainty(group, 0.62),
            prompt_atoms=["relation_direction", "schema_constraint", "hallucination_guard", "evidence_span"],
        )

    split_group = cast_id or trace_id or raw_id
    return {
        "record_id": record_id,
        "domain": "baosteel_quality_traceability",
        "language": "zh",
        "text": builder.text,
        "source": {
            "source_id": raw_id,
            "source_type": "baosteel_processed_traceability_row",
            "process_stage": QUALITY_GROUP_STAGE.get(group, "quality_traceability"),
            "timestamp": process_time or None,
            "split_group": split_group,
            "original_record_id": raw_id,
            "cast_id": cast_id or None,
            "material_tracking_id": material_id or None,
            "trace_record_id": trace_id or None,
            "quality_abnormal_group": group,
            "quality_abnormal_groups": groups_text,
            "selected_features": feature_rows,
        },
        "task_scope": ["ner", "re", "plm_candidate", "llm_adjudication", "active_learning"],
        "annotation_status": "weak_labeled",
        "annotations": {"entities": builder.entities, "relations": builder.relations},
        "plm_candidates": builder.candidates,
        "llm_adjudications": [],
        "quality": {
            "reviewer": None,
            "review_status": "unreviewed",
            "notes": "Derived from processed Baosteel quality traceability table; weak labels require expert review before gold reporting.",
        },
    }


def _event_confidence(event: dict[str, Any]) -> float:
    risk = (event.get("risk_warning") or {}).get("risk_probability")
    cls = (event.get("abnormal_identification") or {}).get("class_confidence")
    values = [x for x in (_safe_float(risk), _safe_float(cls)) if x is not None]
    if not values:
        return 0.65
    return sum(values) / len(values)


def _path_confidence(path: dict[str, Any], event_conf: float) -> float:
    score = _safe_float(path.get("path_score"))
    if score is None:
        return event_conf
    return _bounded((score + event_conf) / 2)


def build_event_record(event: dict[str, Any]) -> dict[str, Any]:
    event_id = _clean(event.get("event_id")) or hashlib.sha1(json.dumps(event, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    sample_id = _clean(event.get("sample_id")) or event_id
    record_id = f"baosteel-event-{sample_id}"
    builder = TextRecordBuilder(record_id=record_id)
    event_conf = _event_confidence(event)

    risk = event.get("risk_warning") or {}
    abnormal = event.get("abnormal_identification") or {}
    traceability = event.get("traceability") or {}
    recommendation = event.get("recommendation") or {}
    primary_class = _clean(abnormal.get("primary_abnormal_class")) or "unknown_quality_class"
    true_class = _clean(abnormal.get("true_abnormal_class")) or primary_class
    primary_cn = QUALITY_GROUP_CN.get(primary_class, primary_class)
    true_cn = QUALITY_GROUP_CN.get(true_class, true_class)

    builder.append(f"宝钢三层质量事件 {event_id}（样本 {sample_id}）：")
    stage = _clean(event.get("precursor_stage")) or "unknown"
    builder.append("预警阶段 ")
    stage_eid = builder.add_entity(stage, "ProcessStage", confidence=0.85, normalization_id=stage)
    builder.append("，风险等级 ")
    risk_eid = builder.add_entity(_clean(risk.get("risk_level")) or "unknown", "QualityIndicator", confidence=event_conf)
    builder.append(f"，风险概率 {_format_value(risk.get('risk_probability')) or '未提供'}，边界状态 ")
    boundary_eid = builder.add_entity(_clean(risk.get("boundary_status")) or "unknown", "EquipmentState", confidence=event_conf)
    builder.append("。异常识别结果为 ")
    primary_eid = builder.add_entity(primary_cn, "QualityDefect", confidence=event_conf, normalization_id=primary_class)
    builder.append(f"（{primary_class}），真实异常类别为 ")
    true_eid = builder.add_entity(true_cn, "QualityDefect", confidence=event_conf, normalization_id=true_class)
    builder.append(f"（{true_class}），分类置信度 {_format_value(abnormal.get('class_confidence')) or '未提供'}。")

    builder.add_relation("classified_as", risk_eid, primary_eid, (0, len(builder.text)), confidence=event_conf)
    builder.add_relation("associated_with", boundary_eid, risk_eid, (0, len(builder.text)), confidence=event_conf)
    builder.add_relation("classified_as", primary_eid, true_eid, (0, len(builder.text)), confidence=event_conf)

    top_vars = risk.get("top_risk_variables") or []
    top_var_eids: list[str] = []
    if top_vars:
        risk_start = len(builder.text)
        builder.append("主要风险变量包括：")
        for idx, var in enumerate(top_vars[:5]):
            if idx:
                builder.append("；")
            feature = _clean(var.get("feature")) or f"risk_feature_{idx + 1}"
            value = _format_value(var.get("value")) or "missing"
            eid = builder.add_entity(
                f"{feature}={value}",
                "ProcessParameter",
                confidence=_bounded(_safe_float(var.get("importance")), default=0.55),
                normalization_id=feature,
                extra={"importance": _safe_float(var.get("importance")), "risk_score": _safe_float(var.get("score"))},
            )
            top_var_eids.append(eid)
        builder.append("。")
        risk_end = len(builder.text)
        for eid in top_var_eids:
            rel_id = builder.add_relation("risk_evidence", eid, risk_eid, (risk_start, risk_end), confidence=event_conf)
            builder.add_candidate(
                "relation",
                {"relation_id": rel_id, "head": eid, "tail": risk_eid, "relation_type": "risk_evidence"},
                (risk_start, risk_end),
                confidence=event_conf,
                uncertainty_type="high_confidence" if event_conf >= 0.8 else "low_confidence",
                prompt_atoms=["evidence_span", "relation_direction", "hallucination_guard"],
            )

    for path_idx, path in enumerate((traceability.get("top_k_paths") or [])[:3], start=1):
        path_start = len(builder.text)
        builder.append(f"追溯路径{path_idx}：")
        node_ids: dict[str, str] = {}
        nodes = path.get("nodes") or []
        if nodes:
            for idx, node in enumerate(nodes):
                if idx:
                    builder.append(" -> ")
                label = _clean(node.get("label")) or _clean(node.get("id")) or f"path_node_{idx + 1}"
                layer = _clean(node.get("layer")) or "unknown_layer"
                ent_type = LAYER_ENTITY_TYPES.get(layer, "EquipmentState")
                node_key = f"{path_idx}:{idx}:{layer}:{label}"
                node_ids[node_key] = builder.add_entity(
                    label,
                    ent_type,
                    confidence=_path_confidence(path, event_conf),
                    normalization_id=_clean(node.get("id")) or label,
                    extra={"path_layer": layer, "path_id": _clean(path.get("path_id")) or None},
                )
        else:
            labels = [
                _clean(path.get("feature")),
                _clean(path.get("variable_group")),
                _clean(path.get("equipment_zone")),
                _clean(path.get("process_state")),
                _clean(path.get("defect_mechanism")),
                _clean(path.get("event_target")),
            ]
            for idx, label in enumerate([x for x in labels if x]):
                if idx:
                    builder.append(" -> ")
                node_key = f"{path_idx}:{idx}:fallback:{label}"
                node_ids[node_key] = builder.add_entity(label, "EquipmentState", confidence=_path_confidence(path, event_conf))
        builder.append(f"，路径分数 {_format_value(path.get('path_score')) or '未提供'}。")
        path_end = len(builder.text)

        ordered_ids = list(node_ids.values())
        for head, tail in zip(ordered_ids, ordered_ids[1:]):
            rel_id = builder.add_relation(
                "hierarchical_trace",
                head,
                tail,
                (path_start, path_end),
                confidence=_path_confidence(path, event_conf),
                extra={
                    "path_id": _clean(path.get("path_id")) or None,
                    "path_template_id": _clean(path.get("path_template_id")) or None,
                    "feature_value": _safe_float(path.get("feature_value")),
                },
            )
            builder.add_candidate(
                "relation",
                {"relation_id": rel_id, "head": head, "tail": tail, "relation_type": "hierarchical_trace"},
                (path_start, path_end),
                confidence=_path_confidence(path, event_conf),
                uncertainty_type="high_confidence" if _path_confidence(path, event_conf) >= 0.8 else "low_confidence",
                prompt_atoms=["path_consistency", "relation_direction", "evidence_span"],
            )

    checks = [_clean(x) for x in recommendation.get("recommended_checks") or [] if _clean(x)]
    if checks:
        check_start = len(builder.text)
        builder.append("建议检查：")
        for idx, check in enumerate(checks[:3]):
            if idx:
                builder.append("；")
            check_eid = builder.add_entity(check, "Operation", confidence=0.62, normalization_id=check)
            builder.add_relation("recommended_check", check_eid, primary_eid, (check_start, len(builder.text)), confidence=0.62)
        builder.append("。")

    adjustments = [_clean(x) for x in recommendation.get("recommended_adjustments") or [] if _clean(x)]
    if adjustments:
        adjust_start = len(builder.text)
        builder.append("建议调整：")
        for idx, adjustment in enumerate(adjustments[:3]):
            if idx:
                builder.append("；")
            adjustment_eid = builder.add_entity(adjustment, "Operation", confidence=0.62, normalization_id=adjustment)
            builder.add_relation("recommended_adjustment", adjustment_eid, primary_eid, (adjust_start, len(builder.text)), confidence=0.62)
        builder.append("。")

    builder.add_candidate(
        "entity",
        {"entity_id": primary_eid, "text": primary_cn, "type": "QualityDefect", "normalization_id": primary_class},
        (0, len(builder.text)),
        confidence=event_conf,
        uncertainty_type="high_confidence" if event_conf >= 0.8 else "low_confidence",
        prompt_atoms=["schema_constraint", "entity_boundary", "evidence_span"],
    )
    builder.add_candidate(
        "evidence_window",
        {
            "event_id": event_id,
            "sample_id": sample_id,
            "risk_level": _clean(risk.get("risk_level")) or "unknown",
            "primary_abnormal_class": primary_class,
        },
        (0, len(builder.text)),
        confidence=event_conf,
        uncertainty_type="high_confidence" if event_conf >= 0.8 else "low_confidence",
        prompt_atoms=["evidence_span", "path_consistency", "hallucination_guard"],
    )

    return {
        "record_id": record_id,
        "domain": "baosteel_quality_traceability",
        "language": "mixed",
        "text": builder.text,
        "source": {
            "source_id": sample_id,
            "source_type": "baosteel_three_level_event_explanation",
            "process_stage": stage,
            "timestamp": None,
            "split_group": event_id,
            "event_id": event_id,
            "sample_id": sample_id,
            "primary_abnormal_class": primary_class,
            "true_abnormal_class": true_class,
            "lead_horizon_min": event.get("lead_horizon_min"),
        },
        "task_scope": ["ner", "re", "plm_candidate", "llm_adjudication", "active_learning"],
        "annotation_status": "weak_labeled",
        "annotations": {"entities": builder.entities, "relations": builder.relations},
        "plm_candidates": builder.candidates,
        "llm_adjudications": [],
        "quality": {
            "reviewer": None,
            "review_status": "unreviewed",
            "notes": "Derived from Baosteel three-level warning-identification-traceability output; path labels are model/expert-template weak supervision.",
        },
    }


def iter_structured_records(
    quality_dir: Path,
    *,
    top_features: int,
    max_records: int,
) -> Iterator[dict[str, Any]]:
    xy_path = quality_dir / "xy_quality_traceability.csv"
    if not xy_path.exists():
        raise FileNotFoundError(f"Missing Baosteel traceability table: {xy_path}")
    _, feature_to_group = load_feature_groups(quality_dir / "feature_groups.json")
    with xy_path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        feature_columns = [c for c in (reader.fieldnames or []) if c not in META_COLUMNS and c not in Y_COLUMNS]
        for idx, row in enumerate(reader):
            if max_records and idx >= max_records:
                break
            yield build_structured_record(row, feature_columns, feature_to_group, top_features=top_features)


def iter_event_records(three_level_dir: Path, *, max_records: int) -> Iterator[dict[str, Any]]:
    event_path = three_level_dir / "event_explanations.jsonl"
    if not event_path.exists():
        return
    with event_path.open("r", encoding="utf-8-sig") as fh:
        for idx, line in enumerate(fh):
            if max_records and idx >= max_records:
                break
            line = line.strip()
            if not line:
                continue
            yield build_event_record(json.loads(line))


def _bio_labels(text: str, entities: Iterable[dict[str, Any]]) -> list[str]:
    labels = ["O"] * len(text)
    for entity in entities:
        start = int(entity["start"])
        end = int(entity["end"])
        typ = str(entity["type"])
        if not (0 <= start < end <= len(text)):
            continue
        labels[start] = f"B-{typ}"
        for pos in range(start + 1, end):
            labels[pos] = f"I-{typ}"
    return labels


def to_plm_minimal(record: dict[str, Any]) -> dict[str, Any]:
    text = record["text"]
    entities = [
        {
            "text": ent["text"],
            "type": ent["type"],
            "start": ent["start"],
            "end": ent["end"],
            "source": ent.get("source"),
            "confidence": ent.get("confidence"),
        }
        for ent in record["annotations"]["entities"]
    ]
    by_id = {ent["entity_id"]: ent for ent in record["annotations"]["entities"]}
    entity_pairs: list[list[int]] = []
    relation_ids: list[int] = []
    relation_types: list[str] = []
    for relation in record["annotations"]["relations"]:
        head = by_id.get(relation["head"])
        tail = by_id.get(relation["tail"])
        if not head or not tail:
            continue
        relation_type = str(relation["type"])
        entity_pairs.append([int(head["start"]), int(head["end"]), int(tail["start"]), int(tail["end"])])
        relation_ids.append(RELATION_TYPE_IDS.get(relation_type, len(RELATION_TYPE_IDS) + 1))
        relation_types.append(relation_type)
    return {
        "id": record["record_id"],
        "text": text,
        "ner": {"text": text, "labels": _bio_labels(text, entities), "entities": entities},
        "re": {
            "text": text,
            "entity_pairs": entity_pairs,
            "relations": relation_ids,
            "relation_types": relation_types,
            "dependency_graph": {"nodes": [], "edges": []},
        },
        "source": record["source"],
        "annotation_status": record["annotation_status"],
    }


class JsonArrayWriter:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fh: TextIO | None = None
        self.count = 0

    def __enter__(self) -> "JsonArrayWriter":
        self.fh = self.path.open("w", encoding="utf-8")
        self.fh.write("[\n")
        return self

    def write(self, item: dict[str, Any]) -> None:
        if self.fh is None:
            raise RuntimeError("JsonArrayWriter is not open")
        if self.count:
            self.fh.write(",\n")
        self.fh.write(json.dumps(item, ensure_ascii=False))
        self.count += 1

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self.fh is not None:
            self.fh.write("\n]\n")
            self.fh.close()


def _write_jsonl(fh: TextIO, record: dict[str, Any]) -> None:
    fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def build_dataset(
    *,
    quality_dir: Path = DEFAULT_QUALITY_DIR,
    three_level_dir: Path = DEFAULT_THREE_LEVEL_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    top_features: int = 8,
    max_structured_records: int = 0,
    max_event_records: int = 0,
    preview_records: int = 20,
    split_seed: int = 2026,
    train_ratio: float = 0.8,
    dev_ratio: float = 0.1,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    split_dir = output_dir / "splits"
    split_dir.mkdir(parents=True, exist_ok=True)
    plm_dir = output_dir / "plm"
    plm_dir.mkdir(parents=True, exist_ok=True)

    records_path = output_dir / "records.jsonl"
    split_paths = {
        "train": split_dir / "train.jsonl",
        "dev": split_dir / "dev.jsonl",
        "test": split_dir / "test.jsonl",
    }
    plm_path = plm_dir / "baosteel_plm_train_pool.json"
    relation_map_path = plm_dir / "relation_type_id_map.json"

    counters: Counter[str] = Counter()
    domain_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    label_counts: Counter[str] = Counter()
    split_counts: Counter[str] = Counter()
    entity_counts: Counter[str] = Counter()
    relation_counts: Counter[str] = Counter()
    preview: list[dict[str, Any]] = []

    record_iters = [
        iter_structured_records(quality_dir, top_features=top_features, max_records=max_structured_records),
        iter_event_records(three_level_dir, max_records=max_event_records),
    ]

    with records_path.open("w", encoding="utf-8") as records_fh, JsonArrayWriter(plm_path) as plm_writer:
        split_fhs = {name: path.open("w", encoding="utf-8") for name, path in split_paths.items()}
        try:
            for record_iter in record_iters:
                for record in record_iter:
                    source = record.get("source") or {}
                    split_group = _clean(source.get("split_group")) or record["record_id"]
                    split = _hash_split(split_group, split_seed, train_ratio, dev_ratio)
                    _write_jsonl(records_fh, record)
                    _write_jsonl(split_fhs[split], record)
                    plm_writer.write(to_plm_minimal(record))

                    counters["records"] += 1
                    domain_counts[record["domain"]] += 1
                    source_counts[source.get("source_type", "unknown")] += 1
                    split_counts[split] += 1
                    label = source.get("quality_abnormal_group") or source.get("primary_abnormal_class") or "unknown"
                    label_counts[str(label)] += 1
                    for entity in record["annotations"]["entities"]:
                        entity_counts[str(entity["type"])] += 1
                    for relation in record["annotations"]["relations"]:
                        relation_counts[str(relation["type"])] += 1
                    if len(preview) < preview_records:
                        preview.append(record)
        finally:
            for fh in split_fhs.values():
                fh.close()

    relation_map_path.write_text(json.dumps(RELATION_TYPE_IDS, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "preview.json").write_text(json.dumps(preview, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {
        "dataset_name": "baosteel_knowledge_extraction",
        "description": "Knowledge-extraction dataset derived from processed Baosteel quality traceability tables and three-level system event explanations.",
        "annotation_status": "weak_labeled",
        "records": counters["records"],
        "source_paths": {
            "quality_traceability_dataset": str(Path(quality_dir).resolve()),
            "three_level_system": str(Path(three_level_dir).resolve()),
        },
        "outputs": {
            "records_jsonl": str(records_path),
            "preview_json": str(output_dir / "preview.json"),
            "plm_train_pool_json": str(plm_path),
            "relation_type_id_map": str(relation_map_path),
            "splits": {name: str(path) for name, path in split_paths.items()},
        },
        "generation": {
            "top_features_per_structured_record": top_features,
            "max_structured_records": max_structured_records,
            "max_event_records": max_event_records,
            "split_seed": split_seed,
            "train_ratio": train_ratio,
            "dev_ratio": dev_ratio,
            "test_ratio": max(0.0, 1.0 - train_ratio - dev_ratio),
        },
        "counts": {
            "domains": dict(domain_counts),
            "source_types": dict(source_counts),
            "splits": dict(split_counts),
            "labels": dict(label_counts),
            "entity_types": dict(entity_counts),
            "relation_types": dict(relation_counts),
        },
        "caveats": [
            "Records are weakly labeled from processed structured data and model/path outputs, not manually verified gold NER/RE labels.",
            "Use the split files for prompt tuning and PLM training to avoid cast/event leakage.",
            "Promote records to gold_labeled only after expert review.",
        ],
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build full Baosteel knowledge-extraction dataset from processed exports.")
    parser.add_argument("--quality-dir", type=Path, default=DEFAULT_QUALITY_DIR)
    parser.add_argument("--three-level-dir", type=Path, default=DEFAULT_THREE_LEVEL_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--top-features", type=int, default=8)
    parser.add_argument("--max-structured-records", type=int, default=0, help="0 means use all rows.")
    parser.add_argument("--max-event-records", type=int, default=0, help="0 means use all event explanations.")
    parser.add_argument("--preview-records", type=int, default=20)
    parser.add_argument("--split-seed", type=int, default=2026)
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--dev-ratio", type=float, default=0.1)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = build_dataset(
        quality_dir=args.quality_dir,
        three_level_dir=args.three_level_dir,
        output_dir=args.output_dir,
        top_features=args.top_features,
        max_structured_records=args.max_structured_records,
        max_event_records=args.max_event_records,
        preview_records=args.preview_records,
        split_seed=args.split_seed,
        train_ratio=args.train_ratio,
        dev_ratio=args.dev_ratio,
    )
    print(json.dumps({"records": manifest["records"], "outputs": manifest["outputs"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
