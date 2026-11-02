from __future__ import annotations

import logging
from pathlib import Path
import time
from typing import Any

from PySide6.QtCore import QObject, QThread, Signal

from animatube.ai.interfaces import MusicGenerationProvider
from animatube.ai.models import AIGenerationJob, JobStatus, MusicPrompt

logger = logging.getLogger(__name__)


class MusicGenerationWorker(QThread):
    """
    Asynchronous QThread worker for running AI music and sound effect generation jobs.
    Reports progress, handles cancellations, and emits the finished job without freezing the Qt UI.
    """

    progress_changed = Signal(float, str)    # (progress 0.0-1.0, status message)
    generation_finished = Signal(object)     # AIGenerationJob
    error_occurred = Signal(str)             # error message
    cancelled = Signal()

    def __init__(
        self,
        provider: MusicGenerationProvider,
        prompt: MusicPrompt,
        output_dir: str | Path,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.provider = provider
        self.prompt = prompt
        self.output_dir = Path(output_dir).resolve()
        self._is_cancelled = False
        self._current_job: AIGenerationJob | None = None

    def cancel(self) -> None:
        self._is_cancelled = True
        if self._current_job and self.provider:
            try:
                self.provider.cancel_job(self._current_job.job_id)
            except Exception as exc:
                logger.warning("Error cancelling provider music job: %s", exc)

    def run(self) -> None:
        try:
            self.progress_changed.emit(0.05, "Validating music parameters...")
            self.provider.validate_input(self.prompt)

            if self._is_cancelled:
                self.cancelled.emit()
                return

            self.progress_changed.emit(0.15, "Synthesizing musical arrangement...")
            job = self.provider.submit_job(self.prompt, self.output_dir)
            self._current_job = job

            # Polling loop for asynchronous or simulated providers
            poll_count = 0
            while not job.is_finished():
                if self._is_cancelled:
                    job.cancel()
                    self.cancelled.emit()
                    return

                time.sleep(0.08)
                poll_count += 1
                job = self.provider.get_job_status(job.job_id)
                self._current_job = job

                simulated_progress = min(0.95, 0.2 + (poll_count * 0.1))
                effective_progress = max(job.progress, simulated_progress)
                self.progress_changed.emit(
                    effective_progress,
                    f"Composing audio tracks ({int(effective_progress * 100)}%)...",
                )

            if self._is_cancelled:
                self.cancelled.emit()
                return

            if job.status == JobStatus.COMPLETED:
                self.progress_changed.emit(1.0, "Music generation complete.")
                self.generation_finished.emit(job)
            elif job.status == JobStatus.CANCELLED:
                self.cancelled.emit()
            else:
                err = job.error_message or "Music generation failed."
                self.error_occurred.emit(err)

        except Exception as exc:
            logger.exception("Music generation worker encountered exception: %s", exc)
            self.error_occurred.emit(str(exc))
