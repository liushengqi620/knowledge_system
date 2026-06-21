from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import parse_qs, unquote, urlparse

try:
    from config import CONFIG
    from llm_client import llm_configured, post_chat_completions
except Exception:  # pragma: no cover - optional runtime dependency guard
    CONFIG = {}

    def llm_configured(_api_key: str | None) -> bool:
        return False

    def post_chat_completions(**_kwargs: Any) -> str:
        raise RuntimeError("LLM client is unavailable")


PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_SOURCE_DIR = PROJECT_ROOT / "knowledge_exports" / "baosteel_three_level_system_v1"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "knowledge_exports" / "steel_realtime_system_v1"
UI_ASSET_DIR = PROJECT_ROOT / "assets" / "ui"
STRUCTURED_DATA_DIR = PROJECT_ROOT / "knowledge_exports" / "continuous_casting_grouped_quality_code"
STRUCTURED_CSV_PATH = STRUCTURED_DATA_DIR / "continuous_casting_all.csv"
MODEL_READY_CSV_PATH = STRUCTURED_DATA_DIR / "categories" / "model_ready.csv"
STRUCTURED_SUMMARY_PATH = STRUCTURED_DATA_DIR / "continuous_casting_summary.json"
TRACEABILITY_DATASET_DIR = PROJECT_ROOT / "knowledge_exports" / "quality_traceability_dataset_quality_code"
TRACEABILITY_DATASET_SUMMARY_PATH = TRACEABILITY_DATASET_DIR / "dataset_summary.json"
QUALITY_MODELING_DIR = PROJECT_ROOT / "knowledge_exports" / "quality_modeling_quality_code"
MODEL_EVIDENCE_BUNDLE_PATH = QUALITY_MODELING_DIR / "model_evidence_bundle.json"
CASCADE_PREDICTIONS_PATH = QUALITY_MODELING_DIR / "cascade_test_predictions.csv"
TRACEABILITY_CANDIDATE_EVIDENCE_PATH = QUALITY_MODELING_DIR / "traceability_candidate_evidence_test.csv"
PRODUCTION_PROFILE_FILENAME = "production_data_profile.json"
PRODUCTION_WINDOWS_FILENAME = "production_event_windows_preview.json"


def _fs_path(path: str | Path) -> Path:
    """Return a filesystem path that survives deep Windows recovery folders."""
    p = Path(path)
    if os.name != "nt":
        return p
    text = str(p)
    if text.startswith("\\\\?\\"):
        return p
    if not p.is_absolute():
        p = p.resolve()
        text = str(p)
    if len(text) >= 200:
        return Path("\\\\?\\" + text)
    return p


PROCESS_STEPS = [
    {"id": "roughing", "name": "粗炼", "scope": "context"},
    {"id": "refining", "name": "精炼", "scope": "context"},
    {"id": "tundish", "name": "中间包", "scope": "model"},
    {"id": "mold", "name": "结晶器", "scope": "model"},
    {"id": "flow_control", "name": "流量控制", "scope": "model"},
    {"id": "heat_transfer", "name": "传热/冷却", "scope": "model"},
    {"id": "quality", "name": "品质检测", "scope": "model"},
]


MECHANISM_TO_STEP = {
    "temperature_flux": "tundish",
    "mold_level_slag_risk": "mold",
    "speed_stopper_flow": "flow_control",
    "process_fluctuation": "tundish",
    "heat_transfer_imbalance": "heat_transfer",
    "transition_tundish": "tundish",
    "other_quality_abnormal": "quality",
}


DISPLAY_LABELS = {
    "temperature_flux": "温度/保护渣异常",
    "mold_level_slag_risk": "液面/卷渣风险",
    "speed_stopper_flow": "拉速/塞棒/流量异常",
    "process_fluctuation": "过程参数波动",
    "heat_transfer_imbalance": "传热不均",
    "transition_tundish": "过渡/中间包状态",
    "other_quality_abnormal": "其他质量异常",
}


PROCESS_LABELS = {str(step["id"]): str(step["name"]) for step in PROCESS_STEPS}


PROCESS_FLOW_EDGES = [
    ("roughing", "refining"),
    ("refining", "tundish"),
    ("tundish", "mold"),
    ("mold", "flow_control"),
    ("mold", "heat_transfer"),
    ("flow_control", "quality"),
    ("heat_transfer", "quality"),
]


MECHANISM_ALIASES = {
    "temperature_flux": ["temperature_flux", "温度/保护渣异常", "温度异常", "保护渣异常", "中包温度", "过热度", "liquidus", "superheat", "flux"],
    "mold_level_slag_risk": ["mold_level_slag_risk", "液面/卷渣风险", "液面波动", "卷渣", "结晶器液位", "mold level", "slag"],
    "speed_stopper_flow": ["speed_stopper_flow", "拉速/塞棒/流量异常", "拉速异常", "塞棒异常", "流量异常", "上水口", "nozzle", "stopper", "flow"],
    "process_fluctuation": ["process_fluctuation", "过程参数波动", "过程波动", "参数波动", "process fluctuation"],
    "heat_transfer_imbalance": ["heat_transfer_imbalance", "传热不均", "冷却不均", "热交换异常", "传热异常", "heat transfer", "heat exchange"],
    "transition_tundish": ["transition_tundish", "过渡/中间包状态", "中间包过渡", "换包过渡", "交接部", "transition", "tundish transition"],
    "other_quality_abnormal": ["other_quality_abnormal", "其他质量异常", "质量异常", "品质异常", "quality abnormal"],
}


PROCESS_ALIASES = {
    "roughing": ["roughing", "粗炼", "铁水预处理", "转炉前"],
    "refining": ["refining", "精炼", "lf", "rh", "二次精炼"],
    "tundish": ["tundish", "中间包", "中包", "td", "transition_tundish", "过渡段"],
    "mold": ["mold", "结晶器", "铸模", "结晶器液位", "保护渣"],
    "flow_control": ["flow_control", "流量控制", "拉速", "塞棒", "上水口", "水口", "nozzle", "stopper", "casting speed"],
    "heat_transfer": ["heat_transfer", "mold_heat_transfer", "传热", "冷却", "传热/冷却", "二冷", "热交换", "heat exchange"],
    "quality": ["quality", "品质检测", "质量检测", "质检", "缺陷", "quality"],
}


VARIABLE_GROUP_ALIASES = {
    "temperature": ["temperature", "temp", "温度", "温度制度", "中包温度", "td_avg_temp", "liquidus_temp", "superheat"],
    "flux": ["flux", "cover_flux", "保护渣", "保护渣状态"],
    "mold_level": ["mold_level", "液面", "液位", "结晶器液位", "mold level"],
    "nozzle_flow": ["nozzle_flow", "stopper_flow", "流量", "上水口流量", "塞棒流量", "水口流量", "nozzle flow"],
    "tundish_weight": ["tundish_weight", "中间包吨位", "中包吨位", "钢水量", "大包注入结束时钢水量", "吨位"],
    "sequence_transition": ["sequence_transition", "transition", "过渡段", "交接部", "换包", "过渡序列"],
    "heat_transfer": ["heat_transfer", "heat_exchange", "热交换", "传热", "冷却", "东西差异"],
    "casting_speed": ["cast_speed", "casting_speed", "拉速", "铸速"],
    "ems_taper_oscillation": ["ems_taper_oscillation", "taper", "oscillation", "ems", "结晶器锥度", "振动", "电磁搅拌", "锥度振动"],
}


VARIABLE_GROUP_LABELS = {
    "temperature": "温度制度",
    "flux": "保护渣状态",
    "mold_level": "结晶器液位",
    "nozzle_flow": "水口/塞棒流量",
    "tundish_weight": "中间包吨位",
    "sequence_transition": "过渡段序列",
    "heat_transfer": "传热/冷却",
    "casting_speed": "拉速/铸速",
    "ems_taper_oscillation": "结晶器锥度/振动",
}


FEATURE_BASE_ALIASES = {
    "transition_start_position": ["交接部开始位置", "transition_start_position", "transition start"],
    "nozzle_flow_fluctuation": ["上水口流量波动", "nozzle_flow_fluctuation", "nozzle flow fluctuation"],
    "heat_exchange_mean": ["heat_exchange_mean", "热交换平均", "热交换平均西", "热交换平均东", "heat exchange mean"],
    "heat_exchange_ew_diff": ["heat_exchange_ew_diff", "热交换东西差异", "热交换ew差异", "heat exchange ew diff"],
    "tundish_weight_min": ["中间包吨位最小值", "tundish_weight_min", "td_weight_min"],
    "ladle_end_weight": ["大包注入结束时钢水量", "ladle_end_weight", "steel_weight_end"],
    "td_avg_temp": ["td_avg_temp", "中包平均温度", "中间包平均温度"],
    "liquidus_temp": ["liquidus_temp", "液相线温度"],
    "superheat": ["superheat", "过热度"],
    "cover_flux_1": ["cover_flux_1", "保护渣1", "保护渣"],
    "mold_level_range": ["mold_level_range", "液面波动", "结晶器液位极差", "结晶器液位波动"],
    "cast_speed_mean": ["cast_speed_mean", "拉速平均", "铸速平均"],
    "mold_taper_north_max": ["结晶器锥度北最大值", "mold_taper_north_max", "taper_north_max"],
    "mold_taper_south_max": ["结晶器锥度南最大值", "mold_taper_south_max", "taper_south_max"],
    "mold_oscillation": ["结晶器振动", "mold_oscillation", "oscillation"],
}


FEATURE_BASE_LABELS = {
    "transition_start_position": "交接部开始位置",
    "nozzle_flow_fluctuation": "上水口流量波动",
    "heat_exchange_mean": "热交换平均",
    "heat_exchange_ew_diff": "热交换东西差异",
    "tundish_weight_min": "中间包吨位最小值",
    "ladle_end_weight": "大包注入结束时钢水量",
    "td_avg_temp": "中包平均温度",
    "liquidus_temp": "液相线温度",
    "superheat": "过热度",
    "cover_flux_1": "保护渣1",
    "mold_level_range": "结晶器液位极差",
    "cast_speed_mean": "拉速平均",
    "mold_taper_north_max": "结晶器北侧锥度最大值",
    "mold_taper_south_max": "结晶器南侧锥度最大值",
    "mold_oscillation": "结晶器振动",
}


FEATURE_STAT_LABELS = {
    "mean": "平均值",
    "std": "波动",
    "trend": "趋势",
    "last": "最新值",
    "max": "最大值",
    "min": "最小值",
}


UNIT_LABELS = {
    "mm": "毫米",
    "t": "吨",
    "l/min": "升/分钟",
    "℃": "摄氏度",
    "c": "摄氏度",
    "min": "分钟",
    "s": "秒",
}


MODEL_FEATURE_MAP = {
    "TD_weight_mean": {"label": "中间包吨位平均值", "variable_group": "tundish_weight", "process_step": "tundish", "mechanism": "process_fluctuation", "unit": "吨"},
    "TD_weight_range": {"label": "中间包吨位波动", "variable_group": "tundish_weight", "process_step": "tundish", "mechanism": "process_fluctuation", "unit": "吨"},
    "TD_avg_temp": {"label": "中包平均温度", "variable_group": "temperature", "process_step": "tundish", "mechanism": "temperature_flux", "unit": "摄氏度"},
    "liquidus_temp": {"label": "液相线温度", "variable_group": "temperature", "process_step": "tundish", "mechanism": "temperature_flux", "unit": "摄氏度"},
    "superheat": {"label": "过热度", "variable_group": "temperature", "process_step": "tundish", "mechanism": "temperature_flux", "unit": "摄氏度"},
    "cast_speed_mean": {"label": "拉速平均值", "variable_group": "casting_speed", "process_step": "flow_control", "mechanism": "speed_stopper_flow", "unit": "米/分钟"},
    "cast_speed_range": {"label": "拉速波动", "variable_group": "casting_speed", "process_step": "flow_control", "mechanism": "speed_stopper_flow", "unit": "米/分钟"},
    "cover_flux_1": {"label": "保护渣1使用量", "variable_group": "flux", "process_step": "mold", "mechanism": "temperature_flux", "unit": "ppm"},
    "cover_flux_2": {"label": "保护渣2使用量", "variable_group": "flux", "process_step": "mold", "mechanism": "temperature_flux", "unit": "ppm"},
    "cover_flux_total": {"label": "保护渣总量", "variable_group": "flux", "process_step": "mold", "mechanism": "temperature_flux", "unit": "ppm"},
    "cover_flux_ratio": {"label": "保护渣配比", "variable_group": "flux", "process_step": "mold", "mechanism": "temperature_flux", "unit": "比例"},
    "mold_level_range": {"label": "结晶器液位波动", "variable_group": "mold_level", "process_step": "mold", "mechanism": "mold_level_slag_risk", "unit": "毫米"},
    "mold_level_mean": {"label": "结晶器液位均值", "variable_group": "mold_level", "process_step": "mold", "mechanism": "mold_level_slag_risk", "unit": "毫米"},
    "mold_level_ge7": {"label": "液位波动大于等于7毫米次数", "variable_group": "mold_level", "process_step": "mold", "mechanism": "mold_level_slag_risk", "unit": "次数"},
    "mold_level_ge10": {"label": "液位波动大于等于10毫米次数", "variable_group": "mold_level", "process_step": "mold", "mechanism": "mold_level_slag_risk", "unit": "次数"},
    "tundish_sequence_count": {"label": "中间包连浇炉数", "variable_group": "sequence_transition", "process_step": "tundish", "mechanism": "transition_tundish", "unit": "炉"},
    "heat_exchange_mean": {"label": "结晶器热交换平均", "variable_group": "heat_transfer", "process_step": "heat_transfer", "mechanism": "heat_transfer_imbalance", "unit": "摄氏度"},
    "heat_exchange_ew_diff": {"label": "东西拔热量差", "variable_group": "heat_transfer", "process_step": "heat_transfer", "mechanism": "heat_transfer_imbalance", "unit": "摄氏度"},
    "heat_exchange_ns_diff": {"label": "南北拔热量差", "variable_group": "heat_transfer", "process_step": "heat_transfer", "mechanism": "heat_transfer_imbalance", "unit": "摄氏度"},
}


QUALITY_GROUP_COLUMNS = [
    ("quality_group_temperature_flux", "temperature_flux"),
    ("quality_group_mold_level_slag_risk", "mold_level_slag_risk"),
    ("quality_group_speed_stopper_flow", "speed_stopper_flow"),
    ("quality_group_heat_transfer_imbalance", "heat_transfer_imbalance"),
    ("quality_group_process_fluctuation", "process_fluctuation"),
    ("quality_group_transition_tundish", "transition_tundish"),
    ("quality_group_other_quality_abnormal", "other_quality_abnormal"),
]


def _abnormal_group_keys(ident: Mapping[str, Any]) -> list[str]:
    keys: list[str] = []
    for field in ("predicted_abnormal_groups", "multi_label_abnormal_groups", "display_group_keys"):
        for group in ident.get(field) or []:
            text = str(group)
            if text and text != "no_quality_abnormal":
                keys.append(text)
    primary = ident.get("primary_abnormal_class") or ident.get("true_abnormal_class")
    if primary and str(primary) != "no_quality_abnormal":
        keys.append(str(primary))
    probabilities = ident.get("class_probability") or ident.get("multilabel_probability") or {}
    if not keys and isinstance(probabilities, Mapping):
        scored = [
            (str(key), _as_score(value))
            for key, value in probabilities.items()
            if str(key) != "no_quality_abnormal" and _as_score(value) > 0
        ]
        if scored:
            keys.append(max(scored, key=lambda item: item[1])[0])
    return list(dict.fromkeys(keys))


API_ROUTE_SPEC = [
    {"method": "GET", "path": "/", "purpose": "serve realtime dashboard"},
    {"method": "GET", "path": "/api/health", "purpose": "runtime health and event count"},
    {"method": "GET", "path": "/api/seed", "purpose": "dashboard seed with events, metrics and knowledge"},
    {"method": "GET", "path": "/api/metrics", "purpose": "three-level model metrics"},
    {"method": "GET", "path": "/risk/events", "purpose": "level-1 anomaly warning events"},
    {"method": "GET", "path": "/identify/events/{event_id}", "purpose": "level-2 abnormal identification"},
    {"method": "GET", "path": "/api/events/{event_id}", "purpose": "single event full detail"},
    {"method": "GET", "path": "/api/trace/events/{event_id}", "purpose": "level-3 path traceability"},
    {"method": "GET", "path": "/api/recommend/events/{event_id}", "purpose": "corrective recommendations"},
    {"method": "GET", "path": "/api/knowledge/search", "purpose": "expert knowledge retrieval"},
    {"method": "GET", "path": "/api/realtime/next", "purpose": "cursor-based realtime event polling"},
    {"method": "GET", "path": "/api/realtime/stream", "purpose": "server-sent realtime event stream"},
    {"method": "POST", "path": "/api/realtime/ingest", "purpose": "realtime event ingestion"},
    {"method": "POST", "path": "/api/assistant/path-question", "purpose": "assistant-only path explanation"},
    {"method": "GET", "path": "/api/data/sources", "purpose": "structured and text source registry"},
    {"method": "POST", "path": "/api/data/structured/upload", "purpose": "structured production data upload contract"},
    {"method": "POST", "path": "/api/data/text/upload", "purpose": "unstructured text source upload contract"},
    {"method": "POST", "path": "/api/data/events/build", "purpose": "event-window dataset build contract"},
    {"method": "GET", "path": "/api/data/events", "purpose": "quality event list"},
    {"method": "GET", "path": "/api/data/events/{event_id}", "purpose": "quality event detail"},
    {"method": "GET", "path": "/api/data/structured/profile", "purpose": "full CSV source profile and data quality"},
    {"method": "GET", "path": "/api/data/processed/windows", "purpose": "processed production event-window preview"},
    {"method": "GET", "path": "/api/data/processed/quality", "purpose": "processed CSV data quality summary"},
    {"method": "POST", "path": "/api/knowledge/extraction/jobs", "purpose": "start text knowledge extraction job"},
    {"method": "GET", "path": "/api/knowledge/extraction/jobs/{job_id}", "purpose": "text knowledge extraction job detail"},
    {"method": "GET", "path": "/api/kg/summary", "purpose": "knowledge graph coverage summary"},
    {"method": "GET", "path": "/api/kg/nodes", "purpose": "knowledge graph node list"},
    {"method": "GET", "path": "/api/kg/edges", "purpose": "knowledge graph edge list"},
    {"method": "GET", "path": "/api/kg/subgraph", "purpose": "filtered knowledge graph subgraph"},
    {"method": "GET", "path": "/api/kg/disambiguation-rules", "purpose": "knowledge graph entity disambiguation and merge policy"},
    {"method": "GET", "path": "/api/kg/path-library", "purpose": "traceability path evidence library"},
    {"method": "GET", "path": "/api/kg/evidence/{event_id}", "purpose": "event-level graph and text evidence package"},
    {"method": "GET", "path": "/api/kg/event-subgraph/{event_id}", "purpose": "event-focused KG subgraph for traceability review"},
    {"method": "GET", "path": "/api/kg/versions", "purpose": "published KG version summary and governance log"},
    {"method": "POST", "path": "/api/kg/case-ingest", "purpose": "reviewed abnormal case to KG candidate contract"},
    {"method": "POST", "path": "/api/kg/governance/actions", "purpose": "record KG review, merge and publish governance actions"},
    {"method": "POST", "path": "/api/knowledge/candidates/validate", "purpose": "validate candidate knowledge against published graph"},
    {"method": "POST", "path": "/api/model/runs", "purpose": "start graph-enhanced model run contract"},
    {"method": "GET", "path": "/api/model/runs", "purpose": "model run list"},
    {"method": "GET", "path": "/api/model/runs/{run_id}", "purpose": "model run detail"},
    {"method": "GET", "path": "/api/model/cascade/summary", "purpose": "quality-code cascade model metrics and gate policy"},
    {"method": "GET", "path": "/api/model/cascade/predictions", "purpose": "quality-code cascade prediction preview"},
    {"method": "GET", "path": "/api/model/traceability/evidence", "purpose": "event-level candidate traceability evidence from cascade model"},
    {"method": "GET", "path": "/api/evaluation/summary", "purpose": "model and data evaluation summary"},
    {"method": "GET", "path": "/api/evaluation/evidence-quality", "purpose": "evidence completeness and KG coverage"},
    {"method": "GET", "path": "/api/system/artifacts", "purpose": "generated artifact registry"},
    {"method": "GET", "path": "/api/assistant/runtime", "purpose": "assistant LLM runtime status without exposing secrets"},
    {"method": "GET", "path": "/assets/{asset_name}", "purpose": "industrial visualization assets"},
]


DEFAULT_DIGITAL_TWIN_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 320">
  <rect width="960" height="320" fill="#07111f"/>
  <rect x="58" y="132" width="74" height="56" rx="10" fill="#10233d" stroke="#2f7dff" stroke-width="2"/>
  <rect x="183" y="132" width="74" height="56" rx="10" fill="#132b47" stroke="#30d180" stroke-width="2"/>
  <rect x="333" y="132" width="74" height="56" rx="10" fill="#10233d" stroke="#f4bc45" stroke-width="2"/>
  <rect x="483" y="132" width="74" height="56" rx="10" fill="#10233d" stroke="#27d4ff" stroke-width="2"/>
  <rect x="633" y="132" width="74" height="56" rx="10" fill="#132b47" stroke="#ff5c65" stroke-width="2"/>
  <rect x="808" y="132" width="74" height="56" rx="10" fill="#10233d" stroke="#a889ff" stroke-width="2"/>
  <g fill="none" stroke="#27d4ff" stroke-width="3" opacity="0.85">
    <path d="M90 160h760"/>
    <path d="M220 105v110M370 105v110M520 105v110M670 105v110"/>
  </g>
  <g font-family="Microsoft YaHei,Arial,sans-serif" font-size="22" fill="#e7f0fb" text-anchor="middle">
    <text x="95" y="92">粗炼</text><text x="220" y="92">精炼</text><text x="370" y="92">中间包</text>
    <text x="520" y="92">结晶器</text><text x="670" y="92">流量控制</text><text x="845" y="92">品质检测</text>
  </g>
  <g fill="#10233d" stroke="#2f7dff" stroke-width="2">
    <circle cx="95" cy="160" r="34"/><circle cx="220" cy="160" r="34"/><circle cx="370" cy="160" r="34"/>
    <circle cx="520" cy="160" r="34"/><circle cx="670" cy="160" r="34"/><circle cx="845" cy="160" r="34"/>
  </g>
