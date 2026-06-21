from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd

from public_benchmark_experiment import DEFAULT_PUBLIC_DATASET_ROOT, load_skab_dataset, split_skab_runs


VERSION = "anomaly-transformer-official-skab-adapter-v1"
CHECKED_ON = "2026-06-21"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = (
    PROJECT_ROOT
    / "knowledge_exports"
    / "external_baseline_protocol_runs"
    / "anomaly_transformer_official_skab_adapter"
)
DEFAULT_OFFICIAL_CHECKOUT = Path.home() / "aaai_external_baseline_checkouts" / "anomaly_transformer"
ANOMALY_TRANSFORMER_COMMIT = "b0ee470c8012"


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _split_ints(raw: str | Sequence[int]) -> list[int]:
    if isinstance(raw, str):
        values = [int(part.strip()) for part in raw.replace(";", ",").split(",") if part.strip()]
    else:
        values = [int(item) for item in raw]
    return values or [42]


def _feature_frame(x_raw: pd.DataFrame) -> pd.DataFrame:
    exclude = {"run_id", "run_group", "sample_index", "record_id"}
    cols = [col for col in x_raw.columns if col not in exclude]
    out = pd.DataFrame(index=x_raw.index)
    for col in cols:
        numeric = pd.to_numeric(x_raw[col], errors="coerce")
        if numeric.notna().any():
            out[col] = numeric
    if out.empty:
        raise ValueError("No numeric SKAB feature columns were found.")
    return out.replace([np.inf, -np.inf], np.nan).fillna(0.0).astype(np.float32)


def _write_official_feature_csv(path: Path, features: pd.DataFrame) -> None:
    os.makedirs(_fs_path(path.parent), exist_ok=True)
    frame = features.reset_index(drop=True).copy()
    frame.insert(0, "timestamp", np.arange(len(frame), dtype=np.int64))
    frame.to_csv(_fs_path(path), index=False)


def _write_label_csv(path: Path, labels: np.ndarray) -> None:
    os.makedirs(_fs_path(path.parent), exist_ok=True)
    frame = pd.DataFrame(
        {
            "timestamp": np.arange(len(labels), dtype=np.int64),
            "label": np.asarray(labels, dtype=np.int64).reshape(-1),
        }
    )
    frame.to_csv(_fs_path(path), index=False)


def _write_meta_csv(path: Path, meta: pd.DataFrame, mask: np.ndarray) -> None:
    os.makedirs(_fs_path(path.parent), exist_ok=True)
    columns = ["run_id", "run_group", "source_file", "sample_index", "anomaly", "changepoint"]
    keep = [col for col in columns if col in meta.columns]
    frame = meta.loc[mask, keep].reset_index(drop=True).copy()
    frame.insert(0, "timestamp", np.arange(len(frame), dtype=np.int64))
    frame.to_csv(_fs_path(path), index=False)


def _window_count(n_rows: int, win_size: int, *, step: int) -> int:
    if int(n_rows) < int(win_size):
        return 0
    return (int(n_rows) - int(win_size)) // int(step) + 1


def _commands(adapter_dir: Path, output_dir: Path, input_c: int, win_size: int, batch_size: int, epochs: int) -> dict[str, str]:
    checkout = DEFAULT_OFFICIAL_CHECKOUT
    checkpoint_dir = output_dir / "official_checkpoints"
    base = (
        "python main.py --dataset PSM --data_path {data_path} --input_c {input_c} "
        "--output_c {input_c} --win_size {win_size} --batch_size {batch_size} "
        "--model_save_path {checkpoint_dir}"
    ).format(
        data_path=str(adapter_dir),
        input_c=int(input_c),
        win_size=int(win_size),
        batch_size=int(batch_size),
        checkpoint_dir=str(checkpoint_dir),
    )
    return {
        "official_unmodified_train_command": f"cd {checkout} && {base} --num_epochs {int(epochs)} --mode train",
        "official_unmodified_test_command": f"cd {checkout} && {base} --mode test",
        "required_matched_wrapper": (
            "patch Solver.train to validate on val.csv, patch Solver.test to tune thresholds on val scores only, "
            "emit raw validation/test scores and disable label-based point adjustment unless explicitly reported"
        ),
    }


