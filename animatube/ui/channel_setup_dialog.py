from __future__ import annotations
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QScrollArea, QTextEdit, QVBoxLayout, QWidget,
)
from animatube.core.channel_manager import ChannelManager, DEFAULT_CHECKLIST

class ChannelSetupDialog(QDialog):
    """Local-first bilingual channel setup wizard and launch checklist."""
    def __init__(self, library_dir: str | Path, parent=None):
        super().__init__(parent)
        self.manager = ChannelManager(library_dir)
        self.profile_path = None
        self.profile = {}
        self.setWindowTitle("AnimaTube — YouTube Channel Setup")
        self.resize(980, 760)
        root = QVBoxLayout(self)
        root.addWidget(QLabel("CHANNEL SETUP · Local profile only — no YouTube account is connected"))
        self.channel_list = QListWidget()
        self.channel_list.currentItemChanged.connect(self._select_channel)
        root.addWidget(self.channel_list)
        controls = QHBoxLayout()
        for label, callback in (("New channel", self.create_channel), ("Delete profile", self.delete_channel)):
            button = QPushButton(label); button.clicked.connect(callback); controls.addWidget(button)
        controls.addStretch(1); root.addLayout(controls)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        host = QWidget(); form = QFormLayout(host)
        self.name = QLineEdit(); self.handle = QLineEdit()
        self.category = QLineEdit("Animation and storytelling")
        self.languages = QLineEdit("Telugu, English")
        self.format = QComboBox()
        for label, value in (("Faceless channel","faceless"),("My own face and voice","own_face_voice"),("AI animation and voice-over","ai_animation_voiceover"),("Combination","hybrid")):
            self.format.addItem(label, value)
        self.goal = QComboBox()
        for label, value in (("Long-term monetized channel","long_term_monetized"),("Personal brand","personal_brand"),("Education and audience building","education_audience"),("Storytelling and entertainment","storytelling_entertainment")):
            self.goal.addItem(label, value)
        self.audience = QLineEdit(); self.problem = QLineEdit()
        self.pillars = QTextEdit(); self.pillars.setMaximumHeight(85)
        self.description = QTextEdit(); self.description.setMaximumHeight(110)
        self.tagline = QLineEdit(); self.colors = QLineEdit("#111827, #F5B942, #FFFFFF")
        self.fonts = QLineEdit()
        self.profile_image = QLineEdit(); self.banner_image = QLineEdit(); self.watermark = QLineEdit()
        self.trailer = QTextEdit(); self.trailer.setMaximumHeight(120)
        self.featured = QLineEdit(); self.playlists = QTextEdit(); self.playlists.setMaximumHeight(80)
        fields = (
            ("Channel name",self.name),("Handle (optional)",self.handle),("Content category",self.category),
            ("Languages",self.languages),("Channel format",self.format),("Main objective",self.goal),
            ("Target audience",self.audience),("Audience need / problem",self.problem),
            ("Content pillars (one per line)",self.pillars),("About description",self.description),
            ("Tagline",self.tagline),("Brand colours (hex, comma-separated)",self.colors),("Brand fonts",self.fonts),
            ("Profile image path",self.profile_image),("Banner image path",self.banner_image),
            ("Watermark path",self.watermark),("Channel trailer script",self.trailer),
            ("Featured video (optional)",self.featured),("Initial playlists (one per line)",self.playlists),
        )
        for label, widget in fields: form.addRow(label, widget)
        for field, label in ((self.profile_image,"Choose profile image"),(self.banner_image,"Choose banner image"),(self.watermark,"Choose watermark")):
            browse = QPushButton(label)
            browse.clicked.connect(lambda checked=False, target=field: self._browse_image(target))
            form.addRow("", browse)
        form.addRow(QLabel("LAUNCH CHECKLIST"))
        self.checks = {}
        for item in DEFAULT_CHECKLIST:
            check = QCheckBox(item); self.checks[item] = check; form.addRow(check)
        scroll.setWidget(host); root.addWidget(scroll, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Save).clicked.connect(self.save_profile)
        buttons.rejected.connect(self.reject); root.addWidget(buttons)
        self.refresh_channels()

    def _browse_image(self, field):
        filename, _ = QFileDialog.getOpenFileName(self, "Choose branding image", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if filename: field.setText(filename)

    def refresh_channels(self):
        selected = self.profile_path
        self.channel_list.clear()
        for profile in self.manager.list_channels():
            item = QListWidgetItem(profile["channel_name"])
            item.setData(Qt.ItemDataRole.UserRole, profile["profile_path"])
            self.channel_list.addItem(item)
            if profile["profile_path"] == selected: self.channel_list.setCurrentItem(item)
        if self.channel_list.count() and self.channel_list.currentRow() < 0: self.channel_list.setCurrentRow(0)
        elif not self.channel_list.count(): self._load_profile({})

    def _select_channel(self, current, previous):
        if current: self._load_profile(self.manager.load_channel(current.data(Qt.ItemDataRole.UserRole)))

    def _load_profile(self, profile):
        self.profile = profile; self.profile_path = profile.get("profile_path")
        for widget, key, default in (
            (self.name,"channel_name",""),(self.handle,"handle",""),(self.category,"category","Animation and storytelling"),
            (self.languages,"languages",["Telugu","English"]),(self.audience,"target_audience",""),
            (self.problem,"audience_problem",""),(self.tagline,"tagline",""),(self.colors,"brand_colors",["#111827","#F5B942","#FFFFFF"]),
            (self.fonts,"brand_fonts",""),(self.profile_image,"profile_image_path",""),(self.banner_image,"banner_image_path",""),
            (self.watermark,"watermark_path",""),(self.featured,"featured_video",""),
        ):
            value = profile.get(key, default)
            widget.setText(", ".join(value) if isinstance(value, list) else value)
        self.pillars.setPlainText("\n".join(profile.get("content_pillars", [])))
        self.description.setPlainText(profile.get("channel_description", ""))
        self.trailer.setPlainText(profile.get("trailer_script", ""))
        self.playlists.setPlainText("\n".join(profile.get("playlists", [])))
        self._set_combo(self.format, profile.get("channel_format", "faceless"))
        self._set_combo(self.goal, profile.get("goal", "long_term_monetized"))
        for label, check in self.checks.items(): check.setChecked(bool(profile.get("checklist", {}).get(label, False)))

    @staticmethod
    def _set_combo(combo, value):
        index = combo.findData(value); combo.setCurrentIndex(max(0, index))

    def create_channel(self):
        try:
            path = self.manager.create_channel("My Animation Channel")
            self.profile_path = str(path); self.refresh_channels()
            self._load_profile(self.manager.load_channel(path))
        except Exception as exc: QMessageBox.critical(self, "Channel profile failed", str(exc))

    def save_profile(self):
        if not self.profile_path:
            try:
                name = self.name.text().strip() or "My Animation Channel"
                path = self.manager.create_channel(name)
                self.profile_path = str(path)
            except Exception as exc:
                QMessageBox.critical(self, "Channel profile failed", str(exc))
                return
        updates = {
            "channel_name":self.name.text().strip() or "My Animation Channel",
            "handle":self.handle.text().strip(),
            "category":self.category.text().strip(),
            "languages":[x.strip() for x in self.languages.text().split(",") if x.strip()],
            "channel_format":self.format.currentData(),"goal":self.goal.currentData(),
            "target_audience":self.audience.text().strip(),"audience_problem":self.problem.text().strip(),
            "content_pillars":[x.strip() for x in self.pillars.toPlainText().splitlines() if x.strip()],
            "channel_description":self.description.toPlainText().strip(),"tagline":self.tagline.text().strip(),
            "brand_colors":[x.strip() for x in self.colors.text().split(",") if x.strip()],
            "brand_fonts":self.fonts.text().strip(),"profile_image_path":self.profile_image.text().strip(),
            "banner_image_path":self.banner_image.text().strip(),"watermark_path":self.watermark.text().strip(),
            "trailer_script":self.trailer.toPlainText().strip(),"featured_video":self.featured.text().strip(),
            "playlists":[x.strip() for x in self.playlists.toPlainText().splitlines() if x.strip()],
            "checklist":{label:check.isChecked() for label,check in self.checks.items()},
        }
        try:
            self.manager.save_channel(self.profile_path, updates)
            self.profile = self.manager.load_channel(self.profile_path)
            self.refresh_channels(); self._load_profile(self.profile)
            QMessageBox.information(self, "Channel profile saved", "Your channel setup profile is saved locally.")
        except Exception as exc: QMessageBox.warning(self, "Could not save channel profile", str(exc))

    def delete_channel(self):
        if not self.profile_path: return
        if QMessageBox.question(self, "Delete channel profile", "Delete this local profile and its folder? This does not delete a YouTube channel.") != QMessageBox.StandardButton.Yes: return
        try:
            self.manager.delete_channel(self.profile_path); self.profile_path = None; self.refresh_channels()
        except Exception as exc: QMessageBox.critical(self, "Delete failed", str(exc))
