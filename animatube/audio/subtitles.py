from __future__ import annotations

import logging
import os
from pathlib import Path
import re
import shutil
import subprocess

logger = logging.getLogger(__name__)


def format_timestamp_srt(total_seconds: float) -> str:
    """Formats seconds into SRT timestamp: HH:MM:SS,mmm"""
    ms = int(round(total_seconds * 1000))
    hours, ms = divmod(ms, 3600000)
    minutes, ms = divmod(ms, 60000)
    seconds, ms = divmod(ms, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"


def format_timestamp_vtt(total_seconds: float) -> str:
    """Formats seconds into WebVTT timestamp: HH:MM:SS.mmm"""
    ms = int(round(total_seconds * 1000))
    hours, ms = divmod(ms, 3600000)
    minutes, ms = divmod(ms, 60000)
    seconds, ms = divmod(ms, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{ms:03d}"


def generate_subtitles_from_text(
    text: str,
    duration_seconds: float,
    output_path: str | Path,
    words_per_cue: int = 6,
) -> Path:
    """
    Splits narration text into synchronized subtitle cues distributed across the total duration.
    Produces a valid, standards-compliant .srt file.
    """
    target = Path(output_path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    words = text.strip().split()
    if not words:
        words = ["..."]

    # Group words into small, readable cues
    cues: list[str] = []
    for i in range(0, len(words), words_per_cue):
        cues.append(" ".join(words[i : i + words_per_cue]))

    time_per_cue = max(0.5, duration_seconds / len(cues))
    lines: list[str] = []

    current_time = 0.0
    for index, cue in enumerate(cues, start=1):
        start_time = current_time
        end_time = min(duration_seconds, current_time + time_per_cue)
        if index == len(cues):
            end_time = duration_seconds

        lines.append(str(index))
        lines.append(f"{format_timestamp_srt(start_time)} --> {format_timestamp_srt(end_time)}")
        lines.append(cue)
        lines.append("")

        current_time = end_time

    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


class SubtitleGenerator:
    """Wrapper for subtitle generation using local Whisper.cpp or text-based sync."""

    def __init__(
        self,
        executable_path: str | None = None,
        model_path: str | None = None,
    ) -> None:
        self.executable = (
            executable_path
            or os.environ.get("WHISPER_PATH")
            or shutil.which("whisper-cli")
            or shutil.which("whisper")
        )
        self.model_path = model_path or os.environ.get("WHISPER_MODEL")

    def is_available(self) -> bool:
        """Returns True if Whisper executable and model are configured."""
        if not self.executable:
            return False
        return (
            (Path(self.executable).is_file() or shutil.which(self.executable) is not None)
            and self.model_path is not None
            and Path(self.model_path).is_file()
        )

    def generate(
        self,
        audio_path: str | Path,
        output_srt_path: str | Path,
        *,
        reference_text: str = "",
        duration_seconds: float = 0.0,
        allow_fallback: bool = True,
    ) -> Path:
        """
        Generates subtitles for the given audio.
        Uses Whisper.cpp if present; otherwise uses reference text fallback.
        """
        target = Path(output_srt_path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)

        if not self.is_available():
            if allow_fallback and reference_text:
                if duration_seconds <= 0:
                    from animatube.audio.piper_tts import get_wav_duration_seconds
                    try:
                        duration_seconds = get_wav_duration_seconds(audio_path)
                    except Exception:
                        duration_seconds = 10.0
                return generate_subtitles_from_text(reference_text, duration_seconds, target)
            raise RuntimeError("Whisper.cpp binary or model not configured.")

        # Whisper.cpp CLI execution
        cmd = [
            self.executable,
            "-m",
            self.model_path,
            "-f",
            str(audio_path),
            "-osrt",
            "-of",
            str(target.with_suffix("")),  # whisper appends .srt automatically
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return target
