from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from animatube.ai.ollama_client import OllamaClient


APPROVED_CHARACTER_IDS = frozenset(
    {"aarav", "mia", "ellie", "gigi", "bobo", "twinkle"}
)


class JSONGenerator(Protocol):
    def generate_json(
        self,
        prompt: str,
        *,
        system: str | None = None,
        model: str | None = None,
        temperature: float = 0.4,
    ) -> dict[str, Any]: ...


class EpisodePlanError(ValueError):
    """Raised when a generated Little Dreamers episode plan is incomplete or unsafe."""


@dataclass(frozen=True)
class EpisodeBrief:
    title: str
    learning_objective: str
    target_age_min: int = 2
    target_age_max: int = 5
    language: str = "English"
    target_duration_seconds: int = 180
    character_ids: tuple[str, ...] = ("aarav", "bobo")


@dataclass(frozen=True)
class DialogueLine:
    speaker_id: str
    text: str


@dataclass(frozen=True)
class ShotPlan:
    description: str
    duration_seconds: float
    character_ids: tuple[str, ...]


@dataclass(frozen=True)
class ScenePlan:
    scene_id: str
    title: str
    setting: str
    action: str
    narration: str
    dialogue: tuple[DialogueLine, ...]
    shots: tuple[ShotPlan, ...]
    duration_seconds: float


@dataclass(frozen=True)
class EpisodePlan:
    title: str
    logline: str
    learning_objective: str
    target_age_min: int
    target_age_max: int
    language: str
    character_ids: tuple[str, ...]
    scenes: tuple[ScenePlan, ...]

    @property
    def total_duration_seconds(self) -> float:
        return sum(scene.duration_seconds for scene in self.scenes)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EpisodePlan":
        if not isinstance(data, dict):
            raise EpisodePlanError("Episode plan must be a JSON object.")

        raw_scenes = data.get("scenes")
        if not isinstance(raw_scenes, list) or not raw_scenes:
            raise EpisodePlanError("Episode plan must contain at least one scene.")

        scenes: list[ScenePlan] = []
        for index, raw_scene in enumerate(raw_scenes, start=1):
            if not isinstance(raw_scene, dict):
                raise EpisodePlanError(f"Scene {index} must be an object.")
            raw_dialogue = raw_scene.get("dialogue", [])
            raw_shots = raw_scene.get("shots", [])
            if not isinstance(raw_dialogue, list) or not isinstance(raw_shots, list):
                raise EpisodePlanError(f"Scene {index} dialogue and shots must be arrays.")

            dialogue = tuple(
                DialogueLine(
                    speaker_id=str(line.get("speaker_id", "")).strip().lower(),
                    text=str(line.get("text", "")).strip(),
                )
                for line in raw_dialogue
                if isinstance(line, dict)
            )
            shots = tuple(
                ShotPlan(
                    description=str(shot.get("description", "")).strip(),
                    duration_seconds=_positive_number(
                        shot.get("duration_seconds"), f"Scene {index} shot duration"
                    ),
                    character_ids=tuple(_string_list(shot.get("character_ids", []))),
                )
                for shot in raw_shots
                if isinstance(shot, dict)
            )
            scene_duration = _positive_number(
                raw_scene.get("duration_seconds"), f"Scene {index} duration"
            )
            scenes.append(
                ScenePlan(
                    scene_id=str(raw_scene.get("scene_id", f"scene_{index:02d}")).strip(),
                    title=str(raw_scene.get("title", "")).strip(),
                    setting=str(raw_scene.get("setting", "")).strip(),
                    action=str(raw_scene.get("action", "")).strip(),
                    narration=str(raw_scene.get("narration", "")).strip(),
                    dialogue=dialogue,
                    shots=shots,
                    duration_seconds=scene_duration,
                )
            )

        plan = cls(
            title=str(data.get("title", "")).strip(),
            logline=str(data.get("logline", "")).strip(),
            learning_objective=str(data.get("learning_objective", "")).strip(),
            target_age_min=int(data.get("target_age_min", 2)),
            target_age_max=int(data.get("target_age_max", 5)),
            language=str(data.get("language", "English")).strip(),
            character_ids=tuple(_string_list(data.get("character_ids", []))),
            scenes=tuple(scenes),
        )
        validate_episode_plan(plan)
        return plan


