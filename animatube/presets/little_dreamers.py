from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

from animatube.ai.models import VideoPrompt
from animatube.core.models import Layer, Project, Scene

BRAND_NAME = "LITTLE DREAMERS"
TARGET_RESOLUTION = (1920, 1080)
TARGET_FPS = 24
SUPPORTED_LANGUAGES = ["en", "te"]  # English & Telugu


LITTLE_DREAMERS_CHARACTERS: dict[str, dict[str, Any]] = {
    "aarav": {
        "id": "aarav",
        "name": "Aarav",
        "species": "Toddler Boy (2.5 years)",
        "height_cm": 85,
        "anchor_image": "little-dreamers/flow_ready/aarav_flow_anchor.png",
        "voice_id": "aarav_boy",
        "identity_tokens": "cute 2.5yo toddler boy, wavy brown hair with playful cowlick, large expressive brown eyes, chubby cheeks, bright smile",
        "costume_lock": "sky-blue t-shirt with gold star emblem, royal blue shorts, red sneakers with white soles",
        "actions": {
            "idle_curious": "Aarav gently bounces on feet with toddler curiosity, tilting head, smiling cheerfully toward camera",
            "joyful_wave": "Aarav raises his hand giving an energetic preschool wave, laughing happily with twinkling eyes",
            "adventurous_walk": "Aarav waddles forward with bouncy toddler steps, arms swinging gently for balance",
        },
        "negative_prompt": "realistic human skin pores, adult, sharp jawline, missing star emblem, wrong shirt color, dark moody lighting",
    },
    "mia": {
        "id": "mia",
        "name": "Mia",
        "species": "Toddler Girl (2.5 years)",
        "height_cm": 83,
        "anchor_image": "little-dreamers/flow_ready/mia_flow_anchor.png",
        "voice_id": "mia_girl",
        "identity_tokens": "cute 2.5yo toddler girl, silky brown ponytail, pastel pink bow, large brown eyes, sweet smile, rosy cheeks",
        "costume_lock": "pastel pink A-line dress with small yellow flower motif, white socks, magenta shoes",
        "actions": {
            "singing_sway": "Mia gently sways side to side to a preschool melody, ponytail swishing softly, sweet smile",
            "cheerful_skip": "Mia playfully skips forward with light springy toddler steps, pink dress fluttering gently",
            "comforting_hug": "Mia opens arms wide for a warm preschool hug with tender caring expression",
        },
        "negative_prompt": "adult woman, missing pink hair bow, wrong dress color, dark colors, angry expression, extra limbs",
    },
    "ellie": {
        "id": "ellie",
        "name": "Ellie",
        "species": "Baby Elephant",
        "height_cm": 90,
        "anchor_image": "little-dreamers/flow_ready/ellie_flow_anchor.png",
        "voice_id": "ellie_gentle",
        "identity_tokens": "adorable chubby baby purple elephant, pastel lavender velvety skin, large floppy ears with pink inner flaps, round baby belly, tuskless",
        "costume_lock": "vibrant turquoise flower clip pinned to left ear, tuskless baby elephant",
        "actions": {
            "happy_trunk_wave": "Ellie happily curls her trunk upward in friendly greeting, ears gently fanning, sweet smile",
            "playful_waddle": "Ellie waddles forward with cute baby elephant steps, padded feet landing softly, trunk swaying",
            "celebratory_trumpet": "Ellie raises trunk skyward in joyful silent baby trumpet pose, eyes crinkling with happiness",
        },
        "negative_prompt": "sharp adult tusks, realistic grey elephant, aggressive animal, scary trunk, dark purple, flat 2D",
    },
    "gigi": {
        "id": "gigi",
        "name": "Gigi",
        "species": "Baby Giraffe",
        "height_cm": 110,
        "anchor_image": "little-dreamers/flow_ready/gigi_flow_anchor.png",
        "voice_id": "gigi_peppy",
        "identity_tokens": "cute baby giraffe, soft cream-yellow fur, rounded golden honey spots, short adorable neck, tufted ossicones, perky ears, curious large brown eyes",
        "costume_lock": "emerald green leafy neck bandana scarf tied neatly around neck",
        "actions": {
            "curious_peek": "Gigi playfully bends neck down into frame, ears perking up with delightful curiosity, warm smile",
            "graceful_prance": "Gigi prances forward with bouncy baby giraffe steps, leafy bandana fluttering softly",
            "gentle_nuzzle": "Gigi gently leans forward to nuzzle a friend affectionately, eyes half-closed in pure happiness",
        },
        "negative_prompt": "overly long adult giraffe neck, aggressive spots, dark fur, missing leafy bandana, realistic safari animal",
    },
    "bobo": {
        "id": "bobo",
        "name": "Bobo",
        "species": "Baby Golden Puppy",
        "height_cm": 50,
        "anchor_image": "little-dreamers/flow_ready/bobo_flow_anchor.png",
        "voice_id": "bobo_puppy",
        "identity_tokens": "adorable chubby golden retriever puppy, soft fluffy honey-gold fur, floppy ears, wagging tail, large shiny puppy-dog eyes, wet black nose",
        "costume_lock": "cherry-red bandana collar tied around neck with white trim",
        "actions": {
            "excited_tail_wag": "Bobo happily wags his tail in rapid joyful beats, tongue peeking out, bouncing with eagerness",
            "playful_pounce": "Bobo drops into cute puppy play-bow, tail high in the air, then playfully hops forward",
            "happy_spin": "Bobo does a quick adorable puppy spin chasing his tail, flopping down facing camera with big panting grin",
        },
        "negative_prompt": "fierce adult dog, wolf, pointy ears, missing red bandana, aggressive bark, skinny legs, dirty fur",
    },
    "twinkle": {
        "id": "twinkle",
        "name": "Twinkle",
        "species": "Magical Star Baby",
        "height_cm": 40,
        "anchor_image": "little-dreamers/flow_ready/twinkle_flow_anchor.png",
        "voice_id": "twinkle_star",
        "identity_tokens": "enchanting 3D star baby, plump rounded 5-pointed golden star body, warm radiant ambient glow, sweet smiling baby face, tiny hands and feet, soft pastel rainbow aura",
        "costume_lock": "tiny celestial baby nightcap resting on top point",
        "actions": {
            "gentle_hover": "Twinkle floats up and down gently in a soft wave, warm golden light pulsing peacefully, sparkling aura",
            "magical_spin": "Twinkle pirouettes gracefully in mid-air leaving a trail of shimmering harmless pastel star dust",
            "comforting_glow": "Twinkle floats down closer, smiling serenely as golden light expands warmly to soothe bedtime fears",
        },
        "negative_prompt": "sharp metallic star, robotic, harsh glare, angry face, flat 2D graphic, missing nightcap, realistic hands",
    },
}


