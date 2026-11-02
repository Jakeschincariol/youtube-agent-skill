from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import logging
from pathlib import Path
import re
from typing import Any
import urllib.request
from uuid import uuid4

from PIL import Image, ImageDraw, ImageFilter, ImageFont

logger = logging.getLogger("animatube.thumbnails")

# High-visibility palette for YouTube CTR
ACCENT_COLORS = {
    "cyan": "#06b6d4",
    "gold": "#f59e0b",
    "emerald": "#10b981",
    "rose": "#f43f5e",
    "purple": "#8b5cf6",
    "orange": "#f97316",
}

BANNED_CLAIM_PATTERNS = [
    r"\b100%\s*(guarantee|job|placement)\b",
    r"\bguaranteed\s*(job|placement|salary|hiring)\b",
    r"\bcertified\s+in\s+\d+\s*(days|weeks|hours)\b",
    r"\b(earn|make)\s+\$?\d+k\b",
    r"\b\d+\s*lpa\s*(package|salary|offer)\b",
    r"\binstant\s+(hire|job|placement)\b",
    r"\bmoney\s*back\b",
]


def _uid() -> str:
    return uuid4().hex[:6]


def validate_headline(headline: str) -> str:
    """
    Validates and cleans a thumbnail headline.
    Enforces truthfulness: disallows fake guarantees, fake certifications, or fabricated salary claims.
    """
    text = (headline or "").strip()
    if not text:
        raise ValueError("Thumbnail headline cannot be empty.")

    lower = text.lower()
    for pattern in BANNED_CLAIM_PATTERNS:
        if re.search(pattern, lower):
            raise ValueError(
                f"Thumbnail headline contains prohibited or unverifiable claim: '{text}' (matches {pattern})"
            )

    # Clean superfluous punctuation and cap length for thumbnail legibility
    text = re.sub(r"\s+", " ", text)
    if len(text) > 65:
        text = text[:62] + "..."
    return text


@dataclass
class ThumbnailConcept:
    id: str = field(default_factory=_uid)
    concept_name: str = "Concept"
    headline: str = "DEVOPS ROADMAP 2027"
    subheadline: str = "Beginner Step-by-Step Guide"
    badge_text: str = "5 CORE TOOLS"
    accent_color: str = "#06b6d4"
    layout_style: str = "split_hero"  # "split_hero", "roadmap_flow", "card_focus"
    focal_image_path: str = ""
    target_audience: str = "For Freshers, Students & Tech Switchers"
    tool_pills: list[str] = field(default_factory=lambda: ["Linux", "Git", "Docker", "Jenkins", "AWS"])

    def __post_init__(self) -> None:
        self.headline = validate_headline(self.headline)
        if not self.id:
            self.id = _uid()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ThumbnailConcept":
        return cls(
            id=str(data.get("id", _uid())),
            concept_name=str(data.get("concept_name", "Concept")),
            headline=str(data.get("headline", "DEVOPS ROADMAP 2027")),
            subheadline=str(data.get("subheadline", "Beginner Step-by-Step Guide")),
            badge_text=str(data.get("badge_text", "5 CORE TOOLS")),
            accent_color=str(data.get("accent_color", "#06b6d4")),
            layout_style=str(data.get("layout_style", "split_hero")),
            focal_image_path=str(data.get("focal_image_path", "")),
            target_audience=str(data.get("target_audience", "For Freshers, Students & Tech Switchers")),
            tool_pills=list(data.get("tool_pills", ["Linux", "Git", "Docker", "Jenkins", "AWS"])),
        )


