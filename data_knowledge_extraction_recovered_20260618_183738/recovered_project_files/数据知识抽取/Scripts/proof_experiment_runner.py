from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np
import pandas as pd


PaperRunner = Callable[[pd.DataFrame, list[str], dict[str, Any], Path], dict[str, Any]]


@dataclass(frozen=True)
class ProofExperimentSpec:
    name: str
    category: str
    objective: str
    overrides: dict[str, Any] = field(default_factory=dict)
    data_transform: dict[str, Any] = field(default_factory=dict)


def build_proof_experiment_specs(profile: str = "quick") -> list[ProofExperimentSpec]:
    """Build the proof matrix used by the paper-facing experiment runner."""
    base = [
        ProofExperimentSpec(
            name="full_model",
            category="main",
            objective="主方法：事件前驱监督、知识/因果证据、工况动态图、子故障辅助输出全部启用。",
        ),
        ProofExperimentSpec(
            name="no_event_mil_point_label",
            category="event_delay",
            objective="证明事件延迟处理必要：退回逐点标签，不构造前驱窗口和 MIL bag。",
            overrides={"paper_event_supervision_enabled": False},
        ),
        ProofExperimentSpec(
            name="single_precursor_window",
            category="event_delay",
            objective="证明多级前驱窗口必要：只使用单一前驱窗口，不区分 early/mid/late。",
            overrides={
                "event_precursor_levels": [
                    {"name": "single", "min_lag": 1, "max_lag": 12, "weight": 1.0}
                ]
            },
        ),
        ProofExperimentSpec(
            name="no_structured_knowledge_prior",
            category="knowledge_graph",
            objective="证明知识先验必要：关闭 LLM/历史/标注/数据精炼先验，只保留弱规则默认图。",
            overrides={
                "paper_method_enable_llm_prior": False,
                "paper_use_history_state": False,
                "paper_use_annotation_prior": False,
                "paper_use_data_refined_prior": False,
            },
        ),
        ProofExperimentSpec(
            name="no_edge_causal_attributes",
            category="knowledge_graph",
            objective="证明边证据属性必要：去掉 Granger/TE/规则/任务遮蔽等边属性通道。",
            overrides={"paper_disable_edge_attributes": True},
        ),
        ProofExperimentSpec(
            name="static_no_regime_task_update",
            category="dynamic_graph",
            objective="证明工况调制与任务驱动图更新必要：关闭 regime modulation 和 task graph update。",
            overrides={
                "paper_regime_enabled": False,
                "paper_task_driven_graph_update_enabled": False,
                "paper_disable_dynamic_context": True,
            },
        ),
        ProofExperimentSpec(
            name="missing_10pct",
            category="robustness",
            objective="证明缺失扰动稳健性：对过程特征随机注入 10% 缺失值。",
            data_transform={"kind": "missing", "rate": 0.10},
        ),
    ]
    if str(profile).strip().lower() == "quick":
        return base
    return base + [
        ProofExperimentSpec(
            name="no_long_short_memory",
            category="temporal",
            objective="证明类人长短记忆特征必要：关闭 memory-fused temporal features。",
            overrides={"paper_memory_enabled": False},
        ),
        ProofExperimentSpec(
            name="temporal_only_no_graph",
            category="knowledge_graph",
            objective="证明图结构必要：只使用时间编码，不使用图消息传递。",
            overrides={"paper_temporal_only": True},
        ),
        ProofExperimentSpec(
            name="no_graph_refiner",
            category="dynamic_graph",
            objective="证明数据驱动图修正必要：只使用初始先验图。",
            overrides={"paper_disable_graph_refiner": True},
        ),
        ProofExperimentSpec(
            name="no_lagged_message",
            category="temporal",
            objective="证明滞后消息传递必要：关闭图中的 lagged message。",
            overrides={"paper_disable_lagged_message": True},
        ),
        ProofExperimentSpec(
            name="noise_5pct",
            category="robustness",
            objective="证明噪声扰动稳健性：按特征标准差注入 5% 高斯噪声。",
            data_transform={"kind": "noise", "std_ratio": 0.05},
        ),
        ProofExperimentSpec(
            name="missing_20pct",
            category="robustness",
            objective="证明更强缺失扰动下的退化曲线：过程特征随机注入 20% 缺失值。",
            data_transform={"kind": "missing", "rate": 0.20},
        ),
    ]


