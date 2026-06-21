"""Prompt-atom decomposition diagnostic experiment.

This script evaluates whether different prompt decomposition strategies create
useful local update units for EAPA. It intentionally does not fabricate LLM
extraction scores. Instead, it reports decomposition-level diagnostics that can
be run before expensive LLM calls:

- attribution coverage for common continuous-casting error types
- edit locality, or how many unrelated functions an update may disturb
- semantic completeness of atom units
- protection coverage for key atoms
- over-fragmentation and over-coarsening risks

The output files can be used as a reproducible protocol table. Real NER/RE/KHR
numbers should be added only after each strategy is actually evaluated with the
same LLM and held-out test split.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List, Sequence, Set


DEFAULT_OUTPUT_DIR = Path("outputs") / "prompt_atom_decomposition"


@dataclass(frozen=True)
class PromptUnit:
    """A functional prompt unit before strategy-specific grouping."""

    unit_id: str
    category: str
    text: str
    tags: Set[str]
    protected: bool = False


@dataclass
class PromptAtom:
    """A strategy-specific atom used for attribution and local editing."""

    atom_id: str
    strategy: str
    category: str
    text: str
    tags: Set[str] = field(default_factory=set)
    protected: bool = False
    source_units: List[str] = field(default_factory=list)

    @property
    def token_count(self) -> int:
        return len(re.findall(r"\S+", self.text))


@dataclass(frozen=True)
class ErrorProbe:
    """A representative error type and the prompt functions needed to fix it."""

    error_id: str
    description: str
    required_tags: Set[str]
    high_risk_tags: Set[str]


CANONICAL_UNITS: List[PromptUnit] = [
    PromptUnit(
        "F1",
        "Foundation",
        "Extract only process-relevant industrial knowledge from continuous casting text.",
        {"task_scope", "industrial_domain"},
    ),
    PromptUnit(
        "F2",
        "Foundation",
        "All extracted entities and relations must be supported by the input text.",
        {"evidence"},
        protected=True,
    ),
    PromptUnit(
        "F3",
        "Foundation",
        "Do not infer unstated defects, causes, equipment states, or improvement actions.",
        {"evidence", "hallucination"},
        protected=True,
    ),
    PromptUnit(
        "S1",
        "Schema",
        "Entity types are ProcessParameter, EquipmentState, QualityDefect, MaterialState, Operation, ProductPart, and QualityIndicator.",
        {"entity_type", "schema"},
        protected=True,
    ),
    PromptUnit(
        "S2",
        "Schema",
        "Preserve complete entity boundaries, including modifiers such as excessive, insufficient, unstable, or abnormal.",
        {"entity_boundary", "nested_entity", "schema"},
    ),
    PromptUnit(
        "S3",
        "Schema",
        "Relation types include cause, affect, control, improve, located_at, has_parameter, and associated_with.",
        {"relation_type", "schema"},
        protected=True,
    ),
    PromptUnit(
        "S4",
        "Schema",
        "Causal relations must follow cause-to-effect direction, not effect-to-cause direction.",
        {"relation_direction", "causal_chain", "schema"},
        protected=True,
    ),
    PromptUnit(
        "S5",
        "Schema",
        "A relation is valid only when both endpoints appear as extracted entities and the entity-type combination is legal.",
        {"endpoint_consistency", "entity_type", "schema"},
        protected=True,
    ),
    PromptUnit(
        "D1",
        "Demonstration",
        "Example: 'casting speed increased, leading to longitudinal cracks' should produce casting speed -> cause -> longitudinal cracks.",
        {"relation_direction", "causal_chain", "demonstration"},
    ),
    PromptUnit(
        "D2",
        "Demonstration",
        "Example: keep 'mold level fluctuation' as one EquipmentState entity rather than splitting it into unrelated words.",
        {"entity_boundary", "demonstration"},
    ),
    PromptUnit(
        "D3",
        "Demonstration",
        "Example: if one sentence contains a chain A causes B and B causes C, extract both local links when text evidence supports them.",
        {"implicit_chain", "causal_chain", "demonstration"},
    ),
    PromptUnit(
        "D4",
        "Demonstration",
        "Example: reject a triple if the source text mentions only an isolated material state and no relation.",
        {"hallucination", "evidence", "demonstration"},
    ),
    PromptUnit(
        "V1",
        "Validation",
        "Return valid JSON with top-level keys entities and relations.",
        {"json_format", "validation"},
        protected=True,
    ),
    PromptUnit(
        "V2",
        "Validation",
        "Remove entities or relations that are not supported by explicit textual evidence.",
        {"evidence", "hallucination", "validation"},
        protected=True,
    ),
    PromptUnit(
        "V3",
        "Validation",
        "Check relation direction, relation type, endpoint existence, and duplicate triples before final output.",
        {"relation_direction", "relation_type", "endpoint_consistency", "validation"},
        protected=True,
    ),
]


ERROR_PROBES: List[ErrorProbe] = [
    ErrorProbe(
        "entity_boundary",
        "Nested or modified entity boundary is truncated.",
        {"entity_boundary", "nested_entity"},
        {"entity_type", "schema"},
    ),
    ErrorProbe(
        "entity_type",
        "An extracted entity is assigned to an incompatible type.",
        {"entity_type", "schema"},
        {"schema"},
    ),
    ErrorProbe(
        "implicit_chain",
        "A sentence contains an implicit chain-like relation but only one local link is extracted.",
        {"implicit_chain", "causal_chain", "demonstration"},
        {"relation_direction", "schema"},
    ),
    ErrorProbe(
        "wrong_direction",
        "A causal triple is reversed from effect-to-cause.",
        {"relation_direction", "causal_chain"},
        {"relation_direction", "schema"},
    ),
    ErrorProbe(
        "unsupported_triple",
        "A plausible but unsupported triple is generated.",
        {"evidence", "hallucination"},
        {"evidence", "validation"},
    ),
    ErrorProbe(
        "invalid_json",
        "The generated output misses required JSON fields.",
        {"json_format", "validation"},
        {"json_format", "validation"},
    ),
]


def make_atom(strategy: str, atom_id: str, category: str, units: Sequence[PromptUnit]) -> PromptAtom:
    text = " ".join(unit.text for unit in units)
    tags: Set[str] = set()
    protected = False
    source_units: List[str] = []
    for unit in units:
        tags.update(unit.tags)
        protected = protected or unit.protected
        source_units.append(unit.unit_id)
    return PromptAtom(atom_id, strategy, category, text, tags, protected, source_units)


def build_atoms(strategy: str, seed: int = 2026) -> List[PromptAtom]:
    units = CANONICAL_UNITS
    if strategy == "no_atom":
        return [make_atom(strategy, "A1", "WholePrompt", units)]

    if strategy == "fsdv_block":
        atoms = []
        for category in ["Foundation", "Schema", "Demonstration", "Validation"]:
            group = [unit for unit in units if unit.category == category]
            atoms.append(make_atom(strategy, category[0], category, group))
        return atoms

    if strategy == "sentence_level":
        return [
            make_atom(strategy, unit.unit_id, unit.category, [unit])
            for unit in units
        ]

    if strategy == "random_atom":
        rng = random.Random(seed)
        shuffled = list(units)
        rng.shuffle(shuffled)
        atoms = []
        for idx in range(0, len(shuffled), 3):
            group = shuffled[idx : idx + 3]
            atoms.append(make_atom(strategy, f"R{idx // 3 + 1}", "Mixed", group))
        return atoms

    if strategy == "over_fine":
        atoms = []
        for unit in units:
            parts = split_over_fine(unit.text)
            for idx, part in enumerate(parts, start=1):
                # Keep the original tags because the clause is still derived
                # from that function, but mark semantic incompleteness later.
                pseudo = PromptUnit(f"{unit.unit_id}.{idx}", unit.category, part, set(unit.tags), unit.protected)
                atoms.append(make_atom(strategy, pseudo.unit_id, unit.category, [pseudo]))
        return atoms

    if strategy == "functional_atom":
        return [
            make_atom(strategy, unit.unit_id, unit.category, [unit])
            for unit in units
        ]

    raise ValueError(f"Unknown strategy: {strategy}")


def split_over_fine(text: str) -> List[str]:
    pieces = re.split(r"(?i)\b(?:and|or|when|with|including|rather than|before|if)\b|[,.;:]", text)
    pieces = [p.strip() for p in pieces if p.strip()]
    if len(pieces) <= 1:
        words = text.split()
        midpoint = max(1, len(words) // 2)
        pieces = [" ".join(words[:midpoint]), " ".join(words[midpoint:])]
    return pieces


def semantic_completeness(atom: PromptAtom) -> float:
    text = atom.text.lower()
    has_predicate = any(
        marker in text
        for marker in [
            "extract",
            "must",
            "include",
            "preserve",
            "return",
            "remove",
            "check",
            "reject",
            "produce",
            "valid",
            "supported",
        ]
    )
    has_object = len(atom.tags) > 0 and atom.token_count >= 4
    if has_predicate and has_object:
        return 1.0
    if has_predicate or has_object:
        return 0.5
    return 0.0


def attribution_candidates(atoms: Sequence[PromptAtom], probe: ErrorProbe) -> List[PromptAtom]:
    return [atom for atom in atoms if atom.tags.intersection(probe.required_tags)]


def evaluate_strategy(strategy: str, seed: int = 2026) -> Dict[str, object]:
    atoms = build_atoms(strategy, seed)
    tag_universe = set().union(*(unit.tags for unit in CANONICAL_UNITS))
    protected_tags = {"entity_type", "relation_type", "relation_direction", "json_format", "evidence", "validation"}

    coverage_hits = 0
    precision_values: List[float] = []
    locality_values: List[float] = []
    protected_hits = 0
    risky_unprotected = 0
    candidate_counts: List[int] = []

    for probe in ERROR_PROBES:
        candidates = attribution_candidates(atoms, probe)
        candidate_counts.append(len(candidates))
        if candidates:
            coverage_hits += 1
        candidate_tags = set().union(*(atom.tags for atom in candidates)) if candidates else set()
        relevant = candidate_tags.intersection(probe.required_tags)
        precision_values.append(len(relevant) / max(1, len(candidate_tags)))

        unrelated = candidate_tags - probe.required_tags
        locality_values.append(1.0 - len(unrelated) / max(1, len(tag_universe)))

        if any(atom.protected for atom in candidates if atom.tags.intersection(probe.high_risk_tags)):
            protected_hits += 1
        if any((not atom.protected) for atom in candidates if atom.tags.intersection(probe.high_risk_tags)):
            risky_unprotected += 1

    completeness = [semantic_completeness(atom) for atom in atoms]
    mean_tokens = mean([atom.token_count for atom in atoms])
    over_coarse_risk = mean([max(0, len(atom.tags) - 3) / max(1, len(tag_universe) - 3) for atom in atoms])
    over_fine_risk = 1.0 - mean(completeness)
    protected_coverage = len(
        set().union(*(atom.tags for atom in atoms if atom.protected)).intersection(protected_tags)
    ) / len(protected_tags)

    score = (
        0.25 * (coverage_hits / len(ERROR_PROBES))
        + 0.20 * mean(precision_values)
        + 0.20 * mean(locality_values)
        + 0.15 * mean(completeness)
        + 0.10 * protected_coverage
        + 0.10 * (protected_hits / len(ERROR_PROBES))
        - 0.10 * over_coarse_risk
        - 0.10 * over_fine_risk
        - 0.05 * (risky_unprotected / len(ERROR_PROBES))
    )

    return {
        "strategy": strategy,
        "atom_count": len(atoms),
        "mean_tokens_per_atom": round(mean_tokens, 3),
        "error_attribution_coverage": round(coverage_hits / len(ERROR_PROBES), 4),
        "attribution_precision_proxy": round(mean(precision_values), 4),
        "edit_locality": round(mean(locality_values), 4),
        "semantic_completeness": round(mean(completeness), 4),
        "protected_tag_coverage": round(protected_coverage, 4),
        "protected_gate_coverage": round(protected_hits / len(ERROR_PROBES), 4),
        "over_coarse_risk": round(over_coarse_risk, 4),
        "over_fine_risk": round(over_fine_risk, 4),
        "mean_candidate_atoms_per_error": round(mean(candidate_counts), 3),
        "diagnostic_score": round(score, 4),
        "atoms": [serialize_atom(atom) for atom in atoms],
    }


def serialize_atom(atom: PromptAtom) -> Dict[str, object]:
    return {
        "atom_id": atom.atom_id,
        "category": atom.category,
        "protected": atom.protected,
        "source_units": atom.source_units,
        "tags": sorted(atom.tags),
        "text": atom.text,
    }


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_latex_table(path: Path, rows: Sequence[Dict[str, object]]) -> None:
    headers = [
        "Decomposition",
        "Atoms",
        "Coverage",
        "Precision",
        "Locality",
        "Completeness",
        "Protected",
        "Score",
    ]
    lines = [
        r"\begin{tabular}{lccccccc}",
        r"\toprule",
        " & ".join(headers) + r" \\",
        r"\midrule",
    ]
    names = {
        "no_atom": "No-Atom",
        "fsdv_block": "FSDV-Block",
        "sentence_level": "Sentence-Level",
        "random_atom": "Random-Atom",
        "over_fine": "Over-Fine",
        "functional_atom": "Functional Atom",
    }
    for row in rows:
        lines.append(
            " & ".join(
                [
                    names.get(str(row["strategy"]), str(row["strategy"])),
                    str(row["atom_count"]),
                    f"{float(row['error_attribution_coverage']):.3f}",
                    f"{float(row['attribution_precision_proxy']):.3f}",
                    f"{float(row['edit_locality']):.3f}",
                    f"{float(row['semantic_completeness']):.3f}",
                    f"{float(row['protected_tag_coverage']):.3f}",
                    f"{float(row['diagnostic_score']):.3f}",
                ]
            )
            + r" \\"
        )
    lines += [r"\bottomrule", r"\end{tabular}", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_protocol(path: Path) -> None:
    text = """# Prompt Atom Decomposition Granularity Experiment

