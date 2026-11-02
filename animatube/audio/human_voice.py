from __future__ import annotations

import logging
import math
import os
from pathlib import Path
import shutil
import subprocess
import wave

from animatube.core.models import Scene

logger = logging.getLogger(__name__)

SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac"}


def measure_audio_duration(audio_path: str | Path, ffmpeg_path: str | None = None) -> float:
    """
    Measures duration of an audio file in seconds.
    Uses Python's standard wave library for WAV, and ffprobe/ffmpeg for other formats.
    """
    p = Path(audio_path).resolve()
    if not p.is_file() or p.stat().st_size == 0:
        raise FileNotFoundError(f"Audio file not found or empty: {p}")

    ext = p.suffix.lower()
    if ext == ".wav":
        try:
            with wave.open(str(p), "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                if rate > 0:
                    return frames / float(rate)
        except Exception:
            pass

    # Use ffprobe if available
    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        try:
            cmd = [
                ffprobe,
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(p),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if res.returncode == 0 and res.stdout.strip():
                return float(res.stdout.strip())
        except Exception:
            pass

    # Fallback estimate for 128kbps MP3
    size_bytes = p.stat().st_size
    return max(0.5, size_bytes / 16000.0)


class HumanVoiceImporter:
    """
    Imports and processes authentic human voice recordings:
    - Normalizes volume (EBU R128 or peak).
    - Trims leading and trailing silence with configurable thresholds.
    - Synchronizes scene timeline to ensure no speech cutoff.
    """

    def __init__(self, ffmpeg_path: str | None = None) -> None:
        self.ffmpeg_path = ffmpeg_path or os.environ.get("FFMPEG_PATH") or shutil.which("ffmpeg")

    def validate_format(self, path: str | Path) -> Path:
        """Validates that the file exists and is a supported audio format."""
        p = Path(path).resolve()
        if not p.is_file():
            raise FileNotFoundError(f"Audio recording file not found: {p}")
        if p.suffix.lower() not in SUPPORTED_AUDIO_EXTENSIONS:
            raise ValueError(
                f"Unsupported audio format '{p.suffix}'. Supported: {', '.join(sorted(SUPPORTED_AUDIO_EXTENSIONS))}"
            )
        if p.stat().st_size == 0:
            raise ValueError(f"Audio file is 0 bytes: {p}")
        return p

    def process_recording(
        self,
        source_audio_path: str | Path,
        destination_path: str | Path,
        *,
        trim_silence: bool = True,
        normalize_volume: bool = True,
        silence_threshold_db: float = -40.0,
        target_sample_rate: int = 44100,
    ) -> tuple[Path, float]:
        """
        Processes human recording with optional silence removal and loudness normalization.
        Outputs a clean, standardized WAV/MP3 ready for timeline synchronization.
        Returns (processed_path, duration_seconds).
        """
        source = self.validate_format(source_audio_path)
        target = Path(destination_path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)

        if not self.ffmpeg_path:
            # Fallback: Copy file directly if FFmpeg is unavailable
            logger.info("FFmpeg unavailable, copying recording directly: %s", source.name)
            shutil.copy2(source, target)
            return target, measure_audio_duration(target)

        # Build FFmpeg audio filter chain
        filters: list[str] = []

        if trim_silence:
            # Remove leading silence and trailing silence
            th = abs(silence_threshold_db)
            filters.append(
                f"silenceremove=start_periods=1:start_duration=0.1:start_threshold=-{th}dB:"
                f"stop_periods=1:stop_duration=0.25:stop_threshold=-{th}dB"
            )

        if normalize_volume:
            # Loudnorm filter (integrated loudness: -16 LUFS, peak: -1.5 dBFS)
            filters.append("loudnorm=I=-16:TP=-1.5:LRA=11")

        cmd = [
            self.ffmpeg_path,
            "-hide_banner",
            "-loglevel", "error",
            "-y",
            "-i", str(source),
            "-ar", str(target_sample_rate),
            "-ac", "2",
        ]

        if filters:
            cmd.extend(["-af", ",".join(filters)])

        if target.suffix.lower() == ".mp3":
            cmd.extend(["-c:a", "libmp3lame", "-b:a", "192k"])
        else:
            cmd.extend(["-c:a", "pcm_s16le"])

        cmd.append(str(target))

        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode != 0:
            logger.warning("FFmpeg audio filter failed (%s), copying raw file.", res.stderr.strip())
            shutil.copy2(source, target)

        # A silence filter can remove every sample from silent/very quiet takes.
        # Preserve the original recording rather than returning a zero-length timeline.
        duration = 0.0
        if target.is_file() and target.stat().st_size > 0:
            try:
                duration = measure_audio_duration(target, ffmpeg_path=self.ffmpeg_path)
            except (OSError, ValueError, wave.Error):
                logger.warning("Could not measure processed recording; restoring original audio.")

        if not math.isfinite(duration) or duration <= 0:
            logger.warning(
                "Processed recording has no measurable audio; preserving original recording: %s",
                source.name,
            )
            shutil.copy2(source, target)
            duration = measure_audio_duration(source, ffmpeg_path=self.ffmpeg_path)

        return target, duration

    @staticmethod
    def sync_scene_duration(
        scene: Scene,
        audio_duration_seconds: float,
        fps: int = 30,
        tail_grace_seconds: float = 0.35,
    ) -> int:
        """
        Synchronizes scene's duration_frames with audio length.
        Includes a grace margin (+0.35s) to guarantee the last spoken syllable is never truncated.
        """
        safe_duration = max(0.5, audio_duration_seconds + tail_grace_seconds)
        required_frames = max(30, int(round(safe_duration * fps)))
        scene.duration_frames = required_frames
        return required_frames
