from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys

from animatube.assets.devops_diagrams import generate_all_devops_diagrams
from animatube.audio.edge_tts_wrapper import EdgeTTS
from animatube.audio.piper_tts import PiperTTS
from animatube.audio.subtitles import SubtitleGenerator
from animatube.export.composer import VideoComposer, concatenate_audio_files, concatenate_wav_files
from animatube.export.kdenlive import generate_kdenlive_project
from animatube.pipeline.assembler import assemble_animatube_project
from animatube.pipeline.models import MediaManifest, Script, Storyboard
from animatube.pipeline.packaging import generate_thumbnail, generate_video_metadata
from animatube.pipeline.script_generator import (
    OllamaScriptGenerator,
    create_storyboard_from_script,
    generate_devops_roadmap_script,
)

logger = logging.getLogger("animatube.pipeline")


def run_pipeline(
    output_directory: str | Path,
    *,
    project_name: str = "DevOps_2027_Roadmap",
    use_ollama: bool = True,
    fps: int = 30,
    render_video: bool = True,
    dry_run_render: bool = False,
) -> MediaManifest:
    """
    Executes the complete, local-first AnimaTube video production pipeline.
    Produces:
    1. Structured script (JSON)
    2. Storyboard with exact frame allocations (JSON)
    3. Programmatic 1080p DevOps diagrams (PNGs)
    4. Narration voiceover audio per scene (WAV) + Master concatenated audio
    5. Subtitles (SRT)
    6. AnimaTube desktop project (.anima)
    7. Kdenlive NLE editing handoff (.kdenlive)
    8. 1080p YouTube-ready MP4 (via FFmpeg)
    9. High-impact thumbnail (PNG) + Video SEO metadata (JSON) + Chapters (TXT)
    10. Complete project manifest (manifest.json)
    """
    out_dir = Path(output_directory).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    assets_dir = out_dir / "assets"
    audio_dir = out_dir / "audio"
    subs_dir = out_dir / "subtitles"
    assets_dir.mkdir(exist_ok=True)
    audio_dir.mkdir(exist_ok=True)
    subs_dir.mkdir(exist_ok=True)

    manifest = MediaManifest(project_name=project_name)

    # 1. Script Generation
    logger.info("Step 1/8: Generating structured script...")
    if use_ollama:
        ollama = OllamaScriptGenerator()
        script = ollama.generate_script(use_fallback_if_unavailable=True)
    else:
        script = generate_devops_roadmap_script()

    script_path = out_dir / "script.json"
    import json
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(script.to_dict(), f, indent=2, ensure_ascii=False)
        f.write("\n")
    manifest.script_file = str(script_path)
    manifest.add_asset(script_path, "script")

    # 2. Visual Diagram Generation
    logger.info("Step 2/8: Generating 1080p DevOps visual diagrams...")
    diagrams = generate_all_devops_diagrams(assets_dir)
    for name, diag_path in diagrams.items():
        manifest.add_asset(diag_path, "diagram", {"name": name})

    # 3. Audio Narration (Edge TTS / Piper TTS) & Subtitles
    logger.info("Step 3/8: Synthesizing narration and generating subtitles...")
    edge_engine = EdgeTTS() if EdgeTTS.is_available() else None
    piper_tts = PiperTTS()
    sub_gen = SubtitleGenerator()
    storyboard = create_storyboard_from_script(script, fps=fps)

    use_edge = not piper_tts.is_available() and edge_engine is not None
    ext = ".mp3" if use_edge else ".wav"

    audio_files: list[str] = []
    for idx, (scene, sb_scene) in enumerate(zip(script.scenes, storyboard.scenes), start=1):
        # Assign visual diagram
        if scene.diagram_type in diagrams:
            sb_scene.visual_asset_paths = [str(diagrams[scene.diagram_type])]
        else:
            sb_scene.visual_asset_paths = [str(diagrams.get("pillars_overview", ""))]

        # Audio synthesis & Subtitles
        audio_file = audio_dir / f"scene_{idx:02d}_{scene.id}{ext}"
        srt_file = subs_dir / f"scene_{idx:02d}_{scene.id}.srt"

        if use_edge and edge_engine:
            logger.info("Synthesizing scene %d with Edge-TTS (%s)...", idx, edge_engine.voice)
            actual_duration = edge_engine.synthesize(
                scene.narration,
                audio_file,
                output_subtitles_path=srt_file,
            )
        else:
            actual_duration = piper_tts.synthesize(scene.narration, audio_file, allow_fallback=True)
            sub_gen.generate(
                audio_path=audio_file,
                output_srt_path=srt_file,
                reference_text=scene.narration,
                duration_seconds=actual_duration,
                allow_fallback=True,
            )

        sb_scene.duration_seconds = actual_duration
        sb_scene.duration_frames = max(30, int(round(actual_duration * fps)))
        sb_scene.narration_audio_path = str(audio_file)
        sb_scene.subtitle_path = str(srt_file)
        audio_files.append(str(audio_file))
        manifest.add_asset(audio_file, "audio_scene", {"scene_id": scene.id})
        manifest.add_asset(srt_file, "subtitle_scene", {"scene_id": scene.id})

    # Master audio concatenation
    master_audio = out_dir / f"{project_name}_master_narration{ext}"
    concatenate_audio_files(audio_files, master_audio)
    manifest.add_asset(master_audio, "master_audio")

    # Master full subtitles
    master_srt = out_dir / f"{project_name}_subtitles.srt"
    from animatube.audio.subtitles import generate_subtitles_from_text
    full_narration = " ".join(s.narration for s in script.scenes)
    generate_subtitles_from_text(full_narration, storyboard.total_duration_seconds(), master_srt)
    manifest.add_asset(master_srt, "master_subtitles")

    # 4. Save Storyboard
    logger.info("Step 4/8: Saving storyboard manifest...")
    storyboard_path = out_dir / "storyboard.json"
    with open(storyboard_path, "w", encoding="utf-8") as f:
        json.dump(storyboard.to_dict(), f, indent=2, ensure_ascii=False)
        f.write("\n")
    manifest.storyboard_file = str(storyboard_path)
    manifest.add_asset(storyboard_path, "storyboard")

    # 5. AnimaTube Project Assembly
    logger.info("Step 5/8: Assembling AnimaTube project (.anima)...")
    anima_path = out_dir / f"{project_name}.anima"
    project = assemble_animatube_project(storyboard, anima_path, project_name=project_name)
    manifest.anima_project_file = str(anima_path)
    manifest.add_asset(anima_path, "anima_project")

    # 6. Kdenlive NLE Handoff
    logger.info("Step 6/8: Generating Kdenlive project (.kdenlive)...")
    kdenlive_path = out_dir / f"{project_name}.kdenlive"
    generate_kdenlive_project(storyboard, kdenlive_path, project_title=project_name)
    manifest.kdenlive_project_file = str(kdenlive_path)
    manifest.add_asset(kdenlive_path, "kdenlive_project")

    # 7. Packaging (Thumbnail & YouTube Metadata)
    logger.info("Step 7/8: Generating thumbnail, metadata and chapters...")
    thumb_path = out_dir / f"{project_name}_thumbnail.png"
    generate_thumbnail(thumb_path)
    manifest.thumbnail_file = str(thumb_path)
    manifest.add_asset(thumb_path, "thumbnail")

    meta_path = out_dir / "metadata.json"
    chap_path = out_dir / "chapters.txt"
    generate_video_metadata(storyboard, meta_path, chap_path)
    manifest.metadata_file = str(meta_path)
    manifest.chapters_file = str(chap_path)
    manifest.add_asset(meta_path, "metadata")
    manifest.add_asset(chap_path, "chapters")

    # 8. Render Final 1080p MP4
    logger.info("Step 8/8: Rendering 1080p video...")
    output_mp4 = out_dir / f"{project_name}_1080p.mp4"
    composer = VideoComposer()
    if render_video:
        composer.compose_video(
            project,
            storyboard,
            output_mp4,
            master_audio_path=master_audio,
            dry_run=dry_run_render or not composer.is_available(),
        )
        manifest.output_video_file = str(output_mp4)
        manifest.add_asset(output_mp4, "final_video")

    # Save manifest
    manifest_path = out_dir / "manifest.json"
    manifest.save(manifest_path)
    logger.info("Pipeline complete! Manifest saved to: %s", manifest_path)
    return manifest
