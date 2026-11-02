from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QGuiApplication,
    QImage,
    QLinearGradient,
    QPainter,
    QPen,
)

from animatube.audio.subtitles import format_timestamp_srt
from animatube.pipeline.models import Storyboard


def _ensure_qapp() -> QGuiApplication:
    app = QGuiApplication.instance()
    if app is None:
        app = QGuiApplication(sys.argv if hasattr(sys, "argv") and sys.argv else ["animatube"])
    return app


def generate_thumbnail(
    output_path: str | Path,
    width: int = 1280,
    height: int = 720,
    title_text: str = "DEVOPS IN 2027",
    badge_text: str = "ONLY 5 TOOLS",
) -> Path:
    """Generates a high-contrast, high-CTR YouTube thumbnail."""
    _ensure_qapp()
    target = Path(output_path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    image = QImage(width, height, QImage.Format.Format_ARGB32)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    # Dark cybernetic gradient background
    gradient = QLinearGradient(0, 0, width, height)
    gradient.setColorAt(0.0, QColor("#030712"))
    gradient.setColorAt(0.5, QColor("#0b1329"))
    gradient.setColorAt(1.0, QColor("#111827"))
    painter.fillRect(0, 0, width, height, gradient)

    # Neon framing border
    border_pen = QPen(QColor("#38bdf8"), 8)
    painter.setPen(border_pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(QRectF(16, 16, width - 32, height - 32), 24, 24)

    # Glowing Badge: "ONLY 5 TOOLS"
    badge_rect = QRectF(80, 80, 360, 68)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor("#f59e0b")))
    painter.drawRoundedRect(badge_rect, 14, 14)

    b_font = QFont("Segoe UI", 32)
    b_font.setBold(True)
    painter.setFont(b_font)
    painter.setPen(QPen(QColor("#030712")))
    painter.drawText(badge_rect, int(Qt.AlignmentFlag.AlignCenter), badge_text)

    # Main Headline: "DEVOPS IN 2027"
    title_font = QFont("Segoe UI", 76)
    title_font.setBold(True)
    painter.setFont(title_font)
    painter.setPen(QPen(QColor("#f8fafc")))
    painter.drawText(QRectF(80, 180, width - 160, 100), int(Qt.AlignmentFlag.AlignLeft), title_text)

    # Sub-headline: "Zero to Job-Ready Roadmap"
    sub_font = QFont("Segoe UI", 38)
    sub_font.setBold(True)
    painter.setFont(sub_font)
    painter.setPen(QPen(QColor("#38bdf8")))
    painter.drawText(QRectF(80, 290, width - 160, 60), int(Qt.AlignmentFlag.AlignLeft), "ZERO TO PRODUCTION READY")

    # 5 Tool Pills
    tools = [
        ("Linux", "#38bdf8"),
        ("Git", "#f97316"),
        ("Docker", "#0284c7"),
        ("Jenkins", "#eab308"),
        ("AWS", "#10b981"),
    ]
    pill_w = 210
    pill_h = 70
    start_x = 80
    start_y = 440
    gap = 20

    for i, (tool_name, col_hex) in enumerate(tools):
        p_rect = QRectF(start_x + i * (pill_w + gap), start_y, pill_w, pill_h)
        painter.setPen(QPen(QColor(col_hex), 3))
        painter.setBrush(QBrush(QColor(15, 23, 42, 230)))
        painter.drawRoundedRect(p_rect, 12, 12)

        p_font = QFont("Segoe UI", 24)
        p_font.setBold(True)
        painter.setFont(p_font)
        painter.setPen(QPen(QColor("#ffffff")))
        painter.drawText(p_rect, int(Qt.AlignmentFlag.AlignCenter), tool_name)

    # Target Audience Tagline at the bottom
    tag_font = QFont("Segoe UI", 22)
    painter.setFont(tag_font)
    painter.setPen(QPen(QColor("#94a3b8")))
    painter.drawText(QRectF(80, 580, width - 160, 45), int(Qt.AlignmentFlag.AlignLeft), "For Indian Freshers, Students & Tech Career Switchers")

    painter.end()
    image.save(str(target), "PNG")
    return target


