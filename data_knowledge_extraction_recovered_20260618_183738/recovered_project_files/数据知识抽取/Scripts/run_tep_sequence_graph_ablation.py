from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from tep_sequence_heads import DEFAULT_TEP_DATASET_DIR, run_sequence_head_experiment


METRICS = [
    ("sample_multiclass_metrics", "target_defect_macro_f1"),
    ("sample_multiclass_metrics", "macro_f1"),
    ("event_warning_metrics", "event_macro_recall"),
    ("path_explanation_metrics", "path_hit_rate"),
]


def _fs_path(path: Path | str) -> Path:
    p = Path(path)
    if os.name != "nt":
        return p
    raw = str(p if p.is_absolute() else p.resolve())
    if raw.startswith("\\\\?\\"):
        return Path(raw)
    return Path("\\\\?\\" + raw)


def build_variant_configs(
    *,
    graph_strength: float,
    reliability_threshold: float,
    max_edges: int | None,
    include_residual_gated: bool = False,
    selected_variants: list[str] | tuple[str, ...] | None = None,
) -> list[dict[str, Any]]:
    strength = max(0.0, float(graph_strength))
    threshold = max(0.0, min(1.0, float(reliability_threshold)))
    edge_cap = int(max_edges) if max_edges is not None and int(max_edges) > 0 else None
    variants = [
        {
            "name": "no_graph",
            "graph_strength": 0.0,
            "use_lagged_graph": False,
            "graph_reliability_threshold": 0.0,
            "graph_max_edges": None,
            "lagged_graph_fusion_mode": "direct_filter",
        },
        {
            "name": "all_lagged",
            "graph_strength": strength,
            "use_lagged_graph": True,
            "graph_reliability_threshold": 0.0,
            "graph_max_edges": None,
            "lagged_graph_fusion_mode": "direct_filter",
        },
        {
            "name": "reliable_lagged",
            "graph_strength": strength,
            "use_lagged_graph": True,
            "graph_reliability_threshold": threshold,
            "graph_max_edges": edge_cap,
            "lagged_graph_fusion_mode": "direct_filter",
        },
    ]
    if bool(include_residual_gated):
        variants.append(
            {
                "name": "residual_gated_lagged",
                "graph_strength": strength,
                "use_lagged_graph": True,
                "graph_reliability_threshold": threshold,
                "graph_max_edges": edge_cap,
                "lagged_graph_fusion_mode": "residual_channel",
            }
        )
    if selected_variants:
        selected = {str(name).strip() for name in selected_variants if str(name).strip()}
        known = {str(item["name"]) for item in variants}
        unknown = sorted(selected - known)
        if unknown:
            raise ValueError(f"Unknown variants requested: {', '.join(unknown)}")
        variants = [item for item in variants if str(item["name"]) in selected]
        if not variants:
            raise ValueError("At least one variant must be selected")
    return variants


def _metric(result: dict[str, Any], section: str, key: str) -> float | None:
    value = (result.get(section, {}) or {}).get(key)
    if value is None:
        return None
    return float(value)


def _mean_std(values: list[float]) -> tuple[float | None, float | None]:
    if not values:
        return None, None
    return float(mean(values)), float(pstdev(values))


