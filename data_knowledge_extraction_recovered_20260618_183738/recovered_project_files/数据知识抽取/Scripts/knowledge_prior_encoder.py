from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from invariant_event_precursor_graph import EventPrecursorPath


@dataclass(frozen=True)
class EncodedKnowledgePrior:
    edge_mask: np.ndarray
    prior_matrix: np.ndarray
    path_prior_strength: np.ndarray
    lag_prior: np.ndarray
    mechanism_ids: list[str]
    metadata: dict[str, Any]


def encode_knowledge_prior(
    paths: Sequence[EventPrecursorPath],
    config: Mapping[str, Any],
) -> EncodedKnowledgePrior:
    n = len(paths)
    strengths = np.asarray(
        [float(np.clip(path.prior_strength, 0.0, 1.0)) for path in paths],
        dtype=np.float32,
    )
    allowed = np.asarray([1.0 if path.allowed else 0.0 for path in paths], dtype=np.float32)
    edge_mask = np.outer(allowed, allowed).astype(np.float32)
    if n:
        np.fill_diagonal(edge_mask, allowed)
    prior_matrix = np.outer(strengths, strengths).astype(np.float32)
    prior_matrix = np.clip(prior_matrix * edge_mask, 1e-6, 1.0)
    mechanisms = sorted({path.defect_mechanism for path in paths})
    mech_index = {name: i for i, name in enumerate(mechanisms)}
    lag_max = max(1, int(config.get("event_precursor_max_lag", 12)))
    lag_prior = np.asarray(
        [
            float(np.clip(1.0 - (max(0, int(path.lag) - 1) / max(1, lag_max)), 0.05, 1.0))
            for path in paths
        ],
        dtype=np.float32,
    )
    return EncodedKnowledgePrior(
        edge_mask=edge_mask,
        prior_matrix=prior_matrix,
        path_prior_strength=(strengths * allowed).astype(np.float32),
        lag_prior=lag_prior,
        mechanism_ids=[str(mech_index[path.defect_mechanism]) for path in paths],
        metadata={
            "n_paths": int(n),
            "mechanisms": mechanisms,
            "use_edge_mask": bool(config.get("knowledge_prior", {}).get("use_edge_mask", True)),
            "use_kl_prior": bool(config.get("knowledge_prior", {}).get("use_kl_prior", True)),
        },
    )
