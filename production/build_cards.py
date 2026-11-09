#!/usr/bin/env python3
"""Compose the scene cards (1920x1080 canvas, rendered at 2560x1440 for zoom headroom).

Each scene = generated background + scrim + type block + progress rail + grain + vignette.
Run:  python3 build_cards.py
"""
import os, random, glob
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 2560, 1440
OUT = os.path.join(HERE, "cards")
os.makedirs(OUT, exist_ok=True)

FDIR = "/home/user/.venv/lib/python3.11/site-packages/matplotlib/mpl-data/fonts/ttf"
BOLD = os.path.join(FDIR, "DejaVuSans-Bold.ttf")
REG = os.path.join(FDIR, "DejaVuSans.ttf")

AMBER = (232, 163, 61)
BONE = (245, 242, 236)
GREY = (176, 172, 164)
DIM = (122, 118, 110)
FAINT = (58, 56, 52)

SCENES = [
    dict(bg="bg01-hook.png", eyebrow="THE QUOTE PROBLEM", title="SEVEN LEVERS",
         key="Not a mindset problem. A quote problem \u2014 and a quote has parts you can change.",
         zoom="in"),
    dict(bg="bg02-lever1.png", eyebrow="LEVER 01 \u00b7 PAYS ON YOUR NEXT INVOICE", title="THE RENEWAL\nLETTER",
         key="One page, three parts, no apology. Notice, not permission.",
         zoom="out"),
    dict(bg="bg03-lever2.png", eyebrow="LEVER 02 \u00b7 PAYS ON YOUR NEXT QUOTE", title="SELL THE\nDATE",
         key="Same work, half the timeline, one and a half times the price.",
         zoom="in"),
    dict(bg="bg04-lever3.png", eyebrow="LEVER 03 \u00b7 PAYS ON YOUR NEXT QUOTE", title="THREE PRICES\nBEAT ONE",
         key="Smaller scope. The work they asked for. The thing you wish they would buy.",
         zoom="out"),
    dict(bg="bg05-lever4.png", eyebrow="LEVER 04 \u00b7 PROTECTS EVERY QUOTE AFTER IT", title="DOWNSIZE,\nNEVER DISCOUNT",
         key="\u201cI can\u2019t lower the rate. But here is the version that fits your budget.\u201d",
         zoom="in"),
    dict(bg="bg06-lever5.png", eyebrow="LEVER 05 \u00b7 PAYS ON YOUR NEXT PROJECT", title="CHARGE THE\nINVISIBLE HOURS",
         key="The kickoff call is not admin. It is the reason the project works.",
         zoom="out", gain=1.85),
    dict(bg="bg07-lever6.png", eyebrow="LEVER 06 \u00b7 PAYS NEXT QUARTER", title="PRICE THE\nOUTCOME",
         key="Fixed price, fixed scope, capped revisions. Speed stops costing you money.",
         zoom="in"),
    dict(bg="bg08-lever7.png", eyebrow="LEVER 07 \u00b7 COMPOUNDS", title="SELL THE SAME\nBUILD TWICE",
         key="Template, checklist, process. A second sale with no extra hours.",
         zoom="out"),
    dict(bg="bg09-close.png", eyebrow="THE ONE TO PULL", title="PULL ONE\nTHIS WEEK",
         key="Start with lever one. You already have the clients and the inbox.",
         zoom="in", gain=3.1),
]


def font(path, size):
    return ImageFont.truetype(path, size)


def text_width(draw, s, f, tracking=0):
    if not s:
        return 0
    w = sum(draw.textlength(ch, font=f) for ch in s) + tracking * max(0, len(s) - 1)
    return w


def draw_tracked(draw, xy, s, f, fill, tracking=0, anchor_top=True):
    x, y = xy
    for ch in s:
        draw.text((x, y), ch, font=f, fill=fill)
        x += draw.textlength(ch, font=f) + tracking
    return x


