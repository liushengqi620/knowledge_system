from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).absolute().parents[1]
DEFAULT_RAW_DIR = REPO_ROOT / "knowledge_exports" / "public_datasets" / "cmapss" / "raw" / "extracted"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "knowledge_exports" / "aaai_exact_native_protocol_gate"
DEFAULT_RUNNER = REPO_ROOT / "Scripts" / "run_cmapss_mdfa_source_matched.py"
VERSION = "cmapss-mdfa-source-profile-v1"
SUBSETS = ["FD001", "FD002", "FD003", "FD004"]
MDFA_TABLE4_KEY_SENSORS = [
    {"source_code": "Ps30", "local_sensor": "s11", "sensor_id": 11, "description": "Static pressure at HPC outlet"},
    {"source_code": "T24", "local_sensor": "s2", "sensor_id": 2, "description": "Total temperature at LPC outlet"},
    {"source_code": "T30", "local_sensor": "s3", "sensor_id": 3, "description": "Total temperature at HPC outlet"},
    {"source_code": "P30", "local_sensor": "s7", "sensor_id": 7, "description": "Total pressure at HPC outlet"},
    {
        "source_code": "Phi",
        "local_sensor": "s12",
        "sensor_id": 12,
        "description": "Fuel flow to high-pressure compressor static pressure ratio",
    },
    {"source_code": "Nf", "local_sensor": "s8", "sensor_id": 8, "description": "Physical fan speed"},
    {"source_code": "Nc", "local_sensor": "s9", "sensor_id": 9, "description": "Physical core speed"},
    {"source_code": "W31", "local_sensor": "s20", "sensor_id": 20, "description": "HPT coolant bleed"},
    {"source_code": "W32", "local_sensor": "s21", "sensor_id": 21, "description": "LPT coolant bleed"},
]


