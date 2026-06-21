from __future__ import annotations

import argparse
import fnmatch
import json
import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REPORT_DIR = PROJECT_ROOT / "knowledge_exports" / "aaai_formal_public_protocol"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "knowledge_exports" / "aaai_formal_public_runs"


def _fs_path(path: Path) -> str:
    if os.name == "nt":
        resolved = str(Path(path).resolve())
        if not resolved.startswith("\\\\?\\"):
            return "\\\\?\\" + resolved
    return str(path)


def _split_seeds(value: str | Sequence[int]) -> list[int]:
    if isinstance(value, str):
        parts = [part.strip() for part in value.replace(";", ",").split(",") if part.strip()]
        return [int(part) for part in parts]
    return [int(seed) for seed in value]


def _split_names(values: Sequence[str] | None) -> list[str] | None:
    if not values:
        return None
    names: list[str] = []
    for value in values:
        for part in str(value).replace(";", ",").split(","):
            name = part.strip()
            if name:
                names.append(name)
    return names or None


@dataclass(frozen=True)
class FormalRunSpec:
    name: str
    dataset: str
    role: str
    claim_use: str
    ready_root: str
    target: str | None
    output_subdir: str
    flags: tuple[str, ...]
    expected_metric: str
    paper_status: str


def formal_run_specs(only: Sequence[str] | None = None) -> list[FormalRunSpec]:
    skab_strong = (
        "--variant",
        "full",
        "--hidden-dim",
        "64",
        "--window-size",
        "48",
        "--max-rows-per-split",
        "8000",
        "--epochs",
        "40",
        "--batch-size",
        "256",
        "--graph-top-k",
        "4",
        "--max-paths",
        "16",
        "--forecast-weight",
        "0.05",
        "--graph-weight",
        "0.02",
        "--evidence-prior-mode",
        "none",
        "--prior-strength",
        "0",
    )
    cmapss_rul = (
        "--variant",
        "full",
        "--cmapss-target",
        "rul",
        "--hidden-dim",
        "64",
        "--window-size",
        "48",
        "--max-rows-per-split",
        "12000",
        "--epochs",
        "20",
        "--batch-size",
        "256",
        "--graph-top-k",
        "4",
        "--max-paths",
        "16",
        "--forecast-weight",
        "0.10",
        "--graph-weight",
        "0.02",
        "--health-aux-weight",
        "0.20",
        "--health-rul-cap",
        "125",
        "--evidence-prior-mode",
        "none",
        "--prior-strength",
        "0",
    )
    cmapss_rul_direct_regime_tempmix = (
        "--variant",
        "full",
        "--cmapss-target",
        "rul",
        "--hidden-dim",
        "64",
        "--window-size",
        "80",
        "--max-rows-per-split",
        "12000",
        "--epochs",
        "20",
        "--batch-size",
        "256",
        "--graph-top-k",
        "4",
        "--max-paths",
        "16",
        "--forecast-weight",
        "0.10",
        "--graph-weight",
        "0.02",
        "--health-aux-weight",
        "0.20",
        "--rul-loss-weight",
        "1.0",
        "--health-rul-cap",
        "125",
        "--use-regime-prototype-residuals",
        "--regime-prototype-k",
        "6",
        "--regime-healthy-stage-max",
        "0",
        "--use-temporal-mixer",
        "--temporal-mixer-depth",
        "3",
        "--evidence-prior-mode",
        "none",
        "--prior-strength",
        "0",
    )
    cmapss_rul_direct_regime_bitempmix = (
        *cmapss_rul_direct_regime_tempmix,
        "--temporal-encoder-mode",
        "multi_scale_bidirectional",
    )
    cmapss_rul_anchorpath_bigru_cls020 = (
        *cmapss_rul_direct_regime_bitempmix,
        "--temporal-mixer-type",
        "bigru",
        "--classification-loss-weight",
        "0.20",
        "--use-rul-temporal-anchor-fusion",
        "--rul-anchor-residual-scale",
        "1.0",
        "--rul-anchor-gate-bias",
        "-1.0",
    )
    specs = [
        FormalRunSpec(
            name="skab_strong_anchor",
            dataset="skab",
            role="main SKAB anchor protocol",
            claim_use="Primary SKAB matched-protocol result if 3-seed run is complete.",
            ready_root="knowledge_exports/public_benchmark_ready",
            target=None,
            output_subdir="skab_strong_anchor_w48_e40",
            flags=skab_strong,
            expected_metric="macro_f1",
            paper_status="formal_required",
        ),
        FormalRunSpec(
            name="skab_llm_condition_candidate_gate",
            dataset="skab",
            role="LLM verifier reliability branch",
            claim_use="Use as reliability/explanation branch unless it improves 3-seed strong protocol.",
            ready_root="knowledge_exports/public_benchmark_ready_llm_live_skab",
            target=None,
            output_subdir="skab_llm_condition_candidate_gate_valadm001_w005_c010_w48_e40",
            flags=(
                *skab_strong,
                "--use-llm-expert-condition-verifier",
                "--llm-condition-verifier-target",
                "candidate_gate",
                "--llm-condition-verifier-weight",
                "0.05",
                "--llm-condition-verifier-min-data-support",
                "0.05",
                "--llm-condition-verifier-floor",
                "0.10",
                "--use-candidate-prior-admission",
                "--candidate-prior-admission-target",
                "proposal_feature",
                "--candidate-prior-admission-support-mode",
                "absolute",
                "--candidate-prior-admission-scale",
                "0.50",
                "--candidate-coverage-fraction",
                "0.10",
                "--use-llm-condition-verifier-validation-admission",
                "--llm-condition-verifier-min-val-gain",
                "0.01",
            ),
            expected_metric="macro_f1",
            paper_status="formal_required_for_llm_claim",
        ),
        FormalRunSpec(
            name="cmapss_original_rul_anchor",
            dataset="cmapss",
            role="C-MAPSS original RUL protocol",
            claim_use="C-MAPSS anchor uses original RUL regression with terminal test-unit evaluation; stage labels are auxiliary only.",
            ready_root="knowledge_exports/public_benchmark_ready",
            target="rul",
            output_subdir="cmapss_original_rul_terminal_anchor_w48_e20",
            flags=cmapss_rul,
            expected_metric="rul_rmse",
            paper_status="formal_required",
        ),
        FormalRunSpec(
            name="cmapss_rul_direct_regime_tempmix",
            dataset="cmapss",
            role="C-MAPSS RUL enhanced backbone",
            claim_use=(
                "Use as the RUL-specific branch: direct capped-RUL supervision, train-only regime residuals, "
                "longer history, and temporal mixer under terminal test-unit evaluation."
            ),
            ready_root="knowledge_exports/public_benchmark_ready",
            target="rul",
            output_subdir="cmapss_rul_direct_regime_tempmix_w80_e20",
            flags=cmapss_rul_direct_regime_tempmix,
            expected_metric="rul_rmse",
            paper_status="formal_required_for_cmapss_claim",
        ),
        FormalRunSpec(
            name="cmapss_rul_direct_regime_bitempmix",
            dataset="cmapss",
            role="C-MAPSS RUL bidirectional-window enhanced backbone",
            claim_use=(
                "Use as the strongest C-MAPSS RUL branch when reporting terminal-test original RUL: "
                "direct capped-RUL supervision, train-only regime residuals, longer history, temporal mixer, "
                "and bidirectional encoding inside the historical window."
            ),
            ready_root="knowledge_exports/public_benchmark_ready",
            target="rul",
            output_subdir="cmapss_rul_direct_regime_bitempmix_w80_e20",
            flags=cmapss_rul_direct_regime_bitempmix,
            expected_metric="rul_rmse",
            paper_status="formal_required_for_cmapss_claim",
        ),
        FormalRunSpec(
            name="cmapss_rul_anchorpath_bigru_cls020",
            dataset="cmapss",
            role="C-MAPSS RUL temporal-anchor path-residual backbone",
            claim_use=(
                "Use as the strongest C-MAPSS RUL branch if 3-seed protocol remains complete: "
                "weak derived-class supervision, BiGRU temporal anchor, and validation-selected path residual fusion."
            ),
            ready_root="knowledge_exports/public_benchmark_ready",
            target="rul",
            output_subdir="cmapss_rul_anchorpath_bigru_cls020_w80_e20",
            flags=cmapss_rul_anchorpath_bigru_cls020,
            expected_metric="rul_rmse",
            paper_status="formal_required_for_cmapss_claim",
        ),
    ]
    names = _split_names(only)
    if names is None:
        return specs
    by_name = {spec.name: spec for spec in specs}
    unknown = [name for name in names if name not in by_name]
    if unknown:
        raise ValueError(f"Unknown formal run spec(s): {', '.join(unknown)}")
    return [by_name[name] for name in names]


