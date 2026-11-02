def output_dimensions(profile: str, resolution: str) -> tuple[int, int]:
    heights = {"720p": 720, "1080p": 1080, "1440p": 1440, "4K": 2160}
    if resolution not in heights:
        raise ValueError(f"Unsupported resolution: {resolution}")
    height = heights[resolution]
    if profile == "wide":
        width = height * 16 // 9
    elif profile == "vertical":
        width = height * 9 // 16
    elif profile == "square":
        width = height
    else:
        raise ValueError(f"Unsupported profile: {profile}")
    return width - width % 2, height - height % 2
