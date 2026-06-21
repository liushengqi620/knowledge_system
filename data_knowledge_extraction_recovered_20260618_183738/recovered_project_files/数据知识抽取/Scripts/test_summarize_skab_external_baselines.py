from __future__ import annotations

import json
import unittest
import uuid
from pathlib import Path

from summarize_skab_external_baselines import summarize


class SummarizeSKABExternalBaselinesTest(unittest.TestCase):
    def test_summary_interpretation_mentions_gdn_when_present(self) -> None:
        path = Path.cwd() / "knowledge_exports" / f"_test_skab_external_{uuid.uuid4().hex}.json"
        try:
            path.write_text(
                json.dumps(
                    {
                        "methods": ["gdn"],
                        "runs": [
                            {
                                "gdn": {
                                    "metrics": {"macro_f1": 0.55},
                                    "protocol": {
                                        "binary": {
                                            "f1": 0.51,
                                            "far_percent": 52.0,
                                            "mar_percent": 33.0,
                                        }
                                    },
                                }
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = summarize(path)
        finally:
            if path.exists():
                path.unlink()

        self.assertIn("| gdn |", report)
        self.assertIn("GDN-style", report)


if __name__ == "__main__":
    unittest.main()
