from __future__ import annotations
import json, os, re, shutil, tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

SCHEMA_VERSION = 1
DEFAULT_CHECKLIST = (
    "Choose a channel name and verify handle availability on YouTube",
    "Write the channel About description",
    "Create and review the profile picture",
    "Create and review the channel banner",
    "Prepare a watermark and brand kit",
    "Write the channel trailer script",
    "Choose the featured video and Home tab sections",
    "Create initial playlists for the content pillars",
    "Review audience, language and content positioning",
    "Complete YouTube channel setup manually and verify it in YouTube Studio",
)
CHANNEL_FORMATS = {"faceless", "own_face_voice", "ai_animation_voiceover", "hybrid"}
CHANNEL_GOALS = {"long_term_monetized", "personal_brand", "education_audience", "storytelling_entertainment"}

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return slug[:48] if slug else "channel"

def _atomic_write(path: Path, data: dict[str, Any]) -> None:
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
        try: os.unlink(temp_name)
        except OSError: pass
        raise

def new_channel_profile(name: str = "My Animation Channel") -> dict[str, Any]:
    clean = " ".join(name.strip().split())
    if not clean or len(clean) > 100:
        raise ValueError("Channel name must contain 1–100 characters.")
    return {
        "schema_version": SCHEMA_VERSION, "id": uuid4().hex,
        "created_at": _now(), "updated_at": _now(), "channel_name": clean,
        "handle": "", "category": "Animation and storytelling",
        "languages": ["Telugu", "English"], "channel_format": "faceless",
        "goal": "long_term_monetized", "target_audience": "", "audience_problem": "",
        "content_pillars": ["Animated stories", "Telugu moral stories", "Bilingual storytelling"],
        "channel_description": "", "tagline": "",
        "brand_colors": ["#111827", "#F5B942", "#FFFFFF"], "brand_fonts": "",
        "profile_image_path": "", "banner_image_path": "", "watermark_path": "",
        "trailer_script": "", "featured_video": "", "playlists": [],
        "checklist": {item: False for item in DEFAULT_CHECKLIST},
    }

class ChannelManager:
    """Local-first channel profiles; Google credentials and publishing are out of scope."""
    def __init__(self, library_dir: str | Path):
        self.library_dir = Path(library_dir).expanduser().resolve()
        self.library_dir.mkdir(parents=True, exist_ok=True)

    def list_channels(self) -> list[dict[str, Any]]:
        items = []
        for path in self.library_dir.glob("*/channel-profile.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if data.get("schema_version") == SCHEMA_VERSION and data.get("id"):
                    data["profile_path"] = str(path)
                    items.append(data)
            except (OSError, ValueError, TypeError):
                continue
        return sorted(items, key=lambda item: item.get("updated_at", ""), reverse=True)

    def create_channel(self, name: str) -> Path:
        profile = new_channel_profile(name)
        folder = self.library_dir / f"{_slug(profile['channel_name'])}-{profile['id'][:8]}"
        folder.mkdir(parents=True, exist_ok=False)
        path = folder / "channel-profile.json"
        try: _atomic_write(path, profile)
        except Exception:
            path.unlink(missing_ok=True)
            folder.rmdir()
            raise
        return path

    def load_channel(self, profile_path: str | Path) -> dict[str, Any]:
        path = Path(profile_path).expanduser().resolve()
        if self.library_dir not in path.parents or path.parent == self.library_dir or path.name != "channel-profile.json":
            raise ValueError("Channel profile must be inside the AnimaTube channel library.")
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("Unsupported channel profile version.")
        data["profile_path"] = str(path)
        return data

    def save_channel(self, profile_path: str | Path, updates: dict[str, Any]) -> Path:
        path = Path(profile_path).expanduser().resolve()
        current = self.load_channel(path)
        current.pop("profile_path", None)
        allowed = set(new_channel_profile().keys()) - {"schema_version", "id", "created_at", "updated_at"}
        for key, value in updates.items():
            if key not in allowed:
                raise ValueError(f"Unsupported channel profile field: {key}")
            current[key] = value
        name = str(current.get("channel_name", "")).strip()
        if not name or len(name) > 100:
            raise ValueError("Channel name must contain 1–100 characters.")
        handle = str(current.get("handle", "")).strip()
        if handle and not re.fullmatch(r"@[A-Za-z0-9._-]{3,30}", handle):
            raise ValueError("Handle must start with @ and contain 3–30 valid characters.")
        if current.get("channel_format") not in CHANNEL_FORMATS or current.get("goal") not in CHANNEL_GOALS:
            raise ValueError("Choose a supported channel format and goal.")
        if not isinstance(current.get("checklist"), dict) or set(current["checklist"]) != set(DEFAULT_CHECKLIST):
            raise ValueError("Channel checklist is invalid.")
        current["updated_at"] = _now()
        _atomic_write(path, current)
        return path

    def update_checklist(self, profile_path: str | Path, item: str, completed: bool) -> Path:
        current = self.load_channel(profile_path)
        if item not in current.get("checklist", {}):
            raise ValueError("Unknown channel setup checklist item.")
        current["checklist"][item] = bool(completed)
        return self.save_channel(profile_path, {"checklist": current["checklist"]})

    def delete_channel(self, profile_path: str | Path) -> None:
        path = Path(profile_path).expanduser().resolve()
        self.load_channel(path)
        shutil.rmtree(path.parent)