LITTLE_DREAMERS_EDUCATIONAL_THEMES: list[dict[str, str]] = [
    {
        "id": "counting_1_10",
        "title_en": "Counting 1 to 10 with Aarav & Bobo",
        "title_te": "ఆరవ్ మరియు బోబోతో 1 నుండి 10 లెక్కించడం",
        "description": "Fun interactive counting episode where Aarav and Bobo count colorful stars and flowers.",
        "bgm_mood": "playful",
        "genre": "preschool_orchestral",
    },
    {
        "id": "colors_and_shapes",
        "title_en": "Rainbow Colors and Shapes with Mia & Ellie",
        "title_te": "మియా మరియు ఎల్లీతో రంగులు మరియు ఆకారాలు",
        "description": "Educational discovery of red, blue, yellow, stars and circles through playful songs.",
        "bgm_mood": "cheerful",
        "genre": "playful_acoustic",
    },
    {
        "id": "bedtime_lullaby",
        "title_en": "Twinkle's Bedtime Lullaby",
        "title_te": "ట్వింకిల్ పడుకునే జోలపాట",
        "description": "Calming nighttime animation with gentle breathing and soothing melodies to help toddlers sleep.",
        "bgm_mood": "lullaby",
        "genre": "gentle_lullaby",
    },
    {
        "id": "friendship_and_sharing",
        "title_en": "Sharing is Caring with Gigi & Friends",
        "title_te": "గిగి మరియు స్నేహితులతో పంచుకోవడం",
        "description": "Wholesome preschool story showing empathy, sharing toys, and helping little friends.",
        "bgm_mood": "adventurous",
        "genre": "preschool_orchestral",
    },
]


def get_little_dreamers_characters() -> list[dict[str, Any]]:
    """Returns the list of character metadata dictionaries."""
    return list(LITTLE_DREAMERS_CHARACTERS.values())


def get_character_prompt(character_id: str, action: str = "idle_curious") -> VideoPrompt:
    """Builds a validated VideoPrompt configured for the character's visual anchor and motion."""
    char = LITTLE_DREAMERS_CHARACTERS.get(character_id.lower())
    if not char:
        raise KeyError(f"Unknown Little Dreamers character: {character_id}. Available: {list(LITTLE_DREAMERS_CHARACTERS.keys())}")

    action_text = char["actions"].get(action, char["actions"].get("idle_curious", ""))
    full_prompt = (
        f"Pixar 3D preschool animation of {char['name']}, {char['identity_tokens']}, {char['costume_lock']}. "
        f"{action_text}. Soft warm 3-point lighting, pastel background, 24fps smooth character motion."
    )

    anchor_path = char["anchor_image"]
    abs_anchor = str(Path(anchor_path).resolve()) if Path(anchor_path).is_file() else anchor_path

    return VideoPrompt(
        prompt=full_prompt,
        negative_prompt=char["negative_prompt"],
        reference_image_path=abs_anchor,
        aspect_ratio="16:9",
        duration_seconds=4.0,
        camera_motion="pan_right",
        motion_strength=0.5,
    )


