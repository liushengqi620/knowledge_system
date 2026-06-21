from __future__ import annotations

import json
import os
import shutil
import unittest
from pathlib import Path

from pending_baseline_alignment_artifact import build_alignment_artifact


def _fs_path(path: Path | str) -> str:
    text = str(Path(path).resolve())
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


class PendingBaselineAlignmentArtifactTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path("knowledge_exports") / "_tmp_pending_alignment_artifact_test"
        shutil.rmtree(self.root, ignore_errors=True)
        self.root.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_build_alignment_artifact_records_hash_budget_and_best_variant(self) -> None:
        source = self.root / "graph_wavenet_run.json"
        source.write_text(
            json.dumps(
                {
                    "model_name": "graph_wavenet",
                    "seeds": [42, 43, 44],
                    "variants": [{"name": "no_graph"}, {"name": "reliable_lagged"}],
                    "summary": {
                        "no_graph": {"target_defect_macro_f1_mean": 0.10},
                        "reliable_lagged": {"target_defect_macro_f1_mean": 0.12},
                    },
                    "records": [{"seed": 42}, {"seed": 43}],
                }
            ),
            encoding="utf-8",
        )
        output = self.root / "graph_wavenet_tep_seed42_gate.json"

        artifact = build_alignment_artifact(
            source_result=source,
            output=output,
            baseline="Graph WaveNet",
            dataset="TEP",
            budget_status="local_probe",
            admissibility="not_admissible_until_exact_external_alignment",
            notes="test artifact",
        )

        self.assertTrue(os.path.exists(_fs_path(output)))
        self.assertEqual(artifact["artifact_type"], "pending_baseline_alignment_artifact")
        self.assertEqual(artifact["baseline"], "Graph WaveNet")
        self.assertEqual(artifact["budget_status"], "local_probe")
        self.assertEqual(artifact["public_table_admissibility"], "not_admissible_until_exact_external_alignment")
        self.assertEqual(artifact["exact_external_alignment_status"], "pending")
        self.assertEqual(artifact["best_variant"]["name"], "reliable_lagged")
        self.assertEqual(artifact["records_count"], 2)
        self.assertRegex(artifact["source_sha256"], r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
