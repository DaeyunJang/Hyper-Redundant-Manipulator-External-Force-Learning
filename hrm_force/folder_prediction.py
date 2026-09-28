"""Evaluate a frozen checkpoint on an explicitly separate tree of test sessions."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from .data import json_write, load_session, sha256
from .engine import predict_model
from .evaluation import save_evaluation
from .folder_datasets import discover_session_folders


IDENTITY_COLUMNS = ['session_id', 'source_row', 'source_time_ns', 'true_id',
                    'true_load', 'true_fx_N', 'true_fy_N', 'true_fz_N']


def _training_history(bundle, checkpoint):
    """Recover verified roles without requiring historical recording files."""
    hashes = bundle.get('source_hashes')
    if not isinstance(hashes, dict) or not hashes:
        raise ValueError('Cannot verify checkpoint training data hashes')
    roles = bundle.get('source_session_roles')
    audit_source = None
    if roles is None:
        audit = checkpoint.parent.parent / 'dataset_audit.json'
        if not audit.is_file():
            raise ValueError('Cannot verify legacy checkpoint train/val roles: missing dataset_audit.json')
        records = json.loads(audit.read_text())
        if not isinstance(records, list):
            raise ValueError('Invalid legacy checkpoint dataset audit')
        roles = {}
        for item in records:
            sid = item.get('session_id')
            counts = item.get('split_counts')
            if sid in roles or not isinstance(counts, dict) or any(
                    part not in counts for part in ('train', 'val', 'test')):
                raise ValueError('Ambiguous legacy checkpoint session roles')
            roles[sid] = {'sha256': item.get('sha256'),
                          'roles': [part for part in ('train', 'val', 'test') if counts[part] > 0]}
        audit_source = {'path': str(audit), 'sha256': sha256(audit)}
    if not isinstance(roles, dict) or set(roles) != set(hashes):
        raise ValueError('Checkpoint role/source hash coverage differs')
    seen = set(bundle.get('seen_training_validation_session_ids', []))
    trained_hashes = set(bundle.get('seen_training_validation_hashes', []))
    for sid, role in roles.items():
        if not isinstance(role, dict) or not isinstance(role.get('roles'), list):
            raise ValueError('Malformed checkpoint session roles')
        parts = set(role['roles'])
        if not parts or parts - {'train', 'val', 'test'}:
            raise ValueError('Unknown or empty checkpoint session role')
        if 'test' in parts and parts & {'train', 'val'}:
            raise ValueError('Checkpoint session mixes test and train/val')
        if role.get('sha256') != hashes[sid]:
            raise ValueError('Checkpoint role/source hash mismatch')
        if parts & {'train', 'val'}:
            seen.add(sid)
            trained_hashes.add(hashes[sid])
    # Source hashes for inherited seen IDs are included whenever the checkpoint
    # still carries that source; older ancestors may retain IDs but not bytes.
    trained_hashes.update(digest for sid, digest in hashes.items() if sid in seen)
    return seen, trained_hashes, audit_source


def _comparable_provenance(provenance):
    value = deepcopy(provenance)
    repair = value.get('timestamp_repair')
    # Moving an identical recording does not change repair evidence. Remove only
    # the locator when the referenced bytes have their own retained digest.
    if isinstance(repair, dict) and repair.get('original_angle_sha256'):
        repair.pop('original_angle_csv', None)
    return value


def _prepare_test_sessions(bundle, checkpoint, folders):
    cfg = deepcopy(bundle['config'])
    if cfg.get('task') not in ('tip', 'body'):
        raise ValueError('Unsupported checkpoint task')
    special = set(cfg.get('label_overrides', {})) | set(cfg.get('known_trimmed_exports', {}))
    names = [folder.name for folder in folders]
    if any(names.count(name) > 1 for name in special):
        raise ValueError('Ambiguous folder name for checkpoint label/trim exception')
    sessions = [load_session(folder, cfg) for folder in folders]
    seen, trained_hashes, legacy_audit = _training_history(bundle, checkpoint)
    ids = [session['info']['session_id'] for session in sessions]
    hashes = [session['info']['sha256'] for session in sessions]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate physical test session')
    if len(hashes) != len(set(hashes)):
        raise ValueError('Duplicate test summary data hash')
    if seen & set(ids):
        raise ValueError('Test session was previously used for training/validation')
    if trained_hashes & set(hashes):
        raise ValueError('Test data hash matches prior training/validation data')
    for session in sessions:
        sid = session['info']['session_id']
        expected_hash = bundle['source_hashes'].get(sid)
        if expected_hash is not None and expected_hash != session['info']['sha256']:
            raise ValueError('Known test session data changed after training')
        expected_provenance = bundle.get('source_provenance', {}).get(sid)
        actual_provenance = {
            'metadata_sha256': session['info']['metadata_sha256'],
            'timestamp_repair': session['info'].get('timestamp_repair')}
        if (expected_provenance is not None and
                _comparable_provenance(expected_provenance) != _comparable_provenance(actual_provenance)):
            raise ValueError('Known test metadata or repair source changed after training')
        if cfg['task'] == 'tip' and session['id'] != 18:
            raise ValueError('Tip checkpoint supports only ID18 test sessions')
        if not 1 <= session['id'] <= 18:
            raise ValueError('Test contact ID is outside supported 1..18 range')
        if not len(session['ends']):
            raise ValueError(f"No usable test windows: {session['info']['folder']}")
        if session['columns'] != bundle['feature_columns']:
            raise ValueError('Input column order differs from checkpoint')
    indices = np.asarray([(sid, int(end)) for sid, session in enumerate(sessions)
                          for end in session['ends']], dtype=np.int64).reshape(-1, 2)
    return sessions, indices, legacy_audit


def run_folder_prediction(checkpoints, test_root, output, device='cpu'):
    """Save one combined CSV per model; never fit scales or change checkpoints."""
    destination = Path(output).resolve()
    if destination.exists():
        raise FileExistsError(f'Prediction output already exists: {destination}')
    folders = discover_session_folders(test_root)
    prepared = []
    model_names = set()
    for item in checkpoints:
        checkpoint = Path(item).resolve(strict=True)
        bundle = torch.load(checkpoint, map_location='cpu', weights_only=True)
        name = bundle['model']
        if not isinstance(name, str) or not name or Path(name).name != name or name in ('.', '..'):
            raise ValueError('Invalid checkpoint model name')
        if name in model_names:
            raise ValueError(f'Duplicate checkpoint model: {name}')
        model_names.add(name)
        sessions, indices, legacy_audit = _prepare_test_sessions(bundle, checkpoint, folders)
        prepared.append((checkpoint, bundle, sessions, indices, legacy_audit))
    if not prepared:
        raise ValueError('No checkpoints')
    destination.mkdir(parents=True, exist_ok=False)
    json_write(destination / 'evaluation_config.json', {
        'evaluation_mode': 'external_test_folders',
        'test_root': str(Path(test_root).resolve()),
        'session_folders': [str(folder) for folder in folders],
        'checkpoints': [str(item[0]) for item in prepared],
        'device': device,
        'scaler_policy': 'unchanged_checkpoint_scaler',
        'started_at_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'running',
    })
    rows = []
    reference = None
    for checkpoint, bundle, sessions, indices, legacy_audit in prepared:
        frame, model = predict_model(bundle, sessions, indices, device=device)
        del model
        identity = frame[IDENTITY_COLUMNS]
        if reference is None:
            reference = identity.copy()
        else:
            pd.testing.assert_frame_equal(identity, reference, check_exact=True,
                                          obj='Common test identity across checkpoints')
        model_root = destination / bundle['model']
        model_root.mkdir()
        frame.to_csv(model_root / 'predictions.csv', index=False)
        metrics = save_evaluation(frame, model_root, bundle['config']['task'])
        json_write(model_root / 'dataset_audit.json', [session['info'] for session in sessions])
        json_write(model_root / 'evaluation_provenance.json', {
            'checkpoint': str(checkpoint), 'checkpoint_sha256': sha256(checkpoint),
            'test_root': str(Path(test_root).resolve()),
            'evaluation_mode': 'external_test_folders',
            'scaler_policy': 'unchanged_checkpoint_scaler',
            'legacy_role_audit': legacy_audit,
            'source_hashes': {s['info']['session_id']: s['info']['sha256'] for s in sessions},
            'source_provenance': {s['info']['session_id']: {
                'metadata_sha256': s['info']['metadata_sha256'],
                'timestamp_repair': s['info'].get('timestamp_repair')} for s in sessions},
            'label_overrides': bundle['config'].get('label_overrides', {}),
            'evaluated_at_utc': datetime.now(timezone.utc).isoformat(),
        })
        # Training statistics are deliberately separate from external test metrics.
        summary = {'model': bundle['model'], 'task': bundle['config']['task'],
                   'training_statistics': bundle.get('stats', {}), 'test_metrics': metrics,
                   'prediction_csv': str(model_root / 'predictions.csv')}
        json_write(model_root / 'summary.json', summary)
        rows.append({'model': bundle['model'], 'task': bundle['config']['task'],
                     'training_validation_loss': bundle.get('stats', {}).get('validation_loss'),
                     **{f'test_{key}': value for key, value in metrics.items()},
                     'prediction_csv': str(model_root / 'predictions.csv')})
        pd.DataFrame(rows).to_csv(destination / 'test_comparison.csv', index=False)
    config_path = destination / 'evaluation_config.json'
    evaluation_config = json.loads(config_path.read_text())
    evaluation_config.update(status='complete',
                             completed_at_utc=datetime.now(timezone.utc).isoformat(),
                             n_models=len(rows), n_test_windows=len(reference))
    json_write(config_path, evaluation_config)
    return rows
