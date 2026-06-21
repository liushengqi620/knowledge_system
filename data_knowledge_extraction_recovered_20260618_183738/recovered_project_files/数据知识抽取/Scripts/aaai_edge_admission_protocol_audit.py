from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = REPO_ROOT / "knowledge_exports"
DEFAULT_OUTPUT_DIR = EXPORT_DIR / "edge_admission_protocol_audit"
DEFAULT_HIERARCHICAL_CONTRACT = (
    EXPORT_DIR / "hierarchical_edge_probe_admission" / "hierarchical_edge_probe_admission.json"
)
DEFAULT_TEP_PROBE = (
    EXPORT_DIR / "hierarchical_edge_probe_admission" / "tep_hierarchical_edge_validation_probe_3seed_fullrows.json"
)
DEFAULT_LLM_MATRIX = (
    EXPORT_DIR / "ms_gse_rpf_llm_condition_ablation_full" / "llm_condition_verifier_ablation_matrix.json"
)
DEFAULT_MECHANISM_MATRIX = (
    EXPORT_DIR / "ms_gse_rpf_mechanism_gate_ablation_full" / "mechanism_gate_ablation_matrix.json"
)

REQUIRED_GATE_ORDER = ["validation_gain", "low_tail_far_mar_safety", "cf_guard"]
REQUIRED_PROBE_LEVELS = {"source_family", "target_group", "lag_group", "single_edge"}
REQUIRED_RELATION_INTERFACES = {
    "edge_mask",
    "attention_bias",
    "channel_fusion_gate",
    "patch_or_frequency_relation_mask",
}
REQUIRED_LLM_VARIANTS = {
    "a0_algorithmic_only",
    "a1_expert_candidate_gate",
    "a2_independent_llm_candidate",
    "a3_llm_expert_graph_correction",
    "a4_llm_expert_condition_verifier",
    "a5_weak_class_condition_verifier",
}
REQUIRED_MECHANISM_VARIANTS = {
    "no_mechanism",
    "raw_expert_graph",
    "expert_candidate_data_gate",
    "algorithmic_candidate_gate_control",
}


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _read_json(path: Path | str) -> dict[str, Any]:
    source = Path(path)
    if not os.path.exists(_fs_path(source)):
        return {}
    with open(_fs_path(source), encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, dict) else {}


def _requirement(
    requirement_id: str,
    title: str,
    status: str,
    evidence: str,
    next_action: str,
) -> dict[str, str]:
    return {
        "id": requirement_id,
        "title": title,
        "status": status,
        "evidence": evidence,
        "next_action": next_action,
    }


def _gate_order(payload: Mapping[str, Any]) -> list[str]:
    raw = payload.get("gate_order")
    if raw is None:
        raw = (payload.get("admission") or {}).get("gate_order")
    return [str(item) for item in (raw or [])]


def _probe_levels(payload: Mapping[str, Any], *, key: str = "probe_results") -> set[str]:
    rows = payload.get(key)
    if rows is None:
        rows = payload.get("probe_plan")
    return {str(row.get("probe_level")) for row in (rows or []) if isinstance(row, Mapping)}


def _source_families(payload: Mapping[str, Any]) -> set[str]:
    return {
        str(edge.get("source_family"))
        for edge in (payload.get("candidate_edges") or [])
        if isinstance(edge, Mapping) and edge.get("source_family")
    }


def audit_hierarchical_contract(payload: Mapping[str, Any]) -> dict[str, str]:
    if not payload:
        return _requirement(
            "hierarchical_contract",
            "Freeze and hierarchically probe candidate edge pools",
            "missing",
            "The hierarchical edge-admission contract JSON is missing.",
            "Regenerate hierarchical_edge_probe_admission before building the paper package.",
        )
    gate_ok = _gate_order(payload) == REQUIRED_GATE_ORDER
    levels = _probe_levels(payload)
    families = _source_families(payload)
    interfaces = {str(item) for item in payload.get("relation_interface_options", [])}
    llm_role = str(payload.get("llm_role", "")).lower()
    status = (
        "satisfied"
        if gate_ok
        and REQUIRED_PROBE_LEVELS.issubset(levels)
        and {"expert", "llm"}.issubset(families)
        and REQUIRED_RELATION_INTERFACES.issubset(interfaces)
        and "not causal discoveries" in llm_role
        else "partial"
    )
    return _requirement(
        "hierarchical_contract",
        "Freeze and hierarchically probe candidate edge pools",
        status,
        (
            f"Gate order={_gate_order(payload)}; probe levels={sorted(levels)}; "
            f"families={sorted(families)}; relation interfaces={sorted(interfaces)}."
        ),
        (
            "Keep source-family, target-group, lag-group, and single-edge probes synchronized with every new candidate source."
            if status == "satisfied"
            else "Add the missing gate order, probe level, source-family, LLM-role, or relation-interface metadata."
        ),
    )


