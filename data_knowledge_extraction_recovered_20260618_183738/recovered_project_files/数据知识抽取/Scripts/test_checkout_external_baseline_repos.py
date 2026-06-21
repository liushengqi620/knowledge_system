from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from checkout_external_baseline_repos import build_checkout_audit_payload, render_checkout_audit_markdown


def _fs_path(path: Path | str) -> str:
    text = str(Path(path).resolve())
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(["git", *args], cwd=_fs_path(cwd), check=True, capture_output=True, text=True)
    return result.stdout.strip()


class CheckoutExternalBaselineReposTest(unittest.TestCase):
    def test_checkout_audit_records_verified_commit_and_protocol_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkout_root = root / "checkouts"
            checkout = checkout_root / "patchtst"
            checkout.mkdir(parents=True)
            _git(["init"], checkout)
            (checkout / "requirements.txt").write_text("torch\nnumpy\n", encoding="utf-8")
            (checkout / "run_longExp.py").write_text("print('run')\n", encoding="utf-8")
            (checkout / "PatchTST_backbone.py").write_text("class Model: pass\n", encoding="utf-8")
            (checkout / "data_provider.py").write_text("class Dataset: pass\n", encoding="utf-8")
            _git(["add", "."], checkout)
            _git(["-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "init"], checkout)
            commit = _git(["rev-parse", "HEAD"], checkout)

            snapshot = {
                "rows": [
                    {
                        "name": "PatchTST",
                        "repo_url": "https://github.com/yuqinie98/PatchTST",
                        "resolved_default_branch": "main",
                        "resolved_head_commit": commit,
                    }
                ]
            }
            snapshot_path = root / "snapshot.json"
            snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")

            payload = build_checkout_audit_payload(
                source_snapshot=snapshot_path,
                checkout_root=checkout_root,
                skip_clone=True,
            )

            self.assertEqual(payload["overall_status"], "official_repo_checkouts_verified")
            row = payload["rows"][0]
            self.assertEqual(row["checkout_status"], "checkout_verified")
            self.assertTrue(row["commit_matches_snapshot"])
            self.assertFalse(row["official_external_score"])
            self.assertIn(
                row["protocol_wrapper_status"],
                {
                    "not_implemented",
                    "official_source_adapted_backbone_wrapper_available_not_official_score",
                    "patched_skab_official_source_wrapper_available_not_official_score",
                    "official_source_adapted_graph_temporal_wrapper_available_not_official_score",
                },
            )
            self.assertIn("requirements.txt", row["dependency_files"])
            self.assertIn("run_longExp.py", row["entrypoint_candidates"])
            self.assertIn("PatchTST_backbone.py", row["model_file_candidates"])
            self.assertIn("data_provider.py", row["data_interface_candidates"])

            markdown = render_checkout_audit_markdown(payload)
            self.assertIn("Official External Repository Checkout Audit", markdown)
            self.assertIn("checkout_verified", markdown)
            self.assertIn("not official external scores", payload["claim_gate"])


if __name__ == "__main__":
    unittest.main()
