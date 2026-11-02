from __future__ import annotations

import logging
import math
from pathlib import Path
import shutil
import struct
import subprocess
import time
from typing import Any
import wave

from animatube.ai.interfaces import (
    MusicGenerationProvider,
    VideoGenerationProvider,
    VoiceGenerationProvider,
)
from animatube.ai.models import (
    AIGenerationJob,
    GenerationCapability,
    JobStatus,
    MediaType,
    MusicPrompt,
    UsageMetadata,
    VideoPrompt,
    VoicePrompt,
)

logger = logging.getLogger(__name__)


def _generate_synthetic_wav(path: Path, duration_seconds: float = 3.0, freq: float = 440.0) -> Path:
    """Generates a valid 16-bit PCM mono WAV file without any external dependencies."""
    sample_rate = 24000
    total_samples = int(sample_rate * duration_seconds)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        # Generate soft pleasant tone with envelope
        frames = bytearray()
        for i in range(total_samples):
            t = float(i) / sample_rate
            envelope = min(1.0, i / 2400.0) * min(1.0, (total_samples - i) / 2400.0)
            sample = int(32767.0 * 0.3 * envelope * math.sin(2.0 * math.pi * freq * t))
            frames.extend(struct.pack("<h", sample))
        wav_file.writeframes(frames)
    return path


