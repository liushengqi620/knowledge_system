from __future__ import annotations

import unittest

from summarize_paper_references_bib import render_bib, render_reference_verification


class SummarizePaperReferencesBibTest(unittest.TestCase):
    def test_render_bib_contains_core_dataset_and_baseline_entries(self) -> None:
        bib = render_bib()

        self.assertIn("@article{downs1993tep", bib)
        self.assertIn("A plant-wide industrial process control problem", bib)
        self.assertIn("@misc{skab2020", bib)
        self.assertIn("Skoltech Anomaly Benchmark", bib)
        self.assertIn("@misc{helwig2018hydraulic", bib)
        self.assertIn("Condition Monitoring of Hydraulic Systems", bib)
        self.assertIn("@inproceedings{saxena2008cmapss", bib)
        self.assertIn("Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation", bib)
        self.assertIn("@misc{rieth2017tep", bib)
        self.assertIn("10.7910/DVN/6C3JR1", bib)

        self.assertIn("@inproceedings{usad2020", bib)
        self.assertIn("UnSupervised Anomaly Detection on Multivariate Time Series", bib)
        self.assertIn("@article{tranad2022", bib)
        self.assertIn("Deep Transformer Networks for Anomaly Detection in Multivariate Time Series Data", bib)
        self.assertIn("@article{mtadgat2020", bib)
        self.assertIn("Multivariate Time-series Anomaly Detection via Graph Attention Network", bib)
        self.assertIn("@inproceedings{gdn2021", bib)
        self.assertIn("Graph Neural Network-Based Anomaly Detection in Multivariate Time Series", bib)
        self.assertIn("@inproceedings{anomalytransformer2022", bib)
        self.assertIn("@inproceedings{patchtst2023", bib)
        self.assertIn("@inproceedings{timesnet2023", bib)
        self.assertIn("@inproceedings{itransformer2024", bib)

    def test_render_reference_verification_marks_pending_claim_boundaries(self) -> None:
        report = render_reference_verification()

        self.assertIn("# Reference Verification Report", report)
        self.assertIn("verified", report)
        self.assertIn("pending verification", report)
        self.assertIn("USAD", report)
        self.assertIn("Anomaly Transformer", report)
        self.assertIn("PatchTST", report)
        self.assertIn("TimesNet", report)
        self.assertIn("iTransformer", report)
        self.assertIn("do not use for official SOTA", report)
        self.assertIn("paper_citation_related_work_map.md", report)
        self.assertIn("references.bib", report)
        self.assertIn("exact external protocol alignment", report)


if __name__ == "__main__":
    unittest.main()
