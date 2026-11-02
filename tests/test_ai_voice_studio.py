import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox

from animatube.ai.mock_providers import MockVoiceProvider
from animatube.ai.voice_studio import (
    CharacterVoiceProfile,
    DialogueLine,
    DialogueManager,
    DEFAULT_CHARACTER_PROFILES,
)
from animatube.core.models import Project, Scene
from animatube.ui.audio_studio_dialog import AudioStudioDialog


class AIVoiceStudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_default_character_profiles(self):
        names = [p.character_name for p in DEFAULT_CHARACTER_PROFILES]
        self.assertIn("Aarav", names)
        self.assertIn("Mia", names)
        self.assertIn("Ellie", names)
        self.assertIn("Gigi", names)
        self.assertIn("Bobo", names)
        self.assertIn("Twinkle", names)
        self.assertIn("Narrator", names)

        aarav = next(p for p in DEFAULT_CHARACTER_PROFILES if p.character_name == "Aarav")
        prompt = aarav.to_prompt("Look at that bright star!")
        self.assertEqual(prompt.voice_id, "aarav_boy")
        self.assertEqual(prompt.character_name, "Aarav")
        self.assertEqual(prompt.rate, "+5%")

    def test_dialogue_manager_single_line(self):
        provider = MockVoiceProvider()
        dm = DialogueManager(provider=provider)
        line = DialogueLine(character_name="Mia", text="Let's sing a happy song together!")

        with tempfile.TemporaryDirectory() as tmp_dir:
            res_line = dm.generate_dialogue_line(line, tmp_dir)
            self.assertTrue(Path(res_line.audio_path).is_file())
            self.assertGreater(res_line.duration_seconds, 0.5)

    def test_dialogue_manager_multi_character_conversation(self):
        provider = MockVoiceProvider()
        dm = DialogueManager(provider=provider)

        lines = [
            DialogueLine(character_name="Aarav", text="Hi Mia! Look at Twinkle in the sky!"),
            DialogueLine(character_name="Mia", text="Hi Aarav! Twinkle is glowing so brightly!"),
            DialogueLine(character_name="Twinkle", text="Welcome Little Dreamers! Shine your light!"),
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "dialogue_scene1.wav"
            prog_updates = []
            res_path = dm.generate_conversation(
                lines,
                out_file,
                progress_callback=lambda p, msg: prog_updates.append((p, msg)),
            )

            self.assertTrue(res_path.is_file())
            self.assertEqual(res_path, out_file)
            self.assertGreater(res_path.stat().st_size, 0)
            self.assertGreaterEqual(len(prog_updates), 3)

    def test_audio_studio_dialog_dialogue_tab_ui(self):
        project = Project(name="Preschool Video")
        project.scenes = [Scene(name="Intro", duration_frames=120)]

        with tempfile.TemporaryDirectory() as tmp_dir:
            proj_file = str(Path(tmp_dir) / "project.anima")
            dialog = AudioStudioDialog(project, project_file=proj_file)
            try:
                # Check Dialogue Tab exists
                tab_names = [dialog.tabs.tabText(i) for i in range(dialog.tabs.count())]
                self.assertIn("Character Dialogue", tab_names)

                # Add a dialogue line
                dialog.combo_dialogue_char.setCurrentIndex(0)  # Aarav
                dialog.edit_line_text.setText("Adventure awaits, Little Dreamers!")
                dialog._add_dialogue_line()

                self.assertEqual(len(dialog.dialogue_lines), 1)
                self.assertEqual(dialog.table_dialogue.rowCount(), 1)
                self.assertEqual(dialog.dialogue_lines[0].character_name, "Aarav")

                # Synthesize dialogue
                with patch.object(QMessageBox, "information"), patch.object(QMessageBox, "warning"), patch.object(QMessageBox, "critical"):
                    dialog._generate_dialogue_audio()

                self.assertTrue(dialog.btn_attach_dialogue.isEnabled())
                self.assertTrue(dialog.btn_export_dialogue.isEnabled())
                self.assertTrue(Path(dialog.last_dialogue_audio).is_file())

                # Attach to scene
                with patch.object(QMessageBox, "information"):
                    dialog._attach_dialogue_to_scene()

                # Verify scene frames adjusted to speech duration
                self.assertGreater(project.scenes[0].duration_frames, 0)

            finally:
                dialog.close()


if __name__ == "__main__":
    unittest.main()
