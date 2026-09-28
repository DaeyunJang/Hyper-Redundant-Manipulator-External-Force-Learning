"""합성 자료로 masked loss와 train→checkpoint→predict 경로를 검사한다."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest

import numpy as np
import torch

from hrm_force.data import load_labels
from hrm_force.engine import losses, predict_model, train_model, validate
from hrm_force.models import build_model


class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_threads = torch.get_num_threads()
        torch.set_num_threads(1)

    @classmethod
    def tearDownClass(cls):
        torch.set_num_threads(cls.original_threads)

    def test_all_unloaded_body_loss_has_finite_gradients(self):
        torch.manual_seed(44)
        model = build_model("small_gru", 4, task="body", seq_len=3)
        output = model(torch.randn(4, 3, 4))
        # 모두 무부하이면 ID의 유효성에 관계없이 위치 loss를 끈다.
        result = losses(output, torch.zeros(4, 3), torch.zeros(4, dtype=torch.long),
                        torch.tensor([0, 8, 17, -1]), "body",
                        {"load_loss_weight": 0.2, "location_loss_weight": 0.3})
        self.assertTrue(all(torch.isfinite(value) for value in result))
        self.assertEqual(result[3].item(), 0)
        result[0].backward()
        for parameter in model.parameters():
            self.assertIsNotNone(parameter.grad)
            self.assertTrue(torch.isfinite(parameter.grad).all())
        self.assertEqual(torch.count_nonzero(model.location_head.weight.grad).item(), 0)
        self.assertEqual(torch.count_nonzero(model.location_head.bias.grad).item(), 0)
        self.assertGreater(torch.count_nonzero(model.force_head.weight.grad).item(), 0)

    def test_validation_location_mean_is_independent_of_batch_size(self):
        class FixedOutputs(torch.nn.Module):
            def forward(self, x):
                row=x[:, -1]
                return {"force": row[:, :3], "load_logit": row[:, 3],
                        "location_logits": row[:, 4:]}

        torch.manual_seed(81)
        x=torch.randn(9, 1, 22)
        # Sparse eligible labels and very different CE losses reveal wrong denominators.
        x[0, 0, 4:]=0.;x[0, 0, 4]=10.
        x[7, 0, 4:]=0.;x[7, 0, 4]=-10.
        y=torch.randn(9, 3)
        load=torch.tensor([1, 0, 0, 0, 0, 0, 0, 1, 1])
        ids=torch.tensor([0, 0, 0, 0, 0, 0, 0, 0, -1])
        tensors=(x,y,load,ids)
        config={"task":"body","load_loss_weight":.2,"location_loss_weight":.5}
        expected=validate(FixedOutputs(),tensors,dict(config,batch_size=9))
        for size in (1,2,3,4,8):
            with self.subTest(batch_size=size):
                actual=validate(FixedOutputs(),tensors,dict(config,batch_size=size))
                for key in expected:
                    self.assertAlmostEqual(actual[key],expected[key],places=6)
        valid=(load==1)&(ids>=0)
        expected_location=torch.nn.functional.cross_entropy(x[valid,0,4:],ids[valid])
        self.assertAlmostEqual(expected["location_loss"],float(expected_location),places=6)

    def test_synthetic_train_checkpoint_and_prediction_agree(self):
        for task in ("tip", "body"):
            with self.subTest(task=task), tempfile.TemporaryDirectory() as temporary:
                rng = np.random.default_rng(7)
                x = rng.normal(size=(20, 4)).astype(np.float32)
                y = np.stack((x[:, 0] * .1, x[:, 1] * -.2, x[:, 2] * .3), axis=1)
                original_y = y.copy()
                session = {
                    "x": x, "y": y, "ts": np.arange(20, dtype=np.int64)*33_333_333,
                    "id": 18 if task == "tip" else 9,
                    "source_id": 18 if task == "tip" else 9,
                    "columns": [f"feature_{i}" for i in range(4)],
                    "info": {"session_id": "synthetic", "folder": "synthetic_recording",
                             "sha256": "synthetic-no-source-file", "metadata_sha256": {}},
                }
                sessions = [session]
                indices = {"train": np.asarray([(0, i) for i in range(2, 10)]),
                           "val": np.asarray([(0, i) for i in range(12, 16)]),
                           "test": np.asarray([(0, i) for i in range(16, 20)])}
                scaler = {"x_mean": np.array([.1, .2, -.3, .4]),
                          "x_std": np.array([.8, 1.2, 1.5, .7]),
                          "y_mean": np.array([.01, -.02, .03]),
                          "y_std": np.array([.1, .2, .3])}
                config = {"seed": 17, "threads": 1, "task": task, "window_samples": 3,
                          "thresholds_N": [.0454, .0436, .0729], "batch_size": 4,
                          "learning_rate": .001, "weight_decay": 0., "max_epochs": 2,
                          "patience": 3, "load_loss_weight": .2, "location_loss_weight": .3}
                output_dir = Path(temporary) / "trained"
                with contextlib.redirect_stdout(io.StringIO()):
                    stats = train_model("mlp", sessions, indices, scaler, config,
                                        output_dir, torch.device("cpu"))
                self.assertEqual(stats["epochs_run"], 2)
                for filename in ("checkpoint.pt", "history.csv", "training_summary.json",
                                 "bundle_metadata.json"):
                    self.assertTrue((output_dir / filename).is_file())
                bundle = torch.load(output_dir / "checkpoint.pt", map_location="cpu",
                                    weights_only=True)
                self.assertEqual(bundle["training_sign_multiplier"], 1)
                self.assertEqual(bundle["future_hrm_control_multiplier"], -1)
                frame, _ = predict_model(bundle, sessions, indices["test"], batch_size=1)
                batched, _ = predict_model(bundle, sessions, indices["test"], batch_size=16)
                restored = build_model("mlp", 4, task=task, seq_len=3).eval()
                restored.load_state_dict(bundle["state_dict"])
                windows = np.stack([session["x_scaled"][end-2:end+1]
                                    for _, end in indices["test"]])
                with torch.inference_mode():
                    direct = restored(torch.from_numpy(windows))
                expected_force = direct["force"].numpy()*scaler["y_std"] + scaler["y_mean"]
                columns = [f"pred_f{axis}_N" for axis in "xyz"]
                np.testing.assert_allclose(frame[columns], expected_force, rtol=1e-5, atol=1e-7)
                np.testing.assert_allclose(frame[columns], batched[columns], rtol=1e-5, atol=1e-7)
                np.testing.assert_allclose(frame["load_probability"],
                                           direct["load_logit"].sigmoid().numpy(),
                                           rtol=1e-5, atol=1e-7)
                expected_id = (direct["location_logits"].argmax(-1).numpy()+1
                               if task == "body" else np.full(4, 18))
                np.testing.assert_array_equal(frame["conditional_pred_id"], expected_id)
                expected_load = load_labels(expected_force, np.array(config["thresholds_N"]))
                np.testing.assert_array_equal(frame["pred_load"], expected_load)
                np.testing.assert_array_equal(frame["pred_id"],
                                              np.where(expected_load, expected_id, 0))
                for axis in "xyz":
                    np.testing.assert_allclose(frame[f"pred_f{axis}_mN"],
                                               frame[f"pred_f{axis}_N"] * 1000)
                    np.testing.assert_allclose(frame[f"display_f{axis}_N"],
                                               np.where(expected_load, frame[f"pred_f{axis}_N"], 0))
                np.testing.assert_array_equal(session["y"], original_y)
                np.testing.assert_array_equal(frame["source_row"], [16, 17, 18, 19])


if __name__ == "__main__":
    unittest.main()
