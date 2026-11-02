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

if __name__ == "__main__":
    unittest.main()
