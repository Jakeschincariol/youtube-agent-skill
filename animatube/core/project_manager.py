from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from animatube.core.models import Project
from animatube.core.project import load_project, save_project

MANIFEST_NAME = "animatube-project.json"
STAGES = ("script", "storyboard", "animation", "audio")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(data, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def _safe_size(root: Path) -> int:
    total = 0
    if not root.exists():
        return total
    for current, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if not (Path(current) / d).is_symlink()]
        for name in files:
            item = Path(current) / name
            try:
                if not item.is_symlink():
                    total += item.stat().st_size
            except OSError:
                continue
    return total


def _manifest(project_dir: Path) -> dict[str, Any]:
    path = project_dir / MANIFEST_NAME
    if path.exists():
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            if value.get("schema_version") == 1:
                return value
        except (OSError, ValueError, TypeError):
            pass
    anima = next(project_dir.glob("*.anima"), None)
    return {
        "schema_version": 1,
        "id": uuid4().hex,
        "name": anima.stem if anima else project_dir.name,
        "created_at": _now(),
        "updated_at": _now(),
        "stages": {stage: "not_started" for stage in STAGES},
        "notes": "",
    }


class ProjectManager:
    """Local project library. Each project owns its editable source and generated outputs."""

    def __init__(self, library_dir: str | Path):
        self.library_dir = Path(library_dir).expanduser().resolve()
        self.library_dir.mkdir(parents=True, exist_ok=True)

    def list_projects(self) -> list[dict[str, Any]]:
        projects = []
        for folder in self.library_dir.iterdir():
            if not folder.is_dir() or folder.is_symlink():
                continue
            anima = next(folder.glob("*.anima"), None)
            if anima is None:
                continue
            manifest = _manifest(folder)
            try:
                project = load_project(anima)
                scenes = len(project.scenes)
            except (OSError, ValueError):
                scenes = 0
            manifest.update({
                "directory": str(folder),
                "project_file": str(anima),
                "scene_count": scenes,
                "storage_bytes": _safe_size(folder),
                "exports": len(list((folder / "exports").glob("*.mp4"))) if (folder / "exports").is_dir() else 0,
            })
            projects.append(manifest)
        return sorted(projects, key=lambda item: item.get("updated_at", ""), reverse=True)

    def create_project(self, name: str, project: Project | None = None) -> Path:
        clean = " ".join(name.strip().split())
        if not clean or clean in {".", ".."} or any(c in clean for c in "/\\"):
            raise ValueError("Enter a valid project name.")
        folder = self.library_dir / f"{clean[:64]}-{uuid4().hex[:8]}"
        folder.mkdir(parents=True, exist_ok=False)
        try:
            model = project or Project(name=clean)
            model.name = clean
            save_project(model, folder / f"{clean[:64]}.anima")
            manifest = {
                "schema_version": 1, "id": uuid4().hex, "name": clean,
                "created_at": _now(), "updated_at": _now(),
                "stages": {stage: "not_started" for stage in STAGES}, "notes": "",
            }
            _atomic_json(folder / MANIFEST_NAME, manifest)
        except Exception:
            shutil.rmtree(folder, ignore_errors=True)
            raise
        return folder / f"{clean[:64]}.anima"

    def update_stage(self, project_file: str | Path, stage: str, status: str) -> None:
        if stage not in STAGES or status not in {"not_started", "in_progress", "complete", "needs_attention"}:
            raise ValueError("Unsupported production stage or status.")
        folder = Path(project_file).expanduser().resolve().parent
        manifest = _manifest(folder)
        manifest["stages"][stage] = status
        manifest["updated_at"] = _now()
        _atomic_json(folder / MANIFEST_NAME, manifest)

    def rename_project(self, project_file: str | Path, new_name: str) -> Path:
        clean = " ".join(new_name.strip().split())
        if not clean or any(c in clean for c in "/\\") or clean in {".", ".."}:
            raise ValueError("Enter a valid project name.")
        source = Path(project_file).expanduser().resolve()
        folder = source.parent
        target = folder / f"{clean[:64]}.anima"
        if target.exists() and target != source:
            raise FileExistsError(target)
        project = load_project(source)
        project.name = clean
        save_project(project, target)
        if source != target:
            source.unlink()
        manifest = _manifest(folder)
        manifest.update({"name": clean, "updated_at": _now()})
        _atomic_json(folder / MANIFEST_NAME, manifest)
        return target

    def archive_project(self, project_file: str | Path) -> Path:
        source = Path(project_file).expanduser().resolve().parent
        archive = self.library_dir / "Archive"
        archive.mkdir(exist_ok=True)
        target = archive / source.name
        if target.exists():
            target = archive / f"{source.name}-{uuid4().hex[:6]}"
        return Path(shutil.move(str(source), str(target)))

    def delete_project(self, project_file: str | Path) -> None:
        folder = Path(project_file).expanduser().resolve().parent
        if folder == self.library_dir or self.library_dir not in folder.parents:
            raise ValueError("Project is outside this library.")
        shutil.rmtree(folder)

    def storage_breakdown(self, project_file: str | Path) -> dict[str, int]:
        root = Path(project_file).expanduser().resolve().parent
        parts = {"assets": 0, "audio": 0, "scene_cache": 0, "exports": 0, "other": 0}
        for current, dirs, files in os.walk(root, followlinks=False):
            dirs[:] = [d for d in dirs if not (Path(current) / d).is_symlink()]
            rel = Path(current).relative_to(root)
            bucket = "other"
            if "exports" in rel.parts: bucket = "exports"
            elif "audio" in rel.parts: bucket = "audio"
            elif "assets" in rel.parts or any(part.endswith("_assets") for part in rel.parts): bucket = "assets"
            elif any("render_cache" in part or "scene_cache" in part for part in rel.parts): bucket = "scene_cache"
            for name in files:
                item = Path(current) / name
                try:
                    if not item.is_symlink(): parts[bucket] += item.stat().st_size
                except OSError:
                    pass
        return parts

    def save_export_version(self, project_file: str | Path, rendered_video: str | Path) -> Path:
        source = Path(rendered_video).expanduser().resolve()
        if not source.is_file() or source.stat().st_size == 0:
            raise FileNotFoundError("The rendered MP4 is missing or empty.")
        root = Path(project_file).expanduser().resolve().parent
        exports = root / "exports"
        exports.mkdir(parents=True, exist_ok=True)
        existing = [int(p.stem[1:]) for p in exports.glob("v*.mp4") if p.stem[1:].isdigit()]
        version = max(existing, default=0) + 1
        target = exports / f"v{version:03d}.mp4"
        shutil.copy2(source, target)
        hasher = hashlib.sha256()
        with target.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                hasher.update(chunk)
        digest = hasher.hexdigest()
        metadata = {"version": target.stem, "file": target.name, "size_bytes": target.stat().st_size,
                    "sha256": digest, "created_at": _now()}
        _atomic_json(exports / f"{target.stem}.json", metadata)
        manifest = _manifest(root)
        manifest["updated_at"] = _now()
        _atomic_json(root / MANIFEST_NAME, manifest)
        return target

    def scene_preview(self, project_file: str | Path, scene_index: int, destination: str | Path, frame: int = 0) -> Path:
        from animatube.export.renderer import render_frame
        from animatube.export.compiler import _ensure_qapp
        project = load_project(project_file)
        if not 0 <= scene_index < len(project.scenes):
            raise IndexError("Scene index is outside this project.")
        _ensure_qapp()
        scene = project.scenes[scene_index]
        image = render_frame(project, scene, max(0, min(frame, scene.duration_frames - 1)), min(project.width, 960), min(project.height, 540))
        target = Path(destination).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        if not image.save(str(target)):
            raise OSError(f"Could not save scene preview to {target}")
        return target
