"""Regression tests for transcript parsing and yt-edit decision lists."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EDIT_DIR = os.path.join(ROOT, "skills", "yt-edit")
CHAPTERS_DIR = os.path.join(ROOT, "skills", "yt-chapters")
sys.path.insert(0, EDIT_DIR)
sys.path.insert(0, CHAPTERS_DIR)

import deadair  # noqa: E402
import chapters  # noqa: E402


class TranscriptParserTests(unittest.TestCase):
    def write_temp(self, suffix, content):
        handle = tempfile.NamedTemporaryFile(
            mode="w", suffix=suffix, encoding="utf-8", delete=False
        )
        with handle:
            handle.write(content)
        self.addCleanup(lambda: os.path.exists(handle.name) and os.unlink(handle.name))
        return handle.name

    def test_whisper_json_root_list(self):
        path = self.write_temp(".json", json.dumps([
            {"start": 0.0, "end": 1.25, "text": " Hello "},
            {"start": 1.5, "end": 2.0, "text": "world"},
        ]))
        self.assertEqual(deadair.load(path), [(0.0, 1.25, "Hello"), (1.5, 2.0, "world")])

    def test_whisper_json_object_with_segments(self):
        path = self.write_temp(".json", json.dumps({
            "text": "hello world",
            "segments": [{"start": 2, "end": 3, "text": " hello world "}],
        }))
        self.assertEqual(deadair.load(path), [(2.0, 3.0, "hello world")])

    def test_chapters_uses_shared_json_parser(self):
        path = self.write_temp(".json", json.dumps([
            {"start": 0, "end": 1, "text": "first section"},
            {"start": 2, "end": 3, "text": "second section"},
        ]))
        self.assertEqual(chapters.load(path), deadair.load(path))

    def test_srt_input(self):
        path = self.write_temp(
            ".srt",
            "1\n00:00:01,000 --> 00:00:02,500\nHello there\n\n"
            "2\n00:00:03,000 --> 00:00:04,000\nSecond cue\n",
        )
        self.assertEqual(deadair.load(path), [(1.0, 2.5, "Hello there"), (3.0, 4.0, "Second cue")])

    def test_vtt_input(self):
        path = self.write_temp(".vtt", "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nHello VTT\n")
        self.assertEqual(deadair.load(path), [(1.0, 2.0, "Hello VTT")])

    def test_parse_timestamp_formats(self):
        self.assertEqual(deadair.parse_ts("00:01:02,500"), 62.5)
        self.assertEqual(deadair.parse_ts("02:03.250"), 123.25)

    def test_rejects_invalid_timestamp_components(self):
        for value in ("00:60:00.000", "00:00:60.000", "1:2:3:4", "00:-1.0", "NaN:00"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    deadair.parse_ts(value)

    def test_rejects_invalid_json_root(self):
        path = self.write_temp(".json", json.dumps("not a transcript"))
        with self.assertRaisesRegex(ValueError, "must contain a list"):
            deadair.load(path)

    def test_rejects_missing_segment_times(self):
        path = self.write_temp(".json", json.dumps([{"text": "missing times"}]))
        with self.assertRaisesRegex(ValueError, "numeric start and end"):
            deadair.load(path)

    def test_rejects_reversed_segment_times(self):
        path = self.write_temp(".json", json.dumps([{"start": 4, "end": 2, "text": "invalid range"}]))
        with self.assertRaisesRegex(ValueError, "invalid time range"):
            deadair.load(path)

    def test_rejects_non_finite_segment_times(self):
        path = self.write_temp(".json", '[{"start": 0, "end": 1e999, "text": "bad"}]')
        with self.assertRaisesRegex(ValueError, "invalid time range"):
            deadair.load(path)

    def test_rejects_non_string_segment_text(self):
        path = self.write_temp(".json", json.dumps([{"start": 0, "end": 1, "text": ["bad"]}]))
        with self.assertRaisesRegex(ValueError, "text must be a string"):
            deadair.load(path)

    def test_rejects_out_of_order_srt_cues(self):
        path = self.write_temp(
            ".srt",
            "1\n00:00:03,000 --> 00:00:04,000\nLater\n\n"
            "2\n00:00:01,000 --> 00:00:02,000\nEarlier\n",
        )
        with self.assertRaisesRegex(ValueError, "out of order"):
            deadair.load(path)

    def test_rejects_out_of_order_whisper_segments(self):
        path = self.write_temp(".json", json.dumps([
            {"start": 3, "end": 4, "text": "later"},
            {"start": 1, "end": 2, "text": "earlier"},
        ]))
        with self.assertRaisesRegex(ValueError, "out of order"):
            deadair.load(path)


class EditDecisionListTests(unittest.TestCase):
    def test_dead_air_cut_keeps_breath_on_both_sides(self):
        report = deadair.analyze([(0, 1, "Hello"), (3, 4, "World")], floor=0.5)
        dead = next(cut for cut in report["cuts"] if cut["kind"] == "DEAD")
        self.assertEqual((dead["start"], dead["end"]), (1.25, 2.75))

    def test_filler_cue_is_flagged(self):
        report = deadair.analyze([(0, 1, "Hello"), (1, 1.5, "um"), (2, 3, "World")])
        self.assertIn("FILLER", {cut["kind"] for cut in report["cuts"]})

    def test_repeat_is_review_only_not_automatic_removed_time(self):
        report = deadair.analyze([
            (0, 2, "Today we are going to look at this"),
            (2.2, 4, "Today we are going to look at this again"),
        ])
        repeat = next(cut for cut in report["cuts"] if cut["kind"] == "REPEAT")
        self.assertTrue(repeat["review_only"])
        self.assertEqual(report["removed"], 0.0)

    def test_removed_time_does_not_double_count_overlapping_cues(self):
        report = deadair.analyze([(0, 2, "um"), (1, 3, "uh")])
        self.assertEqual(report["removed"], 3.0)

    def test_duration_uses_latest_cue_end(self):
        report = deadair.analyze([(0, 1, "Hello"), (0.5, 4, "World")])
        self.assertEqual(report["duration"], 4)

    def test_rejects_invalid_floor(self):
        for floor in (0, -1, float("inf"), float("nan")):
            with self.subTest(floor=floor):
                with self.assertRaisesRegex(ValueError, "greater than zero"):
                    deadair.analyze([(0, 1, "Hello")], floor=floor)

    def test_cli_bad_floor_is_clean_error(self):
        result = subprocess.run(
            [sys.executable, os.path.join(EDIT_DIR, "deadair.py"), "missing.srt", "--floor", "bad"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Traceback", result.stderr)

    def test_cli_json_output(self):
        path = tempfile.NamedTemporaryFile(mode="w", suffix=".srt", encoding="utf-8", delete=False)
        with path:
            path.write("1\n00:00:00,000 --> 00:00:01,000\nHello\n")
        self.addCleanup(lambda: os.path.exists(path.name) and os.unlink(path.name))
        result = subprocess.run(
            [sys.executable, os.path.join(EDIT_DIR, "deadair.py"), path.name, "--json"],
            capture_output=True, text=True, check=True,
        )
        self.assertEqual(json.loads(result.stdout)["duration"], 1.0)


if __name__ == "__main__":
    unittest.main()
