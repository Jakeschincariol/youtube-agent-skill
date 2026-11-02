from __future__ import annotations

import logging
from typing import Any

from animatube.ai.interfaces import (
    BaseAIProvider,
    MusicGenerationProvider,
    VideoGenerationProvider,
    VoiceGenerationProvider,
)
from animatube.ai.mock_providers import (
    MockMusicProvider,
    MockVideoProvider,
    MockVoiceProvider,
)
from animatube.ai.models import MediaType

logger = logging.getLogger(__name__)


class AIProviderRegistry:
    """
    Central registry for discovering, registering, and selecting AI generation adapters.
    Allows interchangeable providers for video, voice, and music generation.
    """

    _instance: AIProviderRegistry | None = None

    def __init__(self) -> None:
        self._providers: dict[MediaType, dict[str, BaseAIProvider]] = {
            MediaType.VIDEO: {},
            MediaType.VOICE: {},
            MediaType.MUSIC: {},
        }
        self._default_provider_ids: dict[MediaType, str] = {}
        self._register_default_providers()

    @classmethod
    def get_instance(cls) -> AIProviderRegistry:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _register_default_providers(self) -> None:
        # Register built-in mock providers (guaranteed offline / CI availability)
        mock_video = MockVideoProvider()
        mock_voice = MockVoiceProvider()
        mock_music = MockMusicProvider()

        self.register_provider(mock_video, set_as_default=True)
        self.register_provider(mock_voice, set_as_default=True)
        self.register_provider(mock_music, set_as_default=True)

    def register_provider(self, provider: BaseAIProvider, set_as_default: bool = False) -> None:
        """Registers a new provider adapter in the registry."""
        m_type = provider.media_type
        pid = provider.provider_id
        self._providers[m_type][pid] = provider
        if set_as_default or m_type not in self._default_provider_ids:
            self._default_provider_ids[m_type] = pid
        logger.debug("Registered %s provider: %s (%s)", m_type.value, pid, provider.provider_name)

    def unregister_provider(self, media_type: MediaType, provider_id: str) -> None:
        """Removes a provider adapter from the registry."""
        if provider_id in self._providers[media_type]:
            del self._providers[media_type][provider_id]
            if self._default_provider_ids.get(media_type) == provider_id:
                # Fall back to first available
                available = list(self._providers[media_type].keys())
                self._default_provider_ids[media_type] = available[0] if available else ""

    def get_provider(self, media_type: MediaType, provider_id: str | None = None) -> BaseAIProvider:
        """Retrieves provider by ID, or returns the default provider for the requested media type."""
        pid = provider_id or self._default_provider_ids.get(media_type)
        if not pid or pid not in self._providers[media_type]:
            available = list(self._providers[media_type].keys())
            if available:
                pid = available[0]
            else:
                raise KeyError(f"No providers registered for media type: {media_type.value}")
        return self._providers[media_type][pid]

    def get_video_provider(self, provider_id: str | None = None) -> VideoGenerationProvider:
        prov = self.get_provider(MediaType.VIDEO, provider_id)
        assert isinstance(prov, VideoGenerationProvider)
        return prov

    def get_voice_provider(self, provider_id: str | None = None) -> VoiceGenerationProvider:
        prov = self.get_provider(MediaType.VOICE, provider_id)
        assert isinstance(prov, VoiceGenerationProvider)
        return prov

    def get_music_provider(self, provider_id: str | None = None) -> MusicGenerationProvider:
        prov = self.get_provider(MediaType.MUSIC, provider_id)
        assert isinstance(prov, MusicGenerationProvider)
        return prov

    def set_default_provider(self, media_type: MediaType, provider_id: str) -> None:
        if provider_id not in self._providers[media_type]:
            raise KeyError(f"Provider {provider_id} not registered for {media_type.value}")
        self._default_provider_ids[media_type] = provider_id

    def list_providers(self, media_type: MediaType | None = None) -> list[dict[str, Any]]:
        """Lists registered providers and their availability status."""
        types = [media_type] if media_type else [MediaType.VIDEO, MediaType.VOICE, MediaType.MUSIC]
        result = []
        for mt in types:
            for pid, prov in self._providers[mt].items():
                result.append({
                    "media_type": mt.value,
                    "provider_id": pid,
                    "provider_name": prov.provider_name,
                    "is_default": (self._default_provider_ids.get(mt) == pid),
                    "is_available": prov.is_available(),
                    "capabilities": prov.capabilities,
                })
        return result
