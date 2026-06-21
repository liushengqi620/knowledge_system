from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import numpy as np

from skab_official_repository_baseline_audit import DEFAULT_OUTPUT_DIR, _fs_path, _metrics_from_records, _write_json, _write_text


VERSION = "skab-source-rerun-delta-audit-v1"
DEFAULT_OUTPUT_DIR = DEFAULT_OUTPUT_DIR
REPOSITORY_RECORD_DIR = "skab_official_repository_baseline_records"
SOURCE_RECORD_DIR = "skab_official_source_rerun_records"
DEFAULT_METHODS = ["LSTM_AE", "MSCRED", "Vanilla_LSTM"]


def _read_json(path: Path) -> dict[str, Any]:
    if not os.path.exists(_fs_path(path)):
        return {}
    with open(_fs_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not os.path.exists(_fs_path(path)):
        return records
    with open(_fs_path(path), "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def _record_key(record: dict[str, Any]) -> tuple[str, int]:
    return str(record["source_file"]), int(record["sample_index"])


def _index_records(records: list[dict[str, Any]]) -> dict[tuple[str, int], dict[str, Any]]:
    return {_record_key(record): record for record in records}


def _confusion_delta(repo_records: list[dict[str, Any]], source_records: list[dict[str, Any]]) -> dict[str, Any]:
    repo_by_key = _index_records(repo_records)
    source_by_key = _index_records(source_records)
    repo_keys = set(repo_by_key)
    source_keys = set(source_by_key)
    common_keys = sorted(repo_keys & source_keys)
    repo_only = sorted(repo_keys - source_keys)
    source_only = sorted(source_keys - repo_keys)
    common_repo = [repo_by_key[key] for key in common_keys]
    common_source = [source_by_key[key] for key in common_keys]
    y_true_mismatch = sum(
        int(repo_by_key[key]["y_true_original"]) != int(source_by_key[key]["y_true_original"])
        for key in common_keys
    )
    pred_disagreements = [
        key
        for key in common_keys
        if int(repo_by_key[key]["y_pred_original"]) != int(source_by_key[key]["y_pred_original"])
    ]
    disagreements_by_truth: dict[str, int] = {"true_0": 0, "true_1": 0}
    for key in pred_disagreements:
        truth = int(repo_by_key[key]["y_true_original"])
        disagreements_by_truth[f"true_{truth}"] += 1
    repo_metrics_common = _metrics_from_records(common_repo)
    source_metrics_common = _metrics_from_records(common_source)
    repo_metrics_full = _metrics_from_records(repo_records)
    source_metrics_full = _metrics_from_records(source_records)
    repo_pred_positive = int(np.sum([int(record["y_pred_original"]) for record in repo_records]))
    source_pred_positive = int(np.sum([int(record["y_pred_original"]) for record in source_records]))
    return {
        "repository_record_count": int(len(repo_records)),
        "source_record_count": int(len(source_records)),
        "common_record_count": int(len(common_keys)),
        "repository_only_count": int(len(repo_only)),
        "source_only_count": int(len(source_only)),
        "record_set_identical": not repo_only and not source_only,
        "y_true_mismatch_count_on_common": int(y_true_mismatch),
        "y_true_identical_on_common": y_true_mismatch == 0,
        "prediction_disagreement_count_on_common": int(len(pred_disagreements)),
        "prediction_agreement_rate_on_common": float(1.0 - len(pred_disagreements) / max(1, len(common_keys))),
        "prediction_disagreements_by_truth": disagreements_by_truth,
        "repository_predicted_positive_count": repo_pred_positive,
        "source_predicted_positive_count": source_pred_positive,
        "predicted_positive_delta_source_minus_repository": int(source_pred_positive - repo_pred_positive),
        "repository_metrics_full": repo_metrics_full,
        "source_metrics_full": source_metrics_full,
        "repository_metrics_on_common": repo_metrics_common,
        "source_metrics_on_common": source_metrics_common,
        "metric_delta_source_minus_repository_on_common": {
            "f1": float(source_metrics_common["f1"] - repo_metrics_common["f1"]),
            "far_percent": float(source_metrics_common["far_percent"] - repo_metrics_common["far_percent"]),
            "mar_percent": float(source_metrics_common["mar_percent"] - repo_metrics_common["mar_percent"]),
        },
    }


def build_skab_source_rerun_delta_audit(
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    *,
    methods: list[str] | None = None,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    methods = methods or DEFAULT_METHODS
    source_audit = _read_json(output_dir / "skab_official_source_rerun_audit.json")
    unmatched = sorted(str(method) for method in source_audit.get("unmatched_source_rerun_methods", []))
    rows: list[dict[str, Any]] = []
    for method in methods:
        repo_records = _read_jsonl(output_dir / REPOSITORY_RECORD_DIR / f"{method}.jsonl")
        source_records = _read_jsonl(output_dir / SOURCE_RECORD_DIR / f"{method}.jsonl")
        if not repo_records or not source_records:
            rows.append(
                {
                    "method": method,
                    "status": "missing_records",
                    "repository_record_present": bool(repo_records),
                    "source_record_present": bool(source_records),
                }
            )
            continue
        delta = _confusion_delta(repo_records, source_records)
        status = (
            "prediction_delta_only"
            if delta["record_set_identical"] and delta["y_true_identical_on_common"]
            else "record_or_label_delta"
        )
        rows.append(
            {
                "method": method,
                "status": status,
                **delta,
                "interpretation": (
                    "Repository pickle and source-rerun records cover the same keyed samples with identical labels; "
                    "the leaderboard delta is therefore from prediction differences under the rerun, not from row alignment or label mismatch."
                    if status == "prediction_delta_only"
                    else "Repository pickle and source-rerun records differ in keyed sample coverage or labels; this requires protocol/alignment investigation."
                ),
            }
        )
    covered_methods = sorted(row["method"] for row in rows if row.get("status") == "prediction_delta_only")
    missing_delta_methods = sorted(set(unmatched) - set(covered_methods))
    gates = {
        "source_rerun_audit_present": bool(source_audit),
        "unmatched_methods_covered": not missing_delta_methods,
        "records_present_for_all_methods": all(row.get("status") != "missing_records" for row in rows),
        "record_sets_identical_for_unmatched_methods": all(
            row.get("record_set_identical")
            for row in rows
            if row.get("method") in unmatched
        ),
        "labels_identical_for_unmatched_methods": all(
            row.get("y_true_identical_on_common")
            for row in rows
            if row.get("method") in unmatched
        ),
        "deltas_attributed_to_predictions": all(
            row.get("status") == "prediction_delta_only"
            for row in rows
            if row.get("method") in unmatched
        ),
    }
    missing_gates = [name for name, value in gates.items() if not value]
    return {
        "version": VERSION,
        "status": "source_rerun_delta_profile_complete" if not missing_gates else "source_rerun_delta_profile_partial",
        "claim_boundary": (
            "This audit explains source-rerun leaderboard deltas at the frozen-record level. "
            "It does not convert unmatched source reruns into official leaderboard matches."
        ),
        "unmatched_source_rerun_methods": unmatched,
        "covered_delta_methods": covered_methods,
        "missing_delta_methods": missing_delta_methods,
        "gates": gates,
        "missing_gates": missing_gates,
        "rows": rows,
        "global_interpretation": (
            "For the covered unmatched methods, official repository pickles and source reruns have identical keyed sample sets "
            "and labels. The remaining delta is prediction-level and is consistent with stochastic deep-model reruns, "
            "modern TensorFlow/Keras execution differences, and the fact that official pickles are fixed precomputed outputs."
        ),
        "next_actions": [
            "Do not use unmatched source reruns as official leaderboard matches.",
            "Use this audit to distinguish prediction-level rerun variance from split/label/alignment errors.",
            "If exact leaderboard matching is required, recover the original dependency/runtime stack or use the official precomputed rows as repository-result evidence only.",
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# SKAB Source-Rerun Delta Audit",
        "",
        f"- Version: {payload['version']}",
        f"- Status: {payload['status']}",
        f"- Claim boundary: {payload['claim_boundary']}",
        f"- Unmatched source-rerun methods: {', '.join(payload['unmatched_source_rerun_methods']) or 'none'}",
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
            "## Delta Rows",
            "",
            "| Method | Status | Records repo/source/common | Pred disagreement | Agreement | Source-repo F1 | Source-repo FAR | Source-repo MAR | Interpretation |",
            "|---|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in payload["rows"]:
        if row.get("status") == "missing_records":
            lines.append(
                f"| {row['method']} | missing_records | 0 | 0 | 0.0000 | 0.0000 | 0.00 | 0.00 | missing repository or source records |"
            )
            continue
        delta = row["metric_delta_source_minus_repository_on_common"]
        lines.append(
            "| {method} | {status} | {repo}/{source}/{common} | {disagree} | {agree:.4f} | {f1:+.4f} | {far:+.2f} | {mar:+.2f} | {interpretation} |".format(
                method=row["method"],
                status=row["status"],
                repo=int(row["repository_record_count"]),
                source=int(row["source_record_count"]),
                common=int(row["common_record_count"]),
                disagree=int(row["prediction_disagreement_count_on_common"]),
                agree=float(row["prediction_agreement_rate_on_common"]),
                f1=float(delta["f1"]),
                far=float(delta["far_percent"]),
                mar=float(delta["mar_percent"]),
                interpretation=row["interpretation"],
            )
        )
    lines.extend(["", "## Interpretation", "", payload["global_interpretation"], "", "## Next Actions", ""])
    lines.extend(f"- {action}" for action in payload["next_actions"])
    lines.append("")
    return "\n".join(lines)


def write_skab_source_rerun_delta_audit(output_dir: Path | str = DEFAULT_OUTPUT_DIR) -> list[Path]:
    output_dir = Path(output_dir)
    payload = build_skab_source_rerun_delta_audit(output_dir=output_dir)
    json_path = output_dir / "skab_source_rerun_delta_audit.json"
    md_path = output_dir / "skab_source_rerun_delta_audit.md"
    _write_json(json_path, payload)
    _write_text(md_path, render_markdown(payload))
    return [json_path, md_path]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Audit SKAB source-rerun delta attribution.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    for path in write_skab_source_rerun_delta_audit(args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
