from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


VERSION = "skab-official-baseline-gate-v1"


def _find_repo_root() -> Path:
    """Prefer the active workspace over a resolved recovery/symlink target."""
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
        if (candidate / "Scripts" / "skab_official_baseline_gate.py").exists() and (candidate / "knowledge_exports").exists():
            return candidate
    return module_root


REPO_ROOT = _find_repo_root()
EXPORT_DIR = REPO_ROOT / "knowledge_exports"
DEFAULT_OUTPUT_DIR = EXPORT_DIR / "aaai_exact_native_protocol_gate"

STYLE_BASELINE_PATH = (
    EXPORT_DIR
    / "external_baseline_protocol_runs"
    / "skab_external_baselines_native_records_usad_tranad_w48_e8.json"
)
AT_WRAPPER_PATH = (
    EXPORT_DIR
    / "external_baseline_protocol_runs"
    / "anomaly_transformer_official_skab_wrapper_3seed_budget_probe.json"
)
AT_ADAPTER_PATH = (
    EXPORT_DIR
    / "external_baseline_protocol_runs"
    / "anomaly_transformer_official_skab_adapter"
    / "anomaly_transformer_official_skab_adapter.json"
)
OFFICIAL_REPO_SNAPSHOT_PATH = EXPORT_DIR / "external_baseline_official_repos" / "official_external_repo_snapshot.json"
OFFICIAL_REPO_CHECKOUT_PATH = EXPORT_DIR / "external_baseline_official_repos" / "official_external_repo_checkout_audit.json"
OFFICIAL_REPOSITORY_BASELINE_AUDIT_PATH = DEFAULT_OUTPUT_DIR / "skab_official_repository_baseline_audit.json"
OFFICIAL_SOURCE_RERUN_AUDIT_PATH = DEFAULT_OUTPUT_DIR / "skab_official_source_rerun_audit.json"


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _read_json(path: Path) -> dict[str, Any]:
    if not os.path.exists(_fs_path(path)):
        return {}
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


def _mean_std(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"mean": None, "std": None}
    return {"mean": float(mean(values)), "std": float(pstdev(values))}


def _prediction_records_present(item: dict[str, Any]) -> bool:
    records = item.get("prediction_records") or item.get("classification_prediction_records")
    if not isinstance(records, list) or not records:
        return False
    sample = records[0]
    required = {"y_true_original", "y_pred_original", "run_id", "changepoint"}
    return isinstance(sample, dict) and required.issubset(set(sample))


def _style_baseline_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    methods = [str(method) for method in payload.get("methods", [])]
    for method in methods:
        macro: list[float] = []
        far: list[float] = []
        mar: list[float] = []
        frozen_count = 0
        seed_count = 0
        for run in payload.get("runs", []):
            item = run.get(method)
            if not isinstance(item, dict):
                continue
            seed_count += 1
            metrics = item.get("metrics") or {}
            binary = ((item.get("protocol") or {}).get("binary") or {})
            if metrics.get("macro_f1") is not None:
                macro.append(float(metrics["macro_f1"]))
            if binary.get("far_percent") is not None:
                far.append(float(binary["far_percent"]))
            if binary.get("mar_percent") is not None:
                mar.append(float(binary["mar_percent"]))
            if _prediction_records_present(item):
                frozen_count += 1
        rows.append(
            {
                "method": method,
                "source_family": "external_style_reconstruction",
                "n_seeds": seed_count,
                "macro_f1": _mean_std(macro),
                "far_percent": _mean_std(far),
                "mar_percent": _mean_std(mar),
                "frozen_prediction_seed_count": frozen_count,
                "official_source_used": False,
                "official_external_score": False,
                "claim_boundary": "USAD/TranAD-style fair baselines with frozen native records; not official repository reproductions.",
            }
        )
    return rows