</svg>
"""


def _read_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.is_file():
        return rows
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            text = line.strip()
            if not text:
                continue
            rows.append(json.loads(text))
            if limit is not None and len(rows) >= int(limit):
                break
    return rows


def _coerce_csv_value(value: Any) -> Any:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return ""
    lowered = text.lower()
    if lowered in {"nan", "none", "null", "missing"}:
        return None
    try:
        if re.fullmatch(r"[-+]?\d+", text):
            return int(text)
        if re.fullmatch(r"[-+]?(?:\d+\.\d*|\d*\.\d+)(?:[eE][-+]?\d+)?", text) or re.fullmatch(r"[-+]?\d+[eE][-+]?\d+", text):
            return float(text)
    except ValueError:
        return text
    return text


def _read_csv_records(path: Path, limit: int = 20, *, only_abnormal: bool = False) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.is_file():
        return rows
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if only_abnormal and str(row.get("cascade_final_label") or "") == "无品质异常":
                continue
            record = {key: _coerce_csv_value(value) for key, value in row.items()}
            if record.get("cascade_final_label") and not record.get("main_label_text"):
                record["main_label_text"] = record["cascade_final_label"]
            if record.get("process_time") and not record.get("event_time"):
                record["event_time"] = record["process_time"]
            if record.get("binary_abnormal_probability") is not None and not record.get("warning_probability"):
                record["warning_probability"] = record["binary_abnormal_probability"]
            rows.append(record)
            if len(rows) >= max(1, int(limit)):
                break
    return rows


def _load_quality_modeling_artifacts(*, preview_limit: int = 16, only_abnormal: bool = False) -> dict[str, Any]:
    evidence = _read_json(MODEL_EVIDENCE_BUNDLE_PATH, {})
    task_summary = _read_json(TRACEABILITY_DATASET_SUMMARY_PATH, {})
    binary = dict(evidence.get("binary_test") or {})
    multiclass = dict(evidence.get("multiclass_test") or {})
    multilabel = dict(evidence.get("multilabel_test") or {})
    preview = _read_csv_records(CASCADE_PREDICTIONS_PATH, limit=preview_limit, only_abnormal=only_abnormal)
    trace_evidence = _read_csv_records(TRACEABILITY_CANDIDATE_EVIDENCE_PATH, limit=preview_limit, only_abnormal=only_abnormal)
    return {
        "status": "available" if MODEL_EVIDENCE_BUNDLE_PATH.is_file() else "missing",
        "model_contract": "quality_code_cascade_warning_identification_trace_v1",
        "pipeline": [
            {
                "stage": "binary_warning",
                "name": "质量异常预警",
                "output": "预警概率与风险等级",
                "metric": {"macro_f1": binary.get("macro_f1"), "pr_auc": binary.get("pr_auc")},
            },
            {
                "stage": "multiclass_identification",
                "name": "异常种类判断",
                "output": "主要异常种类",
                "metric": {"macro_f1": multiclass.get("macro_f1"), "balanced_accuracy": multiclass.get("balanced_accuracy")},
            },
            {
                "stage": "multilabel_companion",
                "name": "关联异常提示",
                "output": "可能并发的异常线索",
                "metric": {"macro_f1": multilabel.get("macro_f1"), "hamming_loss": multilabel.get("hamming_loss")},
            },
            {
                "stage": "gated_traceability",
                "name": "溯源证据复核",
                "output": "候选原因链路与证据",
                "metric": {"normal_gate_policy": "无异常预警时不触发现场处置"},
            },
        ],
        "metrics": {
            "binary_test": binary,
            "multiclass_test": multiclass,
            "multilabel_test": multilabel,
        },
        "dataset": {
            "n_rows": task_summary.get("n_rows"),
            "n_source_rows": task_summary.get("n_source_rows"),
            "n_auxiliary_rows": task_summary.get("n_auxiliary_rows"),
            "multiclass_counts": task_summary.get("quality_multiclass_counts", {}),
            "multilabel_counts": task_summary.get("target_multilabel_counts", {}),
            "multiple_target_sample_count": task_summary.get("multiple_target_sample_count"),
        },
        "features": {
            "original_count": (evidence.get("features") or {}).get("original_count"),
            "kept_count": (evidence.get("features") or {}).get("kept_count"),
            "dropped_correlated_count": (evidence.get("features") or {}).get("dropped_correlated_count"),
            "top_global_features": list(evidence.get("top_global_features") or [])[:12],
            "module_importance": list(evidence.get("module_importance") or [])[:10],
        },
        "gate_policy": {
            "name": "warning_gate_before_identification_and_traceability",
            "normal_rule": "判断为无品质异常时，系统只保留监测记录，不触发现场处置。",
            "abnormal_rule": "判断为异常时，系统进入异常种类判断、关联异常提示和原因链路复核。",
        },
        "artifacts": {
            "model_evidence_bundle": str(MODEL_EVIDENCE_BUNDLE_PATH),
            "cascade_predictions": str(CASCADE_PREDICTIONS_PATH),
            "traceability_candidate_evidence": str(TRACEABILITY_CANDIDATE_EVIDENCE_PATH),
            "model_dir": str(QUALITY_MODELING_DIR / "models"),
        },
        "preview": preview,
        "traceability_evidence_preview": trace_evidence,
    }


def _to_float(value: Any) -> float | None:
    text = str(value or "").strip()
    if not text or text.lower() in {"missing", "nan", "none", "null"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _count_value(counter: dict[str, int], value: Any) -> None:
    key = str(value if value not in {None, ""} else "missing")
    counter[key] = counter.get(key, 0) + 1


def _quality_groups_from_csv_row(row: Mapping[str, Any]) -> list[str]:
    groups: list[str] = []
    for column, group in QUALITY_GROUP_COLUMNS:
        if _to_float(row.get(column)) and float(_to_float(row.get(column)) or 0.0) > 0:
            groups.append(group)
    raw_groups = str(row.get("quality_abnormal_groups") or "").strip()
    if raw_groups and raw_groups.lower() != "missing":
        for item in re.split(r"[;,，；]+", raw_groups):
            clean = item.strip()
            if clean and clean != "no_quality_abnormal":
                groups.append(clean)
    raw_group = str(row.get("quality_abnormal_group") or "").strip()
    if raw_group and raw_group.lower() != "missing" and raw_group != "no_quality_abnormal":
        groups.append(raw_group)
    return list(dict.fromkeys(groups))


def _feature_mapping_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for field, meta in MODEL_FEATURE_MAP.items():
        variable_group = str(meta["variable_group"])
        process_step = str(meta["process_step"])
        mechanism = str(meta["mechanism"])
        rows.append(
            {
                "field": field,
                "label": meta["label"],
                "unit": meta["unit"],
                "variable_group": variable_group,
                "variable_group_label": VARIABLE_GROUP_LABELS.get(variable_group, variable_group),
                "process_step": process_step,
                "process_step_label": PROCESS_LABELS.get(process_step, process_step),
                "mechanism": mechanism,
                "mechanism_label": DISPLAY_LABELS.get(mechanism, mechanism),
                "target_type": "model_feature",
            }
        )
    return rows


def _production_source_profile_from_summary() -> dict[str, Any]:
    summary = _read_json(STRUCTURED_SUMMARY_PATH, {})
    task_summary = _read_json(TRACEABILITY_DATASET_SUMMARY_PATH, {})
    rows = int(summary.get("n_rows") or 0)
    columns = int(summary.get("n_columns") or 0)
    return {
        "structured_csv_path": str(STRUCTURED_CSV_PATH),
        "model_ready_csv_path": str(MODEL_READY_CSV_PATH),
        "summary_path": str(STRUCTURED_SUMMARY_PATH),
        "records": rows,
        "columns": columns,
        "time_range": {"start": summary.get("time_min"), "end": summary.get("time_max")},
        "labels": summary.get("labels", {}),
        "model_task_summary": {
            "dataset_dir": str(TRACEABILITY_DATASET_DIR),
            "n_rows": task_summary.get("n_rows"),
            "n_source_rows": task_summary.get("n_source_rows"),
            "n_auxiliary_rows": task_summary.get("n_auxiliary_rows"),
            "binary_label_counts": task_summary.get("quality_label_counts", {}),
            "multiclass_counts": task_summary.get("quality_multiclass_counts", {}),
            "multilabel_counts": task_summary.get("target_multilabel_counts", {}),
            "multiple_target_sample_count": task_summary.get("multiple_target_sample_count"),
            "outputs": {
                "y_quality_multiclass": (task_summary.get("outputs") or {}).get("y_quality_multiclass"),
                "y_quality_multilabel": (task_summary.get("outputs") or {}).get("y_quality_multilabel"),
                "label_mapping": (task_summary.get("outputs") or {}).get("label_mapping"),
            },
        },
        "label_policy": {
            "name": "quality_abnormal_code_1_5",
            "positive": "品质异常代码1-5命中目标质量异常大类",
            "negative": "品质异常代码1-5均为空、0或缺失",
            "auxiliary_excluded": "仅命中过渡/中间包状态或其他未归因品质代码",
        },
        "source_status": "available" if STRUCTURED_CSV_PATH.is_file() and MODEL_READY_CSV_PATH.is_file() else "missing",
    }


def _summarize_production_csv(csv_path: Path) -> dict[str, Any]:
    profile = _production_source_profile_from_summary()
    feature_stats = {
        field: {"count": 0, "missing": 0, "sum": 0.0, "sumsq": 0.0, "min": None, "max": None}
        for field in MODEL_FEATURE_MAP
    }
    label_counts: dict[str, dict[str, int]] = {
        "quality_label": {},
        "quality_sample_role": {},
        "quality_code_present_label": {},
        "quality_abnormal_label": {},
        "defect_label": {},
        "defect_label_lock": {},
    }
    group_counts: dict[str, int] = {}
    row_count = 0
    time_min = ""
    time_max = ""
    headers: list[str] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        headers = list(reader.fieldnames or [])
        for row in reader:
            row_count += 1
            timestamp = str(row.get("process_time") or row.get("记录创建时间") or "")
            if timestamp:
                time_min = timestamp if not time_min or timestamp < time_min else time_min
                time_max = timestamp if not time_max or timestamp > time_max else time_max
            for label in label_counts:
                _count_value(label_counts[label], row.get(label))
            groups = _quality_groups_from_csv_row(row)
            if not groups:
                groups = ["unknown"]
            for group in groups:
                group_counts[group] = group_counts.get(group, 0) + 1
            for field, stat in feature_stats.items():
                value = _to_float(row.get(field))
                if value is None:
                    stat["missing"] = int(stat["missing"]) + 1
                    continue
                stat["count"] = int(stat["count"]) + 1
                stat["sum"] = float(stat["sum"]) + value
                stat["sumsq"] = float(stat["sumsq"]) + value * value
                stat["min"] = value if stat["min"] is None else min(float(stat["min"]), value)
                stat["max"] = value if stat["max"] is None else max(float(stat["max"]), value)
    feature_summary: dict[str, dict[str, Any]] = {}
    for field, stat in feature_stats.items():
        count = int(stat["count"])
        mean = float(stat["sum"]) / count if count else 0.0
        variance = max(0.0, float(stat["sumsq"]) / count - mean * mean) if count else 0.0
        feature_summary[field] = {
            "label": MODEL_FEATURE_MAP[field]["label"],
            "variable_group": MODEL_FEATURE_MAP[field]["variable_group"],
            "process_step": MODEL_FEATURE_MAP[field]["process_step"],
            "mechanism": MODEL_FEATURE_MAP[field]["mechanism"],
            "count": count,
            "missing": int(stat["missing"]),
            "missing_ratio": round(int(stat["missing"]) / max(row_count, 1), 6),
            "mean": round(mean, 6),
            "std": round(variance ** 0.5, 6),
            "min": stat["min"],
            "max": stat["max"],
        }
    profile.update(
        {
            "profile_version": "structured_csv_processing_v1",
            "records": row_count,
            "columns": len(headers),
            "time_range": {"start": time_min or profile.get("time_range", {}).get("start"), "end": time_max or profile.get("time_range", {}).get("end")},
            "label_distribution": label_counts,
            "quality_group_distribution": group_counts,
            "field_mapping": _feature_mapping_rows(),
            "feature_statistics": feature_summary,
            "data_quality": {
                "selected_feature_count": len(MODEL_FEATURE_MAP),
                "normal_sample_count": label_counts.get("quality_label", {}).get("0", label_counts.get("quality_abnormal_label", {}).get("0", 0)),
                "abnormal_sample_count": label_counts.get("quality_label", {}).get("1", label_counts.get("quality_abnormal_label", {}).get("1", 0)),
                "auxiliary_sample_count": label_counts.get("quality_sample_role", {}).get("auxiliary_excluded", 0),
                "normal_sample_available": label_counts.get("quality_label", {}).get("0", label_counts.get("quality_abnormal_label", {}).get("0", 0)) > 0,
                "all_rows_are_abnormal_labels": set(label_counts.get("quality_label") or label_counts.get("quality_abnormal_label", {})).issubset({"1", "1.0"}),
                "high_missing_features": [
                    {"field": field, "label": row["label"], "missing_ratio": row["missing_ratio"]}
                    for field, row in feature_summary.items()
                    if float(row["missing_ratio"]) > 0.05
                ],
            },
            "window_strategy": {
                "name": "row_as_event_window_v1",
                "description": "当前 CSV 每行已经是按连铸生产记录聚合后的工艺窗口，先按单条记录构建生产事件窗口。",
                "time_column": "process_time",
                "alignment_keys": ["材料跟踪号", "炼钢材料号", "铸机号", "连铸处理号", "中间包号", "记录识别码"],
            },
        }
    )
    return profile


def _signal_scores_for_row(row: Mapping[str, Any], feature_statistics: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    for field, meta in MODEL_FEATURE_MAP.items():
        value = _to_float(row.get(field))
        if value is None:
            continue
        stat = feature_statistics.get(field, {})
        mean = _to_float(stat.get("mean")) or 0.0
        std = _to_float(stat.get("std")) or 0.0
        z_score = abs((value - mean) / std) if std > 0 else 0.0
        contribution = min(z_score / 4.0, 1.0)
        signals.append(
            {
                "field": field,
                "label": meta["label"],
                "value": round(value, 6),
                "unit": meta["unit"],
                "variable_group": meta["variable_group"],
                "process_step": meta["process_step"],
                "mechanism": meta["mechanism"],
                "z_score": round(z_score, 3),
                "contribution": round(contribution, 3),
            }
        )
    return sorted(signals, key=lambda item: float(item["contribution"]), reverse=True)


def _event_window_from_csv_row(row: Mapping[str, Any], index: int, profile: Mapping[str, Any]) -> dict[str, Any]:
    top_signals = _signal_scores_for_row(row, profile.get("feature_statistics", {}) or {})[:5]
    groups = _quality_groups_from_csv_row(row)
    primary_group = groups[0] if groups else str((top_signals[0] if top_signals else {}).get("mechanism") or "other_quality_abnormal")
    dominant_signal = top_signals[0] if top_signals else {}
    quality_label_value = _to_float(row.get("quality_label"))
    if quality_label_value is None:
        quality_label_value = _to_float(row.get("quality_abnormal_label"))
    quality_label = int(quality_label_value or 0)
    top_contribution = float(dominant_signal.get("contribution") or 0.0)
    group_component = min(len(groups) / 3.0, 1.0)
    risk_probability = min(1.0, 0.25 + 0.45 * quality_label + 0.20 * top_contribution + 0.10 * group_component)
    risk_level = "high" if risk_probability >= 0.75 else "medium" if risk_probability >= 0.55 else "low"
    process_step = str(dominant_signal.get("process_step") or MECHANISM_TO_STEP.get(primary_group, "quality"))
    variable_group = str(dominant_signal.get("variable_group") or "process_variable")
    return {
        "event_window_id": f"csv_window_{index:06d}",
        "source_row_index": index,
        "timestamp": row.get("process_time") or row.get("记录创建时间"),
        "window_strategy": "row_as_event_window_v1",
        "alignment_keys": {
            "material_tracking_no": row.get("材料跟踪号"),
            "steel_material_no": row.get("炼钢材料号"),
            "caster_no": row.get("铸机号"),
            "casting_process_no": row.get("连铸处理号"),
            "tundish_no": row.get("中间包号"),
            "record_id": row.get("记录识别码"),
        },
        "quality_label": {
            "quality_label": row.get("quality_label"),
            "quality_sample_role": row.get("quality_sample_role"),
            "quality_label_source": row.get("quality_label_source"),
            "quality_abnormal_label": quality_label,
            "quality_code_present_label": int(_to_float(row.get("quality_code_present_label")) or 0),
            "defect_label": int(_to_float(row.get("defect_label")) or 0),
            "defect_label_lock": int(_to_float(row.get("defect_label_lock")) or 0),
            "quality_groups": groups,
            "primary_group": primary_group,
            "primary_group_label": DISPLAY_LABELS.get(primary_group, primary_group),
        },
        "risk_warning": {
            "risk_probability": round(risk_probability, 3),
            "risk_level": risk_level,
            "top_signal": dominant_signal.get("label"),
        },
        "trace_seed": {
            "feature": dominant_signal.get("field"),
            "feature_label": dominant_signal.get("label"),
            "variable_group": variable_group,
            "variable_group_label": VARIABLE_GROUP_LABELS.get(variable_group, variable_group),
            "process_step": process_step,
            "process_step_label": PROCESS_LABELS.get(process_step, process_step),
            "mechanism": primary_group,
            "mechanism_label": DISPLAY_LABELS.get(primary_group, primary_group),
        },
        "top_signals": top_signals,
        "model_input": {
            field: _to_float(row.get(field))
            for field in MODEL_FEATURE_MAP
            if _to_float(row.get(field)) is not None
        },
    }


def build_production_data_artifacts(output_dir: str | Path, max_windows: int = 600) -> dict[str, Any]:
    output = _fs_path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    if not STRUCTURED_CSV_PATH.is_file():
        profile = {
            "profile_version": "structured_csv_processing_v1",
            "source_status": "missing",
            "structured_csv_path": str(STRUCTURED_CSV_PATH),
            "records": 0,
            "field_mapping": _feature_mapping_rows(),
            "data_quality": {"normal_sample_available": False, "reason": "structured CSV not found"},
        }
        windows = {"status": "missing_source", "windows": [], "n_windows": 0}
    else:
        profile = _summarize_production_csv(STRUCTURED_CSV_PATH)
        total_rows = int(profile.get("records") or 0)
        stride = max(1, total_rows // max(1, max_windows))
        windows_list: list[dict[str, Any]] = []
        with STRUCTURED_CSV_PATH.open("r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            for idx, row in enumerate(reader, start=1):
                if (idx - 1) % stride == 0 and len(windows_list) < max_windows:
                    windows_list.append(_event_window_from_csv_row(row, idx, profile))
                if len(windows_list) >= max_windows:
                    break
        windows = {
            "status": "built",
            "source": str(STRUCTURED_CSV_PATH),
            "window_strategy": profile.get("window_strategy"),
            "total_source_rows": total_rows,
            "n_windows": len(windows_list),
            "preview_sampling": {"method": "chronological_stride", "stride": stride, "max_windows": max_windows},
            "windows": windows_list,
        }
    (output / PRODUCTION_PROFILE_FILENAME).write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / PRODUCTION_WINDOWS_FILENAME).write_text(json.dumps(windows, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "profile_path": str(Path(output_dir) / PRODUCTION_PROFILE_FILENAME),
        "windows_path": str(Path(output_dir) / PRODUCTION_WINDOWS_FILENAME),
        "records": int(profile.get("records") or 0),
        "preview_windows": int(windows.get("n_windows") or 0),
    }


def _load_processed_profile(root: Path) -> dict[str, Any]:
    return _read_json(_fs_path(root) / PRODUCTION_PROFILE_FILENAME, _production_source_profile_from_summary())


def _load_processed_windows(root: Path) -> dict[str, Any]:
    return _read_json(_fs_path(root) / PRODUCTION_WINDOWS_FILENAME, {"status": "not_built", "windows": [], "n_windows": 0})


def _status_for_step(event: Mapping[str, Any], step_id: str) -> str:
    risk = dict(event.get("risk_warning") or {})
    risk_level = str(risk.get("risk_level") or "low")
    groups = set(_abnormal_group_keys(event.get("abnormal_identification", {}) or {}))
    matched_steps = {MECHANISM_TO_STEP.get(group, "") for group in groups}
    if step_id not in matched_steps:
        return "context" if step_id in {"roughing", "refining"} else "normal"
    if risk_level == "high":
        return "danger"
    if risk_level == "medium":
        return "warning"
    return "active"


def _process_status(event: Mapping[str, Any]) -> list[dict[str, Any]]:
    out = []
    for step in PROCESS_STEPS:
        row = dict(step)
        row["status"] = _status_for_step(event, str(step["id"]))
        row["note"] = "流程背景" if row["scope"] == "context" else "模型分析范围"
        out.append(row)
    return out


def _simplify_event(event: Mapping[str, Any], index: int) -> dict[str, Any]:
    row = dict(event)
    row["sequence_no"] = int(index)
    row["process_status"] = _process_status(row)
    ident = dict(row.get("abnormal_identification") or {})
    group_keys = _abnormal_group_keys(ident)
    ident["display_group_keys"] = group_keys
    ident["display_groups"] = [DISPLAY_LABELS.get(str(group), str(group)) for group in group_keys]
    row["abnormal_identification"] = ident
    return row


def load_source_artifacts(source_dir: str | Path, max_events: int = 400) -> dict[str, Any]:
    root = Path(source_dir)
    metrics = _read_json(root / "model_metrics.json", {})
    summary = _read_json(root / "system_summary.json", {})
    events = _read_jsonl(root / "event_explanations.jsonl", limit=max_events)
    if not events:
        dashboard = _read_json(root / "dashboard_data.json", {})
        events = list(dashboard.get("events", []) or [])[:max_events]
    return {
        "metrics": metrics,
        "summary": summary,
        "events": [_simplify_event(event, idx) for idx, event in enumerate(events)],
    }


def _safe_id(*parts: Any) -> str:
    text = "_".join(str(part) for part in parts if str(part or "").strip())
    safe = "".join(ch.lower() if ch.isalnum() else "_" for ch in text)
    safe = "_".join(chunk for chunk in safe.split("_") if chunk)
    return safe or "unknown"


def _normalize_alias_text(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = (
        text.replace("（", "(")
        .replace("）", ")")
        .replace("／", "/")
        .replace("℃", "c")
        .replace("°c", "c")
    )
    text = re.sub(r"\([^)]*\)", "", text)
    text = re.sub(r"/[a-z0-9.%]+", "", text)
    text = re.sub(r"[\s_\-:/\\|,，。；;·\[\]{}]+", "", text)
    return text


def _alias_match(value: Any, groups: Mapping[str, Sequence[str]]) -> str | None:
    text = _normalize_alias_text(value)
    if not text:
        return None
    for canonical, aliases in groups.items():
        normalized_aliases = {_normalize_alias_text(alias) for alias in [canonical, *aliases]}
        if text in normalized_aliases:
            return canonical
    for canonical, aliases in groups.items():
        for alias in [canonical, *aliases]:
            normalized = _normalize_alias_text(alias)
            if normalized and normalized in text:
                return canonical
    return None


def _split_feature_stat(value: Any) -> tuple[str, str]:
    text = str(value or "").strip()
    lower = text.lower()
    for suffix in ("_mean", "_std", "_trend", "_last", "_max", "_min"):
        if lower.endswith(suffix):
            return text[: -len(suffix)], suffix[1:]
    return text, ""


def _format_feature_label(base_label: str, stat: str) -> str:
    stat_label = FEATURE_STAT_LABELS.get(stat, stat)
    unit_match = re.match(r"^(.+?)/(.+)$", str(base_label))
    if unit_match:
        name, unit = unit_match.groups()
        clean_unit = unit.strip().strip("()").lower()
        unit_label = UNIT_LABELS.get(clean_unit, UNIT_LABELS.get(unit.strip(), unit.strip()))
        return f"{name}（{unit_label}，{stat_label}）" if stat else f"{name}（{unit_label}）"
    return f"{base_label}（{stat_label}）" if stat else base_label


def _entity_prefix(entity_type: str) -> str:
    return {
        "process_step": "process",
        "defect_mechanism": "mechanism",
        "window_feature": "feature",
        "base_variable": "base_variable",
        "variable_group": "variable_group",
        "equipment_zone": "equipment_zone",
        "process_state": "process_state",
        "quality_class": "quality_class",
        "correction_action": "action",
        "text_evidence": "text",
        "reviewed_quality_case": "case",
    }.get(entity_type, _safe_id(entity_type))


def _canonical_entity_parts(entity_type: str, value: Any) -> dict[str, Any]:
    raw = str(value or "").strip()
    aliases = [raw] if raw else []
    if entity_type == "defect_mechanism":
        canonical = _alias_match(raw, MECHANISM_ALIASES) or _safe_id(raw)
        return {
            "key": canonical,
            "label": DISPLAY_LABELS.get(canonical, raw or canonical),
            "aliases": list(dict.fromkeys([*aliases, *MECHANISM_ALIASES.get(canonical, [])])),
            "rule": "mechanism_alias_and_label_dictionary",
        }
    if entity_type in {"process_step", "equipment_zone"}:
        canonical = _alias_match(raw, PROCESS_ALIASES) or _safe_id(raw)
        return {
            "key": canonical,
            "label": PROCESS_LABELS.get(canonical, raw or canonical),
            "aliases": list(dict.fromkeys([*aliases, *PROCESS_ALIASES.get(canonical, [])])),
            "rule": "process_scope_alias_dictionary",
        }
    if entity_type == "variable_group":
        canonical = _alias_match(raw, VARIABLE_GROUP_ALIASES) or _safe_id(raw)
        return {
            "key": canonical,
            "label": VARIABLE_GROUP_LABELS.get(canonical, raw or canonical),
            "aliases": list(dict.fromkeys([*aliases, *VARIABLE_GROUP_ALIASES.get(canonical, [])])),
            "rule": "variable_group_alias_dictionary",
        }
    if entity_type == "window_feature":
        base, stat = _split_feature_stat(raw)
        canonical_base = _alias_match(base, FEATURE_BASE_ALIASES) or _safe_id(base)
        canonical = f"{canonical_base}_{stat}" if stat else canonical_base
        base_label = FEATURE_BASE_LABELS.get(canonical_base, base or canonical_base)
        label = _format_feature_label(base_label, stat)
        return {
            "key": canonical,
            "label": label,
            "aliases": list(dict.fromkeys([raw, base, *FEATURE_BASE_ALIASES.get(canonical_base, [])])),
            "rule": "feature_base_unit_stat_normalization",
        }
    if entity_type == "base_variable":
        base, _stat = _split_feature_stat(raw)
        canonical_base = _alias_match(base, FEATURE_BASE_ALIASES) or _safe_id(base)
        return {
            "key": canonical_base,
            "label": FEATURE_BASE_LABELS.get(canonical_base, base or canonical_base),
            "aliases": list(dict.fromkeys([raw, base, *FEATURE_BASE_ALIASES.get(canonical_base, [])])),
            "rule": "base_variable_normalization",
        }
    if entity_type == "process_state":
        canonical = _alias_match(raw, MECHANISM_ALIASES) or _safe_id(raw)
        return {
            "key": canonical,
            "label": DISPLAY_LABELS.get(canonical, raw or canonical),
            "aliases": aliases,
            "rule": "process_state_from_trace_path",
        }
    if entity_type == "quality_class":
        canonical = _alias_match(raw, MECHANISM_ALIASES) or _safe_id(raw)
        return {
            "key": canonical,
            "label": DISPLAY_LABELS.get(canonical, raw or canonical),
            "aliases": list(dict.fromkeys([*aliases, *MECHANISM_ALIASES.get(canonical, [])])),
            "rule": "quality_class_label_dictionary",
        }
    if entity_type == "text_evidence":
        mechanism = _alias_match(raw, MECHANISM_ALIASES) or _safe_id(raw)
        label = DISPLAY_LABELS.get(mechanism, raw or mechanism)
        return {
            "key": f"{mechanism}_text_evidence",
            "label": f"{label}文本依据",
            "aliases": aliases,
            "rule": "text_evidence_bucket_by_mechanism",
        }
    if entity_type == "reviewed_quality_case":
        return {
            "key": _safe_id(raw),
            "label": raw or "历史异常案例",
            "aliases": aliases,
            "rule": "case_path_key_normalization",
        }
    if entity_type == "correction_action":
        clean = raw.rstrip("。；; ")
        return {
            "key": _safe_id(clean),
            "label": clean or "现场处置建议",
            "aliases": aliases,
            "rule": "action_text_normalization",
        }
    return {"key": _safe_id(raw), "label": raw or "未命名实体", "aliases": aliases, "rule": "safe_id_fallback"}


def _entity_id(entity_type: str, value: Any) -> str:
    parts = _canonical_entity_parts(entity_type, value)
    return f"{_entity_prefix(entity_type)}::{_safe_id(parts['key'])}"


def _process_consistency_score(mechanism_key: str, zone_key: str, variable_group_key: str = "") -> float:
    expected = MECHANISM_TO_STEP.get(mechanism_key, "")
    if expected and expected == zone_key:
        return 1.0
    if mechanism_key == "temperature_flux" and zone_key in {"tundish", "mold"}:
        return 0.88
    if mechanism_key == "heat_transfer_imbalance" and zone_key in {"heat_transfer", "mold"}:
        return 0.9
    if mechanism_key == "process_fluctuation" and variable_group_key in {"tundish_weight", "sequence_transition"}:
        return 0.82
    if zone_key == "quality":
        return 0.58
    return 0.42


def _canonical_path_snapshot(path: Mapping[str, Any]) -> dict[str, Any]:
    feature = _canonical_entity_parts("window_feature", path.get("feature"))
    base_variable = _canonical_entity_parts("base_variable", path.get("feature"))
    variable = _canonical_entity_parts("variable_group", path.get("variable_group"))
    zone = _canonical_entity_parts("equipment_zone", path.get("equipment_zone"))
    process_state = _canonical_entity_parts("process_state", path.get("process_state") or path.get("defect_mechanism"))
    mechanism = _canonical_entity_parts("defect_mechanism", path.get("defect_mechanism"))
    quality_class = _canonical_entity_parts("quality_class", path.get("event_target") or path.get("defect_mechanism"))
    consistency = _process_consistency_score(str(mechanism["key"]), str(zone["key"]), str(variable["key"]))
    return {
        "base_variable_id": _entity_id("base_variable", path.get("feature")),
        "base_variable_label": base_variable["label"],
        "feature_id": _entity_id("window_feature", path.get("feature")),
        "feature_label": feature["label"],
        "variable_group_id": _entity_id("variable_group", path.get("variable_group")),
        "variable_group_label": variable["label"],
        "equipment_zone_id": _entity_id("equipment_zone", path.get("equipment_zone")),
        "equipment_zone_label": zone["label"],
        "process_state_id": _entity_id("process_state", path.get("process_state") or path.get("defect_mechanism")),
        "process_state_label": process_state["label"],
        "mechanism_id": _entity_id("defect_mechanism", path.get("defect_mechanism")),
        "mechanism_key": mechanism["key"],
        "mechanism_label": mechanism["label"],
        "quality_class_id": _entity_id("quality_class", path.get("event_target") or path.get("defect_mechanism")),
        "quality_class_label": quality_class["label"],
        "disambiguation_rules": list({str(feature["rule"]), str(base_variable["rule"]), str(variable["rule"]), str(zone["rule"]), str(process_state["rule"]), str(mechanism["rule"]), str(quality_class["rule"])}),
        "process_consistency": round(consistency, 3),
    }


def _merge_entity(
    entities: dict[str, dict[str, Any]],
    entity_id: str,
    label: str,
    entity_type: str,
    source_type: str,
    confidence: float = 0.8,
    *,
    canonical_key: str | None = None,
    aliases: Sequence[str] | None = None,
    disambiguation_rule: str = "safe_id_fallback",
) -> dict[str, Any]:
    if entity_id not in entities:
        row = _make_entity(entity_id, label, entity_type, source_type, confidence)
        row["canonical_key"] = canonical_key or entity_id.rsplit("::", 1)[-1]
        row["aliases"] = list(dict.fromkeys([label, *(aliases or [])]))
        row["disambiguation_rule"] = disambiguation_rule
        row["source_types"] = [source_type]
        row["evidence_count"] = 1
        entities[entity_id] = row
        return row
    row = entities[entity_id]
    row["confidence"] = round(max(_as_score(row.get("confidence"), 0.0), _as_score(confidence)), 3)
    merged_aliases = list(row.get("aliases") or [])
    merged_aliases.extend([label, *(aliases or [])])
    row["aliases"] = list(dict.fromkeys([str(item) for item in merged_aliases if str(item or "").strip()]))[:16]
    source_types = list(row.get("source_types") or [row.get("source_type")])
    source_types.append(source_type)
    row["source_types"] = list(dict.fromkeys([str(item) for item in source_types if item]))[:8]
    row["evidence_count"] = int(row.get("evidence_count") or 1) + 1
    return row


def _merge_relation(relations: dict[str, dict[str, Any]], relation: dict[str, Any]) -> None:
    relation_id = str(relation.get("id") or "")
    if relation_id not in relations:
        row = dict(relation)
        row["source_types"] = [row.get("source_type")]
        row["evidence_count"] = 1
        row["evidence_snippets"] = [row.get("evidence_snippet")]
        relations[relation_id] = row
        return
    row = relations[relation_id]
    row["confidence"] = round(max(_as_score(row.get("confidence"), 0.0), _as_score(relation.get("confidence"), 0.0)), 3)
    row["evidence_count"] = int(row.get("evidence_count") or 1) + 1
    source_types = list(row.get("source_types") or [row.get("source_type")])
    source_types.append(relation.get("source_type"))
    row["source_types"] = list(dict.fromkeys([str(item) for item in source_types if item]))[:8]
    snippets = list(row.get("evidence_snippets") or [])
    snippets.append(relation.get("evidence_snippet"))
    row["evidence_snippets"] = list(dict.fromkeys([str(item) for item in snippets if item]))[:3]


def _as_score(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return max(0.0, min(1.0, number))


def _event_risk_probability(event: Mapping[str, Any]) -> float:
    return _as_score((event.get("risk_warning") or {}).get("risk_probability"), 0.0)


def _kg_relation_key(source: str, target: str, relation_type: str) -> str:
    return f"{source}|{relation_type}|{target}"


def _kg_evidence_index(kg: Mapping[str, Any] | None) -> dict[str, Any]:
    relation_confidence: dict[str, float] = {}
    relation_sources: dict[str, list[str]] = {}
    relation_snippets: dict[str, list[str]] = {}
    path_library: dict[str, dict[str, Any]] = {}
    if not kg:
        return {
            "relation_confidence": relation_confidence,
            "relation_sources": relation_sources,
            "relation_snippets": relation_snippets,
            "path_library": path_library,
        }
    for edge in kg.get("edges", []) or []:
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        relation_type = str(edge.get("relation_type") or "")
        if not source or not target or not relation_type:
            continue
        key = _kg_relation_key(source, target, relation_type)
        relation_confidence[key] = max(
            relation_confidence.get(key, 0.0),
            _as_score(edge.get("confidence"), 0.0),
        )
        sources = list(relation_sources.get(key, []))
        sources.extend(edge.get("source_types") or [edge.get("source_type")])
        relation_sources[key] = list(dict.fromkeys([str(item) for item in sources if item]))[:8]
        snippets = list(relation_snippets.get(key, []))
        snippets.extend(edge.get("evidence_snippets") or [edge.get("evidence_snippet")])
        relation_snippets[key] = list(dict.fromkeys([str(item) for item in snippets if item]))[:3]
    for item in kg.get("path_library", []) or []:
        variable_ref = _canonical_entity_parts("variable_group", item.get("variable_group"))
        zone_ref = _canonical_entity_parts("equipment_zone", item.get("equipment_zone"))
        mechanism_ref = _canonical_entity_parts("defect_mechanism", item.get("defect_mechanism") or item.get("mechanism_label"))
        key = _safe_id(variable_ref["key"], zone_ref["key"], mechanism_ref["key"])
        path_library[key] = dict(item)
    return {
        "relation_confidence": relation_confidence,
        "relation_sources": relation_sources,
        "relation_snippets": relation_snippets,
        "path_library": path_library,
    }


def _kg_relation_hit(
    kg_index: Mapping[str, Any] | None,
    source: str,
    target: str,
    relation_types: Sequence[str],
) -> dict[str, Any]:
    if not kg_index:
        return {"hit": False, "confidence": 0.0, "relation_type": "", "source_types": [], "snippets": []}
    confidence_index = kg_index.get("relation_confidence") or {}
    source_index = kg_index.get("relation_sources") or {}
    snippet_index = kg_index.get("relation_snippets") or {}
    best = {"hit": False, "confidence": 0.0, "relation_type": "", "source_types": [], "snippets": []}
    for relation_type in relation_types:
        key = _kg_relation_key(source, target, relation_type)
        confidence = _as_score(confidence_index.get(key), 0.0)
        if confidence > _as_score(best.get("confidence"), 0.0):
            best = {
                "hit": confidence > 0,
                "confidence": confidence,
                "relation_type": relation_type,
                "source_types": source_index.get(key, []) or [],
                "snippets": snippet_index.get(key, []) or [],
            }
    return best


def _temporal_consistency_score(event: Mapping[str, Any]) -> float:
    risk = _event_risk_probability(event)
    stage = str(event.get("precursor_stage") or "").lower()
    stage_score = {"early": 0.68, "mid": 0.76, "middle": 0.76, "late": 0.86}.get(stage, 0.72)
    horizon = event.get("lead_horizon_min")
    try:
        horizon_score = 1.0 - min(abs(float(horizon)) / 120.0, 0.45)
    except (TypeError, ValueError):
        horizon_score = stage_score
    return _as_score(0.48 * risk + 0.32 * stage_score + 0.20 * horizon_score)


def _graph_score_for_path(
    path: Mapping[str, Any],
    event: Mapping[str, Any],
    kg_index: Mapping[str, Any] | None,
) -> dict[str, Any]:
    canonical = _canonical_path_snapshot(path)
    base_variable_id = str(canonical.get("base_variable_id") or "")
    feature_id = str(canonical.get("feature_id") or "")
    variable_id = str(canonical.get("variable_group_id") or "")
    zone_id = str(canonical.get("equipment_zone_id") or "")
    process_state_id = str(canonical.get("process_state_id") or "")
    mechanism_id = str(canonical.get("mechanism_id") or "")
    quality_class_id = str(canonical.get("quality_class_id") or "")
    mechanism_key = str(canonical.get("mechanism_key") or path.get("defect_mechanism") or "")
    zone_key = _canonical_entity_parts("equipment_zone", path.get("equipment_zone")).get("key")
    variable_key = _canonical_entity_parts("variable_group", path.get("variable_group")).get("key")
    expected_step = MECHANISM_TO_STEP.get(mechanism_key) or str(zone_key or "")
    step_id = _entity_id("process_step", expected_step)
    text_evidence_id = _entity_id("text_evidence", mechanism_key)
    path_key = _safe_id(variable_key, zone_key, mechanism_key)
    reviewed_case_id = _entity_id("reviewed_quality_case", path_key)

    relation_hits = [
        {
            "label": "基础变量到窗口特征",
            **_kg_relation_hit(kg_index, base_variable_id, feature_id, ["HAS_STAT_FEATURE"]),
        },
        {
            "label": "变量归属",
            **_kg_relation_hit(kg_index, feature_id, variable_id, ["BELONGS_TO_VARIABLE_GROUP", "HAS_KEY_SIGNAL"]),
        },
        {
            "label": "工序观测",
            **_kg_relation_hit(kg_index, variable_id, zone_id, ["OBSERVED_IN_ZONE"]),
        },
        {
            "label": "机理指向",
            **_kg_relation_hit(kg_index, zone_id, mechanism_id, ["INDICATES_MECHANISM", "OBSERVED_IN_ZONE"]),
        },
        {
            "label": "专家机理",
            **_kg_relation_hit(kg_index, step_id, mechanism_id, ["HAS_RISK_MECHANISM"]),
        },
        {
            "label": "变量支持",
            **_kg_relation_hit(kg_index, variable_id, mechanism_id, ["SUPPORTS_MECHANISM"]),
        },
        {
            "label": "变量支持工艺状态",
            **_kg_relation_hit(kg_index, variable_id, process_state_id, ["SUPPORTS_PROCESS_STATE"]),
        },
        {
            "label": "工艺状态指向异常机理",
            **_kg_relation_hit(kg_index, process_state_id, mechanism_id, ["STATE_INDICATES_MECHANISM"]),
        },
        {
            "label": "机理对应质量异常",
            **_kg_relation_hit(kg_index, mechanism_id, quality_class_id, ["CAUSES_QUALITY_RISK"]),
        },
        {
            "label": "文本证据支持",
            **_kg_relation_hit(kg_index, text_evidence_id, mechanism_id, ["SUPPORTED_BY_TEXT"]),
        },
        {
            "label": "历史案例支持",
            **_kg_relation_hit(kg_index, reviewed_case_id, mechanism_id, ["SUPPORTED_BY_CASE"]),
        },
    ]
    matched_hits = [hit for hit in relation_hits if hit.get("hit")]
    relation_score = (
        sum(_as_score(hit.get("confidence"), 0.0) for hit in matched_hits) / len(matched_hits)
        if matched_hits
        else 0.36
    )
    library_item = ((kg_index or {}).get("path_library") or {}).get(path_key, {})
    event_count = int(library_item.get("event_count") or 0)
    library_score = 0.35
    if library_item:
        library_score = _as_score(
            0.46 * _as_score(library_item.get("avg_final_score"), 0.0)
            + 0.34 * min(event_count / 12.0, 1.0)
            + 0.20 * _as_score(library_item.get("process_consistency"), canonical.get("process_consistency")),
            0.35,
        )
    source_types: list[str] = []
    snippets: list[str] = []
    for hit in matched_hits:
        source_types.extend(hit.get("source_types") or [])
        snippets.extend(hit.get("snippets") or [])
    source_diversity = min(len(set(source_types)) / 4.0, 1.0) if source_types else (0.45 if library_item else 0.2)
    process_consistency = _as_score(canonical.get("process_consistency"), 0.5)
    disambiguation_score = min(len(canonical.get("disambiguation_rules") or []) / 4.0, 1.0)
    graph_prior = _as_score(
        0.34 * relation_score
        + 0.28 * library_score
        + 0.22 * process_consistency
        + 0.10 * source_diversity
        + 0.06 * disambiguation_score
    )
    expert_rule_alignment = _as_score(max(
        _as_score(next((hit.get("confidence") for hit in relation_hits if hit.get("label") == "专家机理"), 0.0), 0.0),
        0.45 + 0.45 * process_consistency,
    ))
    path_score = _as_score(path.get("path_score"), 0.55)
    occlusion = _as_score(path.get("path_occlusion_drop"), 0.0)
    model_attribution = _as_score(0.70 * path_score + 0.30 * max(path_score, occlusion))
    temporal = _temporal_consistency_score(event)
    final_score = _as_score(
        0.32 * model_attribution
        + 0.30 * graph_prior
        + 0.14 * temporal
        + 0.12 * expert_rule_alignment
        + 0.12 * process_consistency
    )
    return {
        "canonical_path": canonical,
        "process_consistency": round(process_consistency, 3),
        "graph_prior": round(graph_prior, 3),
        "graph_relation_score": round(relation_score, 3),
        "path_library_score": round(library_score, 3),
        "path_library_match": bool(library_item),
        "path_library_event_count": event_count,
        "model_attribution": round(model_attribution, 3),
        "temporal_consistency": round(temporal, 3),
        "expert_rule_alignment": round(expert_rule_alignment, 3),
        "final_score": round(final_score, 3),
        "score_model": "kg_evidence_fusion_v2",
        "score_components": {
            "weights": {
                "model_attribution": 0.32,
                "graph_prior": 0.30,
                "temporal_consistency": 0.14,
                "expert_rule_alignment": 0.12,
                "process_consistency": 0.12,
            },
            "graph_prior_inputs": {
                "relation_score": round(relation_score, 3),
                "path_library_score": round(library_score, 3),
                "source_diversity": round(source_diversity, 3),
                "disambiguation_score": round(disambiguation_score, 3),
            },
        },
        "graph_evidence_detail": {
            "matched_relation_count": len(matched_hits),
            "matched_relations": [
                {
                    "label": hit.get("label"),
                    "relation_type": hit.get("relation_type"),
                    "confidence": round(_as_score(hit.get("confidence"), 0.0), 3),
                    "source_types": hit.get("source_types") or [],
                }
                for hit in matched_hits
            ],
            "source_types": list(dict.fromkeys([str(item) for item in source_types if item]))[:8],
            "snippets": list(dict.fromkeys([str(item) for item in snippets if item]))[:3],
            "path_library_key": path_key,
        },
    }


def _evidence_sources_for_path(path: Mapping[str, Any], event: Mapping[str, Any]) -> list[dict[str, Any]]:
    canonical = _canonical_path_snapshot(path)
    mechanism = str(canonical.get("mechanism_key") or path.get("defect_mechanism") or "")
    mechanism_label = str(canonical.get("mechanism_label") or DISPLAY_LABELS.get(mechanism, mechanism or "未命名机制"))
    feature = str(canonical.get("feature_label") or path.get("feature") or "unknown_feature")
    variable_group = str(canonical.get("variable_group_label") or path.get("variable_group") or "unknown_group")
    zone = str(canonical.get("equipment_zone_label") or path.get("equipment_zone") or "unknown_zone")
    path_score = _as_score(path.get("final_score") or path.get("path_score"), 0.55)
    occlusion = _as_score(path.get("path_occlusion_drop"), 0.25)
    graph_detail = path.get("graph_evidence_detail") or {}
    matched_count = int(graph_detail.get("matched_relation_count") or 0)
    return [
        {
            "source_id": str(canonical.get("feature_id") or f"structured::{feature}"),
            "source_type": "structured_production",
            "title": "结构化生产信号",
            "confidence": round(max(path_score, occlusion), 3),
            "snippet": f"{feature} 在当前事件窗口内贡献较高，已归并到 {variable_group} 信号组。",
        },
        {
            "source_id": str(canonical.get("mechanism_id") or f"kg::{mechanism}"),
            "source_type": "knowledge_graph",
            "title": "知识图谱机理链路",
            "confidence": round(_as_score(path.get("graph_prior"), 0.68 + 0.22 * path_score), 3),
            "snippet": f"{zone} -> {mechanism_label} 的图谱链路命中 {matched_count} 条关系，并结合历史路径库参与评分。",
        },
        {
            "source_id": f"text::{mechanism}",
            "source_type": "text_knowledge",
            "title": "文本知识抽取证据",
            "confidence": round(0.58 + 0.18 * path_score, 3),
            "snippet": f"规程、异常报告或专家经验中抽取到 {mechanism_label} 与 {variable_group} 的相关描述，进入待审核知识证据。",
        },
        {
            "source_id": "rule::three_level_traceability",
            "source_type": "expert_rule",
            "title": "三层溯源规则对齐",
            "confidence": round(0.62 + 0.2 * occlusion, 3),
            "snippet": "沿用当前风险预警、异常识别、路径溯源三层业务链路作为兼容基线。",
        },
    ]


def _augment_trace_path(
    path: Mapping[str, Any],
    event: Mapping[str, Any],
    kg_index: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    row = dict(path)
    score = _graph_score_for_path(row, event, kg_index)
    row.update(score)
    row["text_evidence"] = [item["snippet"] for item in _evidence_sources_for_path(row, event) if item["source_type"] == "text_knowledge"]
    row["evidence_sources"] = _evidence_sources_for_path(row, event)
    return row


def _build_event_evidence_package(event: Mapping[str, Any], paths: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    top_path = dict(paths[0]) if paths else {}
    sources = list(top_path.get("evidence_sources") or [])
    return {
        "event_id": event.get("event_id"),
        "evidence_role": "graph_text_structured_fusion_for_model_input",
        "structured_signal": {
            "risk_probability": _event_risk_probability(event),
            "primary_feature": top_path.get("feature"),
            "variable_group": top_path.get("variable_group"),
            "window_scope": "event_precursor_window",
        },
        "graph_evidence": {
            "mechanism": top_path.get("defect_mechanism"),
            "equipment_zone": top_path.get("equipment_zone"),
            "graph_prior": top_path.get("graph_prior"),
            "graph_relation_score": top_path.get("graph_relation_score"),
            "path_library_score": top_path.get("path_library_score"),
            "path_library_match": bool(top_path.get("path_library_match")),
            "path_library_event_count": top_path.get("path_library_event_count"),
            "score_model": top_path.get("score_model"),
        },
        "text_evidence": [
            {
                "source_id": item.get("source_id"),
                "snippet": item.get("snippet"),
                "confidence": item.get("confidence"),
            }
            for item in sources
            if item.get("source_type") == "text_knowledge"
        ],
        "evidence_sources": sources,
        "assistant_policy": "LLM assistant is explanation-only and not causal evidence.",
    }


def _augment_event_for_knowledge_fusion(
    event: Mapping[str, Any],
    kg_index: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    row = dict(event)
    row["process_status"] = row.get("process_status") or _process_status(row)
    ident = dict(row.get("abnormal_identification") or {})
    group_keys = _abnormal_group_keys(ident)
    ident.setdefault("display_group_keys", group_keys)
    if not ident.get("display_groups"):
        ident["display_groups"] = [DISPLAY_LABELS.get(str(group), str(group)) for group in group_keys]
    row["abnormal_identification"] = ident
    trace = dict(row.get("traceability") or {})
    paths = [_augment_trace_path(path, row, kg_index) for path in trace.get("top_k_paths", []) or []]
    paths = sorted(paths, key=lambda item: _as_score(item.get("final_score") or item.get("path_score"), 0.0), reverse=True)
    trace["top_k_paths"] = paths
    trace["evidence_package"] = _build_event_evidence_package(row, paths)
    row["traceability"] = trace
    recommendation = dict(row.get("recommendation") or {})
    recommendation.setdefault("verification_actions", ["现场复核关键变量趋势", "检查图谱证据来源", "记录处置反馈用于闭环评估"])
    recommendation.setdefault("evidence_binding", "recommendation_linked_to_top_traceability_path")
    row["recommendation"] = recommendation
    return row


def _make_entity(entity_id: str, label: str, entity_type: str, source_type: str, confidence: float = 0.8) -> dict[str, Any]:
    return {
        "id": entity_id,
        "label": label,
        "entity_type": entity_type,
        "source_type": source_type,
        "confidence": round(_as_score(confidence), 3),
        "review_status": "system_seed",
    }


def _build_knowledge_entities(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    entities: dict[str, dict[str, Any]] = {}
    for step in PROCESS_STEPS:
        ref = _canonical_entity_parts("process_step", step["id"])
        _merge_entity(
            entities,
            _entity_id("process_step", step["id"]),
            str(step["name"]),
            "process_step",
            "structured_production",
            0.95,
            canonical_key=str(ref["key"]),
            aliases=ref["aliases"],
            disambiguation_rule=str(ref["rule"]),
        )
    for mechanism in DISPLAY_LABELS:
        ref = _canonical_entity_parts("defect_mechanism", mechanism)
        _merge_entity(
            entities,
            _entity_id("defect_mechanism", mechanism),
            str(ref["label"]),
            "defect_mechanism",
            "expert_seed",
            0.9,
            canonical_key=str(ref["key"]),
            aliases=ref["aliases"],
            disambiguation_rule=str(ref["rule"]),
        )
        quality_ref = _canonical_entity_parts("quality_class", mechanism)
        _merge_entity(
            entities,
            _entity_id("quality_class", mechanism),
            str(quality_ref["label"]),
            "quality_class",
            "expert_seed",
            0.9,
            canonical_key=str(quality_ref["key"]),
            aliases=quality_ref["aliases"],
            disambiguation_rule=str(quality_ref["rule"]),
        )
        text_ref = _canonical_entity_parts("text_evidence", mechanism)
        _merge_entity(
            entities,
            _entity_id("text_evidence", mechanism),
            str(text_ref["label"]),
            "text_evidence",
            "text_knowledge",
            0.72,
            canonical_key=str(text_ref["key"]),
            aliases=text_ref["aliases"],
            disambiguation_rule=str(text_ref["rule"]),
        )
    for event in events:
        for path in (event.get("traceability", {}) or {}).get("top_k_paths", []) or []:
            feature = str(path.get("feature") or "")
            variable_group = str(path.get("variable_group") or "")
            zone = str(path.get("equipment_zone") or "")
            process_state = str(path.get("process_state") or path.get("defect_mechanism") or "")
            event_target = str(path.get("event_target") or path.get("defect_mechanism") or "")
            action = ""
            for node in path.get("nodes", []) or []:
                if node.get("layer") == "correction_action":
                    action = str(node.get("label") or node.get("id") or "")
            if feature:
                base_ref = _canonical_entity_parts("base_variable", feature)
                _merge_entity(
                    entities,
                    _entity_id("base_variable", feature),
                    str(base_ref["label"]),
                    "base_variable",
                    "structured_production",
                    0.82,
                    canonical_key=str(base_ref["key"]),
                    aliases=base_ref["aliases"],
                    disambiguation_rule=str(base_ref["rule"]),
                )
                ref = _canonical_entity_parts("window_feature", feature)
                _merge_entity(
                    entities,
                    _entity_id("window_feature", feature),
                    str(ref["label"]),
                    "window_feature",
                    "structured_production",
                    0.82,
                    canonical_key=str(ref["key"]),
                    aliases=ref["aliases"],
                    disambiguation_rule=str(ref["rule"]),
                )
            if variable_group:
                ref = _canonical_entity_parts("variable_group", variable_group)
                _merge_entity(
                    entities,
                    _entity_id("variable_group", variable_group),
                    str(ref["label"]),
                    "variable_group",
                    "structured_production",
                    0.84,
                    canonical_key=str(ref["key"]),
                    aliases=ref["aliases"],
                    disambiguation_rule=str(ref["rule"]),
                )
            if zone:
                ref = _canonical_entity_parts("equipment_zone", zone)
                _merge_entity(
                    entities,
                    _entity_id("equipment_zone", zone),
                    str(ref["label"]),
                    "equipment_zone",
                    "structured_production",
                    0.82,
                    canonical_key=str(ref["key"]),
                    aliases=ref["aliases"],
                    disambiguation_rule=str(ref["rule"]),
                )
            if process_state:
                ref = _canonical_entity_parts("process_state", process_state)
                _merge_entity(
                    entities,
                    _entity_id("process_state", process_state),
                    str(ref["label"]),
                    "process_state",
                    "knowledge_graph",
                    0.8,
                    canonical_key=str(ref["key"]),
                    aliases=ref["aliases"],
                    disambiguation_rule=str(ref["rule"]),
                )
            if event_target:
                ref = _canonical_entity_parts("quality_class", event_target)
                _merge_entity(
                    entities,
                    _entity_id("quality_class", event_target),
                    str(ref["label"]),
                    "quality_class",
                    "expert_seed",
                    0.88,
                    canonical_key=str(ref["key"]),
                    aliases=ref["aliases"],
                    disambiguation_rule=str(ref["rule"]),
                )
            if action:
                ref = _canonical_entity_parts("correction_action", action)
                _merge_entity(
                    entities,
                    _entity_id("correction_action", action),
                    str(ref["label"]),
                    "correction_action",
                    "text_knowledge",
                    0.76,
                    canonical_key=str(ref["key"]),
                    aliases=ref["aliases"],
                    disambiguation_rule=str(ref["rule"]),
                )
            if variable_group and zone and event_target:
                path_key = _safe_id(
                    _canonical_entity_parts("variable_group", variable_group)["key"],
                    _canonical_entity_parts("equipment_zone", zone)["key"],
                    _canonical_entity_parts("defect_mechanism", event_target)["key"],
                )
                case_ref = _canonical_entity_parts("reviewed_quality_case", path_key)
                _merge_entity(
                    entities,
                    _entity_id("reviewed_quality_case", path_key),
                    f"{_canonical_entity_parts('variable_group', variable_group)['label']} - {_canonical_entity_parts('defect_mechanism', event_target)['label']}历史案例",
                    "reviewed_quality_case",
                    "case_review",
                    0.74,
                    canonical_key=str(case_ref["key"]),
                    aliases=case_ref["aliases"],
                    disambiguation_rule=str(case_ref["rule"]),
                )
    return list(entities.values())


def _make_relation(source: str, target: str, relation_type: str, label: str, confidence: float, source_type: str, snippet: str) -> dict[str, Any]:
    return {
        "id": f"rel::{_safe_id(source, relation_type, target)}",
        "source": source,
        "target": target,
        "relation_type": relation_type,
        "label": label,
        "confidence": round(_as_score(confidence), 3),
        "source_type": source_type,
        "evidence_snippet": snippet,
    }


def _path_action_text(path: Mapping[str, Any]) -> str:
    for node in path.get("nodes", []) or []:
        if node.get("layer") == "correction_action":
            return str(node.get("label") or node.get("id") or "")
    return ""


def _build_knowledge_relations(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    relations: dict[str, dict[str, Any]] = {}
    for source_step, target_step in PROCESS_FLOW_EDGES:
        _merge_relation(
            relations,
            _make_relation(
                _entity_id("process_step", source_step),
                _entity_id("process_step", target_step),
                "PRECEDES_PROCESS",
                "工艺顺序",
                0.88,
                "expert_seed",
                f"{PROCESS_LABELS.get(source_step, source_step)} 上游衔接 {PROCESS_LABELS.get(target_step, target_step)}。",
            ),
        )
    for mechanism, step_id in MECHANISM_TO_STEP.items():
        source = _entity_id("process_step", step_id)
        target = _entity_id("defect_mechanism", mechanism)
        relation = _make_relation(
            source,
            target,
            "HAS_RISK_MECHANISM",
            "工序关联机理",
            0.9,
            "expert_seed",
            f"{PROCESS_LABELS.get(step_id, step_id)} 关联 {DISPLAY_LABELS.get(mechanism, mechanism)}。",
        )
        _merge_relation(relations, relation)
        _merge_relation(
            relations,
            _make_relation(
                _entity_id("defect_mechanism", mechanism),
                _entity_id("quality_class", mechanism),
                "CAUSES_QUALITY_RISK",
                "机理对应质量异常",
                0.88,
                "expert_seed",
                f"{DISPLAY_LABELS.get(mechanism, mechanism)} 是质量异常分类和现场复核的统一标签。",
            ),
        )
        _merge_relation(
            relations,
            _make_relation(
                _entity_id("text_evidence", mechanism),
                _entity_id("defect_mechanism", mechanism),
                "SUPPORTED_BY_TEXT",
                "文本知识支持机理",
                0.72,
                "text_knowledge",
                f"工艺规程、异常报告和专家经验文本可补充 {DISPLAY_LABELS.get(mechanism, mechanism)} 的机理依据。",
            ),
        )
    observed_zones: set[str] = set()
    for event in events:
        for path in (event.get("traceability", {}) or {}).get("top_k_paths", []) or []:
            feature = str(path.get("feature") or "")
            variable_group = str(path.get("variable_group") or "")
            zone = str(path.get("equipment_zone") or "")
            mechanism = str(path.get("defect_mechanism") or "")
            process_state = str(path.get("process_state") or mechanism)
            event_target = str(path.get("event_target") or mechanism)
            action = _path_action_text(path)
            base_ref = _canonical_entity_parts("base_variable", feature)
            feature_ref = _canonical_entity_parts("window_feature", feature)
            variable_ref = _canonical_entity_parts("variable_group", variable_group)
            zone_ref = _canonical_entity_parts("equipment_zone", zone)
            process_state_ref = _canonical_entity_parts("process_state", process_state)
            mechanism_ref = _canonical_entity_parts("defect_mechanism", mechanism)
            event_target_ref = _canonical_entity_parts("quality_class", event_target)
            zone_key = str(zone_ref.get("key") or zone)
            path_key = _safe_id(variable_ref.get("key"), zone_ref.get("key"), mechanism_ref.get("key"))
            if zone_key:
                observed_zones.add(zone_key)
            score = _as_score(path.get("final_score") or path.get("path_score"), 0.55)
            if feature:
                relation = _make_relation(
                    _entity_id("base_variable", feature),
                    _entity_id("window_feature", feature),
                    "HAS_STAT_FEATURE",
                    "基础变量生成窗口指标",
                    0.76 + 0.12 * score,
                    "structured_production",
                    f"{base_ref['label']} 在实时窗口中形成 {feature_ref['label']}，用于异常预警和溯源排序。",
                )
                _merge_relation(relations, relation)
            if feature and variable_group:
                relation = _make_relation(
                    _entity_id("window_feature", feature),
                    _entity_id("variable_group", variable_group),
                    "BELONGS_TO_VARIABLE_GROUP",
                    "变量归属",
                    0.78 + 0.12 * score,
                    "structured_production",
                    f"{feature_ref['label']} 归入 {variable_ref['label']} 信号组。",
                )
                _merge_relation(relations, relation)
            if variable_group and zone:
                relation = _make_relation(
                    _entity_id("variable_group", variable_group),
                    _entity_id("equipment_zone", zone),
                    "OBSERVED_IN_ZONE",
                    "变量组观测区域",
                    0.74 + 0.12 * score,
                    "structured_production",
                    f"{variable_ref['label']} 在 {zone_ref['label']} 工艺位置形成事件窗口证据。",
                )
                _merge_relation(relations, relation)
            if zone and mechanism:
                relation = _make_relation(
                    _entity_id("equipment_zone", zone),
                    _entity_id("defect_mechanism", mechanism),
                    "INDICATES_MECHANISM",
                    "区域指向异常机理",
                    0.68 + 0.22 * score,
                    "knowledge_graph",
                    f"{zone_ref['label']} 的异常信号指向 {mechanism_ref['label']}。",
                )
                _merge_relation(relations, relation)
            if variable_group and mechanism:
                relation = _make_relation(
                    _entity_id("variable_group", variable_group),
                    _entity_id("defect_mechanism", mechanism),
                    "SUPPORTS_MECHANISM",
                    "变量组支持异常机理",
                    0.64 + 0.24 * score,
                    "knowledge_graph",
                    f"{variable_ref['label']} 的实时波动支持 {mechanism_ref['label']} 机理判断。",
                )
                _merge_relation(relations, relation)
            if variable_group and process_state:
                relation = _make_relation(
                    _entity_id("variable_group", variable_group),
                    _entity_id("process_state", process_state),
                    "SUPPORTS_PROCESS_STATE",
                    "变量组支持工艺状态判断",
                    0.66 + 0.20 * score,
                    "knowledge_graph",
                    f"{variable_ref['label']} 的实时状态用于判断 {process_state_ref['label']}。",
                )
                _merge_relation(relations, relation)
            if process_state and mechanism:
                relation = _make_relation(
                    _entity_id("process_state", process_state),
                    _entity_id("defect_mechanism", mechanism),
                    "STATE_INDICATES_MECHANISM",
                    "工艺状态指向异常机理",
                    0.67 + 0.20 * score,
                    "knowledge_graph",
                    f"{process_state_ref['label']} 状态异常时，优先关联 {mechanism_ref['label']}。",
                )
                _merge_relation(relations, relation)
            if mechanism and event_target:
                relation = _make_relation(
                    _entity_id("defect_mechanism", mechanism),
                    _entity_id("quality_class", event_target),
                    "CAUSES_QUALITY_RISK",
                    "机理对应质量异常",
                    0.70 + 0.18 * score,
                    "knowledge_graph",
                    f"{mechanism_ref['label']} 可解释为 {event_target_ref['label']} 的异常风险。",
                )
                _merge_relation(relations, relation)
            if mechanism:
                relation = _make_relation(
                    _entity_id("text_evidence", mechanism),
                    _entity_id("defect_mechanism", mechanism),
                    "SUPPORTED_BY_TEXT",
                    "文本知识支持机理",
                    0.63 + 0.14 * score,
                    "text_knowledge",
                    f"文本知识库为 {mechanism_ref['label']} 提供工艺机理、异常报告或专家经验依据。",
                )
                _merge_relation(relations, relation)
            if variable_group and zone and mechanism:
                case_id = _entity_id("reviewed_quality_case", path_key)
                relation = _make_relation(
                    case_id,
                    _entity_id("defect_mechanism", mechanism),
                    "SUPPORTED_BY_CASE",
                    "历史案例支持机理",
                    0.58 + 0.20 * score,
                    "case_review",
                    f"历史复盘案例将 {variable_ref['label']}、{zone_ref['label']} 与 {mechanism_ref['label']} 绑定为可复核链路。",
                )
                _merge_relation(relations, relation)
                relation = _make_relation(
                    case_id,
                    _entity_id("variable_group", variable_group),
                    "CASE_HAS_SIGNAL",
                    "历史案例包含关键信号",
                    0.56 + 0.18 * score,
                    "case_review",
                    f"历史复盘案例包含 {variable_ref['label']} 信号证据，可用于相似事件检索。",
                )
                _merge_relation(relations, relation)
            if mechanism and action:
                action_ref = _canonical_entity_parts("correction_action", action)
                relation = _make_relation(
                    _entity_id("defect_mechanism", mechanism),
                    _entity_id("correction_action", action),
                    "SUGGESTS_ACTION",
                    "机理建议处置",
                    0.70 + 0.18 * score,
                    "expert_rule",
                    f"{mechanism_ref['label']} 命中时建议执行：{action_ref['label']}。",
                )
                _merge_relation(relations, relation)
    for zone_key in sorted(observed_zones):
        if zone_key not in PROCESS_LABELS:
            continue
        zone_ref = _canonical_entity_parts("equipment_zone", zone_key)
        relation = _make_relation(
            _entity_id("equipment_zone", zone_key),
            _entity_id("process_step", zone_key),
            "ZONE_BELONGS_TO_PROCESS",
            "区域归属工序",
            0.86,
            "expert_seed",
            f"{zone_ref['label']} 归属于 {PROCESS_LABELS.get(zone_key, zone_key)} 工序。",
        )
        _merge_relation(relations, relation)
    return list(relations.values())


def _build_path_library(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    library: dict[str, dict[str, Any]] = {}
    for event in events:
        for path in (event.get("traceability", {}) or {}).get("top_k_paths", []) or []:
            mechanism_ref = _canonical_entity_parts("defect_mechanism", path.get("defect_mechanism") or "unknown")
            variable_ref = _canonical_entity_parts("variable_group", path.get("variable_group") or "unknown")
            zone_ref = _canonical_entity_parts("equipment_zone", path.get("equipment_zone") or "unknown")
            mechanism = str(mechanism_ref["key"])
            variable_group = str(variable_ref["key"])
            zone = str(zone_ref["key"])
            key = _safe_id(variable_group, zone, mechanism)
            item = library.setdefault(
                key,
                {
                    "path_id": f"path::{key}",
                    "variable_group": str(variable_ref["label"]),
                    "equipment_zone": str(zone_ref["label"]),
                    "defect_mechanism": mechanism,
                    "mechanism_label": str(mechanism_ref["label"]),
                    "canonical_key": key,
                    "process_consistency": _process_consistency_score(mechanism, zone, variable_group),
                    "event_count": 0,
                    "avg_final_score": 0.0,
                    "evidence_types": ["structured_production", "knowledge_graph", "text_knowledge", "expert_rule"],
                },
            )
            item["event_count"] += 1
            item["avg_final_score"] += _as_score(path.get("final_score") or path.get("path_score"), 0.0)
    for item in library.values():
        count = max(1, int(item["event_count"]))
        item["avg_final_score"] = round(float(item["avg_final_score"]) / count, 3)
    return sorted(library.values(), key=lambda row: (-row["event_count"], -row["avg_final_score"]))[:60]


def _counts_by_key(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts


def _graph_connectivity_summary(nodes: Sequence[Mapping[str, Any]], edges: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    degree = {str(node.get("id")): 0 for node in nodes}
    for edge in edges:
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        if source in degree:
            degree[source] += 1
        if target in degree:
            degree[target] += 1
    isolated = [node_id for node_id, value in degree.items() if value == 0]
    low_degree = [node_id for node_id, value in degree.items() if value <= 1]
    node_count = max(1, len(nodes))
    return {
        "isolated_node_count": len(isolated),
        "low_degree_node_count": len(low_degree),
        "isolated_node_rate": round(len(isolated) / node_count, 3),
        "low_degree_node_rate": round(len(low_degree) / node_count, 3),
        "avg_degree": round(sum(degree.values()) / node_count, 3),
        "isolated_node_ids": isolated[:20],
    }


def _disambiguation_summary(nodes: Sequence[Mapping[str, Any]], edges: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    merged_nodes = [node for node in nodes if int(node.get("evidence_count") or 1) > 1 or len(node.get("aliases") or []) > 1]
    merged_edges = [edge for edge in edges if int(edge.get("evidence_count") or 1) > 1]
    return {
        "policy": "canonical_alias_type_scope_merge_v1",
        "node_merge_count": len(merged_nodes),
        "edge_merge_count": len(merged_edges),
        "rule_count": 5,
        "rules": [
            {
                "rule_id": "R1",
                "name": "规范名归一",
                "description": "英文变量、中文字段、单位写法和统计后缀先拆分为规范变量名与统计量。",
                "examples": ["热交换平均(西)/℃_last -> 热交换平均（最新值）", "TD_avg_temp_last -> 中包平均温度（最新值）"],
            },
            {
                "rule_id": "R2",
                "name": "同义词合并",
                "description": "中包/tundish/TD、结晶器/mold、mold_heat_transfer/传热冷却等进入统一工艺实体。",
                "examples": ["mold_heat_transfer -> 传热/冷却", "sequence_transition -> 过渡段序列"],
            },
            {
                "rule_id": "R3",
                "name": "类型隔离",
                "description": "相同文本在变量组、工序区域、异常机理中使用不同实体前缀，避免跨类型误合并。",
                "examples": ["heat_transfer 信号组 != heat_transfer 工序位置"],
            },
            {
                "rule_id": "R4",
                "name": "证据累积",
                "description": "重复实体和重复边不覆盖旧信息，而是保留别名、来源类型、证据次数和最高置信度。",
                "examples": ["多个热交换字段共同增强传热不均链路"],
            },
            {
                "rule_id": "R5",
                "name": "工艺一致性校验",
                "description": "路径评分时检查变量组、工艺位置和异常机理是否符合连铸工艺域。",
                "examples": ["水口流量 -> 流量控制 -> 拉速/塞棒/流量异常"],
            },
        ],
        "top_merged_nodes": [
            {
                "id": node.get("id"),
                "label": node.get("label"),
                "entity_type": node.get("entity_type"),
                "evidence_count": node.get("evidence_count"),
                "aliases": (node.get("aliases") or [])[:6],
            }
            for node in sorted(merged_nodes, key=lambda row: int(row.get("evidence_count") or 1), reverse=True)[:12]
        ],
        "top_merged_edges": [
            {
                "id": edge.get("id"),
                "source": edge.get("source"),
                "target": edge.get("target"),
                "relation_type": edge.get("relation_type"),
                "evidence_count": edge.get("evidence_count"),
                "confidence": edge.get("confidence"),
            }
            for edge in sorted(merged_edges, key=lambda row: int(row.get("evidence_count") or 1), reverse=True)[:12]
        ],
    }


def _build_knowledge_graph(events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    nodes = _build_knowledge_entities(events)
    edges = _build_knowledge_relations(events)
    path_library = _build_path_library(events)
    disambiguation = _disambiguation_summary(nodes, edges)
    connectivity = _graph_connectivity_summary(nodes, edges)
    mechanism_coverage = sorted(
        {
            str(path.get("defect_mechanism"))
            for event in events
            for path in (event.get("traceability", {}) or {}).get("top_k_paths", []) or []
            if path.get("defect_mechanism")
        }
    )
    return {
        "backend": "json_graph_v1_neo4j_ready",
        "summary": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "path_template_count": len(path_library),
            "node_type_counts": _counts_by_key(nodes, "entity_type"),
            "relation_type_counts": _counts_by_key(edges, "relation_type"),
            "mechanism_coverage": mechanism_coverage,
            "fusion_role": "evidence_to_graph_enhanced_model",
            "connectivity": connectivity,
            "entity_disambiguation": {
                "policy": disambiguation["policy"],
                "node_merge_count": disambiguation["node_merge_count"],
                "edge_merge_count": disambiguation["edge_merge_count"],
                "rule_count": disambiguation["rule_count"],
            },
        },
        "nodes": nodes,
        "edges": edges,
        "path_library": path_library,
        "disambiguation": disambiguation,
    }


def _event_kg_focus_ids(event: Mapping[str, Any]) -> set[str]:
    focus: set[str] = set()
    for path in (event.get("traceability", {}) or {}).get("top_k_paths", []) or []:
        canonical = dict(path.get("canonical_path") or _canonical_path_snapshot(path))
        for key in (
            "base_variable_id",
            "feature_id",
            "variable_group_id",
            "equipment_zone_id",
            "process_state_id",
            "mechanism_id",
            "quality_class_id",
        ):
            value = str(canonical.get(key) or "")
            if value:
                focus.add(value)
        mechanism_key = str(canonical.get("mechanism_key") or path.get("defect_mechanism") or "")
        if mechanism_key:
            focus.add(_entity_id("text_evidence", mechanism_key))
        action = _path_action_text(path)
        if action:
            focus.add(_entity_id("correction_action", action))
        variable_key = _canonical_entity_parts("variable_group", path.get("variable_group")).get("key")
        zone_key = _canonical_entity_parts("equipment_zone", path.get("equipment_zone")).get("key")
        path_key = _safe_id(variable_key, zone_key, mechanism_key)
        if path_key:
            focus.add(_entity_id("reviewed_quality_case", path_key))
    for step in event.get("process_status", []) or []:
        if str(step.get("status") or "") in {"active", "warning", "danger"}:
            focus.add(_entity_id("process_step", step.get("id")))
    return {item for item in focus if item}


def _expected_kg_links_for_event(event: Mapping[str, Any]) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    for path in (event.get("traceability", {}) or {}).get("top_k_paths", []) or []:
        canonical = dict(path.get("canonical_path") or _canonical_path_snapshot(path))
        mechanism_key = str(canonical.get("mechanism_key") or path.get("defect_mechanism") or "")
        variable_key = _canonical_entity_parts("variable_group", path.get("variable_group")).get("key")
        zone_key = _canonical_entity_parts("equipment_zone", path.get("equipment_zone")).get("key")
        path_key = _safe_id(variable_key, zone_key, mechanism_key)
        candidates = [
            ("base_variable_id", "feature_id", "HAS_STAT_FEATURE", "基础变量生成窗口指标"),
            ("feature_id", "variable_group_id", "BELONGS_TO_VARIABLE_GROUP", "窗口指标归属变量组"),
            ("variable_group_id", "equipment_zone_id", "OBSERVED_IN_ZONE", "变量组观测工艺区域"),
            ("equipment_zone_id", "mechanism_id", "INDICATES_MECHANISM", "工艺区域指向异常机理"),
            ("variable_group_id", "process_state_id", "SUPPORTS_PROCESS_STATE", "变量组支持工艺状态"),
            ("process_state_id", "mechanism_id", "STATE_INDICATES_MECHANISM", "工艺状态指向异常机理"),
            ("mechanism_id", "quality_class_id", "CAUSES_QUALITY_RISK", "机理对应质量异常"),
        ]
        for source_key, target_key, relation_type, label in candidates:
            source = str(canonical.get(source_key) or "")
            target = str(canonical.get(target_key) or "")
            if source and target:
                links.append({"source": source, "target": target, "relation_type": relation_type, "label": label})
        if mechanism_key:
            links.append(
                {
                    "source": _entity_id("text_evidence", mechanism_key),
                    "target": str(canonical.get("mechanism_id") or ""),
                    "relation_type": "SUPPORTED_BY_TEXT",
                    "label": "文本知识支持机理",
                }
            )
        if path_key and mechanism_key:
            links.append(
                {
                    "source": _entity_id("reviewed_quality_case", path_key),
                    "target": str(canonical.get("mechanism_id") or ""),
                    "relation_type": "SUPPORTED_BY_CASE",
                    "label": "历史案例支持机理",
                }
            )
    deduped: dict[str, dict[str, str]] = {}
    for link in links:
        if not link.get("source") or not link.get("target"):
            continue
        deduped[_kg_relation_key(link["source"], link["target"], link["relation_type"])] = link
    return list(deduped.values())


def _build_event_kg_subgraph(event: Mapping[str, Any], kg: Mapping[str, Any], hops: int = 1) -> dict[str, Any]:
    all_nodes = list(kg.get("nodes", []) or [])
    all_edges = list(kg.get("edges", []) or [])
    node_ids = {str(node.get("id")) for node in all_nodes}
    focus_ids = _event_kg_focus_ids(event) & node_ids
    visible_ids = set(focus_ids)
    for _ in range(max(0, hops)):
        for edge in all_edges:
            source = str(edge.get("source") or "")
            target = str(edge.get("target") or "")
            if source in visible_ids:
                visible_ids.add(target)
            if target in visible_ids:
                visible_ids.add(source)
    if not visible_ids:
        visible_ids = {str(node.get("id")) for node in all_nodes[:36]}
    if len(visible_ids) > 90:
        degree: dict[str, int] = {node_id: 0 for node_id in visible_ids}
        for edge in all_edges:
            source = str(edge.get("source") or "")
            target = str(edge.get("target") or "")
            if source in degree:
                degree[source] += 1
            if target in degree:
                degree[target] += 1
        visible_ids = set(sorted(visible_ids, key=lambda item: (item not in focus_ids, -degree.get(item, 0), item))[:90])
    visible_nodes = [node for node in all_nodes if str(node.get("id")) in visible_ids]
    visible_edges = [
        edge
        for edge in all_edges
        if str(edge.get("source")) in visible_ids and str(edge.get("target")) in visible_ids
    ][:180]
    edge_keys = {
        _kg_relation_key(str(edge.get("source") or ""), str(edge.get("target") or ""), str(edge.get("relation_type") or ""))
        for edge in all_edges
    }
    missing_links = [
        link
        for link in _expected_kg_links_for_event(event)
        if _kg_relation_key(link["source"], link["target"], link["relation_type"]) not in edge_keys
    ]
    matched_path_ids = list(
        dict.fromkeys(
            str((path.get("graph_evidence_detail") or {}).get("path_library_key") or "")
            for path in (event.get("traceability", {}) or {}).get("top_k_paths", []) or []
            if (path.get("graph_evidence_detail") or {}).get("path_library_key")
        )
    )
    return {
        "event_id": event.get("event_id"),
        "hops": hops,
        "focus_node_ids": sorted(focus_ids),
        "nodes": visible_nodes,
        "edges": visible_edges,
        "missing_links": missing_links,
        "matched_path_ids": matched_path_ids,
    }


def _event_kg_fusion_summary(event: Mapping[str, Any], kg: Mapping[str, Any]) -> dict[str, Any]:
    subgraph = _build_event_kg_subgraph(event, kg, hops=1)
    paths = list((event.get("traceability", {}) or {}).get("top_k_paths", []) or [])
    matched_relation_count = sum(
        int((path.get("graph_evidence_detail") or {}).get("matched_relation_count") or 0)
        for path in paths
    )
    avg_graph_prior = (
        sum(_as_score(path.get("graph_prior"), 0.0) for path in paths) / len(paths)
        if paths
        else 0.0
    )
    avg_final_score = (
        sum(_as_score(path.get("final_score") or path.get("path_score"), 0.0) for path in paths) / len(paths)
        if paths
        else 0.0
    )
    avg_model_score = (
        sum(_as_score(path.get("path_score"), 0.0) for path in paths) / len(paths)
        if paths
        else 0.0
    )
    return {
        "mapped_entity_count": len(subgraph["focus_node_ids"]),
        "event_subgraph_node_count": len(subgraph["nodes"]),
        "event_subgraph_edge_count": len(subgraph["edges"]),
        "missing_link_count": len(subgraph["missing_links"]),
        "graph_path_hit_count": matched_relation_count,
        "avg_graph_prior": round(avg_graph_prior, 3),
        "avg_final_score": round(avg_final_score, 3),
        "score_delta_after_kg": round(avg_final_score - avg_model_score, 3),
        "focus_node_ids": subgraph["focus_node_ids"],
        "matched_path_ids": subgraph["matched_path_ids"],
        "role": "kg_as_evidence_prior_for_path_scoring",
    }


def _attach_event_kg_fusion(event: Mapping[str, Any], kg: Mapping[str, Any]) -> dict[str, Any]:
    row = dict(event)
    row["kg_fusion"] = _event_kg_fusion_summary(row, kg)
    trace = dict(row.get("traceability") or {})
    evidence = dict(trace.get("evidence_package") or {})
    evidence["kg_fusion_summary"] = row["kg_fusion"]
    trace["evidence_package"] = evidence
    row["traceability"] = trace
    return row


def _build_data_sources(events: Sequence[Mapping[str, Any]], summary: Mapping[str, Any]) -> dict[str, Any]:
    production_profile = _production_source_profile_from_summary()
    source_records = int(production_profile.get("records") or len(events))
    return {
        "structured_sources": [
            {
                "id": "continuous_casting_real_records_csv",
                "name": "连铸/保护渣真实生产记录（品质异常代码标签版）",
                "source_type": "structured_production",
                "status": production_profile.get("source_status", "available"),
                "records": source_records,
                "columns": int(production_profile.get("columns") or 0),
                "time_range": production_profile.get("time_range", {}),
                "path": str(STRUCTURED_CSV_PATH),
                "label_policy": production_profile.get("label_policy"),
                "fields": list(MODEL_FEATURE_MAP.keys()),
                "alignment_keys": ["材料跟踪号", "炼钢材料号", "铸机号", "连铸处理号", "中间包号", "记录识别码"],
            },
            {
                "id": "recovered_traceability_event_samples",
                "name": "已恢复异常预警溯源解释样本",
                "source_type": "processed_event_explanation",
                "status": "available",
                "records": len(events),
                "fields": ["risk_warning", "abnormal_identification", "traceability", "recommendation"],
                "alignment_keys": ["event_id", "sequence_no"],
            }
        ],
        "text_sources": [
            {
                "id": "text_rules_reports_rag",
                "name": "工艺规程/异常报告/专家经验文本库",
                "source_type": "unstructured_text",
                "status": "ready_for_extraction",
                "documents": 6,
                "extraction_scope": ["entity", "relation", "event", "source_snippet"],
            }
        ],
        "field_mapping": _feature_mapping_rows(),
        "event_window_dataset": {
            "status": "processed_from_real_csv",
            "event_count": len(events),
            "source_record_count": source_records,
            "window_strategy": "row_as_event_window_v1",
            "processed_profile": PRODUCTION_PROFILE_FILENAME,
            "processed_window_preview": PRODUCTION_WINDOWS_FILENAME,
            "summary": dict(summary),
        },
        "quality_checks": {
            "structured_schema": "pass",
            "text_extraction_schema": "pass",
            "event_alignment": "csv_alignment_keys_ready",
        },
    }


def _build_knowledge_extraction(kg: Mapping[str, Any]) -> dict[str, Any]:
    text_entities = [node for node in kg.get("nodes", []) if node.get("source_type") in {"text_knowledge", "expert_seed"}]
    text_relations = [edge for edge in kg.get("edges", []) if edge.get("source_type") in {"text_knowledge", "knowledge_graph", "expert_seed"}]
    return {
        "jobs": [
            {
                "job_id": "kx-demo-001",
                "status": "completed",
                "input_sources": ["text_rules_reports_rag"],
                "extractors": ["NER", "RE", "event_extraction"],
                "entity_count": len(text_entities),
                "relation_count": len(text_relations),
                "output_target": "knowledge_graph.json_graph_v1",
            }
        ],
        "entities": text_entities,
        "relations": text_relations,
    }


def _build_model_runs(events: Sequence[Mapping[str, Any]], kg: Mapping[str, Any]) -> list[dict[str, Any]]:
    cascade = _load_quality_modeling_artifacts(preview_limit=5)
    cascade_metrics = cascade.get("metrics", {}) or {}
    return [
        {
            "run_id": "quality-code-cascade-2022q4",
            "model_contract": "quality_code_cascade_warning_identification_trace_v1",
            "status": "completed",
            "algorithm_status": "binary_gate_multiclass_multilabel_trace_evidence_active",
            "scoring_model": "random_forest_warning_identification_plus_ovr_logistic_multilabel",
            "input_artifacts": [
                "X_process_features.csv",
                "y_quality_multiclass.csv",
                "y_quality_multilabel.csv",
                "knowledge_graph.json_graph_v1",
            ],
            "output_artifacts": [
                "binary_warning_probability",
                "cascade_final_label",
                "companion_abnormal_scores",
                "traceability_candidate_evidence",
            ],
            "event_count": int((cascade.get("dataset") or {}).get("n_rows") or len(events)),
            "test_metrics": {
                "binary_macro_f1": (cascade_metrics.get("binary_test") or {}).get("macro_f1"),
                "binary_pr_auc": (cascade_metrics.get("binary_test") or {}).get("pr_auc"),
                "multiclass_macro_f1": (cascade_metrics.get("multiclass_test") or {}).get("macro_f1"),
                "multilabel_macro_f1": (cascade_metrics.get("multilabel_test") or {}).get("macro_f1"),
            },
            "gate_policy": cascade.get("gate_policy"),
            "kg_node_count": int((kg.get("summary") or {}).get("node_count") or 0),
            "kg_edge_count": int((kg.get("summary") or {}).get("edge_count") or 0),
            "artifact_dir": str(QUALITY_MODELING_DIR),
        }
    ]


def _build_evaluation(events: Sequence[Mapping[str, Any]], metrics: Mapping[str, Any], kg: Mapping[str, Any]) -> dict[str, Any]:
    path_count = sum(len((event.get("traceability", {}) or {}).get("top_k_paths", []) or []) for event in events)
    evidence_count = sum(
        len(path.get("evidence_sources", []) or [])
        for event in events
        for path in (event.get("traceability", {}) or {}).get("top_k_paths", []) or []
    )
    cascade = _load_quality_modeling_artifacts(preview_limit=5)
    return {
        "summary": {
            "event_count": len(events),
            "path_count": path_count,
            "avg_evidence_sources_per_path": round(evidence_count / max(1, path_count), 3),
            "kg_node_count": int((kg.get("summary") or {}).get("node_count") or 0),
            "kg_edge_count": int((kg.get("summary") or {}).get("edge_count") or 0),
            "metrics": dict(metrics),
            "quality_code_cascade_model": {
                "status": cascade.get("status"),
                "contract": cascade.get("model_contract"),
                "metrics": cascade.get("metrics"),
                "dataset": cascade.get("dataset"),
                "features": {
                    "original_count": (cascade.get("features") or {}).get("original_count"),
                    "kept_count": (cascade.get("features") or {}).get("kept_count"),
                    "dropped_correlated_count": (cascade.get("features") or {}).get("dropped_correlated_count"),
                },
                "gate_policy": cascade.get("gate_policy"),
            },
        },
        "evidence_quality": {
            "structured_signal_coverage": 1.0 if events else 0.0,
            "kg_evidence_coverage": 1.0 if path_count else 0.0,
            "text_evidence_coverage": 1.0 if evidence_count else 0.0,
            "assistant_causality_policy": "assistant_not_causal_evidence",
            "cascade_traceability_evidence_rows": len(cascade.get("traceability_evidence_preview") or []),
            "cascade_gate_policy": (cascade.get("gate_policy") or {}).get("name"),
        },
    }


def _build_system_artifacts() -> list[dict[str, Any]]:
    return [
        {"artifact_id": "dashboard", "name": "工业实时工作台 HTML", "path": "knowledge_exports/steel_realtime_system_v1/index.html", "status": "generated"},
        {"artifact_id": "seed", "name": "实时系统种子数据", "path": "knowledge_exports/steel_realtime_system_v1/realtime_seed.json", "status": "generated"},
        {"artifact_id": "api_manifest", "name": "API 契约清单", "path": "knowledge_exports/steel_realtime_system_v1/api_manifest.json", "status": "generated"},
        {"artifact_id": "production_data_profile", "name": "全量真实生产记录数据画像", "path": f"knowledge_exports/steel_realtime_system_v1/{PRODUCTION_PROFILE_FILENAME}", "status": "generated"},
        {"artifact_id": "production_event_windows", "name": "全量生产记录事件窗口预览", "path": f"knowledge_exports/steel_realtime_system_v1/{PRODUCTION_WINDOWS_FILENAME}", "status": "generated"},
        {"artifact_id": "quality_model_evidence", "name": "品质异常质量模型实验证据包", "path": "knowledge_exports/quality_modeling_quality_code/model_evidence_bundle.json", "status": "generated" if MODEL_EVIDENCE_BUNDLE_PATH.is_file() else "missing"},
        {"artifact_id": "quality_model_cascade_predictions", "name": "异常预警-异常种类判断-关联异常提示明细", "path": "knowledge_exports/quality_modeling_quality_code/cascade_test_predictions.csv", "status": "generated" if CASCADE_PREDICTIONS_PATH.is_file() else "missing"},
        {"artifact_id": "traceability_candidate_evidence", "name": "质量模型溯源候选证据", "path": "knowledge_exports/quality_modeling_quality_code/traceability_candidate_evidence_test.csv", "status": "generated" if TRACEABILITY_CANDIDATE_EVIDENCE_PATH.is_file() else "missing"},
        {"artifact_id": "vben_module", "name": "Vben Admin 前端模块", "path": "apps/steel-realtime-vben", "status": "source"},
    ]


def _enrich_realtime_seed(seed: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(seed)
    provisional_events = [_augment_event_for_knowledge_fusion(event) for event in out.get("events", []) or []]
    provisional_kg = _build_knowledge_graph(provisional_events)
    kg_index = _kg_evidence_index(provisional_kg)
    events = [_augment_event_for_knowledge_fusion(event, kg_index) for event in provisional_events]
    kg = _build_knowledge_graph(events)
    kg_index = _kg_evidence_index(kg)
    events = [_augment_event_for_knowledge_fusion(event, kg_index) for event in events]
    kg = _build_knowledge_graph(events)
    events = [_attach_event_kg_fusion(event, kg) for event in events]
    out["events"] = events
    out.setdefault("system_name", "钢铁全流程生产异常预警溯源系统")
    out.setdefault("template", "Vben Admin realtime industrial workspace")
    out.setdefault("realtime_mode", "historical_stream_simulation")
    out.setdefault("process_steps", PROCESS_STEPS)
    out.setdefault("display_labels", DISPLAY_LABELS)
    metrics = dict(out.get("metrics") or {})
    summary = dict(out.get("summary") or {})
    out["data_sources"] = out.get("data_sources") or _build_data_sources(events, summary)
    out["knowledge_graph"] = kg
    out["knowledge_extraction"] = out.get("knowledge_extraction") or _build_knowledge_extraction(kg)
    out["model_runs"] = _build_model_runs(events, kg)
    out["evaluation"] = _build_evaluation(events, metrics, kg)
    out["system_artifacts"] = out.get("system_artifacts") or _build_system_artifacts()
    return out


def build_realtime_seed(source_dir: str | Path, max_events: int = 400) -> dict[str, Any]:
    artifacts = load_source_artifacts(source_dir, max_events=max_events)
    metrics = dict(artifacts.get("metrics") or {})
    summary = dict(artifacts.get("summary") or {})
    events = list(artifacts.get("events") or [])
    seed = {
        "system_name": "钢铁全流程生产异常预警溯源系统",
        "template": "Vben Admin realtime industrial workspace",
        "realtime_mode": "historical_stream_simulation",
        "process_steps": PROCESS_STEPS,
        "display_labels": DISPLAY_LABELS,
        "metrics": metrics,
        "summary": summary,
        "events": events,
    }
    return _enrich_realtime_seed(seed)


def _llm_runtime_status() -> dict[str, Any]:
    api_key = str(CONFIG.get("llm_api_key", "") or "").strip()
    base_url = str(CONFIG.get("llm_base_url", "https://api.n1n.ai/v1") or "").strip().rstrip("/")
    model = str(CONFIG.get("llm_model", "gpt-5.5") or "").strip()
    configured = llm_configured(api_key)
    return {
        "enabled": configured,
        "status": "configured" if configured else "not_configured",
        "base_url": base_url,
        "model": model,
        "api_key": "<set>" if configured else "<missing>",
        "role": "assistant_only_not_causal_evidence",
    }


def load_realtime_seed(output_dir: str | Path) -> dict[str, Any]:
    return _enrich_realtime_seed(_read_json(_fs_path(output_dir) / "realtime_seed.json", {"events": []}))


HTML_TEMPLATE = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>钢铁全流程生产异常预警溯源系统</title>
  <style>
    :root {
      --bg:#07111f; --panel:#0d1b2f; --panel2:#10233d; --line:#24405f;
      --ink:#e7f0fb; --muted:#8ea5bd; --cyan:#27d4ff; --blue:#2f7dff;
      --green:#30d180; --yellow:#f4bc45; --red:#ff5c65; --violet:#a889ff;
    }
    * { box-sizing: border-box; }
    body { margin:0; font-family:"Microsoft YaHei", Inter, Arial, sans-serif; background:radial-gradient(circle at 20% 0%, #14375d 0, #07111f 32%, #050b14 100%); color:var(--ink); }
    .app { display:grid; grid-template-columns:260px 1fr; min-height:100vh; }
    .sidebar { background:linear-gradient(180deg,#0b1729,#08111e); border-right:1px solid var(--line); padding:18px 14px; }
    .brand { font-weight:800; font-size:18px; line-height:1.35; margin-bottom:18px; }
    .brand small { color:var(--muted); font-size:12px; font-weight:500; display:block; margin-top:4px; }
    .menu button { width:100%; border:1px solid transparent; background:transparent; color:#b7c8d9; padding:11px 12px; text-align:left; border-radius:8px; cursor:pointer; margin:3px 0; }
    .menu button.active, .menu button:hover { background:#10233d; border-color:#24405f; color:#fff; }
    .main { min-width:0; }
    .topbar { height:64px; display:flex; justify-content:space-between; align-items:center; padding:0 22px; border-bottom:1px solid var(--line); background:rgba(7,17,31,.78); backdrop-filter:blur(10px); }
    .topbar h1 { font-size:19px; margin:0; letter-spacing:0; }
    .top-actions { display:flex; gap:10px; align-items:center; }
    .btn { border:1px solid #2b547d; color:#e7f0fb; background:#10233d; padding:9px 13px; border-radius:8px; cursor:pointer; }
    .btn.primary { border-color:#1fbce8; background:linear-gradient(135deg,#1160bf,#139bc7); }
    .btn.warning { border-color:#9b6b22; background:#2a210f; }
    .content { padding:18px; display:grid; gap:16px; }
    .grid-4 { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; }
    .grid-2 { display:grid; grid-template-columns:1.3fr .7fr; gap:14px; align-items:start; }
    .card { background:linear-gradient(180deg,rgba(16,35,61,.95),rgba(10,24,42,.96)); border:1px solid var(--line); border-radius:12px; padding:15px; box-shadow:0 14px 40px rgba(0,0,0,.22); }
    .card h2, .card h3 { margin:0 0 12px; font-size:16px; }
    .kpi span { color:var(--muted); font-size:12px; }
    .kpi strong { display:block; font-size:26px; margin-top:6px; }
    .muted { color:var(--muted); }
    .status-dot { display:inline-block; width:9px; height:9px; border-radius:50%; margin-right:6px; background:var(--green); box-shadow:0 0 14px currentColor; }
    .status-dot.warning { background:var(--yellow); }
    .status-dot.danger { background:var(--red); }
    .steel-process-map { position:relative; overflow:hidden; min-height:274px; background:linear-gradient(180deg,#09182b,#07111f); }
    .steel-process-map:before { content:""; position:absolute; inset:0; background:linear-gradient(90deg,transparent,rgba(39,212,255,.15),transparent); animation:scan 4.5s linear infinite; }
    .industrial-visual { position:absolute; inset:48px 0 0; width:100%; height:calc(100% - 48px); object-fit:cover; object-position:center; opacity:.16; pointer-events:none; filter:saturate(1.18) contrast(1.08); }
    @keyframes scan { from { transform:translateX(-100%); } to { transform:translateX(100%); } }
    .process-flow { position:relative; z-index:1; display:grid; grid-template-columns:repeat(7,minmax(0,1fr)); gap:12px; margin-top:18px; padding:30px 0 8px; }
    .process-node { min-height:116px; border:1px solid #294967; border-radius:12px; padding:12px; background:rgba(11,27,48,.9); position:relative; cursor:pointer; transition:.2s; backdrop-filter:blur(2px); }
    .process-node:after { content:""; position:absolute; right:-16px; top:50%; width:20px; height:2px; background:#2a80a8; box-shadow:0 0 14px #27d4ff; }
    .process-node:last-child:after { display:none; }
    .process-node.active { border-color:var(--cyan); box-shadow:0 0 0 1px rgba(39,212,255,.35), 0 0 30px rgba(39,212,255,.14); }
    .process-node.warning { border-color:var(--yellow); box-shadow:0 0 26px rgba(244,188,69,.18); }
    .process-node.danger { border-color:var(--red); box-shadow:0 0 28px rgba(255,92,101,.22); animation:pulse 1.2s ease-in-out infinite; }
    .process-node.context { opacity:.72; }
    .process-node.normal { border-color:#21405d; }
    @keyframes pulse { 50% { transform:translateY(-2px); } }
    .process-node b { display:block; font-size:15px; margin-bottom:8px; overflow-wrap:anywhere; }
    .process-node small { color:var(--muted); line-height:1.45; overflow-wrap:anywhere; }
    .realtime-stream { display:flex; align-items:center; gap:8px; color:#a9dfff; }
    .stream-line { height:5px; border-radius:999px; flex:1; background:linear-gradient(90deg,#123,#27d4ff,#123); background-size:200% 100%; animation:flow 1.4s linear infinite; }
    @keyframes flow { to { background-position:200% 0; } }
    .event-feed { max-height:318px; overflow:auto; display:flex; flex-direction:column; gap:8px; }
    .event-row { border:1px solid var(--line); border-radius:8px; padding:10px; background:#0b1b30; cursor:pointer; }
    .event-row.active { border-color:var(--cyan); background:#102945; }
    .risk-ring { width:132px; height:132px; border-radius:50%; display:grid; place-items:center; margin:auto; background:conic-gradient(var(--red) calc(var(--p)*1%), #173252 0); box-shadow:inset 0 0 0 14px #081524; }
    .risk-ring strong { font-size:25px; }
    .bar { height:9px; background:#132b47; border-radius:999px; overflow:hidden; margin:8px 0 12px; }
    .bar div { height:100%; background:linear-gradient(90deg,#27d4ff,#30d180); }
    .path-layout { display:grid; grid-template-columns:260px 1fr 320px; gap:12px; align-items:start; }
    .path-list { display:flex; flex-direction:column; gap:8px; }
    .path-card { border:1px solid var(--line); border-radius:9px; padding:10px; background:#0b1b30; cursor:pointer; }
    .path-card.active { border-color:var(--cyan); background:#102945; }
    .path-stage { display:grid; grid-template-columns:repeat(7,minmax(110px,1fr)); gap:8px; min-width:900px; }
    .path-canvas { overflow:auto; padding:8px; border:1px solid var(--line); border-radius:10px; background:#071525; }
    .path-node { border:1px solid #31587c; border-radius:10px; min-height:72px; padding:10px; background:#0f2440; cursor:pointer; position:relative; }
    .path-node:hover { border-color:var(--cyan); box-shadow:0 0 18px rgba(39,212,255,.16); }
    .path-node b { display:block; font-size:13px; margin-bottom:6px; }
    .path-node small { color:var(--muted); }
    .path-node:after { content:""; position:absolute; top:50%; right:-10px; width:10px; height:2px; background:#4a89b6; }
    .path-node:last-child:after { display:none; }
    .drawer { border:1px solid var(--line); border-radius:10px; background:#0b1b30; padding:12px; min-height:255px; }
    .evidence { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }
    .evidence .card { box-shadow:none; }
    .ask-path-llm textarea { width:100%; min-height:74px; border:1px solid #2f5578; border-radius:8px; background:#071525; color:var(--ink); padding:10px; resize:vertical; }
    .answer { margin-top:10px; border:1px solid var(--line); background:#071525; border-radius:8px; padding:10px; color:#c7d8e9; line-height:1.6; }
    .tooltip { position:fixed; pointer-events:none; z-index:20; background:#081524; border:1px solid var(--cyan); color:var(--ink); border-radius:8px; padding:8px 10px; max-width:280px; box-shadow:0 18px 40px rgba(0,0,0,.35); display:none; }
    @media (max-width:1450px) { .grid-2 { grid-template-columns:1fr; } }
    @media (max-width:1200px) { .grid-4,.grid-2,.path-layout,.evidence { grid-template-columns:1fr; } .app { grid-template-columns:1fr; } .sidebar { display:none; } }
    @media (max-width:760px) { .process-flow { grid-template-columns:repeat(2,minmax(0,1fr)); } .process-node:after { display:none; } }
  </style>
</head>
<body>
  <div class="app">
    <aside class="sidebar">
      <div class="brand">钢铁全流程生产异常预警溯源系统<small>Vben Admin 实时工业工作台原型</small></div>
      <nav class="menu">
        <button class="active">实时生产总览</button>
        <button>实时数据接入</button>
        <button>异常预警</button>
        <button>异常识别</button>
        <button>缺陷路径溯源</button>
        <button>专家知识与建议</button>
        <button>评估反馈</button>
      </nav>
    </aside>
    <main class="main">
      <header class="topbar">
        <h1>实时生产总览</h1>
        <div class="top-actions">
          <div class="realtime-stream"><span class="status-dot" id="streamDot"></span><span id="streamText">实时流待启动</span><div class="stream-line"></div></div>
          <button class="btn primary" onclick="toggleStream()">开始实时演示</button>
          <button class="btn" onclick="nextEvent()">下一条样本</button>
          <button class="btn warning" onclick="resetStream()">重置</button>
        </div>
      </header>
      <section class="content">
        <div class="grid-4">
          <div class="card kpi"><span>当前事件</span><strong id="kpiEvent">-</strong></div>
          <div class="card kpi"><span>风险概率</span><strong id="kpiRisk">-</strong></div>
          <div class="card kpi"><span>识别异常类</span><strong id="kpiGroups">-</strong></div>
          <div class="card kpi"><span>溯源可信度</span><strong id="kpiAlign">-</strong></div>
        </div>
        <div class="grid-2">
          <div class="card steel-process-map" data-boundary="连铸段模型分析范围">
            <h2>钢铁全流程动态示意 <span class="muted">粗炼/精炼为流程背景，连铸段模型分析范围：中间包/结晶器/流量控制/传热冷却/品质检测</span></h2>
            <img class="industrial-visual" src="assets/steel_realtime_process_bg.png" alt="" aria-hidden="true" />
            <div class="process-flow" id="processFlow"></div>
          </div>
          <div class="card">
            <h2>实时告警流</h2>
            <div class="event-feed" id="eventFeed"></div>
          </div>
        </div>
        <div class="grid-2">
          <div class="card">
            <h2>异常预警与异常识别</h2>
            <div style="display:grid;grid-template-columns:180px 1fr;gap:18px;align-items:center;">
              <div class="risk-ring" id="riskRing" style="--p:0"><strong id="riskValue">0.000</strong></div>
              <div>
                <h3>异常类别概率</h3>
                <div id="labelBars"></div>
              </div>
            </div>
          </div>
          <div class="card">
            <h2>实时数据接入</h2>
            <p class="muted">支持上传 CSV/Excel、选择历史样本、或按时间顺序模拟实时流。当前原型读取已有模型结果作为实时事件种子。</p>
            <input type="file" id="fileInput" accept=".csv,.json,.xlsx" />
            <div class="answer" id="uploadHint">上传文件后可在正式后端中触发字段识别、预处理和实时推理。</div>
          </div>
        </div>
        <div class="card">
          <h2>缺陷路径溯源中心</h2>
          <div class="path-layout">
            <div class="path-list" id="pathList"></div>
            <div class="path-canvas"><div class="path-stage" id="pathStage"></div></div>
            <div class="drawer path-detail-modal" id="pathDrawer"></div>
          </div>
        </div>
        <div class="evidence">
          <div class="card"><h3>多源证据</h3><div id="evidenceBox"></div></div>
          <div class="card"><h3>调整方案</h3><div id="recommendBox"></div></div>
          <div class="card ask-path-llm"><h3>路径相关问答</h3><textarea id="llmQuestion" placeholder="例如：为什么液面波动会导致卷渣？"></textarea><button class="btn primary" onclick="askPathLLM()">询问当前路径</button><div class="answer" id="llmAnswer">LLM 仅用于辅助解释和建议生成，不作为因果证据。</div></div>
        </div>
      </section>
    </main>
  </div>
  <div class="tooltip node-tooltip" id="node-tooltip"></div>
  <script>
    const seed = __SEED__;
    let cursor = 0;
    let currentEvent = seed.events[0] || {};
    let selectedPathIndex = 0;
    let timer = null;
    let streamSource = null;
    const API_ENDPOINTS = {
      stream: '/api/realtime/stream',
      ingest: '/api/realtime/ingest',
      assistant: '/api/assistant/path-question',
      visual: 'assets/steel_realtime_process_bg.png',
    };

    const TERM_LABELS = {
      no_quality_abnormal:'无质量异常',
      high:'高风险', medium:'中风险', low:'低风险',
      context:'流程背景', normal:'稳定', active:'当前关注', warning:'预警关注', danger:'高风险定位',
      roughing:'粗炼', refining:'精炼', tundish:'中间包', mold:'结晶器',
      flow_control:'流量控制', heat_transfer:'传热/冷却', quality:'品质检测',
      mold_heat_transfer:'结晶器传热', nozzle_flow:'水口/流量', mold_level:'结晶器液位',
      casting_speed:'拉速', cooling_water:'二冷水量', tundish_weight:'中间包吨位',
      heat_exchange:'热交换', sequence_transition:'过渡段序列',
      temperature_flux:'温度/保护渣异常', mold_level_slag_risk:'液面/卷渣风险',
      speed_stopper_flow:'拉速/塞棒/流量异常', process_fluctuation:'过程参数波动',
      heat_transfer_imbalance:'传热不均', transition_tundish:'过渡/中间包状态',
      other_quality_abnormal:'其他质量异常',
      tundish_transition:'中间包过渡状态', heat_transfer_uniformity:'传热均匀性',
      flow_control_stability:'流量控制稳定性', process_operation:'工艺操作状态',
      ems_taper_oscillation:'电磁搅拌/锥度/振动', action_transition_tundish:'过渡段处置建议',
      action_speed_stopper_flow:'流量控制处置建议', action_heat_transfer_imbalance:'传热均匀性处置建议',
      action_process_fluctuation:'过程波动处置建议', action_temperature_flux:'温度/保护渣处置建议',
      action_mold_level_slag_risk:'液位/卷渣处置建议',
    };
    const TOKEN_LABELS = {
      ems:'电磁搅拌', taper:'锥度', oscillation:'振动', heat:'传热', transfer:'传热',
      imbalance:'不均', mold:'结晶器', level:'液位', slag:'卷渣', risk:'风险',
      speed:'拉速', stopper:'塞棒', flow:'流量', temperature:'温度', flux:'保护渣',
      transition:'过渡', tundish:'中间包', quality:'品质', abnormal:'异常', other:'其他',
      process:'过程', fluctuation:'波动', range:'范围', mean:'均值', max:'最大值',
      min:'最小值', trend:'趋势', std:'标准差', water:'水量', cooling:'冷却',
      casting:'浇铸', deviation:'偏差', exchange:'交换', nozzle:'水口', sequence:'序列',
      weight:'吨位', last:'最近窗口', first:'起始窗口',
    };
    const MECHANISM_TO_STEP = {
      temperature_flux:'tundish', mold_level_slag_risk:'mold', speed_stopper_flow:'flow_control',
      process_fluctuation:'tundish', heat_transfer_imbalance:'heat_transfer',
      transition_tundish:'tundish', other_quality_abnormal:'quality',
    };
    const fmt = (x) => typeof x === 'number' ? x.toFixed(3) : (x ?? '-');
    function readableFallback(x) {
      const raw = String(x ?? '');
      if (!raw) return '-';
      return raw
        .replace(/\/\(L\/min\)/g, '/流量')
        .replace(/\/mm/g, '/毫米')
        .replace(/\/t/g, '/吨')
        .split(/[_\s]+/)
        .map(part => TOKEN_LABELS[part] || part)
        .join('');
    }
    function labelName(x) {
      const key = String(x ?? '');
      return (seed.display_labels || {})[key] || TERM_LABELS[key] || readableFallback(key);
    }
    function featureName(x) {
      return labelName(String(x ?? '-')
        .replace(/_mean$/,'_均值')
        .replace(/_std$/,'_标准差')
        .replace(/_trend$/,'_趋势')
        .replace(/_last$/,'_最近窗口'));
    }
    function riskName(level) { return TERM_LABELS[level] || labelName(level); }
    function stepIdFromPath(path) {
      const zone = String(path?.equipment_zone || '');
      const zoneMap = { mold_heat_transfer:'heat_transfer', heat_transfer:'heat_transfer', nozzle_flow:'flow_control' };
      return zoneMap[zone] || zone || MECHANISM_TO_STEP[path?.defect_mechanism] || '';
    }
    function abnormalGroupKeys(ident = {}) {
      const keys = [];
      for (const field of ['display_group_keys', 'predicted_abnormal_groups', 'multi_label_abnormal_groups']) {
        for (const value of ident[field] || []) {
          if (value && value !== 'no_quality_abnormal') keys.push(String(value));
        }
      }
      const primary = ident.primary_abnormal_class || ident.true_abnormal_class;
      if (primary && primary !== 'no_quality_abnormal') keys.push(String(primary));
      const probs = ident.class_probability || ident.multilabel_probability || {};
      if (!keys.length && probs && typeof probs === 'object') {
        const top = Object.entries(probs).filter(([k,v]) => k !== 'no_quality_abnormal' && Number(v) > 0).sort((a,b) => Number(b[1]) - Number(a[1]))[0];
        if (top) keys.push(top[0]);
      }
      return [...new Set(keys)];
    }
    function abnormalGroupLabels(ident = {}) {
      const keys = abnormalGroupKeys(ident);
      if (keys.length) return keys.map(labelName);
      return (ident.display_groups || []).map(labelName).filter(Boolean);
    }
    function abnormalProbabilityEntries(ident = {}) {
      const probs = ident.multilabel_probability || ident.class_probability || {};
      const rows = Object.entries(probs)
        .filter(([k,v]) => k !== 'no_quality_abnormal' && Number(v) > 0)
        .sort((a,b) => Number(b[1]) - Number(a[1]));
      if (rows.length) return rows.slice(0, 6);
      const primary = abnormalGroupKeys(ident)[0];
      return primary ? [[primary, Number(ident.class_confidence || 1)]] : [];
    }
    function eventTitle(event = {}) {
      const ident = event.abnormal_identification || {};
      const main = abnormalGroupKeys(ident)[0] || 'quality';
      const match = String(event.event_id || '').match(/event_(\d+)/);
      const no = match ? match[1] : (Number.isFinite(Number(event.sequence_no)) ? Number(event.sequence_no) + 1 : '');
      return `${labelName(main)}${no ? ' · 样本 ' + no : ''}`;
    }
    function activePath() { return currentPaths()[selectedPathIndex] || currentPaths()[0] || {}; }
    function evidenceText(value) {
      if (Array.isArray(value)) return value.map(labelName).join('、') || '-';
      return labelName(value || '-');
    }
    const esc = (x) => String(x ?? '').replace(/[&<>"']/g, s => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[s]));

    function toggleStream() {
      if (timer || streamSource) { stopStream(); document.getElementById('streamText').textContent = '实时流已暂停'; return; }
      document.getElementById('streamText').textContent = '实时流运行中';
      if (!connectSseStream()) {
        timer = setInterval(nextEvent, 1600);
      }
    }
    function stopStream() {
      if (timer) clearInterval(timer);
      timer = null;
      if (streamSource) streamSource.close();
      streamSource = null;
    }
    function connectSseStream() {
      if (!window.EventSource) return false;
      try {
        streamSource = new EventSource(`${API_ENDPOINTS.stream}?cursor=${cursor}&limit=20`);
        streamSource.addEventListener('steel-event', (evt) => {
          const payload = JSON.parse(evt.data || '{}');
          if (!payload.event) return;
          cursor = Number(payload.cursor || cursor + 1);
          currentEvent = payload.event;
          selectedPathIndex = 0;
          renderAll();
        });
        streamSource.onerror = () => {
          if (streamSource) streamSource.close();
          streamSource = null;
          if (!timer) timer = setInterval(nextEvent, 1600);
        };
        return true;
      } catch (_) {
        streamSource = null;
        return false;
      }
    }
    function resetStream() { stopStream(); cursor = 0; currentEvent = seed.events[0] || {}; selectedPathIndex = 0; renderAll(); }
    function nextEvent() {
      if (!seed.events.length) return;
      currentEvent = seed.events[cursor % seed.events.length];
      cursor += 1;
      selectedPathIndex = 0;
      renderAll();
    }
    function setCurrentEvent(index) { currentEvent = seed.events[index] || currentEvent; cursor = index + 1; selectedPathIndex = 0; renderAll(); }
    function renderAll() { renderKpis(); renderProcess(); renderFeed(); renderRisk(); renderPaths(); renderEvidence(); }
    function riskClass(level) { return level === 'high' ? 'danger' : level === 'medium' ? 'warning' : ''; }
    function renderKpis() {
      const risk = currentEvent.risk_warning || {};
      const ident = currentEvent.abnormal_identification || {};
      const trace = seed.metrics?.traceability || {};
      const path = activePath();
      const confidence = path.final_score || path.path_score || trace.mechanism_alignment_at_k;
      document.getElementById('kpiEvent').textContent = eventTitle(currentEvent);
      document.getElementById('kpiRisk').textContent = fmt(risk.risk_probability);
      document.getElementById('kpiGroups').textContent = abnormalGroupLabels(ident).length || 0;
      document.getElementById('kpiAlign').textContent = fmt(confidence);
      const dot = document.getElementById('streamDot');
      dot.className = 'status-dot ' + riskClass(risk.risk_level);
    }
    function renderProcess() {
      const risk = currentEvent.risk_warning || {};
      const ident = currentEvent.abnormal_identification || {};
      const path = activePath();
      const activeStep = stepIdFromPath(path) || MECHANISM_TO_STEP[abnormalGroupKeys(ident)[0]] || '';
      const rows = seed.process_steps || currentEvent.process_status || [];
      document.getElementById('processFlow').innerHTML = rows.map(row => `
        ${(() => {
          let status = row.status || (row.scope === 'context' ? 'context' : 'normal');
          if (row.id === activeStep) status = riskClass(risk.risk_level) || 'active';
          const note = row.id === activeStep ? '当前溯源定位' : (row.scope === 'context' ? '流程背景' : '在线监测稳定');
          const relation = row.id === activeStep ? `<br>关联：${esc(labelName(path.defect_mechanism || abnormalGroupKeys(ident)[0]))}` : '';
          return `<div class="process-node ${status}" onclick="filterByProcess('${row.id}')">
          <b>${esc(row.name)}</b>
          <small class="process-status">${esc(note)}<br>状态：${esc(labelName(status))}${relation}</small>
        </div>`;
        })()}`).join('');
    }
    function renderFeed() {
      const rows = seed.events.slice(Math.max(0, cursor - 14), Math.max(14, cursor + 1));
      document.getElementById('eventFeed').innerHTML = rows.map((event) => {
        const idx = event.sequence_no || 0;
        const risk = event.risk_warning || {};
        const ident = event.abnormal_identification || {};
        const groups = abnormalGroupLabels(ident).join('、') || '待识别';
        return `<div class="event-row ${event.event_id === currentEvent.event_id ? 'active' : ''}" onclick="setCurrentEvent(${idx})">
          <b>${esc(eventTitle(event))}</b><br><span class="muted">${esc(riskName(risk.risk_level))} / ${fmt(risk.risk_probability)} / ${esc(groups)}</span>
        </div>`;
      }).join('');
    }
    function renderRisk() {
      const risk = currentEvent.risk_warning || {};
      const ident = currentEvent.abnormal_identification || {};
      const p = Number(risk.risk_probability || 0);
      document.getElementById('riskRing').style.setProperty('--p', Math.round(p * 100));
      document.getElementById('riskValue').textContent = fmt(p);
      const probs = abnormalProbabilityEntries(ident);
      document.getElementById('labelBars').innerHTML = probs.map(([k,v]) => `
        <div><span>${esc(labelName(k))}</span><span style="float:right">${fmt(Number(v))}</span><div class="bar"><div style="width:${Math.round(Number(v)*100)}%"></div></div></div>
      `).join('') || '<div class="muted">当前事件暂无可用异常类别概率</div>';
    }
    function currentPaths() { return currentEvent.traceability?.top_k_paths || []; }
    function renderPaths() {
      const paths = currentPaths();
      if (selectedPathIndex >= paths.length) selectedPathIndex = 0;
      document.getElementById('pathList').innerHTML = paths.map((path, i) => `
        <div class="path-card ${i === selectedPathIndex ? 'active' : ''}" onclick="selectedPathIndex=${i};renderPaths();renderProcess();renderKpis();">
          <b>路径 ${i + 1}：${esc(labelName(path.defect_mechanism))}</b>
          <div class="muted">${esc(labelName(path.equipment_zone))} · ${esc(labelName(path.variable_group))}</div>
          <div class="bar"><div style="width:${Math.round(Number(path.final_score || path.path_score || 0)*100)}%"></div></div>
          <small>综合评分 ${fmt(path.final_score || path.path_score)} / 遮蔽下降 ${fmt(path.path_occlusion_drop)}</small>
        </div>`).join('') || '<div class="muted">暂无路径</div>';
      const path = paths[selectedPathIndex] || {};
      document.getElementById('pathStage').innerHTML = (path.nodes || []).map((node, i) => `
        <div class="path-node" onmousemove="showNodeTooltip(event,${i})" onmouseleave="hideNodeTooltip()" onclick="showPathDetail(${i})">
          <b>${esc(nodeLabel(node))}</b>
          <small class="path-layer">${esc(layerText(node.layer))}</small>
        </div>`).join('');
      renderDrawer(path);
    }
    function nodeLabel(node) {
      const text = node?.label || node?.id || '-';
      return node?.layer === 'window_feature' ? featureName(text) : labelName(text);
    }
    function layerText(layer) {
      return { window_feature:'变量', variable_group:'变量组', equipment_zone:'工序区域', process_state:'工艺状态', defect_mechanism:'失稳机制', event_quality_class:'异常组', correction_action:'纠正建议' }[layer] || layer;
    }
    function renderDrawer(path) {
      document.getElementById('pathDrawer').innerHTML = `
        <h3>整条链条详细信息</h3>
        <p><b>${esc(labelName(path.variable_group || '-'))}</b> -> <b>${esc(labelName(path.defect_mechanism || '-'))}</b></p>
        <p class="muted">变量：${esc(featureName(path.feature || '-'))}；当前值：${fmt(path.feature_value)}；工艺区：${esc(labelName(path.equipment_zone || '-'))}</p>
        <p>综合评分：${fmt(path.final_score || path.path_score)}<br>遮蔽下降：${fmt(path.path_occlusion_drop)}<br>失稳机制：${esc(labelName(path.defect_mechanism || '-'))}</p>
        <p class="muted">点击链条节点可查看节点属性；下方证据区展示专家规则、原始标签与调整方案。</p>`;
    }
    function showPathDetail(nodeIndex) {
      const path = currentPaths()[selectedPathIndex] || {};
      const node = (path.nodes || [])[nodeIndex] || {};
      document.getElementById('pathDrawer').innerHTML = `
        <h3>节点属性</h3>
        <p><b>${esc(nodeLabel(node))}</b></p>
        <p>节点层级：${esc(layerText(node.layer))}</p>
        <p>所属路径：${esc(labelName(path.variable_group || '-'))} -> ${esc(labelName(path.defect_mechanism || '-'))}</p>
        <p>变量值：${fmt(path.feature_value)}<br>综合评分：${fmt(path.final_score || path.path_score)}<br>遮蔽下降：${fmt(path.path_occlusion_drop)}</p>`;
    }
    function showNodeTooltip(evt, nodeIndex) {
      const path = currentPaths()[selectedPathIndex] || {};
      const node = (path.nodes || [])[nodeIndex] || {};
      const tip = document.getElementById('node-tooltip');
      tip.style.display = 'block';
      tip.style.left = (evt.clientX + 14) + 'px';
      tip.style.top = (evt.clientY + 12) + 'px';
      tip.innerHTML = `<b>${esc(nodeLabel(node))}</b><br><span class="muted">${esc(layerText(node.layer))}</span><br>点击查看节点属性`;
    }
    function hideNodeTooltip() { document.getElementById('node-tooltip').style.display = 'none'; }
    function filterByProcess(stepId) {
      const map = { tundish:'temperature_flux', mold:'mold_level_slag_risk', flow_control:'speed_stopper_flow', heat_transfer:'heat_transfer_imbalance', quality:'other_quality_abnormal' };
      const target = map[stepId];
      if (!target) return;
      const idx = currentPaths().findIndex(p => p.defect_mechanism === target || stepIdFromPath(p) === stepId);
      if (idx >= 0) { selectedPathIndex = idx; renderPaths(); renderProcess(); renderKpis(); }
    }
    function renderEvidence() {
      const trace = currentEvent.traceability || {};
      const rec = currentEvent.recommendation || {};
      document.getElementById('evidenceBox').innerHTML = `
        <p>机制标签：${esc(evidenceText(trace.reason_mechanism_set || '-'))}</p>
        <p>变量组标签：${esc(evidenceText(trace.reason_variable_group_set || '-'))}</p>
        <p>工艺阶段标签：${esc(evidenceText(trace.reason_stage_set || '-'))}</p>`;
      document.getElementById('recommendBox').innerHTML = `
        <b>${esc(rec.risk_summary || '暂无建议')}</b>
        <ul>${(rec.recommended_checks || []).map(x => `<li>${esc(x)}</li>`).join('')}</ul>
        <ul>${(rec.recommended_adjustments || []).map(x => `<li>${esc(x)}</li>`).join('')}</ul>`;
    }
    function askPathLLM() {
      const q = document.getElementById('llmQuestion').value || '解释当前路径';
      const path = currentPaths()[selectedPathIndex] || {};
      document.getElementById('llmAnswer').innerHTML = `问题：${esc(q)}<br>当前路径关联 ${esc(labelName(path.defect_mechanism || '-'))}，关键变量为 ${esc(featureName(path.feature || '-'))}。助手接口 ${API_ENDPOINTS.assistant} 仅用于解释表达；建议优先复核该变量所在工艺区 ${esc(labelName(path.equipment_zone || '-'))} 的稳定性，并结合多源证据确认是否需要执行调整方案。`;
    }
    document.getElementById('fileInput').addEventListener('change', (evt) => {
      const file = evt.target.files?.[0];
      document.getElementById('uploadHint').textContent = file ? `已选择 ${file.name}，正式模式下将上传后端进行实时字段识别与推理。` : '未选择文件';
    });
    renderAll();
  </script>
</body>
</html>
"""


