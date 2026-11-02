"""Audio subsystem for AnimaTube: Piper TTS, Edge TTS, and Whisper.cpp subtitles."""

from animatube.audio.edge_tts_wrapper import EdgeTTS
from animatube.audio.piper_tts import PiperTTS
from animatube.audio.subtitles import SubtitleGenerator

__all__ = ["PiperTTS", "EdgeTTS", "SubtitleGenerator"]
