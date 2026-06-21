from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).absolute().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "knowledge_exports" / "aaai_exact_native_protocol_gate"
DEFAULT_RUN_DIR = REPO_ROOT / "knowledge_exports" / "cmapss_mdfa_source_matched_source2d_smoke"
DEFAULT_RUNNER = REPO_ROOT / "Scripts" / "run_cmapss_mdfa_source_matched.py"
VERSION = "cmapss-mdfa-runner-audit-v1"
EXPECTED_SUBSETS = {"FD001", "FD002", "FD003", "FD004"}
EXPECTED_TERMINAL_RECORDS = 707


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
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


def _seed_files(run_dir: Path) -> list[Path]:
    if not os.path.isdir(_fs_path(run_dir)):
        return []
    return sorted(Path(path) for path in Path(run_dir).glob("cmapss_mdfa_source_matched_seed*.json"))


def _seed_payloads(run_dir: Path) -> list[dict[str, Any]]:
    payloads = []
    for path in _seed_files(run_dir):
        payload = _read_json_if_present(path)
        if payload:
            payloads.append(payload)
    return payloads


def _subset_rows_from_summary(summary: dict[str, Any] | None) -> list[dict[str, Any]]:
    rows = summary.get("subset_seed_rows") if summary else []
    return rows if isinstance(rows, list) else []


