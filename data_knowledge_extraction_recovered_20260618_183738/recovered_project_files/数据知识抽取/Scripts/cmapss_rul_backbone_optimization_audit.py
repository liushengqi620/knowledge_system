from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "knowledge_exports" / "aaai_exact_native_protocol_gate"
VERSION = "cmapss-rul-backbone-optimization-audit-v1"
DEFAULT_PSEUDO_VALIDATION_AUDIT = DEFAULT_OUTPUT_DIR / "cmapss_pseudo_truncation_validation_audit.json"

BASELINE_SUMMARIES: list[dict[str, Any]] = [
    {
        "name": "gru_w80_cap125",
        "path": REPO_ROOT / "knowledge_exports" / "cmapss_rul_deep_baselines_regime_w80" / "cmapss_rul_matched_baselines_summary.json",
        "baseline": "gru_sequence",
        "role": "old matched GRU anchor",
        "rul_cap": 125.0,
        "window_size": 80,
    },
    {
        "name": "gru_w80_cap150",
        "path": REPO_ROOT / "knowledge_exports" / "cmapss_rul_deep_baselines_regime_w80_cap150" / "cmapss_rul_matched_baselines_summary.json",
        "baseline": "gru_sequence",
        "role": "cap-corrected GRU anchor",
        "rul_cap": 150.0,
        "window_size": 80,
    },
    {
        "name": "gru_w160_cap150",
        "path": REPO_ROOT / "knowledge_exports" / "cmapss_rul_deep_baselines_regime_w160_cap150" / "cmapss_rul_matched_baselines_summary.json",
        "baseline": "gru_sequence",
        "role": "long-window cap-corrected GRU anchor",
        "rul_cap": 150.0,
        "window_size": 160,
    },
]

PUBLIC_RUN_SUMMARIES: list[dict[str, Any]] = [
    {
        "name": "anchorpath_w80_cap125",
        "path": REPO_ROOT / "knowledge_exports" / "aaai_formal_public_runs" / "cmapss_rul_anchorpath_bigru_cls020_w80_e20" / "ms_gse_rpf_cmapss_full_summary.json",
        "role": "old AnchorPath-BiGRU path-fusion branch",
        "rul_cap": 125.0,
        "window_size": 80,
    },
    {
        "name": "anchorpath_w80_cap150",
        "path": REPO_ROOT / "knowledge_exports" / "aaai_formal_public_runs" / "cmapss_rul_anchorpath_bigru_cls020_cap150_w80_e20" / "ms_gse_rpf_cmapss_full_summary.json",
        "role": "cap-corrected AnchorPath-BiGRU path-fusion branch",
        "rul_cap": 150.0,
        "window_size": 80,
    },
    {
        "name": "anchorpath_w160_cap150_seed42_smoke",
        "path": REPO_ROOT / "knowledge_exports" / "cmapss_rul_anchorpath_bigru_cls020_cap150_w160_seed42_smoke" / "ms_gse_rpf_cmapss_full_summary.json",
        "role": "long-window path-fusion smoke",
        "rul_cap": 150.0,
        "window_size": 160,
    },
]


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _read_json(path: Path) -> dict[str, Any] | None:
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


def _summary_row(spec: dict[str, Any]) -> dict[str, Any]:
    payload = _read_json(Path(spec["path"]))
    row: dict[str, Any] = {
        "name": spec["name"],
        "role": spec["role"],
        "source": str(Path(spec["path"]).relative_to(REPO_ROOT)),
        "rul_cap": float(spec["rul_cap"]),
        "window_size": int(spec["window_size"]),
        "status": "missing",
    }
    if not payload:
        return row
    for item in payload.get("overall", []):
        if str(item.get("baseline")) == str(spec["baseline"]):
            row.update(
                {
                    "status": "materialized",
                    "n_seeds": int(item.get("n_seeds", 0)),
                    "rmse_mean": float(item.get("rmse_mean")),
                    "rmse_std": float(item.get("rmse_std", 0.0)),
                    "mae_mean": float(item.get("mae_mean")),
                    "score_mean": float(item.get("score_mean")),
                    "score_std": float(item.get("score_std", 0.0)),
                }
            )
            return row
    return row


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _std(values: list[float]) -> float | None:
    if not values:
        return None
    mean = sum(values) / len(values)
    return (sum((value - mean) ** 2 for value in values) / len(values)) ** 0.5