def wrap(draw, text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if draw.textlength(t, font=f) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def scrim(img):
    """Left-to-right darkening plus a bottom gradient, so type always has a floor."""
    a = np.zeros((H, W), dtype=np.float32)
    xs = np.linspace(0, 1, W, dtype=np.float32)
    # plateau over the type column, then a smooth falloff, so bright props never eat the copy
    ramp = np.clip((0.80 - xs) / (0.80 - 0.46), 0, 1)
    left = 0.90 * (ramp * ramp * (3 - 2 * ramp))
    a += np.tile(left[None, :], (H, 1))
    ys = np.linspace(0, 1, H, dtype=np.float32)
    bottom = np.clip((ys - 0.55) / 0.45, 0, 1) ** 1.6 * 0.55
    a += np.tile(bottom[:, None], (1, W))
    a = np.clip(a, 0, 1)[..., None]
    base = np.asarray(img, dtype=np.float32)
    base = base * (1 - a) + np.array([9, 10, 11], dtype=np.float32) * a
    return base


def vignette(arr):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = W * 0.5, H * 0.5
    r = np.sqrt(((xx - cx) / (W * 0.62)) ** 2 + ((yy - cy) / (H * 0.62)) ** 2)
    v = np.clip(1.0 - 0.42 * np.clip(r - 0.55, 0, 3) ** 1.5, 0, 1)[..., None]
    return arr * v


def grain(arr, rng, amount=5.0):
    n = rng.normal(0, amount, (H, W, 1)).astype(np.float32)
    return np.clip(arr + n, 0, 255)


def build(scene, idx, rng):
    path = os.path.join(HERE, "images", scene["bg"])
    if not os.path.exists(path):                      # archived as JPEG to keep the repo light
        path = path.rsplit(".", 1)[0] + ".jpg"
    src = Image.open(path).convert("RGB")
    # fill the 16:9 canvas (sources are 1376x768, same ratio) and upscale once
    src = src.resize((W, H), Image.LANCZOS)
    arr = np.asarray(src, dtype=np.float32) * scene.get("gain", 1.0)
    arr = scrim(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB"))
    arr = vignette(arr)
    arr = grain(arr, rng, 2.0)
    img = Image.fromarray(arr.astype(np.uint8), "RGB")
    d = ImageDraw.Draw(img)

    left = 210
    # eyebrow
    f_eye = font(BOLD, 34)
    draw_tracked(d, (left, 505), scene["eyebrow"], f_eye, AMBER, tracking=8)
    # title
    f_title = font(BOLD, 116)
    y = 566
    for line in scene["title"].split("\n"):
        d.text((left, y), line, font=f_title, fill=BONE)
        y += 132
    # rule
    y += 6
    d.rectangle([left, y, left + 300, y + 6], fill=AMBER)
    # key line
    f_key = font(REG, 46)
    y += 58
    for line in wrap(d, scene["key"], f_key, 930):
        d.text((left, y), line, font=f_key, fill=GREY)
        y += 62

    # vertical hairline in the margin
    d.rectangle([left - 46, 505, left - 42, y - 30], fill=(70, 66, 60))

    # progress rail, 7 ticks
    px, py = left, 1300
    for i in range(7):
        if i + 1 == idx:            # 1-based lever number
            col, wd = AMBER, 86
        elif i + 1 < idx:
            col, wd = (120, 114, 104), 44
        else:
            col, wd = FAINT, 44
        d.rectangle([px, py, px + wd, py + 5], fill=col)
        px += wd + 18
    f_rail = font(BOLD, 26)
    draw_tracked(d, (left, py + 26), "7 PRICING LEVERS", f_rail, (110, 106, 99), tracking=6)

    # right-hand page marker
    f_pg = font(BOLD, 30)
    label = "INTRO" if idx == 0 else ("OUTRO" if idx == 8 else f"{idx:02d} / 07")
    tw = text_width(d, label, f_pg, 4)
    draw_tracked(d, (W - 210 - tw, 1300), label, f_pg, (100, 96, 90), tracking=4)

    p = os.path.join(OUT, f"card{idx:02d}.png")
    img.save(p, optimize=True)
    return p


if __name__ == "__main__":
    rng = np.random.default_rng(7)
    for i, s in enumerate(SCENES):
        print(build(s, i, rng))
