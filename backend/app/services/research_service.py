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

WEB_RESEARCH_SYSTEM_PROMPT = """You are a venture capital analyst. Research the given startup company using web search to find:
1. Latest funding information (round, amount, date, lead investor, other investors)
2. Revenue and growth metrics (MRR, ARR, growth rate)
3. Team size and key hires
4. Customer count and notable customers
5. Market position and competitive landscape

After researching, provide your findings as JSON in the exact format below. Use null for fields you could not find reliable information about.

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

Currency note: Korean startups typically report in KRW. Convert 억 = 100,000,000, 만 = 10,000.
IMPORTANT: List ALL investors you can find across all funding rounds, not just the latest."""


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

        context_hint = f"\nAdditional context: {additional_context}" if additional_context else ""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=WEB_RESEARCH_SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": (
                        f"Research this Korean startup company: {company_name}{context_hint}\n\n"
                        "Search for their latest funding rounds, investors, revenue, team size, "
                        "and growth metrics. Provide structured JSON output."
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

        system_prompt = f"""You are a senior venture capital analyst assistant helping evaluate Korean startups for follow-on investment decisions. You speak Korean by default unless the user writes in English.

You have web search capability. When the user asks about news, articles, funding announcements, or any information that requires up-to-date data, USE web search proactively. Do not say you cannot search — you CAN.

COMPANY CONTEXT:
{company_context}

YOUR ROLE:
- Search the web to find latest news, articles, and announcements about the company
- Help triangulate growth data when direct metrics are unavailable
- Suggest alternative data sources and proxy metrics
- Discuss competitive landscape and market dynamics
- Provide frameworks for evaluating companies with incomplete data
- Share approaches for estimating revenue, growth, burn rate from public signals
- Consider Korean startup ecosystem specifics (TIPS, government grants, local VCs)

TRIANGULATION APPROACHES you can suggest:
1. Job postings analysis (headcount growth proxy)
2. App store rankings / web traffic trends
3. Industry benchmarks by sector and stage
4. Press releases and funding announcements
5. LinkedIn employee count tracking
6. Government registry data (dart.fss.or.kr for Korean companies)
7. Customer review volume and trends
8. Social media presence and engagement growth
9. Partnership and integration announcements
10. Patent filings and R&D signals

When the user asks you to find articles, news, or any web-based information, ALWAYS use web search first before responding. Include source URLs when citing information from searches.

Keep responses concise and actionable. Use Korean unless the user writes in English."""

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
