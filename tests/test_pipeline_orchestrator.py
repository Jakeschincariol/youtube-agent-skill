from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from animatube.audio.edge_tts_wrapper import EdgeTTS
from animatube.pipeline.models import MediaManifest
from animatube.pipeline.orchestrator import run_pipeline


class PipelineOrchestratorTests(unittest.TestCase):
    @patch.object(EdgeTTS, "is_available", return_value=False)
    def test_run_full_pipeline_dry_run(self, _mock_edge):
        with tempfile.TemporaryDirectory() as temp_dir:
            out_path = Path(temp_dir) / "output"

            manifest = run_pipeline(
                output_directory=out_path,
                project_name="Test_DevOps_Pipeline",
                use_ollama=False,  # Use deterministic script
                dry_run_render=True,
                fps=30,
            )

            self.assertIsInstance(manifest, MediaManifest)
            self.assertEqual(manifest.project_name, "Test_DevOps_Pipeline")

            # Check all key files exist
            self.assertTrue(Path(manifest.script_file).is_file())
            self.assertTrue(Path(manifest.storyboard_file).is_file())
            self.assertTrue(Path(manifest.anima_project_file).is_file())
            self.assertTrue(Path(manifest.kdenlive_project_file).is_file())
            self.assertTrue(Path(manifest.thumbnail_file).is_file())
            self.assertTrue(Path(manifest.metadata_file).is_file())
            self.assertTrue(Path(manifest.chapters_file).is_file())
            self.assertTrue(Path(manifest.output_video_file).is_file())

            # Check that manifest file exists on disk and loads back
            manifest_file = out_path / "manifest.json"
            self.assertTrue(manifest_file.is_file())
            loaded = MediaManifest.load(manifest_file)
            self.assertEqual(loaded.project_name, "Test_DevOps_Pipeline")
            self.assertGreaterEqual(len(loaded.assets), 15)

            # Check chapters start at 00:00
            chapters = Path(manifest.chapters_file).read_text(encoding="utf-8")
            self.assertTrue(chapters.startswith("00:00"))


if __name__ == "__main__":
    unittest.main()
