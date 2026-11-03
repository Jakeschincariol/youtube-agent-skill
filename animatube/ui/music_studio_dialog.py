from __future__ import annotations

import logging
from pathlib import Path
import shutil
from typing import Any, Callable
import wave

from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSlider,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

try:
    from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
except ImportError:
    QMediaPlayer = None
    QAudioOutput = None

from animatube.ai.models import AIGenerationJob, JobStatus, MusicPrompt
from animatube.ai.music_worker import MusicGenerationWorker
from animatube.ai.registry import AIProviderRegistry
from animatube.core.models import Project

logger = logging.getLogger(__name__)


class MusicStudioDialog(QDialog):
    """
    AI Music & Sound Effects Studio Dialog.
    Generates original theme songs, background music (BGM), and sound effects (SFX)
    with mood/genre/tempo presets, licensing metadata, playback, and timeline BGM integration.
    """

    def __init__(
        self,
        project: Project,
        parent: QWidget | None = None,
        project_file: str = "",
        on_bgm_selected: Callable[[str], None] | None = None,
        on_sfx_selected: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.project = project
        self.project_file = project_file
        self.on_bgm_selected = on_bgm_selected
        self.on_sfx_selected = on_sfx_selected

        self.setWindowTitle("AnimaVideo — AI Music & Sound Effects Studio")
        self.resize(1060, 720)

        self.registry = AIProviderRegistry.get_instance()
        self.active_worker: MusicGenerationWorker | None = None
        self.current_job: AIGenerationJob | None = None
        self.job_history: list[AIGenerationJob] = []

        # Audio player setup
        self.player = None
        self.audio_output = None
        if QMediaPlayer is not None and QAudioOutput is not None:
            try:
                self.player = QMediaPlayer(self)
                # QMediaPlayer uses its audio output for playback. Parent the
                # output to the player so Qt destroys the dependent object
                # before the player and its multimedia backend are torn down.
                self.audio_output = QAudioOutput(self.player)
                self.player.setAudioOutput(self.audio_output)
            except Exception as exc:
                logger.warning("Could not initialize QMediaPlayer: %s", exc)

        self._build_ui()
        self._load_providers()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        # Header
        header_box = QHBoxLayout()
        header_title = QLabel("AI Music & Sound Effects Studio")
        header_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #a78bfa;")
        header_box.addWidget(header_title)

        header_box.addStretch(1)
        header_box.addWidget(QLabel("Provider:"))
        self.provider_combo = QComboBox()
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        header_box.addWidget(self.provider_combo)
        root.addLayout(header_box)

        # Main splitter (Left: Prompting & Controls, Right: Player & History)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # LEFT PANEL: Music Generation Controls
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # Track type selector
        type_group = QGroupBox("Track Category")
        type_layout = QHBoxLayout(type_group)
        self.radio_bgm = QRadioButton("Background Music (BGM)")
        self.radio_song = QRadioButton("Original Theme Song")
        self.radio_sfx = QRadioButton("Sound Effect (SFX)")
        self.radio_bgm.setChecked(True)
        self.radio_bgm.toggled.connect(self._on_type_changed)
        self.radio_song.toggled.connect(self._on_type_changed)
        self.radio_sfx.toggled.connect(self._on_type_changed)
        type_layout.addWidget(self.radio_bgm)
        type_layout.addWidget(self.radio_song)
        type_layout.addWidget(self.radio_sfx)
        left_layout.addWidget(type_group)

        # Prompt input
        prompt_group = QGroupBox("Music Prompt & Style Description")
        prompt_layout = QVBoxLayout(prompt_group)
        self.edit_prompt = QTextEdit()
        self.edit_prompt.setPlaceholderText(
            "Describe the musical mood, instruments, rhythm, and setting...\n"
            "e.g. 'Gentle acoustic guitar with soft glockenspiel chimes and warm strings, cheerful and comforting preschool melody.'"
        )
        self.edit_prompt.setFixedHeight(80)
        prompt_layout.addWidget(self.edit_prompt)
        left_layout.addWidget(prompt_group)

        # Musical Attributes
        attr_group = QGroupBox("Arrangement Settings")
        attr_layout = QFormLayout(attr_group)

        self.combo_genre = QComboBox()
        self.combo_genre.addItems([
            "Preschool Orchestral",
            "Playful Acoustic",
            "Gentle Lullaby",
            "Upbeat Cartoon",
            "Curious & Exploring",
            "Cinematic Adventure",
            "Ambient Wonder",
            "Cartoon SFX",
        ])
        attr_layout.addRow("Genre / Arrangement:", self.combo_genre)

        self.combo_mood = QComboBox()
        self.combo_mood.addItems([
            "Cheerful",
            "Playful",
            "Curious",
            "Calm",
            "Adventurous",
            "Lullaby",
            "Dramatic",
        ])
        attr_layout.addRow("Emotional Mood:", self.combo_mood)

        self.combo_tempo = QComboBox()
        self.combo_tempo.addItems(["Slow (75 BPM)", "Medium (105 BPM)", "Upbeat (130 BPM)"])
        self.combo_tempo.setCurrentIndex(1)
        attr_layout.addRow("Tempo:", self.combo_tempo)

        # Duration
        dur_box = QHBoxLayout()
        self.spin_duration = QDoubleSpinBox()
        self.spin_duration.setRange(1.0, 180.0)
        self.spin_duration.setValue(30.0)
        self.spin_duration.setSuffix(" sec")
        dur_box.addWidget(self.spin_duration)

        self.check_instrumental = QCheckBox("Instrumental Only (No Vocals)")
        self.check_instrumental.setChecked(True)
        dur_box.addWidget(self.check_instrumental)
        attr_layout.addRow("Duration & Vocals:", dur_box)

        left_layout.addWidget(attr_group)

        # Licensing & Monetization Box
        license_group = QGroupBox("Commercial & YouTube Licensing")
        lic_layout = QVBoxLayout(license_group)
        self.label_license = QLabel(
            "✓ 100% Royalty-Free & Original Composition\n"
            "✓ Cleared for YouTube Monetization & Faceless Channels\n"
            "✓ Safe from Content ID and Copyright Strikes"
        )
        self.label_license.setStyleSheet(
            "color: #10b981; font-weight: bold; background: #064e3b; padding: 8px; border-radius: 4px;"
        )
        lic_layout.addWidget(self.label_license)
        left_layout.addWidget(license_group)

        # Generation Progress & Action Buttons
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)

        self.label_status = QLabel("Ready to compose music.")
        self.label_status.setStyleSheet("color: #94a3b8;")
        left_layout.addWidget(self.label_status)

        action_box = QHBoxLayout()
        self.btn_generate = QPushButton("Compose Music")
        self.btn_generate.setStyleSheet("background-color: #7c3aed; font-weight: bold; padding: 8px;")
        self.btn_generate.clicked.connect(self._on_generate_clicked)
        action_box.addWidget(self.btn_generate)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._on_cancel_clicked)
        action_box.addWidget(self.btn_cancel)
        left_layout.addLayout(action_box)

        splitter.addWidget(left_widget)

        # RIGHT PANEL: Preview Player & Generated Tracks
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Audio Player Preview
        player_group = QGroupBox("Audio Player Preview")
        player_layout = QVBoxLayout(player_group)

        self.label_track_name = QLabel("No track selected.")
        self.label_track_name.setStyleSheet("font-weight: bold; color: #f8fafc;")
        player_layout.addWidget(self.label_track_name)

        self.label_audio_info = QLabel("Duration: 0.0s | Format: WAV | Channels: Stereo")
        self.label_audio_info.setStyleSheet("color: #94a3b8; font-size: 11px;")
        player_layout.addWidget(self.label_audio_info)

        # Playback controls
        play_ctrl_box = QHBoxLayout()
        self.btn_play = QPushButton("▶ Play")
        self.btn_play.setEnabled(False)
        self.btn_play.clicked.connect(self._on_play_clicked)
        play_ctrl_box.addWidget(self.btn_play)

        self.btn_stop = QPushButton("⏹ Stop")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._on_stop_clicked)
        play_ctrl_box.addWidget(self.btn_stop)

        play_ctrl_box.addStretch(1)
        player_layout.addLayout(play_ctrl_box)

        # Timeline integration actions
        timeline_box = QHBoxLayout()
        self.btn_set_bgm = QPushButton("🎵 Set as Project BGM")
        self.btn_set_bgm.setEnabled(False)
        self.btn_set_bgm.setToolTip("Set as project-wide background music track")
        self.btn_set_bgm.clicked.connect(self._on_set_bgm_clicked)
        timeline_box.addWidget(self.btn_set_bgm)

        self.btn_save_wav = QPushButton("💾 Export WAV...")
        self.btn_save_wav.setEnabled(False)
        self.btn_save_wav.clicked.connect(self._on_save_wav_clicked)
        timeline_box.addWidget(self.btn_save_wav)

        player_layout.addLayout(timeline_box)
        right_layout.addWidget(player_group)

        # Track History Table
        history_group = QGroupBox("Generated Tracks Library")
        hist_layout = QVBoxLayout(history_group)

        self.history_table = QTableWidget(0, 4)
        self.history_table.setHorizontalHeaderLabels(["ID", "Category", "Mood / Genre", "Duration"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_table.itemSelectionChanged.connect(self._on_history_row_selected)
        hist_layout.addWidget(self.history_table)

        right_layout.addWidget(history_group)

        splitter.addWidget(right_widget)
        splitter.setSizes([480, 580])
        root.addWidget(splitter)

        # Bottom Close button
        bottom_box = QHBoxLayout()
        bottom_box.addStretch(1)
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        bottom_box.addWidget(btn_close)
        root.addLayout(bottom_box)

    def _load_providers(self) -> None:
        self.provider_combo.clear()
        providers = [p for p in self.registry.list_providers() if p["media_type"] == "music"]
        for p in providers:
            self.provider_combo.addItem(p["provider_name"], p["provider_id"])
        if not providers:
            self.provider_combo.addItem("No Music Provider Available", "")
            self.btn_generate.setEnabled(False)

    def _on_provider_changed(self) -> None:
        pid = self.provider_combo.currentData()
        if not pid:
            return
        prov = self.registry.get_music_provider(pid)
        if prov:
            caps = prov.capabilities
            self.spin_duration.setMaximum(caps.max_duration_seconds)
            self.spin_duration.setMinimum(caps.min_duration_seconds)

    def _on_type_changed(self) -> None:
        if self.radio_sfx.isChecked():
            self.spin_duration.setValue(min(5.0, self.spin_duration.value()))
            self.check_instrumental.setChecked(True)
            self.check_instrumental.setEnabled(False)
            self.combo_genre.setCurrentText("Cartoon SFX")
            self.edit_prompt.setPlaceholderText(
                "Describe the sound effect... e.g. 'Magical sparkle chime', 'Playful giggle pop', 'Whoosh slide'"
            )
            self.btn_generate.setText("Generate SFX")
        elif self.radio_song.isChecked():
            self.spin_duration.setValue(max(45.0, self.spin_duration.value()))
            self.check_instrumental.setChecked(False)
            self.check_instrumental.setEnabled(True)
            self.combo_genre.setCurrentText("Preschool Orchestral")
            self.edit_prompt.setPlaceholderText(
                "Describe theme song lyrics or rhythm... e.g. 'Upbeat preschool counting song with cute vocals'"
            )
            self.btn_generate.setText("Compose Theme Song")
        else:
            self.spin_duration.setValue(30.0)
            self.check_instrumental.setChecked(True)
            self.check_instrumental.setEnabled(True)
            self.combo_genre.setCurrentText("Preschool Orchestral")
            self.edit_prompt.setPlaceholderText(
                "Describe background music mood... e.g. 'Gentle acoustic preschool melody with warm strings'"
            )
            self.btn_generate.setText("Compose Music")

    def _get_output_dir(self) -> Path:
        if self.project_file and Path(self.project_file).is_file():
            base_dir = Path(self.project_file).parent / "ai_music"
        else:
            base_dir = Path.home() / ".animatube" / "ai_music"
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir

    def _on_generate_clicked(self) -> None:
        pid = self.provider_combo.currentData()
        prov = self.registry.get_music_provider(pid) if pid else None
        if not prov:
            QMessageBox.critical(self, "Provider Error", "No valid music provider selected.")
            return

        prompt_text = self.edit_prompt.toPlainText().strip()
        mood = self.combo_mood.currentText()
        genre = self.combo_genre.currentText()
        duration = float(self.spin_duration.value())
        is_instrumental = self.check_instrumental.isChecked()
        is_sfx = self.radio_sfx.isChecked()
        tempo = self.combo_tempo.currentText().split()[0].lower()

        if not prompt_text:
            prompt_text = f"{mood} {genre} {'sound effect' if is_sfx else 'music'}"

        prompt = MusicPrompt(
            prompt=prompt_text,
            mood=mood.lower(),
            genre=genre.lower().replace(" ", "_"),
            duration_seconds=duration,
            is_instrumental=is_instrumental,
            tempo=tempo,
            sound_effect=is_sfx,
        )

        try:
            prov.validate_input(prompt)
        except Exception as exc:
            QMessageBox.warning(self, "Invalid Parameters", str(exc))
            return

        self.btn_generate.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(5)
        self.label_status.setText("Starting music synthesis...")

        self.active_worker = MusicGenerationWorker(prov, prompt, self._get_output_dir(), parent=self)
        self.active_worker.progress_changed.connect(self._on_worker_progress)
        self.active_worker.generation_finished.connect(self._on_worker_finished)
        self.active_worker.error_occurred.connect(self._on_worker_error)
        self.active_worker.cancelled.connect(self._on_worker_cancelled)
        self.active_worker.start()

    def _on_worker_progress(self, progress: float, message: str) -> None:
        self.progress_bar.setValue(int(progress * 100))
        self.label_status.setText(message)

    def _on_worker_finished(self, job: AIGenerationJob) -> None:
        self.btn_generate.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.progress_bar.setValue(100)
        self.label_status.setText("Music generation completed successfully!")
        self.current_job = job
        self.job_history.append(job)
        self._add_job_to_history_table(job)
        self._load_job_preview(job)

    def _on_worker_error(self, error: str) -> None:
        self.btn_generate.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.label_status.setText("Music generation failed.")
        QMessageBox.critical(self, "Music Generation Failed", error)

    def _on_worker_cancelled(self) -> None:
        self.btn_generate.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.label_status.setText("Music generation cancelled.")

    def _on_cancel_clicked(self) -> None:
        if self.active_worker:
            self.active_worker.cancel()
            self.label_status.setText("Cancelling generation...")

    def _add_job_to_history_table(self, job: AIGenerationJob) -> None:
        row = self.history_table.rowCount()
        self.history_table.insertRow(row)

        short_id = job.job_id[:8]
        meta = job.metadata or {}
        cat = "SFX" if meta.get("sound_effect") else ("Song" if not meta.get("is_instrumental", True) else "BGM")
        style = f"{meta.get('mood', 'cheerful').title()} / {meta.get('genre', 'orchestral').title()}"
        dur = f"{meta.get('duration', 0.0):.1f}s"

        self.history_table.setItem(row, 0, QTableWidgetItem(short_id))
        self.history_table.setItem(row, 1, QTableWidgetItem(cat))
        self.history_table.setItem(row, 2, QTableWidgetItem(style))
        self.history_table.setItem(row, 3, QTableWidgetItem(dur))
        self.history_table.selectRow(row)

    def _on_history_row_selected(self) -> None:
        selected_rows = self.history_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        if 0 <= row < len(self.job_history):
            self._load_job_preview(self.job_history[row])

    def _load_job_preview(self, job: AIGenerationJob) -> None:
        self.current_job = job
        if not job.result_path or not Path(job.result_path).is_file():
            return

        res = Path(job.result_path)
        self.label_track_name.setText(f"Track: {res.name}")

        # Probe wave info
        dur = 0.0
        channels = 1
        rate = 44100
        try:
            with wave.open(str(res), "rb") as wf:
                channels = wf.getnchannels()
                rate = wf.getframerate()
                frames = wf.getnframes()
                dur = round(frames / float(rate), 2)
        except Exception:
            dur = job.usage.duration_generated or 0.0

        size_kb = round(res.stat().st_size / 1024, 1)
        self.label_audio_info.setText(
            f"Duration: {dur:.1f}s | Channels: {'Stereo' if channels >= 2 else 'Mono'} | Rate: {rate} Hz | Size: {size_kb} KB"
        )

        self.btn_play.setEnabled(True)
        self.btn_stop.setEnabled(True)
        self.btn_set_bgm.setEnabled(True)
        self.btn_save_wav.setEnabled(True)

    def _on_play_clicked(self) -> None:
        if not self.current_job or not self.current_job.result_path:
            return
        audio_path = str(Path(self.current_job.result_path).resolve())
        if self.player:
            try:
                self.player.setSource(QUrl.fromLocalFile(audio_path))
                self.player.play()
                self.label_status.setText("Playing audio preview...")
            except Exception as exc:
                logger.warning("Error during playback: %s", exc)
                self.label_status.setText("Playback started.")
        else:
            self.label_status.setText("Playback preview ready (No audio device connected).")

    def _on_stop_clicked(self) -> None:
        if self.player:
            try:
                self.player.stop()
            except Exception:
                pass
        self.label_status.setText("Playback stopped.")

    def _on_set_bgm_clicked(self) -> None:
        if not self.current_job or not self.current_job.result_path:
            return
        audio_path = str(Path(self.current_job.result_path).resolve())
        if self.on_bgm_selected:
            self.on_bgm_selected(audio_path)
            QMessageBox.information(
                self,
                "BGM Assigned",
                f"Selected audio has been assigned as project background music:\n{Path(audio_path).name}",
            )
        else:
            QMessageBox.information(
                self,
                "BGM Ready",
                f"Audio track ready for timeline BGM mixing:\n{audio_path}",
            )

    def _on_save_wav_clicked(self) -> None:
        if not self.current_job or not self.current_job.result_path:
            return
        src = Path(self.current_job.result_path)
        dest, _ = QFileDialog.getSaveFileName(
            self,
            "Save Audio Track As",
            str(src.name),
            "Wave Audio (*.wav);;All Files (*.*)",
        )
        if dest:
            shutil.copy2(src, dest)
            QMessageBox.information(self, "Export Saved", f"Audio track saved to:\n{dest}")

    def closeEvent(self, event) -> None:
        if self.active_worker and self.active_worker.isRunning():
            self.active_worker.cancel()
            self.active_worker.wait(1000)

        if self.player:
            try:
                self.player.stop()
                # Detach the output explicitly before either QObject is
                # destroyed. This avoids leaving Qt Multimedia with a
                # dangling audio-sink reference during application shutdown.
                self.player.setAudioOutput(None)
            except Exception:
                logger.exception("Could not release the music preview player cleanly")

        super().closeEvent(event)
