from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from animatube.core.models import Project
from animatube.pipeline.animator import (
    SceneAnimator,
    SceneMotionStyle,
    detect_scene_motion_style,
    enhance_project_with_animations,
)

logger = logging.getLogger("animatube.ui.animator")


class SceneAnimatorDialog(QDialog):
    """
    Dialog allowing creators to review, configure and apply
    lightweight motion graphics and animations across project scenes.
    """

    def __init__(
        self,
        project: Project,
        parent: QWidget | None = None,
        on_applied: Any | None = None,
        on_export: Any | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("AnimaTube — Animated Scene Enhancement")
        self.resize(780, 560)

        self.project = project
        self.on_applied = on_applied
        self.on_export = on_export

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        header = QLabel("Enhance Scenes with Motion Graphics")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #38bdf8;")
        layout.addWidget(header)

        desc = QLabel(
            "Automatically enhances each scene with content-appropriate motion effects:\n"
            "• Cinematic Ken Burns slow zoom-in & zoom-out (camera pans)\n"
            "• Staggered slide transitions for title headers & lower thirds\n"
            "• Glowing keyword highlight badges on key concepts\n"
            "• Moving arrows and progressive pipeline reveals\n"
            "• Smooth scene fade-in and dip transitions"
        )
        desc.setStyleSheet("color: #94a3b8; font-size: 13px; margin-bottom: 8px;")
        layout.addWidget(desc)

        # Scene Motion Breakdown Box
        scenes_box = QGroupBox(f"Scene Animation Breakdown ({len(self.project.scenes)} Scenes)")
        s_layout = QVBoxLayout(scenes_box)

        self.scene_list = QListWidget()
        total = len(self.project.scenes)
        for idx, sc in enumerate(self.project.scenes):
            style = detect_scene_motion_style(sc.name, idx, total)
            item = QListWidgetItem(
                f"Scene {idx+1}: {sc.name}  →  [{style.value.upper()}]  ({sc.duration_frames} frames @ {self.project.fps} fps)"
            )
            self.scene_list.addItem(item)

        s_layout.addWidget(self.scene_list)
        layout.addWidget(scenes_box)

        # Action Buttons
        btn_layout = QHBoxLayout()

        self.btn_apply = QPushButton("✨ Apply Animations to Project")
        self.btn_apply.setStyleSheet("font-weight: bold; padding: 8px; background-color: #0284c7; color: white;")
        self.btn_apply.clicked.connect(self._apply_animations)
        btn_layout.addWidget(self.btn_apply)

        self.btn_export = QPushButton("🎬 Export Animated Complete Video...")
        self.btn_export.setStyleSheet("font-weight: bold; padding: 8px;")
        self.btn_export.clicked.connect(self._apply_and_export)
        btn_layout.addWidget(self.btn_export)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        layout.addLayout(btn_layout)

    def _apply_animations(self) -> None:
        enhance_project_with_animations(self.project)
        if self.on_applied:
            self.on_applied()
        QMessageBox.information(
            self,
            "Animations Applied",
            "Motion graphics and camera keyframes successfully applied!\n"
            "You can now scrub the timeline slider in the main editor to review every frame.",
        )
        self.accept()

    def _apply_and_export(self) -> None:
        enhance_project_with_animations(self.project)
        if self.on_applied:
            self.on_applied()
        self.accept()
        if self.on_export:
            self.on_export()
