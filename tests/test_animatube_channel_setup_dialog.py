import os
import tempfile
import unittest
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from animatube.core.channel_manager import ChannelManager
from animatube.ui.channel_setup_dialog import ChannelSetupDialog

class ChannelSetupDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_dialog_loads_saved_bilingual_faceless_profile(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = ChannelManager(directory)
            path = manager.create_channel("Telugu Story Studio")
            dialog = ChannelSetupDialog(directory)
            try:
                self.assertEqual(dialog.name.text(), "Telugu Story Studio")
                self.assertEqual(dialog.languages.text(), "Telugu, English")
                self.assertEqual(dialog.format.currentData(), "faceless")
                self.assertEqual(dialog.goal.currentData(), "long_term_monetized")
                self.assertEqual(len(dialog.checks), 10)
            finally:
                dialog.close()


    def test_dialog_defaults_when_empty_library(self):
        with tempfile.TemporaryDirectory() as directory:
            dialog = ChannelSetupDialog(directory)
            try:
                self.assertEqual(dialog.channel_list.count(), 0)
                self.assertEqual(dialog.category.text(), "Animation and storytelling")
                self.assertEqual(dialog.languages.text(), "Telugu, English")
                self.assertEqual(dialog.format.currentData(), "faceless")
                self.assertEqual(dialog.goal.currentData(), "long_term_monetized")
                self.assertEqual(len(dialog.checks), 10)
            finally:
                dialog.close()

    def test_dialog_save_from_empty_preserves_user_entered_name_and_fields(self):
        from unittest.mock import patch
        from PySide6.QtWidgets import QMessageBox
        with tempfile.TemporaryDirectory() as directory:
            dialog = ChannelSetupDialog(directory)
            try:
                dialog.name.setText("Telugu Kids Morals")
                dialog.handle.setText("@telugukids")
                dialog.category.setText("Animation and storytelling")
                with patch.object(QMessageBox, "information"), patch.object(QMessageBox, "warning"), patch.object(QMessageBox, "critical"):
                    dialog.save_profile()
                self.assertEqual(dialog.channel_list.count(), 1)
                self.assertEqual(dialog.name.text(), "Telugu Kids Morals")
                self.assertEqual(dialog.handle.text(), "@telugukids")
                loaded = dialog.manager.list_channels()[0]
                self.assertEqual(loaded["channel_name"], "Telugu Kids Morals")
                self.assertEqual(loaded["handle"], "@telugukids")
            finally:
                dialog.close()

    def test_desktop_toolbar_opens_channel_setup(self):
        from unittest.mock import patch, MagicMock
        from pathlib import Path
        from animatube.ui.main_window import MainWindow
        from PySide6.QtWidgets import QPushButton
        window = MainWindow()
        try:
            buttons = [b for b in window.findChildren(QPushButton) if b.text() == "Channel Setup"]
            self.assertEqual(len(buttons), 1)
            with patch("animatube.ui.main_window.ChannelSetupDialog") as MockDialog:
                mock_inst = MagicMock()
                MockDialog.return_value = mock_inst
                buttons[0].click()
                MockDialog.assert_called_once_with(Path.home() / "AnimaTube" / "Channels", window)
                mock_inst.exec.assert_called_once()
        finally:
            window.close()

if __name__ == "__main__":
    unittest.main()
