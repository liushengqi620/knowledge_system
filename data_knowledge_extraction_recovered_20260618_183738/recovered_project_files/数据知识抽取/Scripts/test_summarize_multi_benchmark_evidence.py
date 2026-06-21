from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from summarize_multi_benchmark_evidence import _summarize_skab


class SummarizeMultiBenchmarkEvidenceTest(unittest.TestCase):
    def test_summarize_skab_accepts_strict_run_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "skab_strict.json"
            path.write_text(
                json.dumps(
                    {
                        "status": "ok",
                        "task": "public_benchmark_skab",
                        "runs": [
                            {
                                "main": {"macro_f1": 0.80},
                                "ugmc_selective_correction": {"macro_f1": 0.81},
                                "run_stable_evidence_routing": {"macro_f1": 0.83},
                            },
                            {
                                "main": {"macro_f1": 0.70},
                                "learned_evidence_router": {"macro_f1": 0.72},
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            row = _summarize_skab([path])

        self.assertEqual(row["main"], "0.7500 +/- 0.0500")
        self.assertEqual(row["method"], "0.7750 +/- 0.0550")
        self.assertEqual(row["delta"], "+0.0250")


if __name__ == "__main__":
    unittest.main()