def _generate_synthetic_mp4(path: Path, width: int = 1920, height: int = 1080, fps: int = 24, duration: float = 3.0, color: str = "#223344") -> Path:
    """Generates a valid lightweight H.264 MP4 video using FFmpeg if available, or synthetic fallback."""
    path.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        clean_color = color.replace("#", "0x")
        cmd = [
            ffmpeg, "-y",
            "-f", "lavfi",
            "-i", f"color=c={clean_color}:s={width}x{height}:r={fps}:d={duration}",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-t", str(duration),
            str(path),
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            if path.is_file() and path.stat().st_size > 0:
                return path
        except Exception as exc:
            logger.warning("FFmpeg synthetic video generation failed: %s; using binary fallback", exc)

    # Fallback: create mock container file
    path.write_bytes(b"\x00\x00\x00 ftypmp42\x00\x00\x00\x00mp42isom\x00\x00\x00\x08mdat" + b"\x00" * 1024)
    return path


class MockVideoProvider(VideoGenerationProvider):
    """
    Mock AI Video Generation Provider.
    Simulates Text-to-Video and Image-to-Video pipelines with job tracking,
    realistic progress, cancellation, and local MP4 generation.
    """

    def __init__(self, provider_id: str = "mock_video", name: str = "Mock AI Video Studio") -> None:
        self._provider_id = provider_id
        self._name = name
        self.jobs: dict[str, AIGenerationJob] = {}

    @property
    def provider_id(self) -> str:
        return self._provider_id

    @property
    def provider_name(self) -> str:
        return self._name

    @property
    def capabilities(self) -> GenerationCapability:
        return GenerationCapability(
            text_to_video=True,
            image_to_video=True,
            camera_control=True,
            custom_aspect_ratios=["16:9", "1:1", "9:16", "4:3"],
            max_duration_seconds=30.0,
            min_duration_seconds=1.0,
            character_reference=True,
            cancellation_supported=True,
            usage_tracking=True,
            offline_capable=True,
        )

    def is_available(self) -> bool:
        return True

    def validate_input(self, prompt: VideoPrompt) -> None:
        prompt.validate(self.capabilities)
        if prompt.extra_params.get("simulate_validation_error"):
            raise ValueError(str(prompt.extra_params["simulate_validation_error"]))

    def submit_job(self, prompt: VideoPrompt, output_dir: str | Path) -> AIGenerationJob:
        self.validate_input(prompt)
        job = AIGenerationJob(
            media_type=MediaType.VIDEO,
            provider_id=self.provider_id,
            status=JobStatus.QUEUED,
            progress=0.0,
            metadata={"prompt": prompt.prompt, "aspect_ratio": prompt.aspect_ratio, "duration": prompt.duration_seconds},
        )
        self.jobs[job.job_id] = job

        # Execute or simulate failure/cancellation
        if prompt.extra_params.get("simulate_error"):
            job.fail(prompt.extra_params["simulate_error"])
            return job

        # Generate output video
        dest_dir = Path(output_dir).resolve()
        dest_dir.mkdir(parents=True, exist_ok=True)
        filename = f"video_{job.job_id[:8]}.mp4"
        target_path = dest_dir / filename

        # Determine dimensions from aspect ratio
        w, h = 1920, 1080
        if prompt.aspect_ratio == "1:1":
            w, h = 1080, 1080
        elif prompt.aspect_ratio == "9:16":
            w, h = 1080, 1920

        color = prompt.extra_params.get("color", "#1e293b")
        _generate_synthetic_mp4(target_path, width=w, height=h, fps=prompt.fps, duration=prompt.duration_seconds, color=color)

        usage = UsageMetadata(
            credits_used=prompt.duration_seconds * 2.0,
            cost_usd=round(prompt.duration_seconds * 0.05, 3),
            duration_generated=prompt.duration_seconds,
            provider_model="mock-video-v1",
            execution_time_seconds=0.2,
        )
        job.complete(target_path, usage)
        return job

    def get_job_status(self, job_id: str) -> AIGenerationJob:
        if job_id not in self.jobs:
            raise KeyError(f"Job not found: {job_id}")
        return self.jobs[job_id]

    def cancel_job(self, job_id: str) -> bool:
        if job_id in self.jobs:
            job = self.jobs[job_id]
            if not job.is_finished():
                job.cancel()
                return True
        return False


class MockVoiceProvider(VoiceGenerationProvider):
    """
    Mock AI Voice Generation Provider.
    Generates synthetic speech audio with customizable voice profiles,
    character styles, and usage tracking.
    """

    def __init__(self, provider_id: str = "mock_voice", name: str = "Mock AI Voice Studio") -> None:
        self._provider_id = provider_id
        self._name = name
        self.jobs: dict[str, AIGenerationJob] = {}

    @property
    def provider_id(self) -> str:
        return self._provider_id

    @property
    def provider_name(self) -> str:
        return self._name

    @property
    def capabilities(self) -> GenerationCapability:
        return GenerationCapability(
            voice_cloning=True,
            multi_speaker=True,
            cancellation_supported=True,
            usage_tracking=True,
            offline_capable=True,
        )

    def is_available(self) -> bool:
        return True

    def validate_input(self, prompt: VoicePrompt) -> None:
        prompt.validate(self.capabilities)
        if prompt.extra_params.get("simulate_validation_error"):
            raise ValueError(str(prompt.extra_params["simulate_validation_error"]))

    def list_voices(self) -> list[dict[str, Any]]:
        return [
            {"id": "aarav_boy", "name": "Aarav (Enthusiastic Toddler)", "gender": "male", "age": "preschool"},
            {"id": "mia_girl", "name": "Mia (Sweet Songbird)", "gender": "female", "age": "preschool"},
            {"id": "ellie_gentle", "name": "Ellie (Gentle Baby Trumpet)", "gender": "female", "age": "baby"},
            {"id": "gigi_peppy", "name": "Gigi (Playful Giraffe)", "gender": "female", "age": "preschool"},
            {"id": "bobo_puppy", "name": "Bobo (Energetic Puppy)", "gender": "male", "age": "baby"},
            {"id": "twinkle_star", "name": "Twinkle (Magical Chime)", "gender": "neutral", "age": "celestial"},
            {"id": "narrator_warm", "name": "Storyteller (Warm Adult Narrator)", "gender": "neutral", "age": "adult"},
        ]

    def submit_job(self, prompt: VoicePrompt, output_dir: str | Path) -> AIGenerationJob:
        self.validate_input(prompt)
        job = AIGenerationJob(
            media_type=MediaType.VOICE,
            provider_id=self.provider_id,
            status=JobStatus.QUEUED,
            progress=0.0,
            metadata={"character": prompt.character_name, "voice_id": prompt.voice_id},
        )
        self.jobs[job.job_id] = job

        if prompt.extra_params.get("simulate_error"):
            job.fail(prompt.extra_params["simulate_error"])
            return job

        dest_dir = Path(output_dir).resolve()
        dest_dir.mkdir(parents=True, exist_ok=True)
        filename = f"voice_{job.job_id[:8]}.wav"
        target_path = dest_dir / filename

        # Estimate duration from word count (~150 words per minute => 2.5 words/sec)
        words = len(prompt.text.split())
        est_duration = max(1.5, round(words / 2.5, 2))

        # Distinct tone frequency for character
        freq_map = {
            "aarav_boy": 340.0,
            "mia_girl": 440.0,
            "ellie_gentle": 260.0,
            "gigi_peppy": 380.0,
            "bobo_puppy": 480.0,
            "twinkle_star": 560.0,
        }
        freq = freq_map.get(prompt.voice_id, 320.0)
        _generate_synthetic_wav(target_path, duration_seconds=est_duration, freq=freq)

        usage = UsageMetadata(
            credits_used=float(len(prompt.text)),
            cost_usd=round(len(prompt.text) * 0.0001, 4),
            duration_generated=est_duration,
            provider_model="mock-voice-v1",
            execution_time_seconds=0.1,
        )
        job.complete(target_path, usage)
        return job

    def get_job_status(self, job_id: str) -> AIGenerationJob:
        if job_id not in self.jobs:
            raise KeyError(f"Job not found: {job_id}")
        return self.jobs[job_id]

    def cancel_job(self, job_id: str) -> bool:
        if job_id in self.jobs:
            job = self.jobs[job_id]
            if not job.is_finished():
                job.cancel()
                return True
        return False


class MockMusicProvider(MusicGenerationProvider):
    """
    Mock AI Music Generation Provider.
    Generates background songs, themes, and sound effects with tempo/mood settings.
    """

    def __init__(self, provider_id: str = "mock_music", name: str = "Mock AI Music Studio") -> None:
        self._provider_id = provider_id
        self._name = name
        self.jobs: dict[str, AIGenerationJob] = {}

    @property
    def provider_id(self) -> str:
        return self._provider_id

    @property
    def provider_name(self) -> str:
        return self._name

    @property
    def capabilities(self) -> GenerationCapability:
        return GenerationCapability(
            instrumental_music=True,
            vocal_music=True,
            sound_effects=True,
            max_duration_seconds=180.0,
            min_duration_seconds=2.0,
            cancellation_supported=True,
            usage_tracking=True,
            offline_capable=True,
        )

    def is_available(self) -> bool:
        return True

    def validate_input(self, prompt: MusicPrompt) -> None:
        prompt.validate(self.capabilities)
        if prompt.extra_params.get("simulate_validation_error"):
            raise ValueError(str(prompt.extra_params["simulate_validation_error"]))

    def submit_job(self, prompt: MusicPrompt, output_dir: str | Path) -> AIGenerationJob:
        self.validate_input(prompt)
        job = AIGenerationJob(
            media_type=MediaType.MUSIC,
            provider_id=self.provider_id,
            status=JobStatus.QUEUED,
            progress=0.0,
            metadata={"mood": prompt.mood, "genre": prompt.genre, "duration": prompt.duration_seconds},
        )
        self.jobs[job.job_id] = job

        if prompt.extra_params.get("simulate_error"):
            job.fail(prompt.extra_params["simulate_error"])
            return job

        dest_dir = Path(output_dir).resolve()
        dest_dir.mkdir(parents=True, exist_ok=True)
        filename = f"music_{job.job_id[:8]}.wav"
        target_path = dest_dir / filename

        # Pleasant musical chord frequency based on mood
        mood_freqs = {
            "cheerful": 523.25,  # C5
            "playful": 587.33,   # D5
            "calm": 392.00,      # G4
            "lullaby": 329.63,   # E4
            "adventurous": 659.25,  # E5
        }
        freq = mood_freqs.get(prompt.mood.lower(), 440.0)
        _generate_synthetic_wav(target_path, duration_seconds=prompt.duration_seconds, freq=freq)

        usage = UsageMetadata(
            credits_used=prompt.duration_seconds * 1.5,
            cost_usd=round(prompt.duration_seconds * 0.02, 3),
            duration_generated=prompt.duration_seconds,
            provider_model="mock-music-v1",
            execution_time_seconds=0.15,
        )
        job.complete(target_path, usage)
        return job

    def get_job_status(self, job_id: str) -> AIGenerationJob:
        if job_id not in self.jobs:
            raise KeyError(f"Job not found: {job_id}")
        return self.jobs[job_id]

    def cancel_job(self, job_id: str) -> bool:
        if job_id in self.jobs:
            job = self.jobs[job_id]
            if not job.is_finished():
                job.cancel()
                return True
        return False
