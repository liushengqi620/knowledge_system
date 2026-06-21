from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd


DATASET_TASKS: dict[str, dict[str, Any]] = {
    "tep": {
        "display_name": "Tennessee Eastman Process",
        "task": "22-class process fault diagnosis",
        "label_columns": ["event_quality_class_id", "fault_id"],
        "split_protocol": "official train/test files with train-only validation split",
        "temporal_unit": "source_file/run sample_index",
    },
    "skab": {
        "display_name": "Skoltech Anomaly Benchmark",
        "task": "binary point/run anomaly detection",
        "label_columns": ["anomaly", "changepoint"],
        "split_protocol": "run-held-out split, validation runs selected from training runs",
        "temporal_unit": "run_id sample_index",
    },
    "hydraulic": {
        "display_name": "Condition Monitoring of Hydraulic Systems",
        "task": "four component-state diagnosis targets",
        "label_columns": ["cooler", "valve", "internal_pump_leakage", "hydraulic_accumulator"],
        "split_protocol": "stratified cycle split per component target",
        "temporal_unit": "one cycle summarized from sensor time series",
    },
    "cmapss": {
        "display_name": "C-MAPSS turbofan degradation",
        "task": "degradation-stage classification from RUL thresholds",
        "label_columns": ["degradation_stage_id", "rul"],
        "split_protocol": "NASA train/test units with train-only validation split",
        "temporal_unit": "subset/unit/cycle",
    },
}


SKAB_EXPERT_EDGES: list[dict[str, Any]] = [
    {"source": "Current", "target": "Temperature", "lag": 2, "relation": "motor_load_heating", "reliability": 0.45},
    {"source": "Voltage", "target": "Current", "lag": 1, "relation": "drive_electrical_response", "reliability": 0.35},
    {"source": "Volume Flow RateRMS", "target": "Pressure", "lag": 1, "relation": "flow_pressure_coupling", "reliability": 0.45},
    {"source": "Pressure", "target": "Volume Flow RateRMS", "lag": 1, "relation": "hydraulic_feedback", "reliability": 0.35},
    {"source": "Accelerometer1RMS", "target": "Volume Flow RateRMS", "lag": 2, "relation": "mechanical_vibration_flow", "reliability": 0.30},
    {"source": "Temperature", "target": "Thermocouple", "lag": 1, "relation": "thermal_transfer", "reliability": 0.42},
]


HYDRAULIC_COMPONENT_EDGES: list[dict[str, Any]] = [
    {"source": "FS1_mean", "target": "PS1_mean", "lag": 0, "relation": "flow_pressure_response", "reliability": 0.52},
    {"source": "FS2_mean", "target": "PS2_mean", "lag": 0, "relation": "flow_pressure_response", "reliability": 0.52},
    {"source": "PS1_mean", "target": "VS1_mean", "lag": 0, "relation": "pressure_vibration_response", "reliability": 0.42},
    {"source": "PS2_mean", "target": "VS1_mean", "lag": 0, "relation": "pressure_vibration_response", "reliability": 0.42},
    {"source": "CP_mean", "target": "CE_mean", "lag": 0, "relation": "cooling_power_efficiency", "reliability": 0.55},
    {"source": "CE_mean", "target": "TS1_mean", "lag": 0, "relation": "cooler_temperature_response", "reliability": 0.50},
    {"source": "TS1_mean", "target": "TS4_mean", "lag": 0, "relation": "thermal_gradient", "reliability": 0.40},
    {"source": "SE_mean", "target": "EPS1_mean", "lag": 0, "relation": "system_efficiency_power", "reliability": 0.35},
]


CMAPSS_DEGRADATION_SENSORS = ["sensor_02", "sensor_03", "sensor_04", "sensor_07", "sensor_11", "sensor_12", "sensor_15", "sensor_20", "sensor_21"]


