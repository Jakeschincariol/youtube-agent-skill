from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

from animatube.core.models import Project, Scene
from animatube.ui.main_window import MainWindow


class AIEditorIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = MainWindow()
        self.window.show()
        self.app.processEvents()

    def tearDown(self):
        self.window.close()
        self.app.processEvents()

    def test_ai_studio_toolbar_buttons_exist(self):
        buttons = {b.text(): b for b in self.window.findChildren(QPushButton)}
        self.assertIn("AI Video", buttons)
        self.assertIn("AI Music", buttons)
        self.assertIn("Audio Studio", buttons)

    def test_import_ai_video_creates_timeline_scene(self):
        initial_scene_count = len(self.window.project.scenes)
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(b"mock video data")
            video_file = tmp.name

        try:
            self.window.import_ai_video(video_file, duration_seconds=3.0)
            self.assertEqual(len(self.window.project.scenes), initial_scene_count + 1)
            
            new_scene = self.window.project.scenes[-1]
            self.assertIn("AI Scene", new_scene.name)
            self.assertEqual(new_scene.duration_frames, int(3.0 * self.window.project.fps))
            self.assertEqual(len(new_scene.layers), 1)
            self.assertEqual(new_scene.layers[0].asset_path, video_file)
            self.assertEqual(self.window.scene_index, len(self.window.project.scenes) - 1)
        finally:
            if os.path.exists(video_file):
                os.remove(video_file)

    def test_set_bgm_updates_project_and_status(self):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(b"mock audio data")
            audio_file = tmp.name

        try:
            self.assertIsNone(self.window.bgm_path)
            self.window.set_bgm(audio_file)
            self.assertEqual(self.window.bgm_path, audio_file)
            self.assertIn(Path(audio_file).name, self.window.statusBar().currentMessage())
        finally:
            if os.path.exists(audio_file):
                os.remove(audio_file)

    def test_open_video_and_music_studios(self):
        with patch("animatube.ui.video_studio_dialog.VideoStudioDialog.exec") as mock_v_exec:
            self.window.open_video_studio()
            self.assertTrue(mock_v_exec.called)

        with patch("animatube.ui.music_studio_dialog.MusicStudioDialog.exec") as mock_m_exec:
            self.window.open_music_studio()
            self.assertTrue(mock_m_exec.called)


if __name__ == "__main__":
    unittest.main()
