from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPORTS_DIR = PROJECT_ROOT / "knowledge_exports"


MODE_SLUGS = {
    "reverse_direction": "reverse",
    "lag_shift": "lag",
    "random_target": "random",
}


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _exists(path: Path | str) -> bool:
    return os.path.exists(_fs_path(path))


def _read_text(path: Path | str) -> str:
    with open(_fs_path(path), encoding="utf-8") as handle:
        return handle.read()


def _write_text(path: Path | str, text: str) -> None:
    with open(_fs_path(path), "w", encoding="utf-8") as handle:
        handle.write(text)


@dataclass(frozen=True)
class SuiteConfig:
    exports_dir: Path
    seeds: tuple[int, ...]
    sequence_epochs: int
    probe_epochs: int
    guard_modes: tuple[str, ...]
    min_macro_drop: float
    edge_reliability_threshold: float
    max_far_increase_percent: float
    hidden_dim: int
    batch_size: int
    model: str = "gpt-5.5"


@dataclass(frozen=True)
class SuiteJob:
    seed: int
    source_edges_file: Path
    output_file: Path
    command: list[str]
    is_complete: bool


def _mode_slug(modes: tuple[str, ...]) -> str:
    return "_".join(MODE_SLUGS.get(mode, mode) for mode in modes) or "none"


def _source_edges_file(exports_dir: Path, seed: int) -> Path:
    return exports_dir / f"public_benchmark_skab_dynamic_llm_api_seed{seed}_e8_learned_reliability_probe2_t045_k4.json"


def _output_file(config: SuiteConfig, seed: int) -> Path:
    return config.exports_dir / (
        f"public_benchmark_skab_dynamic_llm_api_seed{seed}_e{config.sequence_epochs}"
        f"_cf_guard_{_mode_slug(config.guard_modes)}_probe{config.probe_epochs}.json"
    )


def _is_complete(path: Path) -> bool:
    if not _exists(path):
        return False
    try:
        data = json.loads(_read_text(path))
    except Exception:
        return False
    return data.get("status") == "ok"


def build_jobs(config: SuiteConfig) -> list[SuiteJob]:
    jobs: list[SuiteJob] = []
    runner = Path("Scripts") / "run_skab_dynamic_llm_graph_experiment.py"
    for seed in config.seeds:
        source = _source_edges_file(config.exports_dir, int(seed))
        output = _output_file(config, int(seed))
        command = [
            sys.executable,
            str(runner),
            "--output",
            str(output),
            "--edge-policy",
            "learned_reliability",
            "--edge-probe-epochs",
            str(config.probe_epochs),
            "--edge-reliability-threshold",
            str(config.edge_reliability_threshold),
            "--edge-max-far-increase-percent",
            str(config.max_far_increase_percent),
            "--edge-counterfactual-guard-modes",
            *config.guard_modes,
            "--edge-counterfactual-min-macro-drop",
            str(config.min_macro_drop),
            "--sequence-epochs",
            str(config.sequence_epochs),
            "--sequence-hidden-dim",
            str(config.hidden_dim),
            "--sequence-batch-size",
            str(config.batch_size),
            "--seed",
            str(seed),
            "--model",
            config.model,
        ]
        if _exists(source):
            command[4:4] = ["--dynamic-edges-file", str(source)]
        jobs.append(
            SuiteJob(
                seed=int(seed),
                source_edges_file=source,
                output_file=output,
                command=command,
                is_complete=_is_complete(output),
            )
        )
    return jobs


def _fmt(value: float) -> str:
    return f"{float(value):.4f}"


def _mean_std(values: list[float]) -> str:
    if not values:
        return "n/a"
    return f"{mean(values):.4f} +/- {pstdev(values):.4f}"


def _load_result(path: Path) -> dict[str, Any] | None:
    if not _exists(path):
        return None
    try:
        data = json.loads(_read_text(path))
    except Exception:
        return None
    if data.get("status") != "ok":
        return None
    return data


