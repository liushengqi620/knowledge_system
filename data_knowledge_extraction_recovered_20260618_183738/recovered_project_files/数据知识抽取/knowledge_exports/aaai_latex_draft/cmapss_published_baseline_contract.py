from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "knowledge_exports" / "aaai_exact_native_protocol_gate"
DEFAULT_ALIGNMENT_ARTIFACT = DEFAULT_OUTPUT_DIR / "cmapss_published_baseline_alignment.json"
DEFAULT_NATIVE_MANIFEST = DEFAULT_OUTPUT_DIR / "cmapss_native_preprocessing_manifest.json"
VERSION = "cmapss-published-baseline-contract-v1"

REQUIRED_REPRODUCTION_FIELDS = [
    {
        "id": "official_data_split",
        "description": "NASA FD001-FD004 train files, test files, and terminal RUL files are used without regrouping test engines.",
    },
    {
        "id": "subset_scope",
        "description": "The compared baseline declares exactly which FD subsets are evaluated, and all reported tables use the same subset scope.",
    },
    {
        "id": "rul_label_policy",
        "description": "RUL target construction is explicit, including any piecewise cap, early-life clipping, or train-unit pseudo-terminal validation policy.",
    },
    {
        "id": "sensor_selection",
        "description": "Selected operational settings and sensors are listed; dropped constant or non-informative channels are reproducible.",
    },
    {
        "id": "normalization_scope",
        "description": "Scaler, regime normalizer, or filtering parameters are fit only on training data and reused for validation/test.",
    },
    {
        "id": "sequence_window",
        "description": "Window length, stride, padding/truncation, and last-cycle terminal evaluation are identical across compared methods.",
    },
    {
        "id": "architecture_config",
        "description": "Layer count, hidden/channel sizes, attention heads, kernels, dropout, and parameter count are declared.",
    },
    {
        "id": "training_budget",
        "description": "Epochs, batch size, optimizer, learning rate, early stopping, hardware device, and seeds are budget-matched.",
    },
    {
        "id": "metric_recompute",
        "description": "RMSE and PHM-style asymmetric RUL score are recomputed from archived per-test-engine predictions.",
    },
    {
        "id": "prediction_archive",
        "description": "Each seed stores per-test-engine prediction records with subset, unit id, true RUL, predicted RUL, and split role.",
    },
]


