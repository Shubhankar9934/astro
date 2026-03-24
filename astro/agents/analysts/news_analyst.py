from __future__ import annotations

from typing import Any, Dict

from astro.agents.shared.grounding import GROUNDING_PREFIX, STUB_NO_NEWS_EVIDENCE
from astro.decision_engine.state_manager import DecisionContext


def create_news_analyst(llm):
    def node(state: Dict[str, Any]) -> Dict[str, Any]:
        ticker = state["company_of_interest"]
        current_date = state["trade_date"]
        ctx: DecisionContext | None = state.get("astro_context")
        if ctx is None:
            return {"news_report": STUB_NO_NEWS_EVIDENCE}
        real_ev = ctx.extra.get("news_has_evidence")
        proxy_ev = ctx.extra.get("news_proxy_has_evidence")
        if ctx.news_summary.startswith("(No news pipeline run.)") and not proxy_ev:
            return {"news_report": STUB_NO_NEWS_EVIDENCE}
        if real_ev is False and not proxy_ev:
            return {"news_report": STUB_NO_NEWS_EVIDENCE}
        data = ctx.news_summary
        proxy_only = ""
        if real_ev is False and proxy_ev:
            proxy_only = "IMPORTANT: No real headline counts — only volatility/ATR spike proxy. Do NOT cite specific news events.\n"
        prompt = f"""{GROUNDING_PREFIX}
{proxy_only}You are a macro and company news analyst for {ticker} as of {current_date}.
Using ONLY the digest below (aggregated counts / fused features), describe intensity as encoded in data. Do not invent stories. End with a Markdown table.

NEWS DIGEST:
{data}
"""
        response = llm.invoke(prompt)
        return {"news_report": response.content}

    return node