def prepare_one_seed(
    dataset_root: Path,
    output_dir: Path,
    *,
    seed: int,
    win_size: int,
    batch_size: int,
    epochs: int,
    train_normals_only: bool = True,
) -> dict[str, Any]:
    x_raw, y, meta = load_skab_dataset(dataset_root)
    features = _feature_frame(x_raw)
    train_runs, val_runs, test_runs = split_skab_runs(meta, seed=int(seed), test_size=0.30, val_fraction=0.25)
    run_series = meta["run_id"].astype(str)
    train_mask = run_series.isin(train_runs).to_numpy(dtype=bool)
    val_mask = run_series.isin(val_runs).to_numpy(dtype=bool)
    test_mask = run_series.isin(test_runs).to_numpy(dtype=bool)
    if train_normals_only:
        train_mask = train_mask & (np.asarray(y, dtype=np.int64) == 0)

    adapter_dir = output_dir / f"seed_{int(seed)}" / "psm_compatible"
    seed_dir = output_dir / f"seed_{int(seed)}"
    _write_official_feature_csv(adapter_dir / "train.csv", features.loc[train_mask])
    _write_official_feature_csv(adapter_dir / "test.csv", features.loc[test_mask])
    _write_label_csv(adapter_dir / "test_label.csv", np.asarray(y, dtype=np.int64)[test_mask])
    _write_official_feature_csv(adapter_dir / "val.csv", features.loc[val_mask])
    _write_label_csv(adapter_dir / "val_label.csv", np.asarray(y, dtype=np.int64)[val_mask])
    _write_meta_csv(adapter_dir / "train_meta.csv", meta, train_mask)
    _write_meta_csv(adapter_dir / "val_meta.csv", meta, val_mask)
    _write_meta_csv(adapter_dir / "test_meta.csv", meta, test_mask)

    row_counts = {
        "train_rows": int(np.sum(train_mask)),
        "val_rows": int(np.sum(val_mask)),
        "test_rows": int(np.sum(test_mask)),
        "train_positive_rows": int(np.sum(np.asarray(y, dtype=np.int64)[train_mask] == 1)),
        "val_positive_rows": int(np.sum(np.asarray(y, dtype=np.int64)[val_mask] == 1)),
        "test_positive_rows": int(np.sum(np.asarray(y, dtype=np.int64)[test_mask] == 1)),
    }
    window_counts = {
        "official_train_windows_step1": _window_count(row_counts["train_rows"], win_size, step=1),
        "official_test_windows_step1": _window_count(row_counts["test_rows"], win_size, step=1),
        "official_thre_windows_step_win_size": _window_count(row_counts["test_rows"], win_size, step=win_size),
        "patched_val_windows_step1": _window_count(row_counts["val_rows"], win_size, step=1),
    }
    manifest = {
        "version": VERSION,
        "checked_on": CHECKED_ON,
        "seed": int(seed),
        "dataset": "SKAB",
        "official_baseline": "Anomaly Transformer",
        "official_checkout": str(DEFAULT_OFFICIAL_CHECKOUT),
        "official_commit": ANOMALY_TRANSFORMER_COMMIT,
        "adapter_format": "PSM-compatible CSV plus validation CSV extension",
        "adapter_dir": str(adapter_dir),
        "train_policy": "normal rows from training runs only" if train_normals_only else "all rows from training runs",
        "feature_columns": list(map(str, features.columns)),
        "input_c": int(features.shape[1]),
        "win_size": int(win_size),
        "batch_size": int(batch_size),
        "epochs": int(epochs),
        "train_runs": list(map(str, train_runs)),
        "val_runs": list(map(str, val_runs)),
        "test_runs": list(map(str, test_runs)),
        "row_counts": row_counts,
        "window_counts": window_counts,
        "files": {
            "train_csv": str(adapter_dir / "train.csv"),
            "val_csv": str(adapter_dir / "val.csv"),
            "val_label_csv": str(adapter_dir / "val_label.csv"),
            "test_csv": str(adapter_dir / "test.csv"),
            "test_label_csv": str(adapter_dir / "test_label.csv"),
            "train_meta_csv": str(adapter_dir / "train_meta.csv"),
            "val_meta_csv": str(adapter_dir / "val_meta.csv"),
            "test_meta_csv": str(adapter_dir / "test_meta.csv"),
        },
        "commands": _commands(adapter_dir, seed_dir, features.shape[1], win_size, batch_size, epochs),
        "protocol_alignment": {
            "official_unmodified_loader_usable": True,
            "official_external_score": False,
            "matched_protocol_score_ready": False,
            "requires_solver_patch": True,
            "validation_only_thresholds": "requires patched score path; official unmodified test uses train+test percentile",
            "point_adjustment": "official unmodified test uses label-based point adjustment; must be disabled or separately declared",
            "early_stopping": "official train currently validates on test_loader; matched wrapper must validate on val.csv",
            "claim_boundary": (
                "This artifact prepares official-source input files and commands only. It is not an official "
                "Anomaly Transformer score until the patched wrapper emits seed-level validation/test scores, "
                "threshold provenance, metrics, and budget records."
            ),
        },
    }
    os.makedirs(_fs_path(seed_dir), exist_ok=True)
    with open(_fs_path(seed_dir / "split_manifest.json"), "w", encoding="utf-8") as handle:
        handle.write(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return manifest


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Anomaly Transformer Official SKAB Adapter",
        "",
        f"- Version: {payload['version']}",
        f"- Overall status: {payload['overall_status']}",
        f"- Claim boundary: {payload['claim_boundary']}",
        "",
        "| Seed | Input C | Train rows | Val rows | Test rows | Train positives | Val positives | Test positives | Matched ready |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in payload["seeds"]:
        counts = row["row_counts"]
        lines.append(
            "| {seed} | {input_c} | {train_rows} | {val_rows} | {test_rows} | {train_pos} | {val_pos} | {test_pos} | {ready} |".format(
                seed=row["seed"],
                input_c=row["input_c"],
                train_rows=counts["train_rows"],
                val_rows=counts["val_rows"],
                test_rows=counts["test_rows"],
                train_pos=counts["train_positive_rows"],
                val_pos=counts["val_positive_rows"],
                test_pos=counts["test_positive_rows"],
                ready=row["protocol_alignment"]["matched_protocol_score_ready"],
            )
        )
    lines.extend(["", "## Protocol Risks", ""])
    risks = [
        "official train validates on `test_loader` in `solver.py`",
        "official threshold is percentile over train and `thre_loader` test scores",
        "official point adjustment uses test labels to expand anomaly segments",
        "matched AAAI protocol therefore needs a patched wrapper before any score is admissible",
    ]
    lines.extend(f"- {risk}" for risk in risks)
    lines.append("")
    return "\n".join(lines)


def build_adapter_payload(
    dataset_root: Path,
    output_root: Path,
    *,
    seeds: Sequence[int],
    win_size: int,
    batch_size: int,
    epochs: int,
    train_normals_only: bool = True,
) -> dict[str, Any]:
    output_root = Path(output_root)
    seed_payloads = [
        prepare_one_seed(
            dataset_root,
            output_root,
            seed=int(seed),
            win_size=int(win_size),
            batch_size=int(batch_size),
            epochs=int(epochs),
            train_normals_only=bool(train_normals_only),
        )
        for seed in seeds
    ]
    return {
        "version": VERSION,
        "checked_on": CHECKED_ON,
        "overall_status": "official_source_adapter_prepared",
        "dataset_root": str(dataset_root),
        "output_root": str(output_root),
        "claim_boundary": "Prepared official-source adapter files only; exact official/matched protocol scores remain pending.",
        "seeds": seed_payloads,
    }


def write_adapter_artifacts(payload: dict[str, Any], output_root: Path) -> list[Path]:
    output_root = Path(output_root)
    os.makedirs(_fs_path(output_root), exist_ok=True)
    json_path = output_root / "anomaly_transformer_official_skab_adapter.json"
    md_path = output_root / "anomaly_transformer_official_skab_adapter.md"
    with open(_fs_path(json_path), "w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    with open(_fs_path(md_path), "w", encoding="utf-8") as handle:
        handle.write(render_markdown(payload))
    return [json_path, md_path]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Prepare SKAB files for the official Anomaly Transformer source tree.")
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_PUBLIC_DATASET_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--seeds", default="42")
    parser.add_argument("--win-size", type=int, default=48)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--include-anomalous-train-rows", action="store_true")
    args = parser.parse_args(argv)
    payload = build_adapter_payload(
        args.dataset_root,
        args.output_root,
        seeds=_split_ints(args.seeds),
        win_size=int(args.win_size),
        batch_size=int(args.batch_size),
        epochs=int(args.epochs),
        train_normals_only=not bool(args.include_anomalous_train_rows),
    )
    for path in write_adapter_artifacts(payload, args.output_root):
        print(path)


if __name__ == "__main__":
    main()
