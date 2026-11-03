from __future__ import annotations

import unittest
from typing import Any

from animatube.ai.little_dreamers_planner import (
    EpisodeBrief,
    EpisodePlanError,
    LittleDreamersStoryPlanner,
)


def valid_payload() -> dict[str, Any]:
    scenes = []
    for index in range(1, 4):
        scenes.append(
            {
                "scene_id": f"scene_{index:02d}",
                "title": f"Scene {index}",
                "setting": "A bright magical meadow",
                "action": "The friends work together to find the next letter.",
                "narration": "Let us look together!",
                "duration_seconds": 40,
                "dialogue": [
                    {"speaker_id": "aarav", "text": "Can you say A with me?"},
                    {"speaker_id": "bobo", "text": "A! We did it!"},
                ],
                "shots": [
                    {
                        "description": "Wide shot of the friends waving.",
                        "duration_seconds": 15,
                        "character_ids": ["aarav", "bobo"],
                    },
                    {
                        "description": "Close-up as the letter glows.",
                        "duration_seconds": 25,
                        "character_ids": ["aarav"],
                    },
                ],
            }
        )
    return {
        "title": "The Magic ABC Train",
        "logline": "Two friends help a magical train find its letters.",
        "learning_objective": "Recognize and say the letters A, B and C.",
        "target_age_min": 2,
        "target_age_max": 5,
        "language": "English",
        "character_ids": ["aarav", "bobo"],
        "scenes": scenes,
    }


class FakeJSONGenerator:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.calls: list[dict[str, Any]] = []

    def generate_json(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        self.calls.append({"prompt": prompt, **kwargs})
        return self.payload


class LittleDreamersPlannerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = valid_payload()
        self.client = FakeJSONGenerator(self.payload)
        self.planner = LittleDreamersStoryPlanner(self.client)

    def test_builds_valid_episode_plan_without_live_ollama(self) -> None:
        plan = self.planner.plan_episode(
            EpisodeBrief(
                title="The Magic ABC Train",
                learning_objective="Recognize and say A, B and C.",
                target_duration_seconds=120,
                character_ids=("aarav", "bobo"),
            )
        )
        self.assertEqual(plan.title, "The Magic ABC Train")
        self.assertEqual(len(plan.scenes), 3)
        self.assertEqual(plan.total_duration_seconds, 120)
        self.assertEqual(plan.character_ids, ("aarav", "bobo"))
        self.assertEqual(self.client.calls[0]["model"], None)
        self.assertIn("ages 2–5", self.client.calls[0]["system"])

    def test_rejects_unapproved_character_in_episode(self) -> None:
        self.payload["character_ids"] = ["aarav", "new_character"]
        with self.assertRaisesRegex(EpisodePlanError, "Unapproved character"):
            self.planner.plan_episode(
                EpisodeBrief("ABC Train", "Recognize letters.", target_duration_seconds=120)
            )

    def test_rejects_dialogue_from_unselected_character(self) -> None:
        self.payload["scenes"][0]["dialogue"][0]["speaker_id"] = "twinkle"
        with self.assertRaisesRegex(EpisodePlanError, "is not selected"):
            self.planner.plan_episode(
                EpisodeBrief(
                    "ABC Train",
                    "Recognize letters.",
                    target_duration_seconds=120,
                    character_ids=("aarav", "bobo"),
                )
            )

    def test_rejects_character_set_different_from_brief(self) -> None:
        self.payload["character_ids"] = ["aarav", "mia"]
        with self.assertRaisesRegex(EpisodePlanError, "exactly match"):
            self.planner.plan_episode(
                EpisodeBrief(
                    "ABC Train",
                    "Recognize letters.",
                    target_duration_seconds=120,
                    character_ids=("aarav", "bobo"),
                )
            )

    def test_rejects_scene_shot_duration_mismatch(self) -> None:
        self.payload["scenes"][1]["shots"][0]["duration_seconds"] = 2
        with self.assertRaisesRegex(EpisodePlanError, "shot durations"):
            self.planner.plan_episode(
                EpisodeBrief(
                    "ABC Train",
                    "Recognize letters.",
                    target_duration_seconds=120,
                    character_ids=("aarav", "bobo"),
                )
            )

    def test_rejects_too_few_scenes(self) -> None:
        self.payload["scenes"] = self.payload["scenes"][:2]
        with self.assertRaisesRegex(EpisodePlanError, "between 3 and 6 scenes"):
            self.planner.plan_episode(
                EpisodeBrief(
                    "ABC Train",
                    "Recognize letters.",
                    target_duration_seconds=80,
                    character_ids=("aarav", "bobo"),
                )
            )

    def test_rejects_invalid_age_range_before_model_call(self) -> None:
        with self.assertRaisesRegex(ValueError, "ages 2–5"):
            self.planner.plan_episode(
                EpisodeBrief(
                    "ABC Train",
                    "Recognize letters.",
                    target_age_min=1,
                    target_age_max=5,
                )
            )
        self.assertEqual(self.client.calls, [])

    def test_rejects_duration_that_does_not_match_brief(self) -> None:
        with self.assertRaisesRegex(EpisodePlanError, "duration is too far"):
            self.planner.plan_episode(
                EpisodeBrief(
                    "ABC Train",
                    "Recognize letters.",
                    target_duration_seconds=300,
                    character_ids=("aarav", "bobo"),
                )
            )


if __name__ == "__main__":
    unittest.main()
