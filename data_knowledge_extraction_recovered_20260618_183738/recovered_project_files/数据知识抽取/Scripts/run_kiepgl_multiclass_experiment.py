from __future__ import annotations

import argparse
import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

try:
    from config import CONFIG, prior_config
except Exception:
    from config import CONFIG

    class _PriorConfig:
        hard_rules: list[Any] = []

    prior_config = _PriorConfig()

try:
    from defect_graph_model import UnifiedDefectGraphModel
except Exception:
    UnifiedDefectGraphModel = None  # type: ignore[assignment]
from multiclass_event_evaluation import summarize_multiclass_event_evaluation
try:
    from prior_graph_builder import build_graph_prior_from_project, build_train_data_prior_edges
except Exception:
    build_graph_prior_from_project = None  # type: ignore[assignment]
    build_train_data_prior_edges = None  # type: ignore[assignment]
try:
    from proof_experiment_runner import summarize_runs
except Exception:
    summarize_runs = None  # type: ignore[assignment]
try:
    from temporal_encoder import encode_temporal_features_from_df
except Exception:
    encode_temporal_features_from_df = None  # type: ignore[assignment]


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASET_DIR = PROJECT_ROOT / "knowledge_exports" / "quality_traceability_dataset_v4_multiclass"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "knowledge_exports" / "kiepgl_multiclass_experiment.json"


@dataclass(frozen=True)
class MulticlassExperimentSpec:
    name: str
    category: str
    objective: str
    overrides: dict[str, Any]


def _json_sanitize(obj: Any) -> Any:
    if obj is None or isinstance(obj, (str, bool)):
        return obj
    if isinstance(obj, (int, float)):
        return obj
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, Mapping):
        return {str(k): _json_sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_sanitize(v) for v in obj]
    return str(obj)


def align_proba_to_class_ids(
    proba: np.ndarray,
    classes: Sequence[int] | np.ndarray,
    *,
    expected_class_ids: Sequence[int],
) -> np.ndarray:
    arr = np.asarray(proba, dtype=float)
    if arr.ndim != 2:
        raise ValueError("proba must be a 2-D array")
    cls = np.asarray(classes, dtype=int).reshape(-1)
    expected = [int(x) for x in expected_class_ids]
    if len(cls) != arr.shape[1]:
        raise ValueError("classes length must match proba columns")
    out = np.zeros((arr.shape[0], len(expected)), dtype=float)
    position = {class_id: i for i, class_id in enumerate(expected)}
    for src_col, class_id in enumerate(cls):
        dst_col = position.get(int(class_id))
        if dst_col is not None:
            out[:, dst_col] = arr[:, src_col]
    row_sum = out.sum(axis=1, keepdims=True)
    np.divide(out, np.where(row_sum > 0, row_sum, 1.0), out=out)
    return out


