from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "knowledge_exports" / "aaai_exact_native_protocol_gate"
DEFAULT_CONTRACT = DEFAULT_OUTPUT_DIR / "cmapss_published_baseline_contract.json"
DEFAULT_LSTM_RUN_DIR = REPO_ROOT / "knowledge_exports" / "cmapss_lstm_published_style_w80_cap125" / "lstm_sequence"
VERSION = "cmapss-lstm-source-protocol-audit-v1"

REQUIRED_EXACT_FIELDS = [
    "subset_scope",
    "sensor_selection",
    "normalization_scope",
    "rul_label_policy",
    "sequence_window",
    "architecture_config",
    "training_budget",
    "optimizer",
    "learning_rate",
    "epochs",
    "batch_size",
    "validation_policy",
    "seed_policy",
    "metric_formula",
    "published_subset_table",
]

SOURCE_ACCESS_RECORDS = [
    {
        "id": "ieee_lstm_2017_record",
        "url": "https://doi.org/10.1109/ICPHM.2017.7998311",
        "source_type": "primary_metadata",
        "status": "metadata_available_protocol_fields_insufficient",
        "usable_for_exact_reproduction": False,
        "notes": "DOI/IEEE identity is sufficient for citation and source targeting, not for exact preprocessing or training-budget reproduction.",
    },
    {
        "id": "ieee_lstm_2017_pdf",
        "url": "https://ieeexplore.ieee.org/iel7/7990620/7998291/07998311.pdf",
        "source_type": "primary_fulltext",
        "status": "not_available_in_current_environment",
        "usable_for_exact_reproduction": False,
        "notes": "The current environment could not retrieve the IEEE full text, so exact protocol fields are not treated as verified.",
    },
    {
        "id": "nasa_cmapss_data",
        "url": "https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data",
        "source_type": "official_dataset",
        "status": "available",
        "usable_for_exact_reproduction": True,
        "notes": "Provides the native C-MAPSS split, terminal test-unit RUL objective, subset counts, and column layout.",
    },
]


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _read_json(path: Path) -> dict[str, Any]:
    with open(_fs_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    os.makedirs(_fs_path(path.parent), exist_ok=True)
    with open(_fs_path(path), "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def _write_text(path: Path, text: str) -> None:
    os.makedirs(_fs_path(path.parent), exist_ok=True)
    with open(_fs_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def _result_files(run_dir: Path) -> list[Path]:
    if not os.path.isdir(_fs_path(run_dir)):
        return []
    return sorted(Path(path) for path in Path(run_dir).glob("cmapss_rul_lstm_sequence_seed*.json"))


def _mean(values: Iterable[float]) -> float | None:
    vals = [float(value) for value in values]
    return sum(vals) / len(vals) if vals else None


def _local_lstm_summary(run_dir: Path) -> dict[str, Any]:
    files = _result_files(run_dir)
    rows: list[dict[str, Any]] = []
    for path in files:
        payload = _read_json(path)
        diag = payload.get("baseline_diagnostics") if isinstance(payload.get("baseline_diagnostics"), dict) else {}
        metrics = payload.get("primary_test_metrics") if isinstance(payload.get("primary_test_metrics"), dict) else {}
        subset_rows = (payload.get("rul_subset_metrics") or {}).get("rows", [])
        rows.append(
            {
                "path": str(path),
                "seed": int(payload.get("seed", -1)),
                "window_size": int(payload.get("window_size", 0) or 0),
                "rul_cap": float(payload.get("rul_cap", 0.0) or 0.0),
                "epochs": int(diag.get("epochs", 0) or 0),
                "batch_size": int(diag.get("batch_size", 0) or 0),
                "learning_rate": float(diag.get("learning_rate", 0.0) or 0.0),
                "hidden_dim": int(diag.get("hidden_dim", 0) or 0),
                "layers": int(diag.get("layers", 0) or 0),
                "dropout": float(diag.get("dropout", 0.0) or 0.0),
                "parameters": int(diag.get("parameters", 0) or 0),
                "device": str(diag.get("device")),
                "rmse": float(metrics.get("rul_rmse", 0.0) or 0.0),
                "score": float(metrics.get("rul_score", 0.0) or 0.0),
                "subset_rows": int(len(subset_rows or [])),
            }
        )
    config_keys = ["window_size", "rul_cap", "epochs", "batch_size", "learning_rate", "hidden_dim", "layers", "dropout"]
    unique_config = {key: sorted({row[key] for row in rows}) for key in config_keys}
    return {
        "run_dir": str(run_dir),
        "n_seed_files": int(len(rows)),
        "seeds": sorted({row["seed"] for row in rows}),
        "unique_config": unique_config,
        "rmse_mean": _mean(row["rmse"] for row in rows),
        "score_mean": _mean(row["score"] for row in rows),
        "rows": rows,
    }


def _contract_lstm_row(contract: dict[str, Any]) -> dict[str, Any] | None:
    rows = contract.get("baseline_contracts")
    if not isinstance(rows, list):
        return None
    for row in rows:
        if row.get("id") == "lstm_rul_2017":
            return row
    return None


def build_cmapss_lstm_source_protocol_audit(
    contract_path: Path = DEFAULT_CONTRACT,
    lstm_run_dir: Path = DEFAULT_LSTM_RUN_DIR,
) -> dict[str, Any]:
    contract = _read_json(Path(contract_path)) if os.path.exists(_fs_path(contract_path)) else {}
    lstm_contract = _contract_lstm_row(contract) or {}
    local_summary = _local_lstm_summary(Path(lstm_run_dir))
    verified_source_fields = {
        "subset_scope": "official_dataset_and_local_archive_cover_fd001_fd004",
        "metric_formula": "local_rul_metrics_recomputed_from_prediction_records",
    }
    unverified_source_fields = [field for field in REQUIRED_EXACT_FIELDS if field not in verified_source_fields]
    gates = {
        "primary_source_identity_verified": True,
        "official_dataset_protocol_verified": True,
        "local_lstm_seed_archive_present": local_summary["n_seed_files"] >= 3,
        "local_config_extracted": bool(local_summary["rows"]),
        "paper_fulltext_protocol_available": False,
        "all_required_source_fields_verified": False,
        "safe_to_promote_lstm_to_exact_reproduction": False,
    }
    return {
        "version": VERSION,
        "status": "source_protocol_incomplete_local_config_extracted",
        "claim_boundary": (
            "The local LSTM sequence branch is a reproducible published-style candidate, but the 2017 LSTM paper "
            "cannot be promoted to an exact reproduced baseline until the primary full-text protocol fields are available "
            "and all required fields are matched."
        ),
        "source_access_records": SOURCE_ACCESS_RECORDS,
        "required_exact_fields": REQUIRED_EXACT_FIELDS,
        "verified_source_fields": verified_source_fields,
        "unverified_source_fields": unverified_source_fields,
        "local_lstm_summary": local_summary,
        "contract_lstm_status": {
            "local_seed_archives_present": bool(lstm_contract.get("local_seed_archives_present")),
            "local_scope_covers_required": bool(lstm_contract.get("local_scope_covers_required")),
            "exact_reproduction_status": lstm_contract.get("exact_reproduction_status"),
            "field_status": lstm_contract.get("field_status"),
        },
        "gates": gates,
        "missing_gates": [name for name, value in gates.items() if not value],
        "next_actions": [
            "Obtain the IEEE-authorized full text or author-provided official manuscript for Zheng et al. 2017.",
            "Extract exact sensor selection, normalization, RUL cap, sequence length, architecture, optimizer, epochs, batch size, validation, and seed policy.",
            "Add a source-matched LSTM runner profile only after those fields are extracted; keep the current local LSTM as published-style evidence until then.",
            "After running the source-matched profile, archive per-test-engine predictions and recompute FD001-FD004 subset RMSE/score before flipping the published-baseline gate.",
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# C-MAPSS LSTM Source Protocol Audit",
        "",
        f"- Version: {payload['version']}",
        f"- Status: `{payload['status']}`",
        f"- Claim boundary: {payload['claim_boundary']}",
        "",
        "## Gate Status",
        "",
        "| Gate | Status |",
        "|---|---|",
    ]
    for name, value in payload["gates"].items():
        lines.append(f"| {name} | {'pass' if value else 'missing'} |")
    lines.extend(["", "## Source Access", "", "| Source | Type | Status | Exact use |", "|---|---|---|---|"])
    for row in payload["source_access_records"]:
        exact_use = "yes" if row["usable_for_exact_reproduction"] else "no"
        lines.append(f"| [{row['id']}]({row['url']}) | {row['source_type']} | {row['status']} | {exact_use} |")
    lines.extend(["", "## Local LSTM Candidate", ""])
    local = payload["local_lstm_summary"]
    lines.append(f"- Seed files: {local['n_seed_files']}")
    lines.append(f"- Seeds: {', '.join(str(seed) for seed in local['seeds']) or '-'}")
    lines.append(f"- Mean RMSE: {float(local['rmse_mean'] or 0.0):.4f}")
    lines.append(f"- Mean score: {float(local['score_mean'] or 0.0):.2f}")
    lines.append(f"- Unique config: `{json.dumps(local['unique_config'], sort_keys=True)}`")
    lines.extend(["", "## Unverified Source Fields", ""])
    lines.extend(f"- {field}" for field in payload["unverified_source_fields"])
    lines.extend(["", "## Next Actions", ""])
    lines.extend(f"- {item}" for item in payload["next_actions"])
    return "\n".join(lines).rstrip() + "\n"


def write_cmapss_lstm_source_protocol_audit(output_dir: Path | str = DEFAULT_OUTPUT_DIR) -> list[Path]:
    output_dir = Path(output_dir)
    payload = build_cmapss_lstm_source_protocol_audit(output_dir / "cmapss_published_baseline_contract.json")
    json_path = output_dir / "cmapss_lstm_source_protocol_audit.json"
    md_path = output_dir / "cmapss_lstm_source_protocol_audit.md"
    _write_json(json_path, payload)
    _write_text(md_path, render_markdown(payload))
    return [json_path, md_path]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Write C-MAPSS LSTM source protocol audit.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    for path in write_cmapss_lstm_source_protocol_audit(args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
