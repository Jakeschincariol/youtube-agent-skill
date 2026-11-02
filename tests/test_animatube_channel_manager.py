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
    def test_telugu_and_unicode_channel_name_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = ChannelManager(directory)
            path = manager.create_channel("తెలుగు కథల ప్రపంచం")
            data = manager.load_channel(path)
            self.assertEqual(data["channel_name"], "తెలుగు కథల ప్రపంచం")
            self.assertTrue(path.is_file())
            self.assertTrue(path.parent.name.startswith("channel-"))

    def test_reject_library_root_profile_path(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = ChannelManager(directory)
            with self.assertRaises(ValueError):
                manager.load_channel(Path(directory) / "channel-profile.json")

    def test_multiple_channels_managed_and_deleted_independently(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = ChannelManager(directory)
            p1 = manager.create_channel("Channel One")
            p2 = manager.create_channel("Channel Two")
            manager.save_channel(p1, {"handle": "@channelone"})
            manager.save_channel(p2, {"handle": "@channeltwo"})
            self.assertEqual(len(manager.list_channels()), 2)

            manager.delete_channel(p1)
            remaining = manager.list_channels()
            self.assertEqual(len(remaining), 1)
            self.assertEqual(remaining[0]["channel_name"], "Channel Two")
            self.assertTrue(p2.is_file())
            self.assertFalse(p1.is_file())

