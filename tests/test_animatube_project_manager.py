import tempfile
import unittest
from pathlib import Path

from animatube.core.project_manager import ProjectManager
from animatube.core.project import load_project


class ProjectManagerTests(unittest.TestCase):
    def test_create_list_reopen_and_track_production_stages(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = ProjectManager(Path(directory) / "library")
            project_file = manager.create_project("My First Film")
            self.assertTrue(project_file.is_file())
            self.assertEqual(load_project(project_file).name, "My First Film")
            manager.update_stage(project_file, "script", "complete")
            manager.update_stage(project_file, "animation", "in_progress")
            entry = manager.list_projects()[0]
            self.assertEqual(entry["stages"]["script"], "complete")
            self.assertEqual(entry["stages"]["animation"], "in_progress")
            self.assertEqual(entry["scene_count"], 1)

    def test_rejects_invalid_stage_and_unsafe_names(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = ProjectManager(directory)
            with self.assertRaises(ValueError):
                manager.create_project("../escape")
            project_file = manager.create_project("Film")
            with self.assertRaises(ValueError):
                manager.update_stage(project_file, "script", "100 percent")

    def test_rename_preserves_project_and_archive_moves_folder(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = ProjectManager(Path(directory) / "library")
            project_file = manager.create_project("Before")
            renamed = manager.rename_project(project_file, "After")
            self.assertEqual(load_project(renamed).name, "After")
            archived = manager.archive_project(renamed)
            self.assertTrue((archived / "After.anima").is_file())
            self.assertEqual(manager.list_projects(), [])

    def test_versioned_exports_never_overwrite_previous_video(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = ProjectManager(Path(directory) / "library")
            project_file = manager.create_project("Film")
            rendered = Path(directory) / "render.mp4"
            rendered.write_bytes(b"first-render")
            first = manager.save_export_version(project_file, rendered)
            rendered.write_bytes(b"second-render")
            second = manager.save_export_version(project_file, rendered)
            self.assertEqual(first.name, "v001.mp4")
            self.assertEqual(second.name, "v002.mp4")
            self.assertEqual(first.read_bytes(), b"first-render")
            self.assertEqual(second.read_bytes(), b"second-render")
            self.assertTrue((second.parent / "v002.json").is_file())

    def test_storage_breakdown_counts_exports_and_assets_without_following_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manager = ProjectManager(root / "library")
            project_file = manager.create_project("Film")
            project_root = project_file.parent
            (project_root / "exports").mkdir()
            (project_root / "exports" / "v001.mp4").write_bytes(b"12345")
            (project_root / "assets").mkdir()
            (project_root / "assets" / "image.png").write_bytes(b"123")
            result = manager.storage_breakdown(project_file)
            self.assertEqual(result["exports"], 5)
            self.assertEqual(result["assets"], 3)
            self.assertGreater(manager.list_projects()[0]["storage_bytes"], 0)

    def test_delete_rejects_paths_outside_library(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = ProjectManager(Path(directory) / "library")
            outside = Path(directory) / "outside"
            outside.mkdir()
            with self.assertRaises(ValueError):
                manager.delete_project(outside / "outside.anima")


if __name__ == "__main__":
    unittest.main()
