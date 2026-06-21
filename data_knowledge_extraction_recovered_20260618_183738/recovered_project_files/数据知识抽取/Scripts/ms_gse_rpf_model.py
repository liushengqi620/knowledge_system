from __future__ import annotations

import math
import os
from dataclasses import dataclass
from typing import Any, Sequence

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass(frozen=True)
class MSGSERPFConfig:
    n_features: int
    n_classes: int
    hidden_dim: int = 32
    scales: tuple[int, ...] = (3, 5, 9)
    temporal_encoder_mode: str = "multi_scale_causal"
    graph_top_k: int = 8
    max_paths: int = 32
    dropout: float = 0.10
    use_graph: bool = True
    use_reliability: bool = True
    use_path_fusion: bool = True
    use_residual_evidence: bool = False
    use_temporal_descriptors: bool = False
    temporal_descriptor_weight: float = 0.50
    prior_strength: float = 0.0
    path_coverage_mode: str = "target_group"
    coverage_dedup_mode: str = "soft"
    coverage_redundancy_penalty: float = 0.05
    deduplicate_exact_paths: bool = False
    use_edge_family_router: bool = False
    edge_family_count: int = 3
    edge_family_router_temperature: float = 1.0
    edge_family_router_floor: float = 0.05
    edge_family_router_blend: float = 1.0
    use_task_salience: bool = False
    salience_selection_strength: float = 0.0
    salience_coverage_fraction: float = 0.0
    use_multihop_paths: bool = False
    multihop_path_fraction: float = 0.25
    use_context_router: bool = True
    prior_coverage_fraction: float = 0.0
    candidate_coverage_fraction: float = 0.0
    use_class_conditioned_evidence: bool = False
    class_evidence_gate_threshold: float = 0.0
    class_evidence_gate_temperature: float = 0.05
    class_evidence_gate_floor: float = 0.0
    class_evidence_router_temperature: float = 1.0
    class_evidence_router_top_k: int = 0
    use_class_conditioned_prior_admission: bool = False
    class_prior_admission_floor: float = 0.10
    use_adaptive_prior_admission: bool = False
    adaptive_prior_admission_threshold: float = 0.20
    adaptive_prior_admission_temperature: float = 0.05
    use_candidate_prior_admission: bool = False
    candidate_prior_admission_floor: float = 0.05
    candidate_prior_admission_threshold: float = 0.50
    candidate_prior_admission_temperature: float = 0.05
    candidate_prior_admission_support_mode: str = "relative_evidence"
    candidate_prior_admission_scale: float = 0.50
    candidate_prior_admission_min_support: float = 0.0
    candidate_prior_admission_protected_min_support: float = 0.0
    candidate_prior_admission_target: str = "coverage"
    use_edge_calibrator: bool = False
    edge_calibrator_floor: float = 0.05
    edge_calibrator_init_bias: float = 2.0
    use_path_reliability_calibrator: bool = False
    path_reliability_context_scale: float = 1.0
    use_learned_path_admission: bool = False
    path_admission_strength: float = 1.0
    use_path_prior_consistency: bool = False
    path_prior_consistency_strength: float = 0.0
    path_prior_consistency_threshold: float = 0.25
    path_prior_consistency_temperature: float = 0.05
    path_prior_consistency_support_mode: str = "max"
    path_prior_consistency_class_floor: float = 0.25
    use_path_evidence_consistency: bool = False
    path_evidence_consistency_strength: float = 0.0
    path_evidence_consistency_threshold: float = 0.35
    path_evidence_consistency_temperature: float = 0.05
    path_evidence_consistency_floor: float = 0.0
    path_evidence_consistency_support_mode: str = "absolute"
    use_path_proposal_consistency: bool = False
    path_proposal_consistency_strength: float = 0.0
    path_proposal_consistency_threshold: float = 0.35
    path_proposal_consistency_temperature: float = 0.05
    path_proposal_consistency_floor: float = 0.10
    path_proposal_consistency_support_mode: str = "max"
    path_proposal_consistency_protected_strength: float = 0.0
    path_proposal_retention_fraction: float = 0.0
    use_temporal_mixer: bool = False
    temporal_mixer_type: str = "conv"
    temporal_mixer_depth: int = 3
    use_rul_temporal_anchor_fusion: bool = False
    rul_anchor_residual_scale: float = 1.0
    rul_anchor_gate_bias: float = -1.0


TEMPORAL_ENCODER_MODE_ALIASES: dict[str, str] = {
    "single": "single_scale_causal",
    "single_scale": "single_scale_causal",
    "single_scale_unidirectional": "single_scale_causal",
    "single_scale_uni": "single_scale_causal",
    "single_scale_causal": "single_scale_causal",
    "single_scale_forward": "single_scale_causal",
    "single_bi": "single_scale_bidirectional",
    "single_scale_bi": "single_scale_bidirectional",
    "single_scale_bidirectional": "single_scale_bidirectional",
    "multi": "multi_scale_causal",
    "multi_scale": "multi_scale_causal",
    "multi_scale_unidirectional": "multi_scale_causal",
    "multi_scale_uni": "multi_scale_causal",
    "multi_scale_causal": "multi_scale_causal",
    "multi_scale_forward": "multi_scale_causal",
    "multi_bi": "multi_scale_bidirectional",
    "multi_scale_bi": "multi_scale_bidirectional",
    "multi_scale_bidirectional": "multi_scale_bidirectional",
}


def normalize_temporal_encoder_mode(mode: str) -> str:
    normalized = str(mode or "multi_scale_causal").strip().lower().replace("-", "_")
    if normalized not in TEMPORAL_ENCODER_MODE_ALIASES:
        valid = ", ".join(sorted(TEMPORAL_ENCODER_MODE_ALIASES))
        raise ValueError(f"Unknown temporal encoder mode: {mode}. Expected one of: {valid}")
    return TEMPORAL_ENCODER_MODE_ALIASES[normalized]


