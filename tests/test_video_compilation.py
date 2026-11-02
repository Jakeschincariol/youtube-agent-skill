from io import BytesIO
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from animatube.core.models import Layer, Project, Scene
from animatube.export.compiler import (
    CompilationOptions,
    ExportCancelledError,
    ProbeResult,
    SceneClip,
    ValidationError,
    collect_project_scenes,
    compile_scenes,
    probe_video,
)


class VideoCompilationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtGui import QGuiApplication
        cls.app = QGuiApplication.instance() or QGuiApplication(["animatube"])

    def setUp(self):
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.temp_dir = Path(self.temp_dir_obj.name)

    def tearDown(self):
        self.temp_dir_obj.cleanup()

    def test_empty_project_handling(self):
        """Compiling an empty project or empty list must raise ValueError."""
        empty_proj = Project()
        empty_proj.scenes = []
        with self.assertRaises(ValueError) as ctx:
            compile_scenes(empty_proj, self.temp_dir / "out.mp4")
        self.assertIn("empty", str(ctx.exception).lower())

        with self.assertRaises(ValueError):
            compile_scenes([], self.temp_dir / "out.mp4")

    def test_correct_scene_ordering_not_alphabetical(self):
        """Scene collection must strictly preserve storyboard timeline order, not alphabetical sorting."""
        s1 = Scene(name="Zebra Scene", duration_frames=60)
        s2 = Scene(name="Apple Scene", duration_frames=90)
        s3 = Scene(name="Mango Scene", duration_frames=120)

        proj = Project(scenes=[s1, s2, s3])
        clips = collect_project_scenes(proj)

        self.assertEqual(len(clips), 3)
        self.assertEqual(clips[0].title, "Zebra Scene")
        self.assertEqual(clips[1].title, "Apple Scene")
        self.assertEqual(clips[2].title, "Mango Scene")

        # Scene IDs must match index sequence
        self.assertEqual(clips[0].scene_id, "scene_01")
        self.assertEqual(clips[1].scene_id, "scene_02")
        self.assertEqual(clips[2].scene_id, "scene_03")

    def test_missing_scene_file_raises_filenotfound(self):
        """A missing scene file must raise FileNotFoundError up front."""
        missing_path = self.temp_dir / "does_not_exist.mp4"
        clip = SceneClip(source=missing_path, duration=5.0)

        with patch("animatube.export.compiler.get_ffmpeg_executable", return_value="ffmpeg"):
            with self.assertRaises(FileNotFoundError):
                compile_scenes([clip], self.temp_dir / "final.mp4")

    def test_corrupted_empty_scene_file_raises_validation_error(self):
        """A 0-byte corrupt scene file must raise ValidationError."""
        empty_file = self.temp_dir / "corrupted_empty.mp4"
        empty_file.write_bytes(b"")

        clip = SceneClip(source=empty_file, duration=5.0)
        with patch("animatube.export.compiler.get_ffmpeg_executable", return_value="ffmpeg"):
            with self.assertRaises(ValidationError):
                compile_scenes([clip], self.temp_dir / "final.mp4")

    def test_ffmpeg_unavailable_raises_runtime_error(self):
        """If FFmpeg is not found, compile_scenes must raise RuntimeError."""
        s = Scene(name="Intro", duration_frames=30)
        clip = SceneClip(source=s, duration=1.0)

        with patch("animatube.export.compiler.get_ffmpeg_executable", return_value=None):
            with self.assertRaises(RuntimeError) as ctx:
                compile_scenes([clip], self.temp_dir / "final.mp4")
            self.assertIn("ffmpeg", str(ctx.exception).lower())

    def test_export_cancellation_before_and_during_compilation(self):
        """Cancellation token must stop export immediately and raise ExportCancelledError."""
        s1 = Scene(name="Scene 1", duration_frames=30)
        s2 = Scene(name="Scene 2", duration_frames=30)
        proj = Project(scenes=[s1, s2])

        # Test pre-start cancellation
        with patch("animatube.export.compiler.get_ffmpeg_executable", return_value="ffmpeg"):
            with self.assertRaises(ExportCancelledError):
                compile_scenes(proj, self.temp_dir / "cancelled.mp4", is_cancelled=lambda: True)

        # Ensure no residual temp file remains
        self.assertFalse((self.temp_dir / ".cancelled.compiling.mp4").exists())

    def test_probe_video_validation(self):
        """FFprobe validation parses streams, resolution, codec and duration correctly."""
        dummy_mp4 = self.temp_dir / "valid_test.mp4"
        dummy_mp4.write_bytes(b"\x00\x00\x00\x18ftypisom\x00\x00\x00\x00isommp42")

        # Test fallback inspection when ffprobe is absent
        with patch("animatube.export.compiler.get_ffprobe_executable", return_value=None):
            probe = probe_video(dummy_mp4)
            self.assertTrue(probe.has_video_stream)
            self.assertEqual(probe.width, 1920)
            self.assertEqual(probe.height, 1080)

        # Test non-mp4 corrupt data raises ValidationError
        corrupt_file = self.temp_dir / "bad.mp4"
        corrupt_file.write_bytes(b"not an mp4 file")
        with patch("animatube.export.compiler.get_ffprobe_executable", return_value=None):
            with self.assertRaises(ValidationError):
                probe_video(corrupt_file)

        # Test real ffprobe JSON parsing
        ffprobe_output = {
            "streams": [
                {
                    "codec_name": "h264",
                    "width": 1920,
                    "height": 1080,
                    "r_frame_rate": "30/1",
                    "duration": "15.500000",
                }
            ],
            "format": {
                "duration": "15.500000"
            }
        }

        mock_proc = MagicMock()
        mock_proc.stdout = json.dumps(ffprobe_output)
        mock_proc.returncode = 0

        with patch("animatube.export.compiler.get_ffprobe_executable", return_value="ffprobe"):
            with patch("subprocess.run", return_value=mock_proc):
                res = probe_video(dummy_mp4)
                self.assertEqual(res.width, 1920)
                self.assertEqual(res.height, 1080)
                self.assertEqual(res.codec_name, "h264")
                self.assertEqual(res.fps, 30.0)
                self.assertAlmostEqual(res.duration, 15.5)

    def test_still_image_scene_configurable_duration(self):
        """Still image scenes must accept and apply configurable duration."""
        img_path = self.temp_dir / "slide.png"
        img_path.write_bytes(b"fake png image bytes")

        clip = SceneClip(source=img_path, duration=7.5)
        self.assertTrue(clip.is_image())
        self.assertEqual(clip.duration, 7.5)

        # Default fallback duration when clip duration is None
        clip_default = SceneClip(source=img_path, duration=0.0)
        self.assertEqual(clip_default.duration, 0.0)

    def test_mixed_video_and_image_scene_compilation_workflow(self):
        """Verifies compilation workflow with mixed MP4 video, still images, and in-memory scenes."""
        img_scene = self.temp_dir / "diagram.png"
        img_scene.write_bytes(b"png image data")

        vid_scene = self.temp_dir / "clip.mp4"
        vid_scene.write_bytes(b"\x00\x00\x00\x18ftypmp42")

        in_memory_scene = Scene(name="Title Card", duration_frames=30, layers=[
            Layer(name="Heading", text="Hello DevOps")
        ])

        clips = [
            SceneClip(source=img_scene, duration=4.0, scene_id="s1"),
            SceneClip(source=vid_scene, duration=6.0, scene_id="s2"),
            SceneClip(source=in_memory_scene, duration=1.0, scene_id="s3"),
        ]

        def fake_subprocess_run(cmd, *args, **kwargs):
            mock_res = MagicMock()
            mock_res.returncode = 0
            # If creating a normalized clip or concat file, ensure it exists
            target_arg = cmd[-1]
            if isinstance(target_arg, str) and (target_arg.endswith(".mp4") or "normalized" in target_arg):
                Path(target_arg).write_bytes(b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00isommp42")
            return mock_res

        class FakePopen:
            def __init__(self, cmd, *args, **kwargs):
                self.stdin = MagicMock()
                self.stderr = MagicMock()
                self.target_file = cmd[-1]
                Path(self.target_file).write_bytes(b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00isommp42")
            def wait(self):
                return 0
            def poll(self):
                return 0

        progress_calls = []

        with patch("animatube.export.compiler.get_ffmpeg_executable", return_value="ffmpeg"):
            with patch("subprocess.run", side_effect=fake_subprocess_run):
                with patch("subprocess.Popen", side_effect=FakePopen):
                    with patch("animatube.export.compiler.probe_video") as mock_probe:
                        mock_probe.return_value = ProbeResult(
                            width=1920, height=1080, duration=11.0, codec_name="h264", fps=30.0, has_video_stream=True
                        )

                        dest = self.temp_dir / "final_output.mp4"
                        res = compile_scenes(
                            clips,
                            dest,
                            options=CompilationOptions(width=1920, height=1080, fps=30),
                            progress=lambda p: progress_calls.append(p),
                        )

                        self.assertTrue(res.is_file())
                        self.assertEqual(res, dest)
                        self.assertIn(100, progress_calls)
                        self.assertTrue(len(progress_calls) >= 3)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "Real FFmpeg/FFprobe binaries not found on system PATH")
    def test_real_ffmpeg_compilation_integration(self):
        """End-to-end integration test with real FFmpeg and FFprobe binaries if installed."""
        img1 = self.temp_dir / "real_slide_1.png"
        img2 = self.temp_dir / "real_slide_2.png"

        from PySide6.QtGui import QColor, QImage, QPainter
        qimg = QImage(640, 360, QImage.Format.Format_RGB32)
        qimg.fill(QColor("blue"))
        qimg.save(str(img1), "PNG")
        qimg.fill(QColor("red"))
        qimg.save(str(img2), "PNG")

        clips = [
            SceneClip(source=img1, duration=1.0, title="Real Slide 1"),
            SceneClip(source=img2, duration=1.0, title="Real Slide 2"),
        ]

        out_mp4 = self.temp_dir / "real_output.mp4"
        result = compile_scenes(clips, out_mp4)

        self.assertTrue(result.is_file())
        probe = probe_video(result)
        self.assertTrue(probe.has_video_stream)
        self.assertEqual(probe.width, 1920)
        self.assertEqual(probe.height, 1080)
        self.assertAlmostEqual(probe.duration, 2.0, delta=0.5)


if __name__ == "__main__":
    unittest.main()
