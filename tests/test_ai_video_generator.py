import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox

from animatube.ai.mock_providers import MockVideoProvider
from animatube.ai.models import AIGenerationJob, JobStatus, VideoPrompt
from animatube.ai.video_worker import VideoGenerationWorker
from animatube.core.models import Project
from animatube.ui.video_studio_dialog import VideoStudioDialog


def wait_worker(worker, timeout=5.0):
    start = time.time()
    while not worker.isFinished() and (time.time() - start) < timeout:
        QApplication.processEvents()
        time.sleep(0.01)
    QApplication.processEvents()


class AIVideoGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_video_worker_successful_generation(self):
        provider = MockVideoProvider()
        prompt = VideoPrompt(prompt="Aarav waving to friends", duration_seconds=2.0)

        with tempfile.TemporaryDirectory() as tmp_dir:
            worker = VideoGenerationWorker(provider, prompt, tmp_dir)
            
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
            self.assertGreater(len(progress_updates), 1)

    def test_video_worker_cancellation(self):
        provider = MockVideoProvider()
        prompt = VideoPrompt(prompt="Long slow render", duration_seconds=5.0)

        with tempfile.TemporaryDirectory() as tmp_dir:
            worker = VideoGenerationWorker(provider, prompt, tmp_dir)
            cancelled_signals = []
            worker.cancelled.connect(lambda: cancelled_signals.append(True))

            worker.cancel()
            worker.start()
            wait_worker(worker)

            self.assertTrue(worker._is_cancelled)

    def test_video_worker_error_handling(self):
        provider = MockVideoProvider()
        prompt = VideoPrompt(prompt="Faulty prompt", extra_params={"simulate_error": "Connection lost"})

        with tempfile.TemporaryDirectory() as tmp_dir:
            worker = VideoGenerationWorker(provider, prompt, tmp_dir)
            errors = []
            worker.error_occurred.connect(lambda err: errors.append(err))

            worker.start()
            wait_worker(worker)

            self.assertEqual(len(errors), 1)
            self.assertIn("Connection lost", errors[0])

    def test_video_studio_dialog_workflow(self):
        project = Project(name="Test Video Project")
        imported_clips = []

        def on_import(path, duration):
            imported_clips.append((path, duration))

        with tempfile.TemporaryDirectory() as tmp_dir:
            proj_file = str(Path(tmp_dir) / "test.anima")
            dialog = VideoStudioDialog(project, project_file=proj_file, on_video_imported=on_import)
            try:
                # Test initial mode
                self.assertTrue(dialog.radio_t2v.isChecked())
                self.assertFalse(dialog.ref_box.isEnabled())

                # Switch to image-to-video mode
                dialog.radio_i2v.setChecked(True)
                self.assertTrue(dialog.ref_box.isEnabled())

                # Fill inputs
                dialog.prompt_input.setText("Mia dancing in petal dress")
                dialog.aspect_combo.setCurrentText("16:9")
                dialog.duration_spin.setValue(2.0)

                # Patch QMessageBox to prevent modal popups
                with patch.object(QMessageBox, "information"), patch.object(QMessageBox, "warning"), patch.object(QMessageBox, "critical"):
                    dialog._start_generation()
                    if dialog.active_worker:
                        wait_worker(dialog.active_worker)

                # Verify job history and completion
                self.assertEqual(len(dialog.job_history), 1)
                self.assertEqual(dialog.history_table.rowCount(), 1)
                self.assertTrue(dialog.btn_import_timeline.isEnabled())

                # Test timeline import
                with patch.object(QMessageBox, "information"):
                    dialog._import_to_timeline()

                self.assertEqual(len(imported_clips), 1)
                self.assertTrue(Path(imported_clips[0][0]).is_file())
                self.assertEqual(imported_clips[0][1], 2.0)

            finally:
                dialog.close()


if __name__ == "__main__":
    unittest.main()