def apply_robustness_transform(
    df: pd.DataFrame,
    feature_cols: Sequence[str],
    transform: Mapping[str, Any] | None,
    *,
    seed: int,
) -> pd.DataFrame:
    """Apply deterministic perturbations for robustness experiments."""
    if not transform:
        return df.copy(deep=True)
    out = df.copy(deep=True)
    rng = np.random.default_rng(int(seed))
    cols = [c for c in feature_cols if c in out.columns and pd.api.types.is_numeric_dtype(out[c])]
    if not cols:
        return out
    kind = str(transform.get("kind", "")).strip().lower()
    if kind == "missing":
        rate = float(np.clip(transform.get("rate", 0.1), 0.0, 0.95))
        if rate <= 0:
            return out
        mask = rng.random((len(out), len(cols))) < rate
        for j, col in enumerate(cols):
            out.loc[mask[:, j], col] = np.nan
        return out
    if kind == "noise":
        std_ratio = float(max(0.0, transform.get("std_ratio", 0.05)))
        if std_ratio <= 0:
            return out
        values = out[cols].to_numpy(dtype=np.float64, copy=True)
        scale = np.nanstd(values, axis=0)
        scale = np.where(np.isfinite(scale) & (scale > 0), scale, 1.0)
        values = values + rng.normal(loc=0.0, scale=scale * std_ratio, size=values.shape)
        out.loc[:, cols] = values
        return out
    return out


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


def _nested_get(row: Mapping[str, Any], path: Sequence[str], default: Any = None) -> Any:
    cur: Any = row
    for key in path:
        if not isinstance(cur, Mapping):
            return default
        cur = cur.get(key, default)
    return cur


def _mean_std(values: list[float]) -> tuple[float | None, float | None]:
    clean = [float(v) for v in values if np.isfinite(float(v))]
    if not clean:
        return None, None
    return float(np.mean(clean)), float(np.std(clean))


