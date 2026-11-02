from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from animatube.ai.models import (
    AIGenerationJob,
    GenerationCapability,
    MediaType,
    MusicPrompt,
    VideoPrompt,
    VoicePrompt,
)


class BaseAIProvider(ABC):
    """Abstract base class for all AI generation provider adapters."""

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Unique identifier, e.g. 'mock_video', 'luma_dream_machine', 'elevenlabs', 'suno'."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable display name, e.g. 'Mock Video Generator', 'Luma Dream Machine'."""
        pass

    @property
    @abstractmethod
    def media_type(self) -> MediaType:
        """Type of media generated: VIDEO, VOICE, or MUSIC."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> GenerationCapability:
        """Declared capabilities supported by this provider."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Checks if provider dependencies, local engines, or required credentials exist."""
        pass

    @abstractmethod
    def validate_input(self, prompt: Any) -> None:
        """Validates prompt parameters against provider constraints; raises ValueError on error."""
        pass

    @abstractmethod
    def submit_job(self, prompt: Any, output_dir: str | Path) -> AIGenerationJob:
        """Submits an asynchronous generation job and returns the tracking record."""
        pass

    @abstractmethod
    def get_job_status(self, job_id: str) -> AIGenerationJob:
        """Polls current status and progress of an active or completed job."""
        pass

    @abstractmethod
    def cancel_job(self, job_id: str) -> bool:
        """Attempts to cancel an active job. Returns True if successfully aborted."""
        pass

    def generate_sync(self, prompt: Any, output_path: str | Path) -> AIGenerationJob:
        """Synchronous generation helper for command-line batch runs or unit tests."""
        dest = Path(output_path).resolve()
        job = self.submit_job(prompt, dest.parent)
        # Default polling loop; subclasses may override with direct generation
        import time
        while not job.is_finished():
            time.sleep(0.1)
            job = self.get_job_status(job.job_id)
        return job


class VideoGenerationProvider(BaseAIProvider):
    """Abstract interface for AI Video Generation (Text-to-Video and Image-to-Video)."""

    @property
    def media_type(self) -> MediaType:
        return MediaType.VIDEO

    @abstractmethod
    def validate_input(self, prompt: VideoPrompt) -> None:
        pass

    @abstractmethod
    def submit_job(self, prompt: VideoPrompt, output_dir: str | Path) -> AIGenerationJob:
        pass


class VoiceGenerationProvider(BaseAIProvider):
    """Abstract interface for AI Voice and Speech Generation."""

    @property
    def media_type(self) -> MediaType:
        return MediaType.VOICE

    @abstractmethod
    def validate_input(self, prompt: VoicePrompt) -> None:
        pass

    @abstractmethod
    def submit_job(self, prompt: VoicePrompt, output_dir: str | Path) -> AIGenerationJob:
        pass

    @abstractmethod
    def list_voices(self) -> list[dict[str, Any]]:
        """Returns list of available voice profiles with id, name, gender, and description."""
        pass


class MusicGenerationProvider(BaseAIProvider):
    """Abstract interface for AI Music and Sound Effect Generation."""

    @property
    def media_type(self) -> MediaType:
        return MediaType.MUSIC

    @abstractmethod
    def validate_input(self, prompt: MusicPrompt) -> None:
        pass

    @abstractmethod
    def submit_job(self, prompt: MusicPrompt, output_dir: str | Path) -> AIGenerationJob:
        pass
