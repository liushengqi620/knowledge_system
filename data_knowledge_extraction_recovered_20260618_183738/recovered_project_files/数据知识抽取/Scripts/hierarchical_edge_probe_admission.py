from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

from build_tep_knowledge_prior import VARIABLE_SEMANTICS, expert_edges, llm_candidate_edges


VERSION = "hierarchical-edge-probe-admission-v1"
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "knowledge_exports" / "hierarchical_edge_probe_admission"


THRESHOLDS = {
    "min_validation_gain": 0.0,
    "min_low_tail_delta": -0.002,
    "max_far_delta": 0.005,
    "max_mar_delta": 0.005,
    "min_cf_sensitivity": 0.0,
}


LITERATURE_GUARDS = [
    {
        "name": "CUTS+",
        "url": "https://ojs.aaai.org/index.php/AAAI/article/view/29034",
        "implication": "probe variable and lag relations selectively instead of injecting an undifferentiated edge pool",
    },
    {
        "name": "CATCH",
        "url": "https://arxiv.org/html/2410.12261v2",
        "implication": "prefer mask, attention-bias, channel-gate, or patch/frequency relation interfaces over crude shifted-difference channels",
    },
    {
        "name": "Corr2Cause",
        "url": "https://arxiv.org/abs/2306.05836",
        "implication": "do not treat LLM correlation-to-causation judgments as reliable causal discovery",
    },
    {
        "name": "LLM causal discovery survey",
        "url": "https://www.ijcai.org/proceedings/2025/1186",
        "implication": "use LLMs as imperfect experts for candidate generation or expert-edge conditional verification",
    },
]


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _family(edge: Mapping[str, Any]) -> str:
    raw = " ".join(
        [
            str(edge.get("source", "")),
            str(edge.get("dominant_source", "")),
            str(edge.get("rationale_id", "")),
        ]
    ).lower()
    if "llm" in raw:
        return "llm"
    if "boundary" in raw or "lag_predictive" in raw or "algorithm" in raw or "data" in raw:
        return "data"
    return "expert"


def _source(edge: Mapping[str, Any]) -> str:
    return str(edge.get("from", edge.get("source", "")))


def _target(edge: Mapping[str, Any]) -> str:
    return str(edge.get("to", edge.get("target", "")))


def _lag(edge: Mapping[str, Any]) -> int:
    return int(float(edge.get("lag", 0) or 0))


def _target_group(target: str) -> str:
    return str(VARIABLE_SEMANTICS.get(str(target), {}).get("group", "unknown"))


def _lag_group(lag: int) -> str:
    if int(lag) <= 0:
        return "lag0"
    if int(lag) == 1:
        return "lag1"
    if int(lag) == 2:
        return "lag2"
    return "lag3plus"


def _edge_id(edge: Mapping[str, Any], index: int) -> str:
    raw = str(edge.get("edge_id", edge.get("rationale_id", ""))).strip()
    if raw:
        return raw
    return f"edge_{index:04d}_{_source(edge)}_to_{_target(edge)}_lag{_lag(edge)}"


