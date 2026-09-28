"""실제 forward/backward, 시간 인과성 및 체크포인트 재구성을 검증한다.

실행: /home/daeyun/HRM_env/bin/python -m unittest discover -s tests -p test_models.py -v
"""
import unittest

import torch
from torch.nn import functional as F

from hrm_force.models import MODEL_NAMES, build_model, count_parameters


class ModelZooTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_threads = torch.get_num_threads()
        torch.set_num_threads(1)

    @classmethod
    def tearDownClass(cls):
        torch.set_num_threads(cls.original_threads)

    def test_all_models_forward_backward_and_task_shapes(self):
        for name in MODEL_NAMES:
            for task in ("tip", "body", "force_only"):
                with self.subTest(model=name, task=task):
                    torch.manual_seed(19)
                    model = build_model(name, 26, task=task, seq_len=8)
                    output = model(torch.randn(3, 8, 26))
                    self.assertEqual(output["force"].shape, (3, 3))
                    loss = F.mse_loss(output["force"], torch.randn(3, 3))
                    if task == "force_only":
                        self.assertEqual(set(output), {"force"})
                    else:
                        self.assertEqual(output["load_logit"].shape, (3,))
                        loss = loss + F.binary_cross_entropy_with_logits(
                            output["load_logit"], torch.tensor([0., 1., 0.]))
                    if task == "body":
                        self.assertEqual(output["location_logits"].shape, (3, 18))
                        loss = loss + F.cross_entropy(
                            output["location_logits"], torch.tensor([0, 8, 17]))
                    else:
                        self.assertNotIn("location_logits", output)
                    self.assertTrue(torch.isfinite(loss))
                    loss.backward()
                    for parameter in model.parameters():
                        self.assertIsNotNone(parameter.grad)
                        self.assertTrue(torch.isfinite(parameter.grad).all())
                    self.assertLess(count_parameters(model), 100_000)

    def test_feature_dimensions_and_single_sample_batch(self):
        for name in MODEL_NAMES:
            for feature_dim in (4, 8, 18, 22, 48):
                with self.subTest(model=name, features=feature_dim):
                    model = build_model(name, feature_dim, seq_len=1).eval()
                    with torch.no_grad():
                        output = model(torch.randn(1, 1, feature_dim))
                    self.assertEqual(output["force"].shape, (1, 3))
                    self.assertEqual(output["load_logit"].shape, (1,))

    def test_encoders_cannot_see_future_input(self):
        # 미래 suffix를 바꿔도 그 이전 모든 hidden feature는 같아야 한다.
        for name in MODEL_NAMES:
            with self.subTest(model=name):
                torch.manual_seed(42)
                model = build_model(name, 4, seq_len=12).eval()
                original = torch.randn(2, 12, 4)
                modified = original.clone()
                modified[:, 7:, :] = torch.randn(2, 5, 4) * 100
                with torch.no_grad():
                    first = model.encode_sequence(original)[:, :7]
                    second = model.encode_sequence(modified)[:, :7]
                torch.testing.assert_close(first, second, atol=1e-5, rtol=1e-5)

    def test_mlp_uses_only_last_input(self):
        model = build_model("mlp", 4).eval()
        original = torch.randn(2, 30, 4)
        modified = original.clone()
        modified[:, :-1] = 1000
        with torch.no_grad():
            a, b = model(original), model(modified)
        for key in a:
            torch.testing.assert_close(a[key], b[key], atol=0, rtol=0)

    def test_temporal_models_use_history(self):
        for name in MODEL_NAMES:
            if name == "mlp":
                continue
            with self.subTest(model=name):
                torch.manual_seed(31)
                model = build_model(name, 4, seq_len=12).eval()
                original = torch.randn(2, 12, 4)
                modified = original.clone()
                modified[:, :-1] += torch.randn(2, 11, 4) * 5
                with torch.no_grad():
                    a, b = model(original)["force"], model(modified)["force"]
                self.assertGreater(torch.max(torch.abs(a - b)).item(), 1e-7)

    def test_tcn_receptive_fields(self):
        for name, receptive_field in (("tcn", 15), ("residual_tcn", 29)):
            with self.subTest(model=name):
                torch.manual_seed(12)
                model = build_model(name, 4, seq_len=40).eval()
                original = torch.randn(2, 40, 4)
                modified = original.clone()
                modified[:, :-receptive_field] = 1000
                with torch.no_grad():
                    a, b = model(original)["force"], model(modified)["force"]
                torch.testing.assert_close(a, b, atol=1e-6, rtol=1e-6)

    def test_state_dict_restores_predictions(self):
        for name in MODEL_NAMES:
            with self.subTest(model=name):
                model = build_model(name, 8, task="body", seq_len=5).eval()
                restored = build_model(name, 8, task="body", seq_len=5).eval()
                restored.load_state_dict(model.state_dict())
                x = torch.randn(2, 5, 8)
                with torch.no_grad():
                    expected, actual = model(x), restored(x)
                for key in expected:
                    torch.testing.assert_close(expected[key], actual[key], atol=0, rtol=0)

    def test_force_output_preserves_signed_values(self):
        model = build_model("mlp", 4, task="force_only")
        with torch.no_grad():
            model.force_head.weight.zero_()
            model.force_head.bias.copy_(torch.tensor([-1., 0., 1.]))
            output = model(torch.zeros(1, 3, 4))["force"]
        torch.testing.assert_close(output, torch.tensor([[-1., 0., 1.]]))

    def test_invalid_configuration_and_inputs_raise(self):
        for kwargs in ({"name": "unknown", "input_dim": 4},
                       {"name": "mlp", "input_dim": 0},
                       {"name": "mlp", "input_dim": 4, "seq_len": 0},
                       {"name": "mlp", "input_dim": 4, "task": "unknown"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                build_model(**kwargs)
        model = build_model("mlp", 4)
        for x in (torch.zeros(3, 4), torch.zeros(2, 3, 5), torch.zeros(2, 0, 4)):
            with self.subTest(shape=x.shape), self.assertRaises(ValueError):
                model(x)
        with self.assertRaises(ValueError):
            build_model("transformer", 4, seq_len=3)(torch.zeros(2, 4, 4))


if __name__ == "__main__":
    unittest.main()
