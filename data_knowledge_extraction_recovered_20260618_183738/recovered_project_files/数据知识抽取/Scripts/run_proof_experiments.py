from __future__ import annotations

import argparse
import sys
from pathlib import Path

from config import CONFIG
from data_processing import load_and_process_data
from feature_extraction import base_feature_columns
from paper_defect_pipeline import run_paper_defect_pipeline
from proof_experiment_runner import run_proof_experiments


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _split_csv(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run paper proof experiments: event delay, MIL, knowledge graph, dynamic graph, and robustness."
    )
    parser.add_argument("--profile", choices=["quick", "full"], default="quick")
    parser.add_argument("--max-rows", type=int, default=8000, help="Use the first N time-ordered rows for quick experiments.")
    parser.add_argument("--epochs", type=int, default=2, help="MLP epochs for each proof run.")
    parser.add_argument("--seeds", type=str, default="42", help="Comma-separated random seeds, e.g. 7,13,42.")
    parser.add_argument(
        "--methods",
        type=str,
        default="",
        help="Optional comma-separated method names. Empty means all methods in the selected profile.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="knowledge_exports/proof_experiment_suite.json",
        help="Output JSON path. A .summary.csv file is written beside it.",
    )
    parser.add_argument("--enable-llm", action="store_true", help="Allow LLM prior calls if API key is configured.")
    args = parser.parse_args()

    try:
        stdout_reconfigure = getattr(sys.stdout, "reconfigure", None)
        if callable(stdout_reconfigure):
            stdout_reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    cfg = dict(CONFIG)
    cfg.update(
        {
            "paper_mlp_epochs": int(args.epochs),
            "training_visualization_enabled": False,
            "knowledge_state_enabled": False,
            "proof_experiment_output_path": str(args.output),
            "proof_experiment_seeds": [int(x) for x in _split_csv(args.seeds)] or [42],
            "paper_evidence_eval_max_rows": 1000,
            "paper_edge_occlusion_top_k": 3,
            "knowledge_candidate_top_k": 5,
            "paper_task_graph_update_top_k": 3,
        }
    )
    methods = _split_csv(args.methods)
    if methods:
        cfg["proof_experiment_methods"] = methods
    if not args.enable_llm:
        cfg["llm_topology_enabled"] = False
        cfg["paper_method_enable_llm_prior"] = False

    print("=== Proof Experiment Runner ===")
    print(f"profile={args.profile}, max_rows={args.max_rows}, epochs={args.epochs}, seeds={cfg['proof_experiment_seeds']}")
    if methods:
        print(f"methods={methods}")
    print(f"output={args.output}")

    df = load_and_process_data(str(cfg.get("file_path")))
    feature_cols = base_feature_columns(df)
    result = run_proof_experiments(
        df,
        feature_cols,
        cfg,
        PROJECT_ROOT,
        profile=args.profile,
        max_rows=int(args.max_rows),
        paper_runner=run_paper_defect_pipeline,
    )
    print("\n=== Proof Experiment Summary ===")
    print(f"runs={len(result.get('runs', []))}")
    print(f"saved_to={result.get('saved_to')}")
    print(f"summary_saved_to={result.get('summary_saved_to')}")
    for row in result.get("summary_table", [])[:20]:
        print(
            f"- {row.get('experiment_name')} [{row.get('category')}]: "
            f"PR-AUC={row.get('pr_auc_test_mean')}, "
            f"F1={row.get('f1_defect_test_tuned_mean')}, "
            f"MIL={row.get('mil_enabled_any')}, "
            f"registry_updates={row.get('candidate_registry_updated_total')}"
        )


if __name__ == "__main__":
    main()
