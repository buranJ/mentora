"""The single backend boundary for LiveKit credentials and token grants."""

from dataclasses import dataclass
from datetime import timedelta
import os

from livekit import api as livekit_api


TOKEN_TTL = timedelta(minutes=10)


class LiveKitConfigurationError(RuntimeError):
    """Raised when a deployment has not configured the server-side provider."""


@dataclass(frozen=True)
class LiveKitSettings:
    server_url: str
    api_key: str
    api_secret: str

    @classmethod
    def from_environment(cls) -> "LiveKitSettings":
        server_url = os.getenv("LIVEKIT_URL", "").strip().rstrip("/")
        api_key = os.getenv("LIVEKIT_API_KEY", "").strip()
        api_secret = os.getenv("LIVEKIT_API_SECRET", "").strip()
        if not (server_url and api_key and api_secret):
            raise LiveKitConfigurationError("LiveKit is not configured")
        if not server_url.startswith(("ws://", "wss://")):
            raise LiveKitConfigurationError("LiveKit URL must use ws:// or wss://")
        return cls(server_url=server_url, api_key=api_key, api_secret=api_secret)


class LiveKitService:
    """Issues narrow, short-lived classroom tokens after application authz."""

    def __init__(self, settings: LiveKitSettings | None = None):
        self.settings = settings or LiveKitSettings.from_environment()

    def create_join_token(
        self,
        *,
        room_name: str,
        participant_identity: str,
        display_name: str,
        is_instructor: bool,
    ) -> str:
        publish_sources = ["camera", "microphone"]
        if is_instructor:
            publish_sources.append("screen_share")
        grants = livekit_api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True,
            can_publish_sources=publish_sources,
            # Deliberately omit administration, recording, ingress and room creation.
            room_admin=False,
            room_create=False,
            room_record=False,
            ingress_admin=False,
        )
        return (
            livekit_api.AccessToken(self.settings.api_key, self.settings.api_secret)
            .with_identity(participant_identity)
            .with_name(display_name)
            .with_ttl(TOKEN_TTL)
            .with_grants(grants)
            .to_jwt()
        )
