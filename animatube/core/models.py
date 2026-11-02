from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4


KINDS = {"text", "rect", "ellipse", "image"}
EASINGS = {"linear", "ease-in", "ease-out", "ease-in-out"}


def _id() -> str:
    return uuid4().hex


def _finite_number(value: Any, name: str) -> float:
    number = float(value)
    if number != number or number in (float("inf"), float("-inf")):
        raise ValueError(f"{name} must be a finite number")
    return number


@dataclass
class Keyframe:
    frame: int
    x: float
    y: float
    scale: float = 1.0
    rotation: float = 0.0
    opacity: float = 1.0
    easing: str = "linear"

    def __post_init__(self) -> None:
        if self.frame < 0:
            raise ValueError("Keyframe frame cannot be negative")
        if self.easing not in EASINGS:
            raise ValueError(f"Unsupported easing: {self.easing}")
        for name in ("x", "y", "scale", "rotation", "opacity"):
            setattr(self, name, _finite_number(getattr(self, name), name))
        if self.scale <= 0:
            raise ValueError("Keyframe scale must be greater than zero")
        if not 0 <= self.opacity <= 1:
            raise ValueError("Keyframe opacity must be between 0 and 1")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Keyframe":
        return cls(**{key: data[key] for key in ("frame", "x", "y")},
                   scale=data.get("scale", 1), rotation=data.get("rotation", 0),
                   opacity=data.get("opacity", 1), easing=data.get("easing", "linear"))


@dataclass
class Layer:
    id: str = field(default_factory=_id)
    name: str = "Text"
    kind: str = "text"
    x: float = 80
    y: float = 80
    width: float = 480
    height: float = 120
    text: str = "Your title"
    color: str = "#ffffff"
    font_size: int = 56
    asset_path: str = ""
    keyframes: list[Keyframe] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(f"Unsupported layer kind: {self.kind}")
        for name in ("x", "y", "width", "height"):
            setattr(self, name, _finite_number(getattr(self, name), name))
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Layer dimensions must be greater than zero")
        if not 1 <= int(self.font_size) <= 512:
            raise ValueError("Font size must be between 1 and 512")
        self.font_size = int(self.font_size)
        if not isinstance(self.text, str) or not isinstance(self.asset_path, str):
            raise ValueError("Layer text and asset path must be strings")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Layer":
        return cls(id=str(data.get("id") or _id()), name=str(data.get("name", "Layer")),
                   kind=str(data.get("kind", "text")), x=data.get("x", 80), y=data.get("y", 80),
                   width=data.get("width", 480), height=data.get("height", 120),
                   text=str(data.get("text", "")), color=str(data.get("color", "#ffffff")),
                   font_size=data.get("font_size", 56), asset_path=str(data.get("asset_path", "")),
                   keyframes=[Keyframe.from_dict(item) for item in data.get("keyframes", [])])


@dataclass
class Scene:
    id: str = field(default_factory=_id)
    name: str = "Scene 1"
    duration_frames: int = 150
    layers: list[Layer] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not 1 <= int(self.duration_frames) <= 60 * 60 * 60:
            raise ValueError("Scene duration must be between 1 and 216000 frames")
        self.duration_frames = int(self.duration_frames)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Scene":
        return cls(id=str(data.get("id") or _id()), name=str(data.get("name", "Scene")),
                   duration_frames=data.get("duration_frames", 150),
                   layers=[Layer.from_dict(item) for item in data.get("layers", [])])


@dataclass
class Project:
    name: str = "Untitled Project"
    width: int = 1920
    height: int = 1080
    fps: int = 30
    background: str = "#151821"
    scenes: list[Scene] = field(default_factory=lambda: [Scene()])
    path: str = ""

    def __post_init__(self) -> None:
        if not 16 <= int(self.width) <= 7680 or not 16 <= int(self.height) <= 7680:
            raise ValueError("Project dimensions must be between 16 and 7680 pixels")
        if int(self.fps) not in (24, 25, 30, 50, 60):
            raise ValueError("Frame rate must be 24, 25, 30, 50 or 60 fps")
        self.width, self.height, self.fps = int(self.width), int(self.height), int(self.fps)
        if not self.scenes:
            self.scenes = [Scene()]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("path", None)
        data["format_version"] = 1
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Project":
        if not isinstance(data, dict) or data.get("format_version", 1) != 1:
            raise ValueError("Unsupported or invalid AnimaTube project format")
        return cls(name=str(data.get("name", "Untitled Project")), width=data.get("width", 1920),
                   height=data.get("height", 1080), fps=data.get("fps", 30),
                   background=str(data.get("background", "#151821")),
                   scenes=[Scene.from_dict(item) for item in data.get("scenes", [])])

    def resolve_asset(self, asset_path: str) -> Path:
        path = Path(asset_path).expanduser()
        if path.is_absolute() or not self.path:
            return path
        return (Path(self.path).parent / path).resolve()
