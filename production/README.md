# production/

Everything needed to rebuild the video, and the video itself. No dependencies beyond a Python 3
venv with `pillow numpy matplotlib imageio-ffmpeg` (ffmpeg comes from that last one, so nothing has
to be installed system-wide).

```
pip install pillow numpy matplotlib imageio-ffmpeg
```

## What is here

| file | what it is |
|---|---|
| `final.mp4` | the deliverable — 1920×1080, 25 fps, 8:12, AAC stereo, 37 MB (git-ignored) |
| `thumbnail.png` | 1280×720 packaging asset |
| `thumbnail_feedtest.png` | the same thumbnail at 320×180, the only size that matters |
| `script.md` | hooks with scores, the beat-by-beat script with `[ON SCREEN]`, runtime check |
| `package.md` | title, thumbnail brief, description, chapters, tags, queries, pinned comment |
| `audio/*.mp3` | the nine narration takes, one per beat |
| `images/*.jpg` | the nine generated scene backgrounds + the thumbnail prop shot |
| `timeline.json` | scene start times, measured from the slowed audio |

## How it was built

```bash
python3 build_cards.py    # backgrounds -> composited 2560x1440 cards (type, rail, scrim, grain)
python3 build_audio.py    # 0.87x pacing, 0.85s gaps, music bed 21 dB down, loudnorm -16 LUFS
python3 build_thumb.py    # thumbnail + feed test
python3 render.py         # Ken Burns per card, concat, mux -> final.mp4
```

`render.py` writes `segments/` and `cards/` as it goes. Both are regenerable, and both are ignored
by `.gitignore` — the cards alone are ~36 MB of PNG, and the intermediates add up to ~300 MB.

`render.py` encodes at CRF 24, which lands around 87 MB; the shipped file is a second pass at CRF 28
(37 MB). Static type and a gently moving background survive it — checked on a frame at 3:30 before
committing to it. The source art is archived as JPEG for the same reason.

## Voice

One voice, `voice-00` from this session's audition, read at ~205 wpm raw. `build_audio.py` slows it
to 0.87x with `atempo` (pitch preserved) for ~178 wpm, which is the difference between a listicle
and a terms-of-service read. If you ever want a different pace, change `SPEED` and re-run
`build_audio.py` + `render.py`; `timeline.json` and the chapter list are regenerated from it.