MDFA_SOURCE = {
    "id": "mdfa_2025",
    "title": "Remaining Useful Life Prediction for Aero-Engines Based on Multi-Scale Dilated Fusion Attention Model",
    "url": "https://www.mdpi.com/2076-3417/15/17/9813",
    "doi": "https://doi.org/10.3390/app15179813",
    "published_table_counts": {
        "FD001": {"train_units": 100, "test_units": 100, "operating_conditions": 1, "fault_modes": 1},
        "FD002": {"train_units": 260, "test_units": 259, "operating_conditions": 6, "fault_modes": 1},
        "FD003": {"train_units": 100, "test_units": 100, "operating_conditions": 1, "fault_modes": 2},
        "FD004": {"train_units": 249, "test_units": 248, "operating_conditions": 6, "fault_modes": 2},
    },
    "published_hyperparameters": {
        "batch_size": 32,
        "window_size": 30,
        "epochs": 100,
        "optimizer": "Adam",
        "loss": "MSE",
        "learning_rate": 0.0001,
        "dropout": 0.3,
    },
    "published_architecture": {
        "model_family": "multi-scale dilated fusion attention",
        "dilation_rates": [1, 2, 4],
        "kernel_size": "3x3",
        "conv_formulation": "source_2d_time_feature",
        "attention": ["channel_attention", "spatial_attention"],
        "fusion": "four branches concatenated then compressed with 1x1 convolution",
    },
    "published_metrics": ["RMSE", "Score"],
    "published_mdfa_results": {
        "FD001": {"rmse": 11.78, "score": 299.08},
        "FD002": {"rmse": 16.38, "score": 1380.65},
        "FD003": {"rmse": 11.89, "score": 303.34},
        "FD004": {"rmse": 19.23, "score": 3566.44},
    },
    "published_preprocessing_claims": [
        "Piecewise linear RUL labeling is used.",
        "The initial RUL is set to 125 cycles.",
        "PCA is used to transform correlated variables into orthogonal principal components.",
        "Optimal component count is selected by cumulative contribution rate.",
        "Key sensor variables are reported in the source table.",
    ],
    "published_rul_label_policy": {
        "piecewise_linear_rul": True,
        "initial_rul": 125,
        "test_scoring_cap_policy": "not_explicitly_machine_readable",
    },
    "published_table4_key_sensors": MDFA_TABLE4_KEY_SENSORS,
}


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    os.makedirs(_fs_path(path.parent), exist_ok=True)
    with open(_fs_path(path), "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def _write_text(path: Path, text: str) -> None:
    os.makedirs(_fs_path(path.parent), exist_ok=True)
    with open(_fs_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def _read_text(path: Path) -> str:
    with open(_fs_path(path), "r", encoding="utf-8", errors="replace") as handle:
        return handle.read()


def _data_file(raw_dir: Path, prefix: str, subset: str) -> Path:
    return raw_dir / f"{prefix}_{subset}.txt"


def _count_data_file(path: Path) -> dict[str, Any]:
    if not os.path.exists(_fs_path(path)):
        return {"present": False, "rows": 0, "unique_units": 0, "columns": 0, "max_cycle": None}
    rows = 0
    unique_units: set[int] = set()
    columns = 0
    max_cycle: int | None = None
    with open(_fs_path(path), "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            parts = [part for part in line.strip().split() if part]
            if not parts:
                continue
            rows += 1
            columns = max(columns, len(parts))
            try:
                unique_units.add(int(float(parts[0])))
            except ValueError:
                pass
            if len(parts) > 1:
                try:
                    cycle = int(float(parts[1]))
                    max_cycle = cycle if max_cycle is None else max(max_cycle, cycle)
                except ValueError:
                    pass
    return {
        "present": True,
        "rows": int(rows),
        "unique_units": int(len(unique_units)),
        "columns": int(columns),
        "max_cycle": max_cycle,
    }


def _count_rul_file(path: Path) -> dict[str, Any]:
    if not os.path.exists(_fs_path(path)):
        return {"present": False, "rows": 0}
    rows = 0
    with open(_fs_path(path), "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                rows += 1
    return {"present": True, "rows": int(rows)}


def _parse_readme_counts(readme_path: Path) -> dict[str, dict[str, int]]:
    if not os.path.exists(_fs_path(readme_path)):
        return {}
    text = _read_text(readme_path)
    rows: dict[str, dict[str, int]] = {}
    for subset in SUBSETS:
        section_match = re.search(
            rf"Data Set:\s*{subset}(.*?)(?=Data Set:\s*FD\d{{3}}|Experimental Scenario|\Z)",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            continue
        section = section_match.group(1)
        train_match = re.search(r"Train\s+\w+:\s*(\d+)", section, flags=re.IGNORECASE)
        test_match = re.search(r"Test\s+\w+:\s*(\d+)", section, flags=re.IGNORECASE)
        conditions_match = re.search(r"Conditions:\s*(\w+)", section, flags=re.IGNORECASE)
        fault_match = re.search(r"Fault Modes:\s*(\w+)", section, flags=re.IGNORECASE)
        row: dict[str, int] = {}
        if train_match:
            row["train_units"] = int(train_match.group(1))
        if test_match:
            row["test_units"] = int(test_match.group(1))
        if conditions_match:
            token = conditions_match.group(1).upper()
            row["operating_conditions"] = {"ONE": 1, "SIX": 6}.get(token, int(token) if token.isdigit() else 0)
        if fault_match:
            token = fault_match.group(1).upper()
            row["fault_modes"] = {"ONE": 1, "TWO": 2}.get(token, int(token) if token.isdigit() else 0)
        rows[subset] = row
    return rows


def _local_subset_counts(raw_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    readme_counts = _parse_readme_counts(raw_dir / "readme.txt")
    for subset in SUBSETS:
        train = _count_data_file(_data_file(raw_dir, "train", subset))
        test = _count_data_file(_data_file(raw_dir, "test", subset))
        rul = _count_rul_file(_data_file(raw_dir, "RUL", subset))
        mdfa_counts = MDFA_SOURCE["published_table_counts"][subset]
        readme_row = readme_counts.get(subset, {})
        rows.append(
            {
                "subset": subset,
                "local_train_rows": train["rows"],
                "local_test_rows": test["rows"],
                "local_train_units": train["unique_units"],
                "local_test_units": test["unique_units"],
                "local_rul_rows": rul["rows"],
                "columns_train": train["columns"],
                "columns_test": test["columns"],
                "local_max_train_cycle": train["max_cycle"],
                "local_max_test_cycle": test["max_cycle"],
                "mdfa_train_units": mdfa_counts["train_units"],
                "mdfa_test_units": mdfa_counts["test_units"],
                "readme_train_units": readme_row.get("train_units"),
                "readme_test_units": readme_row.get("test_units"),
                "counts_match_mdfa": bool(
                    train["unique_units"] == mdfa_counts["train_units"]
                    and test["unique_units"] == mdfa_counts["test_units"]
                    and rul["rows"] == mdfa_counts["test_units"]
                ),
                "counts_match_readme": bool(
                    train["unique_units"] == readme_row.get("train_units")
                    and test["unique_units"] == readme_row.get("test_units")
                ),
                "rul_rows_match_test_units": bool(rul["rows"] == test["unique_units"]),
                "raw_files_present": bool(train["present"] and test["present"] and rul["present"]),
            }
        )
    return rows


def build_cmapss_mdfa_source_profile(raw_dir: Path = DEFAULT_RAW_DIR) -> dict[str, Any]:
    raw_dir = Path(raw_dir)
    local_counts = _local_subset_counts(raw_dir)
    gates = {
        "open_fulltext_protocol_available": True,
        "mdfa_hyperparameters_extracted": True,
        "mdfa_architecture_fields_extracted": True,
        "mdfa_piecewise_rul_cap_machine_readable": True,
        "mdfa_table4_key_sensors_machine_readable": True,
        "local_raw_files_present": bool(local_counts) and all(row["raw_files_present"] for row in local_counts),
        "local_unit_counts_match_mdfa_table": bool(local_counts) and all(row["counts_match_mdfa"] for row in local_counts),
        "local_rul_rows_match_test_units": bool(local_counts) and all(row["rul_rows_match_test_units"] for row in local_counts),
        "readme_counts_match_local_files": bool(local_counts) and all(row["counts_match_readme"] for row in local_counts),
        "exact_pca_preprocessing_machine_readable": False,
        "exact_test_label_policy_machine_readable": False,
        "source_matched_runner_code_present": os.path.exists(_fs_path(DEFAULT_RUNNER)),
        "full_source_matched_prediction_archive_present": False,
        "safe_to_promote_mdfa_to_exact_reproduction": False,
    }
    missing = [name for name, value in gates.items() if not value]
    return {
        "version": VERSION,
        "status": "source_profile_count_reconciled_runner_pending",
        "claim_boundary": (
            "MDFA 2025 is now a concrete open-source-profile target for C-MAPSS. The local raw files match "
            "the MDFA FD001-FD004 unit-count table, while the bundled readme has an FD004 count inconsistency. "
            "This profile does not prove an exact reproduction until PCA/key-sensor preprocessing, the runner, "
            "matched budget, and seed-level predictions are materialized."
        ),
        "raw_dir": str(raw_dir),
        "source": MDFA_SOURCE,
        "table4_key_sensor_mapping": MDFA_TABLE4_KEY_SENSORS,
        "local_count_reconciliation": local_counts,
        "gates": gates,
        "missing_gates": missing,
        "readme_count_inconsistencies": [
            {
                "subset": row["subset"],
                "readme_train_units": row["readme_train_units"],
                "readme_test_units": row["readme_test_units"],
                "local_train_units": row["local_train_units"],
                "local_test_units": row["local_test_units"],
                "mdfa_train_units": row["mdfa_train_units"],
                "mdfa_test_units": row["mdfa_test_units"],
            }
            for row in local_counts
            if not row["counts_match_readme"]
        ],
        "next_actions": [
            "Keep the source-matched MDFA runner fixed with source_2d time-feature input, window=30, batch=32, epochs=100, Adam, lr=0.0001, dropout=0.3, and dilation rates 1/2/4.",
            "Treat the source PCA cumulative-contribution threshold and test-label scoring policy as non-machine-readable until the original authors or supplementary code specify the exact values.",
            "Retain the machine-readable Table-4 feature policy (`mdfa_key_sensors_pca`) as a source-aligned negative/control branch, not as an exact reproduction proof.",
            "Run exact-source three-seed FD001-FD004 terminal RUL only if the missing PCA threshold and preprocessing policy are resolved.",
            "Report the bundled readme FD004 train/test count inconsistency, but use the raw file unique-unit counts because they match the MDFA published table and RUL line counts.",
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# C-MAPSS MDFA Source Profile",
        "",
        f"- Version: {payload['version']}",
        f"- Status: `{payload['status']}`",
        f"- Claim boundary: {payload['claim_boundary']}",
        f"- Source: [{payload['source']['title']}]({payload['source']['url']})",
        "",
        "## Gate Status",
        "",
        "| Gate | Status |",
        "|---|---|",
    ]
    for name, value in payload["gates"].items():
        lines.append(f"| {name} | {'pass' if value else 'missing'} |")

    lines.extend(
        [
            "",
            "## Count Reconciliation",
            "",
            "| Subset | Local train units | Local test units | RUL rows | MDFA train/test | Readme train/test | Match MDFA | Match readme |",
            "|---|---:|---:|---:|---|---|---|---|",
        ]
    )
    for row in payload["local_count_reconciliation"]:
        lines.append(
            "| {subset} | {local_train_units} | {local_test_units} | {local_rul_rows} | {mdfa_train_units}/{mdfa_test_units} | {readme_train_units}/{readme_test_units} | {mdfa} | {readme} |".format(
                subset=row["subset"],
                local_train_units=row["local_train_units"],
                local_test_units=row["local_test_units"],
                local_rul_rows=row["local_rul_rows"],
                mdfa_train_units=row["mdfa_train_units"],
                mdfa_test_units=row["mdfa_test_units"],
                readme_train_units=row["readme_train_units"],
                readme_test_units=row["readme_test_units"],
                mdfa="yes" if row["counts_match_mdfa"] else "no",
                readme="yes" if row["counts_match_readme"] else "no",
            )
        )
    lines.extend(
        [
            "",
            "## Table 4 Key Sensor Mapping",
            "",
            "| Source code | Local channel | Sensor id | Description |",
            "|---|---|---:|---|",
        ]
    )
    for item in payload["table4_key_sensor_mapping"]:
        lines.append(
            "| {code} | {channel} | {sensor_id} | {description} |".format(
                code=item["source_code"],
                channel=item["local_sensor"],
                sensor_id=int(item["sensor_id"]),
                description=item["description"],
            )
        )

    hyper = payload["source"]["published_hyperparameters"]
    arch = payload["source"]["published_architecture"]
    lines.extend(
        [
            "",
            "## Extracted Protocol Fields",
            "",
            f"- Window/budget: window={hyper['window_size']}, batch={hyper['batch_size']}, epochs={hyper['epochs']}, optimizer={hyper['optimizer']}, lr={hyper['learning_rate']}, dropout={hyper['dropout']}.",
            f"- Architecture: {arch['model_family']} with {arch['conv_formulation']}, dilation rates {', '.join(str(v) for v in arch['dilation_rates'])}, kernel={arch['kernel_size']}, attention={', '.join(arch['attention'])}.",
            f"- Metrics: {', '.join(payload['source']['published_metrics'])}.",
            "",
            "## Next Actions",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in payload["next_actions"])
    return "\n".join(lines).rstrip() + "\n"


def write_cmapss_mdfa_source_profile(output_dir: Path | str = DEFAULT_OUTPUT_DIR, raw_dir: Path | str = DEFAULT_RAW_DIR) -> list[Path]:
    output_dir = Path(output_dir)
    payload = build_cmapss_mdfa_source_profile(Path(raw_dir))
    json_path = output_dir / "cmapss_mdfa_source_profile.json"
    md_path = output_dir / "cmapss_mdfa_source_profile.md"
    _write_json(json_path, payload)
    _write_text(md_path, render_markdown(payload))
    return [json_path, md_path]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Write C-MAPSS MDFA source profile and raw-count reconciliation.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    args = parser.parse_args(argv)
    for path in write_cmapss_mdfa_source_profile(args.output_dir, args.raw_dir):
        print(path)


if __name__ == "__main__":
    main()
