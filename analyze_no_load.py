"""수동 F/T 무부하 범위와 부하 라벨. 회귀 정답은 바꾸지 않습니다.

설정: configs/train.yaml의 ft_sensor_calibration, 각 축 [최솟값, 최댓값].
실행: python analyze_no_load.py --config configs/train.yaml [--input 기록.csv]
--input은 지정 범위에 대한 기록 통계만 구하며 학습 경계를 자동 변경하지 않습니다.
"""
from __future__ import annotations

import argparse
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np


def calibrate_no_load(config):
    """CSV 원값에 적용할 수동 범위를 N 단위로 저장합니다. 교정 CSV를 읽지 않습니다."""
    if 'calibration' in config:
        raise ValueError('Replace legacy calibration with ft_sensor_calibration: unit, fx, fy, fz')
    policy = config.get('ft_sensor_calibration')
    if not isinstance(policy, Mapping):
        raise ValueError('ft_sensor_calibration must specify unit and fx/fy/fz [minimum, maximum]')
    extra = set(policy) - {'unit', 'fx', 'fy', 'fz'}
    if extra:
        raise ValueError(f'Unknown ft_sensor_calibration keys: {sorted(extra)}')
    unit = policy.get('unit')
    if unit not in ('mN', 'N'):
        raise ValueError('ft_sensor_calibration.unit must be mN or N')
    bounds = []
    for axis in ('fx', 'fy', 'fz'):
        pair = policy.get(axis)
        if (not isinstance(pair, (list, tuple)) or len(pair) != 2 or
                any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in pair)):
            raise ValueError(f'ft_sensor_calibration.{axis} must be [minimum, maximum] numbers')
        if not np.isfinite(pair).all() or not pair[0] < pair[1]:
            raise ValueError(f'ft_sensor_calibration.{axis} requires finite minimum < maximum')
        bounds.append(pair)
    bounds = np.asarray(bounds, dtype=np.float64) * (.001 if unit == 'mN' else 1.)
    return {
        'method': 'manual_axis_ranges', 'source_unit': unit, 'unit': 'N',
        'force_columns': list(config.get('force_columns', [f'fts_kalman.aligned_f{a}' for a in 'xyz'])),
        'frame': config.get('force_frame', 'unverified'),
        'lower_N': bounds[:, 0].tolist(), 'upper_N': bounds[:, 1].tolist(),
        'decision_rule': 'all axes inside inclusive ranges => unloaded; any axis outside => loaded',
        'force_comparison': 'recorded force after unit conversion only; no offset subtraction',
        'uncertain_policy': 'none',
        'regression_force_transform': 'source_unit_to_N_only',
    }


def load_states(force, valid, calibration):
    """0=무부하, 1=유부하, -2=무효. 과거 bundle만 기존 불확실(-1) 판정을 보존합니다."""
    force = np.asarray(force, dtype=np.float64)
    valid = np.asarray(valid, dtype=bool)
    if force.ndim != 2 or force.shape[1] != 3 or valid.shape != (len(force),):
        raise ValueError('Expected force (rows, 3) and valid (rows,)')
    valid = valid & np.isfinite(force).all(axis=1)
    result = np.full(len(force), -2, dtype=np.int8)
    if calibration.get('method') == 'manual_axis_ranges':
        lower, upper = np.asarray(calibration['lower_N']), np.asarray(calibration['upper_N'])
        inside = ((force[valid] >= lower) & (force[valid] <= upper)).all(axis=1)
        result[valid] = np.where(inside, 0, 1)
    elif all(key in calibration for key in ('center_N', 'scale_N', 'off_score', 'on_score')):
        # 기존 checkpoint 재현 전용. 새 학습은 위의 수동 범위만 사용합니다.
        score = np.max(np.abs(force[valid] - np.asarray(calibration['center_N'])) /
                       np.asarray(calibration['scale_N']), axis=1)
        state = np.full(len(score), -1, dtype=np.int8)
        state[score <= calibration['off_score']] = 0
        state[score >= calibration['on_score']] = 1
        result[valid] = state
    else:
        raise ValueError('Unsupported saved F/T calibration')
    return result


def main(argv=None):
    from data_utils import ROOT, _frame, _number, _path, load_config, sha256, write_json

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default='configs/train.yaml')
    parser.add_argument('--input', help='선택: 지정한 무부하 범위로 통계를 확인할 CSV')
    parser.add_argument('--output', help='새 결과 폴더 경로')
    args = parser.parse_args(argv)
    config = load_config(args.config)
    report = calibrate_no_load(config)
    if args.input:
        source = _path(args.input, config)
        before = sha256(source)
        force = _number(_frame(source, config['force_columns']), config['force_columns'])
        force *= .001 if config['source_force_unit'] == 'mN' else 1.
        valid = np.isfinite(force).all(axis=1)
        if not valid.any():
            raise ValueError('No finite Fx/Fy/Fz rows in the selected recording')
        states = load_states(force, valid, report)
        report['recording'] = {
            'path': str(source), 'sha256': before,
            'valid_rows': int(valid.sum()), 'invalid_rows': int((~valid).sum()),
            'mean_N': force[valid].mean(axis=0), 'std_N': force[valid].std(axis=0),
            'minimum_N': force[valid].min(axis=0), 'maximum_N': force[valid].max(axis=0),
            'unloaded_fraction': float(np.mean(states[valid] == 0)),
            'loaded_fraction': float(np.mean(states[valid] == 1)),
        }
        if sha256(source) != before:
            raise ValueError('Recording changed during reading')
    stamp = datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y%m%d_%H%M%S')
    output = Path(args.output) if args.output else ROOT / 'results/train' / (stamp + '_no_load')
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / 'analysis.json', report)
    print(output.resolve())
    for axis, low, high in zip(('Fx', 'Fy', 'Fz'), report['lower_N'], report['upper_N']):
        print(f'{axis} 무부하 범위 [mN]: [{low * 1000:.6f}, {high * 1000:.6f}]')
    if 'recording' in report:
        print('기록의 무부하 판정 비율:', report['recording']['unloaded_fraction'])
    return output


if __name__ == '__main__':
    main()