SOURCE_REGISTRY: list[dict[str, Any]] = [
    {
        "id": "nasa_open_data_cmapss",
        "title": "NASA CMAPSS Jet Engine Simulated Data",
        "url": "https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data",
        "source_type": "official_dataset",
        "confirmed_fields": [
            "four FD subsets",
            "train/test trajectory counts",
            "three operating settings",
            "test-set terminal RUL vector",
            "26 space-separated columns",
        ],
        "contract_use": "Authoritative native task, split, and terminal-test RUL source.",
    },
    {
        "id": "local_cmapss_readme",
        "title": "Downloaded NASA C-MAPSS readme.txt",
        "url": "knowledge_exports/public_datasets/cmapss/raw/extracted/readme.txt",
        "source_type": "local_dataset_readme",
        "confirmed_fields": [
            "FD001-FD004 trajectory counts",
            "operating-condition and fault-mode definitions",
            "terminal test RUL objective",
            "column layout",
        ],
        "contract_use": "Local checksum-level evidence that the ready data follows the NASA package description.",
    },
    {
        "id": "saxena2008_cmapss",
        "title": "Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation",
        "url": "https://doi.org/10.1109/PHM.2008.4711414",
        "source_type": "dataset_lineage_paper",
        "confirmed_fields": ["C-MAPSS simulation lineage", "PHM 2008 turbofan degradation reference"],
        "contract_use": "Dataset lineage and benchmark citation, not a neural baseline protocol.",
    },
    {
        "id": "deep_cnn_rul_2016",
        "title": "Deep convolutional neural network based regression approach for estimation of remaining useful life",
        "url": "https://doi.org/10.1007/978-3-319-32025-0_14",
        "source_type": "published_baseline_family",
        "confirmed_fields": ["CNN regression family", "temporal filters over multi-channel sensor data", "RUL regression task"],
        "contract_use": "Candidate published CNN baseline family; exact preprocessing and budget must still be reproduced.",
    },
    {
        "id": "lstm_rul_2017",
        "title": "Long Short-Term Memory Network for Remaining Useful Life estimation",
        "url": "https://doi.org/10.1109/ICPHM.2017.7998311",
        "source_type": "published_baseline_family",
        "confirmed_fields": ["LSTM sequence RUL family", "C-MAPSS benchmark use", "ICPHM 2017 source identity"],
        "contract_use": "Highest-priority exact reproduction target because a local LSTM runner already exists.",
    },
    {
        "id": "mdfa_2025",
        "title": "Remaining Useful Life Prediction for Aero-Engines Based on Multi-Scale Dilated Fusion Attention Model",
        "url": "https://www.mdpi.com/2076-3417/15/17/9813",
        "source_type": "open_fulltext_published_baseline",
        "confirmed_fields": [
            "FD001-FD004 all-subset scope",
            "window=30, batch=32, epochs=100, Adam, lr=0.0001, dropout=0.3",
            "dilation rates 1/2/4 with channel and spatial attention",
            "Table-4 key-sensor map now machine-readable",
            "RMSE and score table",
            "raw-file count reconciliation through cmapss_mdfa_source_profile",
        ],
        "contract_use": "Open full-text P0 exact-source target after PCA/key-sensor preprocessing and budget equivalence are verified.",
    },
    {
        "id": "attention_lstm_ijphm_2025",
        "title": "Remaining Useful Life Prediction Using Attention-LSTM Neural Network of Aircraft Engines",
        "url": "https://doi.org/10.36001/ijphm.2025.v16i2.4274",
        "source_type": "recent_published_reference",
        "confirmed_fields": ["FD001 and FD003 results", "RMSE and score reporting", "self-attention plus LSTM family"],
        "contract_use": "Recent high-performing subset-limited reference; useful for FD001/FD003 discussion, not FD001-FD004 all-subset proof.",
    },
    {
        "id": "fd001_change_point_cnn_lstm_2023",
        "title": "Remaining Useful Life Estimation of Turbofan Engines with Deep Learning Using Change-Point Detection Based Labeling and Feature Engineering",
        "url": "https://www.mdpi.com/2076-3417/13/21/11893",
        "source_type": "recent_protocol_reference",
        "confirmed_fields": [
            "FD001-only protocol",
            "14 selected sensors",
            "min-max scaling",
            "RMSE and score metrics",
        ],
        "contract_use": "Useful FD001 preprocessing reference; not sufficient for all-subset official SOTA wording.",
    },
]


PUBLISHED_BASELINE_CONTRACTS: list[dict[str, Any]] = [
    {
        "id": "lstm_rul_2017",
        "family": "LSTM",
        "priority": "p0_exact_reproduction_target",
        "local_counterpart_names": ["lstm_sequence"],
        "required_scope": ["FD001", "FD002", "FD003", "FD004"],
        "source_ids": ["nasa_open_data_cmapss", "lstm_rul_2017"],
        "known_not_exact_reasons": [
            "local row is published-style only",
            "exact hidden size, layer count, preprocessing, validation split, and budget are not proven to match the paper",
        ],
    },
    {
        "id": "deep_cnn_rul_2016",
        "family": "temporal CNN",
        "priority": "p1_implementation_needed",
        "local_counterpart_names": [],
        "required_scope": ["FD001", "FD002", "FD003", "FD004"],
        "source_ids": ["nasa_open_data_cmapss", "deep_cnn_rul_2016"],
        "known_not_exact_reasons": [
            "no exact local CNN reproduction artifact exists",
            "source preprocessing, windowing, and training budget are not encoded in the current runner",
        ],
    },
    {
        "id": "mdfa_2025",
        "family": "multi-scale dilated fusion attention",
        "priority": "p0_open_exact_source_target",
        "local_counterpart_names": [],
        "required_scope": ["FD001", "FD002", "FD003", "FD004"],
        "source_ids": ["nasa_open_data_cmapss", "mdfa_2025"],
        "known_not_exact_reasons": [
            "source_2d runner and local branch archives exist, but the best branch changes window/dropout/condition preprocessing relative to the MDFA table",
            "Table-4 key-sensor PCA is machine-readable but performs poorly in a short-budget probe, especially on multi-condition subsets",
            "exact cumulative-contribution threshold and budget equivalence are not yet verified against the source",
        ],
    },
    {
        "id": "attention_lstm_ijphm_2025",
        "family": "attention LSTM",
        "priority": "p1_subset_reference",
        "local_counterpart_names": [],
        "required_scope": ["FD001", "FD003"],
        "source_ids": ["nasa_open_data_cmapss", "attention_lstm_ijphm_2025"],
        "known_not_exact_reasons": [
            "published result covers FD001 and FD003, not all FD001-FD004 subsets",
            "no local attention-LSTM exact reproduction artifact exists",
        ],
    },
    {
        "id": "fd001_change_point_cnn_lstm_2023",
        "family": "change-point CNN-LSTM",
        "priority": "p2_fd001_auxiliary",
        "local_counterpart_names": [],
        "required_scope": ["FD001"],
        "source_ids": ["nasa_open_data_cmapss", "fd001_change_point_cnn_lstm_2023"],
        "known_not_exact_reasons": [
            "FD001-only study cannot prove FD001-FD004 all-subset alignment",
            "change-point label and filter details are not implemented in the current exact-native runner",
        ],
    },
]


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _read_json_if_present(path: Path) -> dict[str, Any] | None:
    if not os.path.exists(_fs_path(path)):
        return None
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