def _anomaly_transformer_official_row(payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload.get("summary") or {}
    runs = payload.get("runs") or []
    alignments = [run.get("protocol_alignment") or {} for run in runs if isinstance(run, dict)]
    frozen_records_present = any(
        _prediction_records_present(run.get("matched_row_level") or {})
        or _prediction_records_present(run.get("official_flattened_no_adjustment") or {})
        for run in runs
        if isinstance(run, dict)
    )
    return {
        "method": "anomaly_transformer_official_source_wrapper",
        "source_family": "official_source_patched_skab_adapter",
        "n_seeds": len(runs),
        "official_commit": payload.get("official_commit"),
        "macro_f1": {
            "mean": summary.get("macro_f1_mean"),
            "std": summary.get("macro_f1_std"),
        },
        "far_percent": {
            "mean": summary.get("far_percent_mean"),
            "std": summary.get("far_percent_std"),
        },
        "mar_percent": {
            "mean": summary.get("mar_percent_mean"),
            "std": summary.get("mar_percent_std"),
        },
        "official_source_used": all(bool(item.get("official_source_model_used")) for item in alignments) if alignments else False,
        "validation_only_thresholds": all(bool(item.get("validation_only_thresholds")) for item in alignments) if alignments else False,
        "point_adjustment": sorted({str(item.get("point_adjustment")) for item in alignments}) if alignments else [],
        "official_external_score": any(bool(item.get("official_external_score")) for item in alignments),
        "frozen_prediction_records_present": frozen_records_present,
        "claim_boundary": payload.get("claim_boundary") or "Official-source wrapper; not an official paper score.",
    }


def _repo_provenance(snapshot: dict[str, Any], checkout: dict[str, Any]) -> dict[str, Any]:
    rows = snapshot.get("rows") or []
    anomaly = next((row for row in rows if str(row.get("name")).lower() == "anomaly transformer"), {})
    checkout_rows = checkout.get("rows") or []
    anomaly_checkout = next((row for row in checkout_rows if str(row.get("name")).lower() == "anomaly transformer"), {})
    return {
        "snapshot_present": bool(snapshot),
        "checkout_present": bool(checkout),
        "anomaly_transformer_head_commit": anomaly.get("resolved_head_commit"),
        "anomaly_transformer_checkout_verified": bool(anomaly_checkout.get("commit_matches_snapshot")),
        "provenance_claim_boundary": checkout.get("claim_gate") or snapshot.get("claim_gate"),
    }


def _official_repository_baseline_audit() -> dict[str, Any]:
    audit = _read_json(OFFICIAL_REPOSITORY_BASELINE_AUDIT_PATH)
    if audit:
        return audit
    try:
        from skab_official_repository_baseline_audit import build_skab_official_repository_baseline_audit

        return build_skab_official_repository_baseline_audit(output_dir=DEFAULT_OUTPUT_DIR)
    except Exception:
        return {}


def _official_repository_precomputed_rows(audit: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in audit.get("method_rows", []):
        if not row.get("expected_leaderboard"):
            continue
        metrics = row.get("metrics") or {}
        rows.append(
            {
                "method": row.get("method"),
                "leaderboard_name": row.get("leaderboard_name"),
                "n_prediction_records": row.get("n_prediction_records"),
                "f1": metrics.get("f1"),
                "far_percent": metrics.get("far_percent"),
                "mar_percent": metrics.get("mar_percent"),
                "matches_expected_leaderboard": row.get("matches_expected_leaderboard"),
                "record_file": row.get("record_file"),
                "claim_boundary": "Official SKAB repository precomputed result pickle recomputed with frozen records; not a notebook/source rerun.",
            }
        )
    return rows


def _official_source_rerun_audit() -> dict[str, Any]:
    audit = _read_json(OFFICIAL_SOURCE_RERUN_AUDIT_PATH)
    if audit:
        return audit
    try:
        from skab_official_source_rerun_audit import build_skab_official_source_rerun_audit

        return build_skab_official_source_rerun_audit(output_dir=DEFAULT_OUTPUT_DIR)
    except Exception:
        return {}


def _official_source_rerun_rows(audit: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in audit.get("source_rerun_rows", []):
        metrics = row.get("metrics") or {}
        rows.append(
            {
                "method": row.get("method"),
                "notebook": row.get("notebook"),
                "n_prediction_records": row.get("n_prediction_records"),
                "f1": metrics.get("f1"),
                "far_percent": metrics.get("far_percent"),
                "mar_percent": metrics.get("mar_percent"),
                "matches_expected_leaderboard": row.get("matches_expected_leaderboard"),
                "record_file": row.get("record_file"),
                "claim_boundary": row.get("claim_boundary"),
            }
        )
    return rows


def build_skab_official_baseline_gate() -> dict[str, Any]:
    style_payload = _read_json(STYLE_BASELINE_PATH)
    at_payload = _read_json(AT_WRAPPER_PATH)
    at_adapter = _read_json(AT_ADAPTER_PATH)
    repo_snapshot = _read_json(OFFICIAL_REPO_SNAPSHOT_PATH)
    repo_checkout = _read_json(OFFICIAL_REPO_CHECKOUT_PATH)
    official_repo_audit = _official_repository_baseline_audit()
    official_source_audit = _official_source_rerun_audit()

    style_rows = _style_baseline_rows(style_payload)
    official_rows = [_anomaly_transformer_official_row(at_payload)] if at_payload else []
    official_precomputed_rows = _official_repository_precomputed_rows(official_repo_audit)
    official_source_rows = _official_source_rerun_rows(official_source_audit)
    official_repo_gates = official_repo_audit.get("gates") or {}
    official_source_gates = official_source_audit.get("gates") or {}
    official_source_delta_audit = official_source_audit.get("source_rerun_delta_audit") or {}
    style_records_complete = bool(style_rows) and all(
        int(row["frozen_prediction_seed_count"]) == int(row["n_seeds"]) and int(row["n_seeds"]) >= 3
        for row in style_rows
    )
    official_source_wrapper_present = bool(official_rows) and all(bool(row["official_source_used"]) for row in official_rows)
    official_source_wrapper_has_frozen_records = bool(official_rows) and all(
        bool(row["frozen_prediction_records_present"]) for row in official_rows
    )
    official_external_score_safe = bool(official_rows) and not any(
        bool(row["official_external_score"]) for row in official_rows
    )
    official_repo_artifacts_present = all(
        bool(official_repo_gates.get(name))
        for name in [
            "official_skab_repository_extracted",
            "official_notebooks_present",
            "official_core_modules_present",
            "official_result_pickles_present",
        ]
    )
    official_precomputed_rows_recomputed = bool(official_precomputed_rows) and all(
        [
            bool(official_repo_gates.get("official_result_pickles_align_to_raw_data")),
            bool(official_repo_gates.get("official_outlier_leaderboard_recomputed")),
            bool(official_repo_gates.get("official_frozen_prediction_records_materialized")),
        ]
    )
    partial_source_rerun_evidence = bool(official_source_rows) and all(
        [
            bool(official_source_gates.get("source_rerun_t2_family_recomputed")),
            bool(official_source_gates.get("source_rerun_frozen_records_materialized")),
        ]
    )
    gates = {
        "style_baseline_frozen_records_present": style_records_complete,
        "official_repo_provenance_present": bool(repo_snapshot) and bool(repo_checkout),
        "anomaly_transformer_official_source_adapter_present": bool(at_adapter),
        "anomaly_transformer_official_source_wrapper_present": official_source_wrapper_present,
        "official_source_wrapper_frozen_prediction_records_present": official_source_wrapper_has_frozen_records,
        "official_external_score_claim_blocked": official_external_score_safe,
        "skab_official_repository_artifacts_present": official_repo_artifacts_present,
        "skab_official_precomputed_outlier_baselines_recomputed": official_precomputed_rows_recomputed,
        "skab_official_partial_source_rerun_evidence_present": partial_source_rerun_evidence,
        "skab_official_repository_notebook_baselines_reproduced": bool(
            official_repo_gates.get("official_notebooks_rerun_from_source", False)
            and official_source_gates.get("official_notebooks_rerun_from_source", False)
        ),
        "exact_split_preprocessing_budget_matched": False,
        "safe_to_flip_skab_official_baseline_gate": False,
    }
    missing = [name for name, value in gates.items() if not value]
    return {
        "version": VERSION,
        "status": "skab_official_baseline_gate_not_closed",
        "claim_boundary": (
            "Current SKAB external evidence includes fair reconstruction baselines with frozen records and an "
            "official-source Anomaly Transformer wrapper, but it is not an official SKAB leaderboard or paper-score reproduction."
        ),
        "gates": gates,
        "missing_gates": missing,
        "repo_provenance": _repo_provenance(repo_snapshot, repo_checkout),
        "style_baseline_rows": style_rows,
        "official_source_rows": official_rows,
        "official_repository_audit_status": official_repo_audit.get("status"),
        "official_repository_precomputed_rows": official_precomputed_rows,
        "official_source_rerun_audit_status": official_source_audit.get("status"),
        "official_source_rerun_rows": official_source_rows,
        "official_source_rerun_unmatched_methods": official_source_audit.get("unmatched_source_rerun_methods") or [],
        "official_source_rerun_delta_audit": official_source_delta_audit,
        "official_source_rerun_blockers": [
            name for name, value in official_source_gates.items() if not value
        ],
        "adapter_summary": {
            "overall_status": at_adapter.get("overall_status"),
            "seed_count": len(at_adapter.get("seeds") or []),
            "claim_boundary": at_adapter.get("claim_boundary"),
        },
        "next_actions": [
            "Run or faithfully port the official SKAB repository notebook/core baselines, not only style-matched reconstruction models.",
            "Use the official precomputed leaderboard rows only as frozen repository-result evidence until notebook/source rerun is closed.",
            (
                "Use T2/T2+Q, Isolation Forest, MSET, Vanilla-AE, and Conv-AE source reruns as partial provenance evidence; keep LSTM-AE/MSCRED/Vanilla-LSTM as diagnostic reruns because their deltas are prediction-level rerun variance rather than official leaderboard matches; keep ArimaFD blocked until rerun or formally scoped out."
                if official_source_delta_audit.get("explained")
                else "Use T2/T2+Q, Isolation Forest, MSET, Vanilla-AE, and Conv-AE source reruns as partial provenance evidence; keep LSTM-AE/MSCRED/Vanilla-LSTM as diagnostic reruns until their deltas are explained, and keep ArimaFD blocked until rerun or formally scoped out."
            ),
            "Add the official SKAB notebook/core baseline predictions to the same frozen-record audit format used by the fair controls and official-source wrapper.",
            "Freeze the exact split, preprocessing, threshold, event-window, and budget contract across proposed and baseline models.",
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# SKAB Official Baseline Gate",
        "",
        f"- Version: {payload['version']}",
        f"- Status: {payload['status']}",
        f"- Claim boundary: {payload['claim_boundary']}",
        "",
        "## Gate Status",
        "",
        "| Gate | Status |",
        "|---|---:|",
    ]
    for gate, value in payload["gates"].items():
        lines.append(f"| {gate} | {'pass' if value else 'blocked'} |")
    lines.extend(["", "## Style Baselines", "", "| Method | Seeds | Macro-F1 | FAR | MAR | Frozen records | Boundary |", "|---|---:|---:|---:|---:|---:|---|"])
    for row in payload["style_baseline_rows"]:
        macro = row["macro_f1"]
        far = row["far_percent"]
        mar = row["mar_percent"]
        lines.append(
            "| {method} | {seeds} | {macro_mean:.4f} +/- {macro_std:.4f} | {far_mean:.2f} | {mar_mean:.2f} | {frozen}/{seeds} | {boundary} |".format(
                method=row["method"],
                seeds=int(row["n_seeds"]),
                macro_mean=float(macro["mean"] or 0.0),
                macro_std=float(macro["std"] or 0.0),
                far_mean=float(far["mean"] or 0.0),
                mar_mean=float(mar["mean"] or 0.0),
                frozen=int(row["frozen_prediction_seed_count"]),
                boundary=row["claim_boundary"],
            )
        )
    lines.extend(["", "## Official-Source Adapted Controls", "", "| Method | Seeds | Macro-F1 | FAR | Official score? | Frozen records? | Boundary |", "|---|---:|---:|---:|---:|---:|---|"])
    for row in payload["official_source_rows"]:
        macro = row["macro_f1"]
        far = row["far_percent"]
        lines.append(
            "| {method} | {seeds} | {macro_mean:.4f} +/- {macro_std:.4f} | {far_mean:.2f} | {official} | {frozen} | {boundary} |".format(
                method=row["method"],
                seeds=int(row["n_seeds"]),
                macro_mean=float(macro["mean"] or 0.0),
                macro_std=float(macro["std"] or 0.0),
                far_mean=float(far["mean"] or 0.0),
                official="yes" if row["official_external_score"] else "no",
                frozen="yes" if row["frozen_prediction_records_present"] else "no",
                boundary=row["claim_boundary"],
            )
        )
    lines.extend(
        [
            "",
            "## Official Repository Precomputed Rows",
            "",
            "| Method | Records | F1 | FAR | MAR | README match | Frozen record file | Boundary |",
            "|---|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for row in payload["official_repository_precomputed_rows"]:
        lines.append(
            "| {method} | {records} | {f1:.4f} | {far:.2f} | {mar:.2f} | {match} | `{record}` | {boundary} |".format(
                method=row["method"],
                records=int(row["n_prediction_records"] or 0),
                f1=float(row["f1"] or 0.0),
                far=float(row["far_percent"] or 0.0),
                mar=float(row["mar_percent"] or 0.0),
                match="yes" if row["matches_expected_leaderboard"] else "no",
                record=row["record_file"] or "",
                boundary=row["claim_boundary"],
            )
        )
    lines.extend(
        [
            "",
            "## Official Notebook/Core Source Rerun Rows",
            "",
            "| Method | Notebook | Records | F1 | FAR | MAR | README match | Frozen record file | Boundary |",
            "|---|---|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for row in payload["official_source_rerun_rows"]:
        lines.append(
            "| {method} | `{notebook}` | {records} | {f1:.4f} | {far:.2f} | {mar:.2f} | {match} | `{record}` | {boundary} |".format(
                method=row["method"],
                notebook=row["notebook"],
                records=int(row["n_prediction_records"] or 0),
                f1=float(row["f1"] or 0.0),
                far=float(row["far_percent"] or 0.0),
                mar=float(row["mar_percent"] or 0.0),
                match="yes" if row["matches_expected_leaderboard"] else "no",
                record=row["record_file"] or "",
                boundary=row["claim_boundary"] or "",
            )
        )
    if payload["official_source_rerun_blockers"]:
        lines.extend(["", "Source rerun blockers: " + ", ".join(payload["official_source_rerun_blockers"])])
    delta_audit = payload.get("official_source_rerun_delta_audit") or {}
    if delta_audit:
        lines.extend(
            [
                "",
                "Source rerun delta audit: "
                + f"{delta_audit.get('status') or 'missing'}; explained={'yes' if delta_audit.get('explained') else 'no'}; "
                + "covered="
                + (", ".join(str(method) for method in delta_audit.get("covered_delta_methods", [])) or "none"),
            ]
        )
    if payload.get("official_source_rerun_unmatched_methods"):
        lines.extend(
            [
                "",
                "Source rerun unmatched methods: "
                + ", ".join(str(method) for method in payload["official_source_rerun_unmatched_methods"]),
            ]
        )
    lines.extend(["", "## Next Actions", ""])
    lines.extend(f"- {action}" for action in payload["next_actions"])
    lines.append("")
    return "\n".join(lines)


def write_skab_official_baseline_gate(output_dir: Path | str = DEFAULT_OUTPUT_DIR) -> list[Path]:
    output_dir = Path(output_dir)
    payload = build_skab_official_baseline_gate()
    json_path = output_dir / "skab_official_baseline_gate.json"
    md_path = output_dir / "skab_official_baseline_gate.md"
    _write_json(json_path, payload)
    _write_text(md_path, render_markdown(payload))
    return [json_path, md_path]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Write SKAB official/fair baseline gate audit.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    for path in write_skab_official_baseline_gate(args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
