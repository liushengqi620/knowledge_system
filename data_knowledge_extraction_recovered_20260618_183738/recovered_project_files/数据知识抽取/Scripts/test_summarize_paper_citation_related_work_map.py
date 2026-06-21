from __future__ import annotations

import unittest

from summarize_paper_citation_related_work_map import render_citation_map


class SummarizePaperCitationRelatedWorkMapTest(unittest.TestCase):
    def test_render_citation_map_contains_related_work_and_verification_status(self) -> None:
        report = render_citation_map()

        self.assertIn("# Citation and Related Work Map", report)
        self.assertIn("## Citation Status Legend", report)
        self.assertIn("verified", report)
        self.assertIn("pending verification", report)

        self.assertIn("## Related Work Buckets", report)
        self.assertIn("industrial fault diagnosis", report)
        self.assertIn("graph-based time-series diagnosis", report)
        self.assertIn("knowledge-enhanced diagnosis", report)
        self.assertIn("LLM-assisted scientific reasoning", report)

        self.assertIn("## Dataset and Baseline Citation Matrix", report)
        self.assertIn("TEP", report)
        self.assertIn("Tennessee Eastman", report)
        self.assertIn("SKAB", report)
        self.assertIn("Hydraulic", report)
        self.assertIn("C-MAPSS", report)
        self.assertIn("NASA", report)

        self.assertIn("USAD", report)
        self.assertIn("TranAD", report)
        self.assertIn("GDN", report)
        self.assertIn("MTAD-GAT", report)
        self.assertIn("Anomaly Transformer", report)
        self.assertIn("PatchTST", report)
        self.assertIn("TimesNet", report)
        self.assertIn("iTransformer", report)

        self.assertIn("## Verified Source URLs", report)
        self.assertIn("10.7910/DVN/6C3JR1", report)
        self.assertIn("10.34740/KAGGLE/DSV/1693952", report)
        self.assertIn("https://arxiv.org/abs/2211.14730", report)
        self.assertIn("terminal-test RUL task verified", report)

        self.assertIn("## Manuscript Insertion Plan", report)
        self.assertIn("Related Work", report)
        self.assertIn("Experiments", report)
        self.assertIn("Limitations", report)
        self.assertIn("non-identical reference", report)

        self.assertIn("## BibTeX To-Do", report)
        self.assertIn("exact title", report)
        self.assertIn("official URL", report)
        self.assertIn("protocol match", report)


if __name__ == "__main__":
    unittest.main()
