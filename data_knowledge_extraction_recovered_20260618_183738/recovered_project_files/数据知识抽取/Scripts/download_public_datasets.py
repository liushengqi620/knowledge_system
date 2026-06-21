from __future__ import annotations

import argparse
import json
import os
import shutil
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASET_ROOT = PROJECT_ROOT / "knowledge_exports" / "public_datasets"
DEFAULT_TEP_LEGACY_DIR = (
    PROJECT_ROOT
    / "\u6570\u636e\u96c6"
    / "\u6d41\u7a0b\u5de5\u4e1a\u7530\u7eb3\u897f\u5316\u5de5\u8fc7\u7a0b\u6545\u969c\u8bca\u65ad\u4e0e\u5206\u6790\u6570\u636e\u96c6"
)


DATASET_SOURCES: dict[str, dict[str, str]] = {
    "tep": {
        "url": "https://github.com/jkitchin/tennessee-eastman-profbraatz/archive/refs/heads/master.zip",
        "archive": "tennessee-eastman-profbraatz-master.zip",
        "note": "Classic Prof. Braatz TEP .dat files used by the existing TEP adapter.",
    },
    "skab": {
        "url": "https://github.com/waico/SKAB/archive/refs/heads/master.zip",
        "archive": "skab-master.zip",
        "note": "Official SKAB GitHub repository containing the v0.9 CSV data folder.",
    },
    "hydraulic": {
        "url": "https://archive.ics.uci.edu/static/public/447/condition+monitoring+of+hydraulic+systems.zip",
        "archive": "condition_monitoring_of_hydraulic_systems.zip",
        "note": "UCI Condition Monitoring of Hydraulic Systems dataset.",
    },
    "cmapss": {
        "url": "https://zenodo.org/records/15346912/files/CMAPSSData.zip?download=1",
        "archive": "CMAPSSData.zip",
        "note": "Zenodo archive of the NASA PCoE C-MAPSS turbofan degradation data. NASA's current catalog page reports the legacy download as unavailable.",
    },
}

TEP_DAT_MIRROR_BASE = "https://huggingface.co/spaces/jkitchin/tennessee-eastman-process/resolve/main"


def _tep_dat_names() -> list[str]:
    names: list[str] = []
    for i in range(22):
        names.append(f"d{i:02d}.dat")
        names.append(f"d{i:02d}_te.dat")
    return names


def _fs_path(path: Path) -> str:
    text = str(path)
    if os.name == "nt":
        resolved = str(path.resolve())
        if not resolved.startswith("\\\\?\\"):
            return "\\\\?\\" + resolved
    return text


def _exists(path: Path) -> bool:
    return os.path.exists(_fs_path(path))


def _size(path: Path) -> int:
    return int(os.stat(_fs_path(path)).st_size)


def _download(url: str, destination: Path, *, force: bool) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if _exists(destination) and not force and _size(destination) > 0:
        return {"path": str(destination), "status": "already_exists", "bytes": _size(destination)}
    tmp = destination.with_suffix(destination.suffix + ".tmp")
    if _exists(tmp):
        os.unlink(_fs_path(tmp))
    with urllib.request.urlopen(url, timeout=120) as response, open(_fs_path(tmp), "wb") as fh:
        shutil.copyfileobj(response, fh)
    Path(_fs_path(tmp)).replace(_fs_path(destination))
    return {"path": str(destination), "status": "downloaded", "bytes": _size(destination)}


def _extract_zip(archive: Path, output_dir: Path, *, force: bool) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    marker = output_dir / ".extract_complete"
    if _exists(marker) and not force:
        return {"path": str(output_dir), "status": "already_extracted"}
    if force and _exists(output_dir):
        for child in output_dir.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    with zipfile.ZipFile(_fs_path(archive)) as zf:
        zf.extractall(_fs_path(output_dir))
    with open(_fs_path(marker), "w", encoding="utf-8") as fh:
        fh.write("ok\n")
    return {"path": str(output_dir), "status": "extracted"}


def _copy_tep_dat_files(extract_dir: Path, legacy_dir: Path, *, force: bool) -> dict[str, Any]:
    dat_files = sorted(extract_dir.rglob("d*.dat"))
    if not dat_files:
        return {"status": "missing_dat_files", "copied": 0, "legacy_dir": str(legacy_dir)}
    train_dir = legacy_dir / "\u8bad\u7ec3\u96c6"
    test_dir = legacy_dir / "\u6d4b\u8bd5\u96c6"
    train_dir.mkdir(parents=True, exist_ok=True)
    test_dir.mkdir(parents=True, exist_ok=True)
    copied = 0
    for src in dat_files:
        dst = test_dir / src.name if src.name.lower().endswith("_te.dat") else train_dir / src.name
        if dst.exists() and not force:
            continue
        shutil.copy2(src, dst)
        copied += 1
    return {
        "status": "copied",
        "copied": int(copied),
        "train_files": int(len(list(train_dir.glob("d*.dat")))),
        "test_files": int(len(list(test_dir.glob("d*_te.dat")))),
        "legacy_dir": str(legacy_dir),
    }


