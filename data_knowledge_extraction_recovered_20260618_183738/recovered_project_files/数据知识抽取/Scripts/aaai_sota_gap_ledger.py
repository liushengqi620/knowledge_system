from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from aaai_exact_native_protocol_gate import build_exact_native_protocol_gate


VERSION = "aaai-sota-gap-ledger-v1"


def _find_repo_root() -> Path:
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
        if (candidate / "Scripts" / "aaai_sota_gap_ledger.py").exists() and (candidate / "knowledge_exports").exists():
            return candidate
    return module_root


REPO_ROOT = _find_repo_root()
DEFAULT_OUTPUT_DIR = REPO_ROOT / "knowledge_exports" / "aaai_exact_native_protocol_gate"


MATCHED_RESULT_ROWS = {
    "TEP": {
        "metric": "Target-F1",
        "direction": "higher_is_better",
        "anchor": 0.9122,
        "current": 0.9549,
        "claim_level": "strong_matched_protocol_mechanism_diagnosis",
    },
    "SKAB": {
        "metric": "Macro-F1",
        "direction": "higher_is_better",
        "anchor": 0.8192811077663172,
        "current": 0.8449753177134814,
        "claim_level": "native_metric_audited_matched_protocol",
    },
    "Hydraulic": {
        "metric": "Macro-F1",
        "direction": "higher_is_better",
        "anchor": 0.9773,
        "current": 0.9784,
        "claim_level": "near_ceiling_non_degradation",
    },
    "C-MAPSS": {
        "metric": "RMSE",
        "direction": "lower_is_better",
        "anchor": 20.7559,
        "current": 18.06174213416199,
        "validation_safe_current": 18.2840,
        "claim_level": "original_terminal_rul_matched_protocol",
    },
}

MDFA_TABLE5_RMSE = {
    "FD001": 11.78,
    "FD002": 16.38,
    "FD003": 11.89,
    "FD004": 19.23,
}


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


def _delta(anchor: float, current: float, direction: str) -> float:
    if direction == "lower_is_better":
        return float(anchor - current)
    return float(current - anchor)


def _gate_rows_by_dataset() -> dict[str, dict[str, Any]]:
    gate = build_exact_native_protocol_gate()
    return {row["dataset"]: row for row in gate["rows"]}


def _skab_updates() -> dict[str, Any]:
    audit = _read_json(REPO_ROOT / "knowledge_exports" / "aaai_latex_draft" / "skab_native_metric_audit.json")
    if not audit:
        audit = _read_json(REPO_ROOT / "knowledge_exports" / "aaai_exact_native_protocol_gate" / "skab_native_metric_audit.json")
    decision = audit.get("decision") or {}
    summary_by_branch = {row.get("branch"): row for row in audit.get("branch_summary", [])}
    current_branch = decision.get("current_native_audited_branch")
    current = summary_by_branch.get(current_branch or "", {})
    strong = summary_by_branch.get("skab_strong_anchor_w48_e40", {})
    llm = summary_by_branch.get("skab_llm_condition_candidate_gate_valadm001_w005_c010_w48_e40", {})
    return {
        "current_branch": current_branch or "a0_algorithmic_only",
        "current_macro_f1": float(decision.get("current_native_audited_macro_f1") or current.get("macro_f1_mean") or MATCHED_RESULT_ROWS["SKAB"]["current"]),
        "anchor_macro_f1": float(decision.get("strong_anchor_macro_f1") or strong.get("macro_f1_mean") or MATCHED_RESULT_ROWS["SKAB"]["anchor"]),
        "current_changepoint_event_recall": current.get("changepoint_event_recall_mean"),
        "llm_condition_macro_f1": decision.get("llm_condition_macro_f1") or llm.get("macro_f1_mean"),
        "llm_condition_deployed_as_accuracy_branch": bool(decision.get("llm_condition_deployed_as_accuracy_branch", False)),
    }


