from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aaai_edge_admission_protocol_audit import (
    audit_hierarchical_contract,
    audit_measured_tep_probe,
    build_protocol_audit,
    render_markdown,
)


def _hierarchical_payload() -> dict:
    return {
        "gate_order": ["validation_gain", "low_tail_far_mar_safety", "cf_guard"],
        "candidate_edges": [
            {"edge_id": "e_expert", "source_family": "expert"},
            {"edge_id": "e_llm", "source_family": "llm"},
        ],
        "probe_results": [
            {"probe_level": "source_family"},
            {"probe_level": "target_group"},
            {"probe_level": "lag_group"},
            {"probe_level": "single_edge"},
        ],
        "relation_interface_options": [
            "edge_mask",
            "attention_bias",
            "channel_fusion_gate",
            "patch_or_frequency_relation_mask",
        ],
        "llm_role": "LLM outputs are mechanism candidates only; they are not causal discoveries.",
    }


def _tep_probe_payload(*, seeds: list[int]) -> dict:
    return {
        "status": "ok",
        "protocol": "hierarchical_validation_gain_then_safety_then_cf",
        "seeds": seeds,
        "max_rows": 1200 if len(seeds) == 1 else None,
        "probe_levels": ["source_family", "target_group", "lag_group", "single_edge"],
        "admission": {
            "gate_order": ["validation_gain", "low_tail_far_mar_safety", "cf_guard"],
            "validation_admitted_edges": [{"edge_id": "good_edge"}],
            "probe_results": [
                {
                    "probe_level": "single_edge",
                    "probe_key": "good_edge",
                    "admitted": True,
                    "cf_evaluated": True,
                    "stage_reached": "cf_guard",
                    "reject_reasons": [],
                },
                {
                    "probe_level": "single_edge",
                    "probe_key": "bad_edge",
                    "admitted": False,
                    "cf_evaluated": False,
                    "stage_reached": "validation_gain",
                    "reject_reasons": ["validation_gain_not_positive"],
                },
            ],
        },
    }


def _llm_matrix_payload() -> dict:
    names = [
        "a0_algorithmic_only",
        "a1_expert_candidate_gate",
        "a2_independent_llm_candidate",
        "a3_llm_expert_graph_correction",
        "a4_llm_expert_condition_verifier",
        "a5_weak_class_condition_verifier",
    ]
    return {
        "seeds": [42],
        "variants": [{"name": name} for name in names],
        "commands": {
            "a2_independent_llm_candidate": [
                "python",
                "--external-edge-candidate-only",
                "--external-candidate-families",
                "llm",
            ],
            "a4_llm_expert_condition_verifier": [
                "python",
                "--use-llm-expert-condition-verifier",
                "--llm-condition-verifier-target",
                "candidate_gate",
            ],
        },
        "summary": [{"variant": name, "n_runs": 0} for name in names],
    }


def _mechanism_matrix_payload() -> dict:
    names = [
        "no_mechanism",
        "raw_expert_graph",
        "expert_candidate_data_gate",
        "algorithmic_candidate_gate_control",
    ]
    return {
        "seeds": [42, 43, 44],
        "variants": [{"name": name} for name in names],
        "summary": [{"variant": name, "n_runs": 3} for name in names],
    }


class AaaiEdgeAdmissionProtocolAuditTest(unittest.TestCase):
    def test_hierarchical_contract_requires_ordered_gates_and_noncausal_llm_role(self) -> None:
        result = audit_hierarchical_contract(_hierarchical_payload())

        self.assertEqual(result["status"], "satisfied")
        self.assertIn("validation_gain", result["evidence"])
        self.assertIn("attention_bias", result["evidence"])

    def test_measured_tep_probe_marks_smoke_as_partial_not_final(self) -> None:
        result = audit_measured_tep_probe(_tep_probe_payload(seeds=[42]))

        self.assertEqual(result["status"], "partial")
        self.assertIn("pre_cf_rejections=1", result["evidence"])
        self.assertIn("full three-seed", result["next_action"])

    def test_build_protocol_audit_separates_complete_contract_from_partial_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = {
                "hierarchical_contract": root / "hierarchical.json",
                "tep_probe": root / "tep_probe.json",
                "llm_matrix": root / "llm_matrix.json",
                "mechanism_matrix": root / "mechanism_matrix.json",
            }
            paths["hierarchical_contract"].write_text(json.dumps(_hierarchical_payload()), encoding="utf-8")
            paths["tep_probe"].write_text(json.dumps(_tep_probe_payload(seeds=[42])), encoding="utf-8")
            paths["llm_matrix"].write_text(json.dumps(_llm_matrix_payload()), encoding="utf-8")
            paths["mechanism_matrix"].write_text(json.dumps(_mechanism_matrix_payload()), encoding="utf-8")

            report = build_protocol_audit(**paths)
            markdown = render_markdown(report)

        self.assertEqual(report["overall_status"], "protocol_contract_complete_evidence_partial")
        self.assertIn("LLM verifier", markdown)
        self.assertIn("measured evidence, including negative evidence", markdown)


if __name__ == "__main__":
    unittest.main()
