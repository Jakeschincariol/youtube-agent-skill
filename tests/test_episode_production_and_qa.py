from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from animatube.pipeline.production_models import (
    EpisodeProduction,
    SceneProduction,
    ShotDirection,
)
from animatube.pipeline.qa_validator import QAValidator
from animatube.presets.ep01_magic_abc_train import create_ep01_production_specification


class EpisodeProductionAndQATests(unittest.TestCase):
    def setUp(self):
        self.episode = create_ep01_production_specification()
        self.qa = QAValidator()

    def test_episode_spec_complete_11_scenes(self):
        self.assertEqual(len(self.episode.scenes), 11)
        self.assertEqual(self.episode.total_duration_seconds, 600.0)
        self.assertGreaterEqual(self.episode.total_shots_count, 50)
        self.assertEqual(self.episode.fps, 24)
        self.assertEqual(self.episode.resolution, (1920, 1080))

    def test_qa_validation_curriculum_and_references(self):
        report = self.qa.run_full_validation(episode=self.episode)
        self.assertTrue(report.passed)
        self.assertEqual(report.passed_checks, report.total_checks)

        # Check curriculum pass
        curr_check = next(c for c in report.checks if c.name == "Alphabet Curriculum Complete")
        self.assertTrue(curr_check.passed)
        self.assertIn("Found 26/26 letters", curr_check.details)

        # Check references pass
        ref_check = next(c for c in report.checks if c.name == "Character Visual References")
        self.assertTrue(ref_check.passed)
        self.assertIn("Missing: None", ref_check.details)

    def test_export_storyboard_and_shot_list(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            json_path = Path(tmp_dir) / "storyboard.json"
            md_path = Path(tmp_dir) / "SHOT_LIST.md"

            self.episode.export_storyboard_json(json_path)
            self.episode.export_shot_list_markdown(md_path)

            self.assertTrue(json_path.is_file())
            self.assertTrue(md_path.is_file())

            data = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(data["title"], "THE MAGIC ABC TRAIN")
            self.assertEqual(len(data["scenes"]), 11)

            md_content = md_path.read_text(encoding="utf-8")
            self.assertIn("Scene 1: Welcome to Dreamland", md_content)
            self.assertIn("Scene 9: ABC Musical Celebration", md_content)
            self.assertIn("Scene 11: Goodbye", md_content)

    def test_qa_validates_scene_01_sample_if_present(self):
        sample_path = Path("little-dreamers/episodes/ep01_magic_abc_train/exports/scene_01_sample_preview_1080p.mp4")
        if sample_path.is_file():
            report = self.qa.run_full_validation(video_path=sample_path, episode=self.episode)
            self.assertTrue(report.passed)
            self.assertGreater(report.passed_checks, 5)


if __name__ == "__main__":
    unittest.main()
