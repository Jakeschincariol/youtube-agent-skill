from __future__ import annotations

from pathlib import Path
from typing import Any

from animatube.core.animation import set_keyframe
from animatube.core.models import Keyframe, Layer, Project, Scene
from animatube.core.project import save_project
from animatube.pipeline.models import Storyboard, StoryboardScene


def assemble_animatube_project(
    storyboard: Storyboard,
    destination_anima_path: str | Path,
    *,
    project_name: str = "DevOps 2027",
) -> Project:
    """
    Assembles a full multi-scene AnimaTube Project from a Storyboard.
    Each scene duration is matched to audio narration timing.
    Adds visual diagram image layers and animated keyframe overlays.
    """
    target = Path(destination_anima_path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    scenes: list[Scene] = []

    for idx, sb_scene in enumerate(storyboard.scenes, start=1):
        layers: list[Layer] = []
        frames = max(30, sb_scene.duration_frames)

        # 1. Background image layer (if a diagram was generated for this scene)
        if sb_scene.visual_asset_paths:
            primary_asset = sb_scene.visual_asset_paths[0]
            if Path(primary_asset).is_file():
                img_layer = Layer(
                    name=f"Diagram_{idx}",
                    kind="image",
                    x=0,
                    y=0,
                    width=storyboard.width,
                    height=storyboard.height,
                    asset_path=str(primary_asset),
                    keyframes=[
                        Keyframe(frame=0, x=0, y=0, scale=0.98, opacity=0.85, easing="ease-out"),
                        Keyframe(frame=min(15, frames // 4), x=0, y=0, scale=1.0, opacity=1.0),
                    ],
                )
                layers.append(img_layer)

        # 2. Lower-third indicator banner (dark transluscent rounded card)
        banner_w = 1200
        banner_h = 90
        banner_x = (storyboard.width - banner_w) / 2
        banner_y = storyboard.height - banner_h - 40

        banner_card = Layer(
            name=f"BannerCard_{idx}",
            kind="rect",
            x=banner_x,
            y=banner_y,
            width=banner_w,
            height=banner_h,
            color="#0f172a",
            keyframes=[
                Keyframe(frame=0, x=banner_x, y=banner_y + 20, opacity=0.0, easing="ease-out"),
                Keyframe(frame=min(12, frames // 4), x=banner_x, y=banner_y, opacity=0.92),
            ],
        )
        layers.append(banner_card)

        # 3. Scene Title Text
        title_text = Layer(
            name=f"TitleText_{idx}",
            kind="text",
            x=banner_x + 30,
            y=banner_y + 15,
            width=banner_w - 60,
            height=banner_h - 30,
            text=f"{idx}. {sb_scene.title}",
            color="#38bdf8",
            font_size=32,
            keyframes=[
                Keyframe(frame=0, x=banner_x + 30, y=banner_y + 20, opacity=0.0, easing="ease-out"),
                Keyframe(frame=min(12, frames // 4), x=banner_x + 30, y=banner_y + 15, opacity=1.0),
            ],
        )
        layers.append(title_text)

        scene = Scene(
            name=f"Scene {idx}: {sb_scene.title}",
            duration_frames=frames,
            layers=layers,
        )
        scenes.append(scene)

    project = Project(
        name=project_name,
        width=storyboard.width,
        height=storyboard.height,
        fps=storyboard.fps,
        background="#0a0f1d",
        scenes=scenes,
    )

    save_project(project, target)
    return project
