from __future__ import annotations

from dataclasses import dataclass, field
import json
import logging
from pathlib import Path
import tempfile
from typing import Any, Callable

from animatube.ai.interfaces import VoiceGenerationProvider
from animatube.ai.mock_providers import MockVoiceProvider, _generate_synthetic_wav
from animatube.ai.models import VoicePrompt
from animatube.ai.registry import AIProviderRegistry
from animatube.export.composer import concatenate_audio_files

logger = logging.getLogger(__name__)


@dataclass
class CharacterVoiceProfile:
    """Voice configuration specifically tuned to a distinct character personality."""
    character_name: str
    voice_id: str
    gender: str = "neutral"
    age_category: str = "preschool"  # preschool, baby, adult, celestial
    style: str = "cheerful"
    rate: str = "+0%"
    pitch: str = "+0Hz"
    stability: float = 0.8
    description: str = ""

    def to_prompt(self, text: str) -> VoicePrompt:
        return VoicePrompt(
            text=text,
            voice_id=self.voice_id,
            character_name=self.character_name,
            style=self.style,
            rate=self.rate,
            pitch=self.pitch,
            stability=self.stability,
        )


# Standard character voice profiles for Little Dreamers and preschool storytelling
DEFAULT_CHARACTER_PROFILES: list[CharacterVoiceProfile] = [
    CharacterVoiceProfile(
        character_name="Aarav",
        voice_id="aarav_boy",
        gender="male",
        age_category="preschool",
        style="adventurous",
        rate="+5%",
        pitch="+5Hz",
        description="Enthusiastic 2.5yo toddler boy, curious and playful cadence",
    ),
    CharacterVoiceProfile(
        character_name="Mia",
        voice_id="mia_girl",
        gender="female",
        age_category="preschool",
        style="cheerful",
        rate="+0%",
        pitch="+8Hz",
        description="Sweet, musical 2.5yo toddler girl with clear melodic lilt",
    ),
    CharacterVoiceProfile(
        character_name="Ellie",
        voice_id="ellie_gentle",
        gender="female",
        age_category="baby",
        style="gentle",
        rate="-5%",
        pitch="-5Hz",
        description="Gentle baby elephant, warm, soothing with soft breathy tones",
    ),
    CharacterVoiceProfile(
        character_name="Gigi",
        voice_id="gigi_peppy",
        gender="female",
        age_category="preschool",
        style="curious",
        rate="+8%",
        pitch="+6Hz",
        description="Energetic baby giraffe, bubbly, fast inquisitive inflections",
    ),
    CharacterVoiceProfile(
        character_name="Bobo",
        voice_id="bobo_puppy",
        gender="male",
        age_category="baby",
        style="playful",
        rate="+10%",
        pitch="+12Hz",
        description="Joyful, excitable puppy, high-frequency happy giggles and yips",
    ),
    CharacterVoiceProfile(
        character_name="Twinkle",
        voice_id="twinkle_star",
        gender="neutral",
        age_category="celestial",
        style="calm",
        rate="-8%",
        pitch="+15Hz",
        description="Magical smiling star, bell-like, soothing chime resonance",
    ),
    CharacterVoiceProfile(
        character_name="Narrator",
        voice_id="narrator_warm",
        gender="neutral",
        age_category="adult",
        style="storytelling",
        rate="+0%",
        pitch="+0Hz",
        description="Warm, comforting preschool storyteller narrator",
    ),
]


@dataclass
class DialogueLine:
    """Single line of character dialogue within a scene or episode."""
    character_name: str
    text: str
    audio_path: str = ""
    duration_seconds: float = 0.0
    scene_idx: int = 0


class DialogueManager:
    """
    Manages character voice profiles and generates multi-character dialogue sequences.
    """

    def __init__(self, provider: VoiceGenerationProvider | None = None) -> None:
        self.provider = provider or AIProviderRegistry.get_instance().get_voice_provider()
        self.profiles: dict[str, CharacterVoiceProfile] = {
            p.character_name: p for p in DEFAULT_CHARACTER_PROFILES
        }

    def get_profile(self, character_name: str) -> CharacterVoiceProfile:
        return self.profiles.get(
            character_name,
            CharacterVoiceProfile(character_name=character_name, voice_id="default"),
        )

    def set_profile(self, profile: CharacterVoiceProfile) -> None:
        self.profiles[profile.character_name] = profile

    def generate_dialogue_line(self, line: DialogueLine, output_dir: str | Path) -> DialogueLine:
        """Generates speech audio for an individual dialogue line using its character profile."""
        profile = self.get_profile(line.character_name)
        prompt = profile.to_prompt(line.text)
        dest_dir = Path(output_dir).resolve()
        dest_dir.mkdir(parents=True, exist_ok=True)

        job = self.provider.generate_sync(prompt, dest_dir / f"temp_{line.character_name}.wav")
        if job.result_path and Path(job.result_path).is_file():
            line.audio_path = job.result_path
            line.duration_seconds = job.usage.duration_generated
        return line

    def generate_conversation(
        self,
        lines: list[DialogueLine],
        output_path: str | Path,
        pause_seconds: float = 0.4,
        progress_callback: Callable[[float, str], None] | None = None,
    ) -> Path:
        """
        Synthesizes an entire multi-character conversation and concatenates lines into one audio file.
        """
        dest = Path(output_path).resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)

        audio_parts: list[Path] = []
        total = len(lines)
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            for idx, line in enumerate(lines):
                if progress_callback:
                    progress_callback(float(idx) / max(1, total), f"Generating line {idx + 1}/{total} ({line.character_name})...")

                line_file = temp_path / f"line_{idx:03d}_{line.character_name}.wav"
                profile = self.get_profile(line.character_name)
                prompt = profile.to_prompt(line.text)
                job = self.provider.submit_job(prompt, temp_path)
                
                # Wait for finish
                import time
                while not job.is_finished():
                    time.sleep(0.05)
                    job = self.provider.get_job_status(job.job_id)

                if job.result_path and Path(job.result_path).is_file():
                    audio_parts.append(Path(job.result_path))
                    line.audio_path = job.result_path
                    line.duration_seconds = job.usage.duration_generated

            if not audio_parts:
                raise RuntimeError("No dialogue lines were generated successfully.")

            if progress_callback:
                progress_callback(0.9, "Concatenating conversation lines...")

            if len(audio_parts) == 1:
                import shutil
                shutil.copy2(audio_parts[0], dest)
            else:
                concatenate_audio_files(audio_parts, dest)

        if progress_callback:
            progress_callback(1.0, "Conversation audio ready.")
        return dest
