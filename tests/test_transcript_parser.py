"""Regression tests for the shared transcript parser used by yt-edit and yt-chapters."""
import json
import os
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
        self.assertEqual(
            deadair.load(path),
            [(0.0, 1.25, "Hello"), (1.5, 2.0, "world")],
        )

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
        self.assertEqual(
            deadair.load(path),
            [(1.0, 2.5, "Hello there"), (3.0, 4.0, "Second cue")],
        )

    def test_vtt_input(self):
        path = self.write_temp(
            ".vtt",
            "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nHello VTT\n",
        )
        self.assertEqual(deadair.load(path), [(1.0, 2.0, "Hello VTT")])

    def test_parse_timestamp_formats(self):
        self.assertEqual(deadair.parse_ts("00:01:02,500"), 62.5)
        self.assertEqual(deadair.parse_ts("02:03.250"), 123.25)

    def test_rejects_invalid_json_root(self):
        path = self.write_temp(".json", json.dumps("not a transcript"))
        with self.assertRaisesRegex(ValueError, "must contain a list"):
            deadair.load(path)

    def test_rejects_missing_segment_times(self):
        path = self.write_temp(".json", json.dumps([{"text": "missing times"}]))
        with self.assertRaisesRegex(ValueError, "numeric start and end"):
            deadair.load(path)

    def test_rejects_reversed_segment_times(self):
        path = self.write_temp(".json", json.dumps([
            {"start": 4, "end": 2, "text": "invalid range"}
        ]))
        with self.assertRaisesRegex(ValueError, "invalid time range"):
            deadair.load(path)


if __name__ == "__main__":
    unittest.main()