def _download_tep_dat_mirror(raw_dir: Path, legacy_dir: Path, *, force: bool) -> dict[str, Any]:
    mirror_dir = Path(raw_dir) / "dat_files"
    mirror_dir.mkdir(parents=True, exist_ok=True)
    train_dir = Path(legacy_dir) / "\u8bad\u7ec3\u96c6"
    test_dir = Path(legacy_dir) / "\u6d4b\u8bd5\u96c6"
    train_dir.mkdir(parents=True, exist_ok=True)
    test_dir.mkdir(parents=True, exist_ok=True)
    downloaded = 0
    copied = 0
    errors: list[dict[str, str]] = []
    for name in _tep_dat_names():
        url = f"{TEP_DAT_MIRROR_BASE}/{name}"
        dst = mirror_dir / name
        try:
            status = _download(url, dst, force=force)
            if status["status"] == "downloaded":
                downloaded += 1
            target = (test_dir if name.endswith("_te.dat") else train_dir) / name
            if not _exists(target) or force:
                shutil.copy2(_fs_path(dst), _fs_path(target))
                copied += 1
        except Exception as exc:  # keep downloading other files if one mirror request fails
            errors.append({"file": name, "error": str(exc)})
    return {
        "status": "ok" if not errors else "partial",
        "mirror_base": TEP_DAT_MIRROR_BASE,
        "downloaded": int(downloaded),
        "copied": int(copied),
        "train_files": int(len(list(train_dir.glob("d*.dat")))),
        "test_files": int(len(list(test_dir.glob("d*_te.dat")))),
        "errors": errors,
    }


def _normalize_dataset_names(raw: Iterable[str]) -> list[str]:
    values = [item.strip().lower() for part in raw for item in str(part).split(",") if item.strip()]
    if not values or "all" in values:
        return list(DATASET_SOURCES)
    unknown = sorted(set(values) - set(DATASET_SOURCES))
    if unknown:
        raise ValueError(f"Unknown datasets: {unknown}. Known: {sorted(DATASET_SOURCES)}")
    return values


def _read_existing_manifest(path: Path) -> dict[str, Any]:
    if not _exists(path):
        return {}
    try:
        with open(_fs_path(path), "r", encoding="utf-8") as fh:
            loaded = json.load(fh)
        return loaded if isinstance(loaded, dict) else {}
    except Exception:
        return {}


def download_public_datasets(
    datasets: Iterable[str],
    *,
    dataset_root: Path = DEFAULT_DATASET_ROOT,
    tep_legacy_dir: Path = DEFAULT_TEP_LEGACY_DIR,
    force: bool = False,
) -> dict[str, Any]:
    selected = _normalize_dataset_names(datasets)
    results: dict[str, Any] = {}
    for name in selected:
        source = DATASET_SOURCES[name]
        raw_dir = Path(dataset_root) / name / "raw"
        archive = raw_dir / source["archive"]
        extract_dir = raw_dir / "extracted"
        download = _download(source["url"], archive, force=force)
        extract = _extract_zip(archive, extract_dir, force=force)
        result: dict[str, Any] = {
            "source_url": source["url"],
            "source_note": source["note"],
            "archive": download,
            "extract": extract,
        }
        if name == "tep":
            result["legacy_dat_copy"] = _copy_tep_dat_files(extract_dir, Path(tep_legacy_dir), force=force)
            if int(result["legacy_dat_copy"].get("train_files", 0)) < 22 or int(result["legacy_dat_copy"].get("test_files", 0)) < 22:
                result["tep_dat_mirror"] = _download_tep_dat_mirror(raw_dir, Path(tep_legacy_dir), force=force)
        results[name] = result
    manifest_path = Path(dataset_root) / "download_manifest.json"
    previous = _read_existing_manifest(manifest_path)
    merged_datasets = dict(previous.get("datasets", {})) if isinstance(previous.get("datasets", {}), dict) else {}
    merged_datasets.update(results)
    manifest = {
        "dataset_root": str(dataset_root),
        "tep_legacy_dir": str(tep_legacy_dir),
        "datasets": merged_datasets,
    }
    Path(dataset_root).mkdir(parents=True, exist_ok=True)
    with open(_fs_path(manifest_path), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Download public datasets used by the AAAI experiments.")
    parser.add_argument("--datasets", nargs="*", default=["all"], help="Comma-separated names or list: tep, skab, hydraulic, cmapss, all.")
    parser.add_argument("--dataset-root", default=str(DEFAULT_DATASET_ROOT))
    parser.add_argument("--tep-legacy-dir", default=str(DEFAULT_TEP_LEGACY_DIR))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    manifest = download_public_datasets(
        args.datasets,
        dataset_root=Path(args.dataset_root),
        tep_legacy_dir=Path(args.tep_legacy_dir),
        force=bool(args.force),
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
