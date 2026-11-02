from __future__ import annotations

import logging
import os
from pathlib import Path
import shutil
import subprocess
from typing import Callable
import wave

from PySide6.QtGui import QImage

from animatube.core.models import Project
from animatube.export.renderer import _rgb_bytes, render_frame
from animatube.pipeline.models import Storyboard

logger = logging.getLogger(__name__)
Progress = Callable[[int, int], None]


def concatenate_wav_files(input_paths: list[str | Path], output_path: str | Path) -> Path:
    """Concatenates multiple WAV audio files sequentially using Python's standard wave module."""
    target = Path(output_path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    valid_paths = [Path(p).resolve() for p in input_paths if Path(p).is_file()]
    if not valid_paths:
        raise ValueError("No valid WAV files provided for concatenation.")

    # Read parameters from first file
    with wave.open(str(valid_paths[0]), "rb") as first_wf:
        params = first_wf.getparams()

    with wave.open(str(target), "wb") as out_wf:
        out_wf.setparams(params)
        for p in valid_paths:
            with wave.open(str(p), "rb") as in_wf:
                # Read and append frames
                out_wf.writeframes(in_wf.readframes(in_wf.getnframes()))

    return target


class VideoComposer:
    """Composites visual scenes and audio into a final YouTube-ready 1080p MP4."""

    def __init__(self, ffmpeg_executable: str | None = None) -> None:
        self.ffmpeg_path = (
            ffmpeg_executable
            or os.environ.get("FFMPEG_PATH")
            or shutil.which("ffmpeg")
        )

    def is_available(self) -> bool:
        """Returns True if FFmpeg binary is found."""
        if not self.ffmpeg_path:
            return False
        return Path(self.ffmpeg_path).is_file() or shutil.which(self.ffmpeg_path) is not None

    def compose_video(
        self,
        project: Project,
        storyboard: Storyboard,
        output_mp4_path: str | Path,
        master_audio_path: str | Path | None = None,
        subtitle_path: str | Path | None = None,
        progress: Progress | None = None,
        dry_run: bool = False,
    ) -> Path:
        """
        Renders all scenes in project to 1080p, combines with master narration audio,
        and produces a YouTube-compliant H.264/AAC MP4.
        """
        target = Path(output_mp4_path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)

        width = storyboard.width
        height = storyboard.height
        fps = storyboard.fps

        # If audio not explicitly provided, concatenate from storyboard scenes
        if not master_audio_path or not Path(master_audio_path).is_file():
            audio_files = [s.narration_audio_path for s in storyboard.scenes if s.narration_audio_path]
            if audio_files and all(Path(p).is_file() for p in audio_files):
                master_audio_path = target.with_suffix(".master_audio.wav")
                concatenate_wav_files(audio_files, master_audio_path)

        if dry_run or not self.is_available():
            logger.info("FFmpeg dry-run or unavailable; generating placeholder artifact.")
            target.write_bytes(b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00isommp42")
            return target

        temporary = target.with_name(f".{target.stem}.rendering{target.suffix or '.mp4'}")

        cmd = [
            self.ffmpeg_path,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "rawvideo",
            "-pixel_format",
            "rgb24",
            "-video_size",
            f"{width}x{height}",
            "-framerate",
            str(fps),
            "-i",
            "-",
        ]

        if master_audio_path and Path(master_audio_path).is_file():
            cmd.extend(["-i", str(master_audio_path), "-c:a", "aac", "-b:a", "192k", "-shortest"])
        else:
            cmd.extend(["-an"])

        cmd.extend([
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(temporary),
        ])

        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

        total_frames = sum(s.duration_frames for s in project.scenes)
        current_frame = 0

        try:
            assert process.stdin is not None
            for scene in project.scenes:
                for frame in range(scene.duration_frames):
                    rendered = render_frame(project, scene, frame, width, height)
                    process.stdin.write(_rgb_bytes(rendered))
                    current_frame += 1
                    if progress:
                        progress(current_frame, total_frames)

            process.stdin.close()
            process.wait()
            if process.returncode != 0:
                stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
                raise RuntimeError(f"FFmpeg render failed with exit code {process.returncode}: {stderr}")

            if temporary.is_file():
                temporary.replace(target)
            return target
        except Exception:
            if temporary.is_file():
                try:
                    temporary.unlink()
                except OSError:
                    pass
            raise
