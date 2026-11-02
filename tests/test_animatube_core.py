import json
import tempfile
import unittest
from pathlib import Path

from animatube.core.animation import set_keyframe, state_at
from animatube.core.models import Keyframe, Layer, Project, Scene
from animatube.core.profiles import output_dimensions
from animatube.core.project import load_project, save_project


class AnimationTests(unittest.TestCase):
    def test_linear_interpolation(self):
        layer = Layer(keyframes=[Keyframe(0, 0, 10), Keyframe(10, 100, 50, scale=3, rotation=90, opacity=0.5)])
        self.assertEqual(state_at(layer, 5), {"x": 50, "y": 30, "scale": 2, "rotation": 45, "opacity": 0.75})

    def test_easing_is_applied_to_segment(self):
        layer = Layer(keyframes=[Keyframe(0, 0, 0), Keyframe(10, 100, 0, easing="ease-in")])
        self.assertEqual(state_at(layer, 5)["x"], 25)

    def test_frame_boundaries_hold_first_and_last_key(self):
        layer = Layer(keyframes=[Keyframe(5, 12, 14), Keyframe(10, 40, 50)])
        self.assertEqual(state_at(layer, 0)["x"], 12)
        self.assertEqual(state_at(layer, 99)["x"], 40)

    def test_set_keyframe_replaces_same_frame_and_preserves_other_values(self):
        layer = Layer(x=10, y=20)
        set_keyframe(layer, 0, "x", 42)
        set_keyframe(layer, 0, "rotation", 15)
        self.assertEqual(len(layer.keyframes), 1)
        self.assertEqual(state_at(layer, 0)["x"], 42)
        self.assertEqual(state_at(layer, 0)["rotation"], 15)

    def test_invalid_property_is_rejected(self):
        with self.assertRaises(ValueError):
            set_keyframe(Layer(), 0, "color", 1)

    def test_invalid_keyframe_values_are_rejected(self):
        with self.assertRaises(ValueError):
            Keyframe(-1, 0, 0)
        with self.assertRaises(ValueError):
            Keyframe(0, 0, 0, scale=0)
        with self.assertRaises(ValueError):
            Keyframe(0, 0, 0, opacity=2)


class ProjectTests(unittest.TestCase):
    def test_round_trip_keeps_scenes_layers_and_keyframes(self):
        project = Project(name="Demo", width=1280, height=720, scenes=[Scene(name="Intro", layers=[
            Layer(name="Title", text="Hello", keyframes=[Keyframe(12, 30, 40)])
        ])])
        restored = Project.from_dict(project.to_dict())
        self.assertEqual(restored.name, "Demo")
        self.assertEqual(restored.scenes[0].layers[0].text, "Hello")
        self.assertEqual(restored.scenes[0].layers[0].keyframes[0].frame, 12)

    def test_rejects_unsupported_format_dimensions_and_frame_rate(self):
        with self.assertRaises(ValueError):
            Project.from_dict({"format_version": 99})
        with self.assertRaises(ValueError):
            Project(width=9000)
        with self.assertRaises(ValueError):
            Project(fps=29)

    def test_save_bundles_image_asset_and_load_resolves_it(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "art.png"
            image.write_bytes(b"test image bytes")
            project = Project(scenes=[Scene(layers=[Layer(kind="image", asset_path=str(image))])])
            target = root / "project.anima"
            save_project(project, target)
            loaded = load_project(target)
            bundled = loaded.resolve_asset(loaded.scenes[0].layers[0].asset_path)
            self.assertTrue(bundled.is_file())
            self.assertEqual(bundled.read_bytes(), b"test image bytes")

    def test_saving_twice_reuses_bundled_asset_without_nested_copies(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "art.png"
            image.write_bytes(b"repeatable asset")
            project = Project(scenes=[Scene(layers=[Layer(kind="image", asset_path=str(image))])])
            target = root / "project.anima"
            save_project(project, target)
            first_asset = project.scenes[0].layers[0].asset_path
            save_project(project, target)
            self.assertEqual(project.scenes[0].layers[0].asset_path, first_asset)
            self.assertEqual(len(list((root / "project_assets").iterdir())), 1)

    def test_missing_image_asset_prevents_silent_broken_project(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Project(scenes=[Scene(layers=[Layer(kind="image", asset_path="missing.png")])])
            with self.assertRaises(FileNotFoundError):
                save_project(project, Path(directory) / "project.anima")

    def test_corrupt_project_has_actionable_error(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "broken.anima"
            target.write_text("{broken", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Could not load"):
                load_project(target)


class ProfileTests(unittest.TestCase):
    def test_common_output_profiles_have_even_dimensions(self):
        self.assertEqual(output_dimensions("wide", "1080p"), (1920, 1080))
        self.assertEqual(output_dimensions("vertical", "1080p"), (606, 1080))
        self.assertEqual(output_dimensions("square", "720p"), (720, 720))
        for profile in ("wide", "vertical", "square"):
            for resolution in ("720p", "1080p", "1440p", "4K"):
                width, height = output_dimensions(profile, resolution)
                self.assertEqual(width % 2, 0)
                self.assertEqual(height % 2, 0)


if __name__ == "__main__":
    unittest.main()
