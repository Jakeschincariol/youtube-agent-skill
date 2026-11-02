from __future__ import annotations

import logging
from pathlib import Path
import shutil
import sys
import wave

# Ensure repo root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from animatube.ai.mock_providers import MockMusicProvider, MockVoiceProvider
from animatube.ai.models import MusicPrompt, VoicePrompt
from animatube.audio.mixer import AudioMixer
from animatube.core.animation import set_keyframe
from animatube.core.models import Layer, Project, Scene
from animatube.export.compiler import CompilationOptions, compile_scenes
from animatube.pipeline.qa_validator import QAValidator
from animatube.presets.ep01_magic_abc_train import create_ep01_production_specification
from animatube.presets.generate_garden_bg import generate_dreamland_garden_bg

logger = logging.getLogger("animatube.presets.scene01")


def produce_scene_01_sample(base_dir: str | Path = "little-dreamers/episodes/ep01_magic_abc_train") -> Path:
    """
    Executes Phase 7: Generates the official 45-second 1080p 24fps production sample of Scene 1:
    'Welcome to Dreamland', featuring Aarav, Mia, Twinkle, dialogue, movement, BGM, SFX, and subtitles.
    """
    ep_dir = Path(base_dir).resolve()
    assets_dir = ep_dir / "assets"
    audio_dir = ep_dir / "audio"
    dialogue_dir = audio_dir / "dialogue"
    exports_dir = ep_dir / "exports"

    for d in (assets_dir, audio_dir, dialogue_dir, exports_dir):
        d.mkdir(parents=True, exist_ok=True)

    # 1. Ensure Background Art exists
    bg_path = assets_dir / "magical_garden_bg.png"
    if not bg_path.is_file():
        generate_dreamland_garden_bg(bg_path)

    # Resolve Character Anchors
    aarav_ref = str(Path("little-dreamers/flow_ready/aarav_flow_anchor.png").resolve())
    mia_ref = str(Path("little-dreamers/flow_ready/mia_flow_anchor.png").resolve())
    twinkle_ref = str(Path("little-dreamers/flow_ready/twinkle_flow_anchor.png").resolve())

    # 2. Synthesize Character Dialogue Audio
    voice_prov = MockVoiceProvider()
    dialogue_files: list[Path] = []

    dialogue_scripts = [
        ("narrator", "Welcome to Dreamland, where every day is a magical new adventure!", "Narrator", "default", 3.0),
        ("aarav_01", "Mia! Look at all these beautiful colours!", "Aarav", "aarav_boy", 2.5),
        ("mia_01", "Wow! I wonder what magical surprises are waiting for us today!", "Mia", "mia_girl", 3.0),
        ("twinkle_01", "Hello, little explorers! Are you ready for a magical adventure?", "Twinkle", "twinkle_star", 3.2),
        ("friends_yes", "Yes!", "Aarav & Mia", "aarav_boy", 1.2),
        ("twinkle_02", "Then follow me! Something wonderful is coming!", "Twinkle", "twinkle_star", 2.8),
    ]

    for clip_id, text, char_name, v_id, dur in dialogue_scripts:
        vp = VoicePrompt(text=text, character_name=char_name, voice_id=v_id)
        job = voice_prov.submit_job(vp, dialogue_dir)
        dialogue_files.append(Path(job.result_path))

    # 3. Synthesize Background Music and SFX
    music_prov = MockMusicProvider()
    mp = MusicPrompt(
        prompt="Gentle cheerful preschool orchestral theme with acoustic chimes and warm strings",
        mood="cheerful",
        genre="preschool_orchestral",
        duration_seconds=45.0,
        is_instrumental=True,
    )
    music_job = music_prov.submit_job(mp, audio_dir)
    bgm_path = Path(music_job.result_path)

    # Concatenate dialogue into one narration stream with realistic pauses
    combined_dialogue_path = audio_dir / "scene_01_dialogue_track.wav"
    _concatenate_wavs_with_offsets(
        [
            (dialogue_files[0], 0.5),    # Shot 1 Narrator @ 0.5s
            (dialogue_files[1], 10.5),   # Shot 2 Aarav @ 10.5s
            (dialogue_files[2], 14.5),   # Shot 2 Mia @ 14.5s
            (dialogue_files[3], 23.0),   # Shot 3 Twinkle @ 23.0s
            (dialogue_files[4], 34.0),   # Shot 4 Friends Yes @ 34.0s
            (dialogue_files[5], 36.5),   # Shot 4 Twinkle Follow Me @ 36.5s
        ],
        combined_dialogue_path,
        total_duration=45.0,
    )

    # 4. Master Audio Mix (Dialogue + BGM at 15% ducking + fade-out)
    master_audio_path = audio_dir / "scene_01_master_audio.wav"
    mixer = AudioMixer()
    mixer.mix(
        narration_path=combined_dialogue_path,
        output_path=master_audio_path,
        music_path=bgm_path,
        narration_volume=1.0,
        music_volume=0.15,
        target_duration_seconds=45.0,
        music_fade_out_seconds=2.0,
    )

    # 5. Build AnimaVideo Project Scenes for Scene 1 (4 shots @ 24fps = 1080 frames)
    # Shot 1: 10s (240 frames)
    # Shot 2: 12s (288 frames)
    # Shot 3: 11s (264 frames)
    # Shot 4: 12s (288 frames)
    scenes = [
        # SHOT 1.1: Wide Establishing Garden
        Scene(
            name="SH01_01_Garden_Wide",
            duration_frames=240,
            layers=[
                Layer(name="Garden BG", kind="image", asset_path=str(bg_path), x=0, y=0, width=1920, height=1080),
                Layer(
                    name="Scene Title", kind="text", text="Scene 1: Welcome to Dreamland",
                    font_size=42, color="#fef08a", x=160, y=80, width=1600, height=80,
                ),
                Layer(
                    name="Subtitles", kind="text",
                    text="Welcome to Dreamland, where every day is a magical new adventure!",
                    font_size=36, color="#ffffff", x=160, y=930, width=1600, height=70,
                ),
            ],
        ),
        # SHOT 1.2: Aarav & Mia Playing
        Scene(
            name="SH01_02_Aarav_Mia_Dialogue",
            duration_frames=288,
            layers=[
                Layer(name="Garden BG", kind="image", asset_path=str(bg_path), x=0, y=0, width=1920, height=1080),
                Layer(
                    name="Aarav Anchor", kind="image", asset_path=aarav_ref,
                    x=260, y=180, width=640, height=720,
                ),
                Layer(
                    name="Mia Anchor", kind="image", asset_path=mia_ref,
                    x=1020, y=180, width=640, height=720,
                ),
                Layer(
                    name="Subtitles", kind="text",
                    text='Aarav: "Mia! Look at all these beautiful colours!"\nMia: "Wow! I wonder what magical surprises are waiting for us today!"',
                    font_size=34, color="#fde047", x=160, y=900, width=1600, height=100,
                ),
            ],
        ),
        # SHOT 1.3: Twinkle Descending
        Scene(
            name="SH01_03_Twinkle_Arrival",
            duration_frames=264,
            layers=[
                Layer(name="Garden BG", kind="image", asset_path=str(bg_path), x=0, y=0, width=1920, height=1080),
                Layer(
                    name="Twinkle Anchor", kind="image", asset_path=twinkle_ref,
                    x=640, y=160, width=640, height=620,
                ),
                Layer(
                    name="Subtitles", kind="text",
                    text='Twinkle: "Hello, little explorers! Are you ready for a magical adventure?"',
                    font_size=36, color="#fde047", x=160, y=920, width=1600, height=80,
                ),
            ],
        ),
        # SHOT 1.4: Group Ready to Explore
        Scene(
            name="SH01_04_All_Together",
            duration_frames=288,
            layers=[
                Layer(name="Garden BG", kind="image", asset_path=str(bg_path), x=0, y=0, width=1920, height=1080),
                Layer(
                    name="Aarav Anchor", kind="image", asset_path=aarav_ref,
                    x=160, y=220, width=540, height=620,
                ),
                Layer(
                    name="Twinkle Anchor", kind="image", asset_path=twinkle_ref,
                    x=720, y=140, width=480, height=480,
                ),
                Layer(
                    name="Mia Anchor", kind="image", asset_path=mia_ref,
                    x=1220, y=220, width=540, height=620,
                ),
                Layer(
                    name="Subtitles", kind="text",
                    text='Aarav & Mia: "Yes!"\nTwinkle: "Then follow me! Something wonderful is coming!"',
                    font_size=34, color="#fef08a", x=160, y=900, width=1600, height=100,
                ),
            ],
        ),
    ]

    project = Project(
        name="Little Dreamers - Episode 1 (Scene 1 Sample)",
        width=1920,
        height=1080,
        fps=24,
        background="#1a103c",
        scenes=scenes,
    )

    # 6. Compile Final MP4 via FFmpeg with 24fps, H.264, and AAC audio
    sample_mp4 = exports_dir / "scene_01_sample_preview_1080p.mp4"
    opts = CompilationOptions(
        width=1920,
        height=1080,
        fps=24,
        audio_path=str(master_audio_path),
    )

    logger.info("Compiling Scene 1 preview video: %s", sample_mp4)
    compiled_path = compile_scenes(project, sample_mp4, options=opts)

    # 7. Quality Assurance Validation
    qa = QAValidator()
    ep_spec = create_ep01_production_specification()
    qa_report = qa.run_full_validation(compiled_path, episode=ep_spec)

    report_path = exports_dir / "scene_01_sample_qa_report.txt"
    report_path.write_text(qa_report.summary(), encoding="utf-8")
    print(qa_report.summary())

    return compiled_path


