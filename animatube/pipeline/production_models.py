from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any


@dataclass
class ShotDirection:
    """Detailed shot direction specification for AI video and audio generation."""
    scene_number: int
    shot_number: int
    shot_id: str
    duration_seconds: float
    characters: list[str]
    environment: str
    actions: str
    facial_expressions: str
    camera_angle: str       # "Wide Establishing", "Medium Two-Shot", "Character Close-up", "Reaction"
    camera_movement: str    # "pan_right", "pan_left", "zoom_in", "zoom_out", "orbit", "static"
    lighting: str
    dialogue: list[dict[str, str]] = field(default_factory=list)  # [{"speaker": "Aarav", "text": "...", "voice_id": "aarav_boy"}]
    narration: str = ""
    sound_effects: list[str] = field(default_factory=list)
    music_cue: str = ""
    character_references: list[str] = field(default_factory=list)
    transition: str = "crossfade"  # "cut", "crossfade", "sparkle_reveal", "slide"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SceneProduction:
    """Production breakdown of a single scene containing individual shots."""
    scene_number: int
    title: str
    duration_seconds: float
    setting: str
    shots: list[ShotDirection] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scene_number": self.scene_number,
            "title": self.title,
            "duration_seconds": self.duration_seconds,
            "setting": self.setting,
            "shots": [s.to_dict() for s in self.shots],
        }


@dataclass
class EpisodeProduction:
    """Complete multi-scene preschool animation episode master specification."""
    episode_id: str = "ep01_magic_abc_train"
    title: str = "THE MAGIC ABC TRAIN"
    series: str = "Little Dreamers"
    tagline: str = "Sing • Learn • Play • Grow"
    target_audience: str = "Children aged 2–5"
    language: str = "English"
    resolution: tuple[int, int] = (1920, 1080)
    fps: int = 24
    scenes: list[SceneProduction] = field(default_factory=list)

    @property
    def total_duration_seconds(self) -> float:
        return sum(s.duration_seconds for s in self.scenes)

    @property
    def total_shots_count(self) -> int:
        return sum(len(s.shots) for s in self.scenes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "title": self.title,
            "series": self.series,
            "tagline": self.tagline,
            "target_audience": self.target_audience,
            "language": self.language,
            "resolution": list(self.resolution),
            "fps": self.fps,
            "total_duration_seconds": self.total_duration_seconds,
            "total_shots_count": self.total_shots_count,
            "scenes": [s.to_dict() for s in self.scenes],
        }

    def export_storyboard_json(self, output_path: str | Path) -> Path:
        out = Path(output_path).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return out

    def export_shot_list_markdown(self, output_path: str | Path) -> Path:
        out = Path(output_path).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            f"# {self.series} — {self.title}",
            f"**Tagline:** {self.tagline} | **Audience:** {self.target_audience} | **Format:** {self.resolution[0]}x{self.resolution[1]} @ {self.fps}fps",
            f"**Total Duration:** {self.total_duration_seconds:.0f}s (~{self.total_duration_seconds / 60:.1f} mins) | **Total Shots:** {self.total_shots_count}\n",
            "---",
        ]

        for sc in self.scenes:
            lines.append(f"\n## Scene {sc.scene_number}: {sc.title} ({sc.duration_seconds:.0f}s)")
            lines.append(f"**Setting:** {sc.setting}\n")
            lines.append("| Shot | Duration | Angle / Movement | Characters | Action / Dialogue | Audio & Cues |")
            lines.append("| :--- | :---: | :--- | :--- | :--- | :--- |")
            for sh in sc.shots:
                chars = ", ".join(sh.characters) if sh.characters else "Environment"
                diag_text = " ".join(f"**{d['speaker']}**: \"{d['text']}\"" for d in sh.dialogue)
                diag_summary = f"{sh.actions}. {diag_text}".strip()
                audio_summary = f"BGM: {sh.music_cue}. SFX: {', '.join(sh.sound_effects) if sh.sound_effects else 'None'}"
                cam = f"{sh.camera_angle} ({sh.camera_movement})"
                lines.append(f"| **{sh.shot_id}** | {sh.duration_seconds:.1f}s | {cam} | {chars} | {diag_summary} | {audio_summary} |")

        out.write_text("\n".join(lines), encoding="utf-8")
        return out