def generate_video_metadata(
    storyboard: Storyboard,
    output_metadata_path: str | Path,
    output_chapters_path: str | Path,
) -> tuple[Path, Path]:
    """Generates verified YouTube metadata and chapters derived from the storyboard."""
    meta_target = Path(output_metadata_path).resolve()
    meta_target.parent.mkdir(parents=True, exist_ok=True)
    chap_target = Path(output_chapters_path).resolve()
    chap_target.parent.mkdir(parents=True, exist_ok=True)

    # Build Chapters
    chapter_lines: list[str] = []
    current_time = 0.0

    for idx, scene in enumerate(storyboard.scenes):
        total_seconds = int(current_time)
        minutes, seconds = divmod(total_seconds, 60)
        timecode = f"{minutes:02d}:{seconds:02d}"
        chapter_lines.append(f"{timecode} - {scene.title}")
        current_time += scene.duration_seconds

    chap_target.write_text("\n".join(chapter_lines) + "\n", encoding="utf-8")

    description = (
        "Looking to become a DevOps engineer in 2027? Here is a practical, step-by-step DevOps roadmap "
        "for beginners, college freshers, and IT professionals looking to build real-world skills from scratch.\n\n"
        "TIMESTAMPS / CHAPTERS:\n"
        + "\n".join(chapter_lines)
        + "\n\n"
        "THE 5 CORE PILLARS COVERED:\n"
        "1. Linux: Terminal navigation, permissions, process monitoring, and Bash automation.\n"
        "2. Git & GitHub: Branching models, pull requests, merge conflict resolution, and webhooks.\n"
        "3. Docker: Writing clean Dockerfiles, managing container lifecycles, and Docker Compose.\n"
        "4. Jenkins: Automated testing, container builds, and declarative Jenkinsfiles.\n"
        "5. AWS Cloud: Virtual compute (EC2), secure storage (S3), IAM roles, and custom VPC networking.\n\n"
        "WHO THIS ROADMAP IS FOR:\n"
        "- Indian engineering students and freshers preparing for cloud/DevOps placements.\n"
        "- QA testers, system administrators, and tech support engineers switching to DevOps.\n"
        "- Beginners who want a structured, practical study plan without expensive bootcamps.\n\n"
        "#DevOps #DevOpsRoadmap #DevOpsEngineer #CloudComputing #CareerInTech\n"
    )

    tags = [
        "devops roadmap 2027",
        "how to become a devops engineer",
        "devops for beginners",
        "devops roadmap for freshers",
        "devops engineer roadmap",
        "devops tutorial for beginners",
        "devops tools",
        "docker for beginners",
        "linux for devops",
        "jenkins pipeline tutorial",
        "aws for devops",
        "git and github for devops",
        "devops roadmap",
        "devops course",
        "devops career path",
        "devops engineer salary in india",
        "how to switch to devops",
        "ci cd pipeline tutorial",
        "learn devops step by step",
        "devops engineer skills",
    ]

    hashtags = [
        "#DevOps",
        "#DevOpsRoadmap",
        "#DevOpsEngineer",
        "#CloudComputing",
        "#CareerInTech",
    ]

    metadata_payload = {
        "title": "How to Become a DevOps Engineer in 2027 (Complete Beginner Roadmap)",
        "description": description,
        "tags": tags,
        "tag_count": len(tags),
        "hashtags": hashtags,
        "hashtag_count": len(hashtags),
        "chapters": chapter_lines,
        "total_duration_seconds": storyboard.total_duration_seconds(),
    }

    with open(meta_target, "w", encoding="utf-8") as f:
        json.dump(metadata_payload, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return meta_target, chap_target
