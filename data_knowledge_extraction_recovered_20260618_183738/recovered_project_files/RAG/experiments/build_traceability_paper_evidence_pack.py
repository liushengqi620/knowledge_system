"""Build paper-ready evidence artifacts for KG-enhanced traceability.

This script consumes the already generated paper-demo outputs. It does not
rerun the long traceability experiment. Its job is to package metrics, audit
templates, blinded review files, and paper tables in a reproducible form.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DEMO_DIR = PROJECT_ROOT / "outputs" / "paper_demo_traceability"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "traceability_paper_evidence_pack"

AUDIT_DIMENSIONS = [
    ("expert_root_cause_correct", "Root-cause correctness"),
    ("expert_path_plausible", "Trace-path plausibility"),
    ("expert_action_useful", "Action usefulness"),
]

PAPER_METHODS = [
    "label_prior_majority",
    "feature_group_prior",
    "feature_name_naive_bayes",
    "kg_anchor_reasoning",
    "kg_path_reasoning",
    "proposed_score_fusion",
    "proposed_explainable_rerank",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: Sequence[dict[str, Any]], fieldnames: Sequence[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        keys: list[str] = []
        for row in rows:
            for key in row:
                if key not in keys:
                    keys.append(key)
        fieldnames = keys
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def fmt(value: Any, digits: int = 4) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, str):
        try:
            value = float(value)
        except ValueError:
            return value
    return f"{float(value):.{digits}f}"


def tex_escape(text: Any) -> str:
    return str(text).replace("_", r"\_").replace("%", r"\%").replace("&", r"\&")


def parse_audit_score(value: Any) -> float | None:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    normalized = raw.lower()
    missing = {"na", "n/a", "none", "null", "-", "skip", "unknown", "not sure"}
    yes = {"1", "1.0", "yes", "y", "true", "correct", "plausible", "useful", "pass"}
    no = {"0", "0.0", "no", "n", "false", "incorrect", "implausible", "useless", "fail"}
    partial = {"0.5", ".5", "partial", "partly", "half", "weak", "acceptable_with_reservation"}
    if normalized in missing:
        return None
    if normalized in yes:
        return 1.0
    if normalized in no:
        return 0.0
    if normalized in partial:
        return 0.5
    try:
        score = float(normalized)
    except ValueError:
        return None
    if 0.0 <= score <= 1.0:
        return score
    return None


def wilson_interval(accepted: int, total: int, z: float = 1.96) -> tuple[float | None, float | None]:
    if total <= 0:
        return None, None
    p = accepted / total
    denom = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    margin = z * math.sqrt((p * (1 - p) / total) + (z * z / (4 * total * total))) / denom
    return max(0.0, center - margin), min(1.0, center + margin)


def summarize_scores(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    dimension_rows: list[dict[str, Any]] = []
    total_scores = 0
    for column, label in AUDIT_DIMENSIONS:
        scores = [parse_audit_score(row.get(column)) for row in rows]
        valid = [score for score in scores if score is not None]
        accepted = [score for score in valid if score >= 0.5]
        strict = [score for score in valid if score == 1.0]
        low, high = wilson_interval(len(accepted), len(valid))
        total_scores += len(valid)
        dimension_rows.append(
            {
                "dimension": label,
                "column": column,
                "scored_cases": len(valid),
                "mean_score": round(sum(valid) / len(valid), 4) if valid else None,
                "strict_acceptance_rate": round(len(strict) / len(valid), 4) if valid else None,
                "usable_acceptance_rate": round(len(accepted) / len(valid), 4) if valid else None,
                "usable_acceptance_ci95_low": round(low, 4) if low is not None else None,
                "usable_acceptance_ci95_high": round(high, 4) if high is not None else None,
            }
        )

    complete_rows = []
    usable_rows = []
    strict_rows = []
    for row in rows:
        scores = {column: parse_audit_score(row.get(column)) for column, _ in AUDIT_DIMENSIONS}
        if all(score is not None for score in scores.values()):
            complete_rows.append(row)
            if all(score == 1.0 for score in scores.values() if score is not None):
                strict_rows.append(row)
            if all(score is not None and score >= 0.5 for score in scores.values()):
                usable_rows.append(row)

    scenario_rows: list[dict[str, Any]] = []
    by_scenario: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_scenario[row.get("scenario", "unknown")].append(row)
    for scenario in sorted(by_scenario):
        subset = by_scenario[scenario]
        scored = 0
        mean_scores: list[float] = []
        for row in subset:
            values = [parse_audit_score(row.get(column)) for column, _ in AUDIT_DIMENSIONS]
            valid = [value for value in values if value is not None]
            if valid:
                scored += 1
                mean_scores.append(sum(valid) / len(valid))
        scenario_rows.append(
            {
                "scenario": scenario,
                "audit_rows": len(subset),
                "rows_with_any_score": scored,
                "mean_available_score": round(sum(mean_scores) / len(mean_scores), 4) if mean_scores else None,
            }
        )

    agreement = pairwise_reviewer_agreement(rows)
    status = "audit_scored" if total_scores else "audit_pending"
    return {
        "status": status,
        "audit_rows": len(rows),
        "total_scored_cells": total_scores,
        "complete_case_count": len(complete_rows),
        "strict_full_acceptance_rate": round(len(strict_rows) / len(complete_rows), 4) if complete_rows else None,
        "usable_full_acceptance_rate": round(len(usable_rows) / len(complete_rows), 4) if complete_rows else None,
        "dimensions": dimension_rows,
        "scenarios": scenario_rows,
        "inter_reviewer_agreement": agreement,
    }


def pairwise_reviewer_agreement(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (row.get("scenario", ""), row.get("record_id", "") or row.get("case_id", ""))
        groups[key].append(row)

    output: list[dict[str, Any]] = []
    for column, label in AUDIT_DIMENSIONS:
        agree = 0
        pairs = 0
        for group_rows in groups.values():
            if len(group_rows) < 2:
                continue
            values = [parse_audit_score(row.get(column)) for row in group_rows]
            values = [value for value in values if value is not None]
            for i in range(len(values)):
                for j in range(i + 1, len(values)):
                    pairs += 1
                    agree += int(values[i] == values[j])
        output.append(
            {
                "dimension": label,
                "reviewer_pairs": pairs,
                "pairwise_agreement": round(agree / pairs, 4) if pairs else None,
            }
        )
    return output


def metric_lookup(metrics: Sequence[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(row["scenario"], row["method"]): row for row in metrics}


def build_controlled_setting_rows(metrics: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    lookup = metric_lookup(metrics)
    scenarios = [
        "full_weak_label_masked_text",
        "balanced_label_masked_text",
        "balanced_group_only",
        "balanced_feature_anonymized",
    ]
    rows: list[dict[str, Any]] = []
    for scenario in scenarios:
        feature = lookup.get((scenario, "feature_group_prior"), {})
        kg = lookup.get((scenario, "kg_path_reasoning"), {})
        proposed = lookup.get((scenario, "proposed_explainable_rerank"), {})
        rows.append(
            {
                "scenario": scenario,
                "feature_hit1": feature.get("primary_hit1"),
                "kg_hit1": kg.get("primary_hit1"),
                "kg_hit3": kg.get("primary_hit3"),
                "kg_coverage": kg.get("explanation_coverage"),
                "kg_path_quality": kg.get("avg_path_quality"),
                "proposed_hit1": proposed.get("primary_hit1"),
                "proposed_coverage": proposed.get("explanation_coverage"),
                "proposed_path_quality": proposed.get("avg_path_quality"),
            }
        )
    return rows


def build_ablation_rows(metrics: Sequence[dict[str, Any]], scenario: str = "balanced_label_masked_text") -> list[dict[str, Any]]:
    lookup = metric_lookup(metrics)
    rows: list[dict[str, Any]] = []
    for method in PAPER_METHODS:
        row = lookup.get((scenario, method), {})
        if not row:
            continue
        rows.append(
            {
                "method": method,
                "hit1": row.get("primary_hit1"),
                "hit3": row.get("primary_hit3"),
                "mrr": row.get("mrr"),
                "macro_f1": row.get("macro_f1"),
                "coverage": row.get("explanation_coverage"),
                "path_quality": row.get("avg_path_quality"),
                "faithful_path_rate": row.get("faithful_path_rate"),
            }
        )
    return rows


def build_explainability_rows(metrics: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    lookup = metric_lookup(metrics)
    rows: list[dict[str, Any]] = []
    scenarios = ["full_weak_label_masked_text", "balanced_label_masked_text", "balanced_group_only"]
    methods = ["kg_path_reasoning", "proposed_score_fusion", "proposed_explainable_rerank"]
    for scenario in scenarios:
        for method in methods:
            row = lookup.get((scenario, method), {})
            if not row:
                continue
            rows.append(
                {
                    "scenario": scenario,
                    "method": method,
                    "explanation_coverage": row.get("explanation_coverage", 0),
                    "avg_path_quality": row.get("avg_path_quality", 0),
                    "faithful_path_rate": row.get("faithful_path_rate", 0),
                }
            )
    return rows


def render_markdown_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    return lines


def render_paper_tables_md(controlled: Sequence[dict[str, Any]], ablation: Sequence[dict[str, Any]], audit: dict[str, Any]) -> str:
    lines = [
        "# Paper-Ready Traceability Tables",
        "",
        "## Controlled Scenario Results",
        "",
    ]
    lines.extend(
        render_markdown_table(
            [
                "Scenario",
                "Feature Hit@1",
                "KG Hit@1",
                "KG Hit@3",
                "KG Coverage",
                "KG Path Quality",
                "Proposed Hit@1",
                "Proposed Coverage",
                "Proposed Path Quality",
            ],
            [
                [
                    row["scenario"],
                    fmt(row["feature_hit1"]),
                    fmt(row["kg_hit1"]),
                    fmt(row["kg_hit3"]),
                    fmt(row["kg_coverage"]),
                    fmt(row["kg_path_quality"]),
                    fmt(row["proposed_hit1"]),
                    fmt(row["proposed_coverage"]),
                    fmt(row["proposed_path_quality"]),
                ]
                for row in controlled
            ],
        )
    )
    lines.extend(["", "## Balanced-Scenario Ablation", ""])
    lines.extend(
        render_markdown_table(
            ["Method", "Hit@1", "Hit@3", "MRR", "Macro F1", "Coverage", "Path Quality", "Faithful Path Rate"],
            [
                [
                    row["method"],
                    fmt(row["hit1"]),
                    fmt(row["hit3"]),
                    fmt(row["mrr"]),
                    fmt(row["macro_f1"]),
                    fmt(row["coverage"]),
                    fmt(row["path_quality"]),
                    fmt(row["faithful_path_rate"]),
                ]
                for row in ablation
            ],
        )
    )
    lines.extend(["", "## Expert Audit Status", ""])
    lines.append(f"- Status: `{audit['status']}`")
    lines.append(f"- Audit rows: `{audit['audit_rows']}`")
    lines.append(f"- Total scored cells: `{audit['total_scored_cells']}`")
    if audit["status"] == "audit_pending":
        lines.append("- No expert-score cells are filled yet. Use the blinded audit CSV before claiming expert-validated traceability performance.")
    else:
        lines.extend(["", "| Dimension | Scored Cases | Mean Score | Usable Acceptance | 95% CI |", "|---|---:|---:|---:|---:|"])
        for row in audit["dimensions"]:
            ci = f"{fmt(row['usable_acceptance_ci95_low'])}-{fmt(row['usable_acceptance_ci95_high'])}"
            lines.append(
                f"| {row['dimension']} | {row['scored_cases']} | {fmt(row['mean_score'])} | {fmt(row['usable_acceptance_rate'])} | {ci} |"
            )
    return "\n".join(lines) + "\n"


def render_paper_tables_tex(controlled: Sequence[dict[str, Any]], ablation: Sequence[dict[str, Any]]) -> str:
    lines = [
        "% Generated by experiments/build_traceability_paper_evidence_pack.py",
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Controlled scenario results for KG-enhanced traceability.}",
        "\\begin{tabular}{lrrrr}",
        "\\toprule",
        "Scenario & KG Hit@3 & KG Cov. & Proposed Hit@1 & Proposed PathQ \\\\",
        "\\midrule",
    ]
    for row in controlled:
        lines.append(
            f"{tex_escape(row['scenario'])} & {fmt(row['kg_hit3'])} & {fmt(row['kg_coverage'])} & {fmt(row['proposed_hit1'])} & {fmt(row['proposed_path_quality'])} \\\\"
        )
    lines.extend(
        [
            "\\bottomrule",
            "\\end{tabular}",
            "\\end{table}",
            "",
            "\\begin{table}[t]",
            "\\centering",
            "\\caption{Balanced-scenario ablation.}",
            "\\begin{tabular}{lrrrr}",
            "\\toprule",
            "Method & Hit@1 & Hit@3 & Macro-F1 & PathQ \\\\",
            "\\midrule",
        ]
    )
    for row in ablation:
        lines.append(
            f"{tex_escape(row['method'])} & {fmt(row['hit1'])} & {fmt(row['hit3'])} & {fmt(row['macro_f1'])} & {fmt(row['path_quality'])} \\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}", "\\end{table}", ""])
    return "\n".join(lines)


def render_svg_bar(rows: Sequence[dict[str, Any]]) -> str:
    selected = [row for row in rows if row["scenario"] == "balanced_label_masked_text"]
    labels = [row["method"].replace("_", " ") for row in selected]
    values = [float(row.get("avg_path_quality") or 0.0) for row in selected]
    width = 900
    height = 320
    left = 220
    top = 40
    bar_h = 34
    gap = 24
    max_w = 600
    colors = ["#3b82f6", "#10b981", "#f59e0b"]
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="24" y="26" font-family="Arial" font-size="18" font-weight="700">Balanced Scenario: Path Quality</text>',
    ]
    for idx, (label, value) in enumerate(zip(labels, values)):
        y = top + idx * (bar_h + gap)
        w = max(2, int(value * max_w))
        color = colors[idx % len(colors)]
        lines.append(f'<text x="24" y="{y + 23}" font-family="Arial" font-size="13" fill="#111827">{label}</text>')
        lines.append(f'<rect x="{left}" y="{y}" width="{max_w}" height="{bar_h}" rx="4" fill="#e5e7eb"/>')
        lines.append(f'<rect x="{left}" y="{y}" width="{w}" height="{bar_h}" rx="4" fill="{color}"/>')
        lines.append(f'<text x="{left + max_w + 16}" y="{y + 23}" font-family="Arial" font-size="13" fill="#111827">{value:.4f}</text>')
    axis_y = top + len(selected) * (bar_h + gap) + 6
    lines.append(f'<line x1="{left}" y1="{axis_y}" x2="{left + max_w}" y2="{axis_y}" stroke="#9ca3af" stroke-width="1"/>')
    for tick in [0.0, 0.25, 0.5, 0.75, 1.0]:
        x = left + int(tick * max_w)
        lines.append(f'<line x1="{x}" y1="{axis_y}" x2="{x}" y2="{axis_y + 6}" stroke="#9ca3af" stroke-width="1"/>')
        lines.append(f'<text x="{x - 10}" y="{axis_y + 24}" font-family="Arial" font-size="11" fill="#4b5563">{tick:.2f}</text>')
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def build_blinded_audit_files(audit_rows: Sequence[dict[str, Any]], output_dir: Path) -> dict[str, str]:
    blind_rows: list[dict[str, Any]] = []
    key_rows: list[dict[str, Any]] = []
    for idx, row in enumerate(audit_rows, start=1):
        case_id = f"TACE-{idx:04d}"
        blind_rows.append(
            {
                "case_id": case_id,
                "scenario": row.get("scenario", ""),
                "predicted_top3": row.get("predicted_top3", ""),
                "top_features": row.get("top_features", ""),
                "trace_path": row.get("trace_path", ""),
                "path_quality_proxy": row.get("path_quality_proxy", ""),
                "expert_root_cause_correct": row.get("expert_root_cause_correct", ""),
                "expert_path_plausible": row.get("expert_path_plausible", ""),
                "expert_action_useful": row.get("expert_action_useful", ""),
                "expert_notes": row.get("expert_notes", ""),
            }
        )
        key_rows.append(
            {
                "case_id": case_id,
                "scenario": row.get("scenario", ""),
                "record_id": row.get("record_id", ""),
                "gold_primary_label": row.get("gold_primary_label", ""),
                "predicted_top3": row.get("predicted_top3", ""),
            }
        )
    blind_path = output_dir / "expert_audit_blind.csv"
    key_path = output_dir / "expert_audit_key.csv"
    write_csv(blind_path, blind_rows)
    write_csv(key_path, key_rows)
    return {"blind_audit_csv": str(blind_path), "audit_key_csv": str(key_path)}


def render_casebook(audit_rows: Sequence[dict[str, Any]], *, limit: int = 30) -> str:
    lines = [
        "# Expert Review Casebook",
        "",
        "Use this casebook together with `expert_audit_blind.csv`. Scores should be entered as 1, 0.5, 0, or left blank when the case is not reviewable.",
        "",
    ]
    for idx, row in enumerate(audit_rows[:limit], start=1):
        lines.extend(
            [
                f"## Case TACE-{idx:04d}",
                "",
                f"- Scenario: `{row.get('scenario', '')}`",
                f"- Predicted top-3 causes: `{row.get('predicted_top3', '')}`",
                f"- Top features: `{row.get('top_features', '')}`",
                f"- Trace path: {row.get('trace_path', '') or 'none'}",
                f"- Path-quality proxy: `{row.get('path_quality_proxy', '')}`",
                "",
            ]
        )
    return "\n".join(lines)


def build_evidence_pack(
    demo_dir: Path = DEFAULT_DEMO_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    audit_file: Path | None = None,
) -> dict[str, Any]:
    metrics_path = demo_dir / "metrics.json"
    audit_path = audit_file or demo_dir / "expert_audit_template.csv"
    if not metrics_path.exists():
        raise FileNotFoundError(f"Missing metrics file: {metrics_path}")
    if not audit_path.exists():
        raise FileNotFoundError(f"Missing expert audit template: {audit_path}")

    metrics = read_json(metrics_path)
    audit_rows = read_csv(audit_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    audit_scores = summarize_scores(audit_rows)
    controlled_rows = build_controlled_setting_rows(metrics)
    ablation_rows = build_ablation_rows(metrics)
    explainability_rows = build_explainability_rows(metrics)

    write_csv(output_dir / "controlled_scenario_table.csv", controlled_rows)
    write_csv(output_dir / "balanced_ablation_table.csv", ablation_rows)
    write_csv(output_dir / "figure_data_explainability.csv", explainability_rows)
    write_json(output_dir / "expert_audit_scores.json", audit_scores)
    write_csv(output_dir / "expert_audit_dimension_scores.csv", audit_scores["dimensions"])
    write_csv(output_dir / "expert_audit_scenario_scores.csv", audit_scores["scenarios"])

    blinded = build_blinded_audit_files(audit_rows, output_dir)
    (output_dir / "paper_ready_tables.md").write_text(
        render_paper_tables_md(controlled_rows, ablation_rows, audit_scores),
        encoding="utf-8",
    )
    (output_dir / "paper_ready_tables.tex").write_text(
        render_paper_tables_tex(controlled_rows, ablation_rows),
        encoding="utf-8",
    )
    (output_dir / "explainability_path_quality.svg").write_text(
        render_svg_bar(explainability_rows),
        encoding="utf-8",
    )
    (output_dir / "expert_review_casebook.md").write_text(
        render_casebook(audit_rows),
        encoding="utf-8",
    )
    (output_dir / "expert_audit_scoring_report.md").write_text(
        render_audit_report(audit_scores, audit_path),
        encoding="utf-8",
    )

    summary = {
        "status": "traceability_paper_evidence_pack_built",
        "demo_dir": str(demo_dir),
        "audit_file": str(audit_path),
        "audit_status": audit_scores["status"],
        "outputs": {
            "paper_ready_tables_md": str(output_dir / "paper_ready_tables.md"),
            "paper_ready_tables_tex": str(output_dir / "paper_ready_tables.tex"),
            "controlled_scenario_table": str(output_dir / "controlled_scenario_table.csv"),
            "balanced_ablation_table": str(output_dir / "balanced_ablation_table.csv"),
            "figure_data_explainability": str(output_dir / "figure_data_explainability.csv"),
            "explainability_path_quality_svg": str(output_dir / "explainability_path_quality.svg"),
            "expert_audit_scores": str(output_dir / "expert_audit_scores.json"),
            "expert_audit_scoring_report": str(output_dir / "expert_audit_scoring_report.md"),
            "expert_review_casebook": str(output_dir / "expert_review_casebook.md"),
            **blinded,
        },
        "claim_boundary": "Paper tables are reproducible demo artifacts. Treat scored audit metrics as expert validation only when the audit file was filled by independent human experts.",
    }
    write_json(output_dir / "summary.json", summary)
    return summary


def render_audit_report(audit: dict[str, Any], audit_path: Path) -> str:
    lines = [
        "# Expert Audit Scoring Report",
        "",
        f"- Audit file: `{audit_path}`",
        f"- Status: `{audit['status']}`",
        f"- Audit rows: `{audit['audit_rows']}`",
        f"- Total scored cells: `{audit['total_scored_cells']}`",
        f"- Complete scored cases: `{audit['complete_case_count']}`",
        "",
        "## Dimension Scores",
        "",
        "| Dimension | Scored Cases | Mean Score | Strict Acceptance | Usable Acceptance | 95% CI |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in audit["dimensions"]:
        ci = ""
        if row["usable_acceptance_ci95_low"] is not None:
            ci = f"{fmt(row['usable_acceptance_ci95_low'])}-{fmt(row['usable_acceptance_ci95_high'])}"
        lines.append(
            f"| {row['dimension']} | {row['scored_cases']} | {fmt(row['mean_score'])} | {fmt(row['strict_acceptance_rate'])} | {fmt(row['usable_acceptance_rate'])} | {ci} |"
        )
    lines.extend(["", "## Scenario Coverage", ""])
    lines.extend(
        render_markdown_table(
            ["Scenario", "Audit Rows", "Rows With Any Score", "Mean Available Score"],
            [
                [row["scenario"], row["audit_rows"], row["rows_with_any_score"], fmt(row["mean_available_score"])]
                for row in audit["scenarios"]
            ],
        )
    )
    lines.extend(["", "## Inter-Reviewer Agreement", ""])
    lines.extend(
        render_markdown_table(
            ["Dimension", "Reviewer Pairs", "Pairwise Agreement"],
            [
                [row["dimension"], row["reviewer_pairs"], fmt(row["pairwise_agreement"])]
                for row in audit["inter_reviewer_agreement"]
            ],
        )
    )
    if audit["status"] == "audit_pending":
        lines.extend(
            [
                "",
                "## Current Interpretation",
                "",
                "No expert-score cells are filled yet. This report is therefore a review workflow artifact, not evidence of expert-validated traceability accuracy.",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "## Current Interpretation",
                "",
                "Expert-score cells are present. Use the dimension scores and complete-case acceptance rates as the human-evaluation evidence in the paper.",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build paper-ready traceability evidence artifacts.")
    parser.add_argument("--demo-dir", type=Path, default=DEFAULT_DEMO_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--audit-file", type=Path, default=None)
    args = parser.parse_args()
    summary = build_evidence_pack(demo_dir=args.demo_dir, output_dir=args.output_dir, audit_file=args.audit_file)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
