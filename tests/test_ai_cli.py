from __future__ import annotations

import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from animatube.ai.cli import main


class AICLITests(unittest.TestCase):
    def test_cli_providers_list(self):
        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            ret = main(["providers", "--type", "all"])
        self.assertEqual(ret, 0)
        out = stdout_buf.getvalue()
        self.assertIn("mock_video", out)
        self.assertIn("mock_voice", out)
        self.assertIn("mock_music", out)

    def test_cli_video_generation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            stdout_buf = io.StringIO()
            with patch("sys.stdout", stdout_buf):
                ret = main([
                    "video",
                    "--prompt", "Aarav playing in garden",
                    "--duration", "1.5",
                    "--output-dir", tmp_dir,
                ])
            self.assertEqual(ret, 0)
            out = stdout_buf.getvalue()
            self.assertIn("COMPLETED", out)
            self.assertIn("Output Video:", out)
            self.assertEqual(len(list(Path(tmp_dir).glob("*.mp4"))), 1)

    def test_cli_voice_generation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            stdout_buf = io.StringIO()
            with patch("sys.stdout", stdout_buf):
                ret = main([
                    "voice",
                    "--text", "Hello, little explorers!",
                    "--character", "Twinkle",
                    "--voice-id", "twinkle_star",
                    "--output-dir", tmp_dir,
                ])
            self.assertEqual(ret, 0)
            out = stdout_buf.getvalue()
            self.assertIn("COMPLETED", out)
            self.assertIn("Output Audio:", out)
            self.assertEqual(len(list(Path(tmp_dir).glob("*.wav"))), 1)

    def test_cli_music_and_sfx_generation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            stdout_buf = io.StringIO()
            with patch("sys.stdout", stdout_buf):
                ret = main([
                    "music",
                    "--prompt", "Magical sparkle chime",
                    "--mood", "playful",
                    "--duration", "3.0",
                    "--sfx",
                    "--output-dir", tmp_dir,
                ])
            self.assertEqual(ret, 0)
            out = stdout_buf.getvalue()
            self.assertIn("COMPLETED", out)
            self.assertIn("Output Track:", out)
            self.assertEqual(len(list(Path(tmp_dir).glob("*.wav"))), 1)

    def test_cli_credentials_management(self):
        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            ret_set = main(["credentials", "set", "mock_key_test", "sk-secret-test-12345"])
            self.assertEqual(ret_set, 0)

            ret_get = main(["credentials", "get", "mock_key_test"])
            self.assertEqual(ret_get, 0)

            ret_list = main(["credentials", "list"])
            self.assertEqual(ret_list, 0)

        out = stdout_buf.getvalue()
        self.assertIn("mock_key_test", out)
        self.assertIn("sk-s...2345", out)


if __name__ == "__main__":
    unittest.main()
