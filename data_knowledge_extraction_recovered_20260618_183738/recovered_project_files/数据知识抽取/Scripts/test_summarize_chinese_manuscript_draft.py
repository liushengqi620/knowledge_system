from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from summarize_chinese_manuscript_draft import render_chinese_draft, write_chinese_draft


class SummarizeChineseManuscriptDraftTest(unittest.TestCase):
    def test_render_chinese_draft_contains_current_claim_boundaries(self) -> None:
        draft = render_chinese_draft()

        self.assertIn("可靠性校准机理证据融合", draft)
        self.assertIn("候选机理证据", draft)
        self.assertIn("LLM 不作为独立最终边源", draft)
        self.assertIn("CF 0.8798 +/- 0.0317", draft)
        self.assertIn("no-CF 0.8801 +/- 0.0317", draft)
        self.assertIn("Macro-F1 0.8450 +/- 0.0189", draft)
        self.assertIn("反事实项不应被包装为主要性能来源", draft)
        self.assertIn("PatchTST、Anomaly Transformer 和 Graph WaveNet", draft)
        self.assertIn("官方源码适配对照", draft)
        self.assertIn("FAR 38.34", draft)
        self.assertIn("MAR 63.29", draft)
        self.assertIn("skab_official_baseline_gate", draft)
        self.assertIn("skab_official_repository_baseline_audit", draft)
        self.assertIn("skab_official_source_rerun_audit", draft)
        self.assertIn("official-source Anomaly Transformer wrapper", draft)
        self.assertIn("Conv-AE F1 0.7838", draft)
        self.assertIn("T2+Q F1 0.7581", draft)
        self.assertIn("MSET F1 0.7800", draft)
        self.assertIn("Vanilla-AE F1 0.3938", draft)
        self.assertIn("Conv-AE F1 0.7842", draft)
        self.assertIn("LSTM-AE（F1 0.7515）", draft)
        self.assertIn("MSCRED（F1 0.3382）", draft)
        self.assertIn("Vanilla-LSTM（F1 0.5111）", draft)
        self.assertIn("诊断复现", draft)
        self.assertIn("ArimaFD", draft)
        self.assertIn("冻结 JSONL 预测记录", draft)
        self.assertIn("部分官方源码复现证据", draft)
        self.assertIn("部分源码重跑、delta 归因和诊断复现证据", draft)
        self.assertIn("差异来自预测层面的重跑方差", draft)
        self.assertIn("已补齐冻结预测记录", draft)
        self.assertIn("split、preprocessing 和 budget 也未精确对齐", draft)
        self.assertIn("不能写官方排行榜 SOTA", draft)
        self.assertIn("英文投稿稿保留在官方 LaTeX 包中", draft)
        self.assertNotIn("通用官方 SOTA", draft.split("## 4 主要结果", 1)[0])
        self.assertNotIn("闈", draft)
        self.assertNotIn("銆", draft)

    def test_write_chinese_draft_outputs_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "manuscript_chinese_draft.md"
            written = write_chinese_draft(output)

            self.assertEqual(written, output)
            self.assertTrue(output.exists())
            text = output.read_text(encoding="utf-8")
            self.assertIn("## 9 结论", text)
            self.assertIn("面向工业时序故障诊断", text)
            self.assertNotIn("闈", text)


if __name__ == "__main__":
    unittest.main()