def normalize_edges(edges: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    frozen: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw_edge in enumerate(edges):
        edge = dict(raw_edge)
        src = _source(edge)
        dst = _target(edge)
        if not src or not dst or src == dst:
            continue
        edge_id = _edge_id(edge, index)
        if edge_id in seen:
            continue
        seen.add(edge_id)
        lag = _lag(edge)
        family = _family(edge)
        frozen.append(
            {
                "edge_id": edge_id,
                "source": src,
                "target": dst,
                "lag": int(lag),
                "source_family": family,
                "target_group": _target_group(dst),
                "lag_group": _lag_group(lag),
                "relation": str(edge.get("relation_type", edge.get("relation", ""))),
                "confidence": float(edge.get("confidence", 0.0) or 0.0),
                "weight": float(edge.get("weight", 0.0) or 0.0),
                "raw_source": str(edge.get("source", "")),
            }
        )
    return frozen


def build_frozen_tep_candidate_pool(
    *,
    include_expert: bool = True,
    include_llm: bool = True,
    data_edges: Sequence[Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    raw: list[Mapping[str, Any]] = []
    if include_expert:
        raw.extend(expert_edges())
    if include_llm:
        raw.extend(llm_candidate_edges())
    raw.extend(list(data_edges or []))
    return normalize_edges(raw)


def _probe_id(level: str, key: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in str(key))
    return f"{level}:{safe}"


def build_probe_plan(edges: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    frozen = [dict(edge) for edge in edges]
    plan: list[dict[str, Any]] = []
    for level, key_name in [
        ("source_family", "source_family"),
        ("target_group", "target_group"),
        ("lag_group", "lag_group"),
    ]:
        keys = sorted({str(edge[key_name]) for edge in frozen})
        for key in keys:
            members = [edge["edge_id"] for edge in frozen if str(edge[key_name]) == key]
            plan.append(
                {
                    "probe_id": _probe_id(level, key),
                    "probe_level": level,
                    "probe_key": key,
                    "edge_ids": members,
                    "n_edges": int(len(members)),
                    "status": "needs_validation_probe",
                }
            )
    for edge in frozen:
        plan.append(
            {
                "probe_id": _probe_id("single_edge", edge["edge_id"]),
                "probe_level": "single_edge",
                "probe_key": edge["edge_id"],
                "edge_ids": [edge["edge_id"]],
                "n_edges": 1,
                "status": "needs_validation_probe",
            }
        )
    return plan


def _metric(row: Mapping[str, Any], key: str) -> float | None:
    value = row.get(key)
    if value is None:
        return None
    return float(value)


def evaluate_probe_row(
    row: Mapping[str, Any],
    *,
    thresholds: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    t = {**THRESHOLDS, **dict(thresholds or {})}
    reasons: list[str] = []
    stage = "validation_gain"
    cf_evaluated = False

    validation_gain = _metric(row, "validation_gain")
    if validation_gain is None:
        reasons.append("validation_gain_missing")
    elif validation_gain <= float(t["min_validation_gain"]):
        reasons.append("validation_gain_not_positive")

    if not reasons:
        stage = "low_tail_far_mar_safety"
        low_tail_delta = _metric(row, "low_tail_delta")
        far_delta = _metric(row, "far_delta")
        mar_delta = _metric(row, "mar_delta")
        if low_tail_delta is None:
            reasons.append("low_tail_delta_missing")
        elif low_tail_delta < float(t["min_low_tail_delta"]):
            reasons.append("low_tail_harm")
        if far_delta is None:
            reasons.append("far_delta_missing")
        elif far_delta > float(t["max_far_delta"]):
            reasons.append("far_increase")
        if mar_delta is None:
            reasons.append("mar_delta_missing")
        elif mar_delta > float(t["max_mar_delta"]):
            reasons.append("mar_increase")

    if not reasons:
        stage = "cf_guard"
        cf_evaluated = True
        cf_sensitivity = _metric(row, "cf_sensitivity")
        if cf_sensitivity is None:
            reasons.append("cf_sensitivity_missing")
        elif cf_sensitivity < float(t["min_cf_sensitivity"]):
            reasons.append("cf_dependency_too_weak")

    admitted = not reasons
    return {
        **dict(row),
        "admitted": bool(admitted),
        "stage_reached": stage,
        "cf_evaluated": bool(cf_evaluated),
        "reject_reasons": reasons,
    }


def admit_edges_from_probe_results(
    edges: Sequence[Mapping[str, Any]],
    probe_results: Sequence[Mapping[str, Any]],
    *,
    thresholds: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    edge_by_id = {str(edge["edge_id"]): dict(edge) for edge in edges}
    evaluated = [evaluate_probe_row(row, thresholds=thresholds) for row in probe_results]
    admitted_single = {
        str(edge_id)
        for row in evaluated
        if row["admitted"] and row.get("probe_level") == "single_edge"
        for edge_id in row.get("edge_ids", [])
    }
    admitted_edges = [edge_by_id[edge_id] for edge_id in sorted(admitted_single) if edge_id in edge_by_id]
    return {
        "version": VERSION,
        "thresholds": {**THRESHOLDS, **dict(thresholds or {})},
        "gate_order": ["validation_gain", "low_tail_far_mar_safety", "cf_guard"],
        "candidate_edges": list(edge_by_id.values()),
        "probe_results": evaluated,
        "validation_admitted_edges": admitted_edges,
        "n_validation_admitted_edges": int(len(admitted_edges)),
    }


def build_default_hierarchical_artifact(output_dir: Path | str) -> list[Path]:
    output_dir = Path(output_dir)
    os.makedirs(_fs_path(output_dir), exist_ok=True)
    candidate_edges = build_frozen_tep_candidate_pool()
    probe_plan = build_probe_plan(candidate_edges)
    payload = admit_edges_from_probe_results(candidate_edges, probe_plan)
    payload.update(
        {
            "dataset": "TEP",
            "artifact_status": "probe_plan_only_no_validation_scores",
            "candidate_pool_policy": "frozen expert and LLM candidates; data-only candidates must be added as a separate family before admission",
            "llm_role": "LLM outputs are mechanism candidates or expert-edge condition verifiers only; they are not causal discoveries.",
            "relation_interface_options": [
                "edge_mask",
                "attention_bias",
                "channel_fusion_gate",
                "patch_or_frequency_relation_mask",
                "residual_channel_after_validation_admission",
            ],
            "literature_guards": LITERATURE_GUARDS,
        }
    )
    json_path = output_dir / "hierarchical_edge_probe_admission.json"
    md_path = output_dir / "hierarchical_edge_probe_admission.md"
    with open(_fs_path(json_path), "w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    with open(_fs_path(md_path), "w", encoding="utf-8") as handle:
        handle.write(render_markdown(payload))
    return [json_path, md_path]


def render_markdown(payload: Mapping[str, Any]) -> str:
    rows = list(payload.get("probe_results", []) or [])
    edges = list(payload.get("candidate_edges", []) or [])
    family_counts: dict[str, int] = {}
    for edge in edges:
        family_counts[str(edge.get("source_family", "unknown"))] = family_counts.get(str(edge.get("source_family", "unknown")), 0) + 1
    lines = [
        "# Hierarchical Edge Probe Admission",
        "",
        f"- Version: {payload.get('version', VERSION)}",
        f"- Dataset: {payload.get('dataset', 'unknown')}",
        f"- Artifact status: {payload.get('artifact_status', '')}",
        f"- Candidate edges: {len(edges)}",
        f"- Validation-admitted edges: {payload.get('n_validation_admitted_edges', 0)}",
        f"- Gate order: {', '.join(payload.get('gate_order', []))}",
        f"- LLM role: {payload.get('llm_role', '')}",
        "",
        "## Source-Family Counts",
        "",
        "| Family | Edges |",
        "|---|---:|",
    ]
    for family, count in sorted(family_counts.items()):
        lines.append(f"| {family} | {count} |")
    lines.extend(
        [
            "",
            "## Probe Levels",
            "",
            "| Level | Probes | Edges Covered |",
            "|---|---:|---:|",
        ]
    )
    for level in ["source_family", "target_group", "lag_group", "single_edge"]:
        level_rows = [row for row in rows if row.get("probe_level") == level]
        covered = sum(int(row.get("n_edges", 0) or 0) for row in level_rows)
        lines.append(f"| {level} | {len(level_rows)} | {covered} |")
    lines.extend(
        [
            "",
            "## Guard Interpretation",
            "",
            "- CF guard is evaluated only after validation gain and low-tail/FAR/MAR safety pass.",
            "- A high CF sensitivity on a harmful edge is not treated as evidence of usefulness.",
            "- Missing validation-gain measurements reject candidates before CF, so CF/no-CF fallback to baseline is interpreted as a functioning reliability guard.",
            "- Final `validation_admitted_edges` must be formed from single-edge probes that pass the ordered gates.",
            "",
            "## Relation Interfaces",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in payload.get("relation_interface_options", []))
    lines.extend(["", "## Literature Guards", ""])
    for item in payload.get("literature_guards", []):
        lines.append(f"- {item['name']}: {item['url']} -> {item['implication']}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build hierarchical edge probe/admission artifact.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    for path in build_default_hierarchical_artifact(args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
