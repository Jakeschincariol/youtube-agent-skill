import json
import os
import sys
import tempfile
import unittest

# Allow running from repo root or test directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import swipe  # noqa: E402


class TestSwipeFormatSeparation(unittest.TestCase):
    def setUp(self):
        # Channel A has 4 Shorts (~102.5k median) and 4 Long videos (~10k median)
        # If mixed together, median would be ~55k and a 40k long-form outlier (4x) would be missed!
        self.sample_videos = [
            {"channel": "ChanA", "title": "Short 1", "views": 90_000, "duration": 30},
            {"channel": "ChanA", "title": "Short 2", "views": 100_000, "duration": 45},
            {"channel": "ChanA", "title": "Short 3", "views": 110_000, "duration": 59},
            {"channel": "ChanA", "title": "Short 4", "views": 105_000, "duration": 60},
            {"channel": "ChanA", "title": "Long 1", "views": 10_000, "duration": 600},
            {"channel": "ChanA", "title": "Long 2", "views": 10_000, "duration": 720},
            {"channel": "ChanA", "title": "Long 3", "views": 10_000, "duration": 800},
            {"channel": "ChanA", "title": "Why I quit 3 tools", "views": 40_000, "duration": 900},
        ]

    def test_video_format_classification(self):
        self.assertEqual(swipe.video_format(45, shorts_max=60), "shorts")
        self.assertEqual(swipe.video_format(60, shorts_max=60), "shorts")
        self.assertEqual(swipe.video_format(61, shorts_max=60), "long")
        self.assertEqual(swipe.video_format(150, shorts_max=180), "shorts")
        self.assertEqual(swipe.video_format(None), "unknown")
        self.assertEqual(swipe.video_format(0), "unknown")

    def test_separate_medians_surface_long_outlier(self):
        out, thin, _ = swipe.analyze(self.sample_videos, min_multiple=2.0, fmt_filter="all")
        self.assertEqual(thin, [])
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["title"], "Why I quit 3 tools")
        self.assertEqual(out[0]["format"], "long")
        self.assertEqual(out[0]["median"], 10_000)
        self.assertEqual(out[0]["multiple"], 4.0)

    def test_filter_shorts_only(self):
        out, thin, _ = swipe.analyze(self.sample_videos, min_multiple=0.0, fmt_filter="shorts")
        self.assertEqual(thin, [])
        self.assertTrue(all(r["format"] == "shorts" for r in out))
        self.assertEqual(len(out), 4)

    def test_thin_format_bucket_skipped_independently(self):
        videos = self.sample_videos[:4] + [
            {"channel": "ChanA", "title": "Only 1 Long", "views": 500_000, "duration": 700}
        ]
        out, thin, _ = swipe.analyze(videos, min_multiple=0.0, fmt_filter="all")
        self.assertEqual(len(thin), 1)
        self.assertEqual(thin[0], ("ChanA", "long", 1))
        self.assertTrue(all(r["format"] == "shorts" for r in out))

    def test_missing_duration_backward_compatible(self):
        no_dur = [
            {"channel": "ChanB", "title": "V1", "views": 1_000},
            {"channel": "ChanB", "title": "V2", "views": 1_000},
            {"channel": "ChanB", "title": "V3", "views": 1_000},
            {"channel": "ChanB", "title": "V4", "views": 3_000},
        ]
        out, thin, _ = swipe.analyze(no_dur, min_multiple=2.0, fmt_filter="all")
        self.assertEqual(thin, [])
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["format"], "unknown")
        self.assertEqual(out[0]["multiple"], 3.0)

    def test_utf8_cli_execution(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as tf:
            json.dump([
                {"channel": "Kênh Việt", "title": "Video 1", "views": 1000, "duration": 300},
                {"channel": "Kênh Việt", "title": "Video 2", "views": 1000, "duration": 300},
                {"channel": "Kênh Việt", "title": "Video 3", "views": 1000, "duration": 300},
                {"channel": "Kênh Việt", "title": "Tại sao 90% thất bại 🚀", "views": 5000, "duration": 300},
            ], tf, ensure_ascii=False)
            path = tf.name
        try:
            swipe.main([path, "--min", "2.0", "--format", "long", "--json"])
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()