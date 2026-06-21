"""Run the in-repository BERT-CRF plus relation-classification baseline.

This is the executable adapter used by ``extended_plm_baselines.py``.  It keeps
dataset-specific schemas explicit, especially for the electrochemistry dataset,
where the default project schema would otherwise fall back to steel casting.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parent.parent

ECHEM_ENTITY_TYPES = ["MATERIAL", "VALUE"]
ECHEM_RELATION_TYPES = [
    "Voltage",
    "Capacity",
    "Coulombic Efficiency",
    "Energy",
    "Conductivity",
    "无关系",
]


def import_module_from_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def schema_for_dataset(dataset: str) -> tuple[Optional[List[str]], Optional[List[str]]]:
    if dataset == "electrochemistry":
        return ECHEM_ENTITY_TYPES, ECHEM_RELATION_TYPES
    return None, None


def max_numeric(values) -> Optional[float]:
    nums = [float(v) for v in values if isinstance(v, (int, float))]
    return max(nums) if nums else None


def collect_metrics(output_dir: Path) -> Dict[str, float]:
    ner_path = output_dir / "ner" / "training_metrics.json"
    re_path = output_dir / "re" / "training_metrics.json"
    ner_data = json.loads(ner_path.read_text(encoding="utf-8"))
    re_data = json.loads(re_path.read_text(encoding="utf-8"))

    ner_f1 = max_numeric(ner_data.get("val_metrics", {}).get("f1", []))
    if ner_f1 is None:
        ner_f1 = max_numeric(ner_data.get("train_metrics", {}).get("f1", []))
    re_f1 = max_numeric(re_data.get("val_f1", []))
    if re_f1 is None:
        re_f1 = max_numeric(re_data.get("train_f1", []))
    ner_f1 = float(ner_f1 or 0.0)
    re_f1 = float(re_f1 or 0.0)
    return {"ner_f1": ner_f1, "re_f1": re_f1, "overall_f1": (ner_f1 + re_f1) / 2}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run local BERT-CRF+CasRel-style PLM baseline.")
    parser.add_argument("--dataset", required=True, choices=["continuous_casting", "electrochemistry"])
    parser.add_argument("--train-data", type=Path, required=True)
    parser.add_argument("--val-data", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--encoder", required=True)
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()

    ner_mod = import_module_from_path(
        "train_advanced_ner_local",
        PROJECT_ROOT / "scripts" / "训练脚本" / "train_advanced_ner.py",
    )
    re_mod = import_module_from_path(
        "train_re_local",
        PROJECT_ROOT / "scripts" / "训练脚本" / "train_re.py",
    )

    entity_types, relation_types = schema_for_dataset(args.dataset)
    if entity_types is not None:
        ner_mod.ENTITY_TYPES = entity_types
        re_mod.ENTITY_TYPES = entity_types
    if relation_types is not None:
        re_mod.RELATION_TYPES = relation_types

    args.output_dir.mkdir(parents=True, exist_ok=True)
    ner_out = args.output_dir / "ner"
    re_out = args.output_dir / "re"
    val_path = str(args.val_data) if args.val_data and args.val_data.exists() else None

    ner_mod.train_ner_model(
        train_data_file=str(args.train_data),
        val_data_file=val_path,
        backbone_model=args.encoder,
        decoder_type="crf",
        output_dir=str(ner_out),
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        num_epochs=args.epochs,
        device=args.device,
        max_length=args.max_length,
        entity_types=entity_types,
    )

    re_mod.train(
        train_data_path=str(args.train_data),
        val_data_path=val_path,
        output_dir=str(re_out),
        backbone=args.encoder,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        num_epochs=args.epochs,
        max_no_relation_ratio=2.0,
        max_length=args.max_length,
        device=args.device,
    )

    metrics = collect_metrics(args.output_dir)
    (args.output_dir / "summary_metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False))


if __name__ == "__main__":
    main()
