from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "knowledge_exports" / "aaai_exact_native_protocol_gate"
DEFAULT_NATIVE_MANIFEST = DEFAULT_OUTPUT_DIR / "cmapss_native_preprocessing_manifest.json"
DEFAULT_MATCHED_BASELINES = REPO_ROOT / "knowledge_exports" / "cmapss_rul_deep_baselines_regime_w80" / "cmapss_rul_matched_baselines_summary.json"
DEFAULT_PUBLISHED_STYLE_CANDIDATES = [
    REPO_ROOT
    / "knowledge_exports"
    / "cmapss_lstm_published_style_w80_cap125"
    / "cmapss_rul_matched_baselines_summary.json"
]
VERSION = "cmapss-published-baseline-alignment-v1"
EXPECTED_SUBSETS = {"FD001", "FD002", "FD003", "FD004"}
PUBLISHED_STYLE_REFERENCE_BY_BASELINE = {
    "lstm_sequence": "lstm_rul_2017",
}


REFERENCE_SOURCES: list[dict[str, str]] = [
    {
        "id": "nasa_open_data_cmapss",
        "title": "NASA CMAPSS Jet Engine Simulated Data",
        "url": "https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data",
        "protocol_use": "Primary data source for train/test trajectories, terminal test-unit RUL labels, three operating settings, and sensor columns.",
    },
    {
        "id": "nasa_pcoe_repository",
        "title": "NASA PCoE Turbofan Engine Degradation Simulation",
        "url": "https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/",
        "protocol_use": "Repository-level description of four C-MAPSS subsets under different operating-condition and fault-mode combinations.",
    },
    {
        "id": "saxena2008_cmapss",
        "title": "Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation",
        "url": "https://doi.org/10.1109/PHM.2008.4711414",
        "protocol_use": "Original PHM 2008 C-MAPSS simulation reference; use for dataset lineage and PHM-style RUL scoring context.",
    },
]


