from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
import pandas as pd

from run_cmapss_rul_baselines import fit_deep_baseline
from run_public_ms_gse_rpf_experiment import (
    _limit_indices,
    apply_regime_prototype_residuals,
    build_causal_windows,
    build_rul_prediction_records,
    build_rul_targets,
    build_split,
    load_ready_task,
    rul_regression_metrics,
    scale_windows,
    select_cmapss_terminal_rul_indices,
    summarize_rul_by_subset,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_READY_ROOT = PROJECT_ROOT / "knowledge_exports" / "public_benchmark_ready"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "knowledge_exports" / "aaai_exact_native_protocol_gate"
VERSION = "cmapss-pseudo-truncation-validation-audit-v1"
DEFAULT_TARGET_RULS = (20, 50, 80, 110, 140, 170)
DEFAULT_CANDIDATES = ("gru_w80_cap125", "gru_w80_cap150", "gru_w160_cap150")


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


def _split_csv_ints(value: str) -> list[int]:
    return [int(part.strip()) for part in value.replace(";", ",").split(",") if part.strip()]


def parse_candidate(value: str) -> dict[str, Any]:
    parts = value.strip().lower().split("_")
    if len(parts) != 3 or parts[0] != "gru" or not parts[1].startswith("w") or not parts[2].startswith("cap"):
        raise ValueError(f"Unsupported C-MAPSS pseudo-validation candidate: {value}")
    return {
        "candidate": value.strip(),
        "baseline": "gru_sequence",
        "window_size": int(parts[1][1:]),
        "rul_cap": float(parts[2][3:]),
    }


def build_pseudo_terminal_indices(
    meta: pd.DataFrame,
    candidate_idx: Sequence[int],
    target_ruls: Iterable[int | float] = DEFAULT_TARGET_RULS,
) -> np.ndarray:
    idx = np.asarray(candidate_idx, dtype=np.int64)
    if len(idx) == 0:
        return idx
    required_cols = {"subset", "unit", "rul"}
    missing = required_cols.difference(meta.columns)
    if missing:
        raise ValueError(f"C-MAPSS meta is missing required columns: {sorted(missing)}")
    panel = meta.iloc[idx].copy()
    panel["_row_pos"] = idx
    selected: list[int] = []
    targets = [float(value) for value in target_ruls]
    for (_subset, _unit), group in panel.groupby(["subset", "unit"], sort=True):
        rul_values = group["rul"].astype(float)
        for target in targets:
            if target < float(rul_values.min()) or target > float(rul_values.max()):
                continue
            nearest = (rul_values - target).abs().sort_values(kind="mergesort").index[0]
            selected.append(int(group.loc[nearest, "_row_pos"]))
    return np.asarray(sorted(set(selected)), dtype=np.int64)


def _metric_mean(rows: Sequence[dict[str, Any]], key: str) -> float | None:
    values = [float(row[key]) for row in rows if row.get(key) is not None]
    return float(np.mean(values)) if values else None


def _metric_std(rows: Sequence[dict[str, Any]], key: str) -> float | None:
    values = [float(row[key]) for row in rows if row.get(key) is not None]
    return float(np.std(values)) if values else None


def _rul_distribution(values: np.ndarray) -> dict[str, Any]:
    arr = np.asarray(values, dtype=np.float32)
    if len(arr) == 0:
        return {"count": 0}
    return {
        "count": int(len(arr)),
        "min": float(np.min(arr)),
        "p25": float(np.percentile(arr, 25)),
        "median": float(np.percentile(arr, 50)),
        "mean": float(np.mean(arr)),
        "p75": float(np.percentile(arr, 75)),
        "max": float(np.max(arr)),
        "count_gt_125": int(np.sum(arr > 125.0)),
        "count_gt_150": int(np.sum(arr > 150.0)),
    }


def _candidate_result(
    *,
    candidate: dict[str, Any],
    seed: int,
    ready_root: Path,
    max_rows_per_split: int | None,
    target_ruls: Sequence[int],
    device: str,
    epochs: int,
    batch_size: int,
    hidden_dim: int,
    layers: int,
    dropout: float,
    use_regime_residuals: bool,
    regime_prototype_k: int,
    regime_healthy_stage_max: int,
) -> dict[str, Any]:
    task = load_ready_task(Path(ready_root), "cmapss", target="rul")
    split = build_split(task, seed=int(seed))
    train_idx = _limit_indices(split.train_idx, split.y_internal, seed=seed, limit=max_rows_per_split)
    pseudo_val_idx = build_pseudo_terminal_indices(task.meta, split.val_idx, target_ruls)
    test_idx = select_cmapss_terminal_rul_indices(task, split.test_idx)
    model_task = task
    regime_diag: dict[str, Any] = {"enabled": False}
    if bool(use_regime_residuals):
        model_task, regime_diag = apply_regime_prototype_residuals(
            task,
            train_idx,
            split.y_internal,
            n_regimes=regime_prototype_k,
            healthy_stage_max=regime_healthy_stage_max,
            seed=seed,
        )
    windows = build_causal_windows(model_task, window_size=int(candidate["window_size"]))
    x_train, x_val, x_test = scale_windows(windows, train_idx=train_idx, val_idx=pseudo_val_idx, test_idx=test_idx)
    rul_all = build_rul_targets(task)
    if rul_all is None:
        raise ValueError("C-MAPSS ready task is missing RUL targets.")
    y_train_raw = np.asarray(rul_all[train_idx], dtype=np.float32)
    y_val = np.asarray(rul_all[pseudo_val_idx], dtype=np.float32)
    y_test = np.asarray(rul_all[test_idx], dtype=np.float32)
    start = time.perf_counter()
    val_pred, test_pred, diagnostics = fit_deep_baseline(
        "gru_sequence",
        x_train=x_train,
        y_train=y_train_raw,
        x_val=x_val,
        y_val=y_val,
        x_test=x_test,
        seed=seed,
        rul_cap=float(candidate["rul_cap"]),
        device=device,
        epochs=epochs,
        batch_size=batch_size,
        learning_rate=1.0e-3,
        hidden_dim=hidden_dim,
        layers=layers,
        dropout=dropout,
    )
    elapsed = max(1.0e-9, time.perf_counter() - start)
    pseudo_records = build_rul_prediction_records(
        task.meta,
        pseudo_val_idx,
        y_val,
        val_pred,
        prediction_source=f"{candidate['candidate']}_pseudo_val",
    )
    test_records = build_rul_prediction_records(
        task.meta,
        test_idx,
        y_test,
        test_pred,
        prediction_source=f"{candidate['candidate']}_official_test",
    )
    return {
        "status": "ok",
        "candidate": candidate["candidate"],
        "baseline": "gru_sequence",
        "seed": int(seed),
        "window_size": int(candidate["window_size"]),
        "rul_cap": float(candidate["rul_cap"]),
        "protocol": "train_unit_pseudo_terminal_validation_for_cmapss_rul",
        "split_protocol": split.split_protocol,
        "train_size": int(len(train_idx)),
        "pseudo_val_size": int(len(pseudo_val_idx)),
        "official_test_size": int(len(test_idx)),
        "target_ruls": [int(value) for value in target_ruls],
        "pseudo_val_rul_distribution": _rul_distribution(y_val),
        "official_test_rul_distribution": _rul_distribution(y_test),
        "regime_prototype": regime_diag,
        "baseline_diagnostics": diagnostics,
        "fit_seconds": float(elapsed),
        "pseudo_val_metrics": rul_regression_metrics(y_val, val_pred),
        "official_test_metrics": rul_regression_metrics(y_test, test_pred),
        "pseudo_val_subset_metrics": summarize_rul_by_subset(pseudo_records),
        "official_test_subset_metrics": summarize_rul_by_subset(test_records),
    }


def summarize_candidate_runs(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    by_candidate: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_candidate.setdefault(str(row["candidate"]), []).append(row)
    summary: list[dict[str, Any]] = []
    for candidate, group in sorted(by_candidate.items()):
        pseudo_metrics = [dict(item["pseudo_val_metrics"], seed=item["seed"]) for item in group]
        test_metrics = [dict(item["official_test_metrics"], seed=item["seed"]) for item in group]
        first = group[0]
        summary.append(
            {
                "candidate": candidate,
                "n_seeds": int(len(group)),
                "window_size": int(first["window_size"]),
                "rul_cap": float(first["rul_cap"]),
                "pseudo_val_rmse_mean": _metric_mean(pseudo_metrics, "rul_rmse"),
                "pseudo_val_rmse_std": _metric_std(pseudo_metrics, "rul_rmse"),
                "pseudo_val_score_mean": _metric_mean(pseudo_metrics, "rul_score"),
                "official_test_rmse_mean": _metric_mean(test_metrics, "rul_rmse"),
                "official_test_rmse_std": _metric_std(test_metrics, "rul_rmse"),
                "official_test_score_mean": _metric_mean(test_metrics, "rul_score"),
                "fit_seconds_mean": float(np.mean([float(item["fit_seconds"]) for item in group])),
            }
        )
    return summary


def build_audit_payload(
    *,
    ready_root: Path = DEFAULT_READY_ROOT,
    candidates: Sequence[str] = DEFAULT_CANDIDATES,
    seeds: Sequence[int] = (42, 43, 44),
    max_rows_per_split: int | None = 12000,
    target_ruls: Sequence[int] = DEFAULT_TARGET_RULS,
    device: str = "auto",
    epochs: int = 25,
    batch_size: int = 256,
    hidden_dim: int = 64,
    layers: int = 2,
    dropout: float = 0.10,
    use_regime_residuals: bool = True,
    regime_prototype_k: int = 6,
    regime_healthy_stage_max: int = 0,
) -> dict[str, Any]:
    candidate_specs = [parse_candidate(value) for value in candidates]
    rows: list[dict[str, Any]] = []
    for seed in seeds:
        for candidate in candidate_specs:
            rows.append(
                _candidate_result(
                    candidate=candidate,
                    seed=int(seed),
                    ready_root=Path(ready_root),
                    max_rows_per_split=max_rows_per_split,
                    target_ruls=[int(value) for value in target_ruls],
                    device=device,
                    epochs=epochs,
                    batch_size=batch_size,
                    hidden_dim=hidden_dim,
                    layers=layers,
                    dropout=dropout,
                    use_regime_residuals=use_regime_residuals,
                    regime_prototype_k=regime_prototype_k,
                    regime_healthy_stage_max=regime_healthy_stage_max,
                )
            )
    summary = summarize_candidate_runs(rows)
    by_pseudo = sorted(summary, key=lambda row: float(row["pseudo_val_rmse_mean"]))
    by_test = sorted(summary, key=lambda row: float(row["official_test_rmse_mean"]))
    by_pseudo_score = sorted(summary, key=lambda row: float(row["pseudo_val_score_mean"]))
    by_test_score = sorted(summary, key=lambda row: float(row["official_test_score_mean"]))
    selected = by_pseudo[0] if by_pseudo else None
    best_test = by_test[0] if by_test else None
    selected_score = by_pseudo_score[0] if by_pseudo_score else None
    best_test_score = by_test_score[0] if by_test_score else None
    selected_name = selected["candidate"] if selected else None
    best_test_name = best_test["candidate"] if best_test else None
    selected_score_name = selected_score["candidate"] if selected_score else None
    best_test_score_name = best_test_score["candidate"] if best_test_score else None
    core_gates = {
        "pseudo_terminal_validation_train_only": bool(rows)
        and all(str(row["protocol"]) == "train_unit_pseudo_terminal_validation_for_cmapss_rul" for row in rows),
        "all_candidates_materialized": len(summary) == len(candidate_specs),
        "selection_declared_without_test_metrics": selected is not None,
        "pseudo_rmse_selection_matches_best_test_rmse": bool(selected_name and selected_name == best_test_name),
        "cap150_preferred_over_cap125_w80_by_pseudo_rmse": _candidate_better(summary, "gru_w80_cap150", "gru_w80_cap125", "pseudo_val_rmse_mean"),
        "long_window_preferred_over_w80_cap150_by_pseudo_rmse": _candidate_better(summary, "gru_w160_cap150", "gru_w80_cap150", "pseudo_val_rmse_mean"),
    }
    diagnostic_gates = {
        "pseudo_score_selection_matches_best_test_score": bool(selected_score_name and selected_score_name == best_test_score_name),
        "official_score_tradeoff_disclosed": True,
    }
    gates = {**core_gates, **diagnostic_gates}
    core_complete = all(core_gates.values())
    score_complete = bool(diagnostic_gates["pseudo_score_selection_matches_best_test_score"])
    status = (
        "pseudo_truncation_validation_complete"
        if core_complete and score_complete
        else "pseudo_truncation_validation_complete_with_score_tradeoff"
        if core_complete
        else "pseudo_truncation_validation_partial"
    )
    return {
        "version": VERSION,
        "status": status,
        "claim_boundary": (
            "This audit validates C-MAPSS cap/window selection on train-split pseudo-terminal units. "
            "It supports RMSE-oriented temporal-anchor selection only; path-fusion branches still require their own validation-admission proof, "
            "and PHM score trade-offs must be reported separately."
        ),
        "candidates": [dict(item) for item in candidate_specs],
        "seeds": [int(seed) for seed in seeds],
        "target_ruls": [int(value) for value in target_ruls],
        "summary": summary,
        "selected_by_pseudo_validation": selected,
        "best_by_official_test": best_test,
        "selected_by_pseudo_validation_score": selected_score,
        "best_by_official_test_score": best_test_score,
        "official_score_tradeoff": _score_tradeoff(selected, best_test_score),
        "gates": gates,
        "missing_gates": [name for name, value in gates.items() if not value],
        "runs": rows,
        "next_actions": [
            "If pseudo-selection and official-test ranking disagree, keep C-MAPSS as exploratory support and rerun a predeclared wider validation panel.",
            "Path-fusion variants must be evaluated against the same pseudo-terminal panel before any C-MAPSS path-fusion claim is admitted.",
            "Published C-MAPSS baselines still require exact cap, subset, score, preprocessing, and budget alignment before literature-wide SOTA wording.",
        ],
    }


def _candidate_better(summary: Sequence[dict[str, Any]], better: str, worse: str, metric: str) -> bool:
    by_name = {str(row["candidate"]): row for row in summary}
    if better not in by_name or worse not in by_name:
        return False
    return float(by_name[better][metric]) < float(by_name[worse][metric])


def _score_tradeoff(selected: dict[str, Any] | None, best_score: dict[str, Any] | None) -> dict[str, Any]:
    if not selected or not best_score:
        return {"present": False}
    selected_score = float(selected.get("official_test_score_mean", 0.0))
    best = float(best_score.get("official_test_score_mean", selected_score))
    return {
        "present": selected.get("candidate") != best_score.get("candidate"),
        "selected_candidate": selected.get("candidate"),
        "selected_official_test_score": selected_score,
        "best_score_candidate": best_score.get("candidate"),
        "best_official_test_score": best,
        "score_gap": float(selected_score - best),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# C-MAPSS Pseudo-Truncation Validation Audit",
        "",
        f"- Version: {payload['version']}",
        f"- Status: `{payload['status']}`",
        f"- Claim boundary: {payload['claim_boundary']}",
        f"- Seeds: {', '.join(str(seed) for seed in payload['seeds'])}",
        f"- Target pseudo-terminal RULs: {', '.join(str(value) for value in payload['target_ruls'])}",
        "",
        "## Candidate Summary",
        "",
        "| Candidate | Seeds | Cap | Window | Pseudo-val RMSE | Pseudo-val score | Official-test RMSE | Official-test score |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["summary"]:
        lines.append(
            "| {candidate} | {seeds} | {cap:.0f} | {window} | {p_rmse:.4f} +/- {p_std:.4f} | {p_score:.2f} | {t_rmse:.4f} +/- {t_std:.4f} | {t_score:.2f} |".format(
                candidate=row["candidate"],
                seeds=int(row["n_seeds"]),
                cap=float(row["rul_cap"]),
                window=int(row["window_size"]),
                p_rmse=float(row["pseudo_val_rmse_mean"]),
                p_std=float(row["pseudo_val_rmse_std"] or 0.0),
                p_score=float(row["pseudo_val_score_mean"] or 0.0),
                t_rmse=float(row["official_test_rmse_mean"]),
                t_std=float(row["official_test_rmse_std"] or 0.0),
                t_score=float(row["official_test_score_mean"] or 0.0),
            )
        )
    selected = payload.get("selected_by_pseudo_validation") or {}
    best_test = payload.get("best_by_official_test") or {}
    selected_score = payload.get("selected_by_pseudo_validation_score") or {}
    best_score = payload.get("best_by_official_test_score") or {}
    score_tradeoff = payload.get("official_score_tradeoff") or {}
    lines.extend(
        [
            "",
            "## Selection",
            "",
            f"- Selected by pseudo-validation RMSE: `{selected.get('candidate', '-')}`",
            f"- Best by official-test RMSE audit: `{best_test.get('candidate', '-')}`",
            f"- Selected by pseudo-validation PHM score: `{selected_score.get('candidate', '-')}`",
            f"- Best by official-test PHM score audit: `{best_score.get('candidate', '-')}`",
            f"- Official-test score trade-off if RMSE-selected branch is deployed: `{float(score_tradeoff.get('score_gap', 0.0)):.2f}`",
            "",
            "## Gate Status",
            "",
            "| Gate | Status |",
            "|---|---|",
        ]
    )
    for name, value in payload["gates"].items():
        lines.append(f"| {name} | {'pass' if value else 'closed'} |")
    lines.extend(["", "## Next Actions", ""])
    lines.extend(f"- {item}" for item in payload["next_actions"])
    return "\n".join(lines).rstrip() + "\n"


def write_audit(payload: dict[str, Any], output_dir: Path | str = DEFAULT_OUTPUT_DIR) -> list[Path]:
    output_dir = Path(output_dir)
    os.makedirs(_fs_path(output_dir), exist_ok=True)
    json_path = output_dir / "cmapss_pseudo_truncation_validation_audit.json"
    md_path = output_dir / "cmapss_pseudo_truncation_validation_audit.md"
    _write_json(json_path, payload)
    _write_text(md_path, render_markdown(payload))
    return [json_path, md_path]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Audit C-MAPSS cap/window selection using train-unit pseudo-terminal validation.")
    parser.add_argument("--ready-root", type=Path, default=DEFAULT_READY_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--candidates", default=",".join(DEFAULT_CANDIDATES))
    parser.add_argument("--seeds", default="42,43,44")
    parser.add_argument("--target-ruls", default=",".join(str(value) for value in DEFAULT_TARGET_RULS))
    parser.add_argument("--max-rows-per-split", type=int, default=12000)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--epochs", type=int, default=25)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--layers", type=int, default=2)
    parser.add_argument("--dropout", type=float, default=0.10)
    parser.add_argument("--no-regime-prototype-residuals", action="store_true")
    args = parser.parse_args(argv)
    payload = build_audit_payload(
        ready_root=args.ready_root,
        candidates=[part.strip() for part in args.candidates.replace(";", ",").split(",") if part.strip()],
        seeds=_split_csv_ints(args.seeds),
        max_rows_per_split=int(args.max_rows_per_split),
        target_ruls=_split_csv_ints(args.target_ruls),
        device=args.device,
        epochs=int(args.epochs),
        batch_size=int(args.batch_size),
        hidden_dim=int(args.hidden_dim),
        layers=int(args.layers),
        dropout=float(args.dropout),
        use_regime_residuals=not bool(args.no_regime_prototype_residuals),
    )
    for path in write_audit(payload, args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
