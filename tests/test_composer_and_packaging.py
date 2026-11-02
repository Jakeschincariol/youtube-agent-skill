from pathlib import Path
import tempfile
import unittest

from PySide6.QtGui import QImage

from animatube.audio.piper_tts import create_mock_wav, get_wav_duration_seconds
from animatube.core.models import Project, Scene
from animatube.export.composer import VideoComposer, concatenate_wav_files
from animatube.pipeline.models import Storyboard, StoryboardScene
from animatube.pipeline.packaging import generate_thumbnail, generate_video_metadata


class ComposerAndPackagingTests(unittest.TestCase):
    def test_audio_concatenation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            f1 = temp_path / "part1.wav"
            f2 = temp_path / "part2.wav"
            create_mock_wav(f1, duration_seconds=1.5, sample_rate=16000)
            create_mock_wav(f2, duration_seconds=2.5, sample_rate=16000)

            out_wav = temp_path / "combined.wav"
            concatenate_wav_files([f1, f2], out_wav)

            dur = get_wav_duration_seconds(out_wav)
            self.assertAlmostEqual(dur, 4.0, places=1)

    def test_video_composer_dry_run(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            out_mp4 = temp_path / "test.mp4"

            project = Project(name="TestProj", width=1920, height=1080, fps=30, scenes=[
                Scene(name="S1", duration_frames=30)
            ])
            sb = Storyboard(title="Test", fps=30, width=1920, height=1080, scenes=[
                StoryboardScene(scene_id="s1", title="S1", duration_seconds=1.0, duration_frames=30)
            ])

            composer = VideoComposer()
            res = composer.compose_video(project, sb, out_mp4, dry_run=True)
            self.assertTrue(res.is_file())
            self.assertGreater(res.stat().st_size, 0)

    def test_thumbnail_generation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            thumb_path = Path(temp_dir) / "thumb.png"
            generate_thumbnail(thumb_path, width=1280, height=720)

            self.assertTrue(thumb_path.is_file())
            img = QImage(str(thumb_path))
            self.assertEqual(img.width(), 1280)
            self.assertEqual(img.height(), 720)

    def test_metadata_generation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            meta_json = temp_path / "metadata.json"
            chap_txt = temp_path / "chapters.txt"

            sb = Storyboard(title="Test", scenes=[
                StoryboardScene(scene_id="1", title="Hook", duration_seconds=15.0, duration_frames=450),
                StoryboardScene(scene_id="2", title="Linux", duration_seconds=25.0, duration_frames=750),
            ])

            generate_video_metadata(sb, meta_json, chap_txt)

            self.assertTrue(meta_json.is_file())
            self.assertTrue(chap_txt.is_file())

            chaps = chap_txt.read_text(encoding="utf-8")
            self.assertIn("00:00 - Hook", chaps)
            self.assertIn("00:15 - Linux", chaps)

            import json
            data = json.loads(meta_json.read_text(encoding="utf-8"))
            self.assertEqual(data["tag_count"], 20)
            self.assertEqual(data["hashtag_count"], 5)
            self.assertEqual(len(data["tags"]), 20)
            self.assertEqual(len(data["hashtags"]), 5)


if __name__ == "__main__":
    unittest.main()
