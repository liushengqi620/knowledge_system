from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from run_rule_temporal_ablation_experiments import (
    DEFAULT_RULES,
    add_temporal_history_features,
    fit_rule_margin_transformer,
    parse_process_sequence_key,
)


class RuleTemporalAblationComponentTests(unittest.TestCase):
    def test_parse_process_sequence_key_extracts_line_and_strand(self) -> None:
        parsed = parse_process_sequence_key("2|1|255928.0|missing|20220101035536|0")

        self.assertEqual(parsed["caster_id"], "2")
        self.assertEqual(parsed["strand_id"], "1")
        self.assertEqual(parsed["heat_id"], "255928.0")

    def test_rule_margin_scale_is_fitted_from_training_rows_only(self) -> None:
        df = pd.DataFrame(
            {
                "过热度/℃": [10.0, 20.0, 30.0, 2000.0],
                "液面波动极差/mm": [6.0, 7.0, 8.0, 9.0],
            }
        )
        transformer = fit_rule_margin_transformer(
            df,
            train_idx=np.array([0, 1, 2]),
            rules=[rule for rule in DEFAULT_RULES if rule.column == "过热度/℃"],
        )
        margin = transformer.transform(df)

        self.assertAlmostEqual(transformer.rules_[0].scale, 10.0)
        self.assertGreater(margin.loc[3, "rule_margin"], 100.0)

    def test_temporal_history_features_use_only_prior_rows_within_line(self) -> None:
        df = pd.DataFrame(
            {
                "process_sequence_key": ["2|1|h1|m|t|0", "2|1|h2|m|t|1", "2|2|h3|m|t|2"],
                "process_time": ["2022-01-01 00:00:00", "2022-01-01 00:10:00", "2022-01-01 00:20:00"],
                "过热度/℃": [10.0, 20.0, 99.0],
            }
        )

        out, cols = add_temporal_history_features(df, ["过热度/℃"], max_features=1)

        self.assertIn("hist_lag1__过热度_C", cols)
        self.assertTrue(np.isnan(out.loc[0, "hist_lag1__过热度_C"]))
        self.assertEqual(out.loc[1, "hist_lag1__过热度_C"], 10.0)
        self.assertTrue(np.isnan(out.loc[2, "hist_lag1__过热度_C"]))


if __name__ == "__main__":
    unittest.main()
