# Prompt Atom Decomposition Granularity Experiment

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
