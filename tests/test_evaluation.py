"""Deterministic metric tests, independent of model training and raw datasets."""

import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from hrm_force.evaluation import _session_parts, evaluate_predictions, save_evaluation


def prediction_frame() -> pd.DataFrame:
    frame = pd.DataFrame({
        "session_id": ["one"] * 4,
        "source_row": [0, 1, 3, 4],
        "source_time_ns": np.array([0, 10, 30, 40], dtype=np.int64) * 1_000_000 + 1_700_000_000_000_000_000,
        "elapsed_s": [0.0, 0.01, 0.03, 0.04],
        "true_fx_N": [0.0, 1.0, 2.0, 0.0],
        "true_fy_N": [0.0] * 4,
        "true_fz_N": [0.0] * 4,
        "pred_fx_N": [0.0, 0.0, 3.0, 0.2],
        "pred_fy_N": [0.0] * 4,
        "pred_fz_N": [0.0] * 4,
        "true_load": [0, 1, 1, 0],
        "pred_load": [0, 0, 1, 1],
        "load_probability": [0.1, 0.8, 0.9, 0.2],
        "load_head_pred": [0, 1, 1, 0],
        "true_id": [18, 18, 18, 18],
        "pred_id": [0, 0, 17, 18],
        "conditional_pred_id": [18, 18, 17, 18],
    })
    return frame


class EvaluationTests(unittest.TestCase):
    def test_force_units_bias_and_vector_definition(self):
        metrics = evaluate_predictions(prediction_frame())
        self.assertEqual(metrics["n_samples"], 4)
        self.assertAlmostEqual(metrics["fx_mae_N"], 0.55)
        self.assertAlmostEqual(metrics["fx_bias_N"], 0.05)
        self.assertAlmostEqual(metrics["fx_rmse_N"], np.sqrt(2.04 / 4))
        self.assertAlmostEqual(metrics["force_rmse_N"], np.sqrt(2.04 / 12))
        self.assertAlmostEqual(metrics["vector_mae_N"], 0.55)
        self.assertAlmostEqual(metrics["vector_rmse_N"], np.sqrt(2.04 / 4))
        self.assertAlmostEqual(metrics["fx_bias_mN"], 50)
        self.assertAlmostEqual(metrics["loaded_fx_mae_N"], 1.0)
        self.assertAlmostEqual(metrics["unloaded_fx_mae_N"], 0.1)

    def test_load_and_conditional_location_do_not_share_denominators(self):
        frame = prediction_frame()
        original_id = frame["true_id"].copy()
        metrics = evaluate_predictions(frame)
        for key in ("load_tp", "load_tn", "load_fp", "load_fn"):
            self.assertEqual(metrics[key], 1)
        self.assertEqual(metrics["load_f1"], 0.5)
        self.assertEqual(metrics["load_head_f1"], 1.0)
        self.assertEqual(metrics["location_n_loaded"], 2)
        self.assertEqual(metrics["location_accuracy_loaded"], 0.5)
        self.assertEqual(metrics["location_gated_accuracy_loaded"], 0.0)
        self.assertEqual(metrics["end_to_end_id_accuracy"], 0.25)
        pd.testing.assert_series_equal(frame["true_id"], original_id)

    def test_empty_and_all_unloaded_undefined_metrics(self):
        frame = prediction_frame().iloc[[0]]
        metrics = evaluate_predictions(frame)
        self.assertTrue(np.isnan(metrics["load_f1"]))
        self.assertTrue(np.isnan(metrics["location_accuracy_loaded"]))
        self.assertTrue(np.isnan(metrics["loaded_fx_rmse_N"]))
        self.assertEqual(metrics["end_to_end_id_accuracy"], 1.0)
        empty = evaluate_predictions(frame.iloc[:0])
        self.assertEqual(empty["n_samples"], 0)
        self.assertTrue(np.isnan(empty["force_rmse_N"]))

    def test_unknown_loaded_location_is_excluded_not_zeroed(self):
        frame = prediction_frame()
        frame.loc[1, "true_id"] = np.nan
        metrics = evaluate_predictions(frame)
        self.assertEqual(metrics["location_n_loaded"], 1)
        self.assertEqual(metrics["end_to_end_n_samples"], 3)
        self.assertEqual(metrics["end_to_end_id_accuracy"], 1 / 3)
        self.assertEqual(metrics["loaded_n_samples"], 2)

    def test_missing_or_nonfinite_is_not_no_load(self):
        frame = prediction_frame()
        frame.loc[0, "true_fx_N"] = np.nan
        with self.assertRaises(ValueError):
            evaluate_predictions(frame)
        frame = prediction_frame()
        frame.loc[0, "true_load"] = np.nan
        with self.assertRaises(ValueError):
            evaluate_predictions(frame)
        with self.assertRaises(ValueError):
            evaluate_predictions(prediction_frame().drop(columns="pred_fz_N"))

    def test_boolean_strings_are_explicit(self):
        frame = prediction_frame()
        frame["true_load"] = ["False", "True", "True", "False"]
        metrics = evaluate_predictions(frame)
        self.assertEqual(metrics["loaded_n_samples"], 2)
        self.assertEqual(metrics["load_tn"], 1)

    def test_plot_segments_preserve_row_gaps_and_sessions(self):
        frame = prediction_frame()
        frame["_plot_position"] = np.arange(len(frame))
        parts = _session_parts(frame)
        self.assertEqual([list(segment) for segment in parts[0][2]], [[0, 1], [2, 3]])
        frame.loc[2:, "session_id"] = "two"
        parts = _session_parts(frame)
        self.assertEqual(len(parts), 2)
        self.assertGreater(parts[1][1][0], parts[0][1][-1])
        # Remove elapsed_s and preserve exact 10 ms differences at epoch ns scale.
        parts = _session_parts(frame.drop(columns="elapsed_s"))
        self.assertAlmostEqual(parts[0][1][1] - parts[0][1][0], 0.01)

    def test_files_confusion_and_valid_json(self):
        frame = prediction_frame()
        with tempfile.TemporaryDirectory() as temporary:
            result = save_evaluation(frame, temporary, "body")
            destination = Path(temporary)
            expected = ["metrics.json", "metrics.csv", "per_id_metrics.csv", "confusion.csv",
                        "conditional_confusion.csv", "error_by_force.csv",
                        "force_timeseries.png", "load_timeseries.png"]
            for filename in expected:
                self.assertGreater((destination / filename).stat().st_size, 0)
            written = json.loads((destination / "metrics.json").read_text())
            self.assertEqual(written["load_f1"], result["load_f1"])
            confusion = pd.read_csv(destination / "confusion.csv", index_col=0)
            self.assertEqual(int(confusion.to_numpy().sum()), 4)
            self.assertEqual(confusion.loc[0, "pred_id_18"], 1)
            conditional = pd.read_csv(destination / "conditional_confusion.csv", index_col=0)
            self.assertEqual(int(conditional.to_numpy().sum()), 2)
            per_id = pd.read_csv(destination / "per_id_metrics.csv")
            self.assertEqual(per_id["true_id"].tolist(), [18])
            self.assertEqual(per_id["n_samples"].tolist(), [4])
            # Empty subsets are valid JSON null, not nonstandard NaN literals.
            save_evaluation(frame.iloc[:1], destination / "unloaded", "tip")
            empty_json = json.loads((destination / "unloaded/metrics.json").read_text())
            self.assertIsNone(empty_json["loaded_fx_rmse_N"])


if __name__ == "__main__":
    unittest.main()
