from __future__ import annotations

import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox

from animatube.ai.mock_providers import MockMusicProvider
from animatube.ai.models import AIGenerationJob, JobStatus, MusicPrompt
from animatube.ai.music_worker import MusicGenerationWorker
from animatube.core.models import Project
from animatube.ui.music_studio_dialog import MusicStudioDialog, QAudioOutput, QMediaPlayer


def wait_worker(worker, timeout=5.0):
    start = time.time()
    while not worker.isFinished() and (time.time() - start) < timeout:
        QApplication.processEvents()
        time.sleep(0.01)
    QApplication.processEvents()


class AIMusicStudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @unittest.skipIf(QMediaPlayer is None or QAudioOutput is None, "Qt Multimedia is unavailable")
    def test_music_dialog_owns_and_detaches_audio_output(self):
        dialog = MusicStudioDialog(Project(name="Audio lifecycle test"))
        player = dialog.player
        audio_output = dialog.audio_output
        self.assertIsNotNone(player)
        self.assertIsNotNone(audio_output)
        self.assertIs(audio_output.parent(), player)
        self.assertIs(player.audioOutput(), audio_output)

        dialog.close()

        self.assertIsNone(player.audioOutput())

    def test_music_prompt_validation(self):
        prompt = MusicPrompt(prompt="Happy preschool song", duration_seconds=15.0)
        prompt.validate()

        invalid_dur = MusicPrompt(prompt="Valid", duration_seconds=500.0)
        with self.assertRaises(ValueError):
            invalid_dur.validate()

        empty_prompt = MusicPrompt(prompt="   ", mood="")
        with self.assertRaises(ValueError):
            empty_prompt.validate()

    def test_music_worker_generation(self):
        provider = MockMusicProvider()
        prompt = MusicPrompt(prompt="Playful cartoon intro", mood="cheerful", duration_seconds=3.0)

        with tempfile.TemporaryDirectory() as tmp_dir:
            worker = MusicGenerationWorker(provider, prompt, tmp_dir)
            finished_jobs = []
            progress_updates = []

            worker.generation_finished.connect(lambda job: finished_jobs.append(job))
            worker.progress_changed.connect(lambda p, msg: progress_updates.append((p, msg)))

            worker.start()
            wait_worker(worker)

            self.assertEqual(len(finished_jobs), 1)
            job = finished_jobs[0]
            self.assertEqual(job.status, JobStatus.COMPLETED)
            self.assertTrue(Path(job.result_path).is_file())
            self.assertGreater(len(progress_updates), 0)

    def test_music_worker_cancellation(self):
        provider = MockMusicProvider()
        prompt = MusicPrompt(prompt="Long lullaby track", duration_seconds=10.0)

        with tempfile.TemporaryDirectory() as tmp_dir:
            worker = MusicGenerationWorker(provider, prompt, tmp_dir)
            worker.cancel()
            worker.start()
            wait_worker(worker)
            self.assertTrue(worker._is_cancelled)

    def test_music_worker_error_handling(self):
        provider = MockMusicProvider()
        prompt = MusicPrompt(prompt="Error track", extra_params={"simulate_error": "Synthesis pipe broken"})

        with tempfile.TemporaryDirectory() as tmp_dir:
            worker = MusicGenerationWorker(provider, prompt, tmp_dir)
            errors = []
            worker.error_occurred.connect(lambda err: errors.append(err))

            worker.start()
            wait_worker(worker)

            self.assertEqual(len(errors), 1)
            self.assertIn("Synthesis pipe broken", errors[0])

    def test_music_studio_dialog_workflow(self):
        project = Project(name="Test Music Project")
        selected_bgm = []

        def on_bgm(path):
            selected_bgm.append(path)

        with tempfile.TemporaryDirectory() as tmp_dir:
            proj_file = str(Path(tmp_dir) / "test.anima")
            dialog = MusicStudioDialog(project, project_file=proj_file, on_bgm_selected=on_bgm)
            try:
                # Track type toggle
                self.assertTrue(dialog.radio_bgm.isChecked())
                self.assertEqual(dialog.btn_generate.text(), "Compose Music")

                # Switch to SFX
                dialog.radio_sfx.setChecked(True)
                self.assertEqual(dialog.btn_generate.text(), "Generate SFX")
                self.assertEqual(dialog.combo_genre.currentText(), "Cartoon SFX")

                # Switch to Song
                dialog.radio_song.setChecked(True)
                self.assertEqual(dialog.btn_generate.text(), "Compose Theme Song")

                # Switch back to BGM
                dialog.radio_bgm.setChecked(True)

                # Generate a track
                dialog.spin_duration.setValue(2.0)
                dialog.edit_prompt.setPlainText("Whimsical upbeat rhythm")

                dialog._on_generate_clicked()
                self.assertIsNotNone(dialog.active_worker)
                wait_worker(dialog.active_worker)

                self.assertIsNotNone(dialog.current_job)
                self.assertEqual(dialog.current_job.status, JobStatus.COMPLETED)
                self.assertEqual(dialog.history_table.rowCount(), 1)
                self.assertTrue(dialog.btn_play.isEnabled())
                self.assertTrue(dialog.btn_set_bgm.isEnabled())

                # Test BGM assignment callback
                with patch.object(QMessageBox, "information"):
                    dialog._on_set_bgm_clicked()
                self.assertEqual(len(selected_bgm), 1)
                self.assertTrue(Path(selected_bgm[0]).is_file())

            finally:
                dialog.close()


if __name__ == "__main__":
    unittest.main()
