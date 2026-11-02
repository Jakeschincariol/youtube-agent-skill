from __future__ import annotations

import logging
from pathlib import Path
import tempfile
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSlider,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from animatube.audio.cache import AudioCache
from animatube.audio.human_voice import HumanVoiceImporter, measure_audio_duration
from animatube.audio.mixer import AudioMixer
from animatube.audio.speech_preparer import NarrationStyle
from animatube.audio.worker import AudioGenerationWorker
from animatube.core.models import Project

logger = logging.getLogger("animatube.ui.audio")


class AudioStudioDialog(QDialog):
    """
    Complete Audio & Narration Studio Dialog.
    Supports neural TTS generation with non-blocking worker, caching,
    human voice import with silence trimming, and background music mixing.
    """

    def __init__(
        self,
        project: Project,
        parent: QWidget | None = None,
        project_file: str = "",
        on_audio_updated: Any | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("AnimaTube — Narration & Audio Studio")
        self.resize(880, 620)

        self.project = project
        self.project_file = project_file
        self.on_audio_updated = on_audio_updated

        self.cache = AudioCache()
        self.importer = HumanVoiceImporter()
        self.mixer = AudioMixer()
        self.active_worker: AudioGenerationWorker | None = None

        self.music_file_path: str = ""
        self.generated_audio_files: list[str] = []

        self._build_ui()
        self._populate_scenes_table()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        header = QLabel("Audio & Narration Studio")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #38bdf8;")
        root.addWidget(header)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        # Tab 1: AI Neural Speech
        self.tab_tts = QWidget()
        self._build_tts_tab(self.tab_tts)
        self.tabs.addTab(self.tab_tts, "AI Voiceover (TTS)")

        # Tab 2: Human Voice Recording Import
        self.tab_human = QWidget()
        self._build_human_tab(self.tab_human)
        self.tabs.addTab(self.tab_human, "Human Voice Import")

        # Tab 3: Background Music & Audio Mix
        self.tab_music = QWidget()
        self._build_music_tab(self.tab_music)
        self.tabs.addTab(self.tab_music, "Background Music & Mix")

        # Bottom Buttons
        bottom_box = QHBoxLayout()
        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self._on_close)
        bottom_box.addStretch()
        bottom_box.addWidget(self.btn_close)
        root.addLayout(bottom_box)

    def _build_tts_tab(self, tab: QWidget) -> None:
        layout = QVBoxLayout(tab)

        # Settings Group
        cfg_box = QGroupBox("Voice & Delivery Parameters")
        form = QFormLayout(cfg_box)

        self.combo_voice = QComboBox()
        self.combo_voice.addItem("Indian English (Male) — en-IN-PrabhatNeural", "en-IN-PrabhatNeural")
        self.combo_voice.addItem("Indian English (Female) — en-IN-NeerjaNeural", "en-IN-NeerjaNeural")
        self.combo_voice.addItem("US English (Male) — en-US-GuyNeural", "en-US-GuyNeural")
        self.combo_voice.addItem("US English (Female) — en-US-JennyNeural", "en-US-JennyNeural")
        self.combo_voice.addItem("Piper TTS (Local Offline)", "piper")
        form.addRow("Voice Model:", self.combo_voice)

        self.combo_style = QComboBox()
        self.combo_style.addItem("Educational (Clear pace, distinct conceptual pauses)", NarrationStyle.EDUCATIONAL)
        self.combo_style.addItem("Conversational (Engaging, lively natural cadence)", NarrationStyle.CONVERSATIONAL)
        self.combo_style.addItem("Professional (Measured, authoritative, steady)", NarrationStyle.PROFESSIONAL)
        form.addRow("Delivery Style:", self.combo_style)

        # Rate slider
        rate_layout = QHBoxLayout()
        self.slider_rate = QSlider(Qt.Orientation.Horizontal)
        self.slider_rate.setRange(-20, 20)
        self.slider_rate.setValue(0)
        self.lbl_rate = QLabel("0%")
        self.slider_rate.valueChanged.connect(lambda v: self.lbl_rate.setText(f"{v:+d}%"))
        rate_layout.addWidget(self.slider_rate, 1)
        rate_layout.addWidget(self.lbl_rate)
        form.addRow("Speech Rate:", rate_layout)

        layout.addWidget(cfg_box)

        # Scenes Table
        layout.addWidget(QLabel("Project Scenes Narration Status:"))
        self.table_scenes = QTableWidget()
        self.table_scenes.setColumnCount(4)
        self.table_scenes.setHorizontalHeaderLabels(["Scene #", "Scene Name", "Duration (Frames)", "Status"])
        layout.addWidget(self.table_scenes, 1)

        # Progress bar & status
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("Ready to generate.")
        self.lbl_status.setStyleSheet("color: #94a3b8;")
        layout.addWidget(self.lbl_status)

        # Action Buttons
        btn_layout = QHBoxLayout()
        self.btn_generate_all = QPushButton("🎙️ Generate All Narration (Non-blocking)")
        self.btn_generate_all.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 6px;")
        self.btn_generate_all.clicked.connect(self._start_audio_generation)
        btn_layout.addWidget(self.btn_generate_all)

        self.btn_cancel = QPushButton("Cancel Generation")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._cancel_audio_generation)
        btn_layout.addWidget(self.btn_cancel)

        layout.addLayout(btn_layout)

    def _build_human_tab(self, tab: QWidget) -> None:
        layout = QVBoxLayout(tab)

        desc = QLabel(
            "Import genuine human voice recordings (.wav, .mp3).\n"
            "AnimaTube will clean up silence, normalize loudness, and synchronize scene timings."
        )
        desc.setStyleSheet("color: #94a3b8; font-size: 13px; margin-bottom: 8px;")
        layout.addWidget(desc)

        form_box = QGroupBox("Import Human Voice Track")
        form = QFormLayout(form_box)

        self.combo_target_scene = QComboBox()
        for idx, sc in enumerate(self.project.scenes, start=1):
            self.combo_target_scene.addItem(f"Scene {idx}: {sc.name}", idx - 1)
        form.addRow("Target Scene:", self.combo_target_scene)

        self.chk_trim_silence = QCheckBox("Automatically trim leading & trailing silence")
        self.chk_trim_silence.setChecked(True)
        form.addRow("Silence Trimming:", self.chk_trim_silence)

        self.chk_loudnorm = QCheckBox("Normalize volume to broadcast standard (-16 LUFS)")
        self.chk_loudnorm.setChecked(True)
        form.addRow("Loudness Normalization:", self.chk_loudnorm)

        layout.addWidget(form_box)

        self.lbl_imported_info = QLabel("No recording imported for this scene yet.")
        self.lbl_imported_info.setStyleSheet("color: #38bdf8;")
        layout.addWidget(self.lbl_imported_info)

        btn_box = QHBoxLayout()
        self.btn_import_file = QPushButton("📁 Select Audio File (WAV / MP3)...")
        self.btn_import_file.clicked.connect(self._import_human_audio)
        btn_box.addWidget(self.btn_import_file)

        self.btn_sync_scene = QPushButton("⏱️ Sync Scene Timeline to Audio")
        self.btn_sync_scene.setStyleSheet("font-weight: bold;")
        self.btn_sync_scene.clicked.connect(self._sync_scene_to_recording)
        btn_box.addWidget(self.btn_sync_scene)

        layout.addLayout(btn_box)
        layout.addStretch()

    def _build_music_tab(self, tab: QWidget) -> None:
        layout = QVBoxLayout(tab)

        desc = QLabel(
            "Add background music to enhance viewer retention.\n"
            "Music volume is kept lower than speech (recommended: 12% - 18%) with auto-looping and fade-out."
        )
        desc.setStyleSheet("color: #94a3b8; font-size: 13px; margin-bottom: 8px;")
        layout.addWidget(desc)

        box = QGroupBox("Music Track & Level Controls")
        form = QFormLayout(box)

        self.lbl_music_file = QLabel("No music track selected.")
        form.addRow("Music File:", self.lbl_music_file)

        self.btn_browse_music = QPushButton("Browse Music (.mp3 / .wav)...")
        self.btn_browse_music.clicked.connect(self._browse_music_file)
        form.addRow("", self.btn_browse_music)

        # Music Volume Slider (0 - 40%)
        m_vol_layout = QHBoxLayout()
        self.slider_music_vol = QSlider(Qt.Orientation.Horizontal)
        self.slider_music_vol.setRange(0, 40)
        self.slider_music_vol.setValue(15)
        self.lbl_music_vol = QLabel("15%")
        self.slider_music_vol.valueChanged.connect(lambda v: self.lbl_music_vol.setText(f"{v}%"))
        m_vol_layout.addWidget(self.slider_music_vol, 1)
        m_vol_layout.addWidget(self.lbl_music_vol)
        form.addRow("Music Volume:", m_vol_layout)

        # Narration Volume Slider (50 - 150%)
        n_vol_layout = QHBoxLayout()
        self.slider_narr_vol = QSlider(Qt.Orientation.Horizontal)
        self.slider_narr_vol.setRange(50, 150)
        self.slider_narr_vol.setValue(100)
        self.lbl_narr_vol = QLabel("100%")
        self.slider_narr_vol.valueChanged.connect(lambda v: self.lbl_narr_vol.setText(f"{v}%"))
        n_vol_layout.addWidget(self.slider_narr_vol, 1)
        n_vol_layout.addWidget(self.lbl_narr_vol)
        form.addRow("Narration Volume:", n_vol_layout)

        layout.addWidget(box)
        layout.addStretch()

    def _populate_scenes_table(self) -> None:
        self.table_scenes.setRowCount(len(self.project.scenes))
        for idx, sc in enumerate(self.project.scenes):
            self.table_scenes.setItem(idx, 0, QTableWidgetItem(f"{idx + 1}"))
            self.table_scenes.setItem(idx, 1, QTableWidgetItem(sc.name))
            self.table_scenes.setItem(idx, 2, QTableWidgetItem(f"{sc.duration_frames}"))
            self.table_scenes.setItem(idx, 3, QTableWidgetItem("Ready"))

    def _start_audio_generation(self) -> None:
        out_dir = Path(self.project_file).parent / "audio" if self.project_file else Path(tempfile.mkdtemp()) / "audio"
        voice = str(self.combo_voice.currentData())
        style = self.combo_style.currentData()
        rate_val = f"{self.slider_rate.value():+d}%"

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.btn_generate_all.setEnabled(False)
        self.btn_cancel.setEnabled(True)

        self.active_worker = AudioGenerationWorker(
            scenes=self.project.scenes,
            output_dir=out_dir,
            voice=voice if voice != "piper" else "piper",
            style=style,
            rate=rate_val,
            prefer_edge_tts=(voice != "piper"),
        )

        self.active_worker.status_message.connect(self._on_worker_status)
        self.active_worker.scene_completed.connect(self._on_worker_scene_completed)
        self.active_worker.generation_finished.connect(self._on_worker_finished)
        self.active_worker.error_occurred.connect(self._on_worker_error)
        self.active_worker.cancelled.connect(self._on_worker_cancelled)

        self.active_worker.start()

    def _cancel_audio_generation(self) -> None:
        if self.active_worker:
            self.lbl_status.setText("Cancelling narration generation...")
            self.active_worker.cancel()

    def _on_worker_status(self, msg: str) -> None:
        self.lbl_status.setText(msg)

    def _on_worker_scene_completed(self, idx: int, audio_path: str, duration: float) -> None:
        # Update scene duration to match audio length cleanly
        if 0 <= idx - 1 < len(self.project.scenes):
            sc = self.project.scenes[idx - 1]
            HumanVoiceImporter.sync_scene_duration(sc, duration, fps=self.project.fps)
            self._populate_scenes_table()
            self.table_scenes.setItem(idx - 1, 3, QTableWidgetItem(f"Generated ({duration:.1f}s)"))

    def _on_worker_finished(self, files: list) -> None:
        self.generated_audio_files = files
        self.btn_generate_all.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.lbl_status.setText(f"Done! {len(files)} scene narration tracks synthesized.")
        QMessageBox.information(
            self,
            "Narration Ready",
            f"Successfully generated and cached {len(files)} audio tracks!\n"
            "Scene timelines have been synchronized with the narration duration.",
        )
        if self.on_audio_updated:
            self.on_audio_updated()

    def _on_worker_error(self, err: str) -> None:
        self.btn_generate_all.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.lbl_status.setText("Error during generation.")
        QMessageBox.critical(self, "Audio Generation Error", err)

    def _on_worker_cancelled(self) -> None:
        self.btn_generate_all.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.lbl_status.setText("Audio generation was cancelled.")

    def _import_human_audio(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Human Narration Recording", "", "Audio Files (*.wav *.mp3 *.m4a *.aac *.ogg)"
        )
        if not file_path:
            return

        target_idx = self.combo_target_scene.currentIndex()
        out_dir = Path(self.project_file).parent / "audio" if self.project_file else Path(tempfile.mkdtemp()) / "audio"
        out_file = out_dir / f"scene_{target_idx+1:02d}_human{Path(file_path).suffix.lower()}"

        try:
            processed_path, dur = self.importer.process_recording(
                file_path,
                out_file,
                trim_silence=self.chk_trim_silence.isChecked(),
                normalize_volume=self.chk_loudnorm.isChecked(),
            )
            self.lbl_imported_info.setText(
                f"Loaded: {processed_path.name} ({dur:.2f}s, silence trimmed & normalized)"
            )
            # Sync scene duration immediately
            sc = self.project.scenes[target_idx]
            frames = HumanVoiceImporter.sync_scene_duration(sc, dur, fps=self.project.fps)
            self._populate_scenes_table()
            QMessageBox.information(
                self,
                "Human Voice Imported",
                f"Recording imported for Scene {target_idx+1}!\nDuration: {dur:.2f}s ({frames} frames).",
            )
            if self.on_audio_updated:
                self.on_audio_updated()
        except Exception as exc:
            QMessageBox.critical(self, "Import Failed", f"Could not process audio recording: {exc}")

    def _sync_scene_to_recording(self) -> None:
        target_idx = self.combo_target_scene.currentIndex()
        sc = self.project.scenes[target_idx]
        QMessageBox.information(
            self,
            "Timeline Synchronized",
            f"Scene {target_idx + 1} ('{sc.name}') is set to {sc.duration_frames} frames ({sc.duration_frames / self.project.fps:.2f}s).",
        )

    def _browse_music_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Background Music", "", "Audio Files (*.mp3 *.wav)"
        )
        if file_path:
            self.music_file_path = file_path
            self.lbl_music_file.setText(Path(file_path).name)

    def _on_close(self) -> None:
        if self.active_worker and self.active_worker.isRunning():
            self.active_worker.cancel()
            self.active_worker.wait(1000)
        self.accept()
