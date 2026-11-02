from __future__ import annotations

import logging
from pathlib import Path
import time
from typing import Any, Callable

from PySide6.QtCore import QObject, QThread, Signal

from animatube.audio.cache import AudioCache
from animatube.audio.edge_tts_wrapper import EdgeTTS
from animatube.audio.piper_tts import PiperTTS
from animatube.audio.speech_preparer import NarrationStyle, SpeechPreparer
from animatube.core.models import Project, Scene

logger = logging.getLogger(__name__)


class AudioGenerationWorker(QThread):
    """
    Asynchronous, non-blocking background worker for scene-by-scene audio narration.
    Supports real-time progress signals, smart caching, automatic retries, and cancellation.
    """

    # Signals
    scene_started = Signal(int, str)             # (scene_idx, scene_name)
    scene_completed = Signal(int, str, float)    # (scene_idx, audio_path, duration)
    progress_changed = Signal(int, int)          # (current_scene, total_scenes)
    status_message = Signal(str)                 # Human-readable status update
    generation_finished = Signal(list)           # List of final audio paths
    error_occurred = Signal(str)                 # Error message
    cancelled = Signal()                         # Cancellation notification

    def __init__(
        self,
        scenes: list[Scene],
        output_dir: str | Path,
        *,
        voice: str = "en-IN-PrabhatNeural",
        style: NarrationStyle = NarrationStyle.EDUCATIONAL,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        prefer_edge_tts: bool = True,
        cache_dir: str | Path | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.scenes = scenes
        self.output_dir = Path(output_dir).resolve()
        self.voice = voice
        self.style = style
        self.rate = rate
        self.pitch = pitch
        self.prefer_edge_tts = prefer_edge_tts

        self.cache = AudioCache(cache_dir=cache_dir)
        self.preparer = SpeechPreparer(style=style)
        self._is_cancelled = False

    def cancel(self) -> None:
        """Requests cooperative cancellation of the running worker."""
        self._is_cancelled = True

    def run(self) -> None:
        """Executes scene-by-scene synthesis in background thread."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        total = len(self.scenes)
        audio_results: list[Path] = []

        edge_engine = EdgeTTS(voice=self.voice) if self.prefer_edge_tts and EdgeTTS.is_available() else None
        piper_engine = PiperTTS()

        for idx, scene in enumerate(self.scenes, start=1):
            if self._is_cancelled:
                self.cancelled.emit()
                return

            self.scene_started.emit(idx, scene.name)
            self.progress_changed.emit(idx - 1, total)

            # Extract scene text (from layer texts or scene narration property)
            text = self._extract_scene_narration(scene)
            if not text.strip():
                logger.info("Scene %d '%s' has empty narration, skipping audio.", idx, scene.name)
                continue

            # 1. Normalize pronunciation & sentence pauses
            normalized_text = self.preparer.prepare_plain_text(text)
            engine_name = "edge_tts" if edge_engine else "piper"
            ext = ".mp3" if edge_engine else ".wav"

            # 2. Check Cache First (Zero Lag on unchanged scenes)
            cached = self.cache.get(
                text=normalized_text,
                voice=self.voice,
                style=self.style.value,
                rate=self.rate,
                pitch=self.pitch,
                engine=engine_name,
                extension=ext,
            )

            target_file = self.output_dir / f"scene_{idx:02d}_{engine_name}{ext}"

            if cached is not None:
                cached_path, duration = cached
                self.status_message.emit(f"Scene {idx}/{total}: Loaded from cache (instant)")
                import shutil
                shutil.copy2(cached_path, target_file)
                audio_results.append(target_file)
                self.scene_completed.emit(idx, str(target_file), duration)
                continue

            # 3. Synthesize with Retries
            duration = 0.0
            attempts = 0
            max_attempts = 2
            success = False

            while attempts < max_attempts and not success and not self._is_cancelled:
                attempts += 1
                try:
                    self.status_message.emit(f"Scene {idx}/{total}: Synthesizing voice ({self.voice})...")

                    if edge_engine:
                        duration = edge_engine.synthesize(
                            normalized_text,
                            target_file,
                            voice=self.voice,
                        )
                    else:
                        duration = piper_engine.synthesize(
                            normalized_text,
                            target_file,
                            allow_fallback=True,
                        )

                    if target_file.is_file() and target_file.stat().st_size > 0:
                        success = True
                except Exception as exc:
                    logger.warning("Synthesis attempt %d failed for scene %d: %s", attempts, idx, exc)
                    if attempts < max_attempts:
                        time.sleep(0.5)

            if self._is_cancelled:
                self.cancelled.emit()
                return

            if not success:
                self.error_occurred.emit(f"Failed to generate audio for scene {idx} ('{scene.name}')")
                return

            # 4. Save to Cache
            self.cache.put(
                text=normalized_text,
                source_audio_path=target_file,
                duration=duration,
                voice=self.voice,
                style=self.style.value,
                rate=self.rate,
                pitch=self.pitch,
                engine=engine_name,
            )

            audio_results.append(target_file)
            self.scene_completed.emit(idx, str(target_file), duration)

        if self._is_cancelled:
            self.cancelled.emit()
            return

        self.progress_changed.emit(total, total)
        self.status_message.emit("All scene narration generated successfully!")
        self.generation_finished.emit([str(p) for p in audio_results])

    def _extract_scene_narration(self, scene: Scene) -> str:
        """Extracts text content to be spoken from a scene."""
        # If scene has a custom narration attribute, use it
        if hasattr(scene, "narration") and scene.narration:
            return str(scene.narration)

        # Otherwise collect text from text layers
        text_chunks: list[str] = []
        for l in scene.layers:
            if l.kind == "text" and l.text and not l.name.startswith("Anim_"):
                text_chunks.append(l.text)

        if text_chunks:
            return " ".join(text_chunks)
        return scene.name