def aggregate_records(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_variant: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        by_variant.setdefault(str(record["variant"]), []).append(record)

    summary: dict[str, dict[str, Any]] = {}
    for variant, rows in by_variant.items():
        out: dict[str, Any] = {"n_runs": int(len(rows))}
        for section, key in METRICS:
            vals = [
                value
                for value in (_metric(row.get("result", {}) or {}, section, key) for row in rows)
                if value is not None
            ]
            m, s = _mean_std(vals)
            out[f"{key}_mean"] = m
            out[f"{key}_std"] = s
        for key in ("candidate_edges", "matched_edges", "pruned_edges"):
            vals = []
            for row in rows:
                graph = (row.get("result", {}) or {}).get("graph_constraint", {}) or {}
                if graph.get(key) is not None:
                    vals.append(float(graph[key]))
            m, s = _mean_std(vals)
            out[f"{key}_mean"] = m
            out[f"{key}_std"] = s
        summary[variant] = out
    return summary


def _fmt(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.4f}"


def render_markdown(summary: dict[str, dict[str, Any]], records: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    lines.append("# TEP Sequence Graph Ablation Summary")
    lines.append("")
    lines.append("| Variant | Runs | Target-F1 | Macro-F1 | Event Macro-Recall | Path Hit | Candidate Edges | Matched Edges | Pruned Edges |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    ordered_variants = ["no_graph", "all_lagged", "reliable_lagged", "residual_gated_lagged"]
    ordered_variants += [name for name in summary if name not in set(ordered_variants)]
    for variant in ordered_variants:
        row = summary.get(variant)
        if not row:
            continue
        lines.append(
            "| {variant} | {n_runs} | {target} +/- {target_std} | {macro} +/- {macro_std} | {event} +/- {event_std} | {path} +/- {path_std} | {cand} | {matched} | {pruned} |".format(
                variant=variant,
                n_runs=int(row.get("n_runs", 0)),
                target=_fmt(row.get("target_defect_macro_f1_mean")),
                target_std=_fmt(row.get("target_defect_macro_f1_std")),
                macro=_fmt(row.get("macro_f1_mean")),
                macro_std=_fmt(row.get("macro_f1_std")),
                event=_fmt(row.get("event_macro_recall_mean")),
                event_std=_fmt(row.get("event_macro_recall_std")),
                path=_fmt(row.get("path_hit_rate_mean")),
                path_std=_fmt(row.get("path_hit_rate_std")),
                cand=_fmt(row.get("candidate_edges_mean")),
                matched=_fmt(row.get("matched_edges_mean")),
                pruned=_fmt(row.get("pruned_edges_mean")),
            )
        )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "This table compares the tree-free sequence head under matched settings: no graph, all lagged graph edges, "
        "and reliability-gated lagged graph edges. Low-budget smoke runs should be treated as pipeline evidence; "
        "competitive claims require longer training and multiple seeds."
    )
    lines.append("")
    lines.append("## Runs")
    lines.append("")
    for record in records:
        result = record.get("result", {}) or {}
        sample = result.get("sample_multiclass_metrics", {}) or {}
        graph = result.get("graph_constraint", {}) or {}
        lines.append(
            "- {variant}/seed={seed}: target-F1={target}, matched_edges={matched}, pruned_edges={pruned}".format(
                variant=record.get("variant"),
                seed=record.get("seed"),
                target=_fmt(sample.get("target_defect_macro_f1")),
                matched=graph.get("matched_edges", "n/a"),
                pruned=graph.get("pruned_edges", "n/a"),
            )
        )
    lines.append("")
    return "\n".join(lines)


def run_ablation_suite(
    *,
    dataset_dir: Path,
    output_path: Path,
    model_name: str,
    seeds: list[int],
    max_rows: int | None,
    window_size: int,
    hidden_dim: int,
    epochs: int,
    batch_size: int,
    normal_pretrain_epochs: int,
    normal_residual_features: bool,
    graph_strength: float,
    reliability_threshold: float,
    max_edges: int | None,
    graph_prior_name: str,
    apply_llm_rerank: bool,
    include_residual_gated: bool = False,
    selected_variants: list[str] | tuple[str, ...] | None = None,
    resume: bool = False,
    device: str = "auto",
) -> dict[str, Any]:
    variants = build_variant_configs(
        graph_strength=graph_strength,
        reliability_threshold=reliability_threshold,
        max_edges=max_edges,
        include_residual_gated=include_residual_gated,
        selected_variants=selected_variants,
    )
    records: list[dict[str, Any]] = []
    run_dir = output_path.with_suffix("")
    run_dir_io = _fs_path(run_dir)
    run_dir_io.mkdir(parents=True, exist_ok=True)
    for seed in seeds:
        for variant in variants:
            run_output = run_dir / f"{variant['name']}_seed{int(seed)}.json"
            run_output_io = _fs_path(run_output)
            if bool(resume) and run_output_io.exists():
                result = json.loads(run_output_io.read_text(encoding="utf-8"))
            else:
                result = run_sequence_head_experiment(
                    dataset_dir=dataset_dir,
                    output_path=run_output_io,
                    max_rows=max_rows,
                    model_name=model_name,
                    window_size=window_size,
                    hidden_dim=hidden_dim,
                    epochs=epochs,
                    batch_size=batch_size,
                    seed=int(seed),
                    device=device,
                    apply_llm_rerank=apply_llm_rerank,
                    normal_pretrain_epochs=normal_pretrain_epochs,
                    normal_residual_features=normal_residual_features,
                    graph_strength=float(variant["graph_strength"]),
                    graph_prior_name=graph_prior_name,
                    use_lagged_graph=bool(variant["use_lagged_graph"]),
                    graph_reliability_threshold=float(variant["graph_reliability_threshold"]),
                    graph_max_edges=variant["graph_max_edges"],
                    lagged_graph_fusion_mode=str(variant["lagged_graph_fusion_mode"]),
                )
            records.append({"variant": variant["name"], "seed": int(seed), "path": str(run_output), "result": result})
    summary = aggregate_records(records)
    payload = {
        "status": "ok",
        "model_name": str(model_name),
        "seeds": [int(s) for s in seeds],
        "include_residual_gated": bool(include_residual_gated),
        "device": str(device),
        "variants": variants,
        "summary": summary,
        "records": records,
    }
    output_io = _fs_path(output_path)
    output_io.parent.mkdir(parents=True, exist_ok=True)
    output_io.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    _fs_path(output_path.with_suffix(".md")).write_text(render_markdown(summary, records), encoding="utf-8")
    return payload


def _parse_seeds(raw: str) -> list[int]:
    seeds = [int(part.strip()) for part in str(raw).split(",") if part.strip()]
    if not seeds:
        raise ValueError("At least one seed is required")
    return seeds


def _parse_variants(raw: str | None) -> list[str] | None:
    if raw is None or not str(raw).strip():
        return None
    variants = [part.strip() for part in str(raw).split(",") if part.strip()]
    return variants or None


def main() -> None:
    parser = argparse.ArgumentParser(description="Run TEP sequence-head graph ablation variants.")
    parser.add_argument("--dataset-dir", type=str, default=str(DEFAULT_TEP_DATASET_DIR))
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--model", type=str, default="tcn", choices=["tcn", "gru", "ft_transformer", "patchtst", "anomaly_transformer", "graph_wavenet", "gdn", "mtad_gat"])
    parser.add_argument("--seeds", type=str, default="42")
    parser.add_argument("--max-rows", type=int, default=2000)
    parser.add_argument("--window-size", type=int, default=16)
    parser.add_argument("--hidden-dim", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--normal-pretrain-epochs", type=int, default=1)
    parser.add_argument("--normal-residual-features", action="store_true")
    parser.add_argument("--graph-strength", type=float, default=0.15)
    parser.add_argument("--reliability-threshold", type=float, default=0.70)
    parser.add_argument("--max-edges", type=int, default=40)
    parser.add_argument("--graph-prior", type=str, default="tep_expert_llm_graph_prior.json")
    parser.add_argument("--apply-llm-rerank", action="store_true")
    parser.add_argument("--include-residual-gated", action="store_true")
    parser.add_argument(
        "--variants",
        type=str,
        default="",
        help="Optional comma-separated subset, e.g. no_graph,residual_gated_lagged.",
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--device", type=str, default="auto")
    args = parser.parse_args()

    payload = run_ablation_suite(
        dataset_dir=Path(args.dataset_dir),
        output_path=Path(args.output),
        model_name=str(args.model),
        seeds=_parse_seeds(args.seeds),
        max_rows=int(args.max_rows) if int(args.max_rows) > 0 else None,
        window_size=int(args.window_size),
        hidden_dim=int(args.hidden_dim),
        epochs=int(args.epochs),
        batch_size=int(args.batch_size),
        normal_pretrain_epochs=int(args.normal_pretrain_epochs),
        normal_residual_features=bool(args.normal_residual_features),
        graph_strength=float(args.graph_strength),
        reliability_threshold=float(args.reliability_threshold),
        max_edges=int(args.max_edges) if int(args.max_edges) > 0 else None,
        graph_prior_name=str(args.graph_prior),
        apply_llm_rerank=bool(args.apply_llm_rerank),
        include_residual_gated=bool(args.include_residual_gated),
        selected_variants=_parse_variants(args.variants),
        resume=bool(args.resume),
        device=str(args.device),
    )
    print(render_markdown(payload["summary"], payload["records"]))


if __name__ == "__main__":
    main()
