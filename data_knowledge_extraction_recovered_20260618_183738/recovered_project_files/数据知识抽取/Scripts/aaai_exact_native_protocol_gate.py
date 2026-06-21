from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


VERSION = "aaai-exact-native-protocol-gate-v1"


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
        if (candidate / "Scripts" / "aaai_exact_native_protocol_gate.py").exists() and (candidate / "knowledge_exports").exists():
            return candidate
    return module_root


REPO_ROOT = _find_repo_root()
DEFAULT_OUTPUT_DIR = REPO_ROOT / "knowledge_exports" / "aaai_exact_native_protocol_gate"


DATASET_GATE_ROWS: list[dict[str, Any]] = [
    {
        "dataset": "TEP",
        "current_result": "Target-F1 0.9549 +/- 0.0023",
        "current_claim": "strong strict 22-class matched-protocol mechanism-diagnosis evidence",
        "native_reference_target": "external TEP/FDD paper protocol with identical split, delay handling, class taxonomy, metric, and budget",
        "gates": {
            "native_task_preserved": True,
            "exact_public_split": False,
            "exact_preprocessing": False,
            "exact_metric": False,
            "official_or_published_baseline_protocol": False,
            "threshold_or_delay_policy": False,
            "matched_budget": False,
            "seed_level_prediction_artifacts": False,
        },
        "blocking_evidence": [
            "Strict TEP full mechanism row is still summary-level in the ablation audit.",
            "External TEP papers use non-identical split, delay, taxonomy, or metric conventions.",
        ],
        "next_action": "Reproduce at least two cited TEP/FDD protocols end-to-end, including their split, preprocessing, delay handling, metric, budget, and seed-level predictions.",
    },
    {
        "dataset": "SKAB",
        "current_result": "Macro-F1 0.8450 +/- 0.0189",
        "current_claim": "matched-protocol native-audited algorithmic anomaly evidence; LLM condition verifier retained as diagnostic evidence",
        "native_reference_target": "official SKAB anomaly scoring with repository-level baseline implementations and declared event/point threshold policy",
        "gates": {
            "native_task_preserved": True,
            "exact_public_split": False,
            "exact_preprocessing": False,
            "exact_metric": True,
            "official_or_published_baseline_protocol": False,
            "threshold_or_delay_policy": True,
            "matched_budget": False,
            "seed_level_prediction_artifacts": True,
        },
        "blocking_evidence": [
            "The SKAB official baseline gate materializes USAD/TranAD-style frozen-record controls, official-source Anomaly Transformer provenance, frozen wrapper prediction records, official SKAB precomputed leaderboard rows with frozen records, matched partial official notebook/core source reruns for T2/T2+Q, Isolation Forest, MSET, Vanilla-AE, and Conv-AE, plus diagnostic LSTM-AE/MSCRED/Vanilla-LSTM source reruns, but keeps the official-baseline gate closed.",
            "Current official-source Anomaly Transformer wrapper is a patched matched control and keeps official_external_score=false.",
            "Official SKAB result pickles are aligned to raw data and the README outlier leaderboard is recomputed; T2/T2+Q, Isolation Forest, MSET, Vanilla-AE, and Conv-AE notebook/core logic are rerun or preserved from the pinned official environment and match the README rows. LSTM-AE, MSCRED, and Vanilla-LSTM are rerun with frozen records but do not match the official leaderboard within tolerance; the source-rerun delta audit attributes those mismatches to prediction-level rerun variance rather than row or label mismatch. ArimaFD, exact split, preprocessing, and budget matching are still not closed.",
            "The current native audit selects the algorithmic-only branch as the accuracy anchor and keeps LLM condition verification as diagnostic evidence.",
            "Proposed branches now have frozen point metrics and right-window changepoint event scores, but exact official split, preprocessing, baseline protocol, and compute budget are still not aligned.",
        ],
        "next_action": "Run official or faithful USAD, TranAD, GDN, MTAD-GAT, and Anomaly Transformer protocols with identical split, preprocessing, threshold, event-window, and budget rules.",
    },
    {
        "dataset": "Hydraulic",
        "current_result": "Macro-F1 0.9784 +/- 0.0301",
        "current_claim": "near-ceiling non-degradation and safety evidence",
        "native_reference_target": "published four-target Hydraulic condition-monitoring table with identical target definitions and metrics",
        "gates": {
            "native_task_preserved": True,
            "exact_public_split": False,
            "exact_preprocessing": False,
            "exact_metric": False,
            "official_or_published_baseline_protocol": False,
            "threshold_or_delay_policy": True,
            "matched_budget": False,
            "seed_level_prediction_artifacts": True,
        },
        "blocking_evidence": [
            "Hydraulic is used as a safety/non-degradation benchmark, not the main novelty benchmark.",
            "The final paper package does not yet align a published four-target table with identical formatting and deep temporal baselines.",
        ],
        "next_action": "Reformat to the published four-target protocol and add at least one compatible temporal neural baseline.",
    },
    {
        "dataset": "C-MAPSS",
        "current_result": "RUL RMSE 18.0617 +/- 0.3621; pseudo-terminal validation rerun RMSE 18.2840 +/- 0.1324",
        "current_claim": "original terminal RUL transfer evidence with cap-corrected long-window temporal anchor; path fusion not admitted",
        "native_reference_target": "NASA C-MAPSS subset-specific RUL scoring with compatible published prognostics baselines",
        "gates": {
            "native_task_preserved": True,
            "exact_public_split": True,
            "exact_preprocessing": True,
            "exact_metric": True,
            "official_or_published_baseline_protocol": False,
            "threshold_or_delay_policy": True,
            "matched_budget": False,
            "seed_level_prediction_artifacts": True,
        },
        "blocking_evidence": [
            "The task is correctly restored to original terminal RUL regression.",
            "The C-MAPSS native preprocessing manifest is complete: FD001-FD004 terminal test-unit records, RUL cap declaration, subset RMSE/score, continuous RUL metrics, train-only preprocessing declaration, and seed-level prediction archives are materialized.",
            "An LSTM sequence branch is materialized as a three-seed published-style local candidate for the LSTM RUL baseline family, but it is not an exact published-baseline reproduction.",
            "The current strongest local branch is the cap=150, window=160 GRU temporal anchor; AnchorPath path fusion is closed for C-MAPSS until it beats the same-window anchor.",
            "Train-unit pseudo-terminal validation selects the same w160/cap150 branch by RMSE, but official-test PHM score favors w80/cap150 by 408.20, so the score trade-off must be disclosed.",
            "The published-baseline alignment table is now materialized, but exact published-baseline reproduction, published-baseline preprocessing equivalence, and matched budget are still missing.",
            "The published-baseline contract is now materialized as a field-level checklist for LSTM, temporal CNN, attention-LSTM, and FD001-only CNN-LSTM references; it keeps official/published protocol and matched-budget gates closed until an exact reproduced baseline has source-matched fields and archived predictions.",
            "The LSTM source-protocol audit extracts the local LSTM configuration but records the primary full-text protocol as unavailable in the current environment, so source fields remain unverified.",
            "The open-protocol candidate audit identifies MDFA 2025 as an accessible all-subset published target and ACB 2021 as a fallback.",
            "The MDFA source profile reconciles FD001-FD004 raw-file counts with the MDFA published table, including FD004 train=249/test=248.",
            "The MDFA source-matched runner now uses source_2d time-feature convolutions; the all-subset smoke prediction archive is materialized and the FD001/FD003 low-dropout long-window plus FD002/FD004 condition-aware local branch archive is complete, but it cannot be promoted until PCA/key-sensor preprocessing and exact budget equivalence are verified.",
            "The MDFA strategy probe audit selects source2d_all24_pca_window80_dropout01_fd001_full and source2d_all24_pca_window80_dropout01_fd003_full for the single-condition branch while explicitly blocking any published-reproduction claim.",
        ],
        "next_action": "Run the MDFA 2025 source-matched runner at full budget after freezing PCA/key-sensor preprocessing, then reproduce selected published RUL baselines with identical FD001-FD004 split, published-compatible preprocessing, RUL cap, score/RMSE reporting, windows, seeds, and budget before literature-wide SOTA claims.",
    },
]


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _row_status(row: dict[str, Any]) -> str:
    gates = row["gates"]
    return "official_sota_admissible" if all(bool(value) for value in gates.values()) else "matched_only"