def _positive_number(value: Any, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise EpisodePlanError(f"{label} must be a number.") from exc
    if number <= 0:
        raise EpisodePlanError(f"{label} must be greater than zero.")
    return number


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        raise EpisodePlanError("Character IDs must be an array.")
    return [str(item).strip().lower() for item in value if str(item).strip()]


def validate_episode_plan(plan: EpisodePlan) -> None:
    if not plan.title or not plan.logline or not plan.learning_objective:
        raise EpisodePlanError("Title, logline and learning objective are required.")
    if not (2 <= plan.target_age_min <= plan.target_age_max <= 5):
        raise EpisodePlanError("Target age range must be within ages 2–5.")
    if not plan.language:
        raise EpisodePlanError("Episode language is required.")
    if not plan.character_ids:
        raise EpisodePlanError("At least one approved character must be selected.")

    used_characters = set(plan.character_ids)
    if len(used_characters) != len(plan.character_ids):
        raise EpisodePlanError("Episode character IDs must not contain duplicates.")
    unknown = used_characters - APPROVED_CHARACTER_IDS
    if unknown:
        raise EpisodePlanError(
            "Unapproved character ID(s): " + ", ".join(sorted(unknown))
        )

    if not plan.scenes:
        raise EpisodePlanError("At least one scene is required.")
    scene_ids: set[str] = set()
    for scene in plan.scenes:
        if not scene.scene_id or scene.scene_id in scene_ids:
            raise EpisodePlanError("Every scene must have a unique, non-empty scene_id.")
        scene_ids.add(scene.scene_id)
        if not all((scene.title, scene.setting, scene.action)):
            raise EpisodePlanError(f"{scene.scene_id} needs a title, setting and action.")
        if not scene.shots:
            raise EpisodePlanError(f"{scene.scene_id} must contain at least one shot.")
        for shot in scene.shots:
            if not shot.description:
                raise EpisodePlanError(f"{scene.scene_id} contains a shot without a description.")
            unknown_shot_characters = set(shot.character_ids) - APPROVED_CHARACTER_IDS
            if unknown_shot_characters:
                raise EpisodePlanError(
                    f"{scene.scene_id} uses unapproved shot character(s): "
                    + ", ".join(sorted(unknown_shot_characters))
                )
            if not set(shot.character_ids).issubset(used_characters):
                raise EpisodePlanError(
                    f"{scene.scene_id} shot references a character not selected for this episode."
                )
        for line in scene.dialogue:
            if not line.text:
                raise EpisodePlanError(f"{scene.scene_id} contains an empty dialogue line.")
            if line.speaker_id not in used_characters:
                raise EpisodePlanError(
                    f"{scene.scene_id} dialogue speaker '{line.speaker_id}' is not selected."
                )


class LittleDreamersStoryPlanner:
    """Creates and validates preschool episode plans using the local Ollama client."""

    SYSTEM_PROMPT = (
        "You are the Little Dreamers preschool animation story planner. "
        "Write warm, playful, age-appropriate stories for children ages 2–5. "
        "Use only the approved character IDs supplied by the creator. "
        "Keep sentences short, concrete and easy to repeat aloud. "
        "Give children a clear learning progression, a simple problem, "
        "a child-participation moment that changes what happens, and a joyful resolution. "
        "Never invent or redesign character appearances. Return only JSON."
    )

    def __init__(self, client: JSONGenerator | None = None) -> None:
        self.client = client or OllamaClient()

    def plan_episode(
        self,
        brief: EpisodeBrief,
        *,
        model: str | None = None,
        temperature: float = 0.35,
    ) -> EpisodePlan:
        if not brief.title.strip() or not brief.learning_objective.strip():
            raise ValueError("Episode title and learning objective are required.")
        if not (2 <= brief.target_age_min <= brief.target_age_max <= 5):
            raise ValueError("Target age range must be within ages 2–5.")
        selected = tuple(item.strip().lower() for item in brief.character_ids)
        if not selected or len(set(selected)) != len(selected):
            raise ValueError("Select one or more unique approved character IDs.")
        unknown = set(selected) - APPROVED_CHARACTER_IDS
        if unknown:
            raise ValueError("Unapproved character ID(s): " + ", ".join(sorted(unknown)))

        prompt = f"""
Create a production-ready episode plan using this brief:
{{
  "title": {brief.title!r},
  "learning_objective": {brief.learning_objective!r},
  "target_age_min": {brief.target_age_min},
  "target_age_max": {brief.target_age_max},
  "language": {brief.language!r},
  "target_duration_seconds": {brief.target_duration_seconds},
  "approved_character_ids": {list(selected)!r}
}}

Return exactly this JSON shape:
{{
  "title": "Episode title",
  "logline": "One-sentence story premise",
  "learning_objective": "What the child will learn",
  "target_age_min": {brief.target_age_min},
  "target_age_max": {brief.target_age_max},
  "language": {brief.language!r},
  "character_ids": {list(selected)!r},
  "scenes": [
    {{
      "scene_id": "scene_01",
      "title": "Short scene title",
      "setting": "Where the scene happens",
      "action": "Visible, filmable action and emotional beat",
      "narration": "Optional short narrator text",
      "duration_seconds": 45,
      "dialogue": [{{"speaker_id": "aarav", "text": "Short spoken line."}}],
      "shots": [
        {{
          "description": "Specific camera framing and visible action",
          "duration_seconds": 8,
          "character_ids": ["aarav"]
        }}
      ]
    }}
  ]
}}

Create 3–6 connected scenes. Keep the total near the requested duration.
Each scene needs 1–5 filmable shots. Shot durations should add up to the scene duration
within 2 seconds. Every dialogue speaker and shot character must be selected above.
Do not add characters, visual redesign notes, production costs, or publishing instructions.
"""
        result = self.client.generate_json(
            prompt,
            system=self.SYSTEM_PROMPT,
            model=model,
            temperature=temperature,
        )
        # Check the episode-level selection before parsing shot-level references.
        # This ensures a mismatched generated character set produces the actionable
        # brief mismatch error rather than a secondary shot validation error.
        if isinstance(result, dict):
            generated_ids = tuple(_string_list(result.get("character_ids", [])))
            unknown_generated = set(generated_ids) - APPROVED_CHARACTER_IDS
            if unknown_generated:
                raise EpisodePlanError(
                    "Unapproved generated character ID(s): "
                    + ", ".join(sorted(unknown_generated))
                )
            if generated_ids != selected:
                raise EpisodePlanError(
                    "Generated episode character IDs must exactly match the approved brief."
                )

        plan = EpisodePlan.from_dict(result)
        if not 3 <= len(plan.scenes) <= 6:
            raise EpisodePlanError("Episode plan must contain between 3 and 6 scenes.")
        if any(not 1 <= len(scene.shots) <= 5 for scene in plan.scenes):
            raise EpisodePlanError("Every scene must contain between 1 and 5 shots.")
        if abs(plan.total_duration_seconds - brief.target_duration_seconds) > max(
            20, brief.target_duration_seconds * 0.25
        ):
            raise EpisodePlanError(
                "Generated episode duration is too far from the requested target."
            )
        for scene in plan.scenes:
            shot_total = sum(shot.duration_seconds for shot in scene.shots)
            if abs(shot_total - scene.duration_seconds) > 2:
                raise EpisodePlanError(
                    f"{scene.scene_id} shot durations ({shot_total:g}s) do not match "
                    f"scene duration ({scene.duration_seconds:g}s)."
                )
        return plan
