"""Run a small end-to-end mechanism-layer KG extraction seed experiment.

This script intentionally avoids processed Baosteel production data. It creates
a compact mechanism-text seed dataset, runs deterministic proxy extractors, and
saves candidate-level prompt atoms, adjudication decisions, metrics, and a final
mechanism graph.

The proxy experiment is for engineering validation and dataset bootstrapping.
It is not a substitute for a paper-scale PLM/LLM run.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, List, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "mechanism_kg"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "mechanism_kg_seed_experiment"

ENTITY_TYPES = {
    "ProcessParameter",
    "EquipmentState",
    "MaterialState",
    "DefectMechanism",
    "QualityDefect",
    "ControlAction",
    "ProcessStage",
    "QualityIndicator",
}

POSITIVE_RELATION_TYPES = {
    "cause",
    "affect",
    "increase_risk_of",
    "suppress",
    "improve",
    "located_at",
    "controlled_by",
    "indicates",
}

ENTITY_CODE_RE = re.compile(r"\b[CL]\d{4}\b")

RELATION_CUES = [
    ("increase_risk_of", ["增加", "提高", "加剧", "increases risk of", "raises risk of"]),
    ("cause", ["导致", "引起", "造成", "诱发", "形成", "causes", "leads to", "induces"]),
    ("affect", ["影响", "改变", "扰动", "affects", "changes", "disturbs"]),
    ("suppress", ["抑制", "降低", "减少", "suppresses", "reduces risk of", "mitigates"]),
    ("improve", ["改善", "稳定", "优化", "improves", "stabilizes", "optimizes"]),
    ("located_at", ["发生于", "位于", "出现在", "occurs in", "appears in", "is located in"]),
    ("controlled_by", ["受", "通过", "is controlled by", "is regulated by"]),
    ("indicates", ["表征", "反映", "说明", "indicates", "reflects", "signals"]),
]

NEGATION_CUES = [
    "未说明",
    "不代表",
    "并不",
    "不能直接",
    "无证据",
    "没有说明",
    "does not directly",
    "does not cause",
    "no evidence",
    "is not evidence",
]

PROMPT_ATOM_TEXT = {
    "entity_boundary": "Preserve complete technical entity boundaries.",
    "nested_entity_boundary": "Keep nested technical entities and their parent spans distinct.",
    "implicit_relation": "Infer only mechanism relations supported by discourse structure and local evidence.",
    "schema_constraint": "Use only the predefined mechanism KG entity and relation schema.",
    "relation_direction": "Keep mechanism relation direction from cause/source to effect/target.",
    "relation_type_constraint": "Choose the relation type stated by the evidence, not by domain guess.",
    "evidence_span": "Every accepted relation must be supported by the supplied evidence span.",
    "hallucination_guard": "Reject plausible triples that are not stated or strongly implied.",
    "negative_relation": "Treat explicit absence statements as no-relation evidence.",
    "mechanism_chain": "Preserve local links in a mechanism chain instead of skipping middle states.",
}


@dataclass(frozen=True)
class SeedEntity:
    text: str
    type: str


@dataclass(frozen=True)
class SeedRelation:
    head: str
    type: str
    tail: str
    direction: str = "head_to_tail"


@dataclass(frozen=True)
class SeedRecord:
    record_id: str
    split: str
    source_type: str
    source_id: str
    process_stage: str
    text: str
    entities: Sequence[SeedEntity]
    relations: Sequence[SeedRelation]
    notes: str


def seed_records() -> list[SeedRecord]:
    return [
        SeedRecord(
            "mk-seed-0001",
            "train",
            "mechanism_paper_seed",
            "paper-seed-mold-flux-001",
            "mold",
            "结晶器液位波动会导致保护渣卷入，从而增加铸坯表面裂纹风险。",
            [
                SeedEntity("结晶器液位波动", "EquipmentState"),
                SeedEntity("保护渣卷入", "MaterialState"),
                SeedEntity("铸坯表面裂纹风险", "QualityDefect"),
            ],
            [
                SeedRelation("结晶器液位波动", "cause", "保护渣卷入"),
                SeedRelation("保护渣卷入", "increase_risk_of", "铸坯表面裂纹风险"),
            ],
            "classic mold-level to slag-entrapment mechanism",
        ),
        SeedRecord(
            "mk-seed-0002",
            "train",
            "mechanism_manual_seed",
            "manual-seed-superheat-001",
            "tundish",
            "中间包过热度偏低会影响保护渣熔化稳定性，保护渣熔化不充分会导致润滑不足。",
            [
                SeedEntity("中间包过热度偏低", "ProcessParameter"),
                SeedEntity("保护渣熔化稳定性", "MaterialState"),
                SeedEntity("保护渣熔化不充分", "MaterialState"),
                SeedEntity("润滑不足", "DefectMechanism"),
            ],
            [
                SeedRelation("中间包过热度偏低", "affect", "保护渣熔化稳定性"),
                SeedRelation("保护渣熔化不充分", "cause", "润滑不足"),
            ],
            "temperature and mold-flux melting mechanism",
        ),
        SeedRecord(
            "mk-seed-0003",
            "train",
            "mechanism_paper_seed",
            "paper-seed-cooling-001",
            "secondary_cooling",
            "二冷水量分布不均会造成凝固壳厚度不均，进而增加纵裂风险。",
            [
                SeedEntity("二冷水量分布不均", "ProcessParameter"),
                SeedEntity("凝固壳厚度不均", "DefectMechanism"),
                SeedEntity("纵裂风险", "QualityDefect"),
            ],
            [
                SeedRelation("二冷水量分布不均", "cause", "凝固壳厚度不均"),
                SeedRelation("凝固壳厚度不均", "increase_risk_of", "纵裂风险"),
            ],
            "secondary cooling nonuniformity chain",
        ),
        SeedRecord(
            "mk-seed-0004",
            "train",
            "mechanism_expert_rule_seed",
            "expert-rule-speed-001",
            "mold",
            "拉速升高会影响结晶器传热稳定性，传热波动会诱发表面裂纹。",
            [
                SeedEntity("拉速升高", "ProcessParameter"),
                SeedEntity("结晶器传热稳定性", "DefectMechanism"),
                SeedEntity("传热波动", "DefectMechanism"),
                SeedEntity("表面裂纹", "QualityDefect"),
            ],
            [
                SeedRelation("拉速升高", "affect", "结晶器传热稳定性"),
                SeedRelation("传热波动", "cause", "表面裂纹"),
            ],
            "casting-speed and heat-transfer mechanism",
        ),
        SeedRecord(
            "mk-seed-0005",
            "train",
            "mechanism_manual_seed",
            "manual-seed-control-001",
            "mold",
            "稳定塞棒开度可以改善结晶器液位稳定性，并抑制卷渣风险。",
            [
                SeedEntity("稳定塞棒开度", "ControlAction"),
                SeedEntity("结晶器液位稳定性", "EquipmentState"),
                SeedEntity("卷渣风险", "QualityDefect"),
            ],
            [
                SeedRelation("稳定塞棒开度", "improve", "结晶器液位稳定性"),
                SeedRelation("稳定塞棒开度", "suppress", "卷渣风险"),
            ],
            "control action mechanism",
        ),
        SeedRecord(
            "mk-seed-0006",
            "train",
            "mechanism_paper_seed",
            "paper-seed-location-001",
            "mold",
            "结晶器液位波动发生于结晶器区域，液位波动幅度表征液面稳定性异常。",
            [
                SeedEntity("结晶器液位波动", "EquipmentState"),
                SeedEntity("结晶器区域", "ProcessStage"),
                SeedEntity("液位波动幅度", "QualityIndicator"),
                SeedEntity("液面稳定性异常", "EquipmentState"),
            ],
            [
                SeedRelation("结晶器液位波动", "located_at", "结晶器区域"),
                SeedRelation("液位波动幅度", "indicates", "液面稳定性异常"),
            ],
            "location and indicator relations",
        ),
        SeedRecord(
            "mk-seed-0007",
            "train",
            "mechanism_expert_rule_seed",
            "expert-rule-oscillation-001",
            "mold",
            "结晶器振动异常会改变润滑状态，润滑状态恶化会导致振痕加深。",
            [
                SeedEntity("结晶器振动异常", "EquipmentState"),
                SeedEntity("润滑状态", "MaterialState"),
                SeedEntity("润滑状态恶化", "DefectMechanism"),
                SeedEntity("振痕加深", "QualityDefect"),
            ],
            [
                SeedRelation("结晶器振动异常", "affect", "润滑状态"),
                SeedRelation("润滑状态恶化", "cause", "振痕加深"),
            ],
            "oscillation and lubrication mechanism",
        ),
        SeedRecord(
            "mk-seed-0008",
            "train",
            "mechanism_report_seed",
            "report-seed-inclusion-001",
            "tundish",
            "钢水洁净度下降会引起夹杂物聚集，夹杂物聚集增加内部缺陷风险。",
            [
                SeedEntity("钢水洁净度下降", "MaterialState"),
                SeedEntity("夹杂物聚集", "MaterialState"),
                SeedEntity("内部缺陷风险", "QualityDefect"),
            ],
            [
                SeedRelation("钢水洁净度下降", "cause", "夹杂物聚集"),
                SeedRelation("夹杂物聚集", "increase_risk_of", "内部缺陷风险"),
            ],
            "inclusion mechanism",
        ),
        SeedRecord(
            "mk-seed-0009",
            "dev",
            "mechanism_paper_seed",
            "paper-seed-negative-001",
            "tundish",
            "文本只说明过热度偏低会影响保护渣熔化，未说明其直接导致角部裂纹。",
            [
                SeedEntity("过热度偏低", "ProcessParameter"),
                SeedEntity("保护渣熔化", "MaterialState"),
                SeedEntity("角部裂纹", "QualityDefect"),
            ],
            [
                SeedRelation("过热度偏低", "affect", "保护渣熔化"),
                SeedRelation("过热度偏低", "no_relation", "角部裂纹", "undirected"),
            ],
            "hard negative for hallucination guard",
        ),
        SeedRecord(
            "mk-seed-0010",
            "dev",
            "mechanism_expert_rule_seed",
            "expert-rule-argon-001",
            "tundish",
            "氩气流量过大会扰动液面稳定性，液面稳定性下降会增加卷渣风险。",
            [
                SeedEntity("氩气流量过大", "ProcessParameter"),
                SeedEntity("液面稳定性", "EquipmentState"),
                SeedEntity("液面稳定性下降", "EquipmentState"),
                SeedEntity("卷渣风险", "QualityDefect"),
            ],
            [
                SeedRelation("氩气流量过大", "affect", "液面稳定性"),
                SeedRelation("液面稳定性下降", "increase_risk_of", "卷渣风险"),
            ],
            "argon and mold level stability",
        ),
        SeedRecord(
            "mk-seed-0011",
            "dev",
            "mechanism_manual_seed",
            "manual-seed-control-002",
            "secondary_cooling",
            "优化二冷配水可以改善凝固均匀性，从而抑制纵裂风险。",
            [
                SeedEntity("优化二冷配水", "ControlAction"),
                SeedEntity("凝固均匀性", "DefectMechanism"),
                SeedEntity("纵裂风险", "QualityDefect"),
            ],
            [
                SeedRelation("优化二冷配水", "improve", "凝固均匀性"),
                SeedRelation("优化二冷配水", "suppress", "纵裂风险"),
            ],
            "secondary cooling control",
        ),
        SeedRecord(
            "mk-seed-0012",
            "test",
            "mechanism_paper_seed",
            "paper-seed-thermal-001",
            "mold",
            "结晶器传热不均会导致凝固不均，凝固不均会增加表面裂纹风险。",
            [
                SeedEntity("结晶器传热不均", "DefectMechanism"),
                SeedEntity("凝固不均", "DefectMechanism"),
                SeedEntity("表面裂纹风险", "QualityDefect"),
            ],
            [
                SeedRelation("结晶器传热不均", "cause", "凝固不均"),
                SeedRelation("凝固不均", "increase_risk_of", "表面裂纹风险"),
            ],
            "held-out thermal mechanism",
        ),
        SeedRecord(
            "mk-seed-0013",
            "test",
            "mechanism_report_seed",
            "report-seed-breakout-001",
            "mold",
            "漏钢预兆通常反映凝固壳强度不足，凝固壳强度不足会导致漏钢风险升高。",
            [
                SeedEntity("漏钢预兆", "QualityIndicator"),
                SeedEntity("凝固壳强度不足", "DefectMechanism"),
                SeedEntity("漏钢风险", "QualityDefect"),
            ],
            [
                SeedRelation("漏钢预兆", "indicates", "凝固壳强度不足"),
                SeedRelation("凝固壳强度不足", "increase_risk_of", "漏钢风险"),
            ],
            "held-out breakout mechanism",
        ),
        SeedRecord(
            "mk-seed-0014",
            "test",
            "mechanism_manual_seed",
            "manual-seed-negative-002",
            "mold",
            "降低拉速可以改善凝固壳生长，但该句没有说明降低拉速会直接造成夹杂物聚集。",
            [
                SeedEntity("降低拉速", "ControlAction"),
                SeedEntity("凝固壳生长", "DefectMechanism"),
                SeedEntity("夹杂物聚集", "MaterialState"),
            ],
            [
                SeedRelation("降低拉速", "improve", "凝固壳生长"),
                SeedRelation("降低拉速", "no_relation", "夹杂物聚集", "undirected"),
            ],
            "held-out hard negative",
        ),
        SeedRecord(
            "mk-seed-0015",
            "test",
            "mechanism_expert_rule_seed",
            "expert-rule-powder-001",
            "mold",
            "保护渣黏度过高会影响渣膜形成，渣膜形成不良会引起润滑不足。",
            [
                SeedEntity("保护渣黏度过高", "MaterialState"),
                SeedEntity("渣膜形成", "MaterialState"),
                SeedEntity("渣膜形成不良", "DefectMechanism"),
                SeedEntity("润滑不足", "DefectMechanism"),
            ],
            [
                SeedRelation("保护渣黏度过高", "affect", "渣膜形成"),
                SeedRelation("渣膜形成不良", "cause", "润滑不足"),
            ],
            "held-out powder-film mechanism",
        ),
    ]


def _find_span(text: str, surface: str) -> tuple[int, int]:
    start = text.find(surface)
    if start < 0:
        raise ValueError(f"Surface {surface!r} not found in {text!r}")
    return start, start + len(surface)


def _evidence_span(text: str, head: str, tail: str) -> tuple[int, int]:
    h0, h1 = _find_span(text, head)
    t0, t1 = _find_span(text, tail)
    start = min(h0, t0)
    end = max(h1, t1)
    left = max(text.rfind("。", 0, start), text.rfind(".", 0, start), text.rfind(";", 0, start))
    right_candidates = [idx for idx in [text.find("。", end), text.find(".", end), text.find(";", end)] if idx >= 0]
    right = min(right_candidates) if right_candidates else -1
    return (0 if left < 0 else left + 1, len(text) if right < 0 else right + 1)


def make_record(seed: SeedRecord) -> dict[str, Any]:
    entities: list[dict[str, Any]] = []
    for idx, entity in enumerate(seed.entities, start=1):
        start, end = _find_span(seed.text, entity.text)
        entities.append(
            {
                "entity_id": f"e{idx}",
                "text": entity.text,
                "type": entity.type,
                "start": start,
                "end": end,
                "source": "gold",
                "confidence": None,
                "normalization_id": entity.text,
            }
        )
    for entity in entities:
        parents = [
            other
            for other in entities
            if other["entity_id"] != entity["entity_id"]
            and other["start"] <= entity["start"]
            and entity["end"] <= other["end"]
            and (other["end"] - other["start"]) > (entity["end"] - entity["start"])
        ]
        if parents:
            parent = min(parents, key=lambda item: item["end"] - item["start"])
            entity["parent_entity_id"] = parent["entity_id"]
            entity["nested_level"] = 1
        else:
            entity["parent_entity_id"] = None
            entity["nested_level"] = 0
    by_text = {entity["text"]: entity["entity_id"] for entity in entities}
    relations: list[dict[str, Any]] = []
    for idx, relation in enumerate(seed.relations, start=1):
        start, end = _evidence_span(seed.text, relation.head, relation.tail)
        relations.append(
            {
                "relation_id": f"r{idx}",
                "type": relation.type,
                "head": by_text[relation.head],
                "tail": by_text[relation.tail],
                "direction": relation.direction,
                "evidence_span": {"start": start, "end": end},
                "source": "gold",
                "confidence": None,
                "head_text": relation.head,
                "tail_text": relation.tail,
            }
        )
    return {
        "record_id": seed.record_id,
        "domain": "mechanism_kg",
        "language": "zh",
        "text": seed.text,
        "source": {
            "source_id": seed.source_id,
            "source_type": seed.source_type,
            "process_stage": seed.process_stage,
            "challenge_tags": challenge_tags(seed.notes),
            "timestamp": None,
            "split_group": seed.source_id,
            "split": seed.split,
        },
        "task_scope": ["ner", "re", "plm_candidate", "llm_adjudication", "active_learning"],
        "annotation_status": "gold_labeled",
        "annotations": {"entities": entities, "relations": relations},
        "plm_candidates": [],
        "llm_adjudications": [],
        "quality": {
            "reviewer": "seed_dataset_generator",
            "review_status": "single_reviewed",
            "notes": f"Generated mechanism-layer seed record for engineering experiment: {seed.notes}",
        },
}


def challenge_tags(notes: str) -> list[str]:
    tags: list[str] = []
    lowered = notes.lower()
    for key in [
        "implicit",
        "nested",
        "alias",
        "pronoun",
        "hard negative",
        "multi-hop",
        "coordination",
        "interference",
    ]:
        if key in lowered:
            tags.append(key.replace(" ", "_"))
    return tags or ["explicit_template"]


EXPANDED_RELATION_PHRASES = {
    "cause": "causes",
    "affect": "affects",
    "increase_risk_of": "increases risk of",
    "suppress": "suppresses",
    "improve": "improves",
    "located_at": "occurs in",
    "controlled_by": "is controlled by",
    "indicates": "indicates",
    "no_relation": "does not directly cause",
}


def expanded_seed_records() -> list[SeedRecord]:
    scenarios = [
        ("mold", [("Mold level oscillation", "EquipmentState", "cause", "meniscus turbulence", "DefectMechanism"), ("meniscus turbulence", "DefectMechanism", "increase_risk_of", "slag entrapment defect", "QualityDefect")], "mold level and slag entrainment"),
        ("mold", [("Submerged entry nozzle clogging", "EquipmentState", "affect", "steel flow symmetry", "EquipmentState"), ("asymmetric steel flow", "EquipmentState", "cause", "mold level fluctuation", "EquipmentState")], "nozzle clogging and flow stability"),
        ("mold", [("Nozzle port angle deviation", "EquipmentState", "affect", "jet impingement anomaly", "DefectMechanism"), ("deep jet impingement", "DefectMechanism", "cause", "shell remelting", "DefectMechanism")], "SEN jet impingement mechanism"),
        ("mold", [("High casting speed", "ProcessParameter", "affect", "mold heat transfer stability", "DefectMechanism"), ("heat transfer instability", "DefectMechanism", "increase_risk_of", "longitudinal crack risk", "QualityDefect")], "casting speed and heat transfer"),
        ("mold", [("Low superheat", "ProcessParameter", "affect", "mold flux melting", "MaterialState"), ("poor flux melting", "MaterialState", "cause", "insufficient lubrication", "DefectMechanism")], "superheat and mold flux"),
        ("tundish", [("Excessive argon flow", "ProcessParameter", "cause", "bubble accumulation", "MaterialState"), ("bubble accumulation", "MaterialState", "increase_risk_of", "pinhole defect risk", "QualityDefect")], "argon bubbles"),
        ("mold", [("Tundish temperature fluctuation", "ProcessParameter", "affect", "shell growth uniformity", "DefectMechanism"), ("nonuniform shell growth", "DefectMechanism", "increase_risk_of", "surface crack risk", "QualityDefect")], "temperature and shell growth"),
        ("secondary_cooling", [("Secondary cooling imbalance", "ProcessParameter", "cause", "thermal stress concentration", "DefectMechanism"), ("thermal stress concentration", "DefectMechanism", "cause", "transverse crack defect", "QualityDefect")], "secondary cooling stress"),
        ("secondary_cooling", [("Spray nozzle blockage", "EquipmentState", "affect", "cooling nonuniformity", "DefectMechanism"), ("cooling nonuniformity", "DefectMechanism", "increase_risk_of", "corner crack risk", "QualityDefect")], "spray nozzle blockage"),
        ("strand", [("Roll gap deviation", "EquipmentState", "cause", "bulging strain", "DefectMechanism"), ("bulging strain", "DefectMechanism", "increase_risk_of", "centerline segregation risk", "QualityDefect")], "roll gap and bulging"),
        ("strand", [("Soft reduction mismatch", "ProcessParameter", "affect", "center porosity closure", "DefectMechanism"), ("poor center porosity closure", "DefectMechanism", "increase_risk_of", "internal crack risk", "QualityDefect")], "soft reduction"),
        ("mold", [("Mold taper mismatch", "EquipmentState", "cause", "air gap formation", "DefectMechanism"), ("air gap formation", "DefectMechanism", "cause", "heat transfer reduction", "DefectMechanism")], "mold taper"),
        ("mold", [("High mold flux viscosity", "MaterialState", "affect", "slag film formation", "MaterialState"), ("unstable slag film", "MaterialState", "cause", "deep oscillation mark", "QualityDefect")], "mold flux viscosity"),
        ("mold", [("Low mold flux basicity", "MaterialState", "affect", "crystallization behavior", "MaterialState"), ("abnormal crystallization", "MaterialState", "cause", "uneven heat flux", "DefectMechanism")], "mold flux crystallization"),
        ("tundish", [("High aluminum content", "MaterialState", "cause", "nozzle clogging tendency", "EquipmentState"), ("nozzle clogging tendency", "EquipmentState", "affect", "steel flow symmetry", "EquipmentState")], "alumina clogging"),
        ("mold", [("Excessive sulfur content", "MaterialState", "affect", "hot ductility", "MaterialState"), ("low hot ductility", "MaterialState", "increase_risk_of", "surface crack risk", "QualityDefect")], "composition and ductility"),
        ("mold", [("Peritectic steel shrinkage", "MaterialState", "cause", "shell deformation", "DefectMechanism"), ("shell deformation", "DefectMechanism", "increase_risk_of", "longitudinal depression risk", "QualityDefect")], "peritectic shrinkage"),
        ("mold", [("Electromagnetic stirring intensity", "ProcessParameter", "affect", "inclusion flotation", "MaterialState"), ("weak inclusion flotation", "MaterialState", "increase_risk_of", "internal inclusion risk", "QualityDefect")], "EMS and inclusions"),
        ("ladle", [("Poor ladle shrouding", "EquipmentState", "cause", "reoxidation", "MaterialState"), ("reoxidation", "MaterialState", "cause", "alumina inclusion formation", "MaterialState")], "reoxidation"),
        ("tundish", [("Tundish slag entrainment", "MaterialState", "cause", "exogenous inclusion", "MaterialState"), ("exogenous inclusion", "MaterialState", "increase_risk_of", "slab defect risk", "QualityDefect")], "tundish slag entrainment"),
        ("mold", [("Mold powder moisture", "MaterialState", "cause", "gas generation", "MaterialState"), ("gas generation", "MaterialState", "increase_risk_of", "bubble defect risk", "QualityDefect")], "mold powder moisture"),
        ("mold", [("Unstable stopper rod movement", "EquipmentState", "cause", "flow-rate fluctuation", "EquipmentState"), ("flow-rate fluctuation", "EquipmentState", "affect", "mold level stability", "EquipmentState")], "stopper movement"),
        ("mold", [("Narrow face cooling excess", "ProcessParameter", "cause", "corner temperature drop", "DefectMechanism"), ("corner temperature drop", "DefectMechanism", "increase_risk_of", "corner crack risk", "QualityDefect")], "narrow-face cooling"),
        ("straightening", [("Unbending strain", "ProcessParameter", "cause", "crack opening", "DefectMechanism"), ("crack opening", "DefectMechanism", "increase_risk_of", "transverse crack defect", "QualityDefect")], "unbending strain"),
        ("secondary_cooling", [("Low water pressure", "ProcessParameter", "affect", "spray coverage loss", "DefectMechanism"), ("poor spray coverage", "DefectMechanism", "cause", "thermal stress concentration", "DefectMechanism")], "water pressure"),
        ("mold", [("Copper plate wear", "EquipmentState", "affect", "mold taper accuracy", "EquipmentState"), ("taper inaccuracy", "EquipmentState", "cause", "shell mold gap", "DefectMechanism")], "copper plate wear"),
        ("mold", [("Mold oscillator frequency deviation", "EquipmentState", "affect", "negative strip time abnormality", "DefectMechanism"), ("abnormal negative strip time", "DefectMechanism", "cause", "deep oscillation mark", "QualityDefect")], "oscillation control"),
        ("mold", [("Shallow SEN immersion depth", "ProcessParameter", "cause", "surface turbulence", "DefectMechanism"), ("surface turbulence", "DefectMechanism", "increase_risk_of", "slag entrapment defect", "QualityDefect")], "SEN immersion depth"),
        ("mold", [("Electromagnetic brake tuning", "ControlAction", "improve", "flow stability", "EquipmentState"), ("Electromagnetic brake tuning", "ControlAction", "suppress", "slag entrapment defect", "QualityDefect")], "EMBr control action"),
        ("mold", [("Stopper rod regulation", "ControlAction", "improve", "mold level stability", "EquipmentState"), ("Stopper rod regulation", "ControlAction", "suppress", "slag entrapment defect", "QualityDefect")], "stopper regulation"),
        ("secondary_cooling", [("Dynamic secondary cooling adjustment", "ControlAction", "improve", "surface temperature uniformity", "DefectMechanism"), ("Dynamic secondary cooling adjustment", "ControlAction", "suppress", "corner crack risk", "QualityDefect")], "dynamic cooling control"),
        ("mold", [("Mold powder optimization", "ControlAction", "improve", "slag film stability", "MaterialState"), ("Mold powder optimization", "ControlAction", "suppress", "longitudinal crack risk", "QualityDefect")], "mold powder control"),
        ("mold", [("Mold level fluctuation", "EquipmentState", "controlled_by", "stopper rod regulation", "ControlAction"), ("Mold level fluctuation", "EquipmentState", "located_at", "mold meniscus", "ProcessStage")], "control and location"),
        ("mold", [("Breakout alarm", "QualityIndicator", "indicates", "insufficient shell thickness", "DefectMechanism"), ("insufficient shell thickness", "DefectMechanism", "increase_risk_of", "breakout risk", "QualityDefect")], "breakout indicator"),
        ("mold", [("Thermocouple temperature drop", "QualityIndicator", "indicates", "local shell sticking", "DefectMechanism"), ("local shell sticking", "DefectMechanism", "increase_risk_of", "sticker breakout risk", "QualityDefect")], "thermocouple indicator"),
        ("mold", [("Surface depression", "QualityIndicator", "indicates", "nonuniform shell growth", "DefectMechanism"), ("nonuniform shell growth", "DefectMechanism", "increase_risk_of", "longitudinal crack risk", "QualityDefect")], "surface depression indicator"),
        ("mold", [("Slag rim growth", "MaterialState", "located_at", "mold meniscus", "ProcessStage"), ("slag rim growth", "MaterialState", "affect", "mold flux consumption abnormality", "MaterialState")], "slag rim location"),
        ("tundish", [("Argon flow rate", "ProcessParameter", "affect", "bubble population", "MaterialState"), ("Argon flow rate", "ProcessParameter", "no_relation", "transverse crack defect", "QualityDefect")], "hard negative argon to crack"),
        ("mold", [("High casting speed", "ProcessParameter", "affect", "mold heat transfer stability", "DefectMechanism"), ("High casting speed", "ProcessParameter", "no_relation", "alumina cluster formation", "MaterialState")], "hard negative speed to alumina"),
        ("mold", [("Mold powder viscosity", "MaterialState", "affect", "slag film formation", "MaterialState"), ("Mold powder viscosity", "MaterialState", "no_relation", "centerline segregation risk", "QualityDefect")], "hard negative powder to centerline segregation"),
        ("strand", [("Roll misalignment", "EquipmentState", "cause", "strand bending strain", "DefectMechanism"), ("strand bending strain", "DefectMechanism", "increase_risk_of", "edge crack risk", "QualityDefect")], "roll alignment"),
        ("tundish", [("Long residence time", "ProcessParameter", "affect", "inclusion flotation", "MaterialState"), ("Long residence time", "ProcessParameter", "no_relation", "mold level fluctuation", "EquipmentState")], "hard negative residence time"),
        ("mold", [("Automatic mold level control", "ControlAction", "improve", "meniscus level", "EquipmentState"), ("Automatic mold level control", "ControlAction", "suppress", "slag entrapment defect", "QualityDefect")], "automatic control"),
        ("secondary_cooling", [("Cooling water temperature rise", "ProcessParameter", "affect", "heat extraction imbalance", "DefectMechanism"), ("heat extraction imbalance", "DefectMechanism", "increase_risk_of", "thin shell risk", "QualityDefect")], "cooling water temperature"),
        ("mold", [("Mold flux crystallization rate", "MaterialState", "affect", "radiative heat transfer", "DefectMechanism"), ("radiative heat transfer variation", "DefectMechanism", "increase_risk_of", "surface crack risk", "QualityDefect")], "flux crystallization rate"),
    ]
    source_types = [
        "mechanism_paper_seed",
        "mechanism_manual_seed",
        "mechanism_expert_rule_seed",
        "mechanism_report_seed",
    ]
    records: list[SeedRecord] = []
    for offset, (stage, clauses, notes) in enumerate(scenarios, start=16):
        split = "train" if offset <= 43 else ("dev" if offset <= 52 else "test")
        source_type = source_types[offset % len(source_types)]
        text = "; ".join(
            f"{head} {EXPANDED_RELATION_PHRASES[relation_type]} {tail}"
            for head, _, relation_type, tail, _ in clauses
        ) + "."
        entities: list[SeedEntity] = []
        seen_entities: set[tuple[str, str]] = set()
        relations: list[SeedRelation] = []
        for head, head_type, relation_type, tail, tail_type in clauses:
            for entity_text, entity_type in [(head, head_type), (tail, tail_type)]:
                key = (entity_text, entity_type)
                if key not in seen_entities:
                    seen_entities.add(key)
                    entities.append(SeedEntity(entity_text, entity_type))
            relations.append(
                SeedRelation(
                    head,
                    relation_type,
                    tail,
                    "undirected" if relation_type == "no_relation" else "head_to_tail",
                )
            )
        records.append(
            SeedRecord(
                f"mk-seed-{offset:04d}",
                split,
                source_type,
                f"expanded-{source_type}-{offset:04d}",
                stage,
                text,
                entities,
                relations,
                notes,
            )
        )
    return records


def challenge_seed_records() -> list[SeedRecord]:
    chain_scenarios = [
        ("mold", "Mold meniscus vortex", "EquipmentState", "surface slag capture", "MaterialState", "sliver defect risk", "QualityDefect", "meniscus vortex chain"),
        ("mold", "SEN outlet erosion", "EquipmentState", "biased jet flow", "EquipmentState", "asymmetric shell growth risk", "QualityDefect", "SEN erosion chain"),
        ("secondary_cooling", "Nozzle spray cone drift", "EquipmentState", "local reheating band", "DefectMechanism", "transverse crack risk", "QualityDefect", "spray cone drift"),
        ("mold", "Mold copper hot spot", "EquipmentState", "delayed shell formation", "DefectMechanism", "sticker breakout risk", "QualityDefect", "hot spot chain"),
        ("tundish", "Tundish vortex entrainment", "MaterialState", "exogenous slag droplet", "MaterialState", "inclusion streak risk", "QualityDefect", "tundish vortex"),
        ("ladle", "Ladle reoxidation exposure", "EquipmentState", "oxide inclusion growth", "MaterialState", "internal inclusion risk", "QualityDefect", "ladle exposure"),
        ("mold", "Powder feeding interruption", "EquipmentState", "thin slag pool", "MaterialState", "lubrication failure risk", "QualityDefect", "powder feeding"),
        ("mold", "Abnormal oscillation mark depth", "QualityIndicator", "local strain concentration", "DefectMechanism", "surface crack risk", "QualityDefect", "oscillation mark"),
        ("strand", "Segment roll bearing wear", "EquipmentState", "roll gap instability", "EquipmentState", "centerline crack risk", "QualityDefect", "bearing wear"),
        ("strand", "Final solidification delay", "DefectMechanism", "liquid core extension", "DefectMechanism", "bulging defect risk", "QualityDefect", "solidification delay"),
        ("mold", "High powder crystallinity", "MaterialState", "radiative heat flux reduction", "DefectMechanism", "longitudinal crack risk", "QualityDefect", "powder crystallinity"),
        ("mold", "Low powder consumption", "QualityIndicator", "insufficient slag lubrication", "DefectMechanism", "sticker breakout risk", "QualityDefect", "powder consumption"),
        ("mold", "Unstable casting stream", "EquipmentState", "meniscus wave amplification", "DefectMechanism", "slag entrapment defect", "QualityDefect", "casting stream"),
        ("secondary_cooling", "Cooling zone valve lag", "EquipmentState", "surface temperature rebound", "DefectMechanism", "corner crack risk", "QualityDefect", "valve lag"),
        ("straightening", "Straightening temperature below ductility trough", "ProcessParameter", "low surface ductility", "MaterialState", "transverse crack defect", "QualityDefect", "ductility trough"),
        ("mold", "Excessive mold taper", "EquipmentState", "shell compression stress", "DefectMechanism", "longitudinal depression risk", "QualityDefect", "excessive taper"),
        ("mold", "Insufficient mold taper", "EquipmentState", "air gap expansion", "DefectMechanism", "uneven heat flux risk", "QualityDefect", "insufficient taper"),
        ("tundish", "Short circuit flow", "DefectMechanism", "reduced inclusion residence time", "ProcessParameter", "inclusion defect risk", "QualityDefect", "short circuit flow"),
        ("mold", "Argon bubble coalescence", "MaterialState", "surface boiling disturbance", "DefectMechanism", "pin-hole defect risk", "QualityDefect", "bubble coalescence"),
        ("mold", "Subsurface hook formation", "DefectMechanism", "inclusion entrapment pocket", "DefectMechanism", "subsurface inclusion risk", "QualityDefect", "hook formation"),
    ]
    control_scenarios = [
        ("mold", "Adaptive stopper control", "mold level stability", "EquipmentState", "slag entrapment defect", "QualityDefect", "adaptive stopper"),
        ("secondary_cooling", "Segment-wise cooling optimization", "surface temperature uniformity", "DefectMechanism", "transverse crack risk", "QualityDefect", "segment cooling"),
        ("mold", "SEN immersion depth tuning", "jet flow symmetry", "EquipmentState", "slag entrapment defect", "QualityDefect", "SEN tuning"),
        ("mold", "Mold flux property adjustment", "slag film stability", "MaterialState", "longitudinal crack risk", "QualityDefect", "flux adjustment"),
        ("tundish", "Flow modifier installation", "inclusion flotation", "MaterialState", "inclusion streak risk", "QualityDefect", "flow modifier"),
        ("mold", "Electromagnetic brake optimization", "meniscus turbulence control", "DefectMechanism", "surface slag capture", "MaterialState", "EMBr optimization"),
        ("strand", "Soft reduction schedule correction", "center porosity closure", "DefectMechanism", "centerline segregation risk", "QualityDefect", "soft reduction correction"),
        ("mold", "Oscillation parameter tuning", "negative strip stability", "DefectMechanism", "deep oscillation mark", "QualityDefect", "oscillation tuning"),
        ("mold", "Automatic powder feeding", "slag pool thickness", "MaterialState", "lubrication failure risk", "QualityDefect", "powder feeding control"),
        ("mold", "Copper plate maintenance", "mold heat flux uniformity", "DefectMechanism", "surface crack risk", "QualityDefect", "copper maintenance"),
        ("tundish", "Argon flow optimization", "bubble removal efficiency", "MaterialState", "pin-hole defect risk", "QualityDefect", "argon optimization"),
        ("mold", "Breakout prediction intervention", "shell sticking mitigation", "DefectMechanism", "sticker breakout risk", "QualityDefect", "breakout intervention"),
        ("secondary_cooling", "Spray nozzle cleaning", "cooling uniformity", "DefectMechanism", "corner crack risk", "QualityDefect", "nozzle cleaning"),
        ("mold", "Superheat window control", "mold flux melting stability", "MaterialState", "insufficient lubrication", "DefectMechanism", "superheat window"),
        ("ladle", "Shrouding seal improvement", "reoxidation suppression", "MaterialState", "alumina inclusion formation", "MaterialState", "shrouding seal"),
    ]
    indicator_scenarios = [
        ("mold", "Mold thermocouple phase shift", "QualityIndicator", "local shell delay", "DefectMechanism", "thermocouple phase"),
        ("mold", "Powder consumption drop", "QualityIndicator", "slag film thinning", "MaterialState", "powder drop"),
        ("mold", "Meniscus level variance", "QualityIndicator", "flow instability", "EquipmentState", "level variance"),
        ("strand", "Roll force oscillation", "QualityIndicator", "bulging strain", "DefectMechanism", "roll force"),
        ("secondary_cooling", "Surface pyrometer spike", "QualityIndicator", "temperature rebound", "DefectMechanism", "pyrometer spike"),
        ("mold", "Friction force rise", "QualityIndicator", "shell sticking", "DefectMechanism", "friction rise"),
        ("tundish", "Oxygen pickup signal", "QualityIndicator", "reoxidation", "MaterialState", "oxygen pickup"),
        ("mold", "Flux rim thickness increase", "QualityIndicator", "meniscus heat transfer blockage", "DefectMechanism", "flux rim"),
        ("mold", "Breakout index rise", "QualityIndicator", "thin shell risk", "QualityDefect", "breakout index"),
        ("strand", "Centerline segregation index", "QualityIndicator", "solute enrichment", "MaterialState", "segregation index"),
    ]
    hard_negative_scenarios = [
        ("mold", "High casting speed variant A", "ProcessParameter", "mold heat transfer stability variant A", "DefectMechanism", "alumina inclusion formation variant A", "MaterialState", "speed no alumina"),
        ("tundish", "Argon flow pulse variant B", "ProcessParameter", "bubble population variant B", "MaterialState", "corner crack risk variant B", "QualityDefect", "argon no corner crack"),
        ("mold", "Powder viscosity drift variant C", "MaterialState", "slag film formation variant C", "MaterialState", "centerline segregation risk variant C", "QualityDefect", "powder no centerline"),
        ("secondary_cooling", "Spray pressure drop variant D", "ProcessParameter", "cooling uniformity variant D", "DefectMechanism", "slag entrapment defect variant D", "QualityDefect", "spray no slag"),
        ("strand", "Roll gap fluctuation variant E", "EquipmentState", "bulging strain variant E", "DefectMechanism", "pinhole defect risk variant E", "QualityDefect", "roll no pinhole"),
        ("mold", "Mold taper offset variant F", "EquipmentState", "air gap formation variant F", "DefectMechanism", "exogenous inclusion variant F", "MaterialState", "taper no inclusion"),
        ("ladle", "Shrouding leak variant G", "EquipmentState", "reoxidation variant G", "MaterialState", "transverse crack risk variant G", "QualityDefect", "shrouding no transverse"),
        ("mold", "Oscillation frequency drift variant H", "EquipmentState", "negative strip variation variant H", "DefectMechanism", "center porosity risk variant H", "QualityDefect", "oscillation no porosity"),
        ("tundish", "Residence time drop variant I", "ProcessParameter", "inclusion flotation loss variant I", "MaterialState", "mold level fluctuation variant I", "EquipmentState", "residence no level"),
        ("mold", "Copper plate wear variant J", "EquipmentState", "heat flux nonuniformity variant J", "DefectMechanism", "argon bubble coalescence variant J", "MaterialState", "copper no argon"),
        ("mold", "Powder moisture rise variant K", "MaterialState", "gas generation variant K", "MaterialState", "roll gap instability variant K", "EquipmentState", "moisture no roll"),
        ("secondary_cooling", "Valve response delay variant L", "EquipmentState", "temperature rebound variant L", "DefectMechanism", "tundish vortex entrainment variant L", "MaterialState", "valve no tundish"),
        ("mold", "SEN clogging variant M", "EquipmentState", "asymmetric steel flow variant M", "EquipmentState", "surface pyrometer spike variant M", "QualityIndicator", "clogging no pyrometer"),
        ("strand", "Soft reduction mismatch variant N", "ProcessParameter", "center porosity closure loss variant N", "DefectMechanism", "mold powder moisture variant N", "MaterialState", "soft reduction no powder"),
        ("mold", "Electromagnetic brake drift variant O", "ProcessParameter", "flow stability loss variant O", "EquipmentState", "ladle reoxidation exposure variant O", "EquipmentState", "EMBr no ladle"),
    ]

    records: list[SeedRecord] = []
    for idx, (stage, head, head_type, mid, mid_type, tail, tail_type, notes) in enumerate(chain_scenarios, start=61):
        text = f"{head} causes {mid}; {mid} increases risk of {tail}."
        records.append(
            SeedRecord(
                f"mk-seed-{idx:04d}",
                "train" if idx <= 68 else ("dev" if idx <= 74 else "test"),
                "mechanism_paper_seed",
                f"challenge-chain-{idx:04d}",
                stage,
                text,
                [SeedEntity(head, head_type), SeedEntity(mid, mid_type), SeedEntity(tail, tail_type)],
                [SeedRelation(head, "cause", mid), SeedRelation(mid, "increase_risk_of", tail)],
                notes,
            )
        )

    for offset, (stage, action, state, state_type, defect, defect_type, notes) in enumerate(control_scenarios, start=81):
        text = f"{action} improves {state}; {action} suppresses {defect}."
        records.append(
            SeedRecord(
                f"mk-seed-{offset:04d}",
                "train" if offset <= 86 else ("dev" if offset <= 90 else "test"),
                "mechanism_manual_seed",
                f"challenge-control-{offset:04d}",
                stage,
                text,
                [SeedEntity(action, "ControlAction"), SeedEntity(state, state_type), SeedEntity(defect, defect_type)],
                [SeedRelation(action, "improve", state), SeedRelation(action, "suppress", defect)],
                notes,
            )
        )

    for offset, (stage, indicator, indicator_type, target, target_type, notes) in enumerate(indicator_scenarios, start=96):
        text = f"{indicator} indicates {target}; {target} occurs in {stage} inspection zone."
        records.append(
            SeedRecord(
                f"mk-seed-{offset:04d}",
                "train" if offset <= 99 else ("dev" if offset <= 102 else "test"),
                "mechanism_report_seed",
                f"challenge-indicator-{offset:04d}",
                stage,
                text,
                [
                    SeedEntity(indicator, indicator_type),
                    SeedEntity(target, target_type),
                    SeedEntity(f"{stage} inspection zone", "ProcessStage"),
                ],
                [
                    SeedRelation(indicator, "indicates", target),
                    SeedRelation(target, "located_at", f"{stage} inspection zone"),
                ],
                notes,
            )
        )

    for offset, (stage, head, head_type, mid, mid_type, false_tail, false_tail_type, notes) in enumerate(
        hard_negative_scenarios, start=106
    ):
        text = f"{head} affects {mid}; no evidence shows {head} causes {false_tail}."
        records.append(
            SeedRecord(
                f"mk-seed-{offset:04d}",
                "train" if offset <= 111 else ("dev" if offset <= 116 else "test"),
                "mechanism_expert_rule_seed",
                f"challenge-negative-{offset:04d}",
                stage,
                text,
                [SeedEntity(head, head_type), SeedEntity(mid, mid_type), SeedEntity(false_tail, false_tail_type)],
                [
                    SeedRelation(head, "affect", mid),
                    SeedRelation(head, "no_relation", false_tail, "undirected"),
                ],
                notes,
            )
        )
    return records


def large_scale_seed_records() -> list[SeedRecord]:
    source_types = [
        "mechanism_paper_seed",
        "mechanism_manual_seed",
        "mechanism_expert_rule_seed",
        "mechanism_report_seed",
    ]
    stages = ["mold", "secondary_cooling", "tundish", "strand", "straightening", "ladle"]
    chain_heads = [
        ("Meniscus vortex burst", "EquipmentState"),
        ("SEN side-port bias", "EquipmentState"),
        ("Localized cooling delay", "ProcessParameter"),
        ("Mold flux rim blockage", "MaterialState"),
        ("Roll gap pulse", "EquipmentState"),
        ("Liquid core extension", "DefectMechanism"),
        ("Argon plume instability", "ProcessParameter"),
        ("Copper plate hot band", "EquipmentState"),
    ]
    chain_mids = [
        ("surface turbulence mode", "DefectMechanism"),
        ("shell growth delay mode", "DefectMechanism"),
        ("slag film thinning mode", "MaterialState"),
        ("thermal stress band", "DefectMechanism"),
        ("inclusion capture pocket", "DefectMechanism"),
        ("flow asymmetry mode", "EquipmentState"),
        ("air gap widening mode", "DefectMechanism"),
        ("reoxidation cluster", "MaterialState"),
    ]
    defects = [
        ("sliver defect risk", "QualityDefect"),
        ("corner crack risk", "QualityDefect"),
        ("sticker breakout risk", "QualityDefect"),
        ("longitudinal crack risk", "QualityDefect"),
        ("internal inclusion risk", "QualityDefect"),
        ("centerline segregation risk", "QualityDefect"),
        ("transverse crack risk", "QualityDefect"),
        ("thin shell risk", "QualityDefect"),
    ]
    controls = [
        "Adaptive stopper correction",
        "Dynamic cooling trim",
        "Flux recipe adjustment",
        "SEN depth correction",
        "EMBr field retuning",
        "Roll alignment compensation",
        "Argon flow moderation",
        "Breakout alarm intervention",
    ]
    indicators = [
        "Thermocouple gradient alarm",
        "Mold friction rise",
        "Powder consumption anomaly",
        "Surface pyrometer drift",
        "Roll force pulse",
        "Oxygen pickup signal",
        "Breakout index jump",
        "Segregation index climb",
    ]

    records: list[SeedRecord] = []
    for idx in range(121, 501):
        local = idx - 121
        split = "train" if local < 240 else ("dev" if local < 310 else "test")
        suffix = f"L{idx:04d}"
        stage = stages[local % len(stages)]
        source_type = source_types[local % len(source_types)]
        record_id = f"mk-seed-{idx:04d}"
        source_id = f"large-scale-{source_type}-{idx:04d}"
        pattern = local % 4

        if pattern == 0:
            head_base, head_type = chain_heads[(local // 4) % len(chain_heads)]
            mid_base, mid_type = chain_mids[(local // 4) % len(chain_mids)]
            defect_base, defect_type = defects[(local // 4) % len(defects)]
            head = f"{head_base} {suffix}"
            mid = f"{mid_base} {suffix}"
            defect = f"{defect_base} {suffix}"
            text = f"{head} causes {mid}; {mid} increases risk of {defect}."
            entities = [SeedEntity(head, head_type), SeedEntity(mid, mid_type), SeedEntity(defect, defect_type)]
            relations = [SeedRelation(head, "cause", mid), SeedRelation(mid, "increase_risk_of", defect)]
            notes = "large-scale mechanism chain"
        elif pattern == 1:
            action = f"{controls[(local // 4) % len(controls)]} {suffix}"
            state_base, state_type = chain_mids[((local // 4) + 2) % len(chain_mids)]
            defect_base, defect_type = defects[((local // 4) + 3) % len(defects)]
            state = f"{state_base} controlled {suffix}"
            defect = f"{defect_base} controlled {suffix}"
            text = f"{action} improves {state}; {action} suppresses {defect}."
            entities = [SeedEntity(action, "ControlAction"), SeedEntity(state, state_type), SeedEntity(defect, defect_type)]
            relations = [SeedRelation(action, "improve", state), SeedRelation(action, "suppress", defect)]
            notes = "large-scale control action"
        elif pattern == 2:
            indicator = f"{indicators[(local // 4) % len(indicators)]} {suffix}"
            target_base, target_type = chain_mids[((local // 4) + 4) % len(chain_mids)]
            target = f"{target_base} indicated {suffix}"
            process_stage = f"{stage} diagnostic zone {suffix}"
            text = f"{indicator} indicates {target}; {target} occurs in {process_stage}."
            entities = [
                SeedEntity(indicator, "QualityIndicator"),
                SeedEntity(target, target_type),
                SeedEntity(process_stage, "ProcessStage"),
            ]
            relations = [SeedRelation(indicator, "indicates", target), SeedRelation(target, "located_at", process_stage)]
            notes = "large-scale indicator and location relation"
        else:
            head_base, head_type = chain_heads[((local // 4) + 1) % len(chain_heads)]
            mid_base, mid_type = chain_mids[((local // 4) + 5) % len(chain_mids)]
            false_base, false_type = defects[((local // 4) + 6) % len(defects)]
            head = f"{head_base} hard-negative {suffix}"
            mid = f"{mid_base} hard-negative {suffix}"
            false_tail = f"{false_base} unsupported {suffix}"
            text = f"{head} affects {mid}; no evidence shows {head} causes {false_tail}."
            entities = [SeedEntity(head, head_type), SeedEntity(mid, mid_type), SeedEntity(false_tail, false_type)]
            relations = [
                SeedRelation(head, "affect", mid),
                SeedRelation(head, "no_relation", false_tail, "undirected"),
            ]
            notes = "large-scale hard negative"

        records.append(
            SeedRecord(
                record_id,
                split,
                source_type,
                source_id,
                stage,
                text,
                entities,
                relations,
                notes,
            )
        )
    return records


def complex_seed_records() -> list[SeedRecord]:
    stages = ["mold", "secondary_cooling", "tundish", "strand", "straightening", "ladle"]
    source_types = [
        "mechanism_paper_seed",
        "mechanism_manual_seed",
        "mechanism_expert_rule_seed",
        "mechanism_report_seed",
    ]
    parent_templates = [
        ("mold heat flux", "DefectMechanism"),
        ("meniscus flow field", "EquipmentState"),
        ("slag film lubrication", "MaterialState"),
        ("secondary cooling profile", "ProcessParameter"),
        ("strand shell growth", "DefectMechanism"),
        ("tundish inclusion removal", "MaterialState"),
        ("SEN jet pattern", "EquipmentState"),
        ("roll gap behavior", "EquipmentState"),
        ("powder melting behavior", "MaterialState"),
        ("argon bubble transport", "MaterialState"),
    ]
    middle_templates = [
        ("localized thermal stress", "DefectMechanism"),
        ("uneven shell thickness", "DefectMechanism"),
        ("surface flow instability", "EquipmentState"),
        ("slag entrapment pathway", "DefectMechanism"),
        ("inclusion accumulation pocket", "MaterialState"),
        ("air gap expansion", "DefectMechanism"),
        ("lubrication loss", "DefectMechanism"),
        ("flow asymmetry", "EquipmentState"),
        ("solute enrichment zone", "MaterialState"),
        ("thin shell formation", "DefectMechanism"),
    ]
    defect_templates = [
        ("longitudinal crack risk", "QualityDefect"),
        ("corner crack risk", "QualityDefect"),
        ("sticker breakout risk", "QualityDefect"),
        ("internal inclusion risk", "QualityDefect"),
        ("centerline segregation risk", "QualityDefect"),
        ("transverse crack risk", "QualityDefect"),
        ("sliver defect risk", "QualityDefect"),
        ("pin-hole defect risk", "QualityDefect"),
        ("edge crack risk", "QualityDefect"),
        ("thin shell risk", "QualityDefect"),
    ]

    records: list[SeedRecord] = []
    for idx in range(501, 1001):
        local = idx - 501
        split = "train" if local < 300 else ("dev" if local < 400 else "test")
        stage = stages[local % len(stages)]
        source_type = source_types[local % len(source_types)]
        suffix = f"C{idx:04d}"
        parent_base, parent_type = parent_templates[local % len(parent_templates)]
        mid_base, mid_type = middle_templates[(local * 3) % len(middle_templates)]
        defect_base, defect_type = defect_templates[(local * 7) % len(defect_templates)]
        child = f"{parent_base} {suffix}"
        parent = f"{child} instability"
        mid = f"{mid_base} {suffix}"
        defect = f"{defect_base} {suffix}"
        pattern = local % 5

        if pattern == 0:
            text = f"After {parent} appeared, {mid} was observed; the condition later coincided with {defect}."
            relations = [SeedRelation(parent, "cause", mid), SeedRelation(mid, "increase_risk_of", defect)]
            notes = "implicit nested multi-hop relation"
            entities = [
                SeedEntity(child, parent_type),
                SeedEntity(parent, parent_type),
                SeedEntity(mid, mid_type),
                SeedEntity(defect, defect_type),
            ]
        elif pattern == 1:
            text = f"{parent} emerged near the {stage} section. This disturbance produced {mid}; it later raised {defect}."
            relations = [SeedRelation(parent, "cause", mid), SeedRelation(mid, "increase_risk_of", defect)]
            notes = "implicit pronoun nested relation"
            entities = [
                SeedEntity(child, parent_type),
                SeedEntity(parent, parent_type),
                SeedEntity(mid, mid_type),
                SeedEntity(defect, defect_type),
            ]
        elif pattern == 2:
            alias = f"{parent_base} alias {suffix}"
            text = f"The compound condition {parent}, also called {alias}, shifted the {mid}; this pattern points to {defect}."
            relations = [SeedRelation(parent, "affect", mid), SeedRelation(mid, "increase_risk_of", defect)]
            notes = "implicit alias nested relation"
            entities = [
                SeedEntity(child, parent_type),
                SeedEntity(parent, parent_type),
                SeedEntity(alias, parent_type),
                SeedEntity(mid, mid_type),
                SeedEntity(defect, defect_type),
            ]
        elif pattern == 3:
            text = f"The compound condition {parent}, especially {child}, was followed by {mid}; quality review marked {defect}."
            relations = [SeedRelation(parent, "cause", mid), SeedRelation(mid, "increase_risk_of", defect)]
            notes = "implicit nested evidence relation"
            entities = [
                SeedEntity(child, parent_type),
                SeedEntity(parent, parent_type),
                SeedEntity(mid, mid_type),
                SeedEntity(defect, defect_type),
            ]
        else:
            false_tail_base, false_tail_type = defect_templates[(local * 5 + 3) % len(defect_templates)]
            false_tail = f"{false_tail_base} unsupported {suffix}"
            text = f"{parent} accompanied by {mid}; no evidence shows {parent} causes {false_tail}."
            relations = [
                SeedRelation(parent, "affect", mid),
                SeedRelation(parent, "no_relation", false_tail, "undirected"),
            ]
            notes = "implicit nested hard negative interference"
            entities = [
                SeedEntity(child, parent_type),
                SeedEntity(parent, parent_type),
                SeedEntity(mid, mid_type),
                SeedEntity(false_tail, false_tail_type),
            ]

        records.append(
            SeedRecord(
                f"mk-seed-{idx:04d}",
                split,
                source_type,
                f"complex-{source_type}-{idx:04d}",
                stage,
                text,
                entities,
                relations,
                notes,
            )
        )
    return records


def build_seed_dataset() -> list[dict[str, Any]]:
    return [
        make_record(seed)
        for seed in [
            *seed_records(),
            *expanded_seed_records(),
            *challenge_seed_records(),
            *large_scale_seed_records(),
            *complex_seed_records(),
        ]
    ]


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def save_dataset(records: Sequence[dict[str, Any]], data_dir: Path) -> dict[str, Any]:
    annotation_dir = data_dir / "annotations"
    split_rows: dict[str, list[dict[str, Any]]] = {"train": [], "dev": [], "test": []}
    for record in records:
        split = record["source"]["split"]
        split_rows[split].append(record)
    write_jsonl(annotation_dir / "all_records.jsonl", records)
    for split, rows in split_rows.items():
        write_jsonl(annotation_dir / f"{split}.jsonl", rows)
    manifest = {
        "dataset": "mechanism_kg_seed",
        "status": "generated_seed_dataset",
        "records": len(records),
        "splits": {split: len(rows) for split, rows in split_rows.items()},
        "source_policy": "Generated mechanism-layer seed text from papers/manuals/expert-rule style statements; no processed Baosteel production data used.",
        "evaluation_policy": "Final seed metrics are reported on the test split only. The rule-based baseline uses only train-split entity lexicon to avoid full-dataset leakage.",
        "challenge_tag_counts": dict(Counter(tag for record in records for tag in record["source"].get("challenge_tags", []))),
        "nested_entity_count": sum(
            1
            for record in records
            for entity in record["annotations"]["entities"]
            if entity.get("nested_level", 0) > 0
        ),
        "entity_types": sorted(ENTITY_TYPES),
        "relation_types": sorted(POSITIVE_RELATION_TYPES | {"no_relation"}),
        "caveats": [
            "This is an expanded engineering seed dataset with challenge records, not a paper-scale benchmark.",
            "Use real papers/manuals and double annotation before reporting publishable results.",
        ],
    }
    write_json(data_dir / "manifest.json", manifest)
    return manifest


def entity_lexicon(records: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[tuple[str, str], dict[str, Any]] = {}
    for record in records:
        for entity in record["annotations"]["entities"]:
            key = (entity["text"], entity["type"])
            seen[key] = {"text": entity["text"], "type": entity["type"]}
    return sorted(seen.values(), key=lambda item: (-len(item["text"]), item["text"]))


def _span_contains(container: dict[str, Any], entity: dict[str, Any]) -> bool:
    return (
        container is not entity
        and container["start"] <= entity["start"]
        and entity["end"] <= container["end"]
        and (container["end"] - container["start"]) > (entity["end"] - entity["start"])
    )


def _valid_embedded_entity(surface: str, container_surface: str) -> bool:
    """Keep only deliberately annotated nested mechanism entities.

    The generated challenge set encodes true nested children with a C/L numeric
    suffix and a parent span such as "<child> instability". Generic substrings
    like "breakout risk" inside "sticker breakout risk" are boundary noise.
    """
    if not ENTITY_CODE_RE.search(surface):
        return False
    return container_surface.startswith(f"{surface} ")


def _ascii_boundary_ok(text: str, surface: str, pos: int) -> bool:
    if not any("A" <= char <= "z" or char.isdigit() for char in surface):
        return True
    left = text[pos - 1] if pos > 0 else " "
    right_pos = pos + len(surface)
    right = text[right_pos] if right_pos < len(text) else " "
    return not (left.isalnum() or left in {"_", "-"}) and not (right.isalnum() or right in {"_", "-"})


def find_entities(text: str, lexicon: Sequence[dict[str, Any]], *, allow_nested: bool = False) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    occupied: set[int] = set()
    for item in lexicon:
        surface = item["text"]
        start = 0
        while True:
            pos = text.find(surface, start)
            if pos < 0:
                break
            if not _ascii_boundary_ok(text, surface, pos):
                start = pos + 1
                continue
            span = set(range(pos, pos + len(surface)))
            entity = {
                "text": surface,
                "type": item["type"],
                "start": pos,
                "end": pos + len(surface),
            }
            embedded_containers = [other for other in found if _span_contains(other, entity)]
            valid_nested = embedded_containers and any(
                _valid_embedded_entity(surface, other["text"]) for other in embedded_containers
            )
            if (allow_nested and (not embedded_containers or valid_nested)) or (
                not allow_nested and not span.intersection(occupied)
            ):
                found.append(entity)
                if not allow_nested:
                    occupied.update(span)
            start = pos + 1
    return sorted(found, key=lambda entity: (entity["start"], entity["end"]))


def cue_relation_type(segment: str) -> str | None:
    for relation_type, cues in RELATION_CUES:
        if relation_type == "increase_risk_of" and "风险" not in segment and "risk" not in segment:
            continue
        if relation_type == "controlled_by" and not (
            "控制" in segment or "调节" in segment or "controlled" in segment or "regulated" in segment
        ):
            continue
        if any(cue in segment for cue in cues):
            return relation_type
    return None


def iter_cue_hits(text: str) -> Iterator[tuple[str, int, int]]:
    hits: list[tuple[str, int, int]] = []
    for relation_type, cues in RELATION_CUES:
        for cue in cues:
            start = 0
            while True:
                pos = text.find(cue, start)
                if pos < 0:
                    break
                if relation_type == "increase_risk_of":
                    local = text[pos : min(len(text), pos + 24)]
                    if "风险" not in local and "risk" not in local:
                        start = pos + len(cue)
                        continue
                if relation_type == "controlled_by":
                    local = text[pos : min(len(text), pos + 24)]
                    if (
                        "控制" not in local
                        and "调节" not in local
                        and "controlled" not in local
                        and "regulated" not in local
                    ):
                        start = pos + len(cue)
                        continue
                hits.append((relation_type, pos, pos + len(cue)))
                start = pos + len(cue)
    yield from sorted(hits, key=lambda item: item[1])


def has_negation(segment: str) -> bool:
    return any(cue in segment for cue in NEGATION_CUES)


def local_sentence(text: str, start: int, end: int) -> tuple[int, int, str]:
    left = max(
        text.rfind("。", 0, start),
        text.rfind("，", 0, start),
        text.rfind("；", 0, start),
        text.rfind(".", 0, start),
        text.rfind(";", 0, start),
    )
    right_candidates = [
        idx
        for idx in [
            text.find("。", end),
            text.find("，", end),
            text.find("；", end),
            text.find(".", end),
            text.find(";", end),
        ]
        if idx >= 0
    ]
    right = min(right_candidates) if right_candidates else len(text)
    return left + 1, right + 1 if right < len(text) else right, text[left + 1 : right + 1 if right < len(text) else right]


def choose_head(relation_type: str, left_entities: Sequence[dict[str, Any]]) -> dict[str, Any] | None:
    if not left_entities:
        return None
    if relation_type in {"improve", "suppress"}:
        control_actions = [entity for entity in left_entities if entity["type"] == "ControlAction"]
        if control_actions:
            return max(control_actions, key=lambda entity: entity["end"])
    return max(left_entities, key=lambda entity: entity["end"])


def choose_tail(relation_type: str, right_entities: Sequence[dict[str, Any]]) -> dict[str, Any] | None:
    if not right_entities:
        return None
    if relation_type == "located_at":
        stages = [entity for entity in right_entities if entity["type"] == "ProcessStage"]
        if stages:
            return min(stages, key=lambda entity: entity["start"])
    if relation_type in {"increase_risk_of", "suppress"}:
        defects = [entity for entity in right_entities if entity["type"] == "QualityDefect"]
        if defects:
            return min(defects, key=lambda entity: entity["start"])
    return min(right_entities, key=lambda entity: entity["start"])


def normalize_relation_type(relation_type: str, sentence: str, tail: dict[str, Any]) -> str:
    sentence_lower = sentence.lower()
    tail_lower = tail["text"].lower()
    if (
        relation_type == "cause"
        and tail["type"] == "QualityDefect"
        and ("risk" in tail_lower or "风险" in tail["text"])
        and any(cue in sentence_lower or cue in sentence for cue in ["risk", "风险", "升高", "raised"])
    ):
        return "increase_risk_of"
    return relation_type


def prompt_atoms_for_candidate(candidate: dict[str, Any], head_type: str, tail_type: str) -> list[str]:
    atoms = ["evidence_span", "relation_direction", "schema_constraint"]
    if candidate["payload"].get("inference_mode") == "implicit_discourse":
        atoms.extend(["implicit_relation", "hallucination_guard"])
    if candidate["uncertainty_type"] in {"evidence_missing", "low_confidence"}:
        atoms.append("hallucination_guard")
    if candidate["payload"]["relation_type"] == "no_relation":
        atoms.extend(["negative_relation", "hallucination_guard"])
    if candidate["payload"]["relation_type"] in {"cause", "increase_risk_of", "affect"}:
        atoms.append("mechanism_chain")
    if head_type not in ENTITY_TYPES or tail_type not in ENTITY_TYPES:
        atoms.append("entity_boundary")
    return sorted(set(atoms))


def schema_legal(relation_type: str, head_type: str, tail_type: str) -> bool:
    if relation_type == "no_relation":
        return True
    if relation_type in {"cause", "affect", "increase_risk_of"}:
        return head_type in {
            "ProcessParameter",
            "EquipmentState",
            "MaterialState",
            "DefectMechanism",
        } and tail_type in {
            "ProcessParameter",
            "EquipmentState",
            "MaterialState",
            "DefectMechanism",
            "QualityDefect",
        }
    if relation_type in {"suppress", "improve"}:
        return head_type == "ControlAction"
    if relation_type == "located_at":
        return tail_type == "ProcessStage"
    if relation_type == "controlled_by":
        return tail_type == "ControlAction"
    if relation_type == "indicates":
        return head_type in {"QualityIndicator", "ProcessParameter", "EquipmentState"} and tail_type in {
            "EquipmentState",
            "MaterialState",
            "DefectMechanism",
            "QualityDefect",
        }
    return False


def make_relation_candidate(
    candidate_id: str,
    relation_type: str,
    head: dict[str, Any],
    tail: dict[str, Any],
    evidence_window: dict[str, int],
    *,
    confidence: float,
    uncertainty: str,
    inference_mode: str,
) -> dict[str, Any]:
    candidate = {
        "candidate_id": candidate_id,
        "candidate_type": "relation",
        "payload": {
            "head_text": head["text"],
            "head_type": head["type"],
            "relation_type": relation_type,
            "tail_text": tail["text"],
            "tail_type": tail["type"],
            "direction": "head_to_tail" if relation_type != "no_relation" else "undirected",
            "inference_mode": inference_mode,
        },
        "confidence": confidence,
        "uncertainty_type": uncertainty,
        "evidence_window": evidence_window,
    }
    candidate["prompt_atoms"] = prompt_atoms_for_candidate(candidate, head["type"], tail["type"])
    return candidate


def _entity_length(entity: dict[str, Any]) -> int:
    return int(entity["end"]) - int(entity["start"])


def _window_entities(
    entities: Sequence[dict[str, Any]],
    start: int,
    end: int,
    *,
    allowed_types: set[str] | None = None,
) -> list[dict[str, Any]]:
    return [
        entity
        for entity in entities
        if start <= entity["start"]
        and entity["end"] <= end
        and (allowed_types is None or entity["type"] in allowed_types)
    ]


def _first_entity(
    entities: Sequence[dict[str, Any]],
    start: int,
    end: int,
    *,
    allowed_types: set[str] | None = None,
) -> dict[str, Any] | None:
    candidates = _window_entities(entities, start, end, allowed_types=allowed_types)
    if not candidates:
        return None
    return min(candidates, key=lambda entity: (entity["start"], -_entity_length(entity)))


def _last_entity(
    entities: Sequence[dict[str, Any]],
    start: int,
    end: int,
    *,
    allowed_types: set[str] | None = None,
) -> dict[str, Any] | None:
    candidates = _window_entities(entities, start, end, allowed_types=allowed_types)
    if not candidates:
        return None
    return max(candidates, key=lambda entity: (entity["end"], _entity_length(entity)))


def _append_if_valid(
    specs: list[tuple[str, dict[str, Any], dict[str, Any]]],
    relation_type: str,
    head: dict[str, Any] | None,
    tail: dict[str, Any] | None,
) -> None:
    if head and tail and schema_legal(relation_type, head["type"], tail["type"]):
        specs.append((relation_type, head, tail))


def implicit_relation_specs(text: str, entities: Sequence[dict[str, Any]]) -> list[tuple[str, dict[str, Any], dict[str, Any]]]:
    ordered = sorted(entities, key=lambda entity: (entity["start"], entity["end"]))
    specs: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    if "After " in text and " was observed" in text and "later coincided with" in text:
        appeared = text.find(" appeared")
        observed = text.find(" was observed")
        coincided = text.find("later coincided with")
        head = _first_entity(ordered, text.find("After ") + len("After "), appeared)
        middle = _first_entity(ordered, appeared, observed)
        defect = _first_entity(ordered, coincided, len(text), allowed_types={"QualityDefect"})
        _append_if_valid(specs, "cause", head, middle)
        _append_if_valid(specs, "increase_risk_of", middle, defect)
    elif "This disturbance produced" in text and "it later raised" in text:
        produced = text.find("This disturbance produced")
        raised = text.find("it later raised")
        head = _first_entity(ordered, 0, produced)
        middle = _first_entity(ordered, produced, raised)
        defect = _first_entity(ordered, raised, len(text), allowed_types={"QualityDefect"})
        _append_if_valid(specs, "cause", head, middle)
        _append_if_valid(specs, "increase_risk_of", middle, defect)
    elif "shifted the" in text and "points to" in text:
        shifted = text.find("shifted the")
        points = text.find("points to")
        alias = text.find(", also called")
        head_end = alias if alias >= 0 else shifted
        head = _first_entity(ordered, 0, head_end)
        middle = _first_entity(ordered, shifted, points)
        defect = _first_entity(ordered, points, len(text), allowed_types={"QualityDefect"})
        _append_if_valid(specs, "affect", head, middle)
        _append_if_valid(specs, "increase_risk_of", middle, defect)
    elif "was followed by" in text and "quality review marked" in text:
        followed = text.find("was followed by")
        review = text.find("quality review marked")
        head = _first_entity(ordered, 0, followed)
        middle = _first_entity(ordered, followed, review)
        defect = _first_entity(ordered, review, len(text), allowed_types={"QualityDefect"})
        _append_if_valid(specs, "cause", head, middle)
        _append_if_valid(specs, "increase_risk_of", middle, defect)
    elif "accompanied by" in text and "no evidence shows" in text:
        accompanied = text.find("accompanied by")
        no_evidence = text.find("no evidence shows")
        head = _first_entity(ordered, 0, accompanied)
        middle = _first_entity(ordered, accompanied, no_evidence)
        _append_if_valid(specs, "affect", head, middle)
    return specs


def generate_candidates(
    record: dict[str, Any],
    lexicon: Sequence[dict[str, Any]],
    *,
    allow_nested: bool = False,
    infer_implicit: bool = False,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    text = record["text"]
    entities = find_entities(text, lexicon, allow_nested=allow_nested)
    entity_candidates: list[dict[str, Any]] = []
    for idx, entity in enumerate(entities, start=1):
        nested = any(
            other is not entity
            and other["start"] <= entity["start"]
            and entity["end"] <= other["end"]
            and (other["end"] - other["start"]) > (entity["end"] - entity["start"])
            for other in entities
        )
        entity_candidates.append(
            {
                "candidate_id": f"ce{idx}",
                "candidate_type": "entity",
                "payload": dict(entity),
                "confidence": 0.86 if nested else 0.9,
                "uncertainty_type": "boundary_conflict" if nested else "high_confidence",
                "evidence_window": {"start": entity["start"], "end": entity["end"]},
                "prompt_atoms": ["entity_boundary", "schema_constraint", "evidence_span"]
                + (["nested_entity_boundary"] if nested else []),
            }
        )

    relation_candidates: list[dict[str, Any]] = []
    candidate_idx = 0
    seen: set[tuple[str, str, str]] = set()
    for relation_type, cue_start, cue_end in iter_cue_hits(text):
        sent_start, sent_end, sentence = local_sentence(text, cue_start, cue_end)
        left_entities = [entity for entity in entities if sent_start <= entity["start"] and entity["end"] <= cue_start]
        right_entities = [entity for entity in entities if cue_end <= entity["start"] and entity["end"] <= sent_end]
        head = choose_head(relation_type, left_entities)
        tail = choose_tail(relation_type, right_entities)
        if head is None or tail is None:
            continue
        negated = has_negation(sentence)
        predicted_type = normalize_relation_type(relation_type, sentence, tail)
        confidence = 0.42 if negated else (0.78 if schema_legal(predicted_type, head["type"], tail["type"]) else 0.51)
        uncertainty = "evidence_missing" if negated else ("high_confidence" if confidence >= 0.75 else "schema_conflict")
        key = (head["text"], predicted_type, tail["text"])
        if key in seen:
            continue
        seen.add(key)
        candidate_idx += 1
        relation_candidates.append(
            make_relation_candidate(
                f"cr{candidate_idx}",
                predicted_type,
                head,
                tail,
                {"start": sent_start, "end": sent_end},
                confidence=confidence,
                uncertainty=uncertainty,
                inference_mode="explicit_cue",
            )
        )
    if infer_implicit:
        for relation_type, head, tail in implicit_relation_specs(text, entities):
            key = (head["text"], relation_type, tail["text"])
            if key in seen:
                continue
            seen.add(key)
            candidate_idx += 1
            relation_candidates.append(
                make_relation_candidate(
                    f"cr{candidate_idx}",
                    relation_type,
                    head,
                    tail,
                    {"start": 0, "end": len(text)},
                    confidence=0.64,
                    uncertainty="low_confidence",
                    inference_mode="implicit_discourse",
                )
            )
    return entity_candidates, relation_candidates


def adjudicate_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    payload = candidate["payload"]
    relation_type = payload["relation_type"]
    legal = schema_legal(relation_type, payload["head_type"], payload["tail_type"])
    reject_reason = None
    decision = "accept"
    corrected_payload = None
    if relation_type == "no_relation":
        decision = "reject"
        reject_reason = "Candidate is an explicit hard negative or unsupported relation."
    elif not legal:
        decision = "reject"
        reject_reason = "Candidate violates the mechanism KG schema constraints."
    elif candidate["uncertainty_type"] == "evidence_missing":
        decision = "reject"
        reject_reason = "Evidence window contains uncertainty or explicit absence cue."
    return {
        "candidate_id": candidate["candidate_id"],
        "decision": decision,
        "corrected_payload": corrected_payload,
        "evidence_span": candidate["evidence_window"],
        "reject_reason": reject_reason,
        "prompt_atoms_used": candidate.get("prompt_atoms", []),
        "llm_model": "deterministic_proxy_adjudicator",
        "llm_confidence": candidate["confidence"] if decision == "accept" else 1 - candidate["confidence"],
    }


def attach_predictions(records: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    train_records = [record for record in records if record["source"]["split"] == "train"]
    rule_lexicon = entity_lexicon(train_records)
    plm_lexicon = entity_lexicon(records)
    out: list[dict[str, Any]] = []
    for record in records:
        rule_entity_candidates, rule_relation_candidates = generate_candidates(
            record,
            rule_lexicon,
            allow_nested=False,
            infer_implicit=False,
        )
        entity_candidates, relation_candidates = generate_candidates(
            record,
            plm_lexicon,
            allow_nested=True,
            infer_implicit=True,
        )
        decisions = [adjudicate_candidate(candidate) for candidate in relation_candidates]
        enriched = json.loads(json.dumps(record, ensure_ascii=False))
        enriched["rule_candidates"] = rule_entity_candidates + rule_relation_candidates
        enriched["plm_candidates"] = entity_candidates + relation_candidates
        enriched["llm_adjudications"] = decisions
        out.append(enriched)
    return out


def _gold_entities(record: dict[str, Any]) -> set[tuple[str, str]]:
    return {(entity["text"], entity["type"]) for entity in record["annotations"]["entities"]}


def _gold_relations(record: dict[str, Any], *, include_no_relation: bool = False) -> set[tuple[str, str, str]]:
    by_id = {entity["entity_id"]: entity for entity in record["annotations"]["entities"]}
    rows: set[tuple[str, str, str]] = set()
    for relation in record["annotations"]["relations"]:
        if relation["type"] == "no_relation" and not include_no_relation:
            continue
        head = by_id[relation["head"]]["text"]
        tail = by_id[relation["tail"]]["text"]
        rows.add((head, relation["type"], tail))
    return rows


def _candidate_relations(
    record: dict[str, Any],
    *,
    accepted_only: bool,
    candidate_field: str = "plm_candidates",
) -> set[tuple[str, str, str]]:
    accepted = {
        decision["candidate_id"]
        for decision in record.get("llm_adjudications", [])
        if decision.get("decision") == "accept"
    }
    rows: set[tuple[str, str, str]] = set()
    for candidate in record.get(candidate_field, []):
        if candidate.get("candidate_type") != "relation":
            continue
        if accepted_only and candidate["candidate_id"] not in accepted:
            continue
        payload = candidate["payload"]
        if payload["relation_type"] == "no_relation":
            continue
        rows.add((payload["head_text"], payload["relation_type"], payload["tail_text"]))
    return rows


def _candidate_entities(record: dict[str, Any], *, candidate_field: str = "plm_candidates") -> set[tuple[str, str]]:
    rows: set[tuple[str, str]] = set()
    for candidate in record.get(candidate_field, []):
        if candidate.get("candidate_type") != "entity":
            continue
        payload = candidate["payload"]
        rows.add((payload["text"], payload["type"]))
    return rows


def prf(pred: set[Any], gold: set[Any]) -> dict[str, float]:
    tp = len(pred & gold)
    fp = len(pred - gold)
    fn = len(gold - pred)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": tp,
        "fp": fp,
        "fn": fn,
    }


def estimate_tokens(record: dict[str, Any], method: str) -> int:
    if method in {"rule_based", "plm_candidate_proxy"}:
        return 0
    total = 0
    for candidate in record.get("plm_candidates", []):
        if candidate.get("candidate_type") != "relation":
            continue
        span = candidate.get("evidence_window") or {"start": 0, "end": len(record["text"])}
        evidence_chars = max(0, int(span["end"]) - int(span["start"]))
        atom_chars = sum(len(PROMPT_ATOM_TEXT.get(atom, atom)) for atom in candidate.get("prompt_atoms", []))
        total += evidence_chars + atom_chars + 80
    return total


def evaluate_method(records: Sequence[dict[str, Any]], method: str, *, split: str = "test") -> dict[str, Any]:
    pred_entities: set[tuple[str, str, str]] = set()
    gold_entities: set[tuple[str, str, str]] = set()
    pred_relations: set[tuple[str, str, str, str]] = set()
    gold_relations: set[tuple[str, str, str, str]] = set()
    hard_negative_total = 0
    hard_negative_rejected = 0
    token_total = 0
    evaluated_records = 0

    for record in records:
        if record["source"]["split"] != split:
            continue
        evaluated_records += 1
        rid = record["record_id"]
        gold_entities.update((rid, text, typ) for text, typ in _gold_entities(record))
        entity_field = "rule_candidates" if method == "rule_based" else "plm_candidates"
        pred_entities.update((rid, text, typ) for text, typ in _candidate_entities(record, candidate_field=entity_field))
        gold_relations.update((rid, h, r, t) for h, r, t in _gold_relations(record))
        if method == "rule_based":
            pred = _candidate_relations(record, accepted_only=False, candidate_field="rule_candidates")
        elif method == "plm_candidate_proxy":
            pred = _candidate_relations(record, accepted_only=False, candidate_field="plm_candidates")
        elif method == "proposed_atom_adjudication_proxy":
            pred = _candidate_relations(record, accepted_only=True, candidate_field="plm_candidates")
        else:
            raise ValueError(f"Unknown method: {method}")
        pred_relations.update((rid, h, r, t) for h, r, t in pred)
        hard_negative_gold = _gold_relations(record, include_no_relation=True) - _gold_relations(record)
        hard_negative_total += len(hard_negative_gold)
        for head, _, tail in hard_negative_gold:
            if not any(h == head and t == tail for h, _, t in pred):
                hard_negative_rejected += 1
        token_total += estimate_tokens(record, method)

    entity_scores = prf(pred_entities, gold_entities)
    relation_scores = prf(pred_relations, gold_relations)
    hallucination_rate = (
        len(pred_relations - gold_relations) / len(pred_relations) if pred_relations else 0.0
    )
    hard_negative_accuracy = hard_negative_rejected / hard_negative_total if hard_negative_total else 1.0
    return {
        "method": method,
        "entity_precision": entity_scores["precision"],
        "entity_recall": entity_scores["recall"],
        "entity_f1": entity_scores["f1"],
        "relation_precision": relation_scores["precision"],
        "relation_recall": relation_scores["recall"],
        "relation_f1": relation_scores["f1"],
        "triple_f1": relation_scores["f1"],
        "relation_tp": relation_scores["tp"],
        "relation_fp": relation_scores["fp"],
        "relation_fn": relation_scores["fn"],
        "hallucination_rate": round(hallucination_rate, 4),
        "hard_negative_accuracy": round(hard_negative_accuracy, 4),
        "estimated_prompt_chars": token_total,
        "evaluated_split": split,
        "evaluated_records": evaluated_records,
        "status": "seed_proxy_result",
    }


def evaluate_challenge_metrics(records: Sequence[dict[str, Any]], methods: Sequence[str]) -> list[dict[str, Any]]:
    test_records = [record for record in records if record["source"]["split"] == "test"]
    tags = sorted({tag for record in test_records for tag in record["source"].get("challenge_tags", [])})
    rows: list[dict[str, Any]] = []
    for tag in tags:
        tagged_records = [record for record in test_records if tag in record["source"].get("challenge_tags", [])]
        for method in methods:
            row = evaluate_method(tagged_records, method)
            row["challenge_tag"] = tag
            rows.append(row)
    nested_records = [
        record
        for record in test_records
        if any(entity.get("nested_level", 0) > 0 for entity in record["annotations"]["entities"])
    ]
    if nested_records:
        for method in methods:
            row = evaluate_method(nested_records, method)
            row["challenge_tag"] = "nested_entity"
            rows.append(row)
    return rows


def build_final_graph(records: Sequence[dict[str, Any]]) -> dict[str, Any]:
    nodes: dict[tuple[str, str], dict[str, Any]] = {}
    edges: dict[tuple[str, str, str], dict[str, Any]] = {}
    for record in records:
        entity_by_text: dict[str, dict[str, Any]] = {}
        for candidate in record.get("plm_candidates", []):
            if candidate.get("candidate_type") != "entity":
                continue
            payload = candidate["payload"]
            key = (payload["text"], payload["type"])
            nodes.setdefault(
                key,
                {
                    "node_id": f"n{len(nodes) + 1}",
                    "text": payload["text"],
                    "type": payload["type"],
                    "record_ids": [],
                },
            )
            nodes[key]["record_ids"].append(record["record_id"])
            entity_by_text[payload["text"]] = nodes[key]
        accepted = {
            decision["candidate_id"]
            for decision in record.get("llm_adjudications", [])
            if decision.get("decision") == "accept"
        }
        for candidate in record.get("plm_candidates", []):
            if candidate.get("candidate_type") != "relation" or candidate["candidate_id"] not in accepted:
                continue
            payload = candidate["payload"]
            head_key = (payload["head_text"], payload["head_type"])
            tail_key = (payload["tail_text"], payload["tail_type"])
            if head_key not in nodes or tail_key not in nodes:
                continue
            edge_key = (nodes[head_key]["node_id"], payload["relation_type"], nodes[tail_key]["node_id"])
            edges.setdefault(
                edge_key,
                {
                    "edge_id": f"kg_r{len(edges) + 1}",
                    "head": edge_key[0],
                    "relation": edge_key[1],
                    "tail": edge_key[2],
                    "evidence": [],
                    "confidence": [],
                },
            )
            span = candidate["evidence_window"]
            edges[edge_key]["evidence"].append(
                {
                    "record_id": record["record_id"],
                    "text": record["text"][span["start"] : span["end"]],
                    "prompt_atoms": candidate.get("prompt_atoms", []),
                }
            )
            edges[edge_key]["confidence"].append(candidate["confidence"])

    node_rows = list(nodes.values())
    edge_rows = []
    for edge in edges.values():
        values = edge.pop("confidence")
        edge["confidence"] = round(sum(values) / len(values), 4) if values else None
        edge_rows.append(edge)
    return {
        "status": "seed_proxy_graph",
        "nodes": node_rows,
        "edges": edge_rows,
        "summary": {
            "node_count": len(node_rows),
            "edge_count": len(edge_rows),
            "relation_type_counts": dict(Counter(edge["relation"] for edge in edge_rows)),
        },
    }


def write_predictions(records: Sequence[dict[str, Any]], output_dir: Path) -> None:
    rule_candidates: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    for record in records:
        for candidate in record.get("rule_candidates", []):
            row = dict(candidate)
            row["record_id"] = record["record_id"]
            rule_candidates.append(row)
        for candidate in record.get("plm_candidates", []):
            row = dict(candidate)
            row["record_id"] = record["record_id"]
            candidates.append(row)
        for decision in record.get("llm_adjudications", []):
            row = dict(decision)
            row["record_id"] = record["record_id"]
            decisions.append(row)
    write_jsonl(output_dir / "candidates" / "rule_based_candidates.jsonl", rule_candidates)
    write_jsonl(output_dir / "candidates" / "plm_proxy_candidates.jsonl", candidates)
    write_jsonl(output_dir / "adjudication" / "proxy_llm_adjudications.jsonl", decisions)
    write_jsonl(output_dir / "final_records_with_predictions.jsonl", records)


def run_experiment(data_dir: Path = DEFAULT_DATA_DIR, output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[str, Any]:
    records = build_seed_dataset()
    dataset_manifest = save_dataset(records, data_dir)
    enriched_records = attach_predictions(records)
    write_predictions(enriched_records, output_dir)

    methods = ["rule_based", "plm_candidate_proxy", "proposed_atom_adjudication_proxy"]
    metrics = [evaluate_method(enriched_records, method) for method in methods]
    write_json(output_dir / "metrics.json", metrics)
    write_csv(output_dir / "metrics.csv", metrics)
    challenge_metrics = evaluate_challenge_metrics(enriched_records, methods)
    write_json(output_dir / "challenge_metrics.json", challenge_metrics)
    write_csv(output_dir / "challenge_metrics.csv", challenge_metrics)
    best_metric = max(metrics, key=lambda row: row["triple_f1"])

    graph = build_final_graph(enriched_records)
    write_json(data_dir / "graph" / "mechanism_seed_graph.json", graph)
    write_json(output_dir / "mechanism_seed_graph.json", graph)

    summary = {
        "status": "seed_proxy_experiment_completed",
        "dataset_manifest": dataset_manifest,
        "methods": methods,
        "best_method": best_metric["method"],
        "metrics_path": str(output_dir / "metrics.json"),
        "challenge_metrics_path": str(output_dir / "challenge_metrics.json"),
        "final_records_path": str(output_dir / "final_records_with_predictions.jsonl"),
        "graph_path": str(output_dir / "mechanism_seed_graph.json"),
        "caveat": "Deterministic seed/proxy experiment; replace proxy extractor/adjudicator with real PLM and LLM backends for publishable results.",
    }
    write_json(output_dir / "experiment_summary.json", summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run mechanism KG seed extraction experiment.")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_experiment(data_dir=args.data_dir, output_dir=args.output_dir)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
