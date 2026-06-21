from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from aaai_experiment_execution_manifest import build_manifest
from aaai_external_baseline_alignment_decision import (
    ALIGNMENT_DECISIONS,
    LOCAL_ADAPTER_ARTIFACTS,
    PRIMARY_SOURCE_SNAPSHOT,
    REPO_ROOT as EXTERNAL_ALIGNMENT_REPO_ROOT,
    official_repo_checkout_status,
    official_repo_snapshot_status,
)


REQUIRED_RUNNER_CONTRACT = [
    "accept declared dataset, seed, split, window, and validation-threshold arguments",
    "use the same train/validation/test units as the reliable-route protocol",
    "write seed-level validation predictions and test predictions",
    "write validation-selected thresholds and no test-tuned thresholds",
    "write metric JSON, config hash, and executable command provenance",
]


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _has_local_adapter_artifact(name: str) -> bool:
    for item in LOCAL_ADAPTER_ARTIFACTS.get(name, []):
        if os.path.exists(_fs_path(EXTERNAL_ALIGNMENT_REPO_ROOT / item["path"])):
            return True
    return False


def _local_runner_status(name: str, fallback: str) -> str:
    artifacts = LOCAL_ADAPTER_ARTIFACTS.get(name, [])
    if any(
        str(item.get("role")) == "three_seed_matched_probe"
        and os.path.exists(_fs_path(EXTERNAL_ALIGNMENT_REPO_ROOT / item["path"]))
        for item in artifacts
    ):
        return "local_matched_three_seed_probe_available"
    if _has_local_adapter_artifact(name):
        return "local_matched_adapter_probe_available"
    return fallback


def _blocking_reasons_for_runner_status(status: str) -> list[str]:
    if status == "local_matched_three_seed_probe_available":
        return [
            "official_protocol_reproduction_required",
            "official_budget_required",
            "public_claim_forbidden_until_gate_passes",
        ]
    if status == "local_matched_adapter_probe_available":
        return [
            "full_seed_budget_required",
            "protocol_alignment_required",
            "seed_level_artifacts_missing",
            "public_claim_forbidden_until_gate_passes",
        ]
    return [
        "implementation_required",
        "protocol_alignment_required",
        "seed_level_artifacts_missing",
        "public_claim_forbidden_until_gate_passes",
    ]


