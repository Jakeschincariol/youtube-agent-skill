import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "yt-retention" / "retention.py"
sys.path.insert(0, str(SCRIPT.parent))
import retention


class RetentionAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.seconds_rows = [
            (0, 100), (10, 90), (20, 82), (30, 75),
            (40, 70), (50, 68), (60, 62), (70, 60),
            (80, 58), (90, 55),
        ]

    def test_short_video_seconds_axis_is_not_mistaken_for_percent(self):
        report = retention.analyze(self.seconds_rows, duration=90)
        self.assertEqual(report["axis"], "seconds")
        self.assertEqual(report["hook_cutoff"], 30)
        self.assertEqual(report["hook_end"], 75)

    def test_percent_axis_uses_duration_to_find_30_seconds(self):
        rows = [(x, y) for x, y in zip(
            range(0, 101, 10), [100, 90, 82, 75, 70, 68, 62, 60, 58, 55, 50]
        )]
        report = retention.analyze(rows, duration=600)
        self.assertEqual(report["axis"], "percent")
        self.assertEqual(report["hook_cutoff"], 5)
        self.assertEqual(report["hook_end"], 95)
        self.assertEqual(report["cliffs"][0]["at_seconds"], 30.0)

    def test_hook_retention_is_interpolated_at_30_seconds(self):
        rows = [(0, 100), (10, 90), (25, 80), (40, 60),
                (50, 58), (60, 55), (70, 52), (80, 50)]
        report = retention.analyze(rows, axis="seconds")
        self.assertEqual(report["hook_end"], 73.33)
        self.assertAlmostEqual(report["hook_leak"], 26.67, places=2)

    def test_zero_start_retention_is_not_replaced_with_100(self):
        rows = [(x, 0) for x in range(0, 80, 10)]
        report = retention.analyze(rows, axis="seconds")
        self.assertEqual(report["start"], 0)
        self.assertEqual(report["hook_leak"], 0)

    def test_auto_axis_requires_explicit_choice_for_ambiguous_short_range(self):
        with self.assertRaisesRegex(ValueError, "specify --axis"):
            retention.analyze(self.seconds_rows[:8])
        report = retention.analyze(self.seconds_rows[:8], axis="seconds")
        self.assertEqual(report["axis"], "seconds")

    def test_csv_skips_header_and_reads_percent_signs(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "retention.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["Position", "Still watching"])
                for x in range(0, 80, 10):
                    writer.writerow([x, f"{100 - x / 2}%"])
            rows = retention.load_csv(path)
        self.assertEqual(len(rows), 8)
        self.assertEqual(rows[0], (0, 100))

    def test_csv_rejects_out_of_range_retention(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.csv"
            path.write_text("0,110\n10,90\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "between 0 and 100"):
                retention.load_csv(path)

    def test_csv_rejects_non_increasing_positions(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.csv"
            path.write_text("0,100\n10,90\n10,80\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "strictly increasing"):
                retention.load_csv(path)

    def test_duration_must_be_positive(self):
        with self.assertRaisesRegex(ValueError, "positive"):
            retention.analyze(self.seconds_rows, duration=0, axis="seconds")

    def test_cli_returns_clear_error_for_missing_transcript(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "retention.csv"
            path.write_text(
                "\n".join(f"{x},{100 - x / 2}" for x in range(0, 80, 10)),
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path), "--axis", "seconds",
                 "--transcript", str(Path(folder) / "missing.srt")],
                capture_output=True, text=True,
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("transcript file not found", result.stderr)

    def test_json_output_is_valid(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "retention.csv"
            path.write_text(
                "\n".join(f"{x},{100 - x / 2}" for x in range(0, 100, 10)),
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path), "--axis", "seconds", "--json"],
                capture_output=True, text=True, check=True,
            )
        report = json.loads(result.stdout)
        self.assertEqual(report["axis"], "seconds")
        self.assertEqual(report["points"], 10)


if __name__ == "__main__":
    unittest.main()
