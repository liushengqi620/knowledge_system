"""Validate rich knowledge-extraction dataset records.

This validator intentionally uses only the Python standard library so it can run
before project dependencies are installed. It checks the constraints that matter
most for NER/RE training and PLM-conditioned prompt compilation:

- stable required fields
- entity character spans match source text
- relation endpoints reference existing entities
- evidence spans are valid
- PLM/LLM candidate IDs are linkable
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class ValidationIssue:
    record_id: str
    severity: str
    field: str
    message: str


def iter_records(path: Path) -> Iterator[dict[str, Any]]:
    if path.suffix.lower() == ".jsonl":
        with path.open("r", encoding="utf-8-sig") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    yield json.loads(line)
        return
    text = path.read_text(encoding="utf-8-sig")
    data = json.loads(text)
    if isinstance(data, list):
        yield from data
        return
    if isinstance(data, dict) and "records" in data:
        yield from data["records"]
        return
    raise ValueError(f"Expected JSON list, JSON object with records, or JSONL: {path}")


def load_records(path: Path) -> List[dict[str, Any]]:
    return list(iter_records(path))


def _issue(record_id: str, severity: str, field: str, message: str) -> ValidationIssue:
    return ValidationIssue(str(record_id or "<missing>"), severity, field, message)


def _valid_span(text: str, span: dict[str, Any] | None) -> bool:
    if not isinstance(span, dict):
        return False
    start = span.get("start")
    end = span.get("end")
    return isinstance(start, int) and isinstance(end, int) and 0 <= start <= end <= len(text)


def validate_record(record: dict[str, Any]) -> List[ValidationIssue]:
    record_id = str(record.get("record_id") or "<missing>")
    issues: List[ValidationIssue] = []
    for field in ["record_id", "domain", "language", "text", "source", "task_scope", "annotation_status", "annotations"]:
        if field not in record:
            issues.append(_issue(record_id, "error", field, "missing required field"))
    text = str(record.get("text") or "")
    if not text:
        issues.append(_issue(record_id, "error", "text", "text is empty"))
        return issues

    annotations = record.get("annotations") or {}
    entities = annotations.get("entities") or []
    relations = annotations.get("relations") or []

    entity_ids: set[str] = set()
    for idx, entity in enumerate(entities):
        field = f"annotations.entities[{idx}]"
        entity_id = str(entity.get("entity_id") or "")
        if not entity_id:
            issues.append(_issue(record_id, "error", field, "entity_id is missing"))
            continue
        if entity_id in entity_ids:
            issues.append(_issue(record_id, "error", field, f"duplicate entity_id {entity_id}"))
        entity_ids.add(entity_id)

        start = entity.get("start")
        end = entity.get("end")
        surface = str(entity.get("text") or "")
        if not isinstance(start, int) or not isinstance(end, int) or not (0 <= start < end <= len(text)):
            issues.append(_issue(record_id, "error", field, "invalid entity span"))
            continue
        if text[start:end] != surface:
            issues.append(
                _issue(
                    record_id,
                    "error",
                    field,
                    f"entity text mismatch: span={text[start:end]!r}, entity.text={surface!r}",
                )
            )

    for idx, relation in enumerate(relations):
        field = f"annotations.relations[{idx}]"
        for endpoint in ["head", "tail"]:
            if relation.get(endpoint) not in entity_ids:
                issues.append(_issue(record_id, "error", field, f"{endpoint} references unknown entity"))
        if not _valid_span(text, relation.get("evidence_span")):
            issues.append(_issue(record_id, "error", field, "invalid evidence_span"))

    candidate_ids: set[str] = set()
    for idx, candidate in enumerate(record.get("plm_candidates") or []):
        field = f"plm_candidates[{idx}]"
        candidate_id = str(candidate.get("candidate_id") or "")
        if not candidate_id:
            issues.append(_issue(record_id, "error", field, "candidate_id is missing"))
            continue
        if candidate_id in candidate_ids:
            issues.append(_issue(record_id, "error", field, f"duplicate candidate_id {candidate_id}"))
        candidate_ids.add(candidate_id)
        if "evidence_window" in candidate and not _valid_span(text, candidate.get("evidence_window")):
            issues.append(_issue(record_id, "error", field, "invalid evidence_window"))

    for idx, decision in enumerate(record.get("llm_adjudications") or []):
        field = f"llm_adjudications[{idx}]"
        candidate_id = decision.get("candidate_id")
        if candidate_id not in candidate_ids:
            issues.append(_issue(record_id, "error", field, "candidate_id does not reference a PLM candidate"))
        if "evidence_span" in decision and not _valid_span(text, decision.get("evidence_span")):
            issues.append(_issue(record_id, "error", field, "invalid evidence_span"))
        if decision.get("decision") == "reject" and not decision.get("reject_reason"):
            issues.append(_issue(record_id, "warning", field, "reject decision should include reject_reason"))

    return issues


def validate_records(records: Iterable[dict[str, Any]]) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    seen: set[str] = set()
    for record in records:
        record_id = str(record.get("record_id") or "<missing>")
        if record_id in seen:
            issues.append(_issue(record_id, "error", "record_id", "duplicate record_id"))
        seen.add(record_id)
        issues.extend(validate_record(record))
    return issues


def validate_records_with_count(records: Iterable[dict[str, Any]]) -> tuple[int, List[ValidationIssue]]:
    count = 0
    issues: List[ValidationIssue] = []
    seen: set[str] = set()
    for record in records:
        count += 1
        record_id = str(record.get("record_id") or "<missing>")
        if record_id in seen:
            issues.append(_issue(record_id, "error", "record_id", "duplicate record_id"))
        seen.add(record_id)
        issues.extend(validate_record(record))
    return count, issues


def write_outputs(issues: List[ValidationIssue], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = [asdict(issue) for issue in issues]
    (output_dir / "dataset_validation_issues.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    with (output_dir / "dataset_validation_issues.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["record_id", "severity", "field", "message"])
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        "issue_count": len(issues),
        "error_count": sum(1 for issue in issues if issue.severity == "error"),
        "warning_count": sum(1 for issue in issues if issue.severity == "warning"),
    }
    (output_dir / "dataset_validation_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate rich knowledge extraction dataset records.")
    parser.add_argument("--input", type=Path, default=PROJECT_ROOT / "data" / "examples" / "continuous_casting_seed.json")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs" / "dataset_validation")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    record_count, issues = validate_records_with_count(iter_records(args.input))
    write_outputs(issues, args.output_dir)
    error_count = sum(1 for issue in issues if issue.severity == "error")
    print(json.dumps({"records": record_count, "issues": len(issues), "errors": error_count}, ensure_ascii=False))
    if error_count:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