def _selected_mdfa_subset_rows() -> list[dict[str, Any]]:
    audit = _read_json(REPO_ROOT / "knowledge_exports" / "aaai_latex_draft" / "cmapss_mdfa_strategy_probe_audit.json")
    if not audit:
        audit = _read_json(
            REPO_ROOT / "knowledge_exports" / "aaai_exact_native_protocol_gate" / "cmapss_mdfa_strategy_probe_audit.json"
        )
    diagnostics = audit.get("diagnostics") or {}
    if "temporal_level_diff_fd003_archive" not in diagnostics:
        try:
            from cmapss_mdfa_strategy_probe_audit import build_mdfa_strategy_probe_audit

            audit = build_mdfa_strategy_probe_audit()
        except Exception:
            pass
    diagnostics = audit.get("diagnostics") or {}
    selected_sources = {
        "FD001": ("full_single_condition_archive", "window80/all24_pca/dropout0.1"),
        "FD003": ("temporal_level_diff_fd003_archive", "window80/all24_pca/dropout0.0+level_diff"),
        "FD002": ("full_multi_condition_archive", "sensor21_pca+kmeans6_settings+condition_onehot"),
        "FD004": ("full_multi_condition_archive", "sensor21_pca+kmeans6_settings+condition_onehot"),
    }
    rows: list[dict[str, Any]] = []
    for subset, (archive_key, selected_branch) in selected_sources.items():
        archive = diagnostics.get(archive_key) or {}
        stats = (archive.get("subset_stats") or {}).get(subset) or {}
        if not stats:
            continue
        current_rmse = float(stats["rmse_mean"])
        reference_rmse = float(MDFA_TABLE5_RMSE[subset])
        rows.append(
            {
                "subset": subset,
                "selected_branch": selected_branch,
                "current_rmse": current_rmse,
                "reference": "MDFA_2025_Table_5_RMSE",
                "reference_rmse": reference_rmse,
                "gap_current_minus_reference": float(current_rmse - reference_rmse),
                "current_score": stats.get("score_mean"),
                "current_raw_rmse": stats.get("raw_rmse_mean"),
                "n_seeds": stats.get("n"),
                "claim_boundary": "source_style_capped_test_only_not_official_sota",
            }
        )
    return rows


