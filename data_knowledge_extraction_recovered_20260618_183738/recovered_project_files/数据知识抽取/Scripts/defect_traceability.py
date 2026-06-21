"""Compatibility entrypoint for defect traceability.

The legacy tabular classifier has been retired. Calls that still reach this
module are routed to the causal process graph pipeline so the project keeps a
single modeling path.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd


def run_defect_prediction_and_traceability(
    df: pd.DataFrame,
    H: np.ndarray | None,
    feature_cols: list[str],
    config: dict,
    project_root: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    del H
    if project_root is None:
        project_root = Path.cwd()
    cfg = dict(config)
    cfg["paper_method_enabled"] = True
    from paper_defect_pipeline import run_paper_defect_pipeline

    return run_paper_defect_pipeline(df, feature_cols, cfg, project_root)
