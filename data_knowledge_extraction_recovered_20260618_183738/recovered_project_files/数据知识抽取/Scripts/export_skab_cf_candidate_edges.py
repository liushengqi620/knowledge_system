from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from public_benchmark_experiment import (
    DEFAULT_PUBLIC_DATASET_ROOT,
    SKAB_LAGGED_MECHANISM_EDGES,
    SKAB_LLM_MECHANISM_EDGE_CANDIDATES,
    build_skab_data_lag_edges,
    load_skab_dataset,
    split_skab_runs,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPORTS_DIR = PROJECT_ROOT / "knowledge_exports"


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _write_text(path: Path | str, text: str) -> None:
    with open(_fs_path(path), "w", encoding="utf-8") as handle:
        handle.write(text)


def _edge_key(edge: Mapping[str, Any]) -> tuple[str, str, int]:
    return (str(edge.get("source", "")), str(edge.get("target", "")), int(edge.get("lag", 0) or 0))


def _normalize_edge(edge: Mapping[str, Any], *, family: str) -> dict[str, Any]:
    out = dict(edge)
    out["source"] = str(out.get("source", "")).strip()
    out["target"] = str(out.get("target", "")).strip()
    out["lag"] = int(out.get("lag", 0) or 0)
    out["relation"] = str(out.get("relation", family))
    out["reliability"] = float(out.get("reliability", 0.0) or 0.0)
    families = set(map(str, out.get("source_families", []) or []))
    families.add(str(family))
    out["source_families"] = sorted(families)
    return out


def merge_candidate_edges(
    edge_groups: Sequence[tuple[str, Sequence[Mapping[str, Any]]]],
    *,
    allowed_features: Sequence[str],
    max_edges: int,
    min_reliability: float,
) -> list[dict[str, Any]]:
    allowed = set(map(str, allowed_features))
    by_key: dict[tuple[str, str, int], dict[str, Any]] = {}
    for family, edges in edge_groups:
        for raw in edges:
            edge = _normalize_edge(raw, family=str(family))
            if not edge["source"] or not edge["target"] or edge["source"] == edge["target"]:
                continue
            if allowed and (edge["source"] not in allowed or edge["target"] not in allowed):
                continue
            if float(edge["reliability"]) < float(min_reliability):
                continue
            key = _edge_key(edge)
            current = by_key.get(key)
            if current is None:
                by_key[key] = edge
                continue
            current["reliability"] = max(float(current.get("reliability", 0.0)), float(edge["reliability"]))
            current["source_families"] = sorted(set(current.get("source_families", [])) | set(edge["source_families"]))
            if "data" in edge["source_families"]:
                current["correlation"] = edge.get("correlation", current.get("correlation"))
    ranked = sorted(
        by_key.values(),
        key=lambda edge: (
            -float(edge.get("reliability", 0.0)),
            str(edge.get("source")),
            str(edge.get("target")),
            int(edge.get("lag", 0) or 0),
        ),
    )
    return ranked[: int(max_edges)]


def balanced_candidate_edges(
    edge_groups: Sequence[tuple[str, Sequence[Mapping[str, Any]]]],
    *,
    allowed_features: Sequence[str],
    max_edges: int,
    min_reliability: float,
    reserve_families: Sequence[str] = ("expert", "llm_static"),
    reserve_per_family: int = 2,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    selected_keys: set[tuple[str, str, int]] = set()
    group_map = {family: edges for family, edges in edge_groups}
    for family in reserve_families:
        reserved = merge_candidate_edges(
            [(family, group_map.get(family, []))],
            allowed_features=allowed_features,
            max_edges=int(reserve_per_family),
            min_reliability=float(min_reliability),
        )
        for edge in reserved:
            key = _edge_key(edge)
            if key in selected_keys or len(selected) >= int(max_edges):
                continue
            selected.append(edge)
            selected_keys.add(key)
    full_ranked = merge_candidate_edges(
        edge_groups,
        allowed_features=allowed_features,
        max_edges=max(int(max_edges) * 4, int(max_edges)),
        min_reliability=float(min_reliability),
    )
    for edge in full_ranked:
        key = _edge_key(edge)
        if key in selected_keys or len(selected) >= int(max_edges):
            continue
        selected.append(edge)
        selected_keys.add(key)
    return selected


def build_seed_candidate_payload(
    *,
    dataset_root: Path,
    seed: int,
    max_edges: int,
    min_reliability: float,
    max_data_edges: int,
) -> dict[str, Any]:
    x_raw, _y, meta = load_skab_dataset(dataset_root)
    allowed_features = [
        str(col)
        for col in x_raw.columns
        if col not in {"run_id", "run_group", "sample_index"} and np.issubdtype(x_raw[col].dtype, np.number)
    ]
    train_runs, val_runs, test_runs = split_skab_runs(meta, seed=int(seed), test_size=0.30, val_fraction=0.25)
    train_mask = meta["run_id"].astype(str).isin(train_runs).to_numpy(dtype=bool)
    data_edges, data_diag = build_skab_data_lag_edges(
        x_raw,
        meta,
        allowed_features,
        train_mask=train_mask,
        top_k=int(max_data_edges),
        min_abs_correlation=0.20,
    )
    edge_groups = [
        ("expert", SKAB_LAGGED_MECHANISM_EDGES),
        ("llm_static", SKAB_LLM_MECHANISM_EDGE_CANDIDATES),
        ("data", data_edges),
    ]
    edges = balanced_candidate_edges(
        edge_groups,
        allowed_features=allowed_features,
        max_edges=int(max_edges),
        min_reliability=float(min_reliability),
    )
    return {
        "status": "ok",
        "schema": "skab_cf_candidate_edges_v1",
        "seed": int(seed),
        "split": {
            "train_runs": list(map(str, train_runs)),
            "val_runs": list(map(str, val_runs)),
            "test_runs": list(map(str, test_runs)),
        },
        "allowed_feature_count": int(len(allowed_features)),
        "dynamic_edges": edges,
        "candidate_edges": edges,
        "diagnostics": {
            "source": "train_split_static_expert_llm_data_candidate_cache",
            "min_reliability": float(min_reliability),
            "max_edges": int(max_edges),
            "family_reserve": {"families": ["expert", "llm_static"], "per_family": 2},
            "data_edges": data_diag,
            "n_exported_edges": int(len(edges)),
            "note": (
                "Frozen candidate cache for matched CF/no-CF ablation. It avoids API variability; "
                "the candidates still pass downstream reliability and counterfactual admission."
            ),
        },
    }


def output_path(exports_dir: Path, seed: int) -> Path:
    return exports_dir / f"public_benchmark_skab_dynamic_llm_api_seed{seed}_e8_learned_reliability_probe2_t045_k4.json"


def write_candidate_edges(
    *,
    dataset_root: Path = DEFAULT_PUBLIC_DATASET_ROOT,
    exports_dir: Path = DEFAULT_EXPORTS_DIR,
    seeds: Sequence[int] = (42, 43, 44),
    max_edges: int = 8,
    min_reliability: float = 0.20,
    max_data_edges: int = 24,
) -> list[Path]:
    paths: list[Path] = []
    os.makedirs(_fs_path(exports_dir), exist_ok=True)
    for seed in seeds:
        payload = build_seed_candidate_payload(
            dataset_root=Path(dataset_root),
            seed=int(seed),
            max_edges=int(max_edges),
            min_reliability=float(min_reliability),
            max_data_edges=int(max_data_edges),
        )
        path = output_path(Path(exports_dir), int(seed))
        _write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        paths.append(path)
    return paths


def _parse_seeds(raw: str) -> tuple[int, ...]:
    return tuple(int(part.strip()) for part in str(raw).split(",") if part.strip())


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Export frozen SKAB candidate edges for matched CF/no-CF ablations.")
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_PUBLIC_DATASET_ROOT)
    parser.add_argument("--exports-dir", type=Path, default=DEFAULT_EXPORTS_DIR)
    parser.add_argument("--seeds", default="42,43,44")
    parser.add_argument("--max-edges", type=int, default=8)
    parser.add_argument("--min-reliability", type=float, default=0.20)
    parser.add_argument("--max-data-edges", type=int, default=24)
    args = parser.parse_args(argv)
    for path in write_candidate_edges(
        dataset_root=args.dataset_root,
        exports_dir=args.exports_dir,
        seeds=_parse_seeds(args.seeds),
        max_edges=int(args.max_edges),
        min_reliability=float(args.min_reliability),
        max_data_edges=int(args.max_data_edges),
    ):
        print(path)


if __name__ == "__main__":
    main()
