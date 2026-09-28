"""Separate test trees retain frozen inference and reject training leakage."""
import copy
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
import torch

import predict
from hrm_force import folder_prediction as fp
from hrm_force.data import feature_spec, sha256
from hrm_force.evaluation import evaluate_predictions


class FolderPredictionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.test_root = self.root / 'testsets'
        self.config = {
            'task': 'tip', 'feature_groups': ['wire_length', 'loadcell_tension', 'relative_angle'],
            'force_source': 'kalman', 'source_force_unit': 'mN', 'window_samples': 3,
            'gap_factor': 1.5, 'max_matching_skew_ms': 25., 'label_overrides': {},
            'thresholds_N': [.0454, .0436, .0729], 'seed': 42,
        }
        self.columns = feature_spec(self.config['feature_groups'])[0]
        self.bundle = {
            'config': self.config, 'model': 'mlp', 'feature_columns': self.columns,
            'scaler': {'x_mean': [0.] * 26, 'x_std': [1.] * 26,
                       'y_mean': [0.] * 3, 'y_std': [1.] * 3},
            'stats': {'validation_loss': .25},
            'source_hashes': {'old-train': 'train-hash', 'old-test': 'test-hash'},
            'source_session_roles': {
                'old-train': {'roles': ['train', 'val'], 'sha256': 'train-hash'},
                'old-test': {'roles': ['test'], 'sha256': 'test-hash'}},
            'seen_training_validation_session_ids': ['old-train', 'ancestor-train'],
        }

    def fixture(self, name='seg-id-18_new', sid='new-session', contact_id=18, offset=0.):
        folder = self.test_root / name
        (folder / 'csv').mkdir(parents=True)
        features, flags, _ = feature_spec(self.config['feature_groups'])
        header = features + flags + [
            'wire.time_difference_ms', 'loadcell.time_difference_ms',
            'fts_kalman.aligned_fx', 'fts_kalman.aligned_fy', 'fts_kalman.aligned_fz',
            'fts_kalman.matched', 'fts_kalman.aligned_force_valid',
            'fts_kalman.time_difference_ms', 'fts_kalman.aligned_frame_id',
            'source_time_ns', 'contact_segment_id']
        with (folder / 'csv/summary.csv').open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=header)
            writer.writeheader()
            for index in range(8):
                row = dict.fromkeys(header, '0')
                row.update({column: str(offset + index + i) for i, column in enumerate(features)})
                row.update({column: 'True' for column in flags})
                row.update({'fts_kalman.matched': 'True', 'fts_kalman.aligned_force_valid': 'True',
                            'fts_kalman.aligned_frame_id': 'hrm_base',
                            'fts_kalman.aligned_fx': '100', 'fts_kalman.aligned_fz': '-200',
                            'source_time_ns': str(1_000_000_000 + index * 100_000_000),
                            'contact_segment_id': str(contact_id)})
                writer.writerow(row)
        alignment = {'enabled': True, 'target_frame': 'hrm_base', 'axes': ['x', 'y', 'z'],
                     'matrix_base_from_sensor': [[1, 0, 0], [0, 1, 0], [0, 0, 1]]}
        files = {
            'session.json': {'session_id': sid, 'snapshot': {
                'contact_segment_id': contact_id, 'force_alignment': alignment}},
            'recording_config.json': {'notes': {'source_units': {'fts_force': 'mN'}}},
            'csv/manifest.json': {'status': 'complete', 'force_alignment': alignment},
            'csv/summary.schema.json': {'status': 'complete', 'columns': header, 'rows_written': 8},
        }
        for filename, value in files.items():
            (folder / filename).write_text(json.dumps(value))
        return folder

    def checkpoint(self, name='mlp', bundle=None):
        checkpoint = self.root / 'run' / name / 'checkpoint.pt'
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        value = copy.deepcopy(self.bundle if bundle is None else bundle)
        value['model'] = name
        torch.save(value, checkpoint)
        return checkpoint

    @staticmethod
    def fake_predict(bundle, sessions, indices, device='cpu'):
        rows = []
        for sid, row in indices:
            session = sessions[sid]
            item = {'session_id': session['info']['session_id'], 'source_row': row,
                    'source_time_ns': session['ts'][row], 'source_folder': session['info']['folder'],
                    'true_id': session['id'], 'conditional_pred_id': session['id'],
                    'pred_id': session['id'], 'true_load': 1, 'pred_load': 1}
            for axis, value in zip('xyz', session['y'][row]):
                item[f'true_f{axis}_N'] = value
                item[f'pred_f{axis}_N'] = value + .01
            rows.append(item)
        return pd.DataFrame(rows), object()

    def predict(self, checkpoints, output=None):
        with patch.object(fp, 'predict_model', side_effect=self.fake_predict), \
                patch.object(fp, 'save_evaluation', side_effect=lambda frame, out, task: evaluate_predictions(frame)):
            return fp.run_folder_prediction(checkpoints, self.test_root,
                                            output or self.root / 'evaluation')

    def test_multiple_sessions_and_models_preserve_frozen_checkpoint_and_unique_output(self):
        first = self.fixture()
        self.fixture('day2/seg-id-18_second', 'second-session', offset=2.)
        checkpoints = [self.checkpoint(), self.checkpoint('gru')]
        before = {path: sha256(path) for path in checkpoints + list(first.rglob('*')) if path.is_file()}
        rows = self.predict(checkpoints)
        self.assertEqual([row['model'] for row in rows], ['mlp', 'gru'])
        output = self.root / 'evaluation'
        frame = pd.read_csv(output / 'mlp/predictions.csv')
        self.assertEqual(len(frame), 12)
        self.assertEqual(set(frame.session_id), {'new-session', 'second-session'})
        summary = json.loads((output / 'mlp/summary.json').read_text())
        self.assertEqual(summary['training_statistics'], {'validation_loss': .25})
        self.assertAlmostEqual(summary['test_metrics']['force_rmse_N'], .01, places=6)
        self.assertEqual(json.loads((output / 'evaluation_config.json').read_text())['status'], 'complete')
        self.assertEqual(before, {path: sha256(path) for path in before})
        with self.assertRaises(FileExistsError):
            self.predict(checkpoints)

    def test_train_id_history_and_copied_train_hash_are_rejected(self):
        folder = self.fixture(sid='ancestor-train')
        checkpoint = self.checkpoint()
        with self.assertRaisesRegex(ValueError, 'previously used'):
            self.predict([checkpoint])
        meta = json.loads((folder / 'session.json').read_text())
        meta['session_id'] = 'new-session'
        (folder / 'session.json').write_text(json.dumps(meta))
        bundle = copy.deepcopy(self.bundle)
        digest = sha256(folder / 'csv/summary.csv')
        bundle['source_hashes']['old-train'] = digest
        bundle['source_session_roles']['old-train']['sha256'] = digest
        with self.assertRaisesRegex(ValueError, 'hash matches prior'):
            self.predict([self.checkpoint(bundle=bundle)])
        inherited = copy.deepcopy(self.bundle)
        inherited['seen_training_validation_hashes'] = [digest]
        with self.assertRaisesRegex(ValueError, 'hash matches prior'):
            self.predict([self.checkpoint(bundle=inherited)])
        self.assertFalse((self.root / 'evaluation').exists())

    def test_heldout_test_can_be_reevaluated_but_changed_bytes_are_rejected(self):
        folder = self.fixture(sid='old-test')
        bundle = copy.deepcopy(self.bundle)
        digest = sha256(folder / 'csv/summary.csv')
        bundle['source_hashes']['old-test'] = digest
        bundle['source_session_roles']['old-test']['sha256'] = digest
        checkpoint = self.checkpoint(bundle=bundle)
        self.predict([checkpoint])
        with (folder / 'csv/summary.csv').open('a') as stream:
            stream.write('\n')
        with self.assertRaisesRegex(ValueError, 'Known test session data changed'):
            self.predict([checkpoint], self.root / 'changed-evaluation')

    def test_relocated_repair_uses_source_hashes_instead_of_absolute_locator(self):
        folder = self.fixture(sid='old-test')
        bundle = copy.deepcopy(self.bundle)
        session = fp.load_session(folder, self.config)
        digest = session['info']['sha256']
        bundle['source_hashes']['old-test'] = digest
        bundle['source_session_roles']['old-test']['sha256'] = digest
        historical = {'metadata_sha256': session['info']['metadata_sha256'],
                      'timestamp_repair': {'original_angle_csv': '/old/angles.csv',
                                           'original_angle_sha256': 'angle-hash', 'repaired_rows': 8}}
        bundle['source_provenance'] = {'old-test': historical}
        session['info']['timestamp_repair'] = dict(historical['timestamp_repair'],
                                                 original_angle_csv='/new/angles.csv')
        checkpoint = self.checkpoint(bundle=bundle)
        with patch.object(fp, 'load_session', return_value=session):
            fp._prepare_test_sessions(bundle, checkpoint, [folder])
            session['info']['timestamp_repair']['original_angle_sha256'] = 'changed-angle-hash'
            with self.assertRaisesRegex(ValueError, 'metadata or repair source changed'):
                fp._prepare_test_sessions(bundle, checkpoint, [folder])

    def test_duplicate_test_session_and_duplicate_summary_are_rejected(self):
        self.fixture()
        self.fixture('seg-id-18_second', 'new-session', offset=2.)
        checkpoint = self.checkpoint()
        with self.assertRaisesRegex(ValueError, 'Duplicate physical test session'):
            self.predict([checkpoint])
        second = self.test_root / 'seg-id-18_second'
        meta = json.loads((second / 'session.json').read_text())
        meta['session_id'] = 'second-session'
        (second / 'session.json').write_text(json.dumps(meta))
        (second / 'csv/summary.csv').write_bytes((self.test_root / 'seg-id-18_new/csv/summary.csv').read_bytes())
        with self.assertRaisesRegex(ValueError, 'Duplicate test summary'):
            self.predict([checkpoint])

    def test_tip_checkpoint_rejects_body_contact(self):
        self.fixture('seg-id-9_body', contact_id=9)
        with self.assertRaisesRegex(ValueError, 'only ID18'):
            self.predict([self.checkpoint()])

    def test_duplicate_model_names_are_rejected(self):
        self.fixture()
        checkpoint = self.checkpoint()
        with self.assertRaisesRegex(ValueError, 'Duplicate checkpoint model'):
            self.predict([checkpoint, checkpoint])

    def test_legacy_audit_is_required_and_verified(self):
        self.fixture()
        bundle = copy.deepcopy(self.bundle)
        del bundle['source_session_roles']
        checkpoint = self.checkpoint(bundle=bundle)
        with self.assertRaisesRegex(ValueError, 'missing dataset_audit'):
            self.predict([checkpoint])
        audit = [{'session_id': sid, 'sha256': digest,
                  'split_counts': {'train': int(sid == 'old-train'), 'val': int(sid == 'old-train'),
                                   'test': int(sid == 'old-test')}}
                 for sid, digest in bundle['source_hashes'].items()]
        (checkpoint.parent.parent / 'dataset_audit.json').write_text(json.dumps(audit))
        self.predict([checkpoint])
        provenance = json.loads((self.root / 'evaluation/mlp/evaluation_provenance.json').read_text())
        self.assertIsNotNone(provenance['legacy_role_audit'])

    def test_model_comparison_rejects_different_test_windows(self):
        self.fixture()
        first = self.checkpoint()
        bundle = copy.deepcopy(self.bundle)
        bundle['config']['window_samples'] = 4
        second = self.checkpoint('gru', bundle)
        with self.assertRaisesRegex(AssertionError, 'Common test identity'):
            self.predict([first, second])
        status = json.loads((self.root / 'evaluation/evaluation_config.json').read_text())['status']
        self.assertNotEqual(status, 'complete')

    def test_cli_rejects_ambiguous_dataset_options(self):
        base = ['predict.py', '--checkpoint', 'checkpoint.pt', '--test-root', 'testsets']
        for extra in ([], ['--output', 'out', '--split', 'train'],
                      ['--output', 'out', '--session', 'session'],
                      ['--output', 'out', '--data-root', 'old']):
            with self.subTest(extra=extra), patch('sys.argv', base + extra), \
                    patch('sys.stderr', new_callable=io.StringIO), self.assertRaises(SystemExit):
                predict.main()

    def test_cli_dispatches_checkpoint_and_run_to_new_output(self):
        checkpoint = self.checkpoint()
        output = self.root / 'evaluation'
        base = ['predict.py', '--test-root', str(self.test_root), '--output', str(output)]
        for selector in (['--checkpoint', str(checkpoint)], ['--run', str(checkpoint.parent.parent)]):
            with self.subTest(selector=selector), patch('sys.argv', base + selector), \
                    patch.object(fp, 'run_folder_prediction', return_value=[]) as run, \
                    patch('sys.stdout', new_callable=io.StringIO):
                predict.main()
                self.assertEqual(run.call_args.args, ([checkpoint], str(self.test_root), str(output), 'cpu'))
        with patch('sys.argv', ['predict.py', '--checkpoint', str(checkpoint), '--output', str(output)]), \
                patch('sys.stderr', new_callable=io.StringIO), self.assertRaises(SystemExit):
            predict.main()

    def test_empty_frozen_test_split_has_actionable_error(self):
        with patch.object(predict.torch, 'load', return_value=self.bundle), \
                patch.object(predict, 'prepare', return_value=([], {'test': np.empty((0, 2), dtype=int)}, {})):
            with self.assertRaisesRegex(ValueError, '--test-root'):
                predict.run_checkpoint('checkpoint.pt')


if __name__ == '__main__':
    unittest.main()
