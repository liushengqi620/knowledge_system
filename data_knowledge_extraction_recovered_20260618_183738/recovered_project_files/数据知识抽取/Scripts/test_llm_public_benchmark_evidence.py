from __future__ import annotations

import json
import unittest

from llm_public_benchmark_evidence import (
    LLM_EVIDENCE_SOURCE,
    LLM_EXPERT_CONDITION_VERIFIER_SOURCE,
    LLM_EXPERT_CORRECTION_SOURCE,
    build_llm_expert_condition_verifier_messages,
    build_llm_expert_graph_correction_messages,
    build_llm_edge_messages,
    merge_llm_expert_condition_verifications_into_graph,
    merge_llm_expert_corrections_into_graph,
    merge_llm_edges_into_graph,
    parse_llm_expert_condition_verifier_response,
    parse_llm_expert_graph_correction_response,
    parse_llm_edge_response,
)


class LLMPublicBenchmarkEvidenceTest(unittest.TestCase):
    def test_parse_llm_edges_filters_and_caps_candidates(self) -> None:
        response = json.dumps(
            {
                "edges": [
                    {
                        "source": "FS1_mean",
                        "target": "PS1_mean",
                        "relation": "flow_pressure_response",
                        "lag": 1,
                        "reliability": 0.91,
                        "rationale": "Flow changes can precede pressure response.",
                    },
                    {
                        "source": "unknown_sensor",
                        "target": "PS1_mean",
                        "relation": "invalid",
                        "lag": 0,
                        "reliability": 0.4,
                    },
                    {
                        "source": "FS1_mean",
                        "target": "PS1_mean",
                        "relation": "duplicate",
                        "lag": 0,
                        "reliability": 0.4,
                    },
                    {
                        "source": "PS1_mean",
                        "target": "VS1_mean",
                        "relation": "pressure_vibration_response",
                        "lag": 9,
                        "reliability": 0.30,
                    },
                ]
            }
        )

        edges, diag = parse_llm_edge_response(
            response,
            dataset="hydraulic",
            feature_names=["FS1_mean", "PS1_mean", "VS1_mean"],
            max_edges=8,
        )

        self.assertEqual(len(edges), 2)
        self.assertEqual(diag["accepted_edges"], 2)
        self.assertEqual(edges[0]["evidence_source"], LLM_EVIDENCE_SOURCE)
        self.assertLessEqual(edges[0]["reliability"], 0.55)
        self.assertEqual(edges[1]["lag"], 5)

    def test_merge_llm_edges_replaces_previous_live_source(self) -> None:
        graph = {
            "schema": "public_benchmark_knowledge_graph_v1",
            "edges": [
                {"source": "A", "target": "B", "evidence_source": "expert_prior"},
                {"source": "old", "target": "edge", "evidence_source": LLM_EVIDENCE_SOURCE},
            ],
        }
        llm_edges = [{"source": "C", "target": "D", "evidence_source": LLM_EVIDENCE_SOURCE}]

        merged = merge_llm_edges_into_graph(graph, llm_edges)

        pairs = {(edge["source"], edge["target"], edge["evidence_source"]) for edge in merged["edges"]}
        self.assertIn(("A", "B", "expert_prior"), pairs)
        self.assertIn(("C", "D", LLM_EVIDENCE_SOURCE), pairs)
        self.assertNotIn(("old", "edge", LLM_EVIDENCE_SOURCE), pairs)
        self.assertEqual(merged["llm_candidate_metadata"][LLM_EVIDENCE_SOURCE]["n_edges"], 1)

    def test_prompt_does_not_include_secret_fields(self) -> None:
        messages = build_llm_edge_messages(
            dataset="skab",
            target="anomaly",
            feature_catalog=[{"name": "Current", "role": "observed", "subsystem": "electrical", "n_unique": 10}],
            existing_edges=[],
            max_edges=2,
        )
        joined = "\n".join(item["content"] for item in messages)

        self.assertIn("allowed_features", joined)
        self.assertNotIn("api_key", joined.lower())
        self.assertNotIn("authorization", joined.lower())

    def test_parse_expert_graph_corrections_keeps_downweight_metadata_only(self) -> None:
        response = json.dumps(
            {
                "corrections": [
                    {
                        "operation": "add",
                        "source": "FS1_mean",
                        "target": "PS1_mean",
                        "relation": "flow_pressure_delay",
                        "lag": 2,
                        "reliability": 0.9,
                        "rationale": "Flow changes can precede pressure.",
                    },
                    {
                        "operation": "downweight",
                        "corrects_edge_id": "e1",
                        "source": "PS1_mean",
                        "target": "VS1_mean",
                        "relation": "weak pressure vibration coupling",
                        "lag": 9,
                        "reliability": 0.4,
                    },
                    {
                        "operation": "revise",
                        "source": "unknown",
                        "target": "PS1_mean",
                        "relation": "invalid feature",
                    },
                ]
            }
        )

        corrections, diag = parse_llm_expert_graph_correction_response(
            response,
            dataset="hydraulic",
            feature_names=["FS1_mean", "PS1_mean", "VS1_mean"],
            expert_edges=[
                {
                    "edge_id": "e1",
                    "source": "PS1_mean",
                    "target": "VS1_mean",
                    "relation": "pressure_to_vibration",
                    "lag": 1,
                    "reliability": 0.8,
                }
            ],
            max_corrections=8,
        )

        self.assertEqual(len(corrections), 2)
        self.assertEqual(diag["accepted_edges"], 1)
        self.assertEqual(diag["metadata_only_corrections"], 1)
        self.assertEqual(corrections[0]["evidence_source"], LLM_EXPERT_CORRECTION_SOURCE)
        self.assertLessEqual(corrections[0]["reliability"], 0.45)
        self.assertEqual(corrections[1]["lag"], 5)
        self.assertFalse(corrections[1]["graph_edge_candidate"])

    def test_merge_expert_corrections_preserves_expert_edges(self) -> None:
        graph = {
            "schema": "public_benchmark_knowledge_graph_v1",
            "edges": [
                {"edge_id": "e1", "source": "A", "target": "B", "evidence_source": "expert_prior"},
                {"source": "old", "target": "edge", "evidence_source": LLM_EXPERT_CORRECTION_SOURCE},
            ],
        }
        corrections = [
            {
                "source": "C",
                "target": "D",
                "evidence_source": LLM_EXPERT_CORRECTION_SOURCE,
                "graph_edge_candidate": True,
            },
            {
                "source": "A",
                "target": "B",
                "evidence_source": LLM_EXPERT_CORRECTION_SOURCE,
                "graph_edge_candidate": False,
                "correction_operation": "downweight",
            },
        ]

        merged = merge_llm_expert_corrections_into_graph(graph, corrections)

        pairs = {(edge["source"], edge["target"], edge["evidence_source"]) for edge in merged["edges"]}
        self.assertIn(("A", "B", "expert_prior"), pairs)
        self.assertIn(("C", "D", LLM_EXPERT_CORRECTION_SOURCE), pairs)
        self.assertNotIn(("old", "edge", LLM_EXPERT_CORRECTION_SOURCE), pairs)
        metadata = merged["llm_expert_graph_correction_metadata"][LLM_EXPERT_CORRECTION_SOURCE]
        self.assertEqual(metadata["n_corrections"], 2)
        self.assertEqual(metadata["n_metadata_only_corrections"], 1)

    def test_expert_graph_correction_prompt_uses_existing_expert_graph(self) -> None:
        messages = build_llm_expert_graph_correction_messages(
            dataset="skab",
            target="anomaly",
            feature_catalog=[{"name": "Current", "role": "observed", "subsystem": "electrical", "n_unique": 10}],
            expert_edges=[{"edge_id": "e1", "source": "Current", "target": "Current", "relation": "self"}],
            max_corrections=2,
        )
        joined = "\n".join(item["content"] for item in messages)

        self.assertIn("current_expert_graph_edges", joined)
        self.assertIn("corrections", joined)
        self.assertNotIn("api_key", joined.lower())
        self.assertNotIn("authorization", joined.lower())

    def test_condition_verifier_prompt_forbids_new_edges(self) -> None:
        messages = build_llm_expert_condition_verifier_messages(
            dataset="skab",
            target="anomaly",
            feature_catalog=[
                {"name": "Current", "role": "observed", "subsystem": "electrical", "n_unique": 10},
                {"name": "Pressure", "role": "observed", "subsystem": "hydraulic", "n_unique": 10},
            ],
            expert_edges=[
                {
                    "edge_id": "expert_1",
                    "source": "Current",
                    "target": "Pressure",
                    "relation": "actuator_pressure_response",
                }
            ],
            max_verifications=2,
        )
        joined = "\n".join(item["content"] for item in messages)

        self.assertIn("current_expert_graph_edges", joined)
        self.assertIn("verifications", joined)
        self.assertIn("Do not add new source-target pairs", joined)
        self.assertNotIn("api_key", joined.lower())
        self.assertNotIn("authorization", joined.lower())

    def test_parse_condition_verifier_requires_existing_expert_edge(self) -> None:
        response = json.dumps(
            {
                "verifications": [
                    {
                        "expert_edge_id": "expert_1",
                        "source": "Current",
                        "target": "Pressure",
                        "activation": "activate",
                        "activation_score": 0.9,
                        "confidence": 0.9,
                        "class_scope": ["all"],
                        "regime_scope": ["steady"],
                        "residual_pattern": "target residual follows source spike",
                        "temporal_pattern": "short lag",
                    },
                    {
                        "expert_edge_id": "missing",
                        "source": "Current",
                        "target": "Temperature",
                        "activation": "activate",
                    },
                ]
            }
        )

        verifications, diag = parse_llm_expert_condition_verifier_response(
            response,
            dataset="skab",
            feature_names=["Current", "Pressure", "Temperature"],
            expert_edges=[
                {
                    "edge_id": "expert_1",
                    "source": "Current",
                    "target": "Pressure",
                    "relation": "actuator_pressure_response",
                    "lag": 1,
                }
            ],
            max_verifications=8,
        )

        self.assertEqual(len(verifications), 1)
        self.assertEqual(diag["accepted_verifications"], 1)
        self.assertEqual(diag["accepted_edges"], 0)
        self.assertEqual(verifications[0]["evidence_source"], LLM_EXPERT_CONDITION_VERIFIER_SOURCE)
        self.assertFalse(verifications[0]["graph_edge_candidate"])
        self.assertEqual(verifications[0]["expert_edge_id"], "expert_1")
        self.assertLessEqual(verifications[0]["confidence"], 0.70)
        self.assertEqual(verifications[0]["condition_activation"], "activate")

    def test_merge_condition_verifier_does_not_add_graph_edges(self) -> None:
        graph = {
            "schema": "public_benchmark_knowledge_graph_v1",
            "edges": [{"edge_id": "expert_1", "source": "A", "target": "B", "evidence_source": "expert_prior"}],
        }
        verifications = [
            {
                "source": "A",
                "target": "B",
                "evidence_source": LLM_EXPERT_CONDITION_VERIFIER_SOURCE,
                "graph_edge_candidate": False,
                "expert_edge_id": "expert_1",
            }
        ]

        merged = merge_llm_expert_condition_verifications_into_graph(graph, verifications)

        self.assertEqual(merged["edges"], graph["edges"])
        metadata = merged["llm_expert_condition_verifier_metadata"][LLM_EXPERT_CONDITION_VERIFIER_SOURCE]
        self.assertEqual(metadata["n_verifications"], 1)
        self.assertEqual(metadata["n_edge_candidates"], 0)


if __name__ == "__main__":
    unittest.main()
