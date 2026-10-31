#!/usr/bin/env python3
"""loudness.py - is the mix too loud, too quiet or too squashed for YouTube?

    python3 loudness.py video.mp4          # or .wav / .mp3 / .m4a
    python3 loudness.py video.mp4 --json

Measures integrated loudness (LUFS), loudness range (LRA) and true peak with ffmpeg's EBU R128
meter, then says what YouTube will do with it. YouTube plays everything back at about -14 LUFS:
a louder upload is turned DOWN, so mastering hotter buys nothing and the extra compression it took
to get there stays audible. A quieter upload is NOT turned up, so it simply sounds weak next to the
video before it.

Needs ffmpeg on PATH. That is the one dependency in this pack, and only this tool has it.
"""
import json, re, shutil, subprocess, sys

TARGET, TP_MAX = -14.0, -1.0

def measure(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vn",
                        "-af", "ebur128=peak=true:framelog=quiet", "-f", "null", "-"],
                       capture_output=True, text=True)
    summary = r.stderr[r.stderr.rfind("Summary:"):]
    get = lambda k: float(re.search(k + r":\s+(-?[\d.]+|-inf)", summary).group(1).replace("-inf", "-99"))
    return {"lufs": get("I"), "lra": get("LRA"), "true_peak": get("Peak")}

def verdict(m):
    notes = []
    d = m["lufs"] - TARGET
    if d > 1.5:
        notes.append(("LOUD", f"{m['lufs']:.1f} LUFS is {d:.1f} dB over YouTube's -14. It will be turned "
                      f"down {d:.1f} dB on playback, so export at -14 and keep the dynamics instead"))
    elif d < -2.5:
        notes.append(("QUIET", f"{m['lufs']:.1f} LUFS is {-d:.1f} dB under -14. YouTube will not turn it up - "
                      f"raise it to about -14"))
    else:
        notes.append(("ok", f"{m['lufs']:.1f} LUFS, inside the band YouTube plays back unchanged"))
    if m["lra"] < 3:
        notes.append(("SQUASHED", f"loudness range {m['lra']:.1f} LU - almost no difference between quiet and "
                      f"loud moments. Ease off the compressor/limiter; 4-8 LU suits voice-over"))
    elif m["lra"] > 15:
        notes.append(("UNEVEN", f"loudness range {m['lra']:.1f} LU - quiet lines will get lost on a phone speaker"))
    else:
        notes.append(("ok", f"loudness range {m['lra']:.1f} LU"))
    if m["true_peak"] > TP_MAX:
        notes.append(("PEAK", f"true peak {m['true_peak']:.1f} dBTP - above {TP_MAX:.0f}, risks clipping after "
                      f"YouTube re-encodes it"))
    else:
        notes.append(("ok", f"true peak {m['true_peak']:.1f} dBTP"))
    return notes

FIX = ('ffmpeg -i in.mp4 -c:v copy -af "loudnorm=I=-14:TP=-1.5:LRA=7" -c:a aac -b:a 192k out.mp4')

def main():
    a = sys.argv[1:]
    as_json = "--json" in a; a = [x for x in a if x != "--json"]
    if not a: print(__doc__); sys.exit(1)
    if not shutil.which("ffmpeg"): print("ffmpeg is not installed - this tool needs it on PATH"); sys.exit(1)
    try:
        m = measure(a[0])
    except AttributeError:
        print("could not read any audio from that file"); sys.exit(1)
    notes = verdict(m)
    if as_json:
        print(json.dumps({**m, "target": TARGET, "notes": [{"flag": f, "why": w} for f, w in notes]}, indent=1)); return
    print(f"\n  {a[0]}\n")
    for f, w in notes: print(f"    {'ok' if f == 'ok' else 'x ':<3}{f if f != 'ok' else '':<9} {w}")
    if any(f != "ok" for f, _ in notes):
        print(f"\n  one-line fix (re-encodes the audio only):\n    {FIX}")
    print()

if __name__ == "__main__":
    main()
