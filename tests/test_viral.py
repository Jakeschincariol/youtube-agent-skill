import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "yt-viral" / "swipe.py"
sys.path.insert(0, str(SCRIPT.parent))
import swipe


class ViralAnalysisTests(unittest.TestCase):
    def make_video(self, title, views, channel="Creator", fmt="long", age=None, duration=600):
        row = {"channel": channel, "title": title, "views": views,
               "format": fmt, "duration": duration}
        if age is not None:
            row["age_days"] = age
        return row

    def test_raw_view_comparison_within_channel_and_format(self):
        data = [self.make_video(f"Long {i}", views) for i, views in enumerate([100, 100, 100, 400])]
        report = swipe.analyze(swipe.load_videos_from_data(data), minimum=1.5)
        self.assertEqual(len(report["outliers"]), 1)
        self.assertEqual(report["outliers"][0]["multiple"], 4.0)
        self.assertFalse(report["outliers"][0]["age_adjusted"])

    def test_shorts_and_long_form_are_separate_cohorts(self):
        data = [self.make_video(f"Long {i}", v, fmt="long") for i, v in enumerate([100, 100, 100, 400])]
        data += [self.make_video(f"Short {i}", v, fmt="short", duration=45) for i, v in enumerate([1000] * 4)]
        report = swipe.analyze(swipe.load_videos_from_data(data))
        self.assertEqual(len(report["outliers"]), 1)
        self.assertEqual(report["outliers"][0]["format"], "long")

    def test_age_adjusted_comparison_uses_views_per_day(self):
        data = [self.make_video(f"Video {i}", views, age=age)
                for i, (views, age) in enumerate([(1000, 10), (2000, 20), (3000, 30), (12000, 10)])]
        report = swipe.analyze(swipe.load_videos_from_data(data))
        self.assertEqual(len(report["outliers"]), 1)
        self.assertEqual(report["outliers"][0]["metric"], "views_per_day")
        self.assertEqual(report["outliers"][0]["multiple"], 4.0)

    def test_age_and_non_age_rows_are_not_mixed(self):
        data = [self.make_video(f"Age {i}", 1000, age=10) for i in range(4)]
        data += [self.make_video(f"Raw {i}", 1000) for i in range(4)]
        report = swipe.analyze(swipe.load_videos_from_data(data))
        self.assertEqual({row["metric"] for row in report["outliers"]}, {"views_per_day", "views"})

    def test_channels_are_never_compared_against_each_other(self):
        data = [self.make_video(f"A{i}", 100, channel="A") for i in range(4)]
        data += [self.make_video(f"B{i}", 10000, channel="B") for i in range(4)]
        report = swipe.analyze(swipe.load_videos_from_data(data))
        self.assertEqual(report["outliers"], [])

    def test_small_cohorts_are_skipped_with_reason(self):
        data = [self.make_video(f"Video {i}", 100) for i in range(3)]
        report = swipe.analyze(swipe.load_videos_from_data(data))
        self.assertEqual(report["outliers"], [])
        self.assertEqual(report["skipped_cohorts"][0]["video_count"], 3)

    def test_duration_fallback_labels_format_as_inferred(self):
        row = {"channel": "C", "title": "Short", "views": 10, "duration": 60}
        video = swipe.load_videos_from_data([row])[0]
        self.assertEqual(video["format"], "short")
        self.assertEqual(video["format_source"], "inferred_from_duration")

    def test_explicit_format_overrides_duration_heuristic(self):
        row = {"channel": "C", "title": "Video", "views": 10, "duration": 60, "format": "long"}
        video = swipe.load_videos_from_data([row])[0]
        self.assertEqual(video["format"], "long")
        self.assertEqual(video["format_source"], "provided")

    def test_rejects_negative_views(self):
        with self.assertRaisesRegex(ValueError, "views"):
            swipe.load_videos_from_data([self.make_video("Bad", -1)])

    def test_rejects_invalid_format(self):
        row = self.make_video("Bad", 100)
        row["format"] = "medium"
        with self.assertRaisesRegex(ValueError, "format"):
            swipe.load_videos_from_data([row])

    def test_rejects_invalid_age(self):
        with self.assertRaisesRegex(ValueError, "age_days"):
            swipe.load_videos_from_data([self.make_video("Bad", 100, age=0)])

    def test_accepts_object_with_videos_key(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "videos.json"
            path.write_text(json.dumps({"videos": [self.make_video("One", 10)]}), encoding="utf-8")
            self.assertEqual(len(swipe.load_videos(path)), 1)

    def test_cli_json_output(self):
        data = [self.make_video(f"Video {i}", value) for i, value in enumerate([100, 100, 100, 400])]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "videos.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPT), str(path), "--json"],
                                    capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout)["outliers"][0]["multiple"], 4.0)

    def test_cli_reports_malformed_input_without_traceback(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.json"
            path.write_text('{"not_videos": []}', encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPT), str(path)],
                                    capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("viral analysis failed", result.stderr)


if __name__ == "__main__":
    unittest.main()
