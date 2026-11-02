import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter


def generate_dreamland_garden_bg(output_path: str | Path, width: int = 1920, height: int = 1080) -> Path:
    """Generates a high-resolution, Pixar-style preschool animated background for Dreamland Garden."""
    out = Path(output_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGBA", (width, height), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)

    # 1. Sky Gradient (Warm morning amber to gentle pastel sky blue to soft lavender)
    for y in range(height):
        factor = y / float(height)
        if factor < 0.45:
            # Upper sky: soft cornflower blue (147, 197, 253) to sky blue (186, 230, 253)
            t = factor / 0.45
            r = int(147 + (186 - 147) * t)
            g = int(197 + (230 - 197) * t)
            b = int(253 + (253 - 253) * t)
        elif factor < 0.65:
            # Horizon glow: warm pastel golden amber (254, 240, 138)
            t = (factor - 0.45) / 0.20
            r = int(186 + (254 - 186) * t)
            g = int(230 + (240 - 230) * t)
            b = int(253 + (138 - 253) * t)
        else:
            # Distant ground transition: soft peach blush
            t = (factor - 0.65) / 0.35
            r = int(254 + (216 - 254) * t)
            g = int(240 + (180 - 240) * t)
            b = int(138 + (254 - 138) * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    # 2. Glowing Pastel Rainbow in the distance
    rainbow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    rb_draw = ImageDraw.Draw(rainbow_layer)
    rb_colors = [
        (244, 114, 182, 90),  # Pink
        (251, 191, 36, 90),   # Yellow
        (52, 211, 153, 90),   # Green
        (96, 165, 250, 90),   # Blue
        (192, 132, 252, 90),  # Purple
    ]
    center_x = width // 2 - 200
    center_y = height + 100
    base_radius = 650
    for i, col in enumerate(rb_colors):
        r = base_radius - (i * 22)
        rb_draw.arc(
            [center_x - r, center_y - r, center_x + r, center_y + r],
            start=200,
            end=340,
            fill=col,
            width=20,
        )
    rainbow_layer = rainbow_layer.filter(ImageFilter.GaussianBlur(radius=6))
    img.alpha_composite(rainbow_layer)

    # 3. Soft Distant Rolling Hills
    hills_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    h_draw = ImageDraw.Draw(hills_layer)
    # Far hill (pastel turquoise green)
    h_draw.chord([-100, 480, width // 2 + 300, 1200], start=0, end=180, fill=(167, 243, 208, 220))
    # Mid hill (soft mint green)
    h_draw.chord([width // 3 - 100, 520, width + 200, 1250], start=0, end=180, fill=(110, 231, 183, 235))
    # Near rolling ground (lush vibrant preschool meadow green)
    h_draw.chord([-200, 620, width + 300, 1400], start=0, end=180, fill=(52, 211, 153, 255))
    img.alpha_composite(hills_layer)

    # 4. Whimsical Foreground Flowers and Sparkles
    fg_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    fg_draw = ImageDraw.Draw(fg_layer)

    # Soft flower stems and blooms
    flower_coords = [
        (120, 840, (244, 114, 182)),  # Pink bloom
        (260, 900, (250, 204, 21)),   # Yellow bloom
        (420, 860, (168, 85, 247)),   # Purple bloom
        (1500, 880, (56, 189, 248)),  # Sky blue bloom
        (1680, 820, (244, 114, 182)), # Pink bloom
        (1820, 890, (251, 146, 60)),  # Warm orange bloom
    ]
    for fx, fy, fcol in flower_coords:
        # Stem
        fg_draw.line([(fx, fy + 20), (fx - 10, fy + 180)], fill=(34, 197, 94, 220), width=8)
        # Petals
        for deg in range(0, 360, 60):
            rad = math.radians(deg)
            px = fx + int(28 * math.cos(rad))
            py = fy + int(28 * math.sin(rad))
            fg_draw.ellipse([px - 22, py - 22, px + 22, py + 22], fill=fcol + (240,))
        # Flower center (soft yellow glow)
        fg_draw.ellipse([fx - 16, fy - 16, fx + 16, fy + 16], fill=(254, 240, 138, 255))

    # Sparkle Stars
    sparkle_coords = [
        (320, 280), (640, 180), (980, 240), (1350, 160), (1620, 320),
        (220, 480), (820, 520), (1420, 460), (1750, 580)
    ]
    for sx, sy in sparkle_coords:
        # Draw 4-pointed star
        size = 14
        fg_draw.polygon([
            (sx, sy - size), (sx + 4, sy - 4), (sx + size, sy), (sx + 4, sy + 4),
            (sx, sy + size), (sx - 4, sy + 4), (sx - size, sy), (sx - 4, sy - 4),
        ], fill=(255, 255, 255, 220))

    img.alpha_composite(fg_layer)

    # Convert to RGB and save
    final_img = img.convert("RGB")
    final_img.save(str(out), "PNG", quality=95)
    return out


if __name__ == "__main__":
    generate_dreamland_garden_bg("little-dreamers/episodes/ep01_magic_abc_train/assets/magical_garden_bg.png")
    print("Generated Dreamland Garden background successfully")
