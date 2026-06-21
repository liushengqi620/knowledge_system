from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence

from mechanism_gate_ablation_matrix import (
    PROJECT_ROOT,
    VariantSpec,
    _fs_path,
    parse_seeds,
    summarize_matrix,
    variant_has_expected_runs,
)


DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "knowledge_exports" / "ms_gse_rpf_llm_condition_ablation"


def llm_condition_variant_specs() -> list[VariantSpec]:
    algorithmic_gate = (
        "--algorithmic-edge-prior-mode",
        "edge_pool",
        "--algorithmic-edge-prior-top-k",
        "12",
        "--algorithmic-edge-prior-group-top-k",
        "3",
        "--algorithmic-edge-prior-max-lag",
        "3",
        "--algorithmic-edge-prior-strength",
        "0.05",
        "--algorithmic-edge-prior-candidate-only",
        "--candidate-coverage-fraction",
        "0.08",
        "--use-task-salience",
        "--salience-mode",
        "class",
        "--algorithmic-evidence-top-k",
        "8",
        "--use-candidate-prior-admission",
        "--candidate-prior-admission-target",
        "coverage_feature",
        "--candidate-prior-admission-support-mode",
        "relative_evidence",
        "--candidate-prior-admission-floor",
        "0.05",
        "--candidate-prior-admission-threshold",
        "0.35",
        "--candidate-prior-admission-scale",
        "0.50",
    )
    expert_candidate = (
        "--evidence-prior-mode",
        "expert",
        "--prior-strength",
        "0",
        "--external-edge-candidate-only",
        "--external-candidate-families",
        "expert",
        "--external-family-calibration-floor",
        "0.10",
        "--external-family-min-data-support",
        "0.05",
        *algorithmic_gate,
    )
    return [
        VariantSpec(
            name="a0_algorithmic_only",
            role="baseline",
            claim="Train-only algorithmic edge/path candidates without expert or LLM evidence.",
            flags=("--evidence-prior-mode", "none", "--prior-strength", "0", *algorithmic_gate),
        ),
        VariantSpec(
            name="a1_expert_candidate_gate",
            role="expert_gate_control",
            claim="Expert mechanism edges are late path candidates admitted by train-only data support.",
            flags=expert_candidate,
        ),
        VariantSpec(
            name="a2_independent_llm_candidate",
            role="negative_llm_control",
            claim="Legacy independent LLM candidate edges are admitted as late candidates; expected to be less stable.",
            flags=(
                "--evidence-prior-mode",
                "llm",
                "--prior-strength",
                "0",
                "--external-edge-candidate-only",
                "--external-candidate-families",
                "llm",
                "--external-family-calibration-floor",
                "0.10",
                "--external-family-min-data-support",
                "0.05",
                *algorithmic_gate,
            ),
        ),
        VariantSpec(
            name="a3_llm_expert_graph_correction",
            role="dynamic_correction_control",
            claim="LLM expert-graph corrections are treated as low-confidence candidate/correction metadata.",
            flags=(
                "--evidence-prior-mode",
                "expert_llm",
                "--prior-strength",
                "0",
                "--external-edge-candidate-only",
                "--external-candidate-families",
                "expert,llm",
                "--external-family-calibration-floor",
                "0.10",
                "--external-family-min-data-support",
                "0.05",
                *algorithmic_gate,
            ),
        ),
        VariantSpec(
            name="a4_llm_expert_condition_verifier",
            role="main_llm_condition_verifier",
            claim="LLM verifies existing expert edges only as condition gates over train-only algorithmic candidates.",
            flags=(
                "--evidence-prior-mode",
                "none",
                "--prior-strength",
                "0",
                *algorithmic_gate,
                "--use-llm-expert-condition-verifier",
                "--llm-condition-verifier-target",
                "candidate_gate",
                "--llm-condition-verifier-weight",
                "0.20",
                "--llm-condition-verifier-min-data-support",
                "0.05",
                "--llm-condition-verifier-floor",
                "0.10",
            ),
        ),
        VariantSpec(
            name="a5_weak_class_condition_verifier",
            role="weak_class_enhancement",
            claim="Condition verifier is paired with weak-class focused class/path evidence for low-tail robustness.",
            flags=(
                "--evidence-prior-mode",
                "none",
                "--prior-strength",
                "0",
                *algorithmic_gate,
                "--use-llm-expert-condition-verifier",
                "--llm-condition-verifier-target",
                "class_evidence",
                "--llm-condition-verifier-weight",
                "0.50",
                "--llm-condition-verifier-min-data-support",
                "0.05",
                "--llm-condition-verifier-floor",
                "0.10",
                "--use-class-conditioned-evidence",
                "--class-evidence-mode",
                "static_lag",
                "--class-evidence-max-lag",
                "3",
                "--class-evidence-lag-weight",
                "0.25",
                "--class-evidence-focus-mode",
                "low_train_separation",
                "--class-evidence-focus-k",
                "2",
                "--class-evidence-focus-nonfocus-weight",
                "0.10",
                "--class-evidence-top-k",
                "8",
            ),
        ),
    ]


