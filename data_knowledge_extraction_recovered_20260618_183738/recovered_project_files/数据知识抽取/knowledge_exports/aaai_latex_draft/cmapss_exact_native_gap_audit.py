from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).absolute().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "knowledge_exports" / "aaai_exact_native_protocol_gate"
VERSION = "cmapss-exact-native-gap-audit-v1"
MDFA_SOURCE_URL = "https://www.mdpi.com/2076-3417/15/17/9813"


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


def _cmapss_gate_row(exact_gate: dict[str, Any]) -> dict[str, Any]:
    for row in exact_gate.get("rows", []):
        if row.get("dataset") == "C-MAPSS":
            return row
    return {}


def _gate(payload: dict[str, Any], name: str) -> bool:
    gates = payload.get("gates") if isinstance(payload.get("gates"), dict) else {}
    return bool(gates.get(name))


def _contract_by_id(contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = contract.get("baseline_contracts") if isinstance(contract.get("baseline_contracts"), list) else []
    return {str(row.get("id")): row for row in rows if isinstance(row, dict)}


def _mdfa_budget_matrix(source_profile: dict[str, Any], strategy: dict[str, Any], ledger: dict[str, Any]) -> list[dict[str, Any]]:
    source = source_profile.get("source") if isinstance(source_profile.get("source"), dict) else {}
    published_hparams = source.get("published_hyperparameters") if isinstance(source.get("published_hyperparameters"), dict) else {}
    decision = strategy.get("decision") if isinstance(strategy.get("decision"), dict) else {}
    gaps = {
        str(row.get("subset")): row
        for row in ledger.get("cmapss_mdfa_source_style_subset_gaps", [])
        if isinstance(row, dict)
    }
    return [
        {
            "subset_group": "MDFA 2025 published protocol",
            "window": published_hparams.get("window_size", 30),
            "epochs": published_hparams.get("epochs", 100),
            "batch_size": published_hparams.get("batch_size", 32),
            "dropout": published_hparams.get("dropout", 0.3),
            "feature_policy": "Table-4/key-sensor PCA policy, exact PCA threshold unresolved",
            "condition_policy": "not machine-readable",
            "claim_use": "reference protocol only",
        },
        {
            "subset_group": "FD001/FD003 selected local branch",
            "window": decision.get("current_fd003_window_size", 80),
            "epochs": 100,
            "batch_size": 32,
            "dropout": "0.1 for FD001; 0.0 selected for FD003",
            "feature_policy": decision.get("current_feature_policy", "all24_pca"),
            "temporal_feature_mode": f"level for FD001; {decision.get('current_fd003_temporal_feature_mode', 'level')} for FD003",
            "condition_policy": "none",
            "fd001_gap_rmse": gaps.get("FD001", {}).get("gap_current_minus_reference"),
            "fd003_gap_rmse": gaps.get("FD003", {}).get("gap_current_minus_reference"),
            "claim_use": "local source-style candidate, not exact MDFA reproduction",
        },
        {
            "subset_group": "FD002/FD004 selected local branch",
            "window": 80,
            "epochs": 100,
            "batch_size": 32,
            "dropout": 0.3,
            "feature_policy": "sensor21_pca",
            "condition_policy": "kmeans6_settings + condition_onehot",
            "fd002_gap_rmse": gaps.get("FD002", {}).get("gap_current_minus_reference"),
            "fd004_gap_rmse": gaps.get("FD004", {}).get("gap_current_minus_reference"),
            "claim_use": "condition-aware local candidate, intentionally deviates from exact MDFA preprocessing",
        },
    ]


def _mdfa_external_source_resolution() -> list[dict[str, Any]]:
    return [
        {
            "field": "paper identity",
            "status": "machine_readable",
            "source": MDFA_SOURCE_URL,
            "evidence": "MDPI article page identifies Applied Sciences 2025, 15(17), 9813 and DOI 10.3390/app15179813.",
        },
        {
            "field": "RUL label cap",
            "status": "machine_readable",
            "source": MDFA_SOURCE_URL,
            "evidence": "The article states a piecewise linear RUL strategy and sets the initial RUL to 125.",
        },
        {
            "field": "C-MAPSS split and subset counts",
            "status": "machine_readable",
            "source": MDFA_SOURCE_URL,
            "evidence": "The article lists FD001-FD004 operating conditions, fault modes, and train/test unit counts.",
        },
        {
            "field": "training hyperparameters",
            "status": "machine_readable",
            "source": MDFA_SOURCE_URL,
            "evidence": "The article lists batch_size 32, window_size 30, epoch 100, Adam, MSE, learning rate 0.0001, and dropout 0.3.",
        },
        {
            "field": "MDFA architecture",
            "status": "machine_readable",
            "source": MDFA_SOURCE_URL,
            "evidence": "The article lists the parallel dilated convolution branches with dilation rates 1, 2, and 4 and attention/fusion module settings.",
        },
        {
            "field": "key sensors",
            "status": "machine_readable",
            "source": MDFA_SOURCE_URL,
            "evidence": "The article's Table 4 lists key C-MAPSS sensor variables including Ps30, T24, T30, P30, Phi, Nf, Nc, and W31/W32.",
        },
        {
            "field": "PCA threshold or per-subset component count",
            "status": "not_machine_readable",
            "source": MDFA_SOURCE_URL,
            "evidence": "The article states that PCA components are selected by cumulative contribution rate and references Figure 4, but does not provide a numeric threshold or exact component counts.",
        },
        {
            "field": "source code or supplementary reproduction package",
            "status": "not_available_from_article_page",
            "source": MDFA_SOURCE_URL,
            "evidence": "The article page exposes no Supplementary or GitHub entry, and the data availability statement says supporting data are available from the corresponding author upon reasonable request.",
        },
    ]


def build_cmapss_exact_native_gap_audit(output_dir: Path | str = DEFAULT_OUTPUT_DIR) -> dict[str, Any]:
    output_dir = Path(output_dir)
    exact_gate = _read_json(output_dir / "aaai_exact_native_protocol_gate.json")
    native_manifest = _read_json(output_dir / "cmapss_native_preprocessing_manifest.json")
    alignment = _read_json(output_dir / "cmapss_published_baseline_alignment.json")
    contract = _read_json(output_dir / "cmapss_published_baseline_contract.json")
    source_profile = _read_json(output_dir / "cmapss_mdfa_source_profile.json")
    runner_audit = _read_json(output_dir / "cmapss_mdfa_runner_audit.json")
    strategy = _read_json(output_dir / "cmapss_mdfa_strategy_probe_audit.json")
    backbone = _read_json(output_dir / "cmapss_rul_backbone_optimization_audit.json")
    pseudo = _read_json(output_dir / "cmapss_pseudo_truncation_validation_audit.json")
    ledger = _read_json(output_dir / "aaai_sota_gap_ledger.json")
    cmapss_row = _cmapss_gate_row(exact_gate)
    mdfa_contract = _contract_by_id(contract).get("mdfa_2025", {})

    gates = {
        "native_exact_nonbaseline_fields_pass": all(
            bool((cmapss_row.get("gates") or {}).get(name))
            for name in [
                "native_task_preserved",
                "exact_public_split",
                "exact_preprocessing",
                "exact_metric",
                "threshold_or_delay_policy",
                "seed_level_prediction_artifacts",
            ]
        ),
        "published_contract_materialized": _gate(contract, "source_registry_present")
        and _gate(contract, "field_matrix_present"),
        "mdfa_open_source_profile_materialized": _gate(source_profile, "open_fulltext_protocol_available")
        and _gate(source_profile, "mdfa_hyperparameters_extracted")
        and _gate(source_profile, "local_unit_counts_match_mdfa_table"),
        "mdfa_local_full_branch_archive_present": _gate(strategy, "full_fd001_fd004_three_seed_archive_present"),
        "mdfa_score_gap_quantified": bool(ledger.get("cmapss_mdfa_source_style_subset_gaps")),
        "exact_published_reproduction_complete": _gate(contract, "exact_published_reproduction_complete"),
        "matched_budget_complete": _gate(contract, "matched_budget_complete"),
        "mdfa_exact_source_policy_verified": _gate(source_profile, "exact_pca_preprocessing_machine_readable")
        and _gate(source_profile, "exact_test_label_policy_machine_readable")
        and _gate(strategy, "safe_to_promote_strategy_to_published_reproduction"),
        "official_sota_admissible": bool(cmapss_row.get("official_sota_claim_admissible")),
    }
    missing_gates = [name for name, value in gates.items() if not value]

    requirement_rows = [
        {
            "requirement": "native C-MAPSS task/split/preprocessing/metric",
            "status": "pass" if gates["native_exact_nonbaseline_fields_pass"] else "blocked",
            "evidence": "exact-native gate and native preprocessing manifest pass all non-baseline C-MAPSS fields",
        },
        {
            "requirement": "published baseline contract",
            "status": "partial" if gates["published_contract_materialized"] else "blocked",
            "evidence": "field-level contract exists, but no published baseline is exact-reproduced",
        },
        {
            "requirement": "MDFA open-source profile",
            "status": "partial" if gates["mdfa_open_source_profile_materialized"] else "blocked",
            "evidence": "open full text, hyperparameters, architecture fields, Table-4 key sensors, and raw-count reconciliation are materialized",
        },
        {
            "requirement": "MDFA local four-subset archive",
            "status": "partial" if gates["mdfa_local_full_branch_archive_present"] else "blocked",
            "evidence": "strategy audit reports a complete FD001-FD004 three-seed local branch archive",
        },
        {
            "requirement": "exact MDFA preprocessing and label policy",
            "status": "blocked",
            "evidence": "PCA cumulative threshold and exact test-label scoring policy are not machine-readable; selected local branches intentionally deviate from MDFA preprocessing",
        },
        {
            "requirement": "matched training budget",
            "status": "blocked",
            "evidence": "local full branches use 100 epochs/batch 32 but selected window/dropout/condition policies are not budget-equivalent to the published MDFA protocol",
        },
        {
            "requirement": "C-MAPSS path fusion",
            "status": "closed_challenger",
            "evidence": "backbone audit keeps path fusion closed until it beats the same-window temporal anchor under the pseudo-terminal validation panel",
        },
    ]

    return {
        "version": VERSION,
        "status": "cmapss_exact_native_gap_protocol_budget_pending",
        "claim_boundary": (
            "This audit separates C-MAPSS score gaps from exact-native protocol gaps. "
            "It does not authorize official or literature-wide SOTA wording."
        ),
        "exact_gate_missing_gates": cmapss_row.get("missing_gates", []),
        "gates": gates,
        "missing_gates": missing_gates,
        "requirement_rows": requirement_rows,
        "mdfa_contract_field_status": mdfa_contract.get("field_status", {}),
        "mdfa_budget_matrix": _mdfa_budget_matrix(source_profile, strategy, ledger),
        "mdfa_external_source_resolution": _mdfa_external_source_resolution(),
        "mdfa_subset_gaps": ledger.get("cmapss_mdfa_source_style_subset_gaps", []),
        "mdfa_mean_gap_current_minus_reference": ledger.get("cmapss_mdfa_source_style_mean_gap_current_minus_reference"),
        "supporting_artifact_status": {
            "native_manifest": native_manifest.get("status"),
            "published_alignment": alignment.get("status"),
            "published_contract": contract.get("status"),
            "mdfa_source_profile": source_profile.get("status"),
            "mdfa_runner_audit": runner_audit.get("status"),
            "mdfa_strategy_probe": strategy.get("status"),
            "backbone_optimization": backbone.get("status"),
            "pseudo_truncation_validation": pseudo.get("status"),
        },
        "next_actions": [
            "Do not spend the next run on broad architecture search; the source audit now shows the MDFA paper is partially machine-readable but does not expose the PCA threshold or code needed for exact reproduction.",
            "For exact MDFA reproduction, obtain the missing PCA threshold/per-subset component policy and any source code from the authors, then rerun the source-compatible window=30/dropout=0.3/batch=32/epoch=100 route with archived per-engine predictions.",
            "For local SOTA-style evidence, target FD001/FD003 residual RMSE gaps while keeping the claim outside official MDFA reproduction wording.",
            "Keep C-MAPSS path fusion as a challenger until it beats the w160/cap150 temporal anchor on the train-only pseudo-terminal validation panel.",
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# C-MAPSS Exact-Native Gap Audit",
        "",
        f"- Version: {payload['version']}",
        f"- Status: {payload['status']}",
        f"- Claim boundary: {payload['claim_boundary']}",
        "- Exact gate missing gates: " + (", ".join(payload["exact_gate_missing_gates"]) or "none"),
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
            "## Requirement Matrix",
            "",
            "| Requirement | Status | Evidence |",
            "|---|---|---|",
        ]
    )
    for row in payload["requirement_rows"]:
        lines.append(f"| {row['requirement']} | {row['status']} | {row['evidence']} |")
    lines.extend(
        [
            "",
            "## MDFA Budget And Protocol Matrix",
            "",
            "| Route | Window | Epochs | Batch | Dropout | Feature policy | Temporal mode | Condition policy | Claim use |",
            "|---|---:|---:|---:|---|---|---|---|---|",
        ]
    )
    for row in payload["mdfa_budget_matrix"]:
        lines.append(
            "| {route} | {window} | {epochs} | {batch} | {dropout} | {feature} | {temporal} | {condition} | {claim} |".format(
                route=row["subset_group"],
                window=row["window"],
                epochs=row["epochs"],
                batch=row["batch_size"],
                dropout=row["dropout"],
                feature=row["feature_policy"],
                temporal=row.get("temporal_feature_mode", "level"),
                condition=row["condition_policy"],
                claim=row["claim_use"],
            )
        )
    lines.extend(
        [
            "",
            "## MDFA External Source Resolution",
            "",
            "| Field | Status | Source | Evidence |",
            "|---|---|---|---|",
        ]
    )
    for row in payload["mdfa_external_source_resolution"]:
        lines.append(f"| {row['field']} | {row['status']} | {row['source']} | {row['evidence']} |")
    lines.extend(
        [
            "",
            "## MDFA Source-Style Subset Gaps",
            "",
            "| Subset | Current RMSE | Reference RMSE | Gap current-reference | Claim boundary |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for row in payload["mdfa_subset_gaps"]:
        lines.append(
            "| {subset} | {current:.4f} | {reference:.4f} | {gap:+.4f} | {boundary} |".format(
                subset=row["subset"],
                current=float(row["current_rmse"]),
                reference=float(row["reference_rmse"]),
                gap=float(row["gap_current_minus_reference"]),
                boundary=row["claim_boundary"],
            )
        )
    lines.extend(["", "## Next Actions", ""])
    lines.extend(f"- {action}" for action in payload["next_actions"])
    lines.append("")
    return "\n".join(lines)


def write_cmapss_exact_native_gap_audit(output_dir: Path | str = DEFAULT_OUTPUT_DIR) -> list[Path]:
    output_dir = Path(output_dir)
    payload = build_cmapss_exact_native_gap_audit(output_dir)
    json_path = output_dir / "cmapss_exact_native_gap_audit.json"
    md_path = output_dir / "cmapss_exact_native_gap_audit.md"
    _write_json(json_path, payload)
    _write_text(md_path, render_markdown(payload))
    return [json_path, md_path]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Audit C-MAPSS exact-native score/protocol gaps.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    for path in write_cmapss_exact_native_gap_audit(args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