def build_command(
    spec: FormalRunSpec,
    *,
    seeds: str,
    output_root: Path,
    python_executable: str = "python",
    device: str = "cpu",
) -> list[str]:
    command = [
        python_executable,
        "-B",
        str(Path("Scripts") / "run_public_ms_gse_rpf_experiment.py"),
        "--ready-root",
        spec.ready_root,
        "--dataset",
        spec.dataset,
        "--seeds",
        str(seeds),
        "--output-dir",
        str(Path(output_root) / spec.output_subdir),
        "--device",
        str(device),
        *spec.flags,
    ]
    return command


def _result_candidates(spec: FormalRunSpec, output_root: Path, seeds: Sequence[int]) -> list[Path]:
    out_dir = Path(output_root) / spec.output_subdir
    target = str(spec.target or ("anomaly" if spec.dataset == "skab" else "unknown"))
    paths: list[Path] = []
    if not os.path.isdir(_fs_path(out_dir)):
        return paths
    for seed in seeds:
        pattern = f"ms_gse_rpf_{spec.dataset}_{target}_*_seed{int(seed)}.json"
        for filename in os.listdir(_fs_path(out_dir)):
            if fnmatch.fnmatch(filename, pattern):
                paths.append(out_dir / filename)
    return paths


def collect_status(spec: FormalRunSpec, output_root: Path, seeds: Sequence[int]) -> dict[str, Any]:
    paths = _result_candidates(spec, output_root, seeds)
    by_seed: dict[int, dict[str, Any]] = {}
    seed_set = set(int(item) for item in seeds)
    for path in paths:
        try:
            with open(_fs_path(path), "r", encoding="utf-8") as fh:
                payload = json.load(fh)
        except Exception:
            continue
        seed = int(payload.get("seed", -1))
        if seed not in seed_set:
            continue
        metrics = payload.get("primary_test_metrics", {})
        metric_value = None
        if isinstance(metrics, dict) and spec.expected_metric in metrics:
            metric_value = float(metrics[spec.expected_metric])
        by_seed[seed] = {
            "path": str(path),
            "status": payload.get("status", "unknown"),
            "metric": metric_value,
            "metric_name": spec.expected_metric,
        }
    missing = [int(seed) for seed in seeds if int(seed) not in by_seed]
    values = [row["metric"] for row in by_seed.values() if row.get("metric") is not None]
    mean_value = float(sum(values) / len(values)) if values else None
    return {
        "complete": not missing and len(by_seed) == len(seeds),
        "expected_seeds": [int(seed) for seed in seeds],
        "completed_seeds": sorted(by_seed),
        "missing_seeds": missing,
        "metric_name": spec.expected_metric,
        "metric_mean": mean_value,
        "runs": by_seed,
    }


