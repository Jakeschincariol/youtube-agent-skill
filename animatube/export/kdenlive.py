from __future__ import annotations

from pathlib import Path
from typing import Any
import xml.dom.minidom
import xml.etree.ElementTree as ET

from animatube.pipeline.models import Storyboard


def generate_kdenlive_project(
    storyboard: Storyboard,
    output_kdenlive_path: str | Path,
    *,
    project_title: str = "DevOps 2027",
) -> Path:
    """
    Generates a standards-compliant Kdenlive project file (.kdenlive / MLT XML).
    Sets up two synchronized tracks:
    - Video Track: Visual diagram scenes and background assets
    - Audio Track: Narration voiceover audio clips
    """
    target = Path(output_kdenlive_path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    mlt = ET.Element("mlt", {
        "version": "7.22.0",
        "title": project_title,
        "producer": "main_bin",
    })

    # Profile
    ET.SubElement(mlt, "profile", {
        "description": f"HD {storyboard.height}p {storyboard.fps} fps",
        "width": str(storyboard.width),
        "height": str(storyboard.height),
        "progressive": "1",
        "sample_aspect_num": "1",
        "sample_aspect_den": "1",
        "display_aspect_num": "16",
        "display_aspect_den": "9",
        "frame_rate_num": str(storyboard.fps),
        "frame_rate_den": "1",
        "colorspace": "709",
    })

    video_entries: list[tuple[str, int]] = []
    audio_entries: list[tuple[str, int]] = []

    for idx, scene in enumerate(storyboard.scenes, start=1):
        frames = max(30, scene.duration_frames)
        out_frame = frames - 1

        # 1. Visual Producer
        vis_id = f"producer_visual_{idx}"
        vis_path = scene.visual_asset_paths[0] if scene.visual_asset_paths else ""
        vis_prod = ET.SubElement(mlt, "producer", {
            "id": vis_id,
            "in": "0",
            "out": str(out_frame),
        })
        ET.SubElement(vis_prod, "property", {"name": "resource"}).text = str(vis_path)
        ET.SubElement(vis_prod, "property", {"name": "length"}).text = str(frames)
        ET.SubElement(vis_prod, "property", {"name": "kdenlive:clipname"}).text = f"Visual: {scene.title}"
        video_entries.append((vis_id, out_frame))

        # 2. Audio Producer (Narration)
        aud_id = f"producer_audio_{idx}"
        aud_path = scene.narration_audio_path or ""
        aud_prod = ET.SubElement(mlt, "producer", {
            "id": aud_id,
            "in": "0",
            "out": str(out_frame),
        })
        ET.SubElement(aud_prod, "property", {"name": "resource"}).text = str(aud_path)
        ET.SubElement(aud_prod, "property", {"name": "length"}).text = str(frames)
        ET.SubElement(aud_prod, "property", {"name": "kdenlive:clipname"}).text = f"Audio: {scene.title}"
        audio_entries.append((aud_id, out_frame))

    # Video Playlist (Track V1)
    playlist_video = ET.SubElement(mlt, "playlist", {"id": "playlist_video"})
    for vis_id, out_frame in video_entries:
        ET.SubElement(playlist_video, "entry", {
            "producer": vis_id,
            "in": "0",
            "out": str(out_frame),
        })

    # Audio Playlist (Track A1)
    playlist_audio = ET.SubElement(mlt, "playlist", {"id": "playlist_audio"})
    for aud_id, out_frame in audio_entries:
        ET.SubElement(playlist_audio, "entry", {
            "producer": aud_id,
            "in": "0",
            "out": str(out_frame),
        })

    # Tractor (Multitrack Timeline)
    tractor = ET.SubElement(mlt, "tractor", {"id": "maintractor", "title": project_title})
    multitrack = ET.SubElement(tractor, "multitrack")
    ET.SubElement(multitrack, "track", {"producer": "playlist_video"})
    ET.SubElement(multitrack, "track", {"producer": "playlist_audio"})

    # Transition to composite video
    transition = ET.SubElement(tractor, "transition", {"id": "transition_composite"})
    ET.SubElement(transition, "property", {"name": "a_track"}).text = "0"
    ET.SubElement(transition, "property", {"name": "b_track"}).text = "1"
    ET.SubElement(transition, "property", {"name": "mlt_service"}).text = "mix"

    raw_xml = ET.tostring(mlt, encoding="utf-8")
    pretty = xml.dom.minidom.parseString(raw_xml).toprettyxml(indent="  ")
    target.write_text(pretty, encoding="utf-8")
    return target
