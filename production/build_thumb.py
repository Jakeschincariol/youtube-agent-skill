#!/usr/bin/env python3
"""Thumbnail: two words, one number in the title, nothing repeated.

Feed test is the only test that matters: at 320px wide, "CHARGE" and "MORE" still read as two
shapes. The generated background carries the prop and the light; the type is flat so it survives
compression.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FDIR = "/home/user/.venv/lib/python3.11/site-packages/matplotlib/mpl-data/fonts/ttf"
BOLD = os.path.join(FDIR, "DejaVuSans-Bold.ttf")
W, H = 1280, 720
AMBER = (232, 163, 61)
BONE = (250, 247, 241)

img = Image.open(os.path.join(HERE, "images", "thumb-bg.png")).convert("RGB").resize((W, H), Image.LANCZOS)
img = img.transpose(Image.FLIP_LEFT_RIGHT)   # prop to the right, clean dark field for the type
arr = np.asarray(img, dtype=np.float32)

# keep the left third clean for type, push the light
xs = np.linspace(0, 1, W, dtype=np.float32)
a = np.clip((0.62 - xs) / 0.62, 0, 1) ** 1.1 * 0.86
arr = arr * (1 - a[None, :, None]) + np.array([10, 10, 11], dtype=np.float32) * a[None, :, None]
# punch: contrast + saturation on the amber
arr = np.clip((arr - 128) * 1.12 + 128, 0, 255)
img = Image.fromarray(arr.astype(np.uint8), "RGB")
d = ImageDraw.Draw(img)

f = ImageFont.truetype(BOLD, 150)
x, y = 62, 214
for line in ("CHARGE", "MORE"):
    d.text((x + 7, y + 9), line, font=f, fill=(0, 0, 0))          # hard shadow, survives downscale
    d.text((x, y), line, font=f, fill=BONE)
    y += 168
d.rectangle([x + 6, y + 4, x + 6 + 430, y + 20], fill=AMBER)

out = os.path.join(HERE, "thumbnail.png")
img.save(out, optimize=True)
img.resize((320, 180), Image.LANCZOS).save(os.path.join(HERE, "thumbnail_feedtest.png"))
print(out)