def build_protocol(
    *,
    seeds: str = "42,43,44",
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    device: str = "cpu",
    python_executable: str = "python",
    only: Sequence[str] | None = None,
) -> dict[str, Any]:
    seed_values = _split_seeds(seeds)
    specs = formal_run_specs(only=only)
    rows: list[dict[str, Any]] = []
    for spec in specs:
        command = build_command(
            spec,
            seeds=seeds,
            output_root=Path(output_root),
            python_executable=python_executable,
            device=device,
        )
        rows.append(
            {
                "name": spec.name,
                "dataset": spec.dataset,
                "role": spec.role,
                "claim_use": spec.claim_use,
                "ready_root": spec.ready_root,
                "target": spec.target,
                "output_subdir": spec.output_subdir,
                "expected_metric": spec.expected_metric,
                "paper_status": spec.paper_status,
                "command": command,
                "status": collect_status(spec, Path(output_root), seed_values),
            }
        )
    return {
        "schema": "aaai_formal_public_protocol_v1",
        "seeds": seed_values,
        "device": str(device),
        "output_root": str(output_root),
        "selected_runs": [spec.name for spec in specs],
        "invariants": [
            "SKAB paper results use window_size=48, hidden_dim=64, max_paths=16, epochs=40.",
        "C-MAPSS paper results use original RUL regression with terminal test-unit evaluation as the primary task.",
            "LLM verifier branches must not add independent graph edges to the main candidate set.",
            "Smoke runs are debugging evidence only and must not be mixed into final tables.",
        ],
        "runs": rows,
    }


