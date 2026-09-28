import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from hrm_force.time_repair import KNOWN_EXPORTS, repair_timestamps


class TimeRepairTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name) / 'audited_test_session'
        (self.folder / 'csv').mkdir(parents=True)
        self.stamps = 1790411625355425537 + np.arange(6, dtype=np.int64) * 33333333
        pan = np.arange(108, dtype=float).reshape(6, 18) / 1000
        tilt = -pan - 0.01
        pd.DataFrame({'source_time_ns': self.stamps.astype(str),
                      'pan_relative': [json.dumps(x.tolist()) for x in pan],
                      'tilt_relative': [json.dumps(x.tolist()) for x in tilt]}
                     ).to_csv(self.folder / 'csv/estimated_segment_angle__test.csv', index=False)
        active = np.empty((6, 18))
        active[:, ::2] = tilt[:, ::2]
        active[:, 1::2] = pan[:, 1::2]
        self.df = pd.DataFrame(active[2:], columns=[f'relative_angle_{i}' for i in range(1, 19)])
        self.df['source_time_ns'] = self.stamps[:4].astype(str)
        for prefix in ['fts', 'fts_kalman']:
            self.df[f'{prefix}.source_time_ns'] = (self.stamps[2:] + 1000000).astype(str)
        self.df.to_csv(self.folder / 'csv/summary.csv', index=False)
        (self.folder / 'session.json').write_text(json.dumps({'session_id': 'test_frozen_id'}))
        (self.folder / 'csv/summary.schema.json').write_text(json.dumps({'rows_written': 6}))
        (self.folder / 'csv/manifest.json').write_text(json.dumps({'summary_csv': {'rows_written': 6}}))
        self.registry = patch.dict(KNOWN_EXPORTS, {self.folder.name: ('test_frozen_id', 6, 2)})
        self.registry.start()
        self.addCleanup(self.registry.stop)

    def test_recovers_exact_integer_clock_without_touching_sources(self):
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in self.folder.rglob('*') if p.is_file()}
        ts, evidence = repair_timestamps(self.folder, self.df)
        np.testing.assert_array_equal(ts, self.stamps[2:])
        self.assertEqual(ts.dtype, np.int64)
        self.assertEqual(evidence['all_active_angle_comparisons'], 72)
        self.assertEqual(evidence['sensor_skews_after_repair']['fts']['max_ms'], 1.0)
        for p, digest in before.items():
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), digest)

    def test_any_active_angle_mismatch_refuses_repair(self):
        for axis in [1, 2, 18]:
            corrupt = self.df.copy()
            corrupt.loc[3, f'relative_angle_{axis}'] += 0.001
            with self.assertRaisesRegex(ValueError, 'row identity failed'):
                repair_timestamps(self.folder, corrupt)

    def test_stale_matched_claim_cannot_hide_bad_sensor_clock(self):
        bad = self.df.copy()
        bad['fts_kalman.source_time_ns'] = (self.stamps[2:] + 1000000000).astype(str)
        bad.to_csv(self.folder / 'csv/summary.csv', index=False)
        with self.assertRaisesRegex(ValueError, 'matching bound'):
            repair_timestamps(self.folder, bad)

    def test_unknown_folder_and_row_count_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'no audited timestamp repair'):
            repair_timestamps(self.folder.parent / 'unknown_session', self.df)
        with self.assertRaisesRegex(ValueError, 'row counts'):
            repair_timestamps(self.folder, self.df.iloc[:-1])

    def test_angle_free_ablation_still_requires_full_audit(self):
        ts, _ = repair_timestamps(self.folder, self.df[['source_time_ns']])
        np.testing.assert_array_equal(ts, self.stamps[2:])


if __name__ == '__main__':
    unittest.main()
