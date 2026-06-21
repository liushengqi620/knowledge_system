"""Evaluate saved local BERT-CRF+CasRel-style PLM baselines on held-out test splits.

The training adapter reports development metrics for early stopping. This
script loads the saved NER and RE final models and evaluates them on the
prepared test split so that paper tables do not mix development and test
scores.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from pathlib import Path
from statistics import mean, stdev
from typing import Any, Dict, List, Optional, Sequence, Tuple

import torch
from torch.utils.data import DataLoader
from transformers import AutoTokenizer


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def import_module_from_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def schema_for_dataset(dataset: str) -> Tuple[Optional[List[str]], Optional[List[str]]]:
    if dataset == "electrochemistry":
        return (
            ["MATERIAL", "VALUE"],
            ["Voltage", "Capacity", "Coulombic Efficiency", "Energy", "Conductivity", "???"],
        )
    return None, None


def load_ner_metrics(run_dir: Path, test_data: Path, dataset: str, device: str, batch_size: int, max_length: int) -> Dict[str, float]:
    train_ner = import_module_from_path(
        "train_advanced_ner_eval",
        PROJECT_ROOT / "scripts" / "训练脚本" / "train_advanced_ner.py",
    )
    from core.advanced_ner_model import AdvancedNERModel

    entity_types, _ = schema_for_dataset(dataset)
    model_dir = run_dir / "ner" / "final_model"
    checkpoint = torch.load(model_dir / "pytorch_model.bin", map_location=device)
    cfg = checkpoint.get("config", {})
    backbone = cfg.get("backbone_model", str(model_dir))
    decoder_type = cfg.get("decoder_type", "crf")
    if entity_types is None:
        entity_types = json.loads((model_dir / "entity_types.json").read_text(encoding="utf-8"))
    num_entity_types = len(entity_types)

    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AdvancedNERModel(
        backbone_model=backbone,
        num_entity_types=num_entity_types,
        decoder_type=decoder_type,
        device=device,
    )
    model.load_state_dict(checkpoint["model_state_dict"], strict=False)
    model.to(device)

    dataset_obj = train_ner.NERDataset(
        data_file=str(test_data),
        tokenizer=tokenizer,
        max_length=max_length,
        entity_types=entity_types,
    )
    loader = DataLoader(dataset_obj, batch_size=batch_size, shuffle=False)
    label_map = dataset_obj.label_map
    return train_ner.compute_ner_metrics(model, loader, device, label_map)


def load_re_metrics(run_dir: Path, test_data: Path, dataset: str, device: str, batch_size: int, max_length: int) -> Dict[str, float]:
    train_re = import_module_from_path(
        "train_re_eval",
        PROJECT_ROOT / "scripts" / "训练脚本" / "train_re.py",
    )
    from core.relation_extraction_model import RelationExtractionModel

    entity_types, relation_types = schema_for_dataset(dataset)
    if entity_types is None:
        entity_types = train_re.ENTITY_TYPES
    if relation_types is None:
        relation_types = train_re.RELATION_TYPES

    model_dir = run_dir / "re" / "final_model"
    checkpoint = torch.load(model_dir / "pytorch_model.bin", map_location=device)
    backbone = checkpoint.get("backbone", str(model_dir))
    tokenizer = AutoTokenizer.from_pretrained(model_dir)

    model = RelationExtractionModel(
        backbone_model=backbone,
        num_relation_types=len(relation_types),
        num_entity_types=len(entity_types),
        device=device,
    )
    model.load_state_dict(checkpoint["model_state_dict"], strict=False)
    model.tokenizer = tokenizer
    model.to(device)

    data = json.loads(test_data.read_text(encoding="utf-8"))
    dataset_obj = train_re.REDataset(
        data=data,
        tokenizer=tokenizer,
        relation_types=relation_types,
        entity_types=entity_types,
        max_length=max_length,
        negative_sampling=False,
        max_no_relation_ratio=None,
    )
    loader = DataLoader(dataset_obj, batch_size=batch_size, shuffle=False)
    return train_re.compute_metrics(model, loader, device, relation_types)


def evaluate_row(run_dir: Path, test_data: Path, dataset: str, device: str, batch_size: int, max_length: int) -> Dict[str, float]:
    ner = load_ner_metrics(run_dir, test_data, dataset, device, batch_size, max_length)
    re = load_re_metrics(run_dir, test_data, dataset, device, batch_size, max_length)
    ner_f1 = float(ner.get("f1", 0.0))
    re_f1 = float(re.get("f1", 0.0))
    return {
        "ner_f1": ner_f1,
        "re_f1": re_f1,
        "overall_f1": (ner_f1 + re_f1) / 2,
        "ner_precision": float(ner.get("precision", 0.0)),
        "ner_recall": float(ner.get("recall", 0.0)),
        "re_precision": float(re.get("precision", 0.0)),
        "re_recall": float(re.get("recall", 0.0)),
    }


def ratio_sort_key(label: str) -> int:
    return {"10%": 10, "50%": 50, "100%": 100}.get(label, 999)


def summarize(rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple[str, str, str], List[Dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault((row["dataset"], row["model"], row["annotation_ratio"]), []).append(row)
    out: List[Dict[str, Any]] = []
    for (dataset, model, ratio), vals in sorted(grouped.items(), key=lambda x: (x[0][0], x[0][1], ratio_sort_key(x[0][2]))):
        def stat(metric: str) -> Tuple[float, float]:
            xs = [float(v[metric]) for v in vals]
            return mean(xs), stdev(xs) if len(xs) > 1 else 0.0
        ner_m, ner_s = stat("ner_f1")
        re_m, re_s = stat("re_f1")
        overall_m, overall_s = stat("overall_f1")
        out.append(
            {
                "dataset": dataset,
                "model": model,
                "annotation_ratio": ratio,
                "seeds": ",".join(str(v["seed"]) for v in vals),
                "ner_f1_mean": f"{ner_m:.4f}",
                "ner_f1_std": f"{ner_s:.4f}",
                "re_f1_mean": f"{re_m:.4f}",
                "re_f1_std": f"{re_s:.4f}",
                "overall_f1_mean": f"{overall_m:.4f}",
                "overall_f1_std": f"{overall_s:.4f}",
            }
        )
    return out


def write_csv(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate saved local PLM baselines on test splits.")
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--datasets", default="continuous_casting,electrochemistry")
    parser.add_argument("--ratios", default="10%,50%,100%")
    parser.add_argument("--seeds", default="2026,2027,2028")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    rows: List[Dict[str, Any]] = []
    for dataset in [x.strip() for x in args.datasets.split(",") if x.strip()]:
        test_data = args.run_root / "splits" / dataset / "test.json"
        if not test_data.exists():
            raise FileNotFoundError(f"Missing test split: {test_data}")
        max_length = 384 if dataset == "electrochemistry" else 256
        for ratio in [x.strip() for x in args.ratios.split(",") if x.strip()]:
            ratio_dir = ratio.replace("%", "pct")
            for seed in [x.strip() for x in args.seeds.split(",") if x.strip()]:
                run_dir = args.run_root / dataset / "BERT-CRF_plus_CasRel" / ratio_dir / f"seed_{seed}" / "plm"
                if not (run_dir / "summary_metrics.json").exists():
                    raise FileNotFoundError(f"Missing trained run: {run_dir}")
                metrics = evaluate_row(run_dir, test_data, dataset, args.device, args.batch_size, max_length)
                row = {
                    "dataset": dataset,
                    "model": "BERT-CRF+CasRel",
                    "annotation_ratio": ratio,
                    "seed": seed,
                    **{k: f"{v:.6f}" for k, v in metrics.items()},
                }
                rows.append(row)
                (run_dir / "test_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    output = args.output or (args.run_root / "test_results.csv")
    write_csv(output, rows)
    summary = summarize(rows)
    write_csv(output.with_name(output.stem + "_summary.csv"), summary)
    print(f"Wrote {output}")
    print(f"Wrote {output.with_name(output.stem + '_summary.csv')}")


if __name__ == "__main__":
    main()