def render_summary(jobs: list[SuiteJob]) -> str:
    rows: list[dict[str, Any]] = []
    for job in jobs:
        data = _load_result(job.output_file)
        if data is None:
            rows.append(
                {
                    "seed": job.seed,
                    "status": "pending",
                    "macro": None,
                    "delta": None,
                    "binary_f1": None,
                    "far": None,
                    "mar": None,
                    "input_edges": None,
                    "kept_edges": None,
                    "far_rejects": None,
                    "val_gain": None,
                    "val_rejects": None,
                    "cf_rejects": None,
                    "output": job.output_file.name,
                }
            )
            continue
        binary = data["dynamic_llm_kg"]["protocol"]["binary"]
        policy = data.get("edge_policy", {}) or {}
        rows.append(
            {
                "seed": int(data.get("seed", job.seed)),
                "status": "ok",
                "macro": float(data["dynamic_llm_kg"]["metrics"]["macro_f1"]),
                "delta": float(data.get("macro_f1_delta", 0.0)),
                "binary_f1": float(binary["f1"]),
                "far": float(binary["far_percent"]),
                "mar": float(binary["mar_percent"]),
                "input_edges": int(policy.get("n_input_edges", 0) or 0),
                "kept_edges": int(policy.get("n_kept_edges", 0) or 0),
                "far_rejects": int(policy.get("n_rejected_by_far_guard", 0) or 0),
                "val_gain": float(policy.get("validation_macro_f1_gain", 0.0) or 0.0),
                "val_rejects": int(policy.get("n_rejected_by_validation_gain_guard", 0) or 0),
                "cf_rejects": int(policy.get("n_rejected_by_counterfactual_guard", 0) or 0),
                "output": job.output_file.name,
            }
        )
    complete = [row for row in rows if row["status"] == "ok"]
    lines: list[str] = []
    lines.append("# SKAB CF-Guarded Admission Suite")
    lines.append("")
    lines.append(
        "This resume-safe suite tracks pre-admission `CF_k` guard experiments. Completed JSON outputs are "
        "skipped on rerun, so the suite can be expanded from smoke evidence to full-budget evidence gradually."
    )
    lines.append("")
    lines.append("| Seed | Status | Macro-F1 | Delta | Binary F1 | FAR | MAR | Input Edges | Kept | Val Gain | Val Rejects | FAR Rejects | CF Rejects | Output |")
    lines.append("|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    for row in rows:
        lines.append(
            "| {seed} | {status} | {macro} | {delta} | {bf1} | {far} | {mar} | {inp} | {kept} | {vgain} | {valrej} | {farrej} | {cfrej} | `{output}` |".format(
                seed=row["seed"],
                status=row["status"],
                macro="n/a" if row["macro"] is None else _fmt(row["macro"]),
                delta="n/a" if row["delta"] is None else f"{row['delta']:+.4f}",
                bf1="n/a" if row["binary_f1"] is None else _fmt(row["binary_f1"]),
                far="n/a" if row["far"] is None else f"{row['far']:.2f}",
                mar="n/a" if row["mar"] is None else f"{row['mar']:.2f}",
                inp="n/a" if row["input_edges"] is None else row["input_edges"],
                kept="n/a" if row["kept_edges"] is None else row["kept_edges"],
                vgain="n/a" if row["val_gain"] is None else f"{row['val_gain']:+.4f}",
                valrej="n/a" if row["val_rejects"] is None else row["val_rejects"],
                farrej="n/a" if row["far_rejects"] is None else row["far_rejects"],
                cfrej="n/a" if row["cf_rejects"] is None else row["cf_rejects"],
                output=row["output"],
            )
        )
    lines.append("")
    lines.append("## Aggregate")
    lines.append("")
    lines.append(f"- Completed runs: {len(complete)}/{len(rows)}")
    lines.append(f"- Macro-F1: {_mean_std([float(row['macro']) for row in complete])}")
    lines.append(f"- Delta: {_mean_std([float(row['delta']) for row in complete])}")
    lines.append(f"- Kept edges: {_mean_std([float(row['kept_edges']) for row in complete])}")
    lines.append(f"- CF rejects: {_mean_std([float(row['cf_rejects']) for row in complete])}")
    lines.append("")
    return "\n".join(lines)


def run_jobs(jobs: list[SuiteJob], *, dry_run: bool = False) -> None:
    for job in jobs:
        if job.is_complete:
            print(f"skip seed={job.seed} output={job.output_file}")
            continue
        print(" ".join(job.command))
        if dry_run:
            continue
        subprocess.run(job.command, cwd=PROJECT_ROOT, check=True)


def _parse_csv_ints(raw: str) -> tuple[int, ...]:
    return tuple(int(item.strip()) for item in str(raw).split(",") if item.strip())


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run or plan SKAB CF-guarded admission suite.")
    parser.add_argument("--exports-dir", default=str(DEFAULT_EXPORTS_DIR))
    parser.add_argument("--seeds", default="42,43,44")
    parser.add_argument("--sequence-epochs", type=int, default=8)
    parser.add_argument("--probe-epochs", type=int, default=2)
    parser.add_argument(
        "--guard-modes",
        nargs="+",
        default=["reverse_direction", "lag_shift", "random_target"],
        choices=["reverse_direction", "lag_shift", "random_target"],
    )
    parser.add_argument("--min-macro-drop", type=float, default=0.01)
    parser.add_argument("--edge-reliability-threshold", type=float, default=0.45)
    parser.add_argument("--max-far-increase-percent", type=float, default=1.0)
    parser.add_argument("--hidden-dim", type=int, default=32)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--model", default="gpt-5.5")
    parser.add_argument("--summary-output", default=str(DEFAULT_EXPORTS_DIR / "skab_cf_guarded_admission_suite.md"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args(argv)

    config = SuiteConfig(
        exports_dir=Path(args.exports_dir),
        seeds=_parse_csv_ints(args.seeds),
        sequence_epochs=int(args.sequence_epochs),
        probe_epochs=int(args.probe_epochs),
        guard_modes=tuple(str(mode) for mode in args.guard_modes),
        min_macro_drop=float(args.min_macro_drop),
        edge_reliability_threshold=float(args.edge_reliability_threshold),
        max_far_increase_percent=float(args.max_far_increase_percent),
        hidden_dim=int(args.hidden_dim),
        batch_size=int(args.batch_size),
        model=str(args.model),
    )
    jobs = build_jobs(config)
    if args.run or args.dry_run:
        run_jobs(jobs, dry_run=bool(args.dry_run and not args.run))
    report = render_summary(build_jobs(config))
    output = Path(args.summary_output)
    os.makedirs(_fs_path(output.parent), exist_ok=True)
    _write_text(output, report)
    print(report)


if __name__ == "__main__":
    main()