def _single_edge_gate_map(payload: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    admission = payload.get("admission") or {}
    return {
        str(row.get("probe_key") or row.get("edge_id"))
        : row
        for row in (admission.get("probe_results") or [])
        if isinstance(row, Mapping) and row.get("probe_level") == "single_edge"
    }


def audit_measured_tep_probe(payload: Mapping[str, Any]) -> dict[str, str]:
    if not payload:
        return _requirement(
            "measured_tep_probe",
            "Materialize measured hierarchical edge-probe evidence",
            "missing",
            "The TEP hierarchical edge validation probe JSON is missing.",
            "Run tep_single_edge_validation_probe.py with source-family, target-group, lag-group, and single-edge probes.",
        )
    admission = payload.get("admission") or {}
    levels = set(str(item) for item in payload.get("probe_levels", []) or [])
    gate_ok = _gate_order(admission) == REQUIRED_GATE_ORDER
    single_gate = _single_edge_gate_map(payload)
    admitted_edges = list(admission.get("validation_admitted_edges") or [])
    admitted_ids = [str(edge.get("edge_id")) for edge in admitted_edges if isinstance(edge, Mapping)]
    admitted_from_single = all(
        str(edge_id) in single_gate and bool(single_gate[str(edge_id)].get("admitted"))
        for edge_id in admitted_ids
    )
    admitted_cf_evaluated = all(bool(single_gate[str(edge_id)].get("cf_evaluated")) for edge_id in admitted_ids)
    pre_cf_rejections = [
        row
        for row in (admission.get("probe_results") or [])
        if isinstance(row, Mapping)
        and not bool(row.get("admitted"))
        and not bool(row.get("cf_evaluated"))
        and str(row.get("stage_reached")) in {"validation_gain", "low_tail_far_mar_safety"}
    ]
    seeds = [int(seed) for seed in payload.get("seeds", []) or []]
    evidence_complete = len(seeds) >= 3 and payload.get("max_rows") is None
    protocol_ok = (
        str(payload.get("status")) == "ok"
        and str(payload.get("protocol")) == "hierarchical_validation_gain_then_safety_then_cf"
        and REQUIRED_PROBE_LEVELS.issubset(levels)
        and gate_ok
        and admitted_from_single
        and admitted_cf_evaluated
        and bool(pre_cf_rejections)
    )
    if protocol_ok and evidence_complete:
        status = "satisfied"
    elif protocol_ok:
        status = "partial"
    else:
        status = "failed"
    return _requirement(
        "measured_tep_probe",
        "Materialize measured hierarchical edge-probe evidence",
        status,
        (
            f"TEP probe status={payload.get('status')}; seeds={seeds}; max_rows={payload.get('max_rows')}; "
            f"levels={sorted(levels)}; admitted_edges={admitted_ids}; pre_cf_rejections={len(pre_cf_rejections)}."
        ),
        (
            "Upgrade the smoke to a full three-seed, full-row measured probe before treating it as final experiment evidence."
            if status == "partial"
            else "Keep the measured probe archived with seed-level rows and admitted single-edge records."
            if status == "satisfied"
            else "Fix the measured probe so admitted edges come only from single-edge passes and CF is evaluated only after validation/safety gates."
        ),
    )


def _variant_names(payload: Mapping[str, Any]) -> set[str]:
    return {
        str(item.get("name") or item.get("variant"))
        for item in (payload.get("variants") or payload.get("summary") or [])
        if isinstance(item, Mapping)
    }


def _command_tokens(payload: Mapping[str, Any], variant: str) -> list[str]:
    commands = payload.get("commands") or {}
    raw = commands.get(variant) if isinstance(commands, Mapping) else None
    return [str(item) for item in (raw or [])]


def audit_llm_condition_matrix(payload: Mapping[str, Any]) -> dict[str, str]:
    if not payload:
        return _requirement(
            "llm_condition_matrix",
            "Compare independent LLM edges against conditional expert-edge verification",
            "missing",
            "The LLM condition-verifier ablation matrix JSON is missing.",
            "Generate llm_condition_verifier_ablation_matrix with a0--a5 variants.",
        )
    names = _variant_names(payload)
    a4 = _command_tokens(payload, "a4_llm_expert_condition_verifier")
    a2 = _command_tokens(payload, "a2_independent_llm_candidate")
    a4_joined = " ".join(a4)
    a2_joined = " ".join(a2)
    summary = [row for row in (payload.get("summary") or []) if isinstance(row, Mapping)]
    complete_runs = [
        row.get("variant")
        for row in summary
        if int(row.get("n_runs", 0) or 0) >= len(payload.get("seeds", []) or [])
        and len(payload.get("seeds", []) or []) > 0
    ]
    rejected_runs = [str(row.get("variant")) for row in summary if str(row.get("status")) == "rejected"]
    admitted_runs = [str(row.get("variant")) for row in summary if str(row.get("status")) == "admitted"]
    protocol_ok = (
        REQUIRED_LLM_VARIANTS.issubset(names)
        and "--use-llm-expert-condition-verifier" in a4
        and "--llm-condition-verifier-target candidate_gate" in a4_joined
        and "--external-edge-candidate-only" not in a4
        and "--external-candidate-families llm" in a2_joined
    )
    if protocol_ok and len(complete_runs) >= len(REQUIRED_LLM_VARIANTS):
        status = "satisfied"
    elif protocol_ok:
        status = "partial"
    else:
        status = "failed"
    return _requirement(
        "llm_condition_matrix",
        "Compare independent LLM edges against conditional expert-edge verification",
        status,
        (
            f"Variants={sorted(names)}; complete run rows={complete_runs}; "
            f"admitted={admitted_runs}; rejected={rejected_runs}; "
            "a4 uses verifier metadata and a2 keeps independent LLM as a negative control."
        ),
        (
            "Report current LLM verifier evidence as reliability-gated negative/diagnostic evidence unless a future verified matrix passes validation and low-tail guards."
            if status == "satisfied" and not admitted_runs
            else "Execute the full matrix once reviewed LLM verifier metadata is available; keep a2/a5 as controls."
            if status == "partial"
            else "Keep LLM condition-verifier evidence and independent-LLM controls under the same validation-gain certificate."
            if status == "satisfied"
            else "Restore a0--a5 variants with a4 metadata-only condition verification and a2 independent LLM control."
        ),
    )


def audit_mechanism_gate_matrix(payload: Mapping[str, Any]) -> dict[str, str]:
    if not payload:
        return _requirement(
            "mechanism_gate_matrix",
            "Prove mechanism evidence helps through admission rather than raw graph injection",
            "missing",
            "The SKAB mechanism-gate ablation matrix JSON is missing.",
            "Generate mechanism_gate_ablation_matrix under the planned seeds.",
        )
    names = _variant_names(payload)
    summary = [row for row in (payload.get("summary") or []) if isinstance(row, Mapping)]
    expected_seed_count = len(payload.get("seeds", []) or [])
    complete = [
        str(row.get("variant"))
        for row in summary
        if expected_seed_count and int(row.get("n_runs", 0) or 0) >= expected_seed_count
    ]
    has_negative = "raw_expert_graph" in names
    has_data_gate = "expert_candidate_data_gate" in names or "expert_candidate_data_gate_consistency" in names
    has_algorithmic = "algorithmic_candidate_gate_control" in names
    protocol_ok = {"no_mechanism", "raw_expert_graph"}.issubset(names) and has_data_gate and has_algorithmic
    if protocol_ok and len(complete) >= 4:
        status = "satisfied"
    elif protocol_ok:
        status = "partial"
    else:
        status = "failed"
    return _requirement(
        "mechanism_gate_matrix",
        "Prove mechanism evidence helps through admission rather than raw graph injection",
        status,
        (
            f"Variants={sorted(names)}; complete rows={complete}; "
            f"negative_control={has_negative}; data_gate={has_data_gate}; algorithmic_control={has_algorithmic}."
        ),
        (
            "Keep raw-expert, data-gated expert, and algorithmic controls in the same seed/budget matrix."
            if status == "satisfied"
            else "Complete the missing rows under the same seeds and budget before using mechanism-gate evidence as a final claim."
        ),
    )


def build_protocol_audit(
    *,
    hierarchical_contract: Path | str = DEFAULT_HIERARCHICAL_CONTRACT,
    tep_probe: Path | str = DEFAULT_TEP_PROBE,
    llm_matrix: Path | str = DEFAULT_LLM_MATRIX,
    mechanism_matrix: Path | str = DEFAULT_MECHANISM_MATRIX,
) -> dict[str, Any]:
    requirements = [
        audit_hierarchical_contract(_read_json(hierarchical_contract)),
        audit_measured_tep_probe(_read_json(tep_probe)),
        audit_llm_condition_matrix(_read_json(llm_matrix)),
        audit_mechanism_gate_matrix(_read_json(mechanism_matrix)),
    ]
    failed = [item for item in requirements if item["status"] in {"missing", "failed"}]
    partial = [item for item in requirements if item["status"] == "partial"]
    if failed:
        overall = "protocol_contract_incomplete"
    elif partial:
        overall = "protocol_contract_complete_evidence_partial"
    else:
        overall = "protocol_and_evidence_complete"
    return {
        "schema": "aaai_edge_admission_protocol_audit_v1",
        "overall_status": overall,
        "artifact_paths": {
            "hierarchical_contract": str(hierarchical_contract),
            "tep_probe": str(tep_probe),
            "llm_matrix": str(llm_matrix),
            "mechanism_matrix": str(mechanism_matrix),
        },
        "required_gate_order": REQUIRED_GATE_ORDER,
        "required_probe_levels": sorted(REQUIRED_PROBE_LEVELS),
        "required_relation_interfaces": sorted(REQUIRED_RELATION_INTERFACES),
        "requirements": requirements,
        "paper_policy": (
            "Use the protocol as the method contract now. The current three-seed/full-row TEP probe is measured "
            "edge-admission evidence for the bounded probe plan and admits no single edge under the ordered guards; "
            "the full SKAB LLM verifier matrix is complete and treats LLM evidence as reliability-gated negative/diagnostic "
            "evidence because no LLM branch passes validation and low-tail admission."
        ),
        "next_actions": [
            item["next_action"]
            for item in requirements
            if item["status"] in {"missing", "failed", "partial"}
        ],
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# AAAI Edge Admission Protocol Audit",
        "",
        f"- Overall status: {report.get('overall_status')}",
        f"- Gate order: {', '.join(report.get('required_gate_order', []))}",
        f"- Probe levels: {', '.join(report.get('required_probe_levels', []))}",
        f"- Relation interfaces: {', '.join(report.get('required_relation_interfaces', []))}",
        "",
        "This audit checks whether the paper's edge/path-fusion story is backed by reusable experiment artifacts. "
        "It deliberately separates the protocol contract from measured evidence, including negative evidence.",
        "",
        "## Requirement Status",
        "",
        "| Requirement | Status | Evidence | Next action |",
        "|---|---|---|---|",
    ]
    for item in report.get("requirements", []) or []:
        lines.append(
            f"| {item.get('title')} | {item.get('status')} | {item.get('evidence')} | {item.get('next_action')} |"
        )
    lines.extend(
        [
            "",
            "## Paper Policy",
            "",
            str(report.get("paper_policy", "")),
            "",
            "## Next Actions",
            "",
        ]
    )
    next_actions = list(report.get("next_actions") or [])
    if next_actions:
        lines.extend(f"- {item}" for item in next_actions)
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def write_protocol_audit(output_dir: Path | str) -> list[Path]:
    output_dir = Path(output_dir)
    os.makedirs(_fs_path(output_dir), exist_ok=True)
    report = build_protocol_audit()
    json_path = output_dir / "aaai_edge_admission_protocol_audit.json"
    md_path = output_dir / "aaai_edge_admission_protocol_audit.md"
    with open(_fs_path(json_path), "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    with open(_fs_path(md_path), "w", encoding="utf-8") as handle:
        handle.write(render_markdown(report))
    return [json_path, md_path]


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Audit the AAAI edge/path admission protocol artifacts.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(list(argv) if argv is not None else None)
    for path in write_protocol_audit(args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
