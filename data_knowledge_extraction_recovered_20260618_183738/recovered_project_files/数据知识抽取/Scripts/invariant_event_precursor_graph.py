from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from research_types import GraphPrior


@dataclass(frozen=True)
class EventPrecursorPath:
    """Path-level instance for KIEP-GL.

    A path is the unit learned by the path MIL branch: variable, lag, stage,
    mechanism, and target event are represented together instead of treating a
    graph edge as a plain variable dependency.
    """

    path_id: str
    variable: str
    downstream: str
    lag: int
    stage: str
    defect_mechanism: str
    event_target: str
    prior_strength: float
    evidence_score: float
    allowed: bool = True
    hierarchy_level: int = 0
    path_template_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _stage_for_lag(lag: int, config: Mapping[str, Any]) -> str:
    levels = config.get("event_precursor_levels") or config.get("stages") or []
    lag_i = max(0, int(lag))
    for item in levels:
        if not isinstance(item, Mapping):
            continue
        lo = int(item.get("min_lag", 0))
        hi = int(item.get("max_lag", lo))
        if lo <= lag_i <= hi:
            return str(item.get("name", "unknown"))
    if lag_i <= 3:
        return "late"
    if lag_i <= 8:
        return "mid"
    return "early"


def _infer_mechanism(src: str, dst: str, metadata: Mapping[str, Any]) -> str:
    mechanism_map = metadata.get("mechanism_map", {}) if isinstance(metadata, Mapping) else {}
    if isinstance(mechanism_map, Mapping):
        for key in (dst, src):
            value = mechanism_map.get(key)
            if value:
                return str(value)
    text = f"{src} {dst}".lower()
    if "mold" in text or "level" in text:
        return "mold_level_slag_risk"
    if "speed" in text or "stopper" in text or "flow" in text:
        return "speed_stopper_flow"
    if "temp" in text or "flux" in text or "superheat" in text:
        return "temperature_flux"
    if "heat" in text or "thermal" in text:
        return "heat_transfer_imbalance"
    return "process_fluctuation"


def build_event_precursor_paths(
    prior: GraphPrior,
    config: Mapping[str, Any],
    *,
    event_targets: Sequence[str] | None = None,
    defect_mechanisms: Sequence[str] | None = None,
) -> list[EventPrecursorPath]:
    targets = [str(x) for x in (event_targets or ["quality_event"])]
    mechanisms = [str(x) for x in (defect_mechanisms or [])]
    metadata = dict(prior.metadata or {})
    paths: list[EventPrecursorPath] = []
    for edge_idx, edge in enumerate(prior.edges):
        lag = int(edge.lag) if int(edge.lag) > 0 else int(config.get("event_precursor_min_lag", 1))
        stage = _stage_for_lag(lag, config)
        mechanism = _infer_mechanism(edge.from_node, edge.to_node, metadata)
        if mechanisms and mechanism not in mechanisms:
            mechanism = mechanisms[0]
        target = edge.to_node if edge.to_node in targets else targets[0]
        prior_strength = float(
            np.clip(
                0.45 * float(edge.weight)
                + 0.25 * float(edge.confidence)
                + 0.20 * float(edge.causal_strength)
                + 0.10 * float(edge.stability),
                0.0,
                1.0,
            )
        )
        evidence_score = float(
            np.clip(
                max([prior_strength, *[float(v) for v in dict(edge.evidence).values() if isinstance(v, (int, float))]]),
                0.0,
                1.0,
            )
        )
        path_template = f"{mechanism}:{edge.from_node}->{edge.to_node}->{target}"
        paths.append(
            EventPrecursorPath(
                path_id=f"path_{edge_idx:04d}_{edge.from_node}_to_{edge.to_node}",
                variable=edge.from_node,
                downstream=edge.to_node,
                lag=lag,
                stage=stage,
                defect_mechanism=mechanism,
                event_target=target,
                prior_strength=prior_strength,
                evidence_score=evidence_score,
                allowed=bool(edge.legal),
                hierarchy_level=1 if edge.relation_type == "quality_effect" else 0,
                path_template_id=path_template,
                metadata={
                    "relation_type": edge.relation_type,
                    "source": edge.source,
                    "dominant_source": edge.dominant_source or edge.source,
                    "evidence": dict(edge.evidence),
                },
            )
        )
    paths.sort(key=lambda p: (-p.prior_strength, -p.evidence_score, p.lag))
    max_paths = int(config.get("kiepgl_max_paths", config.get("max_paths", 128)))
    return paths[: max(1, max_paths)]


def score_event_precursor_paths(
    node_matrix: np.ndarray,
    node_names: Sequence[str],
    paths: Sequence[EventPrecursorPath],
    config: Mapping[str, Any],
) -> np.ndarray:
    node_x = np.asarray(node_matrix, dtype=np.float32)
    index = {str(name): i for i, name in enumerate(node_names)}
    if node_x.ndim != 2:
        raise ValueError("node_matrix must be a 2D array.")
    scores = np.zeros((node_x.shape[0], len(paths)), dtype=np.float32)
    stage_weight = {
        str(item.get("name")): float(item.get("weight", 1.0))
        for item in config.get("event_precursor_levels", [])
        if isinstance(item, Mapping)
    }
    for path_idx, path in enumerate(paths):
        src_idx = index.get(path.variable)
        dst_idx = index.get(path.downstream)
        if src_idx is None:
            continue
        src_signal = np.abs(node_x[:, src_idx])
        if dst_idx is not None:
            dst_signal = np.abs(node_x[:, dst_idx])
            dynamic_signal = 0.65 * src_signal + 0.35 * dst_signal
        else:
            dynamic_signal = src_signal
        scale = float(np.nanstd(dynamic_signal)) or 1.0
        centered = (dynamic_signal - float(np.nanmean(dynamic_signal))) / scale
        sigmoid = 1.0 / (1.0 + np.exp(-centered))
        prior = 0.6 * float(path.prior_strength) + 0.4 * float(path.evidence_score)
        stage = stage_weight.get(path.stage, 1.0)
        lag_penalty = 1.0 / (1.0 + 0.03 * max(0, int(path.lag) - 1))
        scores[:, path_idx] = np.asarray(sigmoid * prior * stage * lag_penalty, dtype=np.float32)
    return np.nan_to_num(scores, nan=0.0, posinf=1.0, neginf=0.0)


def build_regime_groups(
    data: pd.DataFrame | Mapping[str, Sequence[Any]] | np.ndarray,
    *,
    speed_col: str = "cast_speed_mean",
    sequence_col: str = "process_sequence_key",
    bins: int = 3,
) -> np.ndarray:
    if isinstance(data, pd.DataFrame):
        parts: list[pd.Series] = []
        if sequence_col in data.columns:
            parts.append(data[sequence_col].astype(str).fillna("seq_unknown"))
        if speed_col in data.columns:
            numeric = pd.to_numeric(data[speed_col], errors="coerce")
            try:
                parts.append(pd.qcut(numeric.rank(method="first"), q=max(1, int(bins)), labels=False).astype(str))
            except ValueError:
                parts.append(pd.Series(["speed_unknown"] * len(data), index=data.index))
        if parts:
            out = parts[0]
            for part in parts[1:]:
                out = out.astype(str) + "|" + part.astype(str)
            return out.to_numpy(dtype=object)
        return np.array(["global"] * len(data), dtype=object)
    arr = np.asarray(data)
    n = int(arr.shape[0]) if arr.ndim else 0
    return np.array(["global"] * n, dtype=object)
