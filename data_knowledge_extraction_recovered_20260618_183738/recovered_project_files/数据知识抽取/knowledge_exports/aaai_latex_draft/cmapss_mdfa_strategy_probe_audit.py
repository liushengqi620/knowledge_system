from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).absolute().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "knowledge_exports" / "aaai_exact_native_protocol_gate"
EXPORT_DIR = REPO_ROOT / "knowledge_exports"
VERSION = "cmapss-mdfa-strategy-probe-audit-v1"
PREVIOUS_FULL_SINGLE_CONDITION_ARCHIVE = EXPORT_DIR / "cmapss_mdfa_source_matched_single_condition_w80_all24_full"
FULL_SINGLE_CONDITION_ARCHIVE = EXPORT_DIR / "cmapss_mdfa_source_matched_single_condition_w80_all24_dropout01_full"
ZERO_DROPOUT_SINGLE_CONDITION_ARCHIVE = EXPORT_DIR / "cmapss_mdfa_source_matched_single_condition_w80_all24_dropout000_full"
TEMPORAL_LEVEL_DIFF_FD003_ARCHIVE = EXPORT_DIR / "cmapss_mdfa_fd003_leveldiff_full_seed42_43_44"
FULL_MULTI_CONDITION_ARCHIVE = EXPORT_DIR / "cmapss_mdfa_condition_full_fd002_fd004_sensor21_pca_kmeans_onehot"


