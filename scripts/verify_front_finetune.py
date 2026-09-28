#!/usr/bin/env python3
"""Independently verify saved front fine-tuning artifacts without model inference.

Usage: python scripts/verify_front_finetune.py results/20260927_tip_front_finetune_v1
The runner's verification.json is preserved. This writes independent_verification.json.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch


MODEL_NAMES = ('mlp', 'cnn', 'convmixer', 'resnet', 'lstm', 'gru', 'tcn',
               'transformer', 'kalmannet', 'small_gru', 'residual_tcn')
IDENTITY = ['session_id', 'source_row', 'source_time_ns', 'true_id', 'true_load',
            'true_fx_N', 'true_fy_N', 'true_fz_N']


def read_json(path):
    return json.loads(Path(path).read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def equal_number(actual, expected, context, rtol=1e-9, atol=1e-12):
    require(np.isclose(actual, expected, rtol=rtol, atol=atol, equal_nan=True),
            f'{context}: {actual} != {expected}')


def verify_prediction(df, metrics, thresholds):
    """Recalculate force, load, display, and fixed-tip outputs independently."""
    truth = df[[f'true_f{axis}_N' for axis in 'xyz']].to_numpy(dtype=float)
    force = df[[f'pred_f{axis}_N' for axis in 'xyz']].to_numpy(dtype=float)
    require(np.isfinite(truth).all() and np.isfinite(force).all(), 'Nonfinite force')
    # Recover float32 targets before thresholding exact decimal boundary values.
    true_load = (np.abs(truth.astype(np.float32).astype(float)) > thresholds).any(axis=1)
    pred_load = (np.abs(force) > thresholds).any(axis=1)
    np.testing.assert_array_equal(true_load, df.true_load)
    np.testing.assert_array_equal(pred_load, df.pred_load)
    require((df.true_id == 18).all(), 'Unexpected test target ID')
    require((df.conditional_pred_id == 18).all(), 'Tip conditional ID must be18')
    np.testing.assert_array_equal(np.where(pred_load, 18, 0), df.pred_id)
    for i, axis in enumerate('xyz'):
        np.testing.assert_allclose(df[f'true_f{axis}_mN'], truth[:, i] * 1000,
                                   rtol=1e-6, atol=1e-5)
        np.testing.assert_allclose(df[f'pred_f{axis}_mN'], force[:, i] * 1000,
                                   rtol=1e-10, atol=1e-10)
        np.testing.assert_allclose(df[f'display_f{axis}_N'],
                                   np.where(pred_load, force[:, i], 0),
                                   rtol=1e-10, atol=1e-12)
    probability = df.load_probability.to_numpy(dtype=float)
    require(np.isfinite(probability).all() and ((0 <= probability) & (probability <= 1)).all(),
            'Invalid load head probability')
    np.testing.assert_array_equal(probability >= .5, df.load_head_pred)
    error = force - truth
    recalculated = {'n_samples': len(df), 'force_rmse_N': float(np.sqrt(np.mean(error ** 2)))}
    recalculated['force_rmse_mN'] = recalculated['force_rmse_N'] * 1000
    for i, axis in enumerate('xyz'):
        recalculated[f'f{axis}_rmse_N'] = float(np.sqrt(np.mean(error[:, i] ** 2)))
        recalculated[f'f{axis}_rmse_mN'] = recalculated[f'f{axis}_rmse_N'] * 1000
    counts = dict(tp=int(np.sum(true_load & pred_load)),
                  tn=int(np.sum(~true_load & ~pred_load)),
                  fp=int(np.sum(~true_load & pred_load)),
                  fn=int(np.sum(true_load & ~pred_load)))
    recalculated.update({f'load_{key}': value for key, value in counts.items()})
    tp, tn, fp, fn = (counts[key] for key in ('tp', 'tn', 'fp', 'fn'))
    recalculated['load_f1'] = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else np.nan
    recalculated['load_false_positive_rate'] = fp / (fp + tn) if fp + tn else np.nan
    recalculated['load_false_negative_rate'] = fn / (fn + tp) if fn + tp else np.nan
    for key, value in recalculated.items():
        equal_number(metrics[key], value, key, rtol=1e-6, atol=1e-9)
    return recalculated


def historical_roles(parent, parent_path):
    roles = parent.get('source_session_roles')
    if roles is None:
        audit = read_json(parent_path.parent.parent / 'dataset_audit.json')
        roles = {item['session_id']: {'sha256': item['sha256'], 'roles': [
            part for part, count in item['split_counts'].items() if count > 0]} for item in audit}
    require(set(roles) == set(parent['source_hashes']), 'Incomplete parent role history')
    for sid, role in roles.items():
        require(role['sha256'] == parent['source_hashes'][sid], 'Parent role hash mismatch')
        require(not ('test' in role['roles'] and set(role['roles']) & {'train', 'val'}),
                'Historical test mixed with training')
    seen = {sid for sid, role in roles.items() if set(role['roles']) & {'train', 'val'}}
    seen.update(parent.get('seen_training_validation_session_ids', []))
    held = {sid for sid, role in roles.items() if 'test' in role['roles']}
    held.update(parent.get('held_out_test_session_ids', []))
    return roles, seen, held


def verify(root, expected_test_rows=2572):
    root = Path(root).resolve()
    manifest = read_json(root / 'run_manifest.json')
    cfg = read_json(root / 'experiment_config.json')
    require(cfg['task'] == 'tip', 'Expected tip task')
    require(cfg['force_source'] == 'kalman' and cfg['source_force_unit'] == 'mN',
            'This verifier expects aligned Kalman force recorded in mN')
    require(set(manifest['models']) == set(MODEL_NAMES) and len(manifest['models']) == 11,
            'Expected11 distinct models')
    require(manifest['split_counts']['test'] == expected_test_rows, 'Unexpected test size')
    for path, expected in manifest['audited_file_sha256'].items():
        require(digest(path) == expected, f'Source/metadata/parent hash changed: {path}')
    independent_audit = root / 'audit' / 'dataset_audit.json'
    if independent_audit.exists():
        for item in read_json(independent_audit)['sessions']:
            for path, expected in item['source_hashes_sha256'].items():
                original = Path(path)
                if not original.is_absolute():
                    original = Path(__file__).resolve().parents[1] / original
                require(digest(original) == expected, f'Independent original-file hash changed: {path}')

    selection = read_json(root / 'selection.json')
    require(set(selection['all_models_trained']) == set(MODEL_NAMES), 'Incomplete selection pool')
    require(selection['test_predictions_generated'] is False, 'Selection was not frozen before test')
    require(selection['criterion'] == 'lowest_new_validation_combined_force_and_load_loss',
            'Unexpected selection criterion')
    selected_time = datetime.fromisoformat(selection['selected_at_utc'])
    references = {}
    reference_splits = None
    reference_audit = None
    raw_sources = {}
    reports = []
    child_hashes = {}
    all_losses = {}

    for name in manifest['models']:
        run = root / 'runs' / name
        folder = run / name
        parent_path = Path(manifest['parent_checkpoints'][name])
        parent_hash = manifest['parent_sha256'][name]
        require(digest(parent_path) == parent_hash, f'Parent checkpoint changed: {name}')
        parent = torch.load(parent_path, map_location='cpu', weights_only=True)
        child_path = folder / 'checkpoint.pt'
        child = torch.load(child_path, map_location='cpu', weights_only=True)
        child_hashes[name] = digest(child_path)
        require(parent['model'] == child['model'] == name, 'Model name mismatch')
        require(child['config'] == cfg == read_json(run / 'config.json'), 'Configuration mismatch')
        require(child['scaler'] == parent['scaler'] == read_json(run / 'scaler.json'),
                f'Parent normalization changed: {name}')
        require(child['feature_columns'] == parent['feature_columns'], 'Input order mismatch')
        for key, expected in [('force_unit', 'N'), ('force_frame', 'hrm_base'),
                              ('training_sign_multiplier', 1), ('future_hrm_control_multiplier', -1)]:
            require(child[key] == parent[key] == expected, f'Physical contract changed: {key}')
        for lineage in [child['warm_start'], read_json(run / 'warm_start.json')]:
            require(Path(lineage['parent_checkpoint']) == parent_path, 'Wrong parent lineage path')
            require(lineage['parent_sha256'] == parent_hash, 'Wrong parent lineage hash')
            require(lineage['scaler_policy'] == 'frozen_parent_x_and_y', 'Scaler policy changed')
        audit = read_json(run / 'dataset_audit.json')
        if reference_audit is None:
            reference_audit = audit
        else:
            require(reference_audit == audit, 'Dataset audits differ across models')
        sources = {item['session_id']: item for item in audit}
        require(len(sources) == 4, 'Expected three development recordings and one test recording')
        require(child['source_hashes'] == {sid: item['sha256'] for sid, item in sources.items()},
                'Child source hash mismatch')
        for sid, item in sources.items():
            require(item['training_id'] == 18, 'Non-tip training label')
            require(child['source_provenance'][sid] == {
                'metadata_sha256': item['metadata_sha256'], 'timestamp_repair': item.get('timestamp_repair')},
                'Child source metadata mismatch')
            if sid not in raw_sources:
                raw_sources[sid] = pd.read_csv(item['path'], dtype={'source_time_ns': str})
        splits = pd.read_csv(run / 'split_manifest.csv', dtype={'source_time_ns': str})
        if reference_splits is None:
            reference_splits = splits
        else:
            pd.testing.assert_frame_equal(splits, reference_splits, check_exact=True)
        require(not splits.duplicated(['session_id', 'source_row']).any(), 'Duplicate split endpoints')
        roles = {part: set(splits.loc[splits.split == part, 'session_id']) for part in ('train', 'val', 'test')}
        seen = roles['train'] | roles['val']
        require(not seen & roles['test'], 'Test recording in training or validation')
        require(roles['test'] == {sid for sid, item in sources.items() if item['folder'] in cfg['test_sessions']},
                'Test recording differs from explicit test configuration')
        require(len(seen) == 3 and len(roles['test']) == 1, 'Unexpected session roles')
        for part, ids in roles.items():
            require(len(splits.loc[splits.split == part]) == manifest['split_counts'][part],
                    f'Split count mismatch: {part}')
            require(ids == {sid for sid, role in child['source_session_roles'].items() if part in role['roles']},
                    'Checkpoint role and manifest mismatch')
        for sid in seen:
            tr = splits.loc[(splits.session_id == sid) & (splits.split == 'train')]
            va = splits.loc[(splits.session_id == sid) & (splits.split == 'val')]
            last_train = int(tr.source_row.max())
            first_val_input = int(va.source_row.min()) - cfg['window_samples'] + 1
            require(first_val_input > last_train, 'Overlapping train/validation input windows')
            times = raw_sources[sid].source_time_ns
            distance = int(Decimal(times.iloc[first_val_input])) - int(Decimal(times.iloc[last_train]))
            require(distance > 2 * cfg['validation_purge_seconds'] * 1e9, 'Validation purge missing')
        prior_roles, prior_seen, prior_test = historical_roles(parent, parent_path)
        require(not roles['test'] & prior_seen and not seen & prior_test, 'Historical holdout violated')
        require(set(child['seen_training_validation_session_ids']) == seen | prior_seen,
                'Training/validation history lost')
        require(set(child['held_out_test_session_ids']) == roles['test'] | prior_test,
                'Test role history lost')
        for sid in roles['test']:
            require(sources[sid]['sha256'] not in {value['sha256'] for key, value in prior_roles.items() if key in prior_seen},
                    'Current test content previously used for training')
        for sid in seen:
            require(sources[sid]['sha256'] not in {value['sha256'] for key, value in prior_roles.items() if key in prior_test},
                    'Current train content was a historical heldout recording')

        history = pd.read_csv(folder / 'history.csv')
        np.testing.assert_array_equal(history.epoch, np.arange(cfg['max_epochs'] + 1))
        require(np.isfinite(history.val_loss).all() and np.isfinite(history.train_loss.iloc[1:]).all(),
                'Nonfinite training or validation history')
        require(np.isnan(history.train_loss.iloc[0]), 'Epoch0 must be evaluation only')
        best_epoch, best_loss = 0, float(history.val_loss.iloc[0])
        for epoch, value in enumerate(history.val_loss.iloc[1:], start=1):
            if value < best_loss - 1e-6:
                best_epoch, best_loss = epoch, float(value)
        stats = child['stats']
        require(stats['epochs_run'] == cfg['max_epochs'] and stats['best_epoch'] == best_epoch,
                'Training epoch count or best checkpoint epoch mismatch')
        equal_number(stats['validation_loss'], best_loss, 'Best validation loss')
        equal_number(stats['initial_validation_loss'], history.val_loss.iloc[0], 'Epoch0 validation loss')
        require(stats == read_json(folder / 'training_summary.json'), 'Training summary mismatch')
        require(set(parent['state_dict']) == set(child['state_dict']), 'Architecture state keys changed')
        weights_changed = any(not torch.equal(parent['state_dict'][key], child['state_dict'][key])
                              for key in parent['state_dict'])
        require(weights_changed == (best_epoch > 0), 'Saved weights do not match epoch0/new-best status')
        all_losses[name] = best_loss
        report = {'model': name, 'epochs_run': stats['epochs_run'], 'best_epoch': best_epoch,
                  'validation_loss': best_loss, 'weights_changed': weights_changed, 'parent_sha256': parent_hash,
                  'child_sha256': child_hashes[name], 'predictions': {}}

        for split in ('val', 'test'):
            endpoints = splits.loc[splits.split == split, ['session_id', 'source_row', 'source_time_ns']].reset_index(drop=True)
            for stage, base, checkpoint in [('before', root / 'baseline' / name, parent_path),
                                             ('after', folder, child_path)]:
                destination = base / f'{split}_predictions'
                df = pd.read_csv(destination / 'predictions.csv', dtype={'source_time_ns': str})
                require(len(df) == manifest['split_counts'][split], 'Prediction count mismatch')
                pd.testing.assert_frame_equal(df[endpoints.columns], endpoints, check_exact=True)
                if split not in references:
                    references[split] = df[IDENTITY]
                    for sid, group in df.groupby('session_id', sort=False):
                        source = raw_sources[sid]
                        columns = [f'fts_kalman.aligned_f{axis}' for axis in 'xyz']
                        target = (source.iloc[group.source_row.to_numpy()][columns].to_numpy(dtype=float) * .001).astype(np.float32)
                        np.testing.assert_allclose(group[[f'true_f{axis}_N' for axis in 'xyz']], target,
                                                   rtol=1e-6, atol=1e-8)
                        original_times = [str(int(Decimal(value))) for value in source.iloc[
                            group.source_row.to_numpy()].source_time_ns]
                        np.testing.assert_array_equal(group.source_time_ns, original_times)
                else:
                    pd.testing.assert_frame_equal(df[IDENTITY], references[split], check_exact=True)
                metrics = verify_prediction(df, read_json(destination / 'metrics.json'), np.asarray(cfg['thresholds_N']))
                provenance = read_json(destination / 'evaluation_provenance.json')
                require(provenance['checkpoint_sha256'] == digest(checkpoint), 'Prediction checkpoint hash mismatch')
                require(Path(provenance['checkpoint']) == checkpoint, 'Prediction checkpoint path mismatch')
                require(datetime.fromisoformat(provenance['evaluated_at_utc']) >= selected_time,
                        'Evaluation predates validation selection')
                report['predictions'][f'{stage}_{split}'] = metrics
        reports.append(report)

    minimum = min(all_losses.values())
    require(selection['model'] in all_losses, 'Unknown selected model')
    equal_number(all_losses[selection['model']], minimum, 'Selected model was not validation minimum')
    equal_number(selection['validation_loss'], minimum, 'Selection loss mismatch')
    training_comparison = pd.read_csv(root / 'training_comparison.csv')
    require(len(training_comparison) == 11 and set(training_comparison.model) == set(MODEL_NAMES),
            'Incomplete training comparison')
    for row in training_comparison.itertuples():
        equal_number(row.validation_loss, all_losses[row.model], 'Training comparison validation loss')
    runner = read_json(root / 'verification.json')
    require(runner['status'] == 'passed' and runner['child_checkpoint_sha256'] == child_hashes,
            'Runner verification incomplete or checkpoint changed after evaluation')
    result = {'status': 'passed', 'verified_at_utc': datetime.now(timezone.utc).isoformat(),
              'models_checked': 11, 'prediction_files_checked': 44,
              'test_rows_per_prediction': expected_test_rows, 'split_counts': manifest['split_counts'],
              'selected_model': selection['model'], 'models': reports,
              'checks': ['original_csv_metadata_and_angle_hashes_unchanged', 'all_parent_checkpoints_unchanged',
                         'parent_scalers_frozen', 'full_epochs_plus_evaluation_only_epoch0',
                         'best_epoch_matches_saved_validation_history', 'purged_nonoverlapping_input_windows',
                         'test_excluded_from_current_and_historical_training', 'historical_holdouts_preserved',
                         'identical_validation_and_test_identities_and_targets_all_models_and_stages',
                         'prediction_targets_match_original_csv', 'finite_predictions',
                         'load_threshold_display_id18_and_unit_rules', 'force_and_load_metrics_recomputed',
                         'validation_minimum_selection_precedes_evaluation', 'runner_verification_preserved']}
    (root / 'independent_verification.json').write_text(json.dumps(result, indent=2, allow_nan=True) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--expected-test-rows', type=int, default=2572)
    args = parser.parse_args()
    result = verify(args.run, args.expected_test_rows)
    print(json.dumps({key: result[key] for key in ('status', 'models_checked', 'prediction_files_checked',
                                                 'test_rows_per_prediction', 'selected_model')}))


if __name__ == '__main__':
    main()
