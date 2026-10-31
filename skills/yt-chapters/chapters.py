#!/usr/bin/env python3
"""chapters.py - YouTube chapters from a timestamped transcript.

    python3 chapters.py transcript.srt            # or .vtt / whisper .json
    python3 chapters.py transcript.srt --target 8 --json

Prints a description block you can paste straight under a video. YouTube's own rules, enforced here
rather than assumed: the list must start at 00:00, needs at least three entries, and each chapter
must be at least 10 seconds long. A block that breaks any of those silently does not become
chapters, which is why this checks instead of trusting.

Boundaries come from the gaps - the pauses you actually took between sections - scored by how long
the pause was and how much the vocabulary changes across it. Spoken signposts ("Reason number two",
"Step 3", "Now a twist", "Back to our shark") are taken first, because a scripted video already says
where its sections start. Titles come from your own words at the boundary - "Reason 2: Crowding" -
not from keyword counts. It is still a first draft you check, not a summariser.
"""
import json, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "yt-edit"))
from deadair import load, parse_ts  # noqa: E402  (same parser, one implementation)

STOP = set("the a an of for to in on and or is are was were be been with this that it as at by from "
           "you your i my we our they them he she but so if then than there here what which who how "
           "when where why not no yes do does did just really very like about into over out up down "
           "can could will would should have has had get got make made go going went one two".split())

NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
       "nine": 9, "ten": 10, "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5}
NUMBERED = re.compile(r"^\W*(reason|step|number|part|tip|mistake|rule|secret|fact|myth|lesson|sign)"
                      r"\s+(?:number\s+|no\.?\s+|#)?(\d+|" + "|".join(NUM) + r")\b\W*(.*)$", re.I)
TURN = re.compile(r"^\W*(now,? (a|for|let's|the|what)|now,? [a-z]+\.$|next,|finally,|back to|one more|"
                  r"here's the (twist|catch|problem)|but here's|let's start|so why|so what)(?=\W|$)", re.I)
TAIL = set("and or but the a an of to in with for that which who so as at by from its their his her".split())

def signpost(text):
    return bool(NUMBERED.match(text) or TURN.match(text))

def clean_title(text, words=7):
    t = re.sub(r"^\W*(now|so|and|but|okay|well)\b[,.]?\s*", "", text.strip(), flags=re.I)
    first = re.split(r"(?<=[.?!])\s+", t)[0]
    # a whole short sentence reads better than a clipped long one
    w = first.split() if len(first.split()) <= words + 3 else t.split()[:words]
    while len(w) > 2 and w[-1].lower().strip(",.") in TAIL: w.pop()
    t = " ".join(w).rstrip(" ,.;:!-")
    return (t[:1].upper() + t[1:]) if t else "Section"

def title_at(cues, i):
    """Title from the speaker's own words at cue i."""
    text = cues[i][2]
    m = NUMBERED.match(text)
    if m:
        kind, n, rest = m.group(1).capitalize(), m.group(2).lower(), m.group(3).strip(" .,:;-")
        n = NUM.get(n, n)
        if not rest and i + 1 < len(cues) and len(cues[i + 1][2].split()) <= 6:
            rest = cues[i + 1][2].strip(" .,:;-")
        return f"{kind} {n}: {clean_title(rest, 6)}" if rest else f"{kind} {n}"
    if len(text.split()) < 4 and i + 1 < len(cues):
        head = clean_title(text)
        if head != "Section":           # "Now a twist." -> "A twist: If cannibalism has so many benefits"
            return f"{head}: {clean_title(cues[i + 1][2], 6)}"
        text = text.rstrip(" .") + " " + cues[i + 1][2]
    return clean_title(text)

def keywords(text):
    return {w for w in re.findall(r"[a-z']{4,}", text.lower()) if w not in STOP}

def mmss(t):
    t = int(t); h, m, s = t // 3600, (t % 3600) // 60, t % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

def main():
    a = sys.argv[1:]
    as_json = "--json" in a; a = [x for x in a if x != "--json"]
    target = int(a[a.index("--target") + 1]) if "--target" in a else None
    a = [x for x in a if not x.startswith("--") and not x.isdigit()]
    if not a or not os.path.exists(a[0]): print(__doc__); sys.exit(1)
    cues = load(a[0])
    if len(cues) < 6: print("too few cues to chapter"); sys.exit(1)
    dur = cues[-1][1]
    cand = []
    for i in range(1, len(cues)):
        gap = cues[i][0] - cues[i - 1][1]
        before = " ".join(c[2] for c in cues[max(0, i - 12):i])
        after = " ".join(c[2] for c in cues[i:i + 12])
        kb, ka = keywords(before), keywords(after)
        shift = 1 - (len(kb & ka) / len(kb | ka)) if (kb | ka) else 0
        cand.append((gap * 1.6 + shift * 3.2 + (8 if signpost(cues[i][2]) else 0), cues[i][0], i))
    cand.sort(reverse=True)
    posts = sum(1 for c in cand if c[0] >= 8)
    if target is None: target = min(12, max(7, posts + 1))
    picked, MIN = [0.0], 10.0
    for _, t, i in cand:
        if len(picked) >= target: break
        if all(abs(t - p) >= MIN for p in picked) and dur - t >= MIN:
            picked.append(t)
    picked.sort()
    chapters = []
    for n, t in enumerate(picked):
        end = picked[n + 1] if n + 1 < len(picked) else dur
        first = next(k for k, c in enumerate(cues) if c[0] >= t)
        title = title_at(cues, first)
        chapters.append({"start": round(t, 2), "label": mmss(t), "draft_title": title,
                         "seconds": round(end - t, 2)})
    ok = len(chapters) >= 3 and chapters[0]["start"] == 0 and all(c["seconds"] >= MIN for c in chapters)
    if as_json:
        print(json.dumps({"valid": ok, "chapters": chapters}, indent=1)); return
    print()
    for c in chapters: print(f"  {c['label']} {c['draft_title']}")
    print(f"\n  {len(chapters)} chapters"
          f"{'' if ok else '  -- INVALID: YouTube needs 3+, a 00:00 first entry and 10s minimum each'}")
    print("  Titles are your own words at each boundary. Read them once before pasting.\n")

if __name__ == "__main__":
    main()
