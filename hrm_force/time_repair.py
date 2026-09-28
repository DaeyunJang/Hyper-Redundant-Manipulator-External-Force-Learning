"""Strict, read-only timestamp repair for four independently audited exports."""
from decimal import Decimal
from pathlib import Path
import hashlib
import json

import numpy as np
import pandas as pd


# Folder -> (frozen session ID, original angle row count, removed signal rows).
# These are evidence-backed exceptions, never a heuristic for arbitrary files.
KNOWN_EXPORTS = {
    'sine-35deg-both_seg-id-15_right': ('20260926_175958_063786', 5649, 53),
    'sine-35deg-both_seg-id-16_right': ('20260926_174832_441013', 5008, 3),
    'sine-35deg-both_seg-id-17_right': ('20260926_173806_037702', 5205, 30),
    'sine-35deg-both_seg-id-18_right': ('20260926_173345_163794', 5799, 29),
}


def _hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _integer(value):
    value = Decimal(str(value))
    if not value.is_finite() or value != value.to_integral_value() or value <= 0:
        raise ValueError('Timestamp must be a finite positive integer')
    return int(value)


def repair_timestamps(folder, df):
    """Return exact source stamps only after all 18 angles prove row identity.

    Summary signal rows were trimmed while their first timestamp columns were
    left untrimmed. The original angle topic CSV retains the exact source clock.
    Neither inputs/targets nor any source file is modified by this function.
    """
    folder = Path(folder)
    if folder.name not in KNOWN_EXPORTS:
        raise ValueError(f'{folder}: no audited timestamp repair exists')
    expected_session, original_rows, offset = KNOWN_EXPORTS[folder.name]
    meta = json.loads((folder / 'session.json').read_text())
    schema = json.loads((folder / 'csv/summary.schema.json').read_text())
    manifest = json.loads((folder / 'csv/manifest.json').read_text())
    if meta.get('session_id') != expected_session:
        raise ValueError(f'{folder}: repair session identity mismatch')
    if (schema.get('rows_written') != original_rows
            or manifest.get('summary_csv', {}).get('rows_written') != original_rows
            or len(df) != original_rows - offset):
        raise ValueError(f'{folder}: repair row counts no longer match audit')
    candidates = list((folder / 'csv').glob('estimated_segment_angle__*.csv'))
    if len(candidates) != 1:
        raise ValueError(f'{folder}: exactly one original angle CSV is required')
    angle_path = candidates[0]
    original = pd.read_csv(angle_path, dtype=str, keep_default_na=False,
                           usecols=['source_time_ns', 'pan_relative', 'tilt_relative'])
    if len(original) != original_rows:
        raise ValueError(f'{folder}: original angle count differs from audit')
    ts = np.array([_integer(v) for v in original.source_time_ns], dtype=np.int64)
    if np.any(np.diff(ts) <= 0):
        raise ValueError(f'{folder}: original angle stamps are not increasing')
    arrays = {}
    for axis in ['pan', 'tilt']:
        arrays[axis] = np.asarray([json.loads(v) for v in original[f'{axis}_relative']],
                                  dtype=np.float64)
        if arrays[axis].shape != (original_rows, 18):
            raise ValueError(f'{folder}: original {axis} array shape is invalid')
    active = np.column_stack([
        arrays['tilt' if i % 2 else 'pan'][:, i - 1] for i in range(1, 19)
    ])[offset:]
    angle_cols = [f'relative_angle_{i}' for i in range(1, 19)]
    if all(c in df for c in angle_cols):
        summary_angles = df[angle_cols].apply(pd.to_numeric, errors='raise').to_numpy(float)
    else:
        # Feature ablations still require all angles as audit evidence, not X.
        summary_angles = pd.read_csv(folder / 'csv/summary.csv', usecols=angle_cols)[angle_cols].to_numpy(float)
    if summary_angles.shape != active.shape:
        raise ValueError(f'{folder}: summary angle row count mismatch')
    residual = np.abs(summary_angles - active)
    if not np.isfinite(residual).all() or np.any(residual > 1e-12):
        raise ValueError(f'{folder}: row identity failed; timestamp repair refused')
    repaired = ts[offset:].copy()

    # Cross-check original F/T source stamps independently of stale matched flags.
    source_cols = ['source_time_ns', 'fts.source_time_ns', 'fts_kalman.source_time_ns']
    summary = pd.read_csv(folder / 'csv/summary.csv', dtype=str,
                          keep_default_na=False, usecols=source_cols)
    if len(summary) != len(df):
        raise ValueError(f'{folder}: supplied dataframe row count differs from CSV')
    sensor_skews = {}
    for prefix in ['fts', 'fts_kalman']:
        sensor_ts = np.array([_integer(v) for v in summary[f'{prefix}.source_time_ns']],
                             dtype=np.int64)
        skew = (sensor_ts - repaired) / 1e6
        if not np.isfinite(skew).all() or np.any(np.abs(skew) > 25.01):
            raise ValueError(f'{folder}: repaired {prefix} clock exceeds 25ms matching bound')
        sensor_skews[prefix] = {
            'min_ms': float(skew.min()), 'median_ms': float(np.median(skew)),
            'max_ms': float(skew.max()), 'rows_checked': len(skew),
        }
    evidence = {
        'applied': True,
        'method': 'verified_all_18_active_angles_against_original_topic_csv',
        'session_id': expected_session,
        'original_angle_csv': str(angle_path.resolve()),
        'original_angle_sha256': _hash(angle_path),
        'summary_sha256': _hash(folder / 'csv/summary.csv'),
        'original_angle_rows': original_rows,
        'original_angle_start_row_zero_based': offset,
        'summary_rows_verified': len(df),
        'all_active_angle_comparisons': int(residual.size),
        'max_active_angle_error_rad': float(residual.max()),
        'angle_match_atol_rad': 1e-12,
        'source_stamp_first_ns': int(repaired[0]),
        'source_stamp_last_ns': int(repaired[-1]),
        'original_summary_first_source_time_ns': str(summary.source_time_ns.iloc[0]),
        'sensor_skews_after_repair': sensor_skews,
        'scope': 'source anchor clock only; source CSV, input, target and row order unchanged',
        'precision': 'exact int64 anchors from original angle CSV; rounded sensor stamps remain rounded',
        'limitation': 'does not establish camera exposure synchronization or compensate sensor/filter latency',
    }
    return repaired, evidence
