from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from PIL import Image
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtWidgets import QApplication

from animatube.core.models import Keyframe, Layer, Project, Scene
from animatube.export.compiler import (
    CompilationOptions,
    ProbeResult,
    compile_scenes,
    probe_video,
)
from animatube.pipeline.animator import (
    SceneAnimator,
    SceneMotionStyle,
    detect_scene_motion_style,
    enhance_project_with_animations,
)
from animatube.thumbnails.generator import (
    ThumbnailConcept,
    ThumbnailEngine,
    validate_headline,
)
from animatube.ui.thumbnail_studio import ThumbnailStudioDialog


class ThumbnailAndAnimationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(["animatube"])

    def setUp(self):
        self.temp_dir_obj = tempfile.TemporaryDirectory(prefix="animatube_test_")
        self.temp_dir = Path(self.temp_dir_obj.name)

    def tearDown(self):
        self.temp_dir_obj.cleanup()

    # ---------------------------------------------------------
    # Feature 1 Tests: AI Thumbnail Generator
    # ---------------------------------------------------------

    def test_thumbnail_dimensions_and_formats_png_and_jpg(self):
        """Thumbnail must export at exact 1280x720 resolution in both PNG and JPG formats."""
        engine = ThumbnailEngine()
        concept = ThumbnailConcept(
            id="test_c1",
            concept_name="Test Hero",
            headline="DEVOPS ROADMAP 2027",
            subheadline="Beginner Guide",
            badge_text="5 CORE TOOLS",
            layout_style="split_hero",
        )

        png_target = self.temp_dir / "thumb.png"
        jpg_target = self.temp_dir / "thumb.jpg"

        out_png = engine.render_thumbnail(concept, png_target, format="PNG")
        out_jpg = engine.render_thumbnail(concept, jpg_target, format="JPG")

        self.assertTrue(out_png.is_file())
        self.assertTrue(out_jpg.is_file())

        # Verify PNG dimensions and format with Pillow
        with Image.open(out_png) as im_png:
            self.assertEqual(im_png.size, (1280, 720))
            self.assertEqual(im_png.format, "PNG")

        # Verify JPG dimensions and format with Pillow
        with Image.open(out_jpg) as im_jpg:
            self.assertEqual(im_jpg.size, (1280, 720))
            self.assertIn(im_jpg.format, ("JPEG", "JPG"))

    def test_headline_validation_truthfulness_and_bans(self):
        """Disallows fabricated guarantees, fake certifications, or unrealistic salary claims."""
        # Valid headlines pass
        self.assertEqual(validate_headline("DEVOPS ROADMAP 2027"), "DEVOPS ROADMAP 2027")
        self.assertEqual(validate_headline("HOW TO BECOME A DEVOPS ENGINEER"), "HOW TO BECOME A DEVOPS ENGINEER")

        # Prohibited claims raise ValueError
        prohibited_headlines = [
            "100% guarantee placement roadmap",
            "Guaranteed job in 30 days",
            "Certified in 2 weeks easily",
            "Earn $150k tomorrow with this",
            "Get 50 LPA salary package guaranteed",
            "Instant hire devops cheat sheet",
            "100% money back bootcamp",
        ]
        for bad in prohibited_headlines:
            with self.assertRaises(ValueError, msg=f"Should reject: {bad}"):
                validate_headline(bad)

        # Empty headline raises ValueError
        with self.assertRaises(ValueError):
            validate_headline("   ")

        # Overly long headline is cleanly trimmed
        long_headline = "A" * 80
        clipped = validate_headline(long_headline)
        self.assertLessEqual(len(clipped), 65)
        self.assertTrue(clipped.endswith("..."))

    def test_missing_image_handling_fallback_graphic(self):
        """Missing or corrupt focal asset must render a valid fallback graphic without crashing."""
        engine = ThumbnailEngine()
        concept = ThumbnailConcept(
            id="missing_asset_c",
            headline="DEVOPS ROADMAP 2027",
            focal_image_path=str(self.temp_dir / "does_not_exist.png"),
            layout_style="roadmap_flow",
        )

        out_png = self.temp_dir / "fallback_thumb.png"
        engine.render_thumbnail(concept, out_png, format="PNG")

        self.assertTrue(out_png.is_file())
        with Image.open(out_png) as im:
            self.assertEqual(im.size, (1280, 720))

    def test_multiple_thumbnail_variations_concepts(self):
        """Engine must generate at least 3 distinct concepts with varied layouts and accent colors."""
        engine = ThumbnailEngine()
        concepts = engine.generate_concepts(topic="Cloud DevOps 2027", target_audience="Freshers")

        self.assertGreaterEqual(len(concepts), 3)

        ids = [c.id for c in concepts]
        styles = [c.layout_style for c in concepts]
        accents = [c.accent_color for c in concepts]

        # Concepts must have distinct IDs, styles and colors
        self.assertEqual(len(set(ids)), len(concepts))
        self.assertIn("split_hero", styles)
        self.assertIn("roadmap_flow", styles)
        self.assertIn("card_focus", styles)
        self.assertGreaterEqual(len(set(accents)), 2)

    # ---------------------------------------------------------
    # Feature 2 Tests: Animated Scene Generator
    # ---------------------------------------------------------

    def test_scene_animator_motion_styles_and_duration_preservation(self):
        """Motion graphics must preserve exact scene duration and apply contextual styles."""
        s1 = Scene(name="Introduction to DevOps", duration_frames=90)
        s2 = Scene(name="Pillars of Modern DevOps", duration_frames=120)
        s3 = Scene(name="Docker Containers Deep Dive", duration_frames=150)
        s4 = Scene(name="CI CD Pipeline with Jenkins", duration_frames=180)
        s5 = Scene(name="Next Steps and Roadmap Summary", duration_frames=100)

        proj = Project(fps=30, scenes=[s1, s2, s3, s4, s5])
        enhance_project_with_animations(proj)

        # Durations must be strictly preserved
        self.assertEqual(s1.duration_frames, 90)
        self.assertEqual(s2.duration_frames, 120)
        self.assertEqual(s3.duration_frames, 150)
        self.assertEqual(s4.duration_frames, 180)
        self.assertEqual(s5.duration_frames, 100)

        # Motion styles detected correctly
        self.assertEqual(detect_scene_motion_style(s1.name, 0, 5), SceneMotionStyle.HOOK_INTRO)
        self.assertEqual(detect_scene_motion_style(s2.name, 1, 5, "pillars_overview"), SceneMotionStyle.ZOOM_OUT_ROADMAP)
        self.assertEqual(detect_scene_motion_style(s3.name, 2, 5), SceneMotionStyle.PAN_TOOL_FOCUS)
        self.assertEqual(detect_scene_motion_style(s4.name, 3, 5, "ci_cd_pipeline"), SceneMotionStyle.PROGRESSIVE_PIPELINE)
        self.assertEqual(detect_scene_motion_style(s5.name, 4, 5), SceneMotionStyle.OUTRO_CALL_TO_ACTION)

    def test_scene_ordering_preservation(self):
        """Scene ordering must remain strictly identical after animation enhancement."""
        names = ["Intro", "Zebra", "Apple", "Mango", "Summary"]
        scenes = [Scene(name=n, duration_frames=60) for n in names]
        proj = Project(scenes=scenes)

        enhance_project_with_animations(proj)

        self.assertEqual([s.name for s in proj.scenes], names)

    def test_progressive_pipeline_and_moving_arrow_layers(self):
        """Pipeline scenes must receive progressive reveal effects and moving indicator arrow."""
        s = Scene(name="CI CD Automation Pipeline", duration_frames=120)
        animator = SceneAnimator(fps=30)
        animator.enhance_scene(s, scene_index=3, total_scenes=5, style=SceneMotionStyle.PROGRESSIVE_PIPELINE)

        layer_names = [l.name for l in s.layers]
        self.assertIn("Anim_MovingArrow", layer_names)
        self.assertIn("Anim_KeywordBadge", layer_names)
        self.assertIn("Anim_KeywordText", layer_names)

        # Check moving arrow keyframes
        arrow = next(l for l in s.layers if l.name == "Anim_MovingArrow")
        self.assertGreaterEqual(len(arrow.keyframes), 3)
        # Arrow translates horizontally across scene
        first_x = arrow.keyframes[0].x
        last_x = arrow.keyframes[-2].x
        self.assertGreater(last_x, first_x)

    def test_ken_burns_zoom_and_pan_keyframes(self):
        """Image layers must receive cinematic Ken Burns camera movements (zoom/pan)."""
        img_layer = Layer(name="Diagram", kind="image", asset_path="diagram.png", x=0, y=0, width=1920, height=1080)
        s_intro = Scene(name="Intro", duration_frames=90, layers=[img_layer])

        animator = SceneAnimator(fps=30)
        animator.enhance_scene(s_intro, scene_index=0, total_scenes=3, style=SceneMotionStyle.HOOK_INTRO)

        # Intro has zoom-in (scale increases)
        self.assertGreaterEqual(len(img_layer.keyframes), 2)
        start_scale = img_layer.keyframes[0].scale
        end_scale = img_layer.keyframes[-1].scale
        self.assertGreater(end_scale, start_scale)

        # Roadmap has zoom-out (scale decreases)
        img_layer2 = Layer(name="Diagram2", kind="image", asset_path="diagram.png", x=0, y=0, width=1920, height=1080)
        s_roadmap = Scene(name="Roadmap", duration_frames=90, layers=[img_layer2])
        animator.enhance_scene(s_roadmap, scene_index=1, total_scenes=3, style=SceneMotionStyle.ZOOM_OUT_ROADMAP)
        self.assertLess(img_layer2.keyframes[-1].scale, img_layer2.keyframes[0].scale)

    # ---------------------------------------------------------
    # Feature 3 & 4 Tests: UI & Integration
    # ---------------------------------------------------------

    def test_thumbnail_studio_dialog_headless_instantiation(self):
        """ThumbnailStudioDialog must initialize, generate concepts, and update preview cleanly."""
        proj = Project(name="DevOps 2027 Test", scenes=[Scene(name="Test Scene")])
        dialog = ThumbnailStudioDialog(proj)

        self.assertGreaterEqual(len(dialog.concepts), 3)
        self.assertEqual(dialog.active_concept_idx, 0)
        self.assertTrue(dialog.txt_headline.text())

        # Switch concept
        dialog._on_concept_changed(1)
        self.assertEqual(dialog.active_concept_idx, 1)

        # Verify preview label has a valid scaled pixmap
        pix = dialog.preview_label.pixmap()
        self.assertFalse(pix.isNull())
        dialog.close()

    def test_ffmpeg_compilation_with_animated_scenes_and_probe_validation(self):
        """Full compilation of animated scenes with FFprobe validation."""
        s1 = Scene(name="Scene 1", duration_frames=30)
        s2 = Scene(name="Scene 2", duration_frames=30)
        proj = Project(fps=30, scenes=[s1, s2])
        enhance_project_with_animations(proj)

        def fake_run(cmd, *args, **kwargs):
            mock_res = MagicMock()
            mock_res.returncode = 0
            mock_res.stdout = ""
            mock_res.stderr = ""
            target_arg = cmd[-1]
            if isinstance(target_arg, str) and (target_arg.endswith(".mp4") or "normalized" in target_arg):
                Path(target_arg).write_bytes(b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00isommp42")
            if "ffprobe" in str(cmd[0]):
                data = {
                    "streams": [{
                        "codec_type": "video",
                        "codec_name": "h264",
                        "width": 1920,
                        "height": 1080,
                        "r_frame_rate": "30/1",
                        "duration": "2.0",
                    }],
                    "format": {"duration": "2.0", "size": "1048576"},
                }
                mock_res.stdout = json.dumps(data)
            return mock_res

        class FakePopen:
            def __init__(self, cmd, *args, **kwargs):
                self.stdin = MagicMock()
                self.stderr = MagicMock()
                target_file = cmd[-1]
                Path(target_file).write_bytes(b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00isommp42")

            def wait(self):
                return 0

            def poll(self):
                return 0

        with patch("animatube.export.compiler.get_ffmpeg_executable", return_value="ffmpeg"):
            with patch("subprocess.run", side_effect=fake_run):
                with patch("subprocess.Popen", side_effect=FakePopen):
                    with patch("animatube.export.compiler.probe_video") as mock_probe:
                        mock_probe.return_value = ProbeResult(
                            width=1920, height=1080, duration=2.0, codec_name="h264", fps=30.0, has_video_stream=True
                        )

                        dest = self.temp_dir / "animated_complete.mp4"
                        out_path = compile_scenes(proj, dest)

                        self.assertTrue(out_path.is_file())
                        self.assertEqual(out_path, dest)

    def test_ffmpeg_error_handling_in_compilation(self):
        """FFmpeg process failure during compilation raises RuntimeError with error details."""
        s1 = Scene(name="Scene 1", duration_frames=30)
        proj = Project(fps=30, scenes=[s1])

        class FailingPopen:
            def __init__(self, cmd, *args, **kwargs):
                self.stdin = MagicMock()
                self.stderr = MagicMock()
                self.stderr.read.return_value = b"Error decoding stream: invalid codec profile"

            def wait(self):
                return 1

            def poll(self):
                return 1

        with patch("animatube.export.compiler.get_ffmpeg_executable", return_value="ffmpeg"):
            with patch("subprocess.Popen", side_effect=FailingPopen):
                dest = self.temp_dir / "should_fail.mp4"
                with self.assertRaises(RuntimeError) as ctx:
                    compile_scenes(proj, dest)
                self.assertIn("FFmpeg error", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
