from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from public_benchmark_experiment import (
    apply_selective_logit_correction,
    build_skab_llm_graph_update_prompt,
    build_skab_msfg_tcn_windows,
    call_openai_skab_graph_proposer,
    load_skab_dataset,
    parse_skab_llm_edge_proposals,
    tune_selective_correction,
)


class PublicBenchmarkExperimentTest(unittest.TestCase):
    def test_selective_correction_protects_confident_main_predictions(self) -> None:
        base = np.asarray([[0.95, 0.05], [0.52, 0.48]], dtype=float)
        evidence = np.asarray([[0.05, 0.95], [0.05, 0.95]], dtype=float)

        corrected = apply_selective_logit_correction(
            base,
            evidence,
            weight=2.0,
            confidence_threshold=0.7,
            top_k=2,
        )

        self.assertEqual(int(np.argmax(corrected[0])), 0)
        self.assertEqual(int(np.argmax(corrected[1])), 1)

    def test_tuning_can_select_gated_when_plain_would_hurt(self) -> None:
        y = np.asarray([0, 1], dtype=np.int64)
        base = np.asarray([[0.95, 0.05], [0.52, 0.48]], dtype=float)
        evidence = np.asarray([[0.05, 0.95], [0.05, 0.95]], dtype=float)

        tuning = tune_selective_correction(
            y,
            base,
            evidence,
            weight_grid=[0.0, 2.0],
            confidence_threshold_grid=[0.7],
            top_k_grid=[2],
            allow_plain=True,
            prefer_gated_on_tie=True,
        )

        self.assertEqual(tuning["mode"], "gated")
        self.assertEqual(float(tuning["weight"]), 2.0)

    def test_skab_loader_includes_all_public_groups_and_anomaly_free(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_root = root / "skab" / "raw" / "extracted" / "SKAB-master" / "data"
            template = (
                "datetime;Accelerometer1RMS;Accelerometer2RMS;Current;Pressure;Temperature;"
                "Thermocouple;Voltage;Volume Flow RateRMS"
            )
            normal_dir = data_root / "anomaly-free"
            normal_dir.mkdir(parents=True)
            (normal_dir / "anomaly-free.csv").write_text(
                template + "\n"
                "2020-01-01 00:00:00;1;2;3;4;5;6;7;8\n"
                "2020-01-01 00:00:01;2;3;4;5;6;7;8;9\n",
                encoding="utf-8",
            )
            for group in ["other", "valve1", "valve2"]:
                group_dir = data_root / group
                group_dir.mkdir(parents=True)
                (group_dir / "0.csv").write_text(
                    template + ";anomaly;changepoint\n"
                    "2020-01-01 00:00:00;1;2;3;4;5;6;7;8;0;0\n"
                    "2020-01-01 00:00:01;2;3;4;5;6;7;8;9;1;1\n",
                    encoding="utf-8",
                )

            x, y, meta = load_skab_dataset(root)

            self.assertEqual(set(meta["run_group"].astype(str)), {"anomaly-free", "other", "valve1", "valve2"})
            self.assertEqual(int((meta["run_group"].astype(str) == "anomaly-free").sum()), 2)
            self.assertEqual(int(meta.loc[meta["run_group"].astype(str) == "anomaly-free", "anomaly"].sum()), 0)
            self.assertEqual(int(y.sum()), 3)
            self.assertIn("Current", x.columns)

    def test_skab_msfg_windows_add_edge_channels_for_fused_edges(self) -> None:
        base = np.asarray(
            [
                [[1.0, 2.0, 1.0], [2.0, 4.0, 1.0], [3.0, 6.0, 1.0]],
                [[2.0, 1.0, 1.0], [4.0, 2.0, 1.0], [6.0, 3.0, 1.0]],
            ],
            dtype=np.float32,
        )

        out, cols, diag = build_skab_msfg_tcn_windows(
            base,
            ["Current", "Pressure", "valid_mask"],
            fused_edges=[{"source": "Current", "target": "Pressure", "lag": 1, "reliability": 0.5}],
        )

        self.assertEqual(out.shape, (2, 3, 4))
        self.assertIn("edge_Current_to_Pressure_lag1", cols)
        self.assertEqual(diag["n_used_edges"], 1)
        np.testing.assert_allclose(out[0, :, 3], np.asarray([1.0, 1.5, 2.0], dtype=np.float32))

    def test_skab_graph_proposer_stub_is_unpackable_when_api_is_not_configured(self) -> None:
        with patch.dict(os.environ, {"OPENAI_API_KEY": "", "N1N_API_KEY": "", "LLM_API_KEY": ""}):
            text, diag = call_openai_skab_graph_proposer("prompt")

        self.assertEqual(text, "")
        self.assertEqual(diag["status"], "not_configured")
        self.assertNotIn("api_key", diag)

    def test_skab_graph_proposer_reads_openai_compatible_response(self) -> None:
        class FakeResponse:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *_exc):
                return False

            def read(self) -> bytes:
                return json.dumps(
                    {
                        "choices": [
                            {
                                "message": {
                                    "content": (
                                        '{"edges":[{"source":"Current","target":"Pressure",'
                                        '"lag":1,"relation":"load_pressure","reliability":0.5}]}'
                                    )
                                }
                            }
                        ]
                    }
                ).encode("utf-8")

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
            with patch("public_benchmark_experiment.urllib.request.urlopen", return_value=FakeResponse()) as mocked:
                text, diag = call_openai_skab_graph_proposer("prompt", base_url="https://example.test/v1")

        self.assertIn('"edges"', text)
        self.assertEqual(diag["status"], "ok")
        self.assertEqual(diag["base_url"], "https://example.test/v1")
        self.assertNotIn("test-key", json.dumps(diag))
        self.assertTrue(mocked.called)

    def test_skab_llm_graph_prompt_frames_condition_verifier(self) -> None:
        prompt = build_skab_llm_graph_update_prompt(
            allowed_features=["Current", "Pressure"],
            error_summary={"false_negative_rate": 0.2},
            existing_edges=[{"source": "Current", "target": "Pressure", "lag": 1}],
            max_edges=2,
        )

        self.assertIn("conditional mechanism verifier", prompt)
        self.assertIn("not final graph edges", prompt)
        self.assertIn("Current", prompt)
        self.assertIn("required_output_schema", prompt)

    def test_parse_skab_llm_edge_proposals_filters_invalid_edges(self) -> None:
        text = (
            '{"edges": ['
            '{"source": "Current", "target": "Pressure", "lag": 20, "reliability": 0.9},'
            '{"source": "Current", "target": "Pressure", "lag": 1, "reliability": 0.2},'
            '{"source": "Bad", "target": "Pressure", "lag": 1, "reliability": 0.5}'
            "]}"
        )

        edges, diag = parse_skab_llm_edge_proposals(
            text,
            allowed_features=["Current", "Pressure"],
            max_lag=12,
            reliability_cap=0.72,
        )

        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["lag"], 12)
        self.assertEqual(edges[0]["reliability"], 0.72)
        self.assertEqual(diag["accepted_edges"], 1)


if __name__ == "__main__":
    unittest.main()
