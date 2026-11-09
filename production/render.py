#!/usr/bin/env python3
"""Render the 1080p video: Ken Burns per card, hard cuts on the beat boundary, then mux the mix.wav.

Each scene is encoded separately (cheap, restartable), concatenated with the stream copy, and only
then married to audio.
"""
import json, os, subprocess, sys
import imageio_ffmpeg

HERE = os.path.dirname(os.path.abspath(__file__))
FF = imageio_ffmpeg.get_ffmpeg_exe()
CARDS = os.path.join(HERE, "cards")
SEG = os.path.join(HERE, "segments")
os.makedirs(SEG, exist_ok=True)

FPS = 25
ZOOM = 0.065
TAIL = 0.0

meta = json.load(open(os.path.join(HERE, "timeline.json")))
scenes = meta["scenes"]
total = meta["total"] + TAIL


def run(args):
    p = subprocess.run([FF, "-y", "-v", "error", *args], capture_output=True, text=True)
    if p.returncode:
        print(p.stderr[-3000:])
        sys.exit(1)


def scene_duration(i):
    start = scenes[i]["start"]
    end = scenes[i + 1]["start"] if i + 1 < len(scenes) else total
    return round(end - start, 3)


def render_scene(i):
    dur = scene_duration(i)
    nf = max(2, int(round(dur * FPS)))
    card = os.path.join(CARDS, f"card{i:02d}.png")
    out = os.path.join(SEG, f"seg{i:02d}.mp4")
    # alternate push-in / pull-out so cuts do not feel mechanical
    zexpr = (f"1+{ZOOM}*on/{nf}" if i % 2 == 0 else f"{1+ZOOM}-{ZOOM}*on/{nf}")
    vf = (
        f"zoompan=z='{zexpr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d=1:s=1920x1080:fps={FPS},"
        f"fade=t=in:st=0:d=0.30,fade=t=out:st={max(0.0, dur-0.30):.2f}:d=0.30,"
        f"format=yuv420p"
    )
    run(["-loop", "1", "-framerate", str(FPS), "-i", card, "-t", f"{dur}",
         "-vf", vf, "-r", str(FPS),
         "-c:v", "libx264", "-preset", "medium", "-crf", "24",
         "-x264-params", "keyint=50:min-keyint=25:scenecut=0", out])
    print(f"  seg{i:02d}  {dur:6.1f}s")
    return out


if __name__ == "__main__":
    print(f"rendering {len(scenes)} scenes, {total:.1f}s total")
    paths = [render_scene(i) for i in range(len(scenes))]

    lst = os.path.join(SEG, "concat.txt")
    with open(lst, "w") as f:
        for p in paths:
            f.write(f"file '{p}'\n")

    silent = os.path.join(HERE, "video_silent.mp4")
    run(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent])

    final = os.path.join(HERE, "final.mp4")
    run(["-i", silent, "-i", os.path.join(HERE, "mix.wav"),
         "-map", "0:v:0", "-map", "1:a:0",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
         "-shortest", "-movflags", "+faststart", final])
    size = os.path.getsize(final) / 1e6
    print(f"final.mp4  {size:.1f} MB")
