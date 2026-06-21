from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = REPO_ROOT / "knowledge_exports"
DEFAULT_OUTPUT_DIR = EXPORT_DIR
VIS_SOURCE = EXPORT_DIR / "paper_experiment_visualizations" / "experiment_visualization_source_data.csv"
TEP_BASELINE_REPORT = EXPORT_DIR / "tep_matched_strong_baseline_evidence.md"
SKAB_CF_SMOKE = EXPORT_DIR / "skab_cf_guarded_admission_smoke.md"
SEED_LEVEL_LEDGER = EXPORT_DIR / "aaai_seed_level_ablation_evidence.json"
MISSING_ABLATION_PLAN = EXPORT_DIR / "aaai_missing_ablation_execution_plan.md"
SKAB_TAIL_POLICY_REPLAY = (
    EXPORT_DIR
    / "aaai_missing_ablation_runs"
    / "skab_tail_safety_policy_replay"
    / "skab_tail_safety_policy_replay.json"
)
SKAB_CF_SUBSET_SMOKE = (
    EXPORT_DIR
    / "aaai_missing_ablation_runs"
    / "skab_cf_subset_smoke_summary"
    / "skab_cf_subset_smoke_summary.json"
)
SKAB_CF_SUBSET_FORMAL = (
    EXPORT_DIR
    / "aaai_missing_ablation_runs"
    / "skab_cf_subset_formal_summary"
    / "skab_cf_subset_formal_summary.json"
)


PLANNED_ABLATIONS = [
    "Anchor only",
    "Unfiltered evidence",
    "Expert only",
    "LLM only",
    "Lag/residual only",
    "Graph only",
    "No counterfactual guard",
    "No tail safety",
    "No complexity penalty",
    "Full model",
]


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _exists(path: Path) -> bool:
    return os.path.exists(_fs_path(path))


def _read(path: Path) -> str:
    if not _exists(path):
        return ""
    with open(_fs_path(path), encoding="utf-8") as handle:
        return handle.read()


def _rel(path: Path | str) -> str:
    path = Path(path)
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _read_visual_rows(path: Path = VIS_SOURCE) -> list[dict[str, str]]:
    if not _exists(path):
        return []
    with open(_fs_path(path), encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _load_seed_level_ledger(path: Path = SEED_LEVEL_LEDGER) -> dict[str, Any]:
    if not _exists(path):
        return {}
    return json.loads(_read(path))


def _load_json(path: Path) -> dict[str, Any]:
    if not _exists(path):
        return {}
    try:
        return json.loads(_read(path))
    except json.JSONDecodeError:
        return {}


def _ledger_evidence(ledger: dict[str, Any], *fragments: str) -> list[str]:
    rows = ledger.get("rows", [])
    evidence = []
    for row in rows:
        text = " ".join(
            [
                str(row.get("group", "")),
                str(row.get("variant", "")),
                str(row.get("planned_ablation_link", "")),
            ]
        ).lower()
        if all(fragment.lower() in text for fragment in fragments):
            evidence.append(
                f"{row.get('group')}::{row.get('variant')} n={row.get('n_seeds')} "
                f"mean={row.get('mean'):.4f} std={row.get('std'):.4f}"
            )
    return evidence


def _has_complete_ledger_variant(ledger: dict[str, Any], variant: str) -> bool:
    for row in ledger.get("rows", []):
        if str(row.get("variant", "")) != str(variant):
            continue
        if int(row.get("n_seeds", 0) or 0) >= 3 and len(row.get("artifact_paths", {}) or {}) >= 3:
            return True
    return False


def _find_rows(rows: list[dict[str, str]], group: str, *name_fragments: str) -> list[dict[str, str]]:
    found = []
    for row in rows:
        if row.get("group") != group:
            continue
        name = row.get("name", "").lower()
        if all(fragment.lower() in name for fragment in name_fragments):
            found.append(row)
    return found


def _row_summary(row: dict[str, str]) -> str:
    name = row.get("name", "")
    metric_a = row.get("metric_a", "")
    metric_b = row.get("metric_b", "")
    std_a = row.get("std_a", "")
    std_b = row.get("std_b", "")
    delta = row.get("delta", "")
    note = row.get("note", "")
    parts = [name]
    if metric_a:
        parts.append(f"metric_a={metric_a}")
    if metric_b:
        parts.append(f"metric_b={metric_b}")
    if std_a:
        parts.append(f"std_a={std_a}")
    if std_b:
        parts.append(f"std_b={std_b}")
    if delta:
        parts.append(f"delta={delta}")
    if note:
        parts.append(note)
    return "; ".join(parts)


def _evidence_item(name: str, status: str, evidence: list[str], gap: str, next_action: str) -> dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "evidence": evidence,
        "gap": gap,
        "next_action": next_action,
    }


