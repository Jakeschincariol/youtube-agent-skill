#!/usr/bin/env python3
"""hookscore.py - score a YouTube hook before you waste a take on it.

Five properties, 0-100 each, and a verdict that is 60% the mean and 40% the weakest one. The
weakest-link weighting is deliberate: a hook with four strong properties and one dead one is a hook
that leaks at the dead one, and averaging hides that.

    python3 hookscore.py hooks.txt            # one hook per line, ranked
    python3 hookscore.py --hook "one line"    # score a single hook
    python3 hookscore.py --json hooks.txt     # machine-readable
    python3 hookscore.py --narrated hooks.txt # voice-over / faceless explainer mode

NARRATED MODE. The default panel rewards a creator talking to camera ("you" in the first six
words). A narrated explainer opens differently: a concrete image the viewer can picture, a twist
on what they assumed, and a question. --narrated swaps ADDRESS for IMAGE and STAKES for SURPRISE,
and scores BREVITY per sentence, because a voice-over hook is two or three short lines, not one.

WHAT THIS CAN AND CANNOT TELL YOU. Measured against 74 real short-form hooks (first 15 seconds of
auto-captions, top-8 and bottom-8 by views across five channels): it separates deliberately bad
hooks from real ones well, and it separates a creator's own hits from their own misses barely at
all. Treat a low score as a reason to look again, never a high score as a promise.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FORMULAS = json.load(open(os.path.join(HERE, "hooks.json")))["hooks"]

FILLER = {"basically","actually","literally","just","really","very","so","kind","sort","like",
          "guys","hey","welcome","today","video","subscribe","channel"}
VAGUE = {"amazing","incredible","insane","crazy","huge","massive","game","changer","secret",
         "powerful","ultimate","best","revolutionary","mind","blowing","unbelievable"}
CONCRETE = re.compile(r"\b(\d[\d,.]*\s?(%|k|m|x|s|m|h)?|\$\d|\d+\s?(second|minute|hour|day|week|month|year)s?)\b", re.I)
YOU = re.compile(r"\b(you|your|you're|youre|yourself)\b", re.I)
STAKE = re.compile(r"\b(lose|lost|wasting|waste|quit|fail|broke|cost|risk|before|stop|never|die|dying|dead)\b", re.I)
CURIOSITY = re.compile(r"\b(why|how|what|which|until|before|but|nobody|almost|except|reason|actually)\b", re.I)

# narrated mode: things a viewer can picture, and words that turn an assumption over
DEMONSTRATIVE = re.compile(r"\b(this|these|that|those|meet|here's|here is)\s+(?!is\b|was\b|video\b|one\b)[a-z]+", re.I)
VISUAL = {"shark","spider","snake","ant","ants","bee","wasp","fish","frog","toad","bird","owl","bear",
          "wolf","lion","tiger","whale","octopus","squid","crab","beetle","mantis","worm","virus",
          "bacteria","cell","cells","parasite","fungus","plant","tree","flower","seed","egg","eggs",
          "baby","babies","mother","father","brother","brothers","sister","sisters","sibling","siblings",
          "body","bodies","brain","heart","blood","bone","bones","skull","teeth","tooth","eye","eyes",
          "skin","hand","mouth","stomach","womb","corpse","grave","island","cave","ocean","volcano",
          "desert","ice","river","planet","moon","sun","star","stars","storm","fire","city","tomb",
          "mummy","statue","machine","ship","plane","village","tribe","king","queen","soldier"}
SURPRISE = re.compile(r"\b(but|even|before|not|isn't|wasn't|don't|doesn't|never|only|actually|"
                      r"instead|yet|still|without|nobody|no one|wrong|myth|mistake|opposite|"
                      r"strange|weird|impossible|backwards|alive|own|always|right\?)(?=\W|$)", re.I)

def words(t): return re.findall(r"[a-z0-9'%$.]+", t.lower())

def specificity(t):
    w = words(t)
    if not w: return 0
    nums = len(CONCRETE.findall(t))
    vague = sum(1 for x in w if x in VAGUE)
    filler = sum(1 for x in w if x in FILLER)
    s = 34 + nums * 22 - vague * 16 - filler * 5
    # proper nouns that are not sentence-initial read as named things
    s += min(18, 6 * sum(1 for x in t.split()[1:] if x[:1].isupper()))
    return max(0, min(100, s))

def address(t):
    n = len(YOU.findall(t))
    first = 30 if YOU.search(" ".join(t.split()[:6])) else 0
    return max(0, min(100, 26 + n * 20 + first))

def stakes(t):
    n = len(STAKE.findall(t))
    return max(0, min(100, 22 + n * 26 + (14 if CONCRETE.search(t) else 0)))

def curiosity(t):
    n = len(CURIOSITY.findall(t))
    q = 18 if t.strip().endswith("?") else 0
    # a hook that resolves itself has no gap left
    closed = -18 if re.search(r"\b(because|so that|which means)\b", t, re.I) else 0
    return max(0, min(100, 24 + n * 17 + q + closed))

def brevity(t):
    n = len(words(t))
    if n == 0: return 0
    # 9-24 words is the band a spoken hook lands in at ~150wpm inside 10 seconds
    if 9 <= n <= 24: return 100
    if n < 9:  return max(30, 100 - (9 - n) * 11)
    return max(10, 100 - (n - 24) * 7)

def image(t):
    w = words(t)
    if not w: return 0
    demo = 30 if DEMONSTRATIVE.search(t) else 0
    seen = len({x for x in w if x in VISUAL})
    return max(0, min(100, 22 + demo + seen * 14))

def surprise(t):
    n = len(SURPRISE.findall(t))
    flip = 16 if re.search(r"\b(not|isn't|wasn't)\b[^.?!]*[.?!]\s*(it's|it is|this is|that's)\b", t, re.I) else 0
    return max(0, min(100, 22 + n * 16 + flip))

def sentence_brevity(t):
    sents = [x for x in re.split(r"(?<=[.?!])\s+", t.strip()) if words(x)]
    if not sents: return 0
    total = sum(len(words(x)) for x in sents)
    avg = total / len(sents)
    # short spoken lines, and the whole hook inside ~15 seconds (about 38 words at 150wpm)
    s = 100 if avg <= 12 else max(20, 100 - (avg - 12) * 8)
    if total > 38: s -= (total - 38) * 4
    return max(10, min(100, round(s)))

PROPS = [("SPECIFICITY", specificity), ("ADDRESS", address), ("STAKES", stakes),
         ("CURIOSITY", curiosity), ("BREVITY", brevity)]
NARRATED_PROPS = [("SPECIFICITY", specificity), ("IMAGE", image), ("SURPRISE", surprise),
                  ("CURIOSITY", curiosity), ("BREVITY", sentence_brevity)]

def classify(t):
    best, hits = None, 0
    for f in FORMULAS:
        n = sum(1 for p in f["match"] if re.search(p, t, re.I))
        if n > hits: best, hits = f, n
    return (best["name"] if best else "Unclassified"), hits

def score(t, props=PROPS):
    parts = {n: fn(t) for n, fn in props}
    vals = list(parts.values())
    verdict = round(0.6 * (sum(vals) / len(vals)) + 0.4 * min(vals))
    name, hits = classify(t)
    return parts, verdict, name, hits

def band(v): return "STRONG" if v >= 72 else "WORKABLE" if v >= 55 else "WEAK"

def report(t, parts, verdict, name, hits):
    print(f"\n  {t.strip()}")
    print(f"  {'-' * min(72, max(20, len(t.strip())))}")
    for k, v in parts.items():
        print(f"    {k:<12} {v:3d}  {'#' * (v // 5)}")
    print(f"    {'VERDICT':<12} {verdict:3d}  {band(verdict)}")
    print(f"    formula      {name}" + (f"  ({hits} pattern{'s' if hits != 1 else ''} matched)" if hits else "  (no formula matched - that is usually a summary, not a hook)"))
    low = min(parts, key=parts.get)
    print(f"    weakest      {low} - {FIX[low]}")

FIX = {
 "SPECIFICITY": "swap one adjective for a number, a name or a date",
 "ADDRESS": "say 'you' in the first six words",
 "STAKES": "name what it costs them to keep doing it the current way",
 "CURIOSITY": "cut the half of the sentence that answers itself",
 "BREVITY": "9 to 24 words. Read it out loud and stop where you run out of breath",
 "IMAGE": "open on one thing the viewer can picture - 'this shark', not 'some animals'",
 "SURPRISE": "turn an assumption over - 'that's not a mistake, it's a strategy'",
}

def main():
    a = sys.argv[1:]
    as_json = "--json" in a
    props = NARRATED_PROPS if "--narrated" in a else PROPS
    a = [x for x in a if x not in ("--json", "--narrated")]
    if "--hook" in a:
        lines = [a[a.index("--hook") + 1]]
    elif a and os.path.exists(a[0]):
        lines = [l for l in open(a[0]).read().splitlines() if l.strip()]
    else:
        print(__doc__); sys.exit(1 if not a else 0)
    out = []
    for t in lines:
        parts, verdict, name, hits = score(t, props)
        out.append({"hook": t.strip(), "properties": parts, "verdict": verdict,
                    "band": band(verdict), "formula": name, "matched": hits})
    out.sort(key=lambda r: -r["verdict"])
    if as_json:
        print(json.dumps([{k: v for k, v in r.items() if k != "matched"} for r in out], indent=1)); return
    for r in out:
        report(r["hook"], r["properties"], r["verdict"], r["formula"], r["matched"])
    if len(out) > 1:
        print(f"\n  winner: {out[0]['hook'].strip()}  ({out[0]['verdict']}, {out[0]['band']})\n")

if __name__ == "__main__":
    main()
