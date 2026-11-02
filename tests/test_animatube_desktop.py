import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication, QFileDialog, QInputDialog, QPushButton

from animatube.core.models import Layer, Project, Scene
from animatube.core.project import load_project
from animatube.export.renderer import export_scene, render_frame
from animatube.ui.main_window import MainWindow


class AnimaTubeDesktopTests(unittest.TestCase):
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

    def test_main_window_and_canvas_render_visible_content(self):
        with patch.object(QInputDialog, "getText", return_value=("AnimaTube", True)):
            next(button for button in self.window.findChildren(QPushButton) if button.text() == "Add text").click()
        self.app.processEvents()
        self.assertGreater(self.window.width(), 0)
        self.assertFalse(self.window.grab().toImage().isNull())
        self.assertEqual(len(self.window.canvas.items_by_id), 1)

    def test_add_select_and_switch_scene_and_timeline(self):
        layer = Layer(name="Title", kind="text", text="Test")
        self.window.add_layer(layer)
        self.assertEqual(self.window.layer_list.count(), 1)
        self.assertIsNotNone(self.window.selected_layer())
        self.window.add_scene()
        self.assertEqual(self.window.scene_index, 1)
        self.window.frame_slider.setValue(12)
        self.app.processEvents()
        self.assertEqual(self.window.current_frame, 12)
        self.window.scene_picker.setCurrentIndex(0)
        self.app.processEvents()
        self.assertEqual(self.window.scene_index, 0)
        self.assertEqual(self.window.layer_list.count(), 1)

    def test_image_import_and_project_save_reopen(self):
        with tempfile.TemporaryDirectory() as directory:
            image_path = Path(directory) / "source.png"
            image = QImage(32, 24, QImage.Format.Format_ARGB32)
            image.fill(QColor("#ff8800"))
            self.assertTrue(image.save(str(image_path)))

            with patch.object(QFileDialog, "getOpenFileName", return_value=(str(image_path), "Images")):
                next(button for button in self.window.findChildren(QPushButton) if button.text() == "Image").click()
            self.assertEqual(self.window.active_scene.layers[0].kind, "image")

            project_path = Path(directory) / "roundtrip.anima"
            with patch.object(QFileDialog, "getSaveFileName", return_value=(str(project_path), "AnimaTube project")):
                self.window.save_project()
            self.assertTrue(project_path.is_file())

            restored = load_project(project_path)
            restored_image = restored.resolve_asset(restored.scenes[0].layers[0].asset_path)
            self.assertTrue(restored_image.is_file())

            other = MainWindow()
            try:
                with patch.object(QFileDialog, "getOpenFileName", return_value=(str(project_path), "AnimaTube project")):
                    other.open_project()
                self.assertEqual(other.active_scene.layers[0].kind, "image")
                self.assertEqual(other.active_scene.layers[0].name, "source")
            finally:
                other.close()

    def test_renderer_produces_nonempty_frame(self):
        project = Project(width=64, height=64, scenes=[
            Scene(duration_frames=2, layers=[Layer(kind="rect", width=32, height=32, color="#ff0000")])
        ])
        frame = render_frame(project, project.scenes[0], 0, 64, 64)
        self.assertFalse(frame.isNull())
        self.assertEqual(frame.width(), 64)
        self.assertEqual(frame.height(), 64)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg/ffprobe not installed")
    def test_ffmpeg_export_creates_probeable_mp4(self):
        project = Project(width=64, height=64, fps=24, scenes=[
            Scene(duration_frames=2, layers=[Layer(kind="rect", width=32, height=32, color="#00ff00")])
        ])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "smoke.mp4"
            result = export_scene(project, project.scenes[0], output, profile="square", resolution="720p")
            self.assertTrue(result.is_file())
            self.assertGreater(result.stat().st_size, 100)
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-select_streams", "v:0",
                 "-show_entries", "stream=codec_name,width,height",
                 "-of", "default=noprint_wrappers=1", str(result)],
                check=True, capture_output=True, text=True,
            )
            self.assertIn("codec_name=h264", probe.stdout)
            self.assertIn("width=720", probe.stdout)
            self.assertIn("height=720", probe.stdout)


if __name__ == "__main__":
    unittest.main()
