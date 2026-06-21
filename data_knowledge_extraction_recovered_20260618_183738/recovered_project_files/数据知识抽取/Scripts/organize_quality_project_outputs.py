from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_ROOT = ROOT / "archive"
EXPORT_ROOT = ROOT / "knowledge_exports"

TEMP_DIR_NAMES = {
    "tmpf0gf9x2z",
    "tmplpaksk1z",
    "tmp_docx_render",
    "tmp_docx_temp",
    "tmp_tests",
}

LOOSE_EXPORT_SUFFIXES = {
    ".json",
    ".csv",
    ".npy",
    ".log",
}

KEEP_EXPORT_FILE_NAMES = {
    "README.md",
}


def is_inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def unique_destination(base: Path, name: str) -> Path:
    candidate = base / name
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    suffix = candidate.suffix
    for idx in range(1, 1000):
        next_candidate = base / f"{stem}_{idx}{suffix}"
        if not next_candidate.exists():
            return next_candidate
    raise RuntimeError(f"Cannot create unique destination for {candidate}")


def move_path(src: Path, dst_dir: Path, execute: bool) -> dict[str, str]:
    if not is_inside(src, ROOT):
        raise RuntimeError(f"Refuse to move path outside workspace: {src}")
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = unique_destination(dst_dir, src.name)
    item = {
        "source": str(src),
        "destination": str(dst),
        "status": "planned",
    }
    if execute:
        shutil.move(str(src), str(dst))
        item["status"] = "moved"
    return item


def collect_temp_dirs() -> list[Path]:
    return [
        path
        for path in ROOT.iterdir()
        if path.is_dir() and path.name in TEMP_DIR_NAMES
    ]


def collect_word_locks() -> list[Path]:
    return [
        path
        for path in ROOT.iterdir()
        if path.is_file() and path.name.startswith("~$") and path.suffix.lower() == ".docx"
    ]


def collect_loose_export_results() -> list[Path]:
    if not EXPORT_ROOT.exists():
        return []
    files: list[Path] = []
    for path in EXPORT_ROOT.iterdir():
        if not path.is_file():
            continue
        if path.name in KEEP_EXPORT_FILE_NAMES:
            continue
        if path.suffix.lower() in LOOSE_EXPORT_SUFFIXES or path.name.endswith(".summary.csv"):
            files.append(path)
    return sorted(files, key=lambda item: item.name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="Actually move files. Without it, only preview.")
    args = parser.parse_args()

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    cleanup_root = ARCHIVE_ROOT / f"cleanup_{stamp}"

    manifest: dict[str, object] = {
        "workspace": str(ROOT),
        "execute": bool(args.execute),
        "cleanup_root": str(cleanup_root),
        "moved": [],
        "errors": [],
    }

    groups = [
        ("root_temp_dirs", collect_temp_dirs(), cleanup_root / "root_temp_dirs"),
        ("root_word_locks", collect_word_locks(), cleanup_root / "root_word_locks"),
        (
            "knowledge_exports_loose_results",
            collect_loose_export_results(),
            cleanup_root / "knowledge_exports_loose_results",
        ),
    ]

    for group_name, paths, dst_dir in groups:
        for src in paths:
            try:
                item = move_path(src, dst_dir, args.execute)
                item["group"] = group_name
                manifest["moved"].append(item)
            except Exception as exc:  # Keep cleanup best-effort and auditable.
                manifest["errors"].append(
                    {
                        "group": group_name,
                        "source": str(src),
                        "error": str(exc),
                    }
                )

    if args.execute:
        cleanup_root.mkdir(parents=True, exist_ok=True)
        manifest_path = cleanup_root / "cleanup_manifest.json"
    else:
        ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)
        manifest_path = ARCHIVE_ROOT / f"cleanup_preview_{stamp}.json"
    manifest["manifest_path"] = str(manifest_path)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
