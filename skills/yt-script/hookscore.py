#!/usr/bin/env python3
"""Score YouTube hook drafts with a transparent editorial heuristic.

This is a deterministic checklist, not a performance predictor or an empirical
claim about expected views, retention, CTR, or audience response.

Usage:
    python hookscore.py hooks.txt
    python hookscore.py --hook "one line"
    python hookscore.py --json hooks.txt
"""
import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCORE_TYPE = "editorial_heuristic_not_performance_prediction"

with (HERE / "hooks.json").open(encoding="utf-8") as handle:
    FORMULAS = json.load(handle)["hooks"]

FILLER = {"basically", "actually", "literally", "just", "really", "very", "so", "kind", "sort", "like",
          "guys", "hey", "welcome", "today", "video", "subscribe", "channel"}
VAGUE = {"amazing", "incredible", "insane", "crazy", "huge", "massive", "game", "changer", "secret",
         "powerful", "ultimate", "best", "revolutionary", "mind", "blowing", "unbelievable"}
CONCRETE = re.compile(r"\b(\d[\d,.]*\s?(%|k|m|x|s|m|h)?|\$\d|\d+\s?(second|minute|hour|day|week|month|year)s?)\b", re.I)
YOU = re.compile(r"\b(you|your|you're|youre|yourself)\b", re.I)
STAKE = re.compile(r"\b(lose|lost|wasting|waste|quit|fail|broke|cost|risk|before|stop|never|die|dying|dead)\b", re.I)
CURIOSITY = re.compile(r"\b(why|how|what|which|until|before|but|nobody|almost|except|reason|actually)\b", re.I)

def words(text):
    return re.findall(r"[a-z0-9'%$.]+", text.lower())

def specificity(text):
    tokens = words(text)
    if not tokens:
        return 0
    numbers = len(CONCRETE.findall(text))
    vague = sum(token in VAGUE for token in tokens)
    filler = sum(token in FILLER for token in tokens)
    score = 34 + numbers * 22 - vague * 16 - filler * 5
    score += min(18, 6 * sum(1 for word in text.split()[1:] if word[:1].isupper()))
    return max(0, min(100, score))

def address(text):
    count = len(YOU.findall(text))
    first_six = 30 if YOU.search(" ".join(text.split()[:6])) else 0
    return max(0, min(100, 26 + count * 20 + first_six))

def stakes(text):
    count = len(STAKE.findall(text))
    return max(0, min(100, 22 + count * 26 + (14 if CONCRETE.search(text) else 0)))

def curiosity(text):
    count = len(CURIOSITY.findall(text))
    question = 18 if text.strip().endswith("?") else 0
    resolved = -18 if re.search(r"\b(because|so that|which means)\b", text, re.I) else 0
    return max(0, min(100, 24 + count * 17 + question + resolved))

def brevity(text):
    count = len(words(text))
    if count == 0:
        return 0
    if 9 <= count <= 24:
        return 100
    if count < 9:
        return max(30, 100 - (9 - count) * 11)
    return max(10, 100 - (count - 24) * 7)

PROPERTIES = [
    ("SPECIFICITY", specificity),
    ("ADDRESS", address),
    ("STAKES", stakes),
    ("CURIOSITY", curiosity),
    ("BREVITY", brevity),
]

FIXES = {
    "SPECIFICITY": "replace a vague adjective with a verifiable detail, if one is available",
    "ADDRESS": "make the intended viewer clear; do not force the word 'you'",
    "STAKES": "explain a real consequence without exaggerating it",
    "CURIOSITY": "leave a useful question open without hiding the promised answer",
    "BREVITY": "read it aloud and remove words that do not earn their place",
}

def classify(text):
    best, hits = None, 0
    for formula in FORMULAS:
        matched = sum(bool(re.search(pattern, text, re.I)) for pattern in formula["match"])
        if matched > hits:
            best, hits = formula, matched
    return (best["name"] if best else "Unclassified"), hits

def score(text):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("hook must be a non-empty string")
    parts = {name: scorer(text) for name, scorer in PROPERTIES}
    values = list(parts.values())
    verdict = round(0.6 * (sum(values) / len(values)) + 0.4 * min(values))
    formula, hits = classify(text)
    return {
        "hook": text.strip(),
        "properties": parts,
        "verdict": verdict,
        "band": band(verdict),
        "formula": formula,
        "matched": hits,
        "score_type": SCORE_TYPE,
    }

def band(value):
    return "STRONG" if value >= 72 else "WORKABLE" if value >= 55 else "WEAK"

def report(result):
    text = result["hook"]
    print(f"\n  {text}")
    print(f"  {'-' * min(72, max(20, len(text)))}")
    for name, value in result["properties"].items():
        print(f"    {name:<12} {value:3d}  {'#' * (value // 5)}")
    print(f"    {'VERDICT':<12} {result['verdict']:3d}  {result['band']}")
    print(f"    formula      {result['formula']} ({result['matched']} pattern(s) matched)")
    weakest = min(result["properties"], key=result["properties"].get)
    print(f"    weakest      {weakest} - {FIXES[weakest]}")
    print("    note         editorial heuristic only; not a performance prediction")

def read_hooks(path):
    try:
        lines = [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"cannot read hook file: {exc}") from exc
    if not lines:
        raise ValueError("hook file contains no non-empty lines")
    return lines

def build_parser():
    parser = argparse.ArgumentParser(description="Score YouTube hook drafts using an editorial heuristic.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("file", nargs="?", help="UTF-8 text file, one hook per line")
    source.add_argument("--hook", help="score one hook")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    return parser

def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        hooks = [args.hook] if args.hook is not None else read_hooks(args.file)
        results = sorted((score(hook) for hook in hooks), key=lambda item: -item["verdict"])
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return 0
    for result in results:
        report(result)
    if len(results) > 1:
        winner = results[0]
        print(f"\n  highest heuristic score: {winner['hook']} ({winner['verdict']}, {winner['band']})")
    return 0

if __name__ == "__main__":
    sys.exit(main())