def build_ablation_coverage_report() -> dict[str, Any]:
    rows = _read_visual_rows()
    ledger = _load_seed_level_ledger()
    tep_report = _read(TEP_BASELINE_REPORT)
    skab_cf = _read(SKAB_CF_SMOKE)
    tail_policy = _load_json(SKAB_TAIL_POLICY_REPLAY)
    cf_subset_smoke = _load_json(SKAB_CF_SUBSET_SMOKE)
    cf_subset_formal = _load_json(SKAB_CF_SUBSET_FORMAL)
    cf_subset_formal_complete = cf_subset_formal.get("status") == "complete_formal"

    main_rows = _find_rows(rows, "main_multi_benchmark")
    tep_full = _find_rows(rows, "tep_mechanism_ablation", "full")
    tep_all_edge = _find_rows(rows, "tep_mechanism_ablation", "all edges")
    tep_no_expert = _find_rows(rows, "tep_mechanism_ablation", "no expert")
    tep_no_llm = _find_rows(rows, "tep_mechanism_ablation", "no llm")
    tep_no_residual = _find_rows(rows, "tep_mechanism_ablation", "no residual")
    tep_no_pairwise = _find_rows(rows, "tep_mechanism_ablation", "no pairwise")
    reliability_all_edge = _find_rows(rows, "reliability_ablation", "all-edge")
    reliability_prior = _find_rows(rows, "reliability_ablation", "prior-only")
    reliability_cf = _find_rows(rows, "reliability_ablation", "cf-guarded")
    source_pruned = _find_rows(rows, "reliability_ablation", "source-pruned")
    no_complexity_complete = _has_complete_ledger_variant(
        ledger,
        "expert_llm_candidate_data_gate_no_complexity",
    )

    items = [
        _evidence_item(
            "Anchor only",
            "seed_level_evidence",
            _ledger_evidence(ledger, "anchor") + [_row_summary(row) for row in main_rows],
            "Seed-level anchor rows are now copied for SKAB, C-MAPSS, TEP sequence controls, and SKAB mechanism-gate controls; strict TEP mechanism full-model raw predictions remain summary-level.",
            "Attach or regenerate strict TEP mechanism per-seed prediction artifacts if the final table uses that row as the primary anchor contrast.",
        ),
        _evidence_item(
            "Unfiltered evidence",
            "seed_level_evidence",
            _ledger_evidence(ledger, "unfiltered") + [_row_summary(row) for row in tep_all_edge + reliability_all_edge + reliability_prior],
            "Unfiltered graph/lag rows now have copied seed-level artifacts for TEP sequence and SKAB raw expert graph; SKAB prior-only visualization rows still need raw artifact pointers if used.",
            "Use the ledger rows as the formal unfiltered-evidence evidence and keep prior-only SKAB as supporting summary unless raw artifacts are attached.",
        ),
        _evidence_item(
            "Expert only",
            "seed_level_evidence",
            _ledger_evidence(ledger, "expert") + [_row_summary(row) for row in tep_no_expert],
            "SKAB expert-only/late-path mechanism rows are now seed-level; strict TEP has expert-removal summary but not a clean TEP expert-only route.",
            "Use SKAB for expert-gating evidence and avoid claiming a clean TEP expert-only route until it is run or located.",
        ),
        _evidence_item(
            "LLM only",
            "seed_level_safety_evidence",
            _ledger_evidence(ledger, "llm") + [_row_summary(row) for row in tep_no_llm],
            "The SKAB LLM condition candidate gate is now seed-level but is a safety/rejection result, not a positive LLM-only improvement claim.",
            "Report this as reliability admission rejecting/no-gain LLM evidence unless a positive LLM-only route is later validated.",
        ),
        _evidence_item(
            "Lag/residual only",
            "seed_level_evidence",
            _ledger_evidence(ledger, "lag") + _ledger_evidence(ledger, "residual") + [_row_summary(row) for row in tep_no_residual] + (["TEP matched residual-gated sequence baselines present."] if "ResidualGatedLagged" in tep_report else []),
            "TEP sequence residual-gated and C-MAPSS temporal-mixer rows are seed-level; strict TEP no-residual remains a summary row.",
            "Use sequence/C-MAPSS seed-level rows for temporal-path evidence and keep strict TEP no-residual as supporting summary.",
        ),
        _evidence_item(
            "Graph only",
            "seed_level_evidence",
            _ledger_evidence(ledger, "graph") + ["TEP no-expert/sequence-graph and matched graph-temporal reports exist." if tep_report else ""],
            "Graph-only evidence now has TEP no-graph controls and SKAB algorithmic-control rows, but graph propagation is still partly coupled to lag/residual channels.",
            "Frame graph evidence as graph-temporal controls unless a pure graph-only route is needed for the final table.",
        ),
        _evidence_item(
            "No counterfactual guard",
            "seed_level_evidence" if cf_subset_formal_complete else "smoke_only",
            [_row_summary(row) for row in reliability_cf]
            + (["SKAB CF-guarded smoke exists and explicitly says final three-seed ablation is still needed."] if skab_cf else [])
            + (
                [
                    (
                        "SKAB validation-positive subset formal; cf={cf:.4f}+/-{cfstd:.4f}; "
                        "no_cf={no_cf:.4f}+/-{nocfstd:.4f}; cf_minus_no_cf={diff:+.4f}+/-{diffstd:.4f}; source={source}"
                    ).format(
                        cf=float(
                            cf_subset_formal.get("aggregates", {})
                            .get("cf_standard", {})
                            .get("test_macro_f1", {})
                            .get("mean", 0.0)
                        ),
                        cfstd=float(
                            cf_subset_formal.get("aggregates", {})
                            .get("cf_standard", {})
                            .get("test_macro_f1", {})
                            .get("std", 0.0)
                        ),
                        no_cf=float(
                            cf_subset_formal.get("aggregates", {})
                            .get("no_cf", {})
                            .get("test_macro_f1", {})
                            .get("mean", 0.0)
                        ),
                        nocfstd=float(
                            cf_subset_formal.get("aggregates", {})
                            .get("no_cf", {})
                            .get("test_macro_f1", {})
                            .get("std", 0.0)
                        ),
                        diff=float(cf_subset_formal.get("cf_minus_no_cf_test_macro_f1", {}).get("mean", 0.0)),
                        diffstd=float(cf_subset_formal.get("cf_minus_no_cf_test_macro_f1", {}).get("std", 0.0)),
                        source=_rel(SKAB_CF_SUBSET_FORMAL),
                    )
                ]
                if cf_subset_formal
                else []
            )
            + (
                [
                    (
                        "SKAB validation-positive subset smoke; cf={cf:.4f}+/-{cfstd:.4f}; "
                        "no_cf={no_cf:.4f}+/-{nocfstd:.4f}; cf_minus_no_cf={diff:+.4f}+/-{diffstd:.4f}; source={source}"
                    ).format(
                        cf=float(
                            cf_subset_smoke.get("aggregates", {})
                            .get("cf_standard", {})
                            .get("test_macro_f1", {})
                            .get("mean", 0.0)
                        ),
                        cfstd=float(
                            cf_subset_smoke.get("aggregates", {})
                            .get("cf_standard", {})
                            .get("test_macro_f1", {})
                            .get("std", 0.0)
                        ),
                        no_cf=float(
                            cf_subset_smoke.get("aggregates", {})
                            .get("no_cf", {})
                            .get("test_macro_f1", {})
                            .get("mean", 0.0)
                        ),
                        nocfstd=float(
                            cf_subset_smoke.get("aggregates", {})
                            .get("no_cf", {})
                            .get("test_macro_f1", {})
                            .get("std", 0.0)
                        ),
                        diff=float(cf_subset_smoke.get("cf_minus_no_cf_test_macro_f1", {}).get("mean", 0.0)),
                        diffstd=float(cf_subset_smoke.get("cf_minus_no_cf_test_macro_f1", {}).get("std", 0.0)),
                        source=_rel(SKAB_CF_SUBSET_SMOKE),
                    )
                ]
                if cf_subset_smoke
                else []
            ),
            "Formal matched CF/no-CF evidence is complete and shows a non-differential accuracy effect; CF should be treated as a reliability/interpretability guard."
            if cf_subset_formal_complete
            else "Counterfactual admission is implemented and now has a three-seed validation-positive subset smoke, but the no-CF removal row is still not a full-budget formal ablation.",
            "Report the formal non-differential result and keep CF as a safety/diagnostic mechanism rather than a main accuracy source."
            if cf_subset_formal_complete
            else "Run final no-counterfactual-guard vs CF-guarded admission under the formal SKAB protocol after freezing the subset-sweep candidate selection.",
        ),
        _evidence_item(
            "No tail safety",
            "seed_level_policy_replay" if tail_policy.get("status") == "complete_policy_replay" else "missing_final_scored_row",
            [
                (
                    "SKAB tail policy replay; rows={rows}; changed_admissions={changed}; "
                    "candidate_low_tail_gain={mean:.4f}+/-{std:.4f}; source={source}"
                ).format(
                    rows=len(tail_policy.get("rows", []) or []),
                    changed=int(tail_policy.get("changed_admissions", 0) or 0),
                    mean=float(tail_policy.get("candidate_low_tail_gain_mean", 0.0) or 0.0),
                    std=float(tail_policy.get("candidate_low_tail_gain_std", 0.0) or 0.0),
                    source=_rel(SKAB_TAIL_POLICY_REPLAY),
                )
            ]
            if tail_policy
            else [],
            "The matched SKAB policy replay removes only H_k and shows no final-protocol admission changes because all admitted candidates satisfy low-tail safety."
            if tail_policy.get("status") == "complete_policy_replay"
            else "Low-tail harm is part of the theory and diagnostics, but no final row removes only H_k under matched seeds.",
            "Use this as a non-differential safety ablation; add an optional tail-stress branch only if the final paper needs a visibly rejected low-tail case."
            if tail_policy.get("status") == "complete_policy_replay"
            else "Run no-tail-safety admission and report low-tail class/group deltas.",
        ),
        _evidence_item(
            "No complexity penalty",
            "seed_level_evidence" if no_complexity_complete else "partial_seed_level_evidence",
            _ledger_evidence(ledger, "complexity") + [_row_summary(row) for row in source_pruned],
            "The matched complexity-guarded and no-complexity rows are now complete with copied three-seed artifacts."
            if no_complexity_complete
            else "Source-pruning evidence exists, and the narrow source-family scaling ablation flag is now implemented, but the formal three-seed no-complexity row is not yet scored.",
            "Use the no-complexity row as final B_k ablation evidence and report source-family burden beside metric deltas."
            if no_complexity_complete
            else "Execute the `expert_llm_candidate_data_gate_no_complexity` matrix row and report source-family burden beside metric deltas.",
        ),
        _evidence_item(
            "Full model",
            "seed_level_evidence",
            _ledger_evidence(ledger, "full") + [_row_summary(row) for row in tep_full],
            "SKAB and C-MAPSS full/proposed rows are seed-level; strict TEP full mechanism row remains summary-level.",
            "Attach strict TEP full per-seed artifacts if the final main table relies on raw prediction audit for that row.",
        ),
    ]

    missing_or_incomplete = [
        item["name"]
        for item in items
        if item["status"] in {"partial", "smoke_only", "missing_final_scored_row", "partial_seed_level_evidence"}
    ]
    return {
        "status": "not_complete" if missing_or_incomplete else "complete",
        "planned_ablation_count": len(PLANNED_ABLATIONS),
        "covered_ablation_count": len([item for item in items if item["evidence"]]),
        "seed_level_ledger": _rel(SEED_LEVEL_LEDGER) if _exists(SEED_LEVEL_LEDGER) else None,
        "missing_ablation_execution_plan": _rel(MISSING_ABLATION_PLAN) if _exists(MISSING_ABLATION_PLAN) else None,
        "items": items,
        "missing_or_incomplete": missing_or_incomplete,
        "completion_rule": (
            "A final AAAI ablation row is complete only when it has matched-protocol seed-level metrics, "
            "source artifact pointers, and a clear intervention that changes exactly one mechanism term."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# AAAI Ablation Coverage Audit",
        "",
        f"- Status: {report['status']}",
        f"- Planned ablations: {report['planned_ablation_count']}",
        f"- Rows with some evidence: {report['covered_ablation_count']}",
        f"- Completion rule: {report['completion_rule']}",
        f"- Missing-row execution plan: `{report['missing_ablation_execution_plan']}`"
        if report.get("missing_ablation_execution_plan")
        else "- Missing-row execution plan: not generated",
        "",
        "| Ablation | Status | Evidence | Gap | Next action |",
        "|---|---|---|---|---|",
    ]
    for item in report["items"]:
        evidence = "<br>".join(item["evidence"]) if item["evidence"] else "none"
        lines.append(f"| {item['name']} | {item['status']} | {evidence} | {item['gap']} | {item['next_action']} |")
    lines.extend(["", "## Missing or Incomplete Rows", ""])
    lines.extend(f"- {name}" for name in report["missing_or_incomplete"])
    lines.append("")
    return "\n".join(lines)


def write_ablation_coverage(output_dir: Path | str = DEFAULT_OUTPUT_DIR) -> list[Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_ablation_coverage_report()
    json_path = output_dir / "aaai_ablation_coverage_audit.json"
    md_path = output_dir / "aaai_ablation_coverage_audit.md"
    with open(_fs_path(json_path), "w", encoding="utf-8") as handle:
        handle.write(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    with open(_fs_path(md_path), "w", encoding="utf-8") as handle:
        handle.write(render_markdown(report))
    return [json_path, md_path]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Summarize AAAI ablation coverage and remaining final-table gaps.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    for path in write_ablation_coverage(args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