def _matched_result_rows(gate_by_dataset: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    skab = _skab_updates()
    matched = dict(MATCHED_RESULT_ROWS)
    matched["SKAB"] = {
        **matched["SKAB"],
        "anchor": skab["anchor_macro_f1"],
        "current": skab["current_macro_f1"],
    }
    for dataset, row in matched.items():
        direction = str(row["direction"])
        anchor = float(row["anchor"])
        current = float(row["current"])
        gate = gate_by_dataset.get(dataset, {})
        rows.append(
            {
                "dataset": dataset,
                "metric": row["metric"],
                "direction": direction,
                "matched_anchor": anchor,
                "current_matched": current,
                "matched_improvement": _delta(anchor, current, direction),
                "validation_safe_current": row.get("validation_safe_current"),
                "claim_level": row["claim_level"],
                "official_status": gate.get("status", "unknown"),
                "official_sota_claim_admissible": bool(gate.get("official_sota_claim_admissible", False)),
                "missing_exact_native_gates": gate.get("missing_gates", []),
                "protocol_gap": "numeric matched gain is positive but official-native protocol evidence is incomplete"
                if gate.get("status") != "official_sota_admissible"
                else "official-native gate passed",
            }
        )
    return rows


def _priority_actions(gate_by_dataset: dict[str, dict[str, Any]], mdfa_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mdfa_gap_by_subset = {row["subset"]: row["gap_current_minus_reference"] for row in mdfa_rows}
    return [
        {
            "priority": "P0",
            "dataset": "SKAB",
            "reason": (
                "Current Macro-F1 is native-audited and improved, and the SKAB official baseline gate now separates fair frozen-record "
                "controls, official-source controls with frozen wrapper prediction records, recomputed official SKAB precomputed "
                "leaderboard rows, matched partial official notebook/core source reruns for T2/T2+Q, Isolation Forest, MSET, Vanilla-AE, and Conv-AE, and diagnostic LSTM-AE/MSCRED/Vanilla-LSTM reruns with frozen records whose row/label deltas are attributed to prediction-level rerun variance, but exact split/preprocessing, "
                "ArimaFD, and budget gates remain closed."
            ),
            "blocking_gates": gate_by_dataset.get("SKAB", {}).get("missing_gates", []),
            "next_experiments": [
                "Use skab_official_baseline_gate as the gate-closing checklist before any SKAB official SOTA wording.",
                "Promote the official precomputed leaderboard rows only as frozen repository-result evidence; rerun official or faithful SKAB notebook/core baselines before official SOTA wording.",
                "Use the T2/T2+Q, Isolation Forest, MSET, Vanilla-AE, and Conv-AE notebook/core reruns as partial provenance evidence, and keep the LSTM-AE/MSCRED/Vanilla-LSTM reruns as diagnostic frozen-record evidence despite their explained prediction-level deltas.",
                "Run or formally scope out the remaining official ArimaFD notebook.",
                "Add GDN and MTAD-GAT frozen prediction records only after their split, preprocessing, threshold, event-window, and budget contract matches the SKAB official/fair gate.",
                "Keep LLM verifier diagnostic until it beats the algorithmic anchor under validation and low-tail admission.",
            ],
        },
        {
            "priority": "P0",
            "dataset": "C-MAPSS",
            "reason": (
                "Native preprocessing is largely complete and MDFA source-style mean RMSE is competitive, but FD001/FD003 still trail "
                f"MDFA by {mdfa_gap_by_subset.get('FD001', 0.0):.4f}/{mdfa_gap_by_subset.get('FD003', 0.0):.4f} RMSE and exact published-budget gates remain closed."
            ),
            "blocking_gates": gate_by_dataset.get("C-MAPSS", {}).get("missing_gates", []),
            "next_experiments": [
                "Verify MDFA source fields for key-sensor/PCA policy, RUL cap/label policy, scheduler, and full-budget equivalence.",
                "Run the selected FD001/FD003 single-condition branch and FD002/FD004 condition-aware branch under a published-budget reproduction contract.",
                "Treat raw-test cap150 results as a negative control until uncapped/native RUL scoring closes the gap.",
            ],
        },
        {
            "priority": "P1",
            "dataset": "TEP",
            "reason": "The matched Target-F1 gain is largest, but too many external protocol gates are missing for official SOTA wording.",
            "blocking_gates": gate_by_dataset.get("TEP", {}).get("missing_gates", []),
            "next_experiments": [
                "Choose two external TEP/FDD protocols and reproduce their split, delay policy, class taxonomy, and metrics exactly.",
                "Export seed-level prediction artifacts for the strict 22-class route, not summary-only rows.",
            ],
        },
        {
            "priority": "P2",
            "dataset": "Hydraulic",
            "reason": "Near-ceiling gains are too small to carry the paper; use it as non-degradation evidence.",
            "blocking_gates": gate_by_dataset.get("Hydraulic", {}).get("missing_gates", []),
            "next_experiments": [
                "Reformat to a published four-target protocol only after SKAB/C-MAPSS gates stop blocking the main claim.",
                "Add one compatible temporal neural baseline if this benchmark is kept in the final main table.",
            ],
        },
    ]


def build_sota_gap_ledger() -> dict[str, Any]:
    gate_by_dataset = _gate_rows_by_dataset()
    mdfa_rows = _selected_mdfa_subset_rows()
    matched_rows = _matched_result_rows(gate_by_dataset)
    mdfa_mean_gap = None
    if mdfa_rows:
        mdfa_mean_gap = float(sum(row["gap_current_minus_reference"] for row in mdfa_rows) / len(mdfa_rows))
    official_admissible = [
        dataset for dataset, row in gate_by_dataset.items() if bool(row.get("official_sota_claim_admissible", False))
    ]
    return {
        "version": VERSION,
        "status": "official_sota_not_admissible" if not official_admissible else "partial_official_sota_admissible",
        "claim_rule": "Matched numerical gains are not official SOTA unless the exact-native gate for the dataset is fully true.",
        "official_sota_admissible_datasets": official_admissible,
        "matched_result_rows": matched_rows,
        "cmapss_mdfa_source_style_subset_gaps": mdfa_rows,
        "cmapss_mdfa_source_style_mean_gap_current_minus_reference": mdfa_mean_gap,
        "priority_actions": _priority_actions(gate_by_dataset, mdfa_rows),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# AAAI SOTA Gap Ledger",
        "",
        f"- Version: {payload['version']}",
        f"- Status: {payload['status']}",
        f"- Claim rule: {payload['claim_rule']}",
        "",
        "## Matched Results vs Current Anchors",
        "",
        "| Dataset | Metric | Anchor | Current | Improvement | Official status | Missing exact-native gates |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for row in payload["matched_result_rows"]:
        lines.append(
            "| {dataset} | {metric} | {anchor:.4f} | {current:.4f} | {delta:+.4f} | {status} | {missing} |".format(
                dataset=row["dataset"],
                metric=row["metric"],
                anchor=float(row["matched_anchor"]),
                current=float(row["current_matched"]),
                delta=float(row["matched_improvement"]),
                status=row["official_status"],
                missing=", ".join(row["missing_exact_native_gates"]) or "none",
            )
        )
    lines.extend(
        [
            "",
            "## C-MAPSS MDFA Source-Style Gap",
            "",
            "These rows are capped/source-style comparison evidence only. They are not official SOTA proof.",
            "",
            "| Subset | Current branch | Current RMSE | MDFA Table 5 RMSE | Gap current-reference | Boundary |",
            "|---|---|---:|---:|---:|---|",
        ]
    )
    for row in payload["cmapss_mdfa_source_style_subset_gaps"]:
        lines.append(
            "| {subset} | {branch} | {current:.4f} | {reference:.4f} | {gap:+.4f} | {boundary} |".format(
                subset=row["subset"],
                branch=row["selected_branch"],
                current=float(row["current_rmse"]),
                reference=float(row["reference_rmse"]),
                gap=float(row["gap_current_minus_reference"]),
                boundary=row["claim_boundary"],
            )
        )
    mean_gap = payload.get("cmapss_mdfa_source_style_mean_gap_current_minus_reference")
    if mean_gap is not None:
        lines.append("")
        lines.append(f"- Mean source-style RMSE gap current-reference: {float(mean_gap):+.4f}.")
    lines.extend(["", "## Priority Actions", ""])
    for action in payload["priority_actions"]:
        lines.append(f"### {action['priority']} {action['dataset']}")
        lines.append("")
        lines.append(f"- Reason: {action['reason']}")
        lines.append(f"- Blocking gates: {', '.join(action['blocking_gates']) or 'none'}")
        for experiment in action["next_experiments"]:
            lines.append(f"- Next: {experiment}")
        lines.append("")
    return "\n".join(lines)


def write_sota_gap_ledger(output_dir: Path | str = DEFAULT_OUTPUT_DIR) -> list[Path]:
    output_dir = Path(output_dir)
    payload = build_sota_gap_ledger()
    json_path = output_dir / "aaai_sota_gap_ledger.json"
    md_path = output_dir / "aaai_sota_gap_ledger.md"
    _write_json(json_path, payload)
    _write_text(md_path, render_markdown(payload))
    return [json_path, md_path]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Write the AAAI SOTA gap ledger.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    for path in write_sota_gap_ledger(args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
