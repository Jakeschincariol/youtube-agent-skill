from __future__ import annotations

import logging
import os
from pathlib import Path
import shutil
import subprocess

from animatube.audio.human_voice import measure_audio_duration

logger = logging.getLogger(__name__)


class AudioMixer:
    """
    Mixes voiceover narration and background music into a balanced, professional audio track:
    - Keeps background music noticeably lower than speech (configurable volume, e.g. 15%).
    - Auto-loops or trims background music to match total duration.
    - Applies smooth fade-out on music at the end.
    """

    def __init__(self, ffmpeg_path: str | None = None) -> None:
        self.ffmpeg_path = ffmpeg_path or os.environ.get("FFMPEG_PATH") or shutil.which("ffmpeg")

    def mix(
        self,
        narration_path: str | Path,
        output_path: str | Path,
        *,
        music_path: str | Path | None = None,
        narration_volume: float = 1.0,
        music_volume: float = 0.15,
        target_duration_seconds: float | None = None,
        music_fade_out_seconds: float = 1.5,
    ) -> Path:
        """
        Combines narration and background music into one master track.
        If music_path is None or missing, outputs clean narration track.
        """
        narr_file = Path(narration_path).resolve()
        if not narr_file.is_file():
            raise FileNotFoundError(f"Narration audio track not found: {narr_file}")

        target = Path(output_path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)

        music_file = Path(music_path).resolve() if music_path else None
        has_music = music_file and music_file.is_file() and music_file.stat().st_size > 0

        # If no music or FFmpeg missing, just copy narration
        if not has_music or not self.ffmpeg_path:
            shutil.copy2(narr_file, target)
            return target

        duration = target_duration_seconds or measure_audio_duration(narr_file, self.ffmpeg_path)
        fade_start = max(0.5, duration - music_fade_out_seconds)

        # Build FFmpeg filter complex:
        # [0:a]volume=1.0[narr];[1:a]volume=0.15,aloop=loop=-1:size=2e+09,afade=t=out:st=fade_start:d=1.5[music];[narr][music]amix=inputs=2:duration=first:dropout_transition=2[out]
        filter_complex = (
            f"[0:a]volume={max(0.0, narration_volume):.2f}[narr];"
            f"[1:a]volume={max(0.0, music_volume):.2f},aloop=loop=-1:size=2e+09,"
            f"afade=t=out:st={fade_start:.2f}:d={music_fade_out_seconds:.2f}[music];"
            f"[narr][music]amix=inputs=2:duration=first:dropout_transition=2[out]"
        )

        cmd = [
            self.ffmpeg_path,
            "-hide_banner",
            "-loglevel", "error",
            "-y",
            "-i", str(narr_file),
            "-i", str(music_file),
            "-filter_complex", filter_complex,
            "-map", "[out]",
        ]

        if target.suffix.lower() == ".mp3":
            cmd.extend(["-c:a", "libmp3lame", "-b:a", "192k"])
        else:
            cmd.extend(["-c:a", "aac", "-b:a", "192k"])

        cmd.append(str(target))

        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode != 0:
            logger.warning("FFmpeg audio mix failed (%s), falling back to narration only.", res.stderr.strip())
            shutil.copy2(narr_file, target)

        return target
