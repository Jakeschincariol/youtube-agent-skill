from __future__ import annotations

import logging
import os
from pathlib import Path
import shutil
import subprocess
import wave

logger = logging.getLogger(__name__)


def get_wav_duration_seconds(path: str | Path) -> float:
    """Reads duration in seconds from a WAV file using the standard library."""
    p = Path(path).resolve()
    if not p.is_file():
        raise FileNotFoundError(f"Audio file not found: {p}")
    with wave.open(str(p), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        if rate <= 0:
            return 0.0
        return frames / float(rate)


def create_mock_wav(output_path: str | Path, duration_seconds: float, sample_rate: int = 22050) -> float:
    """Generates a valid PCM WAV file for testing or fallback when Piper is not installed."""
    p = Path(output_path).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    num_samples = max(1, int(round(sample_rate * max(0.5, duration_seconds))))
    with wave.open(str(p), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        # Write quiet PCM samples (16-bit)
        wf.writeframes(b"\x00\x00" * num_samples)
    return num_samples / float(sample_rate)


class PiperTTS:
    """Wrapper for local Piper text-to-speech synthesis."""

    def __init__(
        self,
        executable_path: str | None = None,
        model_path: str | None = None,
        config_path: str | None = None,
    ) -> None:
        self.executable = (
            executable_path
            or os.environ.get("PIPER_PATH")
            or shutil.which("piper")
        )
        self.model_path = model_path or os.environ.get("PIPER_MODEL")
        self.config_path = config_path or os.environ.get("PIPER_CONFIG")

    def is_available(self) -> bool:
        """Returns True if the piper binary exists and is executable."""
        if not self.executable:
            return False
        return Path(self.executable).is_file() or shutil.which(self.executable) is not None

    def synthesize(
        self,
        text: str,
        output_path: str | Path,
        *,
        words_per_minute: float = 145.0,
        allow_fallback: bool = True,
    ) -> float:
        """
        Synthesizes speech to a WAV file.
        Returns the duration of the generated audio in seconds.
        """
        target = Path(output_path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)

        if not self.is_available() or not self.model_path or not Path(self.model_path).is_file():
            if allow_fallback:
                # Estimate duration from word count
                words = max(1, len(text.split()))
                est_seconds = (words / words_per_minute) * 60.0
                logger.info(
                    "Piper TTS not available/configured; generating mock audio (%.2fs for %d words)",
                    est_seconds,
                    words,
                )
                return create_mock_wav(target, est_seconds)
            raise RuntimeError("Piper TTS binary or model not configured.")

        # Run Piper CLI: echo text | piper --model ... --output_file ...
        cmd = [
            self.executable,
            "--model",
            self.model_path,
            "--output_file",
            str(target),
        ]
        if self.config_path and Path(self.config_path).is_file():
            cmd.extend(["--config", self.config_path])

        process = subprocess.run(
            cmd,
            input=text.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

        if not target.is_file():
            raise RuntimeError(f"Piper failed to produce output WAV at {target}: {process.stderr.decode('utf-8', errors='replace')}")

        return get_wav_duration_seconds(target)
