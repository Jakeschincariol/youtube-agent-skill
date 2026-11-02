# AnimaVideo — AI Provider Integrations & CLI Guide

This document describes the modular AI provider architecture, CLI commands, and supported capabilities for Video, Voice, and Music generation in AnimaVideo.

---

## 1. Modular Provider Architecture

AnimaVideo uses modular provider adapters (`animatube.ai.interfaces`) allowing creators to switch AI backends without changing the editor or pipeline:

| Capability | Built-in Default (Offline / Free) | Commercial / Cloud Options |
| :--- | :--- | :--- |
| **Video Generation** | `MockVideoProvider` (Local synthetic 1080p MP4) | Google Veo / Flow, Luma Dream Machine, Runway Gen-3 |
| **Voice / Speech** | `MockVoiceProvider`, Piper TTS (CPU Neural), Edge-TTS | ElevenLabs, OpenAI Audio |
| **Music / SFX** | `MockMusicProvider` (Procedural WAV Chords & Tones) | Suno, Udio, Meta AudioCraft / MusicGen |

---

## 2. CLI Usage (`animatube.ai.cli`)

AnimaVideo provides a command-line interface for video, voice, and music generation:

### List Providers
```bash
python -m animatube.ai.cli providers --type all
```

### Video Generation
```bash
# Text-to-Video
python -m animatube.ai.cli video \
  --prompt "Aarav giving a joyful wave in a colorful magical garden" \
  --duration 4.0 \
  --camera pan_right \
  --output-dir output/scenes

# Image-to-Video with Character Anchor Lock
python -m animatube.ai.cli video \
  --prompt "Mia dancing and swaying to a cheerful melody" \
  --reference-image little-dreamers/flow_ready/mia_flow_anchor.png \
  --duration 4.0 \
  --camera zoom_in \
  --output-dir output/scenes
```

### Voice & Dialogue Generation
```bash
python -m animatube.ai.cli voice \
  --text "Hello, little explorers! Are you ready for a magical adventure?" \
  --character "Twinkle" \
  --voice-id "twinkle_star" \
  --style "cheerful" \
  --output-dir output/dialogue
```

### Music & Sound Effects Generation
```bash
# Background Music
python -m animatube.ai.cli music \
  --prompt "Gentle acoustic guitar with soft glockenspiel chimes" \
  --mood "cheerful" \
  --genre "preschool_orchestral" \
  --duration 30.0 \
  --output-dir output/music

# Sound Effect (SFX)
python -m animatube.ai.cli music \
  --prompt "Magical fairy sparkle chime" \
  --mood "playful" \
  --duration 3.0 \
  --sfx \
  --output-dir output/sfx
```

### Credential Management
```bash
python -m animatube.ai.cli credentials set elevenlabs <YOUR_KEY>
python -m animatube.ai.cli credentials list
```

---

## 3. Zero-Cost CI Testing Policy

- Automated CI tests **never** execute paid external API calls.
- `MockVideoProvider`, `MockVoiceProvider`, and `MockMusicProvider` are selected automatically in test mode.
- Mock providers produce genuine, playable media files (valid H.264/MP4 and 44.1/48kHz WAV) so downstream FFmpeg rendering, audio ducking, and ffprobe validation are completely verified during continuous integration.