def common_skab_flags(
    *,
    ready_root: Path | None,
    seeds: str,
    output_dir: Path,
    device: str,
    profile: str,
) -> list[str]:
    if profile == "smoke":
        hidden_dim = "16"
        window_size = "16"
        max_rows = "400"
        epochs = "1"
        batch_size = "128"
        graph_top_k = "4"
        max_paths = "8"
    elif profile == "quick":
        hidden_dim = "32"
        window_size = "32"
        max_rows = "2000"
        epochs = "3"
        batch_size = "256"
        graph_top_k = "6"
        max_paths = "12"
    else:
        hidden_dim = "64"
        window_size = "48"
        max_rows = "8000"
        epochs = "25"
        batch_size = "256"
        graph_top_k = "8"
        max_paths = "16"
    flags = [
        "Scripts\\run_public_ms_gse_rpf_experiment.py",
        "--dataset",
        "skab",
        "--variant",
        "full",
        "--seeds",
        str(seeds),
        "--output-dir",
        str(output_dir),
        "--device",
        str(device),
        "--hidden-dim",
        hidden_dim,
        "--window-size",
        window_size,
        "--max-rows-per-split",
        max_rows,
        "--epochs",
        epochs,
        "--batch-size",
        batch_size,
        "--graph-top-k",
        graph_top_k,
        "--max-paths",
        max_paths,
        "--forecast-weight",
        "0.05",
        "--graph-weight",
        "0.02",
        "--use-prototype-posterior-fusion",
        "--prototype-fusion-max-blend",
        "0.30",
        "--prototype-fusion-blend-steps",
        "7",
        "--prototype-fusion-temperature-grid",
        "0.25,0.50,1.00,2.00",
        "--prototype-fusion-min-val-gain",
        "0.003",
    ]
    if ready_root is not None:
        flags[1:1] = ["--ready-root", str(ready_root)]
    return flags


def build_command(
    spec: VariantSpec,
    *,
    output_root: Path,
    ready_root: Path | None = None,
    seeds: str = "42,43,44",
    device: str = "cuda",
    profile: str = "full",
    python_executable: str = "python",
) -> list[str]:
    output_dir = Path(output_root) / spec.name
    return [
        str(python_executable),
        "-B",
        *common_skab_flags(
            ready_root=ready_root,
            seeds=seeds,
            output_dir=output_dir,
            device=device,
            profile=profile,
        ),
        *spec.flags,
    ]


def render_shell_command(tokens: Sequence[str]) -> str:
    return " ".join(shlex.quote(str(token)) for token in tokens)


def render_report(
    *,
    specs: Sequence[VariantSpec],
    commands: Mapping[str, Sequence[str]],
    summary: Sequence[Mapping[str, Any]],
    output_root: Path,
    ready_root: Path | None,
) -> str:
    spec_map = {spec.name: spec for spec in specs}
    lines: list[str] = []
    lines.append("# LLM Expert-Condition Verifier Ablation Matrix")
    lines.append("")
    lines.append(
        "This protocol compares independent LLM edge candidates against the main LLM-as-condition-verifier branch. "
        "LLM verifier rows are valid evidence only when the ready graph contains verifier metadata generated from a reviewed response."
    )
    lines.append("")
    lines.append(f"- output root: `{output_root}`")
    lines.append(f"- ready root: `{ready_root or 'default public_benchmark_ready'}`")
    lines.append("- baseline: `a0_algorithmic_only`")
    lines.append("- dataset: `SKAB`")
    lines.append("")
    lines.append("## Commands")
    lines.append("")
    lines.append("| Variant | Role | Claim | Command |")
    lines.append("|---|---|---|---|")
    for spec in specs:
        lines.append(
            "| {name} | {role} | {claim} | `{cmd}` |".format(
                name=spec.name,
                role=spec.role,
                claim=spec.claim,
                cmd=render_shell_command(commands[spec.name]),
            )
        )
    lines.append("")
    lines.append("## Current Evidence")
    lines.append("")
    lines.append("| Variant | Status | Runs | Test Macro-F1 | Val gain | Test gain | Low-tail val F1 gain | Reject reasons |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---|")
    for row in summary:
        lines.append(
            "| {variant} | {status} | {runs} | {test:.4f} +/- {test_std:.4f} | {vgain:.4f} | {tgain:.4f} | {tail:.4f} | {reasons} |".format(
                variant=row.get("variant"),
                status=row.get("status"),
                runs=int(row.get("n_runs", 0)),
                test=float(row.get("test_macro_f1_mean", 0.0)),
                test_std=float(row.get("test_macro_f1_std", 0.0)),
                vgain=float(row.get("mean_val_gain_vs_baseline", 0.0)),
                tgain=float(row.get("mean_test_gain_vs_baseline", 0.0)),
                tail=float(row.get("low_tail_val_f1_gain", 0.0)),
                reasons=", ".join(str(item) for item in row.get("reject_reasons", [])) or "none",
            )
        )
    lines.append("")
    lines.append("## Interpretation Rule")
    lines.append("")
    lines.append(
        "`a4_llm_expert_condition_verifier` is the main paper branch only if it improves or stabilizes validation/test "
        "relative to `a0_algorithmic_only`, avoids low-tail harm, and is better behaved than `a2_independent_llm_candidate`."
    )
    lines.append("")
    return "\n".join(lines)


