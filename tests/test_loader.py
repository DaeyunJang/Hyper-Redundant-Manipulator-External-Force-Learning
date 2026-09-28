"""실제 CSV/JSON 로더를 최소 합성 녹화 폴더로 검사한다."""
import copy
import csv
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from hrm_force.data import feature_spec, load_session, prepare, sha256


class LoaderTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.config = {
            "feature_groups": ["wire_length", "loadcell_tension", "relative_angle"],
            "force_source": "kalman", "source_force_unit": "mN", "window_samples": 3,
            "gap_factor": 1.5, "max_matching_skew_ms": 25.,
            "label_overrides": {}, "data_root": str(self.root),
            "validation_fraction": .2, "validation_purge_seconds": 0.,
        }
        self.folder = self._fixture("seg-id-18_train", "recording-1")

    def tearDown(self):
        self.temporary.cleanup()

    def _fixture(self, name, session_id):
        folder = self.root / name
        csv_dir = folder / "csv"
        csv_dir.mkdir(parents=True)
        features, flags, _ = feature_spec(self.config["feature_groups"])
        header = features + flags + ["wire.time_difference_ms", "loadcell.time_difference_ms"]
        for prefix in ("fts", "fts_kalman"):
            header += [f"{prefix}.aligned_f{axis}" for axis in "xyz"]
            header += [f"{prefix}.matched", f"{prefix}.aligned_force_valid",
                       f"{prefix}.time_difference_ms", f"{prefix}.aligned_frame_id"]
        header += ["source_time_ns", "contact_segment_id", "unused_tag_position"]
        rows = []
        for index in range(20):
            row = {column: str((index - 5) * .1 + axis)
                   for axis, column in enumerate(features)}
            row.update({flag: "True" for flag in flags})
            row.update({"wire.time_difference_ms": "0", "loadcell.time_difference_ms": "1"})
            for prefix in ("fts", "fts_kalman"):
                target = [-100., 0., 200.] if prefix == "fts_kalman" else [300., -400., 500.]
                row.update({f"{prefix}.aligned_f{axis}": str(target[i])
                            for i, axis in enumerate("xyz")})
                row.update({f"{prefix}.matched": "True", f"{prefix}.aligned_force_valid": "True",
                            f"{prefix}.time_difference_ms": "0", f"{prefix}.aligned_frame_id": "hrm_base"})
            row.update({"source_time_ns": str(1_000_000_000 + index * 33_333_333),
                        "contact_segment_id": "18", "unused_tag_position": "NaN"})
            rows.append(row)
        with (csv_dir / "summary.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=header)
            writer.writeheader()
            writer.writerows(rows)
        alignment = {"enabled": True, "target_frame": "hrm_base", "axes": ["x", "y", "z"],
                     "matrix_base_from_sensor": [[1, 0, 0], [0, 1, 0], [0, 0, 1]]}
        documents = {
            folder / "session.json": {"session_id": session_id, "snapshot": {
                "contact_segment_id": 18, "force_alignment": alignment}},
            folder / "recording_config.json": {"notes": {"source_units": {"fts_force": "mN"}}},
            csv_dir / "manifest.json": {"status": "complete", "force_alignment": alignment},
            csv_dir / "summary.schema.json": {"status": "complete", "columns": header,
                                                "rows_written": len(rows)},
        }
        for path, content in documents.items():
            path.write_text(json.dumps(content))
        return folder

    def _change_cell(self, row_index, column, value):
        path = self.folder / "csv" / "summary.csv"
        with path.open(newline="") as stream:
            reader = csv.DictReader(stream)
            header, rows = reader.fieldnames, list(reader)
        rows[row_index][column] = value
        with path.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=header)
            writer.writeheader()
            writer.writerows(rows)

    def test_selected_26_inputs_ignore_unused_nan_and_preserve_signed_force(self):
        loaded = load_session(self.folder, self.config)
        self.assertEqual(loaded["x"].shape, (20, 26))
        self.assertTrue(loaded["valid"].all())
        self.assertEqual(len(loaded["ends"]), 18)
        self.assertNotIn("unused_tag_position", loaded["columns"])
        np.testing.assert_allclose(loaded["y"][0], [-.1, 0., .2], atol=1e-7)
        self.assertLess(loaded["x"][0, 0], 0)
        self.assertEqual(loaded["x"][5, 0], 0)
        self.assertEqual(loaded["id"], 18)

    def test_false_flag_rejects_row_and_every_window_containing_it(self):
        self._change_cell(6, "wire.matched", "False")
        loaded = load_session(self.folder, self.config)
        self.assertFalse(loaded["valid"][6])
        self.assertEqual(loaded["info"]["rejected_reason_counts_overlapping"]["wire.matched"], 1)
        for endpoint in loaded["ends"]:
            self.assertFalse(endpoint - 2 <= 6 <= endpoint)
        self.assertEqual(int(loaded["valid"].sum()), 19)

    def test_selected_nan_stays_missing_and_breaks_windows(self):
        self._change_cell(8, "relative_angle_1", "NaN")
        loaded = load_session(self.folder, self.config)
        self.assertFalse(loaded["valid"][8])
        self.assertTrue(np.isnan(loaded["x"][8, 8]))
        self.assertFalse(any(endpoint - 2 <= 8 <= endpoint for endpoint in loaded["ends"]))

    def test_raw_and_kalman_selection_use_separate_targets(self):
        kalman = load_session(self.folder, self.config)
        raw_config = dict(self.config, force_source="raw")
        raw = load_session(self.folder, raw_config)
        np.testing.assert_array_equal(kalman["x"], raw["x"])
        np.testing.assert_allclose(kalman["y"][0], [-.1, 0., .2], atol=1e-7)
        np.testing.assert_allclose(raw["y"][0], [.3, -.4, .5], atol=1e-7)
        # 사용하지 않는 raw의 invalid flag는 Kalman 행을 버리지 않는다.
        self._change_cell(4, "fts.matched", "False")
        self.assertTrue(load_session(self.folder, self.config)["valid"][4])
        self.assertFalse(load_session(self.folder, raw_config)["valid"][4])

    def test_duplicate_physical_session_across_splits_is_rejected(self):
        test_folder = self._fixture("seg-id-18_test", "recording-1")
        config = copy.deepcopy(self.config)
        config.update({"sessions": [self.folder.name, test_folder.name],
                       "test_sessions": [test_folder.name]})
        with self.assertRaisesRegex(ValueError, "Duplicate physical session"):
            prepare(config)

    def test_loading_does_not_change_original_source_files(self):
        files = sorted(path for path in self.folder.rglob("*") if path.is_file())
        before = {path: sha256(path) for path in files}
        load_session(self.folder, self.config)
        load_session(self.folder, dict(self.config, force_source="raw"))
        after = {path: sha256(path) for path in files}
        self.assertEqual(before, after)
        self.assertEqual(files, sorted(path for path in self.folder.rglob("*") if path.is_file()))

    def test_unknown_source_unit_and_conflicting_ids_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "source force unit"):
            load_session(self.folder, dict(self.config, source_force_unit="N"))
        self._change_cell(0, "contact_segment_id", "17")
        with self.assertRaisesRegex(ValueError, "CSV/session ID conflict"):
            load_session(self.folder, self.config)

    def test_explicit_corrected_csv_id_requires_exact_session_and_hash(self):
        path=self.folder/'session.json'
        meta=json.loads(path.read_text());meta['snapshot']['contact_segment_id']=0
        path.write_text(json.dumps(meta))
        before={p:sha256(p) for p in self.folder.rglob('*') if p.is_file()}
        with self.assertRaisesRegex(ValueError,'CSV/session ID conflict'):
            load_session(self.folder,self.config)
        override={'original_id':0,'csv_id':18,'training_id':18,'session_id':'recording-1',
                  'summary_sha256':sha256(self.folder/'csv/summary.csv'),
                  'basis':'User confirmed corrected CSV contains ID18'}
        self.config['label_overrides'][self.folder.name]=override
        loaded=load_session(self.folder,self.config)
        self.assertEqual(loaded['id'],18)
        self.assertEqual(loaded['source_id'],18)
        self.assertEqual(loaded['info']['source_id'],0)
        self.assertEqual(loaded['info']['csv_contact_segment_id'],18)
        self.assertEqual(before,{p:sha256(p) for p in before})
        for key,value in [('session_id','different'),('summary_sha256','different'),
                          ('basis',''),('original_id',1)]:
            with self.subTest(key=key):
                bad=copy.deepcopy(self.config)
                bad['label_overrides'][self.folder.name][key]=value
                with self.assertRaisesRegex(ValueError,'override'):
                    load_session(self.folder,bad)
        self._change_cell(0,'contact_segment_id','17')
        override['summary_sha256']=sha256(self.folder/'csv/summary.csv')
        with self.assertRaisesRegex(ValueError,'CSV/session ID conflict'):
            load_session(self.folder,self.config)

    def test_legacy_label_override_preserves_original_recorded_id(self):
        corrected=self.folder.rename(self.root/'seg-id-17_train')
        self.config['label_overrides'][corrected.name]={
            'original_id':18,'training_id':17,'basis':'explicit test correction'}
        loaded=load_session(corrected,self.config)
        self.assertEqual(loaded['source_id'],18)
        self.assertEqual(loaded['id'],17)


if __name__ == "__main__":
    unittest.main()
