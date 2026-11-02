from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen, QPixmap

from animatube.core.animation import state_at
from animatube.core.models import Project, Scene

Progress = Callable[[int], None]


def render_frame(project: Project, scene: Scene, frame: int, width: int, height: int) -> QImage:
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(QColor(project.background))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    sx, sy = width / project.width, height / project.height

    for layer in scene.layers:
        state = state_at(layer, frame)
        painter.save()
        painter.setOpacity(state["opacity"])
        x, y = state["x"] * sx, state["y"] * sy
        w, h = layer.width * state["scale"] * sx, layer.height * state["scale"] * sy
        bounds = QRectF(-w / 2, -h / 2, w, h)
        painter.translate(x + w / 2, y + h / 2)
        painter.rotate(state["rotation"])
        color = QColor(layer.color)

        if layer.kind == "text":
            font = QFont("Arial", max(1, round(layer.font_size * sy)))
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QPen(color))
            painter.drawText(bounds, int(Qt.AlignmentFlag.AlignCenter) | int(Qt.TextFlag.TextWordWrap), layer.text)
        elif layer.kind in ("rect", "ellipse"):
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            if layer.kind == "ellipse":
                painter.drawEllipse(bounds)
            else:
                painter.drawRoundedRect(bounds, 12, 12)
        elif layer.kind == "image" and layer.asset_path:
            source = project.resolve_asset(layer.asset_path)
            pixmap = QPixmap(str(source))
            if not pixmap.isNull():
                painter.drawPixmap(bounds.toRect(), pixmap)
        painter.restore()

    painter.end()
    return image


def _rgb_bytes(image: QImage) -> bytes:
    converted = image.convertToFormat(QImage.Format.Format_RGB888)
    raw = converted.constBits().tobytes()
    stride = converted.bytesPerLine()
    row_bytes = converted.width() * 3
    return b"".join(raw[row * stride:row * stride + row_bytes] for row in range(converted.height()))


def export_scene(
    project: Project,
    scene: Scene,
    destination: str | Path,
    *,
    profile: str = "wide",
    resolution: str = "720p",
    progress: Progress | None = None,
) -> Path:
    executable = shutil.which("ffmpeg")
    if not executable:
        raise RuntimeError("FFmpeg was not found. Install FFmpeg and add it to PATH before exporting.")
    from animatube.core.profiles import output_dimensions

    width, height = output_dimensions(profile, resolution)
    target = Path(destination).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.stem}.rendering{target.suffix or '.mp4'}")
    command = [
        executable, "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", f"{width}x{height}",
        "-framerate", str(project.fps), "-i", "-", "-an", "-c:v", "libx264",
        "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(temporary),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    total = scene.duration_frames
    try:
        assert process.stdin is not None
        for frame in range(total):
            rendered = render_frame(project, scene, frame, width, height)
            process.stdin.write(_rgb_bytes(rendered))
            if progress:
                progress(round((frame + 1) * 100 / total))
        process.stdin.close()
        stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
        code = process.wait()
        if code != 0:
            raise RuntimeError(f"FFmpeg export failed: {stderr.strip() or f'exit code {code}'}")
        temporary.replace(target)
    except Exception:
        if process.poll() is None:
            process.kill()
        process.wait()
        try:
            temporary.unlink()
        except OSError:
            pass
        raise
    return target