def write_outputs(output_dir: Path, payload: Mapping[str, Any], report: str) -> tuple[Path, Path]:
    os.makedirs(_fs_path(output_dir), exist_ok=True)
    json_path = output_dir / "llm_condition_verifier_ablation_matrix.json"
    md_path = output_dir / "llm_condition_verifier_ablation_matrix.md"
    with open(_fs_path(json_path), "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    with open(_fs_path(md_path), "w", encoding="utf-8") as handle:
        handle.write(report)
    return json_path, md_path


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build and optionally execute the LLM condition-verifier ablation matrix.")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--ready-root", type=Path, default=None)
    parser.add_argument("--seeds", type=str, default="42,43,44")
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--profile", choices=["smoke", "quick", "full"], default="full")
    parser.add_argument("--python", type=str, default="python")
    parser.add_argument("--execute", action="store_true", help="Run every matrix command after writing the protocol.")
    parser.add_argument("--skip-complete", action="store_true")
    parser.add_argument("--min-mean-val-gain", type=float, default=0.0)
    parser.add_argument("--max-seed-val-drop", type=float, default=0.01)
    parser.add_argument("--max-low-tail-f1-drop", type=float, default=0.02)
    parser.add_argument("--min-baseline-path-jaccard", type=float, default=0.0)
    args = parser.parse_args(list(argv) if argv is not None else None)

    specs = llm_condition_variant_specs()
    commands = {
        spec.name: build_command(
            spec,
            output_root=args.output_root,
            ready_root=args.ready_root,
            seeds=args.seeds,
            device=args.device,
            profile=args.profile,
            python_executable=args.python,
        )
        for spec in specs
    }
    expected_seeds = parse_seeds(args.seeds)
    if bool(args.execute):
        for name, tokens in commands.items():
            if bool(args.skip_complete) and variant_has_expected_runs(args.output_root, name, expected_seeds):
                print(f"[llm-condition] skipping complete variant {name}", flush=True)
                continue
            print(f"[llm-condition] running {name}: {render_shell_command(tokens)}", flush=True)
            subprocess.run(list(tokens), cwd=PROJECT_ROOT, check=True)

    summary = summarize_matrix(
        output_root=args.output_root,
        specs=specs,
        expected_seeds=expected_seeds,
        baseline_name="a0_algorithmic_only",
        min_mean_val_gain=float(args.min_mean_val_gain),
        max_seed_val_drop=float(args.max_seed_val_drop),
        max_low_tail_f1_drop=float(args.max_low_tail_f1_drop),
        min_baseline_path_jaccard=float(args.min_baseline_path_jaccard),
    )
    payload = {
        "schema": "llm_condition_verifier_ablation_matrix_v1",
        "output_root": str(args.output_root),
        "ready_root": str(args.ready_root or ""),
        "profile": str(args.profile),
        "seeds": expected_seeds,
        "commands": {name: list(tokens) for name, tokens in commands.items()},
        "variants": [spec.__dict__ for spec in specs],
        "summary": summary,
    }
    report = render_report(
        specs=specs,
        commands=commands,
        summary=summary,
        output_root=args.output_root,
        ready_root=args.ready_root,
    )
    json_path, md_path = write_outputs(args.report_dir, payload, report)
    print(report)
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
