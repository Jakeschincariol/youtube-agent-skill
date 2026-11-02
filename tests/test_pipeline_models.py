import json
from pathlib import Path
import tempfile
import unittest

from animatube.pipeline.models import (
    MediaManifest,
    Script,
    ScriptScene,
    Storyboard,
    StoryboardScene,
)


class PipelineModelTests(unittest.TestCase):
    def test_script_scene_validation(self):
        scene = ScriptScene(
            id="sc1",
            title="Introduction",
            narration="Welcome to DevOps roadmap.",
            target_duration_seconds=15.0,
            on_screen_elements=["Terminal", "Title"],
        )
        self.assertEqual(scene.id, "sc1")
        self.assertEqual(scene.target_duration_seconds, 15.0)

        with self.assertRaises(ValueError):
            ScriptScene(target_duration_seconds=-1)

        with self.assertRaises(ValueError):
            ScriptScene(on_screen_elements="not-a-list")  # type: ignore

    def test_script_roundtrip_and_word_count(self):
        s1 = ScriptScene(id="1", title="Intro", narration="One two three four five.")
        s2 = ScriptScene(id="2", title="Body", narration="Six seven eight nine ten.")
        script = Script(title="Test Script", scenes=[s1, s2])

        self.assertEqual(script.total_words(), 10)
        # 10 words at 150 wpm = (10 / 150) * 60 = 4.0 seconds
        self.assertAlmostEqual(script.estimated_duration_seconds(words_per_minute=150.0), 4.0)

        data = script.to_dict()
        restored = Script.from_dict(data)
        self.assertEqual(restored.title, "Test Script")
        self.assertEqual(len(restored.scenes), 2)
        self.assertEqual(restored.scenes[0].title, "Intro")

    def test_storyboard_durations(self):
        sb1 = StoryboardScene(
            scene_id="s1",
            title="Intro",
            duration_seconds=5.5,
            duration_frames=165,
        )
        sb2 = StoryboardScene(
            scene_id="s2",
            title="Outro",
            duration_seconds=4.5,
            duration_frames=135,
        )
        sb = Storyboard(title="Test SB", fps=30, scenes=[sb1, sb2])

        self.assertEqual(sb.total_duration_seconds(), 10.0)
        self.assertEqual(sb.total_duration_frames(), 300)

        data = sb.to_dict()
        restored = Storyboard.from_dict(data)
        self.assertEqual(restored.total_duration_seconds(), 10.0)
        self.assertEqual(restored.total_duration_frames(), 300)

    def test_media_manifest_save_and_load(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            dummy_asset = temp_path / "graphic.png"
            dummy_asset.write_bytes(b"dummy png bytes")

            manifest = MediaManifest(
                project_name="DevOps 2027",
                script_file="script.json",
                storyboard_file="storyboard.json",
                output_video_file="final.mp4",
            )
            manifest.add_asset(dummy_asset, kind="image", metadata={"role": "diagram"})

            manifest_file = temp_path / "manifest.json"
            manifest.save(manifest_file)

            loaded = MediaManifest.load(manifest_file)
            self.assertEqual(loaded.project_name, "DevOps 2027")
            self.assertEqual(len(loaded.assets), 1)
            self.assertEqual(loaded.assets[0]["kind"], "image")
            self.assertTrue(len(loaded.assets[0]["sha256"]) == 64)
            self.assertEqual(loaded.assets[0]["size_bytes"], len(b"dummy png bytes"))


if __name__ == "__main__":
    unittest.main()