PUBLISHED_BASELINE_REGISTRY: list[dict[str, Any]] = [
    {
        "id": "deep_cnn_rul_2016",
        "family": "CNN regression",
        "title": "Deep convolutional neural network based regression approach for estimation of remaining useful life",
        "url": "https://doi.org/10.1007/978-3-319-32025-0_14",
        "year": 2016,
        "reported_scope": "C-MAPSS RUL baseline family; frequently cited in later FD001-FD004 comparison tables.",
        "alignment_status": "reference_only_not_reproduced",
        "blocking_fields": ["exact sensor selection", "RUL cap", "normalization scope", "training budget", "seed-level prediction archive"],
    },
    {
        "id": "lstm_rul_2017",
        "family": "LSTM sequence RUL",
        "title": "Long Short-Term Memory Network for Remaining Useful Life Estimation",
        "url": "https://doi.org/10.1109/ICPHM.2017.7998311",
        "year": 2017,
        "reported_scope": "Canonical LSTM RUL baseline family on C-MAPSS.",
        "alignment_status": "reference_only_not_reproduced",
        "blocking_fields": ["subset table reproduction", "RUL cap", "validation split", "epochs and hidden size", "seed-level prediction archive"],
    },
    {
        "id": "attention_lstm_ijphm_2025",
        "family": "attention LSTM",
        "title": "Remaining Useful Life Prediction Using Attention-LSTM Neural Networks",
        "url": "https://papers.phmsociety.org/index.php/ijphm/article/download/4274/2620",
        "year": 2025,
        "reported_scope": "Recent attention-LSTM comparison using RMSE and score on NASA C-MAPSS subsets.",
        "alignment_status": "reference_only_not_reproduced",
        "blocking_fields": ["covered FD subsets", "preprocessing equivalence", "RUL cap equivalence", "matched training budget", "seed-level prediction archive"],
    },
    {
        "id": "hierarchical_transformer_sensors_2024",
        "family": "hierarchical Transformer",
        "title": "A Two-Stage Attention-Based Hierarchical Transformer for Turbofan Engine Remaining Useful Life Prediction",
        "url": "https://www.mdpi.com/1424-8220/24/3/824",
        "year": 2024,
        "reported_scope": "Recent Transformer-style C-MAPSS RUL reference; useful as a candidate architecture/baseline family.",
        "alignment_status": "reference_only_not_reproduced",
        "blocking_fields": ["windowing", "label cap", "feature scaling", "FD001-FD004 table comparability", "training budget"],
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


def _load_optional_json(path: Path) -> dict[str, Any] | None:
    if not os.path.exists(_fs_path(path)):
        return None
    return _read_json(path)


def _branch_rows(native_manifest: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not native_manifest:
        return []
    rows = native_manifest.get("branch_summary")
    return rows if isinstance(rows, list) else []


def _matched_baseline_rows(matched_baselines: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not matched_baselines:
        return []
    rows = matched_baselines.get("overall")
    return rows if isinstance(rows, list) else []


def _subset_rows(matched_baselines: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not matched_baselines:
        return []
    rows = matched_baselines.get("subset_summary")
    return rows if isinstance(rows, list) else []


def _local_baseline_alignment(native_manifest: dict[str, Any] | None, matched_baselines: dict[str, Any] | None) -> list[dict[str, Any]]:
    branch_rows = _branch_rows(native_manifest)
    matched_rows = _matched_baseline_rows(matched_baselines)
    local_rows: list[dict[str, Any]] = []
    for row in branch_rows:
        local_rows.append(
            {
                "source": "current_proposed_or_formal_branch",
                "name": row.get("branch"),
                "n_seeds": row.get("n_seeds"),
                "subsets": row.get("subsets"),
                "rul_cap_values": row.get("rul_cap_values"),
                "window_sizes": row.get("window_sizes"),
                "rmse_mean": row.get("rmse_mean"),
                "score_mean": row.get("score_mean"),
                "alignment_status": "local_matched_protocol_seed_archive",
            }
        )
    for row in matched_rows:
        local_rows.append(
            {
                "source": "local_matched_baseline",
                "name": row.get("baseline"),
                "n_seeds": row.get("n_seeds"),
                "subsets": sorted(EXPECTED_SUBSETS),
                "rul_cap_values": [125.0],
                "window_sizes": [80],
                "rmse_mean": row.get("rmse_mean"),
                "score_mean": row.get("score_mean"),
                "alignment_status": "local_matched_protocol_not_published_reproduction",
            }
        )
    return local_rows


def _published_style_candidate_rows(candidate_summaries: list[dict[str, Any] | None]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for summary in candidate_summaries:
        if not summary:
            continue
        subset_rows = _subset_rows(summary)
        subsets_by_baseline: dict[str, set[str]] = {}
        for row in subset_rows:
            if row.get("baseline") is not None and row.get("subset") is not None:
                subsets_by_baseline.setdefault(str(row["baseline"]), set()).add(str(row["subset"]))
        for row in _matched_baseline_rows(summary):
            name = str(row.get("baseline"))
            reference_id = PUBLISHED_STYLE_REFERENCE_BY_BASELINE.get(name)
            rows.append(
                {
                    "source": "published_style_local_candidate",
                    "name": name,
                    "n_seeds": row.get("n_seeds"),
                    "subsets": sorted(subsets_by_baseline.get(name, set())),
                    "rul_cap_values": [125.0],
                    "window_sizes": [80],
                    "rmse_mean": row.get("rmse_mean"),
                    "score_mean": row.get("score_mean"),
                    "alignment_status": "published_style_seed_archive_not_exact_reproduction",
                    "published_reference_id": reference_id,
                }
            )
    return rows


def _coverage_summary(
    native_manifest: dict[str, Any] | None,
    matched_baselines: dict[str, Any] | None,
    published_style_candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    native_gates = native_manifest.get("gates", {}) if native_manifest else {}
    subset_rows = _subset_rows(matched_baselines)
    subset_coverage_by_baseline: dict[str, list[str]] = {}
    for row in subset_rows:
        name = str(row.get("baseline"))
        subset = row.get("subset")
        if subset is not None:
            subset_coverage_by_baseline.setdefault(name, []).append(str(subset))
    return {
        "native_manifest_present": bool(native_manifest),
        "native_manifest_status": native_manifest.get("status") if native_manifest else "missing",
        "native_manifest_gates": native_gates,
        "matched_baseline_summary_present": bool(matched_baselines),
        "local_matched_baselines": sorted(subset_coverage_by_baseline),
        "local_matched_baseline_subset_coverage": {key: sorted(set(value)) for key, value in subset_coverage_by_baseline.items()},
        "published_style_candidates": [
            {
                "name": row.get("name"),
                "published_reference_id": row.get("published_reference_id"),
                "n_seeds": row.get("n_seeds"),
                "subsets": row.get("subsets"),
                "alignment_status": row.get("alignment_status"),
            }
            for row in published_style_candidates
        ],
    }


def build_cmapss_published_baseline_alignment(
    native_manifest_path: Path = DEFAULT_NATIVE_MANIFEST,
    matched_baselines_path: Path = DEFAULT_MATCHED_BASELINES,
    published_style_candidate_paths: list[Path] | tuple[Path, ...] = tuple(DEFAULT_PUBLISHED_STYLE_CANDIDATES),
) -> dict[str, Any]:
    native_manifest = _load_optional_json(Path(native_manifest_path))
    matched_baselines = _load_optional_json(Path(matched_baselines_path))
    candidate_summaries = [_load_optional_json(Path(path)) for path in published_style_candidate_paths]
    published_style_candidates = _published_style_candidate_rows(candidate_summaries)
    local_rows = _local_baseline_alignment(native_manifest, matched_baselines)
    local_rows.extend(published_style_candidates)
    coverage = _coverage_summary(native_manifest, matched_baselines, published_style_candidates)
    native_gates = coverage["native_manifest_gates"]
    local_matched = [row for row in local_rows if row["source"] == "local_matched_baseline"]
    published_registry_present = bool(PUBLISHED_BASELINE_REGISTRY)
    gates = {
        "alignment_artifact_present": True,
        "native_manifest_present": bool(native_manifest),
        "local_fd001_fd004_seed_archive_present": bool(native_gates)
        and bool(native_gates.get("native_fd001_fd004_split_present"))
        and bool(native_gates.get("terminal_test_unit_records_present"))
        and bool(native_gates.get("subset_rmse_score_present")),
        "local_matched_baseline_protocol_present": bool(local_matched),
        "published_reference_registry_present": published_registry_present,
        "published_style_candidate_seed_archive_present": bool(published_style_candidates),
        "published_reproduction_seed_artifacts_present": False,
        "exact_published_preprocessing_matched": False,
        "matched_budget_present": False,
        "literature_wide_sota_admissible": False,
    }
    missing = [name for name, value in gates.items() if not value]
    return {
        "version": VERSION,
        "status": "published_baseline_alignment_partial_not_sota_proof",
        "claim_boundary": (
            "This artifact separates local matched C-MAPSS baselines from published-reference baselines. "
            "It materializes the alignment table, but does not mark any published baseline as reproduced or budget-matched."
        ),
        "reference_sources": REFERENCE_SOURCES,
        "native_protocol_contract": [
            "Use NASA FD001-FD004 train/test units and terminal test-unit RUL labels.",
            "Report subset RMSE and PHM-style asymmetric RUL score; pooled RMSE is secondary.",
            "Declare RUL cap, selected sensors, scaler/regime fit scope, window length, seeds, epochs, and validation-unit split.",
            "Treat local GRU/TCN/tabular rows as matched-protocol controls, not published paper reproductions.",
            "Treat LSTM local matched rows as published-style candidates until the exact published configuration, preprocessing, and budget are reproduced.",
            "Admit literature-wide SOTA wording only after a cited baseline has the same split, cap, preprocessing, metric, budget, and seed-level prediction archive.",
        ],
        "coverage_summary": coverage,
        "local_protocol_rows": local_rows,
        "published_reference_registry": PUBLISHED_BASELINE_REGISTRY,
        "gates": gates,
        "missing_gates": missing,
        "recommended_paper_wording": {
            "safe": "C-MAPSS supports original terminal RUL transfer under local matched FD001-FD004 controls; current path-fusion branches remain challengers unless admitted over the temporal anchor.",
            "unsafe": "C-MAPSS proves literature-wide or official RUL SOTA, or proves path-fusion benefit before validation-safe admission.",
        },
        "next_actions": [
            "Use cmapss_published_baseline_contract as the field-level checklist before promoting any published-style row into an exact published-baseline reproduction.",
            "Select at least two published C-MAPSS RUL baselines and reproduce them with identical FD001-FD004 split, RUL cap, preprocessing, and metrics.",
            "Promote the LSTM published-style candidate only after the exact LSTM paper configuration, preprocessing, epochs, hidden size, and subset table are matched.",
            "Archive per-test-engine predictions for every reproduced published baseline and compute subset RMSE/score from the frozen records.",
            "Normalize or explicitly match training budget: window length, epochs, batch size, hidden size, seeds, and train/validation unit split.",
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# C-MAPSS Published Baseline Alignment",
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
    lines.extend(["", "## Reference Sources", "", "| ID | Source | Protocol use |", "|---|---|---|"])
    for ref in payload["reference_sources"]:
        lines.append(f"| {ref['id']} | [{ref['title']}]({ref['url']}) | {ref['protocol_use']} |")
    lines.extend(
        [
            "",
            "## Local Matched Protocol Rows",
            "",
            "| Source | Name | Seeds | RUL cap | Windows | Subsets | RMSE | Score | Status |",
            "|---|---|---:|---|---|---|---:|---:|---|",
        ]
    )
    for row in payload["local_protocol_rows"]:
        rmse = row.get("rmse_mean")
        score = row.get("score_mean")
        lines.append(
            "| {source} | {name} | {seeds} | {cap} | {windows} | {subsets} | {rmse} | {score} | {status} |".format(
                source=row.get("source"),
                name=row.get("name"),
                seeds=row.get("n_seeds"),
                cap=", ".join(str(value) for value in (row.get("rul_cap_values") or [])) or "-",
                windows=", ".join(str(value) for value in (row.get("window_sizes") or [])) or "-",
                subsets=", ".join(str(value) for value in (row.get("subsets") or [])) or "-",
                rmse=f"{float(rmse):.4f}" if rmse is not None else "-",
                score=f"{float(score):.2f}" if score is not None else "-",
                status=row.get("alignment_status"),
            )
        )
    lines.extend(
        [
            "",
            "## Published Reference Registry",
            "",
            "| ID | Family | Year | Status | Blocking fields |",
            "|---|---|---:|---|---|",
        ]
    )
    for row in payload["published_reference_registry"]:
        lines.append(
            "| {id} | [{family}]({url}) | {year} | {status} | {blocking} |".format(
                id=row["id"],
                family=row["family"],
                url=row["url"],
                year=row["year"],
                status=row["alignment_status"],
                blocking=", ".join(row["blocking_fields"]),
            )
        )
    lines.extend(["", "## Wording", ""])
    lines.append(f"- Safe: {payload['recommended_paper_wording']['safe']}")
    lines.append(f"- Unsafe: {payload['recommended_paper_wording']['unsafe']}")
    lines.extend(["", "## Next Actions", ""])
    lines.extend(f"- {item}" for item in payload["next_actions"])
    return "\n".join(lines).rstrip() + "\n"


def write_cmapss_published_baseline_alignment(output_dir: Path | str = DEFAULT_OUTPUT_DIR) -> list[Path]:
    output_dir = Path(output_dir)
    os.makedirs(_fs_path(output_dir), exist_ok=True)
    payload = build_cmapss_published_baseline_alignment(output_dir / "cmapss_native_preprocessing_manifest.json")
    json_path = output_dir / "cmapss_published_baseline_alignment.json"
    md_path = output_dir / "cmapss_published_baseline_alignment.md"
    _write_json(json_path, payload)
    _write_text(md_path, render_markdown(payload))
    return [json_path, md_path]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Write C-MAPSS published-baseline alignment audit.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    for path in write_cmapss_published_baseline_alignment(args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
