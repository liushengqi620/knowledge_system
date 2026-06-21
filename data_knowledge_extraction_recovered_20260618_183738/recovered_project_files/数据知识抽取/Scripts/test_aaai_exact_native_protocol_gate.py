from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aaai_exact_native_protocol_gate import (
    build_exact_native_protocol_gate,
    render_markdown,
    write_exact_native_protocol_gate,
)


class AaaiExactNativeProtocolGateTest(unittest.TestCase):
    def test_gate_blocks_official_sota_until_exact_native_protocols_match(self) -> None:
        payload = build_exact_native_protocol_gate()

        self.assertEqual("official_sota_not_admissible", payload["overall_status"])
        self.assertEqual([], payload["official_sota_admissible_datasets"])
        self.assertIn("matched-protocol", payload["safe_overall_claim"])
        self.assertIn("universal official leaderboard SOTA", payload["unsafe_overall_claim"])

        rows = {row["dataset"]: row for row in payload["rows"]}
        self.assertEqual({"TEP", "SKAB", "Hydraulic", "C-MAPSS"}, set(rows))
        self.assertFalse(rows["TEP"]["official_sota_claim_admissible"])
        self.assertIn("exact_public_split", rows["TEP"]["missing_gates"])
        self.assertIn("official_or_published_baseline_protocol", rows["C-MAPSS"]["missing_gates"])
        self.assertNotIn("exact_preprocessing", rows["C-MAPSS"]["missing_gates"])
        self.assertTrue(rows["C-MAPSS"]["gates"]["native_task_preserved"])
        self.assertTrue(rows["C-MAPSS"]["gates"]["exact_preprocessing"])
        self.assertTrue(rows["C-MAPSS"]["gates"]["exact_metric"])
        self.assertIn("pseudo-terminal validation rerun RMSE 18.2840", rows["C-MAPSS"]["current_result"])
        self.assertIn("native preprocessing manifest is complete", " ".join(rows["C-MAPSS"]["blocking_evidence"]))
        self.assertIn("LSTM sequence branch is materialized", " ".join(rows["C-MAPSS"]["blocking_evidence"]))
        self.assertIn("PHM score favors w80/cap150 by 408.20", " ".join(rows["C-MAPSS"]["blocking_evidence"]))
        self.assertIn("published-baseline contract is now materialized", " ".join(rows["C-MAPSS"]["blocking_evidence"]))
        self.assertIn("LSTM source-protocol audit extracts", " ".join(rows["C-MAPSS"]["blocking_evidence"]))
        self.assertIn("open-protocol candidate audit identifies MDFA 2025", " ".join(rows["C-MAPSS"]["blocking_evidence"]))
        self.assertIn("MDFA source profile reconciles FD001-FD004", " ".join(rows["C-MAPSS"]["blocking_evidence"]))
        self.assertIn("FD004 train=249/test=248", " ".join(rows["C-MAPSS"]["blocking_evidence"]))
        self.assertIn("source_2d time-feature convolutions", " ".join(rows["C-MAPSS"]["blocking_evidence"]))
        self.assertIn("low-dropout long-window", " ".join(rows["C-MAPSS"]["blocking_evidence"]))
        self.assertIn(
            "source2d_all24_pca_window80_dropout01_fd001_full",
            " ".join(rows["C-MAPSS"]["blocking_evidence"]),
        )
        self.assertIn("exact budget equivalence", " ".join(rows["C-MAPSS"]["blocking_evidence"]))
        self.assertFalse(rows["C-MAPSS"]["gates"]["matched_budget"])
        self.assertTrue(rows["SKAB"]["gates"]["exact_metric"])
        self.assertTrue(rows["SKAB"]["gates"]["threshold_or_delay_policy"])
        self.assertNotIn("exact_metric", rows["SKAB"]["missing_gates"])
        self.assertIn("official_or_published_baseline_protocol", rows["SKAB"]["missing_gates"])
        self.assertIn("official baseline gate", " ".join(rows["SKAB"]["blocking_evidence"]))
        self.assertIn("frozen wrapper prediction records", " ".join(rows["SKAB"]["blocking_evidence"]))
        self.assertIn("official SKAB precomputed leaderboard rows", " ".join(rows["SKAB"]["blocking_evidence"]))
        self.assertIn("README outlier leaderboard is recomputed", " ".join(rows["SKAB"]["blocking_evidence"]))
        self.assertIn("matched partial official notebook/core source reruns for T2/T2+Q, Isolation Forest, MSET, Vanilla-AE, and Conv-AE", " ".join(rows["SKAB"]["blocking_evidence"]))
        self.assertIn("LSTM-AE, MSCRED, and Vanilla-LSTM are rerun with frozen records", " ".join(rows["SKAB"]["blocking_evidence"]))
        self.assertIn("do not match the official leaderboard within tolerance", " ".join(rows["SKAB"]["blocking_evidence"]))
        self.assertIn("prediction-level rerun variance", " ".join(rows["SKAB"]["blocking_evidence"]))
        self.assertIn("ArimaFD, exact split, preprocessing, and budget matching are still not closed", " ".join(rows["SKAB"]["blocking_evidence"]))

    def test_markdown_is_claim_safe(self) -> None:
        markdown = render_markdown(build_exact_native_protocol_gate())

        self.assertIn("# AAAI Exact-Native Protocol Gate", markdown)
        self.assertIn("official_sota_not_admissible", markdown)
        self.assertIn("Missing exact-native gates", markdown)
        self.assertIn("reliability-calibrated mechanism evidence fusion", markdown)
        self.assertNotIn("SOTA-candidate", markdown)

    def test_write_exact_native_protocol_gate_outputs_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            written = write_exact_native_protocol_gate(output_dir)

            self.assertEqual(
                {output_dir / "aaai_exact_native_protocol_gate.json", output_dir / "aaai_exact_native_protocol_gate.md"},
                set(written),
            )
            payload = json.loads((output_dir / "aaai_exact_native_protocol_gate.json").read_text(encoding="utf-8"))
            markdown = (output_dir / "aaai_exact_native_protocol_gate.md").read_text(encoding="utf-8")
            self.assertEqual("official_sota_not_admissible", payload["overall_status"])
            self.assertIn("AAAI Exact-Native Protocol Gate", markdown)


if __name__ == "__main__":
    unittest.main()
