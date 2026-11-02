from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Standard environment variable mappings
ENV_KEY_MAP = {
    "openai": "OPENAI_API_KEY",
    "elevenlabs": "ELEVENLABS_API_KEY",
    "luma": "LUMA_API_KEY",
    "runway": "RUNWAY_API_KEY",
    "suno": "SUNO_API_KEY",
    "replicate": "REPLICATE_API_TOKEN",
    "kling": "KLING_API_KEY",
    "pika": "PIKA_API_KEY",
}


def _config_path() -> Path:
    return Path.home() / ".animatube" / "ai_credentials.json"


class AICredentialManager:
    """
    Secure credential manager for AI provider access tokens.
    Priority order:
    1. Environment variables (e.g. LUMA_API_KEY, ELEVENLABS_API_KEY)
    2. Local user credentials file (~/.animatube/ai_credentials.json)
    
    Security rules:
    - Never hardcoded in source code or committed to version control.
    - Stored outside the repository directory.
    - Masked for UI display (e.g. 'sk-123...89ab').
    """

    def __init__(self, config_file: str | Path | None = None) -> None:
        self.config_file = Path(config_file).expanduser().resolve() if config_file else _config_path()

    def get_key(self, provider_id: str) -> str:
        """Retrieves active API key for a provider, checking env vars first, then local config."""
        pid = provider_id.lower().strip()
        env_var = ENV_KEY_MAP.get(pid, f"{pid.upper()}_API_KEY")
        if env_var in os.environ and os.environ[env_var].strip():
            return os.environ[env_var].strip()

        # Check local config file
        if self.config_file.is_file():
            try:
                data = json.loads(self.config_file.read_text(encoding="utf-8"))
                if isinstance(data, dict) and pid in data and data[pid].strip():
                    return data[pid].strip()
            except Exception as exc:
                logger.warning("Could not read credentials from %s: %s", self.config_file, exc)

        return ""

    def has_key(self, provider_id: str) -> bool:
        """Checks if a valid key is configured without exposing the secret."""
        return bool(self.get_key(provider_id))

    def set_key(self, provider_id: str, secret_key: str) -> None:
        """Saves a key locally to ~/.animatube/ai_credentials.json."""
        pid = provider_id.lower().strip()
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        data: dict[str, Any] = {}
        if self.config_file.is_file():
            try:
                data = json.loads(self.config_file.read_text(encoding="utf-8"))
            except Exception:
                data = {}

        if secret_key.strip():
            data[pid] = secret_key.strip()
        else:
            data.pop(pid, None)

        self.config_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def masked_key(self, provider_id: str) -> str:
        """Returns safe masked representation for UI presentation, e.g. 'sk-ab***wxyz'."""
        key = self.get_key(provider_id)
        if not key:
            return ""
        if len(key) <= 8:
            return "********"
        return f"{key[:4]}...{key[-4:]}"
