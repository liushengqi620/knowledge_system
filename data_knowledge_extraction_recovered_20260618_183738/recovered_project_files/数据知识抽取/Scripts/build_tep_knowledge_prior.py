from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from build_tep_fault_dataset import DEFAULT_OUTPUT_DIR, FAULT_DESCRIPTIONS


VARIABLE_SEMANTICS: dict[str, dict[str, str]] = {
    "xmeas_01": {"name": "A feed flow", "group": "feed_flow"},
    "xmeas_02": {"name": "D feed flow", "group": "feed_flow"},
    "xmeas_03": {"name": "E feed flow", "group": "feed_flow"},
    "xmeas_04": {"name": "A and C feed flow", "group": "feed_flow"},
    "xmeas_05": {"name": "Recycle flow", "group": "recycle"},
    "xmeas_06": {"name": "Reactor feed rate", "group": "reactor_feed"},
    "xmeas_07": {"name": "Reactor pressure", "group": "reactor"},
    "xmeas_08": {"name": "Reactor level", "group": "reactor"},
    "xmeas_09": {"name": "Reactor temperature", "group": "reactor"},
    "xmeas_10": {"name": "Purge rate", "group": "purge"},
    "xmeas_11": {"name": "Separator temperature", "group": "separator"},
    "xmeas_12": {"name": "Separator level", "group": "separator"},
    "xmeas_13": {"name": "Separator pressure", "group": "separator"},
    "xmeas_14": {"name": "Separator underflow", "group": "separator"},
    "xmeas_15": {"name": "Stripper level", "group": "stripper"},
    "xmeas_16": {"name": "Stripper pressure", "group": "stripper"},
    "xmeas_17": {"name": "Stripper underflow", "group": "stripper"},
    "xmeas_18": {"name": "Stripper temperature", "group": "stripper"},
    "xmeas_19": {"name": "Stripper steam flow", "group": "stripper"},
    "xmeas_20": {"name": "Compressor work", "group": "compressor"},
    "xmeas_21": {"name": "Reactor cooling water outlet temperature", "group": "cooling"},
    "xmeas_22": {"name": "Condenser cooling water outlet temperature", "group": "cooling"},
    **{f"xmeas_{i:02d}": {"name": f"Measured composition variable {i}", "group": "composition"} for i in range(23, 42)},
    "xmv_01": {"name": "D feed flow valve", "group": "manipulated_feed"},
    "xmv_02": {"name": "E feed flow valve", "group": "manipulated_feed"},
    "xmv_03": {"name": "A feed flow valve", "group": "manipulated_feed"},
    "xmv_04": {"name": "A and C feed flow valve", "group": "manipulated_feed"},
    "xmv_05": {"name": "Compressor recycle valve", "group": "manipulated_recycle"},
    "xmv_06": {"name": "Purge valve", "group": "manipulated_purge"},
    "xmv_07": {"name": "Separator pot liquid flow valve", "group": "manipulated_separator"},
    "xmv_08": {"name": "Stripper liquid product flow valve", "group": "manipulated_stripper"},
    "xmv_09": {"name": "Stripper steam valve", "group": "manipulated_stripper"},
    "xmv_10": {"name": "Reactor cooling water flow valve", "group": "manipulated_cooling"},
    "xmv_11": {"name": "Condenser cooling water flow valve", "group": "manipulated_cooling"},
}


def _edge(
    source: str,
    target: str,
    *,
    relation_type: str,
    fault_id: int | None = None,
    weight: float = 0.72,
    confidence: float = 0.82,
    lag: int = 1,
    causal_strength: float = 0.78,
    stability: float = 0.82,
    source_name: str = "tep_expert",
    rationale: str | None = None,
    llm: bool = False,
) -> dict[str, Any]:
    class_name = "global" if fault_id is None else FAULT_DESCRIPTIONS[int(fault_id)]
    evidence = {
        "knowledge_prior": float(confidence),
        "expert_mechanism": float(confidence),
        "llm_candidate": float(confidence if llm else 0.0),
    }
    return {
        "from": source,
        "to": target,
        "weight": float(weight),
        "confidence": float(confidence),
        "source": "llm_tep_candidate" if llm else source_name,
        "rationale_id": rationale or ("tep_global" if fault_id is None else f"tep_fault_{int(fault_id):02d}_{source}_to_{target}"),
        "relation_type": relation_type,
        "lag": int(lag),
        "causal_strength": float(causal_strength),
        "stability": float(stability),
        "is_control_loop": relation_type in {"control_loop", "control_feedback", "cooling_loop"},
        "is_feedback": relation_type == "control_feedback",
        "legal": True,
        "evidence": evidence,
        "dominant_source": "llm_candidate" if llm else "knowledge_prior",
        "regime_context": class_name,
    }


