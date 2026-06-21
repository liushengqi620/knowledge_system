from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aaai_exact_native_execution_plan import (
    build_exact_native_execution_plan,
    render_markdown,
    write_exact_native_execution_plan,
)


class AaaiExactNativeExecutionPlanTest(unittest.TestCase):
    def test_plan_prioritizes_skab_and_cmapss_without_claiming_sota(self) -> None:
        payload = build_exact_native_execution_plan()

        self.assertEqual("execution_plan_ready_not_sota_proof", payload["status"])
        self.assertEqual(["SKAB", "C-MAPSS"], payload["primary_next_datasets"])
        by_dataset = {row["dataset"]: row for row in payload["plans"]}
        self.assertEqual({"TEP", "SKAB", "Hydraulic", "C-MAPSS"}, set(by_dataset))
        self.assertIn("event-window", " ".join(by_dataset["SKAB"]["gate_flip_requirements"]))
        self.assertIn("RUL cap", " ".join(by_dataset["C-MAPSS"]["native_protocol_contract"]))
        self.assertIn("materialized_complete", " ".join(item["status"] for item in by_dataset["SKAB"]["required_new_or_tightened_assets"]))
        self.assertIn("skab_official_notebook_reproduction", " ".join(item["name"] for item in by_dataset["SKAB"]["required_new_or_tightened_assets"]))
        self.assertIn("materialized_seed_level", " ".join(item["status"] for item in by_dataset["C-MAPSS"]["required_new_or_tightened_assets"]))
        self.assertIn("native_preprocessing_complete", " ".join(item["status"] for item in by_dataset["C-MAPSS"]["required_new_or_tightened_assets"]))
        self.assertIn("cmapss_published_baseline_alignment", " ".join(item["name"] for item in by_dataset["C-MAPSS"]["required_new_or_tightened_assets"]))
        self.assertIn("cmapss_published_baseline_contract", " ".join(item["name"] for item in by_dataset["C-MAPSS"]["required_new_or_tightened_assets"]))
        self.assertIn("contract_complete_reproduction_pending", " ".join(item["status"] for item in by_dataset["C-MAPSS"]["required_new_or_tightened_assets"]))
        self.assertIn("cmapss_lstm_source_protocol_audit", " ".join(item["name"] for item in by_dataset["C-MAPSS"]["required_new_or_tightened_assets"]))
        self.assertIn("source_protocol_incomplete_local_config_extracted", " ".join(item["status"] for item in by_dataset["C-MAPSS"]["required_new_or_tightened_assets"]))
        self.assertIn("cmapss_open_protocol_candidate_audit", " ".join(item["name"] for item in by_dataset["C-MAPSS"]["required_new_or_tightened_assets"]))
        self.assertIn("open_candidates_identified_exact_profile_pending", " ".join(item["status"] for item in by_dataset["C-MAPSS"]["required_new_or_tightened_assets"]))
        self.assertIn("cmapss_mdfa_source_profile", " ".join(item["name"] for item in by_dataset["C-MAPSS"]["required_new_or_tightened_assets"]))
        self.assertIn("source_profile_count_reconciled_full_budget_pending", " ".join(item["status"] for item in by_dataset["C-MAPSS"]["required_new_or_tightened_assets"]))
        self.assertIn("cmapss_mdfa_source_matched_runner", " ".join(item["name"] for item in by_dataset["C-MAPSS"]["required_new_or_tightened_assets"]))
        self.assertIn("four_subset_three_seed_branch_archive_reproduction_pending", " ".join(item["status"] for item in by_dataset["C-MAPSS"]["required_new_or_tightened_assets"]))
        self.assertIn("cmapss_mdfa_runner_audit", " ".join(item["name"] for item in by_dataset["C-MAPSS"]["required_new_or_tightened_assets"]))
        self.assertIn("cmapss_mdfa_strategy_probe_audit", " ".join(item["name"] for item in by_dataset["C-MAPSS"]["required_new_or_tightened_assets"]))
        self.assertIn("full_branch_archive_reproduction_pending", " ".join(item["status"] for item in by_dataset["C-MAPSS"]["required_new_or_tightened_assets"]))
        self.assertIn("MDFA 2025 open full-text profile", " ".join(by_dataset["C-MAPSS"]["baseline_protocols_to_run"]))
        self.assertIn("condition-aware branch archives", " ".join(by_dataset["C-MAPSS"]["baseline_protocols_to_run"]))
        self.assertIn("run_cmapss_mdfa_source_matched.py", " ".join(by_dataset["C-MAPSS"]["first_commands"]))
        self.assertIn("cmapss_lstm_published_style_candidate", " ".join(item["name"] for item in by_dataset["C-MAPSS"]["required_new_or_tightened_assets"]))
        self.assertIn("not_exact_published_reproduction", " ".join(item["status"] for item in by_dataset["C-MAPSS"]["required_new_or_tightened_assets"]))
        self.assertIn("reproduction_and_budget_missing", " ".join(item["status"] for item in by_dataset["C-MAPSS"]["required_new_or_tightened_assets"]))
        self.assertIn("cmapss_rul_backbone_optimization_audit", " ".join(item["name"] for item in by_dataset["C-MAPSS"]["required_new_or_tightened_assets"]))
        self.assertIn("path_fusion_closed", " ".join(item["status"] for item in by_dataset["C-MAPSS"]["required_new_or_tightened_assets"]))
        self.assertIn("cmapss_pseudo_truncation_validation_audit", " ".join(item["name"] for item in by_dataset["C-MAPSS"]["required_new_or_tightened_assets"]))
        self.assertIn("score_tradeoff_disclosed", " ".join(item["status"] for item in by_dataset["C-MAPSS"]["required_new_or_tightened_assets"]))
        self.assertIn("official", payload["claim_rule"])
        self.assertIn("not evidence", payload["claim_rule"])

    def test_markdown_is_claim_safe_and_actionable(self) -> None:
        markdown = render_markdown(build_exact_native_execution_plan())

        self.assertIn("# AAAI Exact-Native Execution Plan", markdown)
        self.assertIn("SKAB official repository", markdown)
        self.assertIn("NASA C-MAPSS open data page", markdown)
        self.assertIn("NASA PCoE Turbofan Engine Degradation Simulation", markdown)
        self.assertIn("First commands", markdown)
        self.assertIn("Gate flip requirements", markdown)
        self.assertIn("pseudo-truncation validation", markdown)
        self.assertIn("published-baseline preprocessing equivalence", markdown)
        self.assertIn("cmapss_published_baseline_contract", markdown)
        self.assertIn("cmapss_lstm_source_protocol_audit", markdown)
        self.assertIn("cmapss_open_protocol_candidate_audit", markdown)
        self.assertIn("cmapss_mdfa_source_profile", markdown)
        self.assertIn("cmapss_mdfa_runner_audit", markdown)
        self.assertIn("cmapss_mdfa_strategy_probe_audit", markdown)
        self.assertIn("run_cmapss_mdfa_source_matched.py", markdown)
        self.assertIn("MDFA 2025", markdown)
        self.assertIn("ACB 2021", markdown)
        self.assertIn("count reconciliation", markdown)
        self.assertIn("execution_plan_ready_not_sota_proof", markdown)
        self.assertNotIn("official universal leaderboard superiority", markdown)
        self.assertNotIn("SOTA-candidate", markdown)

    def test_write_exact_native_execution_plan_outputs_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            written = write_exact_native_execution_plan(output_dir)

            self.assertEqual(
                {output_dir / "aaai_exact_native_execution_plan.json", output_dir / "aaai_exact_native_execution_plan.md"},
                set(written),
            )
            payload = json.loads((output_dir / "aaai_exact_native_execution_plan.json").read_text(encoding="utf-8"))
            markdown = (output_dir / "aaai_exact_native_execution_plan.md").read_text(encoding="utf-8")
            self.assertEqual("execution_plan_ready_not_sota_proof", payload["status"])
            self.assertIn("C-MAPSS", markdown)


if __name__ == "__main__":
    unittest.main()
