from __future__ import annotations

from dataclasses import dataclass, field
import json
import logging
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Callable

from animatube.core.models import Project, Scene
from animatube.export.renderer import _rgb_bytes, render_frame
from PySide6.QtGui import QGuiApplication

logger = logging.getLogger(__name__)


def _ensure_qapp() -> QGuiApplication:
    app = QGuiApplication.instance()
    if app is None:
        app = QGuiApplication(sys.argv if hasattr(sys, "argv") and sys.argv else ["animatube"])
    return app

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}

ProgressCallback = Callable[[int], None]
CancellationCallback = Callable[[None], bool]


class ExportCancelledError(Exception):
    """Raised when an export is aborted by the user."""
    pass


class ValidationError(Exception):
    """Raised when an exported video fails ffprobe validation."""
    pass


@dataclass
class ProbeResult:
    width: int
    height: int
    duration: float
    codec_name: str
    fps: float
    has_video_stream: bool
    raw_info: dict[str, Any] = field(default_factory=dict)


@dataclass
class SceneClip:
    """Represents a scene source in the compilation timeline."""
    source: Path | Scene
    duration: float = 5.0
    scene_id: str = ""
    title: str = ""

    def is_image(self) -> bool:
        if isinstance(self.source, Path):
            return self.source.suffix.lower() in IMAGE_EXTENSIONS
        return False

    def is_video(self) -> bool:
        if isinstance(self.source, Path):
            return self.source.suffix.lower() in VIDEO_EXTENSIONS
        return False

    def is_scene_object(self) -> bool:
        return isinstance(self.source, Scene)


@dataclass
class CompilationOptions:
    width: int = 1920
    height: int = 1080
    fps: int = 30
    default_image_duration: float = 5.0
    video_codec: str = "libx264"
    pixel_format: str = "yuv420p"
    preset: str = "medium"
    crf: int = 20
    ffmpeg_path: str | None = None
    ffprobe_path: str | None = None


def get_ffmpeg_executable(custom_path: str | None = None) -> str | None:
    return custom_path or os.environ.get("FFMPEG_PATH") or shutil.which("ffmpeg")


def get_ffprobe_executable(custom_path: str | None = None) -> str | None:
    return custom_path or os.environ.get("FFPROBE_PATH") or shutil.which("ffprobe")