def expert_edges() -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    edges += [
        _edge("xmv_03", "xmeas_01", relation_type="control_loop"),
        _edge("xmv_01", "xmeas_02", relation_type="control_loop"),
        _edge("xmv_02", "xmeas_03", relation_type="control_loop"),
        _edge("xmv_04", "xmeas_04", relation_type="control_loop"),
        _edge("xmeas_01", "xmeas_06", relation_type="feed_propagation"),
        _edge("xmeas_02", "xmeas_06", relation_type="feed_propagation"),
        _edge("xmeas_03", "xmeas_06", relation_type="feed_propagation"),
        _edge("xmeas_04", "xmeas_06", relation_type="feed_propagation"),
        _edge("xmeas_06", "xmeas_07", relation_type="reactor_inventory"),
        _edge("xmeas_06", "xmeas_08", relation_type="reactor_inventory"),
        _edge("xmeas_06", "xmeas_09", relation_type="reactor_dynamics"),
        _edge("xmeas_09", "xmeas_21", relation_type="cooling_loop"),
        _edge("xmv_10", "xmeas_21", relation_type="cooling_loop"),
        _edge("xmeas_21", "xmeas_09", relation_type="cooling_feedback"),
        _edge("xmeas_07", "xmeas_11", relation_type="process_propagation"),
        _edge("xmeas_08", "xmeas_12", relation_type="inventory_balance"),
        _edge("xmeas_09", "xmeas_11", relation_type="thermal_propagation"),
        _edge("xmeas_11", "xmeas_13", relation_type="separator_dynamics"),
        _edge("xmeas_12", "xmeas_14", relation_type="inventory_balance"),
        _edge("xmv_11", "xmeas_22", relation_type="cooling_loop"),
        _edge("xmeas_22", "xmeas_11", relation_type="cooling_feedback"),
        _edge("xmeas_14", "xmeas_15", relation_type="inventory_balance"),
        _edge("xmeas_15", "xmeas_17", relation_type="stripper_dynamics"),
        _edge("xmv_09", "xmeas_19", relation_type="control_loop"),
        _edge("xmeas_19", "xmeas_18", relation_type="thermal_propagation"),
        _edge("xmeas_18", "xmeas_35", relation_type="composition_effect"),
        _edge("xmeas_18", "xmeas_36", relation_type="composition_effect"),
        _edge("xmeas_18", "xmeas_37", relation_type="composition_effect"),
        _edge("xmeas_18", "xmeas_38", relation_type="composition_effect"),
        _edge("xmeas_18", "xmeas_39", relation_type="composition_effect"),
    ]

    fault_templates: dict[int, list[tuple[str, str, str]]] = {
        1: [("xmeas_04", "xmeas_06", "feed_ratio"), ("xmeas_06", "xmeas_35", "composition_effect")],
        2: [("xmeas_04", "xmeas_06", "feed_composition"), ("xmeas_06", "xmeas_36", "composition_effect")],
        3: [("xmeas_02", "xmeas_09", "thermal_feed"), ("xmeas_09", "xmeas_11", "thermal_propagation")],
        4: [("xmv_10", "xmeas_21", "cooling_loop"), ("xmeas_21", "xmeas_09", "cooling_feedback")],
        5: [("xmv_11", "xmeas_22", "cooling_loop"), ("xmeas_22", "xmeas_11", "cooling_feedback")],
        6: [("xmv_03", "xmeas_01", "feed_loss"), ("xmeas_01", "xmeas_06", "feed_propagation")],
        7: [("xmeas_04", "xmeas_06", "feed_pressure_loss"), ("xmeas_06", "xmeas_07", "reactor_inventory")],
        8: [("xmeas_23", "xmeas_06", "feed_composition"), ("xmeas_06", "xmeas_37", "composition_effect")],
        9: [("xmeas_02", "xmeas_09", "thermal_feed"), ("xmeas_09", "xmeas_38", "composition_effect")],
        10: [("xmeas_04", "xmeas_09", "feed_temperature"), ("xmeas_09", "xmeas_11", "thermal_propagation")],
        11: [("xmv_10", "xmeas_21", "cooling_loop"), ("xmeas_21", "xmeas_09", "cooling_feedback")],
        12: [("xmv_11", "xmeas_22", "cooling_loop"), ("xmeas_22", "xmeas_13", "cooling_feedback")],
        13: [("xmeas_09", "xmeas_35", "reaction_kinetics"), ("xmeas_09", "xmeas_36", "reaction_kinetics")],
        14: [("xmv_10", "xmeas_09", "reactor_cooling_valve"), ("xmeas_09", "xmeas_07", "reactor_dynamics")],
        15: [("xmv_11", "xmeas_11", "condenser_cooling_valve"), ("xmeas_11", "xmeas_13", "separator_dynamics")],
        16: [("xmeas_07", "xmeas_20", "unknown_process_disturbance"), ("xmeas_20", "xmeas_13", "compressor_separator_coupling")],
        17: [("xmeas_05", "xmeas_20", "unknown_recycle_disturbance"), ("xmeas_20", "xmeas_06", "recycle_feed_coupling")],
        18: [("xmeas_09", "xmeas_18", "unknown_thermal_disturbance"), ("xmeas_18", "xmeas_39", "composition_effect")],
        19: [("xmeas_12", "xmeas_15", "unknown_inventory_disturbance"), ("xmeas_15", "xmeas_17", "inventory_balance")],
        20: [("xmeas_10", "xmeas_13", "unknown_purge_pressure_disturbance"), ("xmeas_13", "xmeas_20", "pressure_compressor_coupling")],
        21: [("xmv_04", "xmeas_04", "stream_4_valve_fixed"), ("xmeas_04", "xmeas_06", "feed_propagation")],
    }
    for fault_id, rows in fault_templates.items():
        for src, dst, rel in rows:
            edges.append(
                _edge(
                    src,
                    dst,
                    relation_type=rel,
                    fault_id=fault_id,
                    weight=0.86,
                    confidence=0.92,
                    lag=1 if "control" in rel or "valve" in rel else 2,
                    causal_strength=0.90,
                    stability=0.88,
                )
            )
    return edges


