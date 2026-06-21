from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aaai_sota_gap_ledger import build_sota_gap_ledger, render_markdown, write_sota_gap_ledger


class AaaiSotaGapLedgerTest(unittest.TestCase):
    def test_ledger_quantifies_matched_gains_without_unlocking_official_sota(self) -> None:
        payload = build_sota_gap_ledger()

        self.assertEqual("official_sota_not_admissible", payload["status"])
        self.assertEqual([], payload["official_sota_admissible_datasets"])
        self.assertIn("exact-native gate", payload["claim_rule"])

        rows = {row["dataset"]: row for row in payload["matched_result_rows"]}
        self.assertEqual({"TEP", "SKAB", "Hydraulic", "C-MAPSS"}, set(rows))
        self.assertAlmostEqual(0.0427, rows["TEP"]["matched_improvement"], places=4)
        self.assertAlmostEqual(0.0257, rows["SKAB"]["matched_improvement"], places=4)
        self.assertAlmostEqual(2.6942, rows["C-MAPSS"]["matched_improvement"], places=4)
        self.assertEqual("matched_only", rows["SKAB"]["official_status"])
        self.assertIn("official_or_published_baseline_protocol", rows["SKAB"]["missing_exact_native_gates"])
        self.assertIn("matched_budget", rows["C-MAPSS"]["missing_exact_native_gates"])

    def test_ledger_records_cmapss_mdfa_subset_gaps_and_priority_actions(self) -> None:
        payload = build_sota_gap_ledger()

        subsets = {row["subset"]: row for row in payload["cmapss_mdfa_source_style_subset_gaps"]}
        self.assertEqual({"FD001", "FD002", "FD003", "FD004"}, set(subsets))
        self.assertAlmostEqual(0.7698, subsets["FD001"]["gap_current_minus_reference"], places=4)
        self.assertLess(subsets["FD002"]["gap_current_minus_reference"], 0.0)
        self.assertAlmostEqual(1.0360, subsets["FD003"]["gap_current_minus_reference"], places=4)
        self.assertLess(subsets["FD004"]["gap_current_minus_reference"], 0.0)
        self.assertAlmostEqual(-0.5009, payload["cmapss_mdfa_source_style_mean_gap_current_minus_reference"], places=4)
        self.assertIn("not_official_sota", subsets["FD001"]["claim_boundary"])

        priorities = {(row["priority"], row["dataset"]): row for row in payload["priority_actions"]}
        self.assertIn(("P0", "SKAB"), priorities)
        self.assertIn(("P0", "C-MAPSS"), priorities)
        self.assertIn("skab_official_baseline_gate", " ".join(priorities[("P0", "SKAB")]["next_experiments"]))
        self.assertIn("frozen wrapper prediction records", priorities[("P0", "SKAB")]["reason"])
        self.assertIn("recomputed official SKAB precomputed", priorities[("P0", "SKAB")]["reason"])
        self.assertIn("matched partial official notebook/core source reruns for T2/T2+Q, Isolation Forest, MSET, Vanilla-AE, and Conv-AE", priorities[("P0", "SKAB")]["reason"])
        self.assertIn("diagnostic LSTM-AE/MSCRED/Vanilla-LSTM reruns with frozen records", priorities[("P0", "SKAB")]["reason"])
        self.assertIn("prediction-level rerun variance", priorities[("P0", "SKAB")]["reason"])
        self.assertIn("ArimaFD, and budget gates remain closed", priorities[("P0", "SKAB")]["reason"])
        self.assertIn("official precomputed leaderboard rows", " ".join(priorities[("P0", "SKAB")]["next_experiments"]))
        self.assertIn("T2/T2+Q, Isolation Forest, MSET, Vanilla-AE, and Conv-AE notebook/core reruns", " ".join(priorities[("P0", "SKAB")]["next_experiments"]))
        self.assertIn("explained prediction-level deltas", " ".join(priorities[("P0", "SKAB")]["next_experiments"]))
        self.assertIn("remaining official ArimaFD notebook", " ".join(priorities[("P0", "SKAB")]["next_experiments"]))
        self.assertIn("MDFA", " ".join(priorities[("P0", "C-MAPSS")]["next_experiments"]))

    def test_markdown_and_writer_are_claim_safe(self) -> None:
        payload = build_sota_gap_ledger()
        markdown = render_markdown(payload)

        self.assertIn("# AAAI SOTA Gap Ledger", markdown)
        self.assertIn("official_sota_not_admissible", markdown)
        self.assertIn("0.8450", markdown)
        self.assertIn("FD003", markdown)
        self.assertIn("not official SOTA proof", markdown)
        self.assertNotIn("SOTA-candidate", markdown)

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            written = write_sota_gap_ledger(output_dir)
            self.assertEqual(
                {output_dir / "aaai_sota_gap_ledger.json", output_dir / "aaai_sota_gap_ledger.md"},
                set(written),
            )
            saved = json.loads((output_dir / "aaai_sota_gap_ledger.json").read_text(encoding="utf-8"))
            self.assertEqual("official_sota_not_admissible", saved["status"])


if __name__ == "__main__":
    unittest.main()
