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
