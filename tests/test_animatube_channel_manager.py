import tempfile
import unittest
from pathlib import Path
from animatube.core.channel_manager import ChannelManager, DEFAULT_CHECKLIST, new_channel_profile

class ChannelManagerTests(unittest.TestCase):
    def test_defaults_match_requested_channel_direction(self):
        profile = new_channel_profile()
        self.assertEqual(profile["category"], "Animation and storytelling")
        self.assertEqual(profile["languages"], ["Telugu", "English"])
        self.assertEqual(profile["channel_format"], "faceless")
        self.assertEqual(profile["goal"], "long_term_monetized")
        self.assertEqual(len(profile["checklist"]), len(DEFAULT_CHECKLIST))

    def test_create_save_reload_and_preserve_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = ChannelManager(directory); path = manager.create_channel("Telugu Story World")
            original = manager.load_channel(path)
            manager.save_channel(path, {"handle":"@telugustoryworld","target_audience":"Telugu-speaking families","content_pillars":["Folktales","Original animation"]})
            restored = manager.load_channel(path)
            self.assertEqual(restored["id"], original["id"])
            self.assertEqual(restored["handle"], "@telugustoryworld")
            self.assertEqual(len(manager.list_channels()), 1)

    def test_checklist_persists(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = ChannelManager(directory); path = manager.create_channel("Stories")
            manager.update_checklist(path, DEFAULT_CHECKLIST[0], True)
            self.assertTrue(manager.load_channel(path)["checklist"][DEFAULT_CHECKLIST[0]])

    def test_reject_invalid_handle_and_unknown_secret_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = ChannelManager(directory); path = manager.create_channel("Stories")
            with self.assertRaises(ValueError): manager.save_channel(path, {"handle":"bad handle"})
            with self.assertRaises(ValueError): manager.save_channel(path, {"oauth_token":"must-not-be-stored"})

    def test_reject_path_escape_and_delete_profile(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = ChannelManager(directory)
            with self.assertRaises(ValueError): manager.load_channel(Path(directory).parent / "outside" / "channel-profile.json")
            path = manager.create_channel("Stories"); manager.delete_channel(path)
            self.assertEqual(manager.list_channels(), [])