def build_realtime_system_app(
    *,
    source_dir: str | Path = DEFAULT_SOURCE_DIR,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    max_events: int = 400,
) -> dict[str, Any]:
    requested_output = Path(output_dir)
    output = _fs_path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    seed = build_realtime_seed(source_dir, max_events=max_events)
    production_artifacts = build_production_data_artifacts(output_dir, max_windows=600)
    (output / "realtime_seed.json").write_text(json.dumps(seed, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "api_manifest.json").write_text(
        json.dumps({"api_routes": API_ROUTE_SPEC, "routes": API_ROUTE_SPEC}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    sample = {
        "event_id": "online-demo-001",
        "timestamp": "2026-06-16 10:00:00",
        "line_id": "line-A",
        "features": {
            "mold_level_range_mm": 7.2,
            "casting_speed_change": 0.18,
            "rule_margin": 0.03,
            "stopper_flow_deviation": 0.11,
        },
    }
    (output / "sample_realtime_event.json").write_text(json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8")
    assets = output / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    svg_path = assets / "steel_process_digital_twin.svg"
    svg_path.write_text(DEFAULT_DIGITAL_TWIN_SVG, encoding="utf-8")
    if UI_ASSET_DIR.is_dir():
        for asset in UI_ASSET_DIR.glob("*.png"):
            target = assets / asset.name
            try:
                shutil.copy2(asset, target)
            except (PermissionError, OSError):
                continue
    html = HTML_TEMPLATE.replace("__SEED__", json.dumps(seed, ensure_ascii=False))
    (output / "index.html").write_text(html, encoding="utf-8")
    return {
        "status": "ok",
        "output_dir": str(requested_output),
        "index": str(requested_output / "index.html"),
        "n_events": len(seed.get("events", [])),
        "n_production_records": production_artifacts["records"],
        "n_production_window_preview": production_artifacts["preview_windows"],
        "template": seed["template"],
    }


def _kg_governance_log_path(root: Path) -> Path:
    return _fs_path(root) / "kg_governance_actions.jsonl"


def _read_kg_governance_log(root: Path, limit: int = 50) -> list[dict[str, Any]]:
    path = _kg_governance_log_path(root)
    if not path.is_file():
        return []
    return _read_jsonl(path, limit=limit)


def _kg_versions_response(root: Path, seed: Mapping[str, Any]) -> dict[str, Any]:
    kg = seed.get("knowledge_graph", {}) or {}
    summary = dict(kg.get("summary") or {})
    log_rows = _read_kg_governance_log(root, limit=80)
    return {
        "current_version": {
            "version_id": "kg-json-v1-current",
            "backend": kg.get("backend", "json_graph_v1"),
            "status": "published_for_runtime",
            "node_count": summary.get("node_count", 0),
            "edge_count": summary.get("edge_count", 0),
            "path_template_count": summary.get("path_template_count", 0),
            "connectivity": summary.get("connectivity", {}),
            "entity_disambiguation": summary.get("entity_disambiguation", {}),
            "storage": "knowledge_exports/steel_realtime_system_v1/realtime_seed.json::knowledge_graph",
            "model_usage": "published graph only; candidate knowledge must be reviewed before model scoring",
        },
        "candidate_store": {
            "case_ingest_log": "case_knowledge_ingest.jsonl",
            "governance_log": "kg_governance_actions.jsonl",
            "merge_policy": "canonical_alias_type_scope_merge_v1",
        },
        "recent_actions": log_rows[-20:],
    }


def _kg_governance_action_response(root: Path, payload: Mapping[str, Any]) -> dict[str, Any]:
    action_type = str(payload.get("action_type") or "mark_review_required")
    target_type = str(payload.get("target_type") or "knowledge_node")
    target_id = str(payload.get("target_id") or payload.get("node_id") or payload.get("relation_id") or "")
    decision = str(payload.get("decision") or "pending_review")
    record = {
        "action_id": f"kg-action-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "action_type": action_type,
        "target_type": target_type,
        "target_id": target_id,
        "decision": decision,
        "note": str(payload.get("note") or ""),
        "operator": str(payload.get("operator") or "process_engineer"),
        "status": "recorded",
        "next_step": {
            "mark_review_required": "人工复核实体、关系、证据来源和适用工序",
            "request_merge": "进入消歧合并队列，比较旧知识和新知识的粒度与方向",
            "publish_candidate": "候选知识通过复核后发布到运行图谱版本",
        }.get(action_type, "进入知识治理记录，等待复核"),
    }
    log_path = _kg_governance_log_path(root)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def response_for_path(output_dir: str | Path, raw_path: str, raw_query: str = "") -> tuple[int, str, Any]:
    root = _fs_path(output_dir)
    path = unquote(raw_path)
    query = parse_qs(raw_query)
    seed = load_realtime_seed(root)
    events = seed.get("events", []) or []
    if path in {"", "/"}:
        return 200, "text/html; charset=utf-8", (root / "index.html").read_text(encoding="utf-8")
    if path == "/api/seed":
        return 200, "application/json; charset=utf-8", seed
    if path == "/api/routes":
        return 200, "application/json; charset=utf-8", {"api_routes": API_ROUTE_SPEC, "routes": API_ROUTE_SPEC}
    if path == "/api/metrics":
        return 200, "application/json; charset=utf-8", seed.get("metrics", {})
    if path == "/risk/events":
        rows = [
            {
                "event_id": event.get("event_id"),
                "sequence_no": event.get("sequence_no"),
                **dict(event.get("risk_warning") or {}),
            }
            for event in events
        ]
        return 200, "application/json; charset=utf-8", {"events": rows}
    if path == "/api/data/sources":
        return 200, "application/json; charset=utf-8", seed.get("data_sources", {})
    if path == "/api/data/structured/profile":
        if not (root / PRODUCTION_PROFILE_FILENAME).is_file():
            build_production_data_artifacts(root, max_windows=600)
        return 200, "application/json; charset=utf-8", _load_processed_profile(root)
    if path == "/api/data/processed/windows":
        if not (root / PRODUCTION_WINDOWS_FILENAME).is_file():
            build_production_data_artifacts(root, max_windows=600)
        payload = _load_processed_windows(root)
        limit = int(query.get("limit", [str(payload.get("n_windows") or 200)])[0])
        windows = list(payload.get("windows", []) or [])[: max(1, limit)]
        row = dict(payload)
        row["windows"] = windows
        row["n_returned"] = len(windows)
        return 200, "application/json; charset=utf-8", row
    if path == "/api/data/processed/quality":
        if not (root / PRODUCTION_PROFILE_FILENAME).is_file():
            build_production_data_artifacts(root, max_windows=600)
        profile = _load_processed_profile(root)
        return 200, "application/json; charset=utf-8", {
            "records": profile.get("records"),
            "time_range": profile.get("time_range"),
            "label_distribution": profile.get("label_distribution"),
            "quality_group_distribution": profile.get("quality_group_distribution"),
            "data_quality": profile.get("data_quality"),
            "feature_statistics": profile.get("feature_statistics"),
        }
    if path == "/api/data/events":
        return 200, "application/json; charset=utf-8", {"events": events, "n_events": len(events)}
    if path.startswith("/api/data/events/"):
        event_id = path.rsplit("/", 1)[-1]
        event = _find_event(events, event_id)
        return (200, "application/json; charset=utf-8", event) if event else (404, "application/json; charset=utf-8", {"detail": "event not found"})
    if path.startswith("/api/knowledge/extraction/jobs/"):
        job_id = path.rsplit("/", 1)[-1]
        jobs = (seed.get("knowledge_extraction", {}) or {}).get("jobs", []) or []
        job = next((dict(row) for row in jobs if str(row.get("job_id")) == job_id), None)
        return (200, "application/json; charset=utf-8", job) if job else (404, "application/json; charset=utf-8", {"detail": "job not found"})
    if path == "/api/kg/summary":
        return 200, "application/json; charset=utf-8", (seed.get("knowledge_graph", {}) or {}).get("summary", {})
    if path == "/api/kg/versions":
        return 200, "application/json; charset=utf-8", _kg_versions_response(root, seed)
    if path == "/api/kg/nodes":
        return 200, "application/json; charset=utf-8", {"nodes": (seed.get("knowledge_graph", {}) or {}).get("nodes", [])}
    if path == "/api/kg/edges":
        return 200, "application/json; charset=utf-8", {"edges": (seed.get("knowledge_graph", {}) or {}).get("edges", [])}
    if path == "/api/kg/disambiguation-rules":
        kg = seed.get("knowledge_graph", {}) or {}
        return 200, "application/json; charset=utf-8", kg.get("disambiguation", _disambiguation_summary(kg.get("nodes", []) or [], kg.get("edges", []) or []))
    if path == "/api/kg/subgraph":
        keyword = str(query.get("q", [""])[0]).lower()
        kg = seed.get("knowledge_graph", {}) or {}
        nodes = list(kg.get("nodes", []) or [])
        edges = list(kg.get("edges", []) or [])
        if keyword:
            matched_ids = {
                str(node.get("id"))
                for node in nodes
                if keyword in json.dumps(node, ensure_ascii=False).lower()
            }
            nodes = [node for node in nodes if str(node.get("id")) in matched_ids]
            edges = [
                edge
                for edge in edges
                if str(edge.get("source")) in matched_ids or str(edge.get("target")) in matched_ids
            ]
        else:
            nodes = nodes[:60]
            node_ids = {str(node.get("id")) for node in nodes}
            edges = [edge for edge in edges if str(edge.get("source")) in node_ids or str(edge.get("target")) in node_ids][:120]
        return 200, "application/json; charset=utf-8", {"query": keyword, "nodes": nodes, "edges": edges}
    if path == "/api/kg/path-library":
        return 200, "application/json; charset=utf-8", {"paths": (seed.get("knowledge_graph", {}) or {}).get("path_library", [])}
    if path.startswith("/api/kg/evidence/"):
        event_id = path.rsplit("/", 1)[-1]
        event = _find_event(events, event_id)
        if not event:
            return 404, "application/json; charset=utf-8", {"detail": "event not found"}
        trace = dict(event.get("traceability") or {})
        evidence = trace.get("evidence_package") or _build_event_evidence_package(event, trace.get("top_k_paths", []) or [])
        return 200, "application/json; charset=utf-8", evidence
    if path.startswith("/api/kg/event-subgraph/"):
        event_id = path.rsplit("/", 1)[-1]
        event = _find_event(events, event_id)
        if not event:
            return 404, "application/json; charset=utf-8", {"detail": "event not found"}
        hops = int(query.get("hops", ["1"])[0])
        kg = seed.get("knowledge_graph", {}) or {}
        return 200, "application/json; charset=utf-8", _build_event_kg_subgraph(event, kg, hops=hops)
    if path == "/api/model/runs":
        return 200, "application/json; charset=utf-8", {"runs": seed.get("model_runs", []) or []}
    if path.startswith("/api/model/runs/"):
        run_id = path.rsplit("/", 1)[-1]
        runs = seed.get("model_runs", []) or []
        run = next((dict(row) for row in runs if str(row.get("run_id")) == run_id), None)
        return (200, "application/json; charset=utf-8", run) if run else (404, "application/json; charset=utf-8", {"detail": "model run not found"})
    if path == "/api/model/cascade/summary":
        return 200, "application/json; charset=utf-8", _load_quality_modeling_artifacts(preview_limit=12)
    if path == "/api/model/cascade/predictions":
        limit = int(query.get("limit", ["20"])[0])
        only_abnormal = str(query.get("only_abnormal", ["false"])[0]).lower() in {"1", "true", "yes"}
        return 200, "application/json; charset=utf-8", {
            "source": str(CASCADE_PREDICTIONS_PATH),
            "rows": _read_csv_records(CASCADE_PREDICTIONS_PATH, limit=limit, only_abnormal=only_abnormal),
        }
    if path == "/api/model/traceability/evidence":
        limit = int(query.get("limit", ["20"])[0])
        only_abnormal = str(query.get("only_abnormal", ["true"])[0]).lower() in {"1", "true", "yes"}
        return 200, "application/json; charset=utf-8", {
            "source": str(TRACEABILITY_CANDIDATE_EVIDENCE_PATH),
            "rows": _read_csv_records(TRACEABILITY_CANDIDATE_EVIDENCE_PATH, limit=limit, only_abnormal=only_abnormal),
        }
    if path == "/api/evaluation/summary":
        return 200, "application/json; charset=utf-8", (seed.get("evaluation", {}) or {}).get("summary", {})
    if path == "/api/evaluation/evidence-quality":
        return 200, "application/json; charset=utf-8", (seed.get("evaluation", {}) or {}).get("evidence_quality", {})
    if path == "/api/system/artifacts":
        return 200, "application/json; charset=utf-8", {"artifacts": seed.get("system_artifacts", []) or []}
    if path == "/api/assistant/runtime":
        return 200, "application/json; charset=utf-8", _llm_runtime_status()
    if path == "/api/realtime/next":
        cursor = int(query.get("cursor", ["0"])[0])
        if not events:
            return 200, "application/json; charset=utf-8", {"cursor": cursor, "event": {}}
        event = events[cursor % len(events)]
        return 200, "application/json; charset=utf-8", {"cursor": cursor + 1, "event": event}
    if path == "/api/realtime/stream":
        cursor = int(query.get("cursor", ["0"])[0])
        limit = max(1, int(query.get("limit", ["3"])[0]))
        lines: list[str] = []
        for offset in range(limit):
            if not events:
                break
            event = events[(cursor + offset) % len(events)]
            lines.append("event: steel-event")
            lines.append("data: " + json.dumps({"cursor": cursor + offset + 1, "event": event}, ensure_ascii=False))
            lines.append("")
        return 200, "text/event-stream; charset=utf-8", "\n".join(lines)
    if path == "/api/health":
        return 200, "application/json; charset=utf-8", {"status": "ok", "n_events": len(events), "assistant": _llm_runtime_status()}
    if path.startswith("/api/events/"):
        event_id = path.rsplit("/", 1)[-1]
        event = _find_event(events, event_id)
        return (200, "application/json; charset=utf-8", event) if event else (404, "application/json; charset=utf-8", {"detail": "event not found"})
    if path.startswith("/identify/events/"):
        event_id = path.rsplit("/", 1)[-1]
        event = _find_event(events, event_id)
        payload = {"event_id": event_id, **dict((event or {}).get("abnormal_identification") or {})}
        return (200, "application/json; charset=utf-8", payload) if event else (404, "application/json; charset=utf-8", {"detail": "event not found"})
    if path.startswith("/api/trace/events/"):
        event_id = path.rsplit("/", 1)[-1]
        event = _find_event(events, event_id)
        payload = {"event_id": event_id, **dict((event or {}).get("traceability") or {})}
        return (200, "application/json; charset=utf-8", payload) if event else (404, "application/json; charset=utf-8", {"detail": "event not found"})
    if path.startswith("/api/recommend/events/"):
        event_id = path.rsplit("/", 1)[-1]
        event = _find_event(events, event_id)
        payload = dict((event or {}).get("recommendation") or {})
        return (200, "application/json; charset=utf-8", payload) if event else (404, "application/json; charset=utf-8", {"detail": "event not found"})
    if path == "/api/knowledge/search":
        keyword = str(query.get("q", [""])[0]).lower()
        rows = _knowledge_rows(events, keyword, seed.get("knowledge_graph", {}) or {})
        return 200, "application/json; charset=utf-8", {"query": keyword, "items": rows}
    if path.startswith("/assets/"):
        asset_name = path.rsplit("/", 1)[-1]
        asset_path = root / "assets" / asset_name
        if asset_path.is_file() and asset_path.suffix.lower() == ".svg":
            return 200, "image/svg+xml; charset=utf-8", asset_path.read_text(encoding="utf-8")
        if asset_path.is_file() and asset_path.suffix.lower() == ".png":
            return 200, "image/png", asset_path.read_bytes()
        return 404, "application/json; charset=utf-8", {"detail": "asset not found"}
    return 404, "application/json; charset=utf-8", {"detail": "not found"}


def _find_event(events: Sequence[Mapping[str, Any]], event_id: str) -> dict[str, Any] | None:
    for event in events:
        if str(event.get("event_id")) == str(event_id):
            return dict(event)
    return None


def _knowledge_item_matches(row: Mapping[str, Any], keyword: str) -> bool:
    if not keyword:
        return True
    text = json.dumps(row, ensure_ascii=False, default=str).lower()
    return keyword.lower() in text or _normalize_alias_text(keyword) in _normalize_alias_text(text)


def _knowledge_rows(
    events: Sequence[Mapping[str, Any]],
    keyword: str = "",
    kg: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(row: dict[str, Any]) -> None:
        if not _knowledge_item_matches(row, keyword):
            return
        key = str(row.get("id") or f"{row.get('type')}::{row.get('title')}::{row.get('summary')}")
        if key in seen:
            return
        seen.add(key)
        rows.append(row)

    for group, label in DISPLAY_LABELS.items():
        step_id = MECHANISM_TO_STEP.get(group, "quality")
        add(
            {
                "id": f"display::{group}",
                "type": "abnormal_class",
                "key": group,
                "title": label,
                "scope": PROCESS_LABELS.get(step_id, step_id),
                "summary": f"{PROCESS_LABELS.get(step_id, step_id)}相关的{label}，用于质量预警分类和路径溯源解释。",
                "content": "系统内置异常类别解释，作为模型输出和知识图谱机理节点之间的映射依据。",
                "source_type": "system_seed",
                "confidence": 0.9,
            }
        )

    graph = dict(kg or {})
    for item in graph.get("path_library", []) or []:
        variable = str(item.get("variable_group") or "工艺信号")
        zone = str(item.get("equipment_zone") or "工艺位置")
        mechanism = str(item.get("mechanism_label") or item.get("defect_mechanism") or "质量异常")
        add(
            {
                "id": str(item.get("path_id") or f"path::{_safe_id(variable, zone, mechanism)}"),
                "type": "traceability_path",
                "key": str(item.get("canonical_key") or item.get("path_id") or ""),
                "title": f"{zone}：{variable} → {mechanism}",
                "scope": zone,
                "summary": f"历史命中 {int(item.get('event_count') or 0)} 次，平均综合评分 {_as_score(item.get('avg_final_score'), 0.0):.3f}。",
                "content": "该链路用于把实时生产信号映射到候选异常机理，并作为根因溯源排序的图谱依据。",
                "source_type": "knowledge_graph",
                "evidence_type": "path_library",
                "event_count": int(item.get("event_count") or 0),
                "confidence": _as_score(item.get("avg_final_score"), 0.0),
            }
        )

    node_labels = {str(node.get("id")): str(node.get("label") or node.get("id")) for node in graph.get("nodes", []) or []}
    for edge in graph.get("edges", []) or []:
        source = node_labels.get(str(edge.get("source")), str(edge.get("source") or "来源实体"))
        target = node_labels.get(str(edge.get("target")), str(edge.get("target") or "目标实体"))
        relation_label = str(edge.get("label") or edge.get("relation_type") or "图谱关系")
        add(
            {
                "id": str(edge.get("id") or f"edge::{_safe_id(source, target, relation_label)}"),
                "type": "graph_relation",
                "key": str(edge.get("relation_type") or ""),
                "title": f"{relation_label}：{source} → {target}",
                "scope": source,
                "summary": str(edge.get("evidence_snippet") or "知识图谱关系依据。"),
                "source_type": str(edge.get("source_type") or "knowledge_graph"),
                "relation_type": str(edge.get("relation_type") or ""),
                "evidence_count": int(edge.get("evidence_count") or 1),
                "confidence": _as_score(edge.get("confidence"), 0.0),
                "content": f"该关系由图谱证据累计 {int(edge.get('evidence_count') or 1)} 次形成，用于依据检索和路径解释。",
            }
        )
        if len(rows) >= 20:
            return rows[:20]

    path_templates: dict[str, dict[str, Any]] = {}
    for event in events[:80]:
        for path in (event.get("traceability", {}) or {}).get("top_k_paths", []) or []:
            canonical = dict(path.get("canonical_path") or _canonical_path_snapshot(path))
            key = _safe_id(canonical.get("variable_group_id"), canonical.get("equipment_zone_id"), canonical.get("mechanism_id"))
            current = path_templates.setdefault(
                key,
                {
                    "id": f"event-path::{key}",
                    "type": "event_path",
                    "key": key,
                    "title": f"{canonical.get('equipment_zone_label')}：{canonical.get('variable_group_label')} → {canonical.get('mechanism_label')}",
                    "scope": str(canonical.get("equipment_zone_label") or ""),
                    "summary": "",
                    "content": "",
                    "source_type": "structured_production",
                    "event_count": 0,
                    "confidence": 0.0,
                    "feature_label": str(canonical.get("feature_label") or path.get("feature") or ""),
                },
            )
            current["event_count"] = int(current.get("event_count") or 0) + 1
            current["confidence"] = max(_as_score(current.get("confidence"), 0.0), _as_score(path.get("final_score") or path.get("path_score"), 0.0))
    for row in path_templates.values():
        row["summary"] = f"来自实时事件样本，累计命中 {int(row.get('event_count') or 0)} 次，最高综合评分 {_as_score(row.get('confidence'), 0.0):.3f}。"
        row["content"] = f"代表性关键变量：{row.get('feature_label') or '生产窗口变量'}。"
        add(row)
        if len(rows) >= 20:
            return rows[:20]
    return rows[:20]


def _parse_json_body(body: bytes | str | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(body, Mapping):
        return dict(body)
    text = body.decode("utf-8") if isinstance(body, bytes) else str(body)
    return json.loads(text or "{}")


def _assistant_local_answer(
    *,
    question: str,
    label: str,
    feature: str,
    zone: str,
) -> str:
    return (
        f"问题：{question}。当前路径指向{label}，关键变量为 {feature}，工艺区域为 {zone}。"
        "该说明仅用于辅助解释和处置建议组织，不作为因果证据；最终判断应以模型输出、专家规则和现场复核共同确认。"
    )


def _assistant_llm_answer(
    *,
    question: str,
    event: Mapping[str, Any],
    path: Mapping[str, Any],
    knowledge: Sequence[Mapping[str, Any]],
    fallback_answer: str,
) -> tuple[str, dict[str, Any]]:
    api_key = str(CONFIG.get("llm_api_key", "") or "").strip()
    base_url = str(CONFIG.get("llm_base_url", "https://api.n1n.ai/v1") or "").strip().rstrip("/")
    model = str(CONFIG.get("llm_model", "gpt-5.5") or "").strip()
    timeout_sec = float(CONFIG.get("llm_timeout_sec", 45) or 45)
    if not llm_configured(api_key):
        return fallback_answer, {"enabled": False, "status": "not_configured", "model": model}
    evidence_payload = {
        "question": question,
        "event_id": event.get("event_id"),
        "timestamp": event.get("timestamp"),
        "line_id": event.get("line_id"),
        "risk_warning": event.get("risk_warning"),
        "abnormal_identification": event.get("abnormal_identification"),
        "selected_trace_path": path,
        "knowledge_items": list(knowledge)[:3],
        "boundary": "assistant output is explanation-only and must not be treated as causal evidence",
    }
    messages = [
        {
            "role": "system",
            "content": (
                "你是钢铁连铸质量异常值班助手。只能基于输入的事件、溯源路径和知识条目进行解释，"
                "不要编造证据。输出用于值班解释、检查顺序和复核建议组织，不作为因果判定来源。"
                "请用简洁中文回答，先说当前判断，再列现场优先复核点。"
            ),
        },
        {"role": "user", "content": json.dumps(evidence_payload, ensure_ascii=False, default=str)},
    ]
    try:
        answer = post_chat_completions(
            api_key=api_key,
            base_url=base_url,
            model=model,
            messages=messages,
            temperature=0.2,
            timeout_sec=timeout_sec,
            max_retries=1,
        )
        return answer.strip(), {"enabled": True, "status": "ok", "base_url": base_url, "model": model}
    except Exception as exc:
        return fallback_answer, {
            "enabled": True,
            "status": "fallback_after_error",
            "base_url": base_url,
            "model": model,
            "error": str(exc),
        }


def _assistant_path_response(seed: Mapping[str, Any], payload: Mapping[str, Any]) -> dict[str, Any]:
    events = list(seed.get("events", []) or [])
    event_id = str(payload.get("event_id") or "")
    found_event = _find_event(events, event_id) if event_id else None
    event = found_event or (dict(events[0]) if events else {})
    paths = (event.get("traceability", {}) or {}).get("top_k_paths", []) or []
    path_index = int(payload.get("path_index", 0) or 0)
    path = dict(paths[path_index]) if 0 <= path_index < len(paths) else (dict(paths[0]) if paths else {})
    question = str(payload.get("question") or "解释当前路径")
    mechanism = str(path.get("defect_mechanism") or "")
    label = DISPLAY_LABELS.get(mechanism, mechanism or "当前异常")
    feature = str(path.get("feature") or "-")
    zone = str(path.get("equipment_zone") or "-")
    knowledge = _knowledge_rows(events, mechanism or feature)[:3]
    fallback_answer = _assistant_local_answer(question=question, label=label, feature=feature, zone=zone)
    answer, llm_runtime = _assistant_llm_answer(
        question=question,
        event=event,
        path=path,
        knowledge=knowledge,
        fallback_answer=fallback_answer,
    )
    return {
        "event_id": event.get("event_id"),
        "path_index": path_index,
        "llm_role": "assistant_only_not_causal_evidence",
        "llm_runtime": llm_runtime,
        "answer": answer,
        "knowledge_items": knowledge,
        "selected_path": path,
    }


def _safe_token(value: Any, fallback: str = "unknown") -> str:
    text = str(value or fallback).strip()
    out = []
    for ch in text:
        out.append(ch if ch.isalnum() or ch in {"_", "-", ":"} else "_")
    token = "".join(out).strip("_")
    return token or fallback


def _case_knowledge_ingest_response(root: Path, payload: Mapping[str, Any]) -> dict[str, Any]:
    seed = load_realtime_seed(root)
    events = list(seed.get("events", []) or [])
    event_id = str(payload.get("event_id") or "")
    found_event = _find_event(events, event_id) if event_id else None
    event = found_event or (dict(events[0]) if events else {})
    paths = (event.get("traceability", {}) or {}).get("top_k_paths", []) or []
    path_index = int(payload.get("path_index", 0) or 0)
    path = dict(paths[path_index]) if 0 <= path_index < len(paths) else (dict(paths[0]) if paths else {})
    recommendation = event.get("recommendation", {}) or {}
    action = (
        (recommendation.get("recommended_checks") or [None])[0]
        or (recommendation.get("recommended_adjustments") or [None])[0]
        or "现场复核"
    )
    mechanism = str(path.get("defect_mechanism") or "process_fluctuation")
    variable_group = str(path.get("variable_group") or path.get("feature") or "process_variable")
    feature = str(path.get("feature") or variable_group)
    zone = str(path.get("equipment_zone") or MECHANISM_TO_STEP.get(mechanism, "quality"))
    variable_ref = _canonical_entity_parts("variable_group", variable_group)
    feature_ref = _canonical_entity_parts("window_feature", feature)
    mechanism_ref = _canonical_entity_parts("defect_mechanism", mechanism)
    zone_ref = _canonical_entity_parts("equipment_zone", zone)
    action_ref = _canonical_entity_parts("correction_action", action)
    feedback = str(payload.get("feedback") or "").strip()
    batch_id = f"case-kg-{datetime.now().strftime('%Y%m%d%H%M%S')}-{_safe_token(event.get('event_id'), 'event')}"
    review_status = str(payload.get("review_status") or "pending_manual_review")
    event_node = f"case::{_safe_token(event.get('event_id'), 'event')}"
    feature_node = _entity_id("window_feature", feature)
    variable_node = _entity_id("variable_group", variable_group)
    mechanism_node = _entity_id("defect_mechanism", mechanism)
    zone_node = _entity_id("equipment_zone", zone)
    action_node = _entity_id("correction_action", action)
    evidence_snippet = feedback or str(recommendation.get("risk_summary") or "历史异常复盘形成知识候选。")
    candidate_entities = [
        {
            "id": event_node,
            "label": str(event.get("event_id") or "历史异常案例"),
            "entity_type": "reviewed_quality_case",
            "source_type": "case_review",
            "confidence": 0.82,
            "review_status": review_status,
        },
        {
            "id": feature_node,
            "label": str(feature_ref["label"]),
            "entity_type": "window_feature",
            "source_type": "case_review",
            "confidence": float(path.get("model_attribution") or path.get("path_score") or 0.72),
            "review_status": review_status,
            "canonical_key": str(feature_ref["key"]),
            "aliases": feature_ref["aliases"],
        },
        {
            "id": variable_node,
            "label": str(variable_ref["label"]),
            "entity_type": "variable_group",
            "source_type": "case_review",
            "confidence": float(path.get("model_attribution") or path.get("path_score") or 0.72),
            "review_status": review_status,
            "canonical_key": str(variable_ref["key"]),
            "aliases": variable_ref["aliases"],
        },
        {
            "id": mechanism_node,
            "label": str(mechanism_ref["label"]),
            "entity_type": "defect_mechanism",
            "source_type": "case_review",
            "confidence": float(path.get("final_score") or path.get("path_score") or 0.72),
            "review_status": review_status,
            "canonical_key": str(mechanism_ref["key"]),
            "aliases": mechanism_ref["aliases"],
        },
        {
            "id": zone_node,
            "label": str(zone_ref["label"]),
            "entity_type": "equipment_zone",
            "source_type": "case_review",
            "confidence": 0.78,
            "review_status": review_status,
            "canonical_key": str(zone_ref["key"]),
            "aliases": zone_ref["aliases"],
        },
        {
            "id": action_node,
            "label": str(action_ref["label"]),
            "entity_type": "correction_action",
            "source_type": "case_review",
            "confidence": 0.76,
            "review_status": review_status,
            "canonical_key": str(action_ref["key"]),
            "aliases": action_ref["aliases"],
        },
    ]
    candidate_relations = [
        {
            "id": f"rel::{_safe_token(batch_id)}::case_signal",
            "source": event_node,
            "target": feature_node,
            "relation_type": "HAS_KEY_SIGNAL",
            "label": "案例关键变量",
            "confidence": 0.82,
            "source_type": "case_review",
            "evidence_snippet": evidence_snippet,
        },
        {
            "id": f"rel::{_safe_token(batch_id)}::signal_group",
            "source": feature_node,
            "target": variable_node,
            "relation_type": "BELONGS_TO_VARIABLE_GROUP",
            "label": "变量归属",
            "confidence": float(path.get("model_attribution") or path.get("path_score") or 0.72),
            "source_type": "case_review",
            "evidence_snippet": evidence_snippet,
        },
        {
            "id": f"rel::{_safe_token(batch_id)}::signal_mechanism",
            "source": variable_node,
            "target": mechanism_node,
            "relation_type": "SUPPORTS_MECHANISM",
            "label": "变量支持机理",
            "confidence": float(path.get("final_score") or path.get("path_score") or 0.72),
            "source_type": "case_review",
            "evidence_snippet": evidence_snippet,
        },
        {
            "id": f"rel::{_safe_token(batch_id)}::zone_mechanism",
            "source": zone_node,
            "target": mechanism_node,
            "relation_type": "OBSERVED_IN_ZONE",
            "label": "工序区域观测",
            "confidence": 0.78,
            "source_type": "case_review",
            "evidence_snippet": f"{zone_ref['label']} 复核支持 {mechanism_ref['label']}。",
        },
        {
            "id": f"rel::{_safe_token(batch_id)}::mechanism_action",
            "source": mechanism_node,
            "target": action_node,
            "relation_type": "SUGGESTS_ACTION",
            "label": "机理建议处置",
            "confidence": 0.76,
            "source_type": "case_review",
            "evidence_snippet": str(action),
        },
    ]
    evidence_sources = list(path.get("evidence_sources") or [])
    if feedback:
        evidence_sources.append(
            {
                "source_id": f"feedback::{batch_id}",
                "source_type": "operator_review",
                "title": "现场复核记录",
                "confidence": 0.75,
                "snippet": feedback,
            }
        )
    record = {
        "batch_id": batch_id,
        "status": "candidate_generated",
        "event_id": event.get("event_id"),
        "review_status": review_status,
        "target_graph": "knowledge_graph.json_graph_v1",
        "merge_policy": "manual_review_required",
        "model_fusion_role": "graph_prior_candidate_for_next_runs",
        "selected_path": path,
        "candidate_entities": candidate_entities,
        "candidate_relations": candidate_relations,
        "evidence_sources": evidence_sources,
        "feedback": feedback,
    }
    out_path = root / "case_knowledge_ingest.jsonl"
    with out_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def _candidate_text(row: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if isinstance(value, Mapping):
            value = _candidate_text(value, "id", "entity_id", "node_id", "label", "name")
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _candidate_alias_tokens(row: Mapping[str, Any]) -> set[str]:
    values: list[Any] = [
        _candidate_text(row, "id", "entity_id", "node_id", "key"),
        _candidate_text(row, "label", "name", "entity_label"),
        _candidate_text(row, "canonical_key", "canonical", "canonical_name", "normalized_name"),
    ]
    for alias_value in [row.get("aliases"), row.get("alias")]:
        if isinstance(alias_value, (str, int, float)):
            values.append(alias_value)
        elif alias_value:
            values.extend(alias_value)
    return {_normalize_alias_text(value) for value in values if _normalize_alias_text(value)}


def _entity_match_score(candidate: Mapping[str, Any], published: Mapping[str, Any]) -> tuple[float, list[str], bool]:
    reasons: list[str] = []
    candidate_type = _candidate_text(candidate, "entity_type", "type", "node_type", "category")
    published_type = str(published.get("entity_type") or "")
    type_match = candidate_type and candidate_type == published_type
    type_conflict = bool(candidate_type and published_type and candidate_type != published_type)
    score = 0.0
    if _candidate_text(candidate, "id", "entity_id", "node_id", "key") == str(published.get("id") or ""):
        score += 0.38
        reasons.append("entity_id一致")
    candidate_key = _candidate_text(candidate, "canonical_key", "canonical", "canonical_name", "normalized_name")
    if candidate_key and candidate_key == str(published.get("canonical_key") or ""):
        score += 0.24
        reasons.append("规范实体键一致")
    candidate_aliases = _candidate_alias_tokens(candidate)
    published_aliases = _candidate_alias_tokens(published)
    overlap = candidate_aliases & published_aliases
    if overlap:
        score += min(0.22, 0.10 + 0.04 * len(overlap))
        reasons.append("别名或字段名重叠")
    candidate_label = _normalize_alias_text(_candidate_text(candidate, "label", "name", "entity_label"))
    published_label = _normalize_alias_text(published.get("label"))
    if candidate_label and published_label and candidate_label == published_label:
        score += 0.18
        reasons.append("显示名称一致")
    elif candidate_label and published_label and (candidate_label in published_label or published_label in candidate_label):
        score += 0.10
        reasons.append("名称存在包含关系")
    if type_match:
        score += 0.14
        reasons.append("实体类型一致")
    elif type_conflict and score >= 0.25:
        reasons.append("实体类型不一致")
    return min(score, 1.0), reasons or ["未命中明确重叠依据"], type_conflict


def _validate_candidate_entities(
    candidates: Sequence[Mapping[str, Any]],
    published_nodes: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        matches: list[dict[str, Any]] = []
        has_type_conflict = False
        for node in published_nodes:
            score, reasons, type_conflict = _entity_match_score(candidate, node)
            if score >= 0.25 or type_conflict:
                has_type_conflict = has_type_conflict or type_conflict
                matches.append(
                    {
                        "published_id": node.get("id"),
                        "published_label": node.get("label"),
                        "published_type": node.get("entity_type"),
                        "score": round(score, 3),
                        "reasons": reasons,
                    }
                )
        matches = sorted(matches, key=lambda row: float(row["score"]), reverse=True)[:3]
        top_score = float(matches[0]["score"]) if matches else 0.0
        if has_type_conflict and top_score >= 0.45:
            decision = "conflict_review"
            action = "类型冲突，需人工确认"
        elif top_score >= 0.88:
            decision = "suggest_merge"
            action = "建议合并到已有实体"
        elif top_score >= 0.72:
            decision = "suggest_alias"
            action = "建议作为已有实体别名"
        elif top_score >= 0.52:
            decision = "overlap_review"
            action = "存在重叠，需人工复核粒度"
        else:
            decision = "suggest_new"
            action = "建议作为新实体候选"
        rows.append(
            {
                "candidate_id": _candidate_text(candidate, "id", "entity_id", "node_id", "key"),
                "candidate_label": _candidate_text(candidate, "label", "name", "entity_label"),
                "candidate_type": _candidate_text(candidate, "entity_type", "type", "node_type", "category"),
                "decision": decision,
                "action": action,
                "top_score": round(top_score, 3),
                "matches": matches,
            }
        )
    return rows


def _validate_candidate_relations(
    candidates: Sequence[Mapping[str, Any]],
    published_edges: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for relation in candidates:
        source = _candidate_text(relation, "source", "source_id", "source_label", "from", "head")
        target = _candidate_text(relation, "target", "target_id", "target_label", "to", "tail")
        relation_type = _candidate_text(relation, "relation_type", "type", "predicate", "relation")
        exact: list[Mapping[str, Any]] = []
        endpoint_overlap: list[Mapping[str, Any]] = []
        reverse_conflict: list[Mapping[str, Any]] = []
        for edge in published_edges:
            edge_source = str(edge.get("source") or "")
            edge_target = str(edge.get("target") or "")
            edge_type = str(edge.get("relation_type") or "")
            if edge_source == source and edge_target == target and edge_type == relation_type:
                exact.append(edge)
            elif edge_source == target and edge_target == source and edge_type == relation_type:
                reverse_conflict.append(edge)
            elif edge_source == source and edge_target == target:
                endpoint_overlap.append(edge)
        if reverse_conflict:
            decision = "conflict_review"
            action = "存在反向关系，需人工确认方向"
            matches = reverse_conflict[:3]
        elif exact:
            decision = "duplicate_relation"
            action = "已有相同关系，建议累积证据"
            matches = exact[:3]
        elif endpoint_overlap:
            decision = "overlap_review"
            action = "实体端点相同但关系类型不同，需复核关系语义"
            matches = endpoint_overlap[:3]
        else:
            decision = "suggest_new"
            action = "建议作为新关系候选"
            matches = []
        rows.append(
            {
                "candidate_id": _candidate_text(relation, "id", "relation_id", "edge_id", "key"),
                "candidate_label": _candidate_text(relation, "label", "name", "description"),
                "relation_type": relation_type,
                "source": source,
                "target": target,
                "decision": decision,
                "action": action,
                "matches": [
                    {
                        "published_id": item.get("id"),
                        "published_label": item.get("label"),
                        "relation_type": item.get("relation_type"),
                        "confidence": item.get("confidence"),
                        "evidence_count": item.get("evidence_count"),
                    }
                    for item in matches
                ],
            }
        )
    return rows


def _knowledge_candidate_validation_response(root: Path, payload: Mapping[str, Any]) -> dict[str, Any]:
    seed = load_realtime_seed(root)
    kg = seed.get("knowledge_graph", {}) or {}
    entities = list(payload.get("candidate_entities") or payload.get("entities") or [])
    relations = list(payload.get("candidate_relations") or payload.get("relations") or [])
    entity_results = _validate_candidate_entities(entities, kg.get("nodes", []) or [])
    relation_results = _validate_candidate_relations(relations, kg.get("edges", []) or [])
    all_decisions = [str(row.get("decision") or "") for row in [*entity_results, *relation_results]]
    conflict_count = sum(1 for item in all_decisions if "conflict" in item)
    review_count = sum(1 for item in all_decisions if "review" in item)
    merge_count = sum(1 for item in all_decisions if item in {"suggest_merge", "suggest_alias", "duplicate_relation"})
    new_count = sum(1 for item in all_decisions if item == "suggest_new")
    if conflict_count:
        status = "candidate_conflict"
        recommendation = "存在冲突，禁止自动发布，进入人工复核"
    elif review_count:
        status = "candidate_review_required"
        recommendation = "存在重叠或粒度差异，建议人工确认后再发布"
    elif merge_count and not new_count:
        status = "candidate_duplicate_or_alias"
        recommendation = "主要为重复或别名知识，建议合并证据"
    else:
        status = "candidate_publish_ready_after_review"
        recommendation = "未发现明显冲突，人工审核通过后可发布到新图谱版本"
    return {
        "batch_id": payload.get("batch_id"),
        "status": status,
        "recommendation": recommendation,
        "summary": {
            "candidate_entity_count": len(entities),
            "candidate_relation_count": len(relations),
            "suggested_merge_count": merge_count,
            "suggested_new_count": new_count,
            "review_required_count": review_count,
            "conflict_count": conflict_count,
        },
        "entity_results": entity_results,
        "relation_results": relation_results,
        "validation_rules": [
            "实体类型一致性",
            "规范实体键匹配",
            "别名与字段名重叠",
            "关系端点与关系类型一致性",
            "反向关系冲突检测",
            "人工审核后发布",
        ],
    }


def response_for_post(output_dir: str | Path, raw_path: str, body: bytes | str | Mapping[str, Any]) -> tuple[int, str, Any]:
    root = _fs_path(output_dir)
    path = unquote(raw_path)
    payload = _parse_json_body(body)
    if path == "/api/assistant/path-question":
        seed = load_realtime_seed(root)
        return 200, "application/json; charset=utf-8", _assistant_path_response(seed, payload)
    if path == "/api/kg/case-ingest":
        return 200, "application/json; charset=utf-8", _case_knowledge_ingest_response(root, payload)
    if path == "/api/kg/governance/actions":
        return 200, "application/json; charset=utf-8", _kg_governance_action_response(root, payload)
    if path == "/api/knowledge/candidates/validate":
        return 200, "application/json; charset=utf-8", _knowledge_candidate_validation_response(root, payload)
    if path == "/api/data/structured/upload":
        return 200, "application/json; charset=utf-8", {
            "status": "accepted",
            "source": {
                "id": str(payload.get("source_id") or "structured-upload-preview"),
                "name": str(payload.get("name") or payload.get("filename") or "结构化生产数据上传预览"),
                "source_type": "structured_production",
                "schema_status": "validated_contract_only",
                "next_step": "POST /api/data/events/build",
            },
        }
    if path == "/api/data/text/upload":
        return 200, "application/json; charset=utf-8", {
            "status": "accepted",
            "source": {
                "id": str(payload.get("source_id") or "text-upload-preview"),
                "name": str(payload.get("name") or payload.get("filename") or "非结构化文本上传预览"),
                "source_type": "unstructured_text",
                "parse_status": "ready_for_knowledge_extraction",
                "next_step": "POST /api/knowledge/extraction/jobs",
            },
        }
    if path == "/api/data/events/build":
        seed = load_realtime_seed(root)
        max_windows = int(payload.get("max_windows") or 600)
        production_artifacts = build_production_data_artifacts(root, max_windows=max_windows)
        profile = _load_processed_profile(root)
        windows = _load_processed_windows(root)
        return 200, "application/json; charset=utf-8", {
            "status": "built",
            "dataset": (seed.get("data_sources", {}) or {}).get("event_window_dataset", {}),
            "production_artifacts": production_artifacts,
            "production_profile": {
                "records": profile.get("records"),
                "columns": profile.get("columns"),
                "time_range": profile.get("time_range"),
                "data_quality": profile.get("data_quality"),
            },
            "processed_windows": {
                "n_windows": windows.get("n_windows"),
                "total_source_rows": windows.get("total_source_rows"),
                "preview_sampling": windows.get("preview_sampling"),
            },
            "contract": {
                "window_strategy": str(payload.get("window_strategy") or "row_as_event_window_v1"),
                "alignment_keys": ["材料跟踪号", "炼钢材料号", "铸机号", "连铸处理号", "中间包号", "记录识别码"],
            },
        }
    if path == "/api/knowledge/extraction/jobs":
        seed = load_realtime_seed(root)
        jobs = list((seed.get("knowledge_extraction", {}) or {}).get("jobs", []) or [])
        job = {
            "job_id": str(payload.get("job_id") or f"kx-preview-{len(jobs) + 1:03d}"),
            "status": "completed",
            "input_sources": payload.get("input_sources") or ["text_rules_reports_rag"],
            "extractors": payload.get("extractors") or ["NER", "RE", "event_extraction"],
            "entity_count": len((seed.get("knowledge_extraction", {}) or {}).get("entities", []) or []),
            "relation_count": len((seed.get("knowledge_extraction", {}) or {}).get("relations", []) or []),
            "output_target": "knowledge_graph.json_graph_v1",
        }
        return 200, "application/json; charset=utf-8", job
    if path == "/api/model/runs":
        seed = load_realtime_seed(root)
        runs = list(seed.get("model_runs", []) or [])
        run = {
            "run_id": str(payload.get("run_id") or f"model-run-preview-{len(runs) + 1:03d}"),
            "model_contract": str(payload.get("model_contract") or "graph_enhanced_knowledge_model_v1"),
            "status": "completed",
            "algorithm_status": "kg_evidence_fusion_scoring_active",
            "scoring_model": "kg_evidence_fusion_v2",
            "input_artifacts": payload.get("input_artifacts") or ["structured_event_windows_v6", "knowledge_graph.json_graph_v1"],
            "output_artifacts": ["risk_warning", "abnormal_identification", "traceability_paths", "evidence_package"],
            "event_count": len(seed.get("events", []) or []),
        }
        return 200, "application/json; charset=utf-8", run
    if path != "/api/realtime/ingest":
        return 404, "application/json; charset=utf-8", {"detail": "not found"}
    seed = load_realtime_seed(root)
    events = list(seed.get("events", []) or [])
    template = dict(events[0]) if events else {}
    event = json.loads(json.dumps(template, ensure_ascii=False))
    event_id = str(payload.get("event_id") or f"ingested-{len(events) + 1:04d}")
    event["event_id"] = event_id
    event["sequence_no"] = len(events)
    for key in ("timestamp", "line_id", "features"):
        if key in payload:
            event[key] = payload[key]
    if not event.get("risk_warning"):
        event["risk_warning"] = {"risk_label": 1, "risk_probability": 0.72, "risk_level": "medium", "boundary_status": "online_ingested"}
    if not event.get("abnormal_identification"):
        event["abnormal_identification"] = {"primary_abnormal_class": "process_fluctuation", "predicted_abnormal_groups": ["process_fluctuation"]}
    if not (event.get("traceability", {}) or {}).get("top_k_paths"):
        event["traceability"] = {"top_k_paths": [{"path_template_id": "online_ingest_path", "feature": "rule_margin", "defect_mechanism": "process_fluctuation"}]}
    event = _augment_event_for_knowledge_fusion(event)
    events.append(event)
    seed["events"] = events
    seed = _enrich_realtime_seed(seed)
    (root / "realtime_seed.json").write_text(json.dumps(seed, ensure_ascii=False, indent=2), encoding="utf-8")
    return 200, "application/json; charset=utf-8", {"status": "accepted", "event": event, "n_events": len(events)}


def create_realtime_http_server(
    output_dir: str | Path,
    host: str = "127.0.0.1",
    port: int = 8018,
) -> ThreadingHTTPServer:
    root = _fs_path(output_dir)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            status, content_type, payload = response_for_path(root, parsed.path, parsed.query)
            body = payload if isinstance(payload, bytes) else (
                payload.encode("utf-8") if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False).encode("utf-8")
            )
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            length = int(self.headers.get("Content-Length", "0") or "0")
            body_bytes = self.rfile.read(length) if length > 0 else b"{}"
            status, content_type, payload = response_for_post(root, parsed.path, body_bytes)
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: Any) -> None:
            return

    return ThreadingHTTPServer((host, int(port)), Handler)


def serve_realtime_app(output_dir: str | Path, host: str = "127.0.0.1", port: int = 8018) -> None:
    server = create_realtime_http_server(output_dir, host=host, port=port)
    print(f"Serving realtime steel system at http://{host}:{port}")
    server.serve_forever()


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build or serve the realtime steel anomaly traceability system.")
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--max-events", type=int, default=400)
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8018)
    args = parser.parse_args(argv)
    summary = build_realtime_system_app(source_dir=args.source_dir, output_dir=args.output_dir, max_events=args.max_events)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.serve:
        serve_realtime_app(args.output_dir, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
