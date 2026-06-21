from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aaai_pdf_float_inspection import build_pdf_float_inspection, render_markdown


class AaaiPdfFloatInspectionTest(unittest.TestCase):
    def test_missing_pdf_reports_blocking_issue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_pdf_float_inspection(Path(tmp))

        self.assertEqual(report["status"], "missing_pdf")
        self.assertIn("main.pdf is missing", report["issues"])

    def test_render_markdown_includes_pages_and_manual_note(self) -> None:
        report = {
            "status": "inspected_clean",
            "pdf_path": "pkg/main.pdf",
            "render_dir": "pkg/pdf_float_inspection",
            "page_count": 1,
            "issues": [],
            "pages": [{"path": "pkg/pdf_float_inspection/main_page-1.png", "bytes": 12345, "width": 100, "height": 200}],
            "manual_inspection_note": "checked",
        }

        markdown = render_markdown(report)

        self.assertIn("AAAI PDF Float Inspection", markdown)
        self.assertIn("inspected_clean", markdown)
        self.assertIn("100x200", markdown)
        self.assertIn("checked", markdown)


if __name__ == "__main__":
    unittest.main()
