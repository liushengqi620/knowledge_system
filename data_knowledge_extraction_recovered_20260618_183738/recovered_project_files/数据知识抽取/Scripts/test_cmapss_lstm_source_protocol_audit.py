from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cmapss_lstm_source_protocol_audit import (
    build_cmapss_lstm_source_protocol_audit,
    render_markdown,
    write_cmapss_lstm_source_protocol_audit,
)


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


class CmapssLstmSourceProtocolAuditTest(unittest.TestCase):
    def test_audit_extracts_local_config_but_blocks_exact_reproduction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = root / "cmapss_published_baseline_contract.json"
            run_dir = root / "lstm_sequence"
            _write(
                contract,
                {
                    "baseline_contracts": [
                        {
                            "id": "lstm_rul_2017",
                            "local_seed_archives_present": True,
                            "local_scope_covers_required": True,
                            "exact_reproduction_status": "not_exact_reproduction",
                            "field_status": {"training_budget": "missing_source_exact"},
                        }
                    ]
                },
            )
            for seed in (42, 43, 44):
                _write(
                    run_dir / f"cmapss_rul_lstm_sequence_seed{seed}.json",
                    {
                        "seed": seed,
                        "window_size": 80,
                        "rul_cap": 125.0,
                        "baseline_diagnostics": {
                            "epochs": 25,
                            "batch_size": 256,
                            "learning_rate": 0.001,
                            "hidden_dim": 64,
                            "layers": 2,
                            "dropout": 0.1,
                            "parameters": 123,
                            "device": "cuda",
                        },
                        "primary_test_metrics": {"rul_rmse": 20.0 + seed / 1000.0, "rul_score": 9000.0},
                        "rul_subset_metrics": {"rows": [{"subset": "FD001"}]},
                    },
                )

            payload = build_cmapss_lstm_source_protocol_audit(contract, run_dir)

            self.assertEqual("source_protocol_incomplete_local_config_extracted", payload["status"])
            self.assertTrue(payload["gates"]["local_lstm_seed_archive_present"])
            self.assertTrue(payload["gates"]["local_config_extracted"])
            self.assertFalse(payload["gates"]["paper_fulltext_protocol_available"])
            self.assertFalse(payload["gates"]["safe_to_promote_lstm_to_exact_reproduction"])
            self.assertIn("training_budget", payload["unverified_source_fields"])
            self.assertEqual([25], payload["local_lstm_summary"]["unique_config"]["epochs"])
            self.assertEqual("not_exact_reproduction", payload["contract_lstm_status"]["exact_reproduction_status"])

    def test_writer_and_markdown_are_claim_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            written = write_cmapss_lstm_source_protocol_audit(output_dir)
            self.assertEqual(
                {
                    output_dir / "cmapss_lstm_source_protocol_audit.json",
                    output_dir / "cmapss_lstm_source_protocol_audit.md",
                },
                set(written),
            )
            payload = json.loads((output_dir / "cmapss_lstm_source_protocol_audit.json").read_text(encoding="utf-8"))
            markdown = render_markdown(payload)
            self.assertIn("C-MAPSS LSTM Source Protocol Audit", markdown)
            self.assertIn("paper_fulltext_protocol_available", markdown)
            self.assertIn("not_available_in_current_environment", markdown)
            self.assertIn("published-style", payload["claim_boundary"])
            self.assertNotIn("official LSTM reproduction is complete", markdown)


if __name__ == "__main__":
    unittest.main()
