from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush, QFont, QImage, QPainter, QPen, QPixmap, QTextOption
from PySide6.QtWidgets import (
    QApplication, QColorDialog, QComboBox, QFileDialog, QGraphicsEllipseItem, QGraphicsItem,
    QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsScene, QGraphicsTextItem,
    QGraphicsView, QHBoxLayout, QInputDialog, QLabel, QListWidget, QListWidgetItem,
    QMainWindow, QMessageBox, QPushButton, QSlider, QVBoxLayout, QWidget,
    QProgressDialog,
)

from animatube.core.animation import set_keyframe, state_at
from animatube.core.models import Layer, Project, Scene
from animatube.core.project import load_project, save_project
from animatube.core.project_manager import ProjectManager
from animatube.ui.project_manager_dialog import ProjectManagerDialog
from animatube.ui.channel_setup_dialog import ChannelSetupDialog
from animatube.export.renderer import export_scene, render_frame
from animatube.export.compiler import compile_scenes, ExportCancelledError
from animatube.ui.animator_dialog import SceneAnimatorDialog
from animatube.ui.thumbnail_studio import ThumbnailStudioDialog
from animatube.ui.audio_studio_dialog import AudioStudioDialog


class Canvas(QGraphicsView):
    positions_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setBackgroundBrush(QBrush(QColor("#0b0d12")))
        self.setMinimumSize(520, 340)
        self.items_by_id = {}

    def show_project(self, project: Project, scene: Scene, frame: int):
        self.scene().clear()
        self.items_by_id.clear()
        scale = min(760 / project.width, 430 / project.height)
        width, height = project.width * scale, project.height * scale
        self.scene().setSceneRect(0, 0, width, height)
        self.scene().setBackgroundBrush(QBrush(QColor(project.background)))
        for layer in scene.layers:
            state = state_at(layer, frame)
            x, y = state["x"] * scale, state["y"] * scale
            w, h = layer.width * scale * state["scale"], layer.height * scale * state["scale"]
            if layer.kind == "text":
                item = QGraphicsTextItem(layer.text)
                font = QFont("Arial", max(8, round(layer.font_size * scale)))
                font.setBold(True)
                item.setFont(font)
                item.setDefaultTextColor(QColor(layer.color))
                item.setTextWidth(w)
                item.document().setDocumentMargin(0)
                text_option = item.document().defaultTextOption()
                text_option.setAlignment(Qt.AlignmentFlag.AlignCenter)
                item.document().setDefaultTextOption(text_option)
                text_height = item.boundingRect().height()
                item.setPos(x, y + max(0, (h - text_height) / 2))
            elif layer.kind in ("rect", "ellipse"):
                item = QGraphicsRectItem(0, 0, w, h) if layer.kind == "rect" else QGraphicsEllipseItem(0, 0, w, h)
                item.setBrush(QBrush(QColor(layer.color)))
                item.setPen(QPen(Qt.PenStyle.NoPen))
                item.setPos(x, y)
            else:
                pixmap = QPixmap(str(project.resolve_asset(layer.asset_path))) if layer.asset_path else QPixmap()
                if pixmap.isNull():
                    item = QGraphicsRectItem(0, 0, w, h)
                    item.setBrush(QBrush(QColor("#555b6d")))
                else:
                    item = QGraphicsPixmapItem(pixmap.scaled(round(w), round(h), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation))
                item.setPos(x, y)
            item.setData(0, layer.id)
            item.setTransformOriginPoint(item.boundingRect().center())
            item.setOpacity(state["opacity"])
            item.setRotation(state["rotation"])
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
            self.scene().addItem(item)
            self.items_by_id[layer.id] = item
        self.fitInView(self.scene().sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.positions_changed.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AnimaTube — Animated Video Editor")
        self.resize(1280, 820)
        self.project = Project()
        self.scene_index = 0
        self.current_frame = 0
        self.project_file = ""
        self.canvas = Canvas()
        self.canvas.positions_changed.connect(self.sync_dragged_items)
        self.layer_list = QListWidget()
        self.layer_list.currentItemChanged.connect(self.select_layer)
        self.scene_picker = QComboBox()
        self.scene_picker.currentIndexChanged.connect(self.change_scene)
        self.frame_slider = QSlider(Qt.Orientation.Horizontal)
        self.frame_slider.valueChanged.connect(self.change_frame)
        self.frame_label = QLabel("Frame 0")
        self._build_ui()
        self.refresh()

    @property
    def active_scene(self) -> Scene:
        return self.project.scenes[self.scene_index]

    def _build_ui(self):
        root = QWidget()
        layout = QVBoxLayout(root)
        toolbar = QHBoxLayout()
        for label, callback in (
            ("Channel Setup", self.open_channel_manager), ("Projects", self.open_project_manager), ("New", self.new_project), ("Open", self.open_project), ("Save", self.save_project),
            ("Add scene", self.add_scene), ("Add text", self.add_text),
            ("Rectangle", self.add_rectangle), ("Ellipse", self.add_ellipse),
            ("Image", self.add_image), ("Keyframe", self.add_keyframe),
            ("Animate Scenes", self.open_scene_animator),
            ("Generate Thumbnail", self.open_thumbnail_studio),
            ("Audio Studio", self.open_audio_studio),
            ("Preview Scene", self.preview_scene), ("Export MP4", self.export), ("Export Complete Video", self.export_complete_video),
        ):
            button = QPushButton(label)
            button.clicked.connect(callback)
            toolbar.addWidget(button)
        layout.addLayout(toolbar)

        middle = QHBoxLayout()
        side = QVBoxLayout()
        side.addWidget(QLabel("SCENES"))
        side.addWidget(self.scene_picker)
        side.addWidget(QLabel("LAYERS — drag objects on canvas"))
        side.addWidget(self.layer_list)
        middle.addLayout(side, 1)
        middle.addWidget(self.canvas, 4)
        layout.addLayout(middle, 1)

        timeline = QHBoxLayout()
        timeline.addWidget(QLabel("TIMELINE"))
        timeline.addWidget(self.frame_slider, 1)
        timeline.addWidget(self.frame_label)
        layout.addLayout(timeline)
        self.setCentralWidget(root)
        self.setStyleSheet("""
            QWidget { background: #11141c; color: #e8eaf0; font: 10pt 'Segoe UI'; }
            QPushButton { background: #272d3b; border: 1px solid #3c4558; border-radius: 6px; padding: 8px; }
            QPushButton:hover { background: #38445a; }
            QListWidget, QComboBox { background: #1a202c; border: 1px solid #30394a; padding: 6px; }
            QSlider::groove:horizontal { height: 6px; background: #38445a; }
            QSlider::handle:horizontal { background: #9b83ff; width: 14px; margin: -5px 0; border-radius: 7px; }
        """)

    def refresh(self):
        self.scene_picker.blockSignals(True)
        self.scene_picker.clear()
        for scene in self.project.scenes:
            self.scene_picker.addItem(scene.name)
        self.scene_picker.setCurrentIndex(self.scene_index)
        self.scene_picker.blockSignals(False)
        self.frame_slider.blockSignals(True)
        self.frame_slider.setRange(0, self.active_scene.duration_frames - 1)
        self.frame_slider.setValue(min(self.current_frame, self.active_scene.duration_frames - 1))
        self.frame_slider.blockSignals(False)
        self.current_frame = self.frame_slider.value()
        self.frame_label.setText(f"Frame {self.current_frame} / {self.active_scene.duration_frames - 1}")
        self.layer_list.clear()
        for layer in self.active_scene.layers:
            item = QListWidgetItem(f"{layer.name}  ·  {layer.kind}")
            item.setData(Qt.ItemDataRole.UserRole, layer.id)
            self.layer_list.addItem(item)
        self.canvas.show_project(self.project, self.active_scene, self.current_frame)

    def selected_layer(self):
        item = self.layer_list.currentItem()
        if not item:
            return None
        layer_id = item.data(Qt.ItemDataRole.UserRole)
        return next((layer for layer in self.active_scene.layers if layer.id == layer_id), None)

    def select_layer(self, current, previous):
        if current is None:
            return
        layer_id = current.data(Qt.ItemDataRole.UserRole)
        item = self.canvas.items_by_id.get(layer_id)
        if item:
            self.canvas.scene().clearSelection()
            item.setSelected(True)

    def change_scene(self, index):
        if 0 <= index < len(self.project.scenes):
            self.scene_index, self.current_frame = index, 0
            self.refresh()

    def change_frame(self, frame):
        self.current_frame = frame
        self.frame_label.setText(f"Frame {frame} / {self.active_scene.duration_frames - 1}")
        self.canvas.show_project(self.project, self.active_scene, frame)

    def sync_dragged_items(self):
        scale = min(760 / self.project.width, 430 / self.project.height)
        for layer in self.active_scene.layers:
            item = self.canvas.items_by_id.get(layer.id)
            if item is None:
                continue
            x, y = item.pos().x() / scale, item.pos().y() / scale
            if abs(x - layer.x) > 0.01 or abs(y - layer.y) > 0.01:
                if layer.keyframes:
                    set_keyframe(layer, self.current_frame, "x", x)
                    set_keyframe(layer, self.current_frame, "y", y)
                else:
                    layer.x, layer.y = x, y

    def add_layer(self, layer):
        self.active_scene.layers.append(layer)
        self.refresh()
        self.layer_list.setCurrentRow(self.layer_list.count() - 1)

    def add_text(self):
        value, accepted = QInputDialog.getText(self, "Add text", "Text:", text="Your title")
        if accepted and value.strip():
            self.add_layer(Layer(name="Text", kind="text", text=value.strip()))

    def add_rectangle(self):
        self.add_layer(Layer(name="Rectangle", kind="rect", width=320, height=180, color="#725cff"))

    def add_ellipse(self):
        self.add_layer(Layer(name="Ellipse", kind="ellipse", width=220, height=220, color="#ff9a4a"))

    def add_image(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Import image", "", "Images (*.png *.jpg *.jpeg *.webp *.bmp)")
        if filename:
            path = Path(filename)
            if QPixmap(str(path)).isNull():
                QMessageBox.warning(self, "Import failed", "The selected file could not be decoded as an image.")
                return
            self.add_layer(Layer(name=path.stem, kind="image", asset_path=str(path), width=400, height=260))

    def add_keyframe(self):
        layer = self.selected_layer()
        if not layer:
            QMessageBox.information(self, "Select a layer", "Choose a layer before adding a keyframe.")
            return
        state = state_at(layer, self.current_frame)
        for field, value in state.items():
            set_keyframe(layer, self.current_frame, field, value)
        self.refresh()

    def add_scene(self):
        self.project.scenes.append(Scene(name=f"Scene {len(self.project.scenes) + 1}"))
        self.scene_index = len(self.project.scenes) - 1
        self.current_frame = 0
        self.refresh()

    def project_library_dir(self) -> Path:
        return Path.home() / "AnimaTube" / "Projects"

    def open_channel_manager(self):
        dialog = ChannelSetupDialog(Path.home() / "AnimaTube" / "Channels", self)
        dialog.exec()

    def open_project_manager(self):
        dialog = ProjectManagerDialog(self.project_library_dir(), self)
        if dialog.exec() == dialog.DialogCode.Accepted and dialog.selected_project:
            try:
                self.project = load_project(dialog.selected_project)
                self.project_file = dialog.selected_project
                self.scene_index = self.current_frame = 0
                self.refresh()
            except Exception as exc:
                QMessageBox.critical(self, "Open project failed", str(exc))

    def preview_scene(self):
        if not self.project_file:
            QMessageBox.information(self, "Save project first", "Save this project before creating a scene preview.")
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Save scene preview", f"scene_{self.scene_index + 1:02d}.png", "PNG image (*.png)")
        if not filename:
            return
        try:
            manager = ProjectManager(self.project_library_dir())
            result = manager.scene_preview(self.project_file, self.scene_index, filename, self.current_frame)
            QMessageBox.information(self, "Scene preview ready", f"Preview saved to:\n{result}")
        except Exception as exc:
            QMessageBox.critical(self, "Preview failed", str(exc))

    def new_project(self):
        if QMessageBox.question(self, "New project", "Discard the current unsaved changes?") != QMessageBox.StandardButton.Yes:
            return
        self.project = Project()
        self.scene_index = self.current_frame = 0
        self.project_file = ""
        self.refresh()

    def save_project(self):
        filename = self.project_file
        if not filename:
            filename, _ = QFileDialog.getSaveFileName(self, "Save project", "untitled.anima", "AnimaTube project (*.anima)")
        if not filename:
            return
        try:
            save_project(self.project, filename)
            self.project_file = filename
            self.statusBar().showMessage(f"Saved {filename}", 5000)
        except Exception as exc:
            QMessageBox.critical(self, "Save failed", str(exc))

    def open_project(self):
        default_dir = "output/devops_2027" if Path("output/devops_2027").is_dir() else ""
        filename, _ = QFileDialog.getOpenFileName(self, "Open project", default_dir, "AnimaTube project (*.anima)")
        if not filename:
            return
        try:
            self.project = load_project(filename)
            self.project_file = filename
            self.scene_index = self.current_frame = 0
            self.refresh()
        except Exception as exc:
            QMessageBox.critical(self, "Open failed", str(exc))

    def export(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Export MP4", "video.mp4", "MP4 video (*.mp4)")
        if not filename:
            return
        progress = QProgressDialog("Rendering scene…", "", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        try:
            def update(value):
                progress.setValue(value)
                QApplication.processEvents()
            result = export_scene(self.project, self.active_scene, filename, progress=update)
            progress.setValue(100)
            QMessageBox.information(self, "Export complete", f"Video exported to:\n{result}")
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", str(exc))

    def export_complete_video(self):
        if not self.project.scenes:
            QMessageBox.warning(self, "No scenes", "Cannot export an empty project with no scenes.")
            return

        default_name = f"{Path(self.project_file).stem if self.project_file else 'project'}_complete.mp4"
        default_dir = Path(self.project_file).parent if self.project_file else Path.cwd()
        default_path = str(default_dir / default_name)

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Complete Video",
            default_path,
            "MP4 video (*.mp4)",
        )
        if not filename:
            return

        progress = QProgressDialog("Compiling complete video…", "Cancel", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)

        cancelled = False
        def on_cancel():
            nonlocal cancelled
            cancelled = True

        progress.canceled.connect(on_cancel)

        try:
            def update(value):
                progress.setValue(value)
                QApplication.processEvents()

            result = compile_scenes(
                self.project,
                filename,
                progress=update,
                is_cancelled=lambda: cancelled,
            )
            saved_version = None
            if self.project_file and (Path(self.project_file).parent / "animatube-project.json").is_file():
                saved_version = ProjectManager(Path(self.project_file).parent.parent).save_export_version(self.project_file, result)
            progress.setValue(100)
            message = f"Complete video exported to:\n{result}"
            if saved_version:
                message += f"\n\nSaved project version: {saved_version.name}"
            QMessageBox.information(self, "Export Complete", message)
        except ExportCancelledError:
            self.statusBar().showMessage("Export cancelled by user.", 4000)
        except Exception as exc:
            QMessageBox.critical(self, "Export Failed", str(exc))

    def open_thumbnail_studio(self) -> None:
        """Opens the AI Thumbnail Studio dialog."""
        dialog = ThumbnailStudioDialog(self.project, parent=self, project_file=self.project_file)
        dialog.exec()

    def open_scene_animator(self) -> None:
        """Opens the Animated Scene Enhancement dialog."""
        if not self.project.scenes:
            QMessageBox.warning(self, "No Scenes", "Project has no scenes to animate.")
            return

        def on_applied():
            self.refresh()
            self.change_frame(0)

        dialog = SceneAnimatorDialog(
            self.project,
            parent=self,
            on_applied=on_applied,
            on_export=self.export_complete_video,
        )
        dialog.exec()

    def open_audio_studio(self) -> None:
        """Opens the Audio & Narration Studio dialog."""
        if not self.project.scenes:
            QMessageBox.warning(self, "No Scenes", "Project has no scenes for audio narration.")
            return

        def on_updated():
            self.refresh()
            self.change_frame(0)

        dialog = AudioStudioDialog(
            self.project,
            parent=self,
            project_file=self.project_file,
            on_audio_updated=on_updated,
        )
        dialog.exec()


def run(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv
    app = QApplication.instance() or QApplication(args)
    window = MainWindow()
    if len(args) > 1 and Path(args[1]).is_file():
        try:
            window.project = load_project(args[1])
            window.project_file = str(Path(args[1]).resolve())
            window.scene_index = window.current_frame = 0
            window.refresh()
        except Exception as exc:
            print(f"Warning: could not auto-load {args[1]}: {exc}")
    window.show()
    return app.exec()
