from __future__ import annotations
"""AI-powered company research using Claude API."""
import json
import re
from app.config import settings


EXTRACTION_SYSTEM_PROMPT = """You are a venture capital analyst assistant. Extract structured growth metrics from the provided text about a startup company.

Return ONLY valid JSON with the following fields. Use null for any field you cannot determine from the text. All monetary values should be in KRW unless clearly stated otherwise.

{
  "monthly_revenue": <number or null, in raw currency units>,
  "revenue_currency": <"KRW" or "USD">,
  "arr": <number or null>,
  "mrr": <number or null>,
  "mrr_growth_rate_pct": <number or null, monthly MoM growth as percentage>,
  "monthly_burn": <number or null>,
  "cash_on_hand": <number or null>,
  "runway_months": <number or null>,
  "headcount": <integer or null>,
  "paying_customers": <integer or null>,
  "ndr_pct": <number or null, net dollar retention percentage>,
  "key_metric_value": <number or null>,
  "key_metric_name": <string or null>,
  "last_funding_date": <"YYYY-MM-DD" string or null>,
  "last_funding_amount": <number or null>,
  "last_funding_round": <string or null, e.g. "seed", "pre-a", "a">,
  "investors": [{"name": "<investor name>", "round": "<funding round>", "role": "<lead or follow>"}],
  "notes": <string summarizing key qualitative insights, in Korean>
}

Important rules:
- Convert annual revenue to monthly by dividing by 12 if only annual is given
- Convert Korean currency units: 억 = 100,000,000, 만 = 10,000
- If ARR is given but not MRR, compute MRR as ARR/12
- Growth rates should be monthly MoM percentage
- Extract ALL investor names mentioned (VC firms, angels, corporate investors)
- The notes field should capture qualitative insights: market position, key customers, product direction, risks"""

WEB_RESEARCH_SYSTEM_PROMPT = """당신은 벤처캐피탈 애널리스트입니다. 주어진 스타트업에 대해 웹 검색을 통해 다음 정보를 조사하세요:
1. 최신 투자 유치 정보 (라운드, 금액, 날짜, 리드 투자자, 기타 투자자)
2. 매출 및 성장 지표 (MRR, ARR, 성장률)
3. 팀 규모 및 주요 채용
4. 고객 수 및 주요 고객
5. 시장 포지션 및 경쟁 환경

CRITICAL SEARCH INSTRUCTIONS:
- 반드시 한국어로 검색하세요. 예: "회사명 투자 유치", "회사명 시리즈A", "회사명 매출"
- 한국어 검색과 영어 검색을 모두 시도하세요
- 한국 뉴스 소스: 플래텀, 벤처스퀘어, 더벨, 아웃스탠딩, 매일경제, 한국경제 등을 우선 확인
- 회사명의 한국어/영어 표기를 모두 검색하세요

조사 후 아래 JSON 형식으로 결과를 제공하세요. 확인할 수 없는 필드는 null로 설정하세요.

{
  "monthly_revenue": <number or null, in raw currency units>,
  "revenue_currency": <"KRW" or "USD">,
  "arr": <number or null>,
  "mrr": <number or null>,
  "mrr_growth_rate_pct": <number or null>,
  "monthly_burn": <number or null>,
  "cash_on_hand": <number or null>,
  "runway_months": <number or null>,
  "headcount": <integer or null>,
  "paying_customers": <integer or null>,
  "ndr_pct": <number or null>,
  "key_metric_value": <number or null>,
  "key_metric_name": <string or null>,
  "last_funding_date": <"YYYY-MM-DD" string or null>,
  "last_funding_amount": <number or null>,
  "last_funding_round": <string or null>,
  "investors": [{"name": "<investor name>", "round": "<funding round>", "role": "<lead or follow>"}],
  "notes": <string summarizing research findings and confidence level, in Korean>,
  "sources": [{"url": "<source url>", "title": "<source title>"}]
}

통화 참고: 한국 스타트업은 보통 KRW 기준. 억 = 100,000,000, 만 = 10,000.
중요: 최신 라운드뿐만 아니라 모든 라운드의 투자자를 빠짐없이 나열하세요."""


