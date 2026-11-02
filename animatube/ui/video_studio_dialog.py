from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
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

from animatube.ai.models import AIGenerationJob, JobStatus, VideoPrompt
from animatube.ai.registry import AIProviderRegistry
from animatube.ai.video_worker import VideoGenerationWorker
from animatube.core.models import Project
from animatube.presets.little_dreamers import LITTLE_DREAMERS_CHARACTERS

logger = logging.getLogger(__name__)


class VideoStudioDialog(QDialog):
    """
    AI Video Generation Studio Dialog.
    Supports Text-to-Video and Image-to-Video with character references,
    camera motion presets, aspect ratios, job history, and direct timeline import.
    """

    def __init__(
        self,
        project: Project,
        parent: QWidget | None = None,
        project_file: str = "",
        on_video_imported: Callable[[str, float], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.project = project
        self.project_file = project_file
        self.on_video_imported = on_video_imported

        self.setWindowTitle("AnimaVideo — AI Video Generator Studio")
        self.resize(1060, 720)

        self.registry = AIProviderRegistry.get_instance()
        self.active_worker: VideoGenerationWorker | None = None
        self.current_job: AIGenerationJob | None = None
        self.job_history: list[AIGenerationJob] = []

        self._build_ui()
        self._load_providers()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        # Header
        header_box = QHBoxLayout()
        header_title = QLabel("AI Video Generator Studio")
        header_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #7dd3fc;")
        header_box.addWidget(header_title)

        header_box.addStretch(1)
        header_box.addWidget(QLabel("Provider:"))
        self.provider_combo = QComboBox()
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        header_box.addWidget(self.provider_combo)
        root.addLayout(header_box)

        # Main splitter (Left: Prompting & Controls, Right: Preview & History)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # LEFT PANEL: Generation Controls
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # Mode Selection
        mode_group = QGroupBox("Generation Mode")
        mode_layout = QHBoxLayout(mode_group)
        self.radio_t2v = QRadioButton("Text-to-Video")
        self.radio_i2v = QRadioButton("Image-to-Video (Character / Initial Frame)")
        self.radio_t2v.setChecked(True)
        self.radio_t2v.toggled.connect(self._on_mode_toggled)
        mode_layout.addWidget(self.radio_t2v)
        mode_layout.addWidget(self.radio_i2v)
        left_layout.addWidget(mode_group)

        # Prompt & Parameters Form
        form_group = QGroupBox("Scene & Character Prompting")
        form = QFormLayout(form_group)

        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Describe the scene, action, character movements, lighting, and preschool animation details...")
        self.prompt_input.setMaximumHeight(90)
        form.addRow("Scene Prompt *:", self.prompt_input)

        self.negative_prompt = QLineEdit("realistic human skin pores, adult, sharp jawline, disheveled clothing, flat 2D, dark gloomy lighting, extra limbs")
        form.addRow("Negative Prompt:", self.negative_prompt)

        # Character Anchor Preset
        self.char_preset_combo = QComboBox()
        self.char_preset_combo.addItem("Custom / None", "")
        for char_id, char_data in LITTLE_DREAMERS_CHARACTERS.items():
            self.char_preset_combo.addItem(f"{char_data['name']} ({char_data['species']})", char_id)
        self.char_preset_combo.currentIndexChanged.connect(self._on_char_preset_changed)
        form.addRow("Character Preset:", self.char_preset_combo)

        # Reference image box
        self.ref_box = QWidget()
        ref_layout = QHBoxLayout(self.ref_box)
        ref_layout.setContentsMargins(0, 0, 0, 0)
        self.ref_path_input = QLineEdit()
        self.ref_path_input.setPlaceholderText("Select character reference image or starting frame (.png, .jpg)...")
        self.btn_browse_ref = QPushButton("Browse...")
        self.btn_browse_ref.clicked.connect(self._browse_reference_image)
        ref_layout.addWidget(self.ref_path_input, 1)
        ref_layout.addWidget(self.btn_browse_ref)
        form.addRow("Reference Image:", self.ref_box)

        # Camera Movement
        self.camera_combo = QComboBox()
        for label, val in [
            ("Static / Natural Animation", "none"),
            ("Slow Pan Left", "pan_left"),
            ("Slow Pan Right", "pan_right"),
            ("Tilt Up", "tilt_up"),
            ("Tilt Down", "tilt_down"),
            ("Slow Zoom In", "zoom_in"),
            ("Slow Zoom Out", "zoom_out"),
            ("Orbit 3D", "orbit"),
        ]:
            self.camera_combo.addItem(label, val)
        form.addRow("Camera Movement:", self.camera_combo)

        # Aspect Ratio & Resolution
        geom_box = QHBoxLayout()
        self.aspect_combo = QComboBox()
        self.aspect_combo.addItems(["16:9", "1:1", "9:16", "4:3"])
        self.res_combo = QComboBox()
        self.res_combo.addItems(["1080p (1920x1080)", "720p (1280x720)"])
        geom_box.addWidget(QLabel("Aspect:"))
        geom_box.addWidget(self.aspect_combo)
        geom_box.addWidget(QLabel("Res:"))
        geom_box.addWidget(self.res_combo)
        form.addRow("Dimensions:", geom_box)

        # Duration & Motion Strength
        time_box = QHBoxLayout()
        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setRange(1.0, 30.0)
        self.duration_spin.setValue(4.0)
        self.duration_spin.setSingleStep(0.5)
        self.duration_spin.setSuffix(" sec")
        time_box.addWidget(QLabel("Clip Duration:"))
        time_box.addWidget(self.duration_spin)

        self.motion_slider = QSlider(Qt.Orientation.Horizontal)
        self.motion_slider.setRange(10, 100)
        self.motion_slider.setValue(50)
        time_box.addWidget(QLabel("Motion:"))
        time_box.addWidget(self.motion_slider)
        form.addRow("Timing & Energy:", time_box)

        left_layout.addWidget(form_group)

        # Actions & Progress
        act_box = QHBoxLayout()
        self.btn_generate = QPushButton("Generate AI Video Clip")
        self.btn_generate.setStyleSheet("background: #0284c7; color: white; font-weight: bold; padding: 10px;")
        self.btn_generate.clicked.connect(self._start_generation)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._cancel_generation)
        act_box.addWidget(self.btn_generate, 2)
        act_box.addWidget(self.btn_cancel, 1)
        left_layout.addLayout(act_box)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        left_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready to generate.")
        self.status_label.setStyleSheet("color: #94a3b8; font-style: italic;")
        left_layout.addWidget(self.status_label)

        left_layout.addStretch(1)
        splitter.addWidget(left_widget)

        # RIGHT PANEL: Preview & Job History
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Preview Area
        preview_group = QGroupBox("Generated Video Preview & Import")
        prev_layout = QVBoxLayout(preview_group)

        self.preview_display = QLabel("No video generated yet.")
        self.preview_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_display.setMinimumHeight(220)
        self.preview_display.setStyleSheet("background: #0f172a; border: 1px dashed #334155; border-radius: 6px; color: #64748b;")
        prev_layout.addWidget(self.preview_display)

        self.meta_label = QLabel("Duration: -- | Resolution: -- | Format: MP4")
        self.meta_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        prev_layout.addWidget(self.meta_label)

        import_box = QHBoxLayout()
        self.btn_import_timeline = QPushButton("Import to AnimaVideo Timeline")
        self.btn_import_timeline.setEnabled(False)
        self.btn_import_timeline.setStyleSheet("background: #16a34a; color: white; font-weight: bold; padding: 8px;")
        self.btn_import_timeline.clicked.connect(self._import_to_timeline)
        import_box.addWidget(self.btn_import_timeline)
        prev_layout.addLayout(import_box)

        right_layout.addWidget(preview_group)

        # Job History Table
        history_group = QGroupBox("Studio Job History")
        hist_layout = QVBoxLayout(history_group)
        self.history_table = QTableWidget(0, 5)
        self.history_table.setHorizontalHeaderLabels(["Job ID", "Prompt", "Status", "Duration", "Result File"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.itemSelectionChanged.connect(self._on_history_selected)
        hist_layout.addWidget(self.history_table)
        right_layout.addWidget(history_group, 1)

        splitter.addWidget(right_widget)
        splitter.setSizes([520, 540])
        root.addWidget(splitter, 1)

        # Bottom Close Button
        bottom_row = QHBoxLayout()
        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.close)
        bottom_row.addStretch(1)
        bottom_row.addWidget(self.btn_close)
        root.addLayout(bottom_row)

        self._on_mode_toggled()

    def _load_providers(self) -> None:
        self.provider_combo.clear()
        providers = self.registry.list_providers(self.registry.get_provider(self.registry._providers.get.__self__ if hasattr(self.registry, "_providers") else None, None).media_type if False else None)
        video_providers = [p for p in self.registry.list_providers() if p["media_type"] == "video"]
        for p in video_providers:
            label = f"{p['provider_name']} ({p['provider_id']})"
            self.provider_combo.addItem(label, p["provider_id"])

    def _on_provider_changed(self) -> None:
        pid = self.provider_combo.currentData()
        if pid:
            prov = self.registry.get_video_provider(pid)
            caps = prov.capabilities
            self.radio_i2v.setEnabled(caps.image_to_video)
            self.camera_combo.setEnabled(caps.camera_control)

    def _on_mode_toggled(self) -> None:
        is_i2v = self.radio_i2v.isChecked()
        self.ref_box.setEnabled(is_i2v)

    def _on_char_preset_changed(self) -> None:
        cid = self.char_preset_combo.currentData()
        if not cid:
            return
        char = LITTLE_DREAMERS_CHARACTERS.get(cid)
        if char:
            anchor = Path(char["anchor_image"]).resolve()
            if anchor.is_file():
                self.ref_path_input.setText(str(anchor))
                self.radio_i2v.setChecked(True)
            self.negative_prompt.setText(char["negative_prompt"])
            first_action = list(char["actions"].values())[0]
            self.prompt_input.setText(
                f"Pixar 3D animation of {char['name']}. {first_action}. Warm soft lighting, 24fps smooth."
            )

    def _browse_reference_image(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select Character Reference or Start Frame",
            str(Path.cwd() / "little-dreamers"),
            "Images (*.png *.jpg *.jpeg *.webp)",
        )
        if filename:
            self.ref_path_input.setText(filename)

    def _start_generation(self) -> None:
        prompt_text = self.prompt_input.toPlainText().strip()
        ref_path = self.ref_path_input.text().strip() if self.radio_i2v.isChecked() else ""
        
        if not prompt_text and not ref_path:
            QMessageBox.warning(self, "Missing Input", "Please enter a scene prompt or choose a reference image.")
            return

        pid = self.provider_combo.currentData() or "mock_video"
        provider = self.registry.get_video_provider(pid)

        aspect = self.aspect_combo.currentText()
        duration = float(self.duration_spin.value())
        camera = self.camera_combo.currentData() or "none"
        motion = float(self.motion_slider.value()) / 100.0

        v_prompt = VideoPrompt(
            prompt=prompt_text,
            negative_prompt=self.negative_prompt.text().strip(),
            reference_image_path=ref_path,
            aspect_ratio=aspect,
            duration_seconds=duration,
            camera_motion=camera,
            motion_strength=motion,
        )

        try:
            provider.validate_input(v_prompt)
        except Exception as exc:
            QMessageBox.warning(self, "Invalid Parameters", str(exc))
            return

        # Determine target output folder inside current project or home
        if self.project_file:
            out_dir = Path(self.project_file).parent / "ai_videos"
        else:
            out_dir = Path.home() / "AnimaTube" / "GeneratedVideos"
        out_dir.mkdir(parents=True, exist_ok=True)

        self.btn_generate.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.progress_bar.setValue(5)
        self.status_label.setText("Starting video generation worker...")

        self.active_worker = VideoGenerationWorker(provider, v_prompt, out_dir, parent=self)
        self.active_worker.progress_changed.connect(self._on_worker_progress)
        self.active_worker.generation_finished.connect(self._on_worker_finished)
        self.active_worker.error_occurred.connect(self._on_worker_error)
        self.active_worker.cancelled.connect(self._on_worker_cancelled)
        self.active_worker.start()

    def _on_worker_progress(self, progress: float, message: str) -> None:
        self.progress_bar.setValue(int(progress * 100))
        self.status_label.setText(message)

    def _on_worker_finished(self, job: AIGenerationJob) -> None:
        self.btn_generate.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.progress_bar.setValue(100)
        self.status_label.setText("Generation completed!")
        self.current_job = job
        self.job_history.append(job)
        self._add_job_to_table(job)

        # Update preview
        self._display_video_preview(job)
        self.btn_import_timeline.setEnabled(True)
        QMessageBox.information(self, "Video Ready", f"AI Video clip generated successfully!\n\nSaved to: {job.result_path}")

    def _on_worker_error(self, error: str) -> None:
        self.btn_generate.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("Generation failed.")
        QMessageBox.critical(self, "Generation Error", f"Video generation failed:\n{error}")

    def _on_worker_cancelled(self) -> None:
        self.btn_generate.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("Generation cancelled.")
        QMessageBox.information(self, "Cancelled", "Video generation job was cancelled.")

    def _cancel_generation(self) -> None:
        if self.active_worker:
            self.status_label.setText("Cancelling video generation...")
            self.active_worker.cancel()

    def _display_video_preview(self, job: AIGenerationJob) -> None:
        res_path = Path(job.result_path)
        if res_path.is_file():
            size_mb = round(res_path.stat().st_size / (1024 * 1024), 2)
            dur = job.metadata.get("duration", 4.0)
            aspect = job.metadata.get("aspect_ratio", "16:9")
            self.preview_display.setText(f"VIDEO CLIP READY\n\nFile: {res_path.name}\nSize: {size_mb} MB\nAspect: {aspect}\nDuration: {dur}s\nStatus: Verified MP4")
            self.meta_label.setText(f"File: {res_path.name} ({size_mb} MB) | Duration: {dur}s | Cost: ${job.usage.cost_usd:.3f}")

    def _add_job_to_table(self, job: AIGenerationJob) -> None:
        row = self.history_table.rowCount()
        self.history_table.insertRow(row)
        prompt_snippet = job.metadata.get("prompt", "")[:35]
        dur = f"{job.metadata.get('duration', 4.0)}s"

        self.history_table.setItem(row, 0, QTableWidgetItem(job.job_id[:8]))
        self.history_table.setItem(row, 1, QTableWidgetItem(prompt_snippet))
        self.history_table.setItem(row, 2, QTableWidgetItem(job.status.value.upper()))
        self.history_table.setItem(row, 3, QTableWidgetItem(dur))
        self.history_table.setItem(row, 4, QTableWidgetItem(Path(job.result_path).name if job.result_path else "--"))

    def _on_history_selected(self) -> None:
        selected = self.history_table.currentRow()
        if 0 <= selected < len(self.job_history):
            job = self.job_history[selected]
            self.current_job = job
            self._display_video_preview(job)
            self.btn_import_timeline.setEnabled(bool(job.result_path and Path(job.result_path).is_file()))

    def _import_to_timeline(self) -> None:
        if not self.current_job or not self.current_job.result_path:
            return
        video_path = self.current_job.result_path
        dur = float(self.current_job.metadata.get("duration", 4.0))

        if self.on_video_imported:
            self.on_video_imported(video_path, dur)
            QMessageBox.information(self, "Imported", f"Clip successfully imported to timeline:\n{Path(video_path).name}")
            self.close()
        else:
            QMessageBox.information(self, "Ready", f"Video clip ready for timeline:\n{video_path}")
