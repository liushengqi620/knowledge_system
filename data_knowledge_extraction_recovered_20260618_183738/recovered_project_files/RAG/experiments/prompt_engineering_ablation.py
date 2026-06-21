"""Minimal FSDV-EAPA prompt engineering ablation scaffold.

The original full experiment pipeline was not recovered with this package.
This module restores the prompt-atom strategy API and a conservative CLI so
other experiment scripts can be exercised without fabricating extraction
metrics. The CLI writes explicit "not_executed" artifacts; real NER/RE scores
must come from a restored evaluator or an integrated LLM extraction backend.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List


SUPPORTED_ATOM_DECOMPOSITION_STRATEGIES = {
    "no_atom",
    "fsdv_block",
    "sentence_level",
    "random_atom",
    "over_fine",
    "functional_atom",
}

_ATOM_DECOMPOSITION_STRATEGY = "functional_atom"


@dataclass(frozen=True)
class PromptAtom:
    atom_id: str
    stage_id: str
    strategy: str
    text: str
    tags: List[str]


def set_atom_decomposition_strategy(strategy: str) -> None:
    if strategy not in SUPPORTED_ATOM_DECOMPOSITION_STRATEGIES:
        raise ValueError(
            "Unsupported atom decomposition strategy "
            f"{strategy!r}. Expected one of: {sorted(SUPPORTED_ATOM_DECOMPOSITION_STRATEGIES)}"
        )
    global _ATOM_DECOMPOSITION_STRATEGY
    _ATOM_DECOMPOSITION_STRATEGY = strategy


def get_atom_decomposition_strategy() -> str:
    return _ATOM_DECOMPOSITION_STRATEGY


def _split_sentences(text: str) -> List[str]:
    parts = [x.strip() for x in re.split(r"(?<=[.!?。！？])\s+", text.strip()) if x.strip()]
    if parts:
        return parts
    return [x.strip() for x in text.splitlines() if x.strip()]


def _functional_chunks(text: str) -> List[str]:
    sentences = _split_sentences(text)
    chunks: List[str] = []
    for sentence in sentences:
        clause_parts = [
            x.strip()
            for x in re.split(r"\s+(?:and|or|but)\s+|[;；]", sentence)
            if x.strip()
        ]
        if len(clause_parts) <= 1:
            chunks.append(sentence)
        else:
            chunks.extend(clause_parts)
    return chunks or [text.strip()]


def _over_fine_chunks(text: str) -> List[str]:
    words = re.findall(r"\S+", text.strip())
    if len(words) <= 1:
        return [text.strip()] if text.strip() else []
    return [" ".join(words[i : i + 3]) for i in range(0, len(words), 3)]


def _fsdv_blocks(text: str) -> List[str]:
    sentences = _split_sentences(text)
    if len(sentences) <= 2:
        return [" ".join(sentences)] if sentences else []
    midpoint = (len(sentences) + 1) // 2
    return [" ".join(sentences[:midpoint]), " ".join(sentences[midpoint:])]


def _random_like_chunks(text: str) -> List[str]:
    # Deterministic pseudo-random grouping for reproducible scaffolding.
    words = re.findall(r"\S+", text.strip())
    if len(words) <= 6:
        return [text.strip()] if text.strip() else []
    chunks: List[str] = []
    i = 0
    sizes = [5, 2, 4, 3]
    while i < len(words):
        size = sizes[len(chunks) % len(sizes)]
        chunks.append(" ".join(words[i : i + size]))
        i += size
    return chunks


def _tags_for_atom(text: str) -> List[str]:
    lowered = text.lower()
    tags: List[str] = []
    keyword_tags = [
        ("entity", "entity"),
        ("relation", "relation"),
        ("json", "format"),
        ("schema", "schema"),
        ("evidence", "evidence"),
        ("causal", "causal_direction"),
        ("direction", "causal_direction"),
        ("extract", "extraction"),
        ("return", "output"),
    ]
    for keyword, tag in keyword_tags:
        if keyword in lowered and tag not in tags:
            tags.append(tag)
    return tags or ["general"]


def decompose_prompt_to_min_atoms(text: str, stage_id: str = "S") -> List[PromptAtom]:
    strategy = get_atom_decomposition_strategy()
    cleaned = text.strip()
    if not cleaned:
        return []

    if strategy == "no_atom":
        chunks = [cleaned]
    elif strategy == "fsdv_block":
        chunks = _fsdv_blocks(cleaned)
    elif strategy == "sentence_level":
        chunks = _split_sentences(cleaned)
    elif strategy == "random_atom":
        chunks = _random_like_chunks(cleaned)
    elif strategy == "over_fine":
        chunks = _over_fine_chunks(cleaned)
    elif strategy == "functional_atom":
        chunks = _functional_chunks(cleaned)
    else:
        raise ValueError(f"Unsupported atom decomposition strategy {strategy!r}")

    return [
        PromptAtom(
            atom_id=f"{stage_id}-{strategy}-{idx + 1:02d}",
            stage_id=stage_id,
            strategy=strategy,
            text=chunk,
            tags=_tags_for_atom(chunk),
        )
        for idx, chunk in enumerate(chunks)
        if chunk.strip()
    ]


def _default_prompt() -> str:
    return (
        "Extract only text-supported industrial knowledge. "
        "Entity types include process parameters, equipment states, and quality defects. "
        "Relation types include cause, affect, control, and improve. "
        "Causal relations must follow cause-to-effect direction. "
        "Return schema-valid JSON with entities and relations."
    )


def _write_scaffold_outputs(args: argparse.Namespace) -> None:
    set_atom_decomposition_strategy(args.atom_decomposition_strategy)
    atoms = decompose_prompt_to_min_atoms(_default_prompt(), "S")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    training_history = [
        {
            "iteration": 0,
            "strategy": args.atom_decomposition_strategy,
            "accepted": False,
            "score": None,
            "improvement": "not_executed: full FSDV-EAPA evaluator was not recovered",
            "atom_count": len(atoms),
        }
    ]
    (output_dir / "training_history.json").write_text(
        json.dumps(training_history, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "prompt_atoms.json").write_text(
        json.dumps([asdict(atom) for atom in atoms], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    result_dir = Path(args.output) / "re_pipeline_post"
    result_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "status": "not_executed",
        "reason": "The full prompt_engineering_ablation evaluator was not recovered.",
        "strategy": args.atom_decomposition_strategy,
        "metrics_policy": "No NER/RE/KHR values are generated by this scaffold.",
        "results": {
            "FSDV-EAPA": {
                "status": "not_executed",
                "avg_ner_f1": None,
                "avg_re_f1": None,
                "avg_f1": None,
                "avg_khr": None,
            }
        },
    }
    (result_dir / "ablation_results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scaffold prompt-engineering ablation outputs.")
    parser.add_argument("--mode", default="re_pipeline")
    parser.add_argument("--domain", default="steel_casting")
    parser.add_argument("--prompt_language", default="auto")
    parser.add_argument("--samples", type=int, default=30)
    parser.add_argument("--valset_size", type=int, default=20)
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--atom_decomposition_strategy", default="functional_atom")
    parser.add_argument("--num_candidates", type=int, default=6)
    parser.add_argument("--collect_n", type=int, default=8)
    parser.add_argument("--max_eval_candidates", type=int, default=4)
    parser.add_argument("--quick_eval_samples", type=int, default=None)
    parser.add_argument("--data", default=None)
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    _write_scaffold_outputs(args)
    print(
        json.dumps(
            {
                "status": "not_executed",
                "strategy": args.atom_decomposition_strategy,
                "output_dir": args.output_dir,
                "output": args.output,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
