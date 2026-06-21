from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "knowledge_exports" / "aaai_exact_native_protocol_gate"
VERSION = "cmapss-open-protocol-candidate-audit-v1"


CANDIDATE_SOURCES: list[dict[str, Any]] = [
    {
        "id": "mdfa_2025",
        "title": "Remaining Useful Life Prediction for Aero-Engines Based on Multi-Scale Dilated Fusion Attention Model",
        "url": "https://www.mdpi.com/2076-3417/15/17/9813",
        "source_type": "open_fulltext_published_baseline",
        "subset_scope": ["FD001", "FD002", "FD003", "FD004"],
        "model_family": "multi-scale dilated convolution plus channel/spatial attention",
        "extractable_fields": {
            "rul_cap_or_plateau": "125",
            "window_size": "30",
            "batch_size": "32",
            "epochs": "100",
            "optimizer": "Adam",
            "loss": "MSE",
            "learning_rate": "0.0001",
            "dropout": "0.3",
            "preprocessing": "PCA-based dimensionality reduction and key-sensor selection are described.",
            "metrics": "RMSE, MAE, and Score are declared; FD001-FD004 table is reported.",
            "architecture": "dilated branches with dilation rates 1, 2, 4; global pooling; channel/spatial attention; 1x1 compression.",
        },
        "blocking_fields": [
            "The bundled C-MAPSS readme has an FD004 train/test count inconsistency, but the raw-file unique-unit counts match the MDFA table after source-profile reconciliation.",
            "PCA component-selection details and exact train-only fitting procedure are not fully machine-readable from the HTML tables.",
            "No official code snapshot is linked in the current source audit.",
            "No source-matched MDFA runner or seed-level prediction archive exists yet.",
        ],
        "priority": "p0_open_exact_candidate_after_count_reconciliation",
    },
    {
        "id": "acb_2021",
        "title": "Effective Latent Representation for Prediction of Remaining Useful Life",
        "url": "https://www.techscience.com/csse/v36n1/40892/html",
        "source_type": "open_fulltext_published_baseline",
        "subset_scope": ["FD001", "FD002", "FD003", "FD004"],
        "model_family": "autoencoder plus CNN plus Bi-LSTM",
        "extractable_fields": {
            "window_size": "90",
            "rul_cap_or_degradation_start": "R=120 for FD001/FD003 and R=130 for FD002/FD004",
            "penalty": "P-RMSE penalty term selected by grid search; lambda=0.3 is described as suitable.",
            "architecture": "CNN autoencoder, CNN layers, Bi-LSTM, dropout 0.2, batch normalization, global average pooling, fully connected RUL head.",
            "metrics": "RMSE and PHM-style Score are declared; FD001-FD004 results are reported.",
        },
        "blocking_fields": [
            "Optimizer, learning rate, epochs, batch size, random seeds, and exact normalization procedure are not fully declared in accessible HTML text.",
            "The published comparison table imports several baselines from other papers, so exact baseline reproduction still needs separate source matching.",
        ],
        "priority": "p0_open_all_subset_candidate_training_budget_missing",
    },
    {
        "id": "attention_lstm_ijphm_2025",
        "title": "Remaining Useful Life Prediction Using Attention-LSTM Neural Network of Aircraft Engines",
        "url": "https://doi.org/10.36001/ijphm.2025.v16i2.4274",
        "source_type": "open_fulltext_subset_reference",
        "subset_scope": ["FD001", "FD003"],
        "model_family": "self-attention plus LSTM",
        "extractable_fields": {
            "metrics": "RMSE and Score are reported for FD001 and FD003.",
            "architecture": "self-attention feature transformation followed by LSTM family model.",
        },
        "blocking_fields": [
            "Only FD001 and FD003 are reported, so it cannot close the all-subset FD001-FD004 C-MAPSS gate.",
            "It is useful as a subset reference, not the primary all-subset exact-native baseline.",
        ],
        "priority": "p1_subset_reference",
    },
    {
        "id": "fd001_change_point_cnn_lstm_2023",
        "title": "Remaining Useful Life Estimation of Turbofan Engines with Deep Learning Using Change-Point Detection Based Labeling and Feature Engineering",
        "url": "https://www.mdpi.com/2076-3417/13/21/11893",
        "source_type": "open_fulltext_fd001_reference",
        "subset_scope": ["FD001"],
        "model_family": "change-point labeling plus 1D-CNN-LSTM",
        "extractable_fields": {
            "sensor_selection": "14 selected sensors after dropping constant/non-trending sensors.",
            "normalization": "min-max scaling is described.",
            "filtering": "first-order low-pass filter at 0.08 Hz is described.",
            "metrics": "RMSE and Score are reported.",
        },
        "blocking_fields": [
            "FD001-only protocol cannot close an FD001-FD004 all-subset gate.",
            "Change-point label construction would be an auxiliary protocol, not the current terminal-test RUL contract without additional alignment.",
        ],
        "priority": "p2_fd001_auxiliary",
    },
    {
        "id": "lstm_rul_2017",
        "title": "Long Short-Term Memory Network for Remaining Useful Life estimation",
        "url": "https://doi.org/10.1109/ICPHM.2017.7998311",
        "source_type": "primary_metadata_only_in_current_environment",
        "subset_scope": ["FD001", "FD002", "FD003", "FD004"],
        "model_family": "deep LSTM",
        "extractable_fields": {
            "local_candidate": "Local lstm_sequence has three-seed FD001-FD004 archives, but source protocol fields are unavailable.",
        },
        "blocking_fields": [
            "IEEE full-text protocol is unavailable in the current environment.",
            "Exact sensor selection, normalization, architecture, sequence length, validation, and budget fields are not verified.",
        ],
        "priority": "blocked_until_primary_fulltext_available",
    },
]


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


