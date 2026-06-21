"""Adapter from the mechanism KG to anomaly traceability rules.

The adapter is intentionally dependency-light. It reads the mechanism KG JSON
exported by the RAG project and produces cause-defect-action rules that can be
consumed by the traceability system or imported into Neo4j.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable, Sequence


TRACE_RELATIONS = {"cause", "affect", "increase_risk_of", "indicates"}
ACTION_RELATIONS = {"improve", "suppress", "control", "reduce"}
MECHANISM_NODE_TYPES = {"ProcessParameter", "EquipmentState", "MaterialState", "DefectMechanism"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def tokens(text: str) -> set[str]:
    return {item.lower() for item in re.findall(r"[A-Za-z0-9_\u4e00-\u9fff]+", text or "")}


def evidence_text(edge: dict[str, Any]) -> str:
    evidence = edge.get("evidence") or []
    return " | ".join(str(item.get("text", "")) for item in evidence if item.get("text"))


def infer_action(cause: str, relation: str, action_candidates: Sequence[str]) -> str:
    if action_candidates:
        return " ; ".join(action_candidates[:2])
    if relation == "increase_risk_of":
        return f"Inspect and suppress upstream factor: {cause}"
    if relation == "indicates":
        return f"Verify observation and trace upstream state: {cause}"
    return f"Check, stabilize, and tune process factor: {cause}"


def collect_action_candidates(
    source_node_id: str,
    nodes_by_id: dict[str, dict[str, Any]],
    outgoing: dict[str, list[dict[str, Any]]],
) -> list[str]:
    candidates: list[str] = []
    for edge in outgoing.get(source_node_id, []):
        if edge.get("relation") not in ACTION_RELATIONS:
            continue
        target = nodes_by_id.get(edge.get("tail"), {})
        text = target.get("text")
        if text:
            candidates.append(str(text))
    return candidates


def build_traceability_rules(
    graph: dict[str, Any],
    *,
    min_confidence: float = 0.7,
    max_rules: int = 600,
) -> list[dict[str, Any]]:
    nodes_by_id = {node["node_id"]: node for node in graph.get("nodes", []) if node.get("node_id")}
    outgoing: dict[str, list[dict[str, Any]]] = {}
    for edge in graph.get("edges", []):
        outgoing.setdefault(edge.get("head", ""), []).append(edge)

    rules: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for edge in graph.get("edges", []):
        relation = edge.get("relation")
        if relation not in TRACE_RELATIONS:
            continue
        if edge.get("layer") not in {"mechanism", "application", None}:
            continue
        confidence = float(edge.get("confidence") or 0.0)
        if confidence < min_confidence:
            continue
        head = nodes_by_id.get(edge.get("head"), {})
        tail = nodes_by_id.get(edge.get("tail"), {})
        if not head or not tail:
            continue
        head_type = head.get("type", "")
        tail_type = tail.get("type", "")
        if head_type not in MECHANISM_NODE_TYPES and tail_type not in MECHANISM_NODE_TYPES | {"QualityDefect"}:
            continue
        cause = str(head.get("text", "")).strip()
        effect = str(tail.get("text", "")).strip()
        if not cause or not effect:
            continue
        defect = effect if tail_type == "QualityDefect" else f"{effect} abnormal risk"
        key = (cause, defect, relation)
        if key in seen:
            continue
        seen.add(key)
        action_candidates = collect_action_candidates(edge.get("head", ""), nodes_by_id, outgoing)
        rules.append(
            {
                "rule_id": f"mk_trace_rule_{len(rules) + 1:04d}",
                "graph_type": "steel",
                "product": "continuous_casting_quality",
                "process": "continuous_casting",
                "cause": cause,
                "defect": defect,
                "solution": infer_action(cause, relation, action_candidates),
                "relation": relation,
                "confidence": round(confidence, 4),
                "evidence": evidence_text(edge),
                "source_edge_id": edge.get("edge_id", ""),
                "source_head_type": head_type,
                "source_tail_type": tail_type,
            }
        )
        if len(rules) >= max_rules:
            break
    return rules


def score_rule(query_terms: set[str], rule: dict[str, Any]) -> float:
    fields = " ".join(str(rule.get(key, "")) for key in ["cause", "defect", "solution", "evidence"])
    rule_terms = tokens(fields)
    overlap = len(query_terms & rule_terms)
    if not query_terms:
        return 0.0
    return round((overlap / len(query_terms)) * 0.7 + float(rule.get("confidence", 0.0)) * 0.3, 4)


def trace_event(event: dict[str, Any], rules: Sequence[dict[str, Any]], *, top_k: int = 5) -> list[dict[str, Any]]:
    text_parts: list[str] = []
    for key in ["event_text", "defect", "process", "stage"]:
        text_parts.append(str(event.get(key, "")))
    for feature in event.get("features", []) or []:
        if isinstance(feature, dict):
            text_parts.extend(str(feature.get(key, "")) for key in ["name", "group", "value"])
        else:
            text_parts.append(str(feature))
    query_terms = tokens(" ".join(text_parts))
    scored = []
    for rule in rules:
        score = score_rule(query_terms, rule)
        if score > 0:
            enriched = dict(rule)
            enriched["match_score"] = score
            scored.append(enriched)
    return sorted(scored, key=lambda row: (row["match_score"], row["confidence"]), reverse=True)[:top_k]


def cypher_string(value: Any) -> str:
    return json.dumps(str(value or ""), ensure_ascii=False)


def render_cypher(rules: Sequence[dict[str, Any]]) -> str:
    lines = [
        "// Generated mechanism-KG traceability seed.",
        "// Import with cypher-shell after checking database labels and constraints.",
    ]
    for rule in rules:
        props = {
            "rule_id": rule["rule_id"],
            "graph_type": rule["graph_type"],
            "product": rule["product"],
            "process": rule["process"],
        }
        prop_text = ", ".join(f"{key}: {cypher_string(value)}" for key, value in props.items())
        lines.extend(
            [
                f"MERGE (c:Cause {{name: {cypher_string(rule['cause'])}}}) SET c += {{{prop_text}}};",
                f"MERGE (d:Defect {{name: {cypher_string(rule['defect'])}}}) SET d += {{{prop_text}}};",
                f"MERGE (s:Solution {{name: {cypher_string(rule['solution'])}}}) SET s += {{{prop_text}}};",
                f"MATCH (c:Cause {{name: {cypher_string(rule['cause'])}}}), (d:Defect {{name: {cypher_string(rule['defect'])}}}) "
                f"MERGE (c)-[r:CAUSES {{rule_id: {cypher_string(rule['rule_id'])}}}]->(d) "
                f"SET r.relation = {cypher_string(rule['relation'])}, r.confidence = {rule['confidence']}, r.evidence = {cypher_string(rule['evidence'])};",
                f"MATCH (d:Defect {{name: {cypher_string(rule['defect'])}}}), (s:Solution {{name: {cypher_string(rule['solution'])}}}) "
                f"MERGE (d)-[r:SOLVED_BY {{rule_id: {cypher_string(rule['rule_id'])}}}]->(s);",
            ]
        )
    return "\n".join(lines) + "\n"


def build_adapter_pack(
    kg_path: Path,
    output_dir: Path,
    *,
    min_confidence: float = 0.7,
    max_rules: int = 600,
) -> dict[str, Any]:
    graph = read_json(kg_path)
    rules = build_traceability_rules(graph, min_confidence=min_confidence, max_rules=max_rules)
    output_dir.mkdir(parents=True, exist_ok=True)
    rules_path = output_dir / "mechanism_traceability_rules.json"
    cypher_path = output_dir / "mechanism_traceability_seed.cypher"
    sample_event = {
        "event_id": "sample-continuous-casting-event",
        "process": "continuous_casting",
        "defect": "surface crack risk",
        "features": [
            {"name": "mold_level_range", "group": "mold_level", "value": "high"},
            {"name": "cast_speed_mean", "group": "casting_speed", "value": "fluctuating"},
        ],
    }
    sample_trace = trace_event(sample_event, rules)
    sample_path = output_dir / "sample_traceability_query.json"
    write_json(rules_path, {"status": "mechanism_traceability_rules_built", "source_kg": str(kg_path), "rules": rules})
    cypher_path.write_text(render_cypher(rules), encoding="utf-8")
    write_json(sample_path, {"sample_event": sample_event, "top_traces": sample_trace})
    summary = {
        "status": "mechanism_kg_traceability_adapter_built",
        "source_kg": str(kg_path),
        "rule_count": len(rules),
        "outputs": {
            "rules": str(rules_path),
            "cypher": str(cypher_path),
            "sample_query": str(sample_path),
        },
        "integration_boundary": "The adapter exports rules and Cypher. Online Neo4j import still depends on the deployed traceability system connection.",
    }
    write_json(output_dir / "summary.json", summary)
    return summary
