from __future__ import annotations

import argparse
import hashlib
import json
import os
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score


VERSION = "skab-official-repository-baseline-audit-v1"


def _find_repo_root() -> Path:
    """Prefer the active workspace over a resolved symlink target."""
    module_root = Path(__file__).absolute().parents[1]
    resolved_root = Path(__file__).resolve().parents[1]
    cwd = Path.cwd()
    candidates: list[Path] = []
    env_root = os.environ.get("AAAI_WORK_ROOT")
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([cwd, cwd.parent, module_root, resolved_root])
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate.absolute()).lower()
        if key in seen:
            continue
        seen.add(key)
        skab_dir = candidate / "knowledge_exports" / "public_datasets" / "skab" / "raw" / "extracted" / "SKAB-master"
        if skab_dir.exists():
            return candidate
    return module_root


REPO_ROOT = _find_repo_root()
DEFAULT_SKAB_REPO = REPO_ROOT / "knowledge_exports" / "public_datasets" / "skab" / "raw" / "extracted" / "SKAB-master"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "knowledge_exports" / "aaai_exact_native_protocol_gate"
RECORD_DIR_NAME = "skab_official_repository_baseline_records"

EXPECTED_OUTLIER_LEADERBOARD = {
    "Conv_AE": {"leaderboard_name": "Conv-AE", "f1": 0.78, "far_percent": 13.55, "mar_percent": 28.02},
    "MSET": {"leaderboard_name": "MSET", "f1": 0.78, "far_percent": 39.73, "mar_percent": 14.13},
    "T2-q": {"leaderboard_name": "T-squared+Q (PCA-based)", "f1": 0.76, "far_percent": 26.62, "mar_percent": 24.92},
    "LSTM_AE": {"leaderboard_name": "LSTM-AE", "f1": 0.74, "far_percent": 29.96, "mar_percent": 25.92},
    "T2": {"leaderboard_name": "T-squared", "f1": 0.66, "far_percent": 19.21, "mar_percent": 42.60},
    "Vanilla_LSTM": {"leaderboard_name": "Vanilla LSTM", "f1": 0.54, "far_percent": 12.54, "mar_percent": 59.53},
    "MSCRED": {"leaderboard_name": "MSCRED", "f1": 0.36, "far_percent": 49.94, "mar_percent": 69.88},
    "Vanilla_AE": {"leaderboard_name": "Vanilla AE", "f1": 0.39, "far_percent": 2.59, "mar_percent": 75.15},
    "Isolation_Forest": {"leaderboard_name": "Isolation forest", "f1": 0.29, "far_percent": 2.56, "mar_percent": 82.89},
}


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    os.makedirs(_fs_path(path.parent), exist_ok=True)
    with open(_fs_path(path), "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def _write_text(path: Path, text: str) -> None:
    os.makedirs(_fs_path(path.parent), exist_ok=True)
    with open(_fs_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(_fs_path(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _method_from_pickle(path: Path) -> str:
    return path.stem.replace("results-", "")


def _load_data_frames(skab_repo: Path) -> list[tuple[Path, pd.DataFrame]]:
    data_dir = skab_repo / "data"
    frames: list[tuple[Path, pd.DataFrame]] = []
    for path in sorted(data_dir.glob("*/*.csv")):
        if path.name == "anomaly-free.csv":
            continue
        frame = pd.read_csv(_fs_path(path), sep=";")
        frame["_datetime_key"] = pd.to_datetime(frame["datetime"]).astype(str)
        frames.append((path, frame))
    return frames


def _best_frame_for_series(series: pd.Series, frames: list[tuple[Path, pd.DataFrame]]) -> tuple[Path, pd.DataFrame, int]:
    keys = set(pd.to_datetime(series.index).astype(str))
    best_path: Path | None = None
    best_frame: pd.DataFrame | None = None
    best_overlap = -1
    for path, frame in frames:
        overlap = int(frame["_datetime_key"].isin(keys).sum())
        if overlap > best_overlap:
            best_path = path
            best_frame = frame
            best_overlap = overlap
    if best_path is None or best_frame is None or best_overlap <= 0:
        raise ValueError("Unable to align official SKAB prediction series to any raw CSV by datetime.")
    return best_path, best_frame, best_overlap


def _records_for_method(pickle_path: Path, frames: list[tuple[Path, pd.DataFrame]], skab_repo: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    with open(_fs_path(pickle_path), "rb") as handle:
        series_list = pickle.load(handle)
    records: list[dict[str, Any]] = []
    alignment_rows: list[dict[str, Any]] = []
    for series_index, series in enumerate(series_list):
        if not isinstance(series, pd.Series):
            raise TypeError(f"{pickle_path.name} item {series_index} is not a pandas Series.")
        source_path, frame, overlap = _best_frame_for_series(series, frames)
        pred_series = pd.Series(
            np.nan_to_num(np.asarray(series), nan=0.0),
            index=pd.to_datetime(series.index).astype(str),
        )
        aligned = frame[frame["_datetime_key"].isin(pred_series.index)].copy()
        y_pred = aligned["_datetime_key"].map(pred_series).fillna(0.0).to_numpy(dtype=float)
        rel_source = str(source_path.relative_to(skab_repo / "data")).replace("\\", "/")
        alignment_rows.append(
            {
                "series_index": int(series_index),
                "source_file": rel_source,
                "series_rows": int(len(series)),
                "matched_rows": int(len(aligned)),
                "overlap_rows": int(overlap),
            }
        )
        for row_index, (_, row) in enumerate(aligned.iterrows()):
            run_id = rel_source.replace("/", "_").replace(".csv", "")
            sample_index = int(row.name) if isinstance(row.name, (int, np.integer)) else row_index
            pred = int(float(y_pred[row_index]) > 0.0)
            true = int(float(row.get("anomaly", 0.0)) > 0.0)
            records.append(
                {
                    "row_index": int(len(records)),
                    "record_id": f"official_skab_{run_id}_{sample_index:05d}",
                    "source_file": rel_source,
                    "datetime": str(row["datetime"]),
                    "y_true_original": true,
                    "y_pred_original": pred,
                    "positive_score": float(pred),
                    "positive_threshold": 0.5,
                    "run_id": run_id,
                    "sample_index": sample_index,
                    "run_group": str(source_path.parent.name),
                    "anomaly": true,
                    "changepoint": int(float(row.get("changepoint", 0.0)) > 0.0),
                }
            )
    return records, {"series_count": int(len(series_list)), "alignment_rows": alignment_rows}


def _metrics_from_records(records: list[dict[str, Any]]) -> dict[str, float]:
    y = np.asarray([int(record["y_true_original"]) for record in records], dtype=np.int64)
    pred = np.asarray([int(record["y_pred_original"]) for record in records], dtype=np.int64)
    fp = int(np.sum((pred == 1) & (y == 0)))
    fn = int(np.sum((pred == 0) & (y == 1)))
    negatives = int(np.sum(y == 0))
    positives = int(np.sum(y == 1))
    return {
        "f1": float(f1_score(y, pred, zero_division=0)),
        "far_percent": float(100.0 * fp / max(1, negatives)),
        "mar_percent": float(100.0 * fn / max(1, positives)),
        "positives": int(positives),
        "negatives": int(negatives),
        "false_positives": int(fp),
        "false_negatives": int(fn),
    }


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    os.makedirs(_fs_path(path.parent), exist_ok=True)
    with open(_fs_path(path), "w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def build_skab_official_repository_baseline_audit(
    skab_repo: Path | str = DEFAULT_SKAB_REPO,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    *,
    materialize_records: bool = True,
) -> dict[str, Any]:
    skab_repo = Path(skab_repo)
    output_dir = Path(output_dir)
    notebooks = sorted((skab_repo / "notebooks").glob("*.ipynb"))
    core_modules = sorted((skab_repo / "core").glob("*.py"))
    result_pickles = sorted((skab_repo / "results").glob("results-*.pkl"))
    frames = _load_data_frames(skab_repo) if skab_repo.exists() else []
    record_dir = output_dir / RECORD_DIR_NAME
    method_rows: list[dict[str, Any]] = []
    for pickle_path in result_pickles:
        method = _method_from_pickle(pickle_path)
        records, alignment = _records_for_method(pickle_path, frames, skab_repo)
        metrics = _metrics_from_records(records)
        record_file: Path | None = None
        record_sha: str | None = None
        if materialize_records:
            record_file = record_dir / f"{method}.jsonl"
            _write_jsonl(record_file, records)
            record_sha = _sha256(record_file)
        expected = EXPECTED_OUTLIER_LEADERBOARD.get(method)
        matches_expected = None
        if expected:
            matches_expected = (
                abs(metrics["f1"] - float(expected["f1"])) <= 0.01
                and abs(metrics["far_percent"] - float(expected["far_percent"])) <= 0.35
                and abs(metrics["mar_percent"] - float(expected["mar_percent"])) <= 0.35
            )
        method_rows.append(
            {
                "method": method,
                "leaderboard_name": (expected or {}).get("leaderboard_name"),
                "result_pickle": str(pickle_path.relative_to(skab_repo)),
                "n_prediction_series": alignment["series_count"],
                "n_prediction_records": int(len(records)),
                "all_series_aligned": all(
                    int(row["series_rows"]) == int(row["matched_rows"]) == int(row["overlap_rows"])
                    for row in alignment["alignment_rows"]
                ),
                "metrics": metrics,
                "expected_leaderboard": expected,
                "matches_expected_leaderboard": matches_expected,
                "record_file": str(record_file.relative_to(output_dir)) if record_file else None,
                "record_sha256": record_sha,
            }
        )
    official_methods = [row for row in method_rows if row["expected_leaderboard"]]
    gates = {
        "official_skab_repository_extracted": skab_repo.exists(),
        "official_notebooks_present": len(notebooks) >= 10,
        "official_core_modules_present": len(core_modules) >= 10,
        "official_result_pickles_present": len(result_pickles) >= 10,
        "official_result_pickles_align_to_raw_data": bool(method_rows) and all(row["all_series_aligned"] for row in method_rows),
        "official_outlier_leaderboard_recomputed": bool(official_methods) and all(row["matches_expected_leaderboard"] for row in official_methods),
        "official_frozen_prediction_records_materialized": bool(method_rows)
        and all(row["record_file"] and row["record_sha256"] for row in method_rows),
        "official_notebooks_rerun_from_source": False,
    }
    missing = [name for name, value in gates.items() if not value]
    return {
        "version": VERSION,
        "status": "official_skab_precomputed_baseline_audit_complete" if not missing else "official_skab_precomputed_baseline_audit_partial",
        "claim_boundary": (
            "This audit recomputes SKAB official outlier leaderboard rows from official repository result pickles "
            "and materializes frozen prediction records. It does not prove that notebooks were rerun from source."
        ),
        "skab_repo": str(skab_repo),
        "notebook_count": len(notebooks),
        "core_module_count": len(core_modules),
        "result_pickle_count": len(result_pickles),
        "record_dir": str(record_dir.relative_to(output_dir)),
        "gates": gates,
        "missing_gates": missing,
        "method_rows": method_rows,
        "next_actions": [
            "Rerun the official notebooks or core modules in a pinned environment to close the source-rerun gate.",
            "Decide whether the paper compares against official precomputed SKAB leaderboard rows or the project train/validation/test split; do not mix them as one protocol.",
            "If using the project split, port the official notebook methods into the same split/preprocessing/budget contract and archive seed-level frozen predictions.",
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# SKAB Official Repository Baseline Audit",
        "",
        f"- Version: {payload['version']}",
        f"- Status: {payload['status']}",
        f"- Claim boundary: {payload['claim_boundary']}",
        f"- Notebook count: {payload['notebook_count']}",
        f"- Core module count: {payload['core_module_count']}",
        f"- Result pickle count: {payload['result_pickle_count']}",
        "",
        "## Gates",
        "",
        "| Gate | Status |",
        "|---|---:|",
    ]
    for gate, value in payload["gates"].items():
        lines.append(f"| {gate} | {'pass' if value else 'blocked'} |")
    lines.extend(
        [
            "",
            "## Official Outlier Rows",
            "",
            "| Method | Records | F1 | FAR | MAR | README match | Frozen record file |",
            "|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in payload["method_rows"]:
        metrics = row["metrics"]
        match = row["matches_expected_leaderboard"]
        lines.append(
            "| {method} | {records} | {f1:.4f} | {far:.2f} | {mar:.2f} | {match} | `{record}` |".format(
                method=row["method"],
                records=int(row["n_prediction_records"]),
                f1=float(metrics["f1"]),
                far=float(metrics["far_percent"]),
                mar=float(metrics["mar_percent"]),
                match="n/a" if match is None else ("yes" if match else "no"),
                record=row["record_file"] or "",
            )
        )
    lines.extend(["", "## Next Actions", ""])
    lines.extend(f"- {action}" for action in payload["next_actions"])
    lines.append("")
    return "\n".join(lines)


def write_skab_official_repository_baseline_audit(
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    *,
    skab_repo: Path | str = DEFAULT_SKAB_REPO,
) -> list[Path]:
    output_dir = Path(output_dir)
    payload = build_skab_official_repository_baseline_audit(skab_repo=skab_repo, output_dir=output_dir)
    json_path = output_dir / "skab_official_repository_baseline_audit.json"
    md_path = output_dir / "skab_official_repository_baseline_audit.md"
    _write_json(json_path, payload)
    _write_text(md_path, render_markdown(payload))
    return [json_path, md_path]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Audit official SKAB repository baseline artifacts.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--skab-repo", type=Path, default=DEFAULT_SKAB_REPO)
    args = parser.parse_args(argv)
    for path in write_skab_official_repository_baseline_audit(args.output_dir, skab_repo=args.skab_repo):
        print(path)


if __name__ == "__main__":
    main()
