from __future__ import annotations
"""AI summarization using Claude API with graceful degradation."""
from app.config import settings


class AISummarizer:
    def __init__(self):
        self.api_key = settings.CLAUDE_API_KEY
        self._client = None

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    @property
    def client(self):
        if self._client is None and self.api_key:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                pass
        return self._client

    def summarize_messages(self, messages: list[str], company_name: str) -> str:
        if not self.enabled:
            return "AI 요약 기능이 비활성화되어 있습니다. .env 파일에 CLAUDE_API_KEY를 설정하세요."

        if not self.client:
            return "Anthropic SDK가 설치되어 있지 않습니다."

        if not messages:
            return "요약할 메시지가 없습니다."

        try:
            combined = "\n---\n".join(messages[:50])  # Limit to 50 messages
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": (
                        f"다음은 {company_name}에 대한 최근 Slack 대화입니다.\n"
                        "투자 판단에 중요한 핵심 내용을 3-5문장으로 요약해주세요.\n"
                        "특히 매출, 성장, 팀, 시장 관련 내용을 강조해주세요.\n\n"
                        f"대화 내용:\n{combined}"
                    ),
                }],
            )
            return response.content[0].text
        except Exception as e:
            return f"AI 요약 생성 실패: {str(e)}"


ai_summarizer = AISummarizer()