def _public_run_row(spec: dict[str, Any]) -> dict[str, Any]:
    payload = _read_json(Path(spec["path"]))
    row: dict[str, Any] = {
        "name": spec["name"],
        "role": spec["role"],
        "source": str(Path(spec["path"]).relative_to(REPO_ROOT)),
        "rul_cap": float(spec["rul_cap"]),
        "window_size": int(spec["window_size"]),
        "status": "missing",
    }
    if not payload:
        return row
    runs = payload.get("runs", [])
    metrics = [run.get("primary_test_metrics", {}) for run in runs if isinstance(run.get("primary_test_metrics"), dict)]
    rmses = [float(item["rul_rmse"]) for item in metrics if item.get("rul_rmse") is not None]
    maes = [float(item["rul_mae"]) for item in metrics if item.get("rul_mae") is not None]
    scores = [float(item["rul_score"]) for item in metrics if item.get("rul_score") is not None]
    if not rmses:
        return row
    row.update(
        {
            "status": "materialized",
            "n_seeds": len(rmses),
            "rmse_mean": float(_mean(rmses) or 0.0),
            "rmse_std": float(_std(rmses) or 0.0),
            "mae_mean": float(_mean(maes) or 0.0),
            "score_mean": float(_mean(scores) or 0.0),
            "score_std": float(_std(scores) or 0.0),
        }
    )
    return row


def _by_name(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row["name"]): row for row in rows}


def _metric(row: dict[str, Any], key: str) -> float | None:
    value = row.get(key)
    return float(value) if value is not None else None


