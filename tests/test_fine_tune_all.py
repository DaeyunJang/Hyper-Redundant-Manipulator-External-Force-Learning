"""All-model warm-start preserves holdout order and exports external baselines."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import numpy as np
import pandas as pd
import torch

from hrm_force.data import sha256
from hrm_force.engine import train_model
from hrm_force.evaluation import evaluate_predictions
from scripts import fine_tune_all as runner


class FineTuneAllTests(unittest.TestCase):
    def test_training_selection_precedes_test_and_parents_stay_original(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cfg = {'task': 'tip', 'seed': 42, 'threads': 1, 'force_source': 'kalman',
                   'source_force_unit': 'mN', 'window_samples': 3,
                   'thresholds_N': [.0454, .0436, .0729], 'threshold_policy': 'test',
                   'validation_purge_seconds': .1, 'batch_size': 16,
                   'learning_rate': .001, 'weight_decay': 0., 'max_epochs': 1,
                   'patience': 2, 'load_loss_weight': .2, 'location_loss_weight': .5,
                   'sessions': ['new_train', 'new_test'], 'test_sessions': ['new_test']}
            rng = np.random.default_rng(1)
            sessions = []
            for sid in ('new_train', 'new_test'):
                source = root / sid / 'csv' / 'summary.csv'
                source.parent.mkdir(parents=True)
                source.write_text(sid)
                x = rng.normal(size=(50, 4)).astype(np.float32)
                sessions.append({'x': x, 'y': x[:, :3] * .1,
                    'ts': np.arange(50, dtype=np.int64) * 1_000_000_000,
                    'columns': ['a', 'b', 'c', 'd'], 'id': 18, 'source_id': 18,
                    'info': {'session_id': sid, 'folder': sid, 'sha256': sha256(source),
                             'path': str(source), 'metadata_sha256': {}}})
            indices = {'train': np.array([(0, i) for i in range(2, 21)]),
                       'val': np.array([(0, i) for i in range(35, 45)]),
                       'test': np.array([(1, i) for i in range(2, 21)])}
            scaler = {'x_mean': np.zeros(4), 'x_std': np.ones(4),
                      'y_mean': np.zeros(3), 'y_std': np.ones(3)}
            old_sessions = copy.deepcopy(sessions)
            for session in old_sessions:
                session['info']['session_id'] = 'old_' + session['info']['session_id']
                session['info']['sha256'] = 'old_' + session['info']['sha256']
            parents = root / 'parents'
            config = root / 'config.json'
            config.write_text(json.dumps(cfg))
            out = root / 'new_run'
            names = ('mlp', 'gru')
            with contextlib.redirect_stdout(io.StringIO()):
                for name in names:
                    train_model(name, copy.deepcopy(old_sessions), indices, scaler, cfg,
                                parents / name, torch.device('cpu'))
            original = {name: sha256(parents / name / 'checkpoint.pt') for name in names}
            completed = []
            train_main = runner.train_cli.main
            predict = runner.predict_model

            def train_and_record(args):
                result = train_main(args)
                completed.append(args[args.index('--models') + 1])
                return result

            def assert_order(bundle, data, ix, **kwargs):
                self.assertEqual(completed, list(names))
                self.assertTrue((out / 'selection.json').is_file())
                return predict(bundle, data, ix, **kwargs)

            with mock.patch.object(runner, 'MODEL_NAMES', names), \
                 mock.patch.object(runner, 'prepare', return_value=(sessions, indices, scaler)), \
                 mock.patch.object(runner.train_cli, 'prepare', return_value=(sessions, indices, scaler)), \
                 mock.patch.object(runner.train_cli, 'main', side_effect=train_and_record), \
                 mock.patch.object(runner.train_cli.subprocess, 'check_output', return_value='test\n'), \
                 mock.patch.object(runner, 'predict_model', side_effect=assert_order), \
                 mock.patch.object(runner, 'save_evaluation', side_effect=lambda df, path, task: evaluate_predictions(df)), \
                 contextlib.redirect_stdout(io.StringIO()):
                runner.run(config, parents, out, 'cpu')
            self.assertEqual(json.loads((out / 'verification.json').read_text())['status'], 'passed')
            self.assertEqual(len(pd.read_csv(out / 'before_after_comparison.csv')), 2)
            for name in names:
                self.assertEqual(sha256(parents / name / 'checkpoint.pt'), original[name])
                baseline = out / 'baseline' / name / 'test_predictions'
                info = json.loads((baseline / 'evaluation_provenance.json').read_text())
                self.assertEqual(info['evaluation_kind'], 'external_new_recordings')
                self.assertTrue(all(sid.startswith('old_') for sid in info['checkpoint_original_source_hashes']))
                self.assertEqual(set(info['evaluation_source_hashes']), {'new_train', 'new_test'})
                before = pd.read_csv(baseline / 'predictions.csv')
                after = pd.read_csv(out / 'runs' / name / name / 'test_predictions' / 'predictions.csv')
                pd.testing.assert_frame_equal(before[runner.IDENTITY_COLUMNS], after[runner.IDENTITY_COLUMNS])
            with self.assertRaises(FileExistsError):
                runner.run(config, parents, out, 'cpu')

    def test_changed_audited_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'summary.csv'
            path.write_text('before')
            files = {str(path): sha256(path)}
            runner.check_hashes(files)
            path.write_text('after')
            with self.assertRaisesRegex(ValueError, 'changed'):
                runner.check_hashes(files)

    def test_renamed_prior_test_cannot_become_training(self):
        bundle = {'source_hashes': {'old-test': 'same-data'},
                  'source_session_roles': {'old-test': {'sha256': 'same-data', 'roles': ['test']}}}
        sessions = [{'info': {'session_id': 'renamed-test', 'sha256': 'same-data'}},
                    {'info': {'session_id': 'new-test', 'sha256': 'new-data'}}]
        roles = {'train': {'renamed-test'}, 'val': {'renamed-test'}, 'test': {'new-test'}}
        with self.assertRaisesRegex(ValueError, 'prior held-out'):
            runner.check_parent_holdout(bundle, Path('unused.pt'), roles, sessions)


if __name__ == '__main__':
    unittest.main()
