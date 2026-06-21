"""Run result-level ablations for prompt-atom decomposition strategies.

This wrapper does not generate synthetic scores. It calls the main
FSDV-EAPA experiment script once per decomposition strategy, then summarizes
the resulting NER F1, RE F1, Overall F1, and KHR from ablation_results.json.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


STRATEGIES = [
    "no_atom",
    "fsdv_block",
    "sentence_level",
    "random_atom",
    "over_fine",
    "functional_atom",
]


def _root_path(output_root: str) -> Path:
    return Path(str(output_root).replace("\\", "/"))


def build_strategy_command(
    strategy: str,
    output_root: str,
    samples: int,
    valset_size: int,
    iterations: int,
    quick_eval_samples: Optional[int],
    mode: str = "re_pipeline",
    data: Optional[str] = None,
    domain: str = "steel_casting",
    prompt_language: str = "auto",
    runs: int = 1,
    num_candidates: int = 6,
    collect_n: int = 8,
    max_eval_candidates: int = 4,
) -> List[str]:
    root = Path(output_root) / strategy
    cmd = [
        sys.executable,
        "experiments/prompt_engineering_ablation.py",
        "--mode",
        mode,
        "--domain",
        domain,
        "--prompt_language",
        prompt_language,
        "--samples",
        str(samples),
        "--valset_size",
        str(valset_size),
        "--iterations",
        str(iterations),
        "--runs",
        str(runs),
        "--output_dir",
        str(root / "prompt_training").replace("\\", "/"),
        "--output",
        str(root / "post_eval").replace("\\", "/"),
        "--atom_decomposition_strategy",
        strategy,
        "--num_candidates",
        str(num_candidates),
        "--collect_n",
        str(collect_n),
        "--max_eval_candidates",
        str(max_eval_candidates),
    ]
    if quick_eval_samples is not None:
        cmd.extend(["--quick_eval_samples", str(quick_eval_samples)])
    if data:
        cmd.extend(["--data", data])
    return cmd


def _find_metric_block(report: Dict[str, Any]) -> Dict[str, Any]:
    results = report.get("results", report)
    if not isinstance(results, dict):
        return {}
    for key in ("FSDV-EAPA", "FSDC (训练后)", "FSDC (完整, 训练后)"):
        block = results.get(key)
        if isinstance(block, dict):
            return block
    for key, block in results.items():
        if isinstance(block, dict) and ("EAPA" in str(key) or block.get("is_trained")):
            return block
    return {}


def extract_transfer_metrics(strategy: str, report: Dict[str, Any]) -> Dict[str, Any]:
    block = _find_metric_block(report)
    metrics = {
        "ner_f1": block.get("avg_ner_f1"),
        "re_f1": block.get("avg_re_f1"),
        "overall_f1": block.get("avg_f1"),
        "khr": block.get("avg_khr"),
    }
    if not block:
        status = "missing_result_block"
    elif all(value is None for value in metrics.values()):
        status = str(block.get("status") or report.get("status") or "missing_metrics")
    else:
        status = "ok"
    return {
        "strategy": strategy,
        **metrics,
        "status": status,
    }


def summarize_training_history(strategy: str, history_path: Path) -> Dict[str, Any]:
    summary = {
        "accepted_updates": None,
        "rollbacks": None,
        "best_val_score": None,
    }
    if not history_path.exists():
        return summary
    try:
        history = json.loads(history_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return summary
    rows = history if isinstance(history, list) else history.get("history", [])
    if not isinstance(rows, list):
        return summary
    accepted = 0
    rollbacks = 0
    best = None
    for row in rows:
        if not isinstance(row, dict):
            continue
        text = str(row.get("improvement", "")).lower()
        if row.get("accepted") is True or "accepted" in text or "采纳" in text:
            accepted += 1
        if "rollback" in text or "回退" in text or "拒绝" in text or "reject" in text:
            rollbacks += 1
        score = row.get("score")
        if isinstance(score, (int, float)):
            best = score if best is None else max(best, float(score))
    summary["accepted_updates"] = accepted
    summary["rollbacks"] = rollbacks
    summary["best_val_score"] = best
    return summary


def result_path_for_strategy(output_root: str, strategy: str) -> Path:
    return _root_path(output_root) / strategy / "post_eval" / "re_pipeline_post" / "ablation_results.json"


def collect_strategy_row(output_root: str, strategy: str) -> Dict[str, Any]:
    result_path = result_path_for_strategy(output_root, strategy)
    row: Dict[str, Any] = {
        "strategy": strategy,
        "ner_f1": None,
        "re_f1": None,
        "overall_f1": None,
        "khr": None,
        "accepted_updates": None,
        "rollbacks": None,
        "best_val_score": None,
        "result_path": str(result_path),
        "status": "missing_result_file",
    }
    if result_path.exists():
        report = json.loads(result_path.read_text(encoding="utf-8"))
        row.update(extract_transfer_metrics(strategy, report))
        row["result_path"] = str(result_path)
    history_path = _root_path(output_root) / strategy / "prompt_training" / "training_history.json"
    row.update(summarize_training_history(strategy, history_path))
    return row


def write_summary(rows: List[Dict[str, Any]], output_root: str) -> None:
    out = _root_path(output_root)
    out.mkdir(parents=True, exist_ok=True)
    fields = [
        "strategy",
        "ner_f1",
        "re_f1",
        "overall_f1",
        "khr",
        "accepted_updates",
        "rollbacks",
        "best_val_score",
        "status",
        "result_path",
    ]
    csv_path = out / "atom_decomposition_result_summary.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})
    json_path = out / "atom_decomposition_result_summary.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    tex_lines = [
        r"\begin{tabular}{lccccc}",
        r"\toprule",
        r"Strategy & NER F1 & RE F1 & Overall F1 & KHR$\downarrow$ & Updates \\",
        r"\midrule",
    ]
    for row in rows:
        tex_lines.append(
            f"{row.get('strategy')} & {_fmt(row.get('ner_f1'))} & {_fmt(row.get('re_f1'))} & "
            f"{_fmt(row.get('overall_f1'))} & {_fmt(row.get('khr'))} & "
            f"{_fmt_int(row.get('accepted_updates'))}/{_fmt_int(row.get('rollbacks'))} \\\\"
        )
    tex_lines.extend([r"\bottomrule", r"\end{tabular}", ""])
    table_path = out / "atom_decomposition_result_table.tex"
    table_path.parent.mkdir(parents=True, exist_ok=True)
    table_path.write_text("\n".join(tex_lines), encoding="utf-8")


def _fmt(value: Any) -> str:
    return "--" if value is None else f"{float(value):.4f}"


def _fmt_int(value: Any) -> str:
    return "--" if value is None else str(int(value))


def run(args: argparse.Namespace) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    for strategy in STRATEGIES:
        cmd = build_strategy_command(
            strategy=strategy,
            output_root=args.output_root,
            samples=args.samples,
            valset_size=args.valset_size,
            iterations=args.iterations,
            quick_eval_samples=args.quick_eval_samples,
            mode=args.mode,
            data=args.data,
            domain=args.domain,
            prompt_language=args.prompt_language,
            runs=args.runs,
            num_candidates=args.num_candidates,
            collect_n=args.collect_n,
            max_eval_candidates=args.max_eval_candidates,
        )
        print("\n" + "=" * 80)
        print(f"Strategy: {strategy}")
        print("Command:", " ".join(cmd))
        if not args.dry_run:
            subprocess.run(cmd, cwd=Path(__file__).resolve().parents[1], check=True, env=env)
        rows.append(collect_strategy_row(args.output_root, strategy))
        write_summary(rows, args.output_root)
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run prompt-atom decomposition result ablations.")
    parser.add_argument("--output-root", default="outputs/atom_decomposition_result")
    parser.add_argument("--mode", default="re_pipeline", choices=["re_pipeline"])
    parser.add_argument("--data", default=None)
    parser.add_argument("--domain", default="steel_casting")
    parser.add_argument("--prompt-language", default="auto", choices=["auto", "zh", "en"])
    parser.add_argument("--samples", type=int, default=30)
    parser.add_argument("--valset-size", type=int, default=20)
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--quick-eval-samples", type=int, default=None)
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--num-candidates", type=int, default=6)
    parser.add_argument("--collect-n", type=int, default=8)
    parser.add_argument("--max-eval-candidates", type=int, default=4)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
