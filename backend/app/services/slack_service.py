from __future__ import annotations
"""Slack integration service with graceful degradation."""
from app.config import settings


class SlackService:
    def __init__(self):
        self.token = settings.SLACK_BOT_TOKEN
        self._client = None

    @property
    def is_connected(self) -> bool:
        return bool(self.token)

    @property
    def client(self):
        if self._client is None and self.token:
            try:
                from slack_sdk import WebClient
                self._client = WebClient(token=self.token)
            except ImportError:
                pass
        return self._client

    def get_status(self) -> dict:
        if not self.is_connected:
            return {"connected": False, "message": "SLACK_BOT_TOKEN not configured. Set it in .env to enable Slack integration."}
        try:
            response = self.client.auth_test()
            return {
                "connected": True,
                "workspace_name": response.get("team", ""),
                "bot_user": response.get("user", ""),
            }
        except Exception as e:
            return {"connected": False, "message": str(e)}

    def search_channels(self, query: str = "") -> list[dict]:
        if not self.client:
            return []
        try:
            response = self.client.conversations_list(limit=100, types="public_channel")
            channels = response.get("channels", [])
            if query:
                channels = [c for c in channels if query.lower() in c.get("name", "").lower()]
            return [
                {"channel_id": c["id"], "channel_name": c["name"], "member_count": c.get("num_members", 0)}
                for c in channels
            ]
        except Exception:
            return []

    def fetch_messages(self, channel_id: str, limit: int = 100) -> list[dict]:
        if not self.client:
            return []
        try:
            response = self.client.conversations_history(channel=channel_id, limit=limit)
            return [
                {
                    "message_ts": m.get("ts", ""),
                    "user_name": m.get("user", "unknown"),
                    "text": m.get("text", ""),
                }
                for m in response.get("messages", [])
            ]
        except Exception:
            return []


slack_service = SlackService()
