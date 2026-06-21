"""Prepare and optionally execute the extended supervised PLM baselines.

The script builds the experiment matrix requested for the paper:

- datasets: continuous casting and electrochemistry
- PLM baselines: BERT-CRF+CasRel, PURE, CasRel, TPLinker, PRGC, OneRel
- annotation ratios: 10%, 50%, 100%
- seeds: 2026, 2027, 2028

Only the in-repository BERT-CRF plus relation-classification pipeline can be
executed directly. Other baselines are represented as adapter slots so that
their real open-source implementations can be connected without changing the
paper table or result schema.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "plm_extended_baselines_runs"
DEFAULT_CONTINUOUS_CASTING = (
    PROJECT_ROOT / "data" / "连铸原始语料" / "ner_re_train_data_continuous_casting.json"
)
DEFAULT_ECHEM = PROJECT_ROOT / "data" / "raw_corpus" / "Structured_dataset.jsonl"
DEFAULT_BAOSTEEL = PROJECT_ROOT / "data" / "baosteel_knowledge_extraction" / "plm" / "baosteel_plm_train_pool.json"

DEFAULT_MODELS = ["BERT-CRF+CasRel", "PURE", "CasRel", "TPLinker", "PRGC", "OneRel"]
DEFAULT_RATIOS = [0.10, 0.50, 1.0]
DEFAULT_SEEDS = [2026, 2027, 2028]

FIXED_REFERENCES = {
    "continuous_casting": {
        "FSDV": (0.9218, 0.7648, 0.8433),
        "FSDV-EAPA": (0.9389, 0.8429, 0.8909),
    },
    "electrochemistry": {
        "FSDV": (0.8950, 0.7480, 0.8215),
        "FSDV-EAPA": (0.9120, 0.7940, 0.8530),
    },
}

DATASET_CONFIGS = {
    "continuous_casting": {
        "source": DEFAULT_CONTINUOUS_CASTING,
        "encoder": "hfl/chinese-macbert-base",
        "max_length": 256,
        "domain": "steel_casting",
    },
    "electrochemistry": {
        "source": DEFAULT_ECHEM,
        "encoder": "allenai/scibert_scivocab_uncased",
        "max_length": 384,
        "domain": "electrochemistry",
    },
    "baosteel_quality_traceability": {
        "source": DEFAULT_BAOSTEEL,
        "encoder": "hfl/chinese-macbert-base",
        "max_length": 384,
        "domain": "baosteel_quality_traceability",
    },
}

ECHEM_ENTITY_TYPES = ["MATERIAL", "VALUE"]
ECHEM_RELATION_TYPES = [
    "Voltage",
    "Capacity",
    "Coulombic Efficiency",
    "Energy",
    "Conductivity",
    "无关系",
]


@dataclass(frozen=True)
class AdapterInfo:
    status: str
    note: str


def ratio_label(ratio: float) -> str:
    pct = ratio * 100
    if abs(pct - round(pct)) < 1e-9:
        return f"{int(round(pct))}%"
    return f"{pct:.1f}%"


def ratio_dir(ratio: float) -> str:
    return ratio_label(ratio).replace("%", "pct").replace(".", "p")


def sample_budget(data: Sequence[Dict[str, Any]], ratio: float, seed: int, min_samples: int) -> List[Dict[str, Any]]:
    if not 0 < ratio <= 1:
        raise ValueError(f"ratio must be in (0, 1], got {ratio}")
    n = min(len(data), max(min_samples, math.ceil(len(data) * ratio)))
    idx = list(range(len(data)))
    random.Random(seed).shuffle(idx)
    return [data[i] for i in sorted(idx[:n])]


def load_json_list(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON list: {path}")
    return data


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def token_spans(text: str) -> List[Tuple[int, int]]:
    return [(m.start(), m.end()) for m in re.finditer(r"\S+", text)]


def safe_span(text: str, mention: str, start_idx: Optional[int], end_idx: Optional[int]) -> Optional[Tuple[int, int]]:
    spans = token_spans(text)
    if start_idx is not None and end_idx is not None and 0 <= int(start_idx) < len(spans):
        start = int(start_idx)
        end = min(int(end_idx), len(spans) - 1)
        return spans[start][0], spans[end][1]

    mention = (mention or "").strip()
    if not mention:
        return None
    pos = text.find(mention)
    if pos >= 0:
        return pos, pos + len(mention)
    compact = re.sub(r"\s+", " ", mention)
    pos = text.find(compact)
    if pos >= 0:
        return pos, pos + len(compact)
    return None


def bio_labels(text: str, entities: Iterable[Dict[str, Any]]) -> List[str]:
    labels = ["O"] * len(text)
    for ent in entities:
        start = int(ent["start"])
        end = int(ent["end"])
        typ = ent["type"]
        if start < 0 or end <= start or end > len(text) or typ not in ECHEM_ENTITY_TYPES:
            continue
        labels[start] = f"B-{typ}"
        for i in range(start + 1, end):
            labels[i] = f"I-{typ}"
    return labels


def convert_echem_record(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    text = (item.get("sentText") or "").strip()
    if not text:
        return None

    rel_map = {name: i for i, name in enumerate(ECHEM_RELATION_TYPES)}
    entity_map: Dict[Tuple[int, int, str], Dict[str, Any]] = {}
    entity_pairs: List[List[int]] = []
    relations: List[int] = []

    for rm in item.get("relationMentions") or []:
        rel = (rm.get("relText") or "").strip()
        if rel not in rel_map:
            continue
        a1_span = safe_span(text, rm.get("arg1Text") or "", rm.get("arg1StartIndex"), rm.get("arg1EndIndex"))
        a2_span = safe_span(text, rm.get("arg2Text") or "", rm.get("arg2StartIndex"), rm.get("arg2EndIndex"))
        if not a1_span or not a2_span:
            continue
        a1 = {"text": text[a1_span[0] : a1_span[1]], "type": "MATERIAL", "start": a1_span[0], "end": a1_span[1]}
        a2 = {"text": text[a2_span[0] : a2_span[1]], "type": "VALUE", "start": a2_span[0], "end": a2_span[1]}
        entity_map[(a1["start"], a1["end"], a1["type"])] = a1
        entity_map[(a2["start"], a2["end"], a2["type"])] = a2
        entity_pairs.append([a1["start"], a1["end"], a2["start"], a2["end"]])
        relations.append(rel_map[rel])

    if not entity_pairs:
        return None

    entities = sorted(entity_map.values(), key=lambda e: (e["start"], e["end"], e["type"]))
    return {
        "id": item.get("id"),
        "text": text,
        "ner": {"text": text, "labels": bio_labels(text, entities), "entities": entities},
        "re": {"text": text, "entity_pairs": entity_pairs, "relations": relations, "dependency_graph": {"nodes": [], "edges": []}},
    }


def split_data(data: Sequence[Dict[str, Any]], seed: int) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    items = list(data)
    random.Random(seed).shuffle(items)
    n = len(items)
    train_n = int(n * 0.8)
    dev_n = int(n * 0.1)
    return items[:train_n], items[train_n : train_n + dev_n], items[train_n + dev_n :]


def load_dataset_pool(dataset: str, source: Path, seed: int, max_echem_samples: int = 1255) -> Dict[str, Any]:
    if dataset == "electrochemistry" and source.suffix.lower() == ".jsonl":
        converted = [x for x in (convert_echem_record(row) for row in load_jsonl(source)) if x is not None]
        if max_echem_samples and max_echem_samples > 0:
            converted = converted[:max_echem_samples]
        train, dev, test = split_data(converted, seed)
        return {"train": train, "dev": dev, "test": test, "total": len(converted), "source_mode": "jsonl_converted_split"}

    data = load_json_list(source)
    return {"train": data, "dev": [], "test": [], "total": len(data), "source_mode": "eligible_training_pool"}


def adapter_info(model: str) -> AdapterInfo:
    if model == "BERT-CRF+CasRel":
        return AdapterInfo("available", "uses in-repository BERT-CRF plus relation extraction scripts")
    if model == "OneRel":
        return AdapterInfo("optional_adapter_missing", "optional external OneRel implementation is not connected")
    return AdapterInfo("adapter_missing", f"external {model} implementation is not connected")


def build_experiment_matrix(
    datasets: Sequence[str],
    models: Sequence[str],
    ratios: Sequence[float],
    seeds: Sequence[int],
    include_fixed_refs: bool = True,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for dataset in datasets:
        if dataset not in DATASET_CONFIGS:
            raise ValueError(f"Unknown dataset: {dataset}")
        cfg = DATASET_CONFIGS[dataset]
        for model in models:
            info = adapter_info(model)
            for ratio in ratios:
                for seed in seeds:
                    rows.append(
                        {
                            "dataset": dataset,
                            "model": model,
                            "annotation_ratio": ratio_label(ratio),
                            "seed": seed,
                            "encoder": cfg["encoder"],
                            "max_sequence_length": cfg["max_length"],
                            "adapter_status": info.status,
                            "notes": info.note,
                        }
                    )
        if include_fixed_refs:
            for ref, metrics in FIXED_REFERENCES.get(dataset, {}).items():
                rows.append(
                    {
                        "dataset": dataset,
                        "model": ref,
                        "annotation_ratio": "--",
                        "seed": "--",
                        "encoder": "frozen LLM",
                        "max_sequence_length": "--",
                        "adapter_status": "fixed_reference",
                        "ner_f1": metrics[0],
                        "re_f1": metrics[1],
                        "overall_f1": metrics[2],
                        "notes": "fixed frozen-LLM reference from the manuscript",
                    }
                )
    return rows


def count_annotations(items: Iterable[Dict[str, Any]]) -> Tuple[int, int]:
    entity_count = 0
    relation_count = 0
    for item in items:
        entity_count += len(item.get("ner", {}).get("entities", []) or item.get("entities", []) or [])
        relation_count += len(item.get("re", {}).get("relations", []) or item.get("relations", []) or [])
    return entity_count, relation_count


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "dataset",
        "model",
        "annotation_ratio",
        "seed",
        "encoder",
        "max_sequence_length",
        "adapter_status",
        "labeled_samples",
        "entity_annotations",
        "relation_annotations",
        "ner_f1",
        "re_f1",
        "overall_f1",
        "prediction_file",
        "per_sample_score_file",
        "notes",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def command_quote(path: Path) -> str:
    return '"' + str(path).replace("/", "\\") + '"'


def local_baseline_commands(row: Dict[str, Any], sample_path: Path, dev_path: Optional[Path], output_dir: Path) -> List[str]:
    cfg = DATASET_CONFIGS[row["dataset"]]
    ner_out = output_dir / "ner"
    re_out = output_dir / "re"
    dev_arg = f" --val_data {command_quote(dev_path)}" if dev_path else ""
    return [
        (
            "python scripts\\训练脚本\\train_advanced_ner.py "
            f"--train_data {command_quote(sample_path)}{dev_arg} "
            f"--output_dir {command_quote(ner_out)} "
            f"--backbone {cfg['encoder']} --decoder crf --batch_size 16 --learning_rate 2e-5 "
            f"--num_epochs 20 --max_length {cfg['max_length']} --device cpu"
        ),
        (
            "python scripts\\训练脚本\\train_re.py "
            f"--train_data {command_quote(sample_path)}{dev_arg} "
            f"--output_dir {command_quote(re_out)} "
            f"--backbone {cfg['encoder']} --batch_size 16 --learning_rate 2e-5 "
            f"--num_epochs 20 --early_stopping_patience 5 --max_length {cfg['max_length']} --device cpu"
        ),
    ]


def write_run_commands(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    lines = [
        "# Auto-generated commands for extended supervised PLM baselines.",
        "# Commands marked adapter_missing require connecting the corresponding external implementation.",
        "$ErrorActionPreference = 'Stop'",
        "Set-Location " + command_quote(PROJECT_ROOT),
        "",
    ]
    for row in rows:
        lines.append(f"# dataset={row['dataset']} model={row['model']} ratio={row['annotation_ratio']} seed={row['seed']} status={row['adapter_status']}")
        for cmd in row.get("commands", []):
            lines.append(cmd)
        if not row.get("commands"):
            lines.append(f"# adapter_missing: {row.get('notes', '')}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def prepare_extended_experiment(
    output_dir: Path,
    datasets: Sequence[str],
    source_overrides: Optional[Dict[str, Path]] = None,
    models: Sequence[str] = DEFAULT_MODELS,
    ratios: Sequence[float] = DEFAULT_RATIOS,
    seeds: Sequence[int] = DEFAULT_SEEDS,
    min_samples: int = 1,
    prepare_only: bool = True,
    include_fixed_refs: bool = True,
    max_echem_samples: int = 1255,
) -> List[Dict[str, Any]]:
    source_overrides = source_overrides or {}
    output_dir.mkdir(parents=True, exist_ok=True)
    all_rows: List[Dict[str, Any]] = []
    dataset_meta: Dict[str, Any] = {}

    for dataset in datasets:
        cfg = DATASET_CONFIGS[dataset]
        source = source_overrides.get(dataset, Path(cfg["source"]))
        pool = load_dataset_pool(dataset, source, seed=2026, max_echem_samples=max_echem_samples)
        dataset_meta[dataset] = {
            "source": str(source),
            "source_mode": pool["source_mode"],
            "total": pool["total"],
            "train": len(pool["train"]),
            "dev": len(pool["dev"]),
            "test": len(pool["test"]),
        }
        if pool["dev"]:
            write_json(output_dir / "splits" / dataset / "dev.json", pool["dev"])
        if pool["test"]:
            write_json(output_dir / "splits" / dataset / "test.json", pool["test"])
        dev_path = output_dir / "splits" / dataset / "dev.json" if pool["dev"] else None

        for model in models:
            info = adapter_info(model)
            for ratio in ratios:
                for seed in seeds:
                    sample = sample_budget(pool["train"], ratio, seed=seed, min_samples=min_samples)
                    ent_n, rel_n = count_annotations(sample)
                    run_dir = output_dir / dataset / model.replace("+", "_plus_") / ratio_dir(ratio) / f"seed_{seed}"
                    sample_path = run_dir / "labeled_train.json"
                    write_json(sample_path, sample)
                    row = {
                        "dataset": dataset,
                        "model": model,
                        "annotation_ratio": ratio_label(ratio),
                        "seed": seed,
                        "encoder": cfg["encoder"],
                        "max_sequence_length": cfg["max_length"],
                        "adapter_status": info.status,
                        "labeled_samples": len(sample),
                        "entity_annotations": ent_n,
                        "relation_annotations": rel_n,
                        "ner_f1": "",
                        "re_f1": "",
                        "overall_f1": "",
                        "prediction_file": "",
                        "per_sample_score_file": "",
                        "sample_path": str(sample_path),
                        "output_dir": str(run_dir),
                        "notes": info.note,
                    }
                    if model == "BERT-CRF+CasRel":
                        row["commands"] = local_baseline_commands(row, sample_path, dev_path, run_dir / "plm")
                    all_rows.append(row)

        if include_fixed_refs:
            for ref, metrics in FIXED_REFERENCES.get(dataset, {}).items():
                all_rows.append(
                    {
                        "dataset": dataset,
                        "model": ref,
                        "annotation_ratio": "--",
                        "seed": "--",
                        "encoder": "frozen LLM",
                        "max_sequence_length": "--",
                        "adapter_status": "fixed_reference",
                        "labeled_samples": "--",
                        "entity_annotations": "--",
                        "relation_annotations": "--",
                        "ner_f1": f"{metrics[0]:.4f}",
                        "re_f1": f"{metrics[1]:.4f}",
                        "overall_f1": f"{metrics[2]:.4f}",
                        "prediction_file": "",
                        "per_sample_score_file": "",
                        "notes": "fixed frozen-LLM reference from the manuscript",
                    }
                )

    manifest = {
        "datasets": dataset_meta,
        "models": list(models),
        "ratios": [ratio_label(r) for r in ratios],
        "seeds": list(seeds),
        "prepare_only": prepare_only,
        "rows": all_rows,
    }
    write_json(output_dir / "manifest.json", manifest)
    write_csv(output_dir / "results_template.csv", all_rows)
    write_run_commands(output_dir / "run_commands.ps1", all_rows)
    return all_rows


def execute_available_rows(rows: Sequence[Dict[str, Any]], limit: Optional[int] = None) -> List[Dict[str, Any]]:
    executed: List[Dict[str, Any]] = []
    for row in rows:
        if row.get("adapter_status") != "available" or not row.get("commands"):
            continue
        if limit is not None and len(executed) >= limit:
            break
        row_log = Path(row["output_dir"]) / "execution.log"
        row_log.parent.mkdir(parents=True, exist_ok=True)
        with row_log.open("w", encoding="utf-8") as log:
            for cmd in row["commands"]:
                log.write(f"$ {cmd}\n")
                log.flush()
                completed = subprocess.run(cmd, cwd=PROJECT_ROOT, shell=True, text=True, stdout=log, stderr=subprocess.STDOUT)
                if completed.returncode != 0:
                    row["adapter_status"] = "failed"
                    row["notes"] = f"command failed with exit code {completed.returncode}; see {row_log}"
                    break
        executed.append(row)
    return executed


def parse_csv_list(value: str) -> List[str]:
    return [x.strip() for x in value.split(",") if x.strip()]


def parse_float_list(value: str) -> List[float]:
    return [float(x.strip()) for x in value.split(",") if x.strip()]


def parse_int_list(value: str) -> List[int]:
    return [int(x.strip()) for x in value.split(",") if x.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare and optionally execute extended supervised PLM baselines.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--datasets", type=str, default="continuous_casting,electrochemistry")
    parser.add_argument("--models", type=str, default=",".join(DEFAULT_MODELS))
    parser.add_argument("--ratios", type=str, default="0.10,0.50,1.0")
    parser.add_argument("--seeds", type=str, default="2026,2027,2028")
    parser.add_argument("--min-samples", type=int, default=1)
    parser.add_argument("--max-echem-samples", type=int, default=1255)
    parser.add_argument("--execute", action="store_true", help="Run rows whose adapters are available.")
    parser.add_argument("--execute-limit", type=int, default=None, help="Limit executed available rows for smoke tests.")
    args = parser.parse_args()

    rows = prepare_extended_experiment(
        output_dir=args.output_dir,
        datasets=parse_csv_list(args.datasets),
        models=parse_csv_list(args.models),
        ratios=parse_float_list(args.ratios),
        seeds=parse_int_list(args.seeds),
        min_samples=args.min_samples,
        prepare_only=not args.execute,
        max_echem_samples=args.max_echem_samples,
    )
    executed: List[Dict[str, Any]] = []
    if args.execute:
        executed = execute_available_rows(rows, limit=args.execute_limit)
        write_csv(args.output_dir / "results_after_execution.csv", rows)

    status_counts: Dict[str, int] = {}
    for row in rows:
        status = str(row.get("adapter_status"))
        status_counts[status] = status_counts.get(status, 0) + 1

    print(f"Prepared extended PLM baseline experiment in: {args.output_dir}")
    print(f"Rows: {len(rows)}")
    print(f"Status counts: {status_counts}")
    if args.execute:
        print(f"Executed available rows: {len(executed)}")


if __name__ == "__main__":
    main()
