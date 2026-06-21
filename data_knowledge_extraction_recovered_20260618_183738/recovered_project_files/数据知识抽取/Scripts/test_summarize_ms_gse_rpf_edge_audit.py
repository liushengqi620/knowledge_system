import json
import tempfile
import unittest
from pathlib import Path

from summarize_ms_gse_rpf_edge_audit import build_edge_audit_report, render_markdown


def _write_run(
    root: Path,
    *,
    seed: int,
    val_macro: float,
    test_macro: float,
    bal_acc: float,
    class_f1: dict[str, float],
    path: str,
    prior_sources: list[str],
) -> None:
    root.mkdir(parents=True, exist_ok=True)
    payload = {
        "dataset": "tep",
        "target": "event_quality_class_id",
        "variant": "full",
        "seed": seed,
        "val_metrics": {
            "macro_f1": val_macro,
            "balanced_accuracy": val_macro,
            "per_class": {cls: {"f1": score, "support": 10} for cls, score in class_f1.items()},
        },
        "primary_test_metrics": {
            "macro_f1": test_macro,
            "balanced_accuracy": bal_acc,
            "per_class": {cls: {"f1": score, "support": 10} for cls, score in class_f1.items()},
        },
        "top_evidence_paths": [
            {
                "path": path,
                "group_path": path,
                "mean_weight": 0.4,
                "mean_prior_weight": 0.3,
                "mean_salience_weight": 0.2,
            }
        ],
        "algorithmic_edge_prior": {
            "mode": "edge_pool",
            "density": 0.10,
            "uncapped_edges": 20,
            "top_edge_indices": [
                {"target": 1, "source": 0, "votes": len(prior_sources), "sources": prior_sources}
            ],
            "edge_pool": {
                "corroborated_edges": 8,
                "single_view_edges": 2,
                "mean_votes": 2.0,
                "component_edge_counts": {source: 4 for source in prior_sources},
            },
        },
    }
    (root / f"ms_gse_rpf_tep_full_seed{seed}.json").write_text(json.dumps(payload), encoding="utf-8")


class SummarizeMSGserpfEdgeAuditTest(unittest.TestCase):
    def test_builds_low_tail_and_edge_source_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = root / "baseline"
            candidate = root / "candidate"
            _write_run(
                baseline,
                seed=42,
                val_macro=0.70,
                test_macro=0.72,
                bal_acc=0.73,
                class_f1={"0": 0.20, "1": 0.90, "2": 0.80, "3": 0.30},
                path="A -> B",
                prior_sources=["correlation", "lag"],
            )
            _write_run(
                baseline,
                seed=43,
                val_macro=0.72,
                test_macro=0.74,
                bal_acc=0.75,
                class_f1={"0": 0.30, "1": 0.90, "2": 0.80, "3": 0.35},
                path="A -> B",
                prior_sources=["correlation", "lag"],
            )
            _write_run(
                candidate,
                seed=42,
                val_macro=0.69,
                test_macro=0.70,
                bal_acc=0.71,
                class_f1={"0": 0.10, "1": 0.92, "2": 0.82, "3": 0.28},
                path="C -> D",
                prior_sources=["class", "fault_response"],
            )
            _write_run(
                candidate,
                seed=43,
                val_macro=0.71,
                test_macro=0.73,
                bal_acc=0.74,
                class_f1={"0": 0.20, "1": 0.92, "2": 0.82, "3": 0.31},
                path="C -> D",
                prior_sources=["class", "fault_response"],
            )

            report = build_edge_audit_report(
                baseline_dir=baseline,
                candidates=[("candidate", candidate)],
                dataset="tep",
                target="event_quality_class_id",
                variant="full",
                low_tail_quantile=0.25,
                max_low_tail_classes=1,
            )

        self.assertEqual(report["baseline"]["low_tail_classes"][0]["class"], "0")
        candidate_report = report["candidates"][0]
        self.assertLess(candidate_report["low_tail_val_f1_gain_mean"], 0.0)
        self.assertEqual(candidate_report["path_jaccard"], 0.0)
        self.assertEqual(candidate_report["new_candidate_top_paths"][0]["path"], "C -> D")
        self.assertEqual(candidate_report["edge_prior_summary"]["top_edge_family_counts"]["task"], 4)
        markdown = render_markdown(report)
        self.assertIn("Most Harmed Low-Tail Validation Classes", markdown)
        self.assertIn("C -> D", markdown)


if __name__ == "__main__":
    unittest.main()
