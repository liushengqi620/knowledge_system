from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cmapss_rul_backbone_optimization_audit import (
    build_cmapss_rul_backbone_optimization_audit,
    render_markdown,
    write_cmapss_rul_backbone_optimization_audit,
)


class CmapssRulBackboneOptimizationAuditTest(unittest.TestCase):
    def test_audit_keeps_path_fusion_closed_when_temporal_anchor_is_better(self) -> None:
        payload = build_cmapss_rul_backbone_optimization_audit()

        self.assertEqual("cmapss_rul_backbone_optimization_partial", payload["status"])
        self.assertTrue(payload["gates"]["cap150_improves_w80_gru"])
        self.assertTrue(payload["gates"]["long_window_improves_cap150_gru"])
        self.assertTrue(payload["gates"]["pseudo_terminal_rmse_selection_supports_long_window"])
        self.assertFalse(payload["gates"]["path_fusion_admitted_for_cmapss"])
        self.assertFalse(payload["gates"]["long_window_path_smoke_admitted"])
        self.assertGreater(payload["deltas"]["cap150_vs_cap125_gru_rmse_reduction"], 0.0)
        self.assertGreater(payload["deltas"]["w160_vs_w80_cap150_gru_rmse_reduction"], 0.0)
        self.assertIn("long-window temporal anchor", payload["recommended_cmapss_role"])

    def test_write_outputs_claim_safe_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            written = write_cmapss_rul_backbone_optimization_audit(output_dir)

            self.assertEqual(
                {output_dir / "cmapss_rul_backbone_optimization_audit.json", output_dir / "cmapss_rul_backbone_optimization_audit.md"},
                set(written),
            )
            payload = json.loads((output_dir / "cmapss_rul_backbone_optimization_audit.json").read_text(encoding="utf-8"))
            markdown = render_markdown(payload)
        self.assertIn("C-MAPSS RUL Backbone Optimization Audit", markdown)
        self.assertIn("Pseudo-Terminal Validation", markdown)
        self.assertIn("complete_with_score_tradeoff", markdown)
        self.assertIn("path_fusion_admitted_for_cmapss | closed", markdown)
        self.assertIn("PHM-score trade-off", markdown)
        self.assertNotIn("literature-wide SOTA achieved", markdown)


if __name__ == "__main__":
    unittest.main()
