#!/usr/bin/env python3
"""Lint YouTube title and thumbnail text as a packaging pair.

Examples:
    python title.py --title "How I Automated a DevOps Workflow"
    python title.py --title "..." --thumb "NO MORE MANUAL DEPLOYS"
    python title.py titles.txt
    python title.py titles.txt --json

The score is a transparent editorial heuristic, not a prediction of CTR or views.
YouTube's actual title limit is 100 characters. Display truncation varies by
surface and device, so length guidance here is advisory rather than a fixed
40/60-character rule.
"""
import argparse
import json
import re
import sys
from pathlib import Path

YOUTUBE_TITLE_LIMIT = 100
LONG_TITLE_GUIDANCE = 70
VAGUE = {
    "amazing", "incredible", "insane", "crazy", "huge", "massive",
    "ultimate", "best", "powerful", "secret", "revolutionary",
    "mindblowing", "epic", "perfect", "complete", "everything",
}
STOP = {
    "the", "a", "an", "of", "for", "to", "in", "on", "and", "or",
    "is", "are", "with", "your", "you", "my", "i", "this", "that",
    "it", "how", "what", "why", "from", "by", "at", "as",
}


def words(text):
    """Return case-insensitive word tokens, retaining internal apostrophes."""
    return re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)?", text.casefold())


def meaningful_words(text):
    return {word for word in words(text) if word not in STOP}


def check(title, thumb=None):
    """Return validation findings and a non-predictive editorial score."""
    if not isinstance(title, str) or not title.strip():
        raise ValueError("title must be a non-empty string")
    if thumb is not None and not isinstance(thumb, str):
        raise ValueError("thumbnail text must be a string")

    title = title.strip()
    thumb = thumb.strip() if thumb is not None else None
    issues = []
    good = []
    length = len(title)

    if length > YOUTUBE_TITLE_LIMIT:
        issues.append({
            "code": "title-limit",
            "severity": "error",
            "message": (
                f"{length} characters; YouTube's title limit is "
                f"{YOUTUBE_TITLE_LIMIT}"
            ),
        })
    elif length > LONG_TITLE_GUIDANCE:
        issues.append({
            "code": "length",
            "severity": "suggestion",
            "message": (
                f"{length} characters; consider shortening it and moving "
                "the most important words earlier"
            ),
        })
    else:
        good.append("title is within the suggested concise-length range")

    caps = [token for token in title.split() if len(token) > 2 and token.isupper()]
    if len(caps) >= 3:
        issues.append({
            "code": "all-caps",
            "severity": "suggestion",
            "message": (
                f"{len(caps)} all-caps words; use capitals selectively "
                "for emphasis"
            ),
        })
    elif caps:
        good.append(f"{len(caps)} all-caps word(s) used for emphasis")

    vague = sorted(set(words(title)) & VAGUE)
    if vague:
        issues.append({
            "code": "generic-wording",
            "severity": "suggestion",
            "message": (
                f"review generic wording ({', '.join(vague)}); replace it "
                "only if a more specific, accurate detail is available"
            ),
        })

    if title.endswith("?"):
        good.append("title uses a question to create curiosity")

    title_tokens = meaningful_words(title)
    if title_tokens:
        good.append("title contains identifiable topic words")
    else:
        issues.append({
            "code": "topic-clarity",
            "severity": "suggestion",
            "message": "make the subject or outcome clearer",
        })

    if thumb is not None:
        if not thumb:
            issues.append({
                "code": "empty-thumbnail",
                "severity": "suggestion",
                "message": "thumbnail text is empty",
            })
        else:
            thumb_tokens = meaningful_words(thumb)
            overlap = title_tokens & thumb_tokens
            # A single shared word can be useful for clarity. Flag substantial
            # duplication rather than treating any overlap as automatically bad.
            if thumb_tokens and len(overlap) >= min(2, len(thumb_tokens)):
                issues.append({
                    "code": "pair-duplication",
                    "severity": "suggestion",
                    "message": (
                        "thumbnail repeats most of its meaningful wording "
                        f"from the title ({', '.join(sorted(overlap))}); "
                        "consider adding complementary context"
                    ),
                })
            elif thumb_tokens:
                good.append("title and thumbnail provide mostly complementary wording")

            thumb_word_count = len(words(thumb))
            if thumb_word_count > 4:
                issues.append({
                    "code": "thumbnail-readability",
                    "severity": "suggestion",
                    "message": (
                        f"{thumb_word_count} words on the thumbnail; "
                        "check readability at small sizes"
                    ),
                })

    # Editorial heuristic only. It is not a CTR estimate or a measure of truth.
    errors = sum(item["severity"] == "error" for item in issues)
    suggestions = sum(item["severity"] == "suggestion" for item in issues)
    score = max(0, 100 - errors * 50 - suggestions * 12 + min(len(good), 3) * 4)

    return {
        "title": title,
        "chars": length,
        "score": score,
        "score_type": "editorial_heuristic_not_performance_prediction",
        "valid": errors == 0,
        "issues": issues,
        "good": good,
    }


def read_titles(path):
    """Read one title per line from a UTF-8 text file."""
    with Path(path).open(encoding="utf-8-sig") as handle:
        titles = [line.strip() for line in handle if line.strip()]
    if not titles:
        raise ValueError("title file contains no non-empty titles")
    return titles


def build_parser():
    parser = argparse.ArgumentParser(
        description="Lint YouTube title and thumbnail text before publishing."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--title", help="one title to check")
    source.add_argument("titles_file", nargs="?", help="UTF-8 text file, one title per line")
    parser.add_argument("--thumb", help="optional thumbnail text to compare with the title")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        titles = [args.title] if args.title is not None else read_titles(args.titles_file)
        rows = [check(title, args.thumb) for title in titles]
    except (OSError, UnicodeError, ValueError) as error:
        print(f"title packaging check failed: {error}", file=sys.stderr)
        return 2

    rows.sort(key=lambda row: (-row["score"], row["title"]))
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        for row in rows:
            print(f'\n  "{row["title"]}"')
            print(
                f'  {row["chars"]} characters | editorial heuristic '
                f'{row["score"]}/100 | {"valid" if row["valid"] else "invalid"}'
            )
            for issue in row["issues"]:
                marker = "ERROR" if issue["severity"] == "error" else "NOTE"
                print(f'    {marker:<5} {issue["code"]:<22} {issue["message"]}')
            for message in row["good"]:
                print(f"    OK    {message}")
        print("\n  Score is an editorial heuristic, not a CTR or views prediction.")
    return 0 if all(row["valid"] for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
