from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from aaai_experiment_execution_manifest import build_manifest


VERSION = "external-baseline-alignment-decision-v1"
CHECKED_ON = "2026-06-21"
REPO_ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_REPO_SNAPSHOT_PATH = "knowledge_exports/external_baseline_official_repos/official_external_repo_snapshot.json"
OFFICIAL_REPO_CHECKOUT_AUDIT_PATH = "knowledge_exports/external_baseline_official_repos/official_external_repo_checkout_audit.json"


PRIMARY_SOURCE_SNAPSHOT: dict[str, dict[str, str]] = {
    "PatchTST": {
        "paper_url": "https://openreview.net/forum?id=Jbdc0vTOcol",
        "repo_url": "https://github.com/yuqinie98/PatchTST",
        "venue": "ICLR 2023",
        "official_task": "long-term time-series forecasting and representation learning",
        "source_observation": "official repository and ICLR page describe patch tokens and channel independence for forecasting/representation",
    },
    "Anomaly Transformer": {
        "paper_url": "https://openreview.net/forum?id=LzQQ89U1qm_",
        "repo_url": "https://github.com/thuml/Anomaly-Transformer",
        "venue": "ICLR 2022 Spotlight",
        "official_task": "unsupervised time-series anomaly detection",
        "source_observation": "official repository exposes association discrepancy, anomaly attention, minimax training, and adjusted point evaluation",
    },
    "Graph WaveNet": {
        "paper_url": "https://www.ijcai.org/proceedings/2019/264",
        "repo_url": "https://github.com/nnzhan/Graph-WaveNet",
        "venue": "IJCAI 2019",
        "official_task": "spatial-temporal traffic forecasting",
        "source_observation": "paper and original repository use adaptive dependency matrices with stacked dilated temporal convolutions on METR-LA/PEMS-BAY",
    },
}


ALIGNMENT_DECISIONS: dict[str, dict[str, Any]] = {
    "PatchTST": {
        "family": "temporal sequence",
        "target_datasets": ["TEP", "SKAB"],
        "core_mechanism": [
            "segment each variable history into overlapping patch tokens",
            "share the Transformer encoder across channel-independent univariate series",
            "use the patch encoder as a temporal backbone before a task-specific head",
        ],
        "directness": "task-adapted backbone rather than a direct official anomaly or fault-diagnosis score",
        "protocol_mismatches": [
            "official objective is forecasting/representation, while TEP requires strict 22-class diagnosis and SKAB requires anomaly scoring",
            "official benchmark suite is not the current TEP/SKAB split, window, and validation-threshold protocol",
            "a classification or anomaly-score head must be introduced and archived before any matched result is admissible",
        ],
        "runner_contract": [
            "implement channel-independent patch encoder with declared patch length, stride, lookback window, and head type",
            "accept dataset, seed, train/validation/test split, window, and validation-only threshold arguments",
            "write validation predictions, test predictions, selected threshold/head config, metric JSON, and config hash",
        ],
        "paper_use": "cite as a modern temporal backbone and use only as a matched adaptation after runner artifacts exist",
        "comparison_admissibility": "not_admissible_as_official_external_score",
        "next_action": "use the new official-source adapted TEP wrapper as negative-control evidence; exact official budget/protocol reproduction remains required before public comparison wording",
    },
    "Anomaly Transformer": {
        "family": "temporal anomaly",
        "target_datasets": ["SKAB", "TEP"],
        "core_mechanism": [
            "learn association discrepancy as an anomaly criterion",
            "use anomaly attention to separate prior and series associations",
            "amplify normal-abnormal distinction through minimax training",
        ],
        "directness": "direct anomaly-detection candidate for SKAB and adapted score baseline for TEP",
        "protocol_mismatches": [
            "official evaluation uses unsupervised anomaly scores and adjustment policy that must be matched or explicitly disabled",
            "TEP strict multiclass diagnosis is not the native objective and needs a declared score-to-class adaptation",
            "thresholding must be validation-only under the current protocol and cannot use test labels or post-hoc adjustment unless declared",
        ],
        "runner_contract": [
            "run the official association-discrepancy score path with fixed seed and documented window length",
            "emit raw anomaly scores for validation and test before thresholding",
            "archive whether point adjustment/event adjustment is used, and compute the same Macro-F1/FAR/MAR protocol as the paper table",
        ],
        "paper_use": "high-priority anomaly baseline family; official comparison requires threshold and adjustment alignment",
        "comparison_admissibility": "not_admissible_as_official_external_score",
        "next_action": "wrap official or faithful Anomaly Transformer scoring for SKAB first, then decide whether TEP remains anomaly-only or multiclass-adapted",
    },
    "Graph WaveNet": {
        "family": "graph temporal",
        "target_datasets": ["TEP"],
        "core_mechanism": [
            "learn adaptive node dependencies through trainable node embeddings",
            "combine graph convolution with stacked dilated temporal convolution",
            "model long temporal receptive fields and hidden spatial dependencies jointly",
        ],
        "directness": "graph-temporal architecture reference, not a direct TEP diagnosis leaderboard score",
        "protocol_mismatches": [
            "official task is traffic forecasting on METR-LA/PEMS-BAY rather than industrial fault diagnosis",
            "the native input contract assumes a node graph and forecasting horizon, while TEP uses process variables and class labels",
            "a fair comparison requires a declared process-variable graph, horizon/window adapter, classification head, and no test-tuned thresholds",
        ],
        "runner_contract": [
            "define the process-variable graph contract: static, adaptive, or reliability-admitted adjacency",
            "accept identical TEP windows, seeds, split, normalization, and class labels as the main protocol",
            "write adjacency provenance, validation/test logits, metric JSON, config hash, and executable command",
        ],
        "paper_use": "cite as graph-temporal design motivation; compare only as a matched adaptation after graph contract is archived",
        "comparison_admissibility": "not_admissible_as_official_external_score",
        "next_action": "use the official-source adapted TEP wrapper as negative graph-temporal control evidence; exact traffic-forecasting protocol reproduction remains out of scope for public comparison wording",
    },
}


