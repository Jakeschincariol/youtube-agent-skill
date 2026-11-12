#!/usr/bin/env python3
"""hookscore.py - score a YouTube hook before you waste a take on it.

Five properties, 0-100 each, and a verdict that is 60% the mean and 40% the weakest one. The
weakest-link weighting is deliberate: a hook with four strong properties and one dead one is a hook
that leaks at the dead one, and averaging hides that.

    python3 hookscore.py hooks.txt            # one hook per line, ranked
    python3 hookscore.py --hook "one line"    # score a single hook
    python3 hookscore.py --json hooks.txt     # machine-readable

WHAT THIS CAN AND CANNOT TELL YOU. Measured against 74 real short-form hooks (first 15 seconds of
auto-captions, top-8 and bottom-8 by views across five channels): it separates deliberately bad
hooks from real ones well, and it separates a creator's own hits from their own misses barely at
all. Treat a low score as a reason to look again, never a high score as a promise.

TURKISH. Hooks are scored in English and Turkish. Every word list has a Turkish side, matched on
folded text (lowercase, ı/I/İ -> i) with Turkish suffixes allowed, and the language is detected per
hook so the brevity band and the fix advice follow it. The calibration above was English-only: the
Turkish side carries the same logic, not the same evidence.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FORMULAS = json.load(open(os.path.join(HERE, "hooks.json"), encoding="utf-8"))["hooks"]

def fold(t):
    """Case-fold for both languages: Turkish dotted/dotless i collapse to plain i."""
    return t.replace("İ", "i").replace("I", "i").lower().replace("ı", "i").replace("i̇", "i")

# English rules: unchanged from the calibrated original, applied to every hook.
EN = {
 "filler": {"basically","actually","literally","just","really","very","so","kind","sort","like",
            "guys","hey","welcome","today","video","subscribe","channel"},
 "vague": {"amazing","incredible","insane","crazy","huge","massive","game","changer","secret",
           "powerful","ultimate","best","revolutionary","mind","blowing","unbelievable"},
 "you": re.compile(r"\b(you|your|you're|youre|yourself)\b", re.I),
 "stake": re.compile(r"\b(lose|lost|wasting|waste|quit|fail|broke|cost|risk|before|stop|never|die|dying|dead)\b", re.I),
 "curiosity": re.compile(r"\b(why|how|what|which|until|before|but|nobody|almost|except|reason|actually)\b", re.I),
 "closed": re.compile(r"\b(because|so that|which means)\b", re.I),
}
# Turkish rules: written for folded text, added only when the hook reads as Turkish, so an English
# hook never trips on a Turkish suffix ("chosen" is not "-sen").
TR = {
 "filler": {"yani","işte","şey","sadece","gerçekten","çok","cidden","falan","filan","arkadaşlar",
            "merhaba","selam","bugün","video","videoda","videoya","abone","kanal","kanalima","kanala"},
 "vague": {"inanilmaz","muhteşem","harika","çilgin","çilginca","efsane","devasa","müthiş","sir","sirri",
           "güçlü","nihai","devrim","devrimsel","şok","şaşirtici","mükemmel"},
 # pronouns, plus 2nd-person verb endings: yapabilirsin, biliyor musun, istersen, yaparsaniz
 "you": re.compile(r"\b(sen|senin|sana|seni|sende|senden|siz|sizin|size|sizi|sizde|sizden)\b"
                   r"|\b\w{2,}(sin|sun|sün|siniz|sunuz|sünüz|san|sen|saniz|seniz)\b", re.I),
 "stake": re.compile(r"\b(kaybet|kaybed|kayip|kaybi|boşa|israf|birak|vazgeç|başarisiz|batir|batt|mahv|"
                     r"iflas|maliyet|pahali|risk|tehlike|zarar|pişman)\w*"
                     r"|\b(önce|asla|dur|durun|öldü|ölü|bitti|biter)\b", re.I),
 "curiosity": re.compile(r"\b(neden|niye|nasil|ne|hangi|hangisi|kim|kimse|kimsenin|ama|fakat|ancak|"
                         r"meğer|neredeyse|aslinda|sebep|sebebi|sebebini|mi|mu|mü)\b"
                         r"|\b\w+(ana|ene) kadar\b", re.I),
 "closed": re.compile(r"\b(çünkü|bu yüzden|bu nedenle|yani)\b", re.I),
}
NOT_YOU = {"kesin","basin","yasin","kasin","hassasin"}
CONCRETE = re.compile(r"\b(\d[\d,.]*\s?(%|k|m|x|s|m|h)?|\$\d|\d+\s?(second|minute|hour|day|week|month|year)s?)\b", re.I)

TR_HINT = set("ve bir bu şu için ama ne da de mi mu mü çok gibi sen ben siz neden nasil daha en "
              "olan değil var yok kadar sonra önce".split())
EN_HINT = set("the and you your to is a an of in it i this that for with but why how what".split())

def lang(t):
    w = re.findall(r"[\w']+", fold(t))
    tr = 2 * len(re.findall(r"[çğışöüÇĞİŞÖÜ]", t)) + sum(1 for x in w if x in TR_HINT)
    en = sum(1 for x in w if x in EN_HINT)
    return "tr" if tr > en else "en"

def rules(t): return [EN, TR] if lang(t) == "tr" else [EN]

def hits(t, key, rs):
    f = fold(t)
    return sum(1 for r in rs for m in r[key].finditer(f) if not (r is TR and key == "you" and m.group(0) in NOT_YOU))

def words(t): return re.findall(r"[\w'%$.₺]+", fold(t))

def count_you(t, rs=None): return hits(t, "you", rs or rules(t))

def specificity(t):
    w = words(t)
    if not w: return 0
    rs = rules(t)
    nums = len(CONCRETE.findall(t))
    vague = sum(1 for x in w if any(x in r["vague"] for r in rs))
    filler = sum(1 for x in w if any(x in r["filler"] for r in rs))
    s = 34 + nums * 22 - vague * 16 - filler * 5
    # proper nouns that are not sentence-initial read as named things
    s += min(18, 6 * sum(1 for x in t.split()[1:] if x[:1].isupper()))
    return max(0, min(100, s))

def address(t):
    rs = rules(t)
    n = count_you(t, rs)
    first = 30 if count_you(" ".join(t.split()[:6]), rs) else 0
    return max(0, min(100, 26 + n * 20 + first))

def stakes(t):
    n = hits(t, "stake", rules(t))
    return max(0, min(100, 22 + n * 26 + (14 if CONCRETE.search(t) else 0)))

def curiosity(t):
    rs = rules(t)
    n = hits(t, "curiosity", rs)
    q = 18 if t.strip().endswith("?") else 0
    # a hook that resolves itself has no gap left
    closed = -18 if hits(t, "closed", rs) else 0
    return max(0, min(100, 24 + n * 17 + q + closed))

# Words that fit a spoken hook inside ~10 seconds. English: 9-24 at ~150wpm. Turkish packs suffixes
# into fewer, longer words and is spoken at ~120wpm, so the same ten seconds holds 7-20.
BAND = {"en": (9, 24), "tr": (7, 20)}

def brevity(t):
    n = len(words(t))
    if n == 0: return 0
    lo, hi = BAND[lang(t)]
    if lo <= n <= hi: return 100
    if n < lo: return max(30, 100 - (lo - n) * 11)
    return max(10, 100 - (n - hi) * 7)

PROPS = [("SPECIFICITY", specificity), ("ADDRESS", address), ("STAKES", stakes),
         ("CURIOSITY", curiosity), ("BREVITY", brevity)]

def classify(t):
    f, tr = fold(t), lang(t) == "tr"
    best, top = None, 0
    for fm in FORMULAS:
        n = sum(1 for p in fm["match"] if re.search(p, t, re.I))
        if tr: n = max(n, sum(1 for p in fm.get("match_tr", []) if re.search(p, f.strip(), re.I)))
        if n > top: best, top = fm, n
    return (best["name"] if best else "Unclassified"), top

def score(t):
    parts = {n: fn(t) for n, fn in PROPS}
    vals = list(parts.values())
    verdict = round(0.6 * (sum(vals) / len(vals)) + 0.4 * min(vals))
    name, hits = classify(t)
    return parts, verdict, name, hits

def band(v): return "STRONG" if v >= 72 else "WORKABLE" if v >= 55 else "WEAK"

def report(t, parts, verdict, name, hits, lg):
    print(f"\n  {t.strip()}")
    print(f"  {'-' * min(72, max(20, len(t.strip())))}")
    for k, v in parts.items():
        print(f"    {k:<12} {v:3d}  {'#' * (v // 5)}")
    print(f"    {'VERDICT':<12} {verdict:3d}  {band(verdict)}")
    print(f"    formula      {name}" + (f"  ({hits} pattern{'s' if hits != 1 else ''} matched)" if hits else "  (no formula matched - that is usually a summary, not a hook)"))
    low = min(parts, key=parts.get)
    print(f"    weakest      {low} - {FIX[lg][low]}")
    print(f"    language     {lg}")

FIX = {
 "en": {
  "SPECIFICITY": "swap one adjective for a number, a name or a date",
  "ADDRESS": "say 'you' in the first six words",
  "STAKES": "name what it costs them to keep doing it the current way",
  "CURIOSITY": "cut the half of the sentence that answers itself",
  "BREVITY": "9 to 24 words. Read it out loud and stop where you run out of breath",
 },
 "tr": {
  "SPECIFICITY": "bir sıfatı sayı, isim ya da tarihle değiştir",
  "ADDRESS": "ilk altı kelimede izleyiciye 'sen' diye seslen",
  "STAKES": "bunu böyle yapmaya devam etmenin ona neye mal olduğunu söyle",
  "CURIOSITY": "cümlenin kendi sorusunu cevaplayan yarısını at",
  "BREVITY": "7-20 kelime. Sesli oku, nefesin bittiği yerde kes",
 },
}

def main():
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    a = sys.argv[1:]
    as_json = "--json" in a
    a = [x for x in a if x != "--json"]
    if "--hook" in a:
        lines = [a[a.index("--hook") + 1]]
    elif a and os.path.exists(a[0]):
        lines = [l for l in open(a[0], encoding="utf-8-sig").read().splitlines() if l.strip()]
    else:
        print(__doc__); sys.exit(1 if not a else 0)
    out = []
    for t in lines:
        parts, verdict, name, hits = score(t)
        out.append({"hook": t.strip(), "properties": parts, "verdict": verdict,
                    "band": band(verdict), "formula": name, "language": lang(t), "matched": hits})
    out.sort(key=lambda r: -r["verdict"])
    if as_json:
        print(json.dumps([{k: v for k, v in r.items() if k != "matched"} for r in out],
                         indent=1, ensure_ascii=False)); return
    for r in out:
        report(r["hook"], r["properties"], r["verdict"], r["formula"], r["matched"], r["language"])
    if len(out) > 1:
        print(f"\n  winner: {out[0]['hook'].strip()}  ({out[0]['verdict']}, {out[0]['band']})\n")

if __name__ == "__main__":
    main()
