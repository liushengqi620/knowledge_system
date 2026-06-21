from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "knowledge_exports" / "aaai_exact_native_protocol_gate"
DEFAULT_FORMAL_RUNS = [
    REPO_ROOT / "knowledge_exports" / "aaai_formal_public_runs" / "skab_strong_anchor_w48_e40",
    REPO_ROOT
    / "knowledge_exports"
    / "aaai_formal_public_runs"
    / "skab_llm_condition_candidate_gate_valadm001_w005_c010_w48_e40",
    REPO_ROOT
    / "knowledge_exports"
    / "ms_gse_rpf_llm_condition_ablation_full"
    / "a0_algorithmic_only",
]
DEFAULT_EXTERNAL_ARTIFACTS = [
    REPO_ROOT
    / "knowledge_exports"
    / "external_baseline_protocol_runs"
    / "skab_external_baselines_native_records_usad_tranad_w48_e8.json",
    REPO_ROOT
    / "knowledge_exports"
    / "external_baseline_protocol_runs"
    / "anomaly_transformer_official_skab_wrapper_3seed_budget_probe.json",
    REPO_ROOT / "knowledge_exports" / "external_baseline_protocol_runs" / "skab_anomaly_transformer_3seed_probe.json",
]
VERSION = "skab-native-metric-audit-v1"
DEFAULT_CHANGEPOINT_EVENT_WINDOW_STEPS = 60


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _read_json(path: Path) -> dict[str, Any]:
    with open(_fs_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    os.makedirs(_fs_path(path.parent), exist_ok=True)
    with open(_fs_path(path), "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def _write_text(path: Path, text: str) -> None:
    os.makedirs(_fs_path(path.parent), exist_ok=True)
    with open(_fs_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _result_files(run_dir: Path) -> list[Path]:
    if not os.path.isdir(_fs_path(run_dir)):
        return []
    return sorted(
        run_dir / name
        for name in os.listdir(_fs_path(run_dir))
        if name.endswith(".json") and "_seed" in name and "summary" not in name
    )


def _has_frozen_prediction_archive(payload: dict[str, Any]) -> bool:
    candidate_keys = [
        "classification_prediction_records",
        "prediction_records",
        "test_prediction_records",
        "test_predictions",
        "test_scores",
        "test_proba",
        "y_test",
        "test_labels",
    ]
    return any(key in payload and payload.get(key) not in (None, []) for key in candidate_keys)


def _binary_metrics_from_records(records: list[dict[str, Any]]) -> dict[str, float] | None:
    if not records:
        return None
    y_true: list[int] = []
    y_pred: list[int] = []
    for record in records:
        if "y_true_original" in record and "y_pred_original" in record:
            y_true.append(int(record["y_true_original"]))
            y_pred.append(int(record["y_pred_original"]))
    if not y_true or len(y_true) != len(y_pred):
        return None
    tp = sum(1 for true, pred in zip(y_true, y_pred) if true == 1 and pred == 1)
    tn = sum(1 for true, pred in zip(y_true, y_pred) if true == 0 and pred == 0)
    fp = sum(1 for true, pred in zip(y_true, y_pred) if true == 0 and pred == 1)
    fn = sum(1 for true, pred in zip(y_true, y_pred) if true == 1 and pred == 0)

    def _f1(precision_denom: int, recall_denom: int, hits: int) -> float:
        precision = float(hits / precision_denom) if precision_denom else 0.0
        recall = float(hits / recall_denom) if recall_denom else 0.0
        return float(2.0 * precision * recall / (precision + recall)) if precision + recall > 0.0 else 0.0

    positive_f1 = _f1(tp + fp, tp + fn, tp)
    negative_f1 = _f1(tn + fn, tn + fp, tn)
    return {
        "macro_f1": float(0.5 * (positive_f1 + negative_f1)),
        "positive_f1": float(positive_f1),
        "far_percent": float(100.0 * fp / max(1, fp + tn)),
        "mar_percent": float(100.0 * fn / max(1, fn + tp)),
    }


def _changepoint_event_window_metrics_from_records(
    records: list[dict[str, Any]],
    *,
    window_steps: int = DEFAULT_CHANGEPOINT_EVENT_WINDOW_STEPS,
) -> dict[str, float | int] | None:
    if not records:
        return None

    by_run: dict[str, list[dict[str, Any]]] = {}
    for index, record in enumerate(records):
        if "changepoint" not in record:
            continue
        run_id = str(record.get("run_id") or "unknown")
        copied = dict(record)
        copied["_record_position"] = index
        by_run.setdefault(run_id, []).append(copied)

    total_events = 0
    detected_events = 0
    for run_records in by_run.values():
        ordered = sorted(
            run_records,
            key=lambda item: (
                int(item["row_index"]) if item.get("row_index") is not None else int(item["_record_position"]),
                int(item["_record_position"]),
            ),
        )
        event_positions = [
            idx
            for idx, item in enumerate(ordered)
            if int(item.get("changepoint") or 0) == 1
        ]
        for event_idx in event_positions:
            total_events += 1
            right = min(len(ordered), event_idx + int(window_steps) + 1)
            window = ordered[event_idx:right]
            if any(int(item.get("y_pred_original") or 0) == 1 for item in window):
                detected_events += 1

    if total_events <= 0:
        return None
    return {
        "changepoint_events": int(total_events),
        "changepoint_events_detected": int(detected_events),
        "changepoint_event_recall": float(detected_events / total_events),
        "event_window_steps": int(window_steps),
    }


def _formal_seed_row(path: Path) -> dict[str, Any]:
    payload = _read_json(path)
    primary = payload.get("primary_test_metrics") or {}
    thresholded = payload.get("thresholded_test_metrics") or {}
    metrics = thresholded or primary
    records = payload.get("classification_prediction_records") or []
    record_metrics = _binary_metrics_from_records(records) if isinstance(records, list) else None
    changepoint_metrics = (
        _changepoint_event_window_metrics_from_records(records)
        if isinstance(records, list)
        else None
    )
    has_archive = _has_frozen_prediction_archive(payload)
    return {
        "branch": path.parent.name,
        "seed": int(payload.get("seed", -1)),
        "source": str(path),
        "artifact_type": "formal_model_seed",
        "test_size": int(payload.get("test_size", 0) or 0),
        "threshold": _safe_float(payload.get("positive_threshold")),
        "threshold_policy": "validation_tuned_binary_threshold" if payload.get("positive_threshold") is not None else "not_declared",
        "point_metrics_from_frozen_predictions": bool(record_metrics),
        "frozen_prediction_archive_present": has_archive,
        "point_adjustment_disabled": True,
        "point_adjusted_metric_present": False,
        "changepoint_event_window_present": bool(changepoint_metrics),
        "event_window_steps": int(changepoint_metrics["event_window_steps"]) if changepoint_metrics else None,
        "changepoint_events": int(changepoint_metrics["changepoint_events"]) if changepoint_metrics else None,
        "changepoint_events_detected": (
            int(changepoint_metrics["changepoint_events_detected"]) if changepoint_metrics else None
        ),
        "changepoint_event_recall": (
            _safe_float(changepoint_metrics.get("changepoint_event_recall")) if changepoint_metrics else None
        ),
        "macro_f1": _safe_float((record_metrics or {}).get("macro_f1")) or _safe_float(metrics.get("macro_f1")),
        "positive_f1": _safe_float((record_metrics or {}).get("positive_f1")) or _safe_float(metrics.get("positive_f1")),
        "far_percent": _safe_float((record_metrics or {}).get("far_percent")),
        "mar_percent": _safe_float((record_metrics or {}).get("mar_percent")),
        "claim_use": "matched-protocol model evidence with frozen point and changepoint audit records; not an official leaderboard score until split, baselines, and budget are aligned",
    }


def _protocol_metric_row(branch: str, seed: int, source: Path, method_payload: dict[str, Any], *, artifact_type: str) -> dict[str, Any]:
    protocol = method_payload.get("protocol") or {}
    binary = protocol.get("binary") or {}
    cp = protocol.get("right_window_changepoint") or {}
    point_adjusted = protocol.get("point_adjusted") or {}
    metrics = method_payload.get("metrics") or {}
    threshold = method_payload.get("threshold") or method_payload.get("threshold_tuning") or {}
    records = method_payload.get("prediction_records") or []
    record_metrics = _binary_metrics_from_records(records) if isinstance(records, list) else None
    changepoint_metrics = (
        _changepoint_event_window_metrics_from_records(records)
        if isinstance(records, list)
        else None
    )
    record_macro = _safe_float((record_metrics or {}).get("macro_f1")) if record_metrics else None
    record_positive = _safe_float((record_metrics or {}).get("positive_f1")) if record_metrics else None
    record_far = _safe_float((record_metrics or {}).get("far_percent")) if record_metrics else None
    record_mar = _safe_float((record_metrics or {}).get("mar_percent")) if record_metrics else None
    return {
        "branch": branch,
        "seed": int(seed),
        "source": str(source),
        "artifact_type": artifact_type,
        "test_size": None,
        "threshold": _safe_float(threshold.get("threshold") if isinstance(threshold, dict) else None),
        "threshold_policy": "validation_only_threshold_reported" if isinstance(threshold, dict) else "not_declared",
        "point_metrics_from_frozen_predictions": True,
        "frozen_prediction_archive_present": bool(records),
        "point_adjustment_disabled": True,
        "point_adjusted_metric_present": bool(point_adjusted),
        "changepoint_event_window_present": bool(cp) or bool(changepoint_metrics),
        "event_window_steps": (
            int(changepoint_metrics["event_window_steps"])
            if changepoint_metrics
            else int(cp.get("window_steps")) if cp.get("window_steps") is not None else None
        ),
        "changepoint_events": (
            int(changepoint_metrics["changepoint_events"])
            if changepoint_metrics
            else int(cp.get("events")) if cp.get("events") is not None else None
        ),
        "changepoint_events_detected": (
            int(changepoint_metrics["changepoint_events_detected"])
            if changepoint_metrics
            else int(cp.get("detected_events")) if cp.get("detected_events") is not None else None
        ),
        "changepoint_event_recall": (
            _safe_float(changepoint_metrics.get("changepoint_event_recall"))
            if changepoint_metrics
            else _safe_float(cp.get("event_recall") or cp.get("recall"))
        ),
        "macro_f1": record_macro if record_macro is not None else _safe_float(metrics.get("macro_f1")),
        "positive_f1": record_positive if record_positive is not None else _safe_float(binary.get("f1")),
        "far_percent": record_far if record_far is not None else _safe_float(binary.get("far_percent")),
        "mar_percent": record_mar if record_mar is not None else _safe_float(binary.get("mar_percent")),
        "claim_use": "external/style baseline protocol evidence; supports comparison policy but not proposed-branch exact-native proof",
    }


def _external_rows(path: Path) -> list[dict[str, Any]]:
    if not os.path.exists(_fs_path(path)):
        return []
    payload = _read_json(path)
    rows: list[dict[str, Any]] = []
    for run in payload.get("runs", []):
        seed = int(run.get("seed", -1))
        if "matched_row_level" in run:
            rows.append(
                _protocol_metric_row(
                    str(payload.get("baseline", "anomaly_transformer_official_wrapper")),
                    seed,
                    path,
                    run["matched_row_level"],
                    artifact_type="official_source_adapted_protocol",
                )
            )
        for key, value in run.items():
            if key == "matched_row_level":
                continue
            if isinstance(value, dict) and "protocol" in value and "metrics" in value:
                rows.append(
                    _protocol_metric_row(
                        key,
                        seed,
                        path,
                        value,
                        artifact_type="style_baseline_protocol",
                    )
                )
    return rows


def _mean(values: Iterable[float | None]) -> float | None:
    vals = [float(v) for v in values if v is not None]
    return sum(vals) / len(vals) if vals else None


def build_skab_native_metric_audit(
    formal_run_dirs: list[Path] | None = None,
    external_artifacts: list[Path] | None = None,
) -> dict[str, Any]:
    formal_run_dirs = formal_run_dirs if formal_run_dirs is not None else DEFAULT_FORMAL_RUNS
    external_artifacts = external_artifacts if external_artifacts is not None else DEFAULT_EXTERNAL_ARTIFACTS

    formal_rows: list[dict[str, Any]] = []
    for run_dir in formal_run_dirs:
        for path in _result_files(Path(run_dir)):
            formal_rows.append(_formal_seed_row(path))

    external_rows: list[dict[str, Any]] = []
    for path in external_artifacts:
        external_rows.extend(_external_rows(Path(path)))

    rows = sorted(formal_rows + external_rows, key=lambda row: (str(row["branch"]), int(row["seed"])))
    proposed_rows = [
        row
        for row in formal_rows
        if (
            "skab_strong_anchor" in str(row["branch"])
            or "llm_condition" in str(row["branch"])
            or str(row["branch"]) == "a0_algorithmic_only"
        )
    ]
    gates = {
        "proposed_frozen_prediction_archive": bool(proposed_rows) and all(row["frozen_prediction_archive_present"] for row in proposed_rows),
        "proposed_point_metrics_recomputable": bool(proposed_rows) and all(row["point_metrics_from_frozen_predictions"] for row in proposed_rows),
        "proposed_changepoint_event_window_scored": bool(proposed_rows) and all(row["changepoint_event_window_present"] for row in proposed_rows),
        "external_protocol_controls_present": any(row["changepoint_event_window_present"] for row in external_rows),
        "point_adjustment_disabled_for_claim_rows": bool(rows) and all(bool(row["point_adjustment_disabled"]) for row in rows),
        "validation_thresholds_recorded": bool(rows) and all(row["threshold_policy"] != "not_declared" for row in rows),
    }
    missing = [name for name, value in gates.items() if not value]
    status = "native_metric_audit_complete" if not missing else "native_metric_audit_partial"

    branch_summary: list[dict[str, Any]] = []
    for branch in sorted({str(row["branch"]) for row in rows}):
        branch_rows = [row for row in rows if str(row["branch"]) == branch]
        branch_summary.append(
            {
                "branch": branch,
                "n_seeds": len({int(row["seed"]) for row in branch_rows}),
                "macro_f1_mean": _mean(row["macro_f1"] for row in branch_rows),
                "positive_f1_mean": _mean(row["positive_f1"] for row in branch_rows),
                "far_percent_mean": _mean(row["far_percent"] for row in branch_rows),
                "mar_percent_mean": _mean(row["mar_percent"] for row in branch_rows),
                "changepoint_event_recall_mean": _mean(row.get("changepoint_event_recall") for row in branch_rows),
                "has_changepoint_event_window": any(row["changepoint_event_window_present"] for row in branch_rows),
                "has_frozen_prediction_archive": all(row["frozen_prediction_archive_present"] for row in branch_rows),
            }
        )

    formal_branch_summary = [row for row in branch_summary if any(seed_row["branch"] == row["branch"] for seed_row in formal_rows)]
    best_native_audited = max(
        (row for row in formal_branch_summary if row["macro_f1_mean"] is not None and row["has_frozen_prediction_archive"]),
        key=lambda row: float(row["macro_f1_mean"]),
        default=None,
    )
    llm_branch = next((row for row in branch_summary if "llm_condition" in str(row["branch"])), None)
    strong_anchor = next((row for row in branch_summary if "skab_strong_anchor" in str(row["branch"])), None)

    return {
        "version": VERSION,
        "status": status,
        "claim_boundary": (
            "This audit tracks SKAB native metric readiness. It is not an official leaderboard result unless "
            "all proposed-branch gates are true and official/fair baselines share the same split, threshold, and event-window policy."
        ),
        "gates": gates,
        "missing_gates": missing,
        "decision": {
            "current_native_audited_branch": (best_native_audited or {}).get("branch"),
            "current_native_audited_macro_f1": (best_native_audited or {}).get("macro_f1_mean"),
            "strong_anchor_macro_f1": (strong_anchor or {}).get("macro_f1_mean"),
            "llm_condition_macro_f1": (llm_branch or {}).get("macro_f1_mean"),
            "llm_condition_deployed_as_accuracy_branch": False,
            "rationale": (
                "Use the algorithmic-only branch as the current native-audited SKAB accuracy anchor because it has "
                "frozen prediction records and higher recomputed point/event metrics than the conservative LLM "
                "condition-verifier branch. LLM evidence remains a conditional diagnostic mechanism and is not deployed "
                "as the SKAB accuracy branch unless it passes validation and low-tail admission."
            ),
        },
        "branch_summary": branch_summary,
        "rows": rows,
        "next_actions": [
            "Align official/fair SKAB baselines to the same split, validation-only threshold policy, event-window width, and compute budget.",
            "Keep point adjustment disabled unless reproducing an explicitly declared native point-adjusted protocol.",
            "Do not upgrade to official leaderboard wording until exact public split, preprocessing, baseline, threshold, and budget gates are all true.",
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# SKAB Native Metric Audit",
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
    lines.extend(["", "## Branch Summary", "", "| Branch | Seeds | Macro-F1 | Positive F1 | FAR % | MAR % | CP Recall | Event-window | Frozen predictions |", "|---|---:|---:|---:|---:|---:|---:|---|---|"])
    for row in payload["branch_summary"]:
        lines.append(
            "| {branch} | {seeds} | {macro:.4f} | {pf1:.4f} | {far} | {mar} | {cp} | {event} | {archive} |".format(
                branch=row["branch"],
                seeds=row["n_seeds"],
                macro=float(row["macro_f1_mean"] or 0.0),
                pf1=float(row["positive_f1_mean"] or 0.0),
                far="-" if row["far_percent_mean"] is None else f"{float(row['far_percent_mean']):.2f}",
                mar="-" if row["mar_percent_mean"] is None else f"{float(row['mar_percent_mean']):.2f}",
                cp=(
                    "-"
                    if row.get("changepoint_event_recall_mean") is None
                    else f"{float(row['changepoint_event_recall_mean']):.4f}"
                ),
                event="yes" if row["has_changepoint_event_window"] else "no",
                archive="yes" if row["has_frozen_prediction_archive"] else "no",
            )
        )
    lines.extend(["", "## Next Actions", ""])
    lines.extend(f"- {item}" for item in payload["next_actions"])
    return "\n".join(lines).rstrip() + "\n"


def write_skab_native_metric_audit(output_dir: Path | str = DEFAULT_OUTPUT_DIR) -> list[Path]:
    output_dir = Path(output_dir)
    os.makedirs(_fs_path(output_dir), exist_ok=True)
    payload = build_skab_native_metric_audit()
    json_path = output_dir / "skab_native_metric_audit.json"
    md_path = output_dir / "skab_native_metric_audit.md"
    _write_json(json_path, payload)
    _write_text(md_path, render_markdown(payload))
    return [json_path, md_path]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Audit SKAB native metric readiness from current seed artifacts.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    for path in write_skab_native_metric_audit(args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
