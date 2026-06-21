"""Audit recovered RAG experiment readiness.

This script reports which experiment tracks are runnable, partially runnable,
or blocked by missing datasets, adapters, or recovered source files. It is
intended to prevent paper tables from silently mixing completed, placeholder,
and planned results.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CORE_FILES = [
    ("prompt_diagnostic", "experiments/prompt_atom_decomposition_experiment.py", True),
    ("prompt_result_runner", "experiments/run_atom_decomposition_result_experiment.py", True),
    ("prompt_ablation_pipeline", "experiments/prompt_engineering_ablation.py", True),
    ("plm_matrix", "experiments/extended_plm_baselines.py", True),
    ("local_plm_train_adapter", "experiments/run_local_plm_baseline.py", True),
    ("local_plm_test_evaluator", "experiments/evaluate_local_plm_baseline.py", True),
    ("external_adapter_template", "experiments/plm_external_adapters.template.json", True),
]

DEFAULT_DATASETS = [
    (
        "continuous_casting",
        [
            "data/continuous_casting.json",
            "data/continuous_casting/ner_re_train_data_continuous_casting.json",
            "data/连铸原始语料/ner_re_train_data_continuous_casting.json",
            "data/杩為摳鍘熷璇枡/ner_re_train_data_continuous_casting.json",
        ],
    ),
    (
        "electrochemistry",
        [
            "data/electrochemistry.jsonl",
            "data/raw_corpus/Structured_dataset.jsonl",
        ],
    ),
    (
        "baosteel_quality_traceability",
        [
            "data/baosteel_knowledge_extraction/records.jsonl",
            "data/baosteel_knowledge_extraction/plm/baosteel_plm_train_pool.json",
        ],
    ),
]

LOCAL_TRAINING_MODULES = [
    (
        "advanced_ner_training_module",
        [
            "scripts/训练脚本/train_advanced_ner.py",
            "scripts/璁粌鑴氭湰/train_advanced_ner.py",
        ],
    ),
    (
        "relation_extraction_training_module",
        [
            "scripts/训练脚本/train_re.py",
            "scripts/璁粌鑴氭湰/train_re.py",
        ],
    ),
]


@dataclass(frozen=True)
class StatusItem:
    area: str
    name: str
    status: str
    path: str
    note: str


def _exists_any(root: Path, rel_paths: Iterable[str]) -> tuple[bool, str]:
    for rel in rel_paths:
        path = root / rel
        if path.exists():
            return True, rel
    return False, next(iter(rel_paths), "")


def inspect_core_files(root: Path) -> List[StatusItem]:
    rows: List[StatusItem] = []
    for name, rel, required in CORE_FILES:
        path = root / rel
        exists = path.exists()
        rows.append(
            StatusItem(
                area="core_file",
                name=name,
                status="ready" if exists else ("missing_required" if required else "missing_optional"),
                path=rel,
                note="found" if exists else "not found in recovered package",
            )
        )
    return rows


def inspect_datasets(root: Path) -> List[StatusItem]:
    rows: List[StatusItem] = []
    for name, candidates in DEFAULT_DATASETS:
        exists, rel = _exists_any(root, candidates)
        rows.append(
            StatusItem(
                area="dataset",
                name=name,
                status="ready" if exists else "missing",
                path=rel,
                note="found candidate dataset" if exists else "provide dataset or pass source override before PLM runs",
            )
        )
    return rows


def inspect_local_training_modules(root: Path) -> List[StatusItem]:
    rows: List[StatusItem] = []
    for name, candidates in LOCAL_TRAINING_MODULES:
        exists, rel = _exists_any(root, candidates)
        rows.append(
            StatusItem(
                area="training_module",
                name=name,
                status="ready" if exists else "missing",
                path=rel,
                note="found local training module" if exists else "required only for BERT-CRF+CasRel execution",
            )
        )
    return rows


def inspect_external_adapters(root: Path) -> List[StatusItem]:
    path = root / "experiments" / "plm_external_adapters.template.json"
    if not path.exists():
        return [
            StatusItem(
                area="external_adapter",
                name="adapter_template",
                status="missing",
                path=str(path.relative_to(root)),
                note="adapter template not found",
            )
        ]
    data = json.loads(path.read_text(encoding="utf-8"))
    rows: List[StatusItem] = []
    for model, info in sorted(data.items()):
        command = str(info.get("command") or "")
        has_placeholder_path = "path\\to" in command or "path/to" in command
        rows.append(
            StatusItem(
                area="external_adapter",
                name=model,
                status="pending" if has_placeholder_path else "configured",
                path=str(path.relative_to(root)),
                note=str(info.get("note") or ""),
            )
        )
    return rows


def inspect_existing_results(root: Path) -> List[StatusItem]:
    path = root / "outputs" / "plm_extended_baselines" / "results_template.csv"
    if not path.exists():
        return [
            StatusItem(
                area="result",
                name="plm_results_template",
                status="missing",
                path=str(path.relative_to(root)),
                note="no recovered result template",
            )
        ]
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    completed = [
        row
        for row in rows
        if row.get("ner_f1") not in (None, "")
        and row.get("re_f1") not in (None, "")
        and row.get("overall_f1") not in (None, "")
    ]
    pending = len(rows) - len(completed)
    return [
        StatusItem(
            area="result",
            name="plm_results_template",
            status="partial" if completed else "empty",
            path=str(path.relative_to(root)),
            note=f"{len(completed)} rows with metrics, {pending} rows pending",
        )
    ]


def build_status_report(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    root = root.resolve()
    items: List[StatusItem] = []
    items.extend(inspect_core_files(root))
    items.extend(inspect_datasets(root))
    items.extend(inspect_local_training_modules(root))
    items.extend(inspect_external_adapters(root))
    items.extend(inspect_existing_results(root))

    blockers = [item for item in items if item.status in {"missing_required", "missing"}]
    pending = [item for item in items if item.status in {"pending", "partial", "empty"}]
    return {
        "project_root": str(root),
        "summary": {
            "total_items": len(items),
            "blocker_count": len(blockers),
            "pending_count": len(pending),
            "ready_count": sum(1 for item in items if item.status == "ready"),
        },
        "items": [asdict(item) for item in items],
        "recommended_next_steps": recommend_next_steps(items),
    }


def recommend_next_steps(items: List[StatusItem]) -> List[str]:
    by_name = {item.name: item for item in items}
    steps: List[str] = []
    if by_name.get("continuous_casting") and by_name["continuous_casting"].status == "missing":
        steps.append("Restore or point to the continuous-casting extraction dataset.")
    if by_name.get("electrochemistry") and by_name["electrochemistry"].status == "missing":
        steps.append("Restore or point to the electrochemistry extraction dataset.")
    if by_name.get("advanced_ner_training_module") and by_name["advanced_ner_training_module"].status == "missing":
        steps.append("Restore local NER/RE training modules before running BERT-CRF+CasRel.")
    pending_adapters = [item.name for item in items if item.area == "external_adapter" and item.status == "pending"]
    if pending_adapters:
        steps.append("Replace placeholder commands for external adapters: " + ", ".join(pending_adapters) + ".")
    if not steps:
        steps.append("Run prompt diagnostics and prepare the PLM matrix as the first smoke workflow.")
    return steps


def write_report(report: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "status_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    items = report["items"]
    with (output_dir / "status_items.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["area", "name", "status", "path", "note"])
        writer.writeheader()
        writer.writerows(items)
    (output_dir / "status_report.md").write_text(render_markdown(report), encoding="utf-8")


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# RAG Experiment Status",
        "",
        f"Project root: `{report['project_root']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Items", "", "| Area | Name | Status | Note |", "|---|---|---|---|"])
    for item in report["items"]:
        lines.append(f"| {item['area']} | `{item['name']}` | {item['status']} | {item['note']} |")
    lines.extend(["", "## Recommended Next Steps", ""])
    for step in report["recommended_next_steps"]:
        lines.append(f"- {step}")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit recovered RAG experiment readiness.")
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs" / "experiment_status")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_status_report(args.project_root)
    write_report(report, args.output_dir)
    print(json.dumps(report["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
