"""Run a paper-demo package for KG-enhanced anomaly traceability.

The existing Baosteel traceability labels are weak labels generated from
feature rules. This runner is designed for a paper-style demonstration package:
it reports the leakage-prone setting, leakage-controlled settings, KG path
quality, ablations, and an expert-audit template. It still does not replace a
real expert-reviewed benchmark.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.run_advanced_traceability_pilot_experiment import (
    DEFAULT_GRAPH,
    DEFAULT_TEST,
    DEFAULT_TRAIN,
    LABEL_ANCHORS,
    TRACE_RELATIONS,
    MechanismGraph,
    anchor_score,
    build_train_profiles,
    combine_scores,
    evaluate_rankings,
    feature_group,
    feature_key,
    iter_jsonl,
    kg_path_scores,
    label,
    label_set,
    ranked,
    score_feature_group_prior,
    score_feature_name_nb,
    score_label_prior,
    selected_features,
    token_set,
    write_csv,
    write_json,
    write_jsonl,
)


DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "paper_demo_traceability"

LABEL_TEXT_TERMS = [
    "process_fluctuation",
    "other_quality_abnormal",
    "mold_level_slag_risk",
    "transition_tundish",
    "temperature_flux",
    "speed_stopper_flow",
    "heat_transfer_imbalance",
    "过程参数异常类",
    "其他品质异常类",
    "液面/卷渣质量类",
    "温度/热流质量类",
    "拉速/塞棒/流量控制异常类",
    "交接/中间包质量类",
    "传热不均衡类",
    "质量异常",
]


def copy_record(record: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(record, ensure_ascii=False))


def mask_label_text(text: str) -> str:
    masked = text
    for term in LABEL_TEXT_TERMS:
        masked = masked.replace(term, "[MASK_LABEL]")
    masked = re.sub(r"主异常组为\s*[^，。]+", "主异常组为 [MASK_LABEL]", masked)
    masked = re.sub(r"多标签异常组为\s*[^，。]+", "多标签异常组为 [MASK_LABEL]", masked)
    return masked


def transform_record(record: dict[str, Any], scenario: str) -> dict[str, Any]:
    out = copy_record(record)
    out["text"] = mask_label_text(out.get("text") or "")
    features = out.get("source", {}).get("selected_features") or []
    if scenario == "balanced_group_only":
        for idx, feature in enumerate(features, start=1):
            feature["name"] = f"masked_feature_{idx}"
    elif scenario == "balanced_feature_anonymized":
        for idx, feature in enumerate(features, start=1):
            feature["name"] = f"masked_feature_{idx}"
            feature["group"] = "masked_group"
    return out


def stratified_sample(records: Sequence[dict[str, Any]], *, per_label: int = 200) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        y = label(record)
        if y == "unknown":
            continue
        grouped[y].append(record)
    sampled: list[dict[str, Any]] = []
    for y in sorted(grouped):
        sampled.extend(grouped[y][:per_label])
    return sampled


def path_quality(record: dict[str, Any], gold_label: str, traces: Sequence[dict[str, Any]]) -> float:
    if not traces:
        return 0.0
    feature_terms: set[str] = set()
    for feature in selected_features(record):
        feature_terms.update(token_set(str(feature.get("name") or "")))
        feature_terms.update(token_set(str(feature.get("group") or "")))
    label_terms: set[str] = set()
    for anchor in LABEL_ANCHORS.get(gold_label, []):
        label_terms.update(token_set(anchor))
    best = 0.0
    for trace in traces:
        edges = trace.get("edges") or []
        if not edges:
            continue
        node_text = " ".join(
            str(part or "")
            for edge in edges
            for part in [edge.get("head"), edge.get("tail")]
        )
        trace_terms = token_set(node_text)
        evidence_ok = all(edge.get("evidence") for edge in edges)
        relation_ok = all(edge.get("relation") in TRACE_RELATIONS for edge in edges)
        feature_overlap = bool(feature_terms & trace_terms)
        label_overlap = bool(label_terms & trace_terms)
        causal_ok = any(edge.get("relation") in {"cause", "affect", "increase_risk_of"} for edge in edges)
        score = sum([evidence_ok, relation_ok, feature_overlap, label_overlap, causal_ok]) / 5
        best = max(best, score)
    return best


def evaluate_scenario(
    scenario: str,
    train_records: Sequence[dict[str, Any]],
    eval_records: Sequence[dict[str, Any]],
    graph: MechanismGraph,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    transformed_train = [transform_record(record, scenario) for record in train_records]
    transformed_eval = [transform_record(record, scenario) for record in eval_records]
    profiles = build_train_profiles(transformed_train)
    labels = profiles["labels"]
    method_rankings: dict[str, list[list[str]]] = defaultdict(list)
    method_traces: dict[str, list[list[dict[str, Any]]]] = defaultdict(list)
    case_rows: list[dict[str, Any]] = []

    for original, record in zip(eval_records, transformed_eval):
        prior = score_label_prior(record, profiles)
        group = score_feature_group_prior(record, profiles)
        nb = score_feature_name_nb(record, profiles)
        anchors = anchor_score(record, labels)
        kg_scores, traces_by_label = kg_path_scores(record, labels, graph)
        proposed = combine_scores((0.45, nb), (0.20, group), (0.20, anchors), (0.15, kg_scores))
        explainable = combine_scores((0.32, nb), (0.12, group), (0.18, anchors), (0.38, kg_scores))
        methods = {
            "label_prior_majority": prior,
            "feature_group_prior": group,
            "feature_name_naive_bayes": nb,
            "kg_anchor_reasoning": anchors,
            "kg_path_reasoning": kg_scores,
            "proposed_score_fusion": proposed,
            "proposed_explainable_rerank": explainable,
        }
        case_prediction: dict[str, Any] = {
            "scenario": scenario,
            "record_id": original["record_id"],
            "gold_primary_label": label(original),
            "gold_label_set": sorted(label_set(original)),
            "features": selected_features(original),
            "method_predictions": {},
        }
        for method, scores in methods.items():
            ranks = ranked(scores)
            trace_rows: list[dict[str, Any]] = []
            if method == "kg_path_reasoning" and ranks:
                trace_rows = traces_by_label.get(ranks[0], [])
            elif method in {"proposed_score_fusion", "proposed_explainable_rerank"}:
                for candidate_label in ranks[:3]:
                    trace_rows = traces_by_label.get(candidate_label, [])
                    if trace_rows:
                        break
            method_rankings[method].append(ranks)
            method_traces[method].append(trace_rows)
            if method in {"kg_path_reasoning", "proposed_score_fusion", "proposed_explainable_rerank"}:
                case_prediction["method_predictions"][method] = {
                    "top3": ranks[:3],
                    "trace_paths": trace_rows[:2],
                    "path_quality": round(path_quality(original, label(original), trace_rows), 4),
                }
        case_rows.append(case_prediction)

    metric_rows: list[dict[str, Any]] = []
    for method in [
        "label_prior_majority",
        "feature_group_prior",
        "feature_name_naive_bayes",
        "kg_anchor_reasoning",
        "kg_path_reasoning",
        "proposed_score_fusion",
        "proposed_explainable_rerank",
    ]:
        result = asdict(evaluate_rankings(method, transformed_eval, method_rankings[method], method_traces[method], labels))
        qualities = [
            path_quality(original, label(original), traces)
            for original, traces in zip(eval_records, method_traces[method])
        ]
        result.update(
            {
                "scenario": scenario,
                "avg_path_quality": round(sum(qualities) / len(qualities), 4) if qualities else 0.0,
                "faithful_path_rate": round(sum(1 for score in qualities if score >= 0.8) / len(qualities), 4) if qualities else 0.0,
            }
        )
        metric_rows.append(result)
    return metric_rows, case_rows


def audit_rows(case_rows: Sequence[dict[str, Any]], *, max_rows: int = 80) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in case_rows:
        pred = case.get("method_predictions", {}).get("proposed_explainable_rerank") or {}
        traces = pred.get("trace_paths") or []
        first_path = traces[0] if traces else {"edges": []}
        path_text = " -> ".join(
            f"{edge.get('head')} [{edge.get('relation')}] {edge.get('tail')}"
            for edge in first_path.get("edges", [])
        )
        rows.append(
            {
                "scenario": case["scenario"],
                "record_id": case["record_id"],
                "gold_primary_label": case["gold_primary_label"],
                "predicted_top3": ";".join(pred.get("top3") or []),
                "top_features": ";".join(str(feature.get("name")) for feature in case.get("features", [])[:5]),
                "trace_path": path_text,
                "path_quality_proxy": pred.get("path_quality", 0.0),
                "expert_root_cause_correct": "",
                "expert_path_plausible": "",
                "expert_action_useful": "",
                "expert_notes": "",
            }
        )
        if len(rows) >= max_rows:
            break
    return rows


def run_demo(
    train_path: Path = DEFAULT_TRAIN,
    test_path: Path = DEFAULT_TEST,
    graph_path: Path = DEFAULT_GRAPH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    *,
    per_label: int = 200,
) -> dict[str, Any]:
    train_records = list(iter_jsonl(train_path))
    test_records = list(iter_jsonl(test_path))
    graph = MechanismGraph.load(graph_path)
    balanced = stratified_sample(test_records, per_label=per_label)
    scenarios = {
        "full_weak_label_masked_text": test_records,
        "balanced_label_masked_text": balanced,
        "balanced_group_only": balanced,
        "balanced_feature_anonymized": balanced,
    }
    all_metrics: list[dict[str, Any]] = []
    all_cases: list[dict[str, Any]] = []
    for scenario, rows in scenarios.items():
        metrics, cases = evaluate_scenario(scenario, train_records, rows, graph)
        all_metrics.extend(metrics)
        all_cases.extend(cases[:30])

    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "metrics.json", all_metrics)
    write_csv(output_dir / "metrics.csv", all_metrics)
    write_jsonl(output_dir / "case_studies.jsonl", all_cases)
    audit = audit_rows(all_cases)
    write_csv(output_dir / "expert_audit_template.csv", audit)
    report = render_report(all_metrics, all_cases[:12], len(train_records), len(test_records), len(balanced), graph_path)
    (output_dir / "paper_demo_report.md").write_text(report, encoding="utf-8")
    summary = {
        "status": "paper_demo_traceability_completed",
        "train_records": len(train_records),
        "test_records": len(test_records),
        "balanced_records": len(balanced),
        "per_label_cap": per_label,
        "graph_path": str(graph_path),
        "outputs": {
            "metrics": str(output_dir / "metrics.json"),
            "metrics_csv": str(output_dir / "metrics.csv"),
            "case_studies": str(output_dir / "case_studies.jsonl"),
            "audit_template": str(output_dir / "expert_audit_template.csv"),
            "report": str(output_dir / "paper_demo_report.md"),
        },
        "claim_boundary": "This is a paper-style demonstration package with leakage controls and audit templates. Final paper claims still require expert-reviewed root-cause/path labels.",
    }
    write_json(output_dir / "summary.json", summary)
    return summary


def render_report(
    metrics: Sequence[dict[str, Any]],
    cases: Sequence[dict[str, Any]],
    train_count: int,
    test_count: int,
    balanced_count: int,
    graph_path: Path,
) -> str:
    lines = [
        "# Paper-Demo KG-Enhanced Anomaly Traceability Experiment",
        "",
        "## Scope",
        "",
        "This package upgrades the weak-label pilot into a paper-style demonstration by adding leakage-controlled scenarios, balanced subsets, path-quality proxies, ablations, and an expert-audit template.",
        "",
        "It is still not a final publication benchmark until experts review root causes, trace paths, and recommended actions.",
        "",
        "## Inputs",
        "",
        f"- Train records: {train_count}",
        f"- Full test records: {test_count}",
        f"- Balanced demonstration records: {balanced_count}",
        f"- Mechanism KG: `{graph_path}`",
        "",
        "## Scenario Definitions",
        "",
        "- `full_weak_label_masked_text`: full test set; label text masked from record text, feature names/groups retained.",
        "- `balanced_label_masked_text`: balanced subset; label text masked, feature names/groups retained.",
        "- `balanced_group_only`: balanced subset; feature names masked, feature groups retained.",
        "- `balanced_feature_anonymized`: balanced subset; both feature names and groups masked.",
        "",
        "## Metrics",
        "",
        "| Scenario | Method | Hit@1 | Hit@3 | MRR | Macro F1 | Coverage | Path Quality | Faithful Path Rate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in metrics:
        lines.append(
            f"| {row['scenario']} | `{row['method']}` | {row['primary_hit1']} | {row['primary_hit3']} | {row['mrr']} | {row['macro_f1']} | {row['explanation_coverage']} | {row['avg_path_quality']} | {row['faithful_path_rate']} |"
        )
    lines.extend(["", "## Case Study Samples", ""])
    for case in cases:
        pred = case.get("method_predictions", {}).get("proposed_explainable_rerank") or {}
        lines.append(f"### {case['scenario']} / {case['record_id']}")
        lines.append("")
        lines.append(f"- Gold label: `{case['gold_primary_label']}`")
        lines.append(f"- Proposed top3: `{', '.join(pred.get('top3') or [])}`")
        lines.append(f"- Path quality proxy: `{pred.get('path_quality', 0.0)}`")
        traces = pred.get("trace_paths") or []
        if traces:
            path_text = " -> ".join(
                f"{edge.get('head')} [{edge.get('relation')}] {edge.get('tail')}"
                for edge in traces[0].get("edges", [])
            )
            lines.append(f"- Trace path: {path_text}")
        else:
            lines.append("- Trace path: none")
        lines.append("")
    lines.extend(
        [
            "## How To Use In A Paper Demo",
            "",
            "1. Use the full weak-label scenario only to show the current downstream data is not a gold benchmark.",
            "2. Use balanced and masked scenarios to demonstrate leakage awareness and robustness checks.",
            "3. Use path quality, faithful path rate, and expert audit results as the main traceability evidence.",
            "4. Do not claim production root-cause accuracy until `expert_audit_template.csv` is reviewed.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run paper-demo anomaly traceability experiment.")
    parser.add_argument("--train", type=Path, default=DEFAULT_TRAIN)
    parser.add_argument("--test", type=Path, default=DEFAULT_TEST)
    parser.add_argument("--graph", type=Path, default=DEFAULT_GRAPH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--per-label", type=int, default=200)
    args = parser.parse_args()
    summary = run_demo(
        train_path=args.train,
        test_path=args.test,
        graph_path=args.graph,
        output_dir=args.output_dir,
        per_label=args.per_label,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
