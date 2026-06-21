"""Fill a technical precheck copy of the traceability audit sheet.

The output is not a substitute for independent expert review. It is an
assistant-generated technical precheck for method debugging, case triage, and
paper-demo preparation.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BLIND = PROJECT_ROOT / "outputs" / "traceability_paper_evidence_pack" / "expert_audit_blind.csv"
DEFAULT_KEY = PROJECT_ROOT / "outputs" / "traceability_paper_evidence_pack" / "expert_audit_key.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "outputs" / "traceability_assistant_precheck" / "assistant_technical_audit.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def split_top3(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split(";") if item.strip()]


def score_root_cause(gold: str, predicted_top3: Sequence[str]) -> float:
    if not gold or not predicted_top3:
        return 0.0
    if predicted_top3[0] == gold:
        return 1.0
    if gold in predicted_top3:
        return 0.5
    return 0.0


def score_path(path_quality_proxy: str, trace_path: str) -> float:
    if not trace_path.strip():
        return 0.0
    try:
        quality = float(path_quality_proxy)
    except ValueError:
        quality = 0.0
    if quality >= 0.8:
        return 1.0
    if quality >= 0.4:
        return 0.5
    return 0.0


def score_action(root_score: float, path_score: float) -> float:
    if root_score >= 1.0 and path_score >= 1.0:
        return 1.0
    if root_score >= 0.5 and path_score >= 0.5:
        return 0.5
    return 0.0


def note_for(root_score: float, path_score: float, action_score: float, trace_path: str) -> str:
    parts = ["assistant technical precheck; not independent expert validation"]
    if root_score == 1.0:
        parts.append("gold weak label is top-1 prediction")
    elif root_score == 0.5:
        parts.append("gold weak label appears in top-3 but not top-1")
    else:
        parts.append("gold weak label is absent from top-3")
    if not trace_path.strip():
        parts.append("no trace path available")
    elif path_score == 1.0:
        parts.append("trace path has high proxy quality")
    elif path_score == 0.5:
        parts.append("trace path has partial proxy quality")
    else:
        parts.append("trace path has low proxy quality")
    if action_score < 1.0:
        parts.append("requires human process review before paper claim")
    return "; ".join(parts)


def fill_assistant_audit(blind_path: Path, key_path: Path, output_path: Path) -> dict[str, Any]:
    blind_rows = read_csv(blind_path)
    key_rows = {row["case_id"]: row for row in read_csv(key_path)}
    output_rows: list[dict[str, Any]] = []
    for row in blind_rows:
        key = key_rows.get(row["case_id"], {})
        predicted = split_top3(row.get("predicted_top3", ""))
        gold = key.get("gold_primary_label", "")
        root_score = score_root_cause(gold, predicted)
        path_score = score_path(row.get("path_quality_proxy", ""), row.get("trace_path", ""))
        action_score = score_action(root_score, path_score)
        output_rows.append(
            {
                "case_id": row.get("case_id", ""),
                "scenario": row.get("scenario", ""),
                "record_id": key.get("record_id", ""),
                "gold_primary_label": gold,
                "predicted_top3": row.get("predicted_top3", ""),
                "top_features": row.get("top_features", ""),
                "trace_path": row.get("trace_path", ""),
                "path_quality_proxy": row.get("path_quality_proxy", ""),
                "expert_root_cause_correct": root_score,
                "expert_path_plausible": path_score,
                "expert_action_useful": action_score,
                "reviewer_id": "assistant_technical_precheck",
                "review_type": "ai_precheck_not_expert_validation",
                "expert_notes": note_for(root_score, path_score, action_score, row.get("trace_path", "")),
            }
        )
    write_csv(output_path, output_rows)
    scored = {
        "status": "assistant_traceability_audit_filled",
        "rows": len(output_rows),
        "output": str(output_path),
        "claim_boundary": "Assistant precheck supports debugging and paper-demo preparation only. It must not be reported as independent expert validation.",
    }
    summary_path = output_path.parent / "summary.json"
    summary_path.write_text(json.dumps(scored, ensure_ascii=False, indent=2), encoding="utf-8")
    return scored


def main() -> None:
    parser = argparse.ArgumentParser(description="Fill assistant technical precheck scores for traceability audit cases.")
    parser.add_argument("--blind", type=Path, default=DEFAULT_BLIND)
    parser.add_argument("--key", type=Path, default=DEFAULT_KEY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    summary = fill_assistant_audit(args.blind, args.key, args.output)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