def summarize_runs(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for row in rows:
        if row.get("status") != "ok":
            continue
        key = (str(row.get("experiment_name", "")), str(row.get("category", "")))
        grouped.setdefault(key, []).append(row)

    summary: list[dict[str, Any]] = []
    metric_paths = {
        "pr_auc_test": ("pr_auc_test",),
        "f1_defect_test_tuned": ("f1_defect_test_tuned",),
        "precision_defect_test_tuned": ("precision_defect_test_tuned",),
        "recall_defect_test_tuned": ("recall_defect_test_tuned",),
        "roc_auc_test": ("roc_auc_test",),
        "mil_bag_recall": ("mil_event_metrics", "bag_recall"),
        "mil_false_alarm_rate_point": ("mil_event_metrics", "false_alarm_rate_point"),
        "mil_mean_bag_probability": ("mil_event_metrics", "mean_bag_probability"),
        "lead_time_median_steps": ("fault_outputs", "early_warning", "lead_time_summary", "median_horizon_steps"),
    }
    for (name, category), items in sorted(grouped.items(), key=lambda x: x[0]):
        row: dict[str, Any] = {
            "experiment_name": name,
            "category": category,
            "n_runs": int(len(items)),
        }
        for metric, path in metric_paths.items():
            vals = [
                _nested_get(item, path)
                for item in items
                if isinstance(_nested_get(item, path), (int, float, np.integer, np.floating))
            ]
            mean, std = _mean_std([float(v) for v in vals])
            row[f"{metric}_mean"] = mean
            row[f"{metric}_std"] = std
        row["candidate_registry_updated_total"] = int(
            sum(int(_nested_get(item, ("knowledge_candidate_registry", "updated"), 0) or 0) for item in items)
        )
        row["evidence_source_count_max"] = int(
            max(
                [
                    len(_nested_get(item, ("dynamic_graph_evidence", "edge_evidence_sources"), []) or [])
                    for item in items
                ]
                or [0]
            )
        )
        row["mil_enabled_any"] = bool(any(bool(_nested_get(item, ("mil_event_metrics", "enabled"), False)) for item in items))
        modes = sorted({str(_nested_get(item, ("fault_outputs", "mode"), "")) for item in items if _nested_get(item, ("fault_outputs", "mode"), "")})
        row["fault_output_modes"] = ",".join(modes)
        summary.append(row)
    return summary


def _run_digest(rep: Mapping[str, Any]) -> dict[str, Any]:
    keep = [
        "status",
        "reason",
        "split_protocol_used",
        "pr_auc_test",
        "f1_defect_test_tuned",
        "precision_defect_test_tuned",
        "recall_defect_test_tuned",
        "roc_auc_test",
        "accuracy_test_tuned",
        "event_supervision",
        "mil_event_metrics",
        "fault_outputs",
        "evidence_metrics",
        "edge_occlusion_metrics",
        "knowledge_candidate_registry",
        "dynamic_graph_evidence",
        "time_split_summary",
    ]
    return {k: rep.get(k) for k in keep if k in rep}


def run_proof_experiments(
    df: pd.DataFrame,
    feature_cols: list[str],
    config: Mapping[str, Any],
    project_root: Path,
    *,
    profile: str = "quick",
    max_rows: int | None = None,
    paper_runner: PaperRunner,
) -> dict[str, Any]:
    specs = build_proof_experiment_specs(profile)
    method_filter = config.get("proof_experiment_methods")
    if isinstance(method_filter, (list, tuple)) and method_filter:
        keep = {str(x) for x in method_filter}
        specs = [spec for spec in specs if spec.name in keep]
    seeds = list(config.get("proof_experiment_seeds") or config.get("paper_experiment_seeds") or [42])
    if not seeds:
        seeds = [42]
    base_df = df.head(int(max_rows)).copy(deep=True) if max_rows and int(max_rows) > 0 else df.copy(deep=True)
    runs: list[dict[str, Any]] = []

    for spec in specs:
        print(f"\n=== Proof Experiment: {spec.name} [{spec.category}] ===")
        for seed in seeds:
            run_cfg = copy.deepcopy(dict(config))
            run_cfg.update(spec.overrides)
            run_cfg["random_state"] = int(seed)
            run_cfg["knowledge_state_enabled"] = False
            run_cfg["training_visualization_enabled"] = False
            run_cfg.setdefault("paper_evidence_eval_max_rows", 2000)
            run_df = apply_robustness_transform(base_df, feature_cols, spec.data_transform, seed=int(seed))
            rep = paper_runner(run_df, feature_cols, run_cfg, project_root)
            row = _run_digest(rep if isinstance(rep, Mapping) else {"status": "failed", "reason": "non_mapping_report"})
            row.update(
                {
                    "experiment_name": spec.name,
                    "category": spec.category,
                    "objective": spec.objective,
                    "seed": int(seed),
                    "overrides": dict(spec.overrides),
                    "data_transform": dict(spec.data_transform),
                    "n_rows": int(len(run_df)),
                }
            )
            runs.append(row)

    out = {
        "status": "ok",
        "profile": str(profile),
        "protocol": {
            "split_mode": config.get("defect_split_mode", "time_ordered"),
            "seeds": [int(s) for s in seeds],
            "max_rows": int(max_rows) if max_rows else None,
            "main_metrics": ["PR-AUC", "F1_defect_tuned"],
            "event_metrics": ["Bag Recall", "False Alarm Rate", "Lead Time"],
            "evidence_metrics": ["Evidence Source Contribution", "Edge Occlusion"],
        },
        "experiment_specs": [_json_sanitize(spec.__dict__) for spec in specs],
        "runs": runs,
        "summary_table": summarize_runs(runs),
    }
    output_raw = config.get("proof_experiment_output_path", "knowledge_exports/proof_experiment_suite.json")
    if output_raw:
        output_path = Path(str(output_raw))
        if not output_path.is_absolute():
            output_path = project_root / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(_json_sanitize(out), ensure_ascii=False, indent=2), encoding="utf-8")
        csv_path = output_path.with_suffix(".summary.csv")
        pd.DataFrame(out["summary_table"]).to_csv(csv_path, index=False, encoding="utf-8-sig")
        out["saved_to"] = str(output_path)
        out["summary_saved_to"] = str(csv_path)
    return out