class MultiScaleEventTokenizer(nn.Module):
    """Per-variable temporal tokenizer matched to directed graph/path reasoning."""

    def __init__(
        self,
        n_features: int,
        hidden_dim: int,
        scales: Sequence[int],
        dropout: float,
        temporal_encoder_mode: str = "multi_scale_causal",
    ) -> None:
        super().__init__()
        self.n_features = int(n_features)
        self.hidden_dim = int(hidden_dim)
        self.temporal_encoder_mode = normalize_temporal_encoder_mode(temporal_encoder_mode)
        raw_scales = tuple(max(1, int(s)) for s in scales) or (5,)
        self.scales = raw_scales if self.temporal_encoder_mode.startswith("multi_scale") else (raw_scales[len(raw_scales) // 2],)
        self.bidirectional = self.temporal_encoder_mode.endswith("bidirectional")
        self.convs = nn.ModuleList(
            [
                nn.Conv1d(
                    self.n_features,
                    self.n_features * self.hidden_dim,
                    kernel_size=s,
                    padding=0,
                    groups=self.n_features,
                )
                for s in self.scales
            ]
        )
        self.backward_convs = nn.ModuleList(
            [
                nn.Conv1d(
                    self.n_features,
                    self.n_features * self.hidden_dim,
                    kernel_size=s,
                    padding=0,
                    groups=self.n_features,
                )
                for s in self.scales
            ]
        ) if self.bidirectional else None
        self.scale_gate = nn.Sequential(
            nn.LayerNorm(self.hidden_dim),
            nn.Linear(self.hidden_dim, 1),
        )
        self.out = nn.Sequential(
            nn.LayerNorm(self.hidden_dim),
            nn.Dropout(float(dropout)),
        )

    def _conv_summary(self, conv: nn.Conv1d, x_ch: torch.Tensor) -> torch.Tensor:
        kernel = int(conv.kernel_size[0])
        padded = F.pad(x_ch, (kernel - 1, 0)) if kernel > 1 else x_ch
        raw = torch.tanh(conv(padded))
        raw = raw.view(x_ch.shape[0], self.n_features, self.hidden_dim, raw.shape[-1])
        last = raw[:, :, :, -1]
        mean = raw.mean(dim=-1)
        return 0.65 * last + 0.35 * mean

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        # x: [batch, time, variable]
        x_ch = x.transpose(1, 2)
        scale_tokens: list[torch.Tensor] = []
        for scale_idx, conv in enumerate(self.convs):
            token = self._conv_summary(conv, x_ch)
            if self.backward_convs is not None:
                backward = self._conv_summary(self.backward_convs[scale_idx], torch.flip(x_ch, dims=(-1,)))
                token = 0.50 * token + 0.50 * backward
            scale_tokens.append(token)
        stacked = torch.stack(scale_tokens, dim=1)  # [B, S, C, H]
        gate_logits = self.scale_gate(stacked).squeeze(-1)
        weights = torch.softmax(gate_logits, dim=1)
        token = torch.sum(stacked * weights.unsqueeze(-1), dim=1)
        return self.out(token), weights


class TemporalDescriptorEvidence(nn.Module):
    """Projects explicit local temporal descriptors into per-variable evidence tokens."""

    def __init__(self, hidden_dim: int, dropout: float) -> None:
        super().__init__()
        self.proj = nn.Sequential(
            nn.Linear(5, hidden_dim),
            nn.GELU(),
            nn.LayerNorm(hidden_dim),
            nn.Dropout(float(dropout)),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [batch, time, variable]
        last = x[:, -1, :]
        first = x[:, 0, :]
        mean = x.mean(dim=1)
        std = x.std(dim=1, unbiased=False)
        delta = last - first
        if x.shape[1] > 1:
            time = torch.linspace(-1.0, 1.0, steps=x.shape[1], device=x.device, dtype=x.dtype)
            time = time.view(1, -1, 1)
            centered = x - mean.unsqueeze(1)
            slope = torch.sum(centered * time, dim=1) / torch.clamp(torch.sum(time * time), min=1.0e-6)
        else:
            slope = torch.zeros_like(last)
        descriptors = torch.stack([last, mean, std, delta, slope], dim=-1)
        return self.proj(descriptors)


class TemporalConvMixer(nn.Module):
    """Global dilated temporal mixer used as a strong supervised backbone branch."""

    def __init__(self, n_features: int, hidden_dim: int, dropout: float, depth: int = 3) -> None:
        super().__init__()
        self.input_proj = nn.Conv1d(int(n_features), int(hidden_dim), kernel_size=1)
        blocks: list[nn.Module] = []
        for layer_idx in range(max(1, int(depth))):
            dilation = 2 ** min(layer_idx, 4)
            blocks.append(
                nn.Sequential(
                    nn.Conv1d(
                        int(hidden_dim),
                        int(hidden_dim),
                        kernel_size=3,
                        padding=dilation,
                        dilation=dilation,
                        groups=1,
                    ),
                    nn.GELU(),
                    nn.Dropout(float(dropout)),
                    nn.Conv1d(int(hidden_dim), int(hidden_dim), kernel_size=1),
                )
            )
        self.blocks = nn.ModuleList(blocks)
        self.norm = nn.LayerNorm(int(hidden_dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [batch, time, variable]
        z = self.input_proj(x.transpose(1, 2))
        for block in self.blocks:
            z = z + block(z)
        last = z[:, :, -1]
        mean = z.mean(dim=-1)
        max_pool = z.max(dim=-1).values
        return self.norm(0.50 * last + 0.30 * mean + 0.20 * max_pool)


class RecurrentTemporalMixer(nn.Module):
    """Global recurrent degradation mixer over the observed historical window."""

    def __init__(
        self,
        n_features: int,
        hidden_dim: int,
        dropout: float,
        depth: int = 2,
        *,
        bidirectional: bool = False,
    ) -> None:
        super().__init__()
        self.bidirectional = bool(bidirectional)
        self.gru = nn.GRU(
            input_size=int(n_features),
            hidden_size=int(hidden_dim),
            num_layers=max(1, int(depth)),
            dropout=float(dropout) if int(depth) > 1 else 0.0,
            batch_first=True,
            bidirectional=self.bidirectional,
        )
        out_dim = int(hidden_dim) * (2 if self.bidirectional else 1)
        self.proj = nn.Sequential(
            nn.LayerNorm(out_dim),
            nn.Dropout(float(dropout)),
            nn.Linear(out_dim, int(hidden_dim)),
            nn.GELU(),
            nn.LayerNorm(int(hidden_dim)),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _hidden = self.gru(x)
        last = out[:, -1, :]
        mean = out.mean(dim=1)
        max_pool = out.max(dim=1).values
        return self.proj(0.50 * last + 0.30 * mean + 0.20 * max_pool)


class DynamicVariableGraph(nn.Module):
    """Learns a sparse sample-wise directed dependency graph over variables."""

    def __init__(self, hidden_dim: int, top_k: int, use_graph: bool) -> None:
        super().__init__()
        self.top_k = int(top_k)
        self.use_graph = bool(use_graph)
        self.query = nn.Linear(hidden_dim, hidden_dim, bias=False)
        self.key = nn.Linear(hidden_dim, hidden_dim, bias=False)

    def forward(self, node_tokens: torch.Tensor, prior_adjacency: torch.Tensor | None = None, prior_strength: float = 0.0) -> torch.Tensor:
        batch, n_nodes, hidden = node_tokens.shape
        if not self.use_graph or n_nodes <= 1:
            return node_tokens.new_zeros((batch, n_nodes, n_nodes))
        q = self.query(node_tokens)
        k = self.key(node_tokens)
        scores = torch.bmm(q, k.transpose(1, 2)) / math.sqrt(max(1, hidden))
        if prior_adjacency is not None and float(prior_strength) > 0.0:
            prior = prior_adjacency.to(device=node_tokens.device, dtype=node_tokens.dtype)
            if prior.ndim == 2 and prior.shape == (n_nodes, n_nodes):
                scores = scores + float(prior_strength) * prior.unsqueeze(0)
            elif prior.ndim == 3 and tuple(prior.shape) == (batch, n_nodes, n_nodes):
                scores = scores + float(prior_strength) * prior
        eye = torch.eye(n_nodes, device=node_tokens.device, dtype=torch.bool).unsqueeze(0)
        scores = scores.masked_fill(eye, -1.0e9)
        top_k = max(1, min(int(self.top_k), n_nodes - 1))
        if top_k < n_nodes - 1:
            threshold = torch.topk(scores, k=top_k, dim=-1).values[..., -1:]
            scores = scores.masked_fill(scores < threshold, -1.0e9)
        return torch.softmax(scores, dim=-1).masked_fill(eye, 0.0)


class GraphSelectiveMemory(nn.Module):
    """Mamba-inspired selective scan conditioned by dynamic graph messages."""

    def __init__(self, hidden_dim: int, dropout: float, use_graph: bool) -> None:
        super().__init__()
        self.hidden_dim = int(hidden_dim)
        self.use_graph = bool(use_graph)
        self.input_proj = nn.Linear(2, hidden_dim)
        self.keep_gate = nn.Linear(2, hidden_dim)
        self.write_gate = nn.Linear(2, hidden_dim)
        self.message_proj = nn.Linear(hidden_dim, hidden_dim)
        self.message_gate = nn.Linear(hidden_dim * 2, hidden_dim)
        self.norm = nn.LayerNorm(hidden_dim)
        self.dropout = nn.Dropout(float(dropout))

    def forward(self, x: torch.Tensor, event_tokens: torch.Tensor, adjacency: torch.Tensor) -> torch.Tensor:
        batch, steps, n_nodes = x.shape
        state = x.new_zeros((batch, n_nodes, self.hidden_dim))
        prev = x[:, 0, :]
        for step in range(steps):
            current = x[:, step, :]
            delta = current - prev if step > 0 else torch.zeros_like(current)
            local = torch.stack([current, delta], dim=-1)
            candidate = torch.tanh(self.input_proj(local))
            keep = torch.sigmoid(self.keep_gate(local))
            write = torch.sigmoid(self.write_gate(local))
            state = keep * state + write * candidate
            prev = current
        if self.use_graph:
            message = torch.bmm(adjacency, state)
            gate = torch.sigmoid(self.message_gate(torch.cat([state, message], dim=-1)))
            state = state + gate * self.message_proj(message)
        return self.norm(event_tokens + self.dropout(state))


class EdgePriorCalibrator(nn.Module):
    """Sample-wise gate over candidate prior edges before graph and RPF use them."""

    def __init__(self, hidden_dim: int, floor: float = 0.05, init_bias: float = 2.0) -> None:
        super().__init__()
        self.hidden_dim = int(hidden_dim)
        self.rank = max(4, min(32, self.hidden_dim // 2))
        self.floor = float(min(0.95, max(0.0, floor)))
        self.norm = nn.LayerNorm(self.hidden_dim)
        self.query = nn.Linear(self.hidden_dim, self.rank, bias=False)
        self.key = nn.Linear(self.hidden_dim, self.rank, bias=False)
        self.target_score = nn.Linear(self.hidden_dim, 1)
        self.source_score = nn.Linear(self.hidden_dim, 1)
        self.prior_gain = nn.Parameter(torch.tensor(0.0))
        self.bias = nn.Parameter(torch.tensor(float(init_bias)))
        self.reset_parameters()

    def reset_parameters(self) -> None:
        nn.init.zeros_(self.query.weight)
        nn.init.zeros_(self.key.weight)
        nn.init.zeros_(self.target_score.weight)
        nn.init.zeros_(self.target_score.bias)
        nn.init.zeros_(self.source_score.weight)
        nn.init.zeros_(self.source_score.bias)

    def forward(self, node_tokens: torch.Tensor, prior_adjacency: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        batch, n_nodes, _hidden = node_tokens.shape
        prior = prior_adjacency.to(device=node_tokens.device, dtype=node_tokens.dtype)
        if prior.ndim == 2 and tuple(prior.shape) == (n_nodes, n_nodes):
            base_prior = prior.unsqueeze(0).expand(batch, -1, -1)
        elif prior.ndim == 3 and tuple(prior.shape) == (batch, n_nodes, n_nodes):
            base_prior = prior
        else:
            empty = node_tokens.new_zeros((batch, n_nodes, n_nodes))
            return empty, empty
        tokens = self.norm(node_tokens)
        query = self.query(tokens)
        key = self.key(tokens)
        interaction = torch.bmm(query, key.transpose(1, 2)) / math.sqrt(max(1, self.rank))
        logits = (
            interaction
            + self.target_score(tokens)
            + self.source_score(tokens).transpose(1, 2)
            + self.prior_gain * base_prior
            + self.bias
        )
        gate = self.floor + (1.0 - self.floor) * torch.sigmoid(logits)
        gate = gate * (base_prior > 0.0).to(dtype=gate.dtype)
        eye = torch.eye(n_nodes, device=node_tokens.device, dtype=torch.bool).unsqueeze(0)
        gate = gate.masked_fill(eye, 0.0)
        calibrated = (base_prior * gate).masked_fill(eye, 0.0)
        return calibrated, gate


def _replace_duplicate_flat_paths(flat_index: torch.Tensor, candidate_scores: torch.Tensor) -> torch.Tensor:
    if flat_index.ndim != 2 or candidate_scores.ndim != 2 or flat_index.shape[0] != candidate_scores.shape[0]:
        return flat_index
    if flat_index.shape[1] <= 1 or candidate_scores.shape[1] <= 0:
        return flat_index
    selected = flat_index.clone()
    for pos in range(1, int(selected.shape[1])):
        duplicate = selected[:, :pos].eq(selected[:, pos : pos + 1]).any(dim=1)
        if not bool(duplicate.any().item()):
            continue
        replacement_scores = candidate_scores.clone()
        replacement_scores.scatter_(1, selected[:, :pos], -1.0e9)
        best_score, best_index = torch.max(replacement_scores, dim=1)
        can_replace = duplicate & best_score.gt(-1.0e8)
        selected[:, pos] = torch.where(can_replace, best_index, selected[:, pos])
    return selected


class ReliablePathFusion(nn.Module):
    """Fuses top graph paths with separate importance and reliability scores."""

    def __init__(
        self,
        hidden_dim: int,
        max_paths: int,
        use_reliability: bool,
        use_path_fusion: bool,
        coverage_mode: str = "target_group",
        coverage_dedup_mode: str = "soft",
        coverage_redundancy_penalty: float = 0.05,
        deduplicate_exact_paths: bool = False,
        use_task_salience: bool = False,
        salience_selection_strength: float = 0.0,
        salience_coverage_fraction: float = 0.0,
        use_multihop_paths: bool = False,
        multihop_path_fraction: float = 0.25,
        use_context_router: bool = True,
        prior_coverage_fraction: float = 0.0,
        candidate_coverage_fraction: float = 0.0,
        use_path_reliability_calibrator: bool = False,
        path_reliability_context_scale: float = 1.0,
        use_learned_path_admission: bool = False,
        path_admission_strength: float = 1.0,
        use_path_prior_consistency: bool = False,
        path_prior_consistency_strength: float = 0.0,
        path_prior_consistency_threshold: float = 0.25,
        path_prior_consistency_temperature: float = 0.05,
        path_prior_consistency_support_mode: str = "max",
        path_prior_consistency_class_floor: float = 0.25,
        use_path_evidence_consistency: bool = False,
        path_evidence_consistency_strength: float = 0.0,
        path_evidence_consistency_threshold: float = 0.35,
        path_evidence_consistency_temperature: float = 0.05,
        path_evidence_consistency_floor: float = 0.0,
        path_evidence_consistency_support_mode: str = "absolute",
        use_path_proposal_consistency: bool = False,
        path_proposal_consistency_strength: float = 0.0,
        path_proposal_consistency_threshold: float = 0.35,
        path_proposal_consistency_temperature: float = 0.05,
        path_proposal_consistency_floor: float = 0.10,
        path_proposal_consistency_support_mode: str = "max",
        path_proposal_consistency_protected_strength: float = 0.0,
        path_proposal_retention_fraction: float = 0.0,
    ) -> None:
        super().__init__()
        self.max_paths = int(max_paths)
        self.use_reliability = bool(use_reliability)
        self.use_path_fusion = bool(use_path_fusion)
        self.coverage_mode = str(coverage_mode or "target_group")
        self.coverage_dedup_mode = str(coverage_dedup_mode or "soft")
        self.coverage_redundancy_penalty = float(max(0.0, coverage_redundancy_penalty))
        self.deduplicate_exact_paths = bool(deduplicate_exact_paths)
        self.use_task_salience = bool(use_task_salience)
        self.salience_selection_strength = float(salience_selection_strength)
        self.salience_coverage_fraction = float(min(0.75, max(0.0, salience_coverage_fraction)))
        self.use_multihop_paths = bool(use_multihop_paths)
        self.multihop_path_fraction = float(min(0.75, max(0.0, multihop_path_fraction)))
        self.use_context_router = bool(use_context_router)
        self.prior_coverage_fraction = float(min(0.75, max(0.0, prior_coverage_fraction)))
        self.candidate_coverage_fraction = float(min(0.50, max(0.0, candidate_coverage_fraction)))
        self.use_path_reliability_calibrator = bool(use_path_reliability_calibrator)
        self.path_reliability_context_scale = float(max(0.0, path_reliability_context_scale))
        self.use_learned_path_admission = bool(use_learned_path_admission)
        self.path_admission_strength = float(max(0.0, path_admission_strength))
        self.use_path_prior_consistency = bool(use_path_prior_consistency)
        self.path_prior_consistency_strength = float(max(0.0, path_prior_consistency_strength))
        self.path_prior_consistency_threshold = float(min(1.0, max(0.0, path_prior_consistency_threshold)))
        self.path_prior_consistency_temperature = float(max(1.0e-3, path_prior_consistency_temperature))
        mode = str(path_prior_consistency_support_mode or "max").strip().lower()
        self.path_prior_consistency_support_mode = mode if mode in {"max", "dynamic", "agreement", "class_blend"} else "max"
        self.path_prior_consistency_class_floor = float(min(1.0, max(0.0, path_prior_consistency_class_floor)))
        self.use_path_evidence_consistency = bool(use_path_evidence_consistency)
        self.path_evidence_consistency_strength = float(max(0.0, path_evidence_consistency_strength))
        self.path_evidence_consistency_threshold = float(min(1.0, max(0.0, path_evidence_consistency_threshold)))
        self.path_evidence_consistency_temperature = float(max(1.0e-3, path_evidence_consistency_temperature))
        self.path_evidence_consistency_floor = float(min(1.0, max(0.0, path_evidence_consistency_floor)))
        evidence_mode = str(path_evidence_consistency_support_mode or "absolute").strip().lower()
        self.path_evidence_consistency_support_mode = (
            evidence_mode if evidence_mode in {"absolute", "relative"} else "absolute"
        )
        self.use_path_proposal_consistency = bool(use_path_proposal_consistency)
        self.path_proposal_consistency_strength = float(max(0.0, min(1.0, path_proposal_consistency_strength)))
        self.path_proposal_consistency_protected_strength = float(
            max(0.0, min(1.0, path_proposal_consistency_protected_strength))
        )
        self.path_proposal_consistency_threshold = float(min(1.0, max(0.0, path_proposal_consistency_threshold)))
        self.path_proposal_consistency_temperature = float(max(1.0e-3, path_proposal_consistency_temperature))
        self.path_proposal_consistency_floor = float(min(1.0, max(0.0, path_proposal_consistency_floor)))
        proposal_mode = str(path_proposal_consistency_support_mode or "max").strip().lower()
        self.path_proposal_consistency_support_mode = (
            proposal_mode
            if proposal_mode
            in {
                "max",
                "salience",
                "prior",
                "relative_evidence",
                "evidence_admit",
                "agreement",
                "class_blend",
            }
            else "max"
        )
        self.path_proposal_retention_fraction = float(min(0.75, max(0.0, path_proposal_retention_fraction)))
        extra_path_features = 3 if self.use_task_salience else 2
        self.context_reliability_input_dim = hidden_dim * 3 + extra_path_features
        self.path_admission_input_dim = hidden_dim * 3 + extra_path_features
        path_in = hidden_dim * 4 + extra_path_features
        self.path_encoder = nn.Sequential(
            nn.Linear(path_in, hidden_dim),
            nn.GELU(),
            nn.LayerNorm(hidden_dim),
        )
        self.importance = nn.Linear(hidden_dim, 1)
        self.context_query = nn.Sequential(
            nn.LayerNorm(hidden_dim),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
        )
        self.context_importance = nn.Linear(hidden_dim, 1, bias=False)
        self.reliability = nn.Sequential(
            nn.Linear(hidden_dim + extra_path_features, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, 1),
        )
        self.reliability_gain = nn.Parameter(torch.tensor(-4.0))
        self.context_reliability: nn.Module | None = None
        self.path_admission = (
            nn.Sequential(
                nn.LayerNorm(self.path_admission_input_dim),
                nn.Linear(self.path_admission_input_dim, hidden_dim),
                nn.GELU(),
                nn.Linear(hidden_dim, 1),
            )
            if self.use_learned_path_admission
            else None
        )
        if self.path_admission is not None:
            nn.init.zeros_(self.path_admission[-1].weight)
            nn.init.zeros_(self.path_admission[-1].bias)

    def enable_path_reliability_calibrator(self) -> None:
        if self.context_reliability is not None:
            return
        self.context_reliability = nn.Sequential(
            nn.LayerNorm(self.context_reliability_input_dim),
            nn.Linear(self.context_reliability_input_dim, self.path_encoder[0].out_features),
            nn.GELU(),
            nn.Linear(self.path_encoder[0].out_features, 1),
        )
        nn.init.zeros_(self.context_reliability[-1].weight)
        nn.init.zeros_(self.context_reliability[-1].bias)

    def forward(
        self,
        node_states: torch.Tensor,
        adjacency: torch.Tensor,
        prior_adjacency: torch.Tensor | None = None,
        prior_feature_adjacency: torch.Tensor | None = None,
        candidate_proposal_adjacency: torch.Tensor | None = None,
        feature_group_ids: torch.Tensor | None = None,
        task_salience: torch.Tensor | None = None,
        path_evidence: torch.Tensor | None = None,
        proposal_protected_mass: torch.Tensor | None = None,
        target_allowed_mask: torch.Tensor | None = None,
        source_allowed_mask: torch.Tensor | None = None,
        bridge_allowed_mask: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
        batch, n_nodes, hidden = node_states.shape
        node_pool = node_states.mean(dim=1)
        if (not self.use_path_fusion) or n_nodes <= 1:
            empty = node_states.new_zeros((batch, 0))
            return node_pool, {
                "path_weights": empty,
                "path_reliability": empty,
                "path_reliability_context": empty,
                "path_edge_weight": empty,
                "path_context_importance": empty,
                "path_source": empty.long(),
                "path_target": empty.long(),
                "path_bridge": empty.long(),
                "path_hop_count": empty.long(),
                "path_duplicate_rate": node_states.new_zeros((batch,)),
            }

        masked_adjacency = adjacency.clone()
        eye = torch.eye(n_nodes, device=node_states.device, dtype=torch.bool).unsqueeze(0)
        masked_adjacency = masked_adjacency.masked_fill(eye, -1.0e9)
        if target_allowed_mask is not None and target_allowed_mask.numel() == n_nodes:
            allowed_targets = target_allowed_mask.to(device=node_states.device, dtype=torch.bool)
            if bool(allowed_targets.any().item()) and not bool(allowed_targets.all().item()):
                masked_adjacency = masked_adjacency.masked_fill(~allowed_targets.view(1, n_nodes, 1), -1.0e9)
        if source_allowed_mask is not None and source_allowed_mask.numel() == n_nodes:
            allowed_sources = source_allowed_mask.to(device=node_states.device, dtype=torch.bool)
            if bool(allowed_sources.any().item()) and not bool(allowed_sources.all().item()):
                masked_adjacency = masked_adjacency.masked_fill(~allowed_sources.view(1, 1, n_nodes), -1.0e9)
        pair_salience: torch.Tensor | None = None
        if self.use_task_salience and path_evidence is not None:
            evidence = path_evidence.to(device=node_states.device, dtype=node_states.dtype).clamp(0.0, 1.0)
            if evidence.ndim == 2 and tuple(evidence.shape) == (n_nodes, n_nodes):
                pair_salience = evidence.unsqueeze(0).expand(batch, -1, -1)
            elif evidence.ndim == 3 and tuple(evidence.shape) == (batch, n_nodes, n_nodes):
                pair_salience = evidence
        elif self.use_task_salience and task_salience is not None and task_salience.numel() == n_nodes:
            salience = task_salience.to(device=node_states.device, dtype=node_states.dtype).clamp(0.0, 1.0)
            target_salience = salience.view(1, n_nodes, 1)
            source_salience = salience.view(1, 1, n_nodes)
            pair_salience = torch.maximum(target_salience, source_salience).expand(batch, -1, -1)
        if pair_salience is not None:
            if float(self.salience_selection_strength) > 0.0:
                masked_adjacency = masked_adjacency + float(self.salience_selection_strength) * pair_salience
                masked_adjacency = masked_adjacency.masked_fill(eye, -1.0e9)
        raw_proposal_adjacency = masked_adjacency.clone()
        proposal_support_matrix = torch.zeros((batch, n_nodes, n_nodes), device=node_states.device, dtype=node_states.dtype)
        proposal_gate_matrix = torch.ones_like(proposal_support_matrix)
        proposal_effective_strength = torch.full(
            (batch,),
            float(self.path_proposal_consistency_strength),
            device=node_states.device,
            dtype=node_states.dtype,
        )
        if (
            self.use_path_proposal_consistency
            and max(
                float(self.path_proposal_consistency_strength),
                float(self.path_proposal_consistency_protected_strength),
            )
            > 0.0
        ):
            base_strength = float(self.path_proposal_consistency_strength)
            protected_strength = float(self.path_proposal_consistency_protected_strength)
            proposal_effective_strength = torch.full(
                (batch,),
                base_strength,
                device=node_states.device,
                dtype=node_states.dtype,
            )
            if protected_strength > 0.0 and proposal_protected_mass is not None:
                protected_mass = proposal_protected_mass.to(device=node_states.device, dtype=node_states.dtype).reshape(-1)
                if protected_mass.numel() == batch:
                    protected_mass = protected_mass.clamp(0.0, 1.0)
                    proposal_effective_strength = (
                        base_strength + (protected_strength - base_strength) * protected_mass
                    ).clamp(0.0, 1.0)
            dynamic_support = masked_adjacency.clamp(min=0.0, max=1.0)
            if prior_adjacency is not None:
                proposal_prior = prior_adjacency.to(device=node_states.device, dtype=node_states.dtype).clamp(0.0, 1.0)
                if proposal_prior.ndim == 2 and tuple(proposal_prior.shape) == (n_nodes, n_nodes):
                    proposal_prior = proposal_prior.unsqueeze(0).expand(batch, -1, -1)
                elif proposal_prior.ndim != 3 or tuple(proposal_prior.shape) != (batch, n_nodes, n_nodes):
                    proposal_prior = torch.zeros_like(dynamic_support)
            else:
                proposal_prior = torch.zeros_like(dynamic_support)
            proposal_salience = (
                pair_salience.to(device=node_states.device, dtype=node_states.dtype).clamp(0.0, 1.0)
                if pair_salience is not None and tuple(pair_salience.shape) == (batch, n_nodes, n_nodes)
                else torch.zeros_like(dynamic_support)
            )
            max_evidence = proposal_salience.reshape(batch, n_nodes * n_nodes).max(dim=1).values.view(batch, 1, 1)
            relative_evidence = torch.where(
                max_evidence > 1.0e-8,
                proposal_salience / torch.clamp(max_evidence, min=1.0e-8),
                proposal_salience,
            )
            if self.path_proposal_consistency_support_mode == "prior":
                proposal_support_matrix = proposal_prior
            elif self.path_proposal_consistency_support_mode == "salience":
                proposal_support_matrix = proposal_salience
            elif self.path_proposal_consistency_support_mode == "relative_evidence":
                proposal_support_matrix = relative_evidence
            elif self.path_proposal_consistency_support_mode == "evidence_admit":
                candidate_support = torch.maximum(proposal_prior, dynamic_support)
                proposal_support_matrix = relative_evidence * (
                    self.path_proposal_consistency_floor
                    + (1.0 - self.path_proposal_consistency_floor) * candidate_support
                )
            elif self.path_proposal_consistency_support_mode == "agreement":
                proposal_support_matrix = torch.minimum(
                    dynamic_support,
                    torch.maximum(proposal_prior, proposal_salience),
                )
            elif self.path_proposal_consistency_support_mode == "class_blend":
                evidence_support = torch.maximum(proposal_prior, proposal_salience)
                proposal_support_matrix = dynamic_support * (
                    self.path_proposal_consistency_floor
                    + (1.0 - self.path_proposal_consistency_floor) * evidence_support
                )
            else:
                proposal_support_matrix = torch.maximum(proposal_prior, proposal_salience)
            proposal_gate_matrix = self.path_proposal_consistency_floor + (
                1.0 - self.path_proposal_consistency_floor
            ) * torch.sigmoid(
                (proposal_support_matrix - self.path_proposal_consistency_threshold)
                / self.path_proposal_consistency_temperature
            )
            strength_view = proposal_effective_strength.view(batch, 1, 1)
            proposal_factor = (1.0 - strength_view) + strength_view * proposal_gate_matrix
            masked_adjacency = torch.where(
                masked_adjacency.gt(-1.0e8),
                masked_adjacency.clamp(min=0.0) * proposal_factor,
                masked_adjacency,
            )
            masked_adjacency = masked_adjacency.masked_fill(eye, -1.0e9)
        top_paths = max(1, min(self.max_paths, n_nodes * (n_nodes - 1)))
        multihop_paths = 0
        if self.use_multihop_paths and n_nodes >= 3 and top_paths >= 4:
            multihop_paths = max(1, int(round(top_paths * self.multihop_path_fraction)))
            multihop_paths = min(multihop_paths, top_paths - 1)
        direct_paths = max(1, top_paths - multihop_paths)
        prior_paths = 0
        if (
            self.prior_coverage_fraction > 0.0
            and prior_adjacency is not None
            and (
                (prior_adjacency.ndim == 2 and tuple(prior_adjacency.shape) == (n_nodes, n_nodes))
                or (prior_adjacency.ndim == 3 and tuple(prior_adjacency.shape) == (batch, n_nodes, n_nodes))
            )
            and direct_paths >= 4
        ):
            prior = prior_adjacency.to(device=node_states.device)
            prior_edges = int((prior > 0.0).sum().item())
            if prior_edges > 0:
                available_prior_edges = prior_edges if prior.ndim == 2 else max(1, prior_edges // batch)
                prior_paths = max(1, int(round(direct_paths * self.prior_coverage_fraction)))
                prior_paths = min(prior_paths, direct_paths - 1, available_prior_edges)
        candidate_paths = 0
        if (
            self.candidate_coverage_fraction > 0.0
            and candidate_proposal_adjacency is not None
            and (
                (candidate_proposal_adjacency.ndim == 2 and tuple(candidate_proposal_adjacency.shape) == (n_nodes, n_nodes))
                or (
                    candidate_proposal_adjacency.ndim == 3
                    and tuple(candidate_proposal_adjacency.shape) == (batch, n_nodes, n_nodes)
                )
            )
            and direct_paths >= 4
        ):
            candidate_prior = candidate_proposal_adjacency.to(device=node_states.device)
            candidate_edges = int((candidate_prior > 0.0).sum().item())
            remaining_slots = max(0, direct_paths - prior_paths - 1)
            if candidate_edges > 0 and remaining_slots > 0:
                available_candidate_edges = (
                    candidate_edges if candidate_prior.ndim == 2 else max(1, candidate_edges // batch)
                )
                candidate_paths = max(1, int(round(direct_paths * self.candidate_coverage_fraction)))
                candidate_paths = min(candidate_paths, remaining_slots, available_candidate_edges)
        salience_paths = 0
        if (
            self.salience_coverage_fraction > 0.0
            and pair_salience is not None
            and pair_salience.ndim == 3
            and tuple(pair_salience.shape) == (batch, n_nodes, n_nodes)
            and direct_paths >= 4
        ):
            salience_edges = int((pair_salience > 0.0).sum().item())
            remaining_slots = max(0, direct_paths - prior_paths - candidate_paths - 1)
            if salience_edges > 0 and remaining_slots > 0:
                salience_paths = max(1, int(round(direct_paths * self.salience_coverage_fraction)))
                salience_paths = min(salience_paths, remaining_slots)
        base_direct_paths = max(1, direct_paths - prior_paths - candidate_paths - salience_paths)
        scores = masked_adjacency.reshape(batch, n_nodes * n_nodes)
        retention_scores = raw_proposal_adjacency.reshape(batch, n_nodes * n_nodes)
        global_paths = max(1, int(math.ceil(base_direct_paths * 0.5)))
        coverage_paths = max(0, base_direct_paths - global_paths)
        retention_paths = 0
        if (
            self.use_path_proposal_consistency
            and self.path_proposal_consistency_strength > 0.0
            and self.path_proposal_retention_fraction > 0.0
            and global_paths >= 2
        ):
            retention_paths = max(1, int(round(global_paths * self.path_proposal_retention_fraction)))
            retention_paths = min(retention_paths, global_paths - 1)
        if retention_paths > 0:
            _retained_weight, retained_index = torch.topk(retention_scores, k=retention_paths, dim=1)
            gated_global_scores = scores.clone()
            gated_global_scores.scatter_(1, retained_index, -1.0e9)
            _global_weight, gated_global_index = torch.topk(
                gated_global_scores,
                k=max(1, global_paths - retention_paths),
                dim=1,
            )
            global_index = torch.cat([retained_index, gated_global_index], dim=1)
        else:
            _global_weight, global_index = torch.topk(scores, k=global_paths, dim=1)
        if coverage_paths > 0:
            coverage_scores = scores.clone()
            if self.coverage_dedup_mode == "hard":
                coverage_scores.scatter_(1, global_index, -1.0e9)
            elif self.coverage_dedup_mode == "soft" and self.coverage_redundancy_penalty > 0.0:
                selected_scores = torch.gather(coverage_scores, 1, global_index)
                coverage_scores.scatter_(
                    1,
                    global_index,
                    selected_scores - float(self.coverage_redundancy_penalty),
                )
            coverage_adjacency = coverage_scores.view(batch, n_nodes, n_nodes)
            target_best_weight, target_best_source = torch.max(coverage_adjacency, dim=2)
            if feature_group_ids is not None and feature_group_ids.numel() == n_nodes:
                raw_group_ids = feature_group_ids.to(device=node_states.device, dtype=torch.long)
                _unique_groups, group_ids = torch.unique(raw_group_ids, sorted=True, return_inverse=True)
                n_groups = int(group_ids.max().item() + 1) if group_ids.numel() else 0
                if self.coverage_mode in {"group_pair", "group_pair_inclusive"} and n_groups > 1 and hasattr(torch.Tensor, "scatter_reduce_"):
                    target_index = torch.arange(n_nodes, device=node_states.device).repeat_interleave(n_nodes)
                    source_index = torch.arange(n_nodes, device=node_states.device).repeat(n_nodes)
                    target_group = group_ids[target_index]
                    source_group = group_ids[source_index]
                    pair_ids = target_group * n_groups + source_group
                    valid_group_pair = (
                        target_group.ne(source_group)
                        if self.coverage_mode == "group_pair"
                        else target_index.ne(source_index)
                    )
                    coverage_scores = coverage_scores.masked_fill(~valid_group_pair.unsqueeze(0), -1.0e9)
                    pair_weight = scores.new_full((batch, n_groups * n_groups), -1.0e9)
                    pair_weight.scatter_reduce_(
                        1,
                        pair_ids.unsqueeze(0).expand(batch, -1),
                        coverage_scores,
                        reduce="amax",
                        include_self=True,
                    )
                    local_k = min(coverage_paths, int(pair_weight.shape[1]))
                    _local_weight, local_pair = torch.topk(pair_weight, k=local_k, dim=1)
                    local_indices: list[torch.Tensor] = []
                    for pos in range(local_k):
                        selected_pair = local_pair[:, pos]
                        pair_mask = pair_ids.unsqueeze(0).eq(selected_pair.unsqueeze(1)) & valid_group_pair.unsqueeze(0)
                        pair_scores = coverage_scores.masked_fill(~pair_mask, -1.0e9)
                        _best_weight, best_index = torch.max(pair_scores, dim=1)
                        local_indices.append(best_index)
                    local_index = torch.stack(local_indices, dim=1)
                    local_target = torch.div(local_index, n_nodes, rounding_mode="floor")
                    local_source = local_index.remainder(n_nodes)
                else:
                    unique_groups = torch.unique(group_ids, sorted=True)
                    group_weights: list[torch.Tensor] = []
                    group_targets: list[torch.Tensor] = []
                    group_sources: list[torch.Tensor] = []
                    for group in unique_groups:
                        mask = group_ids.eq(group).unsqueeze(0)
                        group_score = target_best_weight.masked_fill(~mask, -1.0e9)
                        best_weight, best_target = torch.max(group_score, dim=1)
                        best_source = torch.gather(target_best_source, 1, best_target.unsqueeze(1)).squeeze(1)
                        group_weights.append(best_weight)
                        group_targets.append(best_target)
                        group_sources.append(best_source)
                    group_weight_matrix = torch.stack(group_weights, dim=1)
                    group_target_matrix = torch.stack(group_targets, dim=1)
                    group_source_matrix = torch.stack(group_sources, dim=1)
                    local_k = min(coverage_paths, int(group_weight_matrix.shape[1]))
                    _local_weight, local_group = torch.topk(group_weight_matrix, k=local_k, dim=1)
                    local_target = torch.gather(group_target_matrix, 1, local_group)
                    local_source = torch.gather(group_source_matrix, 1, local_group)
            else:
                local_k = min(coverage_paths, n_nodes)
                _local_weight, local_target = torch.topk(target_best_weight, k=local_k, dim=1)
                local_source = torch.gather(target_best_source, 1, local_target)
            local_index = local_target * n_nodes + local_source
            flat_index = torch.cat([global_index, local_index], dim=1)
        else:
            flat_index = global_index
        if prior_paths > 0 and prior_adjacency is not None:
            prior = prior_adjacency.to(device=node_states.device, dtype=node_states.dtype)
            if prior.ndim == 2 and tuple(prior.shape) == (n_nodes, n_nodes):
                flat_prior = prior.reshape(1, n_nodes * n_nodes).expand(batch, -1)
            elif prior.ndim == 3 and tuple(prior.shape) == (batch, n_nodes, n_nodes):
                flat_prior = prior.reshape(batch, n_nodes * n_nodes)
            else:
                flat_prior = torch.zeros_like(scores)
            positive_scores = scores.clamp(min=0.0)
            prior_scores = flat_prior * positive_scores
            if pair_salience is not None:
                prior_scores = prior_scores * (1.0 + pair_salience.reshape(batch, n_nodes * n_nodes))
            prior_scores = prior_scores.masked_fill(flat_prior <= 0.0, -1.0e9)
            prior_scores = prior_scores.masked_fill(scores <= 0.0, -1.0e9)
            de_duplicated_prior_scores = prior_scores.clone()
            de_duplicated_prior_scores.scatter_(1, flat_index, -1.0e9)
            if bool(de_duplicated_prior_scores.gt(-1.0e8).any().item()):
                prior_scores = de_duplicated_prior_scores
            _prior_weight, prior_index = torch.topk(prior_scores, k=prior_paths, dim=1)
            flat_index = torch.cat([flat_index, prior_index], dim=1)
        if salience_paths > 0 and pair_salience is not None:
            flat_salience_for_selection = pair_salience.reshape(batch, n_nodes * n_nodes)
            positive_scores = scores.clamp(min=0.0)
            salience_scores = flat_salience_for_selection * positive_scores
            salience_scores = salience_scores.masked_fill(flat_salience_for_selection <= 0.0, -1.0e9)
            salience_scores = salience_scores.masked_fill(scores <= 0.0, -1.0e9)
            de_duplicated_salience_scores = salience_scores.clone()
            de_duplicated_salience_scores.scatter_(1, flat_index, -1.0e9)
            if bool(de_duplicated_salience_scores.gt(-1.0e8).any().item()):
                salience_scores = de_duplicated_salience_scores
            _salience_weight, salience_index = torch.topk(salience_scores, k=salience_paths, dim=1)
            flat_index = torch.cat([flat_index, salience_index], dim=1)
        if candidate_paths > 0 and candidate_proposal_adjacency is not None:
            candidate_prior = candidate_proposal_adjacency.to(device=node_states.device, dtype=node_states.dtype).clamp(0.0, 1.0)
            if candidate_prior.ndim == 2 and tuple(candidate_prior.shape) == (n_nodes, n_nodes):
                flat_candidate = candidate_prior.reshape(1, n_nodes * n_nodes).expand(batch, -1)
            elif candidate_prior.ndim == 3 and tuple(candidate_prior.shape) == (batch, n_nodes, n_nodes):
                flat_candidate = candidate_prior.reshape(batch, n_nodes * n_nodes)
            else:
                flat_candidate = torch.zeros_like(scores)
            positive_scores = scores.clamp(min=0.0)
            candidate_scores = flat_candidate * positive_scores
            if pair_salience is not None:
                candidate_scores = candidate_scores * (1.0 + pair_salience.reshape(batch, n_nodes * n_nodes))
            candidate_scores = candidate_scores.masked_fill(flat_candidate <= 0.0, -1.0e9)
            candidate_scores = candidate_scores.masked_fill(scores <= 0.0, -1.0e9)
            de_duplicated_candidate_scores = candidate_scores.clone()
            de_duplicated_candidate_scores.scatter_(1, flat_index, -1.0e9)
            if bool(de_duplicated_candidate_scores.gt(-1.0e8).any().item()):
                candidate_scores = de_duplicated_candidate_scores
            _candidate_weight, candidate_index = torch.topk(candidate_scores, k=candidate_paths, dim=1)
            flat_index = torch.cat([flat_index, candidate_index], dim=1)
        if self.deduplicate_exact_paths:
            flat_index = _replace_duplicate_flat_paths(flat_index, scores)
        target = torch.div(flat_index, n_nodes, rounding_mode="floor")
        source = flat_index.remainder(n_nodes)
        bridge = torch.full_like(source, -1)
        hop_count = torch.ones_like(source)
        edge_weight = torch.gather(scores, 1, flat_index)
        edge_weight = torch.clamp(edge_weight, min=0.0)
        if multihop_paths > 0:
            positive_adjacency = adjacency.clamp(min=0.0)
            positive_adjacency = positive_adjacency.masked_fill(eye, 0.0)
            twohop_score = torch.sqrt(
                torch.clamp(
                    positive_adjacency.unsqueeze(3) * positive_adjacency.unsqueeze(1),
                    min=0.0,
                )
                + 1.0e-12
            )
            node_index = torch.arange(n_nodes, device=node_states.device)
            target_grid = node_index.view(n_nodes, 1, 1)
            bridge_grid = node_index.view(1, n_nodes, 1)
            source_grid = node_index.view(1, 1, n_nodes)
            valid_twohop = target_grid.ne(bridge_grid) & bridge_grid.ne(source_grid) & target_grid.ne(source_grid)
            if target_allowed_mask is not None and target_allowed_mask.numel() == n_nodes:
                allowed_targets = target_allowed_mask.to(device=node_states.device, dtype=torch.bool)
                if bool(allowed_targets.any().item()) and not bool(allowed_targets.all().item()):
                    valid_twohop = valid_twohop & allowed_targets.view(n_nodes, 1, 1)
            if bridge_allowed_mask is not None and bridge_allowed_mask.numel() == n_nodes:
                allowed_bridges = bridge_allowed_mask.to(device=node_states.device, dtype=torch.bool)
                if bool(allowed_bridges.any().item()) and not bool(allowed_bridges.all().item()):
                    valid_twohop = valid_twohop & allowed_bridges.view(1, n_nodes, 1)
            if source_allowed_mask is not None and source_allowed_mask.numel() == n_nodes:
                allowed_sources = source_allowed_mask.to(device=node_states.device, dtype=torch.bool)
                if bool(allowed_sources.any().item()) and not bool(allowed_sources.all().item()):
                    valid_twohop = valid_twohop & allowed_sources.view(1, 1, n_nodes)
            if pair_salience is not None and float(self.salience_selection_strength) > 0.0:
                salience = pair_salience.to(device=node_states.device, dtype=node_states.dtype)
                leg_salience = torch.maximum(
                    salience[:, :, :, None],
                    salience[:, None, :, :],
                )
                twohop_score = twohop_score + float(self.salience_selection_strength) * leg_salience
            twohop_score = twohop_score.masked_fill(~valid_twohop.unsqueeze(0), -1.0e9)
            flat_twohop = twohop_score.reshape(batch, n_nodes * n_nodes * n_nodes)
            local_k = min(multihop_paths, int(flat_twohop.shape[1]))
            _twohop_weight, twohop_index = torch.topk(flat_twohop, k=local_k, dim=1)
            twohop_target = torch.div(twohop_index, n_nodes * n_nodes, rounding_mode="floor")
            twohop_remainder = twohop_index.remainder(n_nodes * n_nodes)
            twohop_bridge = torch.div(twohop_remainder, n_nodes, rounding_mode="floor")
            twohop_source = twohop_remainder.remainder(n_nodes)
            twohop_edge_weight = torch.gather(flat_twohop, 1, twohop_index).clamp(min=0.0)
            source = torch.cat([source, twohop_source], dim=1)
            target = torch.cat([target, twohop_target], dim=1)
            bridge = torch.cat([bridge, twohop_bridge], dim=1)
            hop_count = torch.cat([hop_count, torch.full_like(twohop_source, 2)], dim=1)
            edge_weight = torch.cat([edge_weight, twohop_edge_weight], dim=1)
        prior_for_features = prior_feature_adjacency if prior_feature_adjacency is not None else prior_adjacency
        if prior_for_features is not None:
            prior = prior_for_features.to(device=node_states.device, dtype=node_states.dtype)
            if prior.ndim == 2 and prior.shape == (n_nodes, n_nodes):
                flat_prior = prior.reshape(1, n_nodes * n_nodes).expand(batch, -1)
                direct_prior_weight = torch.gather(flat_prior, 1, target[:, : flat_index.shape[1]] * n_nodes + source[:, : flat_index.shape[1]])
                if bridge.shape[1] > flat_index.shape[1]:
                    twohop_slice = slice(flat_index.shape[1], bridge.shape[1])
                    prior_tb = prior[target[:, twohop_slice], bridge[:, twohop_slice]]
                    prior_bs = prior[bridge[:, twohop_slice], source[:, twohop_slice]]
                    twohop_prior_weight = 0.5 * (prior_tb + prior_bs)
                    prior_weight = torch.cat([direct_prior_weight, twohop_prior_weight], dim=1)
                else:
                    prior_weight = direct_prior_weight
            elif prior.ndim == 3 and tuple(prior.shape) == (batch, n_nodes, n_nodes):
                flat_prior = prior.reshape(batch, n_nodes * n_nodes)
                direct_prior_weight = torch.gather(flat_prior, 1, target[:, : flat_index.shape[1]] * n_nodes + source[:, : flat_index.shape[1]])
                if bridge.shape[1] > flat_index.shape[1]:
                    twohop_slice = slice(flat_index.shape[1], bridge.shape[1])
                    batch_index = torch.arange(batch, device=node_states.device).unsqueeze(1)
                    prior_tb = prior[batch_index, target[:, twohop_slice], bridge[:, twohop_slice]]
                    prior_bs = prior[batch_index, bridge[:, twohop_slice], source[:, twohop_slice]]
                    twohop_prior_weight = 0.5 * (prior_tb + prior_bs)
                    prior_weight = torch.cat([direct_prior_weight, twohop_prior_weight], dim=1)
                else:
                    prior_weight = direct_prior_weight
            else:
                prior_weight = torch.zeros_like(edge_weight)
        else:
            prior_weight = torch.zeros_like(edge_weight)
        if pair_salience is not None:
            flat_salience = pair_salience.reshape(batch, n_nodes * n_nodes)
            direct_salience_weight = torch.gather(
                flat_salience,
                1,
                target[:, : flat_index.shape[1]] * n_nodes + source[:, : flat_index.shape[1]],
            )
            if bridge.shape[1] > flat_index.shape[1]:
                twohop_slice = slice(flat_index.shape[1], bridge.shape[1])
                salience = pair_salience.to(device=node_states.device, dtype=node_states.dtype).expand(batch, -1, -1)
                batch_index = torch.arange(batch, device=node_states.device).unsqueeze(1)
                sal_tb = salience[batch_index, target[:, twohop_slice], bridge[:, twohop_slice]]
                sal_bs = salience[batch_index, bridge[:, twohop_slice], source[:, twohop_slice]]
                twohop_salience_weight = torch.maximum(sal_tb, sal_bs)
                salience_weight = torch.cat([direct_salience_weight, twohop_salience_weight], dim=1)
            else:
                salience_weight = direct_salience_weight
        else:
            salience_weight = torch.zeros_like(edge_weight)
        flat_proposal_support = proposal_support_matrix.reshape(batch, n_nodes * n_nodes)
        flat_proposal_gate = proposal_gate_matrix.reshape(batch, n_nodes * n_nodes)
        direct_proposal_support = torch.gather(
            flat_proposal_support,
            1,
            target[:, : flat_index.shape[1]] * n_nodes + source[:, : flat_index.shape[1]],
        )
        direct_proposal_gate = torch.gather(
            flat_proposal_gate,
            1,
            target[:, : flat_index.shape[1]] * n_nodes + source[:, : flat_index.shape[1]],
        )
        if bridge.shape[1] > flat_index.shape[1]:
            twohop_slice = slice(flat_index.shape[1], bridge.shape[1])
            batch_index = torch.arange(batch, device=node_states.device).unsqueeze(1)
            proposal_tb = proposal_support_matrix[batch_index, target[:, twohop_slice], bridge[:, twohop_slice]]
            proposal_bs = proposal_support_matrix[batch_index, bridge[:, twohop_slice], source[:, twohop_slice]]
            proposal_gate_tb = proposal_gate_matrix[batch_index, target[:, twohop_slice], bridge[:, twohop_slice]]
            proposal_gate_bs = proposal_gate_matrix[batch_index, bridge[:, twohop_slice], source[:, twohop_slice]]
            proposal_support_weight = torch.cat(
                [direct_proposal_support, torch.maximum(proposal_tb, proposal_bs)],
                dim=1,
            )
            proposal_gate_weight = torch.cat(
                [direct_proposal_gate, torch.minimum(proposal_gate_tb, proposal_gate_bs)],
                dim=1,
            )
        else:
            proposal_support_weight = direct_proposal_support
            proposal_gate_weight = direct_proposal_gate

        gather_source = source.unsqueeze(-1).expand(-1, -1, hidden)
        gather_target = target.unsqueeze(-1).expand(-1, -1, hidden)
        src_h = torch.gather(node_states, 1, gather_source)
        dst_h = torch.gather(node_states, 1, gather_target)
        valid_bridge = bridge.ge(0)
        bridge_index = bridge.clamp(min=0).unsqueeze(-1).expand(-1, -1, hidden)
        bridge_h = torch.gather(node_states, 1, bridge_index)
        direct_interaction = src_h * dst_h
        twohop_interaction = 0.5 * (src_h * bridge_h + bridge_h * dst_h)
        interaction = torch.where(valid_bridge.unsqueeze(-1), twohop_interaction, direct_interaction)
        path_parts = [src_h, dst_h, dst_h - src_h, interaction, edge_weight.unsqueeze(-1), prior_weight.unsqueeze(-1)]
        if self.use_task_salience:
            path_parts.append(salience_weight.unsqueeze(-1))
        path_input = torch.cat(path_parts, dim=-1)
        path_token = self.path_encoder(path_input)
        importance = self.importance(path_token).squeeze(-1)
        context_importance = torch.zeros_like(importance)
        sample_query = self.context_query(node_pool).unsqueeze(1)
        if self.use_context_router:
            context_importance = self.context_importance(path_token * sample_query).squeeze(-1)
            importance = importance + context_importance
        reliability_parts = [path_token, edge_weight.unsqueeze(-1), prior_weight.unsqueeze(-1)]
        if self.use_task_salience:
            reliability_parts.append(salience_weight.unsqueeze(-1))
        reliability_context = torch.zeros_like(importance)
        if self.use_reliability:
            reliability_logit = self.reliability(torch.cat(reliability_parts, dim=-1)).squeeze(-1)
            if self.use_path_reliability_calibrator and self.context_reliability is not None:
                sample_for_path = sample_query.expand(-1, path_token.shape[1], -1)
                context_parts = [
                    path_token,
                    sample_for_path,
                    path_token * sample_for_path,
                    edge_weight.unsqueeze(-1),
                    prior_weight.unsqueeze(-1),
                ]
                if self.use_task_salience:
                    context_parts.append(salience_weight.unsqueeze(-1))
                raw_reliability_context = self.context_reliability(torch.cat(context_parts, dim=-1)).squeeze(-1)
                reliability_context = float(self.path_reliability_context_scale) * torch.tanh(raw_reliability_context)
                reliability_logit = reliability_logit + reliability_context
            reliability = torch.sigmoid(reliability_logit)
            reliability_adjustment = F.softplus(self.reliability_gain) * torch.tanh(reliability_logit)
        else:
            reliability = torch.ones_like(importance)
            reliability_adjustment = torch.zeros_like(importance)
        path_admission_logit = torch.zeros_like(importance)
        path_admission_gate = torch.full_like(importance, 0.5)
        path_admission_adjustment = torch.zeros_like(importance)
        if self.path_admission is not None:
            sample_for_path = sample_query.expand(-1, path_token.shape[1], -1)
            admission_parts = [
                path_token,
                sample_for_path,
                path_token * sample_for_path,
                edge_weight.unsqueeze(-1),
                prior_weight.unsqueeze(-1),
            ]
            if self.use_task_salience:
                admission_parts.append(salience_weight.unsqueeze(-1))
            path_admission_logit = self.path_admission(torch.cat(admission_parts, dim=-1)).squeeze(-1)
            path_admission_gate = torch.sigmoid(path_admission_logit)
            path_admission_adjustment = float(self.path_admission_strength) * torch.tanh(path_admission_logit)
        salience_for_consistency = salience_weight if self.use_task_salience else torch.zeros_like(edge_weight)
        if self.path_prior_consistency_support_mode == "dynamic":
            path_prior_consistency_support = edge_weight
        elif self.path_prior_consistency_support_mode == "agreement" and self.use_task_salience:
            path_prior_consistency_support = torch.minimum(edge_weight, salience_for_consistency)
        elif self.path_prior_consistency_support_mode == "class_blend" and self.use_task_salience:
            class_factor = float(self.path_prior_consistency_class_floor) + (
                1.0 - float(self.path_prior_consistency_class_floor)
            ) * salience_for_consistency
            path_prior_consistency_support = edge_weight * class_factor
        else:
            path_prior_consistency_support = torch.maximum(edge_weight, salience_for_consistency)
        path_prior_consistency_gate = torch.full_like(importance, 0.5)
        path_prior_consistency_adjustment = torch.zeros_like(importance)
        if self.use_path_prior_consistency and self.path_prior_consistency_strength > 0.0:
            path_prior_consistency_support = path_prior_consistency_support.clamp(0.0, 1.0)
            path_prior_consistency_gate = torch.sigmoid(
                (path_prior_consistency_support - float(self.path_prior_consistency_threshold))
                / float(self.path_prior_consistency_temperature)
            )
            path_prior_consistency_adjustment = (
                float(self.path_prior_consistency_strength)
                * prior_weight.clamp(0.0, 1.0)
                * (2.0 * path_prior_consistency_gate - 1.0)
            )
        raw_path_evidence_consistency_support = salience_for_consistency.clamp(0.0, 1.0)
        if self.path_evidence_consistency_support_mode == "relative":
            max_support = raw_path_evidence_consistency_support.max(dim=1, keepdim=True).values
            path_evidence_consistency_support = torch.where(
                max_support.gt(1.0e-8),
                raw_path_evidence_consistency_support / torch.clamp(max_support, min=1.0e-8),
                raw_path_evidence_consistency_support,
            )
        else:
            path_evidence_consistency_support = raw_path_evidence_consistency_support
        path_evidence_consistency_gate = torch.full_like(importance, 0.5)
        path_evidence_consistency_adjustment = torch.zeros_like(importance)
        if (
            self.use_path_evidence_consistency
            and self.path_evidence_consistency_strength > 0.0
            and pair_salience is not None
        ):
            path_evidence_consistency_gate = torch.sigmoid(
                (path_evidence_consistency_support - float(self.path_evidence_consistency_threshold))
                / float(self.path_evidence_consistency_temperature)
            )
            evidence_scale = float(self.path_evidence_consistency_floor) + (
                1.0 - float(self.path_evidence_consistency_floor)
            ) * path_evidence_consistency_support
            path_evidence_consistency_adjustment = (
                float(self.path_evidence_consistency_strength)
                * evidence_scale
                * (2.0 * path_evidence_consistency_gate - 1.0)
            )
        weight_logits = (
            importance
            + reliability_adjustment
            + path_admission_adjustment
            + path_prior_consistency_adjustment
            + path_evidence_consistency_adjustment
        )
        path_weights = torch.softmax(weight_logits, dim=1)
        path_count = int(source.shape[1])
        previous_mask = torch.tril(
            torch.ones((path_count, path_count), device=node_states.device, dtype=torch.bool),
            diagonal=-1,
        )
        unique_base = n_nodes + 1
        bridge_unique = torch.where(bridge.ge(0), bridge, torch.full_like(bridge, n_nodes))
        unique_index = (target * unique_base + bridge_unique) * n_nodes + source
        duplicate_flags = unique_index.unsqueeze(2).eq(unique_index.unsqueeze(1)) & previous_mask.unsqueeze(0)
        path_duplicate_rate = duplicate_flags.any(dim=2).to(dtype=node_states.dtype).mean(dim=1)
        fused = torch.sum(path_token * path_weights.unsqueeze(-1), dim=1)
        return fused, {
            "path_weights": path_weights,
            "path_reliability": reliability,
            "path_reliability_gain": F.softplus(self.reliability_gain).expand(batch),
            "path_edge_weight": edge_weight,
            "path_context_importance": context_importance,
            "path_reliability_context": reliability_context,
            "path_admission_gate": path_admission_gate,
            "path_admission_logit": path_admission_logit,
            "path_admission_adjustment": path_admission_adjustment,
            "path_prior_consistency_support": path_prior_consistency_support,
            "path_prior_consistency_gate": path_prior_consistency_gate,
            "path_prior_consistency_adjustment": path_prior_consistency_adjustment,
            "path_evidence_consistency_support": path_evidence_consistency_support,
            "path_evidence_consistency_gate": path_evidence_consistency_gate,
            "path_evidence_consistency_adjustment": path_evidence_consistency_adjustment,
            "path_proposal_consistency_support": proposal_support_weight,
            "path_proposal_consistency_gate": proposal_gate_weight,
            "path_proposal_consistency_effective_strength": proposal_effective_strength,
            "path_candidate_quota": torch.full((batch,), int(candidate_paths), device=node_states.device, dtype=node_states.dtype),
            "path_prior_weight": prior_weight,
            "path_salience_weight": salience_weight,
            "path_source": source,
            "path_target": target,
            "path_bridge": bridge,
            "path_hop_count": hop_count,
            "path_duplicate_rate": path_duplicate_rate,
        }


class MSGSERPFNet(nn.Module):
    """Multi-Scale Graph Selective Evidence Network with Reliable Path Fusion."""

    model_family = "ms_gse_rpf"

    def __init__(self, config: MSGSERPFConfig) -> None:
        super().__init__()
        self.config = config
        self.tokenizer = MultiScaleEventTokenizer(
            config.n_features,
            config.hidden_dim,
            config.scales,
            config.dropout,
            config.temporal_encoder_mode,
        )
        self.temporal_evidence = TemporalDescriptorEvidence(config.hidden_dim, config.dropout)
        self.temporal_mixer: nn.Module | None = None
        if config.use_temporal_mixer:
            mixer_type = str(config.temporal_mixer_type or "conv").strip().lower()
            if mixer_type in {"gru", "recurrent"}:
                self.temporal_mixer = RecurrentTemporalMixer(
                    config.n_features,
                    config.hidden_dim,
                    config.dropout,
                    depth=config.temporal_mixer_depth,
                    bidirectional=False,
                )
            elif mixer_type in {"bigru", "bidirectional_gru", "recurrent_bi"}:
                self.temporal_mixer = RecurrentTemporalMixer(
                    config.n_features,
                    config.hidden_dim,
                    config.dropout,
                    depth=config.temporal_mixer_depth,
                    bidirectional=True,
                )
            elif mixer_type in {"conv", "tcn", "temporal_conv"}:
                self.temporal_mixer = TemporalConvMixer(
                    config.n_features,
                    config.hidden_dim,
                    config.dropout,
                    depth=config.temporal_mixer_depth,
                )
            else:
                raise ValueError(f"Unknown temporal_mixer_type: {config.temporal_mixer_type}")
        self.graph = DynamicVariableGraph(config.hidden_dim, config.graph_top_k, config.use_graph)
        self.memory = GraphSelectiveMemory(config.hidden_dim, config.dropout, config.use_graph)
        self.path_fusion = ReliablePathFusion(
            config.hidden_dim,
            config.max_paths,
            config.use_reliability,
            config.use_path_fusion,
            config.path_coverage_mode,
            config.coverage_dedup_mode,
            config.coverage_redundancy_penalty,
            config.deduplicate_exact_paths,
            config.use_task_salience,
            config.salience_selection_strength,
            config.salience_coverage_fraction,
            config.use_multihop_paths,
            config.multihop_path_fraction,
            config.use_context_router,
            config.prior_coverage_fraction,
            config.candidate_coverage_fraction,
            config.use_path_reliability_calibrator,
            config.path_reliability_context_scale,
            config.use_learned_path_admission,
            config.path_admission_strength,
            config.use_path_prior_consistency,
            config.path_prior_consistency_strength,
            config.path_prior_consistency_threshold,
            config.path_prior_consistency_temperature,
            config.path_prior_consistency_support_mode,
            config.path_prior_consistency_class_floor,
            config.use_path_evidence_consistency,
            config.path_evidence_consistency_strength,
            config.path_evidence_consistency_threshold,
            config.path_evidence_consistency_temperature,
            config.path_evidence_consistency_floor,
            config.path_evidence_consistency_support_mode,
            config.use_path_proposal_consistency,
            config.path_proposal_consistency_strength,
            config.path_proposal_consistency_threshold,
            config.path_proposal_consistency_temperature,
            config.path_proposal_consistency_floor,
            config.path_proposal_consistency_support_mode,
            config.path_proposal_consistency_protected_strength,
            config.path_proposal_retention_fraction,
        )
        self.node_context = nn.Sequential(
            nn.LayerNorm(config.hidden_dim),
            nn.Linear(config.hidden_dim, config.hidden_dim),
            nn.GELU(),
        )
        self.residual_evidence = nn.Sequential(
            nn.Linear(1, config.hidden_dim),
            nn.GELU(),
            nn.LayerNorm(config.hidden_dim),
        )
        self.evidence_norm = nn.LayerNorm(config.hidden_dim)
        self.head = nn.Sequential(
            nn.LayerNorm(config.hidden_dim * 2),
            nn.Dropout(config.dropout),
            nn.Linear(config.hidden_dim * 2, config.hidden_dim),
            nn.GELU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.hidden_dim, config.n_classes),
        )
        self.path_aux_head = nn.Sequential(
            nn.LayerNorm(config.hidden_dim),
            nn.Dropout(config.dropout),
            nn.Linear(config.hidden_dim, config.n_classes),
        )
        self.coarse_head = nn.Sequential(
            nn.LayerNorm(config.hidden_dim * 2),
            nn.Dropout(config.dropout),
            nn.Linear(config.hidden_dim * 2, config.hidden_dim),
            nn.GELU(),
            nn.Linear(config.hidden_dim, 2),
        )
        self.health_head = nn.Sequential(
            nn.LayerNorm(config.hidden_dim * 2),
            nn.Dropout(config.dropout),
            nn.Linear(config.hidden_dim * 2, config.hidden_dim),
            nn.GELU(),
            nn.Linear(config.hidden_dim, 1),
        )
        self.rul_head = nn.Sequential(
            nn.LayerNorm(config.hidden_dim * 2),
            nn.Dropout(config.dropout),
            nn.Linear(config.hidden_dim * 2, config.hidden_dim),
            nn.GELU(),
            nn.Linear(config.hidden_dim, 1),
        )
        self.temporal_rul_head = (
            nn.Sequential(
                nn.LayerNorm(config.hidden_dim),
                nn.Dropout(config.dropout),
                nn.Linear(config.hidden_dim, config.hidden_dim),
                nn.GELU(),
                nn.Linear(config.hidden_dim, 1),
            )
            if self.temporal_mixer is not None
            else None
        )
        anchor_fusion_in = config.hidden_dim * 4
        self.rul_anchor_delta_head = (
            nn.Sequential(
                nn.LayerNorm(anchor_fusion_in),
                nn.Dropout(config.dropout),
                nn.Linear(anchor_fusion_in, config.hidden_dim),
                nn.GELU(),
                nn.Linear(config.hidden_dim, 1),
            )
            if self.temporal_mixer is not None and bool(config.use_rul_temporal_anchor_fusion)
            else None
        )
        self.rul_anchor_gate_head = (
            nn.Sequential(
                nn.LayerNorm(anchor_fusion_in),
                nn.Dropout(config.dropout),
                nn.Linear(anchor_fusion_in, config.hidden_dim),
                nn.GELU(),
                nn.Linear(config.hidden_dim, 1),
            )
            if self.temporal_mixer is not None and bool(config.use_rul_temporal_anchor_fusion)
            else None
        )
        if self.rul_anchor_delta_head is not None:
            nn.init.zeros_(self.rul_anchor_delta_head[-1].weight)
            nn.init.zeros_(self.rul_anchor_delta_head[-1].bias)
        if self.rul_anchor_gate_head is not None:
            nn.init.zeros_(self.rul_anchor_gate_head[-1].weight)
            nn.init.constant_(self.rul_anchor_gate_head[-1].bias, float(config.rul_anchor_gate_bias))
        self.class_evidence_router = (
            nn.Sequential(
                nn.LayerNorm(config.hidden_dim),
                nn.Dropout(config.dropout),
                nn.Linear(config.hidden_dim, config.n_classes),
            )
            if config.use_class_conditioned_evidence
            else None
        )
        self.forecast_head = nn.Linear(config.hidden_dim, 1)
        self.edge_calibrator = (
            EdgePriorCalibrator(
                config.hidden_dim,
                floor=config.edge_calibrator_floor,
                init_bias=config.edge_calibrator_init_bias,
            )
            if config.use_edge_calibrator
            else None
        )
        self.edge_family_router = (
            nn.Sequential(
                nn.LayerNorm(config.hidden_dim),
                nn.Dropout(config.dropout),
                nn.Linear(config.hidden_dim, max(1, int(config.edge_family_count))),
            )
            if config.use_edge_family_router
            else None
        )
        if config.use_path_reliability_calibrator:
            self.path_fusion.enable_path_reliability_calibrator()
        self.register_buffer("prior_adjacency", torch.empty(0), persistent=False)
        self.register_buffer("path_candidate_prior", torch.empty(0), persistent=False)
        self.register_buffer("edge_family_priors", torch.empty(0), persistent=False)
        self.register_buffer("feature_group_ids", torch.empty(0, dtype=torch.long), persistent=False)
        self.register_buffer("task_salience", torch.empty(0), persistent=False)
        self.register_buffer("path_evidence", torch.empty(0), persistent=False)
        self.register_buffer("class_path_evidence", torch.empty(0), persistent=False)
        self.register_buffer("candidate_protected_class_mask", torch.empty(0), persistent=False)
        self.register_buffer("path_target_mask", torch.empty(0, dtype=torch.bool), persistent=False)
        self.register_buffer("path_source_mask", torch.empty(0, dtype=torch.bool), persistent=False)
        self.register_buffer("path_bridge_mask", torch.empty(0, dtype=torch.bool), persistent=False)

    def set_graph_prior(self, prior_adjacency: torch.Tensor | np.ndarray | None) -> None:
        if prior_adjacency is None:
            self.prior_adjacency = torch.empty(0)
            return
        prior = torch.as_tensor(prior_adjacency, dtype=torch.float32)
        if prior.ndim != 2 or prior.shape[0] != self.config.n_features or prior.shape[1] != self.config.n_features:
            raise ValueError("Graph prior shape must be [n_features, n_features].")
        self.prior_adjacency = prior

    def set_path_candidate_prior(self, prior_adjacency: torch.Tensor | np.ndarray | None) -> None:
        if prior_adjacency is None:
            self.path_candidate_prior = torch.empty(0)
            return
        prior = torch.as_tensor(prior_adjacency, dtype=torch.float32)
        if prior.ndim != 2 or prior.shape[0] != self.config.n_features or prior.shape[1] != self.config.n_features:
            raise ValueError("Path candidate prior shape must be [n_features, n_features].")
        prior = prior.clamp(0.0, 1.0)
        diagonal = torch.arange(self.config.n_features)
        prior[diagonal, diagonal] = 0.0
        self.path_candidate_prior = prior

    def set_edge_family_priors(self, edge_family_priors: torch.Tensor | np.ndarray | None) -> None:
        if edge_family_priors is None:
            self.edge_family_priors = torch.empty(0)
            return
        priors = torch.as_tensor(edge_family_priors, dtype=torch.float32)
        expected = (self.config.edge_family_count, self.config.n_features, self.config.n_features)
        if priors.ndim != 3 or tuple(priors.shape) != expected:
            raise ValueError("Edge family priors must have shape [edge_family_count, n_features, n_features].")
        priors = priors.clamp(0.0, 1.0)
        diagonal = torch.arange(self.config.n_features)
        priors[:, diagonal, diagonal] = 0.0
        self.edge_family_priors = priors

    def set_feature_groups(self, feature_group_ids: torch.Tensor | np.ndarray | Sequence[int] | None) -> None:
        if feature_group_ids is None:
            self.feature_group_ids = torch.empty(0, dtype=torch.long)
            return
        groups = torch.as_tensor(feature_group_ids, dtype=torch.long)
        if groups.ndim != 1 or groups.numel() != self.config.n_features:
            raise ValueError("Feature group ids must have shape [n_features].")
        self.feature_group_ids = groups

    def set_task_salience(self, task_salience: torch.Tensor | np.ndarray | Sequence[float] | None) -> None:
        if task_salience is None:
            self.task_salience = torch.empty(0)
            return
        salience = torch.as_tensor(task_salience, dtype=torch.float32)
        if salience.ndim != 1 or salience.numel() != self.config.n_features:
            raise ValueError("Task salience must have shape [n_features].")
        self.task_salience = salience.clamp(0.0, 1.0)

    def set_path_evidence(self, path_evidence: torch.Tensor | np.ndarray | None) -> None:
        if path_evidence is None:
            self.path_evidence = torch.empty(0)
            return
        evidence = torch.as_tensor(path_evidence, dtype=torch.float32)
        expected = (self.config.n_features, self.config.n_features)
        if evidence.ndim != 2 or tuple(evidence.shape) != expected:
            raise ValueError("Path evidence must have shape [n_features, n_features].")
        evidence = evidence.clamp(0.0, 1.0)
        evidence.fill_diagonal_(0.0)
        self.path_evidence = evidence

    def set_class_path_evidence(self, class_path_evidence: torch.Tensor | np.ndarray | None) -> None:
        if class_path_evidence is None:
            self.class_path_evidence = torch.empty(0)
            return
        evidence = torch.as_tensor(class_path_evidence, dtype=torch.float32)
        expected = (self.config.n_classes, self.config.n_features, self.config.n_features)
        if evidence.ndim != 3 or tuple(evidence.shape) != expected:
            raise ValueError("Class path evidence must have shape [n_classes, n_features, n_features].")
        evidence = evidence.clamp(0.0, 1.0)
        diagonal = torch.arange(self.config.n_features)
        evidence[:, diagonal, diagonal] = 0.0
        self.class_path_evidence = evidence

    def set_candidate_protected_classes(self, classes: Sequence[int] | torch.Tensor | np.ndarray | None) -> None:
        if classes is None:
            self.candidate_protected_class_mask = torch.empty(0)
            return
        mask = torch.zeros(self.config.n_classes, dtype=torch.float32)
        for cls in torch.as_tensor(classes, dtype=torch.long).reshape(-1).tolist():
            if 0 <= int(cls) < self.config.n_classes:
                mask[int(cls)] = 1.0
        self.candidate_protected_class_mask = mask if bool(mask.sum().item() > 0) else torch.empty(0)

    def set_candidate_protected_class_weights(
        self,
        weights: Sequence[float] | torch.Tensor | np.ndarray | None,
    ) -> None:
        if weights is None:
            self.candidate_protected_class_mask = torch.empty(0)
            return
        values = torch.as_tensor(weights, dtype=torch.float32).reshape(-1)
        if values.numel() != self.config.n_classes:
            raise ValueError("Candidate protected class weights must have shape [n_classes].")
        values = values.clamp(0.0, 1.0)
        self.candidate_protected_class_mask = values if bool(values.sum().item() > 0.0) else torch.empty(0)

    def set_path_target_mask(self, target_allowed_mask: torch.Tensor | np.ndarray | Sequence[bool] | None) -> None:
        if target_allowed_mask is None:
            self.path_target_mask = torch.empty(0, dtype=torch.bool)
            return
        mask = torch.as_tensor(target_allowed_mask, dtype=torch.bool)
        if mask.ndim != 1 or mask.numel() != self.config.n_features:
            raise ValueError("Path target mask must have shape [n_features].")
        if not bool(mask.any().item()):
            raise ValueError("Path target mask must allow at least one target feature.")
        self.path_target_mask = mask

    def set_path_source_mask(self, source_allowed_mask: torch.Tensor | np.ndarray | Sequence[bool] | None) -> None:
        if source_allowed_mask is None:
            self.path_source_mask = torch.empty(0, dtype=torch.bool)
            return
        mask = torch.as_tensor(source_allowed_mask, dtype=torch.bool)
        if mask.ndim != 1 or mask.numel() != self.config.n_features:
            raise ValueError("Path source mask must have shape [n_features].")
        if not bool(mask.any().item()):
            raise ValueError("Path source mask must allow at least one source feature.")
        self.path_source_mask = mask

    def set_path_bridge_mask(self, bridge_allowed_mask: torch.Tensor | np.ndarray | Sequence[bool] | None) -> None:
        if bridge_allowed_mask is None:
            self.path_bridge_mask = torch.empty(0, dtype=torch.bool)
            return
        mask = torch.as_tensor(bridge_allowed_mask, dtype=torch.bool)
        if mask.ndim != 1 or mask.numel() != self.config.n_features:
            raise ValueError("Path bridge mask must have shape [n_features].")
        if not bool(mask.any().item()):
            raise ValueError("Path bridge mask must allow at least one bridge feature.")
        self.path_bridge_mask = mask

    def forward(self, x: torch.Tensor, *, return_diagnostics: bool = False) -> dict[str, Any]:
        event_tokens, scale_weights = self.tokenizer(x)
        if self.config.use_temporal_descriptors:
            event_tokens = event_tokens + float(self.config.temporal_descriptor_weight) * self.temporal_evidence(x)
        prior = self.prior_adjacency if self.prior_adjacency.numel() else None
        edge_calibrator_gate: torch.Tensor | None = None
        calibrated_prior: torch.Tensor | None = prior
        if self.edge_calibrator is not None and prior is not None:
            calibrated_prior, edge_calibrator_gate = self.edge_calibrator(event_tokens, prior)
            if float(torch.max(calibrated_prior).detach().cpu().item()) <= 0.0:
                calibrated_prior = prior
        adjacency = self.graph(event_tokens, prior_adjacency=calibrated_prior, prior_strength=self.config.prior_strength)
        node_states = self.memory(x, event_tokens, adjacency)
        reconstruction = self.forecast_head(node_states).squeeze(-1)
        if self.config.use_residual_evidence:
            residual = torch.abs(reconstruction - x[:, -1, :]).unsqueeze(-1)
            evidence_states = self.evidence_norm(node_states + self.residual_evidence(residual))
        else:
            evidence_states = node_states
        feature_groups = self.feature_group_ids if self.feature_group_ids.numel() else None
        task_salience = self.task_salience if self.task_salience.numel() else None
        path_evidence = self.path_evidence if self.path_evidence.numel() else None
        edge_family_router_logits: torch.Tensor | None = None
        edge_family_router_weights: torch.Tensor | None = None
        edge_family_routed_prior: torch.Tensor | None = None
        evidence_router_logits: torch.Tensor | None = None
        class_evidence_gate: torch.Tensor | None = None
        class_evidence_admission: torch.Tensor | None = None
        routed_class_path_evidence: torch.Tensor | None = None
        if (
            self.config.use_class_conditioned_evidence
            and self.class_evidence_router is not None
            and self.class_path_evidence.numel()
        ):
            evidence_router_logits = self.class_evidence_router(evidence_states.mean(dim=1))
            router_temperature = max(1.0e-3, float(self.config.class_evidence_router_temperature))
            class_gate = torch.softmax(evidence_router_logits / router_temperature, dim=1)
            router_top_k = int(self.config.class_evidence_router_top_k)
            if router_top_k > 0 and router_top_k < class_gate.shape[1]:
                _top_values, top_index = torch.topk(class_gate, k=router_top_k, dim=1)
                top_mask = torch.zeros_like(class_gate)
                top_mask.scatter_(1, top_index, 1.0)
                class_gate = class_gate * top_mask
                class_gate = class_gate / torch.clamp(class_gate.sum(dim=1, keepdim=True), min=1.0e-8)
            class_evidence_gate = class_gate
            class_evidence = self.class_path_evidence.to(device=x.device, dtype=evidence_states.dtype)
            sample_path_evidence = torch.einsum("bc,ctu->btu", class_gate, class_evidence)
            if float(self.config.class_evidence_gate_threshold) > 0.0:
                confidence = torch.max(class_gate, dim=1).values
                temperature = max(1.0e-3, float(self.config.class_evidence_gate_temperature))
                floor = float(min(1.0, max(0.0, self.config.class_evidence_gate_floor)))
                class_evidence_admission = floor + (1.0 - floor) * torch.sigmoid(
                    (confidence - float(self.config.class_evidence_gate_threshold)) / temperature
                )
                sample_path_evidence = sample_path_evidence * class_evidence_admission.view(-1, 1, 1)
            else:
                class_evidence_admission = torch.ones(x.shape[0], device=x.device, dtype=evidence_states.dtype)
            routed_class_path_evidence = sample_path_evidence
            if path_evidence is not None:
                static_evidence = path_evidence.to(device=x.device, dtype=evidence_states.dtype).unsqueeze(0)
                path_evidence = torch.maximum(sample_path_evidence, static_evidence)
            else:
                path_evidence = sample_path_evidence
        path_candidate_prior = self.path_candidate_prior if self.path_candidate_prior.numel() else None
        candidate_prior_admission_gate: torch.Tensor | None = None
        candidate_prior_admission_support: torch.Tensor | None = None
        candidate_prior_admission_mask: torch.Tensor | None = None
        candidate_protected_class_mass: torch.Tensor | None = None
        if (
            class_evidence_gate is not None
            and self.candidate_protected_class_mask.numel() == self.config.n_classes
        ):
            protected_mask = self.candidate_protected_class_mask.to(device=x.device, dtype=evidence_states.dtype)
            candidate_protected_class_mass = torch.sum(class_evidence_gate * protected_mask.view(1, -1), dim=1)
            candidate_protected_class_mass = candidate_protected_class_mass.clamp(0.0, 1.0)
        candidate_prior_overlay: torch.Tensor | None = None
        candidate_prior_base: torch.Tensor | None = None
        rpf_feature_prior: torch.Tensor | None = None
        rpf_candidate_proposal_prior: torch.Tensor | None = None
        rpf_base_prior = (
            calibrated_prior
            if bool(self.config.use_candidate_prior_admission) and path_candidate_prior is not None
            else path_candidate_prior if path_candidate_prior is not None else calibrated_prior
        )
        rpf_prior = rpf_base_prior
        if (
            self.edge_family_router is not None
            and self.edge_family_priors.numel()
            and int(self.edge_family_priors.shape[0]) == max(1, int(self.config.edge_family_count))
        ):
            edge_family_router_logits = self.edge_family_router(evidence_states.mean(dim=1))
            temperature = max(1.0e-3, float(self.config.edge_family_router_temperature))
            raw_family_weights = torch.softmax(edge_family_router_logits / temperature, dim=1)
            floor = float(min(0.95, max(0.0, self.config.edge_family_router_floor)))
            uniform = torch.full_like(raw_family_weights, 1.0 / max(1, raw_family_weights.shape[1]))
            edge_family_router_weights = floor * uniform + (1.0 - floor) * raw_family_weights
            family_priors = self.edge_family_priors.to(device=x.device, dtype=evidence_states.dtype)
            edge_family_routed_prior = torch.einsum("bf,fij->bij", edge_family_router_weights, family_priors)
            if rpf_base_prior is not None:
                base_prior = rpf_base_prior.to(device=x.device, dtype=evidence_states.dtype)
                if base_prior.ndim == 2 and tuple(base_prior.shape) == (self.config.n_features, self.config.n_features):
                    base_prior = base_prior.unsqueeze(0).expand(x.shape[0], -1, -1)
                if base_prior.ndim == 3 and tuple(base_prior.shape) == (x.shape[0], self.config.n_features, self.config.n_features):
                    blend = float(min(1.0, max(0.0, self.config.edge_family_router_blend)))
                    edge_family_routed_prior = (1.0 - blend) * base_prior + blend * edge_family_routed_prior
            rpf_prior = edge_family_routed_prior
        if bool(self.config.use_candidate_prior_admission) and path_candidate_prior is not None:
            candidate_prior = path_candidate_prior.to(device=x.device, dtype=evidence_states.dtype).clamp(0.0, 1.0)
            if candidate_prior.ndim == 2 and tuple(candidate_prior.shape) == (self.config.n_features, self.config.n_features):
                candidate_prior = candidate_prior.unsqueeze(0).expand(x.shape[0], -1, -1)
            elif candidate_prior.ndim != 3 or tuple(candidate_prior.shape) != (
                x.shape[0],
                self.config.n_features,
                self.config.n_features,
            ):
                candidate_prior = torch.zeros(
                    (x.shape[0], self.config.n_features, self.config.n_features),
                    device=x.device,
                    dtype=evidence_states.dtype,
                )
            if rpf_prior is not None:
                base_prior = rpf_prior.to(device=x.device, dtype=evidence_states.dtype).clamp(0.0, 1.0)
                if base_prior.ndim == 2 and tuple(base_prior.shape) == (self.config.n_features, self.config.n_features):
                    base_prior = base_prior.unsqueeze(0).expand(x.shape[0], -1, -1)
                elif base_prior.ndim != 3 or tuple(base_prior.shape) != (
                    x.shape[0],
                    self.config.n_features,
                    self.config.n_features,
                ):
                    base_prior = torch.zeros_like(candidate_prior)
            else:
                base_prior = torch.zeros_like(candidate_prior)
            evidence_support: torch.Tensor | None = None
            if routed_class_path_evidence is not None and path_evidence is not None:
                evidence_support = torch.maximum(
                    routed_class_path_evidence.to(device=x.device, dtype=evidence_states.dtype),
                    path_evidence.to(device=x.device, dtype=evidence_states.dtype),
                )
            elif routed_class_path_evidence is not None:
                evidence_support = routed_class_path_evidence.to(device=x.device, dtype=evidence_states.dtype)
            elif path_evidence is not None:
                evidence_support = path_evidence.to(device=x.device, dtype=evidence_states.dtype)
            if evidence_support is None:
                evidence_support = torch.zeros_like(candidate_prior)
            elif evidence_support.ndim == 2 and tuple(evidence_support.shape) == (
                self.config.n_features,
                self.config.n_features,
            ):
                evidence_support = evidence_support.unsqueeze(0).expand(x.shape[0], -1, -1)
            elif evidence_support.ndim != 3 or tuple(evidence_support.shape) != (
                x.shape[0],
                self.config.n_features,
                self.config.n_features,
            ):
                evidence_support = torch.zeros_like(candidate_prior)
            evidence_support = evidence_support.clamp(0.0, 1.0)
            support_mode = str(self.config.candidate_prior_admission_support_mode or "relative_evidence").strip().lower()
            if support_mode in {"relative", "relative_evidence"}:
                max_support = evidence_support.reshape(x.shape[0], -1).max(dim=1).values.view(x.shape[0], 1, 1)
                candidate_prior_admission_support = torch.where(
                    max_support > 1.0e-8,
                    evidence_support / torch.clamp(max_support, min=1.0e-8),
                    evidence_support,
                )
            else:
                candidate_prior_admission_support = evidence_support
            floor = float(min(1.0, max(0.0, self.config.candidate_prior_admission_floor)))
            threshold = float(min(1.0, max(0.0, self.config.candidate_prior_admission_threshold)))
            temperature = max(1.0e-3, float(self.config.candidate_prior_admission_temperature))
            scale = float(min(1.0, max(0.0, self.config.candidate_prior_admission_scale)))
            candidate_prior_admission_gate = floor + (1.0 - floor) * torch.sigmoid(
                (candidate_prior_admission_support - threshold) / temperature
            )
            min_support = float(min(1.0, max(0.0, self.config.candidate_prior_admission_min_support)))
            protected_min_support = float(
                min(1.0, max(0.0, self.config.candidate_prior_admission_protected_min_support))
            )
            effective_min_support: torch.Tensor | float = min_support
            if (
                protected_min_support > min_support
                and candidate_protected_class_mass is not None
            ):
                effective_min_support = min_support + (
                    protected_min_support - min_support
                ) * candidate_protected_class_mass.view(-1, 1, 1)
            if min_support > 0.0 or protected_min_support > 0.0:
                candidate_prior_admission_mask = candidate_prior_admission_support >= effective_min_support
            else:
                candidate_prior_admission_mask = torch.ones_like(candidate_prior_admission_support, dtype=torch.bool)
            candidate_prior_overlay = candidate_prior * scale * candidate_prior_admission_gate
            candidate_prior_overlay = torch.where(
                candidate_prior_admission_mask,
                candidate_prior_overlay,
                torch.zeros_like(candidate_prior_overlay),
            )
            candidate_prior_base = base_prior
            admitted_candidate_prior = torch.maximum(base_prior, candidate_prior_overlay)
            admission_target = str(self.config.candidate_prior_admission_target or "coverage").strip().lower()
            if admission_target in {"proposal", "candidate_proposal", "explore", "explore_only"}:
                rpf_prior = base_prior
                rpf_candidate_proposal_prior = candidate_prior_overlay
            elif admission_target in {"proposal_feature", "candidate_proposal_feature", "explore_feature"}:
                rpf_prior = base_prior
                rpf_feature_prior = admitted_candidate_prior
                rpf_candidate_proposal_prior = candidate_prior_overlay
            elif admission_target in {"feature", "feature_only", "prior_feature"}:
                rpf_prior = base_prior
                rpf_feature_prior = admitted_candidate_prior
            elif admission_target in {"coverage_feature", "coverage_and_feature", "both"}:
                rpf_prior = admitted_candidate_prior
                rpf_feature_prior = admitted_candidate_prior
            else:
                rpf_prior = admitted_candidate_prior
        class_prior_admission_gate: torch.Tensor | None = None
        class_prior_admission_trust: torch.Tensor | None = None
        if (
            bool(self.config.use_class_conditioned_prior_admission)
            and rpf_prior is not None
            and routed_class_path_evidence is not None
        ):
            evidence_gate = routed_class_path_evidence.to(device=x.device, dtype=evidence_states.dtype).clamp(0.0, 1.0)
            floor = float(min(1.0, max(0.0, self.config.class_prior_admission_floor)))
            filtered_gate = floor + (1.0 - floor) * evidence_gate
            if bool(self.config.use_adaptive_prior_admission) and class_evidence_gate is not None:
                confidence = torch.max(class_evidence_gate, dim=1).values
                threshold = float(min(1.0, max(0.0, self.config.adaptive_prior_admission_threshold)))
                temperature = max(1.0e-3, float(self.config.adaptive_prior_admission_temperature))
                class_prior_admission_trust = torch.sigmoid((confidence - threshold) / temperature)
                class_prior_admission_gate = 1.0 - class_prior_admission_trust.view(-1, 1, 1) * (1.0 - filtered_gate)
            else:
                class_prior_admission_gate = filtered_gate
            prior_for_paths = rpf_prior.to(device=x.device, dtype=evidence_states.dtype)
            if prior_for_paths.ndim == 2 and tuple(prior_for_paths.shape) == (self.config.n_features, self.config.n_features):
                prior_for_paths = prior_for_paths.unsqueeze(0).expand(x.shape[0], -1, -1)
            if prior_for_paths.ndim == 3 and tuple(prior_for_paths.shape) == (x.shape[0], self.config.n_features, self.config.n_features):
                rpf_prior = prior_for_paths * class_prior_admission_gate
            if rpf_feature_prior is not None:
                feature_prior_for_paths = rpf_feature_prior.to(device=x.device, dtype=evidence_states.dtype)
                if feature_prior_for_paths.ndim == 2 and tuple(feature_prior_for_paths.shape) == (
                    self.config.n_features,
                    self.config.n_features,
                ):
                    feature_prior_for_paths = feature_prior_for_paths.unsqueeze(0).expand(x.shape[0], -1, -1)
                if feature_prior_for_paths.ndim == 3 and tuple(feature_prior_for_paths.shape) == (
                    x.shape[0],
                    self.config.n_features,
                    self.config.n_features,
                ):
                    rpf_feature_prior = feature_prior_for_paths * class_prior_admission_gate
            if rpf_candidate_proposal_prior is not None:
                candidate_prior_for_paths = rpf_candidate_proposal_prior.to(device=x.device, dtype=evidence_states.dtype)
                if candidate_prior_for_paths.ndim == 2 and tuple(candidate_prior_for_paths.shape) == (
                    self.config.n_features,
                    self.config.n_features,
                ):
                    candidate_prior_for_paths = candidate_prior_for_paths.unsqueeze(0).expand(x.shape[0], -1, -1)
                if candidate_prior_for_paths.ndim == 3 and tuple(candidate_prior_for_paths.shape) == (
                    x.shape[0],
                    self.config.n_features,
                    self.config.n_features,
                ):
                    rpf_candidate_proposal_prior = candidate_prior_for_paths * class_prior_admission_gate
        path_target_mask = self.path_target_mask if self.path_target_mask.numel() else None
        path_source_mask = self.path_source_mask if self.path_source_mask.numel() else None
        path_bridge_mask = self.path_bridge_mask if self.path_bridge_mask.numel() else None
        path_context, path_diag = self.path_fusion(
            evidence_states,
            adjacency,
            prior_adjacency=rpf_prior,
            prior_feature_adjacency=rpf_feature_prior,
            candidate_proposal_adjacency=rpf_candidate_proposal_prior,
            feature_group_ids=feature_groups,
            task_salience=task_salience,
            path_evidence=path_evidence,
            proposal_protected_mass=candidate_protected_class_mass,
            target_allowed_mask=path_target_mask,
            source_allowed_mask=path_source_mask,
            bridge_allowed_mask=path_bridge_mask,
        )
        node_context = self.node_context(evidence_states.mean(dim=1))
        temporal_context = None
        if self.temporal_mixer is not None:
            temporal_context = self.temporal_mixer(x)
            node_context = node_context + temporal_context
        combined_context = torch.cat([node_context, path_context], dim=-1)
        logits = self.head(combined_context)
        path_aux_logits = self.path_aux_head(path_context)
        coarse_logits = self.coarse_head(combined_context)
        health_pred = torch.sigmoid(self.health_head(combined_context)).squeeze(-1)
        rul_norm_pred = torch.sigmoid(self.rul_head(combined_context)).squeeze(-1)
        temporal_rul_norm_pred: torch.Tensor | None = None
        anchor_rul_norm_pred: torch.Tensor | None = None
        rul_anchor_gate: torch.Tensor | None = None
        rul_anchor_delta: torch.Tensor | None = None
        if temporal_context is not None and self.temporal_rul_head is not None:
            temporal_rul_logit = self.temporal_rul_head(temporal_context).squeeze(-1)
            temporal_rul_norm_pred = torch.sigmoid(temporal_rul_logit)
            if self.rul_anchor_delta_head is not None and self.rul_anchor_gate_head is not None:
                anchor_input = torch.cat(
                    [
                        temporal_context,
                        path_context,
                        temporal_context * path_context,
                        torch.abs(temporal_context - path_context),
                    ],
                    dim=-1,
                )
                residual_scale = float(max(0.0, self.config.rul_anchor_residual_scale))
                rul_anchor_delta = residual_scale * torch.tanh(self.rul_anchor_delta_head(anchor_input).squeeze(-1))
                rul_anchor_gate = torch.sigmoid(self.rul_anchor_gate_head(anchor_input).squeeze(-1))
                anchor_rul_norm_pred = torch.sigmoid(temporal_rul_logit + rul_anchor_gate * rul_anchor_delta)
        out: dict[str, Any] = {
            "logits": logits,
            "path_aux_logits": path_aux_logits,
            "coarse_logits": coarse_logits,
            "health_pred": health_pred,
            "rul_norm_pred": rul_norm_pred,
            "reconstruction": reconstruction,
        }
        if edge_calibrator_gate is not None:
            positive_gate = edge_calibrator_gate[edge_calibrator_gate > 0.0]
            out["edge_calibrator_reg_loss"] = (
                torch.mean((positive_gate - 1.0) ** 2)
                if positive_gate.numel() > 0
                else logits.new_tensor(0.0)
            )
        if evidence_router_logits is not None:
            out["evidence_router_logits"] = evidence_router_logits
        if temporal_rul_norm_pred is not None:
            out["temporal_rul_norm_pred"] = temporal_rul_norm_pred
        if anchor_rul_norm_pred is not None:
            out["anchor_rul_norm_pred"] = anchor_rul_norm_pred
        if return_diagnostics:
            out["diagnostics"] = {
                "adjacency": adjacency.detach(),
                "scale_weights": scale_weights.detach(),
                "node_states": evidence_states.detach(),
                **{key: value.detach() for key, value in path_diag.items()},
            }
            if evidence_router_logits is not None:
                out["diagnostics"]["evidence_router_logits"] = evidence_router_logits.detach()
            if edge_family_router_logits is not None:
                out["diagnostics"]["edge_family_router_logits"] = edge_family_router_logits.detach()
            if edge_family_router_weights is not None:
                out["diagnostics"]["edge_family_router_weights"] = edge_family_router_weights.detach()
            if edge_family_routed_prior is not None:
                out["diagnostics"]["edge_family_routed_prior"] = edge_family_routed_prior.detach()
            if class_evidence_gate is not None:
                out["diagnostics"]["class_evidence_gate"] = class_evidence_gate.detach()
            if class_evidence_admission is not None:
                out["diagnostics"]["class_evidence_admission"] = class_evidence_admission.detach()
            if class_prior_admission_gate is not None:
                out["diagnostics"]["class_prior_admission_gate"] = class_prior_admission_gate.detach()
                if class_prior_admission_trust is not None:
                    out["diagnostics"]["class_prior_admission_trust"] = class_prior_admission_trust.detach()
            if edge_calibrator_gate is not None:
                out["diagnostics"]["edge_calibrator_gate"] = edge_calibrator_gate.detach()
            if rul_anchor_gate is not None:
                out["diagnostics"]["rul_anchor_gate"] = rul_anchor_gate.detach()
            if rul_anchor_delta is not None:
                out["diagnostics"]["rul_anchor_delta"] = rul_anchor_delta.detach()
            if path_candidate_prior is not None:
                out["diagnostics"]["path_candidate_prior_adjacency"] = path_candidate_prior.detach()
            if candidate_prior_admission_gate is not None:
                out["diagnostics"]["candidate_prior_admission_gate"] = candidate_prior_admission_gate.detach()
            if candidate_prior_admission_support is not None:
                out["diagnostics"]["candidate_prior_admission_support"] = candidate_prior_admission_support.detach()
            if candidate_prior_admission_mask is not None:
                out["diagnostics"]["candidate_prior_admission_mask"] = candidate_prior_admission_mask.detach()
            if candidate_protected_class_mass is not None:
                out["diagnostics"]["candidate_protected_class_mass"] = candidate_protected_class_mass.detach()
            if candidate_prior_overlay is not None:
                out["diagnostics"]["candidate_prior_overlay_adjacency"] = candidate_prior_overlay.detach()
            if candidate_prior_base is not None:
                out["diagnostics"]["candidate_prior_base_adjacency"] = candidate_prior_base.detach()
            if rpf_candidate_proposal_prior is not None:
                out["diagnostics"]["rpf_candidate_proposal_adjacency"] = rpf_candidate_proposal_prior.detach()
            if rpf_feature_prior is not None:
                out["diagnostics"]["rpf_feature_prior_adjacency"] = rpf_feature_prior.detach()
            if rpf_prior is not None and (
                path_candidate_prior is not None
                or edge_family_routed_prior is not None
                or class_prior_admission_gate is not None
            ):
                out["diagnostics"]["rpf_prior_adjacency"] = rpf_prior.detach()
            if calibrated_prior is not None and calibrated_prior is not prior:
                out["diagnostics"]["calibrated_prior_adjacency"] = calibrated_prior.detach()
        return out


def class_balanced_weights(y: np.ndarray, n_classes: int) -> torch.Tensor:
    counts = np.bincount(np.asarray(y, dtype=int), minlength=int(n_classes)).astype(np.float64)
    present = counts[counts > 0]
    mean_count = float(np.mean(present)) if present.size else 1.0
    weights = np.ones(int(n_classes), dtype=np.float32)
    for cls, count in enumerate(counts):
        if count > 0:
            weights[cls] = float(np.sqrt(mean_count / count))
    return torch.from_numpy(weights)


def graph_regularization(adjacency: torch.Tensor) -> torch.Tensor:
    if adjacency.numel() == 0:
        return adjacency.new_tensor(0.0)
    entropy = -(adjacency * torch.log(torch.clamp(adjacency, min=1e-6))).sum(dim=-1).mean()
    density = adjacency.mean()
    return 0.02 * density + 0.001 * entropy


def reliability_regularization(path_reliability: torch.Tensor | None) -> torch.Tensor:
    if path_reliability is None or path_reliability.numel() == 0:
        return torch.tensor(0.0)
    return torch.mean(path_reliability * (1.0 - path_reliability))


def count_trainable_parameters(model: nn.Module) -> int:
    return int(sum(p.numel() for p in model.parameters() if p.requires_grad))