def render_markdown(protocol: dict[str, Any]) -> str:
    lines: list[str] = [
        "# AAAI Formal Public Benchmark Protocol",
        "",
        "This file separates formal paper runs from smoke/debug runs.",
        "",
        "## Invariants",
        "",
    ]
    lines.extend(f"- {item}" for item in protocol["invariants"])
    lines.extend(
        [
            "",
            "## Runs",
            "",
            "| Name | Dataset | Role | Metric | Status | Completed | Command |",
            "|---|---|---|---|---|---:|---|",
        ]
    )
    for row in protocol["runs"]:
        status = row["status"]
        completed = len(status["completed_seeds"])
        command = " ".join(shlex.quote(part) for part in row["command"])
        lines.append(
            f"| {row['name']} | {row['dataset']} | {row['role']} | {row['expected_metric']} | "
            f"{row['paper_status']} | {completed}/{len(protocol['seeds'])} | `{command}` |"
        )
    lines.extend(["", "## Current Status", ""])
    for row in protocol["runs"]:
        status = row["status"]
        metric = status["metric_mean"]
        metric_text = "n/a" if metric is None else f"{metric:.4f}"
        lines.append(
            f"- {row['name']}: complete={status['complete']}, missing={status['missing_seeds']}, "
            f"{status['metric_name']}_mean={metric_text}."
        )
    lines.append("")
    return "\n".join(lines)


def write_protocol(protocol: dict[str, Any], report_dir: Path) -> list[Path]:
    report_dir = Path(report_dir)
    Path(_fs_path(report_dir)).mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "aaai_formal_public_protocol.json"
    md_path = report_dir / "aaai_formal_public_protocol.md"
    with open(_fs_path(json_path), "w", encoding="utf-8") as fh:
        fh.write(json.dumps(protocol, ensure_ascii=False, indent=2) + "\n")
    with open(_fs_path(md_path), "w", encoding="utf-8") as fh:
        fh.write(render_markdown(protocol))
    return [json_path, md_path]


def execute_protocol(protocol: dict[str, Any], *, skip_complete: bool = True) -> None:
    for row in protocol["runs"]:
        if skip_complete and bool(row["status"]["complete"]):
            continue
        subprocess.run(row["command"], cwd=PROJECT_ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build or execute formal AAAI public benchmark protocol.")
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--seeds", type=str, default="42,43,44")
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--python-executable", type=str, default="python")
    parser.add_argument(
        "--only",
        action="append",
        default=None,
        help="Run only selected formal spec name(s). Accepts comma-separated values and can be repeated.",
    )
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--no-skip-complete", action="store_true")
    args = parser.parse_args()

    protocol = build_protocol(
        seeds=str(args.seeds),
        output_root=Path(args.output_root),
        device=str(args.device),
        python_executable=str(args.python_executable),
        only=_split_names(args.only),
    )
    written = write_protocol(protocol, Path(args.report_dir))
    if bool(args.execute):
        execute_protocol(protocol, skip_complete=not bool(args.no_skip_complete))
        protocol = build_protocol(
            seeds=str(args.seeds),
            output_root=Path(args.output_root),
            device=str(args.device),
            python_executable=str(args.python_executable),
            only=_split_names(args.only),
        )
        written = write_protocol(protocol, Path(args.report_dir))
    for path in written:
        print(path)


if __name__ == "__main__":
    main()
