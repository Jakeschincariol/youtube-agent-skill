from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import logging
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any

logger = logging.getLogger(__name__)


class AudioCache:
    """
    Persistent SHA-256 content-addressable cache for synthesized narration.
    Guarantees that scenes with unchanged narration and voice settings are never re-synthesized.
    """

    def __init__(self, cache_dir: str | Path | None = None) -> None:
        if cache_dir:
            self.cache_dir = Path(cache_dir).expanduser().resolve()
        else:
            self.cache_dir = Path.home() / "AnimaTube" / "Cache" / "Audio"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def compute_key(
        self,
        text: str,
        voice: str = "",
        style: str = "educational",
        rate: str = "+0%",
        pitch: str = "+0Hz",
        engine: str = "edge_tts",
    ) -> str:
        """Computes a deterministic SHA-256 fingerprint from speech synthesis parameters."""
        payload = f"{engine}|{voice}|{style}|{rate}|{pitch}|{text.strip()}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def get(
        self,
        text: str,
        voice: str = "",
        style: str = "educational",
        rate: str = "+0%",
        pitch: str = "+0Hz",
        engine: str = "edge_tts",
        extension: str = ".mp3",
    ) -> tuple[Path, float] | None:
        """
        Looks up cached narration audio.
        Returns (audio_path, duration_seconds) if found and non-empty, else None.
        """
        key = self.compute_key(text, voice, style, rate, pitch, engine)
        ext = extension if extension.startswith(".") else f".{extension}"
        audio_file = self.cache_dir / f"{key}{ext}"
        meta_file = self.cache_dir / f"{key}.json"

        if audio_file.is_file() and audio_file.stat().st_size > 0:
            duration = 0.0
            if meta_file.is_file():
                try:
                    data = json.loads(meta_file.read_text(encoding="utf-8"))
                    duration = float(data.get("duration", 0.0))
                except (OSError, ValueError):
                    pass
            return audio_file, duration
        return None

    def put(
        self,
        text: str,
        source_audio_path: str | Path,
        duration: float,
        voice: str = "",
        style: str = "educational",
        rate: str = "+0%",
        pitch: str = "+0Hz",
        engine: str = "edge_tts",
    ) -> Path:
        """Stores a newly synthesized audio file and metadata in cache."""
        source = Path(source_audio_path).resolve()
        if not source.is_file() or source.stat().st_size == 0:
            raise FileNotFoundError(f"Source audio file not found or empty: {source}")

        key = self.compute_key(text, voice, style, rate, pitch, engine)
        ext = source.suffix.lower() or ".mp3"
        target_audio = self.cache_dir / f"{key}{ext}"
        target_meta = self.cache_dir / f"{key}.json"

        # Copy audio file
        shutil.copy2(source, target_audio)

        # Write metadata atomically
        meta = {
            "key": key,
            "engine": engine,
            "voice": voice,
            "style": style,
            "rate": rate,
            "pitch": pitch,
            "duration": float(duration),
            "size_bytes": target_audio.stat().st_size,
            "text": text[:200],
        }
        temp_meta = target_meta.with_suffix(".tmp")
        temp_meta.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        os.replace(temp_meta, target_meta)

        return target_audio

    def total_size_bytes(self) -> int:
        """Calculates total disk usage of cached audio assets."""
        total = 0
        for f in self.cache_dir.glob("*"):
            if f.is_file():
                try:
                    total += f.stat().st_size
                except OSError:
                    pass
        return total

    def clear(self) -> None:
        """Clears all cached audio entries."""
        for f in self.cache_dir.glob("*"):
            if f.is_file():
                try:
                    f.unlink()
                except OSError:
                    pass
