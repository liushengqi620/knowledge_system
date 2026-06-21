from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np


@dataclass(frozen=True)
class PathMILOutput:
    bag_ids: list[str]
    bag_logits: np.ndarray
    bag_probabilities: np.ndarray
    instance_scores: np.ndarray
    top_paths_by_bag: dict[str, list[dict[str, Any]]]


def path_mil_topk_pooling(
    path_scores: np.ndarray,
    bag_ids: Sequence[Any],
    *,
    top_k: int = 3,
) -> PathMILOutput:
    scores = np.nan_to_num(np.asarray(path_scores, dtype=np.float32), nan=0.0, posinf=1.0, neginf=0.0)
    if scores.ndim != 2:
        raise ValueError("path_scores must be a 2D array.")
    bag_arr = np.asarray([str(x) for x in bag_ids], dtype=object)
    if len(bag_arr) != scores.shape[0]:
        raise ValueError("bag_ids length must match path_scores rows.")
    k = max(1, int(top_k))
    unique = list(dict.fromkeys(bag_arr.tolist()))
    logits: list[float] = []
    top_paths: dict[str, list[dict[str, Any]]] = {}
    for bag in unique:
        idx = np.where(bag_arr == bag)[0]
        block = scores[idx]
        if block.size == 0:
            logits.append(0.0)
            top_paths[bag] = []
            continue
        path_max = np.max(block, axis=0)
        order = np.argsort(-path_max)[: min(k, path_max.size)]
        top_values = path_max[order]
        logits.append(float(np.mean(top_values)))
        top_paths[bag] = [
            {
                "path_index": int(path_idx),
                "score": float(path_max[path_idx]),
                "bag_id": bag,
            }
            for path_idx in order
        ]
    bag_logits = np.asarray(logits, dtype=np.float32)
    bag_prob = 1.0 / (1.0 + np.exp(-bag_logits))
    return PathMILOutput(
        bag_ids=unique,
        bag_logits=bag_logits,
        bag_probabilities=bag_prob.astype(np.float32),
        instance_scores=scores,
        top_paths_by_bag=top_paths,
    )