def llm_candidate_edges() -> list[dict[str, Any]]:
    candidates = []
    for fault_id, pairs in {
        4: [("xmv_10", "xmeas_09", "cooling_loop"), ("xmeas_21", "xmeas_07", "cooling_pressure_coupling")],
        5: [("xmv_11", "xmeas_13", "cooling_pressure_coupling")],
        13: [("xmeas_07", "xmeas_35", "reaction_kinetics"), ("xmeas_09", "xmeas_40", "composition_effect")],
        16: [("xmeas_20", "xmeas_07", "compressor_reactor_coupling")],
        21: [("xmv_04", "xmeas_35", "stream_4_composition_effect")],
    }.items():
        for src, dst, rel in pairs:
            candidates.append(
                _edge(
                    src,
                    dst,
                    relation_type=rel,
                    fault_id=fault_id,
                    weight=0.55,
                    confidence=0.62,
                    lag=2,
                    causal_strength=0.60,
                    stability=0.55,
                    llm=True,
                    rationale=f"llm_tep_fault_{fault_id:02d}_{src}_to_{dst}",
                )
            )
    return candidates


def build_tep_knowledge_prior(output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    expert = {"schema": "graph_edges_v1", "edges": expert_edges()}
    candidates = {"schema": "llm_boundary_candidates_v1", "edges": llm_candidate_edges()}
    semantics = {"schema": "tep_variable_semantics_v1", "variables": VARIABLE_SEMANTICS}
    (output_dir / "tep_expert_graph_prior.json").write_text(json.dumps(expert, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "tep_llm_boundary_candidates.json").write_text(json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "tep_variable_semantics.json").write_text(json.dumps(semantics, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "output_dir": str(output_dir),
        "expert_edges": len(expert["edges"]),
        "llm_candidate_edges": len(candidates["edges"]),
        "variables": len(VARIABLE_SEMANTICS),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build TEP expert mechanism graph prior resources.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()
    print(json.dumps(build_tep_knowledge_prior(Path(args.output_dir)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
