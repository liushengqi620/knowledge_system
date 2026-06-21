"""Run a pilot KG-enhanced anomaly traceability experiment.

This is an engineering pilot for the advanced experiment matrix. It uses the
existing weak-labeled Baosteel instance pool as downstream validation data and
the extracted mechanism KG as an explanation layer. The metrics are weak-label
pilot evidence, not paper-scale expert-reviewed claims.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter, defaultdict, deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRAIN = PROJECT_ROOT / "data" / "baosteel_knowledge_extraction" / "splits" / "train.jsonl"
DEFAULT_TEST = PROJECT_ROOT / "data" / "baosteel_knowledge_extraction" / "splits" / "test.jsonl"
DEFAULT_GRAPH = PROJECT_ROOT / "data" / "quality_traceability_large_kg" / "quality_traceability_large_kg_seed.json"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "advanced_traceability_pilot"


LABEL_ANCHORS: dict[str, list[str]] = {
    "mold_level_slag_risk": [
        "mold level",
        "meniscus",
        "liquid level",
        "slag",
        "flux",
        "mold",
        "sticker",
        "breakout",
        "oscillation",
        "液面",
        "卷渣",
        "结晶器",
    ],
    "temperature_flux": [
        "temperature",
        "temp",
        "thermal",
        "heat",
        "flux",
        "superheat",
        "liquidus",
        "cooling",
        "温度",
        "传热",
        "热",
    ],
    "heat_transfer_imbalance": [
        "heat exchange",
        "heat flux",
        "thermal stress",
        "ew diff",
        "ns diff",
        "air gap",
        "shell",
        "传热",
        "热流",
        "凝固壳",
    ],
    "speed_stopper_flow": [
        "cast speed",
        "speed",
        "stopper",
        "flow",
        "SEN",
        "jet",
        "nozzle",
        "argon",
        "拉速",
        "塞棒",
        "流量",
    ],
    "transition_tundish": [
        "tundish",
        "td",
        "weight",
        "ladle",
        "transition",
        "reoxidation",
        "inclusion",
        "中间包",
        "钢包",
        "夹杂",
    ],
    "process_fluctuation": [
        "range",
        "fluctuation",
        "process",
        "variation",
        "cast speed",
        "mold level",
        "heat exchange",
        "波动",
        "过程",
        "异常",
    ],
    "other_quality_abnormal": [
        "quality",
        "defect",
        "other",
        "abnormal",
        "risk",
        "质量",
        "异常",
        "缺陷",
    ],
}


FEATURE_ALIASES: dict[str, list[str]] = {
    "cast_speed": ["cast speed", "pulling speed", "speed", "拉速"],
    "mold_level": ["mold level", "meniscus", "liquid level", "mold", "液面", "结晶器"],
    "heat_exchange": ["heat exchange", "heat flux", "heat transfer", "thermal", "传热"],
    "td_": ["tundish", "tundish weight", "superheat", "中间包"],
    "liquidus_temp": ["liquidus temperature", "temperature", "temp"],
    "stopper": ["stopper", "flow", "塞棒"],
    "argon": ["argon", "bubble", "flow"],
    "sen": ["SEN", "nozzle", "jet"],
}


TRACE_RELATIONS = {"cause", "affect", "increase_risk_of", "indicates", "suppress", "improve"}


@dataclass(frozen=True)
class MethodResult:
    method: str
    evaluated_records: int
    primary_hit1: float
    primary_hit3: float
    any_label_hit3: float
    mrr: float
    macro_f1: float
    explanation_coverage: float
    avg_trace_paths: float
    weak_label_caveat: str = "weak-label downstream pilot; expert-reviewed case labels required for paper claims"


def iter_jsonl(path: Path, *, limit: int | None = None) -> Iterable[dict[str, Any]]:
    with path.open(encoding="utf-8") as fh:
        for idx, line in enumerate(fh):
            if limit is not None and idx >= limit:
                break
            if line.strip():
                yield json.loads(line)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def normalize_text(text: str) -> str:
    return re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]+", " ", text.lower()).strip()


def token_set(text: str) -> set[str]:
    tokens = {tok for tok in normalize_text(text).split() if len(tok) > 1}
    compact = normalize_text(text).replace(" ", "")
    if compact:
        tokens.add(compact)
    return tokens


def label(record: dict[str, Any]) -> str:
    return record.get("source", {}).get("quality_abnormal_group") or "unknown"


def label_set(record: dict[str, Any]) -> set[str]:
    raw = record.get("source", {}).get("quality_abnormal_groups") or label(record)
    return {item for item in str(raw).split(";") if item}


def selected_features(record: dict[str, Any]) -> list[dict[str, Any]]:
    return list(record.get("source", {}).get("selected_features") or [])


def feature_key(feature: dict[str, Any]) -> str:
    return normalize_text(str(feature.get("name") or ""))


def feature_group(feature: dict[str, Any]) -> str:
    return normalize_text(str(feature.get("group") or "unknown"))


def expanded_feature_terms(feature: dict[str, Any]) -> set[str]:
    name = str(feature.get("name") or "")
    terms = token_set(name)
    for key, aliases in FEATURE_ALIASES.items():
        if key.lower() in name.lower():
            for alias in aliases:
                terms.update(token_set(alias))
    terms.add(feature_group(feature))
    return terms


def build_train_profiles(records: Sequence[dict[str, Any]]) -> dict[str, Any]:
    label_counts: Counter[str] = Counter()
    feature_counts: dict[str, Counter[str]] = defaultdict(Counter)
    group_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for record in records:
        y = label(record)
        label_counts[y] += 1
        for feature in selected_features(record):
            feature_counts[feature_key(feature)][y] += 1
            group_counts[feature_group(feature)][y] += 1
    return {
        "label_counts": label_counts,
        "feature_counts": feature_counts,
        "group_counts": group_counts,
        "labels": sorted(label_counts),
    }


def log_prior_scores(profiles: dict[str, Any]) -> dict[str, float]:
    labels = profiles["labels"]
    label_counts: Counter[str] = profiles["label_counts"]
    total = sum(label_counts.values())
    return {y: math.log((label_counts[y] + 1) / (total + len(labels))) for y in labels}


def score_label_prior(record: dict[str, Any], profiles: dict[str, Any]) -> dict[str, float]:
    return log_prior_scores(profiles)


def score_feature_group_prior(record: dict[str, Any], profiles: dict[str, Any]) -> dict[str, float]:
    scores = log_prior_scores(profiles)
    label_counts: Counter[str] = profiles["label_counts"]
    labels = profiles["labels"]
    for feature in selected_features(record):
        counts = profiles["group_counts"].get(feature_group(feature), Counter())
        for y in labels:
            scores[y] += math.log((counts[y] + 1) / (label_counts[y] + len(labels)))
    return scores


def score_feature_name_nb(record: dict[str, Any], profiles: dict[str, Any]) -> dict[str, float]:
    scores = log_prior_scores(profiles)
    label_counts: Counter[str] = profiles["label_counts"]
    labels = profiles["labels"]
    vocab = max(1, len(profiles["feature_counts"]))
    for feature in selected_features(record):
        counts = profiles["feature_counts"].get(feature_key(feature), Counter())
        for y in labels:
            scores[y] += math.log((counts[y] + 1) / (label_counts[y] + vocab))
    return scores


def anchor_score(record: dict[str, Any], labels: Sequence[str]) -> dict[str, float]:
    feature_terms = set()
    for feature in selected_features(record):
        feature_terms.update(expanded_feature_terms(feature))
    text = normalize_text(record.get("text") or "")
    scores = {y: 0.0 for y in labels}
    for y in labels:
        for anchor in LABEL_ANCHORS.get(y, []):
            anchor_terms = token_set(anchor)
            overlap = len(feature_terms & anchor_terms)
            if overlap:
                scores[y] += overlap
            if normalize_text(anchor) and normalize_text(anchor) in text:
                scores[y] += 0.5
    return scores


class MechanismGraph:
    def __init__(self, graph: dict[str, Any]):
        self.nodes = {node["node_id"]: node for node in graph.get("nodes", [])}
        self.edges = [edge for edge in graph.get("edges", []) if edge.get("layer") != "schema"]
        self.adj: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for edge in self.edges:
            if edge.get("relation") in TRACE_RELATIONS:
                self.adj[edge["head"]].append(edge)
        self.node_tokens = {
            node_id: token_set(node.get("text", ""))
            for node_id, node in self.nodes.items()
            if node.get("type") not in {"SchemaClass", "InstanceType"}
        }
        self.inverted: dict[str, set[str]] = defaultdict(set)
        for node_id, tokens in self.node_tokens.items():
            for token in tokens:
                self.inverted[token].add(node_id)
        self._label_target_cache: dict[str, list[str]] = {}

    @classmethod
    def load(cls, path: Path) -> "MechanismGraph":
        return cls(json.loads(path.read_text(encoding="utf-8")))

    def match_feature_nodes(self, feature: dict[str, Any], *, max_nodes: int = 5) -> list[str]:
        terms = expanded_feature_terms(feature)
        candidate_counts: Counter[str] = Counter()
        for term in terms:
            candidate_counts.update(self.inverted.get(term, set()))
        scored: list[tuple[float, str]] = []
        for node_id, overlap in candidate_counts.items():
            node = self.nodes[node_id]
            bonus = 1.0 if node.get("type") in {"ProcessParameter", "EquipmentState", "MaterialState"} else 0.0
            scored.append((overlap + bonus, node_id))
        scored.sort(reverse=True)
        return [node_id for _, node_id in scored[:max_nodes]]

    def label_target_nodes(self, label_name: str, *, max_nodes: int = 25) -> list[str]:
        if label_name in self._label_target_cache:
            return self._label_target_cache[label_name]
        anchors = LABEL_ANCHORS.get(label_name, [])
        scored: list[tuple[float, str]] = []
        for node_id, node_terms in self.node_tokens.items():
            node = self.nodes[node_id]
            score = 0.0
            for anchor in anchors:
                score += len(token_set(anchor) & node_terms)
                if normalize_text(anchor) and normalize_text(anchor) in normalize_text(node.get("text", "")):
                    score += 1.0
            if node.get("type") == "QualityDefect":
                score += 0.5
            if score > 0:
                scored.append((score, node_id))
        scored.sort(reverse=True)
        self._label_target_cache[label_name] = [node_id for _, node_id in scored[:max_nodes]]
        return self._label_target_cache[label_name]

    def shortest_trace(self, starts: Sequence[str], targets: Sequence[str], *, max_depth: int = 3) -> list[dict[str, Any]]:
        target_set = set(targets)
        traces: list[dict[str, Any]] = []
        for start in starts[:4]:
            queue = deque([(start, [])])
            seen = {start}
            while queue:
                node_id, path = queue.popleft()
                if node_id in target_set and path:
                    traces.append(self._format_path(path))
                    break
                if len(path) >= max_depth:
                    continue
                for edge in self.adj.get(node_id, [])[:20]:
                    nxt = edge["tail"]
                    if nxt in seen:
                        continue
                    seen.add(nxt)
                    queue.append((nxt, [*path, edge]))
        return traces[:3]

    def _format_path(self, path: Sequence[dict[str, Any]]) -> dict[str, Any]:
        edges: list[dict[str, Any]] = []
        for edge in path:
            head = self.nodes.get(edge["head"], {})
            tail = self.nodes.get(edge["tail"], {})
            edges.append(
                {
                    "head": head.get("text"),
                    "head_type": head.get("type"),
                    "relation": edge.get("relation"),
                    "tail": tail.get("text"),
                    "tail_type": tail.get("type"),
                    "evidence": (edge.get("evidence") or [{}])[0].get("text"),
                }
            )
        return {"length": len(edges), "edges": edges}


def kg_path_scores(record: dict[str, Any], labels: Sequence[str], graph: MechanismGraph) -> tuple[dict[str, float], dict[str, list[dict[str, Any]]]]:
    starts: list[str] = []
    for feature in selected_features(record):
        starts.extend(graph.match_feature_nodes(feature, max_nodes=3))
    starts = list(dict.fromkeys(starts))[:12]
    scores = {y: 0.0 for y in labels}
    traces_by_label: dict[str, list[dict[str, Any]]] = {}
    for y in labels:
        targets = graph.label_target_nodes(y)
        traces = graph.shortest_trace(starts, targets)
        traces_by_label[y] = traces
        scores[y] += 2.0 * len(traces)
        if traces:
            scores[y] += max(0.0, 3.0 - min(trace["length"] for trace in traces))
    anchors = anchor_score(record, labels)
    for y in labels:
        scores[y] += 0.3 * anchors[y]
    return scores, traces_by_label


def combine_scores(*weighted_scores: tuple[float, dict[str, float]]) -> dict[str, float]:
    labels = set()
    for _, scores in weighted_scores:
        labels.update(scores)
    out = {y: 0.0 for y in labels}
    for weight, scores in weighted_scores:
        for y, score in scores.items():
            out[y] += weight * score
    return out


def ranked(scores: dict[str, float]) -> list[str]:
    return [label_name for label_name, _ in sorted(scores.items(), key=lambda item: (-item[1], item[0]))]


def macro_f1(preds: Sequence[str], golds: Sequence[str], labels: Sequence[str]) -> float:
    values: list[float] = []
    for y in labels:
        tp = sum(1 for pred, gold in zip(preds, golds) if pred == y and gold == y)
        fp = sum(1 for pred, gold in zip(preds, golds) if pred == y and gold != y)
        fn = sum(1 for pred, gold in zip(preds, golds) if pred != y and gold == y)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        values.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
    return sum(values) / len(values) if values else 0.0


def evaluate_rankings(
    method: str,
    records: Sequence[dict[str, Any]],
    rankings: Sequence[list[str]],
    traces: Sequence[list[dict[str, Any]]],
    labels: Sequence[str],
) -> MethodResult:
    hit1 = hit3 = any_hit3 = reciprocal = 0.0
    preds: list[str] = []
    golds: list[str] = []
    trace_count = 0
    trace_covered = 0
    for record, ranking, trace_rows in zip(records, rankings, traces):
        gold = label(record)
        golds.append(gold)
        preds.append(ranking[0] if ranking else "")
        if ranking and ranking[0] == gold:
            hit1 += 1
        if gold in ranking[:3]:
            hit3 += 1
        if label_set(record) & set(ranking[:3]):
            any_hit3 += 1
        if gold in ranking:
            reciprocal += 1 / (ranking.index(gold) + 1)
        trace_count += len(trace_rows)
        if trace_rows:
            trace_covered += 1
    n = max(1, len(records))
    return MethodResult(
        method=method,
        evaluated_records=len(records),
        primary_hit1=round(hit1 / n, 4),
        primary_hit3=round(hit3 / n, 4),
        any_label_hit3=round(any_hit3 / n, 4),
        mrr=round(reciprocal / n, 4),
        macro_f1=round(macro_f1(preds, golds, labels), 4),
        explanation_coverage=round(trace_covered / n, 4),
        avg_trace_paths=round(trace_count / n, 4),
    )


def run_pilot(
    train_path: Path = DEFAULT_TRAIN,
    test_path: Path = DEFAULT_TEST,
    graph_path: Path = DEFAULT_GRAPH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    *,
    max_train: int | None = None,
    max_test: int | None = None,
) -> dict[str, Any]:
    train_records = list(iter_jsonl(train_path, limit=max_train))
    test_records = list(iter_jsonl(test_path, limit=max_test))
    profiles = build_train_profiles(train_records)
    labels = profiles["labels"]
    graph = MechanismGraph.load(graph_path)

    method_rankings: dict[str, list[list[str]]] = defaultdict(list)
    method_traces: dict[str, list[list[dict[str, Any]]]] = defaultdict(list)
    prediction_rows: list[dict[str, Any]] = []

    for record in test_records:
        prior = score_label_prior(record, profiles)
        group = score_feature_group_prior(record, profiles)
        nb = score_feature_name_nb(record, profiles)
        anchors = anchor_score(record, labels)
        kg_scores, traces_by_label = kg_path_scores(record, labels, graph)
        proposed = combine_scores(
            (0.45, nb),
            (0.20, group),
            (0.20, anchors),
            (0.15, kg_scores),
        )
        methods = {
            "label_prior_majority": prior,
            "feature_group_prior": group,
            "feature_name_naive_bayes": nb,
            "kg_anchor_reasoning": anchors,
            "kg_path_reasoning": kg_scores,
            "proposed_plm_llm_kg_fusion": proposed,
        }
        for method, scores in methods.items():
            ranks = ranked(scores)
            trace_rows: list[dict[str, Any]] = []
            if method == "kg_path_reasoning" and ranks:
                trace_rows = traces_by_label.get(ranks[0], [])
            elif method == "proposed_plm_llm_kg_fusion":
                for candidate_label in ranks[:3]:
                    trace_rows = traces_by_label.get(candidate_label, [])
                    if trace_rows:
                        break
            method_rankings[method].append(ranks)
            method_traces[method].append(trace_rows)
        best_ranking = method_rankings["proposed_plm_llm_kg_fusion"][-1]
        prediction_rows.append(
            {
                "record_id": record["record_id"],
                "gold_primary_label": label(record),
                "gold_label_set": sorted(label_set(record)),
                "selected_features": selected_features(record),
                "predicted_top3": best_ranking[:3],
                "top_trace_paths": method_traces["proposed_plm_llm_kg_fusion"][-1],
            }
        )

    metrics = [
        asdict(evaluate_rankings(method, test_records, method_rankings[method], method_traces[method], labels))
        for method in [
            "label_prior_majority",
            "feature_group_prior",
            "feature_name_naive_bayes",
            "kg_anchor_reasoning",
            "kg_path_reasoning",
            "proposed_plm_llm_kg_fusion",
        ]
    ]
    best = max(metrics, key=lambda row: (row["primary_hit1"], row["mrr"], row["macro_f1"]))
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "metrics.json", metrics)
    write_csv(output_dir / "metrics.csv", metrics)
    write_jsonl(output_dir / "predictions.jsonl", prediction_rows)
    write_json(
        output_dir / "label_profiles.json",
        {
            "label_counts": dict(profiles["label_counts"]),
            "labels": labels,
            "feature_profile_count": len(profiles["feature_counts"]),
            "group_profile_count": len(profiles["group_counts"]),
        },
    )
    report = render_report(metrics, prediction_rows[:8], train_records, test_records, graph_path)
    (output_dir / "report.md").write_text(report, encoding="utf-8")
    summary = {
        "status": "advanced_traceability_pilot_completed",
        "train_records": len(train_records),
        "test_records": len(test_records),
        "graph_path": str(graph_path),
        "best_method": best,
        "leakage_warning": "feature_group_prior or feature_name_naive_bayes can be near-perfect because current labels are weakly generated from selected process features; use reviewed cases for paper claims.",
        "outputs": {
            "metrics": str(output_dir / "metrics.json"),
            "metrics_csv": str(output_dir / "metrics.csv"),
            "predictions": str(output_dir / "predictions.jsonl"),
            "label_profiles": str(output_dir / "label_profiles.json"),
            "report": str(output_dir / "report.md"),
        },
        "caveat": "Weak-label pilot experiment. Use expert-reviewed traceability labels before making paper-scale claims.",
    }
    write_json(output_dir / "summary.json", summary)
    return summary


def render_report(
    metrics: Sequence[dict[str, Any]],
    examples: Sequence[dict[str, Any]],
    train_records: Sequence[dict[str, Any]],
    test_records: Sequence[dict[str, Any]],
    graph_path: Path,
) -> str:
    lines = [
        "# Advanced Traceability Pilot Experiment",
        "",
        "## Scope",
        "",
        "This pilot evaluates downstream anomaly traceability on weak-labeled Baosteel records after mechanism KG extraction. It is engineering evidence, not paper-scale expert-reviewed evidence.",
        "",
        "## Inputs",
        "",
        f"- Train records: {len(train_records)}",
        f"- Test records: {len(test_records)}",
        f"- Mechanism/traceability KG: `{graph_path}`",
        "",
        "## Metrics",
        "",
        "| Method | Hit@1 | Hit@3 | Any-label Hit@3 | MRR | Macro F1 | Explanation Coverage | Avg Trace Paths |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in metrics:
        lines.append(
            f"| `{row['method']}` | {row['primary_hit1']} | {row['primary_hit3']} | {row['any_label_hit3']} | {row['mrr']} | {row['macro_f1']} | {row['explanation_coverage']} | {row['avg_trace_paths']} |"
        )
    lines.extend(["", "## Proposed Examples", ""])
    for row in examples:
        lines.append(f"### {row['record_id']}")
        lines.append("")
        lines.append(f"- Gold primary label: `{row['gold_primary_label']}`")
        lines.append(f"- Predicted top3: `{', '.join(row['predicted_top3'])}`")
        features = ", ".join(str(feature.get("name")) for feature in row["selected_features"][:5])
        lines.append(f"- Top features: {features}")
        if row["top_trace_paths"]:
            first_path = row["top_trace_paths"][0]
            path_text = " -> ".join(
                f"{edge['head']} [{edge['relation']}] {edge['tail']}" for edge in first_path["edges"]
            )
            lines.append(f"- Example KG path: {path_text}")
        else:
            lines.append("- Example KG path: none")
        lines.append("")
    lines.extend(
        [
            "## Interpretation",
            "",
            "- `feature_name_naive_bayes` is the strongest non-LLM lexical baseline because the weak labels are built from feature names and groups.",
            "- If feature-only baselines approach 1.0, treat this as weak-label leakage evidence rather than true expert-level traceability performance.",
            "- `kg_path_reasoning` measures whether the mechanism graph can provide evidence-backed trace paths, not only label prediction.",
            "- `proposed_plm_llm_kg_fusion` combines feature-level evidence, KG anchors, and trace paths as a pilot proxy for the planned PLM-LLM-KG system.",
            "- Expert-reviewed cases are still required for publication-level trace path and action recommendation claims.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run advanced KG-enhanced traceability pilot experiment.")
    parser.add_argument("--train", type=Path, default=DEFAULT_TRAIN)
    parser.add_argument("--test", type=Path, default=DEFAULT_TEST)
    parser.add_argument("--graph", type=Path, default=DEFAULT_GRAPH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--max-train", type=int, default=None)
    parser.add_argument("--max-test", type=int, default=None)
    args = parser.parse_args()
    summary = run_pilot(
        train_path=args.train,
        test_path=args.test,
        graph_path=args.graph,
        output_dir=args.output_dir,
        max_train=args.max_train,
        max_test=args.max_test,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
