import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "yt-script" / "hookscore.py"
sys.path.insert(0, str(SCRIPT.parent))
import hookscore


class HookScoreTests(unittest.TestCase):
    def test_formula_reference_contains_21_entries(self):
        self.assertEqual(len(hookscore.FORMULAS), 21)

    def test_score_has_five_bounded_properties_and_heuristic_label(self):
        result = hookscore.score("You are wasting time on this deployment mistake?")
        self.assertEqual(set(result["properties"]), {
            "SPECIFICITY", "ADDRESS", "STAKES", "CURIOSITY", "BREVITY"
        })
        self.assertTrue(all(0 <= value <= 100 for value in result["properties"].values()))
        self.assertEqual(result["score_type"], "editorial_heuristic_not_performance_prediction")
        self.assertIn(result["band"], {"STRONG", "WORKABLE", "WEAK"})

    def test_empty_and_non_string_hooks_are_rejected(self):
        for value in ("", "  ", None, 42):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "non-empty"):
                    hookscore.score(value)

    def test_empty_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "empty.txt"
            path.write_text(" \n\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "no non-empty"):
                hookscore.read_hooks(path)

    def test_utf8_file_is_read_and_blank_lines_are_ignored(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "hooks.txt"
            path.write_text("Cómo funciona tu pipeline?\n\nA second hook\n", encoding="utf-8")
            self.assertEqual(hookscore.read_hooks(path), ["Cómo funciona tu pipeline?", "A second hook"])

    def test_missing_file_is_reported(self):
        with self.assertRaisesRegex(ValueError, "cannot read hook file"):
            hookscore.read_hooks("this-file-does-not-exist.txt")

    def test_cli_json_contains_score_type_and_sorted_results(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "hooks.txt"
            path.write_text("A short line\nYou are wasting time on this deployment mistake?\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--json", str(path)],
                capture_output=True, text=True, check=True,
            )
        payload = json.loads(result.stdout)
        self.assertEqual(len(payload), 2)
        self.assertGreaterEqual(payload[0]["verdict"], payload[1]["verdict"])
        self.assertTrue(all(item["score_type"] == hookscore.SCORE_TYPE for item in payload))

    def test_cli_scores_single_hook(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--hook", "How do you fix a failed deployment?"],
            capture_output=True, text=True, check=True,
        )
        self.assertIn("editorial heuristic only", result.stdout)
        self.assertIn("formula", result.stdout)

    def test_cli_missing_source_uses_argparse_error(self):
        result = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)

    def test_cli_missing_hook_value_uses_argparse_error(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--hook"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("argument --hook: expected one argument", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_cli_missing_file_returns_nonzero(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "missing-hooks.txt"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("cannot read hook file", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_cli_rejects_both_file_and_hook(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "hooks.txt", "--hook", "another hook"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("not allowed with argument", result.stderr)


if __name__ == "__main__":
    unittest.main()
