#!/usr/bin/env python3
"""Voice pacing, spacing, music bed, and the timeline the renderer reads.

Raw TTS came out at ~205 wpm. Slowed to 0.87x (pitch preserved) for ~178 wpm, which is where a
listicle stops sounding like a disclaimer. 0.85 s of air between beats so the cuts land.

Outputs: voice.wav, music.wav, timeline.json
"""
import json, os, re, subprocess, wave
import numpy as np
import imageio_ffmpeg

HERE = os.path.dirname(os.path.abspath(__file__))
FF = imageio_ffmpeg.get_ffmpeg_exe()
SR = 48000
SPEED = 0.87
LEAD = 0.35      # before the first word
GAP = 0.85       # between beats

AUDIO = os.path.join(HERE, "audio")
CLIPS = ["s01-hook", "s02-lever1", "s03-lever2", "s04-lever3", "s05-lever4",
         "s06-lever5", "s07-lever6", "s08-lever7", "s09-close"]


def probe_duration(path):
    out = subprocess.run([FF, "-i", path], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out)
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def slowdown(src, dst):
    subprocess.run([FF, "-y", "-v", "error", "-i", src,
                    "-filter:a", f"atempo={SPEED}",
                    "-ar", str(SR), "-ac", "1", dst], check=True)
    return probe_duration(dst)


def read_wav_mono(path):
    with wave.open(path, "rb") as w:
        assert w.getnchannels() == 1, w.getnchannels()
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0


def write_wav(path, mono, sr=SR):
    data = (np.clip(mono, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(data.tobytes())


# ---------------------------------------------------------------- voice track
def build_voice():
    parts, timeline, t = [], [], LEAD / SPEED  # lead is trimmed after the fact, see below
    t = 0.0
    parts.append(np.zeros(int(LEAD * SR), dtype=np.float32))
    t += LEAD
    for i, name in enumerate(CLIPS):
        dst = os.path.join(HERE, "audio", f"{name}.slow.wav")
        dur = slowdown(os.path.join(AUDIO, f"{name}.mp3"), dst)
        clip = read_wav_mono(dst)
        parts.append(clip)
        timeline.append({"scene": i, "file": name, "start": round(t, 3), "dur": round(dur, 3)})
        t += dur
        if i < len(CLIPS) - 1:
            parts.append(np.zeros(int(GAP * SR), dtype=np.float32))
            t += GAP
    voice = np.concatenate(parts + [np.zeros(int(2.0 * SR), dtype=np.float32)])  # tail for the final fade
    write_wav(os.path.join(HERE, "voice_raw.wav"), voice)
    return timeline, len(voice) / SR


# ---------------------------------------------------------------- music bed
def build_music(n_samples):
    """Soft detuned pad, four chords, no percussion. Deliberately boring: it is a floor, not a tune."""
    rng = np.random.default_rng(11)
    n = n_samples + SR * 6
    t = np.arange(n, dtype=np.float32) / SR

    # A minor - F major - C major - G major, roots two octaves down
    chords = [
        [220.00, 261.63, 329.63],   # Am
        [174.61, 220.00, 261.63],   # F
        [130.81, 196.00, 261.63],   # C
        [196.00, 246.94, 293.66],   # G
    ]
    bar = 13.0  # seconds per chord
    out = np.zeros((n, 2), dtype=np.float32)

    idx = (t // bar).astype(np.int32)
    local = (t % bar) / bar
    # raised-cosine envelope per bar = no clicks at the change
    env = 0.5 - 0.5 * np.cos(2 * np.pi * np.clip(local, 0, 1))
    env = 0.35 + 0.65 * env

    for ci, freqs in enumerate(chords):
        mask = (idx % 4) == ci
        if not mask.any():
            continue
        tt = t[mask]
        seg = np.zeros((tt.size, 2), dtype=np.float32)
        for f in freqs:
            for ch, det in ((0, 0.9985), (1, 1.0015)):
                ph = rng.uniform(0, 2 * np.pi)
                for h, amp in ((1, 0.55), (2, 0.18), (3, 0.07)):
                    seg[:, ch] += amp * np.sin(2 * np.pi * f * h * det * tt + ph * h)
        seg *= env[mask][:, None] * 0.5
        out[mask] += seg

    # slow swell so 8 minutes of the same pad does not flatten out
    swell = 0.75 + 0.25 * np.sin(2 * np.pi * t / 47.0)
    out *= swell[:, None]

    # low level air
    air = rng.normal(0, 1, (n, 2)).astype(np.float32) * 0.004
    kern = np.ones(220, dtype=np.float32) / 220.0
    for ch in range(2):
        air[:, ch] = np.convolve(air[:, ch], kern, mode="same")
    out += air

    out = out[:n_samples]
    # fades
    fi, fo = int(SR * 4), int(SR * 6)
    out[:fi] *= np.linspace(0, 1, fi)[:, None]
    out[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return out


def write_wav_stereo(path, data, sr=SR):
    d = (np.clip(data, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(d.reshape(-1).tobytes())


def mix(voice_path, music_path, total_s):
    """Music sits 21 dB under the voice, measured, not guessed."""
    v = read_wav_mono(voice_path)
    m = build_music(len(v))

    speech = v[np.abs(v) > 0.02]
    v_rms = float(np.sqrt(np.mean(speech ** 2))) if speech.size else 0.05
    m_rms = float(np.sqrt(np.mean(m ** 2))) or 1e-6
    target = v_rms * 10 ** (-21 / 20)
    m *= target / m_rms
    print(f"voice rms {20*np.log10(v_rms):.1f} dBFS · music rms {20*np.log10(m_rms*target/m_rms):.1f} dBFS")

    write_wav_stereo(music_path, m)

    # loudness-normalised final mix
    final = os.path.join(HERE, "mix.wav")
    subprocess.run([FF, "-y", "-v", "error",
                    "-i", voice_path,
                    "-i", music_path,
                    "-filter_complex",
                    "[0:a]aformat=channel_layouts=stereo[vc];"
                    "[vc][1:a]amix=inputs=2:duration=first:dropout_transition=0,"
                    "loudnorm=I=-16:TP=-1.5:LRA=11[a]",
                    "-map", "[a]", "-ar", str(SR), final], check=True)
    return final


if __name__ == "__main__":
    timeline, total = build_voice()
    print(f"voice {total:.1f}s = {int(total//60)}:{total%60:04.1f}")
    final = mix(os.path.join(HERE, "voice_raw.wav"), os.path.join(HERE, "music.wav"), total)
    timeline_total = total
    meta = {"total": round(timeline_total, 3), "speed": SPEED, "scenes": timeline}
    json.dump(meta, open(os.path.join(HERE, "timeline.json"), "w"), indent=1)
    print("wrote", final, "and timeline.json")
    for s in timeline:
        m, sec = divmod(s["start"], 60)
        print(f'  {s["file"]:12s} {int(m)}:{sec:04.1f}  ({s["dur"]:.1f}s)')
