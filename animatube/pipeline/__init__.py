"""Pipeline package for AnimaTube automated video production."""

from animatube.pipeline.animator import (
    SceneAnimator,
    SceneMotionStyle,
    enhance_project_with_animations,
)
from animatube.pipeline.models import (
    MediaManifest,
    Script,
    ScriptScene,
    Storyboard,
    StoryboardScene,
)

__all__ = [
    "ScriptScene",
    "Script",
    "StoryboardScene",
    "Storyboard",
    "MediaManifest",
    "SceneAnimator",
    "SceneMotionStyle",
    "enhance_project_with_animations",
]
