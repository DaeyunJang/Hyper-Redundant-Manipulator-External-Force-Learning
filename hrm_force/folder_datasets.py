"""Discover recording folders once and freeze an auditable training configuration."""
import copy
import json
import math
import os
from pathlib import Path

import numpy as np

from .data import ROOT, load_session, sha256

_REQUIRED = ('session.json', 'recording_config.json', 'csv/summary.csv',
             'csv/manifest.json', 'csv/summary.schema.json')


def discover_session_folders(root, allow_empty=False):
    """Find exact csv/summary.csv exports; prune each recording's large raw assets."""
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError(f'Dataset directory does not exist: {root}')
    folders, visited = [], set()
    for current, directories, _ in os.walk(root, followlinks=True):
        path = Path(current)
        canonical = path.resolve()
        if canonical in visited:
            raise ValueError(f'Duplicate directory or symlink cycle: {path}')
        visited.add(canonical)
        directories[:] = sorted(d for d in directories if not d.startswith('.'))
        if (path / 'csv/summary.csv').is_file() or (path / 'session.json').is_file():
            missing = [name for name in _REQUIRED if not (path / name).is_file()]
            if missing:
                raise ValueError(f'Incomplete recording {path}: missing {missing}')
            folders.append(path.absolute())
            directories[:] = []
    if not folders and not allow_empty:
        raise ValueError(f'No recording folders containing csv/summary.csv: {root}')
    names = [p.name for p in folders]
    if len(names) != len(set(names)):
        raise ValueError('Duplicate recording folder names make label/repair overrides ambiguous')
    return sorted(folders)


def source_identity(info):
    return {key: info.get(key) for key in
            ('session_id', 'sha256', 'metadata_sha256', 'timestamp_repair')}


def _identity(folder):
    metadata = json.loads((folder / 'session.json').read_text())
    sid = metadata.get('session_id')
    if not isinstance(sid, str) or not sid:
        raise ValueError(f'Missing physical session_id: {folder}')
    return {'session_id': sid, 'sha256': sha256(folder / 'csv/summary.csv'),
            'path': str(folder / 'csv/summary.csv')}


def resolve_folder_config(config):
    """Only live folder configs discover files; saved snapshots never discover again.

    Test folders reserve identities only. Their targets never enter prepare/scaler/loss.
    """
    cfg = copy.deepcopy(config)
    if cfg.get('dataset_layout') != 'train_test_folders':
        return cfg
    if cfg.get('sessions') or cfg.get('test_sessions') or cfg.get('validation_sessions'):
        raise ValueError('Live folder config must not also supply explicit session lists')
    root = Path(cfg['data_root'])
    root = (ROOT / root).resolve() if not root.is_absolute() else root.resolve()
    train_root = root / cfg.get('train_directory', 'trainsets')
    test_root = root / cfg.get('test_directory', 'testsets')
    if train_root.resolve() == test_root.resolve() or any(
            a.resolve().is_relative_to(b.resolve())
            for a, b in ((train_root, test_root), (test_root, train_root))):
        raise ValueError('trainsets and testsets must be separate, non-nested directories')
    train_folders = discover_session_folders(train_root)
    test_folders = discover_session_folders(test_root, allow_empty=True)
    train_info = [_identity(p) for p in train_folders]
    test_info = [_identity(p) for p in test_folders]
    all_info = train_info + test_info
    for field, label in [('session_id', 'physical session'), ('sha256', 'summary hash')]:
        seen = {}
        for item in all_info:
            if item[field] in seen:
                raise ValueError(f'Duplicate {label}: {seen[item[field]]} and {item["path"]}')
            seen[item[field]] = item['path']
    protected_ids = set(cfg.get('protected_test_session_ids', []))
    protected_hashes = set(cfg.get('protected_test_hashes', []))
    protected_ids.update(item['session_id'] for item in test_info)
    protected_hashes.update(item['sha256'] for item in test_info)
    for item in train_info:
        if item['session_id'] in protected_ids or item['sha256'] in protected_hashes:
            raise ValueError('Protected held-out test recording found in trainsets: '
                             f'{item["path"]} ({item["session_id"]}). '
                             'Keep this recording in testsets, not trainsets.')
    fraction = float(cfg['validation_fraction'])
    if not 0 < fraction < 1:
        raise ValueError('validation_fraction must be between zero and one')
    strategy = cfg.get('validation_strategy')
    if strategy != 'grouped_session_by_contact_id':
        raise ValueError('Folder training requires validation_strategy=grouped_session_by_contact_id')
    include = cfg.get('include_contact_ids')
    include = set(include) if include is not None else None
    if include is not None and (not include or not include <= set(range(1, 19))):
        raise ValueError('include_contact_ids must contain IDs from 1 through 18')
    if cfg['task'] == 'tip':
        if include is not None and include != {18}:
            raise ValueError('Tip force supports only ID18')
        include = {18}
    selected, excluded, groups, snapshots = [], [], {}, {}
    for folder in train_folders:
        session = load_session(folder, cfg)
        if session['id'] not in range(1, 19):
            raise ValueError(f'Unsupported contact ID: {folder}')
        key = folder.relative_to(root).as_posix()
        if include is not None and session['id'] not in include:
            excluded.append({'session': key, 'session_id': session['info']['session_id'],
                             'contact_id': session['id'], 'reason': 'include_contact_ids',
                             'sha256': session['info']['sha256']})
            continue
        if not len(session['ends']):
            raise ValueError(f'No usable windows: {folder}')
        selected.append(key)
        groups.setdefault(session['id'], []).append(key)
        snapshots[key] = source_identity(session['info'])
    if not selected:
        raise ValueError('No training recordings match the selected contact IDs')
    validation = []
    for contact_id, names in sorted(groups.items()):
        if len(names) < 2:
            raise ValueError(f'ID{contact_id} requires at least two independent recordings '
                             'for grouped train/validation; no automatic temporal fallback')
        # Independent per-ID seeds avoid changes to other IDs when a class is added.
        rng = np.random.default_rng(int(cfg.get('seed', 42)) + contact_id)
        count = min(len(names) - 1, max(1, math.ceil(len(names) * fraction)))
        validation.extend(sorted(rng.permutation(sorted(names))[:count].tolist()))
    cfg.update({'dataset_layout': 'frozen_folder_sessions', 'data_root': str(root),
                'sessions': sorted(selected), 'validation_sessions': sorted(validation),
                'test_sessions': [], 'allow_empty_test': True, 'expected_sources': snapshots,
                'protected_test_session_ids': sorted(protected_ids),
                'protected_test_hashes': sorted(protected_hashes),
                'folder_discovery': {'train_root': str(train_root), 'test_root': str(test_root),
                                     'excluded': excluded, 'reserved_tests': test_info,
                                     'validation_policy': 'whole_recordings_stratified_by_contact_id',
                                     'validation_recording_fraction_actual': len(validation) / len(selected)}})
    return cfg