class ResearchService:
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

    def extract_from_text(self, text: str, company_name: str) -> dict:
        """Extract structured growth metrics + investors from unstructured text."""
        if not self.client:
            raise ValueError("AI 서비스를 사용할 수 없습니다. CLAUDE_API_KEY를 확인하세요.")

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                system=EXTRACTION_SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": f"Company: {company_name}\n\nText to analyze:\n{text}",
                }],
            )
            raw_text = response.content[0].text
            metrics = self._parse_metrics_response(raw_text)
            return {"metrics": metrics, "raw": raw_text}
        except Exception as e:
            raise ValueError(f"AI 분석 실패: {str(e)}")

    def web_research(self, company_name: str, additional_context: str = "") -> dict:
        """Research a company using Claude's web search tool."""
        if not self.client:
            raise ValueError("AI 서비스를 사용할 수 없습니다. CLAUDE_API_KEY를 확인하세요.")

        context_hint = f"\n추가 정보: {additional_context}" if additional_context else ""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=WEB_RESEARCH_SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": (
                        f"다음 한국 스타트업을 조사하세요: {company_name}{context_hint}\n\n"
                        f"'{company_name} 투자 유치', '{company_name} 시리즈', '{company_name} 매출' 등의 "
                        "한국어 키워드로 검색하세요. 영어로도 검색해보세요. "
                        "투자 라운드, 투자자, 매출, 팀 규모, 성장 지표를 찾아 구조화된 JSON으로 제공하세요."
                    ),
                }],
                tools=[{
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": 10,
                    "user_location": {
                        "type": "approximate",
                        "country": "KR",
                        "timezone": "Asia/Seoul",
                    },
                }],
            )

            # Extract the final text block (Claude may return tool_use + text blocks)
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text = block.text

            metrics = self._parse_metrics_response(final_text)
            return {"metrics": metrics, "raw": final_text}
        except Exception as e:
            raise ValueError(f"웹 리서치 실패: {str(e)}")

    def chat(self, message: str, company_context: str, history: list[dict]) -> str:
        """Have a multi-turn conversation about a company's growth and data triangulation."""
        if not self.client:
            raise ValueError("AI 서비스를 사용할 수 없습니다. CLAUDE_API_KEY를 확인하세요.")

        system_prompt = f"""당신은 한국 스타트업 후속 투자를 평가하는 시니어 VC 애널리스트 어시스턴트입니다. 한국어로 응답하세요.

웹 검색 기능이 있습니다. 뉴스, 기사, 투자 유치 발표 등 최신 정보가 필요할 때 반드시 웹 검색을 사용하세요.

CRITICAL SEARCH INSTRUCTIONS:
- 반드시 한국어로 검색하세요. 예: "회사명 투자 유치", "회사명 시리즈A", "회사명 뉴스"
- 한국어 검색과 영어 검색을 모두 시도하세요
- 한국 스타트업 뉴스 소스: 플래텀, 벤처스퀘어, 더벨, 아웃스탠딩, 매일경제, 한국경제, 조선비즈, 디지털타임스 등
- 검색 결과에서 찾은 정보는 반드시 출처 URL과 함께 인용하세요

COMPANY CONTEXT:
{company_context}

YOUR ROLE:
- 웹 검색으로 해당 회사의 최신 뉴스, 기사, 투자 유치 정보를 찾기
- 직접적인 지표가 없을 때 간접 데이터로 성장성 삼각측량 (triangulation)
- 경쟁 환경, 시장 동향 분석
- 불완전한 데이터로 회사 평가하는 프레임워크 제공
- 공개 신호로 매출, 성장률, 번레이트 추정하는 방법 제안
- 한국 스타트업 생태계 특성 고려 (TIPS, 정부지원금, 국내 VC 등)

TRIANGULATION 방법:
1. 채용공고 분석 (인원 증가 프록시)
2. 앱스토어 순위 / 웹 트래픽 추이
3. 업종 및 단계별 벤치마크
4. 보도자료 및 투자 유치 공시
5. LinkedIn 직원 수 추적
6. dart.fss.or.kr 공시 데이터
7. 고객 리뷰 양 및 추이
8. SNS 활동 및 팔로워 성장
9. 파트너십 및 연동 발표
10. 특허 출원 및 R&D 신호

사용자가 기사, 뉴스, 웹 기반 정보를 요청하면 반드시 웹 검색을 먼저 수행한 후 응답하세요. 출처 URL을 반드시 포함하세요."""

        messages = []
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": message})

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=system_prompt,
                messages=messages,
                tools=[{
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": 10,
                    "user_location": {
                        "type": "approximate",
                        "country": "KR",
                        "timezone": "Asia/Seoul",
                    },
                }],
            )

            # Extract all text blocks (Claude may return tool_use + text blocks)
            text_parts = []
            for block in response.content:
                if hasattr(block, "text"):
                    text_parts.append(block.text)
            return "\n".join(text_parts) if text_parts else "응답을 생성할 수 없습니다."
        except Exception as e:
            raise ValueError(f"채팅 실패: {str(e)}")

    def _parse_metrics_response(self, response_text: str) -> dict:
        """Extract JSON from Claude's response, handling markdown code blocks.
        Falls back to a default dict with notes if no JSON is found."""
        # Try to extract JSON from markdown code block
        json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", response_text, re.DOTALL)
        if json_match:
            text = json_match.group(1)
        else:
            text = response_text

        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            # Try to find any JSON object in the text
            brace_match = re.search(r"\{.*\}", text, re.DOTALL)
            if brace_match:
                try:
                    return json.loads(brace_match.group(0))
                except json.JSONDecodeError:
                    pass

            # Graceful fallback: return empty metrics with the text as notes
            # This handles cases where Claude returns a text summary instead of JSON
            return self._empty_metrics(notes=response_text[:500])

    @staticmethod
    def _empty_metrics(notes: str = "") -> dict:
        """Return a default metrics dict with all fields null."""
        return {
            "monthly_revenue": None, "revenue_currency": "KRW",
            "arr": None, "mrr": None, "mrr_growth_rate_pct": None,
            "monthly_burn": None, "cash_on_hand": None, "runway_months": None,
            "headcount": None, "paying_customers": None, "ndr_pct": None,
            "key_metric_value": None, "key_metric_name": None,
            "last_funding_date": None, "last_funding_amount": None,
            "last_funding_round": None,
            "investors": [], "sources": [],
            "notes": notes or "데이터를 찾을 수 없습니다.",
        }


research_service = ResearchService()
