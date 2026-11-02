from __future__ import annotations

import os
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from animatube.core.models import Project
from animatube.presets.little_dreamers import (
    BRAND_NAME,
    LITTLE_DREAMERS_CHARACTERS,
    LITTLE_DREAMERS_EDUCATIONAL_THEMES,
    apply_little_dreamers_preset,
    create_little_dreamers_project,
    get_character_prompt,
    get_little_dreamers_characters,
)
from animatube.ui.main_window import MainWindow
from animatube.ui.video_studio_dialog import VideoStudioDialog


class LittleDreamersPresetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_character_definitions_complete(self):
        chars = get_little_dreamers_characters()
        self.assertEqual(len(chars), 6)
        names = {c["name"] for c in chars}
        self.assertEqual(names, {"Aarav", "Mia", "Ellie", "Gigi", "Bobo", "Twinkle"})

        for c in chars:
            self.assertIn("anchor_image", c)
            self.assertIn("voice_id", c)
            self.assertIn("identity_tokens", c)
            self.assertIn("costume_lock", c)
            self.assertIn("actions", c)
            self.assertGreater(len(c["actions"]), 0)
            self.assertIn("negative_prompt", c)

    def test_get_character_prompt_generation(self):
        prompt = get_character_prompt("aarav", "joyful_wave")
        self.assertIn("Aarav", prompt.prompt)
        self.assertIn("preschool wave", prompt.prompt)
        self.assertEqual(prompt.aspect_ratio, "16:9")
        self.assertEqual(prompt.camera_motion, "pan_right")
        self.assertIn("realistic human", prompt.negative_prompt)

        with self.assertRaises(KeyError):
            get_character_prompt("unknown_character")

    def test_create_little_dreamers_project(self):
        proj = create_little_dreamers_project(theme_id="counting_1_10")
        self.assertEqual(proj.width, 1920)
        self.assertEqual(proj.height, 1080)
        self.assertEqual(proj.fps, 24)
        self.assertEqual(proj.background, "#1a103c")
        self.assertGreaterEqual(len(proj.scenes), 4)

        # Check scene durations are properly aligned to 24fps
        for scene in proj.scenes:
            self.assertGreater(scene.duration_frames, 0)
            self.assertGreater(len(scene.layers), 0)

    def test_apply_little_dreamers_preset_to_existing(self):
        proj = Project(name="Custom Project", width=1280, height=720, fps=30)
        applied = apply_little_dreamers_preset(proj)
        self.assertEqual(applied.width, 1920)
        self.assertEqual(applied.height, 1080)
        self.assertEqual(applied.fps, 24)
        self.assertEqual(applied.background, "#1a103c")

    def test_video_studio_character_preset_selection(self):
        proj = Project(name="Test Video Preset Project")
        dialog = VideoStudioDialog(proj)
        try:
            self.assertGreater(dialog.char_preset_combo.count(), 6)
            
            # Select Aarav
            idx = dialog.char_preset_combo.findData("aarav")
            self.assertGreaterEqual(idx, 0)
            dialog.char_preset_combo.setCurrentIndex(idx)

            self.assertTrue(dialog.radio_i2v.isChecked())
            self.assertIn("Aarav", dialog.prompt_input.toPlainText())
            self.assertIn("realistic human", dialog.negative_prompt.text())
            self.assertTrue(dialog.ref_path_input.text().endswith(".png"))
        finally:
            dialog.close()

    def test_main_window_load_little_dreamers_preset(self):
        window = MainWindow()
        try:
            window.load_little_dreamers_preset(theme_id="counting_1_10")
            self.assertEqual(window.project.fps, 24)
            self.assertEqual(window.project.width, 1920)
            self.assertEqual(window.project.height, 1080)
            self.assertIn("Counting 1 to 10", window.project.name)
            self.assertGreaterEqual(len(window.project.scenes), 4)
            self.assertIn("Little Dreamers", window.statusBar().currentMessage())
        finally:
            window.close()


if __name__ == "__main__":
    unittest.main()