def _diagnostic_rows(seed_payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for payload in seed_payloads:
        for subset in payload.get("subsets", []) or []:
            diag = subset.get("diagnostics") if isinstance(subset.get("diagnostics"), dict) else {}
            rows.append(
                {
                    "seed": int(payload.get("seed", subset.get("seed", -1))),
                    "subset": str(subset.get("subset")),
                    "epochs": int(diag.get("epochs", 0) or 0),
                    "batch_size": int(diag.get("batch_size", 0) or 0),
                    "learning_rate": float(diag.get("learning_rate", 0.0) or 0.0),
                    "dropout": float(diag.get("dropout", 0.0) or 0.0),
                    "conv_formulation": str(diag.get("conv_formulation") or subset.get("conv_formulation") or ""),
                    "lr_scheduler": str(diag.get("lr_scheduler") or (subset.get("run_config") or {}).get("lr_scheduler") or ""),
                    "feature_policy": str(subset.get("feature_policy") or (subset.get("run_config") or {}).get("feature_policy") or ""),
                    "condition_normalization": str(
                        subset.get("condition_normalization")
                        or (subset.get("run_config") or {}).get("condition_normalization")
                        or "none"
                    ),
                    "append_condition_onehot": bool(
                        subset.get("append_condition_onehot")
                        or (subset.get("run_config") or {}).get("append_condition_onehot")
                        or False
                    ),
                    "dilation_rates": list(diag.get("dilation_rates") or []),
                    "test_windows": int(subset.get("test_windows", 0) or 0),
                    "train_windows": int(subset.get("train_windows", 0) or 0),
                    "prediction_records": int(len(subset.get("rul_prediction_records") or [])),
                    "alignment_status": str(subset.get("alignment_status")),
                }
            )
    return rows


def build_cmapss_mdfa_runner_audit(
    run_dir: Path = DEFAULT_RUN_DIR,
    runner_path: Path = DEFAULT_RUNNER,
) -> dict[str, Any]:
    run_dir = Path(run_dir)
    summary_path = run_dir / "cmapss_mdfa_source_matched_summary.json"
    summary = _read_json_if_present(summary_path)
    seed_payloads = _seed_payloads(run_dir)
    subset_rows = _subset_rows_from_summary(summary)
    diag_rows = _diagnostic_rows(seed_payloads)
    subsets_present = {str(row.get("subset")) for row in subset_rows}
    seeds_present = sorted({int(row.get("seed", -1)) for row in subset_rows})
    completed_pairs = {
        (int(row.get("seed", -1)), str(row.get("subset")))
        for row in subset_rows
        if int(row.get("seed", -1)) >= 0
    }
    complete_subset_archive_for_present_seeds = bool(seeds_present) and all(
        (int(seed), str(subset)) in completed_pairs
        for seed in seeds_present
        for subset in EXPECTED_SUBSETS
    )
    full_three_seed_archive_present = (
        len([seed for seed in seeds_present if seed >= 0]) >= 3 and complete_subset_archive_for_present_seeds
    )
    all_diag_budget = bool(diag_rows) and all(
        int(row["epochs"]) >= 100
        and int(row["batch_size"]) == 32
        and abs(float(row["learning_rate"]) - 0.0001) < 1.0e-12
        and abs(float(row["dropout"]) - 0.3) < 1.0e-12
        and str(row["conv_formulation"]) == "source_2d"
        and list(row["dilation_rates"]) == [1, 2, 4]
        for row in diag_rows
    )
    total_prediction_records = int((summary or {}).get("n_prediction_records", 0) or 0)
    expected_records_for_present_seeds = EXPECTED_TERMINAL_RECORDS * len([seed for seed in seeds_present if seed >= 0])
    gates = {
        "runner_code_present": os.path.exists(_fs_path(runner_path)),
        "smoke_summary_present": summary is not None,
        "smoke_seed_archive_present": bool(seed_payloads),
        "smoke_all_subsets_present": EXPECTED_SUBSETS.issubset(subsets_present),
        "smoke_terminal_prediction_records_present": total_prediction_records == EXPECTED_TERMINAL_RECORDS,
        "terminal_prediction_records_complete_for_present_seeds": bool(expected_records_for_present_seeds)
        and total_prediction_records == expected_records_for_present_seeds,
        "smoke_claim_safe": bool(summary)
        and str(summary.get("status")) == "source_matched_candidate_not_exact_reproduction",
        "full_three_seed_archive_present": full_three_seed_archive_present,
        "full_source_budget_100epoch_present": full_three_seed_archive_present and all_diag_budget,
        "pca_key_sensor_exact_policy_verified": False,
        "safe_to_promote_mdfa_to_exact_reproduction": False,
    }
    status = (
        "full_budget_archive_materialized_preprocessing_pending"
        if gates["full_three_seed_archive_present"] and gates["full_source_budget_100epoch_present"]
        else "smoke_runner_materialized_full_budget_pending"
    )
    return {
        "version": VERSION,
        "status": status,
        "claim_boundary": (
            "The MDFA source-matched runner and all-subset smoke prediction archive are materialized. "
            "The smoke run is not a published reproduction because it uses a reduced training budget and unresolved PCA/key-sensor policy."
        ),
        "run_dir": str(run_dir),
        "runner_path": str(runner_path),
        "summary_path": str(summary_path),
        "gates": gates,
        "missing_gates": [name for name, value in gates.items() if not value],
        "smoke_metrics": (summary or {}).get("overall_metrics"),
        "subsets_present": sorted(subsets_present),
        "seeds_present": seeds_present,
        "completed_subset_seed_count": int(len(completed_pairs)),
        "expected_records_for_present_seeds": int(expected_records_for_present_seeds),
        "diagnostic_rows": diag_rows,
        "next_actions": [
            "Run the MDFA runner with source_2d formulation, seeds 42/43/44, epochs=100, batch=32, lr=0.0001, dropout=0.3, and full train windows.",
            "Decide and freeze the PCA/key-sensor policy from the MDFA source: all 24 variables with train-only PCA, Table 4 key sensors, or Table 6 screened variables.",
            "Compare FD001-FD004 RMSE/Score against MDFA Table 5 only after the full-budget archive exists.",
            "Keep current smoke metrics out of SOTA tables; use them only as runner and archive readiness evidence.",
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# C-MAPSS MDFA Runner Audit",
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
            "## Smoke Diagnostic Rows",
            "",
            "| Subset | Seed | Formulation | Feature policy | Condition policy | LR scheduler | Epochs | Batch | LR | Dropout | Test windows | Prediction records |",
            "|---|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in payload["diagnostic_rows"]:
        lines.append(
            "| {subset} | {seed} | {formulation} | {feature_policy} | {condition}{onehot} | {lr_scheduler} | {epochs} | {batch} | {lr:.6f} | {dropout:.2f} | {test} | {records} |".format(
                subset=row["subset"],
                seed=int(row["seed"]),
                formulation=row["conv_formulation"] or "-",
                feature_policy=row["feature_policy"] or "-",
                condition=row["condition_normalization"] or "none",
                onehot="+onehot" if bool(row.get("append_condition_onehot")) else "",
                lr_scheduler=row["lr_scheduler"] or "-",
                epochs=int(row["epochs"]),
                batch=int(row["batch_size"]),
                lr=float(row["learning_rate"]),
                dropout=float(row["dropout"]),
                test=int(row["test_windows"]),
                records=int(row["prediction_records"]),
            )
        )
    lines.extend(["", "## Next Actions", ""])
    lines.extend(f"- {item}" for item in payload["next_actions"])
    return "\n".join(lines).rstrip() + "\n"


def write_cmapss_mdfa_runner_audit(
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    run_dir: Path | str = DEFAULT_RUN_DIR,
    runner_path: Path | str = DEFAULT_RUNNER,
) -> list[Path]:
    output_dir = Path(output_dir)
    payload = build_cmapss_mdfa_runner_audit(Path(run_dir), Path(runner_path))
    json_path = output_dir / "cmapss_mdfa_runner_audit.json"
    md_path = output_dir / "cmapss_mdfa_runner_audit.md"
    _write_json(json_path, payload)
    _write_text(md_path, render_markdown(payload))
    return [json_path, md_path]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Audit C-MAPSS MDFA source-matched runner readiness.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--runner-path", type=Path, default=DEFAULT_RUNNER)
    args = parser.parse_args(argv)
    for path in write_cmapss_mdfa_runner_audit(args.output_dir, args.run_dir, args.runner_path):
        print(path)


if __name__ == "__main__":
    main()
