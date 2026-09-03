"""
Speech-to-text service abstraction.
The browser-based provider streams audio processed on the client side via
the Web Speech API. The backend receives the transcript text over WebSocket.
This module handles the provider configuration and abstracts future providers.
"""
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class STTService:
    """
    Speech-to-text service abstraction layer.

    Current providers:
    - "browser": Uses the browser Web Speech API (client-side, no key needed)
    - "deepgram": Deepgram streaming API (requires STT_API_KEY)
    - "assemblyai": AssemblyAI streaming API (requires STT_API_KEY)
    """

    def __init__(self):
        self.provider = settings.stt_provider
        self.api_key = settings.stt_api_key
        logger.info(f"STT provider: {self.provider}")

    def get_provider_info(self) -> dict:
        return {
            "provider": self.provider,
            "streaming": True,
            "requires_key": self.provider != "browser",
            "configured": self.provider == "browser" or bool(self.api_key),
        }

    def validate_transcript_chunk(self, text: str) -> bool:
        """Validate that a received transcript chunk is usable."""
        if not text or not text.strip():
            return False
        if len(text.strip()) < 2:
            return False
        return True


_stt_service: STTService | None = None


def get_stt_service() -> STTService:
    global _stt_service
    if _stt_service is None:
        _stt_service = STTService()
    return _stt_service
