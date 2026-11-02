from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import uuid4


def _uid() -> str:
    return uuid4().hex[:8]


@dataclass
class ScriptScene:
    id: str = field(default_factory=_uid)
    title: str = "Scene"
    narration: str = ""
    visual_description: str = ""
    on_screen_elements: list[str] = field(default_factory=list)
    target_duration_seconds: float = 30.0
    diagram_type: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            self.id = _uid()
        if self.target_duration_seconds <= 0:
            raise ValueError("target_duration_seconds must be positive")
        self.target_duration_seconds = float(self.target_duration_seconds)
        if not isinstance(self.on_screen_elements, list):
            raise ValueError("on_screen_elements must be a list of strings")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScriptScene":
        return cls(
            id=str(data.get("id", _uid())),
            title=str(data.get("title", "Scene")),
            narration=str(data.get("narration", "")),
            visual_description=str(data.get("visual_description", "")),
            on_screen_elements=list(data.get("on_screen_elements", [])),
            target_duration_seconds=float(data.get("target_duration_seconds", 30.0)),
            diagram_type=str(data.get("diagram_type", "")),
        )


@dataclass
class Script:
    title: str = "Untitled Video"
    target_audience: str = "Indian beginners and freshers"
    scenes: list[ScriptScene] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "target_audience": self.target_audience,
            "scenes": [asdict(scene) for scene in self.scenes],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Script":
        scenes = [ScriptScene.from_dict(item) for item in data.get("scenes", [])]
        return cls(
            title=str(data.get("title", "Untitled Video")),
            target_audience=str(data.get("target_audience", "Indian beginners and freshers")),
            scenes=scenes,
        )

    def total_words(self) -> int:
        return sum(len(scene.narration.split()) for scene in self.scenes)

    def estimated_duration_seconds(self, words_per_minute: float = 145.0) -> float:
        words = self.total_words()
        if words == 0:
            return sum(scene.target_duration_seconds for scene in self.scenes)
        return (words / words_per_minute) * 60.0


@dataclass
class StoryboardScene:
    scene_id: str
    title: str
    duration_seconds: float
    duration_frames: int
    narration_audio_path: str = ""
    subtitle_path: str = ""
    visual_asset_paths: list[str] = field(default_factory=list)
    diagram_type: str = ""

    def __post_init__(self) -> None:
        if self.duration_seconds <= 0:
            raise ValueError("duration_seconds must be positive")
        if self.duration_frames <= 0:
            raise ValueError("duration_frames must be positive")
        self.duration_seconds = float(self.duration_seconds)
        self.duration_frames = int(self.duration_frames)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StoryboardScene":
        return cls(
            scene_id=str(data["scene_id"]),
            title=str(data.get("title", "Scene")),
            duration_seconds=float(data["duration_seconds"]),
            duration_frames=int(data["duration_frames"]),
            narration_audio_path=str(data.get("narration_audio_path", "")),
            subtitle_path=str(data.get("subtitle_path", "")),
            visual_asset_paths=list(data.get("visual_asset_paths", [])),
            diagram_type=str(data.get("diagram_type", "")),
        )


@dataclass
class Storyboard:
    title: str
    fps: int = 30
    width: int = 1920
    height: int = 1080
    scenes: list[StoryboardScene] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.fps <= 0:
            raise ValueError("fps must be positive")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("width and height must be positive")

    def total_duration_seconds(self) -> float:
        return sum(scene.duration_seconds for scene in self.scenes)

    def total_duration_frames(self) -> int:
        return sum(scene.duration_frames for scene in self.scenes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "fps": self.fps,
            "width": self.width,
            "height": self.height,
            "total_duration_seconds": self.total_duration_seconds(),
            "total_duration_frames": self.total_duration_frames(),
            "scenes": [asdict(scene) for scene in self.scenes],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Storyboard":
        scenes = [StoryboardScene.from_dict(item) for item in data.get("scenes", [])]
        return cls(
            title=str(data.get("title", "Storyboard")),
            fps=int(data.get("fps", 30)),
            width=int(data.get("width", 1920)),
            height=int(data.get("height", 1080)),
            scenes=scenes,
        )


@dataclass
class MediaManifest:
    project_name: str
    version: str = "1.0"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    script_file: str = ""
    storyboard_file: str = ""
    anima_project_file: str = ""
    kdenlive_project_file: str = ""
    output_video_file: str = ""
    thumbnail_file: str = ""
    metadata_file: str = ""
    chapters_file: str = ""
    assets: list[dict[str, Any]] = field(default_factory=list)

    def add_asset(self, path: str | Path, kind: str, metadata: dict[str, Any] | None = None) -> None:
        p = Path(path)
        sha256 = ""
        size = 0
        if p.is_file():
            content = p.read_bytes()
            sha256 = hashlib.sha256(content).hexdigest()
            size = len(content)
        entry: dict[str, Any] = {
            "path": str(path),
            "kind": kind,
            "sha256": sha256,
            "size_bytes": size,
        }
        if metadata:
            entry["metadata"] = metadata
        self.assets.append(entry)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MediaManifest":
        return cls(
            project_name=str(data.get("project_name", "AnimaTube Project")),
            version=str(data.get("version", "1.0")),
            created_at=str(data.get("created_at", datetime.now(timezone.utc).isoformat())),
            script_file=str(data.get("script_file", "")),
            storyboard_file=str(data.get("storyboard_file", "")),
            anima_project_file=str(data.get("anima_project_file", "")),
            kdenlive_project_file=str(data.get("kdenlive_project_file", "")),
            output_video_file=str(data.get("output_video_file", "")),
            thumbnail_file=str(data.get("thumbnail_file", "")),
            metadata_file=str(data.get("metadata_file", "")),
            chapters_file=str(data.get("chapters_file", "")),
            assets=list(data.get("assets", [])),
        )

    def save(self, destination: str | Path) -> Path:
        target = Path(destination).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            f.write("\n")
        return target

    @classmethod
    def load(cls, source: str | Path) -> "MediaManifest":
        target = Path(source).resolve()
        if not target.is_file():
            raise FileNotFoundError(f"Manifest file not found: {target}")
        with open(target, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))
