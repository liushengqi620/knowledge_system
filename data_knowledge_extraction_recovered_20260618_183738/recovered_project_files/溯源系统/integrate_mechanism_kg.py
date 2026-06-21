#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Export mechanism-KG rules for the anomaly traceability system."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


CURRENT_DIR = Path(__file__).resolve().parent
SRC_DIR = CURRENT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mechanism_kg_traceability_adapter import build_adapter_pack


DEFAULT_KG = (
    CURRENT_DIR.parent
    / "RAG"
    / "data"
    / "quality_traceability_large_kg"
    / "quality_traceability_large_kg_seed.json"
)
DEFAULT_OUTPUT = CURRENT_DIR / "outputs" / "mechanism_kg_traceability_adapter"


def main() -> None:
    parser = argparse.ArgumentParser(description="Integrate mechanism KG into anomaly traceability system.")
    parser.add_argument("--kg", type=Path, default=DEFAULT_KG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--min-confidence", type=float, default=0.7)
    parser.add_argument("--max-rules", type=int, default=600)
    args = parser.parse_args()
    summary = build_adapter_pack(
        kg_path=args.kg,
        output_dir=args.output_dir,
        min_confidence=args.min_confidence,
        max_rules=args.max_rules,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
