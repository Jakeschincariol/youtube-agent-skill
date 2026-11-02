from __future__ import annotations

from enum import Enum
import re
from typing import Any

TECHNICAL_PRONUNCIATION_MAP: dict[str, str] = {
    # Acronyms & Cloud Services
    r"\bCI/CD\b": "C-I C-D",
    r"\bci/cd\b": "C-I C-D",
    r"\bK8s\b": "Kubernetes",
    r"\bk8s\b": "Kubernetes",
    r"\bYAML\b": "Yam-el",
    r"\byaml\b": "Yam-el",
    r"\bAWS\b": "A-W-S",
    r"\bEC2\b": "E-C-2",
    r"\bS3\b": "S-3",
    r"\bVPC\b": "V-P-C",
    r"\bIAM\b": "I-A-M",
    r"\bCLI\b": "C-L-I",
    r"\bAPI\b": "A-P-I",
    r"\bAPIs\b": "A-P-Is",
    r"\bNginx\b": "Engine-X",
    r"\bnginx\b": "Engine-X",
    r"\bSQL\b": "Sequel",
    r"\bsql\b": "Sequel",
    r"\bPostgreSQL\b": "Postgres Q-L",
    r"\bpostgresql\b": "Postgres Q-L",
    r"\bNoSQL\b": "No-Sequel",
    r"\bGUI\b": "Goo-ey",
    r"\bSaaS\b": "Sass",
    r"\bIaaS\b": "Eye-as",
    r"\bPaaS\b": "Pass",
    r"\bOS\b": "O-S",
    r"\bCPU\b": "C-P-U",
    r"\bRAM\b": "Ram",
    r"\bSSH\b": "S-S-H",
    r"\bIP\b": "I-P",
    r"\bDNS\b": "D-N-S",
    r"\bHTTP\b": "H-T-T-P",
    r"\bHTTPS\b": "H-T-T-P-S",
    r"\bJSON\b": "Jason",
    r"\bHTML\b": "H-T-M-L",
    r"\bCSS\b": "C-S-S",
    r"\bSDK\b": "S-D-K",
    r"\bIDE\b": "I-D-E",
}

ABBREVIATIONS = (
    "e.g.", "i.e.", "etc.", "vs.", "mr.", "mrs.", "dr.", "prof.", "inc.", "ltd.", "co.", "v0.", "v1.", "v2.",
)


class NarrationStyle(str, Enum):
    EDUCATIONAL = "educational"       # Clear, moderate pace, distinct conceptual pauses
    CONVERSATIONAL = "conversational" # Natural, engaging cadence, lively inflection
    PROFESSIONAL = "professional"     # Measured, authoritative, steady pace


STYLE_CONFIGS: dict[NarrationStyle, dict[str, Any]] = {
    NarrationStyle.EDUCATIONAL: {
        "rate": "-5%",
        "pitch": "+0Hz",
        "sentence_pause_ms": 350,
        "clause_pause_ms": 180,
    },
    NarrationStyle.CONVERSATIONAL: {
        "rate": "+0%",
        "pitch": "+1Hz",
        "sentence_pause_ms": 280,
        "clause_pause_ms": 140,
    },
    NarrationStyle.PROFESSIONAL: {
        "rate": "-2%",
        "pitch": "-1Hz",
        "sentence_pause_ms": 320,
        "clause_pause_ms": 160,
    },
}


class SpeechPreparer:
    """
    Preprocesses raw video narration scripts into natural, human-like speech inputs:
    - Normalizes technical DevOps terminology for clean phonetic pronunciation.
    - Inserts rhythmic pauses for breathing and emphasis.
    - Handles sentence splitting without mangling common abbreviations.
    - Formats both rich SSML (for Edge-TTS) and rhythmic plain text (for Piper).
    """

    def __init__(self, style: NarrationStyle = NarrationStyle.EDUCATIONAL) -> None:
        self.style = style

    def normalize_technical_terms(self, text: str) -> str:
        """Expands technical terms and acronyms to ensure correct pronunciation."""
        result = text
        for pattern, replacement in TECHNICAL_PRONUNCIATION_MAP.items():
            result = re.sub(pattern, replacement, result)
        return result

    def split_into_sentences(self, text: str) -> list[str]:
        """
        Splits script text into sentences while protecting abbreviations and technical version codes.
        """
        # Protect abbreviations temporarily
        masked = text
        protected: dict[str, str] = {}
        for idx, abbr in enumerate(ABBREVIATIONS):
            token = f"__ABBR_{idx}__"
            pattern = re.compile(re.escape(abbr), re.IGNORECASE)
            if pattern.search(masked):
                protected[token] = abbr
                masked = pattern.sub(token, masked)

        # Split on sentence boundaries: period, question mark, exclamation mark followed by whitespace
        parts = re.split(r"(?<=[.?!])\s+", masked)

        sentences: list[str] = []
        for p in parts:
            p_clean = p.strip()
            if not p_clean:
                continue
            # Restore protected abbreviations
            for token, abbr in protected.items():
                p_clean = p_clean.replace(token, abbr)
            sentences.append(p_clean)

        return sentences

    def prepare_plain_text(self, text: str, style: NarrationStyle | None = None) -> str:
        """
        Produces clean, phonetically normalized plain text for offline TTS engines (e.g. Piper).
        Ensures consistent punctuation spacing for natural rhythmic pauses.
        """
        chosen_style = style or self.style
        normalized = self.normalize_technical_terms(text.strip())

        # Ensure breathing space around commas and colons
        normalized = re.sub(r",\s*", ", ", normalized)
        normalized = re.sub(r":\s*", ": ", normalized)
        normalized = re.sub(r"\s+", " ", normalized)

        return normalized

    def prepare_ssml(
        self,
        text: str,
        voice: str = "en-IN-PrabhatNeural",
        style: NarrationStyle | None = None,
        custom_rate: str | None = None,
        custom_pitch: str | None = None,
    ) -> str:
        """
        Produces studio-quality W3C SSML for neural speech synthesis (e.g. Edge-TTS).
        Applies prosody parameters and sentence-level breath pauses.
        """
        chosen_style = style or self.style
        cfg = STYLE_CONFIGS.get(chosen_style, STYLE_CONFIGS[NarrationStyle.EDUCATIONAL])

        rate = custom_rate or cfg["rate"]
        pitch = custom_pitch or cfg["pitch"]
        sent_pause = cfg["sentence_pause_ms"]
        clause_pause = cfg["clause_pause_ms"]

        normalized = self.normalize_technical_terms(text.strip())
        sentences = self.split_into_sentences(normalized)

        # Build SSML elements
        ssml_sentences: list[str] = []
        for s in sentences:
            # Add clause micro-pause after commas
            s_with_breaks = re.sub(
                r",\s*",
                f', <break time="{clause_pause}ms"/> ',
                s,
            )
            # Add sentence-level breath pause
            ssml_sentences.append(f'{s_with_breaks} <break time="{sent_pause}ms"/>')

        body = "\n  ".join(ssml_sentences)

        return (
            '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">\n'
            f'  <voice name="{voice}">\n'
            f'    <prosody rate="{rate}" pitch="{pitch}">\n'
            f'      {body}\n'
            '    </prosody>\n'
            '  </voice>\n'
            '</speak>'
        )
