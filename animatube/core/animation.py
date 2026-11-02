from __future__ import annotations

from bisect import bisect_right

from animatube.core.models import Keyframe, Layer

FIELDS = ("x", "y", "scale", "rotation", "opacity")


def _ease(value: float, easing: str) -> float:
    value = min(1.0, max(0.0, value))
    if easing == "ease-in":
        return value * value
    if easing == "ease-out":
        return 1 - (1 - value) ** 2
    if easing == "ease-in-out":
        return 2 * value * value if value < 0.5 else 1 - ((-2 * value + 2) ** 2) / 2
    return value


def state_at(layer: Layer, frame: int) -> dict[str, float]:
    base = {"x": layer.x, "y": layer.y, "scale": 1.0, "rotation": 0.0, "opacity": 1.0}
    keys = sorted(layer.keyframes, key=lambda item: item.frame)
    if not keys:
        return base
    positions = [item.frame for item in keys]
    index = bisect_right(positions, max(0, int(frame)))
    if index == 0:
        return {name: getattr(keys[0], name) for name in FIELDS}
    if index == len(keys):
        return {name: getattr(keys[-1], name) for name in FIELDS}
    before, after = keys[index - 1], keys[index]
    span = after.frame - before.frame
    progress = 1.0 if span <= 0 else _ease((frame - before.frame) / span, after.easing)
    return {name: getattr(before, name) + (getattr(after, name) - getattr(before, name)) * progress
            for name in FIELDS}


def set_keyframe(layer: Layer, frame: int, field: str, value: float, easing: str = "linear") -> None:
    if field not in FIELDS:
        raise ValueError(f"Unsupported animated property: {field}")
    current = state_at(layer, frame)
    current[field] = float(value)
    layer.keyframes = [key for key in layer.keyframes if key.frame != frame]
    layer.keyframes.append(Keyframe(frame=max(0, int(frame)), easing=easing, **current))
    layer.keyframes.sort(key=lambda key: key.frame)