LOCAL_ADAPTER_ARTIFACTS: dict[str, list[dict[str, str]]] = {
    "PatchTST": [
        {
            "role": "tep_official_source_wrapper_smoke",
            "path": "knowledge_exports/external_baseline_protocol_runs/patchtst_official_tep_wrapper_smoke.json",
            "interpretation": "official PatchTST supervised source backbone with a lightweight TEP classification head; smoke evidence only, not an official paper score",
        },
        {
            "role": "tep_official_source_wrapper_smoke_summary",
            "path": "knowledge_exports/external_baseline_protocol_runs/patchtst_official_tep_wrapper_smoke.md",
            "interpretation": "Markdown summary for the PatchTST official-source adapted TEP wrapper smoke",
        },
        {
            "role": "tep_official_source_wrapper_three_seed_probe",
            "path": "knowledge_exports/external_baseline_protocol_runs/patchtst_official_tep_wrapper_3seed_probe.json",
            "interpretation": "three-seed low-budget official-source PatchTST supervised backbone adapted with a lightweight TEP classification head; negative-control evidence only",
        },
        {
            "role": "tep_official_source_wrapper_three_seed_summary",
            "path": "knowledge_exports/external_baseline_protocol_runs/patchtst_official_tep_wrapper_3seed_probe.md",
            "interpretation": "Markdown summary for the three-seed PatchTST official-source adapted TEP wrapper probe",
        },
        {
            "role": "tep_official_source_wrapper_three_seed_budget_probe",
            "path": "knowledge_exports/external_baseline_protocol_runs/patchtst_official_tep_wrapper_3seed_budget_probe.json",
            "interpretation": "three-seed budget-escalated official-source PatchTST supervised backbone adapted with a lightweight TEP classification head; negative-control evidence only",
        },
        {
            "role": "tep_official_source_wrapper_three_seed_budget_summary",
            "path": "knowledge_exports/external_baseline_protocol_runs/patchtst_official_tep_wrapper_3seed_budget_probe.md",
            "interpretation": "Markdown summary for the budget-escalated PatchTST official-source adapted TEP wrapper probe",
        },
        {
            "role": "three_seed_matched_probe",
            "path": "knowledge_exports/tep_patchtst_matched_adapter_3seed_probe/patchtst_3seed_probe.json",
            "interpretation": "three-seed, 3000-row, 3-epoch TEP matched-adapter probe; negative-control evidence only",
        },
        {
            "role": "three_seed_alignment_artifact",
            "path": "knowledge_exports/aaai_external_baseline_alignment_decision/patchtst_tep_3seed_alignment_artifact.json",
            "interpretation": "hash-bearing claim-boundary artifact for the local PatchTST-style three-seed probe",
        },
        {
            "role": "pipeline_smoke",
            "path": "knowledge_exports/tep_patchtst_matched_adapter_smoke/patchtst_smoke.json",
            "interpretation": "single-seed, 600-row, 1-epoch smoke; verifies matched adapter execution only",
        },
        {
            "role": "seed42_low_budget_probe",
            "path": "knowledge_exports/tep_patchtst_matched_adapter_seed42_e5/patchtst_seed42_e5.json",
            "interpretation": "single-seed 5000-row 5-epoch probe; current score is weak and not a competitive result",
        },
        {
            "role": "alignment_artifact",
            "path": "knowledge_exports/aaai_external_baseline_alignment_decision/patchtst_tep_smoke_alignment_artifact.json",
            "interpretation": "hash-bearing claim-boundary artifact for the local PatchTST-style adapter smoke",
        },
    ],
    "Anomaly Transformer": [
        {
            "role": "skab_three_seed_matched_probe",
            "path": "knowledge_exports/external_baseline_protocol_runs/skab_anomaly_transformer_3seed_probe.json",
            "interpretation": "three-seed SKAB association-discrepancy-style anomaly scorer; local matched negative-control evidence only",
        },
        {
            "role": "skab_official_source_adapter",
            "path": "knowledge_exports/external_baseline_protocol_runs/anomaly_transformer_official_skab_adapter/anomaly_transformer_official_skab_adapter.json",
            "interpretation": "PSM-compatible SKAB adapter for the verified official Anomaly Transformer source; no official score until solver patch and matched threshold protocol are implemented",
        },
        {
            "role": "skab_official_source_adapter_summary",
            "path": "knowledge_exports/external_baseline_protocol_runs/anomaly_transformer_official_skab_adapter/anomaly_transformer_official_skab_adapter.md",
            "interpretation": "Markdown summary of SKAB official-source adapter files and protocol risks",
        },
        {
            "role": "skab_official_source_wrapper_smoke",
            "path": "knowledge_exports/external_baseline_protocol_runs/anomaly_transformer_official_skab_wrapper_smoke.json",
            "interpretation": "official-source Anomaly Transformer architecture with patched SKAB validation-only threshold protocol; smoke evidence only",
        },
        {
            "role": "skab_official_source_wrapper_smoke_summary",
            "path": "knowledge_exports/external_baseline_protocol_runs/anomaly_transformer_official_skab_wrapper_smoke.md",
            "interpretation": "Markdown summary for the official-source patched SKAB wrapper smoke",
        },
        {
            "role": "skab_official_source_wrapper_three_seed_probe",
            "path": "knowledge_exports/external_baseline_protocol_runs/anomaly_transformer_official_skab_wrapper_3seed_probe.json",
            "interpretation": "three-seed low-budget official-source Anomaly Transformer architecture with patched SKAB validation-only threshold protocol; not an official paper score",
        },
        {
            "role": "skab_official_source_wrapper_three_seed_summary",
            "path": "knowledge_exports/external_baseline_protocol_runs/anomaly_transformer_official_skab_wrapper_3seed_probe.md",
            "interpretation": "Markdown summary for the three-seed official-source patched SKAB wrapper probe",
        },
        {
            "role": "skab_official_source_wrapper_three_seed_budget_probe",
            "path": "knowledge_exports/external_baseline_protocol_runs/anomaly_transformer_official_skab_wrapper_3seed_budget_probe.json",
            "interpretation": "three-seed budget-escalated official-source Anomaly Transformer architecture with patched SKAB validation-only threshold protocol; high-FAR negative-control evidence, not an official paper score",
        },
        {
            "role": "skab_official_source_wrapper_three_seed_budget_summary",
            "path": "knowledge_exports/external_baseline_protocol_runs/anomaly_transformer_official_skab_wrapper_3seed_budget_probe.md",
            "interpretation": "Markdown summary for the budget-escalated official-source patched SKAB wrapper probe",
        },
        {
            "role": "skab_three_seed_summary",
            "path": "knowledge_exports/external_baseline_protocol_runs/skab_anomaly_transformer_3seed_probe.md",
            "interpretation": "Markdown summary for the local SKAB Anomaly-Transformer-style three-seed probe",
        },
        {
            "role": "skab_three_seed_alignment_artifact",
            "path": "knowledge_exports/aaai_external_baseline_alignment_decision/anomaly_transformer_skab_3seed_alignment_artifact.json",
            "interpretation": "hash-bearing claim-boundary artifact for the local SKAB Anomaly-Transformer-style three-seed probe",
        },
        {
            "role": "skab_pipeline_smoke",
            "path": "knowledge_exports/external_baseline_protocol_runs/skab_anomaly_transformer_smoke.json",
            "interpretation": "single-seed, 1-epoch SKAB association-discrepancy-style anomaly scorer; verifies matched SKAB anomaly route only",
        },
        {
            "role": "skab_alignment_artifact",
            "path": "knowledge_exports/aaai_external_baseline_alignment_decision/anomaly_transformer_skab_smoke_alignment_artifact.json",
            "interpretation": "hash-bearing claim-boundary artifact for the local SKAB Anomaly-Transformer-style smoke",
        },
        {
            "role": "three_seed_matched_probe",
            "path": "knowledge_exports/tep_anomaly_transformer_matched_adapter_3seed_probe/anomaly_transformer_3seed_probe.json",
            "interpretation": "three-seed, 3000-row, 3-epoch TEP matched-adapter probe; negative-control evidence only",
        },
        {
            "role": "three_seed_alignment_artifact",
            "path": "knowledge_exports/aaai_external_baseline_alignment_decision/anomaly_transformer_tep_3seed_alignment_artifact.json",
            "interpretation": "hash-bearing claim-boundary artifact for the local Anomaly-Transformer-style three-seed probe",
        },
        {
            "role": "pipeline_smoke",
            "path": "knowledge_exports/tep_anomaly_transformer_matched_adapter_smoke/anomaly_transformer_smoke.json",
            "interpretation": "single-seed, 600-row, 1-epoch TEP matched-adapter smoke; verifies association-discrepancy-style adapter execution only",
        },
        {
            "role": "alignment_artifact",
            "path": "knowledge_exports/aaai_external_baseline_alignment_decision/anomaly_transformer_tep_smoke_alignment_artifact.json",
            "interpretation": "hash-bearing claim-boundary artifact for the local Anomaly-Transformer-style adapter smoke",
        },
    ],
    "Graph WaveNet": [
        {
            "role": "tep_official_source_wrapper_smoke",
            "path": "knowledge_exports/external_baseline_protocol_runs/graph_wavenet_official_tep_wrapper_smoke.json",
            "interpretation": "official Graph WaveNet source backbone with a lightweight TEP classification head and PyTorch Conv2d compatibility patch; smoke evidence only, not an official paper score",
        },
        {
            "role": "tep_official_source_wrapper_smoke_summary",
            "path": "knowledge_exports/external_baseline_protocol_runs/graph_wavenet_official_tep_wrapper_smoke.md",
            "interpretation": "Markdown summary for the Graph WaveNet official-source adapted TEP wrapper smoke",
        },
        {
            "role": "tep_official_source_wrapper_three_seed_probe",
            "path": "knowledge_exports/external_baseline_protocol_runs/graph_wavenet_official_tep_wrapper_3seed_probe.json",
            "interpretation": "three-seed low-budget official-source Graph WaveNet backbone adapted with a lightweight TEP classification head; negative-control evidence only",
        },
        {
            "role": "tep_official_source_wrapper_three_seed_summary",
            "path": "knowledge_exports/external_baseline_protocol_runs/graph_wavenet_official_tep_wrapper_3seed_probe.md",
            "interpretation": "Markdown summary for the three-seed Graph WaveNet official-source adapted TEP wrapper probe",
        },
        {
            "role": "tep_official_source_wrapper_three_seed_budget_probe",
            "path": "knowledge_exports/external_baseline_protocol_runs/graph_wavenet_official_tep_wrapper_3seed_budget_probe.json",
            "interpretation": "three-seed budget-escalated official-source Graph WaveNet backbone adapted with a lightweight TEP classification head; negative-control evidence only",
        },
        {
            "role": "tep_official_source_wrapper_three_seed_budget_summary",
            "path": "knowledge_exports/external_baseline_protocol_runs/graph_wavenet_official_tep_wrapper_3seed_budget_probe.md",
            "interpretation": "Markdown summary for the budget-escalated Graph WaveNet official-source adapted TEP wrapper probe",
        },
        {
            "role": "three_seed_matched_probe",
            "path": "knowledge_exports/tep_graph_wavenet_matched_adapter_3seed_probe/graph_wavenet_3seed_probe.json",
            "interpretation": "three-seed, 3000-row, 3-epoch TEP matched-adapter probe; negative-control evidence only",
        },
        {
            "role": "three_seed_alignment_artifact",
            "path": "knowledge_exports/aaai_external_baseline_alignment_decision/graph_wavenet_tep_3seed_alignment_artifact.json",
            "interpretation": "hash-bearing claim-boundary artifact for the local Graph-WaveNet-style three-seed probe",
        },
        {
            "role": "pipeline_smoke",
            "path": "knowledge_exports/tep_graph_wavenet_matched_adapter_smoke/graph_wavenet_smoke.json",
            "interpretation": "single-seed, 600-row, 1-epoch TEP matched-adapter smoke; verifies adaptive graph-temporal adapter execution only",
        },
        {
            "role": "alignment_artifact",
            "path": "knowledge_exports/aaai_external_baseline_alignment_decision/graph_wavenet_tep_smoke_alignment_artifact.json",
            "interpretation": "hash-bearing claim-boundary artifact for the local Graph-WaveNet-style adapter smoke",
        },
    ],
}


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _existing_local_artifacts(name: str) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    for item in LOCAL_ADAPTER_ARTIFACTS.get(name, []):
        path = REPO_ROOT / item["path"]
        artifacts.append(
            {
                **item,
                "exists": os.path.exists(_fs_path(path)),
            }
        )
    return artifacts