class ThumbnailEngine:
    """
    Local-first AI Thumbnail Generator.
    Produces high-CTR, 1280x720 16:9 thumbnails with typography, high contrast,
    glowing badges, and integrated diagram assets.
    """

    WIDTH = 1280
    HEIGHT = 720

    def __init__(self, ollama_endpoint: str = "http://localhost:11434") -> None:
        self.ollama_endpoint = ollama_endpoint.rstrip("/")

    def _get_font(self, size: int, bold: bool = True) -> ImageFont.ImageFont:
        """Finds the best available high-impact system font with fallback to default."""
        font_candidates: list[str] = []
        if bold:
            font_candidates = [
                "C:/Windows/Fonts/segoeui.ttf",
                "C:/Windows/Fonts/segoeuib.ttf",
                "C:/Windows/Fonts/arialbd.ttf",
                "C:/Windows/Fonts/impact.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/System/Library/Fonts/HelveticaNeue.ttc",
            ]
        else:
            font_candidates = [
                "C:/Windows/Fonts/segoeui.ttf",
                "C:/Windows/Fonts/arial.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            ]

        for path in font_candidates:
            if Path(path).is_file():
                try:
                    return ImageFont.truetype(path, size=size)
                except Exception:
                    continue

        return ImageFont.load_default()

    def query_ollama_for_headlines(self, topic: str, audience: str) -> list[str]:
        """Queries local Ollama instance for punchy, truthful YouTube headlines."""
        prompt = (
            f"Generate 3 punchy, high-CTR YouTube thumbnail headlines for a video about '{topic}'. "
            f"Target audience: {audience}. "
            "Rules:\n"
            "- Short and punchy (3 to 6 words each).\n"
            "- ALL CAPS.\n"
            "- Truthful: NO fake guarantees (no '100% guarantee'), NO fake salary claims.\n"
            "- Return strictly a JSON array of 3 strings, e.g. [\"TITLE 1\", \"TITLE 2\", \"TITLE 3\"]."
        )
        url = f"{self.ollama_endpoint}/api/generate"
        payload = json.dumps({"model": "llama3", "prompt": prompt, "stream": False}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

        try:
            with urllib.request.urlopen(req, timeout=4) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    text = data.get("response", "")
                    match = re.search(r"\[.*?\]", text, re.DOTALL)
                    if match:
                        parsed = json.loads(match.group(0))
                        headlines: list[str] = []
                        for h in parsed:
                            try:
                                headlines.append(validate_headline(str(h)))
                            except Exception:
                                pass
                        if len(headlines) >= 3:
                            return headlines[:3]
        except Exception as exc:
            logger.debug("Ollama headline query skipped/failed (%s), using local templates.", exc)

        # Truthful, high-performing template fallbacks
        return [
            "ONLY 5 TOOLS YOU NEED",
            "STOP LEARNING EVERYTHING",
            "DEVOPS ROADMAP 2027",
        ]

    def generate_concepts(
        self,
        topic: str = "DevOps Roadmap 2027",
        target_audience: str = "Indian beginners and tech switchers",
        available_assets: list[str | Path] | None = None,
    ) -> list[ThumbnailConcept]:
        """Generates 3 distinct, high-impact thumbnail concepts."""
        assets = [str(Path(p).resolve()) for p in (available_assets or []) if Path(p).is_file()]
        primary_asset = assets[0] if assets else ""
        secondary_asset = assets[1] if len(assets) > 1 else primary_asset
        tertiary_asset = assets[2] if len(assets) > 2 else primary_asset

        headlines = self.query_ollama_for_headlines(topic, target_audience)

        # Concept 1: Split Hero (High-contrast Question / Big Truth)
        c1 = ThumbnailConcept(
            id="concept_split",
            concept_name="The Big Focus (Split Hero)",
            headline=headlines[0] if len(headlines) > 0 else "ONLY 5 TOOLS YOU NEED",
            subheadline="Zero to Production Blueprint",
            badge_text="2027 ROADMAP",
            accent_color=ACCENT_COLORS["cyan"],
            layout_style="split_hero",
            focal_image_path=primary_asset,
            target_audience=target_audience,
            tool_pills=["Linux", "Git", "Docker", "Jenkins", "AWS"],
        )

        # Concept 2: Step Roadmap (Progress Flow)
        c2 = ThumbnailConcept(
            id="concept_roadmap",
            concept_name="The Step-by-Step Flow",
            headline=headlines[1] if len(headlines) > 1 else "STOP LEARNING EVERYTHING",
            subheadline="Learn In This Exact Order",
            badge_text="STEP-BY-STEP",
            accent_color=ACCENT_COLORS["gold"],
            layout_style="roadmap_flow",
            focal_image_path=secondary_asset,
            target_audience=target_audience,
            tool_pills=["Linux", "Git", "Docker", "Jenkins", "AWS"],
        )

        # Concept 3: Problem & Solution (High Caution / Curiosity)
        c3 = ThumbnailConcept(
            id="concept_card",
            concept_name="The Blueprint Card",
            headline=headlines[2] if len(headlines) > 2 else "DEVOPS ROADMAP 2027",
            subheadline="Practical Beginner Guide",
            badge_text="BEGINNER GUIDE",
            accent_color=ACCENT_COLORS["emerald"],
            layout_style="card_focus",
            focal_image_path=tertiary_asset,
            target_audience=target_audience,
            tool_pills=["Linux", "Git", "Docker", "Jenkins", "AWS"],
        )

        return [c1, c2, c3]

    def render_thumbnail(
        self,
        concept: ThumbnailConcept,
        output_path: str | Path,
        format: str = "PNG",
        custom_image_path: str | Path | None = None,
    ) -> Path:
        """
        Renders a 1280x720 professional thumbnail layout.
        Supports both JPG and PNG exports.
        """
        target = Path(output_path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        img_fmt = format.upper()
        if img_fmt not in ("PNG", "JPG", "JPEG"):
            img_fmt = "PNG"

        w, h = self.WIDTH, self.HEIGHT
        canvas = Image.new("RGBA", (w, h), (11, 19, 43, 255))
        draw = ImageDraw.Draw(canvas)

        # 1. Background: Dark cybernetic gradient with vignette
        self._render_background(canvas, draw, concept.accent_color)

        # 2. Render layout according to concept style
        focal_path = custom_image_path or concept.focal_image_path
        if concept.layout_style == "roadmap_flow":
            self._render_roadmap_flow_layout(canvas, draw, concept, focal_path)
        elif concept.layout_style == "card_focus":
            self._render_card_focus_layout(canvas, draw, concept, focal_path)
        else:  # default: split_hero
            self._render_split_hero_layout(canvas, draw, concept, focal_path)

        # 3. Outer Neon Border Framing
        draw.rounded_rectangle(
            [(12, 12), (w - 12, h - 12)],
            radius=20,
            outline=concept.accent_color,
            width=6,
        )

        # 4. Save to target format
        if img_fmt in ("JPG", "JPEG"):
            rgb_canvas = canvas.convert("RGB")
            rgb_canvas.save(str(target), "JPEG", quality=92, optimize=True)
        else:
            canvas.save(str(target), "PNG")

        return target

    def _render_background(self, canvas: Image.Image, draw: ImageDraw.ImageDraw, accent_hex: str) -> None:
        """Draws dark atmospheric background with neon glow."""
        w, h = canvas.size

        # Radial accent glow on right/center
        glow_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_layer)

        # Convert hex to rgb
        r = int(accent_hex[1:3], 16)
        g = int(accent_hex[3:5], 16)
        b = int(accent_hex[5:7], 16)

        glow_box = [(int(w * 0.5), int(h * 0.1)), (int(w * 0.95), int(h * 0.9))]
        glow_draw.ellipse(glow_box, fill=(r, g, b, 45))
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(80))
        canvas.alpha_composite(glow_layer)

        # Subtle dark grid lines for tech aesthetic
        grid_draw = ImageDraw.Draw(canvas)
        for x in range(0, w, 80):
            grid_draw.line([(x, 0), (x, h)], fill=(255, 255, 255, 6), width=1)
        for y in range(0, h, 80):
            grid_draw.line([(0, y), (w, y)], fill=(255, 255, 255, 6), width=1)

    def _draw_focal_asset(
        self,
        canvas: Image.Image,
        image_path: str | Path | None,
        box: tuple[int, int, int, int],
        accent_color: str,
    ) -> None:
        """Embeds and scales visual diagram into thumbnail box with border and shadow."""
        bx0, by0, bx1, by1 = box
        bw, bh = bx1 - bx0, by1 - by0

        draw = ImageDraw.Draw(canvas)
        draw.rounded_rectangle(
            [(bx0 - 4, by0 - 4), (bx1 + 4, by1 + 4)],
            radius=16,
            outline=accent_color,
            width=4,
            fill=(15, 23, 42, 230),
        )

        p = Path(image_path) if image_path else None
        if p and p.is_file():
            try:
                src = Image.open(str(p)).convert("RGBA")
                src.thumbnail((bw - 16, bh - 16), Image.Resampling.LANCZOS)
                px = bx0 + (bw - src.width) // 2
                py = by0 + (bh - src.height) // 2
                canvas.alpha_composite(src, (px, py))
                return
            except Exception as exc:
                logger.debug("Could not load focal image (%s), rendering fallback graphic.", exc)

        # Fallback technical graphic if image not available
        draw.rounded_rectangle([(bx0 + 10, by0 + 10), (bx1 - 10, by1 - 10)], radius=12, fill=(30, 41, 59, 255))
        f_font = self._get_font(28, bold=True)
        draw.text(
            (bx0 + bw // 2, by0 + bh // 2 - 20),
            "DEVOPS ARCHITECTURE",
            font=f_font,
            fill=(248, 250, 252, 255),
            anchor="mm",
        )
        sub_font = self._get_font(18, bold=False)
        draw.text(
            (bx0 + bw // 2, by0 + bh // 2 + 25),
            "Visual Architecture Asset",
            font=sub_font,
            fill=(148, 163, 184, 255),
            anchor="mm",
        )

    def _render_split_hero_layout(
        self,
        canvas: Image.Image,
        draw: ImageDraw.ImageDraw,
        concept: ThumbnailConcept,
        focal_path: str | Path | None,
    ) -> None:
        """Layout 1: Split hero. Left=Headline & Badges, Right=Visual Diagram."""
        # Badge
        badge_font = self._get_font(26, bold=True)
        badge_box = [(60, 60), (320, 115)]
        draw.rounded_rectangle(badge_box, radius=10, fill=concept.accent_color)
        draw.text((190, 87), concept.badge_text, font=badge_font, fill=(3, 7, 18), anchor="mm")

        # Headline
        title_font = self._get_font(58, bold=True)
        # Drop shadow
        draw.text((63, 153), concept.headline, font=title_font, fill=(0, 0, 0, 220))
        draw.text((60, 150), concept.headline, font=title_font, fill=(255, 255, 255, 255))

        # Subheadline
        sub_font = self._get_font(32, bold=True)
        draw.text((60, 290), concept.subheadline, font=sub_font, fill=concept.accent_color)

        # Tool Pills
        pill_y = 390
        pill_w = 95
        pill_h = 42
        pill_font = self._get_font(18, bold=True)
        for i, tool in enumerate(concept.tool_pills[:5]):
            px = 60 + i * (pill_w + 14)
            draw.rounded_rectangle([(px, pill_y), (px + pill_w, pill_y + pill_h)], radius=8, fill=(15, 23, 42, 240), outline=(56, 189, 248), width=2)
            draw.text((px + pill_w // 2, pill_y + pill_h // 2), tool, font=pill_font, fill=(255, 255, 255), anchor="mm")

        # Target audience banner at bottom
        aud_font = self._get_font(22, bold=False)
        draw.text((60, 600), concept.target_audience, font=aud_font, fill=(148, 163, 184))

        # Focal Diagram on Right
        self._draw_focal_asset(canvas, focal_path, (650, 70, 1210, 640), concept.accent_color)

    def _render_roadmap_flow_layout(
        self,
        canvas: Image.Image,
        draw: ImageDraw.ImageDraw,
        concept: ThumbnailConcept,
        focal_path: str | Path | None,
    ) -> None:
        """Layout 2: Roadmap Flow. Top=Title, Center=Visual, Bottom=Flow path."""
        # Top Badge
        badge_font = self._get_font(24, bold=True)
        draw.rounded_rectangle([(60, 45), (280, 95)], radius=10, fill=concept.accent_color)
        draw.text((170, 70), concept.badge_text, font=badge_font, fill=(3, 7, 18), anchor="mm")

        # Headline
        title_font = self._get_font(52, bold=True)
        draw.text((310, 50), concept.headline, font=title_font, fill=(255, 255, 255))

        # Center Visual Asset
        self._draw_focal_asset(canvas, focal_path, (60, 130, 1220, 540), concept.accent_color)

        # Bottom Flow Arrow Pills
        flow_y = 575
        pill_w = 170
        pill_h = 55
        flow_font = self._get_font(20, bold=True)
        for i, tool in enumerate(concept.tool_pills[:5]):
            px = 60 + i * (pill_w + 35)
            draw.rounded_rectangle([(px, flow_y), (px + pill_w, flow_y + pill_h)], radius=10, fill=(15, 23, 42, 240), outline=concept.accent_color, width=2)
            draw.text((px + pill_w // 2, flow_y + pill_h // 2), f"{i+1}. {tool}", font=flow_font, fill=(255, 255, 255), anchor="mm")
            if i < 4:
                draw.text((px + pill_w + 16, flow_y + pill_h // 2), "→", font=flow_font, fill=concept.accent_color, anchor="mm")

    def _render_card_focus_layout(
        self,
        canvas: Image.Image,
        draw: ImageDraw.ImageDraw,
        concept: ThumbnailConcept,
        focal_path: str | Path | None,
    ) -> None:
        """Layout 3: Card Focus. Bold upper card with accent highlight and clean graphic."""
        # Top Attention Card
        draw.rounded_rectangle([(60, 50), (1220, 200)], radius=18, fill=(15, 23, 42, 220), outline=concept.accent_color, width=3)

        badge_font = self._get_font(22, bold=True)
        draw.rounded_rectangle([(90, 70), (280, 115)], radius=8, fill=concept.accent_color)
        draw.text((185, 92), concept.badge_text, font=badge_font, fill=(3, 7, 18), anchor="mm")

        title_font = self._get_font(50, bold=True)
        draw.text((310, 70), concept.headline, font=title_font, fill=(255, 255, 255))

        sub_font = self._get_font(26, bold=False)
        draw.text((90, 140), concept.subheadline + f" • {concept.target_audience}", font=sub_font, fill=(148, 163, 184))

        # Bottom Graphic Panel
        self._draw_focal_asset(canvas, focal_path, (60, 230, 1220, 650), concept.accent_color)
