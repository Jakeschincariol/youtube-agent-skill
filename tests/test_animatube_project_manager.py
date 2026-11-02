import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from pathlib import Path

from animatube.core.project_manager import ProjectManager
from animatube.core.project import load_project
from animatube.core.models import Project
from animatube.export.compiler import CompilationOptions, ProbeResult, SceneClip, compile_scenes


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


    def test_interrupted_render_cache_reuses_completed_scene_on_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "scene.png"
            image.write_bytes(b"image-fixture")
            project = Project()
            project.path = str(root / "film.anima")
            destination = root / "final.mp4"
            calls = []

            def fake_run(command, **kwargs):
                calls.append(command)
                Path(command[-1]).write_bytes(b"valid-mp4-fixture")
                return SimpleNamespace(returncode=0, stderr="", stdout="")

            probe = ProbeResult(32, 32, 1.0, "h264", 24.0, True, {})
            options = CompilationOptions(width=32, height=32, fps=24, ffmpeg_path="ffmpeg")
            with patch("animatube.export.compiler.subprocess.run", side_effect=fake_run), \
                 patch("animatube.export.compiler.probe_video", return_value=probe):
                compile_scenes([SceneClip(source=image, duration=1)], destination,
                               options=options, project_ref=project)
                first_call_count = len(calls)
                compile_scenes([SceneClip(source=image, duration=1)], destination,
                               options=options, project_ref=project)

            self.assertEqual(first_call_count, 2)
            self.assertEqual(len(calls), 3)
            self.assertTrue((root / ".animatube_render_cache" / "checkpoint.json").is_file())

    def test_delete_rejects_paths_outside_library(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = ProjectManager(Path(directory) / "library")
            outside = Path(directory) / "outside"
            outside.mkdir()
            with self.assertRaises(ValueError):
                manager.delete_project(outside / "outside.anima")


if __name__ == "__main__":
    unittest.main()
