from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

from animatube.core.models import Project


def save_project(project: Project, destination: str | Path) -> None:
    target = Path(destination).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    asset_dir = target.parent / f"{target.stem}_assets"
    payload = project.to_dict()

    # Copy assets into a project-owned folder; never mutate the caller's model until
    # the JSON file has been written successfully.
    layer_lookup = {layer.id: layer for scene in project.scenes for layer in scene.layers}
    copied: dict[str, str] = {}
    for scene_data, scene in zip(payload["scenes"], project.scenes):
        for layer_data, layer in zip(scene_data["layers"], scene.layers):
            if layer.kind != "image" or not layer.asset_path:
                continue
            source = project.resolve_asset(layer.asset_path)
            if not source.is_file():
                raise FileNotFoundError(f"Image asset not found: {source}")
            digest = hashlib.sha256(source.read_bytes()).hexdigest()[:12]
            destination_asset = asset_dir / f"{digest}_{source.name}"
            if source.resolve() != destination_asset.resolve():
                asset_dir.mkdir(parents=True, exist_ok=True)
                if not destination_asset.exists():
                    shutil.copy2(source, destination_asset)
            layer_data["asset_path"] = str(destination_asset.relative_to(target.parent))
            copied[layer.id] = layer_data["asset_path"]

    fd, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, target)
    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise

    for layer_id, relative_path in copied.items():
        layer_lookup[layer_id].asset_path = relative_path
    project.path = str(target)


def load_project(source: str | Path) -> Project:
    path = Path(source).expanduser().resolve()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not load AnimaTube project: {exc}") from exc
    project = Project.from_dict(raw)
    project.path = str(path)
    return project
