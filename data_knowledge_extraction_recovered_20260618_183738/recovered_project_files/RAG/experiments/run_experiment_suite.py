"""Run or dry-run the recovered RAG experiment workflow."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, List

try:
    from experiment_status import PROJECT_ROOT, build_status_report
except ImportError:  # pragma: no cover - used when imported as experiments.*
    from experiments.experiment_status import PROJECT_ROOT, build_status_report


DEFAULT_PHASES = [
    "status",
    "research_plan",
    "prompt_diagnostic",
    "atom_result_dry_run",
]


@dataclass
class SuiteStep:
    phase: str
    command: List[str]
    status: str = "pending"
    returncode: int | None = None
    note: str = ""


def _python() -> str:
    return sys.executable or "python"


def _arg_path(path: Path) -> str:
    return path.as_posix()


def _has_default_datasets(project_root: Path) -> bool:
    report = build_status_report(project_root)
    statuses = {item["name"]: item["status"] for item in report["items"]}
    return statuses.get("continuous_casting") == "ready" and statuses.get("electrochemistry") == "ready"


def build_suite_steps(args: argparse.Namespace) -> List[SuiteStep]:
    py = _python()
    output_dir = args.output_dir
    phase_set = [phase.strip() for phase in args.phases.split(",") if phase.strip()]
    steps: List[SuiteStep] = []
    for phase in phase_set:
        if phase == "status":
            steps.append(
                SuiteStep(
                    phase=phase,
                    command=[
                        py,
                        "experiments/experiment_status.py",
                        "--output-dir",
                        _arg_path(output_dir / "status"),
                    ],
                )
            )
        elif phase == "research_plan":
            steps.append(
                SuiteStep(
                    phase=phase,
                    command=[
                        py,
                        "experiments/build_experiment_research_plan.py",
                        "--output-dir",
                        _arg_path(output_dir / "research_plan"),
                    ],
                )
            )
        elif phase == "prompt_diagnostic":
            steps.append(
                SuiteStep(
                    phase=phase,
                    command=[
                        py,
                        "experiments/prompt_atom_decomposition_experiment.py",
                        "--output-dir",
                        _arg_path(output_dir / "prompt_atom_decomposition"),
                    ],
                )
            )
        elif phase == "atom_result_dry_run":
            steps.append(
                SuiteStep(
                    phase=phase,
                    command=[
                        py,
                        "experiments/run_atom_decomposition_result_experiment.py",
                        "--dry-run",
                        "--output-root",
                        _arg_path(output_dir / "atom"),
                    ],
                )
            )
        elif phase == "atom_result_scaffold":
            steps.append(
                SuiteStep(
                    phase=phase,
                    command=[
                        py,
                        "experiments/run_atom_decomposition_result_experiment.py",
                        "--output-root",
                        "atom_scaffold",
                    ],
                )
            )
        elif phase == "plm_prepare":
            step = SuiteStep(
                phase=phase,
                command=[
                    py,
                    "experiments/extended_plm_baselines.py",
                    "--output-dir",
                    _arg_path(output_dir / "plm_extended_baselines_runs"),
                ],
            )
            if not args.force_plm_prepare and not _has_default_datasets(args.project_root):
                step.status = "skipped"
                step.note = "default datasets are missing; pass --force-plm-prepare or restore data"
            steps.append(step)
        elif phase == "tests":
            steps.append(SuiteStep(phase=phase, command=[py, "-m", "pytest", "tests"]))
        else:
            steps.append(SuiteStep(phase=phase, command=[], status="skipped", note="unknown phase"))
    return steps


def run_suite(args: argparse.Namespace) -> List[SuiteStep]:
    args.output_dir.mkdir(parents=True, exist_ok=True)
    steps = build_suite_steps(args)
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")

    for step in steps:
        if step.status == "skipped":
            write_suite_artifacts(steps, args.output_dir)
            continue
        if args.dry_run:
            step.status = "planned"
            write_suite_artifacts(steps, args.output_dir)
            continue
        completed = subprocess.run(
            step.command,
            cwd=args.project_root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        step.returncode = completed.returncode
        log_path = args.output_dir / f"{step.phase}.log"
        log_path.write_text(
            "COMMAND: "
            + " ".join(step.command)
            + "\n\nSTDOUT:\n"
            + completed.stdout
            + "\n\nSTDERR:\n"
            + completed.stderr,
            encoding="utf-8",
        )
        if completed.returncode == 0:
            step.status = "ok"
            step.note = f"log: {log_path}"
        else:
            step.status = "failed"
            step.note = f"log: {log_path}"
            write_suite_artifacts(steps, args.output_dir)
            if not args.continue_on_error:
                break
        write_suite_artifacts(steps, args.output_dir)
    return steps


def write_suite_artifacts(steps: List[SuiteStep], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = [asdict(step) for step in steps]
    (output_dir / "suite_manifest.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "suite_commands.ps1").write_text(render_commands(steps), encoding="utf-8")
    (output_dir / "suite_report.md").write_text(render_report(steps), encoding="utf-8")


def render_commands(steps: List[SuiteStep]) -> str:
    lines = ["# Generated RAG experiment suite commands", ""]
    for step in steps:
        if step.command:
            lines.append("# " + step.phase)
            lines.append(" ".join(step.command))
            lines.append("")
    return "\n".join(lines)


def render_report(steps: List[SuiteStep]) -> str:
    lines = [
        "# RAG Experiment Suite Report",
        "",
        "| Phase | Status | Return Code | Note |",
        "|---|---|---:|---|",
    ]
    for step in steps:
        code = "" if step.returncode is None else str(step.returncode)
        lines.append(f"| {step.phase} | {step.status} | {code} | {step.note} |")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run or dry-run a RAG experiment workflow.")
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs" / "experiment_suite")
    parser.add_argument("--phases", default=",".join(DEFAULT_PHASES))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--continue-on-error", action="store_true")
    parser.add_argument("--force-plm-prepare", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    steps = run_suite(args)
    print(json.dumps({"steps": len(steps), "output_dir": str(args.output_dir)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