def _local_rows_by_name(alignment: dict[str, Any] | None) -> dict[str, list[dict[str, Any]]]:
    rows = alignment.get("local_protocol_rows") if alignment else []
    grouped: dict[str, list[dict[str, Any]]] = {}
    if not isinstance(rows, list):
        return grouped
    for row in rows:
        name = row.get("name")
        if name is not None:
            grouped.setdefault(str(name), []).append(row)
    return grouped


def _native_gate_pass(native_manifest: dict[str, Any] | None, gate: str) -> bool:
    gates = native_manifest.get("gates") if native_manifest else {}
    return bool(isinstance(gates, dict) and gates.get(gate))


def _contract_row(contract: dict[str, Any], rows_by_name: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    local_rows = [
        row
        for name in contract["local_counterpart_names"]
        for row in rows_by_name.get(str(name), [])
    ]
    local_seed_archives = bool(local_rows) and all(int(row.get("n_seeds") or 0) >= 3 for row in local_rows)
    local_subset_sets = [set(str(item) for item in (row.get("subsets") or [])) for row in local_rows]
    required_scope = set(str(item) for item in contract["required_scope"])
    local_scope_covers_required = bool(local_subset_sets) and any(required_scope.issubset(scope) for scope in local_subset_sets)
    field_status = {
        "official_data_split": "covered_by_native_manifest",
        "subset_scope": "covered_by_local_rows" if local_scope_covers_required else "missing_or_subset_limited",
        "rul_label_policy": "local_declared_not_source_exact",
        "sensor_selection": "missing_source_exact",
        "normalization_scope": "local_train_only_declared_not_source_exact",
        "sequence_window": "local_declared_not_source_exact" if local_rows else "missing",
        "architecture_config": "local_declared_not_source_exact" if local_rows else "missing",
        "training_budget": "missing_source_exact",
        "metric_recompute": "covered_by_local_prediction_records" if local_seed_archives else "missing",
        "prediction_archive": "covered_by_local_prediction_records" if local_seed_archives else "missing",
    }
    exact_reproduction_ready = False
    return {
        **contract,
        "local_rows": local_rows,
        "local_seed_archives_present": local_seed_archives,
        "local_scope_covers_required": local_scope_covers_required,
        "field_status": field_status,
        "exact_reproduction_ready": exact_reproduction_ready,
        "exact_reproduction_status": "not_exact_reproduction",
    }


def build_cmapss_published_baseline_contract(
    alignment_artifact: Path = DEFAULT_ALIGNMENT_ARTIFACT,
    native_manifest_path: Path = DEFAULT_NATIVE_MANIFEST,
) -> dict[str, Any]:
    alignment = _read_json_if_present(Path(alignment_artifact))
    native_manifest = _read_json_if_present(Path(native_manifest_path))
    rows_by_name = _local_rows_by_name(alignment)
    contracts = [_contract_row(item, rows_by_name) for item in PUBLISHED_BASELINE_CONTRACTS]
    exact_ready = [row for row in contracts if row["exact_reproduction_ready"]]
    gates = {
        "source_registry_present": bool(SOURCE_REGISTRY),
        "native_data_contract_present": _native_gate_pass(native_manifest, "native_fd001_fd004_split_present")
        and _native_gate_pass(native_manifest, "terminal_test_unit_records_present"),
        "field_matrix_present": bool(REQUIRED_REPRODUCTION_FIELDS) and bool(contracts),
        "local_published_style_lstm_archive_present": any(
            row["id"] == "lstm_rul_2017" and row["local_seed_archives_present"] for row in contracts
        ),
        "exact_published_reproduction_complete": bool(exact_ready),
        "matched_budget_complete": False,
        "official_or_published_baseline_protocol_pass": False,
    }
    missing_gates = [name for name, value in gates.items() if not value]
    return {
        "version": VERSION,
        "status": "contract_complete_reproduction_pending",
        "claim_boundary": (
            "This contract converts C-MAPSS published-baseline comparison into a field-by-field reproduction checklist. "
            "It does not open the official SOTA gate until a published baseline has exact source-matched preprocessing, "
            "budget, metrics, and archived predictions."
        ),
        "source_registry": SOURCE_REGISTRY,
        "required_reproduction_fields": REQUIRED_REPRODUCTION_FIELDS,
        "baseline_contracts": contracts,
        "gates": gates,
        "missing_gates": missing_gates,
        "next_reproduction_queue": [
            {
                "baseline_id": "lstm_rul_2017",
                "action": "Promote local lstm_sequence from published-style to exact reproduction by matching the paper preprocessing, sequence length, hidden/layer config, epochs, validation policy, and per-subset table.",
            },
            {
                "baseline_id": "lstm_rul_2017_source_audit",
                "action": "Use cmapss_lstm_source_protocol_audit to keep the local LSTM row blocked until primary full-text protocol fields are available and verified.",
            },
            {
                "baseline_id": "mdfa_2025",
                "action": "Use cmapss_mdfa_source_profile and the Table-4 key-sensor probe to separate exact-source reproduction from the stronger local branch before any gate flip.",
            },
            {
                "baseline_id": "deep_cnn_rul_2016",
                "action": "Implement the temporal CNN baseline only after exact sensor/window/preprocessing and training budget fields are extracted from the source paper.",
            },
            {
                "baseline_id": "attention_lstm_ijphm_2025",
                "action": "Use only as an FD001/FD003 subset reference unless a full FD001-FD004 compatible reproduction is created.",
            },
        ],
        "paper_policy": (
            "Keep C-MAPSS wording at original-task transfer evidence. Do not claim literature-wide RUL SOTA; "
            "do not compare the pooled FD001-FD004 RMSE directly against FD001-only or FD001/FD003-only references."
        ),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# C-MAPSS Published Baseline Contract",
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
    lines.extend(["", "## Source Registry", "", "| Source | Type | Contract use |", "|---|---|---|"])
    for source in payload["source_registry"]:
        lines.append(
            "| {id} | {type} | [{title}]({url}) - {use} |".format(
                id=source["id"],
                type=source["source_type"],
                title=source["title"],
                url=source["url"],
                use=source["contract_use"],
            )
        )
    lines.extend(["", "## Required Reproduction Fields", "", "| Field | Requirement |", "|---|---|"])
    for field in payload["required_reproduction_fields"]:
        lines.append(f"| {field['id']} | {field['description']} |")
    lines.extend(
        [
            "",
            "## Baseline Contracts",
            "",
            "| Baseline | Family | Priority | Required scope | Local archive | Exact status | Main blockers |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for row in payload["baseline_contracts"]:
        lines.append(
            "| {id} | {family} | {priority} | {scope} | {archive} | {status} | {blockers} |".format(
                id=row["id"],
                family=row["family"],
                priority=row["priority"],
                scope=", ".join(row["required_scope"]),
                archive="yes" if row["local_seed_archives_present"] else "no",
                status=row["exact_reproduction_status"],
                blockers=", ".join(row["known_not_exact_reasons"]),
            )
        )
    lines.extend(["", "## Next Reproduction Queue", ""])
    for item in payload["next_reproduction_queue"]:
        lines.append(f"- {item['baseline_id']}: {item['action']}")
    lines.extend(["", "## Paper Policy", "", payload["paper_policy"]])
    return "\n".join(lines).rstrip() + "\n"


def write_cmapss_published_baseline_contract(output_dir: Path | str = DEFAULT_OUTPUT_DIR) -> list[Path]:
    output_dir = Path(output_dir)
    payload = build_cmapss_published_baseline_contract(
        output_dir / "cmapss_published_baseline_alignment.json",
        output_dir / "cmapss_native_preprocessing_manifest.json",
    )
    json_path = output_dir / "cmapss_published_baseline_contract.json"
    md_path = output_dir / "cmapss_published_baseline_contract.md"
    _write_json(json_path, payload)
    _write_text(md_path, render_markdown(payload))
    return [json_path, md_path]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Write C-MAPSS published-baseline exact reproduction contract.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    for path in write_cmapss_published_baseline_contract(args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
