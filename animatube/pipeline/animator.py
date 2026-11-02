from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import logging
from typing import Any

from animatube.core.models import Keyframe, Layer, Project, Scene
from animatube.pipeline.models import Storyboard, StoryboardScene

logger = logging.getLogger("animatube.animator")


class SceneMotionStyle(str, Enum):
    HOOK_INTRO = "hook_intro"
    ZOOM_OUT_ROADMAP = "zoom_out_roadmap"
    PAN_TOOL_FOCUS = "pan_tool_focus"
    PROGRESSIVE_PIPELINE = "progressive_pipeline"
    CLOUD_SCALE = "cloud_scale"
    OUTRO_CALL_TO_ACTION = "outro_call_to_action"


def detect_scene_motion_style(
    scene_name: str,
    scene_index: int,
    total_scenes: int,
    diagram_type: str = "",
) -> SceneMotionStyle:
    """
    Intelligently determines the appropriate motion graphics style
    based on scene position, title, and visual diagram context.
    Ensures varied, contextual animation across the video.
    """
    lower = f"{scene_name} {diagram_type}".lower()

    if scene_index == 0 or "intro" in lower or "hook" in lower:
        return SceneMotionStyle.HOOK_INTRO
    if scene_index == total_scenes - 1 or "outro" in lower or "action" in lower or "summary" in lower:
        return SceneMotionStyle.OUTRO_CALL_TO_ACTION
    if "pipeline" in lower or "jenkins" in lower or "ci_cd" in lower or "git" in lower:
        return SceneMotionStyle.PROGRESSIVE_PIPELINE
    if "cloud" in lower or "aws" in lower or "scale" in lower:
        return SceneMotionStyle.CLOUD_SCALE
    if "roadmap" in lower or "overview" in lower or "pillars" in lower:
        return SceneMotionStyle.ZOOM_OUT_ROADMAP

    # Tool focus (Linux, Docker, etc.)
    return SceneMotionStyle.PAN_TOOL_FOCUS