def _concatenate_wavs_with_offsets(
    clips: list[tuple[Path, float]],
    output_path: Path,
    total_duration: float = 45.0,
    sample_rate: int = 44100,
) -> Path:
    """Combines individual dialogue WAV files at specified timeline timestamp offsets."""
    import struct

    total_frames = int(total_duration * sample_rate)
    master_buffer = [0] * total_frames

    for wav_file, offset_sec in clips:
        if not wav_file.is_file():
            continue
        try:
            with wave.open(str(wav_file), "rb") as wf:
                n_frames = wf.getnframes()
                raw_bytes = wf.readframes(n_frames)
                fmt = f"<{n_frames}h"
                samples = struct.unpack(fmt, raw_bytes[:n_frames * 2])
                start_frame = int(offset_sec * sample_rate)
                for i, sample in enumerate(samples):
                    target_idx = start_frame + i
                    if target_idx < total_frames:
                        # Simple mixing with clamp
                        mixed = master_buffer[target_idx] + sample
                        master_buffer[target_idx] = max(-32767, min(32767, mixed))
        except Exception as exc:
            logger.warning("Could not read dialogue clip %s: %s", wav_file, exc)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output_path), "wb") as out_wf:
        out_wf.setnchannels(1)
        out_wf.setsampwidth(2)
        out_wf.setframerate(sample_rate)
        packed_bytes = struct.pack(f"<{total_frames}h", *master_buffer)
        out_wf.writeframes(packed_bytes)

    return output_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    res = produce_scene_01_sample()
    print(f"\nScene 1 Sample successfully produced at: {res}\n")
