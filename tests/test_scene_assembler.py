from pathlib import Path
import tempfile
import unittest

from animatube.core.project import load_project
from animatube.pipeline.assembler import assemble_animatube_project
from animatube.pipeline.models import Storyboard, StoryboardScene


class SceneAssemblerTests(unittest.TestCase):
    def test_assemble_project_roundtrip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            dummy_img = temp_path / "diagram.png"
            dummy_img.write_bytes(b"dummy png bytes for diagram")

            sb = Storyboard(
                title="DevOps Assemble Test",
                fps=30,
                width=1920,
                height=1080,
                scenes=[
                    StoryboardScene(
                        scene_id="s1",
                        title="Intro Scene",
                        duration_seconds=4.0,
                        duration_frames=120,
                        visual_asset_paths=[str(dummy_img)],
                    ),
                    StoryboardScene(
                        scene_id="s2",
                        title="Tool Scene",
                        duration_seconds=6.0,
                        duration_frames=180,
                    ),
                ],
            )

            target_anima = temp_path / "assembled.anima"
            project = assemble_animatube_project(sb, target_anima, project_name="Test Assembler")

            self.assertEqual(len(project.scenes), 2)
            self.assertEqual(project.scenes[0].duration_frames, 120)
            self.assertEqual(project.scenes[1].duration_frames, 180)

            # Check that the project file was written and can be loaded
            self.assertTrue(target_anima.is_file())
            loaded = load_project(target_anima)
            self.assertEqual(loaded.name, "Test Assembler")
            self.assertEqual(len(loaded.scenes), 2)
            self.assertEqual(loaded.width, 1920)
            self.assertEqual(loaded.height, 1080)


if __name__ == "__main__":
    unittest.main()
