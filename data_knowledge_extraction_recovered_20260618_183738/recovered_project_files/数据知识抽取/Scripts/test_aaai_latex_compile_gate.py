from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from aaai_latex_compile_gate import build_compile_gate, write_compile_gate


class AaaiLatexCompileGateTest(unittest.TestCase):
    def test_blocks_when_official_style_is_not_integrated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            (package_dir / "main.tex").write_text(r"\documentclass{article}", encoding="utf-8")

            report = build_compile_gate(package_dir)

            self.assertEqual(report["status"], "blocked_official_style_not_integrated")
            self.assertFalse(report["official_style_ready"])

    def test_blocks_when_latex_toolchain_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            (package_dir / "main.tex").write_text(r"\usepackage[submission]{aaai2027}", encoding="utf-8")
            (package_dir / "aaai2027.sty").write_text("% style\n", encoding="utf-8")
            (package_dir / "aaai2027.bst").write_text("% bst\n", encoding="utf-8")

            with mock.patch("aaai_latex_compile_gate.shutil.which", return_value=None):
                report = build_compile_gate(package_dir)

            self.assertEqual(report["status"], "blocked_missing_latex_toolchain")
            self.assertTrue(report["official_style_ready"])

    def test_stale_pdf_is_not_reported_as_compiled_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            tex = package_dir / "main.tex"
            pdf = package_dir / "main.pdf"
            log = package_dir / "main.log"
            tex.write_text(r"\usepackage[submission]{aaai2027}", encoding="utf-8")
            (package_dir / "aaai2027.sty").write_text("% style\n", encoding="utf-8")
            (package_dir / "aaai2027.bst").write_text("% bst\n", encoding="utf-8")
            pdf.write_bytes(b"x" * 2000)
            log.write_text("Output written on main.pdf\n", encoding="utf-8")
            old = 1000.0
            new = 2000.0
            os.utime(pdf, (old, old))
            os.utime(log, (old, old))
            os.utime(tex, (new, new))

            report = build_compile_gate(package_dir)

            self.assertEqual("ready_to_compile", report["status"])
            self.assertFalse(report["artifacts_fresh"])

    def test_write_compile_gate_writes_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)

            written = write_compile_gate(output_dir)

            self.assertEqual(set(written), {output_dir / "aaai_latex_compile_gate.json", output_dir / "aaai_latex_compile_gate.md"})
            payload = json.loads((output_dir / "aaai_latex_compile_gate.json").read_text(encoding="utf-8"))
            self.assertIn(
                payload["status"],
                {
                    "blocked_official_style_not_integrated",
                    "blocked_missing_latex_toolchain",
                    "ready_to_compile",
                    "compiled_with_layout_warnings",
                    "compiled_clean",
                },
            )
            self.assertIn("overfull_hbox_count", payload)
            self.assertIn("artifacts_fresh", payload)
            self.assertIn("AAAI LaTeX Compile Gate", (output_dir / "aaai_latex_compile_gate.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