def time_ordered_split_indices(
    n_rows: int,
    *,
    test_size: float = 0.2,
    val_size: float = 0.2,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    n = int(n_rows)
    if n < 10:
        raise ValueError("at least 10 rows are required")
    test_n = max(1, int(round(n * float(test_size))))
    val_n = max(1, int(round(n * float(val_size))))
    train_n = n - val_n - test_n
    if train_n <= 0:
        raise ValueError("split sizes leave no training rows")
    idx = np.arange(n, dtype=np.int64)
    return idx[:train_n], idx[train_n : train_n + val_n], idx[train_n + val_n :]


def split_indices_from_metadata(
    y_meta: pd.DataFrame,
    *,
    test_size: float = 0.2,
    val_fraction: float = 0.2,
    split_mode: str = "metadata",
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    n = int(len(y_meta))
    idx = np.arange(n, dtype=np.int64)
    if "split_role" in y_meta.columns and str(split_mode) in {"metadata", "stratified_time_ordered"}:
        roles = y_meta["split_role"].astype(str).str.lower().to_numpy()
        test_idx = idx[roles == "test"]
        train_pool = idx[roles != "test"]
        val_n = max(1, int(round(len(train_pool) * float(val_fraction)))) if len(train_pool) > 1 else 0
        val_idx = train_pool[-val_n:] if val_n else np.asarray([], dtype=np.int64)
        train_idx = train_pool[:-val_n] if val_n else train_pool
        return train_idx.astype(np.int64), val_idx.astype(np.int64), test_idx.astype(np.int64)
    return time_ordered_split_indices(n, test_size=float(test_size), val_size=float(val_fraction))


def build_event_ids(y: Sequence[int] | np.ndarray, *, normal_class_id: int = 0) -> np.ndarray:
    labels = np.asarray(y, dtype=int).reshape(-1)
    ids: list[str] = []
    active_event_start: int | None = None
    active_class: int | None = None
    for i, label in enumerate(labels):
        class_id = int(label)
        if class_id == int(normal_class_id):
            active_event_start = None
            active_class = None
            ids.append(f"normal_{i}")
            continue
        if active_event_start is None or active_class != class_id:
            active_event_start = i
            active_class = class_id
        ids.append(f"event_{active_event_start}")
    return np.asarray(ids, dtype=object)


def build_event_horizons(y: Sequence[int] | np.ndarray, *, normal_class_id: int = 0) -> np.ndarray:
    labels = np.asarray(y, dtype=int).reshape(-1)
    horizons = np.full(len(labels), -1.0, dtype=float)
    i = 0
    while i < len(labels):
        if int(labels[i]) == int(normal_class_id):
            i += 1
            continue
        j = i + 1
        while j < len(labels) and int(labels[j]) == int(labels[i]):
            j += 1
        run_len = j - i
        horizons[i:j] = np.arange(run_len, 0, -1, dtype=float)
        i = j
    return horizons


def load_class_mapping(dataset_dir: Path) -> tuple[list[int], list[str]]:
    raw = json.loads((dataset_dir / "class_name_mapping.json").read_text(encoding="utf-8"))
    classes = sorted(raw.get("classes", []), key=lambda x: int(x["class_id"]))
    class_ids = [int(row["class_id"]) for row in classes]
    class_names = [str(row["class_name"]) for row in classes]
    return class_ids, class_names


def build_experiment_specs(methods: Sequence[str] | None = None) -> list[MulticlassExperimentSpec]:
    specs = [
        MulticlassExperimentSpec(
            "full_model",
            "main",
            "KIEP-GL full multiclass event warning model.",
            {"paper_model_variant": "invariant_event_precursor_graph", "kiepgl_enabled": True},
        ),
        MulticlassExperimentSpec(
            "no_event_anchored_graph",
            "graph_structure",
            "Use original graph branch without event-anchored KIEP-GL paths.",
            {"paper_model_variant": "original", "kiepgl_enabled": False},
        ),
        MulticlassExperimentSpec(
            "no_knowledge_prior_learning",
            "knowledge_prior",
            "Disable graph prior posterior constraints and learned knowledge-prior weights.",
            {
                "kiepgl_loss_edge_prior_weight": 0.0,
                "paper_method_enable_llm_prior": False,
                "paper_use_history_state": False,
                "paper_use_annotation_prior": False,
                "paper_use_data_refined_prior": False,
            },
        ),
        MulticlassExperimentSpec(
            "no_path_mil",
            "path_mil",
            "Disable class-specific top-k path MIL pressure.",
            {"kiepgl_loss_path_mil_weight": 0.0, "kiepgl_path_top_k": 1},
        ),
        MulticlassExperimentSpec(
            "no_invariance_regularizer",
            "invariance",
            "Disable cross-regime invariant path regularization.",
            {"kiepgl_loss_invariance_weight": 0.0},
        ),
        MulticlassExperimentSpec(
            "no_counterfactual_consistency",
            "counterfactual",
            "Disable counterfactual path occlusion consistency.",
            {"kiepgl_loss_counterfactual_weight": 0.0, "kiepgl_counterfactual_target_drop": 0.0},
        ),
    ]
    if not methods:
        return specs
    keep = {str(x).strip() for x in methods if str(x).strip()}
    return [spec for spec in specs if spec.name in keep]


def load_multiclass_dataset(dataset_dir: Path, *, max_rows: int | None = None) -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray]:
    x = pd.read_csv(dataset_dir / "X_process_features.csv")
    y = pd.read_csv(dataset_dir / "y_quality_label.csv")
    n = min(len(x), len(y))
    if max_rows is not None and int(max_rows) > 0:
        n = min(n, int(max_rows))
    x = x.iloc[:n].reset_index(drop=True)
    y = y.iloc[:n].reset_index(drop=True)
    labels = pd.to_numeric(y["event_quality_class_id"], errors="coerce").fillna(0).astype(int).to_numpy()
    return x, y, labels


def _fit_one_spec(
    x: pd.DataFrame,
    y_meta: pd.DataFrame,
    labels: np.ndarray,
    *,
    feature_cols: list[str],
    class_ids: list[int],
    class_names: list[str],
    spec: MulticlassExperimentSpec,
    config: Mapping[str, Any],
    seed: int,
    project_root: Path,
) -> dict[str, Any]:
    missing = [
        name
        for name, value in {
            "UnifiedDefectGraphModel": UnifiedDefectGraphModel,
            "build_graph_prior_from_project": build_graph_prior_from_project,
            "build_train_data_prior_edges": build_train_data_prior_edges,
            "encode_temporal_features_from_df": encode_temporal_features_from_df,
        }.items()
        if value is None
    ]
    if missing:
        raise ImportError(
            "KIEP-GL full multiclass experiment dependencies are unavailable in this recovered workspace: "
            + ", ".join(missing)
        )
    cfg = copy.deepcopy(dict(config))
    cfg.update(spec.overrides)
    cfg["random_state"] = int(seed)
    cfg["paper_risk_head_type"] = str(cfg.get("paper_risk_head_type", "extra_trees"))
    cfg["knowledge_state_enabled"] = False
    cfg["training_visualization_enabled"] = False
    cfg["llm_topology_enabled"] = False
    cfg["paper_method_enable_llm_prior"] = False

    idx_train, idx_val, idx_test = time_ordered_split_indices(
        len(x),
        test_size=float(cfg.get("defect_test_size", 0.2)),
        val_size=float(cfg.get("defect_val_fraction_of_train", 0.2)),
    )
    y_abnormal_train = (labels[idx_train] != 0).astype(int)
    train_data_prior_edges = build_train_data_prior_edges(
        feature_cols,
        x.iloc[idx_train],
        y_abnormal_train,
        cfg,
    )
    graph_prior = build_graph_prior_from_project(
        project_root,
        feature_cols,
        prior_config.hard_rules,
        cfg,
        runtime_data_refined_edges=train_data_prior_edges,
    )
    embedding = encode_temporal_features_from_df(x, feature_cols, cfg)
    train_embedding = embedding.__class__(
        values=embedding.values[idx_train],
        feature_names=list(embedding.feature_names),
        node_slices=dict(embedding.node_slices),
        metadata=dict(embedding.metadata),
    )
    test_embedding = embedding.__class__(
        values=embedding.values[idx_test],
        feature_names=list(embedding.feature_names),
        node_slices=dict(embedding.node_slices),
        metadata=dict(embedding.metadata),
    )

    model = UnifiedDefectGraphModel(cfg)
    model.fit(train_embedding, labels[idx_train], graph_prior)
    proba_raw, classes = model.predict_class_proba(test_embedding)
    proba = align_proba_to_class_ids(proba_raw, classes, expected_class_ids=class_ids)
    forward_out = model.forward(test_embedding, None, graph_prior)
    top_paths_by_class = dict(forward_out.get("top_paths_by_class", {}))

    event_ids = build_event_ids(labels[idx_test])
    horizons = build_event_horizons(labels[idx_test])
    evaluation = summarize_multiclass_event_evaluation(
        labels[idx_test],
        proba,
        class_names=class_names,
        event_ids=event_ids,
        horizons=horizons,
        top_paths_by_class=top_paths_by_class,
    )
    run = {
        "status": "ok",
        "experiment_name": spec.name,
        "category": spec.category,
        "objective": spec.objective,
        "seed": int(seed),
        "overrides": dict(spec.overrides),
        "n_rows": int(len(x)),
        "n_features": int(len(feature_cols)),
        "class_ids": class_ids,
        "class_names": class_names,
        "train_class_counts": {str(k): int(v) for k, v in pd.Series(labels[idx_train]).value_counts().sort_index().items()},
        "val_class_counts": {str(k): int(v) for k, v in pd.Series(labels[idx_val]).value_counts().sort_index().items()},
        "test_class_counts": {str(k): int(v) for k, v in pd.Series(labels[idx_test]).value_counts().sort_index().items()},
        "split_protocol_used": "time_ordered_multiclass",
        "sample_multiclass_metrics": evaluation["sample_multiclass_metrics"],
        "event_warning_metrics": evaluation["event_warning_metrics"],
        "path_explanation_metrics": evaluation["path_explanation_metrics"],
        "loss_dict": dict(forward_out.get("loss_dict", {})),
        "top_paths_by_class": top_paths_by_class,
        "graph_prior_top_edges": graph_prior.strong_edges(top_k=10),
        "refined_graph_top_edges": model.refined_graph.strong_edges(top_k=10) if model.refined_graph else [],
    }
    return run


def run_kiepgl_multiclass_experiments(
    *,
    dataset_dir: Path = DEFAULT_DATASET_DIR,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    max_rows: int | None = None,
    methods: Sequence[str] | None = None,
    seeds: Sequence[int] = (42,),
    tree_estimators: int | None = None,
    tree_max_depth: int | None = None,
) -> dict[str, Any]:
    class_ids, class_names = load_class_mapping(dataset_dir)
    x, y_meta, labels = load_multiclass_dataset(dataset_dir, max_rows=max_rows)
    feature_cols = [str(c) for c in x.columns if pd.api.types.is_numeric_dtype(x[c])]
    cfg = dict(CONFIG)
    cfg.update(
        {
            "preferred_label_column": "event_quality_class_id",
            "paper_model_variant": "invariant_event_precursor_graph",
            "kiepgl_enabled": True,
            "paper_risk_head_type": "extra_trees",
            "defect_split_mode": "time_ordered",
            "defect_val_fraction_of_train": 0.2,
            "defect_test_size": 0.2,
        }
    )
    if tree_estimators is not None and int(tree_estimators) > 0:
        cfg["paper_tree_n_estimators"] = int(tree_estimators)
    if tree_max_depth is not None and int(tree_max_depth) > 0:
        cfg["paper_tree_max_depth"] = int(tree_max_depth)

    runs: list[dict[str, Any]] = []
    specs = build_experiment_specs(methods)
    for spec in specs:
        for seed in seeds:
            print(f"\n=== KIEP-GL Multiclass Experiment: {spec.name} [{spec.category}] seed={int(seed)} ===")
            try:
                run = _fit_one_spec(
                    x,
                    y_meta,
                    labels,
                    feature_cols=feature_cols,
                    class_ids=class_ids,
                    class_names=class_names,
                    spec=spec,
                    config=cfg,
                    seed=int(seed),
                    project_root=PROJECT_ROOT,
                )
            except Exception as exc:
                run = {
                    "status": "failed",
                    "reason": str(exc),
                    "experiment_name": spec.name,
                    "category": spec.category,
                    "objective": spec.objective,
                    "seed": int(seed),
                }
            runs.append(run)
            if run.get("status") == "ok":
                sample = run.get("sample_multiclass_metrics", {})
                event = run.get("event_warning_metrics", {})
                path = run.get("path_explanation_metrics", {})
                print(
                    "macro_f1={:.4f} macro_recall={:.4f} event_macro_recall={:.4f} "
                    "lead_time={:.4f} path_hit={:.4f} knowledge={:.4f}".format(
                        float(sample.get("macro_f1", 0.0)),
                        float(sample.get("macro_recall", 0.0)),
                        float(event.get("event_macro_recall", 0.0)),
                        float(event.get("average_lead_time", 0.0)),
                        float(path.get("path_hit_rate", 0.0)),
                        float(path.get("knowledge_consistency", 0.0)),
                    )
                )
            else:
                print(f"failed: {run.get('reason')}")

    out = {
        "status": "ok",
        "task": "multiclass_event_level_quality_warning",
        "dataset_dir": str(dataset_dir),
        "n_rows": int(len(x)),
        "n_features": int(len(feature_cols)),
        "class_ids": class_ids,
        "class_names": class_names,
        "methods": [spec.name for spec in specs],
        "seeds": [int(s) for s in seeds],
        "runs": runs,
        "summary_table": summarize_runs(runs),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(_json_sanitize(out), ensure_ascii=False, indent=2), encoding="utf-8")
    summary_path = output_path.with_suffix(".summary.csv")
    pd.DataFrame(out["summary_table"]).to_csv(summary_path, index=False, encoding="utf-8-sig")
    out["saved_to"] = str(output_path)
    out["summary_saved_to"] = str(summary_path)
    return out


def _split_csv(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run KIEP-GL multiclass event-level warning experiments on v4 dataset.")
    parser.add_argument("--dataset-dir", type=str, default=str(DEFAULT_DATASET_DIR))
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT_PATH))
    parser.add_argument("--max-rows", type=int, default=20000)
    parser.add_argument("--methods", type=str, default="full_model,no_event_anchored_graph,no_path_mil")
    parser.add_argument("--seeds", type=str, default="42")
    parser.add_argument("--tree-estimators", type=int, default=80)
    parser.add_argument("--tree-max-depth", type=int, default=10)
    args = parser.parse_args()

    result = run_kiepgl_multiclass_experiments(
        dataset_dir=Path(args.dataset_dir),
        output_path=Path(args.output),
        max_rows=int(args.max_rows) if int(args.max_rows) > 0 else None,
        methods=_split_csv(args.methods),
        seeds=[int(x) for x in _split_csv(args.seeds)] or [42],
        tree_estimators=int(args.tree_estimators),
        tree_max_depth=int(args.tree_max_depth),
    )
    print("\n=== KIEP-GL Multiclass Summary ===")
    print(f"runs={len(result.get('runs', []))}")
    print(f"saved_to={result.get('saved_to')}")
    print(f"summary_saved_to={result.get('summary_saved_to')}")
    for row in result.get("summary_table", []):
        print(
            f"- {row.get('experiment_name')} [{row.get('category')}]: "
            f"macro_f1={row.get('macro_f1_mean')}, "
            f"event_macro_recall={row.get('event_macro_recall_mean')}, "
            f"path_hit={row.get('path_hit_rate_mean')}"
        )


if __name__ == "__main__":
    main()