def build_exact_native_protocol_gate() -> dict[str, Any]:
    rows = []
    for row in DATASET_GATE_ROWS:
        status = _row_status(row)
        rows.append(
            {
                **row,
                "status": status,
                "official_sota_claim_admissible": status == "official_sota_admissible",
                "missing_gates": [name for name, value in row["gates"].items() if not bool(value)],
            }
        )
    admissible = [row["dataset"] for row in rows if row["official_sota_claim_admissible"]]
    return {
        "version": VERSION,
        "overall_status": "official_sota_admissible" if len(admissible) == len(rows) else "official_sota_not_admissible",
        "claim_rule": "Use matched-protocol or official-source adapted controls only until every exact-native gate is true for the target dataset.",
        "safe_overall_claim": "reliability-calibrated mechanism evidence fusion with strong matched-protocol industrial evidence",
        "unsafe_overall_claim": "universal official leaderboard SOTA across all datasets",
        "official_sota_admissible_datasets": admissible,
        "rows": rows,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# AAAI Exact-Native Protocol Gate",
        "",
        f"- Version: {payload['version']}",
        f"- Overall status: {payload['overall_status']}",
        f"- Claim rule: {payload['claim_rule']}",
        f"- Safe overall claim: {payload['safe_overall_claim']}",
        f"- Unsafe overall claim: {payload['unsafe_overall_claim']}",
        "",
        "This gate is stricter than the matched-protocol paper audit. A dataset can support official SOTA wording only when its task, split, preprocessing, metric, threshold/delay policy, budget, baseline protocol, and seed-level artifacts match the cited native benchmark protocol.",
        "",
        "## Dataset Gate Matrix",
        "",
        "| Dataset | Current result | Status | Missing exact-native gates | Safe current claim | Next action |",
        "|---|---|---|---|---|---|",
    ]
    for row in payload["rows"]:
        lines.append(
            "| {dataset} | {result} | {status} | {missing} | {claim} | {next_action} |".format(
                dataset=row["dataset"],
                result=row["current_result"],
                status=row["status"],
                missing=", ".join(row["missing_gates"]) if row["missing_gates"] else "none",
                claim=row["current_claim"],
                next_action=row["next_action"],
            )
        )
    lines.extend(["", "## Blocking Evidence", ""])
    for row in payload["rows"]:
        lines.append(f"### {row['dataset']}")
        lines.append("")
        lines.append(f"- Native reference target: {row['native_reference_target']}")
        lines.extend(f"- {item}" for item in row["blocking_evidence"])
        lines.append("")
    return "\n".join(lines)


def write_exact_native_protocol_gate(output_dir: Path | str = DEFAULT_OUTPUT_DIR) -> list[Path]:
    output_dir = Path(output_dir)
    os.makedirs(_fs_path(output_dir), exist_ok=True)
    payload = build_exact_native_protocol_gate()
    json_path = output_dir / "aaai_exact_native_protocol_gate.json"
    md_path = output_dir / "aaai_exact_native_protocol_gate.md"
    with open(_fs_path(json_path), "w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    with open(_fs_path(md_path), "w", encoding="utf-8") as handle:
        handle.write(render_markdown(payload))
    return [json_path, md_path]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Write exact-native protocol gate for official SOTA wording.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    for path in write_exact_native_protocol_gate(args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
