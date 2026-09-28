"""폴더 기반 녹화 단위 분할과 test 격리를 합성 CSV로 검증한다."""
import copy
import csv
import json
from pathlib import Path
import shutil
import unittest

import numpy as np

from hrm_force.data import load_session, prepare, sha256
from hrm_force.folder_datasets import discover_session_folders, resolve_folder_config
import test_loader as loader_fixture


class FolderDatasetTests(unittest.TestCase):
    def setUp(self):
        # 기존 로더의 합성 CSV 계약만 재사용하며 TestCase를 상속하지 않는다.
        self.fixture = loader_fixture.LoaderTests(methodName="runTest")
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.root = self.fixture.root
        (self.root / "trainsets").mkdir()
        (self.root / "testsets").mkdir()
        self.serial = 0
        self.config = copy.deepcopy(self.fixture.config)
        self.config.update({
            "dataset_layout": "train_test_folders",
            "train_directory": "trainsets", "test_directory": "testsets",
            "validation_strategy": "grouped_session_by_contact_id",
            "validation_fraction": .2, "seed": 42, "task": "body",
        })

    def make_session(self, contact_id=18, partition="trainsets", group="", session_id=None):
        self.serial += 1
        name = f"seg-id-{contact_id}_recording-{self.serial}"
        folder = self.fixture._fixture(
            str(Path(partition) / group / name), session_id or f"recording-{self.serial + 10}")
        metadata_path = folder / "session.json"
        metadata = json.loads(metadata_path.read_text())
        metadata["snapshot"]["contact_segment_id"] = contact_id
        metadata_path.write_text(json.dumps(metadata))
        path = folder / "csv" / "summary.csv"
        with path.open(newline="") as stream:
            reader = csv.DictReader(stream)
            header, rows = reader.fieldnames, list(reader)
        features = load_session(self.fixture.folder, self.fixture.config)["columns"]
        for row in rows:
            row["contact_segment_id"] = str(contact_id)
            # 서로 다른 녹화의 CSV가 byte-identical한 fixture가 되지 않도록 한다.
            row["source_time_ns"] = str(int(row["source_time_ns"]) + self.serial * 10**10)
            for column in features:
                row[column] = str(float(row[column]) + 100 * self.serial**2)
            for axis in "xyz":
                key = f"fts_kalman.aligned_f{axis}"
                row[key] = str(float(row[key]) + 10 * self.serial)
        with path.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=header)
            writer.writeheader()
            writer.writerows(rows)
        return folder

    def test_discovery_is_recursive_sorted_and_uses_exact_csv_summary(self):
        first = self.make_session(group="day_b")
        second = self.make_session(group="day_a")
        (self.root / "trainsets" / "unrelated").mkdir()
        (self.root / "trainsets" / "unrelated" / "summary.csv").write_text("not a session")
        found = discover_session_folders(self.root / "trainsets")
        self.assertEqual(found, sorted([first.resolve(), second.resolve()]))
        self.assertTrue(all(path.is_absolute() for path in found))

    def test_empty_discovery_requires_explicit_allow_empty(self):
        self.assertEqual(discover_session_folders(self.root / "testsets", allow_empty=True), [])
        with self.assertRaises(ValueError):
            discover_session_folders(self.root / "testsets")

    def test_resolve_is_deterministic_and_retains_all_contact_ids(self):
        for contact_id in (1, 4, 18):
            for _ in range(3):
                self.make_session(contact_id)
        original = copy.deepcopy(self.config)
        frozen = resolve_folder_config(self.config)
        again = resolve_folder_config(self.config)
        self.assertEqual(self.config, original)
        self.assertEqual(frozen, again)
        self.assertEqual(frozen["dataset_layout"], "frozen_folder_sessions")
        self.assertEqual(len(frozen["sessions"]), 9)
        self.assertEqual(len(frozen["validation_sessions"]), 3)
        self.assertEqual(frozen["test_sessions"], [])
        self.assertTrue(frozen["allow_empty_test"])
        counts = {contact_id: 0 for contact_id in (1, 4, 18)}
        for name in frozen["validation_sessions"]:
            session = load_session(self.root / name, frozen)
            counts[session["id"]] += 1
        self.assertEqual(counts, {1: 1, 4: 1, 18: 1})

    def test_validation_fraction_rounds_up_per_id_but_keeps_training_session(self):
        for _ in range(6):
            self.make_session(18)
        frozen = resolve_folder_config(self.config)
        self.assertEqual(len(frozen["validation_sessions"]), 2)
        high_fraction = resolve_folder_config(dict(self.config, validation_fraction=.99))
        self.assertEqual(len(high_fraction["validation_sessions"]), 5)

    def test_one_recording_for_a_contact_id_cannot_be_split_by_rows(self):
        self.make_session(1)
        self.make_session(18)
        self.make_session(18)
        with self.assertRaises(ValueError):
            resolve_folder_config(self.config)

    def test_prepare_uses_whole_sessions_and_train_only_scaler_without_test(self):
        for _ in range(5):
            self.make_session(18)
        frozen = resolve_folder_config(self.config)
        sessions, indices, scaler = prepare(frozen)
        self.assertEqual(indices["test"].shape, (0, 2))
        train_ids = set(indices["train"][:, 0])
        val_ids = set(indices["val"][:, 0])
        self.assertFalse(train_ids & val_ids)
        self.assertEqual(train_ids | val_ids, set(range(len(sessions))))
        expected_val = {str((self.root / name).resolve()) for name in frozen["validation_sessions"]}
        actual_val = {str(Path(sessions[index]["info"]["path"]).parent.parent) for index in val_ids}
        self.assertEqual(actual_val, expected_val)
        for part in ("train", "val"):
            for index in set(indices[part][:, 0]):
                endpoints = indices[part][indices[part][:, 0] == index, 1]
                np.testing.assert_array_equal(endpoints, sessions[index]["ends"])
                self.assertEqual(len(endpoints), 18)
                self.assertTrue((endpoints >= frozen["window_samples"] - 1).all())
        expected_x = np.concatenate([sessions[index]["x"] for index in sorted(train_ids)])
        expected_y = np.array([sessions[index]["y"][end] for index, end in indices["train"]])
        np.testing.assert_allclose(scaler["x_mean"], expected_x.mean(0, dtype=np.float64))
        np.testing.assert_allclose(scaler["y_mean"], expected_y.mean(0, dtype=np.float64))
        all_x = np.concatenate([session["x"] for session in sessions])
        self.assertFalse(np.allclose(scaler["x_mean"], all_x.mean(0)))

    def test_testset_is_not_added_to_train_validation_or_scaler(self):
        for _ in range(3):
            self.make_session(18)
        test_folder = self.make_session(18, partition="testsets")
        frozen = resolve_folder_config(self.config)
        self.assertEqual(len(frozen["sessions"]), 3)
        self.assertNotIn(str(test_folder.relative_to(self.root)), frozen["sessions"])
        sessions, indices, _ = prepare(frozen)
        self.assertEqual(len(sessions), 3)
        self.assertEqual(indices["test"].shape, (0, 2))
        self.assertFalse(any(session["info"]["session_id"] == "recording-14" for session in sessions))

    def test_frozen_config_does_not_discover_new_training_recordings(self):
        for _ in range(3):
            self.make_session(18)
        frozen = resolve_folder_config(self.config)
        before = copy.deepcopy(frozen)
        added = self.make_session(1)
        self.assertEqual(frozen, before)
        sessions, _, _ = prepare(frozen)
        self.assertEqual(len(sessions), 3)
        self.assertTrue(all(session["id"] == 18 for session in sessions))
        self.assertNotIn(str(added.relative_to(self.root)), frozen["sessions"])
        self.assertEqual(resolve_folder_config(frozen), frozen)

    def test_duplicate_physical_session_id_is_rejected_within_training_and_across_test(self):
        for partition in ("trainsets", "testsets"):
            with self.subTest(partition=partition):
                for child in (self.root / "trainsets").iterdir():
                    shutil.rmtree(child)
                for child in (self.root / "testsets").iterdir():
                    shutil.rmtree(child)
                self.make_session(session_id="same-recording")
                self.make_session()
                self.make_session(partition=partition, session_id="same-recording")
                with self.assertRaises(ValueError):
                    resolve_folder_config(self.config)

    def test_identical_csv_bytes_with_changed_session_id_are_rejected(self):
        original = self.make_session()
        self.make_session()
        for partition in ("trainsets", "testsets"):
            duplicate = self.root / partition / "seg-id-18_duplicate"
            with self.subTest(partition=partition):
                shutil.copytree(original, duplicate)
                metadata_path = duplicate / "session.json"
                metadata = json.loads(metadata_path.read_text())
                metadata["session_id"] = f"different-id-{partition}"
                metadata_path.write_text(json.dumps(metadata))
                self.assertEqual(sha256(original / "csv/summary.csv"),
                                 sha256(duplicate / "csv/summary.csv"))
                with self.assertRaises(ValueError):
                    resolve_folder_config(self.config)
                shutil.rmtree(duplicate)

    def test_protected_test_recording_cannot_be_moved_to_training(self):
        self.make_session(session_id="historical-held-out-test")
        self.make_session()
        config = dict(self.config, protected_test_session_ids=["historical-held-out-test"])
        with self.assertRaises(ValueError):
            resolve_folder_config(config)

    def test_explicit_contact_filter_keeps_tip_inputs_and_does_not_remove_other_raw_data(self):
        excluded = self.make_session(1)
        selected = [self.make_session(18), self.make_session(18)]
        config = dict(self.config, task="tip", include_contact_ids=[18])
        frozen = resolve_folder_config(config)
        self.assertEqual(set(frozen["sessions"]),
                         {str(folder.relative_to(self.root)) for folder in selected})
        self.assertTrue((excluded / "csv/summary.csv").exists())
        sessions, _, _ = prepare(frozen)
        self.assertEqual({session["id"] for session in sessions}, {18})
        self.assertTrue(all(session["x"].shape[1] == 26 for session in sessions))
        audit = json.dumps(frozen)
        self.assertIn(sha256(selected[0] / "csv/summary.csv"), audit)
        self.assertIn(str(excluded.relative_to(self.root)), audit)

    def test_frozen_source_csv_or_metadata_change_is_rejected(self):
        first = self.make_session()
        self.make_session()
        frozen = resolve_folder_config(self.config)
        summary = first / "csv/summary.csv"
        original_summary = summary.read_bytes()
        summary.write_bytes(original_summary + b"\n")
        with self.assertRaisesRegex(ValueError, "changed after folder snapshot"):
            prepare(frozen)
        summary.write_bytes(original_summary)
        recording_config = first / "recording_config.json"
        metadata = json.loads(recording_config.read_text())
        metadata["added_note"] = "changed after split selection"
        recording_config.write_text(json.dumps(metadata))
        with self.assertRaisesRegex(ValueError, "changed after folder snapshot"):
            prepare(frozen)

    def test_protected_test_hash_rejects_training_even_with_new_session_id(self):
        first = self.make_session()
        self.make_session()
        config = dict(self.config, protected_test_hashes=[sha256(first / "csv/summary.csv")])
        with self.assertRaisesRegex(ValueError, "Protected held-out test"):
            resolve_folder_config(config)

    def test_incomplete_recording_is_rejected_instead_of_silently_skipped(self):
        first = self.make_session()
        (first / "csv/manifest.json").unlink()
        with self.assertRaisesRegex(ValueError, "Incomplete recording"):
            discover_session_folders(self.root / "trainsets")

    def test_resolve_and_prepare_leave_source_files_unchanged(self):
        for _ in range(3):
            self.make_session()
        self.make_session(partition="testsets")
        paths = sorted(path for path in self.root.rglob("*") if path.is_file())
        before = {str(path): sha256(path) for path in paths}
        frozen = resolve_folder_config(self.config)
        prepare(frozen)
        after = {str(path): sha256(path) for path in self.root.rglob("*") if path.is_file()}
        self.assertEqual(before, after)

    def test_legacy_explicit_sessions_keep_temporal_split_and_heldout_test(self):
        training = self.make_session(partition="")
        test = self.make_session(partition="")
        config = copy.deepcopy(self.fixture.config)
        config.update({
            "sessions": [str(training.relative_to(self.root)), str(test.relative_to(self.root))],
            # Existing legacy configs list flat recording folder names.
            "test_sessions": [test.name],
        })
        sessions, indices, _ = prepare(config)
        self.assertEqual(len(sessions), 2)
        self.assertEqual(set(indices["train"][:, 0]), {0})
        self.assertEqual(set(indices["val"][:, 0]), {0})
        self.assertEqual(set(indices["test"][:, 0]), {1})
        self.assertTrue((indices["train"][:, 1] < indices["val"][:, 1].min()).all())


if __name__ == "__main__":
    unittest.main()
