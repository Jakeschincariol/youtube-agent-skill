# AnimaTube desktop editor (MVP)

AnimaTube is a local-first desktop editor for assembling simple animated YouTube scenes. This first increment provides editable text/shape/image layers, basic keyframe animation, portable project files, and MP4 video-only export.

## Requirements

- Python 3.10+
- PySide6 6.6+
- FFmpeg installed separately and available on `PATH` for MP4 export

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-animatube.txt
python -m animatube
```

On macOS/Linux, activate with `source .venv/bin/activate`.

## Current MVP scope

- Create text, rectangle, ellipse and image layers.
- Drag layers on the preview canvas.
- Set a timeline frame and create position/scale/rotation/opacity keyframes.
- Save/open `.anima` project files; imported image assets are copied into a sibling asset folder.
- Export the active scene to H.264 MP4 with FFmpeg.

## Automated Video Production Pipeline

In addition to the interactive desktop editor, AnimaTube includes an automated, local-first video production pipeline:

```powershell
# Run the end-to-end video production pipeline
python -m animatube.pipeline --output-dir output/devops_2027 --project-name DevOps_2027_Roadmap
```

Pipeline capabilities:
- **Local Script & Storyboard**: Structured JSON output via local Ollama inference with deterministic fallback.
- **Local Audio Narration**: Piper TTS synthesis (`.wav`) with precise word/timing measurement.
- **Subtitles**: Whisper.cpp speech-to-text generating `.srt` and `.vtt` subtitles.
- **1080p DevOps Diagrams**: Programmatic generation of Linux, Git, Docker, Jenkins, and AWS visual assets.
- **AnimaTube Project Assembly**: Generates multi-scene `.anima` project files.
- **Kdenlive Handoff**: Generates `.kdenlive` (MLT XML) project files with synced video and audio tracks.
- **Packaging & SEO**: Generates a high-contrast thumbnail, verified YouTube metadata, and `chapters.txt`.
- **Media Manifest**: Comprehensive `manifest.json` tracking all assets and SHA-256 digests.

## Local Ollama foundation

The Little Dreamers hybrid production architecture uses Ollama on the creator's computer for story, dialogue and storyboard intelligence, while media generation is routed through replaceable cloud-provider adapters. The existing desktop editor and FFmpeg renderer remain the production shell; Google Antigravity is used for engineering, not required at runtime.

The reusable Ollama client discovers installed models instead of assuming a fixed model name:

```powershell
# Optional: select a model when more than one is installed
$env:OLLAMA_MODEL = "qwen2.5:7b"

# Check local Ollama connectivity and installed models
python -c "from animatube.ai import OllamaClient; print(OllamaClient().health_check())"

# Run the isolated unit tests (does not require Ollama to be running)
python -m unittest discover -s tests -p "test_ollama_client.py" -v
```

The default Ollama endpoint is loopback-only at `http://127.0.0.1:11434`. Do not expose the unauthenticated local API publicly. If multiple models are installed, set `OLLAMA_MODEL` or pass a model explicitly. See [the hybrid production architecture](../docs/production_studio/HYBRID_AI_PRODUCTION_ARCHITECTURE.md) and [the implementation roadmap](../docs/production_studio/IMPLEMENTATION_ROADMAP.md). For the Antigravity terminal setup, live Ollama connectivity check, and Episode 1 guardrails, see [the Antigravity + Ollama workflow](../docs/production_studio/ANTIGRAVITY_OLLAMA_WORKFLOW.md).

The current generic Ollama script generator is specific to the DevOps sample pipeline; it is not the Little Dreamers story planner. The dedicated cartoon planning service is a later roadmap phase. The six approved character references and Episode 1 canonical storyboard remain protected.

## YouTube Channel Setup

Use the **Channel Setup** button in the desktop toolbar to create a local channel profile and launch checklist. Profiles are stored separately from video projects under:

```text
%USERPROFILE%\\AnimaTube\\Channels\\
```

The wizard captures channel identity, handle, audience, content pillars, About description, brand details, image paths, trailer script, featured video and starter playlists. New profiles default to the requested faceless animation/storytelling direction in Telugu and English.

This is a planning workspace only. It does not create a YouTube channel, connect a Google account, upload videos or publish content. Create the actual channel through YouTube and use the checklist to track setup. See [the channel manager roadmap](../docs/YOUTUBE_CHANNEL_MANAGER_ROADMAP.md).