def official_repo_snapshot_status(name: str) -> dict[str, Any]:
    path = REPO_ROOT / OFFICIAL_REPO_SNAPSHOT_PATH
    status: dict[str, Any] = {
        "artifact": OFFICIAL_REPO_SNAPSHOT_PATH,
        "exists": os.path.exists(_fs_path(path)),
        "snapshot_status": "missing",
        "resolved_default_branch": "",
        "resolved_head_commit": "",
        "official_external_score": False,
        "protocol_reproduction_status": "not_started_from_snapshot",
    }
    if not status["exists"]:
        return status
    try:
        with open(_fs_path(path), encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        status["snapshot_status"] = f"unreadable: {type(exc).__name__}"
        return status
    for row in payload.get("rows", []):
        if row.get("name") == name:
            status.update(
                {
                    "snapshot_status": row.get("snapshot_status", "unknown"),
                    "resolved_default_branch": row.get("resolved_default_branch", ""),
                    "resolved_head_commit": row.get("resolved_head_commit", ""),
                    "official_external_score": bool(row.get("official_external_score", False)),
                    "protocol_reproduction_status": row.get(
                        "protocol_reproduction_status",
                        "not_started_from_snapshot",
                    ),
                }
            )
            return status
    status["snapshot_status"] = "method_missing_from_snapshot"
    return status


def official_repo_checkout_status(name: str) -> dict[str, Any]:
    path = REPO_ROOT / OFFICIAL_REPO_CHECKOUT_AUDIT_PATH
    status: dict[str, Any] = {
        "artifact": OFFICIAL_REPO_CHECKOUT_AUDIT_PATH,
        "exists": os.path.exists(_fs_path(path)),
        "checkout_status": "missing",
        "checkout_dir": "",
        "actual_commit": "",
        "commit_matches_snapshot": False,
        "official_external_score": False,
        "protocol_wrapper_status": "not_implemented",
    }
    if not status["exists"]:
        return status
    try:
        with open(_fs_path(path), encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        status["checkout_status"] = f"unreadable: {type(exc).__name__}"
        return status
    for row in payload.get("rows", []):
        if row.get("name") == name:
            status.update(
                {
                    "checkout_status": row.get("checkout_status", "unknown"),
                    "checkout_dir": row.get("checkout_dir", ""),
                    "actual_commit": row.get("actual_commit", ""),
                    "commit_matches_snapshot": bool(row.get("commit_matches_snapshot", False)),
                    "official_external_score": bool(row.get("official_external_score", False)),
                    "protocol_wrapper_status": row.get("protocol_wrapper_status", "not_implemented"),
                }
            )
            return status
    status["checkout_status"] = "method_missing_from_checkout_audit"
    return status


def _local_adapter_status(name: str) -> str:
    artifacts = _existing_local_artifacts(name)
    if any(item["exists"] and str(item.get("role")) == "three_seed_matched_probe" for item in artifacts):
        return "local_three_seed_probe_available"
    if any(item["exists"] for item in artifacts):
        return "local_probe_available"
    return "not_materialized"


def _manifest_pending(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["name"]: item
        for item in manifest.get("baseline_obligations", [])
        if item.get("name") in ALIGNMENT_DECISIONS
    }


def build_alignment_decision_payload(
    *,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manifest = manifest or build_manifest()
    pending = _manifest_pending(manifest)
    rows: list[dict[str, Any]] = []
    for name, decision in ALIGNMENT_DECISIONS.items():
        source = PRIMARY_SOURCE_SNAPSHOT[name]
        manifest_row = pending.get(name, {})
        status = manifest_row.get("status", "not_declared_pending")
        rows.append(
            {
                "name": name,
                "family": decision["family"],
                "manifest_status": status,
                "checked_on": CHECKED_ON,
                "paper_url": source["paper_url"],
                "repo_url": source["repo_url"],
                "venue": source["venue"],
                "official_task": source["official_task"],
                "source_observation": source["source_observation"],
                "official_repo_snapshot": official_repo_snapshot_status(name),
                "official_repo_checkout": official_repo_checkout_status(name),
                "target_datasets": decision["target_datasets"],
                "manifest_datasets": manifest_row.get("datasets", []),
                "command_template": manifest_row.get("command_template", ""),
                "checks": manifest_row.get("checks", []),
                "core_mechanism": decision["core_mechanism"],
                "directness": decision["directness"],
                "protocol_mismatches": decision["protocol_mismatches"],
                "runner_contract": decision["runner_contract"],
                "local_adapter_status": _local_adapter_status(name),
                "local_adapter_artifacts": _existing_local_artifacts(name),
                "paper_use": decision["paper_use"],
                "comparison_admissibility": decision["comparison_admissibility"],
                "next_action": decision["next_action"],
            }
        )
    missing_manifest_rows = sorted(set(ALIGNMENT_DECISIONS) - set(pending))
    exact_pending = [
        item["name"]
        for item in manifest.get("baseline_obligations", [])
        if item.get("status") == "pending_external_alignment"
    ]
    return {
        "version": VERSION,
        "checked_on": CHECKED_ON,
        "overall_status": "official_source_adapted_controls_materialized" if not exact_pending else "external_alignment_pending",
        "claim_gate": "Use these methods as matched-protocol or official-source adapted controls only; do not use them as official external comparison scores.",
        "rows": rows,
        "missing_manifest_rows": missing_manifest_rows,
        "pending_exact_external_score_rows": exact_pending,
    }


def render_alignment_decision_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = [
        "# AAAI External Baseline Alignment Decision",
        "",
        f"- Version: {payload['version']}",
        f"- Checked on: {payload['checked_on']}",
        f"- Overall status: {payload['overall_status']}",
        f"- Claim gate: {payload['claim_gate']}",
        "",
        "This decision artifact records why the strongest external baselines remain protocol-alignment obligations rather than completed official comparison scores.",
        "",
        "## Decision Matrix",
        "",
        "| Method | Venue | Official task | Target datasets | Local adapter | Directness | Admissibility | Next action |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in payload["rows"]:
        lines.append(
            "| {name} | {venue} | {official_task} | {datasets} | {local_adapter} | {directness} | {admissibility} | {next_action} |".format(
                name=row["name"],
                venue=row["venue"],
                official_task=row["official_task"],
                datasets=", ".join(row["target_datasets"]),
                local_adapter=row["local_adapter_status"],
                directness=row["directness"],
                admissibility=row["comparison_admissibility"],
                next_action=row["next_action"],
            )
        )
    lines.extend(["", "## Per-Method Contracts", ""])
    for row in payload["rows"]:
        lines.extend(
            [
                f"### {row['name']}",
                "",
                f"- Paper: {row['paper_url']}",
                f"- Code: {row['repo_url']}",
                f"- Manifest status: {row['manifest_status']}",
                "- Official repo snapshot: {status} at `{artifact}`; branch `{branch}`; HEAD `{head}`; protocol `{protocol}`".format(
                    status=row["official_repo_snapshot"]["snapshot_status"],
                    artifact=row["official_repo_snapshot"]["artifact"],
                    branch=row["official_repo_snapshot"]["resolved_default_branch"],
                    head=str(row["official_repo_snapshot"]["resolved_head_commit"])[:12],
                    protocol=row["official_repo_snapshot"]["protocol_reproduction_status"],
                ),
                "- Official repo checkout: {status} at `{artifact}`; HEAD `{head}`; wrapper `{wrapper}`".format(
                    status=row["official_repo_checkout"]["checkout_status"],
                    artifact=row["official_repo_checkout"]["artifact"],
                    head=str(row["official_repo_checkout"]["actual_commit"])[:12],
                    wrapper=row["official_repo_checkout"]["protocol_wrapper_status"],
                ),
                f"- Local adapter status: {row['local_adapter_status']}",
                f"- Safe paper use: {row['paper_use']}",
                "- Core mechanism:",
            ]
        )
        lines.extend(f"  - {item}" for item in row["core_mechanism"])
        lines.append("- Protocol mismatches:")
        lines.extend(f"  - {item}" for item in row["protocol_mismatches"])
        lines.append("- Runner contract:")
        lines.extend(f"  - {item}" for item in row["runner_contract"])
        if row.get("local_adapter_artifacts"):
            lines.append("- Local adapter artifacts:")
            for artifact in row["local_adapter_artifacts"]:
                status = "present" if artifact["exists"] else "missing"
                lines.append(f"  - {artifact['role']} ({status}): `{artifact['path']}`; {artifact['interpretation']}")
        lines.append("")
    if payload["missing_manifest_rows"]:
        lines.extend(["## Manifest Mismatches", ""])
        lines.extend(f"- {item}" for item in payload["missing_manifest_rows"])
        lines.append("")
    return "\n".join(lines)


def build_external_baseline_alignment_decision(
    output_dir: Path | str,
    *,
    manifest: dict[str, Any] | None = None,
) -> list[Path]:
    output_dir = Path(output_dir)
    os.makedirs(_fs_path(output_dir), exist_ok=True)
    payload = build_alignment_decision_payload(manifest=manifest)
    json_path = output_dir / "aaai_external_baseline_alignment_decision.json"
    md_path = output_dir / "aaai_external_baseline_alignment_decision.md"
    with open(_fs_path(json_path), "w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    with open(_fs_path(md_path), "w", encoding="utf-8") as handle:
        handle.write(render_alignment_decision_markdown(payload))
    return [json_path, md_path]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build the AAAI external-baseline alignment decision artifact.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("knowledge_exports") / "aaai_external_baseline_alignment_decision",
    )
    args = parser.parse_args(argv)
    for path in build_external_baseline_alignment_decision(args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
