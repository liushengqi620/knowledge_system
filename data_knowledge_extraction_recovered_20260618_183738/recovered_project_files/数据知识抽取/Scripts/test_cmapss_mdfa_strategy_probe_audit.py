from __future__ import annotations

import unittest

from cmapss_mdfa_strategy_probe_audit import build_mdfa_strategy_probe_audit, render_markdown


class CmapssMdfaStrategyProbeAuditTest(unittest.TestCase):
    def test_strategy_probe_selects_fd001_and_fd002_candidates_but_blocks_reproduction(self) -> None:
        payload = build_mdfa_strategy_probe_audit()
        rows = {row["name"]: row for row in payload["probe_rows"]}

        self.assertEqual("full_branch_archive_materialized_reproduction_pending", payload["status"])
        self.assertTrue(payload["gates"]["source2d_full_fd001_present"])
        self.assertTrue(payload["gates"]["fd001_long_window_full_present"])
        self.assertTrue(payload["gates"]["fd002_multicondition_failure_observed"])
        self.assertTrue(payload["gates"]["fd002_condition_aware_full_present"])
        self.assertTrue(payload["gates"]["fd003_short_window_failure_observed"])
        self.assertTrue(payload["gates"]["fd003_trajectory_cluster_negative_observed"])
        self.assertTrue(payload["gates"]["fd003_long_window_full_present"])
        self.assertTrue(payload["gates"]["fd004_condition_aware_full_present"])
        self.assertTrue(payload["gates"]["fd001_fd003_low_dropout_archive_present"])
        self.assertTrue(payload["gates"]["fd003_zero_dropout_full_archive_present"])
        self.assertTrue(payload["gates"]["dropout_sensitivity_probe_present"])
        self.assertTrue(payload["gates"]["batch_sensitivity_probe_present"])
        self.assertTrue(payload["gates"]["table4_key_sensor_probe_present"])
        self.assertTrue(payload["gates"]["pca_threshold_sensitivity_probe_present"])
        self.assertTrue(payload["gates"]["native_raw_rul_probe_present"])
        self.assertTrue(payload["gates"]["validation_output_calibration_probe_present"])
        self.assertTrue(payload["gates"]["validation_snapshot_ensemble_probe_present"])
        self.assertTrue(payload["gates"]["temporal_velocity_feature_probe_present"])
        self.assertTrue(payload["gates"]["feature_policy_probe_complete"])
        self.assertTrue(payload["gates"]["full_fd001_fd004_three_seed_archive_present"])
        self.assertFalse(payload["gates"]["safe_to_promote_strategy_to_published_reproduction"])
        self.assertEqual(
            6,
            payload["diagnostics"]["previous_full_single_condition_archive"]["completed_subset_seed_count"],
        )
        self.assertEqual(6, payload["diagnostics"]["full_single_condition_archive"]["completed_subset_seed_count"])
        self.assertEqual(
            6,
            payload["diagnostics"]["zero_dropout_single_condition_archive"]["completed_subset_seed_count"],
        )
        self.assertEqual(6, payload["diagnostics"]["full_multi_condition_archive"]["completed_subset_seed_count"])
        self.assertEqual(
            "source2d_all24_pca_window80_dropout01_fd001_full",
            payload["decision"]["current_fd001_full_candidate"],
        )
        self.assertEqual("all24_pca", payload["decision"]["current_feature_policy"])
        self.assertEqual(
            "source2d_all24_pca_window80_dropout000_leveldiff_fd003_full",
            payload["decision"]["current_fd003_two_fault_candidate"],
        )
        self.assertEqual(80, payload["decision"]["current_fd003_window_size"])
        self.assertEqual("level_diff", payload["decision"]["current_fd003_temporal_feature_mode"])
        self.assertAlmostEqual(12.9260, payload["decision"]["current_fd003_three_seed_rmse"], places=4)
        self.assertEqual(
            "source2d_sensor21_pca_kmeans_onehot_fd002_full",
            payload["decision"]["current_fd002_multicondition_candidate"],
        )
        self.assertEqual("kmeans6_settings", payload["decision"]["current_fd002_condition_policy"])
        self.assertEqual(
            "source2d_sensor21_pca_kmeans_onehot_fd004_full",
            payload["decision"]["current_fd004_multicondition_candidate"],
        )
        self.assertEqual("kmeans6_settings", payload["decision"]["current_fd004_condition_policy"])
        self.assertIn("source-style cap policy is not yet exact-native", payload["claim_boundary"])
        self.assertLess(
            rows["source2d_all24_pca_window80_dropout01_fd001_full"]["rmse"],
            rows["source2d_all24_pca_window80_fd001_full"]["rmse"],
        )
        self.assertLess(
            rows["source2d_all24_pca_window80_dropout01_fd003_full"]["rmse"],
            rows["source2d_all24_pca_window80_fd003_full"]["rmse"],
        )
        self.assertLess(
            rows["source2d_all24_pca_window80_dropout000_fd003_full"]["rmse"],
            rows["source2d_all24_pca_window80_dropout01_fd003_full"]["rmse"],
        )
        self.assertGreater(
            rows["source2d_all24_pca_window80_dropout01_leveldiff_fd001_probe25"]["rmse"],
            rows["source2d_all24_pca_window80_dropout01_fd001_probe25"]["rmse"],
        )
        self.assertLess(
            rows["source2d_all24_pca_window80_dropout000_leveldiff_fd003_probe25"]["rmse"],
            rows["source2d_all24_pca_window80_dropout000_fd003_probe25"]["rmse"],
        )
        self.assertLess(
            payload["diagnostics"]["temporal_level_diff_fd003_archive"]["subset_stats"]["FD003"]["rmse_mean"],
            payload["diagnostics"]["zero_dropout_single_condition_archive"]["subset_stats"]["FD003"]["rmse_mean"],
        )
        self.assertLess(payload["diagnostics"]["fd003_leveldiff_full_mean_rmse_delta_vs_level_full"], 0.0)
        self.assertGreater(payload["diagnostics"]["fd003_leveldiff_full_seed42_rmse_delta_vs_level_full"], 0.0)
        self.assertGreater(
            payload["diagnostics"]["zero_dropout_single_condition_archive"]["subset_stats"]["FD001"]["rmse_mean"],
            payload["diagnostics"]["full_single_condition_archive"]["subset_stats"]["FD001"]["rmse_mean"],
        )
        self.assertLess(
            payload["diagnostics"]["zero_dropout_single_condition_archive"]["subset_stats"]["FD003"]["rmse_mean"],
            payload["diagnostics"]["full_single_condition_archive"]["subset_stats"]["FD003"]["rmse_mean"],
        )
        self.assertLess(
            rows["source2d_sensor21_pca_kmeans_onehot_fd002_full"]["rmse"],
            rows["source2d_all24_pca_full_fd002_failed_multicondition"]["rmse"],
        )
        self.assertLess(
            rows["source2d_all24_pca_window80_fd003_full"]["rmse"],
            rows["source2d_all24_pca_window30_fd003_failure"]["rmse"],
        )
        self.assertGreater(
            rows["source2d_common_sensors_pca_kmeans4_trajectory_fd003_negative"]["rmse"],
            rows["source2d_all24_pca_window80_dropout01_fd003_full"]["rmse"],
        )
        self.assertIn("safe_to_promote_strategy_to_published_reproduction", payload["missing_gates"])
        self.assertNotIn("full_fd001_fd004_three_seed_archive_present", payload["missing_gates"])
        self.assertIn("table4_key_sensor_probe", payload["diagnostics"])
        self.assertIn("pca_threshold_sensitivity_probe", payload["diagnostics"])
        self.assertIn("native_raw_rul_probe", payload["diagnostics"])
        self.assertIn("validation_output_calibration_probe", payload["diagnostics"])
        self.assertFalse(payload["diagnostics"]["validation_output_calibration_probe"]["FD001"]["applied"])
        self.assertFalse(payload["diagnostics"]["validation_output_calibration_probe"]["FD003"]["applied"])
        self.assertIn("validation_snapshot_ensemble_probe", payload["diagnostics"])
        self.assertIn("temporal_velocity_feature_probe", payload["diagnostics"])
        self.assertFalse(payload["diagnostics"]["validation_snapshot_ensemble_probe"]["FD001"]["applied"])
        self.assertFalse(payload["diagnostics"]["validation_snapshot_ensemble_probe"]["FD003"]["applied"])
        self.assertEqual(
            "validation_rmse_delta_guard_failed",
            payload["diagnostics"]["validation_snapshot_ensemble_probe"]["FD001"]["reason"],
        )
        self.assertLess(
            payload["diagnostics"]["validation_snapshot_ensemble_probe"]["FD001"]["val_rmse_delta"],
            0.0,
        )
        self.assertEqual(
            "validation_rmse_delta_guard_failed",
            payload["diagnostics"]["validation_output_calibration_probe"]["FD001"]["reason"],
        )
        self.assertEqual(
            "validation_rmse_delta_guard_failed",
            rows["source2d_all24_pca_window80_dropout000_affine_cal_fd003_probe25"]["output_calibration_reason"],
        )
        self.assertGreater(payload["diagnostics"]["native_raw_rul_probe"]["FD002"]["rmse"], 20.0)
        self.assertGreater(payload["diagnostics"]["native_raw_rul_probe"]["FD004"]["rmse"], 20.0)
        self.assertEqual(
            9,
            rows["source2d_all24_pca_pca090_fd001_probe25"]["pca_feature_dim"],
        )
        self.assertEqual(
            2,
            rows["source2d_all24_pca_pca090_fd002_probe25"]["pca_feature_dim"],
        )
        self.assertGreater(
            rows["source2d_sensor21_pca_kmeans_onehot_fd002_full"]["raw_rmse"],
            rows["source2d_sensor21_pca_kmeans_onehot_fd002_full"]["rmse"],
        )
        self.assertGreater(
            rows["source2d_sensor21_pca_kmeans_onehot_fd004_full"]["raw_rmse"],
            rows["source2d_sensor21_pca_kmeans_onehot_fd004_full"]["rmse"],
        )
        self.assertIn("selected_full_budget_fd001_raw_rmse", payload["diagnostics"])
        self.assertIn("raw_rmse_mean", payload["diagnostics"]["full_multi_condition_archive"]["subset_stats"]["FD002"])
        self.assertLess(
            rows["source2d_sensor21_pca_kmeans_onehot_fd002_full"]["rmse"],
            rows["source2d_mdfa_key_sensors_pca_fd002_probe25"]["rmse"],
        )
        self.assertLess(
            rows["source2d_sensor21_pca_kmeans_onehot_fd004_full"]["rmse"],
            rows["source2d_mdfa_key_sensors_pca_fd004_probe25"]["rmse"],
        )
        self.assertLess(
            rows["source2d_sensor21_pca_kmeans_onehot_fd002_full"]["rmse"],
            rows["source2d_all24_pca_pca090_fd002_probe25"]["rmse"],
        )
        self.assertLess(
            rows["source2d_sensor21_pca_kmeans_onehot_fd004_full"]["rmse"],
            rows["source2d_all24_pca_pca090_fd004_probe25"]["rmse"],
        )

    def test_markdown_is_claim_safe(self) -> None:
        markdown = render_markdown(build_mdfa_strategy_probe_audit())
        self.assertIn("C-MAPSS MDFA Strategy Probe Audit", markdown)
        self.assertIn("source2d_all24_pca_window80_dropout01_fd001_full", markdown)
        self.assertIn("source2d_all24_pca_window80_dropout000_fd003_full", markdown)
        self.assertIn("source2d_sensor21_pca_kmeans_onehot_fd002_full", markdown)
        self.assertIn("source2d_sensor21_pca_kmeans_onehot_fd004_full", markdown)
        self.assertIn("source2d_mdfa_key_sensors_pca_fd002_probe25", markdown)
        self.assertIn("source2d_all24_pca_pca090_fd004_probe25", markdown)
        self.assertIn("PCA=0.90 sensitivity", markdown)
        self.assertIn("cap150/raw-test probe", markdown)
        self.assertIn("Validation-only affine output calibration", markdown)
        self.assertIn("affine_val:blocked", markdown)
        self.assertIn("snapshot-ensemble probes", markdown)
        self.assertIn("k5:blocked", markdown)
        self.assertIn("source2d_all24_pca_window80_dropout000_leveldiff_fd003_full", markdown)
        self.assertIn("level_diff", markdown)
        self.assertIn("Temporal level+diff FD003 challenger", markdown)
        self.assertIn("Raw RMSE", markdown)
        self.assertIn("Raw Score", markdown)
        self.assertIn("Full Archive Stats", markdown)
        self.assertIn("Previous single-condition archive", markdown)
        self.assertIn("Selected single-condition archive", markdown)
        self.assertIn("not a published MDFA reproduction", markdown)
        self.assertNotIn("official SOTA is proven", markdown)


if __name__ == "__main__":
    unittest.main()
