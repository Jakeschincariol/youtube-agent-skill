import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "yt-package" / "title.py"
sys.path.insert(0, str(SCRIPT.parent))
import title


class PackageTitleTests(unittest.TestCase):
    def test_accepts_title_at_youtube_limit(self):
        result = title.check("x" * 100)
        self.assertTrue(result["valid"])
        self.assertEqual(result["chars"], 100)

    def test_rejects_title_over_youtube_limit(self):
        result = title.check("x" * 101)
        self.assertFalse(result["valid"])
        self.assertIn("title-limit", {issue["code"] for issue in result["issues"]})

    def test_does_not_claim_fixed_mobile_or_desktop_truncation(self):
        result = title.check("A useful title with a clear subject and outcome")
        codes = {issue["code"] for issue in result["issues"]}
        self.assertNotIn("mobile", codes)
        self.assertNotIn("desktop", codes)

    def test_does_not_require_a_number(self):
        result = title.check("How to automate a deployment safely")
        self.assertNotIn("no-number", {issue["code"] for issue in result["issues"]})

    def test_long_title_gets_advisory_not_validation_error(self):
        result = title.check("A" * 75)
        length_issue = next(i for i in result["issues"] if i["code"] == "length")
        self.assertEqual(length_issue["severity"], "suggestion")
        self.assertTrue(result["valid"])

    def test_empty_title_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "non-empty"):
            title.check("   ")

    def test_non_string_title_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "non-empty"):
            title.check(None)

    def test_three_all_caps_words_get_advisory(self):
        result = title.check("THIS IS A BIG CHANGE")
        self.assertIn("all-caps", {i["code"] for i in result["issues"]})

    def test_single_all_caps_word_is_not_flagged(self):
        result = title.check("AWS makes deployments safer")
        self.assertNotIn("all-caps", {i["code"] for i in result["issues"]})

    def test_generic_adjective_is_only_a_suggestion(self):
        result = title.check("The amazing deployment workflow")
        issue = next(i for i in result["issues"] if i["code"] == "generic-wording")
        self.assertEqual(issue["severity"], "suggestion")
        self.assertTrue(result["valid"])

    def test_thumbnail_duplication_detects_meaningful_overlap(self):
        result = title.check("Automate your deployment pipeline", "AUTOMATE DEPLOYMENT")
        self.assertIn("pair-duplication", {i["code"] for i in result["issues"]})

    def test_single_shared_word_is_not_automatically_duplication(self):
        result = title.check("Build a better deployment pipeline", "DEPLOYMENT")
        self.assertNotIn("pair-duplication", {i["code"] for i in result["issues"]})

    def test_long_thumbnail_text_gets_readability_suggestion(self):
        result = title.check("A useful title", "ONE TWO THREE FOUR FIVE")
        self.assertIn("thumbnail-readability", {i["code"] for i in result["issues"]})

    def test_score_is_explicitly_labelled_heuristic(self):
        result = title.check("A useful title")
        self.assertEqual(result["score_type"], "editorial_heuristic_not_performance_prediction")

    def test_reads_utf8_title_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "titles.txt"
            path.write_text("First title\nSecond title\n", encoding="utf-8")
            self.assertEqual(title.read_titles(path), ["First title", "Second title"])

    def test_empty_title_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "empty.txt"
            path.write_text(" \n\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "no non-empty"):
                title.read_titles(path)

    def test_cli_json_output(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--title", "A useful DevOps title", "--json"],
            capture_output=True, text=True, check=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload[0]["title"], "A useful DevOps title")
        self.assertEqual(payload[0]["score_type"], "editorial_heuristic_not_performance_prediction")

    def test_cli_missing_argument_has_argparse_error(self):
        result = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)

    def test_cli_missing_file_returns_clean_error(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "missing-titles-file.txt"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("title packaging check failed", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