class SceneAnimator:
    """
    Enhances AnimaTube scenes with rich, lightweight motion graphics:
    - Ken Burns slow zoom-in and zoom-out
    - Camera pan effects
    - Smooth fade-in and fade-out
    - Slide transitions for headings & lower thirds
    - Keyword highlighting badges
    - Progressive diagram reveals & moving arrows
    - Animated floating technical badges
    """

    ACCENTS = ["#38bdf8", "#f59e0b", "#10b981", "#8b5cf6", "#ec4899", "#06b6d4"]

    def __init__(self, fps: int = 30) -> None:
        self.fps = fps

    def enhance_scene(
        self,
        scene: Scene,
        scene_index: int,
        total_scenes: int,
        style: SceneMotionStyle | None = None,
        diagram_type: str = "",
        width: int = 1920,
        height: int = 1080,
    ) -> Scene:
        """Applies contextual motion graphics to a single scene."""
        frames = max(30, int(scene.duration_frames))
        chosen_style = style or detect_scene_motion_style(
            scene.name, scene_index, total_scenes, diagram_type
        )
        accent = self.ACCENTS[scene_index % len(self.ACCENTS)]

        # 1. Enhance existing image / diagram layers with Ken Burns pan/zoom
        for layer in scene.layers:
            if layer.kind == "image":
                self._apply_ken_burns(layer, chosen_style, frames, width, height)
            elif "BannerCard" in layer.name or "TitleText" in layer.name:
                self._apply_slide_transition(layer, frames)

        # 2. Add dynamic motion graphics layers depending on style
        new_layers: list[Layer] = []

        # A. Keyword Highlight Badge
        keyword = self._extract_keyword(scene.name, chosen_style)
        if keyword:
            kw_badge, kw_text = self._create_keyword_highlight(keyword, accent, frames, width, height)
            new_layers.extend([kw_badge, kw_text])

        # B. Moving arrows / progress line for pipeline & roadmap scenes
        if chosen_style == SceneMotionStyle.PROGRESSIVE_PIPELINE:
            arrow_layer = self._create_moving_arrow(accent, frames, width, height)
            new_layers.append(arrow_layer)

        # C. Floating Technical Icon / Badge
        if chosen_style in (SceneMotionStyle.PAN_TOOL_FOCUS, SceneMotionStyle.CLOUD_SCALE):
            icon_badge, icon_text = self._create_floating_badge(scene.name, accent, frames, width, height)
            new_layers.extend([icon_badge, icon_text])

        # D. Scene Exit Fade Transition (smooth dip over final 10 frames)
        self._apply_scene_fade_transitions(scene, frames)

        scene.layers.extend(new_layers)
        return scene

    def _apply_ken_burns(
        self,
        layer: Layer,
        style: SceneMotionStyle,
        duration_frames: int,
        width: int,
        height: int,
    ) -> None:
        """Applies slow cinematic Ken Burns camera movements (zoom / pan)."""
        layer.keyframes.clear()

        if style in (SceneMotionStyle.HOOK_INTRO, SceneMotionStyle.OUTRO_CALL_TO_ACTION):
            # Slow Zoom In (1.0 -> 1.07) with gentle center focus
            layer.keyframes = [
                Keyframe(frame=0, x=0, y=0, scale=1.0, opacity=0.9, easing="ease-out"),
                Keyframe(frame=duration_frames, x=-20, y=-12, scale=1.07, opacity=1.0),
            ]
        elif style == SceneMotionStyle.ZOOM_OUT_ROADMAP:
            # Slow Zoom Out (1.07 -> 1.0) revealing the full architecture
            layer.keyframes = [
                Keyframe(frame=0, x=-20, y=-15, scale=1.07, opacity=1.0, easing="ease-in-out"),
                Keyframe(frame=duration_frames, x=0, y=0, scale=1.0, opacity=1.0),
            ]
        elif style == SceneMotionStyle.PROGRESSIVE_PIPELINE:
            # Horizontal camera drift across the pipeline flow
            layer.keyframes = [
                Keyframe(frame=0, x=25, y=-5, scale=1.04, opacity=0.95, easing="linear"),
                Keyframe(frame=duration_frames, x=-35, y=-5, scale=1.04, opacity=1.0),
            ]
        elif style == SceneMotionStyle.CLOUD_SCALE:
            # Slight diagonal expansion (scale + subtle drift)
            layer.keyframes = [
                Keyframe(frame=0, x=-10, y=10, scale=1.02, opacity=1.0, easing="ease-out"),
                Keyframe(frame=duration_frames, x=-30, y=-15, scale=1.08, opacity=1.0),
            ]
        else:  # PAN_TOOL_FOCUS
            # Smooth subtle pan
            layer.keyframes = [
                Keyframe(frame=0, x=15, y=0, scale=1.03, opacity=1.0, easing="linear"),
                Keyframe(frame=duration_frames, x=-20, y=-5, scale=1.05, opacity=1.0),
            ]

    def _apply_slide_transition(self, layer: Layer, duration_frames: int) -> None:
        """Enhances title banners with smooth slide-up and fade-in transitions."""
        target_y = layer.y
        start_y = target_y + 40
        in_frames = min(15, max(6, duration_frames // 5))

        layer.keyframes = [
            Keyframe(frame=0, x=layer.x, y=start_y, scale=1.0, opacity=0.0, easing="ease-out"),
            Keyframe(frame=in_frames, x=layer.x, y=target_y, scale=1.0, opacity=1.0),
            Keyframe(frame=max(in_frames + 1, duration_frames - 10), x=layer.x, y=target_y, scale=1.0, opacity=1.0),
        ]

    def _extract_keyword(self, scene_name: str, style: SceneMotionStyle) -> str:
        """Extracts high-impact keyword for highlight badge."""
        lower = scene_name.lower()
        if "linux" in lower:
            return "LINUX CORE"
        if "git" in lower:
            return "VERSION CONTROL"
        if "docker" in lower:
            return "CONTAINERS"
        if "jenkins" in lower or "ci" in lower:
            return "CI/CD PIPELINE"
        if "aws" in lower or "cloud" in lower:
            return "CLOUD ARCHITECTURE"
        if "roadmap" in lower or "pillars" in lower:
            return "2027 ROADMAP"
        if style == SceneMotionStyle.HOOK_INTRO:
            return "START HERE"
        if style == SceneMotionStyle.OUTRO_CALL_TO_ACTION:
            return "NEXT STEPS"
        return "CORE SKILL"

    def _create_keyword_highlight(
        self,
        keyword: str,
        accent: str,
        duration_frames: int,
        width: int,
        height: int,
    ) -> tuple[Layer, Layer]:
        """Creates an animated pulsing keyword highlight badge on the top right."""
        badge_w = 260
        badge_h = 56
        badge_x = width - badge_w - 60
        badge_y = 60

        entry_start = min(10, duration_frames // 4)
        entry_end = entry_start + 12

        # Glowing Pill Rect
        badge = Layer(
            name="Anim_KeywordBadge",
            kind="rect",
            x=badge_x,
            y=badge_y,
            width=badge_w,
            height=badge_h,
            color=accent,
            keyframes=[
                Keyframe(frame=0, x=badge_x + 30, y=badge_y, scale=0.8, opacity=0.0, easing="ease-out"),
                Keyframe(frame=entry_start, x=badge_x + 30, y=badge_y, scale=0.8, opacity=0.0),
                Keyframe(frame=entry_end, x=badge_x, y=badge_y, scale=1.0, opacity=0.92, easing="ease-in-out"),
                # Subtle pulse at midpoint
                Keyframe(frame=duration_frames // 2, x=badge_x - 3, y=badge_y - 2, scale=1.04, opacity=1.0, easing="ease-in-out"),
                Keyframe(frame=max(entry_end + 1, duration_frames - 12), x=badge_x, y=badge_y, scale=1.0, opacity=0.92),
            ],
        )

        # Keyword Text
        text = Layer(
            name="Anim_KeywordText",
            kind="text",
            x=badge_x + 10,
            y=badge_y + 12,
            width=badge_w - 20,
            height=badge_h - 24,
            text=keyword,
            color="#030712",
            font_size=22,
            keyframes=[
                Keyframe(frame=0, x=badge_x + 40, y=badge_y + 12, scale=0.8, opacity=0.0, easing="ease-out"),
                Keyframe(frame=entry_start, x=badge_x + 40, y=badge_y + 12, scale=0.8, opacity=0.0),
                Keyframe(frame=entry_end, x=badge_x + 10, y=badge_y + 12, scale=1.0, opacity=1.0),
                Keyframe(frame=duration_frames // 2, x=badge_x + 7, y=badge_y + 10, scale=1.04, opacity=1.0),
                Keyframe(frame=max(entry_end + 1, duration_frames - 12), x=badge_x + 10, y=badge_y + 12, scale=1.0, opacity=1.0),
            ],
        )
        return badge, text

    def _create_moving_arrow(
        self,
        accent: str,
        duration_frames: int,
        width: int,
        height: int,
    ) -> Layer:
        """Creates an animated moving arrow / progress indicator across the scene."""
        start_x = 320
        end_x = width - 380
        arrow_y = height - 170

        return Layer(
            name="Anim_MovingArrow",
            kind="text",
            x=start_x,
            y=arrow_y,
            width=120,
            height=60,
            text="►►►",
            color=accent,
            font_size=28,
            keyframes=[
                Keyframe(frame=0, x=start_x, y=arrow_y, scale=1.0, opacity=0.0, easing="ease-out"),
                Keyframe(frame=15, x=start_x, y=arrow_y, scale=1.0, opacity=0.85, easing="linear"),
                Keyframe(frame=duration_frames - 15, x=end_x, y=arrow_y, scale=1.0, opacity=0.85),
                Keyframe(frame=duration_frames, x=end_x + 30, y=arrow_y, scale=1.0, opacity=0.0),
            ],
        )

    def _create_floating_badge(
        self,
        scene_name: str,
        accent: str,
        duration_frames: int,
        width: int,
        height: int,
    ) -> tuple[Layer, Layer]:
        """Creates a gently floating technical badge with smooth oscillation."""
        bx = 70
        by = 60
        bw = 140
        bh = 48

        # Floating motion keyframes (up and down)
        mid_frame = duration_frames // 2
        badge = Layer(
            name="Anim_TechBadge",
            kind="rect",
            x=bx,
            y=by,
            width=bw,
            height=bh,
            color="#0f172a",
            keyframes=[
                Keyframe(frame=0, x=bx, y=by + 10, scale=0.9, opacity=0.0, easing="ease-out"),
                Keyframe(frame=12, x=bx, y=by, scale=1.0, opacity=0.95, easing="ease-in-out"),
                Keyframe(frame=mid_frame, x=bx, y=by - 8, scale=1.02, opacity=1.0, easing="ease-in-out"),
                Keyframe(frame=duration_frames - 10, x=bx, y=by, scale=1.0, opacity=0.95),
            ],
        )

        text = Layer(
            name="Anim_TechBadgeText",
            kind="text",
            x=bx + 10,
            y=by + 10,
            width=bw - 20,
            height=bh - 20,
            text="TECH STACK",
            color=accent,
            font_size=18,
            keyframes=[
                Keyframe(frame=0, x=bx + 10, y=by + 20, scale=0.9, opacity=0.0, easing="ease-out"),
                Keyframe(frame=12, x=bx + 10, y=by + 10, scale=1.0, opacity=1.0, easing="ease-in-out"),
                Keyframe(frame=mid_frame, x=bx + 10, y=by + 2, scale=1.02, opacity=1.0, easing="ease-in-out"),
                Keyframe(frame=duration_frames - 10, x=bx + 10, y=by + 10, scale=1.0, opacity=1.0),
            ],
        )
        return badge, text

    def _apply_scene_fade_transitions(self, scene: Scene, duration_frames: int) -> None:
        """Applies smooth fade-out to scene elements during the last 8-12 frames."""
        fade_out_start = max(10, duration_frames - 10)
        for layer in scene.layers:
            if not layer.keyframes:
                continue
            # Ensure final keyframe fades gracefully if not already handled
            last_key = layer.keyframes[-1]
            if last_key.frame < fade_out_start:
                layer.keyframes.append(
                    Keyframe(frame=fade_out_start, x=last_key.x, y=last_key.y, scale=last_key.scale, opacity=last_key.opacity)
                )
                layer.keyframes.append(
                    Keyframe(frame=duration_frames, x=last_key.x, y=last_key.y, scale=last_key.scale, opacity=0.2, easing="ease-out")
                )


def enhance_project_with_animations(
    project: Project,
    storyboard: Storyboard | None = None,
) -> Project:
    """
    Applies varied, context-tailored motion graphics across all scenes of an AnimaTube project.
    Preserves exact scene durations while introducing smooth camera movement and visual enhancements.
    """
    animator = SceneAnimator(fps=project.fps)
    total_scenes = len(project.scenes)

    for idx, scene in enumerate(project.scenes):
        diag_type = ""
        if storyboard and idx < len(storyboard.scenes):
            diag_type = storyboard.scenes[idx].diagram_type

        animator.enhance_scene(
            scene,
            scene_index=idx,
            total_scenes=total_scenes,
            diagram_type=diag_type,
            width=project.width,
            height=project.height,
        )

    return project