def _covers_all_subsets(row: dict[str, Any]) -> bool:
    return {"FD001", "FD002", "FD003", "FD004"}.issubset(set(row.get("subset_scope") or []))


def _has_training_budget(row: dict[str, Any]) -> bool:
    fields = row.get("extractable_fields") if isinstance(row.get("extractable_fields"), dict) else {}
    return all(key in fields for key in ("window_size", "batch_size", "epochs", "optimizer", "learning_rate"))


def build_cmapss_open_protocol_candidate_audit() -> dict[str, Any]:
    all_subset = [row["id"] for row in CANDIDATE_SOURCES if _covers_all_subsets(row)]
    budget_candidates = [row["id"] for row in CANDIDATE_SOURCES if _covers_all_subsets(row) and _has_training_budget(row)]
    exact_ready_candidates: list[str] = []
    gates = {
        "open_candidate_audit_present": True,
        "accessible_all_subset_candidate_present": bool(all_subset),
        "accessible_training_budget_candidate_present": bool(budget_candidates),
        "mdfa_count_profile_reconciled": True,
        "exact_source_profile_ready": bool(exact_ready_candidates),
        "safe_to_flip_published_baseline_gate": False,
    }
    return {
        "version": VERSION,
        "status": "open_candidates_identified_exact_profile_pending",
        "claim_boundary": (
            "Accessible published C-MAPSS baselines exist, but none is promoted to exact-native evidence until "
            "dataset-count conflicts, preprocessing, source-matched budget, and prediction archives are resolved."
        ),
        "candidate_sources": CANDIDATE_SOURCES,
        "all_subset_candidates": all_subset,
        "training_budget_candidates": budget_candidates,
        "recommended_next_target": {
            "primary": "mdfa_2025",
            "reason": (
                "It is open full text, covers FD001-FD004, and exposes window, batch, epochs, optimizer, learning rate, "
                "dropout, sensor/PCA preprocessing, architecture, and result table fields; raw-file counts now match "
                "the MDFA table, but PCA/key-sensor preprocessing and a source-matched runner are still needed before exact claims."
            ),
            "fallback": "acb_2021",
            "fallback_reason": (
                "It is open full text and all-subset, but lacks enough budget fields in the accessible HTML text."
            ),
        },
        "gates": gates,
        "missing_gates": [name for name, value in gates.items() if not value],
        "next_actions": [
            "Use cmapss_mdfa_source_profile as the count-reconciled MDFA source profile and treat the bundled readme FD004 mismatch as a disclosed data-package caveat.",
            "Implement a source-matched MDFA runner with window=30, batch=32, epochs=100, Adam, lr=0.0001, dropout=0.3, PCA/key-sensor preprocessing, and FD001-FD004 terminal RUL records.",
            "Run a three-seed reproduction and archive per-test-engine predictions before considering a published-baseline gate flip.",
            "Keep ACB as the fallback all-subset open baseline if MDFA source-count reconciliation fails.",
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# C-MAPSS Open Protocol Candidate Audit",
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
            "## Candidate Sources",
            "",
            "| Candidate | Scope | Priority | Extractable fields | Blocking fields |",
            "|---|---|---|---|---|",
        ]
    )
    for row in payload["candidate_sources"]:
        fields = ", ".join(sorted((row.get("extractable_fields") or {}).keys()))
        blockers = "<br>".join(row["blocking_fields"])
        lines.append(
            "| {id} | {scope} | {priority} | {fields} | {blockers} |".format(
                id=f"[{row['id']}]({row['url']})",
                scope=", ".join(row["subset_scope"]),
                priority=row["priority"],
                fields=fields,
                blockers=blockers,
            )
        )
    lines.extend(["", "## Recommended Next Target", ""])
    target = payload["recommended_next_target"]
    lines.append(f"- Primary: `{target['primary']}` - {target['reason']}")
    lines.append(f"- Fallback: `{target['fallback']}` - {target['fallback_reason']}")
    lines.extend(["", "## Next Actions", ""])
    lines.extend(f"- {item}" for item in payload["next_actions"])
    return "\n".join(lines).rstrip() + "\n"


def write_cmapss_open_protocol_candidate_audit(output_dir: Path | str = DEFAULT_OUTPUT_DIR) -> list[Path]:
    output_dir = Path(output_dir)
    payload = build_cmapss_open_protocol_candidate_audit()
    json_path = output_dir / "cmapss_open_protocol_candidate_audit.json"
    md_path = output_dir / "cmapss_open_protocol_candidate_audit.md"
    _write_json(json_path, payload)
    _write_text(md_path, render_markdown(payload))
    return [json_path, md_path]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Write C-MAPSS open published-protocol candidate audit.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    for path in write_cmapss_open_protocol_candidate_audit(args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
