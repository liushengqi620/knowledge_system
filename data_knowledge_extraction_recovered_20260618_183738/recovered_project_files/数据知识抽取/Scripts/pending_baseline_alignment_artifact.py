from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(_fs_path(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _best_variant(summary: dict[str, Any]) -> dict[str, Any]:
    best_name = ""
    best_score = float("-inf")
    for name, row in summary.items():
        value = row.get("target_defect_macro_f1_mean")
        if value is None:
            continue
        score = float(value)
        if score > best_score:
            best_name = str(name)
            best_score = score
    if not best_name:
        return {"name": "", "target_defect_macro_f1_mean": None}
    out = {"name": best_name}
    out.update(summary[best_name])
    return out


def build_alignment_artifact(
    *,
    source_result: Path | str,
    output: Path | str,
    baseline: str,
    dataset: str,
    budget_status: str,
    admissibility: str,
    notes: str = "",
) -> dict[str, Any]:
    source = Path(source_result)
    if not os.path.exists(_fs_path(source)):
        raise FileNotFoundError(source)
    with open(_fs_path(source), encoding="utf-8") as handle:
        payload = json.load(handle)
    summary = payload.get("summary", {}) or {}
    artifact = {
        "artifact_type": "pending_baseline_alignment_artifact",
        "baseline": str(baseline),
        "dataset": str(dataset),
        "source_result": str(source),
        "source_sha256": _sha256(source),
        "budget_status": str(budget_status),
        "public_table_admissibility": str(admissibility),
        "exact_external_alignment_status": "pending",
        "claim_boundary": "local style evidence only; do not use as public leaderboard comparison",
        "model_name": payload.get("model_name"),
        "methods": payload.get("methods", []),
        "seeds": payload.get("seeds", []),
        "variants": [item.get("name") for item in payload.get("variants", [])],
        "summary": summary,
        "best_variant": _best_variant(summary),
        "records_count": int(len(payload.get("records", []) or payload.get("runs", []) or [])),
        "notes": str(notes),
    }
    out = Path(output)
    os.makedirs(_fs_path(out.parent), exist_ok=True)
    with open(_fs_path(out), "w", encoding="utf-8") as handle:
        handle.write(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n")
    return artifact


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build a pending-baseline alignment artifact from a local run result.")
    parser.add_argument("--source-result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--baseline", type=str, required=True)
    parser.add_argument("--dataset", type=str, required=True)
    parser.add_argument("--budget-status", type=str, default="local_probe")
    parser.add_argument("--admissibility", type=str, default="not_admissible_until_exact_external_alignment")
    parser.add_argument("--notes", type=str, default="")
    args = parser.parse_args(argv)
    build_alignment_artifact(
        source_result=args.source_result,
        output=args.output,
        baseline=args.baseline,
        dataset=args.dataset,
        budget_status=args.budget_status,
        admissibility=args.admissibility,
        notes=args.notes,
    )
    print(args.output)


if __name__ == "__main__":
    main()
