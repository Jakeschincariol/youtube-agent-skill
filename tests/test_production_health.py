from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from animatube.pipeline.production_health import ProductionHealthChecker


class ProductionHealthTests(unittest.TestCase):
    def _workspace(self, root: Path) -> Path:
        chars = root / "little-dreamers/characters"
        flow = root / "little-dreamers/flow_ready"
        for name in ("aarav", "mia", "ellie", "gigi", "bobo", "twinkle"):
            folder = chars / name
            folder.mkdir(parents=True)
            (folder / f"{name}_reference_sheet.png").write_bytes(b"placeholder")
            flow.mkdir(parents=True, exist_ok=True)
            (flow / f"{name}_flow_anchor.png").write_bytes(b"placeholder")
        episode = root / "little-dreamers/episodes/ep01_magic_abc_train"
        episode.mkdir(parents=True)
        storyboard = {
            "resolution": [1920, 1080], "fps": 24,
            "total_duration_seconds": 10, "total_shots_count": 1,
            "scenes": [{"scene_number": 1, "duration_seconds": 10, "shots": [{
                "shot_id": "SH01_01", "duration_seconds": 10,
                "characters": ["Aarav"], "character_references": []
            }]}]
        }
        (episode / "storyboard.json").write_text(json.dumps(storyboard), encoding="utf-8")
        return root

    def test_storyboard_accepts_consistent_timing(self):
        with tempfile.TemporaryDirectory() as temp:
            checker = ProductionHealthChecker(self._workspace(Path(temp)))
            checker.check_storyboard()
            self.assertEqual(checker.checks[-1].status, "PASS")

    def test_storyboard_rejects_duplicate_shot_ids_and_bad_timing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._workspace(Path(temp))
            path = root / "little-dreamers/episodes/ep01_magic_abc_train/storyboard.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["scenes"][0]["shots"][0]["duration_seconds"] = 9
            data["scenes"][0]["shots"].append(dict(data["scenes"][0]["shots"][0]))
            data["total_shots_count"] = 2
            path.write_text(json.dumps(data), encoding="utf-8")
            checker = ProductionHealthChecker(root)
            checker.check_storyboard()
            self.assertEqual(checker.checks[-1].status, "FAIL")
            self.assertIn("duplicate shot_id", checker.checks[-1].details)

    def test_missing_storyboard_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            checker = ProductionHealthChecker(temp)
            checker.check_storyboard()
            self.assertEqual(checker.checks[-1].status, "FAIL")

    def test_ollama_offline_is_warning_or_required_failure(self):
        with patch("urllib.request.urlopen", side_effect=OSError("offline")):
            checker = ProductionHealthChecker(".", require_ollama=False)
            checker.check_ollama()
            self.assertEqual(checker.checks[-1].status, "WARN")
        with patch("urllib.request.urlopen", side_effect=OSError("offline")):
            checker = ProductionHealthChecker(".", require_ollama=True)
            checker.check_ollama()
            self.assertEqual(checker.checks[-1].status, "FAIL")

    def test_missing_repo_root_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            checker = ProductionHealthChecker(Path(temp) / "missing")
            checker.run()
            self.assertFalse(checker.passed)
            self.assertEqual(checker.checks[0].status, "FAIL")


if __name__ == "__main__":
    unittest.main()
