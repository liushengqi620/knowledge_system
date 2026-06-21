from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path

from Scripts.summarize_attention_gate_replacement import summarize


class SummarizeAttentionGateReplacementTest(unittest.TestCase):
    def test_report_separates_gate_proxy_evidence_from_missing_replacement(self) -> None:
        root = Path.cwd() / "tmp_tests" / "attention_gate_replacement_case"
        if root.exists():
            shutil.rmtree(root)
        root.mkdir(parents=True)
        try:
            tep = root / "tep_gatehead.json"
            tep.write_text(
                json.dumps(
                    {
                        "summary": {
                            "no_graph": {"n_runs": 3, "target_defect_macro_f1_mean": 0.5363, "target_defect_macro_f1_std": 0.0197},
                            "all_lagged": {"n_runs": 3, "target_defect_macro_f1_mean": 0.5309, "target_defect_macro_f1_std": 0.0240},
                            "reliable_lagged": {"n_runs": 3, "target_defect_macro_f1_mean": 0.5212, "target_defect_macro_f1_std": 0.0150},
                            "residual_gated_lagged": {"n_runs": 3, "target_defect_macro_f1_mean": 0.5683, "target_defect_macro_f1_std": 0.0053},
                        }
                    }
                ),
                encoding="utf-8",
            )

            report = summarize(
                tep_gatehead_path=tep,
                skab_plan_name="skab_cf_guarded_admission_suite_plan.md",
                replacement_command="python Scripts/run_tep_sequence_graph_ablation.py --model-name residual_gatehead",
            )

            self.assertIn("# Attention/Edge-Gate Replacement Readiness", report)
            self.assertIn("residual_gated_lagged", report)
            self.assertIn("0.5683 +/- 0.0053", report)
            self.assertIn("+0.0320", report)
            self.assertIn("proxy evidence", report)
            self.assertIn("not yet a decisive replacement baseline", report)
            self.assertIn("skab_cf_guarded_admission_suite_plan.md", report)
            self.assertIn("python Scripts/run_tep_sequence_graph_ablation.py", report)
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