def build_cmapss_rul_backbone_optimization_audit() -> dict[str, Any]:
    baseline_rows = [_summary_row(spec) for spec in BASELINE_SUMMARIES]
    path_rows = [_public_run_row(spec) for spec in PUBLIC_RUN_SUMMARIES]
    rows = baseline_rows + path_rows
    by_name = _by_name(rows)
    old_gru = by_name.get("gru_w80_cap125", {})
    cap_gru = by_name.get("gru_w80_cap150", {})
    long_gru = by_name.get("gru_w160_cap150", {})
    cap_path = by_name.get("anchorpath_w80_cap150", {})
    long_path_smoke = by_name.get("anchorpath_w160_cap150_seed42_smoke", {})
    cap_gain = None
    if _metric(old_gru, "rmse_mean") is not None and _metric(cap_gru, "rmse_mean") is not None:
        cap_gain = float(_metric(old_gru, "rmse_mean") - _metric(cap_gru, "rmse_mean"))
    long_gain = None
    if _metric(cap_gru, "rmse_mean") is not None and _metric(long_gru, "rmse_mean") is not None:
        long_gain = float(_metric(cap_gru, "rmse_mean") - _metric(long_gru, "rmse_mean"))
    path_delta = None
    if _metric(cap_gru, "rmse_mean") is not None and _metric(cap_path, "rmse_mean") is not None:
        path_delta = float(_metric(cap_path, "rmse_mean") - _metric(cap_gru, "rmse_mean"))
    long_path_seed42_delta = None
    long_seed42 = _read_json(REPO_ROOT / "knowledge_exports" / "cmapss_rul_deep_baselines_regime_w160_cap150" / "gru_sequence" / "cmapss_rul_gru_sequence_seed42.json")
    if long_seed42 and _metric(long_path_smoke, "rmse_mean") is not None:
        long_gru_seed42 = float(long_seed42["primary_test_metrics"]["rul_rmse"])
        long_path_seed42_delta = float(_metric(long_path_smoke, "rmse_mean") - long_gru_seed42)
    pseudo_validation = _read_json(DEFAULT_PSEUDO_VALIDATION_AUDIT) or {}
    pseudo_gates = pseudo_validation.get("gates") if isinstance(pseudo_validation.get("gates"), dict) else {}
    gates = {
        "cap150_improves_w80_gru": bool(cap_gain is not None and cap_gain > 0.0),
        "long_window_improves_cap150_gru": bool(long_gain is not None and long_gain > 0.0),
        "pseudo_terminal_rmse_selection_supports_long_window": bool(
            pseudo_gates.get("pseudo_rmse_selection_matches_best_test_rmse")
            and pseudo_gates.get("long_window_preferred_over_w80_cap150_by_pseudo_rmse")
        ),
        "path_fusion_admitted_for_cmapss": bool(path_delta is not None and path_delta < 0.0),
        "long_window_path_smoke_admitted": bool(long_path_seed42_delta is not None and long_path_seed42_delta < 0.0),
    }
    return {
        "version": VERSION,
        "status": "cmapss_rul_backbone_optimization_partial",
        "claim_boundary": (
            "The current C-MAPSS evidence supports a cap-corrected long-window temporal anchor. "
            "Path residual fusion is not admitted for C-MAPSS until it beats the same-window temporal anchor under validation-safe evidence."
        ),
        "rows": rows,
        "deltas": {
            "cap150_vs_cap125_gru_rmse_reduction": cap_gain,
            "w160_vs_w80_cap150_gru_rmse_reduction": long_gain,
            "anchorpath_w80_cap150_minus_gru_w80_cap150_rmse": path_delta,
            "anchorpath_w160_cap150_seed42_minus_gru_w160_cap150_seed42_rmse": long_path_seed42_delta,
        },
        "pseudo_terminal_validation": {
            "present": bool(pseudo_validation),
            "status": pseudo_validation.get("status"),
            "selected_by_pseudo_validation": (pseudo_validation.get("selected_by_pseudo_validation") or {}).get("candidate")
            if isinstance(pseudo_validation.get("selected_by_pseudo_validation"), dict)
            else None,
            "best_by_official_test": (pseudo_validation.get("best_by_official_test") or {}).get("candidate")
            if isinstance(pseudo_validation.get("best_by_official_test"), dict)
            else None,
            "official_score_tradeoff": pseudo_validation.get("official_score_tradeoff"),
        },
        "gates": gates,
        "recommended_cmapss_role": (
            "Use C-MAPSS as original-task RUL transfer evidence with a long-window temporal anchor. "
            "Do not claim C-MAPSS path-fusion gain unless a future validation-admitted path branch improves this anchor."
        ),
        "next_actions": [
            "Use the pseudo-terminal validation audit when reporting C-MAPSS cap/window selection, and disclose the PHM-score trade-off.",
            "Promote w160/cap150 GRU or an equivalent temporal anchor as the C-MAPSS local matched anchor for RMSE-oriented claims.",
            "Redesign RUL path fusion as a challenger: deploy it only when the same pseudo-terminal panel improves RMSE and passes a predeclared score trade-off rule.",
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# C-MAPSS RUL Backbone Optimization Audit",
        "",
        f"- Version: {payload['version']}",
        f"- Status: `{payload['status']}`",
        f"- Claim boundary: {payload['claim_boundary']}",
        "",
        "## Result Rows",
        "",
        "| Name | Role | Seeds | Cap | Window | RMSE | RMSE std | Score | Status |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in payload["rows"]:
        lines.append(
            "| {name} | {role} | {seeds} | {cap:.0f} | {window} | {rmse} | {std} | {score} | {status} |".format(
                name=row["name"],
                role=row["role"],
                seeds=row.get("n_seeds", 0),
                cap=float(row["rul_cap"]),
                window=int(row["window_size"]),
                rmse=f"{float(row['rmse_mean']):.4f}" if row.get("rmse_mean") is not None else "-",
                std=f"{float(row['rmse_std']):.4f}" if row.get("rmse_std") is not None else "-",
                score=f"{float(row['score_mean']):.2f}" if row.get("score_mean") is not None else "-",
                status=row["status"],
            )
        )
    lines.extend(["", "## Deltas", ""])
    for name, value in payload["deltas"].items():
        lines.append(f"- {name}: {value:.4f}" if value is not None else f"- {name}: n/a")
    pseudo = payload.get("pseudo_terminal_validation") or {}
    lines.extend(["", "## Pseudo-Terminal Validation", ""])
    if pseudo.get("present"):
        lines.append(f"- Status: `{pseudo.get('status')}`")
        lines.append(f"- Selected by pseudo validation: `{pseudo.get('selected_by_pseudo_validation')}`")
        lines.append(f"- Best by official test RMSE: `{pseudo.get('best_by_official_test')}`")
        tradeoff = pseudo.get("official_score_tradeoff") or {}
        if tradeoff:
            lines.append(
                "- Official PHM-score trade-off: `{gap:.2f}` ({selected} vs {best})".format(
                    gap=float(tradeoff.get("score_gap", 0.0)),
                    selected=tradeoff.get("selected_candidate"),
                    best=tradeoff.get("best_score_candidate"),
                )
            )
    else:
        lines.append("- missing")
    lines.extend(["", "## Gates", "", "| Gate | Status |", "|---|---|"])
    for name, value in payload["gates"].items():
        lines.append(f"| {name} | {'pass' if value else 'closed'} |")
    lines.extend(["", "## Recommendation", "", payload["recommended_cmapss_role"], "", "## Next Actions", ""])
    lines.extend(f"- {item}" for item in payload["next_actions"])
    return "\n".join(lines).rstrip() + "\n"


def write_cmapss_rul_backbone_optimization_audit(output_dir: Path | str = DEFAULT_OUTPUT_DIR) -> list[Path]:
    output_dir = Path(output_dir)
    payload = build_cmapss_rul_backbone_optimization_audit()
    json_path = output_dir / "cmapss_rul_backbone_optimization_audit.json"
    md_path = output_dir / "cmapss_rul_backbone_optimization_audit.md"
    _write_json(json_path, payload)
    _write_text(md_path, render_markdown(payload))
    return [json_path, md_path]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Write C-MAPSS RUL backbone optimization audit.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    for path in write_cmapss_rul_backbone_optimization_audit(args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
