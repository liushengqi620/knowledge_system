from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RESULT_DIR = PROJECT_ROOT / "knowledge_exports" / "ms_gse_rpf"


def _fs_path(path: Path) -> str:
    if os.name == "nt":
        resolved = str(Path(path).resolve())
        if not resolved.startswith("\\\\?\\"):
            return "\\\\?\\" + resolved
    return str(path)


def _iter_result_files(result_dir: Path) -> list[Path]:
    root = Path(result_dir)
    files: list[Path] = []
    try:
        with os.scandir(_fs_path(root)) as entries:
            for entry in entries:
                if not entry.is_file():
                    continue
                name = str(entry.name)
                if name.startswith("ms_gse_rpf_") and "_seed" in name and name.endswith(".json"):
                    files.append(root / name)
    except FileNotFoundError:
        return []
    return sorted(files, key=lambda item: item.name)


def load_runs(
    result_dir: Path,
    *,
    dataset: str | None = None,
    target: str | None = None,
    variants: set[str] | None = None,
    filename_contains: str | None = None,
    n_rows_total: int | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in _iter_result_files(result_dir):
        if filename_contains and str(filename_contains) not in path.name:
            continue
        with open(_fs_path(path), "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if dataset and str(payload.get("dataset")) != str(dataset):
            continue
        if target and str(payload.get("target")) != str(target):
            continue
        if variants is not None and str(payload.get("variant")) not in variants:
            continue
        if n_rows_total is not None and int(payload.get("n_rows_total", -1)) != int(n_rows_total):
            continue
        payload["_path"] = str(path)
        rows.append(payload)
    return rows


def _metric(row: Mapping[str, Any], key: str) -> float:
    metrics = row.get("primary_test_metrics") or row.get("test_metrics") or {}
    if key not in metrics and key == "macro_f1":
        return float(metrics.get("aux_macro_f1", (row.get("test_metrics") or {}).get("macro_f1", 0.0)))
    if key not in metrics and key == "balanced_accuracy":
        return float(metrics.get("aux_balanced_accuracy", (row.get("test_metrics") or {}).get("balanced_accuracy", 0.0)))
    return float(metrics.get(key, 0.0))


def _mean_std(values: Sequence[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    return float(mean(values)), float(pstdev(values))


def _run_prior_label(row: Mapping[str, Any]) -> str:
    prior = row.get("evidence_prior") or {}
    prior_label = str(prior.get("mode", "none"))
    if prior.get("enabled"):
        strength = ((row.get("diagnostics") or {}).get("config") or {}).get("prior_strength")
        if strength is not None:
            prior_label = f"{prior_label}@{float(strength):.2f}"
    return prior_label


def _run_setting_label(row: Mapping[str, Any]) -> str:
    budget = row.get("path_budget") or {}
    efficiency = row.get("efficiency") or {}
    diagnostics = row.get("diagnostics") or {}
    config = diagnostics.get("config") or {}
    parts: list[str] = []

    coverage_mode = str(budget.get("path_coverage_mode", "target_group") or "target_group")
    if coverage_mode != "target_group":
        parts.append(coverage_mode)
    dedup_mode = str(budget.get("coverage_dedup_mode", "soft") or "soft")
    if dedup_mode != "soft":
        parts.append(f"dedup-{dedup_mode}")
    if bool(budget.get("deduplicate_exact_paths", config.get("deduplicate_exact_paths", False))):
        parts.append("dedup-exact")

    if bool(budget.get("use_regime_prototype_residuals", False)):
        k = int(budget.get("regime_prototype_k", 0) or 0)
        parts.append(f"regime{k}" if k > 0 else "regime")
    if bool(budget.get("protect_order_anchor_path_nodes", False)):
        parts.append("no-order-path")
    elif bool(budget.get("protect_order_anchor_target", False)):
        parts.append("no-order-target")

    if bool(budget.get("use_task_salience", False)):
        mode = str(budget.get("salience_mode", "class") or "class")
        strength = float(budget.get("salience_selection_strength", 0.0) or 0.0)
        coverage = float(budget.get("salience_coverage_fraction", 0.0) or 0.0)
        label = f"salience-{mode}@{strength:.2f}"
        if coverage > 0.0:
            label = f"{label}-cover{coverage:.2f}"
        parts.append(label)
    elif float(budget.get("salience_coverage_fraction", 0.0) or 0.0) > 0.0:
        parts.append(f"salience-cover@{float(budget.get('salience_coverage_fraction')):.2f}")
    if bool(budget.get("use_temporal_descriptors", False)):
        parts.append("temporal-desc")
    temporal_encoder_mode = str(budget.get("temporal_encoder_mode", config.get("temporal_encoder_mode", "multi_scale_causal")) or "multi_scale_causal")
    if temporal_encoder_mode != "multi_scale_causal":
        parts.append(f"temporal-{temporal_encoder_mode.replace('_', '-')}")
    if bool(budget.get("use_temporal_mixer", False)):
        depth = int(budget.get("temporal_mixer_depth", 3) or 3)
        parts.append(f"temporal-mixer-d{depth}")
    focal = float(budget.get("focal_loss_gamma", 0.0) or 0.0)
    if focal > 0.0:
        parts.append(f"focal{focal:.2f}")
    smoothing = float(budget.get("label_smoothing", 0.0) or 0.0)
    if smoothing > 0.0:
        parts.append(f"smooth{smoothing:.2f}")
    if bool(budget.get("use_prototype_posterior_fusion", False)):
        max_blend = float(budget.get("prototype_fusion_max_blend", 0.50) or 0.0)
        proto_label = f"proto-post-b{max_blend:.2f}"
        min_gain = float(budget.get("prototype_fusion_min_val_gain", 0.0) or 0.0)
        if min_gain > 0.0:
            proto_label = f"{proto_label}-mingain{min_gain:.3f}"
        parts.append(proto_label)
    ordinal_boundary = float(budget.get("ordinal_boundary_loss_weight", 0.0) or 0.0)
    if ordinal_boundary > 0.0:
        gamma = float(budget.get("ordinal_boundary_focal_gamma", 0.0) or 0.0)
        focus = float(budget.get("ordinal_boundary_focus", 0.0) or 0.0)
        parts.append(f"ord-boundary-w{ordinal_boundary:.3f}-g{gamma:.2f}-f{focus:.2f}")
    if bool(budget.get("use_multihop_paths", False)):
        parts.append(f"multihop@{float(budget.get('multihop_path_fraction', 0.0) or 0.0):.2f}")
    if bool(budget.get("use_class_conditioned_prior_admission", config.get("use_class_conditioned_prior_admission", False))):
        floor = float(budget.get("class_prior_admission_floor", config.get("class_prior_admission_floor", 0.10)) or 0.0)
        prior_label = f"class-prior-admit-f{floor:.2f}"
        if bool(budget.get("use_adaptive_prior_admission", config.get("use_adaptive_prior_admission", False))):
            threshold = float(budget.get("adaptive_prior_admission_threshold", config.get("adaptive_prior_admission_threshold", 0.20)) or 0.0)
            temperature = float(budget.get("adaptive_prior_admission_temperature", config.get("adaptive_prior_admission_temperature", 0.05)) or 0.0)
            prior_label = f"{prior_label}-adaptive@{threshold:.2f}t{temperature:.2f}"
        parts.append(prior_label)
    if bool(budget.get("use_candidate_prior_admission", config.get("use_candidate_prior_admission", False))):
        floor = float(
            budget.get("candidate_prior_admission_floor", config.get("candidate_prior_admission_floor", 0.05))
            or 0.0
        )
        threshold = float(
            budget.get("candidate_prior_admission_threshold", config.get("candidate_prior_admission_threshold", 0.50))
            or 0.0
        )
        temperature = float(
            budget.get("candidate_prior_admission_temperature", config.get("candidate_prior_admission_temperature", 0.05))
            or 0.0
        )
        mode = str(
            budget.get(
                "candidate_prior_admission_support_mode",
                config.get("candidate_prior_admission_support_mode", "relative_evidence"),
            )
            or "relative_evidence"
        )
        scale = float(
            budget.get("candidate_prior_admission_scale", config.get("candidate_prior_admission_scale", 0.50))
            or 0.0
        )
        min_support = float(
            budget.get("candidate_prior_admission_min_support", config.get("candidate_prior_admission_min_support", 0.0))
            or 0.0
        )
        protected_min_support = float(
            budget.get(
                "candidate_prior_admission_protected_min_support",
                config.get("candidate_prior_admission_protected_min_support", 0.0),
            )
            or 0.0
        )
        target = str(
            budget.get("candidate_prior_admission_target", config.get("candidate_prior_admission_target", "coverage"))
            or "coverage"
        )
        label = f"candidate-prior-admit-f{floor:.2f}-thr{threshold:.2f}-t{temperature:.2f}-{mode}-s{scale:.2f}"
        if target != "coverage":
            label = f"{label}-{target}"
        if min_support > 0.0:
            label = f"{label}-minsup{min_support:.2f}"
        if protected_min_support > 0.0:
            label = f"{label}-pmin{protected_min_support:.2f}"
        parts.append(label)
    if bool(budget.get("use_path_reliability_calibrator", config.get("use_path_reliability_calibrator", False))):
        rel_label = "path-rel-cal"
        rel_scale = float(budget.get("path_reliability_context_scale", config.get("path_reliability_context_scale", 1.0)) or 0.0)
        if abs(rel_scale - 1.0) > 1.0e-9:
            rel_label = f"{rel_label}-s{rel_scale:.2f}"
        rel_reg = float(budget.get("path_reliability_context_reg_weight", 0.0) or 0.0)
        if rel_reg > 0.0:
            rel_label = f"{rel_label}-reg{rel_reg:.3f}"
        parts.append(rel_label)
    if bool(budget.get("use_learned_path_admission", config.get("use_learned_path_admission", False))):
        strength = float(budget.get("path_admission_strength", config.get("path_admission_strength", 1.0)) or 0.0)
        reg = float(budget.get("path_admission_reg_weight", 0.0) or 0.0)
        admission_label = f"learned-path-admit-s{strength:.2f}"
        if reg > 0.0:
            admission_label = f"{admission_label}-reg{reg:.3f}"
        parts.append(admission_label)
    if bool(budget.get("use_path_prior_consistency", config.get("use_path_prior_consistency", False))):
        strength = float(
            budget.get("path_prior_consistency_strength", config.get("path_prior_consistency_strength", 0.0)) or 0.0
        )
        threshold = float(
            budget.get("path_prior_consistency_threshold", config.get("path_prior_consistency_threshold", 0.25)) or 0.0
        )
        temperature = float(
            budget.get("path_prior_consistency_temperature", config.get("path_prior_consistency_temperature", 0.05)) or 0.0
        )
        mode = str(
            budget.get("path_prior_consistency_support_mode", config.get("path_prior_consistency_support_mode", "max"))
            or "max"
        )
        label = f"path-prior-cons-s{strength:.2f}-thr{threshold:.2f}-t{temperature:.2f}"
        if mode != "max":
            label = f"{label}-{mode}"
        if mode == "class_blend":
            class_floor = float(
                budget.get(
                    "path_prior_consistency_class_floor",
                    config.get("path_prior_consistency_class_floor", 0.25),
                )
                or 0.0
            )
            label = f"{label}-cf{class_floor:.2f}"
        parts.append(label)
    if bool(budget.get("use_path_evidence_consistency", config.get("use_path_evidence_consistency", False))):
        strength = float(
            budget.get("path_evidence_consistency_strength", config.get("path_evidence_consistency_strength", 0.0))
            or 0.0
        )
        threshold = float(
            budget.get("path_evidence_consistency_threshold", config.get("path_evidence_consistency_threshold", 0.35))
            or 0.0
        )
        temperature = float(
            budget.get("path_evidence_consistency_temperature", config.get("path_evidence_consistency_temperature", 0.05))
            or 0.0
        )
        floor = float(
            budget.get("path_evidence_consistency_floor", config.get("path_evidence_consistency_floor", 0.0))
            or 0.0
        )
        mode = str(
            budget.get(
                "path_evidence_consistency_support_mode",
                config.get("path_evidence_consistency_support_mode", "absolute"),
            )
            or "absolute"
        )
        label = f"path-evid-cons-s{strength:.2f}-thr{threshold:.2f}-t{temperature:.2f}"
        if mode != "absolute":
            label = f"{label}-{mode}"
        if floor > 0.0:
            label = f"{label}-f{floor:.2f}"
        parts.append(label)
    if bool(budget.get("use_path_proposal_consistency", config.get("use_path_proposal_consistency", False))):
        strength = float(
            budget.get("path_proposal_consistency_strength", config.get("path_proposal_consistency_strength", 0.0))
            or 0.0
        )
        threshold = float(
            budget.get("path_proposal_consistency_threshold", config.get("path_proposal_consistency_threshold", 0.35))
            or 0.0
        )
        temperature = float(
            budget.get("path_proposal_consistency_temperature", config.get("path_proposal_consistency_temperature", 0.05))
            or 0.0
        )
        floor = float(
            budget.get("path_proposal_consistency_floor", config.get("path_proposal_consistency_floor", 0.10))
            or 0.0
        )
        mode = str(
            budget.get(
                "path_proposal_consistency_support_mode",
                config.get("path_proposal_consistency_support_mode", "max"),
            )
            or "max"
        )
        label = f"path-proposal-cons-s{strength:.2f}-thr{threshold:.2f}-t{temperature:.2f}-f{floor:.2f}"
        if mode != "max":
            label = f"{label}-{mode}"
        protected_strength = float(
            budget.get(
                "path_proposal_consistency_protected_strength",
                config.get("path_proposal_consistency_protected_strength", 0.0),
            )
            or 0.0
        )
        if protected_strength > 0.0:
            label = f"{label}-pstr{protected_strength:.2f}"
        retention = float(
            budget.get("path_proposal_retention_fraction", config.get("path_proposal_retention_fraction", 0.0))
            or 0.0
        )
        if retention > 0.0:
            label = f"{label}-retain{retention:.2f}"
        parts.append(label)
    if bool(budget.get("use_edge_family_router", config.get("use_edge_family_router", False))):
        temp = float(budget.get("edge_family_router_temperature", config.get("edge_family_router_temperature", 1.0)) or 1.0)
        floor = float(budget.get("edge_family_router_floor", config.get("edge_family_router_floor", 0.05)) or 0.0)
        blend = float(budget.get("edge_family_router_blend", config.get("edge_family_router_blend", 1.0)) or 0.0)
        balance = float(budget.get("edge_family_router_balance_weight", 0.0) or 0.0)
        family_label = f"edge-family-router-t{temp:.2f}-f{floor:.2f}-b{blend:.2f}"
        if balance > 0.0:
            family_label = f"{family_label}-bal{balance:.3f}"
        parts.append(family_label)
    if bool(budget.get("use_stable_path_evidence", False)):
        stable_mode = str(budget.get("stable_path_evidence_mode", "static_lag") or "static_lag")
        splits = int(budget.get("stable_path_evidence_splits", 0) or 0)
        vote = float(budget.get("stable_path_evidence_min_vote_fraction", 0.0) or 0.0)
        strength = float(budget.get("stable_path_evidence_strength", 1.0) or 0.0)
        top_k = int(budget.get("stable_path_evidence_top_k", 0) or 0)
        edge_top_k = int(budget.get("stable_path_evidence_edge_top_k", 0) or 0)
        stable_label = f"stable-path-{stable_mode}-s{splits}-v{vote:.2f}-w{strength:.2f}"
        if stable_mode != "static":
            max_lag = int(budget.get("stable_path_evidence_max_lag", 0) or 0)
            lag_weight = float(budget.get("stable_path_evidence_lag_weight", 0.0) or 0.0)
            stable_label = f"{stable_label}-lag{max_lag}@{lag_weight:.2f}"
        path_mode = str(budget.get("stable_path_evidence_path_mode", "max") or "max")
        if path_mode != "max":
            stable_label = f"{stable_label}-path-{path_mode}"
        if top_k > 0:
            stable_label = f"{stable_label}-k{top_k}"
        if edge_top_k > 0:
            stable_label = f"{stable_label}-edge{edge_top_k}"
        class_mode = str(budget.get("stable_path_evidence_class_mode", "filter") or "filter")
        if class_mode != "off":
            class_floor = float(budget.get("stable_path_evidence_class_floor", 0.0) or 0.0)
            stable_label = f"{stable_label}-class-{class_mode}{class_floor:.2f}"
        parts.append(stable_label)
    if bool(budget.get("use_class_evidence_quality_certificate", False)):
        mode = str(budget.get("class_evidence_quality_mode", "focus_stability") or "focus_stability")
        floor = float(budget.get("class_evidence_quality_floor", 0.15) or 0.0)
        threshold = float(budget.get("class_evidence_quality_threshold", 0.75) or 0.0)
        temperature = float(budget.get("class_evidence_quality_temperature", 0.05) or 0.0)
        parts.append(f"class-evid-cert-{mode}-f{floor:.2f}-thr{threshold:.2f}-t{temperature:.2f}")
    if bool(budget.get("use_path_family_quality_certificate", False)):
        mode = str(budget.get("path_family_quality_mode", "focus_path_family") or "focus_path_family")
        floor = float(budget.get("path_family_quality_floor", 0.15) or 0.0)
        threshold = float(budget.get("path_family_quality_threshold", 0.25) or 0.0)
        temperature = float(budget.get("path_family_quality_temperature", 0.05) or 0.0)
        direct = float(budget.get("path_family_quality_direct_weight", 1.0) or 0.0)
        group = float(budget.get("path_family_quality_group_weight", 0.50) or 0.0)
        stability = float(budget.get("path_family_quality_stability_weight", 0.0) or 0.0)
        family_k = int(budget.get("path_family_quality_family_k", 0) or 0)
        family_weight = float(budget.get("path_family_quality_family_weight", 0.0) or 0.0)
        family_label = (
            f"path-family-cert-{mode}-f{floor:.2f}-thr{threshold:.2f}-t{temperature:.2f}"
            f"-d{direct:.2f}-g{group:.2f}"
        )
        if stability > 0.0:
            family_label = f"{family_label}-stab{stability:.2f}"
        if family_k > 0 and family_weight > 0.0:
            family_label = f"{family_label}-fam{family_k}@{family_weight:.2f}"
        if bool(budget.get("use_path_family_protected_proposal_weights", False)):
            family_label = f"{family_label}-pf-protect"
        parts.append(family_label)
    if bool(budget.get("use_stable_class_edge_overlay", False)):
        scale = float(budget.get("stable_class_edge_overlay_scale", 0.25) or 0.0)
        top_k = int(budget.get("stable_class_edge_overlay_top_k", 0) or 0)
        group_top_k = int(budget.get("stable_class_edge_overlay_group_top_k", 0) or 0)
        mode = str(budget.get("stable_class_edge_overlay_mode", "max") or "max")
        focus = float(budget.get("stable_class_edge_overlay_focus_weight", 1.25) or 0.0)
        nonfocus = float(budget.get("stable_class_edge_overlay_nonfocus_weight", 0.50) or 0.0)
        overlay_label = (
            f"stable-class-edge-overlay-{mode}-s{scale:.2f}-k{top_k}-g{group_top_k}"
            f"-fw{focus:.2f}-nw{nonfocus:.2f}"
        )
        parts.append(overlay_label)
    if bool(budget.get("use_certified_graph_prior_core", False)):
        top_k = int(budget.get("graph_prior_core_top_k", 0) or 0)
        group_top_k = int(budget.get("graph_prior_core_group_top_k", 0) or 0)
        floor = float(budget.get("graph_prior_core_floor", 0.05) or 0.0)
        threshold = float(budget.get("graph_prior_core_threshold", 0.35) or 0.0)
        temperature = float(budget.get("graph_prior_core_temperature", 0.05) or 0.0)
        direct = float(budget.get("graph_prior_core_direct_weight", 1.0) or 0.0)
        group = float(budget.get("graph_prior_core_group_weight", 0.40) or 0.0)
        stability = float(budget.get("graph_prior_core_stability_weight", 0.50) or 0.0)
        prior = float(budget.get("graph_prior_core_prior_weight", 0.20) or 0.0)
        core_label = (
            f"graph-core-cert-k{top_k}-g{group_top_k}-f{floor:.2f}-thr{threshold:.2f}-t{temperature:.2f}"
            f"-d{direct:.2f}-grp{group:.2f}-stab{stability:.2f}-p{prior:.2f}"
        )
        if bool(budget.get("use_separate_path_candidate_prior", False)):
            core_label = f"{core_label}-sep-path-candidate"
        parts.append(core_label)
    prior_coverage = float(budget.get("prior_coverage_fraction", config.get("prior_coverage_fraction", 0.0)) or 0.0)
    if prior_coverage > 0.0:
        parts.append(f"prior-cover@{prior_coverage:.2f}")
    candidate_coverage = float(
        budget.get("candidate_coverage_fraction", config.get("candidate_coverage_fraction", 0.0)) or 0.0
    )
    if candidate_coverage > 0.0:
        parts.append(f"candidate-cover@{candidate_coverage:.2f}")
    if bool(budget.get("calibrate_prior_edges", False)):
        min_support = float(budget.get("prior_calibration_min_support", 0.0) or 0.0)
        parts.append(f"prior-cal@{min_support:.2f}")
    if bool(budget.get("use_edge_calibrator", config.get("use_edge_calibrator", False))):
        floor = float(budget.get("edge_calibrator_floor", config.get("edge_calibrator_floor", 0.05)) or 0.0)
        init_bias = float(budget.get("edge_calibrator_init_bias", config.get("edge_calibrator_init_bias", 2.0)) or 0.0)
        reg_weight = float(budget.get("edge_calibrator_reg_weight", 0.0) or 0.0)
        edge_label = f"edge-cal-f{floor:.2f}-b{init_bias:.1f}"
        if reg_weight > 0.0:
            edge_label = f"{edge_label}-reg{reg_weight:.2f}"
        parts.append(edge_label)
    alg_mode = str(budget.get("algorithmic_edge_prior_mode", "none") or "none")
    external_candidate_only = bool(budget.get("external_edge_candidate_only", False))
    external_candidate_label = ""
    if external_candidate_only:
        expert_scale = float(budget.get("external_candidate_expert_scale", 1.0) or 0.0)
        llm_scale = float(budget.get("external_candidate_llm_scale", 0.70) or 0.0)
        floor = float(budget.get("external_family_calibration_floor", 0.15) or 0.0)
        min_support = float(budget.get("external_family_min_data_support", 0.0) or 0.0)
        external_candidate_label = f"ext-cand-e{expert_scale:.2f}-l{llm_scale:.2f}-f{floor:.2f}"
        families = budget.get("external_candidate_families") or []
        if isinstance(families, str):
            family_parts = [part.strip() for part in families.split(",") if part.strip()]
        elif isinstance(families, Sequence):
            family_parts = [str(part).strip() for part in families if str(part).strip()]
        else:
            family_parts = []
        family_label = ",".join(sorted(family_parts))
        if family_label and family_label != "expert,llm":
            external_candidate_label = f"{external_candidate_label}-fam{family_label}"
        if min_support > 0.0:
            external_candidate_label = f"{external_candidate_label}-ms{min_support:.2f}"
    if alg_mode != "none":
        alg_top_k = int(budget.get("algorithmic_edge_prior_top_k", 0) or 0)
        alg_group_top_k = int(budget.get("algorithmic_edge_prior_group_top_k", 0) or 0)
        alg_lag = int(budget.get("algorithmic_edge_prior_max_lag", 0) or 0)
        alg_strength = float(budget.get("algorithmic_edge_prior_strength", 0.0) or 0.0)
        alg_label = f"alg-prior-{alg_mode}"
        if alg_top_k > 0:
            alg_label = f"{alg_label}-k{alg_top_k}"
        if alg_group_top_k > 0:
            alg_label = f"{alg_label}-g{alg_group_top_k}"
        if alg_mode in {"lag", "hybrid", "multiview", "edge_bank", "bank", "edge_pool", "edge_canvas", "edge_universe", "edge_sieve", "edge_overlay", "edge_lattice", "edge_dual_lattice", "edge_guarded_lattice", "edge_cert_pool", "edge_cert_overlay", "certified_edge_pool"} and alg_lag > 0:
            alg_label = f"{alg_label}-lag{alg_lag}"
        if alg_mode in {"edge_bank", "bank", "edge_pool", "edge_canvas", "edge_universe", "edge_sieve", "edge_overlay", "edge_lattice", "edge_dual_lattice", "edge_guarded_lattice", "edge_cert_pool", "edge_cert_overlay", "certified_edge_pool"}:
            bank_min_votes = int(budget.get("algorithmic_edge_prior_bank_min_votes", 2) or 2)
            bank_single_view = float(budget.get("algorithmic_edge_prior_bank_single_view_scale", 0.55) or 0.0)
            bank_vote_boost = float(budget.get("algorithmic_edge_prior_bank_vote_boost", 0.15) or 0.0)
            alg_label = f"{alg_label}-vote{bank_min_votes}-sv{bank_single_view:.2f}-vb{bank_vote_boost:.2f}"
            bank_global_budget = float(budget.get("algorithmic_edge_prior_bank_global_budget_multiplier", 0.0) or 0.0)
            if bank_global_budget > 0.0:
                alg_label = f"{alg_label}-gb{bank_global_budget:.1f}"
            if alg_mode in {"edge_pool", "edge_canvas", "edge_universe", "edge_sieve", "edge_overlay", "edge_lattice", "edge_dual_lattice", "edge_guarded_lattice", "edge_cert_pool", "edge_cert_overlay", "certified_edge_pool"}:
                pool_multiplier = float(budget.get("algorithmic_edge_prior_pool_multiplier", 2.0) or 0.0)
                pool_rank_weight = float(budget.get("algorithmic_edge_prior_pool_rank_weight", 0.35) or 0.0)
                pool_min_score = float(budget.get("algorithmic_edge_prior_pool_min_score", 0.0) or 0.0)
                alg_label = f"{alg_label}-pool{pool_multiplier:.1f}-rank{pool_rank_weight:.2f}"
                if pool_min_score > 0.0:
                    alg_label = f"{alg_label}-min{pool_min_score:.2f}"
        if alg_strength > 0.0:
            alg_label = f"{alg_label}@{alg_strength:.2f}"
        combine_mode = str(budget.get("prior_algorithmic_combine_mode", "max") or "max")
        if combine_mode != "max":
            external_scale = float(budget.get("prior_external_isolated_scale", 1.0) or 0.0)
            overlap_boost = float(budget.get("prior_overlap_boost", 0.0) or 0.0)
            if combine_mode == "anchored_subgraph":
                nonanchor_scale = float(budget.get("prior_nonanchor_algorithmic_scale", 1.0) or 0.0)
                alg_label = f"{alg_label}+anchor-e{external_scale:.2f}-b{overlap_boost:.2f}-n{nonanchor_scale:.2f}"
            else:
                alg_label = f"{alg_label}+corrob-e{external_scale:.2f}-b{overlap_boost:.2f}"
        if external_candidate_label:
            alg_label = f"{alg_label}+{external_candidate_label}"
        parts.append(alg_label)
    elif external_candidate_label:
        parts.append(external_candidate_label)
    if bool(budget.get("use_llm_expert_condition_verifier", False)):
        weight = float(budget.get("llm_condition_verifier_weight", 0.50) or 0.0)
        min_support = float(budget.get("llm_condition_verifier_min_data_support", 0.05) or 0.0)
        floor = float(budget.get("llm_condition_verifier_floor", 0.10) or 0.0)
        target = str(budget.get("llm_condition_verifier_target", "candidate_gate") or "candidate_gate")
        parts.append(f"llm-expert-condition-verifier-{target}-w{weight:.2f}-ms{min_support:.2f}-f{floor:.2f}")
    if bool(budget.get("use_class_conditioned_evidence", config.get("use_class_conditioned_evidence", False))):
        top_k = int(budget.get("class_evidence_top_k", 0) or 0)
        class_mode = str(budget.get("class_evidence_mode", "static") or "static")
        class_label = "class-evidence" if class_mode == "static" else f"class-evidence-{class_mode}"
        if class_mode != "static":
            max_lag = int(budget.get("class_evidence_max_lag", 0) or 0)
            lag_weight = float(budget.get("class_evidence_lag_weight", 0.0) or 0.0)
            class_label = f"{class_label}-lag{max_lag}@{lag_weight:.2f}"
        family_k = int(budget.get("class_evidence_family_k", 0) or 0)
        family_weight = float(budget.get("class_evidence_family_weight", 0.0) or 0.0)
        if family_k > 0 and family_weight > 0.0:
            class_label = f"{class_label}-family{family_k}@{family_weight:.2f}"
        focus_mode = str(budget.get("class_evidence_focus_mode", "none") or "none")
        if focus_mode != "none":
            focus_k = int(budget.get("class_evidence_focus_k", 0) or 0)
            focus_weight = float(budget.get("class_evidence_focus_nonfocus_weight", 0.0) or 0.0)
            focus_classes = budget.get("class_evidence_focus_classes") or []
            if isinstance(focus_classes, list) and focus_classes:
                class_label = f"{class_label}-focus-{focus_mode}{len(focus_classes)}"
            elif focus_k > 0:
                class_label = f"{class_label}-focus-{focus_mode}{focus_k}"
            else:
                class_label = f"{class_label}-focus-{focus_mode}"
            if focus_weight > 0.0:
                class_label = f"{class_label}@{focus_weight:.2f}"
        gate_threshold = float(budget.get("class_evidence_gate_threshold", 0.0) or 0.0)
        if gate_threshold > 0.0:
            class_label = f"{class_label}-gate@{gate_threshold:.2f}"
        router_top_k = int(budget.get("class_evidence_router_top_k", 0) or 0)
        router_temp = float(budget.get("class_evidence_router_temperature", 1.0) or 1.0)
        if router_top_k > 0:
            class_label = f"{class_label}-router{router_top_k}"
        if abs(router_temp - 1.0) > 1.0e-9:
            class_label = f"{class_label}-temp{router_temp:.2f}"
        parts.append(f"{class_label}@{top_k}" if top_k > 0 else class_label)

    path_aux = float(efficiency.get("path_aux_weight", budget.get("path_aux_weight", 0.0)) or 0.0)
    if path_aux > 0.0:
        parts.append(f"path-aux@{path_aux:.2f}")
    coarse_aux = float(efficiency.get("coarse_aux_weight", budget.get("coarse_aux_weight", 0.0)) or 0.0)
    if coarse_aux > 0.0:
        parts.append(f"coarse@{coarse_aux:.2f}")
    router_aux = float(efficiency.get("evidence_router_aux_weight", budget.get("evidence_router_aux_weight", 0.0)) or 0.0)
    if router_aux > 0.0:
        parts.append(f"router@{router_aux:.2f}")
    health_aux = float(efficiency.get("health_aux_weight", budget.get("health_aux_weight", 0.0)) or 0.0)
    if health_aux > 0.0:
        parts.append(f"health@{health_aux:.2f}")
    if config and not bool(config.get("use_context_router", budget.get("use_context_router", True))):
        parts.append("ctx-off")

    return "+".join(parts) if parts else "default"


STAT_SUFFIXES = ("_last_minus_first", "_mean", "_std", "_min", "_max")


def _feature_group_name(feature: str) -> str:
    name = str(feature)
    for suffix in STAT_SUFFIXES:
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def _path_set(row: Mapping[str, Any], *, top_k: int = 10, group_level: bool = False) -> set[tuple[str, str]]:
    out: set[tuple[str, str]] = set()
    for item in list(row.get("top_evidence_paths") or [])[: int(top_k)]:
        source = str(item.get("source", ""))
        target = str(item.get("target", ""))
        if source and target:
            if group_level:
                source = _feature_group_name(source)
                target = _feature_group_name(target)
            out.add((source, target))
    return out


def _pairwise_jaccard(rows: Sequence[Mapping[str, Any]], *, top_k: int = 10, group_level: bool = False) -> float | None:
    if len(rows) < 2:
        return None
    sets = [_path_set(row, top_k=top_k, group_level=group_level) for row in rows]
    values: list[float] = []
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            union = sets[i] | sets[j]
            if not union:
                continue
            values.append(float(len(sets[i] & sets[j]) / len(union)))
    if not values:
        return None
    return float(mean(values))


def aggregate(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str, str], list[Mapping[str, Any]]] = {}
    for row in rows:
        prior_label = _run_prior_label(row)
        setting_label = _run_setting_label(row)
        key = (str(row.get("dataset")), str(row.get("target")), str(row.get("variant")), prior_label, setting_label)
        grouped.setdefault(key, []).append(row)
    out: list[dict[str, Any]] = []
    for (dataset, target, variant, prior_label, setting_label), items in sorted(grouped.items()):
        macro, macro_std = _mean_std([_metric(item, "macro_f1") for item in items])
        bal, bal_std = _mean_std([_metric(item, "balanced_accuracy") for item in items])
        speed, speed_std = _mean_std(
            [float((item.get("efficiency") or {}).get("test_inference_samples_per_second", 0.0)) for item in items]
        )
        prior_mass, prior_mass_std = _mean_std(
            [
                float((((item.get("diagnostics") or {}).get("test_diagnostics") or {}).get("mean_path_prior_weight")) or 0.0)
                for item in items
            ]
        )
        salience_mass, salience_mass_std = _mean_std(
            [
                float((((item.get("diagnostics") or {}).get("test_diagnostics") or {}).get("mean_path_salience_weight")) or 0.0)
                for item in items
            ]
        )
        context_importance, context_importance_std = _mean_std(
            [
                float((((item.get("diagnostics") or {}).get("test_diagnostics") or {}).get("mean_path_context_importance")) or 0.0)
                for item in items
            ]
        )
        duplicate_rate, duplicate_rate_std = _mean_std(
            [
                float((((item.get("diagnostics") or {}).get("test_diagnostics") or {}).get("mean_path_duplicate_rate")) or 0.0)
                for item in items
            ]
        )
        class_admission, class_admission_std = _mean_std(
            [
                float((((item.get("diagnostics") or {}).get("test_diagnostics") or {}).get("mean_class_evidence_admission")) or 0.0)
                for item in items
            ]
        )
        path_jaccard = _pairwise_jaccard(items, top_k=10)
        group_path_jaccard = _pairwise_jaccard(items, top_k=10, group_level=True)
        params = int((items[0].get("efficiency") or {}).get("parameters", 0))
        config = ((items[0].get("diagnostics") or {}).get("config") or {})
        path_aux_weight = float((items[0].get("efficiency") or {}).get("path_aux_weight", 0.0) or 0.0)
        coarse_aux_weight = float((items[0].get("efficiency") or {}).get("coarse_aux_weight", 0.0) or 0.0)
        evidence_router_aux_weight = float((items[0].get("efficiency") or {}).get("evidence_router_aux_weight", 0.0) or 0.0)
        health_aux_weight = float((items[0].get("efficiency") or {}).get("health_aux_weight", 0.0) or 0.0)
        prior_coverage_fraction = float(((items[0].get("path_budget") or {}).get("prior_coverage_fraction", config.get("prior_coverage_fraction", 0.0))) or 0.0)
        health_mae, health_mae_std = _mean_std(
            [
                float((item.get("efficiency") or {}).get("test_health_mae", 0.0) or 0.0)
                for item in items
            ]
        )
        rul_mae, rul_mae_std = _mean_std(
            [
                float(
                    ((item.get("primary_test_metrics") or {}).get("rul_mae"))
                    or ((item.get("efficiency") or {}).get("test_rul_mae"))
                    or 0.0
                )
                for item in items
            ]
        )
        rul_rmse, rul_rmse_std = _mean_std(
            [
                float(
                    ((item.get("primary_test_metrics") or {}).get("rul_rmse"))
                    or ((item.get("efficiency") or {}).get("test_rul_rmse"))
                    or 0.0
                )
                for item in items
            ]
        )
        rul_score, rul_score_std = _mean_std(
            [
                float(
                    ((item.get("primary_test_metrics") or {}).get("rul_score"))
                    or ((item.get("efficiency") or {}).get("test_rul_score"))
                    or 0.0
                )
                for item in items
            ]
        )
        out.append(
            {
                "dataset": dataset,
                "target": target,
                "variant": variant,
                "prior": prior_label,
                "setting": setting_label,
                "runs": int(len(items)),
                "macro_f1_mean": macro,
                "macro_f1_std": macro_std,
                "balanced_accuracy_mean": bal,
                "balanced_accuracy_std": bal_std,
                "inference_samples_per_second_mean": speed,
                "inference_samples_per_second_std": speed_std,
                "mean_path_prior_weight": prior_mass,
                "mean_path_prior_weight_std": prior_mass_std,
                "mean_path_salience_weight": salience_mass,
                "mean_path_salience_weight_std": salience_mass_std,
                "mean_path_context_importance": context_importance,
                "mean_path_context_importance_std": context_importance_std,
                "mean_path_duplicate_rate": duplicate_rate,
                "mean_path_duplicate_rate_std": duplicate_rate_std,
                "mean_class_evidence_admission": class_admission,
                "mean_class_evidence_admission_std": class_admission_std,
                "top10_path_jaccard": path_jaccard,
                "top10_group_path_jaccard": group_path_jaccard,
                "parameters": params,
                "path_aux_weight": path_aux_weight,
                "coarse_aux_weight": coarse_aux_weight,
                "evidence_router_aux_weight": evidence_router_aux_weight,
                "health_aux_weight": health_aux_weight,
                "prior_coverage_fraction": prior_coverage_fraction,
                "test_health_mae": health_mae,
                "test_health_mae_std": health_mae_std,
                "rul_mae_mean": rul_mae,
                "rul_mae_std": rul_mae_std,
                "rul_rmse_mean": rul_rmse,
                "rul_rmse_std": rul_rmse_std,
                "rul_score_mean": rul_score,
                "rul_score_std": rul_score_std,
                "use_context_router": bool(config.get("use_context_router", False)),
            }
        )
    return out


def render_markdown(summary: Sequence[Mapping[str, Any]], rows: Sequence[Mapping[str, Any]]) -> str:
    lines: list[str] = []
    lines.append("# MS-GSE + RPF Result Summary")
    lines.append("")
    lines.append("| Dataset | Target | Variant | Prior | Setting | Runs | Macro-F1 | Balanced Acc. | RUL RMSE | RUL MAE | RUL Score | Path Jaccard | Group Path Jaccard | Prior mass | Salience mass | Context imp. | Class adm. | Duplicate rate | Path aux | Coarse aux | Health aux | Health MAE | Context router | Inference/s | Params |")
    lines.append("|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|")
    for item in summary:
        lines.append(
            "| {dataset} | {target} | {variant} | {prior} | {setting} | {runs} | {macro:.4f} +/- {macro_std:.4f} | {bal:.4f} +/- {bal_std:.4f} | {rul_rmse:.4f} | {rul_mae:.4f} | {rul_score:.2f} | {jaccard} | {group_jaccard} | {prior_mass:.4f} | {salience_mass:.4f} | {context_imp:.4f} | {class_adm:.4f} | {duplicate_rate:.4f} | {path_aux:.2f} | {coarse_aux:.2f} | {health_aux:.2f} | {health_mae:.4f} | {context_router} | {speed:.1f} | {params} |".format(
                dataset=item["dataset"],
                target=item["target"],
                variant=item["variant"],
                prior=item["prior"],
                setting=item["setting"],
                runs=item["runs"],
                macro=item["macro_f1_mean"],
                macro_std=item["macro_f1_std"],
                bal=item["balanced_accuracy_mean"],
                bal_std=item["balanced_accuracy_std"],
                rul_rmse=item["rul_rmse_mean"],
                rul_mae=item["rul_mae_mean"],
                rul_score=item["rul_score_mean"],
                jaccard="n/a" if item["top10_path_jaccard"] is None else f"{float(item['top10_path_jaccard']):.4f}",
                group_jaccard="n/a"
                if item["top10_group_path_jaccard"] is None
                else f"{float(item['top10_group_path_jaccard']):.4f}",
                prior_mass=item["mean_path_prior_weight"],
                salience_mass=item["mean_path_salience_weight"],
                context_imp=item["mean_path_context_importance"],
                class_adm=item["mean_class_evidence_admission"],
                duplicate_rate=item["mean_path_duplicate_rate"],
                path_aux=item["path_aux_weight"],
                coarse_aux=item["coarse_aux_weight"],
                health_aux=item["health_aux_weight"],
                health_mae=item["test_health_mae"],
                context_router="on" if item["use_context_router"] else "off",
                speed=item["inference_samples_per_second_mean"],
                params=item["parameters"],
            )
        )
    lines.append("")
    lines.append("## Top Evidence Paths")
    lines.append("")
    for row in sorted(rows, key=lambda item: (str(item.get("dataset")), str(item.get("target")), str(item.get("variant")))):
        paths = list(row.get("top_evidence_paths") or [])[:5]
        if not paths:
            continue
        prior = row.get("evidence_prior") or {}
        strength = (((row.get("diagnostics") or {}).get("config") or {}).get("prior_strength"))
        prior_text = str(prior.get("mode", "none"))
        if strength is not None and prior.get("enabled"):
            prior_text = f"{prior_text}@{float(strength):.2f}"
        lines.append(
            f"### {row.get('dataset')} / {row.get('target')} / {row.get('variant')} / prior={prior_text} / seed={row.get('seed')}"
        )
        lines.append("")
        lines.append("| Path | Group path | Mean weight | Mean reliability | Mean edge weight | Mean prior weight | Mean salience weight | Mean hop count |")
        lines.append("|---|---|---:|---:|---:|---:|---:|---:|")
        for path in paths:
            source = str(path.get("source", ""))
            bridge = str(path.get("bridge", ""))
            target = str(path.get("target", ""))
            path_text = str(path.get("path", "")) or (
                f"{source} -> {bridge} -> {target}" if bridge else f"{source} -> {target}"
            )
            if path.get("group_path"):
                group_path = str(path.get("group_path"))
            elif bridge:
                group_path = f"{_feature_group_name(source)} -> {_feature_group_name(bridge)} -> {_feature_group_name(target)}"
            else:
                group_path = f"{_feature_group_name(source)} -> {_feature_group_name(target)}" if source and target else ""
            lines.append(
                "| {path} | {group_path} | {weight:.4f} | {rel:.4f} | {edge:.4f} | {prior:.4f} | {salience:.4f} | {hop:.1f} |".format(
                    path=path_text,
                    group_path=group_path,
                    weight=float(path.get("mean_weight", 0.0)),
                    rel=float(path.get("mean_reliability", 0.0)),
                    edge=float(path.get("mean_edge_weight", 0.0)),
                    prior=float(path.get("mean_prior_weight", 0.0)),
                    salience=float(path.get("mean_salience_weight", 0.0)),
                    hop=float(path.get("mean_hop_count", 1.0)),
                )
            )
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize MS-GSE + RPF experiment JSON files.")
    parser.add_argument("--result-dir", type=str, default=str(DEFAULT_RESULT_DIR))
    parser.add_argument("--dataset", type=str, default="")
    parser.add_argument("--target", type=str, default="")
    parser.add_argument("--variants", type=str, default="")
    parser.add_argument("--filename-contains", type=str, default="")
    parser.add_argument("--n-rows-total", type=int, default=None)
    parser.add_argument("--output", type=str, default="")
    args = parser.parse_args()
    rows = load_runs(
        Path(args.result_dir),
        dataset=str(args.dataset) or None,
        target=str(args.target) or None,
        variants=set(part.strip() for part in str(args.variants).split(",") if part.strip()) or None,
        filename_contains=str(args.filename_contains) or None,
        n_rows_total=args.n_rows_total,
    )
    summary = aggregate(rows)
    markdown = render_markdown(summary, rows)
    output = Path(args.output) if args.output else Path(args.result_dir) / "ms_gse_rpf_result_summary.md"
    os.makedirs(_fs_path(output.parent), exist_ok=True)
    with open(_fs_path(output), "w", encoding="utf-8") as fh:
        fh.write(markdown)
        fh.write("\n")
    print(markdown)


if __name__ == "__main__":
    main()
