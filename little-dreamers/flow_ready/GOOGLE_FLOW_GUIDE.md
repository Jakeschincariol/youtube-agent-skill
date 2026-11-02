# GOOGLE FLOW — IMAGE-TO-VIDEO PRODUCTION PIPELINE GUIDE
**Brand:** LITTLE DREAMERS  
**Engine Compatibility:** Google Flow / Google Veo / Runway Gen-3 / Luma Dream Machine / Kling AI  
**Pipeline Role:** Permanent Character Motion & Animation Generation

---

## 1. Overview
This guide provides the exact operational procedure for translating the approved 2D/3D character design references into fluid, consistent, high-fidelity preschool animation video clips using AI image-to-video engines.

---

## 2. Directory Structure & Anchor Assets

All optimized seed images are located in `little-dreamers/flow_ready/`:

| Character | Anchor File | Format / Ratio | Role in Video Pipeline |
|---|---|---|---|
| **Aarav** | `aarav_flow_anchor.png` | 1024×1024 PNG | Primary seed frame for Aarav solo shots & dialogue |
| **Mia** | `mia_flow_anchor.png` | 1024×1024 PNG | Primary seed frame for Mia singing, dancing, skips |
| **Ellie** | `ellie_flow_anchor.png` | 1024×1024 PNG | Primary seed frame for Ellie helper & water-spray actions |
| **Gigi** | `gigi_flow_anchor.png` | 1024×1024 PNG | Primary seed frame for Gigi peeking, trotting, curiosity |
| **Bobo** | `bobo_flow_anchor.png` | 1024×1024 PNG | Primary seed frame for Bobo wagging, play-bows, runs |
| **Twinkle** | `twinkle_flow_anchor.png` | 1024×1024 PNG | Primary seed frame for Twinkle floating, guidance, transitions |
| **Cast Lineup** | `master_lineup_flow.png` | 1376×768 PNG | Baseline seed frame for multi-character staging & group shots |

---

## 3. Recommended Engine Settings

- **Motion Strength / Flow Intensity:** `0.45` to `0.60`.  
  *(Keep under 0.65 to prevent limb hallucination or clothing drift; keep above 0.40 to allow lively preschool character acting).*
- **Guidance Scale (CFG):** `7.0` to `8.0`.
- **Interpolation / Frame Rate:** Target `24 FPS` (cinematic) or `30 FPS` (standard preschool video).
- **Camera Controls:**
  - *Slow Dolly In:* Ideal for dialogue and emotional connection.
  - *Slow Pan Left/Right:* Ideal for walk/run sequences across background.
  - *Static Camera with Subject Motion:* Ideal for songs, dances, and demonstration scenes.

---

## 4. Prompt Conditioning Syntax

When initiating a clip in Google Flow, combine:
1. **[Anchor Image Upload]** as Initial Frame (`image_0`).
2. **[Subject & Action Prompt]** from `GOOGLE_FLOW_PROMPTS.json`.
3. **[Costume & Identity Lock]**.
4. **[Negative Prompt String]**.

### Example Prompt String for Aarav Waving:
```text
[Input Image: aarav_flow_anchor.png]
Aarav, cute 2.5-year-old toddler boy from Little Dreamers, raises his right hand and waves enthusiastically toward the camera with a joyful smiling expression. Wearing his bright sky-blue t-shirt with golden-yellow five-pointed star emblem, royal blue shorts, and red sneakers. Pixar 3D preschool animation style, soft cinematic lighting, smooth character movement, 24fps.

Negative Prompt: realistic skin pores, teenager, adult, sharp jawline, missing star emblem on shirt, wrong shirt color, green eyes, extra fingers, morphing limbs, flickering, flat 2D, dark gloomy lighting.
```

---

## 5. Multi-Character Interaction Rules

1. **Height Integrity:** Always refer to `master_lineup_flow.png` to maintain correct character relative scale. Gigi's head must always be highest, Ellie's body widest, Twinkle floating at toddler eye-level, and Bobo at Aarav's waist level.
2. **Contact Shadows:** Ensure ground plane contact shadows are generated consistently beneath all grounded characters (Aarav, Mia, Ellie, Gigi, Bobo), while Twinkle casts a soft diffused glowing light circle instead of a dark shadow.
3. **Pacing:** Preschool animation requires readable, deliberate staging. Never exceed 1 primary action per 3-second shot.
