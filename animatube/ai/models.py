from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4


class MediaType(str, Enum):
    VIDEO = "video"
    VOICE = "voice"
    MUSIC = "music"


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class GenerationCapability:
    """Declared capabilities supported by a specific provider adapter."""
    text_to_video: bool = False
    image_to_video: bool = False
    camera_control: bool = False
    custom_aspect_ratios: list[str] = field(default_factory=lambda: ["16:9", "1:1", "9:16"])
    max_duration_seconds: float = 60.0
    min_duration_seconds: float = 1.0
    character_reference: bool = False
    voice_cloning: bool = False
    multi_speaker: bool = False
    instrumental_music: bool = False
    vocal_music: bool = False
    sound_effects: bool = False
    cancellation_supported: bool = True
    usage_tracking: bool = True
    offline_capable: bool = False


@dataclass
class VideoPrompt:
    """Input parameters for AI video generation."""
    prompt: str
    negative_prompt: str = ""
    reference_image_path: str = ""
    aspect_ratio: str = "16:9"
    duration_seconds: float = 4.0
    fps: int = 24
    resolution: str = "1080p"
    camera_motion: str = "none"  # pan_left, pan_right, tilt_up, tilt_down, zoom_in, zoom_out, orbit, none
    seed: int | None = None
    motion_strength: float = 0.5  # 0.0 to 1.0
    extra_params: dict[str, Any] = field(default_factory=dict)

    def validate(self, capabilities: GenerationCapability | None = None) -> None:
        clean = self.prompt.strip()
        if not clean and not self.reference_image_path:
            raise ValueError("Video generation requires either a prompt description or a reference image.")
        if len(clean) > 2000:
            raise ValueError("Prompt must not exceed 2000 characters.")
        if self.reference_image_path:
            ref = Path(self.reference_image_path).expanduser()
            if not ref.is_file():
                raise FileNotFoundError(f"Reference image not found: {self.reference_image_path}")
        if self.aspect_ratio not in ("16:9", "1:1", "9:16", "4:3"):
            raise ValueError(f"Unsupported aspect ratio: {self.aspect_ratio}")
        if not 1.0 <= self.duration_seconds <= 120.0:
            raise ValueError(f"Duration must be between 1.0 and 120.0 seconds (got {self.duration_seconds}).")
        if not 0.0 <= self.motion_strength <= 1.0:
            raise ValueError("Motion strength must be between 0.0 and 1.0.")


@dataclass
class VoicePrompt:
    """Input parameters for AI voice and dialogue generation."""
    text: str
    voice_id: str = "default"
    character_name: str = "Narrator"
    language: str = "en"
    style: str = "conversational"  # educational, conversational, cheerful, story, gentle
    rate: str = "+0%"
    pitch: str = "+0Hz"
    stability: float = 0.75
    extra_params: dict[str, Any] = field(default_factory=dict)

    def validate(self, capabilities: GenerationCapability | None = None) -> None:
        clean = self.text.strip()
        if not clean:
            raise ValueError("Voice text cannot be empty.")
        if len(clean) > 10000:
            raise ValueError("Voice text exceeds maximum allowed length (10,000 characters).")


@dataclass
class MusicPrompt:
    """Input parameters for AI music and sound effect generation."""
    prompt: str
    mood: str = "cheerful"  # cheerful, playful, curious, calm, adventurous, lullaby, dramatic
    genre: str = "preschool_orchestral"  # preschool_orchestral, acoustic, synth_pop, ambient, cinematic
    duration_seconds: float = 30.0
    is_instrumental: bool = True
    tempo: str = "medium"  # slow, medium, upbeat
    sound_effect: bool = False
    extra_params: dict[str, Any] = field(default_factory=dict)

    def validate(self, capabilities: GenerationCapability | None = None) -> None:
        clean = self.prompt.strip()
        if not clean and not self.mood:
            raise ValueError("Music generation requires a prompt description or mood setting.")
        if not 1.0 <= self.duration_seconds <= 300.0:
            raise ValueError(f"Music duration must be between 1.0 and 300.0 seconds (got {self.duration_seconds}).")


@dataclass
class UsageMetadata:
    """Cost, credits, and execution metadata for a generation job."""
    credits_used: float = 0.0
    cost_usd: float = 0.0
    duration_generated: float = 0.0
    provider_model: str = "default"
    cached: bool = False
    execution_time_seconds: float = 0.0


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AIGenerationJob:
    """Asynchronous tracking record for any AI media generation request."""
    job_id: str = field(default_factory=lambda: uuid4().hex)
    media_type: MediaType = MediaType.VIDEO
    provider_id: str = "mock"
    status: JobStatus = JobStatus.QUEUED
    progress: float = 0.0  # 0.0 to 1.0
    result_path: str = ""
    error_message: str = ""
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    usage: UsageMetadata = field(default_factory=UsageMetadata)
    metadata: dict[str, Any] = field(default_factory=dict)

    def update_status(self, status: JobStatus, progress: float | None = None, error: str = "") -> None:
        self.status = status
        if progress is not None:
            self.progress = max(0.0, min(1.0, float(progress)))
        if error:
            self.error_message = str(error)
        self.updated_at = _now_iso()

    def complete(self, result_path: str | Path, usage: UsageMetadata | None = None) -> None:
        self.status = JobStatus.COMPLETED
        self.progress = 1.0
        self.result_path = str(Path(result_path).resolve())
        if usage:
            self.usage = usage
        self.updated_at = _now_iso()

    def fail(self, error: str) -> None:
        self.status = JobStatus.FAILED
        self.error_message = str(error)
        self.updated_at = _now_iso()

    def cancel(self) -> None:
        self.status = JobStatus.CANCELLED
        self.updated_at = _now_iso()

    def is_finished(self) -> bool:
        return self.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED)
