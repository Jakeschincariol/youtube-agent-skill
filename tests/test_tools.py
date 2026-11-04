import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "yt-script"))
sys.path.insert(0, str(ROOT / "skills" / "yt-chapters"))

import chapters
import hookscore


LOUDNESS_PATH = ROOT / "skills" / "yt-edit" / "loudness.py"
LOUDNESS_SPEC = importlib.util.spec_from_file_location("loudness", LOUDNESS_PATH)
loudness = importlib.util.module_from_spec(LOUDNESS_SPEC)
LOUDNESS_SPEC.loader.exec_module(loudness)


class HookscoreTests(unittest.TestCase):
    def test_direct_address_wins_over_overlapping_superlative(self):
        examples = (
            "If you have under a thousand subscribers, this is the only video you need this week.",
            "If you want more views, this is the only video you need this week.",
            "If you can grow a channel, this is the only video you need this week.",
        )
        for hook in examples:
            with self.subTest(hook=hook):
                self.assertEqual(hookscore.classify(hook)[0], "The Direct Address")

    def test_question_does_not_match_do_not_warning(self):
        patterns = next(
            formula["match"]
            for formula in hookscore.FORMULAS
            if formula["id"] == "the-question"
        )
        self.assertFalse(__import__("re").search(patterns[0], "Do not upload this", __import__("re").I))


class ChapterTests(unittest.TestCase):
    def test_documented_spoken_signposts_are_recognized(self):
        for text in ("Now, humans", "Okay, so what", "Now a twist.", "Reason number two"):
            with self.subTest(text=text):
                self.assertTrue(chapters.signpost(text))

    def test_explicit_target_fails_if_transcript_cannot_supply_it(self):
        cues = [(0, 5, "Opening topic")]
        cues.extend(
            (index * 12, 5, "Ordinary narration section {}".format(index))
            for index in range(1, 6)
        )
        lines = []
        for index, (start, end, text) in enumerate(cues, 1):
            start_minutes, start_seconds = divmod(start, 60)
            end_minutes, end_seconds = divmod(end, 60)
            lines.extend(
                [
                    str(index),
                    "00:{:02d}:{:02d},000 --> 00:{:02d}:{:02d},000".format(
                        start_minutes, start_seconds, end_minutes, end_seconds
                    ),
                    text,
                    "",
                ]
            )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".srt", encoding="utf-8") as transcript:
            transcript.write("\n".join(lines))
            transcript.flush()
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "skills" / "yt-chapters" / "chapters.py"),
                    transcript.name,
                    "--target",
                    "8",
                    "--json",
                ],
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("only", result.stdout)
        self.assertIn("valid boundaries", result.stdout)


class LoudnessTests(unittest.TestCase):
    def test_silence_is_reported_as_unmeasurable(self):
        stderr = (
            "Summary:\n"
            "Integrated loudness:\n"
            "I: -inf LUFS\n"
            "Loudness range:\n"
            "LRA: 0.0 LU\n"
            "True peak:\n"
            "Peak: -inf dBFS\n"
        )
        result = type("FFmpegResult", (), {"stderr": stderr})()
        with patch.object(loudness.subprocess, "run", return_value=result):
            measured = loudness.measure("silent.wav")
        self.assertEqual(measured, {"lufs": None, "lra": 0.0, "true_peak": None})
        self.assertEqual(loudness.verdict(measured)[0][0], "UNMEASURABLE")


class ManifestTests(unittest.TestCase):
    def test_json_manifests_parse(self):
        paths = (
            ROOT / ".claude-plugin" / "marketplace.json",
            ROOT / ".claude-plugin" / "plugin.json",
            ROOT / "skills" / "yt-script" / "hooks.json",
        )
        for path in paths:
            with self.subTest(path=path):
                json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