PROBE_SPECS = [
    {
        "name": "legacy_temporal_1d_full_fd001",
        "role": "legacy_pre_source2d_calibration",
        "path": EXPORT_DIR / "cmapss_mdfa_source_matched_full",
        "claim_use": "historical diagnostic only",
    },
    {
        "name": "source2d_all24_pca_full_fd001",
        "role": "current_full_budget_candidate",
        "path": EXPORT_DIR / "cmapss_mdfa_source_matched_full_source2d",
        "subset": "FD001",
        "claim_use": "best current FD001 100-epoch calibration candidate",
    },
    {
        "name": "source2d_all24_pca_full_fd002_failed_multicondition",
        "role": "multicondition_failure_diagnostic",
        "path": EXPORT_DIR / "cmapss_mdfa_source_matched_full_source2d",
        "subset": "FD002",
        "claim_use": "diagnostic showing all24_pca is unsafe for multi-condition C-MAPSS",
    },
    {
        "name": "source2d_all24_pca_window80_fd001_full",
        "role": "single_condition_long_window_candidate",
        "path": EXPORT_DIR / "cmapss_mdfa_fd001_window80_full_all24_pca",
        "subset": "FD001",
        "claim_use": "FD001 100-epoch long-window single-condition candidate, single seed only",
    },
    {
        "name": "source2d_all24_pca_window80_dropout01_fd001_probe25",
        "role": "single_condition_low_dropout_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_fd001_w80_all24_dropout01_probe25",
        "subset": "FD001",
        "claim_use": "short-budget probe showing lower dropout improves the single-condition branch",
    },
    {
        "name": "source2d_all24_pca_window80_dropout01_fd001_full",
        "role": "single_condition_long_window_candidate",
        "path": EXPORT_DIR / "cmapss_mdfa_source_matched_single_condition_w80_all24_dropout01_full",
        "subset": "FD001",
        "claim_use": "FD001 100-epoch long-window low-dropout single-condition candidate, selected archive member",
    },
    {
        "name": "source2d_all24_pca_window30_fd003_failure",
        "role": "two_fault_mode_short_window_failure_diagnostic",
        "path": EXPORT_DIR / "cmapss_mdfa_source_matched_single_condition_full_source2d",
        "subset": "FD003",
        "claim_use": "diagnostic showing source window=30 is insufficient for FD003 two-fault-mode trajectories",
    },
    {
        "name": "source2d_common_sensors_pca_kmeans4_trajectory_fd003_negative",
        "role": "two_fault_mode_trajectory_cluster_negative",
        "path": EXPORT_DIR / "cmapss_mdfa_fd003_trajectory_probe_common_sensors_pca_kmeans4_onehot",
        "subset": "FD003",
        "claim_use": "negative diagnostic showing naive trajectory-family clustering is not validation-admitted",
    },
    {
        "name": "source2d_common_sensors_pca_window80_fd003_full",
        "role": "two_fault_mode_long_window_candidate",
        "path": EXPORT_DIR / "cmapss_mdfa_fd003_window80_full_common_sensors_pca",
        "subset": "FD003",
        "claim_use": "FD003 100-epoch long-window RMSE candidate, single seed only",
    },
    {
        "name": "source2d_all24_pca_window80_fd003_full",
        "role": "two_fault_mode_long_window_candidate",
        "path": EXPORT_DIR / "cmapss_mdfa_fd003_window80_full_all24_pca",
        "subset": "FD003",
        "claim_use": "FD003 100-epoch long-window balanced RMSE/Score candidate, single seed only",
    },
    {
        "name": "source2d_all24_pca_window80_dropout01_fd003_probe25",
        "role": "two_fault_mode_low_dropout_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_fd003_w80_all24_dropout01_probe25",
        "subset": "FD003",
        "claim_use": "short-budget probe showing lower dropout stabilizes the two-fault FD003 branch",
    },
    {
        "name": "source2d_all24_pca_window80_dropout01_fd003_full",
        "role": "two_fault_mode_long_window_candidate",
        "path": EXPORT_DIR / "cmapss_mdfa_source_matched_single_condition_w80_all24_dropout01_full",
        "subset": "FD003",
        "claim_use": "FD003 100-epoch long-window low-dropout two-fault candidate, selected archive member",
    },
    {
        "name": "source2d_all24_pca_window80_dropout005_fd001_probe25",
        "role": "single_condition_dropout_sensitivity_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_fd001_fd003_w80_all24_dropout005_probe25",
        "subset": "FD001",
        "claim_use": "short-budget dropout sensitivity probe; not selected after full-seed stability check",
    },
    {
        "name": "source2d_all24_pca_window80_dropout005_fd003_probe25",
        "role": "two_fault_mode_dropout_sensitivity_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_fd001_fd003_w80_all24_dropout005_probe25",
        "subset": "FD003",
        "claim_use": "short-budget dropout sensitivity probe showing FD003 benefits from lower dropout",
    },
    {
        "name": "source2d_all24_pca_window80_dropout000_fd001_probe25",
        "role": "single_condition_dropout_sensitivity_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_fd001_fd003_w80_all24_dropout000_probe25",
        "subset": "FD001",
        "claim_use": "short-budget zero-dropout probe; FD001 improves at seed42 but needs stability screening",
    },
    {
        "name": "source2d_all24_pca_window80_dropout000_fd003_probe25",
        "role": "two_fault_mode_dropout_sensitivity_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_fd001_fd003_w80_all24_dropout000_probe25",
        "subset": "FD003",
        "claim_use": "short-budget zero-dropout probe; best FD003 screening result",
    },
    {
        "name": "source2d_all24_pca_window80_dropout01_batch64_fd001_probe25",
        "role": "single_condition_batch_sensitivity_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_fd001_fd003_w80_all24_dropout01_batch64_probe25",
        "subset": "FD001",
        "claim_use": "short-budget batch-size probe; FD001 improves but FD003 regresses",
    },
    {
        "name": "source2d_all24_pca_window80_dropout01_batch64_fd003_probe25",
        "role": "two_fault_mode_batch_sensitivity_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_fd001_fd003_w80_all24_dropout01_batch64_probe25",
        "subset": "FD003",
        "claim_use": "short-budget batch-size negative probe for the two-fault FD003 subset",
    },
    {
        "name": "source2d_all24_pca_window80_dropout000_fd001_full",
        "role": "single_condition_zero_dropout_full_challenger",
        "path": EXPORT_DIR / "cmapss_mdfa_source_matched_single_condition_w80_all24_dropout000_full",
        "subset": "FD001",
        "claim_use": "100-epoch zero-dropout full challenger; not selected for FD001 because three-seed stability regresses",
    },
    {
        "name": "source2d_all24_pca_window80_dropout000_fd003_full",
        "role": "two_fault_mode_long_window_candidate",
        "path": EXPORT_DIR / "cmapss_mdfa_source_matched_single_condition_w80_all24_dropout000_full",
        "subset": "FD003",
        "claim_use": "100-epoch zero-dropout full challenger; selected for FD003 if three-seed mean remains better",
    },
    {
        "name": "source2d_all24_pca_window80_dropout01_leveldiff_fd001_probe25",
        "role": "temporal_velocity_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_fd001_leveldiff_probe25",
        "subset": "FD001",
        "claim_use": "level+first-difference temporal channel probe; FD001 regresses and therefore is not promoted",
    },
    {
        "name": "source2d_all24_pca_window80_dropout000_leveldiff_fd003_probe25",
        "role": "temporal_velocity_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_fd003_leveldiff_probe25",
        "subset": "FD003",
        "claim_use": "level+first-difference temporal channel probe; improves the FD003 two-fault screening run",
    },
    {
        "name": "source2d_all24_pca_window80_dropout000_leveldiff_fd003_full",
        "role": "two_fault_mode_long_window_candidate",
        "path": EXPORT_DIR / "cmapss_mdfa_fd003_leveldiff_full_seed42_43_44",
        "subset": "FD003",
        "claim_use": "100-epoch three-seed level+first-difference temporal channel challenger; selected for FD003 if it beats level-only zero dropout",
    },
    {
        "name": "source2d_sensor21_pca_kmeans_onehot_fd002_probe25",
        "role": "multicondition_condition_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_condition_probe_fd002_sensor21_pca_kmeans_onehot",
        "subset": "FD002",
        "claim_use": "short-budget screening for operating-condition-aware preprocessing",
    },
    {
        "name": "source2d_sensor21_pca_kmeans_onehot_fd002_full",
        "role": "multicondition_full_budget_candidate",
        "path": EXPORT_DIR / "cmapss_mdfa_condition_full_fd002_sensor21_pca_kmeans_onehot",
        "subset": "FD002",
        "claim_use": "FD002 100-epoch condition-aware candidate, single seed only",
    },
    {
        "name": "source2d_sensor21_pca_kmeans_onehot_fd004_probe25",
        "role": "multicondition_condition_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_condition_probe_fd004_sensor21_pca_kmeans_onehot",
        "subset": "FD004",
        "claim_use": "short-budget screening for operating-condition-aware preprocessing on the hardest multi-condition subset",
    },
    {
        "name": "source2d_sensor21_pca_kmeans_onehot_fd004_full",
        "role": "multicondition_full_budget_candidate",
        "path": EXPORT_DIR / "cmapss_mdfa_condition_full_fd004_sensor21_pca_kmeans_onehot",
        "subset": "FD004",
        "claim_use": "FD004 100-epoch condition-aware candidate, single seed only",
    },
    {
        "name": "source2d_settings_common_sensors_pca_full_fd001",
        "role": "feature_policy_full_budget_candidate",
        "path": EXPORT_DIR / "cmapss_mdfa_source_matched_full_source2d_settings_common_sensors_pca",
        "claim_use": "feature-policy challenger, not selected after 100-epoch calibration",
    },
    {
        "name": "source2d_all24_pca_probe25",
        "role": "feature_policy_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_feature_policy_probe_all24_pca",
        "claim_use": "short-budget screening only",
    },
    {
        "name": "source2d_all24_pca_pca090_fd001_probe25",
        "role": "pca_threshold_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_pca090_probe_all24_pca",
        "subset": "FD001",
        "claim_use": "PCA cumulative-contribution sensitivity probe; retained as low-threshold negative/control evidence",
    },
    {
        "name": "source2d_all24_pca_pca090_fd002_probe25",
        "role": "pca_threshold_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_pca090_probe_all24_pca",
        "subset": "FD002",
        "claim_use": "PCA cumulative-contribution sensitivity probe; retained as low-threshold negative/control evidence",
    },
    {
        "name": "source2d_all24_pca_pca090_fd003_probe25",
        "role": "pca_threshold_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_pca090_probe_all24_pca",
        "subset": "FD003",
        "claim_use": "PCA cumulative-contribution sensitivity probe; retained as low-threshold negative/control evidence",
    },
    {
        "name": "source2d_all24_pca_pca090_fd004_probe25",
        "role": "pca_threshold_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_pca090_probe_all24_pca",
        "subset": "FD004",
        "claim_use": "PCA cumulative-contribution sensitivity probe; retained as low-threshold negative/control evidence",
    },
    {
        "name": "source2d_all24_pca_cap150_raw_fd001_probe25",
        "role": "native_raw_rul_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_native_raw_probe_fd001_fd003_cap150",
        "subset": "FD001",
        "claim_use": "native/raw-test label-policy probe; cap150 raw scoring is not selected",
    },
    {
        "name": "source2d_all24_pca_cap150_raw_fd003_probe25",
        "role": "native_raw_rul_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_native_raw_probe_fd001_fd003_cap150",
        "subset": "FD003",
        "claim_use": "native/raw-test label-policy probe; cap150 raw scoring is not selected",
    },
    {
        "name": "source2d_sensor21_pca_kmeans_onehot_cap150_raw_fd002_probe25",
        "role": "native_raw_rul_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_native_raw_probe_fd002_fd004_cap150_condition",
        "subset": "FD002",
        "claim_use": "native/raw-test label-policy probe; improves over capped-output raw recomputation only slightly",
    },
    {
        "name": "source2d_sensor21_pca_kmeans_onehot_cap150_raw_fd004_probe25",
        "role": "native_raw_rul_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_native_raw_probe_fd002_fd004_cap150_condition",
        "subset": "FD004",
        "claim_use": "native/raw-test label-policy probe; improves over capped-output raw recomputation only slightly",
    },
    {
        "name": "source2d_mdfa_key_sensors_pca_fd001_probe25",
        "role": "table4_key_sensor_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_table4_key_sensors_probe25",
        "subset": "FD001",
        "claim_use": "source-aligned Table-4 key-sensor probe; retained as negative/control evidence",
    },
    {
        "name": "source2d_mdfa_key_sensors_pca_fd002_probe25",
        "role": "table4_key_sensor_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_table4_key_sensors_probe25",
        "subset": "FD002",
        "claim_use": "source-aligned Table-4 key-sensor probe; retained as negative/control evidence",
    },
    {
        "name": "source2d_mdfa_key_sensors_pca_fd003_probe25",
        "role": "table4_key_sensor_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_table4_key_sensors_probe25",
        "subset": "FD003",
        "claim_use": "source-aligned Table-4 key-sensor probe; retained as negative/control evidence",
    },
    {
        "name": "source2d_mdfa_key_sensors_pca_fd004_probe25",
        "role": "table4_key_sensor_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_table4_key_sensors_probe25",
        "subset": "FD004",
        "claim_use": "source-aligned Table-4 key-sensor probe; retained as negative/control evidence",
    },
    {
        "name": "source2d_sensor21_pca_probe25",
        "role": "feature_policy_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_feature_policy_probe_sensor21_pca",
        "claim_use": "short-budget screening only",
    },
    {
        "name": "source2d_common_sensors_raw_probe25",
        "role": "feature_policy_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_feature_policy_probe_common_sensors_raw",
        "claim_use": "short-budget screening only",
    },
    {
        "name": "source2d_common_sensors_pca_probe25",
        "role": "feature_policy_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_feature_policy_probe_common_sensors_pca",
        "claim_use": "short-budget screening only",
    },
    {
        "name": "source2d_settings_common_sensors_raw_probe25",
        "role": "feature_policy_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_feature_policy_probe_settings_common_sensors_raw",
        "claim_use": "short-budget screening only",
    },
    {
        "name": "source2d_settings_common_sensors_pca_probe25",
        "role": "feature_policy_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_feature_policy_probe_settings_common_sensors_pca",
        "claim_use": "short-budget screening only",
    },
    {
        "name": "source2d_reduce_on_plateau_probe25",
        "role": "lr_scheduler_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_lr_scheduler_probe_all24_pca",
        "claim_use": "short-budget scheduler screening only",
    },
    {
        "name": "source2d_val0_probe25",
        "role": "validation_split_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_val0_probe_all24_pca",
        "claim_use": "short-budget validation split screening only",
    },
    {
        "name": "source2d_all24_pca_window80_dropout000_affine_cal_fd001_probe25",
        "role": "validation_output_calibration_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_fd001_fd003_val_affine_probe25",
        "subset": "FD001",
        "claim_use": "validation-only affine output calibration probe; guard blocks calibration because validation RMSE gain is below threshold",
    },
    {
        "name": "source2d_all24_pca_window80_dropout000_affine_cal_fd003_probe25",
        "role": "validation_output_calibration_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_fd001_fd003_val_affine_probe25",
        "subset": "FD003",
        "claim_use": "validation-only affine output calibration probe; guard blocks calibration because validation RMSE gain is below threshold",
    },
    {
        "name": "source2d_all24_pca_window80_dropout01_snapshot_fd001_probe25",
        "role": "validation_snapshot_ensemble_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_fd001_snapshot_ensemble_probe25",
        "subset": "FD001",
        "claim_use": "validation-only checkpoint ensemble probe; guard blocks ensemble because validation RMSE regresses versus the best checkpoint",
    },
    {
        "name": "source2d_all24_pca_window80_dropout000_snapshot_fd003_probe25",
        "role": "validation_snapshot_ensemble_probe_25epoch",
        "path": EXPORT_DIR / "cmapss_mdfa_fd003_snapshot_ensemble_probe25",
        "subset": "FD003",
        "claim_use": "validation-only checkpoint ensemble probe; guard blocks ensemble because validation RMSE regresses versus the best checkpoint",
    },
]


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).absolute()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _read_json_if_present(path: Path) -> dict[str, Any] | None:
    if not os.path.exists(_fs_path(path)):
        return None
    with open(_fs_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    os.makedirs(_fs_path(path.parent), exist_ok=True)
    with open(_fs_path(path), "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def _write_text(path: Path, text: str) -> None:
    os.makedirs(_fs_path(path.parent), exist_ok=True)
    with open(_fs_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def _first_subset_payload(run_dir: Path, seed: int, subset: str) -> dict[str, Any] | None:
    direct = _read_json_if_present(run_dir / f"cmapss_mdfa_source_matched_seed{seed}_{subset}.json")
    if direct:
        return direct
    seed_payload = _read_json_if_present(run_dir / f"cmapss_mdfa_source_matched_seed{seed}.json")
    if not seed_payload:
        return None
    for item in seed_payload.get("subsets", []) or []:
        if str(item.get("subset")) == subset:
            return item
    return None


def _summary_path(run_dir: Path) -> Path:
    return run_dir / "cmapss_mdfa_source_matched_summary.json"


def _rul_metrics_from_records(records: list[dict[str, Any]], *, use_raw_truth: bool) -> dict[str, float] | None:
    if not records:
        return None
    truth_key = "rul_true_raw" if use_raw_truth else "rul_true"
    errors: list[float] = []
    abs_errors: list[float] = []
    score = 0.0
    for row in records:
        if truth_key not in row or "rul_pred" not in row:
            return None
        err = float(row["rul_pred"]) - float(row[truth_key])
        errors.append(err)
        abs_errors.append(abs(err))
        score += math.exp(-err / 13.0) - 1.0 if err < 0.0 else math.exp(err / 10.0) - 1.0
    mse = sum(err * err for err in errors) / max(1, len(errors))
    return {
        "rul_mae": float(sum(abs_errors) / max(1, len(abs_errors))),
        "rul_rmse": float(math.sqrt(mse)),
        "rul_score": float(score),
    }


def _full_archive_stats(run_dir: Path) -> dict[str, Any]:
    summary = _read_json_if_present(_summary_path(Path(run_dir))) or {}
    rows = summary.get("subset_seed_rows") if isinstance(summary.get("subset_seed_rows"), list) else []
    subset_stats: dict[str, dict[str, Any]] = {}
    for subset in sorted({str(row.get("subset")) for row in rows}):
        subset_rows = [row for row in rows if str(row.get("subset")) == subset]
        rmses = [float(row.get("rul_rmse", 0.0) or 0.0) for row in subset_rows]
        scores = [float(row.get("rul_score", 0.0) or 0.0) for row in subset_rows]
        raw_rmses: list[float] = []
        raw_scores: list[float] = []
        for row in subset_rows:
            payload = _first_subset_payload(Path(run_dir), int(row.get("seed", 42) or 42), subset) or {}
            records = payload.get("rul_prediction_records") if isinstance(payload.get("rul_prediction_records"), list) else []
            raw_metrics = _rul_metrics_from_records(records, use_raw_truth=True)
            if raw_metrics:
                raw_rmses.append(float(raw_metrics["rul_rmse"]))
                raw_scores.append(float(raw_metrics["rul_score"]))
        subset_stats[subset] = {
            "seeds": [int(row.get("seed", -1)) for row in subset_rows],
            "n": int(len(subset_rows)),
            "rmse_mean": float(sum(rmses) / len(rmses)) if rmses else None,
            "rmse_min": float(min(rmses)) if rmses else None,
            "rmse_max": float(max(rmses)) if rmses else None,
            "score_mean": float(sum(scores) / len(scores)) if scores else None,
            "score_min": float(min(scores)) if scores else None,
            "score_max": float(max(scores)) if scores else None,
            "raw_rmse_mean": float(sum(raw_rmses) / len(raw_rmses)) if raw_rmses else None,
            "raw_score_mean": float(sum(raw_scores) / len(raw_scores)) if raw_scores else None,
        }
    return {
        "run_dir": str(run_dir),
        "present": bool(summary),
        "run_complete": bool(summary.get("run_complete") or False),
        "expected_subset_seed_count": int(summary.get("expected_subset_seed_count", 0) or 0),
        "completed_subset_seed_count": int(summary.get("completed_subset_seed_count", 0) or 0),
        "n_prediction_records": int(summary.get("n_prediction_records", 0) or 0),
        "overall_metrics": summary.get("overall_metrics") if isinstance(summary.get("overall_metrics"), dict) else {},
        "subset_stats": subset_stats,
    }


def _infer_feature_policy(name: str) -> str:
    for policy in (
        "settings_common_sensors_pca",
        "settings_common_sensors_raw",
        "mdfa_key_sensors_pca",
        "mdfa_key_sensors_raw",
        "common_sensors_pca",
        "common_sensors_raw",
        "sensor21_pca",
        "all24_pca",
    ):
        if policy in name:
            return policy
    return "legacy_or_unknown"


def _infer_conv_formulation(name: str) -> str:
    if "source2d" in name or "source_2d" in name:
        return "source_2d"
    if "temporal_1d" in name:
        return "temporal_1d"
    return "legacy_or_unknown"


def _infer_temporal_feature_mode(name: str) -> str:
    if "leveldiff" in name or "level_diff" in name:
        return "level_diff"
    return "level"


def _row_from_spec(spec: dict[str, Any]) -> dict[str, Any]:
    run_dir = Path(spec["path"])
    summary = _read_json_if_present(_summary_path(run_dir))
    subset_rows = (summary or {}).get("subset_seed_rows") or []
    target_subset = spec.get("subset")
    target_seed = spec.get("seed")
    first_row = {}
    for row in subset_rows:
        if target_subset is not None and str(row.get("subset")) != str(target_subset):
            continue
        if target_seed is not None and int(row.get("seed", -1)) != int(target_seed):
            continue
        first_row = row
        break
    if not first_row and subset_rows and target_subset is None:
        first_row = subset_rows[0]
    subset = str(first_row.get("subset") or target_subset or "FD001")
    seed = int(first_row.get("seed", target_seed or 42) or target_seed or 42)
    subset_payload = _first_subset_payload(run_dir, seed, subset) or {}
    config = subset_payload.get("run_config") if isinstance(subset_payload.get("run_config"), dict) else {}
    diagnostics = subset_payload.get("diagnostics") if isinstance(subset_payload.get("diagnostics"), dict) else {}
    output_calibration = (
        diagnostics.get("output_calibration")
        if isinstance(diagnostics.get("output_calibration"), dict)
        else {}
    )
    snapshot_ensemble = (
        diagnostics.get("snapshot_ensemble")
        if isinstance(diagnostics.get("snapshot_ensemble"), dict)
        else {}
    )
    metrics = subset_payload.get("primary_test_metrics") if isinstance(subset_payload.get("primary_test_metrics"), dict) else {}
    if not metrics:
        metrics = (summary or {}).get("overall_metrics") if isinstance((summary or {}).get("overall_metrics"), dict) else {}
    records = subset_payload.get("rul_prediction_records") if isinstance(subset_payload.get("rul_prediction_records"), list) else []
    raw_metrics = _rul_metrics_from_records(records, use_raw_truth=True)
    published = ((summary or {}).get("source") or {}).get("published_mdfa_results", {}).get(subset, {})
    rmse = float(metrics.get("rul_rmse", first_row.get("rul_rmse", 0.0)) or 0.0)
    published_rmse = float(published.get("rmse", 0.0) or 0.0)
    name = str(spec["name"])
    feature_policy = str(subset_payload.get("feature_policy") or config.get("feature_policy") or _infer_feature_policy(name))
    conv_formulation = str(diagnostics.get("conv_formulation") or config.get("conv_formulation") or _infer_conv_formulation(name))
    lr_scheduler = str(diagnostics.get("lr_scheduler") or config.get("lr_scheduler") or ("reduce_on_plateau" if "reduce_on_plateau" in name else "none"))
    temporal_feature_mode = str(
        subset_payload.get("temporal_feature_mode")
        or first_row.get("temporal_feature_mode")
        or config.get("temporal_feature_mode")
        or _infer_temporal_feature_mode(name)
    )
    present = summary is not None and bool(first_row or subset_payload or target_subset is None)
    return {
        "name": name,
        "role": str(spec["role"]),
        "claim_use": str(spec["claim_use"]),
        "present": present,
        "run_dir": str(run_dir),
        "subset": subset,
        "seed": seed,
        "epochs": int(diagnostics.get("epochs", config.get("epochs", 0)) or 0),
        "window_size": int(config.get("window_size", subset_payload.get("window_size", 0)) or 0),
        "conv_formulation": conv_formulation,
        "temporal_feature_mode": temporal_feature_mode,
        "feature_policy": feature_policy,
        "condition_normalization": str(
            subset_payload.get("condition_normalization") or config.get("condition_normalization") or "none"
        ),
        "append_condition_onehot": bool(
            subset_payload.get("append_condition_onehot") or config.get("append_condition_onehot") or False
        ),
        "lr_scheduler": lr_scheduler,
        "output_calibration": str(config.get("output_calibration") or output_calibration.get("policy") or "none"),
        "output_calibration_applied": bool(output_calibration.get("applied") or False),
        "output_calibration_val_rmse_delta": output_calibration.get("val_rmse_delta"),
        "output_calibration_reason": str(output_calibration.get("reason") or ""),
        "snapshot_ensemble_k": int(config.get("snapshot_ensemble_k") or snapshot_ensemble.get("requested_k") or 1),
        "snapshot_ensemble_applied": bool(snapshot_ensemble.get("applied") or False),
        "snapshot_ensemble_val_rmse_delta": snapshot_ensemble.get("val_rmse_delta"),
        "snapshot_ensemble_reason": str(snapshot_ensemble.get("reason") or ""),
        "val_fraction": config.get("val_fraction"),
        "rmse": rmse,
        "mae": float(metrics.get("rul_mae", first_row.get("rul_mae", 0.0)) or 0.0),
        "score": float(metrics.get("rul_score", first_row.get("rul_score", 0.0)) or 0.0),
        "raw_rmse": float(raw_metrics["rul_rmse"]) if raw_metrics else None,
        "raw_score": float(raw_metrics["rul_score"]) if raw_metrics else None,
        "pca_feature_dim": int(subset_payload.get("pca_feature_dim", first_row.get("pca_feature_dim", 0)) or 0),
        "model_input_feature_dim": int(
            subset_payload.get("model_input_feature_dim", first_row.get("model_input_feature_dim", 0)) or 0
        ),
        "pca_variance_threshold": subset_payload.get("pca_variance_threshold", config.get("pca_variance")),
        "train_seconds": float((diagnostics or {}).get("train_seconds", first_row.get("train_seconds", 0.0)) or 0.0),
        "n_prediction_records": int((summary or {}).get("n_prediction_records", 0) or 0),
        "published_rmse": published_rmse,
        "rmse_gap_to_published": float(rmse - published_rmse) if published_rmse else None,
    }


def _best_row(rows: list[dict[str, Any]], *, role: str | None = None, epochs: int | None = None) -> dict[str, Any] | None:
    candidates = [row for row in rows if row["present"]]
    if role is not None:
        candidates = [row for row in candidates if row["role"] == role]
    if epochs is not None:
        candidates = [row for row in candidates if int(row["epochs"]) == int(epochs)]
    if not candidates:
        return None
    return min(candidates, key=lambda row: float(row["rmse"]))


def _subset_archive_stats(archive: dict[str, Any], subset: str) -> dict[str, Any]:
    subset_stats = archive.get("subset_stats") if isinstance(archive.get("subset_stats"), dict) else {}
    stats = subset_stats.get(subset)
    return stats if isinstance(stats, dict) else {}


def build_mdfa_strategy_probe_audit() -> dict[str, Any]:
    rows = [_row_from_spec(spec) for spec in PROBE_SPECS]
    previous_single_archive = _full_archive_stats(PREVIOUS_FULL_SINGLE_CONDITION_ARCHIVE)
    single_archive = _full_archive_stats(FULL_SINGLE_CONDITION_ARCHIVE)
    zero_dropout_single_archive = _full_archive_stats(ZERO_DROPOUT_SINGLE_CONDITION_ARCHIVE)
    temporal_level_diff_fd003_archive = _full_archive_stats(TEMPORAL_LEVEL_DIFF_FD003_ARCHIVE)
    multi_archive = _full_archive_stats(FULL_MULTI_CONDITION_ARCHIVE)
    full_branch_archive_present = (
        bool(single_archive["run_complete"])
        and bool(zero_dropout_single_archive["run_complete"])
        and bool(multi_archive["run_complete"])
        and int(single_archive["completed_subset_seed_count"]) == 6
        and int(zero_dropout_single_archive["completed_subset_seed_count"]) == 6
        and int(multi_archive["completed_subset_seed_count"]) == 6
    )
    best_25 = _best_row(rows, role="feature_policy_probe_25epoch", epochs=25)
    fd001_full_candidates = [
        row
        for row in rows
        if row["present"]
        and row["subset"] == "FD001"
        and row["role"] == "single_condition_long_window_candidate"
        and int(row["epochs"]) == 100
    ]
    best_100 = min(fd001_full_candidates, key=lambda row: float(row["rmse"])) if fd001_full_candidates else None
    fd002_failed = next(
        (
            row
            for row in rows
            if row["name"] == "source2d_all24_pca_full_fd002_failed_multicondition" and row["present"]
        ),
        None,
    )
    fd002_condition_full = next(
        (
            row
            for row in rows
            if row["name"] == "source2d_sensor21_pca_kmeans_onehot_fd002_full" and row["present"]
        ),
        None,
    )
    fd004_condition_full = next(
        (
            row
            for row in rows
            if row["name"] == "source2d_sensor21_pca_kmeans_onehot_fd004_full" and row["present"]
        ),
        None,
    )
    fd001_long_window_candidates = [
        row
        for row in rows
        if row["present"] and row["subset"] == "FD001" and row["role"] == "single_condition_long_window_candidate"
    ]
    fd001_long_window = (
        min(fd001_long_window_candidates, key=lambda row: (float(row["rmse"]), float(row["score"])))
        if fd001_long_window_candidates
        else None
    )
    fd003_short_failure = next(
        (
            row
            for row in rows
            if row["name"] == "source2d_all24_pca_window30_fd003_failure" and row["present"]
        ),
        None,
    )
    fd003_trajectory_negative = next(
        (
            row
            for row in rows
            if row["name"] == "source2d_common_sensors_pca_kmeans4_trajectory_fd003_negative" and row["present"]
        ),
        None,
    )
    fd003_long_window_candidates = [
        row
        for row in rows
        if row["present"] and row["subset"] == "FD003" and row["role"] == "two_fault_mode_long_window_candidate"
    ]
    fd003_long_window = (
        min(fd003_long_window_candidates, key=lambda row: (float(row["rmse"]), float(row["score"])))
        if fd003_long_window_candidates
        else None
    )
    table4_key_sensor_rows = [
        row for row in rows if row["present"] and row["role"] == "table4_key_sensor_probe_25epoch"
    ]
    pca_threshold_rows = [
        row for row in rows if row["present"] and row["role"] == "pca_threshold_probe_25epoch"
    ]
    native_raw_rows = [
        row for row in rows if row["present"] and row["role"] == "native_raw_rul_probe_25epoch"
    ]
    output_calibration_rows = [
        row for row in rows if row["present"] and row["role"] == "validation_output_calibration_probe_25epoch"
    ]
    snapshot_ensemble_rows = [
        row for row in rows if row["present"] and row["role"] == "validation_snapshot_ensemble_probe_25epoch"
    ]
    temporal_velocity_rows = [
        row for row in rows if row["present"] and row["temporal_feature_mode"] == "level_diff"
    ]
    dropout_sensitivity_rows = [
        row for row in rows if row["present"] and "dropout_sensitivity_probe_25epoch" in row["role"]
    ]
    batch_sensitivity_rows = [
        row for row in rows if row["present"] and "batch_sensitivity_probe_25epoch" in row["role"]
    ]
    fd003_zero_dropout_full = next(
        (
            row
            for row in rows
            if row["name"] == "source2d_all24_pca_window80_dropout000_fd003_full" and row["present"]
        ),
        None,
    )
    legacy = next((row for row in rows if row["name"] == "legacy_temporal_1d_full_fd001" and row["present"]), None)
    source2d = next((row for row in rows if row["name"] == "source2d_all24_pca_full_fd001" and row["present"]), None)
    gates = {
        "all_probe_summaries_present": all(row["present"] for row in rows if row["role"] != "legacy_pre_source2d_calibration"),
        "source2d_full_fd001_present": source2d is not None,
        "fd001_long_window_full_present": fd001_long_window is not None,
        "fd002_multicondition_failure_observed": fd002_failed is not None,
        "fd002_condition_aware_full_present": fd002_condition_full is not None,
        "fd003_short_window_failure_observed": fd003_short_failure is not None,
        "fd003_trajectory_cluster_negative_observed": fd003_trajectory_negative is not None,
        "fd003_long_window_full_present": fd003_long_window is not None,
        "fd004_condition_aware_full_present": fd004_condition_full is not None,
        "fd001_fd003_low_dropout_archive_present": bool(single_archive["run_complete"]),
        "fd003_zero_dropout_full_archive_present": bool(zero_dropout_single_archive["run_complete"]),
        "dropout_sensitivity_probe_present": len(dropout_sensitivity_rows) >= 4,
        "batch_sensitivity_probe_present": len(batch_sensitivity_rows) >= 2,
        "table4_key_sensor_probe_present": len(table4_key_sensor_rows) == 4,
        "pca_threshold_sensitivity_probe_present": len(pca_threshold_rows) == 4,
        "native_raw_rul_probe_present": len(native_raw_rows) == 4,
        "validation_output_calibration_probe_present": len(output_calibration_rows) >= 2,
        "validation_snapshot_ensemble_probe_present": len(snapshot_ensemble_rows) >= 2,
        "temporal_velocity_feature_probe_present": len(temporal_velocity_rows) >= 3
        and bool(temporal_level_diff_fd003_archive["run_complete"]),
        "feature_policy_probe_complete": best_25 is not None,
        "best_full_candidate_identified": best_100 is not None,
        "full_fd001_fd004_three_seed_archive_present": full_branch_archive_present,
        "safe_to_promote_strategy_to_published_reproduction": False,
    }
    diagnostics: dict[str, Any] = {}
    if legacy and source2d:
        diagnostics["legacy_to_source2d_rmse_delta"] = float(source2d["rmse"] - legacy["rmse"])
    if best_25:
        diagnostics["best_25epoch_feature_policy"] = best_25["feature_policy"]
        diagnostics["best_25epoch_rmse"] = float(best_25["rmse"])
    if best_100:
        diagnostics["selected_full_budget_fd001_candidate"] = best_100["name"]
        diagnostics["selected_full_budget_fd001_rmse"] = float(best_100["rmse"])
        diagnostics["selected_full_budget_fd001_raw_rmse"] = best_100.get("raw_rmse")
        diagnostics["selected_gap_to_mdfa_fd001"] = best_100["rmse_gap_to_published"]
    if source2d and fd001_long_window:
        diagnostics["fd001_window80_rmse_delta_vs_window30"] = float(fd001_long_window["rmse"] - source2d["rmse"])
        diagnostics["fd001_window80_score_delta_vs_window30"] = float(fd001_long_window["score"] - source2d["score"])
    if fd002_failed and fd002_condition_full:
        diagnostics["fd002_condition_aware_rmse_delta_vs_all24_pca"] = float(
            fd002_condition_full["rmse"] - fd002_failed["rmse"]
        )
        diagnostics["fd002_condition_aware_gap_to_mdfa"] = fd002_condition_full["rmse_gap_to_published"]
    if fd003_short_failure and fd003_long_window:
        diagnostics["fd003_long_window_rmse_delta_vs_window30"] = float(
            fd003_long_window["rmse"] - fd003_short_failure["rmse"]
        )
        diagnostics["fd003_long_window_gap_to_mdfa"] = fd003_long_window["rmse_gap_to_published"]
    previous_fd003_dropout01 = next(
        (
            row
            for row in rows
            if row["name"] == "source2d_all24_pca_window80_dropout01_fd003_full" and row["present"]
        ),
        None,
    )
    if previous_fd003_dropout01 and fd003_zero_dropout_full:
        diagnostics["fd003_zero_dropout_rmse_delta_vs_dropout01_seed42"] = float(
            fd003_zero_dropout_full["rmse"] - previous_fd003_dropout01["rmse"]
        )
    if fd003_trajectory_negative and fd003_long_window:
        diagnostics["fd003_trajectory_cluster_rmse_delta_vs_long_window"] = float(
            fd003_trajectory_negative["rmse"] - fd003_long_window["rmse"]
        )
    if fd004_condition_full:
        diagnostics["fd004_condition_aware_gap_to_mdfa"] = fd004_condition_full["rmse_gap_to_published"]
    fd003_archive_candidates: list[dict[str, Any]] = []
    for candidate in [
        {
            "name": "source2d_all24_pca_window80_dropout000_fd003_full",
            "archive": zero_dropout_single_archive,
            "temporal_feature_mode": "level",
        },
        {
            "name": "source2d_all24_pca_window80_dropout000_leveldiff_fd003_full",
            "archive": temporal_level_diff_fd003_archive,
            "temporal_feature_mode": "level_diff",
        },
    ]:
        stats = _subset_archive_stats(candidate["archive"], "FD003")
        if stats.get("rmse_mean") is None:
            continue
        fd003_archive_candidates.append(
            {
                "name": candidate["name"],
                "window_size": 80,
                "feature_policy": "all24_pca",
                "dropout": 0.0,
                "temporal_feature_mode": candidate["temporal_feature_mode"],
                "rmse_mean": float(stats["rmse_mean"]),
                "score_mean": stats.get("score_mean"),
                "raw_rmse_mean": stats.get("raw_rmse_mean"),
                "n_seeds": stats.get("n"),
                "gap_to_mdfa": float(stats["rmse_mean"]) - 11.89,
            }
        )
    selected_fd003_archive = (
        min(
            fd003_archive_candidates,
            key=lambda row: (float(row["rmse_mean"]), float(row["score_mean"] or 0.0)),
        )
        if fd003_archive_candidates
        else {}
    )
    if selected_fd003_archive:
        diagnostics["selected_full_budget_fd003_candidate"] = selected_fd003_archive["name"]
        diagnostics["selected_full_budget_fd003_rmse"] = selected_fd003_archive["rmse_mean"]
        diagnostics["selected_full_budget_fd003_score"] = selected_fd003_archive.get("score_mean")
        diagnostics["selected_gap_to_mdfa_fd003"] = selected_fd003_archive["gap_to_mdfa"]
    zero_fd003_stats = _subset_archive_stats(zero_dropout_single_archive, "FD003")
    leveldiff_fd003_stats = _subset_archive_stats(temporal_level_diff_fd003_archive, "FD003")
    if zero_fd003_stats.get("rmse_mean") is not None and leveldiff_fd003_stats.get("rmse_mean") is not None:
        diagnostics["fd003_leveldiff_full_mean_rmse_delta_vs_level_full"] = float(
            leveldiff_fd003_stats["rmse_mean"] - zero_fd003_stats["rmse_mean"]
        )
        diagnostics["fd003_leveldiff_full_mean_score_delta_vs_level_full"] = float(
            (leveldiff_fd003_stats.get("score_mean") or 0.0) - (zero_fd003_stats.get("score_mean") or 0.0)
        )
    if table4_key_sensor_rows:
        diagnostics["table4_key_sensor_probe"] = {
            row["subset"]: {
                "rmse": float(row["rmse"]),
                "score": float(row["score"]),
                "raw_rmse": row.get("raw_rmse"),
                "raw_score": row.get("raw_score"),
                "pca_feature_dim": int(row["pca_feature_dim"]),
                "gap_to_mdfa": row["rmse_gap_to_published"],
            }
            for row in table4_key_sensor_rows
        }
    if pca_threshold_rows:
        diagnostics["pca_threshold_sensitivity_probe"] = {
            row["subset"]: {
                "rmse": float(row["rmse"]),
                "score": float(row["score"]),
                "raw_rmse": row.get("raw_rmse"),
                "raw_score": row.get("raw_score"),
                "pca_feature_dim": int(row["pca_feature_dim"]),
                "pca_variance_threshold": row.get("pca_variance_threshold"),
                "gap_to_mdfa": row["rmse_gap_to_published"],
            }
            for row in pca_threshold_rows
        }
    if native_raw_rows:
        diagnostics["native_raw_rul_probe"] = {
            row["subset"]: {
                "rmse": float(row["rmse"]),
                "score": float(row["score"]),
                "rul_cap": 150.0,
                "cap_eval_rul": False,
                "gap_to_mdfa": row["rmse_gap_to_published"],
            }
            for row in native_raw_rows
        }
    if output_calibration_rows:
        diagnostics["validation_output_calibration_probe"] = {
            row["subset"]: {
                "rmse": float(row["rmse"]),
                "score": float(row["score"]),
                "output_calibration": row["output_calibration"],
                "applied": bool(row["output_calibration_applied"]),
                "val_rmse_delta": row["output_calibration_val_rmse_delta"],
                "reason": row["output_calibration_reason"],
                "gap_to_mdfa": row["rmse_gap_to_published"],
            }
            for row in output_calibration_rows
        }
    if snapshot_ensemble_rows:
        diagnostics["validation_snapshot_ensemble_probe"] = {
            row["subset"]: {
                "rmse": float(row["rmse"]),
                "score": float(row["score"]),
                "snapshot_ensemble_k": int(row["snapshot_ensemble_k"]),
                "applied": bool(row["snapshot_ensemble_applied"]),
                "val_rmse_delta": row["snapshot_ensemble_val_rmse_delta"],
                "reason": row["snapshot_ensemble_reason"],
                "gap_to_mdfa": row["rmse_gap_to_published"],
            }
            for row in snapshot_ensemble_rows
        }
    if temporal_velocity_rows:
        diagnostics["temporal_velocity_feature_probe"] = {
            row["name"]: {
                "subset": row["subset"],
                "rmse": float(row["rmse"]),
                "score": float(row["score"]),
                "raw_rmse": row.get("raw_rmse"),
                "raw_score": row.get("raw_score"),
                "epochs": int(row["epochs"]),
                "temporal_feature_mode": row["temporal_feature_mode"],
                "model_input_feature_dim": row.get("model_input_feature_dim"),
                "gap_to_mdfa": row["rmse_gap_to_published"],
            }
            for row in temporal_velocity_rows
        }
    fd001_leveldiff_probe = next(
        (
            row
            for row in rows
            if row["name"] == "source2d_all24_pca_window80_dropout01_leveldiff_fd001_probe25" and row["present"]
        ),
        None,
    )
    fd001_level_probe = next(
        (
            row
            for row in rows
            if row["name"] == "source2d_all24_pca_window80_dropout01_fd001_probe25" and row["present"]
        ),
        None,
    )
    fd003_leveldiff_probe = next(
        (
            row
            for row in rows
            if row["name"] == "source2d_all24_pca_window80_dropout000_leveldiff_fd003_probe25" and row["present"]
        ),
        None,
    )
    fd003_zero_probe = next(
        (
            row
            for row in rows
            if row["name"] == "source2d_all24_pca_window80_dropout000_fd003_probe25" and row["present"]
        ),
        None,
    )
    fd003_leveldiff_full = next(
        (
            row
            for row in rows
            if row["name"] == "source2d_all24_pca_window80_dropout000_leveldiff_fd003_full" and row["present"]
        ),
        None,
    )
    if fd001_leveldiff_probe and fd001_level_probe:
        diagnostics["fd001_leveldiff_rmse_delta_vs_level_probe25"] = float(
            fd001_leveldiff_probe["rmse"] - fd001_level_probe["rmse"]
        )
    if fd003_leveldiff_probe and fd003_zero_probe:
        diagnostics["fd003_leveldiff_rmse_delta_vs_level_probe25"] = float(
            fd003_leveldiff_probe["rmse"] - fd003_zero_probe["rmse"]
        )
    if fd003_leveldiff_full and fd003_zero_dropout_full:
        diagnostics["fd003_leveldiff_full_seed42_rmse_delta_vs_level_full"] = float(
            fd003_leveldiff_full["rmse"] - fd003_zero_dropout_full["rmse"]
        )
    fd002_table4 = next((row for row in table4_key_sensor_rows if row["subset"] == "FD002"), None)
    fd004_table4 = next((row for row in table4_key_sensor_rows if row["subset"] == "FD004"), None)
    fd002_pca090 = next((row for row in pca_threshold_rows if row["subset"] == "FD002"), None)
    fd004_pca090 = next((row for row in pca_threshold_rows if row["subset"] == "FD004"), None)
    if fd002_table4 and fd002_condition_full:
        diagnostics["fd002_condition_aware_rmse_delta_vs_table4_key_sensors"] = float(
            fd002_condition_full["rmse"] - fd002_table4["rmse"]
        )
    if fd004_table4 and fd004_condition_full:
        diagnostics["fd004_condition_aware_rmse_delta_vs_table4_key_sensors"] = float(
            fd004_condition_full["rmse"] - fd004_table4["rmse"]
        )
    if fd002_pca090 and fd002_condition_full:
        diagnostics["fd002_condition_aware_rmse_delta_vs_pca090_all24"] = float(
            fd002_condition_full["rmse"] - fd002_pca090["rmse"]
        )
    if fd004_pca090 and fd004_condition_full:
        diagnostics["fd004_condition_aware_rmse_delta_vs_pca090_all24"] = float(
            fd004_condition_full["rmse"] - fd004_pca090["rmse"]
        )
    diagnostics["previous_full_single_condition_archive"] = previous_single_archive
    diagnostics["full_single_condition_archive"] = single_archive
    diagnostics["zero_dropout_single_condition_archive"] = zero_dropout_single_archive
    diagnostics["temporal_level_diff_fd003_archive"] = temporal_level_diff_fd003_archive
    diagnostics["full_multi_condition_archive"] = multi_archive
    return {
        "version": VERSION,
        "status": (
            "full_branch_archive_materialized_reproduction_pending"
            if full_branch_archive_present
            else "fd001_fd002_fd003_fd004_strategy_probe_complete_full_archive_pending"
        ),
            "claim_boundary": (
            "These rows are seed-42 strategy-selection and source-fidelity diagnostics. FD001 probes calibrate the "
            "single-condition route, and FD002 probes show that multi-condition C-MAPSS requires condition-aware "
            "preprocessing. They justify the next full-budget route. The current four-subset local branch archive is "
            "source-matched candidate evidence, not a published MDFA reproduction or C-MAPSS SOTA proof. Capped-test "
            "and raw-test RUL metrics are both audited because the source-style cap policy is not yet exact-native."
        ),
        "gates": gates,
        "missing_gates": [name for name, value in gates.items() if not value],
        "diagnostics": diagnostics,
        "probe_rows": rows,
        "decision": {
            "current_fd001_full_candidate": (best_100 or {}).get("name"),
            "current_feature_policy": (best_100 or {}).get("feature_policy"),
            "current_conv_formulation": (best_100 or {}).get("conv_formulation"),
            "current_fd003_two_fault_candidate": selected_fd003_archive.get(
                "name", (fd003_long_window or {}).get("name")
            ),
            "current_fd003_window_size": selected_fd003_archive.get(
                "window_size", (fd003_long_window or {}).get("window_size")
            ),
            "current_fd003_temporal_feature_mode": selected_fd003_archive.get(
                "temporal_feature_mode", (fd003_long_window or {}).get("temporal_feature_mode")
            ),
            "current_fd003_three_seed_rmse": selected_fd003_archive.get("rmse_mean"),
            "current_fd002_multicondition_candidate": (fd002_condition_full or {}).get("name"),
            "current_fd002_condition_policy": (fd002_condition_full or {}).get("condition_normalization"),
            "current_fd002_condition_onehot": bool((fd002_condition_full or {}).get("append_condition_onehot") or False),
            "current_fd004_multicondition_candidate": (fd004_condition_full or {}).get("name"),
            "current_fd004_condition_policy": (fd004_condition_full or {}).get("condition_normalization"),
            "current_fd004_condition_onehot": bool((fd004_condition_full or {}).get("append_condition_onehot") or False),
            "rationale": (
                "Use source_2d/all24_pca as the single-condition branch, with window80 and lower dropout selected by "
                "FD001/FD003 validation probes to stabilize the two-fault FD003 subset. Do not extend this policy "
                "blindly to every subset: the FD002 failure diagnostic shows all24_pca collapses multi-condition "
                "structure, while sensor21_pca with kmeans6 setting normalization and condition one-hot materially "
                "improves the multi-condition route. A Table-4 key-sensor probe is retained as source-aligned negative "
                "control because the key-sensor PCA branch collapses multi-condition subsets. The PCA=0.90 sensitivity "
                "probe is also retained as negative evidence: lowering the cumulative-contribution threshold compresses "
                "multi-condition subsets too aggressively and does not repair the source-matched route. The zero-dropout "
                "challenger improves the FD003 two-fault subset but is not promoted to FD001 because seed-level stability "
                "regresses there. A cap150/raw-test probe is retained as a native-label negative control because it does "
                "not close the public raw-test C-MAPSS gap. Validation-only affine output calibration and checkpoint "
                "snapshot-ensemble probes are retained as guarded negative results because their validation RMSE gains "
                "stay below the admission threshold, so post-hoc output calibration and checkpoint averaging are not "
                "treated as admitted path-fusion improvements. A level+first-difference temporal-channel probe is "
                "subset-conditional: it regresses FD001, but its full three-seed FD003 challenger gives a small "
                "stable improvement over the level-only zero-dropout FD003 branch. The selected full archive therefore "
                "freezes a stable low-dropout FD001 branch, a level+first-difference FD003 two-fault branch, and a "
                "condition-aware branch for FD002/FD004 under the source-style capped-test claim boundary."
            ),
        },
        "next_actions": [
            "Verify whether the low-dropout single-condition branch remains source-compatible with the MDFA protocol or must be reported as an improved local candidate.",
            "Treat the source PCA cumulative-contribution threshold and exact test-label scoring policy as non-machine-readable until the original authors or supplementary code specify them.",
            "Compare the completed local branch archive against exact MDFA Table 5 only after PCA/key-sensor policy is verified.",
            "Keep the local branch archive out of official SOTA tables until exact-source preprocessing and budget equivalence are verified.",
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# C-MAPSS MDFA Strategy Probe Audit",
        "",
        f"- Version: {payload['version']}",
        f"- Status: `{payload['status']}`",
        f"- Claim boundary: {payload['claim_boundary']}",
        "",
        "## Gate Status",
        "",
        "| Gate | Status |",
        "|---|---|",
    ]
    for name, value in payload["gates"].items():
        lines.append(f"| {name} | {'pass' if value else 'missing'} |")
    lines.extend(
        [
            "",
            "## Probe Rows",
            "",
            "| Name | Subset | Role | Window | Epochs | Conv | Temporal mode | Feature policy | PCA/Input dim | Condition policy | Scheduler | Output calibration | Snapshot ensemble | Val frac | Capped RMSE | Capped Score | Raw RMSE | Raw Score | Gap to MDFA |",
            "|---|---|---|---:|---:|---|---|---|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in payload["probe_rows"]:
        gap = row["rmse_gap_to_published"]
        raw_rmse = row.get("raw_rmse")
        raw_score = row.get("raw_score")
        lines.append(
            "| {name} | {subset} | {role} | {window} | {epochs} | {conv} | {temporal} | {feature} | {dims} | {condition}{onehot} | {sched} | {calibration} | {snapshot} | {val} | {rmse:.4f} | {score:.2f} | {raw_rmse} | {raw_score} | {gap} |".format(
                name=row["name"],
                subset=row["subset"],
                role=row["role"],
                window=int(row.get("window_size") or 0),
                epochs=int(row["epochs"]),
                conv=row["conv_formulation"],
                temporal=row["temporal_feature_mode"],
                feature=row["feature_policy"],
                dims=f"{int(row.get('pca_feature_dim') or 0)}/{int(row.get('model_input_feature_dim') or row.get('pca_feature_dim') or 0)}",
                condition=row.get("condition_normalization") or "none",
                onehot="+onehot" if bool(row.get("append_condition_onehot")) else "",
                sched=row["lr_scheduler"],
                calibration=(
                    f"{row.get('output_calibration')}:{'applied' if row.get('output_calibration_applied') else 'blocked'}"
                    if row.get("output_calibration") and row.get("output_calibration") != "none"
                    else "none"
                ),
                snapshot=(
                    f"k{int(row.get('snapshot_ensemble_k') or 1)}:{'applied' if row.get('snapshot_ensemble_applied') else 'blocked'}"
                    if int(row.get("snapshot_ensemble_k") or 1) > 1
                    else "none"
                ),
                val="-" if row["val_fraction"] is None else row["val_fraction"],
                rmse=float(row["rmse"]),
                score=float(row["score"]),
                raw_rmse="-" if raw_rmse is None else f"{float(raw_rmse):.4f}",
                raw_score="-" if raw_score is None else f"{float(raw_score):.2f}",
                gap="-" if gap is None else f"{float(gap):.4f}",
            )
        )
    full_archives = [
        ("Previous single-condition archive", payload["diagnostics"].get("previous_full_single_condition_archive") or {}),
        ("Selected single-condition archive", payload["diagnostics"].get("full_single_condition_archive") or {}),
        ("Zero-dropout single-condition challenger", payload["diagnostics"].get("zero_dropout_single_condition_archive") or {}),
        ("Temporal level+diff FD003 challenger", payload["diagnostics"].get("temporal_level_diff_fd003_archive") or {}),
        ("Multi-condition archive", payload["diagnostics"].get("full_multi_condition_archive") or {}),
    ]
    lines.extend(
        [
            "",
            "## Full Archive Stats",
            "",
            "| Archive | Complete | Records | Subset | Seeds | Capped RMSE mean | RMSE range | Capped Score mean | Raw RMSE mean | Raw Score mean |",
            "|---|---|---:|---|---|---:|---|---:|---:|---:|",
        ]
    )
    for archive_name, archive in full_archives:
        subset_stats = archive.get("subset_stats") if isinstance(archive.get("subset_stats"), dict) else {}
        if not subset_stats:
            lines.append(
                f"| {archive_name} | {archive.get('run_complete', False)} | {int(archive.get('n_prediction_records', 0) or 0)} | - | - | - | - | - | - | - |"
            )
            continue
        for subset, stats in subset_stats.items():
            seeds = ",".join(str(seed) for seed in stats.get("seeds", []))
            rmse_min = stats.get("rmse_min")
            rmse_max = stats.get("rmse_max")
            rmse_range = "-" if rmse_min is None or rmse_max is None else f"{float(rmse_min):.4f}-{float(rmse_max):.4f}"
            raw_rmse = stats.get("raw_rmse_mean")
            raw_score = stats.get("raw_score_mean")
            lines.append(
                "| {archive} | {complete} | {records} | {subset} | {seeds} | {rmse_mean:.4f} | {rmse_range} | {score_mean:.2f} | {raw_rmse} | {raw_score} |".format(
                    archive=archive_name,
                    complete=bool(archive.get("run_complete", False)),
                    records=int(archive.get("n_prediction_records", 0) or 0),
                    subset=subset,
                    seeds=seeds,
                    rmse_mean=float(stats.get("rmse_mean") or 0.0),
                    rmse_range=rmse_range,
                    score_mean=float(stats.get("score_mean") or 0.0),
                    raw_rmse="-" if raw_rmse is None else f"{float(raw_rmse):.4f}",
                    raw_score="-" if raw_score is None else f"{float(raw_score):.2f}",
                )
            )
    decision = payload["decision"]
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Current FD001 full candidate: `{decision['current_fd001_full_candidate']}`",
            f"- Feature policy: `{decision['current_feature_policy']}`",
            f"- Conv formulation: `{decision['current_conv_formulation']}`",
            f"- Current FD003 two-fault candidate: `{decision['current_fd003_two_fault_candidate']}`",
            f"- FD003 window size: `{decision['current_fd003_window_size']}`",
            f"- FD003 temporal mode: `{decision.get('current_fd003_temporal_feature_mode')}`",
            f"- FD003 three-seed RMSE: `{decision.get('current_fd003_three_seed_rmse')}`",
            f"- Current FD002 multi-condition candidate: `{decision['current_fd002_multicondition_candidate']}`",
            f"- FD002 condition policy: `{decision['current_fd002_condition_policy']}`",
            f"- Current FD004 multi-condition candidate: `{decision['current_fd004_multicondition_candidate']}`",
            f"- FD004 condition policy: `{decision['current_fd004_condition_policy']}`",
            f"- Rationale: {decision['rationale']}",
            "",
            "## Next Actions",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in payload["next_actions"])
    return "\n".join(lines).rstrip() + "\n"


def write_mdfa_strategy_probe_audit(output_dir: Path | str = DEFAULT_OUTPUT_DIR) -> list[Path]:
    output_dir = Path(output_dir)
    payload = build_mdfa_strategy_probe_audit()
    json_path = output_dir / "cmapss_mdfa_strategy_probe_audit.json"
    md_path = output_dir / "cmapss_mdfa_strategy_probe_audit.md"
    _write_json(json_path, payload)
    _write_text(md_path, render_markdown(payload))
    return [json_path, md_path]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Audit C-MAPSS MDFA source-matched strategy probes.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    for path in write_mdfa_strategy_probe_audit(args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
