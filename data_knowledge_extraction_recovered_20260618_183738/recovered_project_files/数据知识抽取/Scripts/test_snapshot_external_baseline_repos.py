from __future__ import annotations

import json
import os
import shutil
import unittest
from pathlib import Path

from snapshot_external_baseline_repos import (
    build_official_repo_snapshot,
    build_official_repo_snapshot_payload,
    render_official_repo_snapshot_markdown,
)


def _fs_path(path: Path | str) -> str:
    text = str(Path(path).resolve())
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _fake_ls_remote(_repo_url: str, _timeout: int) -> str:
    return "ref: refs/heads/main\tHEAD\n0123456789abcdef0123456789abcdef01234567\tHEAD\n"


def _fake_json(url: str, _timeout: int):
    if url.endswith("/contents?ref=main"):
        return [{"name": "README.md"}, {"name": "LICENSE"}, {"name": "model.py"}]
    return {
        "default_branch": "main",
        "license": {"key": "mit"},
        "description": "fake official repository",
        "pushed_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-02T00:00:00Z",
    }


class ExternalBaselineRepoSnapshotTest(unittest.TestCase):
    def setUp(self) -> None:
        self.output_dir = Path("knowledge_exports") / "_tmp_external_repo_snapshot_test"
        shutil.rmtree(self.output_dir, ignore_errors=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.output_dir, ignore_errors=True)

    def test_payload_records_repo_head_without_claiming_official_score(self) -> None:
        payload = build_official_repo_snapshot_payload(
            allow_network=True,
            json_fetcher=_fake_json,
            ls_remote_runner=_fake_ls_remote,
        )

        self.assertEqual(payload["overall_status"], "official_repo_heads_resolved")
        rows = {row["name"]: row for row in payload["rows"]}
        self.assertEqual(set(rows), {"PatchTST", "Anomaly Transformer", "Graph WaveNet"})
        for name, row in rows.items():
            self.assertEqual(row["snapshot_status"], "repo_head_resolved", name)
            self.assertEqual(row["resolved_default_branch"], "main", name)
            self.assertTrue(row["resolved_head_commit"].startswith("012345"), name)
            self.assertFalse(row["official_external_score"], name)
            self.assertEqual(row["protocol_reproduction_status"], "not_started_from_snapshot", name)
            self.assertTrue(row["root_files"]["has_readme"], name)
            self.assertTrue(row["root_files"]["has_license_file"], name)

        markdown = render_official_repo_snapshot_markdown(payload)
        self.assertIn("Official External Repository Snapshot", markdown)
        self.assertIn("not_started_from_snapshot", markdown)
        self.assertIn("Repository snapshots are provenance evidence only", markdown)

    def test_writes_offline_source_only_snapshot(self) -> None:
        written = build_official_repo_snapshot(self.output_dir, allow_network=False)
        expected = {
            self.output_dir / "official_external_repo_snapshot.json",
            self.output_dir / "official_external_repo_snapshot.md",
        }
        self.assertEqual(set(written), expected)
        for path in expected:
            self.assertTrue(os.path.exists(_fs_path(path)), path)
            self.assertGreater(os.stat(_fs_path(path)).st_size, 500, path)

        with open(_fs_path(self.output_dir / "official_external_repo_snapshot.json"), encoding="utf-8") as handle:
            payload = json.load(handle)
        self.assertEqual(payload["overall_status"], "official_repo_snapshot_partial")
        self.assertTrue(all(row["snapshot_status"] == "source_only_unresolved" for row in payload["rows"]))


if __name__ == "__main__":
    unittest.main()
