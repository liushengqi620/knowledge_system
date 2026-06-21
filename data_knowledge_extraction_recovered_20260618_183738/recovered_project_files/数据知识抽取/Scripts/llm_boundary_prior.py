from __future__ import annotations

import json
import re
from typing import Any, Mapping, Sequence

import numpy as np

from research_types import GraphEdge


def _safe_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_llm_boundary_prior(text: str, feature_names: Sequence[str]) -> list[GraphEdge]:
    """Parse LLM-proposed graph candidates without trusting them as evidence."""

    known = {str(name) for name in feature_names}
    match = re.search(r"\{[\s\S]*\}", str(text or "").strip())
    if not match:
        return []
    try:
        payload = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    rows = payload.get("edges") if isinstance(payload, Mapping) else None
    if not isinstance(rows, list):
        return []
    out: list[GraphEdge] = []
    for idx, row in enumerate(rows):
        if not isinstance(row, Mapping):
            continue
        src = str(row.get("from") or row.get("source") or "").strip()
        dst = str(row.get("to") or row.get("target") or "").strip()
        if src not in known or dst not in known or src == dst:
            continue
        confidence = float(np.clip(_safe_float(row.get("confidence"), 0.55), 0.0, 1.0))
        weight = float(np.clip(_safe_float(row.get("weight"), 0.50), 0.0, 1.0))
        out.append(
            GraphEdge(
                from_node=src,
                to_node=dst,
                weight=weight,
                confidence=confidence,
                source="llm_boundary_candidate",
                rationale_id=str(row.get("rationale_id") or f"llm_boundary_{idx}"),
                relation_type=str(row.get("relation_type") or "event_precursor"),
                lag=max(1, int(_safe_float(row.get("lag"), 1))),
                causal_strength=float(np.clip(_safe_float(row.get("causal_strength"), confidence), 0.0, 1.0)),
                stability=float(np.clip(_safe_float(row.get("stability"), confidence), 0.0, 1.0)),
                evidence={
                    "knowledge_prior": confidence,
                    "llm_candidate": confidence,
                    "boundary_verified": 0.0,
                },
                dominant_source="llm_candidate",
            )
        )
    return out


def _boundary_support(edge: GraphEdge) -> float:
    evidence = dict(edge.evidence or {})
    return float(
        np.clip(
            max(
                _safe_float(evidence.get("lag_predictive_gain"), 0.0),
                _safe_float(evidence.get("boundary_enrichment"), 0.0),
                _safe_float(evidence.get("boundary_verified"), 0.0),
                float(edge.weight),
            ),
            0.0,
            1.0,
        )
    )


def audit_llm_candidate_edges(
    candidate_edges: Sequence[GraphEdge],
    boundary_edges: Sequence[GraphEdge],
    *,
    min_support: float = 0.10,
) -> tuple[list[GraphEdge], list[dict[str, Any]]]:
    """Accept LLM candidates only when data-derived boundary edges support them."""

    boundary_by_pair = {(edge.from_node, edge.to_node): edge for edge in boundary_edges}
    accepted: list[GraphEdge] = []
    review: list[dict[str, Any]] = []
    threshold = max(0.0, float(min_support))
    for edge in candidate_edges:
        support_edge = boundary_by_pair.get((edge.from_node, edge.to_node))
        if support_edge is None:
            review.append(
                {
                    "from": edge.from_node,
                    "to": edge.to_node,
                    "status": "rejected_no_boundary_support",
                    "llm_confidence": float(edge.confidence),
                    "boundary_support": 0.0,
                }
            )
            continue
        support = _boundary_support(support_edge)
        if support < threshold:
            review.append(
                {
                    "from": edge.from_node,
                    "to": edge.to_node,
                    "status": "rejected_weak_boundary_support",
                    "llm_confidence": float(edge.confidence),
                    "boundary_support": support,
                }
            )
            continue
        evidence = dict(edge.evidence or {})
        evidence.update(
            {
                "knowledge_prior": float(np.clip(edge.confidence, 0.0, 1.0)),
                "llm_candidate": float(np.clip(edge.confidence, 0.0, 1.0)),
                "boundary_verified": support,
            }
        )
        accepted.append(
            GraphEdge(
                from_node=edge.from_node,
                to_node=edge.to_node,
                weight=float(np.clip(0.5 * edge.weight + 0.5 * support_edge.weight, 0.0, 1.0)),
                confidence=float(np.clip(0.5 * edge.confidence + 0.5 * support_edge.confidence, 0.0, 1.0)),
                source="llm_boundary_verified",
                rationale_id=edge.rationale_id,
                relation_type=edge.relation_type or support_edge.relation_type,
                lag=int(support_edge.lag or edge.lag),
                causal_strength=float(np.clip(max(edge.causal_strength, support_edge.causal_strength), 0.0, 1.0)),
                stability=float(np.clip(max(edge.stability, support_edge.stability), 0.0, 1.0)),
                is_control_loop=bool(edge.is_control_loop or support_edge.is_control_loop),
                is_feedback=bool(edge.is_feedback or support_edge.is_feedback),
                legal=bool(edge.legal and support_edge.legal),
                evidence=evidence,
                dominant_source="boundary_verified",
                regime_context=str(support_edge.regime_context or "boundary"),
            )
        )
        review.append(
            {
                "from": edge.from_node,
                "to": edge.to_node,
                "status": "accepted",
                "llm_confidence": float(edge.confidence),
                "boundary_support": support,
            }
        )
    return accepted, review
