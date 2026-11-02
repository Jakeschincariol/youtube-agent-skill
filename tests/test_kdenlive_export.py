from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from animatube.export.kdenlive import generate_kdenlive_project
from animatube.pipeline.models import Storyboard, StoryboardScene


class KdenliveExportTests(unittest.TestCase):
    def test_kdenlive_project_generation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            kdenlive_file = temp_path / "project.kdenlive"

            sb = Storyboard(
                title="DevOps 2027 Kdenlive",
                fps=30,
                width=1920,
                height=1080,
                scenes=[
                    StoryboardScene(
                        scene_id="s1",
                        title="Hook Scene",
                        duration_seconds=5.0,
                        duration_frames=150,
                        narration_audio_path="scene_01.wav",
                        visual_asset_paths=["pillars.png"],
                    ),
                    StoryboardScene(
                        scene_id="s2",
                        title="Terminal Scene",
                        duration_seconds=10.0,
                        duration_frames=300,
                        narration_audio_path="scene_02.wav",
                        visual_asset_paths=["terminal.png"],
                    ),
                ],
            )

            res = generate_kdenlive_project(sb, kdenlive_file, project_title="DevOps 2027")
            self.assertTrue(res.is_file())

            # Parse XML
            tree = ET.parse(str(res))
            root = tree.getroot()
            self.assertEqual(root.tag, "mlt")
            self.assertEqual(root.attrib.get("title"), "DevOps 2027")

            profile = root.find("profile")
            self.assertIsNotNone(profile)
            self.assertEqual(profile.attrib.get("width"), "1920")
            self.assertEqual(profile.attrib.get("height"), "1080")
            self.assertEqual(profile.attrib.get("frame_rate_num"), "30")

            # Check tracks in tractor
            tractor = root.find("tractor")
            self.assertIsNotNone(tractor)
            multitrack = tractor.find("multitrack")
            tracks = multitrack.findall("track")
            self.assertEqual(len(tracks), 2)


if __name__ == "__main__":
    unittest.main()
