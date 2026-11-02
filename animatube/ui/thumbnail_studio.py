from __future__ import annotations

import logging
from pathlib import Path
import tempfile
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from animatube.core.models import Project
from animatube.thumbnails.generator import (
    ThumbnailConcept,
    ThumbnailEngine,
    validate_headline,
)

logger = logging.getLogger("animatube.ui.thumbnails")


class ThumbnailStudioDialog(QDialog):
    """
    Interactive Desktop AI Thumbnail Studio.
    Provides live preview, headline editing, concept selection,
    asset swapping, and dual JPG/PNG export.
    """

    def __init__(
        self,
        project: Project,
        parent: QWidget | None = None,
        project_file: str = "",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("AnimaTube — AI Thumbnail Studio")
        self.resize(1100, 720)

        self.project = project
        self.project_file = project_file
        self.engine = ThumbnailEngine()
        self.temp_dir = Path(tempfile.mkdtemp(prefix="animatube_thumb_"))

        # Collect available diagram images
        self.available_assets = self._discover_assets()
        self.concepts = self.engine.generate_concepts(
            topic=project.name or "DevOps Roadmap 2027",
            available_assets=self.available_assets,
        )
        self.active_concept_idx = 0
        self.custom_image_path: str = ""

        self._build_ui()
        self.load_concept_into_controls(0)
        self.update_preview()

    def _discover_assets(self) -> list[Path]:
        assets: list[Path] = []
        # Check scene image layers
        for s in self.project.scenes:
            for l in s.layers:
                if l.kind == "image" and l.asset_path:
                    p = self.project.resolve_asset(l.asset_path)
                    if p.is_file() and p not in assets:
                        assets.append(p)

        # Check project directory assets/
        if self.project_file:
            proj_dir = Path(self.project_file).parent
            for sub in (proj_dir / "assets", proj_dir):
                if sub.is_dir():
                    for ext in ("*.png", "*.jpg", "*.jpeg"):
                        for f in sub.glob(ext):
                            if f.is_file() and f not in assets:
                                assets.append(f)
        return assets

    def _build_ui(self) -> None:
        main_layout = QHBoxLayout(self)

        # Left Editor Panel
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setFixedWidth(380)

        # Concept Selection Box
        concept_group = QGroupBox("Thumbnail Concepts (AI Generated)")
        c_layout = QVBoxLayout(concept_group)

        self.concept_picker = QComboBox()
        for idx, c in enumerate(self.concepts):
            self.concept_picker.addItem(f"{idx+1}. {c.concept_name}")
        self.concept_picker.currentIndexChanged.connect(self._on_concept_changed)
        c_layout.addWidget(self.concept_picker)

        self.btn_regenerate = QPushButton("✨ Regenerate AI Concepts")
        self.btn_regenerate.clicked.connect(self._on_regenerate_concepts)
        c_layout.addWidget(self.btn_regenerate)
        left_layout.addWidget(concept_group)

        # Customization Box
        edit_group = QGroupBox("Customize Layout & Typography")
        form = QFormLayout(edit_group)

        self.txt_headline = QLineEdit()
        self.txt_headline.textChanged.connect(self._on_editor_changed)
        form.addRow("Headline:", self.txt_headline)

        self.txt_subheadline = QLineEdit()
        self.txt_subheadline.textChanged.connect(self._on_editor_changed)
        form.addRow("Subheadline:", self.txt_subheadline)

        self.txt_badge = QLineEdit()
        self.txt_badge.textChanged.connect(self._on_editor_changed)
        form.addRow("Badge Text:", self.txt_badge)

        self.img_picker = QComboBox()
        self.img_picker.addItem("(Default Asset)")
        for a in self.available_assets:
            self.img_picker.addItem(a.name, str(a))
        self.img_picker.currentIndexChanged.connect(self._on_image_selected)
        form.addRow("Visual Asset:", self.img_picker)

        self.btn_browse_img = QPushButton("Browse Image...")
        self.btn_browse_img.clicked.connect(self._on_browse_image)
        form.addRow("", self.btn_browse_img)

        left_layout.addWidget(edit_group)

        # Export Buttons
        btn_box = QGroupBox("Export Thumbnail")
        b_layout = QVBoxLayout(btn_box)

        self.btn_export_png = QPushButton("Export 1280x720 PNG")
        self.btn_export_png.clicked.connect(lambda: self.export_thumbnail("PNG"))
        b_layout.addWidget(self.btn_export_png)

        self.btn_export_jpg = QPushButton("Export 1280x720 JPG")
        self.btn_export_jpg.clicked.connect(lambda: self.export_thumbnail("JPG"))
        b_layout.addWidget(self.btn_export_jpg)

        self.btn_export_both = QPushButton("Export Complete Thumbnail Pack (PNG + JPG)")
        self.btn_export_both.setStyleSheet("font-weight: bold; background-color: #0284c7; color: white;")
        self.btn_export_both.clicked.connect(self.export_pack)
        b_layout.addWidget(self.btn_export_both)

        left_layout.addWidget(btn_box)
        left_layout.addStretch()

        # Close / Done
        self.btn_done = QPushButton("Close Studio")
        self.btn_done.clicked.connect(self.accept)
        left_layout.addWidget(self.btn_done)

        main_layout.addWidget(left_panel)

        # Right Preview Area
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        header_lbl = QLabel("1280 × 720 (16:9) YouTube High Quality Live Preview")
        header_lbl.setStyleSheet("font-weight: bold; font-size: 14px; color: #38bdf8;")
        right_layout.addWidget(header_lbl)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.preview_label.setStyleSheet("background-color: #0b1329; border: 2px solid #1e293b; border-radius: 8px;")
        right_layout.addWidget(self.preview_label, 1)

        main_layout.addWidget(right_panel, 1)

    def load_concept_into_controls(self, idx: int) -> None:
        if 0 <= idx < len(self.concepts):
            self.active_concept_idx = idx
            concept = self.concepts[idx]
            self.txt_headline.blockSignals(True)
            self.txt_subheadline.blockSignals(True)
            self.txt_badge.blockSignals(True)

            self.txt_headline.setText(concept.headline)
            self.txt_subheadline.setText(concept.subheadline)
            self.txt_badge.setText(concept.badge_text)

            self.txt_headline.blockSignals(False)
            self.txt_subheadline.blockSignals(False)
            self.txt_badge.blockSignals(False)

    def _on_concept_changed(self, idx: int) -> None:
        self.load_concept_into_controls(idx)
        self.update_preview()

    def _on_editor_changed(self) -> None:
        concept = self.concepts[self.active_concept_idx]
        headline = self.txt_headline.text()
        try:
            concept.headline = validate_headline(headline) if headline else "DEVOPS ROADMAP 2027"
        except ValueError:
            pass  # Keep current valid headline if editing
        concept.subheadline = self.txt_subheadline.text()
        concept.badge_text = self.txt_badge.text()
        self.update_preview()

    def _on_image_selected(self, idx: int) -> None:
        data = self.img_picker.currentData()
        self.custom_image_path = str(data) if data else ""
        self.update_preview()

    def _on_browse_image(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select Visual Asset", "", "Images (*.png *.jpg *.jpeg)"
        )
        if filename:
            self.custom_image_path = filename
            self.img_picker.addItem(Path(filename).name, filename)
            self.img_picker.setCurrentIndex(self.img_picker.count() - 1)
            self.update_preview()

    def _on_regenerate_concepts(self) -> None:
        self.concepts = self.engine.generate_concepts(
            topic=self.project.name or "DevOps Roadmap 2027",
            available_assets=self.available_assets,
        )
        self.concept_picker.blockSignals(True)
        self.concept_picker.clear()
        for idx, c in enumerate(self.concepts):
            self.concept_picker.addItem(f"{idx+1}. {c.concept_name}")
        self.concept_picker.blockSignals(False)
        self.load_concept_into_controls(0)
        self.update_preview()
        QMessageBox.information(self, "Concepts Regenerated", "Generated 3 fresh thumbnail variations!")

    def update_preview(self) -> None:
        if not self.concepts:
            return
        concept = self.concepts[self.active_concept_idx]
        preview_file = self.temp_dir / f"preview_c{self.active_concept_idx}.png"

        try:
            self.engine.render_thumbnail(
                concept,
                preview_file,
                format="PNG",
                custom_image_path=self.custom_image_path or None,
            )
            pix = QPixmap(str(preview_file))
            if not pix.isNull():
                scaled = pix.scaled(
                    self.preview_label.width() - 20,
                    self.preview_label.height() - 20,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.preview_label.setPixmap(scaled)
        except Exception as exc:
            logger.error("Preview render failed: %s", exc)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.update_preview()

    def export_thumbnail(self, fmt: str) -> None:
        ext = ".png" if fmt == "PNG" else ".jpg"
        default_name = f"{Path(self.project_file).stem if self.project_file else 'project'}_thumbnail{ext}"
        default_dir = Path(self.project_file).parent if self.project_file else Path.cwd()

        dest, _ = QFileDialog.getSaveFileName(
            self,
            f"Save {fmt} Thumbnail",
            str(default_dir / default_name),
            f"{fmt} Image (*{ext})",
        )
        if not dest:
            return

        concept = self.concepts[self.active_concept_idx]
        try:
            out_path = self.engine.render_thumbnail(
                concept,
                dest,
                format=fmt,
                custom_image_path=self.custom_image_path or None,
            )
            QMessageBox.information(self, "Thumbnail Saved", f"Successfully exported 1280x720 {fmt} thumbnail to:\n{out_path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export Failed", f"Could not export thumbnail: {exc}")

    def export_pack(self) -> None:
        default_dir = Path(self.project_file).parent if self.project_file else Path.cwd()
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Save Thumbnail Pack", str(default_dir))
        if not folder:
            return

        out_folder = Path(folder)
        base_stem = Path(self.project_file).stem if self.project_file else "project"
        concept = self.concepts[self.active_concept_idx]

        png_path = out_folder / f"{base_stem}_thumbnail.png"
        jpg_path = out_folder / f"{base_stem}_thumbnail.jpg"

        try:
            self.engine.render_thumbnail(concept, png_path, format="PNG", custom_image_path=self.custom_image_path or None)
            self.engine.render_thumbnail(concept, jpg_path, format="JPG", custom_image_path=self.custom_image_path or None)
            QMessageBox.information(
                self,
                "Thumbnail Pack Exported",
                f"Successfully exported 1280x720 thumbnails:\n- {png_path.name}\n- {jpg_path.name}",
            )
        except Exception as exc:
            QMessageBox.critical(self, "Export Failed", f"Could not export thumbnail pack: {exc}")
