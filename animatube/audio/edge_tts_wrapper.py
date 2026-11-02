from __future__ import annotations

import logging
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

logger = logging.getLogger(__name__)


def parse_vtt_last_timestamp(vtt_text: str) -> float:
    """Extracts the latest end-time timestamp from a VTT/SRT text in seconds."""
    matches = re.findall(r"-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})", vtt_text)
    if not matches:
        return 0.0
    h, m, s, ms = matches[-1]
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


class EdgeTTS:
    """Wrapper for Microsoft Edge Neural Text-to-Speech synthesis via CLI runner."""

    DEFAULT_VOICE = "en-IN-PrabhatNeural"   # Natural Indian English (Male)
    FEMALE_VOICE = "en-IN-NeerjaNeural"     # Natural Indian English (Female)
    US_VOICE = "en-US-GuyNeural"            # Natural US English (Male)

    def __init__(self, voice: str = DEFAULT_VOICE) -> None:
        self.voice = voice

    @classmethod
    def is_available(cls) -> bool:
        """Returns True if the edge_tts module can be called."""
        try:
            res = subprocess.run(
                [sys.executable, "-m", "edge_tts", "--version"],
                capture_output=True,
                check=False,
            )
            return res.returncode == 0
        except Exception:
            return False

    def synthesize(
        self,
        text: str,
        output_path: str | Path,
        *,
        output_subtitles_path: str | Path | None = None,
        voice: str | None = None,
    ) -> float:
        """
        Synthesizes text to an MP3 file using Edge TTS.
        Optionally outputs timed subtitles (.vtt or .srt).
        Returns the duration of the audio in seconds.
        """
        target = Path(output_path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        chosen_voice = voice or self.voice

        temp_vtt = target.with_suffix(".temp.vtt")

        cmd = [
            sys.executable,
            "-m",
            "edge_tts",
            "--text",
            text,
            "-v",
            chosen_voice,
            "--write-media",
            str(target),
            "--write-subtitles",
            str(temp_vtt),
        ]

        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"Edge TTS synthesis failed: {proc.stderr}")

        duration = 0.0
        if temp_vtt.is_file():
            vtt_content = temp_vtt.read_text(encoding="utf-8")
            duration = parse_vtt_last_timestamp(vtt_content)

            if output_subtitles_path:
                sub_target = Path(output_subtitles_path).resolve()
                sub_target.parent.mkdir(parents=True, exist_ok=True)
                # Save as subtitle
                sub_target.write_text(vtt_content, encoding="utf-8")

            try:
                temp_vtt.unlink()
            except OSError:
                pass

        if duration <= 0.0:
            # Fallback duration estimate from word count at 145 wpm
            words = max(1, len(text.split()))
            duration = (words / 145.0) * 60.0

        return duration