## Purpose

This experiment evaluates whether prompt-atom decomposition creates useful
local units for EAPA. It compares no decomposition, FSDV-block decomposition,
sentence-level decomposition, random grouping, over-fine clause splitting, and
the proposed functional atom decomposition.

## Dataset

The full performance experiment should use the continuous casting dataset with
the same train/dev/test split as the main paper. The development split is used
for EAPA error profiling and prompt update selection; the test split is reserved
for final NER F1, RE F1, Overall F1, KHR, invalid-output rate, and update
stability.

## Controlled Variables

- Same LLM backbone and decoding settings.
- Same initial FSDV prompt content.
- Same EAPA iterations, candidate count, and acceptance rule.
- Same evaluation script for all strategies.
- Same random seeds for random atom grouping.

## Strategy Definitions

- No-Atom: the entire prompt is treated as one update unit.
- FSDV-Block: four update units, Foundation, Schema, Demonstration, Validation.
- Sentence-Level: each canonical prompt sentence is treated as one atom.
- Random-Atom: canonical units are randomly grouped into mixed atoms.
- Over-Fine: clauses or short fragments are treated as atoms.
- Functional Atom: each atom is functionally complete, locally editable,
  attributable to errors, and protectable.

## Reporting Rule

The diagnostic CSV reports decomposition-level properties only. Do not report
NER F1, RE F1, Overall F1, or KHR for a strategy until that strategy has been
actually run through the LLM extraction and held-out test evaluation pipeline.
"""
    path.write_text(text, encoding="utf-8")


def run(output_dir: Path, seed: int) -> List[Dict[str, object]]:
    strategies = [
        "no_atom",
        "fsdv_block",
        "sentence_level",
        "random_atom",
        "over_fine",
        "functional_atom",
    ]
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = [evaluate_strategy(strategy, seed) for strategy in strategies]
    summary_rows = [{k: v for k, v in row.items() if k != "atoms"} for row in rows]

    (output_dir / "diagnostic_results.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(
        output_dir / "diagnostic_summary.csv",
        summary_rows,
        [
            "strategy",
            "atom_count",
            "mean_tokens_per_atom",
            "error_attribution_coverage",
            "attribution_precision_proxy",
            "edit_locality",
            "semantic_completeness",
            "protected_tag_coverage",
            "protected_gate_coverage",
            "over_coarse_risk",
            "over_fine_risk",
            "mean_candidate_atoms_per_error",
            "diagnostic_score",
        ],
    )
    write_latex_table(output_dir / "diagnostic_table.tex", summary_rows)
    write_protocol(output_dir / "experiment_protocol.md")
    return summary_rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Run prompt-atom decomposition diagnostic experiment.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()

    rows = run(args.output_dir, args.seed)
    print(f"Wrote results to {args.output_dir}")
    for row in rows:
        print(
            f"{row['strategy']}: atoms={row['atom_count']}, "
            f"coverage={row['error_attribution_coverage']}, "
            f"locality={row['edit_locality']}, score={row['diagnostic_score']}"
        )


if __name__ == "__main__":
    main()