def _fs_path(path: Path) -> str:
    if os.name == "nt":
        resolved = str(Path(path).resolve())
        if not resolved.startswith("\\\\?\\"):
            return "\\\\?\\" + resolved
    return str(path)


def _write_json(path: Path, data: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(_fs_path(path), "w", encoding="utf-8") as fh:
        json.dump(dict(data), fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def _safe_id(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", str(text)).strip("_")[:80] or "feature"


def _is_numeric(series: pd.Series) -> bool:
    converted = pd.to_numeric(series, errors="coerce")
    return bool(converted.notna().any())


def _feature_subsystem(dataset: str, feature: str) -> str:
    name = str(feature)
    lower = name.lower()
    if name in {"record_id", "run_id", "run_group", "source_file"}:
        return "identity"
    if name in {"sample_index", "cycle", "unit", "subset_id"}:
        return "temporal_context"
    if dataset == "tep":
        try:
            from build_tep_knowledge_prior import VARIABLE_SEMANTICS

            return str(VARIABLE_SEMANTICS.get(name, {}).get("group", "tep_process_variable"))
        except Exception:
            return "tep_process_variable"
    if dataset == "skab":
        if "accelerometer" in lower or "rms" in lower and "flow" not in lower:
            return "mechanical_vibration"
        if "current" in lower or "voltage" in lower:
            return "electrical_drive"
        if "pressure" in lower or "flow" in lower:
            return "hydraulic_flow"
        if "temperature" in lower or "thermocouple" in lower:
            return "thermal"
        return "skab_sensor"
    if dataset == "hydraulic":
        prefix = name.split("_", 1)[0]
        return {
            "PS1": "pressure",
            "PS2": "pressure",
            "PS3": "pressure",
            "PS4": "pressure",
            "PS5": "pressure",
            "PS6": "pressure",
            "FS1": "flow",
            "FS2": "flow",
            "TS1": "thermal",
            "TS2": "thermal",
            "TS3": "thermal",
            "TS4": "thermal",
            "VS1": "vibration",
            "CE": "cooling_efficiency",
            "CP": "cooling_power",
            "SE": "system_efficiency",
            "EPS1": "motor_power",
        }.get(prefix, "hydraulic_sensor")
    if dataset == "cmapss":
        if lower.startswith("op_setting"):
            return "operating_condition"
        if lower.startswith("sensor"):
            return "engine_sensor"
        if lower == "cycle":
            return "lifecycle"
        return "cmapss_context"
    return "generic_feature"


def _feature_role(dataset: str, feature: str) -> str:
    name = str(feature)
    if name in {"record_id", "run_id", "run_group", "source_file", "unit", "subset", "subset_id"}:
        return "identifier_or_group"
    if name in {"sample_index", "cycle"}:
        return "time_index"
    if name.startswith("kg_"):
        return "mechanism_edge_feature"
    if dataset == "hydraulic" and any(name.endswith(f"_{stat}") for stat in ["mean", "std", "min", "max", "last_minus_first"]):
        return "cycle_summary_statistic"
    return "observed_process_variable"


def build_feature_catalog(dataset: str, x: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for col in x.columns:
        series = x[col]
        numeric = _is_numeric(series)
        converted = pd.to_numeric(series, errors="coerce") if numeric else pd.Series([], dtype=float)
        rows.append(
            {
                "feature_name": str(col),
                "role": _feature_role(dataset, str(col)),
                "subsystem": _feature_subsystem(dataset, str(col)),
                "is_numeric": bool(numeric),
                "missing_rate": float(converted.isna().mean()) if numeric and len(converted) else 0.0,
                "n_unique": int(series.nunique(dropna=True)),
            }
        )
    return pd.DataFrame(rows)


def _edge(
    edge_id: str,
    source: str,
    target: str,
    *,
    relation: str,
    lag: int,
    reliability: float,
    evidence_source: str,
    target_kind: str = "feature",
    rationale: str = "",
) -> dict[str, Any]:
    return {
        "edge_id": str(edge_id),
        "source": str(source),
        "target": str(target),
        "source_kind": "feature",
        "target_kind": str(target_kind),
        "relation": str(relation),
        "lag": int(lag),
        "reliability": float(np.clip(reliability, 0.0, 1.0)),
        "evidence_source": str(evidence_source),
        "admission_role": "candidate_mechanism_evidence",
        "rationale": str(rationale or relation),
    }


def _tep_edges(feature_cols: set[str]) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    try:
        from build_tep_knowledge_prior import expert_edges, llm_candidate_edges

        raw_edges = [("expert_prior", edge) for edge in expert_edges()] + [("llm_candidate", edge) for edge in llm_candidate_edges()]
    except Exception:
        raw_edges = []
    for idx, (source_name, row) in enumerate(raw_edges):
        src = str(row.get("from", row.get("source", "")))
        dst = str(row.get("to", row.get("target", "")))
        if src not in feature_cols or dst not in feature_cols:
            continue
        edges.append(
            _edge(
                f"tep_{idx:03d}_{_safe_id(src)}_{_safe_id(dst)}",
                src,
                dst,
                relation=str(row.get("relation_type", "process_mechanism")),
                lag=int(row.get("lag", 1)),
                reliability=float(row.get("confidence", row.get("weight", 0.5))),
                evidence_source=source_name,
                rationale=str(row.get("rationale_id", "")),
            )
        )
    return edges


def _skab_edges(feature_cols: set[str]) -> list[dict[str, Any]]:
    edges = []
    for idx, row in enumerate(SKAB_EXPERT_EDGES):
        src, dst = str(row["source"]), str(row["target"])
        if src in feature_cols and dst in feature_cols:
            edges.append(
                _edge(
                    f"skab_{idx:03d}_{_safe_id(src)}_{_safe_id(dst)}",
                    src,
                    dst,
                    relation=str(row["relation"]),
                    lag=int(row["lag"]),
                    reliability=float(row["reliability"]),
                    evidence_source="expert_lag_prior",
                )
            )
    return edges


def _hydraulic_edges(feature_cols: set[str]) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    for idx, row in enumerate(HYDRAULIC_COMPONENT_EDGES):
        src, dst = str(row["source"]), str(row["target"])
        if src in feature_cols and dst in feature_cols:
            edges.append(
                _edge(
                    f"hydraulic_{idx:03d}_{_safe_id(src)}_{_safe_id(dst)}",
                    src,
                    dst,
                    relation=str(row["relation"]),
                    lag=int(row["lag"]),
                    reliability=float(row["reliability"]),
                    evidence_source="component_physics_prior",
                )
            )
    label_targets = {
        "cooler": ["CE_mean", "CP_mean", "TS1_mean", "TS4_mean"],
        "valve": ["FS1_mean", "FS2_mean", "PS1_mean", "PS2_mean"],
        "internal_pump_leakage": ["PS1_mean", "PS2_mean", "VS1_mean", "SE_mean"],
        "hydraulic_accumulator": ["PS3_mean", "PS4_mean", "PS5_mean", "PS6_mean"],
    }
    for target, sources in label_targets.items():
        for src in sources:
            if src in feature_cols:
                edges.append(
                    _edge(
                        f"hydraulic_label_{_safe_id(src)}_{target}",
                        src,
                        target,
                        relation="component_state_indicator",
                        lag=0,
                        reliability=0.46,
                        evidence_source="component_target_prior",
                        target_kind="label",
                    )
                )
    return edges


def _cmapss_edges(feature_cols: set[str]) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    for sensor in CMAPSS_DEGRADATION_SENSORS:
        if sensor in feature_cols and "cycle" in feature_cols:
            edges.append(
                _edge(
                    f"cmapss_cycle_{sensor}",
                    "cycle",
                    sensor,
                    relation="lifecycle_degradation_trend",
                    lag=0,
                    reliability=0.38,
                    evidence_source="rul_lifecycle_prior",
                )
            )
        if sensor in feature_cols and "op_setting_1" in feature_cols:
            edges.append(
                _edge(
                    f"cmapss_op1_{sensor}",
                    "op_setting_1",
                    sensor,
                    relation="operating_condition_sensor_response",
                    lag=0,
                    reliability=0.28,
                    evidence_source="operating_condition_prior",
                )
            )
        if sensor in feature_cols:
            edges.append(
                _edge(
                    f"cmapss_label_{sensor}",
                    sensor,
                    "degradation_stage_id",
                    relation="degradation_stage_indicator",
                    lag=0,
                    reliability=0.34,
                    evidence_source="rul_threshold_prior",
                    target_kind="label",
                )
            )
    for idx, pair in enumerate([("sensor_02", "sensor_03"), ("sensor_07", "sensor_11"), ("sensor_12", "sensor_15"), ("sensor_20", "sensor_21")]):
        src, dst = pair
        if src in feature_cols and dst in feature_cols:
            edges.append(
                _edge(
                    f"cmapss_sensor_coupling_{idx}",
                    src,
                    dst,
                    relation="engine_sensor_coupling",
                    lag=0,
                    reliability=0.30,
                    evidence_source="engine_degradation_prior",
                )
            )
    return edges


def build_knowledge_graph(dataset: str, x: pd.DataFrame, y: pd.DataFrame | None = None) -> dict[str, Any]:
    name = str(dataset).lower()
    feature_cols = {str(c) for c in x.columns if str(c) != "record_id"}
    catalog = build_feature_catalog(name, x)
    if name == "tep":
        edges = _tep_edges(feature_cols)
    elif name == "skab":
        edges = _skab_edges(feature_cols)
    elif name == "hydraulic":
        edges = _hydraulic_edges(feature_cols)
    elif name == "cmapss":
        edges = _cmapss_edges(feature_cols)
    else:
        edges = []
    label_cols = [str(c) for c in (y.columns if y is not None else []) if c not in {"record_id"}]
    nodes = [
        {
            "node_id": str(row.feature_name),
            "node_kind": "feature",
            "role": str(row.role),
            "subsystem": str(row.subsystem),
        }
        for row in catalog.itertuples(index=False)
    ]
    nodes.extend({"node_id": col, "node_kind": "label", "role": "prediction_target", "subsystem": "target"} for col in label_cols)
    return {
        "schema": "public_benchmark_knowledge_graph_v1",
        "dataset": name,
        "task": DATASET_TASKS.get(name, {}).get("task", "unknown"),
        "nodes": nodes,
        "edges": edges,
        "admission_policy": {
            "min_reliability_for_direct_evidence": 0.30,
            "requires_validation_gain": True,
            "negative_transfer_guard": "selective_logit_correction_or_ERE_router",
            "claim_boundary": "candidate mechanism evidence, not true causal discovery",
        },
    }


def build_data_processing_manifest(dataset: str, x: pd.DataFrame, y: pd.DataFrame, summary: Mapping[str, Any] | None = None) -> dict[str, Any]:
    name = str(dataset).lower()
    catalog = build_feature_catalog(name, x)
    role_counts = catalog.groupby("role").size().to_dict() if not catalog.empty else {}
    subsystem_counts = catalog.groupby("subsystem").size().to_dict() if not catalog.empty else {}
    return {
        "schema": "public_benchmark_data_processing_v1",
        "dataset": name,
        "display_name": DATASET_TASKS.get(name, {}).get("display_name", name),
        "task": DATASET_TASKS.get(name, {}).get("task", ""),
        "source_summary": dict(summary or {}),
        "ready_files": ["X_process_features.csv", "y_labels.csv", "xy_public_benchmark.csv"],
        "label_columns": [col for col in DATASET_TASKS.get(name, {}).get("label_columns", []) if col in y.columns],
        "split_protocol": DATASET_TASKS.get(name, {}).get("split_protocol", "dataset-specific"),
        "temporal_unit": DATASET_TASKS.get(name, {}).get("temporal_unit", ""),
        "feature_blocks": {
            "role_counts": {str(k): int(v) for k, v in role_counts.items()},
            "subsystem_counts": {str(k): int(v) for k, v in subsystem_counts.items()},
        },
        "cleaning": {
            "numeric_casting": "coerce non-numeric values to NaN",
            "imputation": "median imputation inside the sklearn pipeline",
            "scaling": "standard scaling inside the sklearn pipeline",
            "leakage_guards": [
                "validation split is drawn from training-only units/runs/files where official test exists",
                "RUL labels are used only to form stage labels, not as input features",
                "residual center is fitted on train data only",
            ],
        },
    }


def build_model_architecture_spec(dataset: str, x: pd.DataFrame, y: pd.DataFrame, graph: Mapping[str, Any]) -> dict[str, Any]:
    name = str(dataset).lower()
    numeric_features = [c for c in x.columns if c != "record_id" and _is_numeric(x[c])]
    label_cols = [col for col in DATASET_TASKS.get(name, {}).get("label_columns", []) if col in y.columns]
    anchor_by_dataset = {
        "tep": {
            "name": "strict_mechanism_kiep_gl_tree_anchor",
            "purpose": "strong strict-protocol 22-class TEP discriminator; recovered evidence reports 0.9122 main/no-pairwise and 0.9549 with pairwise/support-gated mechanism evidence",
            "implementation_status": "recovered evidence and legacy runners; public_benchmark_experiment.py still keeps ExtraTrees as a smoke-test fallback",
            "candidate_replacements": ["TCN", "GRU", "FT-Transformer", "GDN-style", "MTAD-GAT-style"],
        },
        "skab": {
            "name": "run_level_anomaly_anchor_with_dynamic_graph_challengers",
            "purpose": "run-held-out anomaly baseline challenged by learned-reliability dynamic LLM/graph evidence",
            "implementation_status": "recovered evidence reports main 0.8343 and learned reliability route 0.8532; smoke fallback uses ExtraTrees",
            "candidate_replacements": ["MSFG-Time-TCN", "USAD-style", "TranAD-style", "GDN-style", "MTAD-GAT-style"],
        },
        "hydraulic": {
            "name": "strong_tabular_component_state_anchor",
            "purpose": "near-ceiling four-target component-state discriminator used to test non-degradation safety",
            "implementation_status": "recovered evidence reports SafeLearned/ERE-style routing; smoke fallback uses ExtraTrees",
            "candidate_replacements": ["LightGBM", "calibrated tree ensemble", "cycle-summary MLP"],
        },
        "cmapss": {
            "name": "lightgbm_lifecycle_anchor",
            "purpose": "LightGBM degradation-stage main head challenged by GRU multiscale normal-dynamics residual evidence",
            "implementation_status": "recovered evidence reports LightGBM + GRU multiscale residual + adaptive/fixed ERE on FD001-FD004",
            "candidate_replacements": ["GRU lifecycle head", "TCN lifecycle head", "Transformer lifecycle head"],
        },
    }
    sequence_candidate = {
        "tep": "TCN/GRU/FT-Transformer over causal run windows",
        "skab": "MSFG-TCN or temporal context windows over run_id/sample_index",
        "cmapss": "GRU/TCN over unit lifecycle windows",
        "hydraulic": "cycle-summary MLP or tabular residual head",
    }.get(name, "dataset-specific temporal head")
    return {
        "schema": "public_benchmark_model_architecture_v1",
        "dataset": name,
        "input": {
            "n_ready_columns": int(x.shape[1]),
            "n_numeric_features": int(len(numeric_features)),
            "target_columns": label_cols,
            "mechanism_edges": int(len(graph.get("edges", []))),
        },
        "anchor_model": {
            **anchor_by_dataset.get(
                name,
                {
                    "name": "strong_protocol_selected_discriminator",
                    "purpose": "dataset-specific main classifier used as p0",
                    "implementation_status": "ExtraTrees is available as a smoke-test fallback",
                    "candidate_replacements": ["LightGBM", "TCN", "GRU", "Transformer"],
                },
            ),
            "preprocess": ["median_imputer", "standard_scaler"],
            "smoke_test_fallback": "balanced_extra_trees_anchor",
        },
        "candidate_evidence_models": [
            {
                "name": "normal_residual_evidence_head",
                "family": "ExtraTrees on |scaled feature - normal center| plus missingness mask",
                "role": "detect deviations from normal process state",
                "fit_scope": "train split only",
            },
            {
                "name": "mechanism_edge_feature_head",
                "family": "knowledge graph edge deltas/ratios generated from admitted feature-feature edges",
                "role": "convert candidate mechanism graph into falsifiable features",
                "n_graph_edges": int(len([e for e in graph.get("edges", []) if e.get("target_kind") == "feature"])),
            },
            {
                "name": "temporal_sequence_candidate",
                "family": sequence_candidate,
                "role": "dataset-specific temporal evidence candidate",
            },
        ],
        "router": {
            "name": "UGMC_selective_logit_correction",
            "validation_objective": "macro-F1 plus positive/rare recall term",
            "gate_features": ["anchor_confidence", "candidate_agreement", "top-k membership"],
            "fallback": "anchor prediction when candidate evidence is unsafe",
        },
        "safety_checks": [
            "report main anchor and candidate-routed metrics separately",
            "retain class id mapping for non-contiguous public labels",
            "store graph admission policy next to every ready dataset",
        ],
    }


def build_candidate_evidence_registry(dataset: str, graph: Mapping[str, Any]) -> dict[str, Any]:
    name = str(dataset).lower()
    graph_edges = list(graph.get("edges", []))
    return {
        "schema": "public_benchmark_candidate_evidence_registry_v1",
        "dataset": name,
        "candidates": [
            {"candidate_id": "p0_anchor", "kind": "anchor", "requires_graph": False, "deployment_role": "fallback"},
            {"candidate_id": "normal_residual", "kind": "residual", "requires_graph": False, "deployment_role": "candidate"},
            {
                "candidate_id": "mechanism_graph_edges",
                "kind": "mechanism_prior",
                "requires_graph": True,
                "deployment_role": "candidate_with_validation_admission",
                "n_edges": int(len(graph_edges)),
            },
            {
                "candidate_id": "temporal_context",
                "kind": "sequence_or_lifecycle",
                "requires_graph": name in {"tep", "skab"},
                "deployment_role": "candidate",
            },
        ],
        "edge_sources": sorted({str(edge.get("evidence_source", "unknown")) for edge in graph_edges}),
    }


def _edge_feature_pairs(dataset: str, x: pd.DataFrame, edges: Sequence[Mapping[str, Any]] | None = None) -> list[dict[str, Any]]:
    graph_edges = list(edges) if edges is not None else build_knowledge_graph(dataset, x).get("edges", [])
    feature_cols = {str(c) for c in x.columns}
    pairs = []
    for edge in graph_edges:
        if str(edge.get("target_kind", "feature")) != "feature":
            continue
        src = str(edge.get("source", ""))
        dst = str(edge.get("target", ""))
        if src in feature_cols and dst in feature_cols and src != dst:
            pairs.append(dict(edge))
    return pairs


def build_mechanism_edge_features(
    dataset: str,
    x: pd.DataFrame,
    *,
    edges: Sequence[Mapping[str, Any]] | None = None,
    max_edges: int = 32,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    pairs = _edge_feature_pairs(dataset, x, edges)[: max(0, int(max_edges))]
    out = pd.DataFrame(index=x.index)
    for idx, edge in enumerate(pairs):
        src = str(edge["source"])
        dst = str(edge["target"])
        src_values = pd.to_numeric(x[src], errors="coerce")
        dst_values = pd.to_numeric(x[dst], errors="coerce")
        prefix = f"kg_{idx:02d}_{_safe_id(src)}_to_{_safe_id(dst)}"
        out[f"{prefix}_diff"] = dst_values - src_values
        out[f"{prefix}_absdiff"] = (dst_values - src_values).abs()
        denom = src_values.replace(0.0, np.nan)
        out[f"{prefix}_ratio"] = (dst_values / denom).replace([np.inf, -np.inf], np.nan)
    return out, {
        "dataset": str(dataset).lower(),
        "candidate_edges": int(len(pairs)),
        "generated_features": int(out.shape[1]),
        "max_edges": int(max_edges),
    }


def _summary_markdown(dataset: str, manifest: Mapping[str, Any], graph: Mapping[str, Any], architecture: Mapping[str, Any]) -> str:
    anchor = architecture.get("anchor_model", {})
    lines = [
        f"# {DATASET_TASKS.get(dataset, {}).get('display_name', dataset)} knowledge model",
        "",
        f"- task: {manifest.get('task', '')}",
        f"- split protocol: {manifest.get('split_protocol', '')}",
        f"- temporal unit: {manifest.get('temporal_unit', '')}",
        f"- knowledge nodes: {len(graph.get('nodes', []))}",
        f"- mechanism edges: {len(graph.get('edges', []))}",
        f"- numeric features: {architecture.get('input', {}).get('n_numeric_features', 0)}",
        f"- anchor model: {anchor.get('name', 'strong_protocol_selected_discriminator')}",
        "",
        "## Model stack",
        "",
        "1. Anchor classifier: protocol-selected strong discriminator. ExtraTrees is kept only as the unified smoke-test fallback.",
        "2. Residual evidence: train-only normal residual and missingness head.",
        "3. Mechanism evidence: admitted graph edges converted into edge-difference features.",
        "4. Router: validation-selected UGMC selective logit correction with anchor fallback.",
    ]
    return "\n".join(lines) + "\n"


def build_public_benchmark_knowledge_model(
    dataset: str,
    x: pd.DataFrame,
    y: pd.DataFrame,
    *,
    output_dir: Path,
    summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    name = str(dataset).lower()
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    catalog = build_feature_catalog(name, x)
    graph = build_knowledge_graph(name, x, y)
    manifest = build_data_processing_manifest(name, x, y, summary=summary)
    architecture = build_model_architecture_spec(name, x, y, graph)
    registry = build_candidate_evidence_registry(name, graph)
    edge_features, edge_feature_diag = build_mechanism_edge_features(name, x)

    catalog.to_csv(_fs_path(out / "feature_catalog.csv"), index=False, encoding="utf-8-sig")
    if not edge_features.empty:
        edge_features.to_csv(_fs_path(out / "mechanism_edge_features.csv"), index=False, encoding="utf-8-sig")
    _write_json(out / "knowledge_graph.json", graph)
    _write_json(out / "data_processing_manifest.json", manifest)
    _write_json(out / "model_architecture.json", architecture)
    _write_json(out / "candidate_evidence_registry.json", registry)
    _write_json(out / "mechanism_edge_feature_diagnostics.json", edge_feature_diag)
    with open(_fs_path(out / "knowledge_model_summary.md"), "w", encoding="utf-8") as fh:
        fh.write(_summary_markdown(name, manifest, graph, architecture))

    return {
        "dataset": name,
        "output_dir": str(out),
        "n_features": int(x.shape[1]),
        "n_labels": int(y.shape[1]),
        "n_edges": int(len(graph.get("edges", []))),
        "n_edge_features": int(edge_feature_diag["generated_features"]),
        "files": [
            "feature_catalog.csv",
            "knowledge_graph.json",
            "data_processing_manifest.json",
            "model_architecture.json",
            "candidate_evidence_registry.json",
            "mechanism_edge_feature_diagnostics.json",
            "knowledge_model_summary.md",
        ],
    }
