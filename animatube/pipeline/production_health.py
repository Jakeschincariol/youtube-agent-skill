from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import urllib.request
from typing import Any

CHARACTERS = ("aarav", "mia", "ellie", "gigi", "bobo", "twinkle")
MODULES = ("PIL", "edge_tts", "PySide6", "imageio_ffmpeg")
VIDEO_SUFFIXES = {".mp4", ".mov", ".mkv", ".webm", ".avi"}


@dataclass(frozen=True)
class HealthCheck:
    name: str
    status: str
    details: str


class ProductionHealthChecker:
    """Read-only preflight checks for the Little Dreamers production workspace."""

    def __init__(self, repo_root: str | Path, *, require_ollama: bool = False,
                 check_exports: bool = False, ollama_url: str | None = None) -> None:
        self.root = Path(repo_root).resolve()
        self.require_ollama = require_ollama
        self.check_exports = check_exports
        self.ollama_url = (ollama_url or os.environ.get("OLLAMA_HOST") or
                           "http://127.0.0.1:11434").rstrip("/")
        self.checks: list[HealthCheck] = []

    @property
    def passed(self) -> bool:
        return all(check.status != "FAIL" for check in self.checks)

    def add(self, name: str, status: str, details: str) -> None:
        self.checks.append(HealthCheck(name, status, details))

    def check_dependencies(self) -> None:
        missing = []
        for module in MODULES:
            try:
                if importlib.util.find_spec(module) is None:
                    missing.append(module)
            except (ImportError, ValueError):
                missing.append(module)
        self.add("Python dependencies", "FAIL" if missing else "PASS",
                 "Missing modules: " + ", ".join(missing) if missing else
                 "Pillow, Edge TTS, PySide6 and imageio-ffmpeg are importable")
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            try:
                import imageio_ffmpeg
                ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
            except Exception:
                ffmpeg = None
        self.add("FFmpeg", "PASS" if ffmpeg and Path(ffmpeg).is_file() else "FAIL",
                 f"Available: {ffmpeg}" if ffmpeg else "FFmpeg executable not found")

    def _image_ok(self, path: Path) -> tuple[bool, str]:
        if not path.is_file() or path.stat().st_size == 0:
            return False, "missing or empty"
        try:
            from PIL import Image
            with Image.open(path) as image:
                image.verify()
            with Image.open(path) as image:
                return True, f"{image.width}x{image.height}, {path.stat().st_size} bytes"
        except Exception as exc:
            return False, f"image decode failed: {exc}"

    def check_character_assets(self) -> None:
        missing, invalid = [], []
        for character in CHARACTERS:
            paths = (
                self.root / "little-dreamers/characters" / character / f"{character}_reference_sheet.png",
                self.root / "little-dreamers/flow_ready" / f"{character}_flow_anchor.png",
            )
            for path in paths:
                if not path.is_file():
                    missing.append(path.relative_to(self.root).as_posix())
                else:
                    ok, detail = self._image_ok(path)
                    if not ok:
                        invalid.append(f"{path.relative_to(self.root).as_posix()}: {detail}")
        problems = []
        if missing:
            problems.append("missing: " + ", ".join(missing))
        if invalid:
            problems.append("invalid: " + "; ".join(invalid))
        self.add("Approved character references", "FAIL" if problems else "PASS",
                 " | ".join(problems) if problems else "All 12 reference-sheet and Flow-anchor images decode successfully")

    def check_storyboard(self) -> None:
        path = self.root / "little-dreamers/episodes/ep01_magic_abc_train/storyboard.json"
        if not path.is_file():
            self.add("Episode 1 storyboard", "FAIL", f"Missing: {path}")
            return
        try:
            data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            self.add("Episode 1 storyboard", "FAIL", f"Invalid JSON: {exc}")
            return
        errors: list[str] = []
        scenes = data.get("scenes")
        if not isinstance(scenes, list) or not scenes:
            self.add("Episode 1 storyboard", "FAIL", "No scenes found")
            return
        if data.get("resolution") != [1920, 1080]:
            errors.append("resolution must be 1920x1080")
        if data.get("fps") != 24:
            errors.append("frame rate must be 24 fps")
        if len(scenes) != 11:
            errors.append(f"expected 11 scenes, found {len(scenes)}")
        known = {name.title() for name in CHARACTERS}
        ids: set[str] = set()
        total_duration = 0.0
        total_shots = 0
        refs: set[str] = set()
        for number, scene in enumerate(scenes, 1):
            if scene.get("scene_number") != number:
                errors.append(f"scene numbering gap at {number}")
            duration = scene.get("duration_seconds")
            shots = scene.get("shots")
            if not isinstance(duration, (int, float)) or duration <= 0:
                errors.append(f"scene {number} has invalid duration")
                continue
            if not isinstance(shots, list) or not shots:
                errors.append(f"scene {number} has no shots")
                continue
            total_duration += float(duration)
            shot_duration = 0.0
            for shot in shots:
                total_shots += 1
                shot_id = shot.get("shot_id")
                if not shot_id or shot_id in ids:
                    errors.append(f"missing or duplicate shot_id: {shot_id!r}")
                ids.add(shot_id)
                seconds = shot.get("duration_seconds")
                if not isinstance(seconds, (int, float)) or seconds <= 0:
                    errors.append(f"{shot_id or 'unnamed shot'} has invalid duration")
                else:
                    shot_duration += float(seconds)
                for character in shot.get("characters", []):
                    if character not in known:
                        errors.append(f"{shot_id}: unapproved character {character}")
                refs.update(shot.get("character_references", []))
            if abs(shot_duration - float(duration)) > 0.05:
                errors.append(f"scene {number} shot timings do not equal scene duration")
        if abs(total_duration - float(data.get("total_duration_seconds", -1))) > 0.05:
            errors.append("episode duration metadata does not equal scene total")
        if total_shots != data.get("total_shots_count"):
            errors.append("shot-count metadata does not equal actual shot count")
        for ref in sorted(refs):
            if not (self.root / ref).is_file():
                errors.append(f"missing referenced character asset: {ref}")
        self.add("Episode 1 storyboard", "FAIL" if errors else "PASS",
                 "; ".join(errors[:12]) if errors else
                 f"{len(scenes)} scenes, {total_shots} unique shots, {total_duration:g}s, 1920x1080 @ 24fps; timings and asset references valid")

    def check_ollama(self) -> None:
        url = f"{self.ollama_url}/api/tags"
        try:
            request = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(request, timeout=1.5) as response:
                data = json.loads(response.read().decode("utf-8"))
            names = [item.get("name", "") for item in data.get("models", [])]
            model = os.environ.get("OLLAMA_MODEL", "").strip()
            missing = bool(model) and not any(model == name or model + ":latest" == name for name in names)
            if missing:
                self.add("Ollama", "FAIL" if self.require_ollama else "WARN",
                         f"Server reachable, but configured model {model!r} is not installed")
            else:
                self.add("Ollama", "PASS", "Local server reachable" +
                         (f"; models: {', '.join(names)}" if names else "; no models listed"))
        except Exception as exc:
            self.add("Ollama", "FAIL" if self.require_ollama else "WARN",
                     f"Not reachable at {url}: {exc}")

    def check_rendered_exports(self) -> None:
        folder = self.root / "little-dreamers/episodes/ep01_magic_abc_train/exports"
        if not folder.is_dir():
            self.add("Episode exports", "WARN", "Exports directory not created yet")
            return
        videos = [p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in VIDEO_SUFFIXES]
        if not videos:
            self.add("Episode exports", "WARN", "No rendered videos found; decode validation deferred")
            return
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            try:
                import imageio_ffmpeg
                ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
            except Exception:
                ffmpeg = None
        if not ffmpeg:
            self.add("Episode exports", "FAIL", "FFmpeg unavailable for render decoding")
            return
        failures = []
        for video in videos:
            if video.stat().st_size == 0:
                failures.append(f"{video.name}: empty")
                continue
            try:
                result = subprocess.run([ffmpeg, "-v", "error", "-i", str(video),
                                         "-f", "null", "-"], capture_output=True,
                                        text=True, timeout=180)
                if result.returncode:
                    failures.append(f"{video.name}: {result.stderr.strip()[:200] or 'decode failed'}")
            except (OSError, subprocess.TimeoutExpired) as exc:
                failures.append(f"{video.name}: {exc}")
        self.add("Episode exports", "FAIL" if failures else "PASS",
                 "; ".join(failures[:8]) if failures else f"FFmpeg decoded all {len(videos)} rendered video(s)")

    def run(self) -> list[HealthCheck]:
        self.checks = []
        if not self.root.is_dir():
            self.add("Repository root", "FAIL", f"Directory not found: {self.root}")
            return self.checks
        self.add("Repository root", "PASS", str(self.root))
        self.check_dependencies()
        self.check_character_assets()
        self.check_storyboard()
        self.check_ollama()
        if self.check_exports:
            self.check_rendered_exports()
        return self.checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Little Dreamers production-readiness preflight")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--require-ollama", action="store_true")
    parser.add_argument("--check-exports", action="store_true")
    parser.add_argument("--ollama-url")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    checker = ProductionHealthChecker(args.repo_root, require_ollama=args.require_ollama,
                                      check_exports=args.check_exports, ollama_url=args.ollama_url)
    checks = checker.run()
    if args.json:
        print(json.dumps({"passed": checker.passed, "checks": [asdict(c) for c in checks]}, indent=2))
    else:
        print("LITTLE DREAMERS — PRODUCTION HEALTH CHECK")
        for check in checks:
            print(f"[{check.status}] {check.name}: {check.details}")
        passed = sum(c.status == "PASS" for c in checks)
        print(f"\nRESULT: {'PASS' if checker.passed else 'FAIL'} ({passed}/{len(checks)} passed; WARN is non-blocking)")
    return 0 if checker.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
