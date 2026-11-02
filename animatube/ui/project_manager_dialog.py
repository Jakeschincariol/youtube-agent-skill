from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFileDialog, QHBoxLayout, QInputDialog,
    QLabel, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QVBoxLayout,
)

from animatube.core.project_manager import ProjectManager, STAGES


class ProjectManagerDialog(QDialog):
    def __init__(self, library_dir: str | Path, parent=None):
        super().__init__(parent)
        self.manager = ProjectManager(library_dir)
        self.selected_project = ""
        self.setWindowTitle("AnimaTube — Video Project Manager")
        self.resize(820, 560)
        root = QVBoxLayout(self)
        root.addWidget(QLabel("YOUR VIDEO PROJECTS  ·  Stored locally on this device"))
        self.projects = QListWidget()
        self.projects.currentItemChanged.connect(self._selection_changed)
        root.addWidget(self.projects, 1)

        actions = QHBoxLayout()
        for label, callback in (
            ("New project", self.create_project), ("Open", self.open_project),
            ("Rename", self.rename_project), ("Archive", self.archive_project),
            ("Delete", self.delete_project), ("Refresh", self.refresh),
        ):
            button = QPushButton(label)
            button.clicked.connect(callback)
            actions.addWidget(button)
        root.addLayout(actions)

        root.addWidget(QLabel("PRODUCTION TRACKER"))
        stages = QHBoxLayout()
        self.stage_controls = {}
        for stage in STAGES:
            column = QVBoxLayout()
            column.addWidget(QLabel(stage.title()))
            combo = QComboBox()
            combo.addItems(["not_started", "in_progress", "complete", "needs_attention"])
            combo.currentTextChanged.connect(lambda status, key=stage: self._set_stage(key, status))
            self.stage_controls[stage] = combo
            column.addWidget(combo)
            stages.addLayout(column)
        root.addLayout(stages)
        self.storage = QLabel("Select a project to view its storage usage.")
        self.storage.setWordWrap(True)
        root.addWidget(self.storage)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        root.addWidget(buttons)
        self.refresh()

    def _selected(self):
        item = self.projects.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else ""

    def refresh(self):
        selected = self._selected()
        self.projects.clear()
        for project in self.manager.list_projects():
            path = project["project_file"]
            size_mb = project["storage_bytes"] / (1024 * 1024)
            item = QListWidgetItem(
                f'{project["name"]}   ·   {project["scene_count"]} scenes   ·   '
                f'{size_mb:.1f} MB   ·   {project["exports"]} exports'
            )
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.projects.addItem(item)
            if path == selected:
                self.projects.setCurrentItem(item)
        if self.projects.count() and self.projects.currentRow() < 0:
            self.projects.setCurrentRow(0)
        self._selection_changed(self.projects.currentItem(), None)

    def _selection_changed(self, current, previous):
        path = current.data(Qt.ItemDataRole.UserRole) if current else ""
        self.selected_project = path
        if not path:
            self.storage.setText("Select a project to view its storage usage.")
            return
        folder = Path(path).parent
        manifest = self.manager.list_projects()
        entry = next((p for p in manifest if p["project_file"] == path), {})
        for stage, combo in self.stage_controls.items():
            combo.blockSignals(True)
            combo.setCurrentText(entry.get("stages", {}).get(stage, "not_started"))
            combo.blockSignals(False)
        parts = self.manager.storage_breakdown(path)
        labels = [f"{key.replace('_', ' ').title()}: {value / (1024 * 1024):.1f} MB" for key, value in parts.items()]
        self.storage.setText("Storage breakdown  ·  " + "   |   ".join(labels))

    def _set_stage(self, stage, status):
        if self.selected_project:
            self.manager.update_stage(self.selected_project, stage, status)
            self.refresh()

    def create_project(self):
        name, ok = QInputDialog.getText(self, "New video project", "Project name:")
        if ok and name.strip():
            try:
                self.selected_project = str(self.manager.create_project(name))
                self.refresh()
            except Exception as exc:
                QMessageBox.critical(self, "Could not create project", str(exc))

    def open_project(self):
        if self._selected():
            self.selected_project = self._selected()
            self.accept()

    def rename_project(self):
        path = self._selected()
        if not path: return
        name, ok = QInputDialog.getText(self, "Rename project", "New name:", text=Path(path).stem)
        if ok and name.strip():
            try:
                self.selected_project = str(self.manager.rename_project(path, name))
                self.refresh()

            except Exception as exc:
                QMessageBox.critical(self, "Rename failed", str(exc))

    def archive_project(self):
        path = self._selected()
        if not path: return
        if QMessageBox.question(self, "Archive project", "Move this project into the library Archive folder?") != QMessageBox.StandardButton.Yes:
            return
        try:
            self.manager.archive_project(path)
            self.selected_project = ""
            self.refresh()
        except Exception as exc:
            QMessageBox.critical(self, "Archive failed", str(exc))

    def delete_project(self):
        path = self._selected()
        if not path: return
        if QMessageBox.warning(self, "Delete project", "Permanently delete this project and all its assets, caches and exports?",
                               QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel) != QMessageBox.StandardButton.Yes:
            return
        try:
            self.manager.delete_project(path)
            self.selected_project = ""
            self.refresh()
        except Exception as exc:
            QMessageBox.critical(self, "Delete failed", str(exc))