def create_little_dreamers_project(
    name: str = "Little Dreamers - Episode 1",
    theme_id: str | None = None,
) -> Project:
    """
    Creates a new 1920x1080 24fps project pre-configured for Little Dreamers preschool production.
    Includes 4 storyboard scenes with character visual anchors.
    """
    theme = next((t for t in LITTLE_DREAMERS_EDUCATIONAL_THEMES if t["id"] == theme_id), LITTLE_DREAMERS_EDUCATIONAL_THEMES[0])

    proj_name = f"Little Dreamers: {theme['title_en']}" if theme_id else name

    # Resolve master lineup or character anchors if available
    lineup_path = str(Path("little-dreamers/flow_ready/master_lineup_flow.png").resolve())
    aarav_path = str(Path("little-dreamers/flow_ready/aarav_flow_anchor.png").resolve())
    mia_path = str(Path("little-dreamers/flow_ready/mia_flow_anchor.png").resolve())
    ellie_path = str(Path("little-dreamers/flow_ready/ellie_flow_anchor.png").resolve())
    twinkle_path = str(Path("little-dreamers/flow_ready/twinkle_flow_anchor.png").resolve())

    scenes = [
        # Scene 1: Lineup Intro (4 seconds @ 24fps = 96 frames)
        Scene(
            name="01_Lineup_Intro",
            duration_frames=96,
            layers=[
                Layer(
                    name="Master Lineup",
                    kind="image" if Path(lineup_path).is_file() else "rect",
                    asset_path=lineup_path if Path(lineup_path).is_file() else "",
                    x=0,
                    y=0,
                    width=1920,
                    height=1080,
                    color="#1a103c",
                ),
                Layer(
                    name="Episode Title",
                    kind="text",
                    text=f"Little Dreamers: {theme['title_en']}",
                    font_size=48,
                    color="#fef08a",
                    x=160,
                    y=860,
                    width=1600,
                    height=100,
                ),
            ],
        ),
        # Scene 2: Aarav & Mia Story Beat (5 seconds @ 24fps = 120 frames)
        Scene(
            name="02_Aarav_Mia_Adventure",
            duration_frames=120,
            layers=[
                Layer(
                    name="Aarav Anchor",
                    kind="image" if Path(aarav_path).is_file() else "ellipse",
                    asset_path=aarav_path if Path(aarav_path).is_file() else "",
                    x=180,
                    y=140,
                    width=680,
                    height=760,
                    color="#38bdf8",
                ),
                Layer(
                    name="Mia Anchor",
                    kind="image" if Path(mia_path).is_file() else "ellipse",
                    asset_path=mia_path if Path(mia_path).is_file() else "",
                    x=1020,
                    y=140,
                    width=680,
                    height=760,
                    color="#f472b6",
                ),
                Layer(
                    name="Subtitles",
                    kind="text",
                    text=theme.get("title_te", "Welcome little friends!"),
                    font_size=40,
                    color="#ffffff",
                    x=160,
                    y=920,
                    width=1600,
                    height=80,
                ),
            ],
        ),
        # Scene 3: Ellie & Animal Friends (5 seconds @ 24fps = 120 frames)
        Scene(
            name="03_Animal_Friends",
            duration_frames=120,
            layers=[
                Layer(
                    name="Ellie Anchor",
                    kind="image" if Path(ellie_path).is_file() else "ellipse",
                    asset_path=ellie_path if Path(ellie_path).is_file() else "",
                    x=520,
                    y=140,
                    width=880,
                    height=760,
                    color="#c084fc",
                ),
                Layer(
                    name="Subtitle Beat",
                    kind="text",
                    text="Sharing and learning together!",
                    font_size=40,
                    color="#ffffff",
                    x=160,
                    y=920,
                    width=1600,
                    height=80,
                ),
            ],
        ),
        # Scene 4: Twinkle Star Bedtime / Celebration (4 seconds @ 24fps = 96 frames)
        Scene(
            name="04_Twinkle_Star_Outro",
            duration_frames=96,
            layers=[
                Layer(
                    name="Twinkle Anchor",
                    kind="image" if Path(twinkle_path).is_file() else "ellipse",
                    asset_path=twinkle_path if Path(twinkle_path).is_file() else "",
                    x=600,
                    y=180,
                    width=720,
                    height=680,
                    color="#facc15",
                ),
                Layer(
                    name="Outro Text",
                    kind="text",
                    text="Good night, Little Dreamers! ✨",
                    font_size=48,
                    color="#fde047",
                    x=160,
                    y=880,
                    width=1600,
                    height=100,
                ),
            ],
        ),
    ]

    return Project(
        name=proj_name,
        width=1920,
        height=1080,
        fps=24,
        background="#1a103c",
        scenes=scenes,
    )


def apply_little_dreamers_preset(project: Project) -> Project:
    """Applies the Little Dreamers preset configuration to an existing project."""
    project.width = 1920
    project.height = 1080
    project.fps = 24
    project.background = "#1a103c"
    return project