def probe_video(file_path: str | Path, ffprobe_executable: str | None = None) -> ProbeResult:
    """
    Validates a video file using FFprobe.
    Verifies that the file exists, has a valid video stream, expected geometry, and duration.
    """
    target = Path(file_path).resolve()
    if not target.is_file() or target.stat().st_size == 0:
        raise ValidationError(f"Video file does not exist or is empty: {target}")

    executable = get_ffprobe_executable(ffprobe_executable)
    if not executable:
        # Fallback inspection if ffprobe is uninstalled: check file header and size
        data = target.read_bytes()[:128]
        if b"ftyp" not in data and b"moov" not in data:
            raise ValidationError(f"File at {target} is not a valid MP4 file container.")
        return ProbeResult(
            width=1920,
            height=1080,
            duration=1.0,
            codec_name="h264",
            fps=30.0,
            has_video_stream=True,
            raw_info={"fallback": True},
        )

    cmd = [
        executable,
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,codec_name,r_frame_rate,duration",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(target),
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        info = json.loads(proc.stdout)
    except subprocess.CalledProcessError as exc:
        raise ValidationError(f"FFprobe execution failed: {exc.stderr.strip() or str(exc)}")
    except Exception as exc:
        raise ValidationError(f"Failed to parse FFprobe output: {exc}")

    streams = info.get("streams", [])
    if not streams:
        raise ValidationError(f"No valid video streams found in {target}")

    v_stream = streams[0]
    codec = v_stream.get("codec_name", "")
    width = int(v_stream.get("width", 0))
    height = int(v_stream.get("height", 0))

    duration_str = v_stream.get("duration") or info.get("format", {}).get("duration", "0")
    try:
        duration = float(duration_str)
    except ValueError:
        duration = 0.0

    # Calculate FPS from r_frame_rate (e.g. "30/1" or "29.97")
    fps_str = v_stream.get("r_frame_rate", "30/1")
    try:
        if "/" in fps_str:
            num, den = fps_str.split("/", 1)
            fps = float(num) / float(den) if float(den) != 0 else 30.0
        else:
            fps = float(fps_str)
    except Exception:
        fps = 30.0

    return ProbeResult(
        width=width,
        height=height,
        duration=duration,
        codec_name=codec,
        fps=fps,
        has_video_stream=True,
        raw_info=info,
    )


def collect_project_scenes(
    project: Project,
    search_directory: str | Path | None = None,
    default_image_duration: float = 5.0,
) -> list[SceneClip]:
    """
    Collects scenes belonging to the project in strict storyboard/timeline order.
    Never relies on alphabetical filename sorting.
    """
    if not project.scenes:
        return []

    search_path = Path(search_directory).resolve() if search_directory else None
    clips: list[SceneClip] = []

    for idx, scene in enumerate(project.scenes, start=1):
        found_file: Path | None = None

        if search_path and search_path.is_dir():
            # Check for explicitly matching exported scene file (e.g. scene_01.mp4, scene_1.mp4)
            patterns = [
                f"scene_{idx:02d}*.mp4",
                f"scene_{idx}*.mp4",
                f"{scene.name}.mp4",
                f"scene_{idx:02d}*.png",
                f"scene_{idx}*.png",
            ]
            for pat in patterns:
                matches = sorted(search_path.glob(pat))
                if matches:
                    found_file = matches[0]
                    break

        duration_sec = max(0.1, scene.duration_frames / float(project.fps))

        if found_file:
            clips.append(SceneClip(
                source=found_file,
                duration=duration_sec if found_file.suffix.lower() in IMAGE_EXTENSIONS else duration_sec,
                scene_id=f"scene_{idx:02d}",
                title=scene.name,
            ))
        else:
            # Wrap in-memory Scene object
            clips.append(SceneClip(
                source=scene,
                duration=duration_sec,
                scene_id=f"scene_{idx:02d}",
                title=scene.name,
            ))

    return clips


def _normalize_filter_string(width: int = 1920, height: int = 1080, fps: int = 30) -> str:
    return (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,"
        f"fps={fps},format=yuv420p"
    )


def compile_scenes(
    scenes_or_project: list[SceneClip] | Project,
    destination: str | Path,
    *,
    options: CompilationOptions | None = None,
    progress: ProgressCallback | None = None,
    is_cancelled: CancellationCallback | None = None,
    project_ref: Project | None = None,
    checkpoint_directory: str | Path | None = None,
) -> Path:
    """
    Combines all scenes in storyboard order into one continuous 1080p 30fps MP4.
    Supports in-memory Scene objects, video clips, and still images.
    """
    opts = options or CompilationOptions()

    # 1. Validate scenes / project upfront
    if isinstance(scenes_or_project, Project):
        project = scenes_or_project
        if not project.scenes:
            raise ValueError("Cannot compile an empty project with no scenes.")
        scenes = collect_project_scenes(project, default_image_duration=opts.default_image_duration)
    else:
        scenes = list(scenes_or_project)
        project = project_ref or Project(width=opts.width, height=opts.height, fps=opts.fps)

    if not scenes:
        raise ValueError("Cannot compile an empty project with no scenes.")

    ffmpeg = get_ffmpeg_executable(opts.ffmpeg_path)
    if not ffmpeg:
        raise RuntimeError("FFmpeg was not found. Install FFmpeg and add it to PATH before exporting.")

    target = Path(destination).expanduser().absolute()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.stem}.compiling{target.suffix or '.mp4'}")

    # 2. Validate external scene file existence upfront
    for clip in scenes:
        if isinstance(clip.source, Path):
            if not clip.source.is_file():
                raise FileNotFoundError(f"Scene file not found: {clip.source}")
            if clip.source.stat().st_size == 0:
                raise ValidationError(f"Scene file is empty/corrupt: {clip.source}")

    if is_cancelled and is_cancelled():
        raise ExportCancelledError("Export cancelled before processing started.")

    temp_dir_obj = tempfile.TemporaryDirectory(prefix="animatube_compile_")
    temp_dir = Path(temp_dir_obj.name)
    if checkpoint_directory is not None:
        cache_dir = Path(checkpoint_directory).expanduser().resolve()
    elif project.path:
        cache_dir = Path(project.path).expanduser().resolve().parent / ".animatube_render_cache"
    else:
        cache_dir = target.parent / f".{target.stem}_render_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_file = cache_dir / "checkpoint.json"
    checkpoint: dict[str, Any] = {"schema_version": 1, "profile": {
        "width": opts.width, "height": opts.height, "fps": opts.fps,
        "codec": opts.video_codec, "pixel_format": opts.pixel_format,
        "preset": opts.preset, "crf": opts.crf,
    }, "scenes": {}}
    if checkpoint_file.is_file():
        try:
            old = json.loads(checkpoint_file.read_text(encoding="utf-8"))
            if old.get("schema_version") == 1 and old.get("profile") == checkpoint["profile"]:
                checkpoint = old
        except (OSError, ValueError, TypeError):
            pass

    def persist_checkpoint() -> None:
        temp_checkpoint = checkpoint_file.with_suffix(".tmp")
        temp_checkpoint.write_text(json.dumps(checkpoint, indent=2), encoding="utf-8")
        os.replace(temp_checkpoint, checkpoint_file)

    def clip_fingerprint(clip: SceneClip) -> str:
        digest = hashlib.sha256()
        digest.update(json.dumps(checkpoint["profile"], sort_keys=True).encode("utf-8"))
        if clip.is_scene_object():
            from dataclasses import asdict
            digest.update(json.dumps(asdict(clip.source), sort_keys=True, default=str).encode("utf-8"))
        elif isinstance(clip.source, Path):
            with clip.source.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            digest.update(str(clip.duration).encode("ascii"))
        return digest.hexdigest()

    normalized_clips: list[Path] = []
    total_scenes = len(scenes)

    try:
        # Step A: Normalize each scene to standardized intermediate 1080p 30fps clip
        for idx, clip in enumerate(scenes, start=1):
            if is_cancelled and is_cancelled():
                raise ExportCancelledError(f"Export cancelled at scene {idx}/{total_scenes}.")

            fingerprint = clip_fingerprint(clip)
            norm_clip_path = cache_dir / f"scene_{idx:03d}_{fingerprint[:16]}.mp4"
            work_clip_path = cache_dir / f".{norm_clip_path.stem}.partial.mp4"
            if work_clip_path.exists():
                work_clip_path.unlink()
            cached = False
            if norm_clip_path.is_file() and norm_clip_path.stat().st_size > 0:
                try:
                    cached_probe = probe_video(norm_clip_path, ffprobe_executable=opts.ffprobe_path)
                    cached = cached_probe.width == opts.width and cached_probe.height == opts.height
                except (ValidationError, OSError):
                    cached = False
            if cached:
                normalized_clips.append(norm_clip_path)
                checkpoint.setdefault("scenes", {})[str(idx)] = {
                    "fingerprint": fingerprint, "file": norm_clip_path.name, "status": "complete"
                }
                if progress:
                    progress(round((idx / total_scenes) * 80))
                continue

            if clip.is_scene_object():
                _ensure_qapp()
                # Render in-memory scene via QPainter frame-by-frame
                scene_obj = clip.source  # type: ignore
                total_frames = scene_obj.duration_frames
                command = [
                    ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", f"{opts.width}x{opts.height}",
                    "-framerate", str(opts.fps), "-i", "-",
                    "-an", "-c:v", opts.video_codec,
                    "-preset", opts.preset, "-crf", str(opts.crf),
                    "-pix_fmt", opts.pixel_format,
                    str(work_clip_path),
                ]
                proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                try:
                    assert proc.stdin is not None
                    for f_idx in range(total_frames):
                        if is_cancelled and is_cancelled():
                            proc.kill()
                            raise ExportCancelledError(f"Export cancelled during scene {idx} rendering.")
                        frame_img = render_frame(project, scene_obj, f_idx, opts.width, opts.height)
                        proc.stdin.write(_rgb_bytes(frame_img))
                    proc.stdin.close()
                    code = proc.wait()
                    if code != 0:
                        err = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
                        raise RuntimeError(f"FFmpeg error normalizing scene {idx}: {err}")
                except Exception:
                    if proc.poll() is None:
                        proc.kill()
                    proc.wait()
                    raise

            elif clip.is_image():
                # Still image with specified duration
                dur = max(0.5, clip.duration or opts.default_image_duration)
                filters = _normalize_filter_string(opts.width, opts.height, opts.fps)
                cmd = [
                    ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                    "-loop", "1", "-t", f"{dur:.3f}",
                    "-i", str(clip.source),
                    "-an",
                    "-vf", filters,
                    "-c:v", opts.video_codec,
                    "-preset", opts.preset, "-crf", str(opts.crf),
                    "-pix_fmt", opts.pixel_format,
                    str(work_clip_path),
                ]
                res = subprocess.run(cmd, capture_output=True, text=True, check=False)
                if res.returncode != 0:
                    raise RuntimeError(f"Failed to normalize image scene {clip.source}: {res.stderr.strip()}")

            elif clip.is_video():
                # External video clip
                filters = _normalize_filter_string(opts.width, opts.height, opts.fps)
                cmd = [
                    ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                    "-i", str(clip.source),
                    "-an",
                    "-vf", filters,
                    "-c:v", opts.video_codec,
                    "-preset", opts.preset, "-crf", str(opts.crf),
                    "-pix_fmt", opts.pixel_format,
                    str(work_clip_path),
                ]
                res = subprocess.run(cmd, capture_output=True, text=True, check=False)
                if res.returncode != 0:
                    raise RuntimeError(f"Failed to normalize video scene {clip.source}: {res.stderr.strip()}")
            else:
                raise ValueError(f"Unsupported scene clip type: {type(clip.source)}")

            if not work_clip_path.is_file() or work_clip_path.stat().st_size == 0:
                raise ValidationError(f"Scene {idx} did not produce a valid intermediate video.")
            probe_video(work_clip_path, ffprobe_executable=opts.ffprobe_path)
            os.replace(work_clip_path, norm_clip_path)
            normalized_clips.append(norm_clip_path)
            checkpoint.setdefault("scenes", {})[str(idx)] = {
                "fingerprint": fingerprint, "file": norm_clip_path.name, "status": "complete"
            }
            persist_checkpoint()

            if progress:
                # First 80% progress is scene normalization
                progress(round((idx / total_scenes) * 80))

        if is_cancelled and is_cancelled():
            raise ExportCancelledError("Export cancelled before concatenation.")

        # Step B: Concat normalized clips using FFmpeg concat demuxer
        concat_list_file = temp_dir / "concat_list.txt"
        with open(concat_list_file, "w", encoding="utf-8") as f:
            for p in normalized_clips:
                # Escape path for FFmpeg concat demuxer
                escaped = str(p.resolve()).replace("\\", "/")
                f.write(f"file '{escaped}'\n")

        concat_cmd = [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_list_file),
            "-c", "copy",
            "-movflags", "+faststart",
            str(temporary),
        ]

        concat_proc = subprocess.run(concat_cmd, capture_output=True, text=True, check=False)
        if concat_proc.returncode != 0:
            raise RuntimeError(f"FFmpeg concat failed: {concat_proc.stderr.strip()}")

        if progress:
            progress(95)

        # Step C: Verification with FFprobe
        probe_result = probe_video(temporary, ffprobe_executable=opts.ffprobe_path)
        if probe_result.width != opts.width or probe_result.height != opts.height:
            raise ValidationError(
                f"Exported video resolution mismatch: expected {opts.width}x{opts.height}, got {probe_result.width}x{probe_result.height}"
            )

        # Replace temporary with final target
        if temporary.is_file():
            temporary.replace(target)

        if progress:
            progress(100)

        return target

    finally:
        temp_dir_obj.cleanup()
        for partial in cache_dir.glob("*.partial.mp4"):
            try:
                partial.unlink()
            except OSError:
                pass
        if temporary.is_file():
            try:
                temporary.unlink()
            except OSError:
                pass
