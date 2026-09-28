#!/usr/bin/env python3
"""Warm-start all existing tip models, then compare on a new held-out test.

Training reuses train.py with a separate run directory per model. Parent weights,
normalization and physical contracts stay unchanged. All training and validation
selection finish before any test prediction is generated. Parent evaluation on
new data is explicitly external evaluation; historical source hashes are never
replaced to make a checkpoint appear trained on the new recordings.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import train as train_cli
from hrm_force.data import json_write, prepare, sha256
from hrm_force.engine import predict_model
from hrm_force.evaluation import save_evaluation
from hrm_force.models import MODEL_NAMES


IDENTITY_COLUMNS = ['session_id', 'source_row', 'source_time_ns', 'true_id',
                    'true_load', 'true_fx_N', 'true_fy_N', 'true_fz_N']
CONTRACT_REQUIRED = ('task', 'force_source', 'source_force_unit', 'window_samples',
                     'thresholds_N')
CONTRACT_OPTIONAL = ('threshold_policy', 'load_threshold_source', 'thresholds_source',
                     'calibration_file', 'calibration_hash', 'baseline_N',
                     'target_offset_N', 'max_matching_skew_ms', 'gap_factor')
PHYSICAL_CONTRACT = {'force_frame': 'hrm_base', 'force_unit': 'N',
                     'training_sign_multiplier': 1, 'future_hrm_control_multiplier': -1}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def model_device(name, requested='auto'):
    if requested == 'cpu' or name in ('tcn', 'residual_tcn'):
        return 'cpu'
    return 'cuda' if torch.cuda.is_available() else 'cpu'


def source_files(sessions):
    """Snapshot every file used by the audited loader, including repair inputs."""
    files = {}
    for session in sessions:
        info = session['info']
        summary = Path(info['path'])
        files[str(summary)] = info['sha256']
        for filename, digest in info['metadata_sha256'].items():
            base = summary.parent if filename in ('manifest.json', 'summary.schema.json') else summary.parent.parent
            files[str(base / filename)] = digest
        repair = info.get('timestamp_repair')
        if repair:
            files[str(repair['original_angle_csv'])] = repair['original_angle_sha256']
    return files


def check_hashes(files):
    for path, expected in files.items():
        if sha256(path) != expected:
            raise ValueError(f'Source or checkpoint changed: {path}')


def source_provenance(sessions):
    return {s['info']['session_id']: {
        'metadata_sha256': s['info']['metadata_sha256'],
        'timestamp_repair': s['info'].get('timestamp_repair')}
        for s in sessions}


def check_contract(bundle, cfg, sessions, name):
    if bundle['model'] != name:
        raise ValueError(f'Checkpoint model mismatch: {name}')
    for key in CONTRACT_REQUIRED:
        if key not in bundle['config'] or key not in cfg or bundle['config'][key] != cfg[key]:
            raise ValueError(f'Incompatible checkpoint {key}: {name}')
    for key in CONTRACT_OPTIONAL:
        if bundle['config'].get(key) != cfg.get(key):
            raise ValueError(f'Incompatible checkpoint {key}: {name}')
    for key, expected in PHYSICAL_CONTRACT.items():
        if (bundle.get(key) != expected or cfg.get(key, expected) != expected
                or bundle['config'].get(key, expected) != expected):
            raise ValueError(f'Incompatible physical contract {key}: {name}')
    if any(s['columns'] != bundle['feature_columns'] for s in sessions):
        raise ValueError(f'Input column order mismatch: {name}')
    for key, size in (('x_mean', len(bundle['feature_columns'])),
                      ('x_std', len(bundle['feature_columns'])), ('y_mean', 3), ('y_std', 3)):
        value = np.asarray(bundle['scaler'][key], dtype=np.float64)
        if value.shape != (size,) or not np.isfinite(value).all():
            raise ValueError(f'Invalid parent scaler {key}: {name}')
        if key.endswith('_std') and np.any(value <= 0):
            raise ValueError(f'Nonpositive parent scaler {key}: {name}')


def check_splits(sessions, indices, cfg):
    """Verify recording holdout and disjoint, time-purged input windows."""
    ids = [s['info']['session_id'] for s in sessions]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate physical session')
    roles = {part: {ids[int(index)] for index in indices[part][:, 0]}
             for part in ('train', 'val', 'test')}
    if roles['test'] & (roles['train'] | roles['val']):
        raise ValueError('Test recording overlaps train/validation')
    declared = {s['info']['session_id'] for s in sessions
                if s['info']['folder'] in cfg['test_sessions']}
    if declared != roles['test']:
        raise ValueError('Test recordings differ from explicit configuration')
    window = cfg['window_samples']
    guard = int(cfg['validation_purge_seconds'] * 1e9)
    for index, session in enumerate(sessions):
        tr = indices['train'][indices['train'][:, 0] == index, 1]
        va = indices['val'][indices['val'][:, 0] == index, 1]
        if len(tr) and len(va):
            last_train = int(tr.max())
            first_val_input = int(va.min()) - window + 1
            if last_train >= first_val_input:
                raise ValueError('Training and validation input windows overlap')
            if int(session['ts'][first_val_input]) - int(session['ts'][last_train]) <= 2 * guard:
                raise ValueError('Validation purge was not preserved')
    return roles


def parent_roles(bundle, path):
    """Read legacy role audit without accessing any historical raw dataset."""
    roles = bundle.get('source_session_roles')
    audit_file = None
    if roles is None:
        audit_file = path.parent.parent / 'dataset_audit.json'
        audit = json.loads(audit_file.read_text())
        roles = {}
        for item in audit:
            sid = item['session_id']
            counts = item['split_counts']
            if sid in roles or any(part not in counts for part in ('train', 'val', 'test')):
                raise ValueError('Ambiguous parent session role audit')
            roles[sid] = {'sha256': item['sha256'],
                          'roles': [part for part in ('train', 'val', 'test') if counts[part] > 0]}
    if set(roles) != set(bundle['source_hashes']):
        raise ValueError('Incomplete parent session roles')
    for sid, value in roles.items():
        if value['sha256'] != bundle['source_hashes'][sid]:
            raise ValueError('Parent role/source hash mismatch')
        if set(value['roles']) - {'train', 'val', 'test'}:
            raise ValueError('Unknown parent session role')
        if 'test' in value['roles'] and set(value['roles']) & {'train', 'val'}:
            raise ValueError('Parent session mixes training and test')
    return roles, audit_file


def check_parent_holdout(bundle, path, roles, sessions):
    previous, audit_file = parent_roles(bundle, path)
    seen = {sid for sid, info in previous.items() if set(info['roles']) & {'train', 'val'}}
    seen.update(bundle.get('seen_training_validation_session_ids', []))
    heldout = {sid for sid, info in previous.items() if 'test' in info['roles']}
    heldout.update(bundle.get('held_out_test_session_ids', []))
    current_seen = roles['train'] | roles['val']
    if roles['test'] & seen:
        raise ValueError('Current test was used for prior training/validation')
    if current_seen & heldout:
        raise ValueError('A prior held-out recording cannot become train/validation')
    hashes = {s['info']['session_id']: s['info']['sha256'] for s in sessions}
    seen_hashes = {value['sha256'] for sid, value in previous.items() if sid in seen}
    heldout_hashes = {value['sha256'] for sid, value in previous.items() if sid in heldout}
    if any(hashes[sid] in seen_hashes for sid in roles['test']):
        raise ValueError('Current test hash matches prior training/validation')
    if any(hashes[sid] in heldout_hashes for sid in current_seen):
        raise ValueError('Current training hash matches a prior held-out recording')
    return audit_file


def check_child(bundle, parent, path, parent_hash, sessions, roles):
    hashes = {s['info']['session_id']: s['info']['sha256'] for s in sessions}
    if bundle['source_hashes'] != hashes or bundle['source_provenance'] != source_provenance(sessions):
        raise ValueError('Child checkpoint dataset differs from evaluation data')
    if bundle['scaler'] != parent['scaler']:
        raise ValueError('Warm-start parent scaler changed')
    lineage = bundle['warm_start']
    if lineage['parent_sha256'] != parent_hash or Path(lineage['parent_checkpoint']) != path:
        raise ValueError('Child parent checkpoint lineage differs')
    child_roles = bundle['source_session_roles']
    for part in roles:
        actual = {sid for sid, value in child_roles.items() if part in value['roles']}
        if actual != roles[part]:
            raise ValueError('Child checkpoint split roles differ')
    seen = set(bundle['seen_training_validation_session_ids'])
    if roles['test'] & seen:
        raise ValueError('Child test recording was used for training/validation')
    if not roles['test'] <= set(bundle['held_out_test_session_ids']):
        raise ValueError('Child checkpoint lost held-out role history')


def save_predictions(bundle, sessions, ix, device, destination, reference, provenance):
    df, model = predict_model(bundle, sessions, ix, device=device)
    del model
    identity = df[IDENTITY_COLUMNS]
    if reference is not None:
        pd.testing.assert_frame_equal(identity, reference, check_exact=True)
    destination.mkdir(parents=True, exist_ok=False)
    df.to_csv(destination / 'predictions.csv', index=False)
    metrics = save_evaluation(df, destination, 'tip')
    # Re-read the exported artifact to check both calculation and CSV persistence.
    saved = pd.read_csv(destination / 'predictions.csv', dtype={'source_time_ns': str})
    error = (saved[[f'pred_f{a}_N' for a in 'xyz']].to_numpy()
             - saved[[f'true_f{a}_N' for a in 'xyz']].to_numpy())
    recomputed = float(np.sqrt(np.mean(error ** 2)))
    if not np.isfinite(error).all() or not np.isclose(recomputed, metrics['force_rmse_N'], rtol=1e-6, atol=1e-9):
        raise ValueError('Saved prediction RMSE verification failed')
    json_write(destination / 'evaluation_provenance.json', {
        **provenance, 'rows': len(df), 'recomputed_force_rmse_N': recomputed,
        'source_provenance': source_provenance(sessions),
        'scaler_policy': 'unchanged_checkpoint_scaler', 'evaluated_at_utc': utc_now()})
    return metrics, identity.copy()


def run(config_path, parents, output, device='auto'):
    config_path = Path(config_path).resolve(strict=True)
    parents = Path(parents).resolve(strict=True)
    root = Path(output).resolve()
    cfg = json.loads(config_path.read_text())
    if cfg['task'] != 'tip':
        raise ValueError('This experiment runner requires task=tip')
    if root.is_relative_to(parents) or parents.is_relative_to(root):
        raise ValueError('Output must be separate from parent checkpoints')
    reserved = ['runs', 'baseline', 'code_snapshot', 'selection.json', 'experiment_config.json',
                'run_manifest.json', 'training_comparison.csv', 'validation_comparison.csv',
                'test_comparison.csv', 'before_after_comparison.csv', 'verification.json']
    for name in reserved:
        if (root / name).exists():
            raise FileExistsError(f'Experiment output exists: {root / name}')
    model_names = list(MODEL_NAMES)
    checkpoints = {name: (parents / name / 'checkpoint.pt').resolve(strict=True) for name in model_names}
    sessions, indices, _ = prepare(cfg)
    if any(s['id'] != 18 for s in sessions):
        raise ValueError('Tip experiment requires ID18 in every selected recording')
    roles = check_splits(sessions, indices, cfg)
    files = source_files(sessions)
    files[str(config_path)] = sha256(config_path)
    parent_hashes = {}
    for name, path in checkpoints.items():
        bundle = torch.load(path, map_location='cpu', weights_only=True)
        check_contract(bundle, cfg, sessions, name)
        audit_file = check_parent_holdout(bundle, path, roles, sessions)
        parent_hashes[name] = sha256(path)
        files[str(path)] = parent_hashes[name]
        if audit_file:
            files[str(audit_file)] = sha256(audit_file)
    check_hashes(files)
    root.mkdir(parents=True, exist_ok=True)
    json_write(root / 'experiment_config.json', cfg)
    json_write(root / 'run_manifest.json', {
        'started_at_utc': utc_now(), 'models': model_names,
        'parent_checkpoints': {name: str(path) for name, path in checkpoints.items()},
        'parent_sha256': parent_hashes, 'audited_file_sha256': files,
        'data_policy': 'current_config_only_no_automatic_parent_replay',
        'test_policy': 'all_training_and_validation_selection_finish_before_test_predictions',
        'split_counts': {part: len(ix) for part, ix in indices.items()}})
    snapshot = root / 'code_snapshot'
    snapshot.mkdir()
    shutil.copy2(__file__, snapshot / Path(__file__).name)
    training = []
    for name in model_names:
        check_hashes(files)
        print(f'Warm-start {name} from {checkpoints[name]}', flush=True)
        train_cli.main(['--config', str(config_path), '--output', str(root / 'runs' / name),
                        '--models', name, '--device', model_device(name, device),
                        '--init-checkpoint', str(checkpoints[name])])
        child_dir = root / 'runs' / name / name
        training.append(json.loads((child_dir / 'training_summary.json').read_text()))
        pd.DataFrame(training).sort_values('validation_loss', kind='stable').to_csv(
            root / 'training_comparison.csv', index=False)
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    ranking = pd.DataFrame(training).sort_values('validation_loss', kind='stable')
    selected = ranking.iloc[0]
    json_write(root / 'selection.json', {
        'model': selected['model'], 'validation_loss': float(selected['validation_loss']),
        'criterion': 'lowest_new_validation_combined_force_and_load_loss',
        'all_models_trained': model_names, 'selected_at_utc': utc_now(),
        'test_predictions_generated': False,
        'note': 'Selection fixed before test. Same-session temporal validation is not independent-trial validation.'})
    check_hashes(files)
    eval_rows = {'val': [], 'test': []}
    references = {'val': None, 'test': None}
    before_after = []
    child_hashes = {}
    for name in model_names:
        parent_path = checkpoints[name]
        child_path = root / 'runs' / name / name / 'checkpoint.pt'
        parent = torch.load(parent_path, map_location='cpu', weights_only=True)
        child = torch.load(child_path, map_location='cpu', weights_only=True)
        check_contract(child, cfg, sessions, name)
        check_child(child, parent, parent_path, parent_hashes[name], sessions, roles)
        child_hashes[name] = sha256(child_path)
        metrics_by_stage = {}
        for split in ('val', 'test'):
            for stage, bundle, checkpoint in [('before', parent, parent_path), ('after', child, child_path)]:
                base = root / 'baseline' / name if stage == 'before' else child_path.parent
                print(f'Evaluating {split}/{stage}/{name}', flush=True)
                provenance = {
                    'evaluation_kind': 'external_new_recordings' if stage == 'before' else 'frozen_current_split',
                    'stage': stage, 'split': split, 'checkpoint': str(checkpoint),
                    'checkpoint_sha256': sha256(checkpoint),
                    'checkpoint_original_source_hashes': bundle['source_hashes'],
                    'evaluation_source_hashes': {s['info']['session_id']: s['info']['sha256'] for s in sessions},
                    'selection_file': str(root / 'selection.json')}
                metrics, references[split] = save_predictions(
                    bundle, sessions, indices[split], model_device(name, device),
                    base / f'{split}_predictions', references[split], provenance)
                row = {'model': name, 'stage': stage, 'split': split,
                       'selected_by_validation': name == selected['model'], **metrics,
                       'prediction_csv': str(base / f'{split}_predictions' / 'predictions.csv')}
                eval_rows[split].append(row)
                filename = 'validation_comparison.csv' if split == 'val' else 'test_comparison.csv'
                pd.DataFrame(eval_rows[split]).to_csv(root / filename, index=False)
                if split == 'test':
                    metrics_by_stage[stage] = metrics
        before, after = metrics_by_stage['before'], metrics_by_stage['after']
        row = {'model': name, 'selected_by_validation': name == selected['model'],
               'best_epoch': int(child['stats']['best_epoch']),
               'validation_loss_before': child['stats']['initial_validation_loss'],
               'validation_loss_after': child['stats']['validation_loss']}
        for metric in ('force_rmse_mN', 'fx_rmse_mN', 'fy_rmse_mN', 'fz_rmse_mN',
                       'load_f1', 'load_false_positive_rate', 'load_false_negative_rate'):
            row[f'before_{metric}'] = before[metric]
            row[f'after_{metric}'] = after[metric]
            row[f'delta_{metric}'] = after[metric] - before[metric]
        before_after.append(row)
        pd.DataFrame(before_after).to_csv(root / 'before_after_comparison.csv', index=False)
    check_hashes(files)
    for name, expected in child_hashes.items():
        if sha256(root / 'runs' / name / name / 'checkpoint.pt') != expected:
            raise ValueError(f'Checkpoint changed during evaluation: {name}')
    json_write(root / 'verification.json', {
        'status': 'passed', 'completed_at_utc': utc_now(), 'models_checked': len(model_names),
        'new_test_rows': len(indices['test']), 'validation_rows': len(indices['val']),
        'parent_checkpoint_sha256': parent_hashes, 'child_checkpoint_sha256': child_hashes,
        'checks': ['source_and_metadata_hashes_unchanged', 'parents_unchanged',
                   'fixed_parent_scalers', 'child_source_provenance_matches',
                   'historical_and_current_test_roles_preserved', 'purged_validation_input_windows',
                   'same_test_rows_targets_all_parent_and_child_models',
                   'same_validation_rows_targets_all_parent_and_child_models',
                   'recomputed_saved_force_rmse', 'validation_selection_saved_before_any_test_prediction']})
    print(f'Fine-tuning and evaluation complete: {root}', flush=True)
    return root


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--parents', required=True, help='Existing tip run containing model/checkpoint.pt')
    parser.add_argument('--output', required=True)
    parser.add_argument('--device', choices=['auto', 'cpu'], default='auto')
    args = parser.parse_args(argv)
    run(args.config, args.parents, args.output, args.device)


if __name__ == '__main__':
    main()
