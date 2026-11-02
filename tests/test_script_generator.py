from io import BytesIO
import json
import unittest
from unittest.mock import MagicMock, patch

from animatube.pipeline.script_generator import (
    OllamaScriptGenerator,
    create_storyboard_from_script,
    generate_devops_roadmap_script,
)


class ScriptGeneratorTests(unittest.TestCase):
    def test_default_devops_roadmap_script(self):
        script = generate_devops_roadmap_script()
        self.assertIn("DevOps Engineer in 2027", script.title)
        self.assertGreaterEqual(len(script.scenes), 8)

        # Check diagram types are categorized
        diagram_types = {s.diagram_type for s in script.scenes}
        self.assertIn("terminal", diagram_types)
        self.assertIn("git_tree", diagram_types)
        self.assertIn("docker", diagram_types)
        self.assertIn("jenkins", diagram_types)
        self.assertIn("aws", diagram_types)

        # Check total estimated duration is positive
        self.assertGreater(script.estimated_duration_seconds(), 60.0)

    def test_create_storyboard_from_script(self):
        script = generate_devops_roadmap_script()
        storyboard = create_storyboard_from_script(script, fps=30)

        self.assertEqual(len(storyboard.scenes), len(script.scenes))
        self.assertEqual(storyboard.fps, 30)
        self.assertEqual(storyboard.width, 1920)
        self.assertEqual(storyboard.height, 1080)

        total_frames = storyboard.total_duration_frames()
        total_seconds = storyboard.total_duration_seconds()
        self.assertAlmostEqual(total_frames / 30.0, total_seconds, places=1)

    @patch("urllib.request.urlopen", side_effect=Exception("Connection refused"))
    def test_ollama_generator_fallback_when_offline(self, _mock_urlopen):
        generator = OllamaScriptGenerator(host="http://localhost:11434")
        self.assertFalse(generator.is_available())

        # Fallback should return production script without crashing
        script = generator.generate_script(use_fallback_if_unavailable=True)
        self.assertIn("2027", script.title)

        # When fallback is disabled, should raise RuntimeError
        with self.assertRaises(RuntimeError):
            generator.generate_script(use_fallback_if_unavailable=False)

    @patch("urllib.request.urlopen")
    def test_ollama_generator_with_mocked_response(self, mock_urlopen):
        sample_response = {
            "response": json.dumps({
                "title": "Custom DevOps Guide",
                "target_audience": "Beginners",
                "scenes": [
                    {
                        "id": "s1",
                        "title": "Scene 1",
                        "narration": "Hello world.",
                        "visual_description": "Intro card",
                        "on_screen_elements": ["Title"],
                        "target_duration_seconds": 10.0,
                        "diagram_type": "terminal",
                    }
                ],
            })
        }
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps(sample_response).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        generator = OllamaScriptGenerator()
        with patch.object(generator, "is_available", return_value=True):
            script = generator.generate_script(use_fallback_if_unavailable=False)
            self.assertEqual(script.title, "Custom DevOps Guide")
            self.assertEqual(len(script.scenes), 1)
            self.assertEqual(script.scenes[0].diagram_type, "terminal")


if __name__ == "__main__":
    unittest.main()
