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

## Not included in this increment

Audio mixing/recording, text-to-speech, scene transitions, undo/redo, autosave, OAuth, YouTube uploads, scheduling, and packaged installers. The app does not connect to YouTube or publish anything. These should be separate, tested follow-up features; publishing must require an explicit confirmation step.

## Export note

The initial renderer exports the active scene as video-only. It does not claim to render audio tracks. Use a 16:9, 9:16 or 1:1 project canvas; FFmpeg must support `libx264`.
