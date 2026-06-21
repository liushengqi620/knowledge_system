from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from config import CONFIG
from llm_client import llm_configured, post_chat_completions
from public_benchmark_knowledge_model import DATASET_TASKS, build_feature_catalog


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_READY_ROOT = PROJECT_ROOT / "knowledge_exports" / "public_benchmark_ready"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "knowledge_exports" / "llm_evidence"
LLM_EVIDENCE_SOURCE = "llm_candidate_live"
LLM_EXPERT_CORRECTION_SOURCE = "llm_expert_graph_dynamic_correction"
LLM_EXPERT_CONDITION_VERIFIER_SOURCE = "llm_expert_condition_verifier"


def _fs_path(path: Path) -> str:
    if os.name == "nt":
        resolved = str(Path(path).resolve())
        if not resolved.startswith("\\\\?\\"):
            return "\\\\?\\" + resolved
    return str(path)


def _safe_id(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", str(text)).strip("_")[:80] or "feature"


def _read_json(path: Path) -> dict[str, Any]:
    with open(_fs_path(path), "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    os.makedirs(_fs_path(path.parent), exist_ok=True)
    with open(_fs_path(path), "w", encoding="utf-8") as handle:
        json.dump(dict(payload), handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def load_ready_feature_frame(ready_root: Path, dataset: str) -> pd.DataFrame:
    path = Path(ready_root) / str(dataset).lower() / "X_process_features.csv"
    try:
        return pd.read_csv(_fs_path(path), low_memory=False)
    except FileNotFoundError:
        raise FileNotFoundError(path)


def numeric_feature_names(dataset: str, x: pd.DataFrame) -> list[str]:
    exclude = {"record_id"}
    if str(dataset).lower() == "skab":
        exclude |= {"run_id", "run_group", "sample_index"}
    if str(dataset).lower() == "tep":
        exclude |= {"source_split", "source_file"}
    if str(dataset).lower() == "cmapss":
        exclude |= {"unit", "subset", "subset_id", "rul"}
    names: list[str] = []
    for col in x.columns:
        if str(col) in exclude:
            continue
        values = pd.to_numeric(x[col], errors="coerce")
        if values.notna().any() and values.nunique(dropna=True) > 1:
            names.append(str(col))
    return names


def compact_feature_catalog(dataset: str, x: pd.DataFrame, feature_names: Sequence[str], *, max_features: int) -> list[dict[str, Any]]:
    catalog = build_feature_catalog(str(dataset).lower(), x[list(feature_names)])
    rows: list[dict[str, Any]] = []
    for row in catalog.head(max(1, int(max_features))).itertuples(index=False):
        rows.append(
            {
                "name": str(row.feature_name),
                "role": str(row.role),
                "subsystem": str(row.subsystem),
                "n_unique": int(row.n_unique),
            }
        )
    return rows


def build_llm_edge_messages(
    *,
    dataset: str,
    target: str,
    feature_catalog: Sequence[Mapping[str, Any]],
    existing_edges: Sequence[Mapping[str, Any]],
    max_edges: int,
) -> list[dict[str, str]]:
    task = DATASET_TASKS.get(str(dataset).lower(), {}).get("task", "industrial time-series diagnosis")
    allowed = [str(row["name"]) for row in feature_catalog]
    existing = [
        {
            "source": str(edge.get("source", "")),
            "target": str(edge.get("target", "")),
            "relation": str(edge.get("relation", "")),
            "source_type": str(edge.get("evidence_source", "")),
        }
        for edge in existing_edges[:24]
    ]
    user_payload = {
        "dataset": str(dataset).lower(),
        "target": str(target),
        "task": task,
        "allowed_features": allowed,
        "feature_catalog": list(feature_catalog),
        "existing_candidate_edges": existing,
        "max_edges": int(max_edges),
        "required_json_schema": {
            "edges": [
                {
                    "source": "one allowed feature name",
                    "target": "one allowed feature name",
                    "relation": "short mechanism relation",
                    "lag": "integer 0 to 5",
                    "reliability": "float 0.05 to 0.55",
                    "rationale": "one short falsifiable mechanism sentence",
                }
            ]
        },
    }
    return [
        {
            "role": "system",
            "content": (
                "You generate weak candidate mechanism edges for industrial multivariate time-series models. "
                "Return only valid JSON. These edges are not causal truth; they are low-confidence candidates "
                "that must be validated by downstream experiments."
            ),
        },
        {
            "role": "user",
            "content": (
                "Propose feature-to-feature mechanism edges only from the allowed feature names. "
                "Avoid label targets, identifiers, duplicates, and generic correlations. "
                "Prefer edges that could explain propagation, thermal/flow/pressure/electrical coupling, "
                "or degradation dynamics. JSON input:\n"
                + json.dumps(user_payload, ensure_ascii=False)
            ),
        },
    ]


def _edge_is_expert_prior(edge: Mapping[str, Any]) -> bool:
    source = str(edge.get("evidence_source", edge.get("source_type", ""))).lower()
    dominant = str(edge.get("dominant_source", "")).lower()
    relation = str(edge.get("relation", "")).lower()
    return (
        "expert" in source
        or "knowledge_prior" in source
        or "mechanism" in source
        or "expert" in dominant
        or "knowledge" in dominant
        or "expert" in relation
    )


def _compact_graph_edges(edges: Sequence[Mapping[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    compact: list[dict[str, Any]] = []
    for idx, edge in enumerate(edges[: max(1, int(limit))]):
        source = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        if not source or not target:
            continue
        compact.append(
            {
                "edge_id": str(edge.get("edge_id", f"edge_{idx:03d}")),
                "source": source,
                "target": target,
                "relation": str(edge.get("relation", "")),
                "lag": int(float(edge.get("lag", 0) or 0)),
                "reliability": float(edge.get("reliability", 0.0) or 0.0),
                "source_type": str(edge.get("evidence_source", "")),
            }
        )
    return compact


def build_llm_expert_graph_correction_messages(
    *,
    dataset: str,
    target: str,
    feature_catalog: Sequence[Mapping[str, Any]],
    expert_edges: Sequence[Mapping[str, Any]],
    max_corrections: int,
) -> list[dict[str, str]]:
    task = DATASET_TASKS.get(str(dataset).lower(), {}).get("task", "industrial time-series diagnosis")
    allowed = [str(row["name"]) for row in feature_catalog]
    user_payload = {
        "dataset": str(dataset).lower(),
        "target": str(target),
        "task": task,
        "allowed_features": allowed,
        "feature_catalog": list(feature_catalog),
        "current_expert_graph_edges": _compact_graph_edges(expert_edges, limit=48),
        "max_corrections": int(max_corrections),
        "required_json_schema": {
            "corrections": [
                {
                    "operation": "add|revise|downweight|remove",
                    "source": "one allowed feature name",
                    "target": "one allowed feature name",
                    "corrects_edge_id": "existing expert edge id when revising/downweighting/removing, otherwise empty",
                    "relation": "short corrected mechanism relation",
                    "lag": "integer 0 to 5",
                    "reliability": "float 0.03 to 0.45, because this is only a correction candidate",
                    "rationale": "one short falsifiable reason grounded in industrial mechanism",
                }
            ]
        },
    }
    return [
        {
            "role": "system",
            "content": (
                "You dynamically correct an expert mechanism graph for an industrial multivariate time-series model. "
                "Return only valid JSON. You must not create an authoritative causal graph; every output is a "
                "low-confidence correction candidate that downstream data validation may reject."
            ),
        },
        {
            "role": "user",
            "content": (
                "Inspect the current expert graph and propose a small set of corrections. "
                "Use only allowed feature names. Prefer corrections that address missing propagation links, "
                "implausible direction, overly static expert assumptions, delayed response, or dataset-specific "
                "sensor coupling. Do not include identifiers or label nodes. JSON input:\n"
                + json.dumps(user_payload, ensure_ascii=False)
            ),
        },
    ]


def build_llm_expert_condition_verifier_messages(
    *,
    dataset: str,
    target: str,
    feature_catalog: Sequence[Mapping[str, Any]],
    expert_edges: Sequence[Mapping[str, Any]],
    max_verifications: int,
) -> list[dict[str, str]]:
    task = DATASET_TASKS.get(str(dataset).lower(), {}).get("task", "industrial time-series diagnosis")
    allowed = [str(row["name"]) for row in feature_catalog]
    user_payload = {
        "dataset": str(dataset).lower(),
        "target": str(target),
        "task": task,
        "allowed_features": allowed,
        "feature_catalog": list(feature_catalog),
        "current_expert_graph_edges": _compact_graph_edges(expert_edges, limit=64),
        "max_verifications": int(max_verifications),
        "required_json_schema": {
            "verifications": [
                {
                    "expert_edge_id": "existing expert edge id from current_expert_graph_edges",
                    "source": "source feature from that expert edge",
                    "target": "target feature from that expert edge",
                    "activation": "activate|suppress|uncertain",
                    "activation_score": "float 0.0 to 1.0; conditional edge activation strength",
                    "confidence": "float 0.0 to 0.70; LLM is weak evidence only",
                    "class_scope": ["all or dataset class/fault names where this condition may hold"],
                    "regime_scope": ["all or operating/degradation regimes where this condition may hold"],
                    "residual_pattern": "short condition on residual or co-activation pattern",
                    "temporal_pattern": "short condition on lag, spike, drift, or persistence pattern",
                    "rationale": "one short falsifiable mechanism sentence",
                }
            ]
        },
    }
    return [
        {
            "role": "system",
            "content": (
                "You are a weak conditional verifier for an existing expert mechanism graph. "
                "Return only valid JSON. Do not propose new graph edges. Do not assert causal truth. "
                "Your output is only a conditional gate feature that downstream data, residual, validation, "
                "and reliability admission may reject."
            ),
        },
        {
            "role": "user",
            "content": (
                "For each selected existing expert edge, decide whether it should be conditionally activated, "
                "suppressed, or left uncertain under class, operating regime, residual, and temporal patterns. "
                "Use only expert_edge_id values from current_expert_graph_edges. Do not add new source-target pairs. "
                "Prefer specific, falsifiable conditions that can be checked by time-series residual/data support. "
                "JSON input:\n"
                + json.dumps(user_payload, ensure_ascii=False)
            ),
        },
    ]


def _json_from_text(text: str) -> Any:
    raw = str(text).strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start < 0 or end <= start:
            raise
        return json.loads(raw[start : end + 1])


def parse_llm_edge_response(
    response_text: str,
    *,
    dataset: str,
    feature_names: Sequence[str],
    max_edges: int,
    evidence_source: str = LLM_EVIDENCE_SOURCE,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    payload = _json_from_text(response_text)
    if isinstance(payload, list):
        raw_edges = payload
    elif isinstance(payload, Mapping):
        raw_edges = payload.get("edges", [])
    else:
        raw_edges = []
    if not isinstance(raw_edges, list):
        raw_edges = []

    allowed = {str(name) for name in feature_names}
    seen: set[tuple[str, str]] = set()
    edges: list[dict[str, Any]] = []
    skipped = 0
    for raw in raw_edges:
        if not isinstance(raw, Mapping):
            skipped += 1
            continue
        source = str(raw.get("source", "")).strip()
        target = str(raw.get("target", "")).strip()
        if source not in allowed or target not in allowed or source == target:
            skipped += 1
            continue
        pair = (source, target)
        if pair in seen:
            skipped += 1
            continue
        seen.add(pair)
        reliability = float(raw.get("reliability", 0.30) or 0.30)
        reliability = float(np.clip(reliability, 0.05, 0.55))
        lag = int(float(raw.get("lag", 0) or 0))
        lag = int(max(0, min(5, lag)))
        relation = str(raw.get("relation", "llm_candidate_mechanism")).strip() or "llm_candidate_mechanism"
        edges.append(
            {
                "edge_id": f"{str(dataset).lower()}_llm_{len(edges):03d}_{_safe_id(source)}_{_safe_id(target)}",
                "source": source,
                "target": target,
                "source_kind": "feature",
                "target_kind": "feature",
                "relation": relation,
                "lag": lag,
                "reliability": reliability,
                "evidence_source": str(evidence_source),
                "admission_role": "candidate_mechanism_evidence",
                "rationale": str(raw.get("rationale", relation)).strip() or relation,
            }
        )
        if len(edges) >= int(max_edges):
            break
    return edges, {
        "raw_edge_count": int(len(raw_edges)),
        "accepted_edges": int(len(edges)),
        "skipped_edges": int(skipped),
        "evidence_source": str(evidence_source),
    }


def _correction_operation(value: str) -> str:
    op = str(value or "add").strip().lower().replace("-", "_")
    aliases = {
        "insert": "add",
        "create": "add",
        "update": "revise",
        "modify": "revise",
        "lower": "downweight",
        "down_weight": "downweight",
        "decrease": "downweight",
        "delete": "remove",
        "drop": "remove",
    }
    op = aliases.get(op, op)
    return op if op in {"add", "revise", "downweight", "remove"} else "add"


def _condition_activation(value: str) -> str:
    activation = str(value or "uncertain").strip().lower().replace("-", "_")
    aliases = {
        "active": "activate",
        "enable": "activate",
        "enabled": "activate",
        "support": "activate",
        "supported": "activate",
        "verify": "activate",
        "verified": "activate",
        "deactivate": "suppress",
        "disable": "suppress",
        "disabled": "suppress",
        "downweight": "suppress",
        "remove": "suppress",
        "reject": "suppress",
        "abstain": "uncertain",
        "unknown": "uncertain",
        "conditional": "uncertain",
    }
    activation = aliases.get(activation, activation)
    return activation if activation in {"activate", "suppress", "uncertain"} else "uncertain"


def _scope_list(value: Any) -> list[str]:
    if value is None:
        return ["all"]
    if isinstance(value, str):
        items = re.split(r"[,;/|]+", value)
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        items = [str(item) for item in value]
    else:
        items = [str(value)]
    scope = [str(item).strip() for item in items if str(item).strip()]
    return scope[:12] if scope else ["all"]


def parse_llm_expert_graph_correction_response(
    response_text: str,
    *,
    dataset: str,
    feature_names: Sequence[str],
    expert_edges: Sequence[Mapping[str, Any]],
    max_corrections: int,
    evidence_source: str = LLM_EXPERT_CORRECTION_SOURCE,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    payload = _json_from_text(response_text)
    if isinstance(payload, list):
        raw_corrections = payload
    elif isinstance(payload, Mapping):
        raw_corrections = payload.get("corrections", payload.get("edges", []))
    else:
        raw_corrections = []
    if not isinstance(raw_corrections, list):
        raw_corrections = []

    allowed = {str(name) for name in feature_names}
    existing_by_id: dict[str, Mapping[str, Any]] = {}
    existing_by_pair: dict[tuple[str, str], Mapping[str, Any]] = {}
    for idx, edge in enumerate(expert_edges):
        if not isinstance(edge, Mapping):
            continue
        source = str(edge.get("source", "")).strip()
        target = str(edge.get("target", "")).strip()
        if source and target:
            existing_by_pair[(source, target)] = edge
        edge_id = str(edge.get("edge_id", f"edge_{idx:03d}")).strip()
        if edge_id:
            existing_by_id[edge_id] = edge

    seen: set[tuple[str, str, str, str]] = set()
    corrections: list[dict[str, Any]] = []
    skipped = 0
    metadata_only = 0
    for raw in raw_corrections:
        if not isinstance(raw, Mapping):
            skipped += 1
            continue
        operation = _correction_operation(str(raw.get("operation", "add")))
        corrects_edge_id = str(raw.get("corrects_edge_id", raw.get("edge_id", ""))).strip()
        existing = existing_by_id.get(corrects_edge_id) if corrects_edge_id else None
        source = str(raw.get("source", existing.get("source", "") if existing else "")).strip()
        target = str(raw.get("target", existing.get("target", "") if existing else "")).strip()
        pair_existing = existing_by_pair.get((source, target))
        if existing is None:
            existing = pair_existing
        if source not in allowed or target not in allowed or source == target:
            skipped += 1
            continue
        if operation != "add" and existing is None:
            skipped += 1
            continue
        if not corrects_edge_id and existing is not None:
            corrects_edge_id = str(existing.get("edge_id", "")).strip()
        key = (operation, source, target, corrects_edge_id)
        if key in seen:
            skipped += 1
            continue
        seen.add(key)
        reliability_default = existing.get("reliability", 0.25) if existing is not None else 0.25
        reliability = float(raw.get("reliability", reliability_default) or reliability_default)
        reliability = float(np.clip(reliability, 0.03, 0.45))
        lag_default = existing.get("lag", 0) if existing is not None else 0
        lag = int(float(raw.get("lag", lag_default) or 0))
        lag = int(max(0, min(5, lag)))
        relation_default = existing.get("relation", "expert_graph_dynamic_correction") if existing is not None else "expert_graph_dynamic_correction"
        relation = str(raw.get("relation", relation_default)).strip() or str(relation_default)
        graph_edge_candidate = operation in {"add", "revise"}
        if not graph_edge_candidate:
            metadata_only += 1
        corrections.append(
            {
                "edge_id": (
                    f"{str(dataset).lower()}_llm_expert_correction_{len(corrections):03d}_"
                    f"{_safe_id(source)}_{_safe_id(target)}_{operation}"
                ),
                "source": source,
                "target": target,
                "source_kind": "feature",
                "target_kind": "feature",
                "relation": relation,
                "lag": lag,
                "reliability": reliability,
                "evidence_source": str(evidence_source),
                "admission_role": (
                    "expert_graph_dynamic_correction_candidate"
                    if graph_edge_candidate
                    else "expert_graph_dynamic_metadata_correction"
                ),
                "graph_edge_candidate": bool(graph_edge_candidate),
                "correction_operation": operation,
                "corrects_edge_id": corrects_edge_id,
                "rationale": str(raw.get("rationale", relation)).strip() or relation,
            }
        )
        if len(corrections) >= int(max_corrections):
            break
    return corrections, {
        "raw_correction_count": int(len(raw_corrections)),
        "accepted_corrections": int(len(corrections)),
        "accepted_edges": int(sum(1 for item in corrections if bool(item.get("graph_edge_candidate", True)))),
        "metadata_only_corrections": int(metadata_only),
        "skipped_corrections": int(skipped),
        "evidence_source": str(evidence_source),
    }


def parse_llm_expert_condition_verifier_response(
    response_text: str,
    *,
    dataset: str,
    feature_names: Sequence[str],
    expert_edges: Sequence[Mapping[str, Any]],
    max_verifications: int,
    evidence_source: str = LLM_EXPERT_CONDITION_VERIFIER_SOURCE,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    payload = _json_from_text(response_text)
    if isinstance(payload, list):
        raw_verifications = payload
    elif isinstance(payload, Mapping):
        raw_verifications = payload.get("verifications", payload.get("conditions", payload.get("edges", [])))
    else:
        raw_verifications = []
    if not isinstance(raw_verifications, list):
        raw_verifications = []

    allowed = {str(name) for name in feature_names}
    existing_by_id: dict[str, Mapping[str, Any]] = {}
    existing_by_pair: dict[tuple[str, str], Mapping[str, Any]] = {}
    for idx, edge in enumerate(expert_edges):
        if not isinstance(edge, Mapping):
            continue
        source = str(edge.get("source", "")).strip()
        target = str(edge.get("target", "")).strip()
        if source and target:
            existing_by_pair[(source, target)] = edge
        edge_id = str(edge.get("edge_id", f"edge_{idx:03d}")).strip()
        if edge_id:
            existing_by_id[edge_id] = edge

    seen: set[tuple[str, str, str, tuple[str, ...], tuple[str, ...]]] = set()
    verifications: list[dict[str, Any]] = []
    skipped = 0
    activation_counts = {"activate": 0, "suppress": 0, "uncertain": 0}
    for raw in raw_verifications:
        if not isinstance(raw, Mapping):
            skipped += 1
            continue
        expert_edge_id = str(
            raw.get("expert_edge_id", raw.get("corrects_edge_id", raw.get("edge_id", "")))
        ).strip()
        existing = existing_by_id.get(expert_edge_id) if expert_edge_id else None
        source = str(raw.get("source", existing.get("source", "") if existing else "")).strip()
        target = str(raw.get("target", existing.get("target", "") if existing else "")).strip()
        if existing is None:
            existing = existing_by_pair.get((source, target))
        if existing is None:
            skipped += 1
            continue
        if not expert_edge_id:
            expert_edge_id = str(existing.get("edge_id", "")).strip()
        source = str(existing.get("source", source)).strip()
        target = str(existing.get("target", target)).strip()
        if source not in allowed or target not in allowed or source == target:
            skipped += 1
            continue
        activation = _condition_activation(str(raw.get("activation", raw.get("decision", raw.get("gate", "")))))
        class_scope = _scope_list(raw.get("class_scope", raw.get("fault_scope", "all")))
        regime_scope = _scope_list(raw.get("regime_scope", raw.get("condition_scope", "all")))
        key = (expert_edge_id, source, target, tuple(class_scope), tuple(regime_scope))
        if key in seen:
            skipped += 1
            continue
        seen.add(key)
        confidence = float(raw.get("confidence", raw.get("reliability", 0.35)) or 0.35)
        confidence = float(np.clip(confidence, 0.0, 0.70))
        activation_score = float(raw.get("activation_score", raw.get("score", confidence)) or confidence)
        activation_score = float(np.clip(activation_score, 0.0, 1.0))
        evidence_strength = float(np.clip(confidence * activation_score, 0.0, 0.70))
        lag_default = existing.get("lag", 0)
        lag = int(float(raw.get("lag", lag_default) or 0))
        lag = int(max(0, min(5, lag)))
        relation = str(raw.get("relation", existing.get("relation", "expert_edge_condition"))).strip()
        if not relation:
            relation = "expert_edge_condition"
        activation_counts[activation] += 1
        verifications.append(
            {
                "edge_id": (
                    f"{str(dataset).lower()}_llm_expert_condition_{len(verifications):03d}_"
                    f"{_safe_id(expert_edge_id or source + '_' + target)}"
                ),
                "source": source,
                "target": target,
                "source_kind": "feature",
                "target_kind": "feature",
                "relation": relation,
                "lag": lag,
                "reliability": evidence_strength,
                "confidence": confidence,
                "activation_score": activation_score,
                "evidence_source": str(evidence_source),
                "admission_role": "expert_edge_condition_gate_metadata",
                "graph_edge_candidate": False,
                "condition_verification": True,
                "condition_activation": activation,
                "expert_edge_id": expert_edge_id,
                "corrects_edge_id": expert_edge_id,
                "class_scope": class_scope,
                "regime_scope": regime_scope,
                "residual_pattern": str(raw.get("residual_pattern", "")).strip(),
                "temporal_pattern": str(raw.get("temporal_pattern", "")).strip(),
                "requires_data_support": True,
                "rationale": str(raw.get("rationale", relation)).strip() or relation,
            }
        )
        if len(verifications) >= int(max_verifications):
            break
    return verifications, {
        "raw_verification_count": int(len(raw_verifications)),
        "accepted_verifications": int(len(verifications)),
        "accepted_edges": 0,
        "skipped_verifications": int(skipped),
        "activation_counts": activation_counts,
        "evidence_source": str(evidence_source),
    }


def merge_llm_edges_into_graph(
    graph: Mapping[str, Any],
    llm_edges: Sequence[Mapping[str, Any]],
    *,
    evidence_source: str = LLM_EVIDENCE_SOURCE,
    replace_existing_source: bool = True,
) -> dict[str, Any]:
    merged = dict(graph)
    existing = list(graph.get("edges", []) or [])
    if replace_existing_source:
        existing = [edge for edge in existing if str(edge.get("evidence_source", "")) != str(evidence_source)]
    seen = {
        (str(edge.get("source", "")), str(edge.get("target", "")), str(edge.get("evidence_source", "")))
        for edge in existing
    }
    added: list[dict[str, Any]] = []
    for edge in llm_edges:
        key = (str(edge.get("source", "")), str(edge.get("target", "")), str(edge.get("evidence_source", "")))
        if key in seen:
            continue
        seen.add(key)
        added.append(dict(edge))
    merged["edges"] = existing + added
    metadata = dict(merged.get("llm_candidate_metadata", {}))
    metadata[str(evidence_source)] = {
        "n_edges": int(len(added)),
        "role": "candidate edges only; downstream reliability/path validation required",
    }
    merged["llm_candidate_metadata"] = metadata
    return merged


def merge_llm_expert_condition_verifications_into_graph(
    graph: Mapping[str, Any],
    verifications: Sequence[Mapping[str, Any]],
    *,
    evidence_source: str = LLM_EXPERT_CONDITION_VERIFIER_SOURCE,
    replace_existing_source: bool = True,
) -> dict[str, Any]:
    merged = dict(graph)
    merged["edges"] = list(graph.get("edges", []) or [])
    metadata = dict(merged.get("llm_expert_condition_verifier_metadata", {}))
    if replace_existing_source:
        metadata.pop(str(evidence_source), None)
    metadata[str(evidence_source)] = {
        "n_verifications": int(len(verifications)),
        "n_edge_candidates": 0,
        "role": (
            "conditional gate features for existing expert edges only; no LLM edge is added to the graph, "
            "and downstream data/residual/validation reliability admission must decide activation"
        ),
        "condition_verifications": [dict(item) for item in verifications],
    }
    merged["llm_expert_condition_verifier_metadata"] = metadata
    return merged


def merge_llm_expert_corrections_into_graph(
    graph: Mapping[str, Any],
    corrections: Sequence[Mapping[str, Any]],
    *,
    evidence_source: str = LLM_EXPERT_CORRECTION_SOURCE,
    replace_existing_source: bool = True,
) -> dict[str, Any]:
    merged = dict(graph)
    existing = list(graph.get("edges", []) or [])
    if replace_existing_source:
        existing = [edge for edge in existing if str(edge.get("evidence_source", "")) != str(evidence_source)]
    seen = {
        (str(edge.get("source", "")), str(edge.get("target", "")), str(edge.get("evidence_source", "")))
        for edge in existing
    }
    added: list[dict[str, Any]] = []
    metadata_only: list[dict[str, Any]] = []
    for correction in corrections:
        item = dict(correction)
        if not bool(item.get("graph_edge_candidate", True)):
            metadata_only.append(item)
            continue
        key = (str(item.get("source", "")), str(item.get("target", "")), str(item.get("evidence_source", "")))
        if key in seen:
            continue
        seen.add(key)
        added.append(item)
    merged["edges"] = existing + added
    metadata = dict(merged.get("llm_expert_graph_correction_metadata", {}))
    metadata[str(evidence_source)] = {
        "n_corrections": int(len(corrections)),
        "n_edge_candidates": int(len(added)),
        "n_metadata_only_corrections": int(len(metadata_only)),
        "role": (
            "dynamic correction of expert graph; add/revise become low-confidence candidates, "
            "downweight/remove stay metadata until data validation admits them"
        ),
        "metadata_only_corrections": metadata_only,
    }
    merged["llm_expert_graph_correction_metadata"] = metadata
    return merged


def generate_llm_evidence(
    *,
    ready_root: Path,
    dataset: str,
    target: str,
    output_dir: Path,
    max_edges: int,
    max_prompt_features: int,
    mode: str,
    response_text: str | None,
    dry_run: bool,
    merge_into_ready_graph: bool,
    temperature: float,
    timeout_sec: float,
) -> dict[str, Any]:
    name = str(dataset).lower()
    ready_dir = Path(ready_root) / name
    x = load_ready_feature_frame(ready_root, name)
    feature_names = numeric_feature_names(name, x)
    catalog = compact_feature_catalog(name, x, feature_names, max_features=max_prompt_features)
    graph_path = ready_dir / "knowledge_model" / "knowledge_graph.json"
    graph = _read_json(graph_path)
    normalized_mode = str(mode or "expert_graph_correction").strip().lower()
    if normalized_mode not in {"expert_graph_correction", "candidate_edges", "expert_condition_verifier"}:
        raise ValueError("mode must be expert_graph_correction, candidate_edges, or expert_condition_verifier")
    graph_edges = list(graph.get("edges", []) or [])
    expert_edges = [edge for edge in graph_edges if isinstance(edge, Mapping) and _edge_is_expert_prior(edge)]
    if not expert_edges:
        expert_edges = [edge for edge in graph_edges if isinstance(edge, Mapping)]
    verifications: list[dict[str, Any]] = []
    if normalized_mode == "candidate_edges":
        messages = build_llm_edge_messages(
            dataset=name,
            target=str(target),
            feature_catalog=catalog,
            existing_edges=graph_edges,
            max_edges=max_edges,
        )
    elif normalized_mode == "expert_condition_verifier":
        messages = build_llm_expert_condition_verifier_messages(
            dataset=name,
            target=str(target),
            feature_catalog=catalog,
            expert_edges=expert_edges,
            max_verifications=max_edges,
        )
    else:
        messages = build_llm_expert_graph_correction_messages(
            dataset=name,
            target=str(target),
            feature_catalog=catalog,
            expert_edges=expert_edges,
            max_corrections=max_edges,
        )
    model = str(CONFIG.get("llm_model", "gpt-5.5")).strip()
    base_url = str(CONFIG.get("llm_base_url", "https://api.n1n.ai/v1")).rstrip("/")

    if response_text is None and not dry_run:
        api_key = str(CONFIG.get("llm_api_key", "")).strip()
        if not llm_configured(api_key):
            raise RuntimeError("LLM API key is not configured; set LLM_API_KEY or STEEL_LLM_API_KEY in the environment.")
        response_text = post_chat_completions(
            api_key=api_key,
            base_url=base_url,
            model=model,
            messages=messages,
            temperature=float(temperature),
            timeout_sec=float(timeout_sec),
            max_retries=1,
        )

    edges: list[dict[str, Any]] = []
    corrections: list[dict[str, Any]] = []
    parse_diag: dict[str, Any] = {"accepted_edges": 0, "skipped_edges": 0}
    if response_text:
        if normalized_mode == "candidate_edges":
            edges, parse_diag = parse_llm_edge_response(
                response_text,
                dataset=name,
                feature_names=feature_names,
                max_edges=max_edges,
            )
        elif normalized_mode == "expert_condition_verifier":
            verifications, parse_diag = parse_llm_expert_condition_verifier_response(
                response_text,
                dataset=name,
                feature_names=feature_names,
                expert_edges=expert_edges,
                max_verifications=max_edges,
            )
        else:
            corrections, parse_diag = parse_llm_expert_graph_correction_response(
                response_text,
                dataset=name,
                feature_names=feature_names,
                expert_edges=expert_edges,
                max_corrections=max_edges,
            )
            edges = [dict(item) for item in corrections if bool(item.get("graph_edge_candidate", True))]

    schema = (
        "public_benchmark_llm_candidate_edges_v1"
        if normalized_mode == "candidate_edges"
        else (
            "public_benchmark_llm_expert_condition_verifier_v1"
            if normalized_mode == "expert_condition_verifier"
            else "public_benchmark_llm_expert_graph_dynamic_corrections_v1"
        )
    )
    bundle = {
        "schema": schema,
        "dataset": name,
        "target": str(target),
        "mode": normalized_mode,
        "model": model,
        "base_url": base_url,
        "dry_run": bool(dry_run),
        "prompt_messages": messages,
        "raw_response": str(response_text or ""),
        "edges": edges,
        "corrections": corrections,
        "verifications": verifications,
        "diagnostics": {
            **parse_diag,
            "n_allowed_features": int(len(feature_names)),
            "n_prompt_features": int(len(catalog)),
            "n_expert_edges_in_prompt": int(len(expert_edges)),
            "ready_graph": str(graph_path),
            "api_key_saved": False,
        },
    }
    output_dir = Path(output_dir)
    suffix = (
        "llm_candidate_edges"
        if normalized_mode == "candidate_edges"
        else (
            "llm_expert_condition_verifier"
            if normalized_mode == "expert_condition_verifier"
            else "llm_expert_graph_corrections"
        )
    )
    evidence_path = output_dir / f"{name}_{_safe_id(str(target))}_{suffix}.json"
    _write_json(evidence_path, bundle)

    if merge_into_ready_graph and (edges or corrections or verifications):
        if normalized_mode == "candidate_edges":
            merged = merge_llm_edges_into_graph(graph, edges)
        elif normalized_mode == "expert_condition_verifier":
            merged = merge_llm_expert_condition_verifications_into_graph(graph, verifications)
        else:
            merged = merge_llm_expert_corrections_into_graph(graph, corrections)
        _write_json(graph_path, merged)
        bundle["merged_graph_path"] = str(graph_path)
        _write_json(evidence_path, bundle)

    return {
        "status": "ok",
        "dataset": name,
        "target": str(target),
        "n_edges": int(len(edges)),
        "n_corrections": int(len(corrections)),
        "n_verifications": int(len(verifications)),
        "mode": normalized_mode,
        "evidence_path": str(evidence_path),
        "merged_graph_path": str(graph_path) if merge_into_ready_graph and (edges or corrections or verifications) else "",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate LLM-assisted expert-graph corrections for public benchmarks.")
    parser.add_argument("--ready-root", type=Path, default=DEFAULT_READY_ROOT)
    parser.add_argument("--dataset", required=True, choices=["tep", "skab", "hydraulic", "cmapss"])
    parser.add_argument("--target", default="default")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--max-edges", type=int, default=12)
    parser.add_argument("--max-prompt-features", type=int, default=120)
    parser.add_argument(
        "--mode",
        type=str,
        default="expert_graph_correction",
        choices=["expert_graph_correction", "candidate_edges", "expert_condition_verifier"],
        help=(
            "Default uses the LLM to dynamically correct the expert graph; candidate_edges keeps the legacy "
            "free-edge mode; expert_condition_verifier emits metadata-only gates for existing expert edges."
        ),
    )
    parser.add_argument("--response-file", type=Path, default=None, help="Parse an existing LLM response instead of calling the API.")
    parser.add_argument("--dry-run", action="store_true", help="Write the prompt bundle without calling the API.")
    parser.add_argument("--merge-into-ready-graph", action="store_true", help="Merge accepted LLM edge candidates/corrections to the ready knowledge_graph.json.")
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--timeout-sec", type=float, default=float(CONFIG.get("llm_timeout_sec", 45)))
    args = parser.parse_args()

    response_text = None
    if args.response_file is not None:
        with open(_fs_path(Path(args.response_file)), "r", encoding="utf-8") as handle:
            response_text = handle.read()
    result = generate_llm_evidence(
        ready_root=Path(args.ready_root),
        dataset=str(args.dataset),
        target=str(args.target),
        output_dir=Path(args.output_dir),
        max_edges=int(args.max_edges),
        max_prompt_features=int(args.max_prompt_features),
        mode=str(args.mode),
        response_text=response_text,
        dry_run=bool(args.dry_run),
        merge_into_ready_graph=bool(args.merge_into_ready_graph),
        temperature=float(args.temperature),
        timeout_sec=float(args.timeout_sec),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