def _pending_records(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for baseline in manifest.get("baseline_obligations", []):
        if baseline.get("status") != "pending_external_alignment":
            continue
        name = baseline["name"]
        source = PRIMARY_SOURCE_SNAPSHOT.get(name, {})
        decision = ALIGNMENT_DECISIONS.get(name, {})
        repo_snapshot = official_repo_snapshot_status(name)
        repo_checkout = official_repo_checkout_status(name)
        runner_status = _local_runner_status(
            name,
            baseline.get("runner_status", "blocked_unimplemented_runner"),
        )
        records.append(
            {
                "name": name,
                "family": baseline["family"],
                "datasets": baseline["datasets"],
                "status": baseline["status"],
                "runner_status": runner_status,
                "score_status": "unscored",
                "official_task": source.get("official_task", ""),
                "official_paper_url": source.get("paper_url", ""),
                "official_repo_url": source.get("repo_url", ""),
                "official_repo_snapshot": repo_snapshot["artifact"],
                "official_repo_snapshot_status": repo_snapshot["snapshot_status"],
                "official_repo_head_commit": repo_snapshot["resolved_head_commit"],
                "official_repo_checkout": repo_checkout["artifact"],
                "official_repo_checkout_status": repo_checkout["checkout_status"],
                "official_repo_checkout_commit": repo_checkout["actual_commit"],
                "official_repo_protocol_wrapper_status": repo_checkout["protocol_wrapper_status"],
                "checks": baseline["checks"],
                "input_contract": baseline.get("input_contract", "same train/validation/test units and declared dataset/seed/window arguments"),
                "output_contract": baseline.get("output_contract", "seed-level predictions, validation thresholds, metric JSON, and config hash"),
                "claim_gate": baseline.get("claim_gate", "no public comparison claim until exact external protocol alignment passes"),
                "alignment_artifact": baseline.get(
                    "alignment_artifact",
                    "knowledge_exports/aaai_external_baseline_alignment_decision/aaai_external_baseline_alignment_decision.json",
                ),
                "comparison_admissibility": decision.get("comparison_admissibility", "not_admissible_as_official_external_score"),
                "next_action": decision.get("next_action", "implement exact external runner and seed-level artifacts"),
                "command_template": baseline["command_template"],
                "blocking_reasons": _blocking_reasons_for_runner_status(runner_status),
                "required_runner_contract": list(REQUIRED_RUNNER_CONTRACT),
            }
        )
    return records


def _materialized_control_records(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for baseline in manifest.get("baseline_obligations", []):
        if baseline.get("status") != "materialized_official_source_adapted_control":
            continue
        name = baseline["name"]
        source = PRIMARY_SOURCE_SNAPSHOT.get(name, {})
        decision = ALIGNMENT_DECISIONS.get(name, {})
        repo_snapshot = official_repo_snapshot_status(name)
        repo_checkout = official_repo_checkout_status(name)
        records.append(
            {
                "name": name,
                "family": baseline["family"],
                "datasets": baseline["datasets"],
                "status": baseline["status"],
                "runner_status": "official_source_adapted_budget_probe_available",
                "score_status": "matched_protocol_control_scored",
                "official_task": source.get("official_task", ""),
                "official_paper_url": source.get("paper_url", ""),
                "official_repo_url": source.get("repo_url", ""),
                "official_repo_snapshot_status": repo_snapshot["snapshot_status"],
                "official_repo_checkout_status": repo_checkout["checkout_status"],
                "official_repo_protocol_wrapper_status": repo_checkout["protocol_wrapper_status"],
                "checks": baseline.get("checks", []),
                "score_artifact": baseline.get("score_artifact", ""),
                "official_external_score": bool(baseline.get("official_external_score", False)),
                "comparison_admissibility": decision.get("comparison_admissibility", "not_admissible_as_official_external_score"),
                "claim_gate": baseline.get(
                    "claim_gate",
                    "matched-protocol control only; no public leaderboard claim",
                ),
                "command_template": baseline.get("command_template", ""),
            }
        )
    return records


def build_pending_baseline_payload(
    *,
    manifest: dict[str, Any] | None = None,
    baseline: str | None = None,
    dataset: str | None = None,
    seed: int | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    manifest = manifest or build_manifest()
    records = _pending_records(manifest)
    materialized = _materialized_control_records(manifest)
    if baseline:
        records = [item for item in records if item["name"].lower() == baseline.lower()]
        materialized = [item for item in materialized if item["name"].lower() == baseline.lower()]
    if dataset:
        records = [item for item in records if dataset in item["datasets"]]
        materialized = [item for item in materialized if dataset in item["datasets"]]
    if status:
        records = [item for item in records if item["status"] == status]
        materialized = [item for item in materialized if item["status"] == status]
    for item in records:
        if seed is not None:
            item["seed"] = int(seed)
    for item in materialized:
        if seed is not None:
            item["seed"] = int(seed)
    return {
        "overall_status": "blocked_by_unimplemented_external_runners" if records else "no_pending_baselines",
        "claim_rule": "official-source adapted controls are scored matched-protocol controls but remain inadmissible as official external leaderboard scores",
        "pending_baselines": records,
        "materialized_external_controls": materialized,
    }


def render_pending_baseline_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# AAAI Pending Baseline Alignment Gate",
        "",
        f"- Overall status: {payload['overall_status']}",
        f"- Claim rule: {payload['claim_rule']}",
        "",
        "This gate is intentionally not a training result. It records which strong external baselines still require implementation, protocol alignment, seed-level artifacts, and validation-only thresholding before any public comparison claim is allowed.",
        "",
        "| Method | Family | Official task | Repo snapshot | Repo checkout | Datasets | Runner status | Score status | Admissibility | Checks | Command template | Input contract | Output contract | Claim gate | Decision artifact | Blocking reasons |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for item in payload["pending_baselines"]:
        lines.append(
            "| {name} | {family} | {official_task} | {repo_snapshot} | {repo_checkout} | {datasets} | {runner_status} | {score_status} | {admissibility} | {checks} | `{command_template}` | {input_contract} | {output_contract} | {claim_gate} | `{alignment_artifact}` | {blocking_reasons} |".format(
                name=item["name"],
                family=item["family"],
                official_task=item.get("official_task", ""),
                repo_snapshot=item.get("official_repo_snapshot_status", "missing"),
                repo_checkout=item.get("official_repo_checkout_status", "missing"),
                datasets=", ".join(item["datasets"]),
                runner_status=item["runner_status"],
                score_status=item["score_status"],
                admissibility=item.get("comparison_admissibility", "not_admissible_as_official_external_score"),
                checks=", ".join(item["checks"]),
                command_template=item.get("command_template", ""),
                input_contract=item["input_contract"],
                output_contract=item["output_contract"],
                claim_gate=item["claim_gate"],
                alignment_artifact=item.get("alignment_artifact", ""),
                blocking_reasons=", ".join(item["blocking_reasons"]),
            )
        )
    controls = payload.get("materialized_external_controls", []) or []
    if controls:
        lines.extend(
            [
                "",
                "## Materialized Official-Source Adapted Controls",
                "",
                "These rows have executable source-provenance-controlled artifacts under the matched protocol. They are not official external leaderboard scores.",
                "",
                "| Method | Family | Official task | Datasets | Runner status | Score status | Official external score | Score artifact | Claim gate |",
                "|---|---|---|---|---|---|---|---|---|",
            ]
        )
        for item in controls:
            lines.append(
                "| {name} | {family} | {official_task} | {datasets} | {runner_status} | {score_status} | {official_external_score} | `{score_artifact}` | {claim_gate} |".format(
                    name=item["name"],
                    family=item["family"],
                    official_task=item.get("official_task", ""),
                    datasets=", ".join(item["datasets"]),
                    runner_status=item["runner_status"],
                    score_status=item["score_status"],
                    official_external_score=item.get("official_external_score", False),
                    score_artifact=item.get("score_artifact", ""),
                    claim_gate=item.get("claim_gate", ""),
                )
            )
    lines.extend(["", "## Required Runner Contract", ""])
    contract = (
        payload["pending_baselines"][0]["required_runner_contract"]
        if payload["pending_baselines"]
        else REQUIRED_RUNNER_CONTRACT
    )
    lines.extend(f"- {item}" for item in contract)
    lines.append("")
    return "\n".join(lines)


def build_pending_baseline_gate(
    output_dir: Path | str,
    *,
    manifest: dict[str, Any] | None = None,
) -> list[Path]:
    output_dir = Path(output_dir)
    os.makedirs(_fs_path(output_dir), exist_ok=True)
    payload = build_pending_baseline_payload(manifest=manifest)
    json_path = output_dir / "aaai_pending_baseline_gate.json"
    md_path = output_dir / "aaai_pending_baseline_gate.md"
    with open(_fs_path(json_path), "w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    with open(_fs_path(md_path), "w", encoding="utf-8") as handle:
        handle.write(render_pending_baseline_markdown(payload))
    return [json_path, md_path]


def _write_single_output(output: Path, payload: dict[str, Any]) -> list[Path]:
    output.parent.mkdir(parents=True, exist_ok=True)
    os.makedirs(_fs_path(output.parent), exist_ok=True)
    with open(_fs_path(output), "w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    markdown = output.with_suffix(".md")
    with open(_fs_path(markdown), "w", encoding="utf-8") as handle:
        handle.write(render_pending_baseline_markdown(payload))
    return [output, markdown]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate an AAAI pending-baseline alignment gate report.")
    parser.add_argument("--baseline", type=str, default="")
    parser.add_argument("--dataset", type=str, default="")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--status", type=str, default="")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("knowledge_exports") / "aaai_latex_draft",
    )
    args = parser.parse_args(argv)

    if args.output:
        payload = build_pending_baseline_payload(
            baseline=args.baseline or None,
            dataset=args.dataset or None,
            seed=args.seed,
            status=args.status or None,
        )
        written = _write_single_output(args.output, payload)
    else:
        written = build_pending_baseline_gate(args.output_dir)
    for path in written:
        print(path)


if __name__ == "__main__":
    main()
