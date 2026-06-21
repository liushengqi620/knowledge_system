from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cmapss_open_protocol_candidate_audit import (
    build_cmapss_open_protocol_candidate_audit,
    render_markdown,
    write_cmapss_open_protocol_candidate_audit,
)


class CmapssOpenProtocolCandidateAuditTest(unittest.TestCase):
    def test_audit_identifies_open_candidates_but_keeps_exact_gate_closed(self) -> None:
        payload = build_cmapss_open_protocol_candidate_audit()

        self.assertEqual("open_candidates_identified_exact_profile_pending", payload["status"])
        self.assertTrue(payload["gates"]["open_candidate_audit_present"])
        self.assertTrue(payload["gates"]["accessible_all_subset_candidate_present"])
        self.assertTrue(payload["gates"]["accessible_training_budget_candidate_present"])
        self.assertTrue(payload["gates"]["mdfa_count_profile_reconciled"])
        self.assertFalse(payload["gates"]["exact_source_profile_ready"])
        self.assertFalse(payload["gates"]["safe_to_flip_published_baseline_gate"])
        self.assertIn("exact_source_profile_ready", payload["missing_gates"])
        self.assertIn("safe_to_flip_published_baseline_gate", payload["missing_gates"])
        self.assertEqual("mdfa_2025", payload["recommended_next_target"]["primary"])
        self.assertEqual("acb_2021", payload["recommended_next_target"]["fallback"])

        rows = {row["id"]: row for row in payload["candidate_sources"]}
        self.assertEqual(["FD001", "FD002", "FD003", "FD004"], rows["mdfa_2025"]["subset_scope"])
        self.assertIn("batch_size", rows["mdfa_2025"]["extractable_fields"])
        self.assertIn("learning_rate", rows["mdfa_2025"]["extractable_fields"])
        self.assertIn("raw-file unique-unit counts match", " ".join(rows["mdfa_2025"]["blocking_fields"]))
        self.assertIn("optimizer", " ".join(rows["acb_2021"]["blocking_fields"]).lower())
        self.assertIn("mdfa_2025", payload["training_budget_candidates"])
        self.assertIn("cmapss_mdfa_source_profile", " ".join(payload["next_actions"]))
        self.assertIn("source-matched MDFA runner", " ".join(payload["next_actions"]))

    def test_writer_and_markdown_are_claim_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            written = write_cmapss_open_protocol_candidate_audit(output_dir)
            self.assertEqual(
                {
                    output_dir / "cmapss_open_protocol_candidate_audit.json",
                    output_dir / "cmapss_open_protocol_candidate_audit.md",
                },
                set(written),
            )
            payload = json.loads((output_dir / "cmapss_open_protocol_candidate_audit.json").read_text(encoding="utf-8"))
            markdown = render_markdown(payload)

            self.assertIn("C-MAPSS Open Protocol Candidate Audit", markdown)
            self.assertIn("mdfa_2025", markdown)
            self.assertIn("acb_2021", markdown)
            self.assertIn("exact_source_profile_ready", markdown)
            self.assertIn("safe_to_flip_published_baseline_gate", markdown)
            self.assertIn("open_candidates_identified_exact_profile_pending", markdown)
            self.assertNotIn("official C-MAPSS SOTA is proven", markdown)


if __name__ == "__main__":
    unittest.main()
